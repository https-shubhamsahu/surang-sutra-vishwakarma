"""2V icosahedral geodesic cage geometry for SURANG.

One icosahedron vertex on each +/-Y (axle) pole. 42 hubs, 120 struts, 80 faces.
All lengths in mm.
"""
import numpy as np
from scipy.spatial import ConvexHull

R_CAGE = 290.0


def icosahedron_y_poles(R=R_CAGE):
    lat = np.arctan(0.5)  # 26.565 deg ring latitude
    pts = [(0.0, R, 0.0)]
    for i in range(5):
        az = np.radians(72.0 * i)
        pts.append((R * np.cos(lat) * np.cos(az), R * np.sin(lat), R * np.cos(lat) * np.sin(az)))
    for i in range(5):
        az = np.radians(72.0 * i + 36.0)
        pts.append((R * np.cos(lat) * np.cos(az), -R * np.sin(lat), R * np.cos(lat) * np.sin(az)))
    pts.append((0.0, -R, 0.0))
    return np.array(pts)


def _faces(P):
    hull = ConvexHull(P)
    F = hull.simplices.copy()
    # orient outward
    for k, (a, b, c) in enumerate(F):
        n = np.cross(P[b] - P[a], P[c] - P[a])
        if np.dot(n, P[a] + P[b] + P[c]) < 0:
            F[k] = (a, c, b)
    return F


def geodesic_2v(R=R_CAGE):
    """Return nodes (42x3), struts (120x2), faces (80x3), hub valence, strut class ('A'/'B')."""
    V = icosahedron_y_poles(R)
    F = _faces(V)
    assert len(F) == 20
    nodes = [tuple(v) for v in V]
    key = {}

    def mid(a, b):
        k = (min(a, b), max(a, b))
        if k not in key:
            m = V[a] + V[b]
            m = R * m / np.linalg.norm(m)
            key[k] = len(nodes)
            nodes.append(tuple(m))
        return key[k]

    faces = []
    for a, b, c in F:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        faces += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
    nodes = np.array(nodes)
    edges = set()
    for f in faces:
        for i in range(3):
            a, b = f[i], f[(i + 1) % 3]
            edges.add((min(a, b), max(a, b)))
    struts = np.array(sorted(edges))
    faces = np.array(faces)
    valence = np.bincount(struts.ravel(), minlength=len(nodes))
    L = np.linalg.norm(nodes[struts[:, 1]] - nodes[struts[:, 0]], axis=1)
    cls = np.where(L < L.mean(), "A", "B")
    return nodes, struts, faces, valence, cls


def describe(R=R_CAGE):
    nodes, struts, faces, val, cls = geodesic_2v(R)
    L = np.linalg.norm(nodes[struts[:, 1]] - nodes[struts[:, 0]], axis=1)
    lat = np.degrees(np.arcsin(np.clip(nodes[:, 1] / R, -1, 1)))
    return dict(
        n_nodes=len(nodes), n_struts=len(struts), n_faces=len(faces),
        L_A=float(L[cls == "A"].mean()), L_B=float(L[cls == "B"].mean()),
        n_A=int((cls == "A").sum()), n_B=int((cls == "B").sum()),
        n_pent=int((val == 5).sum()), n_hex=int((val == 6).sum()),
        hub_latitudes_deg=sorted(set(np.round(lat, 2).tolist())),
        total_strut_length_mm=float(L.sum()),
    )


if __name__ == "__main__":
    import json
    print(json.dumps(describe(), indent=1))
