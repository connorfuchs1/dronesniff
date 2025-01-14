import json
import csv
import requests
from datetime import datetime, timezone
import pytz  # Install with: pip install pytz

# File paths
gps_log_file = "../captures/gps_capture_20250112-222320.log"
wifi_csv_file = "../captures/capture_20250112-222320-01.csv"

# Function to parse GPS data
def parse_gps_log(file_path):
    gps_data = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                try:
                    fixed_line = line.replace("'", '"')
                    data = json.loads(fixed_line)
                except json.JSONDecodeError:
                    print(f"Skipping irreparable line: {line}")
                    continue

            if data.get("class") == "TPV" and all(key in data for key in ["lat", "lon", "time"]):
                gps_data.append({
                    "timestamp": datetime.fromisoformat(data["time"].replace("Z", "+00:00")),
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "alt": data.get("alt", None)
                })

    print(f"Total valid GPS entries processed: {len(gps_data)}")
    return gps_data

# Function to parse Wi-Fi CSV data
def parse_wifi_csv(file_path):
    dataset1 = []
    dataset2 = []
    local_tz = pytz.timezone("America/New_York")  # Adjust to your timezone

    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        current_dataset = None  # Track which dataset is being processed

        for i, row in enumerate(reader):
            # Skip empty rows
            if not row:
                continue

            # Detect dataset type
            if row[0].strip() == "BSSID":
                current_dataset = 1
                continue
            elif row[0].strip() == "Station MAC":
                current_dataset = 2
                continue

            # Process Dataset 1
            if current_dataset == 1:
                try:
                    # Convert timestamps to UTC
                    first_seen = local_tz.localize(
                        datetime.strptime(row[1].strip(), "%Y-%m-%d %H:%M:%S")
                    ).astimezone(pytz.utc)
                    last_seen = local_tz.localize(
                        datetime.strptime(row[2].strip(), "%Y-%m-%d %H:%M:%S")
                    ).astimezone(pytz.utc)

                    dataset1.append({
                        "bssid": row[0].strip(),
                        "first_seen": first_seen,
                        "last_seen": last_seen,
                        "channel": row[3].strip(),
                        "privacy": row[5].strip(),
                        "ssid": row[13].strip(),
                        "key": row[14].strip() if len(row) > 14 else "Unknown"
                    })
                except (ValueError, IndexError) as e:
                    print(f"Skipping Dataset 1 row {i} due to error: {e}\nRow: {row}")

            # Process Dataset 2
            elif current_dataset == 2:
                try:
                    probed_essids = row[6].split(",") if len(row) > 6 and row[6].strip() else []
                    dataset2.append({
                        "station_mac": row[0].strip(),
                        "first_seen": datetime.strptime(row[1].strip(), "%Y-%m-%d %H:%M:%S"),
                        "last_seen": datetime.strptime(row[2].strip(), "%Y-%m-%d %H:%M:%S"),
                        "power": row[3].strip(),
                        "packets": row[4].strip(),
                        "associated_bssid": row[5].strip(),
                        "probed_essids": probed_essids
                    })
                except (ValueError, IndexError) as e:
                    print(f"Skipping Dataset 2 row {i} due to error: {e}\nRow: {row}")

    print(f"Total entries in Dataset 1: {len(dataset1)}")
    print(f"Total entries in Dataset 2: {len(dataset2)}")
    return dataset1




# Function to lookup MAC address vendor
def lookup_mac_vendor(mac):
    url = f"https://api.macvendors.com/{mac}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text
        else:
            return "Unknown Vendor"
    except requests.RequestException:
        return "Lookup Failed"

# Function to associate GPS and Wi-Fi data
def associate_data(gps_data, wifi_data):
    combined_data = []
    for wifi in wifi_data:
        for i in range(len(gps_data) - 1):
            current_gps = gps_data[i]
            next_gps = gps_data[i + 1]
            
            #print(f"Wi-Fi start time: {wifi['start_time']}, MAC: {wifi['mac']}")
            #print(f"Current GPS range: {current_gps['timestamp']} to {next_gps['timestamp']}")

            # Check if the WiFi start time is between the current and next GPS timestamps
            if current_gps["timestamp"] <= wifi["last_seen"] <= next_gps["timestamp"]:
                
                # Lookup MAC vendor
                vendor = lookup_mac_vendor(wifi["bssid"])
                
                # Combine dataa
                combined_data.append({
                    "mac": wifi["bssid"],
                    "ssid": wifi["ssid"],
                    "gps_lat": current_gps["lat"],
                    "gps_lon": current_gps["lon"],
                    "gps_alt": current_gps["alt"],
                    "vendor": vendor  # Add the vendor to the output
                })
                break
    print(f"Total combined entries: {len(combined_data)}")
    return combined_data

# Main processing
gps_data = parse_gps_log(gps_log_file)
wifi_data = parse_wifi_csv(wifi_csv_file)
combined_data = associate_data(gps_data, wifi_data)

# Save combined data
output_file = "combined_data_with_vendors.json"
with open(output_file, 'w') as f:
    json.dump(combined_data, f, indent=4)

print(f"Data saved to {output_file}")
