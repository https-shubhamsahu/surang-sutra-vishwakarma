"""Stage 3 prototype BOM data (INR).

Price type codes
  L  = supplier-listed price checked 22 Oct 2026
  LA = supplier-listed price reused from the Ambetronics proposal BOM (13 Sep 2026)
  EA = planning estimate reused from the Ambetronics proposal BOM (13 Sep 2026)
  E  = new planning estimate (22 Oct 2026), not a quote
Stock notes say OOS when the listing was out of stock on 22 Oct 2026.
"""

# (id, section, item, part/MPN, qty, unit, price_type, vendor, local/imported, lead, notes)
VEHICLE = [
    # A. airframe + propulsion
    ('A1', 'Airframe & propulsion', 'Carbon plate for arms, 3K, 300x200x5 mm', 'Robu CF sheet 300x200x5', 1, 3889, 'L', 'Robu', 'Local', '3-5 d',
     '4 arms 25 mm wide; 295 mm motor-to-motor X'),
    ('A2', 'Airframe & propulsion', 'Carbon plate for stack/centre plates, 100x250x2 mm', 'Robu CF sheet 100x250x2', 2, 1279, 'L', 'Robu', 'Local', '3-5 d', 'top, bottom, battery plates'),
    ('A3', 'Airframe & propulsion', 'CNC cutting of frame plates', 'DXF from cad/; IndiaMART CF cutters (Ultrasafe, RGM)', 1, 2000, 'E', 'IndiaMART RFQ', 'Local', '7-10 d', 'quote on request'),
    ('A4', 'Airframe & propulsion', 'Brushless motor 2809 1280KV (6S, 7-inch)', 'GEPRC SPEEDX2 2809 1280KV', 4, 3169, 'L', 'Robu', 'Local', '3-5 d',
     'in stock; alt. T-Motor Velox V2808 1300KV Rs 3,819'),
    ('A5', 'Airframe & propulsion', 'Props 7x4x3 tri-blade (set 2CW+2CCW)', 'HQProp 7X4X3 light grey PC', 3, 375, 'L', 'Robu', 'Local', '3-5 d', '1 fitted + 2 spare sets'),
    ('A6', 'Airframe & propulsion', '4-in-1 ESC 6S 65 A', 'Hobbywing XRotor FPV G2 65A 4in1', 1, 6279, 'LA', 'Robu', 'Local', 'OOS',
     'Robu 22 Oct: new version Rs 11,269 (OOS), old Rs 5,499 (OOS) - price risk'),
    ('A7', 'Airframe & propulsion', 'Bulk cap at ESC pads 470 uF 50 V low-ESR', 'Panasonic EEU-FR1H471', 1, 40, 'E', 'Robu / Evelta', 'Local', '3-5 d', ''),
    # B. battery + power
    ('B1', 'Battery & power', '6S LiPo 3300 mAh 95C, XT90-S, 490 g', 'Tattu G-Tech TAS33006S95X9', 1, 9000, 'EA', 'Robu / Robocraze RFQ', 'Local', 'RFQ',
     'India price/stock unconfirmed'),
    ('B2', 'Battery & power', 'Balance charger 1-6S (ground equipment)', 'SkyRC S100neo', 1, 5169, 'LA', 'Robu', 'Local', '3-5 d', 'not flown'),
    ('B3', 'Battery & power', 'Power module, V/I sense, 5.2 V/3 A BEC', 'Holybro PM02 V3 (2-12S, 60 A cont./100 A burst)', 1, 2469, 'L', 'Robu', 'Local', '3-5 d',
     'replaces Ambetronics item 06 estimate Rs 3,500; re-terminate XT60 leads to XT90/solder'),
    ('B4', 'Battery & power', 'Pi 5 buck 6S -> 5 V 5.5 A', 'Pololu D36V50F5 (#4091)', 1, 4000, 'E', 'Pololu direct ($34.95 + ship/duty)', 'Imported', '2-3 wk',
     'not stocked in India on 22 Oct'),
    ('B5', 'Battery & power', 'Aux UBEC 2-6S -> 5 V 3 A', 'ReadytoSky 2-6S 5V/3A + 12V/3A UBEC', 1, 279, 'L', 'Robu', 'Local', '3-5 d', 'servo, pump, IR, LiDAR, scout'),
    ('B6', 'Battery & power', 'Mini blade fuse holders + 2 A/3 A fuses', 'Littelfuse 0297002 / 0297003 + inline holders', 1, 150, 'E', 'Robu / local', 'Local', '3-5 d', 'F1, F2'),
    ('B7', 'Battery & power', 'TVS 28 V standoff, SMB', 'SMBJ28A', 5, 8, 'E', 'LCSC / Robu', 'Local', '3-5 d', 'D1, D2 + spares'),
    ('B8', 'Battery & power', 'XT90 male + female pair', 'Amass XT90H', 1, 149, 'L', 'Robu', 'Local', '3-5 d', 'vehicle-side receptacle'),
    ('B9', 'Battery & power', '12 AWG silicone wire, 1 m', 'ultra-flexible 12AWG (red + black)', 2, 179, 'L', 'Robu', 'Local', '3-5 d', ''),
    ('B10', 'Battery & power', 'USB-C power pigtail for Pi 5 (5 V only, 20 AWG)', 'USB-C male DIY pigtail', 1, 150, 'E', 'Robu / local', 'Local', '3-5 d', 'set usb_max_current_enable=1'),
    # C. avionics + companion
    ('C1', 'Avionics & companion', 'Flight controller', 'Holybro Pixhawk 6C Mini', 1, 28269, 'LA', 'Robu', 'Local', 'OOS', 'still Rs 28,269 and OOS on 22 Oct'),
    ('C2', 'Avionics & companion', 'RC transmitter + receiver (iBUS)', 'FlySky FS-i6 + FS-iA6B', 1, 5729, 'LA', 'Robu', 'Local', '3-5 d', ''),
    ('C3', 'Avionics & companion', 'Optical flow + ToF for GPS-free hold (NEW, recommended)', 'MicoAir MTF-01', 1, 4199, 'L', 'Probots', 'Local', 'OOS',
     'alt. Matek 3901-L0X Rs 6,999 (OOS)'),
    ('C4', 'Avionics & companion', 'Companion computer', 'Raspberry Pi 5 Model B 8GB', 1, 16825, 'LA', 'Silverline Electronics', 'Local', '3-5 d', ''),
    ('C5', 'Avionics & companion', 'Pi active cooler + 64 GB endurance microSD', 'Raspberry Pi Active Cooler + SanDisk High Endurance 64GB', 1, 1700, 'EA', 'Silverline / Robu', 'Local', '3-5 d', ''),
    # D. sensors + payload + release
    ('D1', 'Sensors, payload & release', '2D LiDAR kit', 'LDROBOT STL-19P / D500 kit', 1, 8499, 'LA', 'Robu', 'Local', '3-5 d', 'UART to Pi GPIO5'),
    ('D2', 'Sensors, payload & release', 'Low-light camera 2MP IR-CUT + 22-15 pin cable', 'Waveshare IMX327 2MP IR-CUT Camera (A)', 1, 4459, 'LA', 'Robu', 'Local', '3-5 d', ''),
    ('D3', 'Sensors, payload & release', 'Thermal array 32x24, 110 deg', '7Semi MLX90640 110deg breakout', 1, 4711, 'LA', 'Robocraze', 'Local', '3-5 d', 'I2C 0x33'),
    ('D4', 'Sensors, payload & release', '850 nm illumination + MOSFET driver', '4 x 1 W 850 nm star LEDs, 2 x AO3400A, 2512 4.7R, gate R', 1, 1000, 'EA', 'Robu / Robocraze', 'Local', '3-5 d',
     'AO3400A Rs 6 L; 850 nm 3 W chips Rs 2,799/10 on Amazon'),
    ('D5', 'Sensors, payload & release', 'Sample pump, 370 micro diaphragm 6 V', '370 micro DC air pump 6V', 1, 359, 'L', 'Robu', 'Local', '3-5 d', 'run at 5 V via PWM'),
    ('D6', 'Sensors, payload & release', 'Flow cell, inlet tube, PTFE filter, fittings', 'printed cell + silicone tube + 0.45 um PTFE disc', 1, 400, 'E', 'Local', 'Local', '7 d', 'gas sensors themselves are outside core'),
    ('D7', 'Sensors, payload & release', 'IR break-beam pair, 3 mm', 'Adafruit 2167', 1, 1491, 'L', 'Amazon.in', 'Imported', '1-2 wk', 'DIY IR LED + phototransistor ~Rs 100 fallback'),
    ('D8', 'Sensors, payload & release', 'Micro servo, metal gear (escapement)', 'MG90S', 2, 269, 'L', 'Robu', 'Local', '3-5 d', '1 + spare'),
    ('D9', 'Sensors, payload & release', 'Neodymium magnets 6x3 mm (60 pcs)', 'N35+ disc 6x3', 1, 299, 'L', 'Amazon.in', 'Local', '3-5 d', 'cassette hall-hold, one per puck slot'),
    ('D10', 'Sensors, payload & release', 'Scout radio node (Wi-Fi/ESP-NOW-LR, FTM)', 'Seeed XIAO ESP32C3 (U.FL antenna incl.)', 1, 749, 'L', 'ThinkRobotics', 'Local', '2-4 wk',
     'pre-order; Robu OOS'),
    ('D11', 'Sensors, payload & release', 'Scout LoRa module 868 MHz', 'HopeRF RFM95W-868S2', 1, 819, 'L', 'Robu', 'Local', 'OOS', 'in-stock alt: LionCircuits Rs 2,423+'),
    ('D12', 'Sensors, payload & release', '868 MHz antenna + IPEX-SMA pigtail', 'IPEX1-RP-SMA 15 cm + 865-868 MHz whip', 1, 215, 'E', 'Robu', 'Local', '3-5 d', 'check SMA vs RP-SMA'),
    # E. cage + mechanical
    ('E1', 'Cage & mechanical', '3 mm pultruded GFRP rod, 1 m', 'GFRP 3 mm solid rod', 25, 120, 'E', 'IndiaMART pultrusion RFQ', 'Local', '1-2 wk',
     '120 struts = 20.3 m; 5 struts per rod; fallback Amazon 420 mm 10-pack Rs 1,776'),
    ('E2', 'Cage & mechanical', 'Cage hubs 18 x 12 mm, PA12 MJF', '42 + 6 spare, from cad/', 48, 60, 'E', 'JLC3DP / local MJF bureau', 'Imported', '10-15 d', 'PETG in-house fallback ~Rs 10 each'),
    ('E3', 'Cage & mechanical', 'TPU 95A filament 500 g', 'TPU 95A 1.75 mm', 1, 1200, 'E', 'Robu / Amazon.in', 'Local', '3-5 d', 'hub caps, puck bumpers'),
    ('E4', 'Cage & mechanical', 'PETG filament 1 kg', 'PETG 1.75 mm', 1, 1100, 'E', 'Robu / Amazon.in', 'Local', '3-5 d', 'cassette, mounts, puck shells'),
    ('E5', 'Cage & mechanical', 'Bearing 6800-2RS 10x19x5 (10-pack)', '6800-2RS', 1, 660, 'L', 'Amazon.in (XERFU)', 'Local', '3-5 d', '2 fitted + spares'),
    ('E6', 'Cage & mechanical', 'Carbon tube 10 OD x 8 ID x 1000 mm (pack of 2)', 'Robu CF tube twill 10x8x1000', 1, 1239, 'L', 'Robu', 'Local', 'OOS', 'axle ~580 mm; 500 mm tube Rs 349 too short'),
    ('E7', 'Cage & mechanical', 'Epoxy, CA, heat-set inserts, M2/M3 fasteners for cage', 'misc', 1, 800, 'E', 'local', 'Local', '3 d', ''),
    # G. integration (reused Ambetronics lines)
    ('G1', 'Integration', 'Mounts, fasteners, signal wiring, JST-GH/Dupont, strain relief', 'Ambetronics item 21', 1, 2500, 'EA', 'Robu / local', 'Local', '3-5 d', ''),
    ('G2', 'Integration', 'Bench consumables + charging accessories (LiPo bag, checker)', 'Ambetronics item 22', 1, 1500, 'EA', 'Robu / Robocraze', 'Local', '3-5 d', ''),
    ('G3', 'Integration', 'Puck charging: 5-port USB charger + USB-C cables', 'generic', 1, 500, 'E', 'Amazon.in', 'Local', '3 d', 'or cassette pogo pads'),
]

# Per-board SUTRA carrier BOM (one puck). (id, item, MPN, qty, unit, type, vendor, L/I, notes)
PUCK = [
    ('P1', 'Wi-Fi MCU module', 'ESP32-C3-MINI-1 (-N4; Robu lists -H4)', 1, 249, 'L', 'Robu', 'Local', ''),
    ('P2', 'LoRa module 868 MHz (SX1276)', 'HopeRF RFM95W-868S2', 1, 819, 'L', 'Robu', 'Local', 'OOS 22 Oct; LionCircuits Rs 2,423+ in stock'),
    ('P3', '1S LiPo 400 mAh, JST-PH', '502030/502035 class', 1, 200, 'E', 'Amazon.in / Robu', 'Local', 'KP 602035 Rs 299 L; WLY502040 Rs 135 (OOS)'),
    ('P4', 'Li-ion charger', 'MCP73831T-2ACI/OT', 1, 62, 'L', 'LCSC C424093', 'Imported', 'Robu Rs 130 (OOS)'),
    ('P5', '3.3 V LDO 600 mA', 'AP2112K-3.3TRG1', 1, 17, 'L', 'Robu / LCSC C51118', 'Local', ''),
    ('P6', 'Hall wake switch', 'DRV5032FBDBZR', 1, 16, 'L', 'LCSC (FA C140921 price)', 'Imported', ''),
    ('P7', 'USB ESD array', 'USBLC6-2SC6', 1, 15, 'E', 'LCSC', 'Imported', ''),
    ('P8', 'USB-C receptacle 16P', 'HRO TYPE-C-31-M-12', 1, 26, 'L', 'Robu', 'Local', ''),
    ('P9', 'Battery connector JST-PH 2p SMD', 'S2B-PH-SM4-TB', 1, 10, 'E', 'LCSC / Robu', 'Local', ''),
    ('P10', 'U.FL receptacle', 'Hirose U.FL-R-SMT-1', 1, 22, 'L', 'Robu', 'Local', ''),
    ('P11', '868 MHz antenna (U.FL FPC, flexible)', 'generic 868 MHz FPC U.FL', 1, 120, 'E', 'Robu / LCSC', 'Local', 'or 82 mm wire on J4: Rs 2'),
    ('P12', 'Passives 0603/0805 (12 R, 11 C)', 'per schematic', 1, 30, 'E', 'LCSC / Robu', 'Local', ''),
    ('P13', 'LEDs 0603 x2 + KMR2 buttons x2', 'per schematic', 1, 24, 'E', 'Robu', 'Local', ''),
    ('P14', 'PCB 2-layer ~50 mm, qty 10 incl. shipping', 'JLCPCB', 1, 70, 'E', 'JLCPCB', 'Imported', '~Rs 700 per 10 boards incl. economy freight'),
    ('P15', 'Shell: PETG body + TPU bumper print', '~12 g PETG + 5 g TPU', 1, 40, 'E', 'in-house', 'Local', ''),
    ('P16', 'AprilTag 36h11 30 mm label + solder/flux', '', 1, 15, 'E', 'local', 'Local', ''),
]
PUCK_BOARDS = 7       # 5 pucks + 2 base-station boards (Wi-Fi base, LoRa base); 10 PCBs fabricated
PUCK_TARGET = 900

# Cost-down variant (same schematic except LoRa footprint): Ra-01H (SX1276), wire antenna
PUCK_COSTDOWN = {'P2': ('Ai-Thinker Ra-01H (SX1276, 868/915) - footprint change', 409, 'L', 'LCSC C503593 (18+)'),
                 'P11': ('82 mm quarter-wave wire on J4', 2, 'E', 'local')}

GAS_OUTSIDE_CORE = [
    ('X1', 'Gas (outside core)', 'O2 electrochemical, I2C', 'DFRobot SEN0465', 1, 10499, 'L', 'Robu', 'Local', '3-5 d', 'dev fallback'),
    ('X2', 'Gas (outside core)', 'CO electrochemical, I2C', 'DFRobot SEN0466', 1, 7979, 'L', 'Robu', 'Local', '3-5 d', ''),
    ('X3', 'Gas (outside core)', 'H2S electrochemical, I2C', 'DFRobot SEN0467', 1, 8819, 'L', 'Robu', 'Local', 'OOS', ''),
]

AMBETRONICS_CORE_TOTAL = 148942   # incl. 15 % contingency, 13 Sep 2026
AMBETRONICS_BUDGET = 150000
REMOVED = [('Ambetronics 01', 'F450 bare frame', 849, 'replaced by custom 7-inch 295 mm carbon X (A1-A3)'),
           ('Ambetronics 02', 'XRotor 3115 900KV motors x4', 12000, 'replaced by 2809 1280KV (A4)'),
           ('Ambetronics 04', 'HQ 9x4x3 props', 1600, 'replaced by 7x4x3 (A5)'),
           ('Ambetronics 06', 'Power module + harness (E)', 3500, 'now PM02 V3 L + itemised harness (B3, B6-B10)'),
           ('Ambetronics 10', 'SiK 433 MHz telemetry pair', 4139, 'dropped: MAVLink rides Pi Wi-Fi / ESP-NOW + LoRa lifeline'),
           ('Ambetronics 13', 'Pi + accessory converters (E)', 3000, 'now D36V50F5 + UBEC + fuses/TVS (B4-B7)'),
           ('Ambetronics 18', '3 mm carbon rods', 1287, 'baseline uses 3 mm GFRP (E1)'),
           ('Ambetronics 19', 'Cage race + release mechanism (E)', 5000, 'itemised: E2-E7, D8, D9'),
           ('Ambetronics 20', 'SUTRA development (2 relays, E)', 2500, 'now 7 custom carrier boards (section F)')]
