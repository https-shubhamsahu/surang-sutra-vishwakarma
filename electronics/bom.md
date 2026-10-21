# SURANG-SUTRA Stage 3 prototype BOM (electronics + airframe + cage)

Prepared 22 Oct 2026 for the Vishwakarma Awards Stage 2 deck. Nothing here has been bought or built. INR, GST-inclusive where the store shows it (Robu, Amazon.in, Probots). LCSC prices are converted at Rs 88/USD before shipping and duty.

**Price type:** `L` = listed by the supplier, checked 22 Oct 2026. `LA` = listed price reused from the Ambetronics proposal BOM (13 Sep 2026). `EA` = estimate reused from that BOM. `E` = new planning estimate (not a quote). **OOS** = out of stock when checked.

## Totals

| Block | Rs |
|---|---:|
| SURANG vehicle (airframe, power, avionics, sensors, release, cage) | 1,41,471 |
| SUTRA carrier boards: 7 x Rs 1,735 (5 pucks + Wi-Fi base + LoRa base) | 12,145 |
| Integration (wiring, consumables, charging) | 4,500 |
| **Core subtotal** | **1,58,116** |
| Contingency 15 % | 23,717 |
| **Core total incl. contingency** | **1,81,833** |
| Ambetronics proposal core total (13 Sep 2026, F450 baseline) | 1,48,942 |
| Difference vs the Rs 1.50 lakh core budget | 31,833 |
| Gas package (DFRobot dev fallback), outside core as before | 27,297 |

**Verdict:** the itemised Stage 3 build is **Rs 1,81,833**, i.e. **Rs 31,833 over** the Rs 1.50 lakh core budget. The overrun comes from items the F450 shortlist did not cost: 7 real carrier boards instead of 2 relays, an itemised GFRP cage, a custom carbon frame, the optical-flow sensor and the imported Pi buck. With the cost-downs below the total drops to about **Rs 1,62,946**.

| Cost-down option | Saves Rs |
|---|---:|
| Ra-01H + wire antenna on all 7 boards | 3,696 |
| Ra-01H on the scout too | 410 |
| Skip optical flow (C3) | 4,199 |
| DIY break-beam instead of Adafruit (D7) | 1,391 |
| PETG hubs in-house instead of MJF (E2) | 2,400 |
| One base board for both base roles (6 boards, not 7) | 1,207 |
| Robu Pro-Range 6S 3300 35C (Rs 5,879) instead of Tattu (B1) | 3,121 |
| **Core total incl. contingency after all cost-downs** | **1,62,946** |

## Airframe & propulsion - Rs 28,567

| ID | Item | Part number | Qty | Unit Rs | Total Rs | Type | Vendor | L/I | Lead | Notes |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| A1 | Carbon plate for arms, 3K, 300x200x5 mm | Robu CF sheet 300x200x5 | 1 | 3,889 | 3,889 | L | Robu | Local | 3-5 d | 4 arms 25 mm wide; 295 mm motor-to-motor X |
| A2 | Carbon plate for stack/centre plates, 100x250x2 mm | Robu CF sheet 100x250x2 | 2 | 1,279 | 2,558 | L | Robu | Local | 3-5 d | top, bottom, battery plates |
| A3 | CNC cutting of frame plates | DXF from cad/; IndiaMART CF cutters (Ultrasafe, RGM) | 1 | 2,000 | 2,000 | E | IndiaMART RFQ | Local | 7-10 d | quote on request |
| A4 | Brushless motor 2809 1280KV (6S, 7-inch) | GEPRC SPEEDX2 2809 1280KV | 4 | 3,169 | 12,676 | L | Robu | Local | 3-5 d | in stock; alt. T-Motor Velox V2808 1300KV Rs 3,819 |
| A5 | Props 7x4x3 tri-blade (set 2CW+2CCW) | HQProp 7X4X3 light grey PC | 3 | 375 | 1,125 | L | Robu | Local | 3-5 d | 1 fitted + 2 spare sets |
| A6 | 4-in-1 ESC 6S 65 A | Hobbywing XRotor FPV G2 65A 4in1 | 1 | 6,279 | 6,279 | LA | Robu | Local | OOS | Robu 22 Oct: new version Rs 11,269 (OOS), old Rs 5,499 (OOS) - price risk |
| A7 | Bulk cap at ESC pads 470 uF 50 V low-ESR | Panasonic EEU-FR1H471 | 1 | 40 | 40 | E | Robu / Evelta | Local | 3-5 d |  |

## Battery & power - Rs 21,764

| ID | Item | Part number | Qty | Unit Rs | Total Rs | Type | Vendor | L/I | Lead | Notes |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| B1 | 6S LiPo 3300 mAh 95C, XT90-S, 490 g | Tattu G-Tech TAS33006S95X9 | 1 | 9,000 | 9,000 | EA | Robu / Robocraze RFQ | Local | RFQ | India price/stock unconfirmed |
| B2 | Balance charger 1-6S (ground equipment) | SkyRC S100neo | 1 | 5,169 | 5,169 | LA | Robu | Local | 3-5 d | not flown |
| B3 | Power module, V/I sense, 5.2 V/3 A BEC | Holybro PM02 V3 (2-12S, 60 A cont./100 A burst) | 1 | 2,469 | 2,469 | L | Robu | Local | 3-5 d | replaces Ambetronics item 06 estimate Rs 3,500; re-terminate XT60 leads to XT90/solder |
| B4 | Pi 5 buck 6S -> 5 V 5.5 A | Pololu D36V50F5 (#4091) | 1 | 4,000 | 4,000 | E | Pololu direct ($34.95 + ship/duty) | Imported | 2-3 wk | not stocked in India on 22 Oct |
| B5 | Aux UBEC 2-6S -> 5 V 3 A | ReadytoSky 2-6S 5V/3A + 12V/3A UBEC | 1 | 279 | 279 | L | Robu | Local | 3-5 d | servo, pump, IR, LiDAR, scout |
| B6 | Mini blade fuse holders + 2 A/3 A fuses | Littelfuse 0297002 / 0297003 + inline holders | 1 | 150 | 150 | E | Robu / local | Local | 3-5 d | F1, F2 |
| B7 | TVS 28 V standoff, SMB | SMBJ28A | 5 | 8 | 40 | E | LCSC / Robu | Local | 3-5 d | D1, D2 + spares |
| B8 | XT90 male + female pair | Amass XT90H | 1 | 149 | 149 | L | Robu | Local | 3-5 d | vehicle-side receptacle |
| B9 | 12 AWG silicone wire, 1 m | ultra-flexible 12AWG (red + black) | 2 | 179 | 358 | L | Robu | Local | 3-5 d |  |
| B10 | USB-C power pigtail for Pi 5 (5 V only, 20 AWG) | USB-C male DIY pigtail | 1 | 150 | 150 | E | Robu / local | Local | 3-5 d | set usb_max_current_enable=1 |

## Avionics & companion - Rs 56,722

| ID | Item | Part number | Qty | Unit Rs | Total Rs | Type | Vendor | L/I | Lead | Notes |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| C1 | Flight controller | Holybro Pixhawk 6C Mini | 1 | 28,269 | 28,269 | LA | Robu | Local | OOS | still Rs 28,269 and OOS on 22 Oct |
| C2 | RC transmitter + receiver (iBUS) | FlySky FS-i6 + FS-iA6B | 1 | 5,729 | 5,729 | LA | Robu | Local | 3-5 d |  |
| C3 | Optical flow + ToF for GPS-free hold (NEW, recommended) | MicoAir MTF-01 | 1 | 4,199 | 4,199 | L | Probots | Local | OOS | alt. Matek 3901-L0X Rs 6,999 (OOS) |
| C4 | Companion computer | Raspberry Pi 5 Model B 8GB | 1 | 16,825 | 16,825 | LA | Silverline Electronics | Local | 3-5 d |  |
| C5 | Pi active cooler + 64 GB endurance microSD | Raspberry Pi Active Cooler + SanDisk High Endurance 64GB | 1 | 1,700 | 1,700 | EA | Silverline / Robu | Local | 3-5 d |  |

## Sensors, payload & release - Rs 23,539

| ID | Item | Part number | Qty | Unit Rs | Total Rs | Type | Vendor | L/I | Lead | Notes |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| D1 | 2D LiDAR kit | LDROBOT STL-19P / D500 kit | 1 | 8,499 | 8,499 | LA | Robu | Local | 3-5 d | UART to Pi GPIO5 |
| D2 | Low-light camera 2MP IR-CUT + 22-15 pin cable | Waveshare IMX327 2MP IR-CUT Camera (A) | 1 | 4,459 | 4,459 | LA | Robu | Local | 3-5 d |  |
| D3 | Thermal array 32x24, 110 deg | 7Semi MLX90640 110deg breakout | 1 | 4,711 | 4,711 | LA | Robocraze | Local | 3-5 d | I2C 0x33 |
| D4 | 850 nm illumination + MOSFET driver | 4 x 1 W 850 nm star LEDs, 2 x AO3400A, 2512 4.7R, gate R | 1 | 1,000 | 1,000 | EA | Robu / Robocraze | Local | 3-5 d | AO3400A Rs 6 L; 850 nm 3 W chips Rs 2,799/10 on Amazon |
| D5 | Sample pump, 370 micro diaphragm 6 V | 370 micro DC air pump 6V | 1 | 359 | 359 | L | Robu | Local | 3-5 d | run at 5 V via PWM |
| D6 | Flow cell, inlet tube, PTFE filter, fittings | printed cell + silicone tube + 0.45 um PTFE disc | 1 | 400 | 400 | E | Local | Local | 7 d | gas sensors themselves are outside core |
| D7 | IR break-beam pair, 3 mm | Adafruit 2167 | 1 | 1,491 | 1,491 | L | Amazon.in | Imported | 1-2 wk | DIY IR LED + phototransistor ~Rs 100 fallback |
| D8 | Micro servo, metal gear (escapement) | MG90S | 2 | 269 | 538 | L | Robu | Local | 3-5 d | 1 + spare |
| D9 | Neodymium magnets 6x3 mm (60 pcs) | N35+ disc 6x3 | 1 | 299 | 299 | L | Amazon.in | Local | 3-5 d | cassette hall-hold, one per puck slot |
| D10 | Scout radio node (Wi-Fi/ESP-NOW-LR, FTM) | Seeed XIAO ESP32C3 (U.FL antenna incl.) | 1 | 749 | 749 | L | ThinkRobotics | Local | 2-4 wk | pre-order; Robu OOS |
| D11 | Scout LoRa module 868 MHz | HopeRF RFM95W-868S2 | 1 | 819 | 819 | L | Robu | Local | OOS | in-stock alt: LionCircuits Rs 2,423+ |
| D12 | 868 MHz antenna + IPEX-SMA pigtail | IPEX1-RP-SMA 15 cm + 865-868 MHz whip | 1 | 215 | 215 | E | Robu | Local | 3-5 d | check SMA vs RP-SMA |

## Cage & mechanical - Rs 10,879

| ID | Item | Part number | Qty | Unit Rs | Total Rs | Type | Vendor | L/I | Lead | Notes |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| E1 | 3 mm pultruded GFRP rod, 1 m | GFRP 3 mm solid rod | 25 | 120 | 3,000 | E | IndiaMART pultrusion RFQ | Local | 1-2 wk | 120 struts = 20.3 m; 5 struts per rod; fallback Amazon 420 mm 10-pack Rs 1,776 |
| E2 | Cage hubs 18 x 12 mm, PA12 MJF | 42 + 6 spare, from cad/ | 48 | 60 | 2,880 | E | JLC3DP / local MJF bureau | Imported | 10-15 d | PETG in-house fallback ~Rs 10 each |
| E3 | TPU 95A filament 500 g | TPU 95A 1.75 mm | 1 | 1,200 | 1,200 | E | Robu / Amazon.in | Local | 3-5 d | hub caps, puck bumpers |
| E4 | PETG filament 1 kg | PETG 1.75 mm | 1 | 1,100 | 1,100 | E | Robu / Amazon.in | Local | 3-5 d | cassette, mounts, puck shells |
| E5 | Bearing 6800-2RS 10x19x5 (10-pack) | 6800-2RS | 1 | 660 | 660 | L | Amazon.in (XERFU) | Local | 3-5 d | 2 fitted + spares |
| E6 | Carbon tube 10 OD x 8 ID x 1000 mm (pack of 2) | Robu CF tube twill 10x8x1000 | 1 | 1,239 | 1,239 | L | Robu | Local | OOS | axle ~580 mm; 500 mm tube Rs 349 too short |
| E7 | Epoxy, CA, heat-set inserts, M2/M3 fasteners for cage | misc | 1 | 800 | 800 | E | local | Local | 3 d |  |

## Integration - Rs 4,500

| ID | Item | Part number | Qty | Unit Rs | Total Rs | Type | Vendor | L/I | Lead | Notes |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| G1 | Mounts, fasteners, signal wiring, JST-GH/Dupont, strain relief | Ambetronics item 21 | 1 | 2,500 | 2,500 | EA | Robu / local | Local | 3-5 d |  |
| G2 | Bench consumables + charging accessories (LiPo bag, checker) | Ambetronics item 22 | 1 | 1,500 | 1,500 | EA | Robu / Robocraze | Local | 3-5 d |  |
| G3 | Puck charging: 5-port USB charger + USB-C cables | generic | 1 | 500 | 500 | E | Amazon.in | Local | 3 d | or cassette pogo pads |

## SUTRA carrier board - per-puck cost (target Rs 900)

| ID | Item | Part number | Qty | Rs | Type | Vendor | L/I | Notes |
|---|---|---|---:|---:|---|---|---|---|
| P1 | Wi-Fi MCU module | ESP32-C3-MINI-1 (-N4; Robu lists -H4) | 1 | 249 | L | Robu | Local |  |
| P2 | LoRa module 868 MHz (SX1276) | HopeRF RFM95W-868S2 | 1 | 819 | L | Robu | Local | OOS 22 Oct; LionCircuits Rs 2,423+ in stock |
| P3 | 1S LiPo 400 mAh, JST-PH | 502030/502035 class | 1 | 200 | E | Amazon.in / Robu | Local | KP 602035 Rs 299 L; WLY502040 Rs 135 (OOS) |
| P4 | Li-ion charger | MCP73831T-2ACI/OT | 1 | 62 | L | LCSC C424093 | Imported | Robu Rs 130 (OOS) |
| P5 | 3.3 V LDO 600 mA | AP2112K-3.3TRG1 | 1 | 17 | L | Robu / LCSC C51118 | Local |  |
| P6 | Hall wake switch | DRV5032FBDBZR | 1 | 16 | L | LCSC (FA C140921 price) | Imported |  |
| P7 | USB ESD array | USBLC6-2SC6 | 1 | 15 | E | LCSC | Imported |  |
| P8 | USB-C receptacle 16P | HRO TYPE-C-31-M-12 | 1 | 26 | L | Robu | Local |  |
| P9 | Battery connector JST-PH 2p SMD | S2B-PH-SM4-TB | 1 | 10 | E | LCSC / Robu | Local |  |
| P10 | U.FL receptacle | Hirose U.FL-R-SMT-1 | 1 | 22 | L | Robu | Local |  |
| P11 | 868 MHz antenna (U.FL FPC, flexible) | generic 868 MHz FPC U.FL | 1 | 120 | E | Robu / LCSC | Local | or 82 mm wire on J4: Rs 2 |
| P12 | Passives 0603/0805 (12 R, 11 C) | per schematic | 1 | 30 | E | LCSC / Robu | Local |  |
| P13 | LEDs 0603 x2 + KMR2 buttons x2 | per schematic | 1 | 24 | E | Robu | Local |  |
| P14 | PCB 2-layer ~50 mm, qty 10 incl. shipping | JLCPCB | 1 | 70 | E | JLCPCB | Imported | ~Rs 700 per 10 boards incl. economy freight |
| P15 | Shell: PETG body + TPU bumper print | ~12 g PETG + 5 g TPU | 1 | 40 | E | in-house | Local |  |
| P16 | AprilTag 36h11 30 mm label + solder/flux |  | 1 | 15 | E | local | Local |  |
| | **Per puck (as drawn, RFM95W)** | | | **1,735** | | | | |
| | Per puck, cost-down (Ra-01H + wire whip) | | | 1,207 | | | | |

**Honest answer: the puck does not meet Rs 900.** As drawn it is Rs 1,735 (Rs 835 over); the RFM95W alone is Rs 819 (47 % of the puck). Swapping to an Ai-Thinker Ra-01H (same SX1276, different 16-pad footprint) and a wire whip gives Rs 1,207, still over. Rs 900 is only realistic at volume (100+ boards: LCSC module pricing, panelised PCB, bulk cells). Recommended baseline change: puck BOM target Rs 900 -> **Rs 1,250 for the Stage 3 prototype** (Ra-01H variant), Rs 900 kept as the volume target.

Ten PCBs are fabricated; seven are assembled (7 x per-puck cost above). The two base-station boards are identical carrier boards on the laptop USB, so the base ESP32-C3 node and base LoRa node need no separate parts.

## Gas package (outside core, as in the Ambetronics proposal)

| ID | Item | Part | Qty | Rs | Type | Vendor | Stock |
|---|---|---|---:|---:|---|---|---|
| X1 | O2 electrochemical, I2C | DFRobot SEN0465 | 1 | 10,499 | L | Robu | 3-5 d |
| X2 | CO electrochemical, I2C | DFRobot SEN0466 | 1 | 7,979 | L | Robu | 3-5 d |
| X3 | H2S electrochemical, I2C | DFRobot SEN0467 | 1 | 8,819 | L | Robu | OOS |

Ambetronics OEM electrochemical O2/CO/H2S + CH4 NDIR remains a separate quote / in-kind request.

## What changed from the Ambetronics (13 Sep 2026) BOM

| Old line | Item | Old Rs | Now |
|---|---|---:|---|
| Ambetronics 01 | F450 bare frame | 849 | replaced by custom 7-inch 295 mm carbon X (A1-A3) |
| Ambetronics 02 | XRotor 3115 900KV motors x4 | 12,000 | replaced by 2809 1280KV (A4) |
| Ambetronics 04 | HQ 9x4x3 props | 1,600 | replaced by 7x4x3 (A5) |
| Ambetronics 06 | Power module + harness (E) | 3,500 | now PM02 V3 L + itemised harness (B3, B6-B10) |
| Ambetronics 10 | SiK 433 MHz telemetry pair | 4,139 | dropped: MAVLink rides Pi Wi-Fi / ESP-NOW + LoRa lifeline |
| Ambetronics 13 | Pi + accessory converters (E) | 3,000 | now D36V50F5 + UBEC + fuses/TVS (B4-B7) |
| Ambetronics 18 | 3 mm carbon rods | 1,287 | baseline uses 3 mm GFRP (E1) |
| Ambetronics 19 | Cage race + release mechanism (E) | 5,000 | itemised: E2-E7, D8, D9 |
| Ambetronics 20 | SUTRA development (2 relays, E) | 2,500 | now 7 custom carrier boards (section F) |

Unchanged and reused at the 13 Sep price: ESC (A6), battery (B1), charger (B2), Pixhawk 6C Mini (C1), FS-i6 (C2), Pi 5 (C4), cooler/SD (C5), STL-19P (D1), IMX327 (D2), MLX90640 (D3), lighting (D4), wiring/consumables (G1, G2).

## Supply risks (22 Oct 2026)

- Out of stock: Pixhawk 6C Mini, XRotor G2 4-in-1 (the new version now lists at Rs 11,269, +Rs 4,990 vs the reused price), RFM95W bare module, MTF-01, CF tube 1 m, XIAO ESP32C3 (pre-order).
- Not stocked in India: Pololu D36V50F5 (import), 850 nm star LEDs, 1 m GFRP rod (RFQ), exact 502030 JST-PH cell.
- Fallbacks: Matek H743-SLIM V3 for the FC (baseline fallback); T-Motor F55A Pro-class 4-in-1; LionCircuits RFM95W at Rs 2,423+; Ra-01H via LCSC.
