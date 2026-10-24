"""SURANG-SUTRA render script (Blender 5.x, Cycles).

    blender -b --factory-startup --python renders/render.py -- <view> [--samples 96] [--width 2400] [--preview]

views: hero | exploded | cutaway | puck | side | plan
Meshes come from cad/mesh/ (written by cad/build_surang.py). Output: renders/_raw/<view>.png (RGBA) plus
renders/_raw/<view>.json (camera + projected label anchors). renders/annotate.py composites them onto
white and adds labels/dimensions.
"""
import bpy, sys, os, json, math
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

ROOT = '/home/shubh/_Active_Projects/SURANG-SUTRA-VK26'
MESH = os.path.join(ROOT, 'cad', 'mesh')
RAW = os.path.join(ROOT, 'renders', '_raw')
os.makedirs(RAW, exist_ok=True)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['hero']
VIEW = argv[0]
def arg(name, default, typ=float):
    return typ(argv[argv.index(name) + 1]) if name in argv else default
SAMPLES = arg('--samples', 96, int)
WIDTH = arg('--width', 2400, int)
PREVIEW = '--preview' in argv

MAN = json.load(open(os.path.join(MESH, 'manifest.json')))
P = MAN['params']
R = P['cage_R']

# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for dev_type in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = dev_type
            prefs.refresh_devices()
            gpus = [d for d in prefs.devices if d.type == dev_type]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == dev_type
                sc.cycles.device = 'GPU'
                print('render device', dev_type, [d.name for d in gpus])
                break
        except Exception as e:
            print('device', dev_type, 'unavailable', e)
except Exception as e:
    print('GPU setup failed, CPU', e)
sc.cycles.samples = 16 if PREVIEW else SAMPLES
sc.cycles.use_denoising = True
try:
    sc.cycles.denoiser = 'OPTIX' if sc.cycles.device == 'GPU' else 'OPENIMAGEDENOISE'
except Exception:
    pass
sc.cycles.max_bounces = 8
sc.cycles.transparent_max_bounces = 16
sc.cycles.transmission_bounces = 8
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '8'

world = bpy.data.worlds.new('W'); sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (1, 1, 1, 1)
bg.inputs['Strength'].default_value = arg('--world', 0.28)

# ------------------------------------------------------------------ materials
def hexrgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)

MATS = {
    'gfrp':       dict(c='#D9C36E', r=0.3, coat=0.3),
    'pa12':       dict(c='#D5D9DF', r=0.62),
    'tpu':        dict(c='#1D4ED8', r=0.45),
    'carbon':     dict(c='#23272E', r=0.28, coat=0.6),
    'motor':      dict(c='#3B4250', r=0.3, m=0.85),
    'prop':       dict(c='#0F172A', r=0.35),
    'prop_disc':  dict(c='#94A3B8', r=0.2, a=0.10),
    'battery':    dict(c='#475569', r=0.5),
    'battery_small': dict(c='#C9CED6', r=0.35, m=0.6),
    'esc':        dict(c='#111827', r=0.4),
    'fc':         dict(c='#334155', r=0.35, m=0.5),
    'electronics': dict(c='#1E293B', r=0.45),
    'pcb':        dict(c='#15803D', r=0.4),
    'metal':      dict(c='#A7ADB6', r=0.3, m=1.0),
    'lidar':      dict(c='#0F172A', r=0.3),
    'camera':     dict(c='#111827', r=0.3),
    'irled':      dict(c='#7F1D1D', r=0.2),
    'ptfe':       dict(c='#F1F5F9', r=0.45),
    'amber':      dict(c='#D97706', r=0.5),
    'petg_clear': dict(c='#DBEAFE', r=0.08, trans=1.0, ior=1.5),
    'petg_white': dict(c='#EEF1F5', r=0.42),
    'steel':      dict(c='#9CA3AF', r=0.25, m=1.0),
    'servo':      dict(c='#1F2937', r=0.45),
    'module':     dict(c='#8B95A5', r=0.3, m=0.9),
    'brass':      dict(c='#B7791F', r=0.3, m=1.0),
    'tag':        dict(c='#0F172A', r=0.6),
}
_mcache = {}
def mat(key):
    if key in _mcache:
        return _mcache[key]
    spec = MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hexrgb(spec['c'])
    b.inputs['Roughness'].default_value = spec.get('r', 0.5)
    b.inputs['Metallic'].default_value = spec.get('m', 0.0)
    if spec.get('coat'):
        b.inputs['Coat Weight'].default_value = spec['coat']
    if spec.get('trans'):
        b.inputs['Transmission Weight'].default_value = spec['trans']
        b.inputs['IOR'].default_value = spec.get('ior', 1.45)
    if 'a' in spec:
        b.inputs['Alpha'].default_value = spec['a']
    _mcache[key] = m
    return m

# ------------------------------------------------------------------ import
def import_obj(fn):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=os.path.join(MESH, fn), forward_axis='Y', up_axis='Z', global_scale=0.001)
    objs = [o for o in bpy.data.objects if o not in before]
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception as e:
        print('smooth failed', e)
    for o in objs:
        o.select_set(False)
    return {o.name: o for o in objs}

if VIEW == 'puck':
    OB = import_obj('puck.obj')
    ENT = {e['name']: e for e in MAN['puck']}
else:
    OB = import_obj('assembly.obj')
    ENT = {e['name']: e for e in MAN['assembly']}
for nm, o in OB.items():
    e = ENT.get(nm)
    if e is None:
        print('no manifest entry for', nm); continue
    o.data.materials.clear()
    o.data.materials.append(mat(e['rmat']))
    if e['rmat'] == 'prop_disc':
        o.visible_shadow = False

def hide(o):
    o.hide_render = True; o.hide_viewport = True

def is_cage(e):
    return e.get('alloc') == 'Cage'

# ------------------------------------------------------------------ view-specific scene edits
labels = {}     # name -> world point (m)
floor_z = -(R + P['hub_h'] / 2 + P['cap_h']) * math.cos(math.radians(18)) / 1000.0
shadow = VIEW in ('hero', 'cutaway')
cam_az, cam_el, lens, ortho = -32.0, 20.0, 70.0, None
aspect = (3, 2)

def group_centre(pred):
    pts = []
    for nm, o in OB.items():
        e = ENT.get(nm)
        if e and pred(e) and not o.hide_render:
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    if not pts:
        return None
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (lo + hi) / 2, lo, hi

if VIEW == 'exploded':
    cam_az, cam_el, lens = -28.0, 22.0, 60.0
    aspect = (16, 10)
    ze = P['cassette_exit_z']
    for nm, o in OB.items():
        e = ENT.get(nm)
        if e:
            ex = Vector(e['explode'])
            if e['group'].startswith('puck'):
                K = int(e['group'][4:])
                orig_bottom = ze + 4.5 + P['puck_h'] * (K - 1)
                target = ze - 230 - 45 - 50 * (5 - K)
                ex = Vector((0, 90, target - orig_bottom))
            o.location = ex * 0.001
    bpy.context.view_layer.update()
    G = {
        'Geodesic cage, +Y half': lambda e: e['group'] == 'cage_pos',
        'Geodesic cage, -Y half': lambda e: e['group'] == 'cage_neg',
        'Pole hub + 6800 bearing': lambda e: e['group'] == 'pole_pos',
        '7-inch tri-blade props': lambda e: e['group'] == 'prop' and e['rmat'] == 'prop',
        '2809 motors': lambda e: e['group'] == 'motor',
        'Carbon X frame + axle': lambda e: e['group'] in ('frame',),
        'Avionics deck': lambda e: e['group'] == 'deck',
        '4-in-1 ESC': lambda e: e['group'] == 'esc',
        'Pixhawk 6C Mini': lambda e: e['group'] == 'fc',
        'Pi 5 + cooler': lambda e: e['group'] == 'pi',
        '2D LiDAR': lambda e: e['group'] in ('lidar',),
        'Camera + thermal + IR': lambda e: e['group'] == 'nose',
        'Gas flow cell + pump': lambda e: e['group'] == 'gas',
        '6S 3300 mAh': lambda e: e['group'] == 'battery',
        'Cassette + escapement': lambda e: e['group'] == 'cassette',
        '5 SUTRA pucks': lambda e: e['group'].startswith('puck'),
    }
    for k, f in G.items():
        g = group_centre(f)
        if g:
            labels[k] = dict(c=list(g[0]), lo=list(g[1]), hi=list(g[2]))
elif VIEW == 'cutaway':
    cam_az, cam_el, lens = 38.0, 16.0, 70.0
    aspect = (2, 1)
    v = Vector((math.cos(math.radians(cam_az)), math.sin(math.radians(cam_az)), 0))
    for nm, o in OB.items():
        e = ENT.get(nm)
        if e and is_cage(e) and e['group'] in ('cage_pos', 'cage_neg'):
            c = Vector(e['center'])
            if c.dot(v) > -0.05 * R:
                hide(o)
    bpy.context.view_layer.update()
    bx = P['batt_x']
    y0c = P['cassette_y']
    vis_caps = [(ENT[n]['center'], n) for n, o in OB.items() if n.startswith('Cap_') and not o.hide_render]
    top_cap = max(vis_caps, key=lambda c: c[0][2])[0]
    vis_str = [ENT[n]['center'] for n, o in OB.items() if n.startswith('Strut_') and not o.hide_render]
    far = min(vis_str, key=lambda c: (c[0] + 60) ** 2 + (c[1] + 200) ** 2 + (c[2] - 160) ** 2)
    ANCH = {
        '2D LiDAR (STL-19P)': (15, 11.7, 82), 'Pi 5 + active cooler': (0, 28, 45.5),
        'Pixhawk 6C Mini (FC)': (8, 19.5, 33), 'IMX327 + MLX90640 + 850 nm IR': (78, 0, 54),
        '10 mm carbon axle on 6800 bearings': (0, 170, 0), '6S 3300 mAh pack': (bx + 62, 10, -45),
        '7-inch X frame, 295 mm diagonal': (62, 62, -9), 'Gas inlet (pumped flow cell)': (224, -40, -29),
        'Puck cassette, 5 SUTRA': (0, y0c + 30.2, -75), 'MG90S escapement servo': (15, y0c + 45, -104),
        'IR break-beam at the exit': (0, y0c + 34, -132), 'Pole hub with 6800 bearing': (0, 291, 14),
        'TPU 95A cap on PA12 hub (42)': tuple(top_cap), '3 mm GFRP strut (120)': tuple(far),
    }
    for k, w in ANCH.items():
        c = Vector(w) * 0.001
        labels[k] = dict(c=list(c), lo=list(c), hi=list(c))
    pick = {}
    for k, f in pick.items():
        g = group_centre(f)
        if g:
            labels[k] = dict(c=list(g[0]), lo=list(g[1]), hi=list(g[2]))
elif VIEW == 'hero':
    cam_az, cam_el, lens = -34.0, 19.0, 70.0
elif VIEW == 'side':
    ortho = dict(dir='side', scale=0.70, centre=(0.0, -0.035))
    aspect = (1, 1); shadow = False
    for nm, o in OB.items():      # section at y = 0: drop the near (-Y) half of the cage
        e = ENT.get(nm)
        if e and is_cage(e) and e['center'][1] < -1.0:
            hide(o)
elif VIEW == 'bottom':
    ortho = dict(dir='bottom', scale=0.70, centre=(0.0, 0.0))
    aspect = (1, 1); shadow = False
    for nm, o in OB.items():      # keep only the lower cap of the cage (z < -150) in front of the internals
        e = ENT.get(nm)
        if e and is_cage(e) and e['center'][2] > -150:
            hide(o)
elif VIEW == 'plan':
    ortho = dict(dir='plan', scale=0.70, centre=(0.0, 0.0))
    aspect = (1, 1); shadow = False
    for nm, o in OB.items():
        e = ENT.get(nm)
        if e and is_cage(e) and e['center'][2] > P['prop_z'] + 0.0:
            hide(o)
elif VIEW == 'puck':
    cam_az, cam_el, lens = -30.0, 24.0, 85.0
    aspect = (4, 5); shadow = False
    for nm, o in OB.items():
        e = ENT.get(nm)
        if e:
            o.location = Vector(e['explode']) * 0.001
        if nm == 'Puck_AprilTag':
            hide(o)
    # AprilTag-style placeholder decal (pattern is illustrative, not a specific tag ID)
    N = 10; px = 40
    img = bpy.data.images.new('tag', N * px, N * px)
    bits = [0b101101, 0b010011, 0b111000, 0b001110, 0b110101, 0b011010]
    pix = []
    for yy in range(N * px):
        for xx in range(N * px):
            i, j = xx // px, N - 1 - yy // px
            if i in (0, N - 1) or j in (0, N - 1):
                v = 1.0
            elif i in (1, N - 2) or j in (1, N - 2):
                v = 0.0
            else:
                v = float((bits[j - 2] >> (i - 2)) & 1)
            pix += [v, v, v, 1.0]
    img.pixels = pix
    bpy.ops.mesh.primitive_plane_add(size=0.0304, location=(0, 0, (17.8 + 0.1 + ENT['Puck_AprilTag']['explode'][2]) / 1000))
    tagp = bpy.context.active_object
    tm = bpy.data.materials.new('tagimg'); tm.use_nodes = True
    tex = tm.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Closest'
    bsdf = tm.node_tree.nodes['Principled BSDF']
    tm.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.9
    bsdf.inputs['Specular IOR Level'].default_value = 0.1
    tagp.data.materials.append(tm)
    bpy.context.view_layer.update()
    ca, sa = math.cos(math.radians(-30)), math.sin(math.radians(-30))
    PA = {'Puck_AprilTag': (9, -9, 17.95), 'Puck_Shell_Lid': (14, -14, 19.0), 'Puck_Bumper_TPU': (28 * ca, 28 * sa, 9),
          'Puck_ESP32C3_MINI1': (-9.7, -6.7, 11.4), 'Puck_RFM95W_868': (12, -3, 10.8), 'Puck_Antenna_Stub': (16, 14, 14),
          'Puck_Passives_LED_Hall': (-8, 9, 10), 'Puck_PCB': (21, -9, 9.0), 'Puck_LiPo_1S_400': (9, -6, 6.8),
          'Puck_Shell_Base': (26 * ca, 26 * sa, 5), 'Puck_ChargePads': (12.5, -1.5, 0)}
    for nm, w in PA.items():
        c = (Vector(w) + Vector(ENT[nm]['explode'])) * 0.001
        labels[nm] = dict(c=list(c), lo=list(c), hi=list(c))

# ------------------------------------------------------------------ lights
def area(name, loc, target, size, energy, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.size = size; ld.energy = energy; ld.color = color
    lo = bpy.data.objects.new(name, ld); sc.collection.objects.link(lo)
    lo.location = loc
    d = Vector(target) - Vector(loc)
    lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return lo

S = 0.4 if VIEW == 'puck' else 1.0
LS = arg('--light', 1.0)
area('Key', (2.2 * S, -2.0 * S, 2.6 * S), (0, 0, 0), 2.2 * S, 170 * S * S * LS)
area('Fill', (-1.6 * S, -2.6 * S, 0.8 * S), (0, 0, 0), 2.5 * S, 60 * S * S * LS)
area('Rim', (-1.8 * S, 2.2 * S, 2.4 * S), (0, 0, 0), 2.0 * S, 110 * S * S * LS)
area('Top', (0, 0, 3.0 * S), (0, 0, 0), 3.0 * S, 50 * S * S * LS)
if VIEW == 'bottom':
    area('Under', (0.8, -1.0, -2.6), (0, 0, 0), 2.5, 160 * LS)
    area('Under2', (-1.2, 1.0, -2.2), (0, 0, 0), 2.5, 70 * LS)

if shadow:
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, floor_z))
    pl = bpy.context.active_object
    pl.is_shadow_catcher = True

# ------------------------------------------------------------------ camera
cd = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam)
sc.camera = cam
W = WIDTH if not PREVIEW else 900
H = int(round(W * aspect[1] / aspect[0]))
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
cd.clip_start, cd.clip_end = 0.01, 50
cd.sensor_fit = 'AUTO'

vis = [o for o in sc.objects if o.type == 'MESH' and not o.hide_render and o.name in OB]
corners = [o.matrix_world @ Vector(c) for o in vis for c in o.bound_box]

if ortho:
    cd.type = 'ORTHO'
    cd.ortho_scale = ortho['scale']
    cx, cz = ortho['centre']
    if ortho['dir'] == 'side':      # look along +Y from -Y; +X right, +Z up
        cam.location = (cx, -5.0, cz)
        cam.rotation_euler = (math.radians(90), 0, 0)
    elif ortho['dir'] == 'bottom':  # look up +Z from below; +X right, -Y up
        cam.location = (cx, cz, -5.0)
        cam.rotation_euler = (math.radians(180), 0, 0)
    else:                           # look down -Z; +X right, +Y up
        cam.location = (cx, cz, 5.0)
        cam.rotation_euler = (0, 0, 0)
else:
    cd.lens = lens
    az, el = math.radians(cam_az), math.radians(cam_el)
    dvec = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    lo = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
    hi = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
    tgt = (lo + hi) / 2
    dist = (hi - lo).length * 1.6
    margin = 0.06 if VIEW != 'puck' else 0.10
    for it in range(6):
        cam.location = tgt + dvec * dist
        cam.rotation_euler = (-dvec).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        pr = [world_to_camera_view(sc, cam, p) for p in corners]
        x0, x1 = min(p.x for p in pr), max(p.x for p in pr)
        y0, y1 = min(p.y for p in pr), max(p.y for p in pr)
        # recentre target in the image plane
        right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
        up = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))
        fov = 2 * math.atan(cd.sensor_width / (2 * cd.lens))
        if W >= H:
            fw = 2 * dist * math.tan(fov / 2); fh = fw * H / W
        else:
            fh = 2 * dist * math.tan(fov / 2); fw = fh * W / H
        tgt += right * ((x0 + x1) / 2 - 0.5) * fw + up * ((y0 + y1) / 2 - 0.5) * fh
        span = max((x1 - x0) / (1 - 2 * margin), (y1 - y0) / (1 - 2 * margin))
        dist *= span
    cam.location = tgt + dvec * dist
    bpy.context.view_layer.update()

# ------------------------------------------------------------------ render + metadata
out = os.path.join(RAW, f'{VIEW}{"_preview" if PREVIEW else ""}.png')
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
meta = dict(view=VIEW, width=W, height=H, ortho=ortho, floor_z_m=floor_z, labels={})
for k, v in labels.items():
    p = world_to_camera_view(sc, cam, Vector(v['c']))
    cs = [(a, b, cc) for a in (v['lo'][0], v['hi'][0]) for b in (v['lo'][1], v['hi'][1]) for cc in (v['lo'][2], v['hi'][2])]
    qs = [world_to_camera_view(sc, cam, Vector(c)) for c in cs]
    meta['labels'][k] = dict(px=[p.x * W, (1 - p.y) * H], world=v['c'],
                             box=[[q.x * W, (1 - q.y) * H] for q in qs])
# some fixed world points for annotations
def proj(pt):
    p = world_to_camera_view(sc, cam, Vector(pt))
    return [p.x * W, (1 - p.y) * H]
meta['points'] = {'origin': proj((0, 0, 0))}
json.dump(meta, open(out.replace('.png', '.json'), 'w'), indent=1)
print('WROTE', out)
