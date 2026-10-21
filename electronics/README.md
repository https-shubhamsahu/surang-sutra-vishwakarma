# SURANG-SUTRA electronics: Stage 2 design package

Vishwakarma Awards 2026-27, Stage 2 (deadline 25 Oct 2026). Team Palanteen, TSEC Mumbai. VK26-AU-PAI-0065.

**Status:** this is a design. Nothing has been built, flashed or measured. Every current, runtime and price below is a datasheet value, a calculation or a quote-level estimate. No PCB layout exists yet; layout is Month 1 of the roadmap.

## Files

| Path | What it is |
|---|---|
| `kicad/surang-sutra/sutra-puck.kicad_pro` / `.kicad_sch` | SUTRA puck carrier board, the PCB we will fabricate (A3, 44 parts) |
| `kicad/surang-sutra/surang-avionics.kicad_pro` / `.kicad_sch` | SURANG interconnect and power distribution at connector level (A2, 48 parts) |
| `kicad/surang-sutra/surang-sutra.kicad_sym` | custom symbols: ESP32-C3-MINI-1, DRV5032 (DBZ) and the module blocks. Project `sym-lib-table` / `fp-lib-table` point at the KiCad 10 libraries |
| `erc-puck.rpt` / `.json`, `erc-avionics.rpt` / `.json` | ERC reports (`kicad-cli sch erc --severity-all`) |
| `exports/*.pdf`, `exports/*.svg` | plain KiCad exports of both sheets |
| `exports/sutra-puck-deck.png` (4800 px), `exports/surang-avionics-deck.png` (7000 px) | deck renders, recoloured to the deck palette (`*-deck.svg` too) |
| `exports/sutra-puck.net`, `exports/sutra-puck-bom-kicad.csv` | puck netlist and BOM from kicad-cli. The avionics netlist and BOM are there too |
| `pinmap.md`, `pinmap.png` / `.svg` | every SURANG link (22 harness runs), Pi header and Pixhawk port allocation, I2C map, puck GPIO map |
| `power-budget.md`, `power-budget.png` / `.svg` | rail-by-rail loads and margins, plus the puck energy budget |
| `bom.csv`, `bom.md` | itemised Stage 3 prototype BOM with totals, 15 % contingency, the per-puck breakdown and the comparison with the Ambetronics BOM |
| `scripts/` | generators. `./scripts/export_all.sh` rebuilds both schematics, runs ERC, exports everything and cross-checks each netlist against the intended connections. `make_bom.py`, `make_power.py` and `make_pinmap.py` build the documents |

## ERC status

- **Both schematics: 0 errors, 0 warnings** (KiCad 10.0.7, all severities).
- KiCad skips four checks by default: single global label, four-way junction, SPICE model and footprint-filter match. None applies here: there are no global labels, no simulation, and footprints were assigned by hand.
- ERC alone can pass on a wrong design, so `scripts/check_netlist.py` also compares every exported net against the connection list the generator meant to draw. Both sheets match.
- PWR_FLAGs mark nets that enter through passive parts (battery, XT90, fuses, USB VBUS) and therefore have no power-output pin to drive them.
- The module symbols use real pin types: TX = output, RX = input, open-collector, power in/out. That means ERC would catch a TX-to-TX or an undriven input.

## Key design decisions

**ESP32-C3 + SX1276 at 865-867 MHz.**
- The ESP32-C3 provides Wi-Fi / ESP-NOW long-range relaying and 802.11mc FTM ranging, which the original ESP32 lacks.
- It has native USB-Serial/JTAG on IO18/19, so the one USB-C port both charges and flashes the board.
- The ESP32-C3-MINI-1 module costs about Rs 249.
- The SX1276 (RFM95W-868) gives a low-rate LoRa lifeline that bends around corners far better than 2.4 GHz.
- **Regulation.** India delicensed **865-868 MHz for short-range devices under G.S.R. 853(E), 10 Dec 2021**. For tracking, telemetry and sensor data the limits are 500 mW ERP, at most 200 kHz bandwidth, at most 2.5 % duty (10 % for network access points), adaptive power control, and equipment type approval still required. We read the gazette copy.
- The older 865-867 MHz exemption is reported as **G.S.R. 564(E), 30 Jul 2008** (1 W transmitter, 4 W ERP, 200 kHz). We saw it only through DoT/WPC search snippets and did not read it.
- We stay inside 865-867 MHz, which fits both, run PA_BOOST at +17 dBm and keep duty at or below 2.5 % (SF9 beacon every 10 s = 1.85 %).
- On the RFM95W the RFO pin is not routed to the antenna, so firmware must use PA_BOOST.

**Hall wake gates the LDO.**
- A DRV5032FB (omnipolar, push-pull, 5 Hz, 0.69 uA at 3 V) runs from VBAT and drives the AP2112K EN pin directly.
- In the cassette, the magnet pulls OUT low, so the LDO is off and the ESP32 is fully unpowered. The whole board then draws about 3 uA, so a stored puck is limited by LiPo self-discharge, not by firmware.
- Out of the tube, OUT goes high and the puck boots. No GPIO wake and no deep-sleep firmware path is needed.

**Strapping and pins.**
- IO2 and IO8 are pulled up with 10k. IO9 is BOOT (10k pull-up and a button).
- LoRa SPI runs through the GPIO matrix: SCK IO6, MOSI IO7, MISO IO5, NSS IO10 (with pull-up), RST IO4.
- DIO0 is on IO1 and DIO1 on IO3. Both can wake the chip from deep sleep.
- The battery ADC is on IO0 = ADC1_CH0, because ADC2 on the C3 is uncalibrated and has an erratum.

**Puck power path.**
- USB-C (CC 5.1k pull-downs) or cassette pogo pads feed an MCP73831 set to 196 mA (RPROG 5.1k), then a 1S 400 mAh cell, then an AP2112K-3.3 (600 mA, peak load about 0.44 A).
- USBLC6-2SC6 provides ESD protection on the field-exposed USB port.

**Vehicle power.**
- 6S XT90-S goes to the PM02 V3 (V/I sense to POWER1), then to the 4-in-1 ESC, with 470 uF at the ESC pads.
- Two fused branches leave the 6S bus, each with a 2 A or 3 A mini-blade fuse and an SMBJ28A TVS:
  - Pololu D36V50F5 to the Pi 5 through a USB-C power pigtail (`usb_max_current_enable=1`).
  - A 3 A UBEC for +5V_AUX: servo rail, LiDAR, scout node, IR, pump, break-beam.
- If the battery is reversed, the TVS conducts and the fuse opens.

**Signals.**
- MAVLink2 at 921600 runs on TELEM2 to Pi UART0.
- DShot600 runs on FMU AUX1-4. The IO/MAIN outputs cannot do DShot.
- The release servo is on AUX5.
- LiDAR goes to UART2, the scout ESP32-C3 to UART3, and the camera to CSI.
- MOSFET low-side drivers (AO3400A, 100R gate, 100k pull-down) run the IR and the pump.

**I2C address map.**
- I2C1 (GPIO2/3): MLX90640 at **0x33**, alone on the bus so it can run fast.
- I2C3 (GPIO6/7, 100 kHz, 4.7k pull-ups): **SEN0465 O2 0x74, SEN0466 CO 0x75, SEN0467 H2S 0x76**, set with the A0/A1 DIP switches.
- **0x77**, the DFRobot factory default, is deliberately left unused.
- All sensors run from the Pi 3V3 rail.

**Base station.** The base ESP32-C3 node and the base LoRa node are two spare SUTRA carrier boards on the laptop USB, using the same firmware family. Ten PCBs are fabricated and seven are assembled.

## Headline numbers

- **BOM:**
  - Vehicle: Rs 1,41,471.
  - Seven carrier boards at Rs 1,735: Rs 12,145.
  - Integration: Rs 4,500.
  - Core: Rs 1,58,116. With 15 % contingency: **Rs 1,81,833**, which is Rs 31,833 over the Rs 1.50 lakh core budget. With the listed cost-downs: Rs 1,62,946.
  - The gas package (Rs 27,297) stays outside the core, as it was in the Ambetronics proposal.
- **Per puck:** Rs 1,735 as drawn. **This misses the Rs 900 target**; the RFM95W is Rs 819 of it. The cost-down version (Ra-01H plus a wire whip) is Rs 1,207.
- **Puck runtime** on 306 mAh usable:
  - About 2.7 h of worst-case full-rate relaying (112 mA).
  - About 10 h as a telemetry relay in Wi-Fi power-save (31 mA).
  - About 4 days as a parked LoRa beacon (3 mA).
- **Rails at peak:**
  - 6S at 80 % of the PM02 burst rating, with an 80 A cap.
  - +5V_AUX at 86 % (amber).
  - Pi rail at 45 %.
  - Puck 3V3 at 73 %.

## Baseline changes recommended (old -> new, why)

1. **Puck BOM target Rs 900 -> Rs 1,250 for the prototype.** The RFM95W alone is Rs 819 at Robu (and out of stock). Keep Rs 900 as the volume target. Consider the Ai-Thinker Ra-01H: same SX1276, but a different footprint.
2. **Hall sensor "DRV5032" -> DRV5032FB, gating the LDO.** It gives true power-off in the cassette instead of a GPIO wake. FA, FB and DU are push-pull; AJ, FC and ZE are open-drain.
3. **Add an optical-flow + ToF sensor (MTF-01) on TELEM1.** It gives GPS-free Loiter in the gallery and adds Rs 4,199.
4. **Add a total current cap of 80 A (MOT_BAT_CURR_MAX).** The PM02 V3 is rated 60 A continuous and 100 A burst; an unconstrained 2809/7-inch full throttle is about 120 A. Re-terminate the PM02's XT60 (60 A) to XT90 or solder it. The other option is a PM rated for at least 120 A.
5. **+5V_AUX UBEC 3 A -> 5 A.** Peak is 86 % if the servo stalls during a Wi-Fi burst.
6. **Drop the SiK 433 MHz telemetry (Rs 4,139).** MAVLink rides the Pi link and the LoRa lifeline.
7. **The DFRobot gas boards default to 0x77, not 0x74.** Set the DIP switches to 0x74/0x75/0x76.
8. **Price risk on the ESC.** The XRotor G2 65A now lists at Rs 11,269 (out of stock), against the Rs 6,279 reused from 13 Sep. The Pixhawk 6C Mini is also out of stock; the Matek H743-SLIM V3 fallback stands.

## Limitations

- Not built, not measured. The puck runtime uses datasheet currents and an assumed 10 % TX duty; it needs a PPK2/INA219 bench measurement.
- No PCB layout, no RF matching or antenna tuning, no thermal check of the 1 W ballast resistors.
- The ESP32-C3-MINI-1 footprint borrows the ESP32-C6-MINI-1 land pattern, which Espressif's datasheets give as the same 53-pad LGA. Check it against the C3 datasheet before layout.
- The avionics sheet is connector-level. Module internals (Pi, Pixhawk, ESC, sensors) are vendor boards. There is no harness drawing or crimp schedule yet.
- Not intrinsically safe, not DGMS/ATEX/IECEx. For gas-free mock galleries only. Any radio placed on the market still needs WPC equipment type approval.
- Many prices are estimates (E) or reused from 13 Sep 2026 (LA/EA). Out-of-stock items are flagged in `bom.md`.

## Regenerate

```bash
cd electronics/scripts
./export_all.sh                  # schematics, ERC, PDF/SVG/PNG, netlists, KiCad BOMs
python3 make_bom.py && python3 make_power.py && python3 make_pinmap.py
```

The scripts need KiCad 10 (`kicad-cli`), Python 3 with matplotlib, and `rsvg-convert`.
