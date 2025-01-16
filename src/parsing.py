import json
import csv
from datetime import datetime, timezone
import pytz  # Install with: pip install pytz
import math

# File paths
gps_log_file = "../captures/gps_capture_20250115-182326.log"
wifi_csv_file = "../captures/capture_20250115-182326-01.csv"
mac_vendor_file = "../macdata/mac.csv"  # Path to  MAC vendor CSV file

# Function to load MAC vendor data
def load_mac_vendor_data(file_path):
    mac_vendor_map = {}
    with open(file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row["Assignment"] and row["OrganizationName"]:
                # Use the Assignment column (OUI) as the key, and OrganizationName as the value
                mac_vendor_map[row["Assignment"].strip().upper()] = row["OrganizationName"].strip()
    return mac_vendor_map

# Local MAC vendor lookup
def lookup_mac_vendor(mac, mac_vendor_map):
    oui = mac.replace(":", "").upper()[:6]  # Extract OUI (first 6 characters)
    return mac_vendor_map.get(oui, "Unknown Vendor")

# Function to parse GPS data
# Constants for WGS84
WGS84_A = 6378137.0  # Semi-major axis (meters)
WGS84_F = 1 / 298.257223563  # Flattening
WGS84_B = WGS84_A * (1 - WGS84_F)  # Semi-minor axis

# Helper function to convert ECEF to geodetic coordinates
def ecef_to_geodetic(x, y, z):
    e2 = 1 - (WGS84_B**2 / WGS84_A**2)  # Square of eccentricity
    ep2 = (WGS84_A**2 / WGS84_B**2) - 1  # Second eccentricity squared

    p = math.sqrt(x**2 + y**2)
    theta = math.atan2(z * WGS84_A, p * WGS84_B)

    # Latitude
    lat = math.atan2(
        z + ep2 * WGS84_B * math.sin(theta)**3,
        p - e2 * WGS84_A * math.cos(theta)**3,
    )

    # Longitude
    lon = math.atan2(y, x)

    # Altitude
    sin_lat = math.sin(lat)
    N = WGS84_A / math.sqrt(1 - e2 * sin_lat**2)  # Radius of curvature in prime vertical
    alt = (p / math.cos(lat)) - N

    # Convert latitude and longitude to degrees
    lat = math.degrees(lat)
    lon = math.degrees(lon)

    return lat, lon, alt

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

            if data.get("class") == "TPV" and all(key in data for key in ["ecefx", "ecefy", "ecefz", "time"]):
                # Convert ECEF to geodetic coordinates
                lat, lon, alt = ecef_to_geodetic(data["ecefx"], data["ecefy"], data["ecefz"])

                # Append data with converted lat/lon/alt
                gps_data.append({
                    "timestamp": datetime.fromisoformat(data["time"].replace("Z", "+00:00")),
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "ecefx": data["ecefx"],
                    "ecefy": data["ecefy"],
                    "ecefz": data["ecefz"]
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
                if len(row) < 15:  # Ensure row has enough columns
                    print(f"Skipping Dataset 1 row {i} due to insufficient columns.\nRow: {row}")
                    continue
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
                        "authentication": row[7].strip(),
                        "ssid": row[13].strip() if len(row) > 13 else "",
                        "key": row[14].strip() if len(row) > 14 else "Unknown"
                    })
                except (ValueError, IndexError) as e:
                    print(f"Skipping Dataset 1 row {i} due to error: {e}\nRow: {row}")

            # Process Dataset 2
            elif current_dataset == 2:
                if len(row) < 7:  # Ensure row has enough columns
                    print(f"Skipping Dataset 2 row {i} due to insufficient columns.\nRow: {row}")
                    continue
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

# Function to associate GPS and Wi-Fi data
def associate_data(gps_data, wifi_data, mac_vendor_map):
    combined_data = []
    for wifi in wifi_data:
        for i in range(len(gps_data) - 1):
            current_gps = gps_data[i]
            next_gps = gps_data[i + 1]

            # Check if the WiFi last seen time is between the current and next GPS timestamps
            if current_gps["timestamp"] <= wifi["last_seen"] <= next_gps["timestamp"]:
                # Lookup MAC vendor
                vendor = lookup_mac_vendor(wifi["bssid"], mac_vendor_map)
                
                # Combine data
                combined_data.append({
                    "mac": wifi["bssid"],
                    "ssid": wifi["ssid"],
                    "security": wifi["privacy"],
                    "authentication": wifi["authentication"],
                    "gps_lat": current_gps["lat"],
                    "gps_lon": current_gps["lon"],
                    "gps_alt": current_gps["alt"],
                    "vendor": vendor  # Add the vendor to the output
                })
                break
    print(f"Total combined entries: {len(combined_data)}")
    return combined_data

# Main processing
mac_vendor_map = load_mac_vendor_data(mac_vendor_file)
gps_data = parse_gps_log(gps_log_file)
wifi_data = parse_wifi_csv(wifi_csv_file)
combined_data = associate_data(gps_data, wifi_data, mac_vendor_map)

# Save combined data
output_file = "combined_data_with_vendors.json"
with open(output_file, 'w') as f:
    json.dump(combined_data, f, indent=4)

print(f"Data saved to {output_file}")
