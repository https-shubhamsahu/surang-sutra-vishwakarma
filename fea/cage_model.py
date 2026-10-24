"""SURANG cage + axle structural model builder (shared by linear and nonlinear solvers).

Coordinate system (cage frame): Y = axle. Units N, mm, MPa, kg for masses.
"""
from dataclasses import dataclass, field
import numpy as np
import scipy.sparse as sp

from geodesic import geodesic_2v, R_CAGE
from frame3d import Section, subdivide, local_frames, k_local, kg_local, big_T, assemble

G0 = 9.81  # m/s^2

# ------------------------------------------------------------------ materials (see README for sources)
GFRP3 = Section("GFRP rod 3 mm", E=40000, G=4000, do=3.0, rho=2.0e-3, s_allow=400, s_ult=800)
GFRP4 = Section("GFRP rod 4 mm", E=40000, G=4000, do=4.0, rho=2.0e-3, s_allow=400, s_ult=800)
GFRP5 = Section("GFRP rod 5 mm", E=40000, G=4000, do=5.0, rho=2.0e-3, s_allow=400, s_ult=800)
CFRP3 = Section("CFRP rod 3 mm", E=125000, G=5000, do=3.0, rho=1.55e-3, s_allow=600, s_ult=1500)
CFRP4 = Section("CFRP rod 4 mm", E=125000, G=5000, do=4.0, rho=1.55e-3, s_allow=600, s_ult=1500)


def cf_tube(do, di):
    return Section(f"CF tube {do:g}/{di:g} mm", E=100000, G=5000, do=do, di=di, rho=1.55e-3,
                   s_allow=500, s_ult=1000)


AXLE_10 = cf_tube(10, 8)

# TPU 95A cap: tensile modulus 26 MPa (Ultimaker TPU 95A TDS); bonded-pad shape-factor correction
E_TPU = 26.0
CAP_D, CAP_T = 18.0, 5.0


def cap_stiffness(E=E_TPU, D=CAP_D, t=CAP_T):
    S = (D / 2) / (2 * t)                    # shape factor = loaded area / free area
    Ec = E * (1 + 2 * S**2)                  # Gent bonded-pad apparent modulus
    return Ec * np.pi * D**2 / 4 / t         # N/mm


K_CAP = cap_stiffness()

M_TOTAL = 2.4     # kg all-up
M_CAGE = 0.40     # kg (allocation)
HUB_MASS_G = 3.0  # PA12 hub + TPU cap, g each (estimate)


@dataclass
class System:
    X: np.ndarray            # node coords
    elems: np.ndarray        # beam elements
    secs: list               # Section per element
    ref: np.ndarray          # reference dir per element
    owner: np.ndarray        # strut id (>=0) or -1 (axle +Y side) / -2 (axle -Y side)
    n_hub: int               # first n_hub nodes are cage hubs
    hubs: np.ndarray
    struts: np.ndarray
    strut_secs: list
    strut_L: np.ndarray
    poles: tuple             # (+Y pole hub, -Y pole hub)
    springs: list = field(default_factory=list)   # (nodeA, nodeB, dof_list, k)
    fixed: np.ndarray = None
    axle: Section = None
    axle_nodes: dict = None
    b_clamp: float = None
    n_sub: int = 1

    @property
    def nn(self):
        return len(self.X)


def build(strut_secs=None, n_sub=4, axle=AXLE_10, b_clamp=40.0, n_axle=10, R=R_CAGE,
          rigid_axle=False):
    nodes, struts, faces, val, cls = geodesic_2v(R)
    if strut_secs is None:
        strut_secs = [GFRP3] * len(struts)
    if isinstance(strut_secs, Section):
        strut_secs = [strut_secs] * len(struts)
    X, el, owner = subdivide(nodes, struts, n_sub)
    mid = 0.5 * (nodes[struts[:, 0]] + nodes[struts[:, 1]])
    ref = mid[owner] / np.linalg.norm(mid[owner], axis=1)[:, None]   # local z = outward radial
    secs = [strut_secs[s] for s in owner]
    pP = int(np.argmax(nodes[:, 1])); pM = int(np.argmin(nodes[:, 1]))
    sysm = System(X=X, elems=el, secs=secs, ref=ref, owner=owner, n_hub=len(nodes), hubs=nodes,
                  struts=struts, strut_secs=strut_secs,
                  strut_L=np.linalg.norm(nodes[struts[:, 1]] - nodes[struts[:, 0]], axis=1),
                  poles=(pP, pM), n_sub=n_sub, axle=axle, b_clamp=b_clamp)
    fixed = []
    if rigid_axle:
        for p in (pP, pM):
            fixed += [6 * p, 6 * p + 1, 6 * p + 2]
        fixed.append(6 * pP + 4)      # lock cage spin about Y (no torque in these load cases)
        sysm.fixed = np.array(fixed)
        sysm.axle = None
        return sysm
    # axle: from clamp (y = +/- b_clamp) to pole bearing (y = +/- R). Inner frame rigid between clamps.
    Xl = list(X); el2 = list(el); own2 = list(owner); secs2 = list(secs); ref2 = list(ref)
    axle_nodes = {}
    for sgn, pole, tag in ((+1, pP, -1), (-1, pM, -2)):
        ys = np.linspace(b_clamp, R, n_axle + 1)
        ids = []
        for y in ys:
            Xl.append(np.array([0.0, sgn * y, 0.0])); ids.append(len(Xl) - 1)
        for a, b in zip(ids[:-1], ids[1:]):
            el2.append((a, b)); own2.append(tag); secs2.append(axle); ref2.append(np.array([1.0, 0, 0]))
        fixed += list(range(6 * ids[0], 6 * ids[0] + 6))          # clamp in rigid inner frame
        # bearing: pin (translations) between axle tip and pole hub; spin locked at +Y only
        dofs = [0, 1, 2] + ([4] if sgn > 0 else [])
        sysm.springs.append((ids[-1], pole, dofs, 1e6))
        axle_nodes[sgn] = ids
    sysm.X = np.array(Xl); sysm.elems = np.array(el2); sysm.owner = np.array(own2)
    sysm.secs = secs2; sysm.ref = np.array(ref2); sysm.fixed = np.array(fixed)
    sysm.axle_nodes = axle_nodes
    return sysm


def spring_matrix(sysm):
    rows, cols, vals = [], [], []
    for a, b, dofs, k in sysm.springs:
        for d in dofs:
            ia, ib = 6 * a + d, 6 * b + d
            rows += [ia, ib, ia, ib]; cols += [ia, ib, ib, ia]; vals += [k, k, -k, -k]
    n = 6 * sysm.nn
    return sp.coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()


def cage_mass_g(strut_secs, struts_L, n_hubs=42, hub_g=HUB_MASS_G):
    rods = sum(s.rho * s.A * L for s, L in zip(strut_secs, struts_L))
    return rods, n_hubs * hub_g


def hub_info(R=R_CAGE):
    nodes, struts, faces, val, cls = geodesic_2v(R)
    lat = np.degrees(np.arcsin(np.clip(nodes[:, 1] / R, -1, 1)))
    return nodes, lat, val
