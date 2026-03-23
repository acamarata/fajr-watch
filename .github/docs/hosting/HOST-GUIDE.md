# Volunteer Host Guide

Thank you for helping calibrate Islamic prayer times with real observations. This guide covers everything you need to host a fajr-watch station.

## What You Receive

A complete, pre-configured package:

1. Raspberry Pi 4B computer (pre-flashed SD card)
2. ZWO ASI224MC astronomical camera with fisheye lens
3. Weatherproof dome enclosure (assembled)
4. Solar panel + battery pack + cables
5. Pole mounting bracket
6. This guide

Everything is plug-and-play. You provide a mounting location and WiFi.

## What You Need

### Required

- **A clear view of the eastern horizon** (for Fajr/dawn detection). The camera needs to see the sky from roughly 0 to 30 degrees elevation in the east. Trees, buildings, or hills that block the low eastern sky will reduce data quality.
- **WiFi within range** (or you can run an ethernet cable). The station uploads small data files (a few KB per night). If you have no WiFi at the mounting location, let us know and we can provide a cellular-equipped unit.
- **A mounting point** at least 2 meters (6 feet) above ground level. A fence post, roof edge, deck railing, or pole works. The station comes with a universal bracket.

### Nice to Have (Not Required)

- A clear western horizon too (for Isha/dusk detection). If you only have one clear direction, that's fine. One-direction data is still valuable.
- A dark sky. Urban and suburban sites produce useful data too. The light pollution offset is itself a measurement we need.
- A flat horizon (ocean, lake, prairie). Horizon obstructions below ~3 degrees elevation are common and acceptable.

## Site Selection

### Best Locations

1. **Rooftop with open eastern sky.** Flat commercial roofs are ideal. Residential roofs work if you have a safe, permanent mounting point.
2. **Lake or ocean shoreline.** Water gives the flattest possible horizon. Conneaut OH on Lake Erie, Florida coasts, etc.
3. **Open field or farmland.** Rural properties with no eastern obstructions.
4. **Mosque rooftop or minaret.** Many mosques have flat roofs with clear sky views. The imam may be interested in supporting prayer time research.
5. **Backyard on a tall pole.** A 10-foot pole (fence post, antenna mast) in the yard clears most fences and shrubs.

### Avoid

- Under tree canopy or heavy vegetation
- Inside a building (windows block UV and distort brightness)
- Next to bright security lights or street lamps that face the camera
- Locations with frequent vibration (on top of HVAC units, etc.)

## Installation (10 minutes)

### Step 1: Mount the enclosure

Attach the mounting bracket to your chosen location using the included hardware. The dome should face UP (skyward). The cable exits from the bottom.

The camera inside is pre-aimed. For an all-sky (fisheye) setup, orientation does not matter as long as the dome faces straight up. For a horizon-pointed setup, aim the cable exit toward the south (so the camera looks north-east).

### Step 2: Connect the solar panel

Place the solar panel where it gets direct sunlight for at least 4-5 hours per day. South-facing is ideal in the Northern Hemisphere. Connect the panel to the charge controller (pre-wired in the battery box). Connect the battery box to the enclosure via the USB-C cable.

If you have outdoor AC power nearby, you can skip the solar panel entirely and plug the Pi into a weatherproof USB-C adapter.

### Step 3: Configure WiFi

Before powering on, insert the SD card into a computer and edit the file `fajr-watch/station.yaml` on the boot partition:

```yaml
network:
  wifi_ssid: "YourNetworkName"
  wifi_password: "YourPassword"
```

Save and eject. Insert the SD card into the Pi.

Your station ID, coordinates, and camera settings are pre-configured.

### Step 4: Power on

Connect power. The status LED will:
- Blink rapidly (booting, ~30 seconds)
- Solid green (connected and healthy)
- Blink amber (capturing twilight frames)
- Solid red (error, see troubleshooting)

That's it. The station runs itself from here.

## What Happens Each Night

1. **Evening:** Station wakes up ~30 minutes before sunset. Captures one frame every 10 seconds through dusk until full darkness. Detects the moment Shafaq al-Abyad (white twilight glow) disappears. Records the solar depression angle.

2. **Night:** Station sleeps (conserves power).

3. **Morning:** Station wakes up ~2 hours before sunrise. Captures frames through dawn. Detects the moment of Fajr Sadiq (first visible white light on the eastern horizon). Records the solar depression angle.

4. **Upload:** Once per hour, the station uploads its results to our central server. Each result is ~2 KB. A month of data uses less than 1 MB of bandwidth.

## Data and Privacy

- The station does NOT capture identifiable images of people or property. The camera points at the sky.
- Raw sky images are processed on-device and deleted. Only numerical brightness measurements and computed angles are uploaded.
- Your name and location are used only for data attribution and station health monitoring. They are not shared publicly without your consent.
- You can opt out at any time. Unplug the station and mail it back (we cover return shipping).

## Troubleshooting

**Status LED is red:**
- Check that the SD card is fully inserted
- Check that the USB-C power cable is connected
- Try unplugging and re-plugging power (30-second wait between)
- If the LED stays red after 3 reboots, contact us

**No data uploading (check at fajr.watch/stations):**
- Verify WiFi credentials in station.yaml
- Move the station closer to the WiFi router
- Check that your router allows new devices

**Camera not detected:**
- Ensure the USB cable (ZWO) or ribbon cable (Pi camera) is firmly seated
- Try a different USB port on the Pi

**Solar panel not charging:**
- Panel must face the sun with no shadows
- Check charge controller LED (should show charging during daylight)
- In winter at high latitudes, you may need AC power backup

## Contact

Questions, problems, or want to adjust your station setup:

- Email: fajr-watch@acamarata.com
- GitHub: https://github.com/acamarata/fajr-watch/issues
