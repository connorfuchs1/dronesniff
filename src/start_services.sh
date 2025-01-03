#!/bin/bash
set -e

# Start WLAN Sniffer in the background
echo "Starting WLAN Sniffer..."
/usr/bin/python3 /home/pi/drone_sniff/src/startup_sniffer.py &

# Start GPS Logger in the background
echo "Starting GPS Logger..."
/usr/bin/python3 /home/pi/drone_sniff/src/startup_gps.py &

# Wait for all background processes to start properly
wait
