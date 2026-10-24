"""2V icosahedral geodesic sphere with one icosahedron vertex on each +/-Y pole.

Pure-Python (no numpy) so it can be imported by freecadcmd, Blender and the
analysis script alike. Units: mm. Body axes: X forward, Y axle (left), Z up.
"""
import math


def _norm(v):
    l = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / l, v[1] / l, v[2] / l)


def icosahedron(phase_deg=0.0):
    """Unit icosahedron, vertex 0 = +Y, vertex 11 = -Y.

    phase_deg rotates the two 5-vertex rings about Y (cage roll angle)."""
    s = 1.0 / math.sqrt(5.0)
    rr = 2.0 / math.sqrt(5.0)
    ph = math.radians(phase_deg)
    v = [(0.0, 1.0, 0.0)]
    for k in range(5):
        a = ph + math.radians(72 * k)
        v.append((rr * math.cos(a), s, rr * math.sin(a)))
    for k in range(5):
        a = ph + math.radians(72 * k + 36)
        v.append((rr * math.cos(a), -s, rr * math.sin(a)))
    v.append((0.0, -1.0, 0.0))
    f = []
    for k in range(5):
        f.append((0, 1 + k, 1 + (k + 1) % 5))            # top cap
        f.append((1 + k, 6 + k, 1 + (k + 1) % 5))        # band, apex down
        f.append((1 + (k + 1) % 5, 6 + k, 6 + (k + 1) % 5))  # band, apex up
        f.append((11, 6 + (k + 1) % 5, 6 + k))           # bottom cap
    return v, f


def geodesic_2v(R=290.0, phase_deg=0.0):
    """Return (hubs, struts, faces).

    hubs   : list of (x, y, z) on the sphere of radius R (strut centreline nodes)
    struts : list of (i, j) index pairs, 120 of them
    faces  : list of (i, j, k) index triples, 80 of them
    hub_kind: list 'V' (original icosahedron vertex, valence 5) or 'M' (valence 6)
    """
    v, f = icosahedron(phase_deg)
    pts = list(v)
    kind = ['V'] * len(v)
    mid = {}

    def m(a, b):
        key = (min(a, b), max(a, b))
        if key not in mid:
            p = _norm(tuple((pts[a][i] + pts[b][i]) / 2 for i in range(3)))
            pts.append(p)
            kind.append('M')
            mid[key] = len(pts) - 1
        return mid[key]

    faces = []
    for a, b, c in f:
        ab, bc, ca = m(a, b), m(b, c), m(c, a)
        faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    edges = set()
    for a, b, c in faces:
        for i, j in ((a, b), (b, c), (c, a)):
            edges.add((min(i, j), max(i, j)))
    hubs = [(p[0] * R, p[1] * R, p[2] * R) for p in pts]
    return hubs, sorted(edges), faces, kind


if __name__ == '__main__':
    h, e, fa, k = geodesic_2v()
    print(len(h), 'hubs', len(e), 'struts', len(fa), 'faces')
    ls = sorted(set(round(math.dist(h[i], h[j]), 1) for i, j in e))
    print('chord lengths', ls)
