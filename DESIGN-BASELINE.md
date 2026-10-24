# SURANG-SUTRA: Stage 2 design baseline (Vishwakarma Awards 2026-27)

This file is the single source of truth for the Stage 2 deck. CAD, FEA, electronics and the deck all use these numbers.
If an analysis shows a number has to change, change it in your output and say so explicitly (old → new, and why).
Those changes become the "Stage 1 → Stage 2 design iterations" on the deck, so they're welcome.

- **Team:** Team Palanteen, Thakur Shyamnarayan Engineering College (TSEC), Mumbai
- **Vishwakarma ID:** VK26-AU-PAI-0065
- **Theme:** 7, Physical AI for Resilience & Inclusion. Sub-theme: Autonomous Search, Rescue & Tactical Robotics.
- **Stage 2 is a design stage.** Nothing has been built or measured yet, so every number is a TARGET or a CALCULATION, never a measured result.
- **Safety boundary:** a gas-free mock gallery only. The design is not intrinsically safe, not DGMS-approved and not ATEX/IECEx-certified.

## System
- **SURANG** is a reusable scout: an X-quad inside a **single-axis rotating geodesic cage**.
  - Roll mode: on a sound floor the cage rolls about its axle, and a small pitch of the thrust vector drives it, as in HyTAQ (ICRA 2013).
  - Fly mode: it lifts over debris, falls or standing water.
  - The inner frame and sensor core hang on the axle bearings and stay level while the cage turns.
- **SUTRA** is a set of communication-only relay pucks, 5 of them in a central cassette.
  - A one-servo, two-pin escapement releases exactly one puck per command, and a break-beam sensor confirms the exit.
  - A puck drops before a bend, at a link-quality threshold. It relays data and acts as a position beacon (AprilTag plus radio ID).
- **Ground station:** a laptop plus a base ESP32-C3 node and a base LoRa node, running the existing mission-control simulation/replay (surang-sutra-simulation).

## SURANG mechanical (targets)
| Item | Baseline |
|---|---|
| Cage | 2V icosahedral geodesic sphere, **Ø 580 mm** (R = 290 mm), with one icosahedron vertex on each ±Y (axle) pole. 42 hubs, 120 struts. |
| Cage struts | **3 mm pultruded GFRP rod** (E ≈ 40 GPa, flexural strength ≈ 800 MPa, ρ ≈ 2.0 g/cm³). Two chord lengths, ≈ 159 mm and ≈ 179 mm at R = 290. |
| Cage hubs | 3D-printed PA12 (MJF) or PETG, 18 mm dia × 12 mm. Each has a **TPU 95A** contact cap (bumper) on its outer face. |
| Axle | 10 mm OD / 8 mm ID carbon tube along body Y, through the centre plate. A 6800-2RS bearing (10×19×5) sits in each pole hub. |
| Inner frame | Custom 7-inch X frame. **295 mm** motor-to-motor diagonal, 5 mm 3K carbon arms (25 mm wide), 2 mm carbon stack plates. |
| Propulsion | 4 × 2808/2809-class 1250–1300 KV motors (6S), with 7-inch tri-blade props (HQ 7×4×3). The prop tip envelope is ≈ 237 mm radius in the rotor plane. |
| Clearance | The cage inner surface (face centroid at ≈ 0.92 R ≈ 267 mm) must clear the prop tips by **≥ 20 mm**. Check this. |
| Core stack (top → bottom) | GPS-free; Pi 5 + cooler; FC; ESC 4-in-1; 6S 3300 mAh battery (490 g) slung under the centre plate; cassette tube along body −Z below the battery, pucks exiting downward. |
| Sensor spine | Forward-facing: 2D LiDAR (STL-19P, Ø 38 × 34 mm) on top, IMX327 camera + MLX90640 thermal + 850 nm IR LEDs at the nose, gas inlet tube at the nose (pumped flow cell). |
| Release | One MG90S-class micro servo. A cam drives an upper capture pin and a lower release pin, with an IR break-beam at the tube exit. |
| Mass target | ≤ 2.4 kg all-up. Allocation: cage 0.40, frame + mounts 0.30, motors 0.25, ESC + props 0.10, battery 0.49, FC + avionics 0.10, Pi + cooler 0.10, sensors + lights 0.14, gas package 0.10, cassette + 5 pucks 0.17, wiring 0.08, reserve 0.07. |
| Thrust target | ≥ 2.5:1 thrust-to-weight at minimum planned battery voltage, with the cage fitted (≥ 6 kgf total). |

## SURANG electronics (targets)
- **FC:** Holybro Pixhawk 6C Mini (STM32H743, ArduPilot). Fallback: Matek H743-SLIM V3.
- **Power:** a 6S PM with V/I sensing feeds the FC. A 4-in-1 6S 55–65 A ESC (DShot). A separate 6S → 5.1 V / 5 A buck for the Pi 5 (e.g. Pololu D36V50F5), and a separate 5 V rail for the servo, pump and LEDs.
- **Companion:** Raspberry Pi 5 8 GB + active cooler, linked to the FC over MAVLink UART.
- **Sensors:**
  - STL-19P 2D LiDAR (UART)
  - IMX327 (CSI)
  - MLX90640 110° (I²C)
  - Gas: O₂ / CO / H₂S on I²C (DFRobot SEN0465 / 0466 / 0467 as the development fallback; Ambetronics OEM electrochemical + CH₄ NDIR planned), in a pumped flow cell
  - 850 nm IR LEDs (MOSFET-switched)
- **Radios:**
  - RC: FlySky FS-i6 / FS-iA6B (iBUS), or ExpressLRS
  - Scout node: an ESP32-C3 on the vehicle (UART to the Pi) for the Wi-Fi / ESP-NOW-LR mesh and FTM ranging
  - LoRa: SX1276 (RFM95W-868) at **865–867 MHz**, India's licence-exempt band, for the low-rate lifeline
- **Fail-safes:** the ArduPilot RC/GCS failsafe does a hold, then land or return. The Pi has a watchdog. A battery failsafe. A CH₄ interlock rule for the future mine mode (Coal Mines Regulations 2017: 0.75% turn back, 1.25% land). The props idle while perched.

## SUTRA puck (targets)
- **Shell:** Ø 56 mm × 20 mm disc. PETG shell, TPU bumper ring. It self-rights: the battery sits low and the top is domed. A 30 mm AprilTag 36h11 goes on top. Mass ≤ 30 g. BOM ≤ ₹900.
- **Electronics:**
  - ESP32-C3-MINI-1
  - RFM95W-868 (SX1276) over SPI
  - 1S 400 mAh LiPo (502030 class)
  - MCP73831 charger with USB-C (or charge pads in the cassette)
  - AP2112K-3.3 LDO
  - DRV5032 hall sensor, so it wakes when it leaves the cassette magnet
  - status LED and a battery ADC divider
- **Cassette:** a vertical tube holding the 5 stacked pucks (≈ 100 mm stack).

## Style for every figure
- White background, sans font (Inter or DejaVu Sans), 2400 px wide or more, PNG. Also export SVG for diagrams.
- Colours: blue #1D4ED8, green #16A34A, ink #0F172A, slate #475569, light panel #F0FDF4, amber accent #D97706 (warnings), red #DC2626 (critical stress only).
- Anything AI-generated or AI-assisted that ends up in the deck will carry an "AI Generated" label. Don't bake fake photos into figures.

## Stage 2 changes found by the analysis (24 Oct 2026)
These replace the values above. Details in `cad/README.md` and `fea/README.md`.
- **Cage struts:** 3 mm → **4 mm** pultruded GFRP. **Axle:** 10/8 → **15/13 mm** carbon tube, bearings 6800 → **61802-2RS (15×24×5)**. **Hub caps:** 5 mm solid TPU 95A → **20 mm soft TPU**. Why: the 3 mm cage reaches allowable stress at 1.7 J and breaks struts in a 2 m/s strike; the selected cage takes 5.3 J and stays under allowable at all hub types at the 1.5 m/s speed limit.
- **Envelope:** about Ø630 mm over the soft caps, so the scout needs ≥ 0.65 m openings (was 0.6 m).
- **Mass target:** ≤ 2.4 → **≤ 2.5 kg**. The CAD is 2.17 kg with the Stage 1 cage and 2.47 kg with the selected one. Calculated T/W at minimum voltage 3.2 (1250 KV), hover ≈ 6.5 min, roll ≈ 30 min.
- **Puck exit:** the cassette moves from the centreline to **y = +54 mm**, because the equator strut ring blocks a centred drop at every cage angle.
- **After a drop:** hop in fly mode before rolling on (a 20 mm puck under the cage would be struck).
- **Puck:** 34.5 g as drawn; 1.0 mm walls and a 1.0 mm PCB bring it to about 29 g. The dome does not self-right, so the AprilTag goes on both faces.
- **Motors are never cut in the air:** no cage variant survives a 1 m fall onto one hub.
