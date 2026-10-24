"""SURANG-SUTRA Stage 2 (VK26) parametric CAD model.

Run headless (from anywhere):
    freecadcmd -c "exec(open('/home/shubh/_Active_Projects/SURANG-SUTRA-VK26/cad/build_surang.py').read())"

Produces (all inside cad/):
    SURANG-SUTRA.FCStd            model with 'Params' spreadsheet + named feature tree
    step/*.step                   assembly + per-part STEP
    stl/*.stl                     printable parts (hubs, pole hub, TPU caps, puck shell)
    mesh/assembly.obj, mesh/puck.obj, mesh/manifest.json   per-part meshes for renders/render.py
    mass-properties.json          raw numbers for mass-properties.md (written by this script too)

Axes: origin = cage centre = axle centreline. X forward (nose), Y along the axle (left), Z up.
Everything is a design target / calculation. Nothing here is measured.
"""
import os, sys, math, json, time, importlib
import FreeCAD as App
import Part, Sketcher, Import, Mesh, MeshPart

V = App.Vector
CAD = '/home/shubh/_Active_Projects/SURANG-SUTRA-VK26/cad'
sys.path.insert(0, CAD)
import params, geodesic
importlib.reload(params); importlib.reload(geodesic)
from params import P
from geodesic import geodesic_2v

T0 = time.time()
def log(*a):
    print('[build %5.1fs]' % (time.time() - T0), *a, flush=True)

for d in ('step', 'stl', 'mesh'):
    os.makedirs(os.path.join(CAD, d), exist_ok=True)

DENS = {'GFRP': 2.0, 'CF': 1.6, 'PA12': 1.0, 'PETG': 1.27, 'TPU': 1.2,
        'Al': 2.7, 'Steel': 7.85, 'FR4': 1.85, 'PTFE': 2.2}

if App.listDocuments().get('SURANG_SUTRA'):
    App.closeDocument('SURANG_SUTRA')
doc = App.newDocument('SURANG_SUTRA')

# ---------------------------------------------------------------------------------------------
# Parameter spreadsheet
# ---------------------------------------------------------------------------------------------
SS_ROWS = [
    ('cage_R', P['cage_R'], 'mm', 'Hub-centre sphere radius (cage Ø580)'),
    ('cage_phase', P['cage_phase'], 'deg', 'Cage roll angle used in the model (rest pose); build-time'),
    ('strut_d', P['strut_d'], 'mm', 'Pultruded GFRP strut rod diameter'),
    ('hub_d', P['hub_d'], 'mm', 'Printed hub diameter'),
    ('hub_h', P['hub_h'], 'mm', 'Printed hub height (radial)'),
    ('cap_h', P['cap_h'], 'mm', 'TPU 95A bumper cap dome height'),
    ('socket_depth', P['socket_depth'], 'mm', 'Strut socket depth in hub'),
    ('pole_hub_d', P['pole_hub_d'], 'mm', 'Axle pole hub diameter'),
    ('pole_hub_h', P['pole_hub_h'], 'mm', 'Axle pole hub length'),
    ('bearing_od', P['bearing_od'], 'mm', '6800-2RS OD'),
    ('bearing_w', P['bearing_w'], 'mm', '6800-2RS width'),
    ('axle_od', P['axle_od'], 'mm', 'Carbon axle tube OD'),
    ('axle_id', P['axle_id'], 'mm', 'Carbon axle tube ID'),
    ('axle_clamp_y', P['axle_clamp_y'], 'mm', 'Axle clamp block offset from centre'),
    ('frame_diag', P['frame_diag'], 'mm', 'Motor-to-motor diagonal (7-inch X)'),
    ('arm_w', P['arm_w'], 'mm', 'Carbon arm width'),
    ('arm_t', P['arm_t'], 'mm', 'Carbon arm thickness'),
    ('plate_t', P['plate_t'], 'mm', 'Carbon stack plate thickness'),
    ('plate_w', P['plate_w'], 'mm', 'Sandwich plate size (square)'),
    ('plate_bot_z', P['plate_bot_z'], 'mm', 'Underside of bottom plate (axle at z=0)'),
    ('deck_z', P['deck_z'], 'mm', 'Underside of avionics deck'),
    ('motor_d', P['motor_d'], 'mm', '2809-class motor bell diameter'),
    ('motor_h', P['motor_h'], 'mm', 'Motor height'),
    ('prop_d', P['prop_d'], 'mm', '7-inch prop diameter'),
    ('prop_hub_h', P['prop_hub_h'], 'mm', 'Prop hub height'),
    ('prop_z', '=plate_bot_z + plate_t + arm_t + motor_h + prop_hub_h / 2', 'mm', 'Rotor plane height (derived)'),
    ('batt_l', P['batt_l'], 'mm', '6S 3300 mAh pack length'),
    ('batt_w', P['batt_w'], 'mm', 'pack width'),
    ('batt_h', P['batt_h'], 'mm', 'pack height'),
    ('batt_x', P['batt_x'], 'mm', 'Battery fore-aft position (set by CG balance)'),
    ('puck_d', P['puck_d'], 'mm', 'SUTRA puck diameter over TPU bumper'),
    ('puck_h', P['puck_h'], 'mm', 'SUTRA puck height'),
    ('puck_shell_d', P['puck_shell_d'], 'mm', 'PETG shell diameter'),
    ('tube_wall', P['tube_wall'], 'mm', 'Cassette tube wall'),
    ('tube_clear', P['tube_clear'], 'mm', 'Radial puck clearance in tube'),
    ('cassette_y', P['cassette_y'], 'mm', 'Cassette axis offset along +Y (puck exit window)'),
    ('cassette_top_z', P['cassette_top_z'], 'mm', 'Top of cassette tube'),
    ('cassette_len', P['cassette_len'], 'mm', 'Cassette tube length'),
    ('cassette_exit_z', '=cassette_top_z - cassette_len', 'mm', 'Tube exit plane (derived)'),
]
ss = doc.addObject('Spreadsheet::Sheet', 'Params')
ss.Label = 'Params'
for col, h in zip('ABCD', ('Parameter', 'Value', 'Unit', 'Note')):
    ss.set(f'{col}1', h)
for i, (a, v, u, n) in enumerate(SS_ROWS, start=2):
    ss.set(f'A{i}', a); ss.set(f'B{i}', str(v)); ss.setAlias(f'B{i}', a)
    ss.set(f'C{i}', u); ss.set(f'D{i}', n)
doc.recompute()
S0 = 'Params.hub_d / 2 - Params.socket_depth'          # strut start offset from a hub centre
S0P = 'Params.pole_hub_d / 2 - Params.socket_depth'    # ... from a pole hub centre

# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def meta(o, material, source='CAD', cat_g=None, note=''):
    for nm, typ, val in (('SurangMaterial', 'App::PropertyString', material),
                         ('MassSource', 'App::PropertyString', source),
                         ('SurangNote', 'App::PropertyString', note)):
        if nm not in o.PropertiesList:
            o.addProperty(typ, nm, 'SURANG')
        setattr(o, nm, val)
    if cat_g is not None:
        if 'CatalogueMass_g' not in o.PropertiesList:
            o.addProperty('App::PropertyFloat', 'CatalogueMass_g', 'SURANG')
        o.CatalogueMass_g = float(cat_g)
    return o


def origin_feat(body, role):
    return [f for f in body.Origin.OriginFeatures if f.Role == role][0]


def new_sketch(body, name, role='XY_Plane', z=0.0):
    sk = body.newObject('Sketcher::SketchObject', name)
    sk.AttachmentSupport = [(origin_feat(body, role), '')]
    sk.MapMode = 'FlatFace'
    if z:
        sk.AttachmentOffset = App.Placement(V(0, 0, z), App.Rotation())
    return sk


def _join(sk, ids):
    """coincident-constrain consecutive geometry endpoints (closest pair) of a closed loop"""
    for k in range(len(ids)):
        a, b = ids[k], ids[(k + 1) % len(ids)]
        best = None
        for pa in (1, 2):
            for pb in (1, 2):
                d = (sk.getPoint(a, pa) - sk.getPoint(b, pb)).Length
                if best is None or d < best[0]:
                    best = (d, pa, pb)
        sk.addConstraint(Sketcher.Constraint('Coincident', a, best[1], b, best[2]))


def sk_poly(sk, pts):
    ids = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        ids.append(sk.addGeometry(Part.LineSegment(V(a[0], a[1], 0), V(b[0], b[1], 0))))
    _join(sk, ids)
    return ids


def sk_circle(sk, cx, cy, r, name=None, expr=None):
    g = sk.addGeometry(Part.Circle(V(cx, cy, 0), V(0, 0, 1), r))
    if name:
        c = sk.addConstraint(Sketcher.Constraint('Diameter', g, 2 * r))
        sk.renameConstraint(c, name)
        if expr:
            sk.setExpression(f'Constraints.{name}', expr)
    return g


def sk_rrect(sk, cx, cy, w, h, r):
    """rounded rectangle centred at (cx, cy)"""
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    ids = [
        sk.addGeometry(Part.LineSegment(V(x0 + r, y0, 0), V(x1 - r, y0, 0))),
        sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(x1 - r, y0 + r, 0), V(0, 0, 1), r), -math.pi / 2, 0)),
        sk.addGeometry(Part.LineSegment(V(x1, y0 + r, 0), V(x1, y1 - r, 0))),
        sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(x1 - r, y1 - r, 0), V(0, 0, 1), r), 0, math.pi / 2)),
        sk.addGeometry(Part.LineSegment(V(x1 - r, y1, 0), V(x0 + r, y1, 0))),
        sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(x0 + r, y1 - r, 0), V(0, 0, 1), r), math.pi / 2, math.pi)),
        sk.addGeometry(Part.LineSegment(V(x0, y1 - r, 0), V(x0, y0 + r, 0))),
        sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(x0 + r, y0 + r, 0), V(0, 0, 1), r), math.pi, 1.5 * math.pi)),
    ]
    _join(sk, ids)
    return ids


def sk_profile(sk, segs):
    """segs: ('L',(x,y),(x,y)) or ('A',(cx,cy),r,a0,a1) - closed loop, joined by proximity"""
    ids = []
    for s in segs:
        if s[0] == 'L':
            ids.append(sk.addGeometry(Part.LineSegment(V(*s[1], 0), V(*s[2], 0))))
        else:
            ids.append(sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(*s[1], 0), V(0, 0, 1), s[2]), s[3], s[4])))
    _join(sk, ids)
    return ids


def pad(body, sk, name, length, sym=False, rev=False, expr=None):
    p = body.newObject('PartDesign::Pad', name)
    p.Profile = sk
    p.Length = length
    if sym:
        p.SideType = 'Symmetric'
    p.Reversed = rev
    if expr:
        p.setExpression('Length', expr)
    sk.Visibility = False
    return p


def pocket_through(body, sk, name):
    p = body.newObject('PartDesign::Pocket', name)
    p.Profile = sk
    p.Type = 'ThroughAll'
    p.SideType = 'Symmetric'
    sk.Visibility = False
    return p


def revolve(body, sk, name):
    r = body.newObject('PartDesign::Revolution', name)
    r.Profile = sk
    r.ReferenceAxis = (sk, ['V_Axis'])
    r.Angle = 360
    sk.Visibility = False
    return r


def prim(body, typ, name, plc=None, **kw):
    o = body.newObject('PartDesign::' + typ, name)
    for k, v in kw.items():
        setattr(o, k, v)
    if plc is not None:
        o.Placement = plc
    return o


def rot_z_to(d):
    return App.Rotation(V(0, 0, 1), d)


def feature(name, shape, parent, material, source='catalogue', cat_g=None, note='', plc=None):
    o = doc.addObject('Part::Feature', name)
    o.Shape = shape
    if plc is not None:
        o.Placement = plc
    meta(o, material, source, cat_g, note)
    parent.addObject(o)
    return o


def link(name, target, parent, plc=App.Placement()):
    l = doc.addObject('App::Link', name)
    l.LinkedObject = target
    l.Placement = plc
    parent.addObject(l)
    return l


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, h, base=(0, 0, 0), d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*base), V(*d))


def finish(body, tip=None):
    if tip is not None:
        body.Tip = tip
    return body


# ---------------------------------------------------------------------------------------------
# containers
# ---------------------------------------------------------------------------------------------
LIB = doc.addObject('App::DocumentObjectGroup', 'Part_Library')
LIB.Label = 'Part_Library (masters, hidden)'
ASM = doc.addObject('App::Part', 'SURANG_SUTRA_Assembly')
CAGE = doc.addObject('App::Part', 'Cage'); ASM.addObject(CAGE)
G_STRUT = doc.addObject('App::DocumentObjectGroup', 'Cage_Struts_GFRP'); CAGE.addObject(G_STRUT)
G_HUB = doc.addObject('App::DocumentObjectGroup', 'Cage_Hubs_PA12'); CAGE.addObject(G_HUB)
G_CAP = doc.addObject('App::DocumentObjectGroup', 'Cage_Caps_TPU'); CAGE.addObject(G_CAP)
G_POLE = doc.addObject('App::DocumentObjectGroup', 'Cage_PoleHubs_Bearings'); CAGE.addObject(G_POLE)
FRAME = doc.addObject('App::Part', 'Frame'); ASM.addObject(FRAME)
PROP = doc.addObject('App::Part', 'Propulsion'); ASM.addObject(PROP)
CORE = doc.addObject('App::Part', 'Core_Stack'); ASM.addObject(CORE)
SENS = doc.addObject('App::Part', 'Sensor_Spine'); ASM.addObject(SENS)
CASS = doc.addObject('App::Part', 'Cassette'); ASM.addObject(CASS)
HELP = doc.addObject('App::DocumentObjectGroup', 'Render_Helpers')
HELP.Label = 'Render_Helpers (not in assembly/mass)'

# ---------------------------------------------------------------------------------------------
# geodesic geometry
# ---------------------------------------------------------------------------------------------
R = P['cage_R']
hubs_u, struts, faces, kind = geodesic_2v(1.0, P['cage_phase'])
U = [V(*h) for h in hubs_u]
POLES = (0, 11)  # +Y, -Y (see geodesic.icosahedron)
assert abs(U[0].y - 1) < 1e-9 and abs(U[11].y + 1) < 1e-9
NB = {i: [] for i in range(len(U))}
for i, j in struts:
    NB[i].append(j); NB[j].append(i)


def local_frame(i):
    n = V(U[i]); n.normalize()
    if kind[i] == 'M':
        j0 = [j for j in NB[i] if kind[j] == 'V'][0]
    else:
        j0 = sorted(NB[i])[0]
    d0 = U[j0] - U[i]
    t = d0 - n * n.dot(d0); t.normalize()
    ey = n.cross(t)
    m = App.Matrix(t.x, ey.x, n.x, 0, t.y, ey.y, n.y, 0, t.z, ey.z, n.z, 0, 0, 0, 0, 1)
    dirs = []
    for j in NB[i]:
        d = U[j] - U[i]; d.normalize()
        dirs.append(V(d.dot(t), d.dot(ey), d.dot(n)))
    dirs.sort(key=lambda v: (math.atan2(v.y, v.x) + 1e-6) % (2 * math.pi))
    return n, App.Placement(m).Rotation, dirs


REP = {}
for i in range(len(U)):
    if i in POLES:
        continue
    _, _, dirs = local_frame(i)
    k = kind[i]
    if k not in REP:
        REP[k] = dirs
    else:  # all hubs of a kind are congruent - verify
        dev = max(math.degrees(a.getAngle(b)) for a, b in zip(REP[k], dirs))
        assert dev < 0.05, (i, dev)
_, _, POLE_DIRS = local_frame(0)
log('hub kinds', {k: len(v) for k, v in REP.items()}, 'socket dips M:',
    sorted(set(round(math.degrees(math.asin(-d.z)), 2) for d in REP['M'])),
    'V:', sorted(set(round(math.degrees(math.asin(-d.z)), 2) for d in REP['V'])))

# ---------------------------------------------------------------------------------------------
# Library: cage hubs, caps, pole hub
# ---------------------------------------------------------------------------------------------
def make_hub(name, dirs, polar=False, sfx=''):
    b = doc.addObject('PartDesign::Body', name); LIB.addObject(b)
    sk = new_sketch(b, f'Sketch_{name}_Profile')
    sk_circle(sk, 0, 0, P['hub_d'] / 2, 'hub_dia', 'Params.hub_d')
    sk.addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))
    pd = pad(b, sk, f'Pad_HubBody{sfx}', P['hub_h'], sym=True, expr='Params.hub_h')
    seat = prim(b, 'SubtractiveCylinder', f'Pocket_CapSeat{sfx}', App.Placement(V(0, 0, P['hub_h'] / 2 - 3.5), App.Rotation()),
                Radius=3.1, Height=4.0)
    tip = seat
    s0 = P['hub_d'] / 2 - P['socket_depth']
    use = dirs[:1] if polar else dirs
    socks = []
    for k, d in enumerate(use):
        sc = prim(b, 'SubtractiveCylinder', f'Socket{sfx}_{k + 1}', App.Placement(d * s0, rot_z_to(d)),
                  Radius=P['strut_d'] / 2 + 0.05, Height=P['socket_depth'] + 4)
        sc.setExpression('Radius', 'Params.strut_d / 2 + 0.05')
        socks.append(sc); tip = sc
    if polar:
        pp = b.newObject('PartDesign::PolarPattern', f'PolarPattern_Sockets{sfx}')
        pp.Originals = socks
        pp.Axis = (sk, ['N_Axis'])
        pp.Occurrences = len(dirs)
        tip = pp
    finish(b, tip)
    meta(b, 'PA12', 'CAD', note='MJF PA12 (or PETG) printed hub, axis radial; rod sockets drilled toward hub centre')
    return b


HUB_M = make_hub('CageHub_M6', REP['M'], sfx='_M6')
HUB_V = make_hub('CageHub_V5', REP['V'], polar=True, sfx='_V5')


def make_cap(name, rbase, h, spig_r, spig_h, sfx):
    b = doc.addObject('PartDesign::Body', name); LIB.addObject(b)
    sk = new_sketch(b, f'Sketch_{name}_Profile', 'XZ_Plane')
    rho = (rbase ** 2 + h ** 2) / (2 * h)
    a0 = math.atan2(rho - h, rbase)
    sk_profile(sk, [('L', (0, -spig_h), (spig_r, -spig_h)), ('L', (spig_r, -spig_h), (spig_r, 0)),
                    ('L', (spig_r, 0), (rbase, 0)), ('A', (0, h - rho), rho, a0, math.pi / 2),
                    ('L', (0, h), (0, -spig_h))])
    rv = revolve(b, sk, f'Revolution_Dome{sfx}')
    finish(b, rv)
    meta(b, 'TPU', 'CAD', note='TPU 95A bumper cap, press-fit spigot')
    return b


CAP = make_cap('CageHub_TPUCap', P['hub_d'] / 2, P['cap_h'], 3.0, 3.0, '_HubCap')
POLECAP = make_cap('PoleHub_TPUCap', P['pole_hub_d'] / 2, P['pole_cap_h'], 6.8, 4.0, '_PoleCap')

# pole hub
PH = doc.addObject('PartDesign::Body', 'PoleHub'); LIB.addObject(PH)
sk = new_sketch(PH, 'Sketch_PoleHub_Profile')
sk_circle(sk, 0, 0, P['pole_hub_d'] / 2, 'pole_dia', 'Params.pole_hub_d')
sk.addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))
pad(PH, sk, 'Pad_PoleHubBody', P['pole_hub_h'], sym=True, expr='Params.pole_hub_h')
prim(PH, 'SubtractiveCylinder', 'Pocket_BearingSeat_6800',
     App.Placement(V(0, 0, -P['pole_hub_h'] / 2 - 0.01), App.Rotation()),
     Radius=P['bearing_od'] / 2 + 0.03, Height=P['bearing_w'] + 0.2)
prim(PH, 'SubtractiveCylinder', 'Hole_Bore_CapSpigot', App.Placement(V(0, 0, -P['pole_hub_h'] / 2 - 1), App.Rotation()),
     Radius=7.0, Height=P['pole_hub_h'] + 2)
s0p = P['pole_hub_d'] / 2 - P['socket_depth']
d = POLE_DIRS[0]
psock = prim(PH, 'SubtractiveCylinder', 'Socket_Pole_1', App.Placement(d * s0p, rot_z_to(d)),
             Radius=P['strut_d'] / 2 + 0.05, Height=P['socket_depth'] + 4)
pp = PH.newObject('PartDesign::PolarPattern', 'PolarPattern_PoleSockets')
pp.Originals = [psock]; pp.Axis = (sk, ['N_Axis']); pp.Occurrences = 5
finish(PH, pp)
meta(PH, 'PA12', 'CAD', note='Axle pole hub: 5 strut sockets + 6800-2RS bearing seat on inner face')

# ---------------------------------------------------------------------------------------------
# Cage assembly (expression-driven by Params.cage_R / strut_d / hub dims)
# ---------------------------------------------------------------------------------------------
def set_base_expr(o, comp_exprs):
    for c, e in zip('xyz', comp_exprs):
        o.setExpression(f'Placement.Base.{c}', e)


CAGE_ITEMS = []  # (obj, kind, extra)
for k, (i, j) in enumerate(struts):
    a, b_ = U[i], U[j]
    dvec = b_ - a; kc = dvec.Length; dvec.normalize()
    si = S0P if i in POLES else S0
    sj = S0P if j in POLES else S0
    c = doc.addObject('Part::Cylinder', f'Strut_{k:03d}')
    c.Radius = P['strut_d'] / 2
    c.setExpression('Radius', 'Params.strut_d / 2')
    c.setExpression('Height', f'Params.cage_R * {kc:.9f} - ({si}) - ({sj})')
    c.Placement = App.Placement(a * R, rot_z_to(dvec))
    set_base_expr(c, [f'Params.cage_R * {a[q]:.9f} + {dvec[q]:.9f} * ({si})' for q in range(3)])
    meta(c, 'GFRP', 'CAD', note=f'chord {"A" if kc < 0.58 else "B"} {kc * R:.1f} mm hub-to-hub')
    G_STRUT.addObject(c)
    CAGE_ITEMS.append((c, 'strut', (i, j)))

for i in range(len(U)):
    if i in POLES:
        continue
    n, rot, _ = local_frame(i)
    tgt = HUB_M if kind[i] == 'M' else HUB_V
    h = link(f'Hub_{kind[i]}_{i:02d}', tgt, G_HUB, App.Placement(n * R, rot))
    set_base_expr(h, [f'Params.cage_R * {n[q]:.9f}' for q in range(3)])
    meta(h, 'PA12', 'CAD')
    cp = link(f'Cap_{i:02d}', CAP, G_CAP, App.Placement(n * (R + P['hub_h'] / 2), rot))
    set_base_expr(cp, [f'(Params.cage_R + Params.hub_h / 2) * {n[q]:.9f}' for q in range(3)])
    meta(cp, 'TPU', 'CAD')
    CAGE_ITEMS += [(h, 'hub', i), (cp, 'cap', i)]

for pi_, sgn, tag_ in ((0, 1, 'PosY'), (11, -1, 'NegY')):
    n, rot, _ = local_frame(pi_)
    h = link(f'PoleHub_{tag_}', PH, G_POLE, App.Placement(n * R, rot))
    set_base_expr(h, [f'Params.cage_R * {n[q]:.9f}' for q in range(3)])
    meta(h, 'PA12', 'CAD')
    cp = link(f'PoleCap_{tag_}', POLECAP, G_POLE, App.Placement(n * (R + P['pole_hub_h'] / 2), rot))
    set_base_expr(cp, [f'(Params.cage_R + Params.pole_hub_h / 2) * {n[q]:.9f}' for q in range(3)])
    meta(cp, 'TPU', 'CAD')
    y0 = sgn * (R - P['pole_hub_h'] / 2)
    brg = cyl(P['bearing_od'] / 2, P['bearing_w'], (0, y0, 0), (0, sgn, 0)).cut(
        cyl(P['bearing_id'] / 2, P['bearing_w'], (0, y0, 0), (0, sgn, 0)))
    bo = feature(f'Bearing_6800_2RS_{tag_}', brg, G_POLE, 'Steel', 'catalogue', 5.5, '6800-2RS 10x19x5 deep-groove bearing')
    CAGE_ITEMS += [(h, 'polehub', pi_), (cp, 'polecap', pi_), (bo, 'bearing', pi_)]
log('cage objects', len(CAGE_ITEMS))

# ---------------------------------------------------------------------------------------------
# Axle
# ---------------------------------------------------------------------------------------------
AX = doc.addObject('PartDesign::Body', 'Axle'); ASM.addObject(AX)
sk = new_sketch(AX, 'Sketch_Axle_Section', 'XZ_Plane')
sk_circle(sk, 0, 0, P['axle_od'] / 2, 'axle_od', 'Params.axle_od')
sk_circle(sk, 0, 0, P['axle_id'] / 2, 'axle_id', 'Params.axle_id')
sk.addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))
sk.addConstraint(Sketcher.Constraint('Coincident', 1, 3, -1, 1))
axl = 2 * (R - P['pole_hub_h'] / 2 + P['bearing_w'])
finish(AX, pad(AX, sk, 'Pad_AxleTube', axl, sym=True,
               expr='2 * (Params.cage_R - Params.pole_hub_h / 2 + Params.bearing_w)'))
meta(AX, 'CF', 'CAD', note='10/8 mm roll-wrapped carbon tube, ends in the 6800 bearings')

# ---------------------------------------------------------------------------------------------
# Frame
# ---------------------------------------------------------------------------------------------
MR = P['frame_diag'] / 2
# arm master (local +X)
ARM = doc.addObject('PartDesign::Body', 'Arm'); LIB.addObject(ARM)
sk = new_sketch(ARM, 'Sketch_ArmOutline')
hw = P['arm_w'] / 2
g0 = sk.addGeometry(Part.LineSegment(V(P['arm_root'], -hw, 0), V(MR, -hw, 0)))
g1 = sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(MR, 0, 0), V(0, 0, 1), hw), -math.pi / 2, math.pi / 2))
g2 = sk.addGeometry(Part.LineSegment(V(MR, hw, 0), V(P['arm_root'], hw, 0)))
g3 = sk.addGeometry(Part.LineSegment(V(P['arm_root'], hw, 0), V(P['arm_root'], -hw, 0)))
sk.addConstraint(Sketcher.Constraint('Tangent', g0, 2, g1, 1))
sk.addConstraint(Sketcher.Constraint('Tangent', g1, 2, g2, 1))
sk.addConstraint(Sketcher.Constraint('Coincident', g2, 2, g3, 1))
sk.addConstraint(Sketcher.Constraint('Coincident', g3, 2, g0, 1))
sk.addConstraint(Sketcher.Constraint('Horizontal', g0))
sk.addConstraint(Sketcher.Constraint('Vertical', g3))
sk.addConstraint(Sketcher.Constraint('PointOnObject', g1, 3, -1))
c = sk.addConstraint(Sketcher.Constraint('DistanceX', -1, 1, g1, 3, MR)); sk.renameConstraint(c, 'motor_r')
sk.setExpression('Constraints.motor_r', 'Params.frame_diag / 2')
c = sk.addConstraint(Sketcher.Constraint('Radius', g1, hw)); sk.renameConstraint(c, 'arm_half_w')
sk.setExpression('Constraints.arm_half_w', 'Params.arm_w / 2')
c = sk.addConstraint(Sketcher.Constraint('DistanceX', -1, 1, g3, 1, P['arm_root'])); sk.renameConstraint(c, 'arm_root')
pad(ARM, sk, 'Pad_Arm', P['arm_t'], expr='Params.arm_t')
skm = new_sketch(ARM, 'Sketch_MotorMountHoles')
skm.setExpression('AttachmentOffset.Base.x', 'Params.frame_diag / 2')
sk_circle(skm, 0, 0, 4.0)
for a in range(4):
    ang = math.radians(45 + 90 * a)
    sk_circle(skm, 8 * math.sqrt(2) * math.cos(ang), 8 * math.sqrt(2) * math.sin(ang), 1.6)
pocket_through(ARM, skm, 'Pocket_MotorMountHoles')
skl = new_sketch(ARM, 'Sketch_Lightening_ClampHoles')
sk_profile(skl, [('L', (52, -4.5), (112, -4.5)), ('A', (112, 0), 4.5, -math.pi / 2, math.pi / 2),
                 ('L', (112, 4.5), (52, 4.5)), ('A', (52, 0), 4.5, math.pi / 2, 1.5 * math.pi)])
sk_circle(skl, 30, 0, 1.6); sk_circle(skl, 42, 0, 1.6)
finish(ARM, pocket_through(ARM, skl, 'Pocket_Lightening_ClampHoles'))
meta(ARM, 'CF', 'CAD', note='5 mm 3K carbon arm, 25 mm wide')

ZARM = P['plate_bot_z'] + P['plate_t']
ARMS = {}
for nm, ang in (('FR', -45), ('FL', 45), ('RL', 135), ('RR', -135)):
    l = link(f'Arm_{nm}', ARM, FRAME, App.Placement(V(0, 0, ZARM), App.Rotation(V(0, 0, 1), ang)))
    l.setExpression('Placement.Base.z', 'Params.plate_bot_z + Params.plate_t')
    meta(l, 'CF', 'CAD'); ARMS[nm] = l

# sandwich plate master
PLATE = doc.addObject('PartDesign::Body', 'Plate_Sandwich'); LIB.addObject(PLATE)
sk = new_sketch(PLATE, 'Sketch_PlateOutline')
sk_rrect(sk, 0, 0, P['plate_w'], P['plate_w'], 20)
pad(PLATE, sk, 'Pad_Plate', P['plate_t'], expr='Params.plate_t')
skh = new_sketch(PLATE, 'Sketch_PlateHoles')
sk_circle(skh, 0, 0, 12)
for sx in (-1, 1):
    sk_circle(skh, sx * 30, 0, 8)
    sk_poly(skh, [(sx * 43 - 1.5, -13), (sx * 43 + 1.5, -13), (sx * 43 + 1.5, 13), (sx * 43 - 1.5, 13)])
    for sy in (-1, 1):
        sk_circle(skh, sx * 35, sy * 20, 1.6)
        for rr_ in (30, 42):
            sk_circle(skh, sx * rr_ / math.sqrt(2), sy * rr_ / math.sqrt(2), 1.6)
finish(PLATE, pocket_through(PLATE, skh, 'Pocket_PlateHoles'))
meta(PLATE, 'CF', 'CAD', note='2 mm carbon sandwich plate (bottom and top share this master)')
for nm, z, ex in (('Plate_Bottom', P['plate_bot_z'], 'Params.plate_bot_z'),
                  ('Plate_Top', P['plate_bot_z'] + P['plate_t'] + P['arm_t'],
                   'Params.plate_bot_z + Params.plate_t + Params.arm_t')):
    l = link(nm, PLATE, FRAME, App.Placement(V(0, 0, z), App.Rotation()))
    l.setExpression('Placement.Base.z', ex); meta(l, 'CF', 'CAD')
ZTOP = P['plate_bot_z'] + 2 * P['plate_t'] + P['arm_t']   # top face of top plate (-7)

# avionics deck
DECK = doc.addObject('PartDesign::Body', 'Plate_Deck'); FRAME.addObject(DECK)
DECK.Placement = App.Placement(V(0, 0, P['deck_z']), App.Rotation())
DECK.setExpression('Placement.Base.z', 'Params.deck_z')
sk = new_sketch(DECK, 'Sketch_DeckOutline')
sk_rrect(sk, 0, 0, P['deck_l'], P['deck_w'], 8)
pad(DECK, sk, 'Pad_Deck', P['plate_t'], expr='Params.plate_t')
skh = new_sketch(DECK, 'Sketch_DeckHoles')
sk_poly(skh, [(-15, -5), (15, -5), (15, 5), (-15, 5)])
for sx in (-1, 1):
    for sy in (-1, 1):
        sk_circle(skh, sx * 35, sy * 20, 1.6)
        sk_circle(skh, 10 + sx * 29, sy * 24.5, 1.4)
        sk_circle(skh, sx * 15.25, sy * 15.25, 1.6)
finish(DECK, pocket_through(DECK, skh, 'Pocket_DeckHoles'))
meta(DECK, 'CF', 'CAD', note='2 mm carbon avionics deck above the axle')

# axle clamps
CL = doc.addObject('PartDesign::Body', 'AxleClamp'); LIB.addObject(CL)
sk = new_sketch(CL, 'Sketch_AxleClamp', 'XZ_Plane')
sk_poly(sk, [(-15, -7), (15, -7), (15, 7), (-15, 7)])
sk_circle(sk, 0, 0, P['axle_od'] / 2 + 0.05)
pad(CL, sk, 'Pad_Clamp', 14, sym=True)
for sx in (-1, 1):
    tipc = prim(CL, 'SubtractiveCylinder', f'Hole_ClampScrew_{"L" if sx < 0 else "R"}',
                App.Placement(V(sx * 10, 0, -8), App.Rotation()), Radius=1.6, Height=16)
finish(CL, tipc)
meta(CL, 'PA12', 'CAD', note='printed split clamp holding the axle tube to the top plate')
for sy in (-1, 1):
    l = link(f'AxleClamp_{"PosY" if sy > 0 else "NegY"}', CL, FRAME, App.Placement(V(0, sy * P['axle_clamp_y'], 0), App.Rotation()))
    l.setExpression('Placement.Base.y', f'{sy} * Params.axle_clamp_y'); meta(l, 'PA12', 'CAD')

# standoffs and stack posts (aluminium)
st = []
for sx in (-1, 1):
    for sy in (-1, 1):
        st.append(cyl(2.5, P['deck_z'] - ZTOP, (sx * 35, sy * 20, ZTOP)))
feature('Standoffs_Deck_M3', Part.makeCompound(st), FRAME, 'Al', 'CAD', note='4x M3 Al standoffs top plate -> deck')
ZDT = P['deck_z'] + P['plate_t']      # deck top (12)
Z_MAST = 64.0
posts = [cyl(2.5, Z_MAST - ZDT, (10 + sx * 29, sy * 24.5, ZDT)) for sx in (-1, 1) for sy in (-1, 1)]
posts += [cyl(1.5, 3, (sx * 15.25, sy * 15.25, ZDT)) for sx in (-1, 1) for sy in (-1, 1)]
posts += [cyl(1.5, 3, (sx * 15.25, sy * 15.25, ZDT + 9)) for sx in (-1, 1) for sy in (-1, 1)]
feature('Standoffs_Stack_Posts', Part.makeCompound(posts), FRAME, 'Al', 'CAD', note='Pi/LiDAR posts + ESC/FC M3 spacers')

# nose sensor bracket (printed)
NB_ = doc.addObject('PartDesign::Body', 'Nose_Bracket'); FRAME.addObject(NB_)
prim(NB_, 'AdditiveBox', 'Box_Foot', App.Placement(V(37, -18, ZDT), App.Rotation()), Length=9, Width=36, Height=22)
prim(NB_, 'AdditiveBox', 'Box_Head', App.Placement(V(44, -18, 28), App.Rotation()), Length=26, Width=36, Height=44)
prim(NB_, 'SubtractiveBox', 'Cut_HeadCavity', App.Placement(V(46, -16, 30), App.Rotation()), Length=22, Width=32, Height=40)
RX = App.Rotation(V(0, 1, 0), 90)
prim(NB_, 'SubtractiveCylinder', 'Hole_CameraLens', App.Placement(V(66, 0, 54), RX), Radius=7.3, Height=6)
prim(NB_, 'SubtractiveCylinder', 'Hole_Thermal', App.Placement(V(66, 0, 34), RX), Radius=5.0, Height=6)
prim(NB_, 'SubtractiveCylinder', 'Hole_IR_L', App.Placement(V(66, 12, 34), RX), Radius=4.2, Height=6)
finish(NB_, prim(NB_, 'SubtractiveCylinder', 'Hole_IR_R', App.Placement(V(66, -12, 34), RX), Radius=4.2, Height=6))
meta(NB_, 'PA12', 'CAD', note='nose head: camera, thermal, 850 nm IR LEDs; sits above the rotor plane')

# LiDAR mast plate (printed)
LM = doc.addObject('PartDesign::Body', 'LiDAR_Mast'); FRAME.addObject(LM)
prim(LM, 'AdditiveBox', 'Box_MastPlate', App.Placement(V(-24, -28, Z_MAST), App.Rotation()), Length=67, Width=56, Height=3)
finish(LM, prim(LM, 'SubtractiveCylinder', 'Hole_Cable', App.Placement(V(0, 0, Z_MAST - 1), App.Rotation()), Radius=6, Height=5))
meta(LM, 'PA12', 'CAD', note='printed LiDAR mast plate on the 4 stack posts')

# ---------------------------------------------------------------------------------------------
# Propulsion
# ---------------------------------------------------------------------------------------------
def motor_shape():
    s = cyl(14, 3, (0, 0, 0)).fuse(cyl(16.9, 13, (0, 0, 3.5))).fuse(cyl(11, 2.5, (0, 0, 16.5)))
    s = s.fuse(cyl(2.5, 3.5, (0, 0, 16.5)))
    return s


def prop_shape(pitch_deg):
    tipR = P['prop_d'] / 2
    hub = cyl(7, P['prop_hub_h'], (0, 0, -P['prop_hub_h'] / 2)).cut(cyl(2.6, P['prop_hub_h'] + 2, (0, 0, -P['prop_hub_h'] / 2 - 1)))
    # tapered blade planform along +X (chord along Y), 1.4 mm thick
    st_ = [(5, 6), (20, 9), (45, 9.5), (70, 7.5), (84, 5.0), (tipR - 1.2, 2.2)]
    pts = [V(r, -c, 0) for r, c in st_] + [V(tipR, 0, 0)] + [V(r, c * 0.55, 0) for r, c in reversed(st_)]
    w = Part.makePolygon(pts + [pts[0]])
    blade = Part.Face(w).extrude(V(0, 0, 1.4))
    blade.translate(V(0, 0, -0.7))
    blade.rotate(V(0, 0, 0), V(1, 0, 0), pitch_deg)
    blades = [blade.copy() for _ in range(3)]
    for k, bl in enumerate(blades):
        bl.rotate(V(0, 0, 0), V(0, 0, 1), 120 * k)
    return Part.makeCompound([hub] + blades)


Z_MOTOR = ZARM + P['arm_t']          # -9
Z_PROP = P['prop_z']
MOTORS = {}
for nm, sx, sy, cw, spin in (('FR', 1, -1, False, 10), ('FL', 1, 1, True, 50), ('RL', -1, 1, False, 85), ('RR', -1, -1, True, 25)):
    m = feature(f'Motor_{nm}', motor_shape(), PROP, 'motor', 'catalogue', 62.0, '2808/2809-class 1250-1300 KV, ~62 g with leads',
                App.Placement(V(sx * MR / math.sqrt(2), sy * MR / math.sqrt(2), Z_MOTOR), App.Rotation()))
    m.setExpression('Placement.Base.x', f'{sx} * Params.frame_diag / 2 * 0.70710678')
    m.setExpression('Placement.Base.y', f'{sy} * Params.frame_diag / 2 * 0.70710678')
    m.setExpression('Placement.Base.z', 'Params.plate_bot_z + Params.plate_t + Params.arm_t')
    p = feature(f'Prop_{nm}', prop_shape(-14 if cw else 14), PROP, 'prop', 'catalogue', 8.0,
                f'HQ 7x4x3 tri-blade, {"CW" if cw else "CCW"} (simplified blades)',
                App.Placement(V(sx * MR / math.sqrt(2), sy * MR / math.sqrt(2), Z_PROP), App.Rotation(V(0, 0, 1), spin)))
    p.setExpression('Placement.Base.x', f'{sx} * Params.frame_diag / 2 * 0.70710678')
    p.setExpression('Placement.Base.y', f'{sy} * Params.frame_diag / 2 * 0.70710678')
    p.setExpression('Placement.Base.z', 'Params.prop_z')
    nut = feature(f'PropNut_{nm}', cyl(5, 5, (0, 0, 0)), PROP, 'steel', 'catalogue', 0.0, 'M5 prop nut (in motor mass)',
                  App.Placement(V(sx * MR / math.sqrt(2), sy * MR / math.sqrt(2), Z_PROP + P['prop_hub_h'] / 2), App.Rotation()))
    disc = doc.addObject('Part::Cylinder', f'PropDisc_{nm}')
    disc.Radius = P['prop_d'] / 2; disc.setExpression('Radius', 'Params.prop_d / 2')
    disc.Height = 0.6
    disc.Placement = App.Placement(V(sx * MR / math.sqrt(2), sy * MR / math.sqrt(2), Z_PROP - 0.3), App.Rotation())
    HELP.addObject(disc)
    MOTORS[nm] = (m, p, nut, disc)

# ---------------------------------------------------------------------------------------------
# Core stack (bought parts as envelope blocks + catalogue masses)
# ---------------------------------------------------------------------------------------------
BAT = doc.addObject('PartDesign::Body', 'Battery_6S_3300'); CORE.addObject(BAT)
sk = new_sketch(BAT, 'Sketch_BatteryFootprint')
sk_rrect(sk, 0, 0, P['batt_l'], P['batt_w'], 3)
finish(BAT, pad(BAT, sk, 'Pad_BatteryBlock', P['batt_h'], rev=True, expr='Params.batt_h'))
BAT.Placement = App.Placement(V(P['batt_x'], 0, P['plate_bot_z'] - 1), App.Rotation())
BAT.setExpression('Placement.Base.x', 'Params.batt_x')
BAT.setExpression('Placement.Base.z', 'Params.plate_bot_z - 1')
meta(BAT, 'battery', 'catalogue', 490.0, '6S 3300 mAh LiPo, 490 g per baseline; slung under bottom plate with 2 straps')

ESC = feature('ESC_4in1_6S', box(-21, 21, -20, 20, ZDT + 3, ZDT + 9).fuse(cyl(5, 18, (-35, -9, ZDT + 5), (0, 1, 0))),
              CORE, 'esc', 'catalogue', 28.0, '4-in-1 6S 55-65 A ESC (DShot) + low-ESR cap')
FC = feature('FC_Pixhawk6C_Mini', box(-26.65, 26.65, -19.5, 19.5, ZDT + 12, ZDT + 28.7), CORE, 'fc', 'catalogue', 39.2,
             'Holybro Pixhawk 6C Mini, 53.3x39x16.7 mm')
ZPI = 44.0
pi_board = box(-42.5, 42.5, -28, 28, ZPI, ZPI + 1.6)
pi_ports = box(-42.5, -22.0, -26.5, 26.5, ZPI + 1.6, ZPI + 17.6)
pi_cool = box(-12, 28, -18, 18, ZPI + 1.6, ZPI + 10.6).fuse(cyl(15, 1.5, (8, 0, ZPI + 10.6)))
pi_gpio = box(-20, 31, 22, 27, ZPI + 1.6, ZPI + 10.1)
PI_BOARD = feature('Pi5_Board', pi_board.fuse(pi_gpio), CORE, 'pcb', 'catalogue', 46.0, 'Raspberry Pi 5 8 GB (~46 g)')
PI_PORTS = feature('Pi5_PortBlock', pi_ports, CORE, 'metal', 'catalogue', 0.0, 'USB/Ethernet stack (in board mass)')
PI_COOL = feature('Pi5_ActiveCooler', pi_cool, CORE, 'metal', 'catalogue', 22.0, 'Official active cooler (~22 g)')
PMB = feature('PowerModule_Buck', box(18, 42, -16, 16, ZTOP, ZTOP + 12), CORE, 'electronics', 'catalogue', 30.0,
              '6S PM with V/I sense (~20 g) + 6S->5.1 V/5 A buck (~10 g)')
RADIO = feature('RadioPod_ESP32C3_LoRa_RX', box(-42, -18, -16, 16, ZTOP, ZTOP + 12), CORE, 'electronics', 'catalogue', 27.0,
                'ESP32-C3 scout node (~5 g) + RFM95W-868 (~5 g) + FS-iA6B/ELRS RX (~15 g) + misc')
ANT = feature('LoRa_Antenna_868', cyl(3, 55, (-42, 0, 0), (-1, 0, 0)), CORE, 'electronics', 'catalogue', 8.0,
              '868 MHz stub antenna, rearward on the centreline')

# ---------------------------------------------------------------------------------------------
# Sensor spine
# ---------------------------------------------------------------------------------------------
ZL = Z_MAST + 3
LIDAR = feature('LiDAR_STL19P', cyl(19, 20, (0, 0, ZL)).fuse(cyl(17, 14, (0, 0, ZL + 20))), SENS, 'lidar', 'catalogue', 47.0,
                'STL-19P 2D LiDAR envelope Ø38x34 (~47 g)')
CAM = feature('Camera_IMX327', box(64, 66, -15, 15, 39.5, 69.5).fuse(cyl(7, 14, (66, 0, 54), (1, 0, 0))),
              SENS, 'camera', 'catalogue', 15.0, 'IMX327 CSI module (30x30) + M12 lens')
THERM = feature('Thermal_MLX90640', box(62, 64, -7, 7, 30.5, 39).fuse(cyl(4.6, 6, (64, 0, 34), (1, 0, 0))), SENS, 'metal',
                'catalogue', 5.0, 'MLX90640 110 deg (TO39) on breakout')
IRL = []
for sy in (-1, 1):
    IRL.append(feature(f'IR_LED_850nm_{"L" if sy > 0 else "R"}', cyl(3.9, 1.5, (63, sy * 12, 34), (1, 0, 0)).fuse(
        cyl(3.9, 8, (64.5, sy * 12, 34), (1, 0, 0))), SENS, 'irled', 'catalogue', 3.0, '850 nm IR LED + 8 mm optic'))
# gas package (under bottom plate, -Y side)
ZB = P['plate_bot_z']
FCELL = doc.addObject('PartDesign::Body', 'Gas_FlowCell'); SENS.addObject(FCELL)
prim(FCELL, 'AdditiveBox', 'Box_Manifold', App.Placement(V(-30, -55, ZB - 19), App.Rotation()), Length=42, Width=30, Height=18)
finish(FCELL, prim(FCELL, 'SubtractiveCylinder', 'Bore_FlowPath', App.Placement(V(-31, -40, ZB - 10), RX), Radius=2.0, Height=44))
meta(FCELL, 'PA12', 'CAD', note='printed pumped flow cell holding the O2/CO/H2S cells')
GSENS = feature('Gas_Sensors_O2_CO_H2S', Part.makeCompound([cyl(10, 12, (x, -40, ZB - 31)) for x in (-21, -9, 3)]), SENS,
                'metal', 'catalogue', 36.0, '3 electrochemical cells/boards (DFRobot SEN0465/66/67 dev fallback)')
PUMP = feature('Gas_Pump', cyl(11, 34, (14, -40, ZB - 13), (1, 0, 0)), SENS, 'electronics', 'catalogue', 25.0,
               'micro diaphragm sampling pump')
X_TIP = 225.0
GTUBE = feature('GasInlet_Tube', cyl(2, X_TIP - 12 - 48, (48, -40, ZB - 13), (1, 0, 0)).cut(
    cyl(1, X_TIP - 12 - 48, (48, -40, ZB - 13), (1, 0, 0))), SENS, 'ptfe', 'CAD',
    note='4/2 mm PTFE inlet tube to the nose')
GFILT = feature('GasInlet_Filter', cyl(4, 12, (X_TIP - 12, -40, ZB - 13), (1, 0, 0)), SENS, 'amber', 'catalogue', 2.0,
                'sintered inlet filter tip, 32 mm ahead of the prop tip envelope')

# ---------------------------------------------------------------------------------------------
# SUTRA puck master (local: base at z=0, axis Z)
# ---------------------------------------------------------------------------------------------
PUCK = doc.addObject('App::Part', 'SUTRA_Puck'); LIB.addObject(PUCK)
rs = P['puck_shell_d'] / 2          # 26
rb = P['puck_d'] / 2                # 28
wall = 1.4
DOME_Z0, PUCK_H = 17.5, P['puck_h']
rho = (rs ** 2 + (PUCK_H - DOME_Z0) ** 2) / (2 * (PUCK_H - DOME_Z0))
B1 = doc.addObject('PartDesign::Body', 'Puck_Shell_Base'); PUCK.addObject(B1)
sk = new_sketch(B1, 'Sketch_BaseProfile', 'XZ_Plane')
sk_poly(sk, [(0, 0), (rs - 1, 0), (rs, 1), (rs, 9), (rs - wall, 9), (rs - wall, wall), (0, wall)])
revolve(B1, sk, 'Revolution_BaseCup')
for sx in (-1, 1):
    tip1 = prim(B1, 'SubtractiveCylinder', f'Pocket_ChargePad_{"A" if sx < 0 else "B"}',
                App.Placement(V(sx * 10, 0, -0.1), App.Rotation()), Radius=3.1, Height=0.7)
finish(B1, tip1)
meta(B1, 'PETG', 'CAD', note='PETG base cup; charge-pad recesses underneath')

B2 = doc.addObject('PartDesign::Body', 'Puck_Shell_Lid'); PUCK.addObject(B2)
sk = new_sketch(B2, 'Sketch_LidProfile', 'XZ_Plane')
a0 = math.atan2(DOME_Z0 - (PUCK_H - rho), rs)
CEIL = 16.3
sk_profile(sk, [('A', (0, PUCK_H - rho), rho, a0, math.pi / 2), ('L', (0, PUCK_H), (0, CEIL)), ('L', (0, CEIL), (rs - wall, CEIL)),
                ('L', (rs - wall, CEIL), (rs - wall, 9)), ('L', (rs - wall, 9), (rs, 9)), ('L', (rs, 9), (rs, DOME_Z0))])
revolve(B2, sk, 'Revolution_DomedLid')
TAG_FLOOR = 17.8
prim(B2, 'SubtractiveBox', 'Pocket_AprilTag_30mm', App.Placement(V(-15.2, -15.2, TAG_FLOOR), App.Rotation()),
     Length=30.4, Width=30.4, Height=3)
finish(B2, prim(B2, 'SubtractiveCylinder', 'Hole_LightPipe', App.Placement(V(0, 21.5, CEIL - 1), App.Rotation()),
                Radius=1.5, Height=5))
meta(B2, 'PETG', 'CAD', note='PETG domed lid, 30 mm AprilTag 36h11 recess (flat landing), LED light pipe')

B3 = doc.addObject('PartDesign::Body', 'Puck_Bumper_TPU'); PUCK.addObject(B3)
sk = new_sketch(B3, 'Sketch_BumperRing', z=5.0)
sk_circle(sk, 0, 0, rb, 'bumper_od', 'Params.puck_d'); sk_circle(sk, 0, 0, rs, 'bumper_id', 'Params.puck_shell_d')
finish(B3, pad(B3, sk, 'Pad_BumperRing', 8.0))
meta(B3, 'TPU', 'CAD', note='TPU 95A bumper ring over the shell seam')

B4 = doc.addObject('PartDesign::Body', 'Puck_PCB'); PUCK.addObject(B4)
sk = new_sketch(B4, 'Sketch_PCB', z=7.4)
sk_circle(sk, 0, 0, 24.0, 'pcb_dia')
finish(B4, pad(B4, sk, 'Pad_PCB', 1.6))
meta(B4, 'FR4', 'CAD', note='Ø48x1.6 FR4: ESP32-C3-MINI-1, RFM95W, MCP73831, AP2112K, DRV5032, LED')
PK_BAT = feature('Puck_LiPo_1S_400', box(-15, 15, -10, 10, 1.8, 6.8), PUCK, 'battery', 'catalogue', 8.5,
                 '1S 400 mAh LiPo (502030 class) - lowest item, keeps the CG low')
PK_ESP = feature('Puck_ESP32C3_MINI1', box(-18, -1.4, -15, 1.6, 9.0, 11.4), PUCK, 'module', 'catalogue', 1.0, 'ESP32-C3-MINI-1')
PK_RFM = feature('Puck_RFM95W_868', box(1, 17, -8, 8, 9.0, 10.8), PUCK, 'module', 'catalogue', 1.5, 'RFM95W-868 (SX1276)')
PK_ANT = feature('Puck_Antenna_Stub', cyl(2.5, 6.8, (14, 16, 9.0)), PUCK, 'brass', 'catalogue', 0.6, '868 MHz helical stub antenna')
PK_PAD = feature('Puck_ChargePads', Part.makeCompound([cyl(3, 0.6, (sx * 10, 0, 0)) for sx in (-1, 1)]), PUCK, 'brass',
                 'catalogue', 0.4, 'charge contacts (cassette pads)')
PK_MISC = feature('Puck_Passives_LED_Hall', box(-14, -2, 6, 12, 9.0, 10.0), PUCK, 'module', 'catalogue', 0.6,
                  'MCP73831, AP2112K-3.3, DRV5032, LED, passives')
TAG = doc.addObject('Part::Feature', 'Puck_AprilTag_Label')
TAG.Shape = box(-15, 15, -15, 15, TAG_FLOOR, TAG_FLOOR + 0.15)
HELP.addObject(TAG)
PUCK_PARTS = [(B1, 'petg_white', 'PETG', None), (B2, 'petg_white', 'PETG', None), (B3, 'tpu', 'TPU', None),
              (B4, 'pcb', 'FR4', None), (PK_BAT, 'battery_small', None, 8.5), (PK_ESP, 'module', None, 1.0),
              (PK_RFM, 'module', None, 1.5), (PK_ANT, 'brass', None, 0.6), (PK_PAD, 'brass', None, 0.4),
              (PK_MISC, 'module', None, 0.6)]
PUCK_EXTRA_G = 0.8   # screws + tag label (catalogue allowance)

# ---------------------------------------------------------------------------------------------
# Cassette
# ---------------------------------------------------------------------------------------------
Y0 = P['cassette_y']
ZE = P['cassette_exit_z']
r_in = P['puck_d'] / 2 + P['tube_clear']           # 29
r_out = r_in + P['tube_wall']
TUBE = doc.addObject('PartDesign::Body', 'Cassette_Tube'); CASS.addObject(TUBE)
TUBE.Placement = App.Placement(V(0, Y0, P['cassette_top_z']), App.Rotation())
TUBE.setExpression('Placement.Base.y', 'Params.cassette_y')
TUBE.setExpression('Placement.Base.z', 'Params.cassette_top_z')
sk = new_sketch(TUBE, 'Sketch_TubeSection')
sk_circle(sk, 0, 0, r_out, 'tube_od', 'Params.puck_d + 2 * (Params.tube_clear + Params.tube_wall)')
sk_circle(sk, 0, 0, r_in, 'tube_id', 'Params.puck_d + 2 * Params.tube_clear')
pad(TUBE, sk, 'Pad_Tube', P['cassette_len'], rev=True, expr='Params.cassette_len')
ZREL = ZE + 3.0
ZCAP = ZE + 4.5 + 20 + 9.0
for nm, z in (('Slot_ReleasePin', ZREL), ('Slot_CapturePin', ZCAP)):
    prim(TUBE, 'SubtractiveCylinder', nm, App.Placement(V(0, r_in - 2, z - P['cassette_top_z']),
                                                        App.Rotation(V(1, 0, 0), -90)), Radius=1.7, Height=6)
R45 = App.Rotation(V(0, 0, 1), 45)
win = prim(TUBE, 'SubtractiveBox', 'Pocket_Window', App.Placement(R45.multVec(V(r_in - 2, -13, -98)), R45),
           Length=6, Width=26, Height=76)
pp = TUBE.newObject('PartDesign::PolarPattern', 'PolarPattern_Windows')
pp.Originals = [win]; pp.Axis = (sk, ['N_Axis']); pp.Occurrences = 4
finish(TUBE, pp)
meta(TUBE, 'PETG', 'CAD', note='clear PETG cassette tube, 4 windows; pins enter from +Y')

TC = doc.addObject('PartDesign::Body', 'Cassette_TopCap'); CASS.addObject(TC)
prim(TC, 'AdditiveCylinder', 'Cyl_Cap', App.Placement(V(0, Y0, P['cassette_top_z'] + 3), App.Rotation()), Radius=r_out + 1.5, Height=3)
prim(TC, 'AdditiveCylinder', 'Cyl_Spigot', App.Placement(V(0, Y0, P['cassette_top_z']), App.Rotation()), Radius=r_in - 0.1, Height=3.1)
prim(TC, 'SubtractiveCylinder', 'Pocket_Spigot_Lightening', App.Placement(V(0, Y0, P['cassette_top_z'] - 0.1), App.Rotation()),
     Radius=r_in - 2.0, Height=3.1)
prim(TC, 'AdditiveCylinder', 'Cyl_MagnetBoss', App.Placement(V(0, Y0, P['cassette_top_z']), App.Rotation()), Radius=7, Height=3.1)
prim(TC, 'AdditiveBox', 'Box_MountTab', App.Placement(V(-15, 24, P['cassette_top_z'] + 3), App.Rotation()), Length=30, Width=Y0 - 24, Height=3)
finish(TC, prim(TC, 'SubtractiveCylinder', 'Pocket_WakeMagnet', App.Placement(V(0, Y0, P['cassette_top_z'] - 0.1), App.Rotation()),
                Radius=5.1, Height=3))
meta(TC, 'PA12', 'CAD', note='top cap + mount tab to bottom plate; holds the puck wake magnet')

COL = doc.addObject('PartDesign::Body', 'BreakBeam_Collar'); CASS.addObject(COL)
prim(COL, 'AdditiveCylinder', 'Cyl_Collar', App.Placement(V(0, Y0, ZE - 8), App.Rotation()), Radius=r_out + 4, Height=8)
prim(COL, 'SubtractiveCylinder', 'Bore_Exit', App.Placement(V(0, Y0, ZE - 9), App.Rotation()), Radius=r_out, Height=10)
finish(COL, prim(COL, 'SubtractiveCylinder', 'Hole_Beam', App.Placement(V(-r_out - 6, Y0, ZE - 4), RX), Radius=1.2,
                 Height=2 * r_out + 12))
meta(COL, 'PA12', 'CAD', note='exit collar carrying the IR break-beam pair across the exit')
BB = feature('BreakBeam_IR_Pair', Part.makeCompound([box(sx * (r_out + 4) - 3 + sx * 3, sx * (r_out + 4) + 3 + sx * 3,
                                                         Y0 - 3, Y0 + 3, ZE - 8, ZE) for sx in (-1, 1)]),
             CASS, 'electronics', 'catalogue', 2.0, '3 mm IR break-beam emitter/receiver')
PIN_R = feature('Pin_Release', cyl(1.5, 17, (0, Y0 + r_in - 10, ZREL), (0, 1, 0)).fuse(cyl(3, 2, (0, Y0 + r_in + 7, ZREL), (0, 1, 0))),
                CASS, 'steel', 'CAD', note='lower release pin (holds the bottom puck)')
PIN_C = feature('Pin_Capture', cyl(1.5, 13, (0, Y0 + r_in - 2, ZCAP), (0, 1, 0)).fuse(cyl(3, 2, (0, Y0 + r_in + 11, ZCAP), (0, 1, 0))),
                CASS, 'steel', 'CAD', note='upper capture pin (pinches puck 2 at its TPU bumper)')
ZC = (ZREL + ZCAP) / 2
CAM_ = feature('Escapement_Cam', cyl(10, 3, (-1.5, Y0 + r_in + 15, ZC), (1, 0, 0)), CASS, 'pa12', 'CAD',
               note='servo cam alternating the two pins (rocker linkage not drawn)')
SERVO = feature('Servo_MG90S', box(3, 25.7, Y0 + r_in + 4, Y0 + r_in + 26.8, ZC - 6.1, ZC + 6.1).fuse(
    box(16, 18.5, Y0 + r_in - 0.7, Y0 + r_in + 31.5, ZC - 6.1, ZC + 6.1)).fuse(cyl(2.5, 3, (0, Y0 + r_in + 15, ZC), (1, 0, 0))),
    CASS, 'servo', 'catalogue', 13.4, 'MG90S micro servo')
sb = box(4, 26, Y0 + 20, Y0 + r_in - 0.7, ZC - 14, ZC + 14).cut(cyl(r_out + 0.2, 40, (0, Y0, ZC - 20)))
SBR = feature('Servo_Bracket', sb, CASS, 'pa12', 'CAD', note='printed saddle bracket tube -> servo')
for o in (PIN_R, PIN_C):
    o.SurangMaterial = 'Steel'
CAM_.SurangMaterial = 'PA12'; SBR.SurangMaterial = 'PA12'
PUCKS = []
for k in range(P['n_pucks']):
    l = link(f'SUTRA_Puck_{k + 1}', PUCK, CASS, App.Placement(V(0, Y0, ZE + 4.5 + 20 * k), App.Rotation()))
    l.setExpression('Placement.Base.y', 'Params.cassette_y')
    l.setExpression('Placement.Base.z', f'Params.cassette_exit_z + 4.5 + Params.puck_h * {k}')
    PUCKS.append(l)

doc.recompute()
LIB.Visibility = False
HELP.Visibility = False
bad = [o.Name for o in doc.Objects if 'Invalid' in o.State or 'Error' in o.State]
log('recompute done; objects:', len(doc.Objects), 'invalid:', bad[:20])
assert not bad, bad

# ---------------------------------------------------------------------------------------------
# Registry for mass / CG / render export
# ---------------------------------------------------------------------------------------------
REG = []   # dicts: name, shape (global), mass_g, mat, alloc, rmat, group, explode, cg (V)


def add(name, shape, alloc, rmat, group, explode=(0, 0, 0), dens=None, cat=None, cg=None, render=True):
    c, vol = cg, 0.0
    if shape is not None and shape.Solids:
        vol = sum(s.Volume for s in shape.Solids)
        c = sum((s.CenterOfMass * s.Volume for s in shape.Solids), V()) * (1.0 / vol)
    m = vol / 1000.0 * DENS[dens] if dens is not None else cat
    REG.append(dict(name=name, shape=shape, mass=m, src='CAD' if dens else 'catalogue', mat=dens or 'bought',
                    alloc=alloc, rmat=rmat, group=group, explode=explode, cg=c, render=render and shape is not None))


# explode vectors (mm) for render (b)
EX = dict(cage_pos=(0, 330, 0), cage_neg=(0, -330, 0), pole_pos=(0, 450, 0), pole_neg=(0, -450, 0),
          axle=(0, 0, 0), frame=(0, 0, 0), motor=(0, 0, 70), prop=(0, 0, 150), deck=(0, 0, 90), esc=(0, 0, 120),
          fc=(0, 0, 150), pi=(0, 0, 190), mast=(0, 0, 230), lidar=(0, 0, 270), nose=(150, 0, 90),
          gas=(0, -150, -60), battery=(0, 0, -150), under=(0, 0, 0), cassette=(0, 90, -230))
for o, k, extra in CAGE_ITEMS:
    s = o.Shape
    if k == 'strut':
        i, j = extra
        ym = (U[i].y + U[j].y) / 2
        side = 'cage_pos' if ym > 1e-6 else 'cage_neg'
        add(o.Name, s, 'Cage', 'gfrp', side, EX[side], dens='GFRP')
    elif k in ('hub', 'cap'):
        side = 'cage_pos' if U[extra].y > 1e-6 else 'cage_neg'
        add(o.Name, s, 'Cage', 'pa12' if k == 'hub' else 'tpu', side, EX[side], dens='PA12' if k == 'hub' else 'TPU')
    else:
        side = 'pole_pos' if U[extra].y > 0 else 'pole_neg'
        if k == 'bearing':
            add(o.Name, s, 'Cage', 'steel', side, EX[side], cat=5.5)
        else:
            add(o.Name, s, 'Cage', 'pa12' if k == 'polehub' else 'tpu', side, EX[side], dens='PA12' if k == 'polehub' else 'TPU')

add('Axle', AX.Shape, 'Frame + mounts', 'carbon', 'axle', EX['axle'], dens='CF')
for nm, l in ARMS.items():
    add(l.Name, l.Shape, 'Frame + mounts', 'carbon', 'frame', EX['frame'], dens='CF')
for nm in ('Plate_Bottom', 'Plate_Top'):
    add(nm, doc.getObject(nm).Shape, 'Frame + mounts', 'carbon', 'frame', EX['frame'], dens='CF')
add('Plate_Deck', DECK.Shape, 'Frame + mounts', 'carbon', 'deck', EX['deck'], dens='CF')
for nm in ('AxleClamp_PosY', 'AxleClamp_NegY'):
    add(nm, doc.getObject(nm).Shape, 'Frame + mounts', 'pa12', 'frame', EX['frame'], dens='PA12')
add('Standoffs_Deck_M3', doc.getObject('Standoffs_Deck_M3').Shape, 'Frame + mounts', 'metal', 'frame', EX['frame'], dens='Al')
add('Standoffs_Stack_Posts', doc.getObject('Standoffs_Stack_Posts').Shape, 'Frame + mounts', 'metal', 'deck', EX['deck'], dens='Al')
add('Nose_Bracket', NB_.Shape, 'Frame + mounts', 'pa12', 'nose', EX['nose'], dens='PA12')
add('LiDAR_Mast', LM.Shape, 'Frame + mounts', 'pa12', 'mast', EX['mast'], dens='PA12')
add('Fasteners_allowance', None, 'Frame + mounts', None, None, cat=25.0, cg=V(0, 0, -5))
for nm, (m, p, nut, disc) in MOTORS.items():
    add(m.Name, m.Shape, 'Motors', 'motor', 'motor', EX['motor'], cat=62.0)
    add(p.Name, p.Shape, 'ESC + props', 'prop', 'prop', EX['prop'], cat=8.0)
    add(nut.Name, nut.Shape, 'Motors', 'steel', 'prop', EX['prop'], cat=0.0)
    add(disc.Name, disc.Shape, None, 'prop_disc', 'prop', EX['prop'], cat=0.0, render=True)
add('ESC_4in1_6S', ESC.Shape, 'ESC + props', 'esc', 'esc', EX['esc'], cat=28.0)
add('Battery_6S_3300', BAT.Shape, 'Battery', 'battery', 'battery', EX['battery'], cat=490.0)
add('FC_Pixhawk6C_Mini', FC.Shape, 'FC + avionics', 'fc', 'fc', EX['fc'], cat=39.2)
add('PowerModule_Buck', PMB.Shape, 'FC + avionics', 'electronics', 'under', EX['under'], cat=30.0)
add('RadioPod_ESP32C3_LoRa_RX', RADIO.Shape, 'FC + avionics', 'electronics', 'under', EX['under'], cat=27.0)
add('LoRa_Antenna_868', ANT.Shape, 'FC + avionics', 'electronics', 'under', (-60, 0, 0), cat=8.0)
add('Pi5_Board', PI_BOARD.Shape, 'Pi + cooler', 'pcb', 'pi', EX['pi'], cat=46.0)
add('Pi5_PortBlock', PI_PORTS.Shape, 'Pi + cooler', 'metal', 'pi', EX['pi'], cat=0.0)
add('Pi5_ActiveCooler', PI_COOL.Shape, 'Pi + cooler', 'metal', 'pi', EX['pi'], cat=22.0)
add('LiDAR_STL19P', LIDAR.Shape, 'Sensors + lights', 'lidar', 'lidar', EX['lidar'], cat=47.0)
add('Camera_IMX327', CAM.Shape, 'Sensors + lights', 'camera', 'nose', EX['nose'], cat=15.0)
add('Thermal_MLX90640', THERM.Shape, 'Sensors + lights', 'metal', 'nose', EX['nose'], cat=5.0)
for o in IRL:
    add(o.Name, o.Shape, 'Sensors + lights', 'irled', 'nose', EX['nose'], cat=3.0)
add('Sensor_harness_mounts_allowance', None, 'Sensors + lights', None, None, cat=10.0, cg=V(40, 0, 40))
add('Gas_FlowCell', FCELL.Shape, 'Gas package', 'pa12', 'gas', EX['gas'], dens='PA12')
add('Gas_Sensors_O2_CO_H2S', GSENS.Shape, 'Gas package', 'metal', 'gas', EX['gas'], cat=36.0)
add('Gas_Pump', PUMP.Shape, 'Gas package', 'electronics', 'gas', EX['gas'], cat=25.0)
add('GasInlet_Tube', GTUBE.Shape, 'Gas package', 'ptfe', 'gas', EX['gas'], dens='PTFE')
add('GasInlet_Filter', GFILT.Shape, 'Gas package', 'amber', 'gas', EX['gas'], cat=2.0)
add('Cassette_Tube', TUBE.Shape, 'Cassette + 5 pucks', 'petg_clear', 'cassette', EX['cassette'], dens='PETG')
add('Cassette_TopCap', TC.Shape, 'Cassette + 5 pucks', 'pa12', 'cassette', EX['cassette'], dens='PA12')
add('BreakBeam_Collar', COL.Shape, 'Cassette + 5 pucks', 'pa12', 'cassette', EX['cassette'], dens='PA12')
add('BreakBeam_IR_Pair', BB.Shape, 'Cassette + 5 pucks', 'electronics', 'cassette', EX['cassette'], cat=2.0)
add('Pin_Release', PIN_R.Shape, 'Cassette + 5 pucks', 'steel', 'cassette', EX['cassette'], dens='Steel')
add('Pin_Capture', PIN_C.Shape, 'Cassette + 5 pucks', 'steel', 'cassette', EX['cassette'], dens='Steel')
add('Escapement_Cam', CAM_.Shape, 'Cassette + 5 pucks', 'pa12', 'cassette', EX['cassette'], dens='PA12')
add('Servo_MG90S', SERVO.Shape, 'Cassette + 5 pucks', 'servo', 'cassette', EX['cassette'], cat=13.4)
add('Servo_Bracket', SBR.Shape, 'Cassette + 5 pucks', 'pa12', 'cassette', EX['cassette'], dens='PA12')
puck_mass = 0.0
for k, l in enumerate(PUCKS):
    M = l.Placement.toMatrix()
    for o, rm, dens, cat in PUCK_PARTS:
        s = o.Shape.copy(); s.transformShape(M)
        ex = (EX['cassette'][0], EX['cassette'][1], EX['cassette'][2] - 40 * (P['n_pucks'] - k))
        add(f'Puck{k + 1}_{o.Name}', s, 'Cassette + 5 pucks', rm, f'puck{k + 1}', ex, dens=dens, cat=cat)
        if k == 0:
            puck_mass += REG[-1]['mass']
    tg = TAG.Shape.copy(); tg.transformShape(M)
    add(f'Puck{k + 1}_AprilTag', tg, 'Cassette + 5 pucks', 'tag', f'puck{k + 1}', ex, cat=PUCK_EXTRA_G)
    if k == 0:
        puck_mass += PUCK_EXTRA_G
add('Wiring_allowance', None, 'Wiring', None, None, cat=80.0, cg=V(0, 0, 0))
log('single puck mass %.1f g' % puck_mass)

# ---------------------------------------------------------------------------------------------
# CG balance: shift the battery so the hanging inner assembly has x_CG = 0 (pendulum stays level)
# ---------------------------------------------------------------------------------------------
def totals(filt=lambda r: True):
    m = sum(r['mass'] for r in REG if filt(r) and r['alloc'])
    c = sum((r['cg'] * r['mass'] for r in REG if filt(r) and r['alloc']), V()) * (1.0 / m)
    return m, c


inner = lambda r: r['alloc'] != 'Cage'
m_in, c_in = totals(inner)
dx = -c_in.x * m_in / 490.0
log('inner CG before balance', c_in, 'battery shift dx = %.1f mm' % dx)
ss.set('B' + str(2 + [r[0] for r in SS_ROWS].index('batt_x')), '%.1f' % dx)
doc.recompute()
for r in REG:
    if r['name'] == 'Battery_6S_3300':
        r['shape'] = BAT.Shape
        r['cg'] = r['cg'] + V(dx, 0, 0)
P['batt_x'] = dx

# ---------------------------------------------------------------------------------------------
# Mass properties + inertia
# ---------------------------------------------------------------------------------------------
m_all, c_all = totals()
m_in, c_in = totals(inner)
m_cage, c_cage = totals(lambda r: r['alloc'] == 'Cage')
I = [[0.0] * 3 for _ in range(3)]
for r in REG:
    if not r['alloc'] or r['mass'] <= 0:
        continue
    m = r['mass'] / 1000.0  # kg
    d = (r['cg'] - c_all) * 0.001
    dv = [d.x, d.y, d.z]
    # own inertia: solid shapes scaled to mass (uniform), point mass otherwise
    if r['shape'] is not None and r['shape'].Solids:
        vol = sum(s.Volume for s in r['shape'].Solids)
        rho_ = m / (vol * 1e-9)
        Mt = App.Matrix()
        for s in r['shape'].Solids:
            mi = s.MatrixOfInertia   # about the solid's own CoM, units mm^5 (volume-weighted)
            dd = (s.CenterOfMass - r['cg']) * 0.001
            for a in range(3):
                for b in range(3):
                    own = mi.A[a * 4 + b] * 1e-15 * rho_
                    sm = s.Volume * 1e-9 * rho_
                    ddv = [dd.x, dd.y, dd.z]
                    par = sm * ((dd.Length ** 2 if a == b else 0) - ddv[a] * ddv[b])
                    I[a][b] += own + par
    for a in range(3):
        for b in range(3):
            I[a][b] += m * ((sum(x * x for x in dv) if a == b else 0) - dv[a] * dv[b])

groups = {}
for r in REG:
    if not r['alloc']:
        continue
    g = groups.setdefault(r['alloc'], dict(mass=0.0, cad=0.0, cat=0.0, items=[]))
    g['mass'] += r['mass']
    g['cad' if r['src'] == 'CAD' else 'cat'] += r['mass']
    g['items'].append((r['name'], r['src'], r['mat'], r['mass']))
ALLOC = [('Cage', 400), ('Frame + mounts', 300), ('Motors', 250), ('ESC + props', 100), ('Battery', 490),
         ('FC + avionics', 100), ('Pi + cooler', 100), ('Sensors + lights', 140), ('Gas package', 100),
         ('Cassette + 5 pucks', 170), ('Wiring', 80)]
MP = dict(total_g=m_all, cg_mm=[c_all.x, c_all.y, c_all.z], inner_g=m_in, inner_cg_mm=[c_in.x, c_in.y, c_in.z],
          cage_g=m_cage, cage_cg_mm=[c_cage.x, c_cage.y, c_cage.z], inertia_kgm2_about_cg=I,
          batt_x_mm=dx, single_puck_g=puck_mass,
          groups={k: dict(mass=v['mass'], cad=v['cad'], cat=v['cat'],
                          items=[dict(name=a, src=b, mat=c, g=d_) for a, b, c, d_ in v['items']]) for k, v in groups.items()},
          alloc=ALLOC, density=DENS)
# puck-level CG (master, local coords)
pm = 0.0; pc = V()
for o, rm, dens, cat in PUCK_PARTS:
    s = o.Shape
    m = s.Volume / 1000 * DENS[dens] if dens else cat
    c = sum((q.CenterOfMass * q.Volume for q in s.Solids), V()) * (1.0 / sum(q.Volume for q in s.Solids))
    pm += m; pc += c * m
pc = pc * (1.0 / pm)
MP['puck_cg_local_mm'] = [pc.x, pc.y, pc.z]
MP['puck_parts'] = [dict(name=o.Name, src='CAD' if dens else 'catalogue', mat=dens or 'bought',
                         g=(o.Shape.Volume / 1000 * DENS[dens]) if dens else cat) for o, rm, dens, cat in PUCK_PARTS]
MP['puck_dome_radius_mm'] = rho
json.dump(MP, open(os.path.join(CAD, 'mass-properties.json'), 'w'), indent=1)
log('TOTAL %.0f g  CG (%.1f, %.1f, %.1f)  inner %.0f g CG z %.1f' % (m_all, c_all.x, c_all.y, c_all.z, m_in, c_in.z))

# ---------------------------------------------------------------------------------------------
# Internal clearance checks (design calculation)
# ---------------------------------------------------------------------------------------------
HULL = None
try:
    HULL = json.load(open(os.path.join(CAD, 'analysis.json')))['cage_inner_hull_min_mm']
except Exception:
    pass
CHK = dict(prop_to_parts=[], parts_vs_hull=[], overlaps=[])
envs = {}
for nm, (m, p, nut, disc) in MOTORS.items():
    b0 = disc.Placement.Base
    envs[nm] = Part.makeCylinder(P['prop_d'] / 2, 2 * P['prop_blade_half_t'], V(b0.x, b0.y, P['prop_z'] - P['prop_blade_half_t']))
skip = ('Prop_', 'PropNut_', 'PropDisc_', 'Motor_')
internal = [r for r in REG if r['shape'] is not None and r['alloc'] not in ('Cage', None) and not r['name'].startswith(skip)
            and r['name'] != 'Axle']
for nm, env in envs.items():
    best = (1e9, '')
    for r in internal:
        if r['shape'].BoundBox.isValid():
            dd = env.distToShape(r['shape'])[0]
            if dd < best[0]:
                best = (dd, r['name'])
    CHK['prop_to_parts'].append(dict(prop=nm, min_mm=best[0], nearest=best[1]))
worst = (1e9, '')
for r in internal + [r for r in REG if r['name'].startswith(('Prop_', 'Motor_'))]:
    pts, _ = r['shape'].tessellate(0.5)
    rm = max(p.Length for p in pts) if pts else 0
    if HULL and HULL - rm < worst[0]:
        worst = (HULL - rm, r['name'], rm)
CHK['parts_vs_hull'] = dict(hull_mm=HULL, worst_clear_mm=worst[0], part=worst[1], r_max_mm=worst[2] if len(worst) > 2 else None)
solids = [r for r in REG if r['shape'] is not None and r['alloc'] not in ('Cage', None)]
for a_ in range(len(solids)):
    for b_ in range(a_ + 1, len(solids)):
        A_, B_ = solids[a_]['shape'], solids[b_]['shape']
        if not A_.BoundBox.intersect(B_.BoundBox):
            continue
        try:
            v = A_.common(B_).Volume
        except Exception:
            continue
        if v > 1.0:
            CHK['overlaps'].append(dict(a=solids[a_]['name'], b=solids[b_]['name'], mm3=round(v, 1)))
json.dump(CHK, open(os.path.join(CAD, 'clearance-internal.json'), 'w'), indent=1)
log('prop->parts', [(c['prop'], round(c['min_mm'], 1), c['nearest']) for c in CHK['prop_to_parts']])
log('parts vs hull', CHK['parts_vs_hull'])
log('overlaps', CHK['overlaps'])

# ---------------------------------------------------------------------------------------------
# Save FCStd
# ---------------------------------------------------------------------------------------------
FCSTD = os.path.join(CAD, 'SURANG-SUTRA.FCStd')
doc.saveAs(FCSTD)
log('saved', FCSTD)

# ---------------------------------------------------------------------------------------------
# Meshes for Blender (one OBJ, one object per part) + manifest
# ---------------------------------------------------------------------------------------------
def write_obj(path, items, tol=0.05):
    with open(path, 'w') as f:
        f.write('# SURANG-SUTRA meshes (mm), generated by build_surang.py\n')
        off = 1
        for name, shape in items:
            pts, tris = shape.tessellate(tol)
            if not tris:
                continue
            f.write(f'o {name}\n')
            for p in pts:
                f.write('v %.4f %.4f %.4f\n' % (p.x, p.y, p.z))
            for t in tris:
                f.write('f %d %d %d\n' % (t[0] + off, t[1] + off, t[2] + off))
            off += len(pts)


man = []
items = []
for r in REG:
    if not r['render']:
        continue
    items.append((r['name'], r['shape']))
    bb = r['shape'].BoundBox
    man.append(dict(name=r['name'], rmat=r['rmat'], group=r['group'], explode=list(r['explode']),
                    center=[bb.Center.x, bb.Center.y, bb.Center.z], alloc=r['alloc']))
write_obj(os.path.join(CAD, 'mesh', 'assembly.obj'), items)
# puck master (local) for the exploded puck render
PEX = {'Puck_Shell_Base': -22, 'Puck_ChargePads': -34, 'Puck_LiPo_1S_400': -9, 'Puck_PCB': 6, 'Puck_ESP32C3_MINI1': 6,
       'Puck_RFM95W_868': 6, 'Puck_Antenna_Stub': 6, 'Puck_Passives_LED_Hall': 6, 'Puck_Bumper_TPU': 30,
       'Puck_Shell_Lid': 50, 'Puck_AprilTag': 66}
pitems, pman = [], []
for o, rm, dens, cat in PUCK_PARTS + [(TAG, 'tag', None, 0)]:
    nm = 'Puck_AprilTag' if o is TAG else o.Name
    pitems.append((nm, o.Shape))
    pman.append(dict(name=nm, rmat=rm, explode=[0, 0, PEX[nm]], center=list(o.Shape.BoundBox.Center)))
write_obj(os.path.join(CAD, 'mesh', 'puck.obj'), pitems, tol=0.02)
json.dump(dict(assembly=man, puck=pman, params=P,
               hub_xyz=[[c * R for c in U[i]] for i in range(len(U))], struts=struts),
          open(os.path.join(CAD, 'mesh', 'manifest.json'), 'w'), indent=0)
log('meshes written', len(items), 'objects')

# ---------------------------------------------------------------------------------------------
# STEP + STL exports
# ---------------------------------------------------------------------------------------------
STEP = os.path.join(CAD, 'step')
for objs, fn in (([ASM], 'SURANG-SUTRA-assembly.step'), ([CAGE], 'cage.step'), ([HUB_M], 'cage-hub.step'),
                 ([HUB_V], 'cage-hub-v5.step'), ([PH], 'pole-hub.step'), ([FRAME], 'frame.step'),
                 ([CASS], 'cassette.step'), ([PUCK], 'sutra-puck.step')):
    Import.export(objs, os.path.join(STEP, fn))
    log('STEP', fn, os.path.getsize(os.path.join(STEP, fn)) // 1024, 'kB')
STL = os.path.join(CAD, 'stl')
for o, fn in ((HUB_M, 'cage-hub-m6.stl'), (HUB_V, 'cage-hub-v5.stl'), (PH, 'pole-hub.stl'), (CAP, 'tpu-cap-hub.stl'),
              (POLECAP, 'tpu-cap-pole.stl'), (B1, 'puck-shell-base.stl'), (B2, 'puck-shell-lid.stl'),
              (B3, 'puck-bumper-tpu.stl')):
    msh = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.01, AngularDeflection=0.08, Relative=False)
    msh.write(os.path.join(STL, fn))
log('all done')
