"""Custom symbols for the SURANG-SUTRA KiCad project (written to surang-sutra.kicad_sym and embedded in schematics)."""
from schgen import box_symbol

LIB = 'surang-sutra'
P, I, O, B, PI, PO, OC, NC = 'passive', 'input', 'output', 'bidirectional', 'power_in', 'power_out', 'open_collector', 'no_connect'

SYMS = {}


def add(name, **kw):
    if name not in ('ESP32-C3-MINI-1', 'DRV5032xxDBZ'):
        kw.setdefault('hide_numbers', True)
    txt, geom = box_symbol(name, **kw)
    SYMS[name] = txt
    return txt


# ---------------------------------------------------------------- SUTRA puck
# ESP32-C3-MINI-1 pin numbers per Espressif ESP32-C3-MINI-1 datasheet, "Pin Definitions" table.
add('ESP32-C3-MINI-1', ref='U', value='ESP32-C3-MINI-1',
    left=[('8', 'EN', I), ('12', 'IO0/ADC1_0', B), ('13', 'IO1/ADC1_1', B), ('5', 'IO2 (strap)', B),
          ('6', 'IO3/ADC1_3', B), ('18', 'IO4/ADC1_4', B), ('19', 'IO5', B), ('20', 'IO6', B), ('21', 'IO7', B),
          ('22', 'IO8 (strap)', B), ('23', 'IO9/BOOT (strap)', B), ('16', 'IO10', B)],
    right=[('26', 'IO18/USB_D-', B), ('27', 'IO19/USB_D+', B), None, ('30', 'IO20/RXD0', B), ('31', 'IO21/TXD0', B)],
    top=[('3', '3V3', PI)], bottom=[('1', 'GND', PI)],
    stacked=[(str(n), 'GND', P, '1') for n in [2, 11, 14] + list(range(36, 54))],
    nc=[str(n) for n in [4, 7, 9, 10, 15, 17, 24, 25, 28, 29, 32, 33, 34, 35]],
    fp='RF_Module:ESP32-C6-MINI-1',
    ds='https://www.espressif.com/sites/default/files/documentation/esp32-c3-mini-1_datasheet_en.pdf',
    desc='ESP32-C3 RISC-V Wi-Fi 4 / BLE 5 module, 4 MB flash, PCB antenna, 13.2x16.6 mm LGA-53',
    keywords='esp32 c3 wifi ble module')

# TI DRV5032 ultra-low-power hall switch, SOT-23 (DBZ): 1 VCC, 2 OUT, 3 GND
add('DRV5032xxDBZ', ref='U', value='DRV5032FB',
    left=[], right=[('2', 'OUT', O)], top=[('1', 'VCC', PI)], bottom=[('3', 'GND', PI)], width=10.16,
    fp='Package_TO_SOT_SMD:SOT-23', ds='https://www.ti.com/lit/ds/symlink/drv5032.pdf',
    desc='Ultra-low-power digital hall switch (FB: omnipolar, push-pull, 5 Hz, 0.69 uA @ 3 V), 1.65-5.5 V, SOT-23', keywords='hall switch')

# ---------------------------------------------------------------- SURANG avionics (connector-level modules)
add('Pixhawk6C_Mini', ref='U', value='Holybro Pixhawk 6C Mini (ArduPilot)',
    left=[('POWER1.1', 'POWER1 5V_IN', PI), ('POWER1.3', 'POWER1 CURRENT', I), ('POWER1.4', 'POWER1 VOLTAGE', I),
          ('POWER1.5', 'POWER1 GND', P), None,
          ('RC.1', 'RC_IN 5V_OUT', PO), ('RC.2', 'RC_IN iBUS/PPM/SBUS', I), ('RC.3', 'RC_IN GND', P), None,
          ('TELEM1.1', 'TELEM1 5V_OUT', PO), ('TELEM1.2', 'TELEM1 TX', O), ('TELEM1.3', 'TELEM1 RX', I), ('TELEM1.6', 'TELEM1 GND', P)],
    right=[('TELEM2.2', 'TELEM2 TX', O), ('TELEM2.3', 'TELEM2 RX', I), ('TELEM2.4', 'TELEM2 CTS', I), ('TELEM2.5', 'TELEM2 RTS', O),
           ('TELEM2.1', 'TELEM2 5V_OUT', PO), ('TELEM2.6', 'TELEM2 GND', P), None,
           ('AUX.1', 'FMU AUX1 DShot (SERVO9)', O), ('AUX.2', 'FMU AUX2 DShot (SERVO10)', O), ('AUX.3', 'FMU AUX3 DShot (SERVO11)', O),
           ('AUX.4', 'FMU AUX4 DShot (SERVO12)', O), ('AUX.5', 'FMU AUX5 PWM (SERVO13)', O), ('AUX.GND', 'PWM header GND', P)],
    width=55.88, desc='Flight controller, STM32H743; ports drawn at connector level (JST-GH); DShot only on the 6 FMU (AUX) outputs',
    ds='https://docs.holybro.com/autopilot/pixhawk-6c-mini')

add('RaspberryPi5', ref='U', value='Raspberry Pi 5 8GB (companion)',
    left=[('USBC.VBUS', 'USB-C 5V_IN (5.1V/5A)', PI), ('USBC.GND', 'USB-C GND', P), None,
          ('8', 'GPIO14 TXD0 [8]', O), ('10', 'GPIO15 RXD0 [10]', I), None,
          ('7', 'GPIO4 TXD2 [7]', O), ('29', 'GPIO5 RXD2 [29]', I), None,
          ('24', 'GPIO8 TXD3 [24]', O), ('21', 'GPIO9 RXD3 [21]', I), None,
          ('CAM1', 'CAM/DISP1 MIPI CSI-2 (22p)', B)],
    right=[('1', '3V3_OUT [1]', PO), ('3', 'GPIO2 SDA1 [3]', B), ('5', 'GPIO3 SCL1 [5]', B), None,
           ('31', 'GPIO6 SDA3 [31]', B), ('26', 'GPIO7 SCL3 [26]', B), None,
           ('11', 'GPIO17 BEAM_IN [11]', I), ('32', 'GPIO12 PWM0_0 IR [32]', O), ('33', 'GPIO13 PWM0_1 PUMP [33]', O), None,
           ('6', 'GND [6,9,14,20,25,30,34,39]', P)],
    width=60.96, desc='Raspberry Pi 5 40-pin header (physical pin in brackets) + USB-C power + CSI',
    ds='https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-product-brief.pdf')

add('PowerModule_PM02', ref='U', value='Holybro PM02 V3 (2-12S, V/I sense)',
    left=[('IN+', 'BATT IN+', PI), ('IN-', 'BATT IN-', P)],
    right=[('OUT+', 'OUT+ (to ESC/bus)', PO), ('OUT-', 'OUT-', P), None, ('PWR.1', 'PWR 5V2_OUT', PO),
           ('PWR.3', 'PWR CURRENT', O), ('PWR.4', 'PWR VOLTAGE', O), ('PWR.5', 'PWR GND', P)],
    width=33.02, desc='Analog power module: shunt current + voltage divider + 5.2 V/3 A BEC for FC')

add('ESC_4in1', ref='U', value='4-in-1 ESC 6S 65A (Hobbywing XRotor G2)',
    left=[('VBAT+', 'VBAT+ (6S)', PI), ('VBAT-', 'VBAT-', P), None, None, ('S1', 'M1 DShot', I), ('S2', 'M2 DShot', I),
          ('S3', 'M3 DShot', I), ('S4', 'M4 DShot', I), ('CUR', 'CUR (n.c.)', O), ('TLM', 'TLM (n.c.)', O), ('SGND', 'SIG GND', P)],
    right=[('M1A', 'M1 A', O), ('M1B', 'M1 B', O), ('M1C', 'M1 C', O), None, None, ('M2A', 'M2 A', O), ('M2B', 'M2 B', O), ('M2C', 'M2 C', O),
           None, None, ('M3A', 'M3 A', O), ('M3B', 'M3 B', O), ('M3C', 'M3 C', O), None, None,
           ('M4A', 'M4 A', O), ('M4B', 'M4 B', O), ('M4C', 'M4 C', O)],
    width=30.48, desc='4-in-1 BLHeli_32/AM32 ESC, 3-6S')

add('BLDC_Motor', ref='M', value='2808 1300KV',
    left=[('A', 'A', I), ('B', 'B', I), ('C', 'C', I)], width=10.16, desc='3-phase brushless motor')

add('Buck_D36V50F5', ref='U', value='Pololu D36V50F5 (5V 5.5A)',
    left=[('VIN', 'VIN 6-50V', PI), ('EN', 'EN', I), ('GND1', 'GND', P)],
    right=[('VOUT', 'VOUT 5V', PO), ('PG', 'PG', OC), ('GND2', 'GND', P)], width=30.48,
    desc='Synchronous buck, 5 V, 5.5 A typ', ds='https://www.pololu.com/product/4091')

add('UBEC_5V', ref='U', value='5V/3A UBEC (2-6S)',
    left=[('VIN', 'VIN 2-6S', PI), ('GND1', 'GND', P)], right=[('VOUT', 'VOUT 5V', PO), ('GND2', 'GND', P)],
    width=22.86, desc='Switching BEC for servo, pump, LEDs, LiDAR, scout node')

add('RX_FS-iA6B', ref='U', value='FlySky FS-iA6B (iBUS)',
    left=[('5V', '5V', PI), ('IBUS', 'iBUS out', O), ('GND', 'GND', P)], width=22.86,
    desc='2.4 GHz RC receiver, iBUS serial')

add('XIAO_ESP32C3', ref='U', value='Seeed XIAO ESP32C3 (scout node)',
    left=[('5V', '5V', PI), ('3V3', '3V3_OUT', PO), ('GND', 'GND', P), None, ('D6', 'D6 GPIO21 TX', O), ('D7', 'D7 GPIO20 RX', I)],
    right=[('D8', 'D8 GPIO8 SCK', O), ('D10', 'D10 GPIO10 MOSI', O), ('D9', 'D9 GPIO9 MISO', I), ('D3', 'D3 GPIO5 NSS', O),
           ('D2', 'D2 GPIO4 RST', O), ('D1', 'D1 GPIO3 DIO0', I), ('D4', 'D4 GPIO6 DIO1', I)],
    width=40.64, desc='ESP32-C3 module board with U.FL antenna; ESP-NOW-LR / FTM scout radio')

add('STL-19P', ref='U', value='LDROBOT STL-19P 2D LiDAR',
    left=[('P5V', 'P5V', PI), ('TX', 'Tx 230400 3V3', O), ('PWM', 'PWM', I), None, ('GND', 'GND', P)], width=30.48,
    desc='2D LiDAR, 5 V, 3.3 V UART')

add('MLX90640', ref='U', value='MLX90640 110deg breakout (I2C 0x33)',
    left=[('VIN', 'VIN 3V3', PI), ('SDA', 'SDA', B), ('SCL', 'SCL', B), ('GND', 'GND', P)], width=25.4,
    desc='32x24 thermal array')

for nm, gas, addr in [('SEN0465_O2', 'O2', '0x74'), ('SEN0466_CO', 'CO', '0x75'), ('SEN0467_H2S', 'H2S', '0x76')]:
    add(nm, ref='U', value=f'DFRobot {nm.split("_")[0]} {gas} (I2C {addr})',
        left=[('VCC', 'VCC 3V3', PI), ('SDA', 'SDA', B), ('SCL', 'SCL', B), ('GND', 'GND', P)], width=22.86,
        desc=f'Gravity factory-calibrated electrochemical {gas} sensor; address set by DIP switch')

add('IMX327_Cam', ref='U', value='Waveshare IMX327 2MP IR-CUT (CSI-2)',
    left=[('CSI', 'MIPI CSI-2 (15p)', B)], width=27.94, desc='Starlight camera; 22-to-15-pin FPC to Pi 5')

add('BreakBeam_TX', ref='U', value='IR break-beam emitter',
    left=[('VCC', 'VCC', PI), ('GND', 'GND', P)], width=15.24)
add('BreakBeam_RX', ref='U', value='IR break-beam receiver',
    left=[('VCC', 'VCC', PI), ('OUT', 'OUT (open-coll.)', OC), ('GND', 'GND', P)], width=22.86)

add('OptFlow_3901L0X', ref='U', value='Matek 3901-L0X flow+ToF (optional)',
    left=[('5V', '4.5-5.5V', PI), ('TX', 'TX (MSP)', O), ('RX', 'RX', I), ('GND', 'GND', P)], width=25.4,
    desc='Optical flow + VL53L0X range, MSP over UART (GPS-free position hold)')


def write_lib(path):
    body = ''.join('\t' + s.replace('\n', '\n\t') + '\n' for s in SYMS.values())
    open(path, 'w').write(f'(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "surang_gen")\n\t(generator_version "10.0")\n{body})\n')
