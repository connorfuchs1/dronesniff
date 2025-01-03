import os
import subprocess
import datetime

# Define captures directory
capture_dir = "/home/pi/drone_sniff/captures"
os.makedirs(capture_dir, exist_ok=True)

# Generate a timestamped filename for the GPS data
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
gps_filename = os.path.join(capture_dir, f"gps_capture_{timestamp}.log")

# Use gpspipe to collect GPS data in JSON format
with open(gps_filename, "w") as gps_file:
    try:
        subprocess.run(["gpspipe", "-w"], stdout=gps_file, check=True)
    except subprocess.SubprocessError as e:
        print(f"Error while collecting GPS data: {e}")
