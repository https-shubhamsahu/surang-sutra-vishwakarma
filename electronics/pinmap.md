# SURANG avionics pin map and wiring table

Design baseline 22 Oct 2026 (Stage 2). Harness not built. Every logic link is 3.3 V; no level shifters are needed. Pin numbers in [brackets] are Raspberry Pi 40-pin header positions. Schematic: `kicad/surang-sutra/surang-avionics.kicad_sch`.

## Every link

| # | From | Port / pin | To | Port / pin | Net | Protocol | Level / rate | Connector | Wire | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| W1 | Battery 6S 3300 | XT90-S lead | PM02 V3 | BATT IN (XT60 re-terminated to XT90) | BATT+ / GND | DC power | 18.0-25.2 V | XT90-S <-> XT90 | 12 AWG | keyed + anti-spark; PM02 ships with XT60 (60 A) - replace |
| W2 | PM02 V3 | OUT+ / OUT- | 4-in-1 ESC | VBAT pads | VBAT_6S | DC power | 18.0-25.2 V, <= 80 A (capped) | solder pads | 12 AWG | 470 uF 50 V low-ESR at the ESC pads |
| W3 | 4-in-1 ESC | M1-M4 A/B/C pads | 4 x 2809 1280KV | motor leads | M1..M4 phases | 3-phase | 6S | solder | 18 AWG motor leads | swap any two phases to reverse rotation |
| W4 | PM02 V3 | PWR (GH-6) | Pixhawk 6C Mini | POWER1 (GH-6) | 5V2 x2, CURRENT, VOLTAGE, GND x2 | power + analog sense | 5.2 V / 0-3.3 V | JST-GH 6 <-> JST-GH 6 | supplied cable | BATT_VOLT_MULT 18.182, BATT_AMP_PERVLT 36.364 |
| W5 | VBAT_6S | ESC pad tap | Pololu D36V50F5 | VIN / GND | VBUCK_IN | DC power | 18.0-25.2 V | F1 3 A mini blade + D1 SMBJ28A | 20 AWG | fuse + TVS crowbar = reverse-polarity and surge protection |
| W6 | Pololu D36V50F5 | VOUT / GND | Raspberry Pi 5 | USB-C power in | +5V1_PI | DC power | 5.0 V, <= 2.3 A real / 5 A spec | USB-C pigtail (power only) | 20 AWG, <= 10 cm | config.txt usb_max_current_enable=1 (no USB-PD) |
| W7 | VBAT_6S | ESC pad tap | UBEC 5 V 3 A | VIN / GND | VBEC_IN | DC power | 18.0-25.2 V | F2 2 A mini blade + D2 SMBJ28A | 20 AWG |  |
| W8 | UBEC 5 V 3 A | VOUT / GND | Pixhawk servo rail, LiDAR, scout, IR, pump, break-beam | +5V_AUX bus | +5V_AUX | DC power | 5.0 V, <= 2.6 A peak | Dupont / JST-PH star | 22 AWG | servo rail fed here so the servo plugs straight into AUX5 |
| W9 | Pixhawk 6C Mini | TELEM2 (GH-6): 2 TX, 3 RX, 6 GND | Raspberry Pi 5 | GPIO15 RXD0 [10], GPIO14 TXD0 [8], GND [9] | MAV_FC_TX / MAV_FC_RX | UART, MAVLink2 | 3.3 V, 921600 8N1 | JST-GH 6 -> Dupont 2.54 F | 28 AWG | TX->RX crossed; CTS/RTS and 5 V pin not connected; SERIAL2_BAUD=921 |
| W10 | FlySky FS-iA6B | iBUS servo port | Pixhawk 6C Mini | RC IN | RC_IBUS + 5 V + GND | iBUS serial | 3.3 V logic, 115200 | 3-pin servo -> GH | 28 AWG | if IOMCU does not decode iBUS: spare UART, SERIALx_PROTOCOL=23 |
| W11 | Pixhawk 6C Mini | FMU AUX1-AUX4 (SERVO9-12) | 4-in-1 ESC | S1-S4 + GND (JST-SH) | ESC_S1..S4 | DShot600 | 3.3 V | servo header -> JST-SH 8 | 28 AWG | IO/MAIN outputs cannot do DShot; MOT_PWM_TYPE=6 |
| W12 | Pixhawk 6C Mini | FMU AUX5 (SERVO13) | MG90S servo | signal / + / - | SERVO_PWM | PWM 50 Hz, 1000-2000 us | 3.3 V signal, 5 V supply | 3-pin servo | servo lead | Pi commands release via MAV_CMD_DO_SET_SERVO |
| W13 | Pixhawk 6C Mini | TELEM1 (GH-6): 1 5V, 2 TX, 3 RX, 6 GND | MTF-01 flow + ToF | UART | T1_FC_TX / T1_FC_RX | MSP (or MAVLink) | 3.3 V, 115200 | JST-GH 6 -> GH 4 | 28 AWG | recommended addition for GPS-free Loiter |
| W14 | STL-19P LiDAR | ZH1.5-4: 1 Tx, 2 PWM, 3 GND, 4 P5V | Raspberry Pi 5 | GPIO5 RXD2 [29] | LIDAR_TX | UART one-way | 3.3 V, 230400 8N1 | ZH1.5-4 -> Dupont | 28 AWG | PWM tied to GND (internal 10 Hz); P5V from +5V_AUX; dtoverlay=uart2-pi5 |
| W15 | Waveshare IMX327 | CSI 15-pin FPC | Raspberry Pi 5 | CAM/DISP1 22-pin | CSI_CAM1 | MIPI CSI-2, 2 lanes | D-PHY | 22-to-15 pin FPC (supplied) | FPC 15 cm | camera_auto_detect=0, dtoverlay=imx290,clock-frequency=37125000 |
| W16 | MLX90640 110 deg | VIN, GND, SDA, SCL | Raspberry Pi 5 | I2C1 GPIO2 SDA [3], GPIO3 SCL [5], 3V3 [1] | I2C1_SDA / I2C1_SCL | I2C, addr 0x33 | 3.3 V, 400 kHz-1 MHz | JST-SH/Dupont | 28 AWG twisted | alone on I2C1; Pi has fixed on-board pull-ups |
| W17 | DFRobot SEN0465/0466/0467 | VCC, GND, SDA, SCL | Raspberry Pi 5 | I2C3 GPIO6 SDA [31], GPIO7 SCL [26], 3V3 [17] | I2C3_SDA / I2C3_SCL | I2C, 0x74 / 0x75 / 0x76 | 3.3 V, 100 kHz | Gravity PH2.0-4 -> Dupont | 28 AWG | dtoverlay=i2c3-pi5; 4.7k pull-ups; set A0/A1 DIP; SEL=0 |
| W18 | XIAO ESP32C3 (scout) | D6 TX (GPIO21), D7 RX (GPIO20) | Raspberry Pi 5 | GPIO9 RXD3 [21], GPIO8 TXD3 [24] | SCOUT_TX / SCOUT_RX | UART, SLIP frames | 3.3 V, 921600 8N1 | Dupont | 28 AWG | dtoverlay=uart3-pi5; scout powered from +5V_AUX |
| W19 | XIAO ESP32C3 (scout) | D8 SCK, D10 MOSI, D9 MISO, D3 NSS, D2 RST, D1 DIO0, D4 DIO1 | RFM95W-868 (scout) | SCK, MOSI, MISO, NSS, RESET, DIO0, DIO1 | S_SCK..S_DIO1 | SPI mode 0 | 3.3 V, 8 MHz | carrier perfboard | short traces | RFM95W powered from XIAO 3V3; U.FL -> 868 MHz whip |
| W20 | IR break-beam receiver | OUT (open collector) | Raspberry Pi 5 | GPIO17 [11] | BEAM_OUT | digital, active-low on beam break | 3.3 V (10k to Pi 3V3) | JST-PH 3 -> Dupont | 28 AWG | emitter + receiver powered from +5V_AUX; edge-count confirms one puck |
| W21 | Raspberry Pi 5 | GPIO12 PWM0_0 [32] | IR driver Q1 AO3400A | gate via 100R, 100k pull-down | IR_PWM | PWM ~1 kHz | 3.3 V | Dupont | 28 AWG | 2 strings x 2 x 850 nm 1 W, 4.7R ballast each |
| W22 | Raspberry Pi 5 | GPIO13 PWM0_1 [33] | Pump driver Q2 AO3400A | gate via 100R, 100k pull-down | PUMP_PWM | PWM ~20 kHz | 3.3 V | Dupont | 28 AWG | SS14 flyback across the pump |

## Raspberry Pi 5 header allocation

| Header pin | Function | Connected to |
|---|---|---|
| 1 | 3V3 out | MLX90640 VIN, I2C3 pull-ups, break-beam pull-up |
| 17 | 3V3 out | gas sensor VCC |
| 3 / 5 | GPIO2 SDA1 / GPIO3 SCL1 | MLX90640 (I2C1) |
| 7 | GPIO4 TXD2 | unused (uart2 TX; LiDAR is receive-only) |
| 8 / 10 | GPIO14 TXD0 / GPIO15 RXD0 | Pixhawk TELEM2 MAVLink |
| 11 | GPIO17 | break-beam input |
| 21 / 24 | GPIO9 RXD3 / GPIO8 TXD3 | scout ESP32-C3 UART |
| 26 / 31 | GPIO7 SCL3 / GPIO6 SDA3 | gas sensors (I2C3) |
| 29 | GPIO5 RXD2 | STL-19P LiDAR Tx |
| 32 | GPIO12 PWM0_0 | IR illuminator MOSFET |
| 33 | GPIO13 PWM0_1 | pump MOSFET |
| 6, 9, 14, 20, 25, 30, 34, 39 | GND | one GND per harness |
| CAM/DISP1 | MIPI CSI-2 22-pin | IMX327 |
| USB-C | 5 V in | D36V50F5 pigtail |

config.txt: `dtparam=i2c_arm=on`, `dtoverlay=i2c3-pi5`, `dtoverlay=uart0-pi5`, `dtoverlay=uart2-pi5`, `dtoverlay=uart3-pi5`, `camera_auto_detect=0`, `dtoverlay=imx290,clock-frequency=37125000`, `usb_max_current_enable=1`. GPIO12/13 hardware PWM via the `pwm-2chan` overlay.

## Pixhawk 6C Mini port allocation

| Port | Use |
|---|---|
| POWER1 | PM02 V3 (5.2 V, V/I sense) |
| TELEM1 | MTF-01 optical flow + ToF (MSP, 115200) |
| TELEM2 | Raspberry Pi 5 UART0 (MAVLink2, 921600) |
| RC IN | FS-iA6B iBUS |
| FMU AUX1-4 | ESC M1-M4 DShot600 (SERVO9-12) |
| FMU AUX5 | MG90S release servo (SERVO13) |
| GPS1 / GPS2 | unused (GPS-free); spare UARTs |
| CAN1 / CAN2, I2C | unused |
| Servo rail + | fed from +5V_AUX (UBEC) |

## I2C address map

| Bus | Pi pins | Speed | Pull-ups | Address | Device |
|---|---|---|---|---|---|
| I2C1 | GPIO2/3 [3, 5] | 400 kHz (1 MHz FM+ possible) | Pi on-board fixed | 0x33 | MLX90640 110 deg |
| I2C3 | GPIO6/7 [31, 26] | 100 kHz | 4.7k (R2, R3) | 0x74 | DFRobot SEN0465 O2 (DIP A0=0, A1=0) |
| I2C3 | | | | 0x75 | DFRobot SEN0466 CO (A0=1, A1=0) |
| I2C3 | | | | 0x76 | DFRobot SEN0467 H2S (A0=0, A1=1) |
| I2C3 | | | | 0x77 | factory default of all three - deliberately unused |

## SUTRA puck GPIO map (ESP32-C3-MINI-1)

| Pin | Function |
|---|---|
| IO0 | BAT_ADC (ADC1_CH0, VBAT/2) |
| IO1 | LORA_DIO0 (deep-sleep wake) |
| IO2 | strap, 10k pull-up |
| IO3 | LORA_DIO1 (wake) |
| IO4 | LORA_RST |
| IO5 | SPI MISO |
| IO6 | SPI SCK |
| IO7 | SPI MOSI |
| IO8 | strap, 10k pull-up |
| IO9 | BOOT button (10k pull-up) |
| IO10 | LORA_NSS (10k pull-up) |
| IO18 / IO19 | USB D- / D+ (native USB-Serial/JTAG) |
| IO20 | status LED |
| IO21 | U0TXD test pad |
| EN | 10k + 1 uF RC, reset button |

Puck power: USB-C or cassette pogo pads (5 V) -> MCP73831 (196 mA) -> 1S 400 mAh -> AP2112K-3.3, whose EN is driven by the DRV5032FB hall switch (magnet in the cassette = off).

