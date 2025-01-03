#!/usr/bin/env bash
set -e

SERVICE_NAME="sniffer"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
START_SCRIPT="/home/pi/drone_sniff/src/start_services.sh"
PYTHON_BIN="/usr/bin/python3"

sudo bash -c "cat << 'EOF' > ${SERVICE_FILE}
[Unit]
Description=Start WLAN Sniffer and GPS Logger on Boot
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 10
ExecStart=${START_SCRIPT}
Restart=on-failure
WorkingDirectory=/home/pi
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"
sudo systemctl start "${SERVICE_NAME}.service"

echo "Setup Complete. Sniffer service is now running and will start automatically on each reboot"
