#!/usr/bin/env bash
set -e

SERVICE_NAME="sniffer"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_PATH="/home/pi/drone_sniff/src/startup_sniffer.py"
PYTHON_BIN="/usr/bin/python3"

cat << 'EOF' > "${SCRIPT_PATH}"


import subprocess

#bring interface down
subprocess.run(["sudo", "ip", "link", "set","wlan", "down"], check=True)

#set monitor mode
subprocess.run(["sudo", "iw", "dev", "wlan1", "set", "type", "monitor"], check=True)

#bring interface back up
subprocess.run(["sudo", "ip", "link", "set","wlan", "up"], check=True)




subprocess.run(["sudo", "airodump-ng", "wlan1"])

EOF

sudo chown pi:pi "${SCRIPT_PATH}"
chmod +x "${SCRIPT_PATH}"

sudo bash -c "cat << 'EOF' > ${SERVICE_FILE}
[Unit]
Description=Start WLAN Sniffer on Boot
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=${PYTHON_BIN} ${SCRIPT_PATH}
Restart=on-failure
User=pi
WorkingDirectory=/home/pi
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=mult-user.target
EOF"

echo "Setup Complete. Sniffer service is now running and will start automatically on each reboot"
