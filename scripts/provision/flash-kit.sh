#!/bin/bash
# flash-kit.sh — Flash a complete fajr-watch SD card for a volunteer kit.
#
# Writes Raspberry Pi OS Lite + fajr-watch software + station config
# to an SD card in one step. Run on your Mac/Linux workstation.
#
# Usage:
#   ./scripts/provision/flash-kit.sh \
#     --station-id "conneaut-01" \
#     --lat 41.95 --lng -80.55 --elevation 175 \
#     --wifi-ssid "MyNetwork" --wifi-pass "password" \
#     --host-name "Aric Camarata" \
#     --environment suburban --horizon lake \
#     --device /dev/disk4
#
# Requirements:
#   - Raspberry Pi Imager CLI (rpi-imager) or dd
#   - A downloaded Raspberry Pi OS Lite image (.img or .img.xz)
#   - An SD card (32GB+) inserted

set -euo pipefail

# ── Parse arguments ──

STATION_ID=""
LAT=""
LNG=""
ELEVATION="0"
WIFI_SSID=""
WIFI_PASS=""
HOST_NAME=""
ENVIRONMENT="unknown"
HORIZON="unknown"
CAMERA_TYPE="pi_cam3_wide"
DEVICE=""
PI_OS_IMAGE="${PI_OS_IMAGE:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --station-id) STATION_ID="$2"; shift 2;;
        --lat) LAT="$2"; shift 2;;
        --lng) LNG="$2"; shift 2;;
        --elevation) ELEVATION="$2"; shift 2;;
        --wifi-ssid) WIFI_SSID="$2"; shift 2;;
        --wifi-pass) WIFI_PASS="$2"; shift 2;;
        --host-name) HOST_NAME="$2"; shift 2;;
        --environment) ENVIRONMENT="$2"; shift 2;;
        --horizon) HORIZON="$2"; shift 2;;
        --camera) CAMERA_TYPE="$2"; shift 2;;
        --device) DEVICE="$2"; shift 2;;
        --image) PI_OS_IMAGE="$2"; shift 2;;
        *) echo "Unknown argument: $1"; exit 1;;
    esac
done

# ── Validate ──

if [ -z "$STATION_ID" ] || [ -z "$LAT" ] || [ -z "$LNG" ]; then
    echo "Error: --station-id, --lat, and --lng are required."
    echo ""
    echo "Usage: $0 --station-id ID --lat LAT --lng LNG [options]"
    exit 1
fi

if [ -z "$DEVICE" ]; then
    echo "Available disks:"
    if [ "$(uname)" = "Darwin" ]; then
        diskutil list external physical
    else
        lsblk -d -o NAME,SIZE,MODEL | grep -v "^loop"
    fi
    echo ""
    echo "Specify the SD card device with --device /dev/diskN"
    exit 1
fi

echo "=== fajr-watch SD Card Flasher ==="
echo "Station: $STATION_ID"
echo "Location: $LAT, $LNG (elev ${ELEVATION}m)"
echo "WiFi: $WIFI_SSID"
echo "Device: $DEVICE"
echo ""

# ── Confirm ──

read -p "This will ERASE $DEVICE. Continue? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Aborted."
    exit 0
fi

# ── Flash Pi OS ──

if [ -z "$PI_OS_IMAGE" ]; then
    # Try to find a downloaded image
    PI_OS_IMAGE=$(ls -t ~/Downloads/*raspios*lite*arm64*.img* 2>/dev/null | head -1 || true)
    if [ -z "$PI_OS_IMAGE" ]; then
        echo "Error: No Raspberry Pi OS image found."
        echo "Download from https://www.raspberrypi.com/software/operating-systems/"
        echo "Then pass with --image /path/to/image.img"
        exit 1
    fi
fi

echo "Flashing Pi OS from: $PI_OS_IMAGE"

if [ "$(uname)" = "Darwin" ]; then
    RDISK="${DEVICE/disk/rdisk}"
    diskutil unmountDisk "$DEVICE"

    if [[ "$PI_OS_IMAGE" == *.xz ]]; then
        xz -dc "$PI_OS_IMAGE" | sudo dd of="$RDISK" bs=4m
    else
        sudo dd if="$PI_OS_IMAGE" of="$RDISK" bs=4m
    fi

    sync
    sleep 2

    # Re-mount boot partition
    diskutil mountDisk "$DEVICE"
    BOOT_MOUNT=$(diskutil info "${DEVICE}s1" 2>/dev/null | grep "Mount Point" | awk '{print $3}')
    if [ -z "$BOOT_MOUNT" ]; then
        BOOT_MOUNT="/Volumes/bootfs"
    fi
else
    if [[ "$PI_OS_IMAGE" == *.xz ]]; then
        xz -dc "$PI_OS_IMAGE" | sudo dd of="$DEVICE" bs=4M status=progress
    else
        sudo dd if="$PI_OS_IMAGE" of="$DEVICE" bs=4M status=progress
    fi
    sync
    sleep 2
    # Mount boot partition
    BOOT_MOUNT="/mnt/fajr-boot"
    sudo mkdir -p "$BOOT_MOUNT"
    sudo mount "${DEVICE}1" "$BOOT_MOUNT"
fi

echo "Boot partition mounted at: $BOOT_MOUNT"

# ── Enable SSH ──

touch "$BOOT_MOUNT/ssh"

# ── Configure WiFi (for Pi OS Bookworm, use NetworkManager via firstrun) ──

if [ -n "$WIFI_SSID" ] && [ -n "$WIFI_PASS" ]; then
    # Create a firstrun script that configures WiFi via nmcli
    cat > "$BOOT_MOUNT/firstrun.sh" << FIRSTRUN
#!/bin/bash
set -e
nmcli device wifi connect "$WIFI_SSID" password "$WIFI_PASS" || true
FIRSTRUN
    chmod +x "$BOOT_MOUNT/firstrun.sh"
fi

# ── Copy fajr-watch software ──

FAJR_DIR="$BOOT_MOUNT/fajr-watch"
mkdir -p "$FAJR_DIR"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cp -r "$REPO_ROOT/src" "$FAJR_DIR/src"
cp -r "$REPO_ROOT/config" "$FAJR_DIR/config"
cp "$REPO_ROOT/requirements.txt" "$FAJR_DIR/"
cp "$REPO_ROOT/scripts/provision/first-boot.sh" "$FAJR_DIR/"

# ── Write station config ──

cat > "$FAJR_DIR/station.yaml" << YAML
station:
  id: "$STATION_ID"
  lat: $LAT
  lng: $LNG
  elevation_m: $ELEVATION
  horizon: "$HORIZON"
  environment: "$ENVIRONMENT"
  host: "$HOST_NAME"
  contact: ""

camera:
  type: "$CAMERA_TYPE"
  lens_mm: 4.74
  orientation: "east"
  azimuth_offset: 0

network:
  wifi_ssid: "$WIFI_SSID"
  wifi_password: "$WIFI_PASS"
  upload_url: "https://api.fajr.watch/v1/upload"
  api_key: ""

capture:
  interval_s: 10
  twilight_margin_deg: 5
  raw_format: true
  max_exposure_s: 30
  target_brightness: 80

processing:
  detect_on_device: true
  min_confidence: 0.5
  keep_raw_frames: false
  retention_days: 30
YAML

# ── Create first-boot trigger ──

touch "$FAJR_DIR/first-boot-trigger"

# ── Create first-boot systemd service (runs once) ──

ROOTFS_MOUNT=""
if [ "$(uname)" = "Darwin" ]; then
    # On macOS, we can't easily write to the ext4 rootfs partition.
    # Instead, we'll use a cmdline.txt hook.
    echo "Note: On macOS, first-boot service must be configured after first SSH login."
    echo "Run: sudo bash /boot/fajr-watch/first-boot.sh"
else
    ROOTFS_MOUNT="/mnt/fajr-rootfs"
    sudo mkdir -p "$ROOTFS_MOUNT"
    sudo mount "${DEVICE}2" "$ROOTFS_MOUNT"

    sudo cp "$FAJR_DIR/first-boot.sh" "$ROOTFS_MOUNT/usr/local/bin/fajr-watch-provision.sh"
    sudo chmod +x "$ROOTFS_MOUNT/usr/local/bin/fajr-watch-provision.sh"

    sudo tee "$ROOTFS_MOUNT/etc/systemd/system/fajr-watch-provision.service" > /dev/null << SERVICE
[Unit]
Description=fajr-watch first-boot provisioning
After=network-online.target
Wants=network-online.target
ConditionPathExists=/boot/fajr-watch/first-boot-trigger

[Service]
Type=oneshot
ExecStart=/usr/local/bin/fajr-watch-provision.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE

    sudo ln -sf /etc/systemd/system/fajr-watch-provision.service \
        "$ROOTFS_MOUNT/etc/systemd/system/multi-user.target.wants/fajr-watch-provision.service"

    sudo umount "$ROOTFS_MOUNT"
fi

# ── Cleanup ──

if [ "$(uname)" = "Darwin" ]; then
    diskutil unmountDisk "$DEVICE"
else
    sudo umount "$BOOT_MOUNT"
fi

echo ""
echo "=== SD card ready ==="
echo "Station: $STATION_ID"
echo "Location: $LAT, $LNG"
echo ""
echo "Insert into Pi, connect camera, apply power."
if [ "$(uname)" = "Darwin" ]; then
    echo ""
    echo "NOTE (macOS): After first boot, SSH in and run:"
    echo "  sudo bash /boot/fajr-watch/first-boot.sh"
fi
