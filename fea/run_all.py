"""SURANG Stage-2 structural analysis driver.

Runs: linear frame + truss FEA, linear buckling, mesh convergence, geometrically nonlinear
impact/crush analysis (design iteration), component checks. Writes data/fea_results.pkl and results.json.
Usage:  .venv/bin/python run_all.py
"""
import json, os, pickle, time
from multiprocessing import Pool
import numpy as np

from cage_model import (build, K_CAP, M_TOTAL, G0, R_CAGE, GFRP3, GFRP4, cage_mass_g, cap_stiffness, E_TPU)
from linear import Linear, truss_case
from nl_cases import (run, strut_layout, AXLES, CAPS, H_EQ, H_PENT, H_31, LAT, VAL, STRUTS, STRUT_L, BAND,
                      E_DROP, E_WALL)
import components as comp

HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
H_58 = int([h for h in range(42) if abs(LAT[h] - 58.28) < 0.01][0])
HUBS = {"eq_0deg": H_EQ, "pent_26.6deg": H_PENT, "hex_31.7deg": H_31, "hex_58.3deg": H_58}
MG = M_TOTAL * G0

DESIGNS = {
    "D0_baseline": ("G3", "CF10/8", "TPU95A-solid"),
    "D1_CFRP3": ("C3", "CF10/8", "TPU95A-solid"),
    "D2_softcaps": ("G3", "CF10/8", "TPU-soft20"),
    "D3_GFRP4_axle10": ("G4", "CF10/8", "TPU95A-solid"),
    "D4_band4_axle15_soft": ("G4band", "CF15/13", "TPU-soft20"),
    "REC_GFRP4_axle15_soft": ("G4", "CF15/13", "TPU-soft20"),
}
LABEL = {
    "D0_baseline": "Baseline: 3 mm GFRP, 10/8 axle, solid TPU caps",
    "D1_CFRP3": "3 mm CFRP rods",
    "D2_softcaps": "3 mm GFRP + soft TPU caps",
    "D3_GFRP4_axle10": "4 mm GFRP, 10/8 axle",
    "D4_band4_axle15_soft": "4 mm GFRP band only + 15/13 axle + soft caps",
    "REC_GFRP4_axle15_soft": "Recommended: 4 mm GFRP + 15/13 axle + soft caps",
}


# ============================================================================ linear
def linear_suite(kind, axle, n_sub=4, eigen=True):
    secs = strut_layout(kind)
    S = build(secs, n_sub=n_sub, axle=AXLES[axle], b_clamp=40.0)
    SR = build(secs, n_sub=n_sub, rigid_axle=True)
    L, LR = Linear(S, anchor_hub=H_EQ), Linear(SR, anchor_hub=H_EQ)
    out = dict(kind=kind, axle=axle, n_sub=n_sub, mesh=dict(nodes=S.nn, elements=len(S.elems), dof=L.ndof,
                                                             free_dof=int(len(L.free))))
    # unit-load sweep over hubs
    sweep = []
    for h in range(42):
        if h in S.poles:
            continue
        Lh, LRh = Linear(S, anchor_hub=h), Linear(SR, anchor_hub=h)
        F, n = Lh.hub_load(h, 1.0)
        r = Lh.results(Lh.solve(F), h)
        FR, _ = LRh.hub_load(h, 1.0)
        rR = LRh.results(LRh.solve(FR), h)
        sweep.append(dict(hub=h, lat=float(LAT[h]), valence=int(VAL[h]), k_sys=1 / r["hub_defl"],
                          k_cage=1 / rR["hub_defl"], sig_per_N=float(r["sig"].max()),
                          Upin_per_N=float(r["U_buck_pin"].max()), axle_sig_per_N=r.get("axle_sig", 0.0)))
    out["sweep"] = sweep
    # eigen buckling (unit load) at representative hubs
    eig = {}
    if eigen:
        for tag, h in HUBS.items():
            Lh = Linear(S, anchor_hub=h)
            F, n = Lh.hub_load(h, 1.0)
            r = Lh.results(Lh.solve(F), h)
            lam, modes = Lh.buckling(r["st"]["N"], k=4)
            pos = lam[lam > 0]
            eig[tag] = dict(F_cr_eigen_N=float(pos.min()), F_cr_euler_pinned_N=float(1 / r["U_buck_pin"].max()),
                            F_cr_euler_fixed_N=float(4 / r["U_buck_pin"].max()),
                            mode1=modes[:, np.argmin(np.where(lam > 0, lam, np.inf))] if tag == "eq_0deg" else None)
    out["eigen"] = eig
    # load cases at the equatorial hub (level drop / frontal strike / rolling contact)
    h = H_EQ
    k_sys = [s for s in sweep if s["hub"] == h][0]["k_sys"]
    k_cage = [s for s in sweep if s["hub"] == h][0]["k_cage"]
    ks = 1 / (1 / k_sys + 1 / K_CAP)
    ksR = 1 / (1 / k_cage + 1 / K_CAP)
    cases = {
        "rolling_1g": MG, "rolling_2g_bump": 2 * MG, "quasi_static_10g": 10 * MG,
        "wall_2mps_linear_peak": float(np.sqrt(2 * E_WALL * ks)),
        "drop_1m_linear_peak": float(np.sqrt(2 * E_DROP * ks)),
        "drop_1m_linear_peak_rigid_axle": float(np.sqrt(2 * E_DROP * ksR)),
    }
    res = {}
    Fcr = eig.get("eq_0deg", {}).get("F_cr_eigen_N", np.nan)
    for name, Fm in cases.items():
        LL = LR if "rigid" in name else L
        F, n = LL.hub_load(h, Fm)
        r = LL.results(LL.solve(F), h)
        allow = np.array([s.s_allow for s in S.strut_secs])
        d = dict(F_N=float(Fm), a_g=float(Fm / MG), sig_max=float(r["sig"].max()),
                 U_sig=float(r["U_sig"].max()), U_buck_pin=float(r["U_buck_pin"].max()),
                 U_buck_fix=float(r["U_buck_fix"].max()), n_struts_pin_over1=int((r["U_buck_pin"] > 1).sum()),
                 n_struts_fix_over1=int((r["U_buck_fix"] > 1).sum()),
                 U_buck_eigen=float(Fm / Fcr) if "rigid" not in name else None,
                 hub_defl_total=r["hub_defl"], hub_defl_cage=r["hub_defl_cage"], max_disp=r["max_disp"],
                 N_min=float(r["N"].min()), N_max=float(r["N"].max()),
                 crit_strut=int(np.argmax(r["U_buck_pin"])), crit_strut_sig=int(np.argmax(r["sig"])))
        if "axle_sig" in r:
            d.update(axle_sig=r["axle_sig"], axle_tip_defl=max(r["axle_tip_defl"]), bearing=r["bearing"])
        d["strut_Upin"] = r["U_buck_pin"]; d["strut_Ufix"] = r["U_buck_fix"]; d["strut_Usig"] = r["U_sig"]
        d["disp"] = r["disp"][: S.n_hub] if name == "quasi_static_10g" else None
        res[name] = d
    out["cases"] = res
    out["k_sys_eq"] = k_sys; out["k_cage_eq"] = k_cage; out["k_series_eq"] = ks; out["k_series_rigid_eq"] = ksR
    # pinned-joint truss variant (rigid axle)
    tr = {}
    k_tr = 1 / truss_case(secs, h, 1.0)["hub_defl"]
    F_tr = dict(rolling_2g_bump=2 * MG, quasi_static_10g=10 * MG,
                wall_2mps_linear_peak=float(np.sqrt(2 * E_WALL / (1 / k_tr + 1 / K_CAP))))
    for name, Fm in F_tr.items():
        t = truss_case(secs, h, Fm)
        tr[name] = dict(F_N=Fm, sig_max=float(t["sig"].max()), U_buck_pin=float(t["U_buck_pin"].max()),
                        hub_defl=t["hub_defl"], N_min=float(t["N"].min()))
    tr["k_truss_eq"] = k_tr
    out["truss"] = tr
    out["S"] = S
    return out


def linear_convergence():
    rows = []
    for n in (1, 2, 4, 8):
        secs = strut_layout("G3")
        S = build(secs, n_sub=n, axle=AXLES["CF10/8"])
        L = Linear(S, anchor_hub=H_EQ)
        F, _ = L.hub_load(H_EQ, 10 * MG)
        r = L.results(L.solve(F), H_EQ)
        lam, _ = L.buckling(r["st"]["N"], k=3)
        rows.append(dict(n_per_strut=n, nodes=S.nn, elements=len(S.elems), dof=L.ndof,
                         sig_max=float(r["sig"].max()), hub_defl=r["hub_defl"], hub_defl_cage=r["hub_defl_cage"],
                         axle_sig=r["axle_sig"], buckling_factor=float(lam[lam > 0].min()),
                         F_cr_N=float(lam[lam > 0].min() * 10 * MG)))
    return rows


# ============================================================================ nonlinear
def nl_job(args):
    key, design, hub, n_sub, keep = args
    kind, axle, cap = DESIGNS[design]
    t = time.time()
    o = run(kind=kind, axle=axle, cap=cap, hub=hub, n_sub=n_sub, s_max=90.0, keep_states=keep)
    curves = {k: o[k] for k in ("s", "F", "U", "Ucage", "Uult", "sig_cage", "sig_axle", "brg", "brg_ax", "mis",
                                "ftan", "nact")}
    snaps = {}
    if keep:
        hist, S = o["hist"], o["sysm"]
        allow = np.array([sec.s_allow for sec in S.secs])
        U = o["U"]
        idx = {"wall": int(min(np.searchsorted(U, E_WALL), len(U) - 1)),
               "allow": int(np.argmax(o["Ucage"] >= 1.0)) if (o["Ucage"] >= 1).any() else len(U) - 1,
               "end": len(U) - 1}
        for tag, i in idx.items():
            snaps[tag] = dict(i=i, s=float(o["s"][i]), F=float(o["F"][i]), U=float(U[i]), x=hist[i]["x"],
                              Uel=hist[i]["sig"] / allow, sig=hist[i]["sig"])
        snaps["geom"] = dict(X0=o["X0"], elems=S.elems, owner=S.owner, n_hub=S.n_hub, hubs=S.hubs,
                             struts=S.struts, secs=[s.name for s in S.strut_secs])
    return dict(key=key, design=design, hub=hub, n_sub=n_sub, kind=kind, axle=axle, cap=cap,
                curves=curves, snaps=snaps, mass_rods_g=o["mass_rods_g"], time=time.time() - t)


def post_nl(r):
    c = r["curves"]; lat = abs(LAT[r["hub"]])
    s, U, F = c["s"], c["U"], c["F"]

    def first(mask):
        idx = np.where(mask)[0]
        return int(idx[0]) if len(idx) else None

    ia, iu = first(c["Ucage"] >= 1.0), first(c["Uult"] >= 1.0)
    ax_allow = 500.0
    iax = first(c["sig_axle"] >= ax_allow)

    def at(i):
        return dict(s=float(s[i]), F=float(F[i]), U_J=float(U[i] / 1000), Fmax=float(F[: i + 1].max()),
                    sig_cage=float(c["sig_cage"][: i + 1].max()), U_cage=float(c["Ucage"][: i + 1].max()),
                    sig_axle=float(c["sig_axle"][: i + 1].max()), brg_radial=float(c["brg"][: i + 1].max()),
                    brg_axial=float(c["brg_ax"][: i + 1].max()), misalign_deg=float(c["mis"][: i + 1].max()),
                    a_core_g=float(F[: i + 1].max() / MG), friction_ratio=float(c["ftan"][: i + 1].max()))
    E_ow = 0.5 * M_TOTAL * (2.0 * np.cos(np.radians(lat))) ** 2 * 1000      # oblique normal energy
    out = dict(design=r["design"], hub=r["hub"], hub_lat=float(LAT[r["hub"]]), n_sub=r["n_sub"],
               mass_rods_g=r["mass_rods_g"])
    lim = [i for i in (ia, iax) if i is not None]
    il = min(lim) if lim else None                      # first of: cage allowable, axle allowable
    out["E_allow_J"] = float(U[il] / 1000) if il is not None else float(U[-1] / 1000)
    out["allow_limited_by"] = ("cage" if il == ia else "axle") if il is not None else "not reached"
    out["v_allow_mps"] = float(np.sqrt(2 * out["E_allow_J"] / M_TOTAL))
    out["h_allow_m"] = float(out["E_allow_J"] / MG - (s[il] / 1000 if il is not None else 0))
    out["E_ult_J"] = float(U[iu] / 1000) if iu is not None else None
    out["v_ult_mps"] = float(np.sqrt(2 * out["E_ult_J"] / M_TOTAL)) if iu is not None else None
    out["h_ult_m"] = float(out["E_ult_J"] / MG - s[iu] / 1000) if iu is not None else None
    out["first_buckle_F_N"] = float(F[: max(3, (first(np.diff(F) < -1.0) or len(F)))].max())
    iw = first(U >= E_WALL)
    out["wall_frontal_4.8J"] = at(iw) if iw is not None else None
    io = first(U >= E_ow)
    out["wall_oblique"] = dict(E_J=float(E_ow / 1000), **at(io)) if io is not None else None
    idr = first(U >= E_DROP + MG * s)
    out["drop_1m"] = at(idr) if idr is not None else dict(reached=False, U_J_max=float(U[-1] / 1000),
                                                          note="ultimate strength exceeded before 23.5 J absorbed")
    return out


def main():
    t0 = time.time()
    R = dict()
    print("linear suites ...", flush=True)
    R["linear"] = {k: linear_suite(*DESIGNS[k][:2]) for k in ("D0_baseline", "REC_GFRP4_axle15_soft")}
    R["linear_convergence"] = linear_convergence()
    print("  done %.0fs" % (time.time() - t0), flush=True)

    jobs = []
    for d in DESIGNS:                                   # iteration ladder, n=4, equatorial hub
        jobs.append((f"ladder|{d}", d, H_EQ, 4, False))
    for d in ("D0_baseline", "REC_GFRP4_axle15_soft", "D2_softcaps"):   # headline n=8
        for tag, h in HUBS.items():
            if d == "D2_softcaps" and tag in ("hex_58.3deg", "hex_31.7deg"):
                continue
            jobs.append((f"final|{d}|{tag}", d, h, 8, tag == "eq_0deg"))
    for d in ("D0_baseline", "REC_GFRP4_axle15_soft"):
        jobs.append((f"conv|{d}|2", d, H_EQ, 2, False))
    print(f"nonlinear runs: {len(jobs)}", flush=True)
    nl = {}
    with Pool(4) as p:
        for r in p.imap_unordered(nl_job, jobs):
            nl[r["key"]] = r
            print(f"  {r['key']:45s} {r['time']:5.0f}s", flush=True)
    R["nl_raw"] = nl
    R["nl"] = {k: post_nl(v) for k, v in nl.items()}

    # ------------------------------------------------------------------ components
    rec = R["nl"]["final|REC_GFRP4_axle15_soft|eq_0deg"]; base = R["nl"]["final|D0_baseline|eq_0deg"]
    C = {}
    a_wall_rec = rec["wall_frontal_4.8J"]["a_core_g"]
    a_drop_rec = rec["drop_1m"]["a_core_g"] if "a_core_g" in rec["drop_1m"] else None
    C["arm_hand"] = comp.arm_hand(comp.QX["T_g"][1] / 1000 * G0, [5.0, round(a_wall_rec, 1)] +
                                  ([round(a_drop_rec, 1)] if a_drop_rec else []))
    C["arm_hand_user_1.9kgf"] = comp.arm_hand(1.9 * G0, [5.0])["thrust"]
    C["arm_skfem"] = comp.arm_skfem(F_N=comp.QX["T_g"][1] / 1000 * G0)
    C["propulsion_2.40kg"] = comp.propulsion(2.40)
    ax = {}
    for tag, r_, tube, brg in (("baseline", base, (10, 8), "61800-2RS1 (10x19x5)"),
                               ("recommended", rec, (15, 13), "61802-2RS1 (15x24x5)")):
        w = r_["wall_frontal_4.8J"]
        ax[tag] = dict(
            wall_hand=comp.axle_hand(*tube, F_total_N=w["Fmax"]),
            wall_fea_sig=w["sig_axle"],
            bearing_wall=comp.bearing_check(w["brg_radial"], w["brg_axial"], brg),
            bearing_misalign_deg=w["misalign_deg"],
            linear_10g_hand=comp.axle_hand(*tube, F_total_N=10 * MG),
        )
        if "Fmax" in r_["drop_1m"]:
            d = r_["drop_1m"]
            ax[tag]["drop_hand"] = comp.axle_hand(*tube, F_total_N=d["Fmax"])
            ax[tag]["bearing_drop"] = comp.bearing_check(d["brg_radial"], d["brg_axial"], brg)
        ax[tag]["user_quoted_C0_1.27kN_is"] = "61803-2RS1 (17x26x5), not 61800"
    C["axle_bearing"] = ax
    C["pole_strike"] = dict(
        solid_cap_axle10=comp.pole_strike(E_WALL / 1000, K_CAP, 10, 8),
        solid_cap_axle15=comp.pole_strike(E_WALL / 1000, K_CAP, 15, 13),
        required_bumper=dict(F_limit_N=0.5 * 1100, k_max_N_per_mm=(0.5 * 1100) ** 2 / (2 * E_WALL),
                             stroke_min_mm=2 * E_WALL / (0.5 * 1100)),
    )
    R["components"] = C

    # ------------------------------------------------------------------ masses
    def cage_mass(kind, cap):
        rods, _ = cage_mass_g(strut_layout(kind), STRUT_L)
        hub_g = 42 * 1.6                                  # PA12 MJF hub body ~1.6 g (18x12 mm, cored)
        cap_g = 42 * (1.5 if cap == "TPU95A-solid" else 2.7)
        return dict(rods_g=rods, hubs_g=hub_g, caps_g=cap_g, total_g=rods + hub_g + cap_g)
    M = {}
    for d, (kind, axle, cap) in DESIGNS.items():
        cm = cage_mass(kind, cap)
        do, di = (10, 8) if axle == "CF10/8" else (15, 13)
        axle_g = np.pi / 4 * (do**2 - di**2) * 580 * 1.55e-3
        brg_g = 2 * (5.5 if do == 10 else 7.5)
        pole_hub_extra = 0 if do == 10 else 10.0
        M[d] = dict(cage=cm, axle_g=axle_g, bearings_g=brg_g, pole_hub_extra_g=pole_hub_extra,
                    struct_total_g=cm["total_g"] + axle_g + brg_g + pole_hub_extra)
    b0 = M["D0_baseline"]["struct_total_g"]
    for d in M:
        M[d]["delta_vs_baseline_g"] = M[d]["struct_total_g"] - b0
        M[d]["AUW_kg"] = 2.40 + M[d]["delta_vs_baseline_g"] / 1000
    R["mass"] = M
    R["components"]["propulsion_recommended"] = comp.propulsion(M["REC_GFRP4_axle15_soft"]["AUW_kg"])

    # ------------------------------------------------------------------ prop clearance (undeformed, all cage spins)
    R["clearance"] = prop_clearance(R)
    with open(os.path.join(HERE, "data", "fea_results.pkl"), "wb") as f:
        pickle.dump(R, f)
    print("total %.0f s" % (time.time() - t0))


# ============================================================================ prop clearance
MOTOR_R = 295.0 / 2          # motor-to-motor diagonal / 2
PROP_R = 7 * 25.4 / 2
Z_PROP = 0.0                 # assumption: rotor plane through the cage centre


def _clearance_points(P):
    """min distance (mm) from points P (body frame) to the 4 prop-tip circles."""
    d = np.inf
    for sx in (1, -1):
        for sy in (1, -1):
            c = np.array([sx, sy, 0.0]) * MOTOR_R / np.sqrt(2)
            c[2] = Z_PROP
            q = P - c
            rho = np.hypot(q[:, 0], q[:, 1])
            dist = np.hypot(rho - PROP_R, q[:, 2])
            d = min(d, dist.min())
    return d


def _rot_y(th):
    c, s = np.cos(th), np.sin(th)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def prop_clearance(R):
    from geodesic import geodesic_2v
    nodes, struts, *_ = geodesic_2v()
    t = np.linspace(0, 1, 41)
    pts = np.concatenate([nodes[a] + (nodes[b] - nodes[a]) * t[:, None] for a, b in struts])
    rod_r, hub_in = 2.0, 6.0      # 4 mm rod radius; hub body protrudes ~6 mm inward of the node
    tin = t[1:-1]
    spts = np.concatenate([nodes[a] + (nodes[b] - nodes[a]) * tin[:, None] for a, b in struts])
    best = (np.inf, 0)
    for th in np.radians(np.arange(0, 72, 0.5)):
        Rb = _rot_y(th)
        d = min(_clearance_points(spts @ Rb.T) - rod_r, _clearance_points(nodes @ Rb.T) - hub_in)
        if d < best[0]:
            best = (d, th)
    out = dict(undeformed_min_mm=float(best[0]), worst_spin_deg=float(np.degrees(best[1])),
               assumption="rotor plane through cage centre; motor circle R=147.5 mm; prop R=88.9 mm",
               requirement_mm=20.0)
    # deformed, frontal wall strike: struck equatorial hub rotated to body +X
    for d in ("D0_baseline", "REC_GFRP4_axle15_soft"):
        raw = R["nl_raw"][f"final|{d}|eq_0deg"]
        g = raw["snaps"]["geom"]; snap = raw["snaps"]["wall"]
        n0 = g["hubs"][H_EQ] / R_CAGE
        th = np.arctan2(n0[2], n0[0])
        Rb = _rot_y(-th) if False else _rot_y(th)
        # choose rotation that maps n0 -> +X
        for cand in (_rot_y(th), _rot_y(-th)):
            if np.allclose(cand @ n0, [1, 0, 0], atol=1e-6):
                Rb = cand
        ncage = g["n_hub"] + len(g["struts"]) * (raw["n_sub"] - 1)
        nh = g["n_hub"]
        P = snap["x"][:ncage] @ Rb.T
        P0 = g["X0"][:ncage] @ Rb.T
        cl = lambda Q: min(_clearance_points(Q[:nh]) - hub_in, _clearance_points(Q[nh:]) - rod_r)
        out[f"{d}_wall_strike"] = dict(undeformed_same_spin_mm=float(cl(P0)),
                                       deformed_mm=float(cl(P)),
                                       state_s_mm=snap["s"], state_U_J=snap["U"] / 1000)
    return out


if __name__ == "__main__":
    main()
