"""Write electronics/bom.csv and electronics/bom.md from bom_data.py; prints the headline totals."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bom_data as B

EL = os.path.join(os.path.dirname(__file__), '..')


def inr(v):
    v = int(round(v))
    s = str(abs(v))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ','.join(parts) + ',' + tail
    return ('-' if v < 0 else '') + s


def puck_cost(over=None):
    rows = []
    for (pid, item, mpn, q, u, t, ven, li, note) in B.PUCK:
        if over and pid in over:
            mpn, u, t, ven = over[pid]
        rows.append((pid, item, mpn, q, u, t, ven, li, note))
    return rows, sum(r[3] * r[4] for r in rows)


def main():
    puck_rows, puck_unit = puck_cost()
    cd_rows, cd_unit = puck_cost(B.PUCK_COSTDOWN)
    sections = {}
    for r in B.VEHICLE:
        sections.setdefault(r[1], []).append(r)
    sub = {k: sum(r[4] * r[5] for r in v) for k, v in sections.items()}
    vehicle = sum(v for k, v in sub.items() if k != 'Integration')
    integ = sub.get('Integration', 0)
    pucks = puck_unit * B.PUCK_BOARDS
    core = vehicle + pucks + integ
    cont = core * 0.15
    total = core + cont
    gas = sum(r[4] * r[5] for r in B.GAS_OUTSIDE_CORE)
    # cost-down scenario
    cd_savings = {
        'Ra-01H + wire antenna on all 7 boards': (puck_unit - cd_unit) * B.PUCK_BOARDS,
        'Ra-01H on the scout too': 819 - 409,
        'Skip optical flow (C3)': 4199,
        'DIY break-beam instead of Adafruit (D7)': 1391,
        'PETG hubs in-house instead of MJF (E2)': 48 * 50,
        'One base board for both base roles (6 boards, not 7)': cd_unit,
        'Robu Pro-Range 6S 3300 35C (Rs 5,879) instead of Tattu (B1)': 9000 - 5879,
    }
    cd_core = core - sum(cd_savings.values())
    cd_total = cd_core * 1.15

    # ---------------------------------------------------------------- CSV
    with open(os.path.join(EL, 'bom.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['id', 'section', 'item', 'part_number', 'qty', 'unit_inr', 'total_inr', 'price_type', 'vendor',
                    'local_or_imported', 'lead_time', 'notes'])
        for r in B.VEHICLE:
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[4] * r[5], r[6], r[7], r[8], r[9], r[10]])
        for (pid, item, mpn, q, u, t, ven, li, note) in puck_rows:
            w.writerow([pid, f'SUTRA carrier board (x{B.PUCK_BOARDS})', item, mpn, q * B.PUCK_BOARDS, u, q * u * B.PUCK_BOARDS, t, ven, li,
                        'OOS' if 'OOS' in note else ('10-15 d' if li == 'Imported' else '3-5 d'), note])
        w.writerow(['SUB', 'Totals', 'Core subtotal (vehicle + boards + integration)', '', '', '', round(core), '', '', '', '', ''])
        w.writerow(['CONT', 'Totals', 'Contingency 15 %', '', '', '', round(cont), 'E', '', '', '', ''])
        w.writerow(['TOTAL', 'Totals', 'Core total incl. contingency', '', '', '', round(total), '', '', '', '', ''])
        for r in B.GAS_OUTSIDE_CORE:
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[4] * r[5], r[6], r[7], r[8], r[9], r[10]])

    # ---------------------------------------------------------------- Markdown
    L = []
    L.append('# SURANG-SUTRA Stage 3 prototype BOM (electronics + airframe + cage)\n')
    L.append('Prepared 22 Oct 2026 for the Vishwakarma Awards Stage 2 deck. Nothing here has been bought or built. '
             'INR, GST-inclusive where the store shows it (Robu, Amazon.in, Probots). LCSC prices are converted at Rs 88/USD before shipping and duty.\n')
    L.append('**Price type:** `L` = listed by the supplier, checked 22 Oct 2026. `LA` = listed price reused from the Ambetronics proposal BOM (13 Sep 2026). '
             '`EA` = estimate reused from that BOM. `E` = new planning estimate (not a quote). **OOS** = out of stock when checked.\n')
    L.append('## Totals\n')
    L.append('| Block | Rs |')
    L.append('|---|---:|')
    L.append(f'| SURANG vehicle (airframe, power, avionics, sensors, release, cage) | {inr(vehicle)} |')
    L.append(f'| SUTRA carrier boards: {B.PUCK_BOARDS} x Rs {inr(puck_unit)} (5 pucks + Wi-Fi base + LoRa base) | {inr(pucks)} |')
    L.append(f'| Integration (wiring, consumables, charging) | {inr(integ)} |')
    L.append(f'| **Core subtotal** | **{inr(core)}** |')
    L.append(f'| Contingency 15 % | {inr(cont)} |')
    L.append(f'| **Core total incl. contingency** | **{inr(total)}** |')
    L.append(f'| Ambetronics proposal core total (13 Sep 2026, F450 baseline) | {inr(B.AMBETRONICS_CORE_TOTAL)} |')
    L.append(f'| Difference vs the Rs 1.50 lakh core budget | {inr(total - B.AMBETRONICS_BUDGET)} |')
    L.append(f'| Gas package (DFRobot dev fallback), outside core as before | {inr(gas)} |\n')
    L.append(f'**Verdict:** the itemised Stage 3 build is **Rs {inr(total)}**, i.e. **Rs {inr(total - B.AMBETRONICS_BUDGET)} over** the Rs 1.50 lakh core budget. '
             f'The overrun comes from items the F450 shortlist did not cost: 7 real carrier boards instead of 2 relays, an itemised GFRP cage, '
             f'a custom carbon frame, the optical-flow sensor and the imported Pi buck. '
             f'With the cost-downs below the total drops to about **Rs {inr(cd_total)}**.\n')
    L.append('| Cost-down option | Saves Rs |')
    L.append('|---|---:|')
    for k, v in cd_savings.items():
        L.append(f'| {k} | {inr(v)} |')
    L.append(f'| **Core total incl. contingency after all cost-downs** | **{inr(cd_total)}** |\n')

    for sec, rows in sections.items():
        L.append(f'## {sec} - Rs {inr(sub[sec])}\n')
        L.append('| ID | Item | Part number | Qty | Unit Rs | Total Rs | Type | Vendor | L/I | Lead | Notes |')
        L.append('|---|---|---|---:|---:|---:|---|---|---|---|---|')
        for r in rows:
            L.append(f'| {r[0]} | {r[2]} | {r[3]} | {r[4]} | {inr(r[5])} | {inr(r[4] * r[5])} | {r[6]} | {r[7]} | {r[8]} | {r[9]} | {r[10]} |')
        L.append('')

    L.append(f'## SUTRA carrier board - per-puck cost (target Rs {B.PUCK_TARGET})\n')
    L.append('| ID | Item | Part number | Qty | Rs | Type | Vendor | L/I | Notes |')
    L.append('|---|---|---|---:|---:|---|---|---|---|')
    for (pid, item, mpn, q, u, t, ven, li, note) in puck_rows:
        L.append(f'| {pid} | {item} | {mpn} | {q} | {inr(q * u)} | {t} | {ven} | {li} | {note} |')
    L.append(f'| | **Per puck (as drawn, RFM95W)** | | | **{inr(puck_unit)}** | | | | |')
    L.append(f'| | Per puck, cost-down (Ra-01H + wire whip) | | | {inr(cd_unit)} | | | | |\n')
    over = puck_unit - B.PUCK_TARGET
    L.append(f'**Honest answer: the puck does not meet Rs {B.PUCK_TARGET}.** As drawn it is Rs {inr(puck_unit)} '
             f'(Rs {inr(over)} over); the RFM95W alone is Rs 819 ({819 * 100 // puck_unit} % of the puck). '
             f'Swapping to an Ai-Thinker Ra-01H (same SX1276, different 16-pad footprint) and a wire whip gives Rs {inr(cd_unit)}, still over. '
             'Rs 900 is only realistic at volume (100+ boards: LCSC module pricing, panelised PCB, bulk cells). '
             'Recommended baseline change: puck BOM target Rs 900 -> **Rs 1,250 for the Stage 3 prototype** (Ra-01H variant), Rs 900 kept as the volume target.\n')
    L.append(f'Ten PCBs are fabricated; seven are assembled ({B.PUCK_BOARDS} x per-puck cost above). The two base-station boards are identical carrier boards on the laptop USB, '
             'so the base ESP32-C3 node and base LoRa node need no separate parts.\n')
    L.append('## Gas package (outside core, as in the Ambetronics proposal)\n')
    L.append('| ID | Item | Part | Qty | Rs | Type | Vendor | Stock |')
    L.append('|---|---|---|---:|---:|---|---|---|')
    for r in B.GAS_OUTSIDE_CORE:
        L.append(f'| {r[0]} | {r[2]} | {r[3]} | {r[4]} | {inr(r[5])} | {r[6]} | {r[7]} | {r[9]} |')
    L.append('\nAmbetronics OEM electrochemical O2/CO/H2S + CH4 NDIR remains a separate quote / in-kind request.\n')
    L.append('## What changed from the Ambetronics (13 Sep 2026) BOM\n')
    L.append('| Old line | Item | Old Rs | Now |')
    L.append('|---|---|---:|---|')
    for r in B.REMOVED:
        L.append(f'| {r[0]} | {r[1]} | {inr(r[2])} | {r[3]} |')
    L.append('\nUnchanged and reused at the 13 Sep price: ESC (A6), battery (B1), charger (B2), Pixhawk 6C Mini (C1), FS-i6 (C2), Pi 5 (C4), '
             'cooler/SD (C5), STL-19P (D1), IMX327 (D2), MLX90640 (D3), lighting (D4), wiring/consumables (G1, G2).\n')
    L.append('## Supply risks (22 Oct 2026)\n')
    L.append('- Out of stock: Pixhawk 6C Mini, XRotor G2 4-in-1 (the new version now lists at Rs 11,269, +Rs 4,990 vs the reused price), RFM95W bare module, MTF-01, CF tube 1 m, XIAO ESP32C3 (pre-order).')
    L.append('- Not stocked in India: Pololu D36V50F5 (import), 850 nm star LEDs, 1 m GFRP rod (RFQ), exact 502030 JST-PH cell.')
    L.append('- Fallbacks: Matek H743-SLIM V3 for the FC (baseline fallback); T-Motor F55A Pro-class 4-in-1; LionCircuits RFM95W at Rs 2,423+; Ra-01H via LCSC.')
    open(os.path.join(EL, 'bom.md'), 'w').write('\n'.join(L) + '\n')
    print(f'vehicle {vehicle}  pucks {pucks} ({B.PUCK_BOARDS} x {puck_unit})  integ {integ}  core {core}  cont {cont:.0f}  total {total:.0f}  '
          f'costdown_total {cd_total:.0f}  puck_cd {cd_unit}  gas {gas}')
    return dict(vehicle=vehicle, pucks=pucks, puck_unit=puck_unit, puck_cd=cd_unit, integ=integ, core=core, cont=cont, total=total,
                cd_total=cd_total, gas=gas)


if __name__ == '__main__':
    main()
