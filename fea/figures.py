"""Deck figures + headline numbers from data/fea_results.pkl (written by run_all.py).

Writes figures/fea-design-ladder.png, figures/fea-cage-stress.png, figures/fea-convergence.png
and data/summary.json. Every number is a CALCULATION (nothing measured).
Usage:  .venv/bin/python figures.py
"""
import json, os, pickle
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from mpl_toolkits.mplot3d.art3d import Line3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)
R = pickle.load(open(os.path.join(HERE, "data", "fea_results.pkl"), "rb"))

BLUE, GREEN, INK, SLATE, AMBER, RED = "#1D4ED8", "#16A34A", "#0F172A", "#475569", "#D97706", "#DC2626"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15, "axes.edgecolor": SLATE, "axes.labelcolor": INK,
                     "xtick.color": SLATE, "ytick.color": SLATE, "axes.spines.top": False,
                     "axes.spines.right": False})
E_WALL, E_DROP = 4.8, 23.5          # J: 2 m/s frontal strike, 1 m drop (2.4 kg, conservative)
E_GAL = 0.5 * 2.47 * 1.5 ** 2       # J: 1.5 m/s gallery speed limit at the 2.47 kg FEA-cage mass
ORDER = ["D0_baseline", "D1_CFRP3", "D2_softcaps", "D3_GFRP4_axle10", "D4_band4_axle15_soft",
         "REC_GFRP4_axle15_soft"]
SHORT = {"D0_baseline": "Stage 1 baseline\n3 mm GFRP · 10/8 axle · solid caps",
         "D1_CFRP3": "3 mm carbon rods",
         "D2_softcaps": "3 mm GFRP + soft TPU caps",
         "D3_GFRP4_axle10": "4 mm GFRP, 10/8 axle",
         "D4_band4_axle15_soft": "4 mm band only + 15/13 axle\n+ soft caps",
         "REC_GFRP4_axle15_soft": "Selected: 4 mm GFRP\n+ 15/13 axle + soft caps"}
COL = {"D0_baseline": RED, "D1_CFRP3": "#7C3AED", "D2_softcaps": AMBER, "D3_GFRP4_axle10": "#0891B2",
       "D4_band4_axle15_soft": SLATE, "REC_GFRP4_axle15_soft": GREEN}
NOTE = "Stage 2 calculation (nonlinear co-rotational beam FEA, Python). Not a test result; nothing here is measured."


def foot(fig):
    fig.text(0.995, 0.01, NOTE, ha="right", va="bottom", fontsize=11, color=SLATE)


nl, raw = R["nl"], R["nl_raw"]
mass = R["mass"]

# ------------------------------------------------------------------ 1. design ladder
fig, (a1, a2) = plt.subplots(1, 2, figsize=(24, 9.6), dpi=100, gridspec_kw=dict(width_ratios=[1.25, 1]))
for d in ORDER:
    c = raw[f"ladder|{d}"]["curves"]
    U = np.asarray(c["U"]) / 1000
    a1.plot(U, c["Ucage"], color=COL[d], lw=4 if d.startswith(("REC", "D0")) else 2.2,
            label=SHORT[d].replace("\n", " "), alpha=1 if d.startswith(("REC", "D0")) else .8)
a1.axhline(1.0, color=INK, lw=1.5, ls="--")
a1.text(12, 1.03, "allowable stress (σ = σ_allow)", color=INK, fontsize=14, va="bottom")
for E, t, ha in ((E_GAL, "1.5 m/s\nspeed limit\n2.8 J", "right"), (E_WALL, "2 m/s\nwall strike\n4.8 J", "left"),
                 (E_DROP, "1 m drop\n23.5 J", "left")):
    a1.axvline(E, color=SLATE, lw=1.4, ls=":")
    a1.text(E + (0.3 if ha == "left" else -0.3), 1.97, t, color=SLATE, fontsize=13, va="top", ha=ha)
a1.set_xlim(0, 30); a1.set_ylim(0, 2.0)
a1.set_xlabel("impact energy absorbed by the cage (J)")
a1.set_ylabel("peak strut stress / allowable")
a1.set_title("Peak cage stress as the impact energy rises (hub on the equator)", loc="left", color=INK,
             fontsize=17, fontweight="bold")
a1.legend(loc="lower right", fontsize=13, frameon=True, framealpha=1, edgecolor="#E2E8F0")

ys = np.arange(len(ORDER))[::-1]
E_al = [nl[f"ladder|{d}"]["E_allow_J"] for d in ORDER]
a2.barh(ys, E_al, color=[COL[d] for d in ORDER], height=0.62)
for y, d, E in zip(ys, ORDER, E_al):
    dm = mass[d]["delta_vs_baseline_g"]
    lim = nl[f"ladder|{d}"]["allow_limited_by"]
    a2.text(E + 0.4, y, f"{E:.1f} J  ({'+' if dm >= 0 else ''}{dm:.0f} g · limit: {lim})", va="center",
            fontsize=13, color=INK)
a2.set_yticks(ys); a2.set_yticklabels([SHORT[d] for d in ORDER], fontsize=12.5)
for E, t, ha in ((E_GAL, "1.5 m/s\n2.8 J", "right"), (E_WALL, "2 m/s\n4.8 J", "left"), (E_DROP, "1 m drop\n23.5 J", "left")):
    a2.axvline(E, color=SLATE, lw=1.4, ls=":")
    a2.text(E + (0.25 if ha == "left" else -0.25), -1.05, t, color=SLATE, fontsize=12, ha=ha, va="bottom")
a2.set_xlim(0, max(max(E_al) * 1.45, 30)); a2.set_ylim(-1.1, len(ORDER) - 0.5)
a2.set_xlabel("energy absorbed before any part reaches its allowable stress (J)")
a2.set_title("Design iterations: energy capacity and mass change", loc="left", color=INK, fontsize=17,
             fontweight="bold")
fig.tight_layout(rect=(0, 0.03, 1, 1))
foot(fig)
fig.savefig(os.path.join(FIG, "fea-design-ladder.png")); plt.close(fig)

# ------------------------------------------------------------------ 2. deformed cage, coloured by stress
cmap = LinearSegmentedColormap.from_list("u", [(0, "#BBF7D0"), (0.45, GREEN), (0.75, AMBER), (0.9, RED),
                                              (1.0, "#7F1D1D")])
norm = Normalize(0, 1.2)
fig = plt.figure(figsize=(24, 9.6), dpi=100)
fig.subplots_adjust(left=0, right=0.93, top=0.86, bottom=0, wspace=0)
for k, d in enumerate(("D0_baseline", "REC_GFRP4_axle15_soft")):
    r = raw[f"final|{d}|eq_0deg"]
    g, sn = r["snaps"]["geom"], r["snaps"]["wall"]
    x, el, U = np.asarray(sn["x"]), np.asarray(g["elems"]), np.asarray(sn["Uel"])
    ax = fig.add_subplot(1, 2, k + 1, projection="3d")
    seg = np.stack([x[el[:, 0]], x[el[:, 1]]], axis=1)
    axle = np.asarray(g["owner"]) if "owner" in g else None
    lw = np.where(axle < 0, 6.0, 3.4) if axle is not None else 3.4
    lc = Line3DCollection(seg, colors=cmap(norm(np.clip(U, 0, 1.2))), linewidths=lw)
    ax.add_collection3d(lc)
    lim = 320
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-lim, lim)
    ax.set_box_aspect((1, 1, 1), zoom=1.45); ax.view_init(elev=14, azim=-58); ax.set_axis_off()
    hub0 = np.asarray(g["hubs"])
    w = nl[f"final|{d}|eq_0deg"]["wall_frontal_4.8J"]
    ttl = SHORT[d].replace("\n", " ")
    ax.set_title(f"{ttl}\npeak stress {w['U_cage']:.2f}× allowable · core load {w['a_core_g']:.0f} g · "
                 f"crush {sn['s']:.0f} mm", color=COL[d], fontsize=16, fontweight="bold", pad=0)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
cax = fig.add_axes([0.94, 0.18, 0.012, 0.6])
cb = fig.colorbar(sm, cax=cax)
cb.set_label("element stress / allowable", color=INK)
fig.suptitle("2 m/s strike on an equator hub (4.8 J): deformed shape at true scale, coloured by stress",
             x=0.02, ha="left", color=INK, fontsize=19, fontweight="bold")
foot(fig)
fig.savefig(os.path.join(FIG, "fea-cage-stress.png")); plt.close(fig)

# ------------------------------------------------------------------ 3. mesh convergence
rows = R["linear_convergence"]
n = np.array([r_["n_per_strut"] for r_ in rows])
fig, (b1, b2) = plt.subplots(1, 2, figsize=(24, 8.5), dpi=100)
for key, lab, c in (("sig_max", "peak strut stress", BLUE), ("hub_defl", "hub deflection", GREEN),
                    ("buckling_factor", "first buckling load", AMBER), ("axle_sig", "axle stress", SLATE)):
    v = np.array([r_[key] for r_ in rows], float)
    b1.plot(n, v / v[-1], "o-", color=c, lw=3, ms=10, label=lab)
b1.axhspan(0.98, 1.02, color=GREEN, alpha=.08)
b1.set_xscale("log", base=2); b1.set_xticks(n); b1.set_xticklabels([str(i) for i in n])
b1.set_xlabel("beam elements per strut")
b1.set_ylabel("value / value at 8 elements")
b1.set_title("Linear model, 10 g load on an equator hub", loc="left", color=INK, fontsize=17, fontweight="bold")
b1.legend(frameon=False, fontsize=13)
b1.text(1.05, 0.955, "stress, deflection and axle stress are identical at every mesh\n(beam elements are exact for loads at the nodes); only buckling needs refinement",
        fontsize=12.5, color=SLATE, va="top")
b1.set_ylim(0.9, 1.5)
for d, c in (("D0_baseline", RED), ("REC_GFRP4_axle15_soft", GREEN)):
    pts = [(2, nl.get(f"conv|{d}|2")), (4, nl.get(f"ladder|{d}")), (8, nl.get(f"final|{d}|eq_0deg"))]
    pts = [(k, p["E_allow_J"]) for k, p in pts if p]
    b2.plot([p[0] for p in pts], [p[1] for p in pts], "o-", color=c, lw=3, ms=10,
            label=SHORT[d].replace("\n", " "))
    for k, e in pts:
        b2.text(k, e * 1.03, f"{e:.1f} J", ha="center", color=c, fontsize=13)
b2.set_xscale("log", base=2); b2.set_xticks([2, 4, 8]); b2.set_xticklabels(["2", "4", "8"])
b2.set_ylim(0, None)
b2.set_xlabel("beam elements per strut")
b2.set_ylabel("energy to first allowable stress (J)")
b2.set_title("Nonlinear impact model", loc="left", color=INK, fontsize=17, fontweight="bold")
b2.legend(frameon=False, fontsize=13, loc="lower right")
fig.tight_layout(rect=(0, 0.04, 1, 1))
foot(fig)
fig.savefig(os.path.join(FIG, "fea-convergence.png")); plt.close(fig)

# ------------------------------------------------------------------ headline numbers
S = {"mesh": R["linear"]["D0_baseline"]["mesh"], "convergence": rows, "designs": {}, "hubs": {},
     "components": {}, "clearance": R["clearance"]}
for d in ORDER:
    p = nl[f"ladder|{d}"]
    S["designs"][d] = dict(label=SHORT[d].replace("\n", " "), E_allow_J=p["E_allow_J"],
                           limited_by=p["allow_limited_by"], v_allow_mps=p["v_allow_mps"],
                           E_ult_J=p["E_ult_J"], delta_g=mass[d]["delta_vs_baseline_g"], AUW_kg=mass[d]["AUW_kg"],
                           wall=p["wall_frontal_4.8J"], drop=p["drop_1m"])
for key, p in nl.items():
    if key.startswith("final|"):
        S["hubs"][key] = dict(E_allow_J=p["E_allow_J"], limited_by=p["allow_limited_by"], E_ult_J=p["E_ult_J"],
                              wall=p["wall_frontal_4.8J"], drop=p["drop_1m"], hub_lat=p["hub_lat"])
C = R["components"]
S["components"]["propulsion_recommended"] = C["propulsion_recommended"]
S["components"]["axle_bearing"] = C["axle_bearing"]
S["components"]["pole_strike"] = C["pole_strike"]
S["components"]["arm_hand"] = C["arm_hand"]


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return clean(o.tolist())
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


json.dump(clean(S), open(os.path.join(HERE, "data", "summary.json"), "w"), indent=1, default=str)
print("figures in", FIG)
