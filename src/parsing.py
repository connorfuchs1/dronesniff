import json
import csv
from datetime import datetime

# File paths
gps_log_file = "../captures/gps_capture_20250108-171710.log"
wifi_csv_file = "../captures/capture_20250108-171710-01.csv"

# Function to parse GPS data
def parse_gps_log(file_path):
    gps_data = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            try:
                # Attempt to parse the line as JSON
                data = json.loads(line)
            except json.JSONDecodeError:
                # Try fixing the line by replacing single quotes with double quotes
                try:
                    fixed_line = line.replace("'", '"')
                    data = json.loads(fixed_line)
                except json.JSONDecodeError:
                    print(f"Skipping irreparable line: {line}")
                    continue
            except Exception as e:
                print(f"Error processing line: {line}\n{e}")
                continue

            # Validate and process TPV entries
            if data.get("class") == "TPV" and all(key in data for key in ["lat", "lon", "time"]):
                gps_data.append({
                    "timestamp": datetime.fromisoformat(data["time"].replace("Z", "+00:00")),
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "alt": data.get("alt", None)  # Use `None` if `alt` is not present
                })

    print(f"Total valid GPS entries processed: {len(gps_data)}")
    return gps_data

# Function to parse Wi-Fi CSV data
from datetime import timezone

import pytz  # Import timezone module if not already installed, run: pip install pytz

def parse_wifi_csv(file_path):
    wifi_data = []
    local_tz = pytz.timezone("America/New_York")  # Replace with your local timezone
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            # Skip header row
            if i == 0:
                print(f"Skipping header row: {row}")
                continue

            # Handle rows with insufficient fields
            if len(row) < 15:  # Adjust based on the minimum expected columns
                print(f"Skipping invalid row due to insufficient fields: {row}")
                continue

            try:
                # Strip extra spaces from each field
                row = [field.strip() for field in row]

                # Convert timestamps to UTC
                start_time_local = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
                end_time_local = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")

                # Localize to local timezone and convert to UTC
                start_time_utc = local_tz.localize(start_time_local).astimezone(pytz.utc)
                end_time_utc = local_tz.localize(end_time_local).astimezone(pytz.utc)

                wifi_data.append({
                    "mac": row[0],
                    "start_time": start_time_utc,
                    "end_time": end_time_utc,
                    "ssid": row[13] if row[13] else "Unknown",  # Default to "Unknown" if SSID is empty
                    "signal_strength": int(row[8]),
                })
            except (ValueError, IndexError) as e:
                print(f"Skipping invalid row due to error: {row}\n{e}")

    print(f"Total valid Wi-Fi entries processed: {len(wifi_data)}")
    return wifi_data



# Function to associate GPS and Wi-Fi data
def associate_data(gps_data, wifi_data):
    combined_data = []
    for wifi in wifi_data:
        for gps in gps_data:
            # Check if Wi-Fi timestamp falls within GPS timestamp window
            print(gps["timestamp"])
            print(wifi["start_time"])
            if gps["timestamp"] <= wifi["start_time"] <= gps["timestamp"]:
                combined_data.append({
                    "mac": wifi["mac"],
                    "ssid": wifi["ssid"],
                    "signal_strength": wifi["signal_strength"],
                    "gps_lat": gps["lat"],
                    "gps_lon": gps["lon"],
                    "gps_alt": gps["alt"]
                })
                break
    print(f"Total combined entries: {len(combined_data)}")
    return combined_data

# Main processing
gps_data = parse_gps_log(gps_log_file)
wifi_data = parse_wifi_csv(wifi_csv_file)
combined_data = associate_data(gps_data, wifi_data)

# Save combined data
output_file = "combined_data.json"
with open(output_file, 'w') as f:
    json.dump(combined_data, f, indent=4)

print(f"Data saved to {output_file}")
