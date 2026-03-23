# Bill of Materials

Three build tiers depending on budget and deployment needs.

## Tier 1: Budget Build ($270)

Best for WiFi-accessible sites, pilot testing.

| # | Component | Model | Qty | Unit Cost | Source |
|---|---|---|---|---|---|
| 1 | Computer | Raspberry Pi Zero 2W | 1 | $15 | Adafruit, PiShop |
| 2 | Camera | Raspberry Pi HQ Camera (IMX477) | 1 | $50 | Raspberry Pi official |
| 3 | Lens | 1.8mm C-mount fisheye 180 FOV f/2.0 | 1 | $35 | eBay (generic Chinese) |
| 4 | CS-to-C adapter | CS to C mount ring | 1 | $5 | Amazon |
| 5 | SD card | 32GB Class 10 A2 | 1 | $8 | Amazon |
| 6 | Solar panel | 20W monocrystalline 12V | 1 | $25 | Amazon |
| 7 | Battery | 20Ah 12V LiFePO4 | 1 | $45 | Amazon |
| 8 | Charge controller | 10A PWM with LVD | 1 | $15 | Amazon |
| 9 | Buck converter | 12V to 5V/3A USB-C | 1 | $8 | Amazon |
| 10 | Enclosure | 4" PVC cap + 6" acrylic dome | 1 | $30 | Hardware store + eBay |
| 11 | Desiccant | Silica gel packets (reusable) | 4 | $5 | Amazon |
| 12 | Sealant | Clear silicone (GE Silicone II) | 1 | $8 | Hardware store |
| 13 | Cables | Micro-USB, CSI ribbon 300mm | 1 | $6 | Amazon |
| 14 | Mounting | L-bracket + U-bolts (pole mount) | 1 | $15 | Hardware store |
| | **Total** | | | **~$270** | |

Limitation: Pi Zero 2W has 512MB RAM. On-device detection works but is slower.

## Tier 2: Recommended Build ($465)

Best for most deployments. Balanced performance and cost.

| # | Component | Model | Qty | Unit Cost | Source |
|---|---|---|---|---|---|
| 1 | Computer | Raspberry Pi 4B (2GB RAM) | 1 | $45 | Adafruit, PiShop |
| 2 | Camera | ZWO ASI224MC | 1 | $180 | ZWO direct, eBay |
| 3 | Lens | 1.8mm C-mount fisheye 180 FOV f/2.0 | 1 | $35 | eBay |
| 4 | GPS module | U-blox NEO-6M with antenna | 1 | $10 | Amazon |
| 5 | SD card | 64GB Class 10 A2 | 1 | $10 | Amazon |
| 6 | Solar panel | 30W monocrystalline 12V | 1 | $35 | Amazon |
| 7 | Battery | 30Ah 12V LiFePO4 | 1 | $65 | Amazon |
| 8 | Charge controller | 10A PWM with LVD | 1 | $15 | Amazon |
| 9 | Buck converter | 12V to 5V/5A USB-C (PD) | 1 | $12 | Amazon |
| 10 | Enclosure | 6" PVC cap + 9" acrylic dome | 1 | $45 | Hardware store + eBay |
| 11 | Dew heater | Nichrome wire strip (5W) | 1 | $8 | Amazon |
| 12 | Desiccant | Silica gel packets (reusable) | 6 | $5 | Amazon |
| 13 | Sealant | Clear silicone | 1 | $8 | Hardware store |
| 14 | Cables | USB-C, USB 3.0 (camera), GPS UART | 1 | $12 | Amazon |
| 15 | Mounting | L-bracket + U-bolts (pole mount) | 1 | $15 | Hardware store |
| | **Total** | | | **~$505** | |

The ZWO ASI224MC has 0.8e read noise at Gain 60. It resolves faint sky gradients that are invisible to consumer cameras. 1000-second maximum exposure covers the full twilight range.

## Tier 2b: Recommended + Cellular ($590)

Same as Tier 2 plus cellular connectivity for remote dark-sky sites.

| # | Component | Model | Qty | Unit Cost | Source |
|---|---|---|---|---|---|
| | All items from Tier 2 | | | $505 | |
| 16 | 4G HAT | Waveshare SIM7600G-H (includes GPS) | 1 | $83 | Waveshare |
| 17 | SIM card | Hologram Global IoT SIM | 1 | $3 | Hologram.io |
| | **Total** | | | **~$590** | |

The Waveshare 4G HAT includes built-in GNSS (GPS/BeiDou/GLONASS), so the separate GPS module can be dropped ($10 savings). Monthly data cost: ~$2-5 depending on upload frequency.

## Tier 3: Research Grade ($1,000+)

For primary anchor stations where precision is the top priority.

| # | Component | Model | Qty | Unit Cost | Source |
|---|---|---|---|---|---|
| 1 | Computer | Raspberry Pi 5 (4GB) | 1 | $60 | Raspberry Pi official |
| 2 | Camera | ZWO ASI462MC (IMX462 Starvis 2) | 1 | $270 | ZWO direct |
| 3 | Lens | Fujinon 2.7mm f/1.8 fisheye | 1 | $250 | eBay (used) |
| 4 | 4G + GPS | Waveshare SIM7600G-H | 1 | $83 | Waveshare |
| 5 | SD card | 128GB Class 10 A2 | 1 | $15 | Amazon |
| 6 | Solar panel | 40W monocrystalline 12V | 1 | $45 | Amazon |
| 7 | Battery | 40Ah 12V LiFePO4 | 1 | $80 | Amazon |
| 8 | Charge controller | 20A MPPT | 1 | $35 | Amazon |
| 9 | Buck converter | 12V to 5V/5A USB-C PD | 1 | $12 | Amazon |
| 10 | Enclosure | IP67 rated + 9" UV-stabilized dome | 1 | $100 | Pelican + eBay |
| 11 | Dew heater | 10W nichrome strip with PWM controller | 1 | $15 | Amazon |
| 12 | Desiccant + hygro | Silica gel + BME280 humidity sensor | 1 | $12 | Amazon |
| 13 | Cables + misc | | | $25 | |
| | **Total** | | | **~$1,000** | |

## Bulk Order for 20 Units (Tier 2)

| Item | 20x Unit Cost | 20x Total |
|---|---|---|
| Pi 4B 2GB | $45 | $900 |
| ZWO ASI224MC | $180 | $3,600 |
| Lens + GPS + SD + cables | $67 | $1,340 |
| Solar + battery + controller + buck | $127 | $2,540 |
| Enclosure + dew heater + sealant + mount | $76 | $1,520 |
| **Grand total (20 units)** | | **$9,900** |

At 20 units, you may get volume pricing on the ZWO cameras (contact ZWO directly) and solar panels. Realistic total: $8,000-10,000 for 20 complete stations.

## Recommended Starter Kit

For someone who wants to buy a ready-made kit and just flash an SD card:

**CanaKit Raspberry Pi 4 Starter Kit** ($90-120)
- Includes: Pi 4B 4GB, 32GB SD card, case, power supply, HDMI cable
- You still need: camera, lens, outdoor enclosure, solar power, GPS
- The CanaKit case and power supply are for indoor bench testing only. The outdoor deployment uses the solar power system and weatherproof enclosure.

Then add:
- ZWO ASI224MC ($180)
- 1.8mm fisheye lens ($35)
- U-blox GPS ($10)
- Outdoor power + enclosure (build from Tier 2 BOM)

## Tools Needed for Assembly

- Phillips screwdriver
- Wire strippers
- Soldering iron (for dew heater nichrome wire only)
- Drill with 1/2" bit (for cable pass-through in enclosure)
- Silicone caulk gun
- Multimeter (for verifying solar voltage)
