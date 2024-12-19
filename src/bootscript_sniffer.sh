#!/usr/bin/env bash
set -e

SERVICE_NAME="sniffer"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_PATH="/home/pi/drone_sniff/src/startup_sniffer.py"
PYTHON_BIN="/usr/bin/python3"

sudo bash -c "cat << 'EOF' > ${SERVICE_FILE}
[Unit]
Description=Start WLAN Sniffer on Boot
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStartPre=/bin/sleep 10
ExecStart=${PYTHON_BIN} ${SCRIPT_PATH}
Restart=on-failure
#User=pi
WorkingDirectory=/home/pi
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"
sudo systemctl start "${SERVICE_NAME}.service"

echo "Setup Complete. Sniffer service is now running and will start automatically on each reboot"
