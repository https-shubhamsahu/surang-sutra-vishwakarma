"""Tiny KiCad 10 schematic writer.

Places library / custom symbols at rotation 0 (power symbols may rotate), computes pin end points
(schematic Y = -symbol Y), and connects pins with short wire stubs + local net labels or power symbols.
Every connection is recorded so the exported KiCad netlist can be checked against the intent.
"""
import uuid, re, copy, os
from kisym import parse, dump, flatten, pins as libpins, find, find1, val

GRID = 1.27


def U():
    return str(uuid.uuid4())


def f(v):
    v = round(v, 4)
    s = f"{v:.4f}".rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def rot(x, y, r):
    r %= 360
    return {0: (x, y), 90: (-y, x), 180: (-x, -y), 270: (y, -x)}[r]


VEC = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}   # schematic unit vectors (y down)

FONT = '(effects (font (size 1.27 1.27)){j})'


def eff(size=1.27, justify=None, bold=False, hide=False, color=None):
    j = f' (justify {justify})' if justify else ''
    b = ' (bold yes)' if bold else ''
    c = f' (color {color})' if color else ''
    return f'(effects (font (size {f(size)} {f(size)}){b}{c}){j})'


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


class Inst:
    def __init__(self, ref, lib_id, x, y, r, node, unit=1):
        self.ref, self.lib_id, self.x, self.y, self.r = ref, lib_id, x, y, r
        self.pins = {}
        for p in libpins(node):
            if p['unit'] not in (0, unit):
                continue
            xr, yr = rot(p['x'], p['y'], r)
            self.pins.setdefault(p['number'], dict(x=round(x + xr, 4), y=round(y - yr, 4),
                                                   out=(p['angle'] + 180 + r) % 360, name=p['name'],
                                                   type=p['type'], hidden=p['hidden'], number=p['number']))

    def pin(self, key):
        key = str(key)
        if key in self.pins:
            return self.pins[key]
        c = [p for p in self.pins.values() if p['name'] == key and not p['hidden']]
        if len(c) == 1:
            return c[0]
        c = [p for p in self.pins.values() if p['name'] == key]
        if c:
            return c[0]
        raise KeyError(f'{self.ref}: no pin {key!r}; have {[(p["number"], p["name"]) for p in self.pins.values()]}')


class Sch:
    POWER = {'GND': 'GND', '+3V3': '+3V3', 'VBUS': 'VBUS', '+5V': '+5V'}

    def __init__(self, project, paper='A3', title='', date='', rev='', company='', comments=()):
        self.project = project
        self.paper = paper
        self.root = U()
        self.tb = (title, date, rev, company, comments)
        self.libsyms = {}
        self.items = []
        self.insts = {}
        self.intent = {}       # ref -> {pin: net}
        self.points = []       # (x, y, kind, owner) for collision checks
        self.segments = []
        self.pwr_n = 0
        self.flg_n = 0
        self.extra_nodes = {}  # custom lib_id -> node
        self.hidden = set()

    # ---------------------------------------------------------------- symbols
    def register_custom(self, lib_id, sexpr_text):
        node = parse(sexpr_text)[0]
        node[1] = ('S', lib_id)
        self.extra_nodes[lib_id] = node

    def libnode(self, lib_id):
        if lib_id not in self.libsyms:
            if lib_id in self.extra_nodes:
                self.libsyms[lib_id] = self.extra_nodes[lib_id]
            else:
                lib, name = lib_id.split(':')
                self.libsyms[lib_id] = flatten(lib, name)
        return self.libsyms[lib_id]

    def lib_prop(self, node, key):
        for p in find(node, 'property'):
            if val(p[1]) == key:
                at = find1(p, 'at')
                return float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0
        return None

    def place(self, lib_id, ref, value, x, y, r=0, fp=None, ds=None, desc=None, fields=None, dnp=False,
              in_bom=True, on_board=True, refpos=None, valpos=None, hide_value=False, unit=1):
        node = self.libnode(lib_id)
        inst = Inst(ref, lib_id, x, y, r, node, unit)
        is_pwr = find1(node, 'power') is not None
        props = []

        def libpos(key, default):
            lp = self.lib_prop(node, key)
            if lp is None:
                return x + default[0], y + default[1], 0
            xr, yr = rot(lp[0], lp[1], r)
            return x + xr, y - yr, lp[2]

        name = lib_id.split(':')[1]
        twopin_v = name in ('R', 'C', 'C_Polarized', 'Fuse', 'R_Small', 'C_Small', 'Battery')
        if refpos is None:
            if twopin_v:
                refpos = (x + 2.54, y - 1.27, 0, 'left')
            else:
                rx, ry, ra = libpos('Reference', (0, -5))
                refpos = (rx, ry, 0, None)
        if valpos is None:
            if twopin_v:
                valpos = (x + 2.54, y + 1.27, 0, 'left')
            else:
                vx, vy, va = libpos('Value', (0, 5))
                valpos = (vx, vy, 0, None)
        if r:
            # KiCad shows field angle relative to the symbol: 90 on a 90/270 symbol reads horizontally,
            # and horizontal justification is mirrored for 90/180 rotations.
            flip = {'left': 'right', 'right': 'left'}

            def fix(pos):
                x0, y0 = pos[0], pos[1]
                j = pos[3] if len(pos) > 3 else None
                ang = 90 if r in (90, 270) else 0
                if j and r in (90, 180):
                    j = flip.get(j, j)
                return (x0, y0, ang, j)
            refpos, valpos = fix(refpos), fix(valpos)
        fpv = fp if fp is not None else self._libval(node, 'Footprint')
        dsv = ds if ds is not None else (self._libval(node, 'Datasheet') or '~')
        dsc = desc if desc is not None else (self._libval(node, 'Description') or '')

        def prop(k, v, pos, hide=False, justify=None, size=1.27):
            hx = ' (hide yes)' if hide else ''
            return (f'\t\t(property "{k}" "{esc(v)}" (at {f(pos[0])} {f(pos[1])} {f(pos[2] if len(pos) > 2 else 0)}){hx}\n'
                    f'\t\t\t{eff(size, justify)})\n')
        props.append(prop('Reference', ref, refpos, hide=is_pwr, justify=refpos[3] if len(refpos) > 3 else None))
        props.append(prop('Value', value, valpos, hide=hide_value, justify=valpos[3] if len(valpos) > 3 else None))
        props.append(prop('Footprint', fpv or '', (x, y, 0), hide=True))
        props.append(prop('Datasheet', dsv, (x, y, 0), hide=True))
        props.append(prop('Description', dsc, (x, y, 0), hide=True))
        for k, v in (fields or {}).items():
            props.append(prop(k, v, (x, y, 0), hide=True))
        pins_s = ''.join(f'\t\t(pin "{n}" (uuid "{U()}"))\n' for n in sorted(inst.pins))
        yn = lambda b: 'yes' if b else 'no'
        s = (f'\t(symbol (lib_id "{lib_id}") (at {f(x)} {f(y)} {r}) (unit {unit})\n'
             f'\t\t(exclude_from_sim no) (in_bom {yn(in_bom and not is_pwr)}) (on_board {yn(on_board and not is_pwr)}) (dnp {yn(dnp)})\n'
             f'\t\t(uuid "{U()}")\n' + ''.join(props) + pins_s +
             f'\t\t(instances (project "{self.project}" (path "/{self.root}" (reference "{ref}") (unit {unit}))))\n\t)\n')
        self.items.append(s)
        if not is_pwr:
            if ref in self.insts:
                raise ValueError('duplicate ref ' + ref)
            self.insts[ref] = inst
            self.intent[ref] = {}
            for p in inst.pins.values():
                self.points.append((p['x'], p['y'], 'pin', f'{ref}.{p["number"]}'))
                if p['hidden']:
                    self.hidden.add((ref, p['number']))
        return inst

    def _libval(self, node, key):
        for p in find(node, 'property'):
            if val(p[1]) == key:
                return val(p[2])
        return ''

    # ---------------------------------------------------------------- primitives
    def wire(self, *pts):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if (x1, y1) == (x2, y2):
                continue
            assert x1 == x2 or y1 == y2, 'non-orthogonal wire'
            self.items.append(f'\t(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))\n')
            self.segments.append(((x1, y1), (x2, y2)))

    def label(self, x, y, name, d):
        ang = {0: 0, 90: 90, 180: 180, 270: 270}[d]
        just = 'left bottom' if d in (0, 90) else 'right bottom'
        self.items.append(f'\t(label "{esc(name)}" (at {f(x)} {f(y)} {ang}) {eff(1.27, just)} (uuid "{U()}"))\n')
        self.points.append((x, y, 'label', name))

    def power(self, x, y, name, d):
        """power symbol whose pin sits at (x,y); body extends in direction d (schematic dir angle)."""
        self.pwr_n += 1
        is_gnd = name.startswith('GND')
        # body direction at rot 0: up for supplies (90), down for GND (270)
        base = 270 if is_gnd else 90
        r = (d - base) % 360
        bx, by = VEC[d]
        off = 3.2 if is_gnd else 3.0
        if d in (90, 270):
            vp = (x, y + by * (off + 1.0) + (0.6 if d == 90 else 0), 0, None)
        else:
            vp = (x + bx * (off + 1.6), y + 0.5, 0, 'left' if d == 0 else 'right')
        self.place(f'power:{self.POWER.get(name, name)}', f'#PWR{self.pwr_n:03d}', name, x, y, r=r,
                   valpos=vp, refpos=(x, y, 0))
        self.points.append((x, y, 'power', name))

    def pwr_flag(self, x, y, net, d=90, length=2.54):
        """PWR_FLAG with its pin at (x,y) body pointing d; stub away and label/power at the other end."""
        self.flg_n += 1
        r = (d - 90) % 360
        self.place('power:PWR_FLAG', f'#FLG{self.flg_n:02d}', 'PWR_FLAG', x, y, r=r,
                   valpos=(x + (2 if d != 180 else -2), y - 3.5 if d == 90 else y, 0, 'left' if d != 180 else 'right'),
                   refpos=(x, y, 0))
        ox, oy = VEC[(d + 180) % 360]
        ex, ey = x + ox * length, y + oy * length
        self.wire((x, y), (ex, ey))
        self._terminate(ex, ey, net, (d + 180) % 360)

    def nc(self, inst, key):
        p = inst.pin(key)
        self.items.append(f'\t(no_connect (at {f(p["x"])} {f(p["y"])}) (uuid "{U()}"))\n')
        self.intent[inst.ref][p['number']] = None

    def text(self, x, y, s, size=1.6, bold=False, justify='left top'):
        self.items.append(f'\t(text "{esc(s)}" (exclude_from_sim no) (at {f(x)} {f(y)} 0) {eff(size, justify, bold)} (uuid "{U()}"))\n')

    def rect(self, x1, y1, x2, y2, color='29 78 216 1', width=0.35, dash=True):
        t = 'dash' if dash else 'solid'
        self.items.append(f'\t(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {f(width)}) (type {t}) (color {color})) (fill (type none)) (uuid "{U()}"))\n')

    def _terminate(self, x, y, net, d):
        if net in self.POWER:
            self.power(x, y, net, d)
        else:
            self.label(x, y, net, d)

    # ---------------------------------------------------------------- connections
    def net(self, inst, key, net, stub=2.54, ld=None):
        p = inst.pin(key)
        d = p['out']
        vx, vy = VEC[d]
        ex, ey = p['x'] + vx * stub, p['y'] + vy * stub
        self.wire((p['x'], p['y']), (ex, ey))
        if net in self.POWER:
            self.power(ex, ey, net, d)
        else:
            if ld is None:
                ld = 0 if d in (90, 270) else d
            self.label(ex, ey, net, ld)
        self.intent[inst.ref][p['number']] = net

    def route(self, inst, key, net, moves, ld=None):
        """polyline from a pin through relative moves [(dx,dy),...]; terminal oriented along the last move."""
        p = inst.pin(key)
        pts = [(p['x'], p['y'])]
        for dx, dy in moves:
            pts.append((round(pts[-1][0] + dx, 4), round(pts[-1][1] + dy, 4)))
        self.wire(*pts)
        dx, dy = moves[-1]
        d = 0 if dx > 0 else 180 if dx < 0 else 270 if dy > 0 else 90
        ex, ey = pts[-1]
        if net in self.POWER:
            self.power(ex, ey, net, d)
        else:
            self.label(ex, ey, net, ld if ld is not None else (0 if d in (90, 270) else d))
        self.intent[inst.ref][p['number']] = net

    def junction(self, x, y):
        self.items.append(f'\t(junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))\n')

    def tie(self, inst, keys, net, depth=2.54):
        """pins on one edge (same out-direction, collinear) -> stubs, a common bar, one terminal in the middle."""
        ps = [inst.pin(k) for k in keys]
        d = ps[0]['out']
        vx, vy = VEC[d]
        ends = []
        for p in ps:
            e = (p['x'] + vx * depth, p['y'] + vy * depth)
            self.wire((p['x'], p['y']), e)
            ends.append(e)
            self.intent[inst.ref][p['number']] = net
        ends.sort()
        for a, b in zip(ends, ends[1:]):
            self.wire(a, b)
        mid = ends[len(ends) // 2]
        for e in ends[1:-1]:
            self.junction(*e)
        m2 = (mid[0] + vx * 2.54, mid[1] + vy * 2.54)
        self.wire(mid, m2)
        if net in self.POWER:
            self.power(m2[0], m2[1], net, d)
        else:
            self.label(m2[0], m2[1], net, 0)

    def nets(self, inst, mapping, stub=2.54):
        for k, n in mapping.items():
            if n is None:
                self.nc(inst, k)
            else:
                self.net(inst, k, n, stub)

    def link(self, a, ka, b, kb, net, how='hv', mid=None):
        """direct wire between two pins (L-route). net is the intended net name (for checking) and a label is
        dropped at pin a's end so the net carries a readable name."""
        pa, pb = a.pin(ka), b.pin(kb)
        x1, y1, x2, y2 = pa['x'], pa['y'], pb['x'], pb['y']
        if x1 == x2 or y1 == y2:
            self.wire((x1, y1), (x2, y2))
        elif how == 'hv':
            self.wire((x1, y1), (x2, y1), (x2, y2))
        elif how == 'vh':
            self.wire((x1, y1), (x1, y2), (x2, y2))
        elif how == 'hvh':
            xm = mid if mid is not None else round((x1 + x2) / 2 / GRID) * GRID
            self.wire((x1, y1), (xm, y1), (xm, y2), (x2, y2))
        self.intent[a.ref][pa['number']] = net
        self.intent[b.ref][pb['number']] = net

    # ---------------------------------------------------------------- output
    def check_geometry(self):
        """fail if a wire passes over a pin end or label it should not touch."""
        errs = []
        for (a, b) in self.segments:
            (x1, y1), (x2, y2) = a, b
            for (px, py, kind, owner) in self.points:
                on = (min(x1, x2) - 1e-6 <= px <= max(x1, x2) + 1e-6 and min(y1, y2) - 1e-6 <= py <= max(y1, y2) + 1e-6
                      and (x1 == x2 == px or y1 == y2 == py) if (x1 == x2 or y1 == y2) else False)
                if on and (px, py) not in (a, b):
                    errs.append(f'wire {a}-{b} passes over {kind} {owner} at {(px, py)}')
        # coincident pin ends of different symbols
        seen = {}
        for (px, py, kind, owner) in self.points:
            if kind != 'pin':
                continue
            k = (round(px, 3), round(py, 3))
            if k in seen and seen[k].split('.')[0] != owner.split('.')[0]:
                errs.append(f'pin {owner} coincides with {seen[k]} at {k}')
            seen[k] = owner
        return errs

    def save_intent(self, path):
        import pickle
        pickle.dump({'intent': self.intent, 'hidden': self.hidden}, open(path, 'wb'))

    def write(self, path):
        title, date, rev, company, comments = self.tb
        cm = ''.join(f'\t\t(comment {i + 1} "{esc(c)}")\n' for i, c in enumerate(comments))
        libs = ''.join('\t\t' + dump(n, 2) + '\n' for n in self.libsyms.values())
        s = (f'(kicad_sch\n\t(version 20250114)\n\t(generator "eeschema")\n\t(generator_version "9.0")\n'
             f'\t(uuid "{self.root}")\n\t(paper "{self.paper}")\n'
             f'\t(title_block\n\t\t(title "{esc(title)}")\n\t\t(date "{date}")\n\t\t(rev "{rev}")\n\t\t(company "{esc(company)}")\n{cm}\t)\n'
             f'\t(lib_symbols\n{libs}\t)\n' + ''.join(self.items) +
             '\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n')
        open(path, 'w').write(s)


def box_symbol(name, ref='U', value=None, left=(), right=(), top=(), bottom=(), width=None, fp='', ds='', desc='',
               keywords='', stacked=(), nc=(), hide_numbers=False):
    """Generate a rectangular custom symbol. Pin lists contain (number, name, type) or None for a gap."""
    value = value or name
    ch = 0.95  # mm per char at 1.27 font (approx)
    lmax = max([len(p[1]) for p in left if p] + [0])
    rmax = max([len(p[1]) for p in right if p] + [0])
    if width is None:
        width = max(15.24, (lmax + rmax) * ch + 6, len(top) * 2.54 + 5.08, len(bottom) * 2.54 + 5.08)
        width = round(width / 2.54 + 0.4999) * 2.54
    h_rows = max(len(left), len(right), 1)
    height = (h_rows + 1) * 2.54
    if top:
        height += 2.54
    if bottom:
        height += 2.54
    hw = width / 2
    y_top = round((height / 2) / 1.27) * 1.27
    y_bot = y_top - height
    L = []
    where = {}

    def pin(t, x, y, a, n, nm, hide=False):
        where[n] = (x, y, a)
        h = ' (hide yes)' if hide else ''
        return (f'(pin {t} line (at {f(x)} {f(y)} {a}) (length 2.54){h} (name "{esc(nm)}" (effects (font (size 1.27 1.27)))) '
                f'(number "{n}" (effects (font (size 1.27 1.27)))))')
    y0 = y_top - 2.54 - (2.54 if top else 0)
    for i, p in enumerate(left):
        if p:
            L.append(pin(p[2], -hw - 2.54, y0 - i * 2.54, 0, p[0], p[1]))
    for i, p in enumerate(right):
        if p:
            L.append(pin(p[2], hw + 2.54, y0 - i * 2.54, 180, p[0], p[1]))
    for i, p in enumerate(top):
        if p:
            xx = -((len(top) - 1) * 2.54) / 2 + i * 2.54
            xx = round(xx / 2.54) * 2.54
            L.append(pin(p[2], xx, y_top + 2.54, 270, p[0], p[1]))
    for i, p in enumerate(bottom):
        if p:
            xx = -((len(bottom) - 1) * 2.54) / 2 + i * 2.54
            xx = round(xx / 2.54) * 2.54
            L.append(pin(p[2], xx, y_bot - 2.54, 90, p[0], p[1]))
    for (n, nm, t, anchor) in stacked:
        x, y, a = where[anchor]
        L.append(pin(t, x, y, a, n, nm, hide=True))
    for i, n in enumerate(nc):
        L.append(pin('no_connect', -hw + 2.54, y_top - 2.54 - i * 1.27, 180, n, 'NC', hide=True))
    hidep = '(hide yes)'
    hn = ' (pin_numbers (hide yes))' if hide_numbers else ''
    s = f'''(symbol "{name}"{hn} (exclude_from_sim no) (in_bom yes) (on_board yes)
  (property "Reference" "{ref}" (at {f(-hw)} {f(y_top + 1.27)} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))
  (property "Value" "{esc(value)}" (at {f(-hw)} {f(y_bot - 1.27)} 0) (effects (font (size 1.27 1.27)) (justify left top)))
  (property "Footprint" "{fp}" (at 0 0 0) {hidep} (effects (font (size 1.27 1.27))))
  (property "Datasheet" "{ds}" (at 0 0 0) {hidep} (effects (font (size 1.27 1.27))))
  (property "Description" "{esc(desc)}" (at 0 0 0) {hidep} (effects (font (size 1.27 1.27))))
  (property "ki_keywords" "{keywords}" (at 0 0 0) {hidep} (effects (font (size 1.27 1.27))))
  (symbol "{name}_0_1" (rectangle (start {f(-hw)} {f(y_top)}) (end {f(hw)} {f(y_bot)}) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol "{name}_1_1" {' '.join(L)})
)'''
    return s, (hw, y_top, y_bot)


def read_netlist(path):
    """{(ref,pin): netname} from a KiCad s-expression netlist."""
    from kisym import parse
    tree = parse(open(path).read())[0]
    nets = find1(tree, 'nets')
    out = {}
    for n in find(nets, 'net'):
        name = val(find1(n, 'name')[1])
        for nd in find(n, 'node'):
            out[(val(find1(nd, 'ref')[1]), val(find1(nd, 'pin')[1]))] = name
    return out


def check_netlist(sch, path):
    """compare intended connectivity (sch.intent) with the exported netlist; returns list of problems."""
    actual = read_netlist(path)
    probs = []
    groups = {}
    for ref, pm in sch.intent.items():
        for pin, net in pm.items():
            if net is None:
                continue
            groups.setdefault(net, set()).add((ref, pin))
    act_groups = {}
    for k, n in actual.items():
        if k[0].startswith('#'):
            continue
        act_groups.setdefault(n, set()).add(k)
    for net, members in groups.items():
        anets = {actual.get(m, '<unconnected>') for m in members}
        if len(anets) != 1:
            probs.append(f'intended net {net} split across {anets}')
            continue
        an = anets.pop()
        extra = act_groups.get(an, set()) - members
        # pins with no recorded intent that landed on this net are suspicious
        extra = {e for e in extra if sch.intent.get(e[0], {}).get(e[1], 'unset') != None and e not in sch.hidden}
        if extra:
            probs.append(f'net {net} (kicad {an}) has unexpected members {sorted(extra)}')
    # pins intended NC but connected
    for ref, pm in sch.intent.items():
        for pin, net in pm.items():
            if net is None:
                an = actual.get((ref, pin), '')
                if an and not an.startswith('unconnected-'):
                    if len(act_groups.get(an, ())) > 1:
                        probs.append(f'{ref}.{pin} intended NC but on {an}')
    return probs


def check_saved(intent_pkl, netfile):
    import pickle
    d = pickle.load(open(intent_pkl, 'rb'))

    class _S:
        pass
    o = _S()
    o.intent, o.hidden = d['intent'], d['hidden']
    return check_netlist(o, netfile)
