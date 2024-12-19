

import subprocess
import datetime
import os

capture_dir = "/home/pi/drone_sniff/captures"
os.makedirs(capture_dir, exist_ok=True)

timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
filename_prefix = f"capture_{timestamp}"

#bring interface down
subprocess.run(["ip", "link", "set","wlan1", "down"], check=True)

#set monitor mode
subprocess.run(["iw", "dev", "wlan1", "set", "type", "monitor"], check=True)

#bring interface back up
subprocess.run(["ip", "link", "set","wlan1", "up"], check=True)



#run airodump with output to csv files
subprocess.run([
    "airodump-ng",
    "--write", os.path.join(capture_dir, filename_prefix),
    "--output-format", "csv,pcap", 
    "wlan1"
])

