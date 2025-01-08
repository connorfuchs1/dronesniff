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
            try:
                data = json.loads(line.strip())
                # Only process TPV entries with the required fields
                if data.get("class") == "TPV" and all(key in data for key in ["lat", "lon", "time"]):
                    gps_data.append({
                        "timestamp": datetime.fromisoformat(data["time"].replace("Z", "+00:00")),
                        "lat": data["lat"],
                        "lon": data["lon"],
                        "alt": data.get("alt", None)  # Use `None` if `alt` is not present
                    })
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line: {line}")
            except Exception as e:
                print(f"Error processing line: {line}\n{e}")
    return gps_data



# Function to parse Wi-Fi CSV data
def parse_wifi_csv(file_path):
    wifi_data = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                wifi_data.append({
                    "mac": row[0].strip(),
                    "start_time": datetime.strptime(row[1].strip(), "%Y-%m-%d %H:%M:%S"),
                    "end_time": datetime.strptime(row[2].strip(), "%Y-%m-%d %H:%M:%S"),
                    "ssid": row[17].strip(),
                    "signal_strength": int(row[8].strip()),
                })
            except (IndexError, ValueError) as e:
                print(f"Skipping invalid row: {row}")
    return wifi_data

# Function to associate GPS and Wi-Fi data
def associate_data(gps_data, wifi_data):
    combined_data = []
    for wifi in wifi_data:
        for gps in gps_data:
            # Check if Wi-Fi timestamp falls within GPS timestamp window
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
    return combined_data

# Main processing
gps_data = parse_gps_log(gps_log_file)
#wifi_data = parse_wifi_csv(wifi_csv_file)
wifi_data = []
combined_data = associate_data(gps_data, wifi_data)

# Save combined data
output_file = "combined_data.json"
with open(output_file, 'w') as f:
    json.dump(combined_data, f, indent=4)

print(f"Data saved to {output_file}")
