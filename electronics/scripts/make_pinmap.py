"""SURANG avionics wiring table (pinmap.md) + block-level wiring figure (pinmap.png/svg)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

EL = os.path.join(os.path.dirname(__file__), '..')
BLUE, GREEN, INK, SLATE, AMBER, PANEL = '#1D4ED8', '#16A34A', '#0F172A', '#475569', '#D97706', '#F0FDF4'

# id, from (device, port/pin), to (device, port/pin), signal, protocol / rate, level, connectors, wire, notes, kind
LINKS = [
    ('W1', 'Battery 6S 3300', 'XT90-S lead', 'PM02 V3', 'BATT IN (XT60 re-terminated to XT90)', 'BATT+ / GND', 'DC power', '18.0-25.2 V', 'XT90-S <-> XT90', '12 AWG',
     'keyed + anti-spark; PM02 ships with XT60 (60 A) - replace', 'power'),
    ('W2', 'PM02 V3', 'OUT+ / OUT-', '4-in-1 ESC', 'VBAT pads', 'VBAT_6S', 'DC power', '18.0-25.2 V, <= 80 A (capped)', 'solder pads', '12 AWG',
     '470 uF 50 V low-ESR at the ESC pads', 'power'),
    ('W3', '4-in-1 ESC', 'M1-M4 A/B/C pads', '4 x 2809 1280KV', 'motor leads', 'M1..M4 phases', '3-phase', '6S', 'solder', '18 AWG motor leads',
     'swap any two phases to reverse rotation', 'power'),
    ('W4', 'PM02 V3', 'PWR (GH-6)', 'Pixhawk 6C Mini', 'POWER1 (GH-6)', '5V2 x2, CURRENT, VOLTAGE, GND x2', 'power + analog sense', '5.2 V / 0-3.3 V',
     'JST-GH 6 <-> JST-GH 6', 'supplied cable', 'BATT_VOLT_MULT 18.182, BATT_AMP_PERVLT 36.364', 'power'),
    ('W5', 'VBAT_6S', 'ESC pad tap', 'Pololu D36V50F5', 'VIN / GND', 'VBUCK_IN', 'DC power', '18.0-25.2 V', 'F1 3 A mini blade + D1 SMBJ28A', '20 AWG',
     'fuse + TVS crowbar = reverse-polarity and surge protection', 'power'),
    ('W6', 'Pololu D36V50F5', 'VOUT / GND', 'Raspberry Pi 5', 'USB-C power in', '+5V1_PI', 'DC power', '5.0 V, <= 2.3 A real / 5 A spec', 'USB-C pigtail (power only)',
     '20 AWG, <= 10 cm', 'config.txt usb_max_current_enable=1 (no USB-PD)', 'power'),
    ('W7', 'VBAT_6S', 'ESC pad tap', 'UBEC 5 V 3 A', 'VIN / GND', 'VBEC_IN', 'DC power', '18.0-25.2 V', 'F2 2 A mini blade + D2 SMBJ28A', '20 AWG', '', 'power'),
    ('W8', 'UBEC 5 V 3 A', 'VOUT / GND', 'Pixhawk servo rail, LiDAR, scout, IR, pump, break-beam', '+5V_AUX bus', '+5V_AUX', 'DC power', '5.0 V, <= 2.6 A peak',
     'Dupont / JST-PH star', '22 AWG', 'servo rail fed here so the servo plugs straight into AUX5', 'power'),
    ('W9', 'Pixhawk 6C Mini', 'TELEM2 (GH-6): 2 TX, 3 RX, 6 GND', 'Raspberry Pi 5', 'GPIO15 RXD0 [10], GPIO14 TXD0 [8], GND [9]', 'MAV_FC_TX / MAV_FC_RX',
     'UART, MAVLink2', '3.3 V, 921600 8N1', 'JST-GH 6 -> Dupont 2.54 F', '28 AWG', 'TX->RX crossed; CTS/RTS and 5 V pin not connected; SERIAL2_BAUD=921', 'data'),
    ('W10', 'FlySky FS-iA6B', 'iBUS servo port', 'Pixhawk 6C Mini', 'RC IN', 'RC_IBUS + 5 V + GND', 'iBUS serial', '3.3 V logic, 115200', '3-pin servo -> GH',
     '28 AWG', 'if IOMCU does not decode iBUS: spare UART, SERIALx_PROTOCOL=23', 'data'),
    ('W11', 'Pixhawk 6C Mini', 'FMU AUX1-AUX4 (SERVO9-12)', '4-in-1 ESC', 'S1-S4 + GND (JST-SH)', 'ESC_S1..S4', 'DShot600', '3.3 V', 'servo header -> JST-SH 8',
     '28 AWG', 'IO/MAIN outputs cannot do DShot; MOT_PWM_TYPE=6', 'data'),
    ('W12', 'Pixhawk 6C Mini', 'FMU AUX5 (SERVO13)', 'MG90S servo', 'signal / + / -', 'SERVO_PWM', 'PWM 50 Hz, 1000-2000 us', '3.3 V signal, 5 V supply',
     '3-pin servo', 'servo lead', 'Pi commands release via MAV_CMD_DO_SET_SERVO', 'control'),
    ('W13', 'Pixhawk 6C Mini', 'TELEM1 (GH-6): 1 5V, 2 TX, 3 RX, 6 GND', 'MTF-01 flow + ToF', 'UART', 'T1_FC_TX / T1_FC_RX', 'MSP (or MAVLink)', '3.3 V, 115200',
     'JST-GH 6 -> GH 4', '28 AWG', 'recommended addition for GPS-free Loiter', 'data'),
    ('W14', 'STL-19P LiDAR', 'ZH1.5-4: 1 Tx, 2 PWM, 3 GND, 4 P5V', 'Raspberry Pi 5', 'GPIO5 RXD2 [29]', 'LIDAR_TX', 'UART one-way', '3.3 V, 230400 8N1',
     'ZH1.5-4 -> Dupont', '28 AWG', 'PWM tied to GND (internal 10 Hz); P5V from +5V_AUX; dtoverlay=uart2-pi5', 'data'),
    ('W15', 'Waveshare IMX327', 'CSI 15-pin FPC', 'Raspberry Pi 5', 'CAM/DISP1 22-pin', 'CSI_CAM1', 'MIPI CSI-2, 2 lanes', 'D-PHY', '22-to-15 pin FPC (supplied)',
     'FPC 15 cm', 'camera_auto_detect=0, dtoverlay=imx290,clock-frequency=37125000', 'data'),
    ('W16', 'MLX90640 110 deg', 'VIN, GND, SDA, SCL', 'Raspberry Pi 5', 'I2C1 GPIO2 SDA [3], GPIO3 SCL [5], 3V3 [1]', 'I2C1_SDA / I2C1_SCL', 'I2C, addr 0x33',
     '3.3 V, 400 kHz-1 MHz', 'JST-SH/Dupont', '28 AWG twisted', 'alone on I2C1; Pi has fixed on-board pull-ups', 'data'),
    ('W17', 'DFRobot SEN0465/0466/0467', 'VCC, GND, SDA, SCL', 'Raspberry Pi 5', 'I2C3 GPIO6 SDA [31], GPIO7 SCL [26], 3V3 [17]', 'I2C3_SDA / I2C3_SCL',
     'I2C, 0x74 / 0x75 / 0x76', '3.3 V, 100 kHz', 'Gravity PH2.0-4 -> Dupont', '28 AWG', 'dtoverlay=i2c3-pi5; 4.7k pull-ups; set A0/A1 DIP; SEL=0', 'data'),
    ('W18', 'XIAO ESP32C3 (scout)', 'D6 TX (GPIO21), D7 RX (GPIO20)', 'Raspberry Pi 5', 'GPIO9 RXD3 [21], GPIO8 TXD3 [24]', 'SCOUT_TX / SCOUT_RX', 'UART, SLIP frames',
     '3.3 V, 921600 8N1', 'Dupont', '28 AWG', 'dtoverlay=uart3-pi5; scout powered from +5V_AUX', 'data'),
    ('W19', 'XIAO ESP32C3 (scout)', 'D8 SCK, D10 MOSI, D9 MISO, D3 NSS, D2 RST, D1 DIO0, D4 DIO1', 'RFM95W-868 (scout)', 'SCK, MOSI, MISO, NSS, RESET, DIO0, DIO1',
     'S_SCK..S_DIO1', 'SPI mode 0', '3.3 V, 8 MHz', 'carrier perfboard', 'short traces', 'RFM95W powered from XIAO 3V3; U.FL -> 868 MHz whip', 'data'),
    ('W20', 'IR break-beam receiver', 'OUT (open collector)', 'Raspberry Pi 5', 'GPIO17 [11]', 'BEAM_OUT', 'digital, active-low on beam break', '3.3 V (10k to Pi 3V3)',
     'JST-PH 3 -> Dupont', '28 AWG', 'emitter + receiver powered from +5V_AUX; edge-count confirms one puck', 'control'),
    ('W21', 'Raspberry Pi 5', 'GPIO12 PWM0_0 [32]', 'IR driver Q1 AO3400A', 'gate via 100R, 100k pull-down', 'IR_PWM', 'PWM ~1 kHz', '3.3 V', 'Dupont', '28 AWG',
     '2 strings x 2 x 850 nm 1 W, 4.7R ballast each', 'control'),
    ('W22', 'Raspberry Pi 5', 'GPIO13 PWM0_1 [33]', 'Pump driver Q2 AO3400A', 'gate via 100R, 100k pull-down', 'PUMP_PWM', 'PWM ~20 kHz', '3.3 V', 'Dupont', '28 AWG',
     'SS14 flyback across the pump', 'control'),
]

PI_PINS = [('1', '3V3 out', 'MLX90640 VIN, I2C3 pull-ups, break-beam pull-up'), ('17', '3V3 out', 'gas sensor VCC'),
           ('3 / 5', 'GPIO2 SDA1 / GPIO3 SCL1', 'MLX90640 (I2C1)'), ('7', 'GPIO4 TXD2', 'unused (uart2 TX; LiDAR is receive-only)'),
           ('8 / 10', 'GPIO14 TXD0 / GPIO15 RXD0', 'Pixhawk TELEM2 MAVLink'), ('11', 'GPIO17', 'break-beam input'),
           ('21 / 24', 'GPIO9 RXD3 / GPIO8 TXD3', 'scout ESP32-C3 UART'), ('26 / 31', 'GPIO7 SCL3 / GPIO6 SDA3', 'gas sensors (I2C3)'),
           ('29', 'GPIO5 RXD2', 'STL-19P LiDAR Tx'), ('32', 'GPIO12 PWM0_0', 'IR illuminator MOSFET'), ('33', 'GPIO13 PWM0_1', 'pump MOSFET'),
           ('6, 9, 14, 20, 25, 30, 34, 39', 'GND', 'one GND per harness'), ('CAM/DISP1', 'MIPI CSI-2 22-pin', 'IMX327'),
           ('USB-C', '5 V in', 'D36V50F5 pigtail')]
FC_PORTS = [('POWER1', 'PM02 V3 (5.2 V, V/I sense)'), ('TELEM1', 'MTF-01 optical flow + ToF (MSP, 115200)'),
            ('TELEM2', 'Raspberry Pi 5 UART0 (MAVLink2, 921600)'), ('RC IN', 'FS-iA6B iBUS'),
            ('FMU AUX1-4', 'ESC M1-M4 DShot600 (SERVO9-12)'), ('FMU AUX5', 'MG90S release servo (SERVO13)'),
            ('GPS1 / GPS2', 'unused (GPS-free); spare UARTs'), ('CAN1 / CAN2, I2C', 'unused'),
            ('Servo rail +', 'fed from +5V_AUX (UBEC)')]
PUCK_PINS = [('IO0', 'BAT_ADC (ADC1_CH0, VBAT/2)'), ('IO1', 'LORA_DIO0 (deep-sleep wake)'), ('IO2', 'strap, 10k pull-up'), ('IO3', 'LORA_DIO1 (wake)'),
             ('IO4', 'LORA_RST'), ('IO5', 'SPI MISO'), ('IO6', 'SPI SCK'), ('IO7', 'SPI MOSI'), ('IO8', 'strap, 10k pull-up'),
             ('IO9', 'BOOT button (10k pull-up)'), ('IO10', 'LORA_NSS (10k pull-up)'), ('IO18 / IO19', 'USB D- / D+ (native USB-Serial/JTAG)'),
             ('IO20', 'status LED'), ('IO21', 'U0TXD test pad'), ('EN', '10k + 1 uF RC, reset button')]


def md():
    L = ['# SURANG avionics pin map and wiring table\n',
         'Design baseline 22 Oct 2026 (Stage 2). Harness not built. Every logic link is 3.3 V; no level shifters are needed. '
         'Pin numbers in [brackets] are Raspberry Pi 40-pin header positions. Schematic: `kicad/surang-sutra/surang-avionics.kicad_sch`.\n',
         '## Every link\n',
         '| # | From | Port / pin | To | Port / pin | Net | Protocol | Level / rate | Connector | Wire | Notes |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    for w in LINKS:
        L.append('| ' + ' | '.join(w[:11]) + ' |')
    L.append('\n## Raspberry Pi 5 header allocation\n')
    L.append('| Header pin | Function | Connected to |')
    L.append('|---|---|---|')
    for p in PI_PINS:
        L.append(f'| {p[0]} | {p[1]} | {p[2]} |')
    L.append('\nconfig.txt: `dtparam=i2c_arm=on`, `dtoverlay=i2c3-pi5`, `dtoverlay=uart0-pi5`, `dtoverlay=uart2-pi5`, `dtoverlay=uart3-pi5`, '
             '`camera_auto_detect=0`, `dtoverlay=imx290,clock-frequency=37125000`, `usb_max_current_enable=1`. GPIO12/13 hardware PWM via the `pwm-2chan` overlay.\n')
    L.append('## Pixhawk 6C Mini port allocation\n')
    L.append('| Port | Use |')
    L.append('|---|---|')
    for p in FC_PORTS:
        L.append(f'| {p[0]} | {p[1]} |')
    L.append('\n## I2C address map\n')
    L.append('| Bus | Pi pins | Speed | Pull-ups | Address | Device |')
    L.append('|---|---|---|---|---|---|')
    L.append('| I2C1 | GPIO2/3 [3, 5] | 400 kHz (1 MHz FM+ possible) | Pi on-board fixed | 0x33 | MLX90640 110 deg |')
    L.append('| I2C3 | GPIO6/7 [31, 26] | 100 kHz | 4.7k (R2, R3) | 0x74 | DFRobot SEN0465 O2 (DIP A0=0, A1=0) |')
    L.append('| I2C3 | | | | 0x75 | DFRobot SEN0466 CO (A0=1, A1=0) |')
    L.append('| I2C3 | | | | 0x76 | DFRobot SEN0467 H2S (A0=0, A1=1) |')
    L.append('| I2C3 | | | | 0x77 | factory default of all three - deliberately unused |')
    L.append('\n## SUTRA puck GPIO map (ESP32-C3-MINI-1)\n')
    L.append('| Pin | Function |')
    L.append('|---|---|')
    for p in PUCK_PINS:
        L.append(f'| {p[0]} | {p[1]} |')
    L.append('\nPuck power: USB-C or cassette pogo pads (5 V) -> MCP73831 (196 mA) -> 1S 400 mAh -> AP2112K-3.3, whose EN is driven by the DRV5032FB hall switch '
             '(magnet in the cassette = off).\n')
    open(os.path.join(EL, 'pinmap.md'), 'w').write('\n'.join(L) + '\n')


def fig():
    plt.rcParams.update({'font.family': 'DejaVu Sans'})
    f = plt.figure(figsize=(18, 10.5), dpi=200)
    f.patch.set_facecolor('white')
    ax = f.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 105)
    ax.axis('off')
    B = {}

    def box(key, x, y, w, h, title, sub='', fc='white', ec=INK):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.25,rounding_size=1.2', fc=fc, ec=ec, lw=1.6))
        ax.text(x + w / 2, y + h - 2.2, title, ha='center', va='top', fontsize=11.5, fontweight='bold', color=INK)
        if sub:
            ax.text(x + w / 2, y + h - 5.4, sub, ha='center', va='top', fontsize=9, color=SLATE, linespacing=1.3)
        B[key] = (x, y, w, h)

    def port(key, side, frac):
        x, y, w, h = B[key]
        return {'l': (x, y + h * frac), 'r': (x + w, y + h * frac), 't': (x + w * frac, y + h), 'b': (x + w * frac, y)}[side]

    def link(a, b, label, kind, lx=None, ly=None, rot=0, path=None):
        col = {'power': GREEN, 'data': BLUE, 'control': INK}[kind]
        lw = {'power': 3.0, 'data': 1.8, 'control': 1.6}[kind]
        ls = {'power': '-', 'data': '-', 'control': (0, (5, 2.5))}[kind]
        pts = [a] + (path or []) + [b]
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=col, lw=lw, ls=ls, solid_capstyle='round', zorder=1)
        ax.plot(*b, marker='o', ms=4.5, color=col, zorder=2)
        if label:
            if lx is None:
                lx, ly = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            ax.text(lx, ly, label, ha='center', va='center', fontsize=8.3, color=INK, rotation=rot, zorder=3, linespacing=1.25,
                    bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=col, lw=0.8))

    ax.text(3, 101.5, 'SURANG avionics - wiring map (connector level, all logic 3.3 V)', fontsize=19, fontweight='bold', color=INK, va='top')
    ax.text(3, 97.3, 'Design baseline, 22 Oct 2026 - not built.  Full pin-by-pin table: electronics/pinmap.md  |  schematic: surang-avionics.kicad_sch',
            fontsize=10.5, color=SLATE, va='top')

    # column 1 - power
    box('bat', 3, 74, 26, 12, '6S LiPo 3300 mAh 95C', 'XT90-S  |  22.2 V nom\n18.0-25.2 V', fc=PANEL)
    box('pm', 3, 55, 26, 13, 'Holybro PM02 V3', '60 A cont. / 100 A burst\nV/I sense + 5.2 V/3 A BEC', fc=PANEL)
    box('buck', 3, 33, 26, 13, 'Pololu D36V50F5 buck', 'F1 3 A fuse + SMBJ28A TVS\n6S -> 5.0 V / 5.5 A (Pi rail)', fc=PANEL)
    box('ubec', 3, 11, 26, 13, 'UBEC 5 V / 3 A', 'F2 2 A fuse + SMBJ28A TVS\n+5V_AUX: servo rail, LiDAR,\nscout, IR, pump, break-beam', fc=PANEL)
    # column 2 - flight
    box('esc', 42, 76, 30, 12, '4-in-1 ESC 6S 65 A', '-> 4 x 2809 1280KV, 7x4x3 props\n470 uF at pads')
    box('fc', 42, 46, 30, 22, 'Pixhawk 6C Mini', 'ArduPilot Copter, GPS-free\nPOWER1  TELEM1  TELEM2\nRC IN  FMU AUX1-5')
    box('rx', 42, 31, 30, 8, 'FlySky FS-iA6B', 'iBUS')
    box('flow', 42, 18, 30, 8, 'MTF-01 flow + ToF', 'recommended addition')
    box('servo', 42, 5, 30, 8, 'MG90S release servo', 'cam escapement, 1 puck/cmd')
    # column 3 - Pi
    box('pi', 86, 22, 32, 46, 'Raspberry Pi 5 8 GB', 'companion computer\n+ active cooler\n\nUART0  GPIO14/15\nUART2  GPIO5 (RX)\nUART3  GPIO8/9\n'
        'I2C1   GPIO2/3\nI2C3   GPIO6/7\nGPIO17 beam in\nGPIO12/13 PWM\nCSI    CAM/DISP1', fc='white')
    # column 4 - sensors / radios
    box('lidar', 140, 84, 37, 8, 'LDROBOT STL-19P 2D LiDAR', '5 V, 290 mA')
    box('cam', 140, 73, 37, 8, 'Waveshare IMX327 2MP IR-CUT', 'starlight, 2-lane CSI-2')
    box('mlx', 140, 62, 37, 8, 'MLX90640 110 deg thermal', 'I2C 0x33')
    box('gas', 140, 49, 37, 10, 'DFRobot O2 / CO / H2S', '0x74 / 0x75 / 0x76\npumped flow cell')
    box('scout', 140, 35, 37, 11, 'Scout node: XIAO ESP32C3', '+ RFM95W-868 on SPI\nESP-NOW-LR / FTM + LoRa')
    box('beam', 140, 24, 37, 8, 'IR break-beam (cassette exit)', 'open-collector, 10k to 3V3')
    box('loads', 140, 5, 37, 15, 'Switched loads (AO3400A)', '4 x 850 nm 1 W IR (0.74 A)\n370 diaphragm pump (0.3 A)\n100R gate + 100k pull-down')

    # power links
    link(port('bat', 'b', 0.5), port('pm', 't', 0.5), 'XT90 | 12 AWG', 'power')
    link(port('pm', 'r', 0.75), port('esc', 'l', 0.5), 'VBAT_6S <= 80 A | 12 AWG', 'power', lx=35.5, ly=73, path=[(35.5, port('pm', 'r', 0.75)[1]), (35.5, 82)])
    link(port('pm', 'r', 0.35), port('fc', 'l', 0.8), 'POWER1 GH-6\n5.2 V + V/I', 'power', lx=36, ly=60)
    link(port('pm', 'b', 0.5), port('buck', 't', 0.5), 'fused 6S tap', 'power')
    link((8, 33), (8, 24), 'F2 tap', 'power')
    link(port('buck', 'r', 0.73), port('pi', 'l', 0.12), 'USB-C pigtail 5 V | 20 AWG', 'power', lx=80.5, ly=35, rot=90, path=[(80, 42.5), (80, 27.5)])
    link(port('ubec', 'r', 0.5), port('loads', 'l', 0.5), '+5V_AUX (also LiDAR, scout, beam, FC servo rail)', 'power', lx=85, ly=1.5,
         path=[(36, 17.5), (36, 1.5), (134, 1.5), (134, 12.5)])
    # flight data
    link(port('fc', 't', 0.5), port('esc', 'b', 0.5), 'AUX1-4 DShot600', 'data')
    link(port('rx', 't', 0.5), port('fc', 'b', 0.5), 'iBUS -> RC IN', 'data')
    link(port('flow', 'r', 0.5), (75, 22), None, 'data', path=[(75, 22)])
    link((75, 22), port('fc', 'r', 0.2), 'TELEM1 MSP 115200', 'data', lx=75, ly=31, rot=90, path=[(75, port('fc', 'r', 0.2)[1])])
    link(port('fc', 'r', 0.75), port('pi', 'l', 0.92), 'TELEM2 <-> UART0\nMAVLink2 921600', 'data', lx=79.5, ly=59.5)
    link(port('fc', 'l', 0.1), port('servo', 'l', 0.5), 'AUX5 PWM 50 Hz', 'control', lx=38, ly=24, rot=90, path=[(38.5, port('fc', 'l', 0.1)[1]), (38.5, 9)])
    # Pi links
    link(port('lidar', 'l', 0.5), port('pi', 'r', 0.97), 'Tx -> UART2 RX (GPIO5) 230400', 'data', lx=128, ly=86.5, path=[(124, 88), (124, port('pi', 'r', 0.97)[1])])
    link(port('cam', 'l', 0.5), port('pi', 'r', 0.84), 'CSI-2 2-lane, 22->15 FPC', 'data', lx=129, ly=77)
    link(port('mlx', 'l', 0.5), port('pi', 'r', 0.66), 'I2C1 GPIO2/3', 'data', lx=129.5, ly=63.5)
    link(port('gas', 'l', 0.5), port('pi', 'r', 0.5), 'I2C3 GPIO6/7 100 kHz', 'data', lx=129.5, ly=50)
    link(port('scout', 'l', 0.5), port('pi', 'r', 0.3), 'UART3 GPIO8/9 921600', 'data', lx=129.5, ly=38)
    link(port('beam', 'l', 0.5), port('pi', 'r', 0.14), 'GPIO17 (active-low)', 'control', lx=129.5, ly=26.3)
    link(port('pi', 'b', 0.6), port('loads', 'l', 0.8), 'GPIO12 IR / GPIO13 pump PWM', 'control', lx=121, ly=17, path=[(105.2, 17), (134, 17)])

    # legend
    lx0, ly0 = 3, 93
    for i, (k, lab) in enumerate([('power', 'power (green, thick)'), ('data', 'serial / bus data (blue)'), ('control', 'GPIO / PWM control (ink, dashed)')]):
        col = {'power': GREEN, 'data': BLUE, 'control': INK}[k]
        ls = {'power': '-', 'data': '-', 'control': (0, (5, 2.5))}[k]
        ax.plot([lx0 + i * 34, lx0 + i * 34 + 6], [ly0, ly0], color=col, lw=3 if k == 'power' else 1.8, ls=ls)
        ax.text(lx0 + i * 34 + 7.5, ly0, lab, va='center', fontsize=10, color=INK)
    f.savefig(os.path.join(EL, 'pinmap.png'), facecolor='white')
    f.savefig(os.path.join(EL, 'pinmap.svg'), facecolor='white')


if __name__ == '__main__':
    md()
    fig()
    print('pinmap written')
