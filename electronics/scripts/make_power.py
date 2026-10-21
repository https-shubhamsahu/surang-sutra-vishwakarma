"""Power budget (vehicle rails + SUTRA puck energy) -> electronics/power-budget.md and power-budget.png."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

EL = os.path.join(os.path.dirname(__file__), '..')
BLUE, GREEN, INK, SLATE, AMBER, PANEL = '#1D4ED8', '#16A34A', '#0F172A', '#475569', '#D97706', '#F0FDF4'

# ------------------------------------------------------------------ vehicle rails
# (load, typical A, peak A, basis)
RAILS = [
    dict(name='6S main bus (PM02 V3)', v='22.2 V nom (18.0-25.2)', cap_typ=60, cap_peak=100, cap_txt='60 A cont. / 100 A burst',
         loads=[('Propulsion: hover 2.4 kg @ ~4.5 gf/W (typ) / capped climb (peak)', 24.0, 78.9,
                 'hover calc: 2400 gf / 4.5 gf/W = 533 W / 22.2 V; peak = MOT_BAT_CURR_MAX 80 A total'),
                ('Avionics via buck + UBEC + PM BEC', 1.0, 1.1, 'sum of 5 V rails below / 0.9 eff / 22.2 V')],
         note='Unconstrained full throttle is ~120 A (4 x ~30 A, 2808-class at 6S/7", E) - above the PM02 burst rating, so the 80 A cap is a design rule.'),
    dict(name='+5V1_PI (Pololu D36V50F5)', v='5.0 V', cap_typ=5.0, cap_peak=5.0, cap_txt='5.5 A typ; derated 5.0 A at 25 V in',
         loads=[('Raspberry Pi 5 8GB (idle 3.3 W / stress 9.8 W)', 0.66, 1.96, 'J. Geerling measurements'),
                ('Active cooler fan', 0.05, 0.10, 'E'),
                ('IMX327 camera on CSI', 0.10, 0.15, 'E - not published by Waveshare'),
                ('Sensors on Pi 3V3 (reflected)', 0.03, 0.04, 'see Pi 3V3 rail'),
                ('USB peripherals', 0.0, 0.0, 'none planned (LiDAR on UART)')],
         note='Pi 5 asks for a 5 V / 5 A supply; the 5 A figure includes 1.6 A of USB budget we do not use. Real peak ~2.3 A leaves 54 % headroom.'),
    dict(name='+5V_AUX (UBEC 5 V 3 A)', v='5.0 V', cap_typ=3.0, cap_peak=3.0, cap_txt='3.0 A',
         loads=[('850 nm IR, 2 strings x 0.37 A', 0.74, 0.74, 'calc: (5.0 - 2 x 1.6 V) / 4.7 R'),
                ('Sample pump 370 (6 V part at 5 V)', 0.30, 0.35, 'E'),
                ('STL-19P LiDAR', 0.29, 0.29, 'Waveshare: 290 mA'),
                ('Scout XIAO ESP32C3 + RFM95W', 0.12, 0.47, 'Wi-Fi TX 0.35 A + LoRa +17 dBm 0.087 A + LDO'),
                ('MG90S servo (idle / stall)', 0.01, 0.70, 'E: stall ~0.7 A'),
                ('IR break-beam pair', 0.02, 0.02, 'Adafruit 3 mm, 5 V')],
         note='Peak assumes servo stall during a Wi-Fi burst - 84 %, amber. Keep cam travel short; a 5 A UBEC removes the risk. '
              'An Ambetronics OEM gas package (target 3 W) needs its own BEC.'),
    dict(name='FC 5.2 V (PM02 BEC)', v='5.2 V', cap_typ=3.0, cap_peak=3.0, cap_txt='3.0 A',
         loads=[('Pixhawk 6C Mini', 0.25, 0.30, 'E ~1.3-1.5 W'),
                ('FS-iA6B receiver', 0.05, 0.05, 'E'),
                ('MTF-01 flow + ToF', 0.06, 0.10, 'E')],
         note='Large margin; servo is NOT on this rail (UBEC feeds the Pixhawk servo header).'),
    dict(name='Pi 3V3 header (sensors)', v='3.3 V', cap_typ=0.3, cap_peak=0.3, cap_txt='0.3 A planning budget (no official Pi 5 per-pin figure)',
         loads=[('MLX90640 (15/20/25 mA)', 0.020, 0.025, 'Melexis datasheet'),
                ('3 x DFRobot gas boards (< 5 mA each)', 0.015, 0.015, 'DFRobot wiki'),
                ('I2C pull-ups + break-beam pull-up', 0.003, 0.004, 'calc')],
         note='~40 mA; sensors stay on the Pi 3V3 so I2C never sees 5 V.'),
    dict(name='Puck 3V3 (AP2112K-3.3)', v='3.3 V', cap_typ=0.6, cap_peak=0.6, cap_txt='600 mA',
         loads=[('ESP32-C3-MINI-1 RX / TX 20.5 dBm', 0.084, 0.350, 'Espressif module datasheet'),
                ('RFM95W RX / TX +17 dBm PA_BOOST', 0.0115, 0.087, 'Semtech SX1276 Table 6'),
                ('LED + misc', 0.002, 0.003, '')],
         note='Peak 0.44 A only if Wi-Fi and LoRa transmit together (firmware avoids it). Dropout ~0.19 V at 0.45 A -> needs VBAT >= 3.5 V for a clean 3.3 V.'),
]

# ------------------------------------------------------------------ puck energy
CELL_MAH = 400
USABLE = 0.85 * 0.90     # usable to ~3.5 V under load, x ageing/temperature derate
ESP_RX, ESP_TX = 82.0, 350.0            # module, mA
LORA_TX17, LORA_RX = 87.0, 11.5         # SX1276, mA
TOA_SF9 = 0.1853                        # s, 20 B, SF9/125 kHz, CR4/5
BEACON_S = 10.0
lora_tx = LORA_TX17 * TOA_SF9 / BEACON_S
lora_rx = LORA_RX * 0.10                 # 10 % RX windows for lifeline commands
lora = lora_tx + lora_rx
misc = 0.055 + 0.002 + 0.001 + 0.04      # LDO Iq, divider, hall, LED blink 2 % x 2 mA
MODES = [
    ('A. Full-rate relay (ESP-NOW-LR always listening, 10 % TX)', 0.9 * ESP_RX + 0.1 * ESP_TX + lora + misc,
     'RX 82 mA x 90 % + TX 350 mA x 10 % + LoRa beacons/RX windows'),
    ('B. Telemetry relay, Wi-Fi power-save', 21.47 + 0.02 * ESP_TX + lora + misc,
     'Espressif measured modem-sleep avg 21.5 mA (DTIM1) + 2 % TX + LoRa'),
    ('C. Parked beacon (Wi-Fi off, auto light-sleep)', 0.13 + lora + misc, 'light-sleep 130 uA + LoRa beacon SF9 every 10 s + 10 % RX'),
]
STORAGE_UA = 0.8 + 1.85 + 0.25 + 0.01


def main():
    L = ['# Power budget - SURANG rails and SUTRA puck energy\n',
         'Design-stage calculation, 22 Oct 2026. Nothing is measured yet. Datasheet values are cited; `E` marks an engineering estimate.\n',
         '## SURANG rail summary\n',
         '| Rail | Capacity | Typical load | Peak load | Peak / capacity | Margin at peak |',
         '|---|---|---:|---:|---:|---:|']
    fig_rows = []
    for r in RAILS:
        typ = sum(l[1] for l in r['loads'])
        pk = sum(l[2] for l in r['loads'])
        cap = r['cap_peak']
        util = pk / cap * 100
        unit = 'A'
        L.append(f"| {r['name']} ({r['v']}) | {r['cap_txt']} | {typ:.2f} {unit} | {pk:.2f} {unit} | {util:.0f} % | {100 - util:.0f} % |")
        fig_rows.append((r['name'], typ / r['cap_typ'] * 100, util, r['cap_txt']))
    L.append('\nThe 6S row compares hover (typical) with the 60 A continuous rating and the 80 A capped burst with the 100 A burst rating.\n')
    for r in RAILS:
        L.append(f"### {r['name']}\n")
        L.append('| Load | Typical A | Peak A | Basis |')
        L.append('|---|---:|---:|---|')
        for l in r['loads']:
            L.append(f'| {l[0]} | {l[1]:.3f} | {l[2]:.3f} | {l[3]} |')
        L.append(f"| **Total** | **{sum(l[1] for l in r['loads']):.2f}** | **{sum(l[2] for l in r['loads']):.2f}** | capacity {r['cap_txt']} |")
        L.append(f"\n{r['note']}\n")
    hover_min = 3.3 * 0.8 / 25.0 * 60
    L.append(f'Endurance cross-check (propulsion owns the final number): 3300 mAh x 80 % usable / ~25 A hover = **~{hover_min:.1f} min hover**.\n')

    L.append('## SUTRA puck energy budget (1S 400 mAh)\n')
    L.append(f'Usable charge = 400 mAh x 0.85 (stop at ~3.5 V so the LDO holds 3.3 V at 0.45 A peaks) x 0.90 (ageing/temperature) = **{CELL_MAH * USABLE:.0f} mAh**.\n')
    L.append('| Datasheet current | Value | Source |')
    L.append('|---|---:|---|')
    for k, v, src in [('ESP32-C3-MINI-1 Wi-Fi RX', '82 mA', 'module datasheet Table 6-4'),
                      ('ESP32-C3-MINI-1 TX 802.11b 1 Mbps @ 20.5 dBm', '350 mA', 'module datasheet Table 6-4'),
                      ('ESP32-C3 modem-sleep avg, DTIM1 (measured by Espressif)', '21.5 mA', 'ESP-IDF low-power Wi-Fi guide'),
                      ('ESP32-C3 light-sleep', '130 uA', 'chip datasheet'),
                      ('SX1276 TX +17 dBm PA_BOOST', '87 mA', 'Semtech SX1276 Table 6 (RFM95W RFO not bonded)'),
                      ('SX1276 RX (LnaBoost on)', '11.5 mA', 'Semtech SX1276 Table 6'),
                      ('LoRa time on air, 20 B, SF9/125 kHz, CR4/5', '185 ms', 'Semtech AN1200.13 formula'),
                      ('AP2112K quiescent / shutdown', '55 uA / 0.01 uA', 'Diodes AP2112 datasheet'),
                      ('DRV5032FB supply at 3 V (5 Hz)', '0.69 uA', 'TI SLVSDC7H'),
                      ('MCP73831 battery reverse current, VDD floating', '0.25 uA', 'Microchip DS20001984H')]:
        L.append(f'| {k} | {v} | {src} |')
    L.append(f'\nLoRa lifeline: one 20-byte beacon every {BEACON_S:.0f} s at SF9 = {TOA_SF9 * 100 / BEACON_S:.2f} % duty '
             f'(G.S.R. 853(E) sensor/telemetry class allows <= 2.5 % for nodes) -> {lora_tx:.2f} mA; 10 % RX windows -> {lora_rx:.2f} mA.\n')
    L.append('| Mode | Average current | Runtime on 306 mAh | Basis |')
    L.append('|---|---:|---:|---|')
    run = {}
    for name, ma, basis in MODES:
        h = CELL_MAH * USABLE / ma
        run[name[0]] = (ma, h)
        t = f'{h:.1f} h' if h < 48 else f'{h:.0f} h ({h / 24:.1f} days)'
        L.append(f'| {name} | {ma:.1f} mA | {t} | {basis} |')
    L.append(f'| D. Stored in cassette (hall holds LDO off) | {STORAGE_UA:.1f} uA | limited by LiPo self-discharge (months) | hall 0.8 + divider 1.85 + charger 0.25 + LDO 0.01 uA |\n')
    a_ma, a_h = run['A']
    b_ma, b_h = run['B']
    L.append(f'**Headline:** about **{a_h:.1f} h** of worst-case full-rate relaying, about **{b_h:.0f} h** as a telemetry relay in Wi-Fi power-save, '
             f'and about **{run["C"][1] / 24:.0f} days** as a parked LoRa beacon. A mock-gallery sortie is ~6 min of flight, so a fresh puck outlasts many sorties; '
             'the binding limit is the vehicle battery, not the puck.\n')
    L.append('Assumptions: 3.3 V rail, linear LDO (battery current = load current), 10 % Wi-Fi TX duty in mode A, firmware never overlaps Wi-Fi and LoRa TX, 25 C. '
             'Measure on the bench with a Nordic PPK2 or INA219 before Stage 3 claims.\n')
    open(os.path.join(EL, 'power-budget.md'), 'w').write('\n'.join(L) + '\n')

    # ------------------------------------------------------------------ figure
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 13})
    fig = plt.figure(figsize=(16, 9), dpi=200)
    fig.patch.set_facecolor('white')
    ax = fig.add_axes([0.30, 0.42, 0.62, 0.46])
    names = [r[0] for r in fig_rows][::-1]
    typ = [r[1] for r in fig_rows][::-1]
    pk = [r[2] for r in fig_rows][::-1]
    caps = [r[3] for r in fig_rows][::-1]
    y = range(len(names))
    h = 0.34
    ax.barh([i + h / 2 + 0.02 for i in y], typ, height=h, color=GREEN, label='typical load')
    colors = [AMBER if p >= 80 else BLUE for p in pk]
    ax.barh([i - h / 2 - 0.02 for i in y], pk, height=h, color=colors, label='peak load')
    for i, (t, p, c) in enumerate(zip(typ, pk, caps)):
        ax.text(p + 1.2, i - h / 2 - 0.02, f'{p:.0f} %', va='center', color=INK, fontsize=12, fontweight='bold')
        ax.text(t + 1.2, i + h / 2 + 0.02, f'{t:.0f} %', va='center', color=SLATE, fontsize=11)
    ax.axvline(100, color=INK, lw=1.5)
    ax.text(100, len(names) - 0.35, ' rated capacity', color=INK, fontsize=11, va='bottom')
    ax.set_yticks(list(y))
    ax.set_yticklabels([f'{n}\n{c}' for n, c in zip(names, caps)], fontsize=11, color=INK)
    ax.set_xlim(0, 115)
    ax.set_xlabel('load as % of rail capacity', color=SLATE)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    ax.spines['left'].set_color(SLATE)
    ax.spines['bottom'].set_color(SLATE)
    ax.tick_params(colors=SLATE)
    ax.grid(axis='x', color='#E2E8F0', lw=0.8)
    ax.set_axisbelow(True)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=GREEN, label='typical'), Patch(color=BLUE, label='peak'), Patch(color=AMBER, label='peak >= 80 % (watch)')],
              loc='lower right', frameon=False, fontsize=11)
    fig.text(0.04, 0.94, 'SURANG power budget - rail utilisation (design calculation, not measured)', fontsize=20, fontweight='bold', color=INK)
    fig.text(0.04, 0.905, '6S row: hover vs 60 A continuous; burst capped at 80 A (MOT_BAT_CURR_MAX) vs 100 A burst.', fontsize=12, color=SLATE)
    # puck panel
    ax2 = fig.add_axes([0.30, 0.08, 0.62, 0.20])
    labels = ['A  full-rate relay', 'B  telemetry relay (power-save)', 'C  parked LoRa beacon']
    hrs = [run['A'][1], run['B'][1], run['C'][1]]
    mas = [run['A'][0], run['B'][0], run['C'][0]]
    ax2.barh(range(3)[::-1], hrs, height=0.55, color=BLUE)
    ax2.set_xscale('log')
    ax2.set_xlim(1, 400)
    ax2.set_xticks([1, 3, 10, 30, 100, 300])
    ax2.set_xticklabels(['1', '3', '10', '30', '100', '300'])
    ax2.minorticks_off()
    for i, (hh, ma) in enumerate(zip(hrs, mas)):
        txt = f'{hh:.1f} h  ({ma:.0f} mA avg)' if hh < 48 else f'{hh:.0f} h = {hh / 24:.1f} days  ({ma:.1f} mA avg)'
        ax2.text(hh * 1.08, 2 - i, txt, va='center', color=INK, fontsize=12, fontweight='bold')
    ax2.set_yticks(range(3))
    ax2.set_yticklabels(labels[::-1], fontsize=11, color=INK)
    ax2.set_xlabel('runtime on 1S 400 mAh (306 mAh usable), hours, log scale', color=SLATE)
    for sp in ('top', 'right'):
        ax2.spines[sp].set_visible(False)
    ax2.spines['left'].set_color(SLATE)
    ax2.spines['bottom'].set_color(SLATE)
    ax2.tick_params(colors=SLATE)
    ax2.grid(axis='x', color='#E2E8F0', lw=0.8, which='both')
    ax2.set_axisbelow(True)
    fig.text(0.04, 0.355, 'SUTRA puck energy budget', fontsize=17, fontweight='bold', color=INK)
    fig.text(0.04, 0.322, 'ESP32-C3 + SX1276, LoRa beacon SF9 every 10 s (1.85 % duty). Storage in cassette ~3 uA.', fontsize=12, color=SLATE)
    fig.savefig(os.path.join(EL, 'power-budget.png'), facecolor='white')
    fig.savefig(os.path.join(EL, 'power-budget.svg'), facecolor='white')
    print('puck modes:', {k: (round(v[0], 1), round(v[1], 1)) for k, v in run.items()})


if __name__ == '__main__':
    main()
