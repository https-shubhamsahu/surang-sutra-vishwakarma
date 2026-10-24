"""Nonlinear impact/crush cases and design variants for the SURANG cage."""
import numpy as np

from cage_model import (build, GFRP3, GFRP4, GFRP5, CFRP3, CFRP4, cf_tube, AXLE_10, K_CAP, M_TOTAL, G0,
                        R_CAGE, hub_info, cage_mass_g)
from corot import Corot
from geodesic import geodesic_2v

NODES, LAT, VAL = hub_info()
H_EQ = int([h for h in range(42) if abs(LAT[h]) < 1e-6][0])                       # equatorial hex hub
H_PENT = int([h for h in range(42) if abs(LAT[h] - 26.565) < 0.01][0])            # pentagon hub, 26.6 deg
H_31 = int([h for h in range(42) if abs(LAT[h] - 31.72) < 0.01][0])               # hex hub, 31.7 deg

_nodes, STRUTS, _f, _v, CLS = geodesic_2v()
STRUT_L = np.linalg.norm(_nodes[STRUTS[:, 1]] - _nodes[STRUTS[:, 0]], axis=1)
BAND = np.array([(abs(LAT[a]) < 32.0) and (abs(LAT[b]) < 32.0) for a, b in STRUTS])

E_DROP = M_TOTAL * G0 * 1.0 * 1000.0          # N.mm, 1.0 m drop
E_WALL = 0.5 * M_TOTAL * 2.0**2 * 1000.0      # N.mm, 2 m/s


def strut_layout(kind):
    if kind == "G3":
        return [GFRP3] * 120
    if kind == "G4":
        return [GFRP4] * 120
    if kind == "G5":
        return [GFRP5] * 120
    if kind == "C3":
        return [CFRP3] * 120
    if kind == "G4band":
        return [GFRP4 if b else GFRP3 for b in BAND]
    if kind == "G5band":
        return [GFRP5 if b else GFRP3 for b in BAND]
    raise KeyError(kind)


AXLES = {"CF10/8": cf_tube(10, 8), "CF12/10": cf_tube(12, 10), "CF15/13": cf_tube(15, 13),
         "CF17/15": cf_tube(17, 15), "CF20/18": cf_tube(20, 18), "rigid": None}

# soft cap options (bilinear): (k1 N/mm, stroke g1 mm, cap height mm)
CAPS = {"TPU95A-solid": (K_CAP, 0.0, 5.0), "TPU-soft15": (12.0, 12.0, 15.0), "TPU-soft20": (10.0, 16.0, 20.0)}


def design_mass(kind):
    secs = strut_layout(kind)
    rods, hubs = cage_mass_g(secs, STRUT_L)
    return rods * 1000 / 1000, hubs   # g (rho in g/mm^3)


def run(kind="G3", axle="CF10/8", cap="TPU95A-solid", hub=H_EQ, n_sub=4, E_stop=E_DROP, s_max=90.0,
        b_clamp=40.0, seed=7, imperfection=1 / 500, keep_states=False, ds0=0.5, verbose=False):
    secs = strut_layout(kind)
    if AXLES[axle] is None:
        sysm = build(secs, n_sub=n_sub, rigid_axle=True)
    else:
        sysm = build(secs, n_sub=n_sub, axle=AXLES[axle], b_clamp=b_clamp)
    k1, g1, ct = CAPS[cap]
    c = Corot(sysm, imperfection=imperfection, seed=seed, cap_k=K_CAP, cap_k1=k1, cap_g1=g1, cap_t=ct)
    n0 = sysm.hubs[hub] / np.linalg.norm(sysm.hubs[hub])
    mg = M_TOTAL * G0
    hist, reached = c.solve_floor(n0, R_CAGE, s_max=s_max, ds0=ds0, verbose=verbose,
                                  stop_energy=lambda s_, U: U >= E_stop + mg * s_ * (E_stop == E_DROP))
    allow = np.array([sec.s_allow for sec in sysm.secs])
    ult = np.array([sec.s_ult for sec in sysm.secs])
    cage = sysm.owner >= 0
    out = dict(kind=kind, axle=axle, cap=cap, hub=int(hub), n_sub=n_sub, reached=bool(reached))
    s = np.array([h["s"] for h in hist]); F = np.array([h["F"] for h in hist]); U = np.array([h["U"] for h in hist])
    Ucage = np.array([np.max((h["sig"] / allow)[cage]) for h in hist])
    Uult = np.array([np.max((h["sig"] / ult)[cage]) for h in hist])
    sig_c = np.array([h["sig_cage"] for h in hist]); sig_a = np.array([h["sig_axle"] for h in hist])
    brg = np.array([max([b["radial"] for b in h["bearing"]] + [0]) for h in hist])
    brg_ax = np.array([max([b["axial"] for b in h["bearing"]] + [0]) for h in hist])
    mis = np.array([max([b["misalign_deg"] for b in h["bearing"]] + [0]) for h in hist])
    ftan = np.array([h["ftan"] for h in hist])
    nact = np.array([h["nact"] for h in hist])
    out.update(s=s, F=F, U=U, Ucage=Ucage, Uult=Uult, sig_cage=sig_c, sig_axle=sig_a, brg=brg, brg_ax=brg_ax,
               mis=mis, ftan=ftan, nact=nact)

    def at_energy(E):
        i = np.searchsorted(U, E)
        if i >= len(U):
            return None
        return i

    def first(mask):
        idx = np.where(mask)[0]
        return int(idx[0]) if len(idx) else None

    ia, iu = first(Ucage >= 1.0), first(Uult >= 1.0)
    out["E_allow"] = float(U[ia]) / 1000 if ia is not None else float(U[-1]) / 1000
    out["E_allow_bounded"] = ia is not None
    out["E_ult"] = float(U[iu]) / 1000 if iu is not None else float(U[-1]) / 1000
    out["E_ult_bounded"] = iu is not None
    for tag, E in (("wall", E_WALL), ("drop", E_DROP)):
        i = at_energy(E)
        if i is None:
            out[tag] = None
        else:
            out[tag] = dict(s=float(s[i]), F=float(F[i]), Fmax=float(F[: i + 1].max()),
                            sig_cage=float(sig_c[: i + 1].max()), U_cage=float(Ucage[: i + 1].max()),
                            sig_axle=float(sig_a[: i + 1].max()), brg=float(brg[: i + 1].max()),
                            brg_ax=float(brg_ax[: i + 1].max()), mis=float(mis[: i + 1].max()),
                            state=int(i))
    out["first_buckle_F"] = float(F[: max(2, first(np.diff(F) < 0) or len(F))].max()) if len(F) > 2 else None
    if keep_states:
        out["hist"] = hist
        out["sysm"] = sysm
        out["X0"] = c.X0
    out["mass_rods_g"], out["mass_hubs_g"] = design_mass(kind)
    return out


def summary(o):
    def v(E):  # equivalent single-hub impact speed, m/s
        return float(np.sqrt(2 * E / M_TOTAL))
    r = dict(kind=o["kind"], axle=o["axle"], cap=o["cap"], hub=o["hub"],
             E_allow_J=round(o["E_allow"], 2), v_allow=round(v(o["E_allow"]), 2),
             E_ult_J=round(o["E_ult"], 2), v_ult=round(v(o["E_ult"]), 2),
             Fmax_N=round(float(o["F"].max()), 0), sig_axle_max=round(float(o["sig_axle"].max()), 0),
             mass_rods_g=round(o["mass_rods_g"], 0))
    for tag in ("wall", "drop"):
        if o[tag]:
            r[tag] = {k: (round(val, 1) if isinstance(val, float) else val) for k, val in o[tag].items()}
        else:
            r[tag] = "energy not reached within crush limit"
    return r
