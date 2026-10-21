# Power budget - SURANG rails and SUTRA puck energy

Design-stage calculation, 22 Oct 2026. Nothing is measured yet. Datasheet values are cited; `E` marks an engineering estimate.

## SURANG rail summary

| Rail | Capacity | Typical load | Peak load | Peak / capacity | Margin at peak |
|---|---|---:|---:|---:|---:|
| 6S main bus (PM02 V3) (22.2 V nom (18.0-25.2)) | 60 A cont. / 100 A burst | 25.00 A | 80.00 A | 80 % | 20 % |
| +5V1_PI (Pololu D36V50F5) (5.0 V) | 5.5 A typ; derated 5.0 A at 25 V in | 0.84 A | 2.25 A | 45 % | 55 % |
| +5V_AUX (UBEC 5 V 3 A) (5.0 V) | 3.0 A | 1.48 A | 2.57 A | 86 % | 14 % |
| FC 5.2 V (PM02 BEC) (5.2 V) | 3.0 A | 0.36 A | 0.45 A | 15 % | 85 % |
| Pi 3V3 header (sensors) (3.3 V) | 0.3 A planning budget (no official Pi 5 per-pin figure) | 0.04 A | 0.04 A | 15 % | 85 % |
| Puck 3V3 (AP2112K-3.3) (3.3 V) | 600 mA | 0.10 A | 0.44 A | 73 % | 27 % |

The 6S row compares hover (typical) with the 60 A continuous rating and the 80 A capped burst with the 100 A burst rating.

### 6S main bus (PM02 V3)

| Load | Typical A | Peak A | Basis |
|---|---:|---:|---|
| Propulsion: hover 2.4 kg @ ~4.5 gf/W (typ) / capped climb (peak) | 24.000 | 78.900 | hover calc: 2400 gf / 4.5 gf/W = 533 W / 22.2 V; peak = MOT_BAT_CURR_MAX 80 A total |
| Avionics via buck + UBEC + PM BEC | 1.000 | 1.100 | sum of 5 V rails below / 0.9 eff / 22.2 V |
| **Total** | **25.00** | **80.00** | capacity 60 A cont. / 100 A burst |

Unconstrained full throttle is ~120 A (4 x ~30 A, 2808-class at 6S/7", E) - above the PM02 burst rating, so the 80 A cap is a design rule.

### +5V1_PI (Pololu D36V50F5)

| Load | Typical A | Peak A | Basis |
|---|---:|---:|---|
| Raspberry Pi 5 8GB (idle 3.3 W / stress 9.8 W) | 0.660 | 1.960 | J. Geerling measurements |
| Active cooler fan | 0.050 | 0.100 | E |
| IMX327 camera on CSI | 0.100 | 0.150 | E - not published by Waveshare |
| Sensors on Pi 3V3 (reflected) | 0.030 | 0.040 | see Pi 3V3 rail |
| USB peripherals | 0.000 | 0.000 | none planned (LiDAR on UART) |
| **Total** | **0.84** | **2.25** | capacity 5.5 A typ; derated 5.0 A at 25 V in |

Pi 5 asks for a 5 V / 5 A supply; the 5 A figure includes 1.6 A of USB budget we do not use. Real peak ~2.3 A leaves 54 % headroom.

### +5V_AUX (UBEC 5 V 3 A)

| Load | Typical A | Peak A | Basis |
|---|---:|---:|---|
| 850 nm IR, 2 strings x 0.37 A | 0.740 | 0.740 | calc: (5.0 - 2 x 1.6 V) / 4.7 R |
| Sample pump 370 (6 V part at 5 V) | 0.300 | 0.350 | E |
| STL-19P LiDAR | 0.290 | 0.290 | Waveshare: 290 mA |
| Scout XIAO ESP32C3 + RFM95W | 0.120 | 0.470 | Wi-Fi TX 0.35 A + LoRa +17 dBm 0.087 A + LDO |
| MG90S servo (idle / stall) | 0.010 | 0.700 | E: stall ~0.7 A |
| IR break-beam pair | 0.020 | 0.020 | Adafruit 3 mm, 5 V |
| **Total** | **1.48** | **2.57** | capacity 3.0 A |

Peak assumes servo stall during a Wi-Fi burst - 84 %, amber. Keep cam travel short; a 5 A UBEC removes the risk. An Ambetronics OEM gas package (target 3 W) needs its own BEC.

### FC 5.2 V (PM02 BEC)

| Load | Typical A | Peak A | Basis |
|---|---:|---:|---|
| Pixhawk 6C Mini | 0.250 | 0.300 | E ~1.3-1.5 W |
| FS-iA6B receiver | 0.050 | 0.050 | E |
| MTF-01 flow + ToF | 0.060 | 0.100 | E |
| **Total** | **0.36** | **0.45** | capacity 3.0 A |

Large margin; servo is NOT on this rail (UBEC feeds the Pixhawk servo header).

### Pi 3V3 header (sensors)

| Load | Typical A | Peak A | Basis |
|---|---:|---:|---|
| MLX90640 (15/20/25 mA) | 0.020 | 0.025 | Melexis datasheet |
| 3 x DFRobot gas boards (< 5 mA each) | 0.015 | 0.015 | DFRobot wiki |
| I2C pull-ups + break-beam pull-up | 0.003 | 0.004 | calc |
| **Total** | **0.04** | **0.04** | capacity 0.3 A planning budget (no official Pi 5 per-pin figure) |

~40 mA; sensors stay on the Pi 3V3 so I2C never sees 5 V.

### Puck 3V3 (AP2112K-3.3)

| Load | Typical A | Peak A | Basis |
|---|---:|---:|---|
| ESP32-C3-MINI-1 RX / TX 20.5 dBm | 0.084 | 0.350 | Espressif module datasheet |
| RFM95W RX / TX +17 dBm PA_BOOST | 0.011 | 0.087 | Semtech SX1276 Table 6 |
| LED + misc | 0.002 | 0.003 |  |
| **Total** | **0.10** | **0.44** | capacity 600 mA |

Peak 0.44 A only if Wi-Fi and LoRa transmit together (firmware avoids it). Dropout ~0.19 V at 0.45 A -> needs VBAT >= 3.5 V for a clean 3.3 V.

Endurance cross-check (propulsion owns the final number): 3300 mAh x 80 % usable / ~25 A hover = **~6.3 min hover**.

## SUTRA puck energy budget (1S 400 mAh)

Usable charge = 400 mAh x 0.85 (stop at ~3.5 V so the LDO holds 3.3 V at 0.45 A peaks) x 0.90 (ageing/temperature) = **306 mAh**.

| Datasheet current | Value | Source |
|---|---:|---|
| ESP32-C3-MINI-1 Wi-Fi RX | 82 mA | module datasheet Table 6-4 |
| ESP32-C3-MINI-1 TX 802.11b 1 Mbps @ 20.5 dBm | 350 mA | module datasheet Table 6-4 |
| ESP32-C3 modem-sleep avg, DTIM1 (measured by Espressif) | 21.5 mA | ESP-IDF low-power Wi-Fi guide |
| ESP32-C3 light-sleep | 130 uA | chip datasheet |
| SX1276 TX +17 dBm PA_BOOST | 87 mA | Semtech SX1276 Table 6 (RFM95W RFO not bonded) |
| SX1276 RX (LnaBoost on) | 11.5 mA | Semtech SX1276 Table 6 |
| LoRa time on air, 20 B, SF9/125 kHz, CR4/5 | 185 ms | Semtech AN1200.13 formula |
| AP2112K quiescent / shutdown | 55 uA / 0.01 uA | Diodes AP2112 datasheet |
| DRV5032FB supply at 3 V (5 Hz) | 0.69 uA | TI SLVSDC7H |
| MCP73831 battery reverse current, VDD floating | 0.25 uA | Microchip DS20001984H |

LoRa lifeline: one 20-byte beacon every 10 s at SF9 = 1.85 % duty (G.S.R. 853(E) sensor/telemetry class allows <= 2.5 % for nodes) -> 1.61 mA; 10 % RX windows -> 1.15 mA.

| Mode | Average current | Runtime on 306 mAh | Basis |
|---|---:|---:|---|
| A. Full-rate relay (ESP-NOW-LR always listening, 10 % TX) | 111.7 mA | 2.7 h | RX 82 mA x 90 % + TX 350 mA x 10 % + LoRa beacons/RX windows |
| B. Telemetry relay, Wi-Fi power-save | 31.3 mA | 9.8 h | Espressif measured modem-sleep avg 21.5 mA (DTIM1) + 2 % TX + LoRa |
| C. Parked beacon (Wi-Fi off, auto light-sleep) | 3.0 mA | 102 h (4.3 days) | light-sleep 130 uA + LoRa beacon SF9 every 10 s + 10 % RX |
| D. Stored in cassette (hall holds LDO off) | 2.9 uA | limited by LiPo self-discharge (months) | hall 0.8 + divider 1.85 + charger 0.25 + LDO 0.01 uA |

**Headline:** about **2.7 h** of worst-case full-rate relaying, about **10 h** as a telemetry relay in Wi-Fi power-save, and about **4 days** as a parked LoRa beacon. A mock-gallery sortie is ~6 min of flight, so a fresh puck outlasts many sorties; the binding limit is the vehicle battery, not the puck.

Assumptions: 3.3 V rail, linear LDO (battery current = load current), 10 % Wi-Fi TX duty in mode A, firmware never overlaps Wi-Fi and LoRa TX, 25 C. Measure on the bench with a Nordic PPK2 or INA219 before Stage 3 claims.

