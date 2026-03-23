#!/bin/bash
# fajr-watch first-boot provisioning script
#
# This runs once on first boot of a fresh Raspberry Pi OS image.
# It installs all dependencies, configures the system, and enables
# the fajr-watch service.
#
# Usage: placed in /boot/fajr-watch/first-boot.sh by the image builder,
# triggered by a systemd oneshot service on first boot.

set -euo pipefail

LOG="/var/log/fajr-watch-provision.log"
exec &> >(tee -a "$LOG")

echo "=== fajr-watch first-boot provisioning ==="
echo "Date: $(date -u)"

# ── System setup ──

echo "[1/8] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

echo "[2/8] Installing system dependencies..."
apt-get install -y -qq \
    python3-pip python3-venv python3-numpy python3-opencv \
    python3-yaml python3-scipy python3-astropy \
    gpsd gpsd-clients libgps-dev \
    libusb-1.0-0-dev libudev-dev \
    ntp ntpdate \
    jq curl

# ── GPS setup ──

echo "[3/8] Configuring GPS..."
if [ -e /dev/ttyUSB0 ] || [ -e /dev/ttyACM0 ]; then
    systemctl enable gpsd
    systemctl start gpsd
    echo "GPS device detected"
else
    echo "No GPS device found. Using NTP for time sync."
fi

# ── Python environment ──

echo "[4/8] Setting up Python environment..."
VENV="/opt/fajr-watch/venv"
python3 -m venv --system-site-packages "$VENV"
source "$VENV/bin/activate"

pip install --quiet \
    ephem \
    pyyaml \
    requests \
    Pillow

# Install ZWO ASI SDK if a ZWO camera is configured
STATION_CONFIG="/boot/fajr-watch/station.yaml"
if [ -f "$STATION_CONFIG" ]; then
    CAMERA_TYPE=$(python3 -c "
import yaml
with open('$STATION_CONFIG') as f:
    c = yaml.safe_load(f)
print(c.get('camera', {}).get('type', ''))
")
    if [[ "$CAMERA_TYPE" == zwo_* ]]; then
        echo "ZWO camera configured. Installing ASI SDK..."
        pip install --quiet zwoasi
        # Download ZWO SDK library
        if [ ! -f /usr/lib/libASICamera2.so ]; then
            ARCH=$(uname -m)
            if [ "$ARCH" = "aarch64" ]; then
                SDK_URL="https://github.com/stevemarple/python-zwoasi/raw/master/lib/armv8/libASICamera2.so"
            else
                SDK_URL="https://github.com/stevemarple/python-zwoasi/raw/master/lib/armv7/libASICamera2.so"
            fi
            curl -sL "$SDK_URL" -o /usr/lib/libASICamera2.so
            chmod 644 /usr/lib/libASICamera2.so
            ldconfig
        fi
    fi

    if [[ "$CAMERA_TYPE" == pi_* ]]; then
        echo "Pi camera configured. Installing picamera2..."
        pip install --quiet picamera2
    fi
fi

# ── Install fajr-watch ──

echo "[5/8] Installing fajr-watch software..."
INSTALL_DIR="/opt/fajr-watch/app"
if [ -d /boot/fajr-watch/src ]; then
    cp -r /boot/fajr-watch/src "$INSTALL_DIR/src"
    cp -r /boot/fajr-watch/config "$INSTALL_DIR/config"
else
    # Clone from GitHub if not bundled on the SD card
    git clone --depth 1 https://github.com/acamarata/fajr-watch.git "$INSTALL_DIR"
fi

# ── Data directories ──

echo "[6/8] Creating data directories..."
mkdir -p /var/lib/fajr-watch/data/{captures,results,upload-queue}
chown -R pi:pi /var/lib/fajr-watch

# ── Copy station config ──

if [ -f "$STATION_CONFIG" ]; then
    cp "$STATION_CONFIG" "$INSTALL_DIR/config/station.yaml"
    echo "Station config loaded from boot partition"
fi

# ── WiFi setup from station config ──

if [ -f "$STATION_CONFIG" ]; then
    WIFI_SSID=$(python3 -c "
import yaml
with open('$STATION_CONFIG') as f:
    c = yaml.safe_load(f)
print(c.get('network', {}).get('wifi_ssid', ''))
")
    WIFI_PASS=$(python3 -c "
import yaml
with open('$STATION_CONFIG') as f:
    c = yaml.safe_load(f)
print(c.get('network', {}).get('wifi_password', ''))
")
    if [ -n "$WIFI_SSID" ] && [ -n "$WIFI_PASS" ]; then
        echo "[6b] Configuring WiFi: $WIFI_SSID"
        nmcli device wifi connect "$WIFI_SSID" password "$WIFI_PASS" || true
    fi
fi

# ── Systemd service ──

echo "[7/8] Installing systemd service..."
cat > /etc/systemd/system/fajr-watch.service << 'UNIT'
[Unit]
Description=fajr-watch twilight observation station
After=network-online.target gpsd.service
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
Environment=PYTHONPATH=/opt/fajr-watch/app
ExecStart=/opt/fajr-watch/venv/bin/python -m src.capture.scheduler
WorkingDirectory=/opt/fajr-watch/app
Restart=always
RestartSec=60
StandardOutput=append:/var/log/fajr-watch.log
StandardError=append:/var/log/fajr-watch.log

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable fajr-watch.service
systemctl start fajr-watch.service

# ── Upload cron ──

echo "[8/8] Setting up data upload cron..."
cat > /etc/cron.d/fajr-watch-upload << 'CRON'
# Upload completed detection results every hour
0 * * * * pi /opt/fajr-watch/venv/bin/python -m src.upload.sync 2>> /var/log/fajr-watch-upload.log
CRON

# ── Disable first-boot trigger ──

rm -f /boot/fajr-watch/first-boot-trigger
systemctl disable fajr-watch-provision.service 2>/dev/null || true

echo ""
echo "=== fajr-watch provisioning complete ==="
echo "Station ID: $(python3 -c "
import yaml
with open('$STATION_CONFIG') as f:
    c = yaml.safe_load(f)
print(c.get('station', {}).get('id', 'unknown'))
" 2>/dev/null || echo 'unknown')"
echo "Service status:"
systemctl status fajr-watch.service --no-pager || true
echo ""
echo "Logs: journalctl -u fajr-watch -f"
echo "Data: /var/lib/fajr-watch/data/results/"
