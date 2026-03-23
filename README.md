# fajr-watch

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A turnkey Raspberry Pi appliance that observes dawn and dusk, measures the exact solar depression angle at the moment of true Fajr and Isha, and uploads the data for prayer time calibration research.

Flash an SD card, connect a camera, plug in power. The station runs unattended, captures the twilight horizon every 10 seconds, detects when dawn begins and dusk ends using multi-channel brightness analysis, computes the solar depression angle at that moment, and uploads the result.

## Why

Every Islamic prayer time algorithm uses a fixed depression angle (15, 18, or 20 degrees depending on convention). Nobody has measured whether those numbers are actually correct across different latitudes, seasons, and atmospheric conditions. This project collects that data.

The output feeds [pray-calc-ml](https://github.com/acamarata/pray-calc-ml), which trains the Dynamic Prayer Calculation algorithm used by [pray-calc](https://github.com/acamarata/pray-calc).

## Hardware

| Component | Model | Cost |
|---|---|---|
| Computer | Raspberry Pi 4B (2GB+) | $45 |
| Camera | ZWO ASI224MC (or Pi HQ Camera) | $50-180 |
| Lens | 1.8mm C-mount fisheye 180 FOV | $35 |
| Power | 30W solar + 30Ah LiFePO4 + controller | $120 |
| Enclosure | PVC housing + 9" acrylic dome | $60 |
| GPS | U-blox NEO-6M (for precise timestamps) | $10 |

Total: ~$320-465 per station. Full bill of materials and assembly guide in [docs/hardware](https://github.com/acamarata/fajr-watch/wiki/Hardware).

## Quick Start

### 1. Flash the SD card

Download the latest fajr-watch image from [Releases](https://github.com/acamarata/fajr-watch/releases), or build your own:

```bash
# On any Linux/macOS machine
git clone https://github.com/acamarata/fajr-watch.git
cd fajr-watch
./scripts/provision/build-image.sh
```

Flash the resulting `.img` to a 32GB+ SD card using [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or `dd`.

### 2. Configure your station

Before first boot, edit `config/station.yaml` on the SD card's boot partition:

```yaml
station:
  id: "conneaut-oh-01"
  lat: 41.95
  lng: -80.55
  elevation_m: 175
  horizon: "lake"        # lake, ocean, flat, hills, mountain
  environment: "suburban" # dark, rural, suburban, urban
  host: "Aric Camarata"
  contact: "email@example.com"

camera:
  type: "zwo_asi224"     # zwo_asi224, zwo_asi462, pi_hq, pi_cam3
  lens_mm: 1.8
  orientation: "east"    # east, west, allsky

network:
  wifi_ssid: "YourNetwork"
  wifi_password: "YourPassword"
  upload_url: "https://api.fajr.watch/upload"

capture:
  interval_s: 10         # seconds between frames during twilight
  twilight_margin_deg: 5 # start capturing at sun depression + this margin
  raw_format: true       # capture RAW (recommended) or JPEG
```

### 3. Boot and forget

Insert the SD card, connect the camera, apply power. The station:

1. Connects to WiFi
2. Syncs time via GPS (or NTP fallback)
3. Computes tonight's twilight windows from its coordinates
4. Sleeps until the twilight window begins
5. Captures frames every 10 seconds during the window
6. Runs the detection algorithm on the captured sequence
7. Uploads the result: `(date, lat, lng, elevation, depression_angle, confidence, metadata)`
8. Sleeps until the next twilight window

Status LED blinks green when healthy, amber when capturing, red on error.

## How Detection Works

The station does not use a fixed brightness threshold. It detects the physical signature of Fajr Sadiq (true dawn):

1. **Horizon ROI extraction.** Isolates the eastern horizon band (azimuth centered on true east, elevation -2 to +15 degrees).

2. **Multi-channel tracking.** Measures R, G, B brightness separately in the horizon ROI every 10 seconds.

3. **Color ratio analysis.** Computes the color index `(R-B)/(R+B)` over time. Before dawn, scattered zodiacal light is warm (positive ratio). True dawn produces a neutral white band (ratio approaches zero).

4. **Temporal derivative.** The rate of brightness change `dB/dt` in the east ROI peaks at a specific moment during the twilight transition. The inflection point marks the onset of sustained brightening.

5. **Solar depression lookup.** At the detected moment, computes the exact solar depression angle using PyEphem with the station's GPS coordinates and UTC timestamp.

6. **Confidence scoring.** Rejects nights with clouds (detected via spatial variance in the ROI), moon interference, or insufficient data.

The same process runs in reverse for Isha (western horizon, brightness decreasing, white glow disappearing).

## Output Format

Each twilight event produces one record:

```json
{
  "station_id": "conneaut-oh-01",
  "date": "2026-06-21",
  "prayer": "fajr",
  "utc_time": "2026-06-21T09:12:34Z",
  "solar_depression_deg": 14.23,
  "confidence": 0.92,
  "lat": 41.95,
  "lng": -80.55,
  "elevation_m": 175,
  "environment": "suburban",
  "horizon": "lake",
  "camera": "zwo_asi224",
  "sky_quality_mpsas": 19.4,
  "moon_alt_deg": -12.3,
  "cloud_score": 0.08,
  "color_index_at_detection": 0.02,
  "brightness_curve_hash": "sha256:..."
}
```

## Project Structure

```
fajr-watch/
├── src/
│   ├── capture/         # Camera control, frame acquisition
│   ├── detect/          # Dawn/dusk detection algorithm
│   ├── upload/          # Data upload to pray-calc-ml
│   └── calibrate/       # Flat-field, dark frame, photometric calibration
├── config/
│   └── station.example.yaml
├── scripts/
│   └── provision/       # OS image build, first-boot setup
├── .github/
│   ├── docs/
│   │   ├── hardware/    # BOM, assembly, wiring diagrams
│   │   └── hosting/     # Volunteer host guide, site selection
│   └── workflows/       # CI
├── .gitignore
├── README.md
└── LICENSE
```

## Contributing Data

Want to host a station? We provide the hardware (camera + Pi + enclosure + solar panel) and you provide a mounting location with a clear eastern or western horizon. Dark sky sites are ideal, but suburban and urban sites are also valuable for measuring the light pollution offset.

See the [Host Guide](https://github.com/acamarata/fajr-watch/wiki/Host-Guide) for requirements and how to sign up.

## Related Projects

- [pray-calc](https://github.com/acamarata/pray-calc) - Islamic prayer time calculator (npm)
- [pray-calc-ml](https://github.com/acamarata/pray-calc-ml) - ML dataset for prayer angle calibration
- [nrel-spa](https://github.com/acamarata/nrel-spa) - Solar position algorithm
- [moon-sighting](https://github.com/acamarata/moon-sighting) - Lunar crescent visibility

## License

MIT
