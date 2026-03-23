# Shippable Kit Design

Goal: 20 identical kits you can assemble, flash, box, and mail. Volunteer opens the box, mounts it pointing east, plugs in power, done.

## Design Principles

1. **Ships in a USPS Medium Flat Rate Box** ($17.10, 11" x 8.5" x 5.5"). No oversized packages.
2. **No pole included.** Volunteers mount it on whatever they have: fence post, deck railing, wall bracket, window sill, tripod. Include zip ties and a universal L-bracket.
3. **No soldering.** All connections are plug-and-play USB cables.
4. **Two power options:** outdoor AC outlet (included 15ft USB-C cable + wall adapter) or solar panel (optional add-on, ships separately if needed).
5. **WiFi pre-configured.** Ask the volunteer for their SSID and password before shipping. Pre-flash it on the SD card. Zero on-site configuration.
6. **One cable to plug in.** Power. That's it. Camera is internal, WiFi is pre-set, GPS is built in.

## The Kit

### What's Inside the Box

| # | Item | Cost | Notes |
|---|---|---|---|
| 1 | Raspberry Pi 4B 2GB | $45 | Pre-flashed SD card inside |
| 2 | Raspberry Pi Camera Module 3 Wide NoIR | $35 | 120 FOV, no IR filter (better low-light), fixed lens (no alignment needed) |
| 3 | Weatherproof junction box (IP65) | $12 | Hammond 1554K or similar, 6.3" x 3.5" x 2.1" polycarbonate. Camera lens hole pre-drilled. |
| 4 | GPS module (U-blox NEO-6M) | $10 | Glued inside the box, antenna on outside |
| 5 | 64GB SD card (pre-flashed) | $10 | Station config pre-loaded |
| 6 | 15ft outdoor USB-C extension cable | $12 | Weatherproof, runs to nearest outlet |
| 7 | 5V/3A USB-C wall adapter | $8 | Standard phone charger |
| 8 | USB-C right-angle adapter | $3 | For clean cable entry into box |
| 9 | Weatherproof cable gland (PG9) | $2 | Seals the power cable entry hole |
| 10 | Silica gel packets (4x) | $2 | Moisture control inside box |
| 11 | Mounting kit: L-bracket + 4 zip ties + 2 screws | $5 | Universal mount |
| 12 | Quick-start card (laminated) | $2 | 5 steps with pictures |
| **Total per kit** | | **~$146** | |
| **20 kits** | | **~$2,920** | |
| **Shipping (20x USPS Medium Flat Rate)** | | **$342** | |
| **Grand total** | | **~$3,262** | |

### Optional Solar Add-On ($80, ships separately)

For volunteers with no outdoor outlet:
- 20W folding solar panel ($25)
- 10Ah USB power bank with pass-through charging ($35)
- 6ft USB-C cable ($5)
- Velcro strips for panel mounting ($3)
- Ships in a separate flat mailer ($12 shipping)

## Why Pi Camera Module 3 Wide NoIR (Not ZWO)

For a shippable kit, the Pi Camera Module 3 Wide wins over ZWO:

| Factor | Pi Cam 3 Wide NoIR | ZWO ASI224MC |
|---|---|---|
| Cost | $35 | $180 |
| Setup | Ribbon cable, zero config | USB, SDK install, gain tuning |
| Lens | Built-in 120 FOV (no alignment) | Separate lens (must focus + align) |
| Low-light | Good (IMX708, 1.4um pixels) | Excellent (IMX224, 3.75um, 0.8e noise) |
| Size | Tiny (25mm x 24mm) | Larger, needs USB port |
| Power | ~0.25W via ribbon | ~1.75W via USB |
| Fragility | Ribbon cable (delicate but enclosed) | USB cable (robust) |

The ZWO is scientifically better. But for 20 mail-out kits where the volunteer never touches the camera, the Pi Cam 3 Wide is simpler, cheaper, and good enough. The 120 FOV wide-angle captures the full eastern horizon band without a separate fisheye lens.

We can always deploy ZWO units at the highest-priority dark-sky sites (your own stations, Cherry Springs, etc.) where you control the setup.

## Assembly (Your Side, Per Kit)

Time: ~15 minutes per unit once you have the process down. 20 units in an afternoon.

### 1. Prepare the junction box

- Drill a 12mm hole on one short end (camera lens)
- Drill a 16mm hole on the bottom (PG9 cable gland for power)
- Drill a 6mm hole on top (GPS antenna cable)

### 2. Install components

- Mount Pi 4B inside box using brass standoffs (pre-tapped holes in the junction box)
- Connect Pi Camera Module 3 via 150mm ribbon cable
- Position camera lens against the drilled hole, secure with hot glue
- Connect GPS module to Pi UART pins (4 wires: VCC, GND, TX, RX)
- Route GPS antenna wire through top hole, seal with silicone
- Install PG9 cable gland in bottom hole
- Place 4 silica gel packets inside
- Close and seal the box

### 3. Flash the SD card

```bash
# On your Mac, for each station:
./scripts/provision/flash-kit.sh \
  --station-id "station-017" \
  --lat 41.95 \
  --lng -80.55 \
  --elevation 175 \
  --wifi-ssid "VolunteerWiFi" \
  --wifi-pass "password123" \
  --host-name "Ahmed in Conneaut" \
  --environment suburban \
  --horizon lake
```

This writes Pi OS + fajr-watch software + station.yaml to the SD card in one command.

### 4. Test

- Insert SD card, connect power, wait 2 minutes
- LED should go green (connected)
- Check the web dashboard at fajr.watch/stations to see the unit reporting
- Capture a test frame to verify the camera works
- Power off, pack it up

### 5. Pack and ship

Contents of the USPS Medium Flat Rate Box:
- Junction box with electronics (wrapped in bubble wrap)
- USB-C wall adapter in a small bag
- 15ft USB-C cable (coiled)
- Mounting bracket + zip ties in a bag
- Laminated quick-start card on top

## Quick-Start Card (What the Volunteer Sees)

```
FAJR-WATCH STATION — Quick Setup

1. MOUNT the box pointing EAST (toward sunrise)
   Use the bracket, zip ties, or set it on a flat surface.
   The camera lens (small hole on the side) must face east
   with a clear view of the sky above the horizon.

2. PLUG the long USB cable into the box (bottom).
   Run the other end to the nearest outdoor outlet.
   Plug in the wall adapter.

3. WAIT 2 minutes. The green light means it's working.

4. DONE. The station runs itself. It observes dawn and dusk
   each day and uploads the data over your WiFi.

Questions? Text/email: fajr-watch@acamarata.com
Your station ID: _______________
```

## Volunteer Onboarding Flow

1. Volunteer signs up (Google Form or website)
2. They provide: name, email, address, WiFi SSID + password, description of their horizon (photo preferred)
3. You evaluate the site (is the eastern horizon clear enough?)
4. You assign a station ID, flash the SD card with their config
5. Assemble, test, pack, ship
6. They receive it, follow the 3-step card, done
7. You see their station appear on the dashboard within 24 hours
