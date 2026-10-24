"""Composite the raw Cycles renders (renders/_raw/*.png, RGBA) onto white and add labels/dimensions.

    python3 renders/annotate.py

Outputs (renders/): surang-hero.png, surang-exploded.png, surang-cutaway.png, sutra-puck-exploded.png,
surang-side-plan-dimensions.png (+ .svg), puck-exit-check.png (+ .svg)
All numbers drawn here come from cad/analysis.json and cad/mass-properties.json (design calculations).
"""
import json, os, math
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, FancyArrowPatch

ROOT = '/home/shubh/_Active_Projects/SURANG-SUTRA-VK26'
RAW = os.path.join(ROOT, 'renders', '_raw')
OUT = os.path.join(ROOT, 'renders')
A = json.load(open(os.path.join(ROOT, 'cad', 'analysis.json')))
M = json.load(open(os.path.join(ROOT, 'cad', 'mass-properties.json')))
MAN = json.load(open(os.path.join(ROOT, 'cad', 'mesh', 'manifest.json')))
P = MAN['params']

INK, SLATE, BLUE, GREEN, AMBER, RED, PANEL = '#0F172A', '#475569', '#1D4ED8', '#16A34A', '#D97706', '#DC2626', '#F0FDF4'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'text.color': INK, 'axes.edgecolor': SLATE,
                     'axes.labelcolor': INK, 'xtick.color': SLATE, 'ytick.color': SLATE})
FOOT = 'Design CAD render (Stage 2 target geometry). Not a photograph; nothing here is measured.'


def load(view):
    im = Image.open(os.path.join(RAW, f'{view}.png')).convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    meta = json.load(open(os.path.join(RAW, f'{view}.json')))
    return np.asarray(bg.convert('RGB')), meta


def canvas(img, extra_right=0, extra_top=0, extra_bottom=0):
    H, W = img.shape[:2]
    WW, HH = W + extra_right, H + extra_top + extra_bottom
    fig = plt.figure(figsize=(WW / 100, HH / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, WW); ax.set_ylim(HH, 0); ax.axis('off')
    ax.imshow(img, extent=[0, W, H + extra_top, extra_top], zorder=0)
    return fig, ax


def title(ax, x, y, t, sub=None, size=30):
    ax.text(x, y, t, fontsize=size, fontweight='bold', color=INK, va='top')
    if sub:
        ax.text(x, y + size * 1.75, sub, fontsize=size * 0.6, color=SLATE, va='top')


def foot(ax, W, H, text=FOOT, size=14):
    ax.text(W - 30, H - 24, text, fontsize=size, color=SLATE, ha='right', va='bottom')


# ------------------------------------------------------------------------------------------ (a) hero
def hero():
    img, meta = load('hero')
    H, W = img.shape[:2]
    fig, ax = canvas(img)
    title(ax, 60, 50, 'SURANG scout with SUTRA relay cassette',
          'Ø580 mm 2V geodesic roll-cage  ·  7-inch X quad, 295 mm diagonal  ·  5-puck SUTRA cassette', 34)
    tot = M['total_g'] / 1000
    ax.text(60, H - 70, f'CAD mass estimate {tot:.2f} kg (target ≤ 2.40 kg)  ·  prop-tip to cage clearance '
            f'{A["prop_clear_vs_inner_hull_mm"]:.0f} mm (target ≥ 20 mm)', fontsize=17, color=SLATE, va='bottom')
    foot(ax, W, H)
    fig.savefig(os.path.join(OUT, 'surang-hero.png'), dpi=100); plt.close(fig)


# ------------------------------------------------------------------------------------------ (b) exploded
def exploded():
    img, meta = load('exploded')
    H, W = img.shape[:2]
    TOP = 150
    fig, ax = canvas(img, extra_top=TOP)
    title(ax, 60, 36, 'SURANG-SUTRA exploded assembly',
          'Cage halves split along the axle (Y); stack lifted along Z; nose forward; cassette and pucks dropped', 32)
    # side: 'L' text left of the group box, 'R' right of it, 'T' above, 'B' below; extra (dx, dy) in px
    place = {
        'Geodesic cage, +Y half': ('B', 0, 10), 'Geodesic cage, -Y half': ('B', 0, 10),
        'Pole hub + 6800 bearing': ('B', 0, 6), '7-inch tri-blade props': ('L', -10, -30),
        '2809 motors': ('L', -10, 0), 'Carbon X frame + axle': ('L', -150, 40), 'Avionics deck': ('R', 10, 0),
        '4-in-1 ESC': ('R', 10, 0), 'Pixhawk 6C Mini': ('R', 10, -6), 'Pi 5 + cooler': ('R', 10, 0),
        '2D LiDAR': ('R', 10, 0), 'Camera + thermal + IR': ('R', 10, 0), 'Gas flow cell + pump': ('L', -10, 0),
        '6S 3300 mAh': ('R', 10, 0), 'Cassette + escapement': ('R', 12, 0), '5 SUTRA pucks': ('R', 12, 0),
    }
    rename = {'Geodesic cage, -Y half': 'Geodesic cage, −Y half (60 struts + hubs)',
              'Geodesic cage, +Y half': 'Geodesic cage, +Y half', '4-in-1 ESC': 'Avionics deck + 4-in-1 ESC'}
    absolute = {'Geodesic cage, +Y half': (2040, 1062, 'center'), 'Geodesic cage, -Y half': (672, 1236, 'center')}
    for k, v in meta['labels'].items():
        if k == 'Avionics deck':
            continue
        if k in absolute:
            x, y, ha = absolute[k]
            ax.text(x, y + TOP, rename.get(k, k), fontsize=17, color=INK, ha=ha, va='center',
                    bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.85))
            continue
        bx = np.array(v['box'])
        x0, x1, y0, y1 = bx[:, 0].min(), bx[:, 0].max(), bx[:, 1].min(), bx[:, 1].max()
        side, dx, dy = place.get(k, ('R', 10, 0))
        if side == 'L':
            x, y, ha, va = x0 + dx, (y0 + y1) / 2 + dy, 'right', 'center'
        elif side == 'R':
            x, y, ha, va = x1 + dx, (y0 + y1) / 2 + dy, 'left', 'center'
        elif side == 'T':
            x, y, ha, va = (x0 + x1) / 2 + dx, y0 - 8 + dy, 'center', 'bottom'
        else:
            x, y, ha, va = (x0 + x1) / 2 + dx, y1 + dy, 'center', 'top'
        ax.text(x, y + TOP, rename.get(k, k), fontsize=17, color=INK, ha=ha, va=va,
                bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.85))
    foot(ax, W, H + TOP)
    fig.savefig(os.path.join(OUT, 'surang-exploded.png'), dpi=100); plt.close(fig)
    return meta


# ------------------------------------------------------------------------------------------ callout helper
def callouts(ax, anchors, W, H, x_left, x_right, top, bottom, size=17, min_gap=64):
    """anchors: list of (label, (px, py)). Two columns of labels with leader lines."""
    left = sorted([a for a in anchors if a[1][0] < W / 2], key=lambda a: a[1][1])
    right = sorted([a for a in anchors if a[1][0] >= W / 2], key=lambda a: a[1][1])
    for col, x_txt, ha in ((left, x_left, 'right'), (right, x_right, 'left')):
        ys = [a[1][1] for a in col]
        # spread to min gap within [top, bottom]
        for i in range(len(ys)):
            ys[i] = max(ys[i], top if i == 0 else ys[i - 1] + min_gap)
        over = ys[-1] - bottom if ys else 0
        if over > 0:
            ys = [y - over for y in ys]
            for i in range(len(ys) - 2, -1, -1):
                ys[i] = min(ys[i], ys[i + 1] - min_gap)
        for (lab, (px, py)), y in zip(col, ys):
            ax.text(x_txt, y, lab, fontsize=size, color=INK, ha=ha, va='center')
            xe = x_txt + (12 if ha == 'right' else -12)
            ax.plot([xe, px], [y, py], color=SLATE, lw=1.3, zorder=5)
            ax.plot([px], [py], 'o', ms=6, color=BLUE, mec='white', mew=1.2, zorder=6)


# ------------------------------------------------------------------------------------------ (c) cutaway
def cutaway():
    img, meta = load('cutaway')
    H, W = img.shape[:2]
    fig, ax = canvas(img)
    title(ax, 60, 44, 'Cut-away: inner frame, core stack and cassette',
          'Near half of the geodesic cage removed. The inner frame hangs on the axle bearings and stays level while the cage rolls.', 34)
    anchors = [(k, tuple(v['px'])) for k, v in meta['labels'].items()]
    xs = [a[1][0] for a in anchors]
    callouts(ax, anchors, (min(xs) + max(xs)) if False else W, H, 760, W - 760, 230, H - 120, size=21, min_gap=86)
    foot(ax, W, H)
    fig.savefig(os.path.join(OUT, 'surang-cutaway.png'), dpi=100); plt.close(fig)


# ------------------------------------------------------------------------------------------ (d) puck
def puck():
    img, meta = load('puck')
    H, W = img.shape[:2]
    extra = 1150
    TOP = 170
    fig, ax = canvas(img, extra_right=extra, extra_top=TOP)
    WW = W + extra
    pm = M['single_puck_g']
    title(ax, 40, 36, 'SUTRA relay puck, exploded', None, 34)
    ax.text(40, 100, f'Ø56 × 20 mm  ·  target ≤ 30 g  ·  CAD estimate {pm:.1f} g (bought parts at catalogue mass)',
            fontsize=20, color=SLATE, va='top')
    names = {
        'Puck_AprilTag': '30 mm AprilTag 36h11 label (pattern shown is a placeholder)',
        'Puck_Shell_Lid': 'PETG domed lid: tag landing + LED light pipe',
        'Puck_Bumper_TPU': 'TPU 95A bumper ring (also the escapement pinch surface)',
        'Puck_ESP32C3_MINI1': 'ESP32-C3-MINI-1 (Wi-Fi / ESP-NOW-LR relay)',
        'Puck_RFM95W_868': 'RFM95W-868 LoRa (865–867 MHz lifeline)',
        'Puck_Antenna_Stub': '868 MHz helical antenna stub',
        'Puck_PCB': 'PCB Ø48 × 1.6: MCP73831, AP2112K-3.3, DRV5032 hall wake',
        'Puck_Passives_LED_Hall': 'Charger, LDO, hall sensor, status LED',
        'Puck_LiPo_1S_400': '1S 400 mAh LiPo, lowest item (low CG)',
        'Puck_Shell_Base': 'PETG base cup (1.4 mm wall)',
        'Puck_ChargePads': 'Charge pads (contacts in the cassette)',
    }
    anchors = []
    for k, lab in names.items():
        v = meta['labels'].get(k)
        if not v:
            continue
        anchors.append((lab, (v['px'][0], v['px'][1] + TOP)))
    anchors.sort(key=lambda a: a[1][1])
    ys = [a[1][1] for a in anchors]
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + 74)
    for (lab, (px, py)), y in zip(anchors, ys):
        ax.text(W + 120, y, lab, fontsize=20, color=INK, va='center')
        ax.plot([W + 108, W + 20, px], [y, y, py], color=SLATE, lw=1.3)
        ax.plot([px], [py], 'o', ms=7, color=BLUE, mec='white', mew=1.2)
    cg = M['puck_cg_local_mm']
    ax.text(40, H + TOP - 40, f'Puck CG {cg[2]:.1f} mm above the base (calculated).\n'
            f'Dome radius {M["puck_dome_radius_mm"]:.0f} mm, so an upside-down landing is statically stable:\n'
            'the dome alone does not self-right. Tag + radio work either way up is the safer fix.',
            fontsize=17, color=SLATE, va='bottom', linespacing=1.5)
    foot(ax, WW, H + TOP)
    fig.savefig(os.path.join(OUT, 'sutra-puck-exploded.png'), dpi=100); plt.close(fig)


# ------------------------------------------------------------------------------------------ dimension helpers
def dim(ax, p0, p1, text, off=(0, 0), color=INK, fs=11, tpos=0.5, rot=None, ext=True):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    o = np.array(off, float)
    a, b = p0 + o, p1 + o
    if ext and np.linalg.norm(o) > 0:
        for p, q in ((p0, a), (p1, b)):
            u = (q - p) / np.linalg.norm(q - p)
            ax.plot([p[0] + u[0] * 4, q[0] + u[0] * 6], [p[1] + u[1] * 4, q[1] + u[1] * 6], color=color, lw=0.8)
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='<|-|>', mutation_scale=11, color=color, lw=1.1, shrinkA=0, shrinkB=0))
    m = a + (b - a) * tpos
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) if rot is None else rot
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    ax.text(m[0], m[1], text, fontsize=fs, color=color, ha='center', va='center', rotation=ang,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.92), zorder=8)


def ortho_ax(ax, view, flip_y=False):
    img, meta = load(view)
    s = meta['ortho']['scale'] * 1000
    cx, cz = [c * 1000 for c in meta['ortho']['centre']]
    ext = [cx - s / 2, cx + s / 2, cz - s / 2, cz + s / 2]
    ax.imshow(img, extent=ext, zorder=0)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect('equal'); ax.axis('off')
    return meta


# ------------------------------------------------------------------------------------------ (e) side + plan
def side_plan():
    fig = plt.figure(figsize=(17, 9.6), dpi=170)
    a1 = fig.add_axes([0.005, 0.03, 0.49, 0.83]); a2 = fig.add_axes([0.505, 0.03, 0.49, 0.83])
    fig.text(0.015, 0.975, 'SURANG key dimensions and clearances', fontsize=20, fontweight='bold', va='top')
    fig.text(0.015, 0.937, 'Orthographic CAD views at the cage rest pose (two equator hubs on the floor). Millimetres. '
             'All values are design targets or calculations.', fontsize=11.5, color=SLATE, va='top')
    fig.text(0.02, 0.885, 'SIDE  (section at y = 0, looking +Y; nose to the right)', fontsize=12.5, fontweight='bold')
    fig.text(0.52, 0.885, 'PLAN  (cage above the rotor plane removed; nose to the right)', fontsize=12.5, fontweight='bold')
    R = P['cage_R']; hull = A['cage_inner_hull_min_mm']; tipR = A['prop_tip_envelope_plan_mm']
    pz = P['prop_z']; floor = -(R + P['hub_h'] / 2 + P['cap_h']) * math.cos(math.radians(18))
    ze = P['cassette_exit_z']; cg = M['cg_mm']; icg = M['inner_cg_mm']
    box = dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.92)
    # ---- side
    ortho_ax(a1, 'side')
    a1.add_patch(Circle((0, 0), hull, fill=False, ls=(0, (6, 4)), lw=1.2, color=BLUE, zorder=4))
    dim(a1, (-R, 0), (R, 0), f'Ø{2 * R:.0f} hub-centre sphere  (Ø{2 * (R + P["hub_h"] / 2 + P["cap_h"]):.0f} over TPU caps)',
        off=(0, 268), fs=11)
    a1.plot([-340, 340], [0, 0], color=SLATE, lw=0.8, ls=(0, (10, 3, 2, 3)), zorder=3)
    xt = 104.3 + 88.9
    a1.plot([-xt, xt], [pz, pz], color=AMBER, lw=2.4, zorder=5)
    dim(a1, (-xt, pz), (xt, pz), f'rotor plane z = +{pz:.0f}; prop span {2 * xt:.0f} in this view', off=(0, 92), fs=10,
        color=AMBER)
    a1.plot([-345, 345], [floor, floor], color=INK, lw=1.4)
    a1.text(-340, floor - 7, f'floor: rest on 2 equator TPU caps, axle {-floor:.0f} above it', fontsize=9.5, va='top')
    for sx in (-1, 1):
        a1.plot([sx * 28, sx * 28], [ze, floor + 2], color=GREEN, lw=1.4, ls=(0, (5, 3)), zorder=6)
    a1.add_patch(FancyArrowPatch((0, ze - 10), (0, floor + 30), arrowstyle='-|>', mutation_scale=16, color=GREEN, lw=1.6, zorder=6))
    a1.annotate('puck exit path, Ø56\n(cassette at y = +54,\nbehind the section)', xy=(28, -215), xytext=(150, -235),
                fontsize=9.5, color=GREEN, va='center', bbox=box, zorder=9,
                arrowprops=dict(arrowstyle='-', color=GREEN, lw=1))
    a1.plot([0], [cg[2]], marker='o', ms=10, mfc='white', mec=RED, mew=2, zorder=9)
    a1.plot([0], [cg[2]], marker='+', ms=10, color=RED, mew=1.6, zorder=10)
    a1.annotate(f'CG z = {cg[2]:.1f} (all-up)\nhanging core CG {-icg[2]:.1f} below the axle\naxle centreline z = 0',
                xy=(0, cg[2]), xytext=(-345, -150), fontsize=9.5, color=RED, va='center', bbox=box, zorder=9,
                arrowprops=dict(arrowstyle='-', color=RED, lw=1))
    a1.annotate(f'inner hull R{hull:.1f}\n(face planes − rod radius)', xy=(-hull * 0.766, hull * 0.643), xytext=(-345, 238),
                fontsize=9.5, color=BLUE, va='center', bbox=box, zorder=9, arrowprops=dict(arrowstyle='-', color=BLUE, lw=1))
    a1.annotate('LiDAR top z = +101', xy=(0, 101), xytext=(-75, 185), fontsize=9.5, color=INK, bbox=box, zorder=9,
                arrowprops=dict(arrowstyle='-', color=SLATE, lw=1))
    # ---- plan
    ortho_ax(a2, 'plan')
    a2.add_patch(Circle((0, 0), tipR, fill=False, ls=(0, (6, 4)), lw=1.4, color=AMBER, zorder=4))
    a2.add_patch(Circle((0, 0), hull, fill=False, ls=(0, (6, 4)), lw=1.4, color=BLUE, zorder=4))
    c = 104.3
    dim(a2, (-c, -c), (c, c), f'{P["frame_diag"]:.0f} motor-to-motor', fs=10.5, tpos=0.30)
    ang = math.radians(-58); u = np.array([math.cos(ang), math.sin(ang)])
    dim(a2, (0, 0), u * tipR, f'R{tipR:.1f} prop-tip envelope', fs=10, color=AMBER, tpos=0.58, ext=False)
    ang2 = math.radians(-30); u2 = np.array([math.cos(ang2), math.sin(ang2)])
    a2.add_patch(FancyArrowPatch(u2 * tipR, u2 * hull, arrowstyle='<|-|>', mutation_scale=10, color=GREEN, lw=1.6, zorder=8))
    sw = min(r['min_clear_to_rod_or_hub_mm'] for r in A['prop_clear_swept_rods_hubs'])
    a2.annotate(f'prop-tip clearance\n{A["prop_clear_vs_inner_hull_mm"]:.1f} to the inner hull\n'
                f'{sw:.1f} to the nearest rod/hub\nat any cage roll angle\n(target ≥ 20)', xy=u2 * (tipR + hull) / 2,
                xytext=(345, -262), fontsize=10, color=GREEN, va='center', ha='right', bbox=box, zorder=9,
                arrowprops=dict(arrowstyle='-', color=GREEN, lw=1))
    a2.annotate(f'inner hull R{hull:.1f}', xy=(-hull * 0.643, hull * 0.766), xytext=(-345, 300), fontsize=10, color=BLUE,
                bbox=box, zorder=9, arrowprops=dict(arrowstyle='-', color=BLUE, lw=1))
    y0 = P['cassette_y']
    a2.add_patch(Circle((0, y0), P['puck_d'] / 2, fill=False, lw=1.6, ls=(0, (4, 3)), color=GREEN, zorder=6))
    a2.annotate('cassette / puck exit Ø56\nat y = +54 (under the deck)', xy=(-20, y0 + 20), xytext=(-345, 205),
                fontsize=9.5, color=GREEN, bbox=box, zorder=9, va='center', arrowprops=dict(arrowstyle='-', color=GREEN, lw=1))
    a2.annotate('axle (Y)', xy=(0, 230), xytext=(40, 255), fontsize=10, color=SLATE, bbox=box, zorder=9,
                arrowprops=dict(arrowstyle='-', color=SLATE, lw=1))
    a2.annotate('gas inlet tip', xy=(219, -40), xytext=(170, -118), fontsize=9.5, color=AMBER, bbox=box, zorder=9,
                arrowprops=dict(arrowstyle='-', color=AMBER, lw=1))
    fig.text(0.985, 0.012, FOOT, fontsize=9, color=SLATE, ha='right')
    for ext in ('png', 'svg'):
        fig.savefig(os.path.join(OUT, f'surang-side-plan-dimensions.{ext}'), dpi=170)
    plt.close(fig)


# ------------------------------------------------------------------------------------------ (f) puck exit check
def exit_check():
    fig = plt.figure(figsize=(17, 8.8), dpi=170)
    a1 = fig.add_axes([0.0, 0.03, 0.46, 0.82]); a2 = fig.add_axes([0.54, 0.19, 0.43, 0.62])
    fig.text(0.015, 0.975, 'Puck exit path through the cage', fontsize=20, fontweight='bold', va='top')
    fig.text(0.015, 0.935, 'A centred drop line (y = 0) always lands on the equatorial strut ring, so the cassette is '
             'offset along the axle to y = +54 mm, under an open face.', fontsize=11.5, color=SLATE, va='top')
    fig.text(0.02, 0.875, 'BOTTOM VIEW  (looking up, rest pose; cage above z = −150 hidden)', fontsize=12, fontweight='bold')
    img, meta = load('bottom')
    s = meta['ortho']['scale'] * 1000
    a1.imshow(img, extent=[-s / 2, s / 2, -s / 2, s / 2], zorder=0)
    a1.set_xlim(-s / 2, s / 2); a1.set_ylim(-s / 2, s / 2); a1.set_aspect('equal'); a1.axis('off')
    hubs = np.array(MAN['hub_xyz'])
    y0 = P['cassette_y']; pr = P['puck_d'] / 2
    d = A['puck_drop_cassette']
    box = dict(boxstyle='round,pad=0.3', fc='white', ec='none', alpha=0.92)
    face = [h for h in hubs if h[2] < -240 and h[1] > -1]
    if len(face) >= 3:
        pts = np.array([[h[0], -h[1]] for h in face[:3]])
        a1.add_patch(Polygon(pts, closed=True, fc=GREEN, alpha=0.12, ec=GREEN, lw=1.5, zorder=3))
    a1.add_patch(Circle((0, -y0), pr, fc='none', ec=GREEN, lw=2.2, zorder=7))
    a1.add_patch(Circle((0, -y0), pr + d['max_gap_mm'], fc='none', ec=GREEN, lw=1.2, ls=(0, (5, 3)), zorder=7))
    a1.annotate(f'puck Ø56 at y = +{y0:.0f}:\n{d["max_gap_mm"]:.1f} mm radial margin\nat this rest pose',
                xy=(pr * 0.7, -y0 - pr * 0.7), xytext=(130, -250), fontsize=10.5, color=GREEN, va='center', bbox=box,
                zorder=9, arrowprops=dict(arrowstyle='-', color=GREEN, lw=1))
    a1.add_patch(Circle((0, 0), pr, fc='none', ec=RED, lw=1.8, ls=(0, (4, 3)), zorder=7))
    a1.annotate('centred drop (y = 0) is\nblocked by the equator\nstrut ring at every angle', xy=(-pr * 0.7, pr * 0.7),
                xytext=(-335, 200), fontsize=10.5, color=RED, va='center', bbox=box, zorder=9,
                arrowprops=dict(arrowstyle='-', color=RED, lw=1))
    a1.annotate('open face (green)', xy=(-40, -110), xytext=(-335, -200), fontsize=10.5, color=GREEN, va='center',
                bbox=box, zorder=9, arrowprops=dict(arrowstyle='-', color=GREEN, lw=1))
    a1.text(-335, -300, 'image up = −Y, right = +X (nose)', fontsize=9.5, color=SLATE)
    th = np.array(A['gap_curve']['theta_deg'])
    g0 = np.array(A['gap_curve']['y0_0']); g1 = np.array(A['gap_curve']['y0_cassette'])
    TH = np.concatenate([th + 72 * k for k in range(5)]); G0 = np.tile(g0, 5); G1 = np.tile(g1, 5)
    a2.axhspan(-60, 0, color=RED, alpha=0.05, lw=0)
    a2.axhline(0, color=INK, lw=1)
    a2.axhline(3, color=GREEN, lw=0.8, ls=(0, (4, 3)))
    a2.fill_between(TH, 0, G1, where=G1 >= 0, color=GREEN, alpha=0.18, lw=0)
    a2.plot(TH, G1, color=GREEN, lw=1.8, label=f'cassette at y = +{y0:.0f} mm (this design)')
    a2.plot(TH, G0, color=RED, lw=1.8, label='centred drop, y = 0')
    for k in range(10):
        a2.axvline(18 + 36 * k, color=SLATE, lw=0.7, ls=':')
    a2.set_xlim(0, 360); a2.set_ylim(-50, 26)
    a2.set_xticks(range(0, 361, 36))
    a2.set_xlabel('cage roll angle about the axle (deg); dotted = floor rest poses', fontsize=11.5)
    a2.set_ylabel('radial margin around the Ø56 puck (mm)', fontsize=11.5)
    a2.legend(loc='lower right', fontsize=10.5, frameon=False)
    for sp in ('top', 'right'):
        a2.spines[sp].set_visible(False)
    a2.text(0, 29, f'Open with ≥ 3 mm margin for {d["open_deg_per_72_margin3"] * 5:.0f}° of each turn (10 windows).\n'
            f'Every rest pose sits inside a window: {d["gap_at_rest_poses_mm"][0]:.1f} or '
            f'{d["gap_at_rest_poses_mm"][1]:.1f} mm margin.', fontsize=11, color=INK, va='bottom')
    fig.text(0.54, 0.03, 'Release rule: drop while perched (cage at rest), or in flight only when a cage-angle sensor\n'
             'reads inside a window. A 20 mm puck under the cage would be struck if the cage rolled over it\n'
             f'(calculated interference {-A["rollover"]["clear_mm"]:.0f} mm), so hop in fly mode before rolling on.',
             fontsize=10.5, color=SLATE, va='bottom', linespacing=1.45)
    for ext in ('png', 'svg'):
        fig.savefig(os.path.join(OUT, f'puck-exit-check.{ext}'), dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    import sys
    todo = sys.argv[1:] or ['hero', 'exploded', 'cutaway', 'puck', 'side_plan', 'exit_check']
    for t in todo:
        globals()[t]()
        print('done', t)
