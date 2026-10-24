"""Motor arm, axle, bearing and propulsion/flight-budget calculations for SURANG.

All values are CALCULATED TARGETS from catalogue data and stated assumptions (nothing measured).
Units: N, mm, MPa, s unless stated.
"""
import numpy as np

G0 = 9.81

# ----------------------------------------------------------------------------- propulsion data
# QX-MOTOR 2809 1300KV, HQ 7x4x3, 23.3-23.8 V static test (catalogue endpoints, rcdrone.top listing)
QX = dict(T_g=(1120.0, 2850.0), P_W=(266.0, 963.0), V=23.55, motor_g=70.0, I_max_A=50.0)
PROP_G = 9.0          # HQ 7x4x3 prop mass, g (approx.)
TIP_HW_G = 11.0       # motor screws, soft-mount, wires on arm, g (estimate)
D_PROP = 7 * 25.4     # mm
CT_STATIC = 0.14      # static thrust coefficient (n in rev/s), chosen so 2850 g -> ~24.5k rpm (= 1300KV x 23.5V x 0.8)
RHO_AIR = 1.2         # kg/m^3 (Mumbai, near sea level, warm)
AVIONICS_W = 18.0     # Pi 5 (~7), FC (1.5), radios (1), LiDAR (1.5), cameras (1.5), IR LEDs (3), pump (1), buck losses (1.5)
BLOCKAGE = 1.07       # thrust penalty for cage/frame in the downwash (assumption, 5-10%)
BATT = dict(cells=6, mAh=3300, usable=0.80, V_nom=3.7, V_min=3.5)


def power_fit():
    (T1, T2), (P1, P2) = QX["T_g"], QX["P_W"]
    b = np.log(P2 / P1) / np.log(T2 / T1)
    a = P1 / T1**b
    return a, b


def motor_power(T_g):
    a, b = power_fit()
    return a * T_g**b


def rpm_for_thrust(T_g):
    T = T_g / 1000 * G0
    n = np.sqrt(T / (CT_STATIC * RHO_AIR * (D_PROP / 1000) ** 4))
    return 60 * n


def propulsion(m_auw):
    a, b = power_fit()
    W_gf = m_auw * 1000
    T_hover = W_gf / 4 * BLOCKAGE                       # g per motor
    P_motor = motor_power(T_hover)
    P_tot = 4 * P_motor + AVIONICS_W
    E_Wh = BATT["cells"] * BATT["V_nom"] * BATT["mAh"] / 1000
    E_use = E_Wh * BATT["usable"]
    V_nom = BATT["cells"] * BATT["V_nom"]
    Tmax_test = QX["T_g"][1]
    Vmin = BATT["cells"] * BATT["V_min"]
    Tmax_vmin = Tmax_test * (Vmin / QX["V"]) ** 2       # static thrust ~ rpm^2 ~ V^2
    tw = dict()
    for kv, f in (("1300KV", 1.0), ("1250KV", (1250 / 1300) ** 2)):
        tw[kv] = dict(T_total_kgf_full=4 * Tmax_test * f / 1000,
                      T_total_kgf_vmin=4 * Tmax_vmin * f / BLOCKAGE / 1000,
                      TW_full=4 * Tmax_test * f / BLOCKAGE / W_gf,
                      TW_vmin=4 * Tmax_vmin * f / BLOCKAGE / W_gf)
    rpm_h = rpm_for_thrust(T_hover)
    # rolling mode (estimates): bare 10-gon equator needs mg*tan(18deg) to tip over a hub;
    # a continuous tread is assumed to give C_rr ~ 0.05.  Low-throttle motor floor ~5 W each.
    roll = {}
    for tag, frac in (("decagon_tip_over", np.tan(np.radians(18))), ("smooth_tread_Crr0.05", 0.05)):
        T_each = W_gf * frac / 4
        P_each = max(motor_power(T_each), 5.0)
        P = 4 * P_each + AVIONICS_W
        roll[tag] = dict(horizontal_force_N=float(m_auw * G0 * frac), thrust_per_motor_g=float(T_each),
                         P_total_W=float(P), endurance_min=float(E_use / P * 60), ratio_vs_hover=float(P_tot / P))
    return dict(
        AUW_kg=m_auw, hover_thrust_per_motor_g=float(T_hover), hover_throttle_frac_of_max=float(T_hover / Tmax_test),
        P_motor_hover_W=float(P_motor), P_total_hover_W=float(P_tot),
        I_hover_A_at_nominal=float(P_tot / V_nom), battery_Wh=float(E_Wh), usable_Wh=float(E_use),
        hover_endurance_min=float(E_use / P_tot * 60), hover_rpm=float(rpm_h),
        hover_1P_Hz=float(rpm_h / 60), hover_3P_Hz=float(3 * rpm_h / 60),
        max_rpm=float(rpm_for_thrust(Tmax_test)), max_1P_Hz=float(rpm_for_thrust(Tmax_test) / 60),
        I_max_per_motor_A=float(QX["P_W"][1] / QX["V"]), thrust_to_weight=tw,
        power_fit=dict(a=float(a), b=float(b), note="P[W] = a*T[g]^b through catalogue endpoints; hover point is an extrapolation below the 1120 g test point"),
        rolling=roll)


# ----------------------------------------------------------------------------- motor arm
ARM = dict(L=110.0, b=25.0, h=5.0, E=55000.0, s_flex=550.0, s_allow=275.0, rho=1.55e-3, nu=0.3)


def arm_hand(F_thrust_N, a_crash_g_list):
    L, b, h, E = ARM["L"], ARM["b"], ARM["h"], ARM["E"]
    I_out = b * h**3 / 12; I_in = h * b**3 / 12
    Z_out = I_out / (h / 2); Z_in = I_in / (b / 2)
    m_tip = (QX["motor_g"] + PROP_G + TIP_HW_G) / 1000
    m_arm = b * h * L * ARM["rho"] / 1000
    out = dict(I_out_mm4=I_out, Z_out_mm3=Z_out, m_tip_kg=m_tip, m_arm_kg=m_arm)
    M = F_thrust_N * L
    out["thrust"] = dict(F_N=F_thrust_N, M_Nmm=M, sigma=M / Z_out, util=M / Z_out / ARM["s_allow"],
                         FoS_allow=ARM["s_allow"] / (M / Z_out), FoS_ult=ARM["s_flex"] / (M / Z_out),
                         tip_defl=F_thrust_N * L**3 / (3 * E * I_out))
    crash = []
    for ag in a_crash_g_list:
        F = m_tip * ag * G0 + m_arm * ag * G0 / 2       # arm self-mass acting at mid-span
        Mo = m_tip * ag * G0 * L + m_arm * ag * G0 * L / 2
        crash.append(dict(a_g=ag, out_of_plane_sigma=Mo / Z_out, in_plane_sigma=Mo / Z_in,
                          util_out=Mo / Z_out / ARM["s_allow"], FoS_out=ARM["s_allow"] / (Mo / Z_out),
                          tip_defl_out=Mo * L**2 / (3 * E * I_out) / L * 1.0))
    out["crash"] = crash
    k = 3 * E * I_out / L**3                       # N/mm
    m_eff = m_tip + 0.236 * m_arm
    f1 = np.sqrt(k * 1000 / m_eff) / (2 * np.pi)
    out["f1_out_of_plane_Hz"] = f1
    k_in = 3 * E * I_in / L**3
    out["f1_in_plane_Hz"] = np.sqrt(k_in * 1000 / m_eff) / (2 * np.pi)
    out["k_out_N_per_mm"] = k
    return out


def arm_skfem(F_N=27.96, levels=(1, 2, 3)):
    """3D linear-elastic hex model of the arm (isotropic in-plane approximation of 3K twill plate).
    Clamped at the stack edge, tip force spread over a 15 mm motor-pad on the top face."""
    try:
        from skfem import MeshHex, ElementHex2, ElementVector, Basis, FacetBasis, asm, condense, solve
        from skfem.models.elasticity import linear_elasticity, lame_parameters
        from skfem.helpers import dot
        from skfem import LinearForm
    except Exception as e:  # pragma: no cover
        return dict(error=str(e))
    L, b, h, E, nu = ARM["L"], ARM["b"], ARM["h"], ARM["E"], ARM["nu"]
    lam, mu = lame_parameters(E, nu)
    res = []
    for lev in levels:
        nx, ny, nz = 22 * lev, 2 * lev, lev
        m = MeshHex.init_tensor(np.linspace(0, L, nx + 1), np.linspace(0, b, ny + 1), np.linspace(0, h, nz + 1))
        e = ElementVector(ElementHex2())
        ib = Basis(m, e)
        K = asm(linear_elasticity(lam, mu), ib)
        pad = m.facets_satisfying(lambda x: (x[2] > h - 1e-9) & (x[0] > L - 15 + 1e-6))
        fb = FacetBasis(m, e, facets=pad)
        q = F_N / (15 * b)

        @LinearForm
        def load(v, w):
            return -q * v[2]

        f = asm(load, fb)
        D = ib.get_dofs(lambda x: x[0] < 1e-9).all()
        u = solve(*condense(K, f, D=D))
        # bending stress sxx at the clamp, from the element-wise strain projected (sample along top fibre)
        from skfem.helpers import sym_grad
        ip = ib.interpolate(u)
        eps = sym_grad(ip)
        tr = eps[0, 0] + eps[1, 1] + eps[2, 2]
        sxx = 2 * mu * eps[0, 0] + lam * tr
        # take max over quadrature points of elements within one element-length of the clamp, excluding
        # the singular clamp corner by sampling at the first element's centroid row
        sxx_max = float(np.abs(sxx).max())
        X = ib.mapping.F(ib.quadrature[0])
        mid = (X[0] > 0.5 * L / nx) & (X[0] < L / nx * 1.5)
        s_near = float(np.abs(sxx[mid]).max())
        # mean deflection under the motor pad from compliance: f.u / F
        F_app = abs(f.sum())
        pad_defl = abs(float(f @ u)) / F_app
        xr = L - 7.5
        Iz = b * h**3 / 12
        xs = np.linspace(L - 15, L, 31); P = F_N / len(xs)

        def wpt(xi, xj):
            return np.where(xi <= xj, P * xi**2 * (3 * xj - xi), P * xj**2 * (3 * xi - xj)) / (6 * E * Iz)
        d_ref = float(np.mean([sum(wpt(xi, xj) for xj in xs) for xi in xs]))
        x_e = float(X[0][mid].mean())
        s_ref = F_N * (xr - x_e) * (h / 2) / Iz
        res.append(dict(level=lev, element="Hex27 (quadratic)", n_elem=int(m.nelements), n_dof=int(K.shape[0]),
                        F_applied_N=float(F_app), pad_defl_mm=pad_defl, pad_defl_beam_theory_mm=d_ref,
                        sxx_near_root_MPa=s_near, sxx_beam_theory_same_x_MPa=float(s_ref),
                        sxx_peak_incl_clamp_singularity_MPa=sxx_max, x_eval_mm=x_e))
    return res


# ----------------------------------------------------------------------------- axle and bearings
BEARINGS = {  # SKF 618xx-2RS1, C0 / C in kN (distributor-listed SKF values; see README)
    "61800-2RS1 (10x19x5)": dict(d=10, D=19, B=5, C=1.72, C0=0.83, mass_g=5.5),
    "61802-2RS1 (15x24x5)": dict(d=15, D=24, B=5, C=1.9, C0=1.1, mass_g=7.5),
    "61803-2RS1 (17x26x5)": dict(d=17, D=26, B=5, C=2.03, C0=1.27, mass_g=8.0),
}


def bearing_check(Fr_N, Fa_N, name):
    bb = BEARINGS[name]
    P0 = max(Fr_N, 0.6 * Fr_N + 0.5 * Fa_N)        # SKF equivalent static load, deep-groove ball bearing
    s0 = bb["C0"] * 1000 / P0 if P0 > 0 else np.inf
    return dict(bearing=name, Fr_N=Fr_N, Fa_N=Fa_N, P0_N=P0, C0_N=bb["C0"] * 1000, s0=s0,
                axial_ok=Fa_N <= 0.5 * bb["C0"] * 1000, s0_shock_ok=s0 >= 1.5)


def axle_hand(do, di, F_total_N, a=250.0, E=100000.0, s_allow=500.0, s_ult=1000.0):
    """Two cantilevers (clamp at +/-40 mm, bearing at +/-290 mm), each carrying F/2 at the tip."""
    I = np.pi / 64 * (do**4 - di**4); Z = I / (do / 2)
    P = F_total_N / 2
    M = P * a
    return dict(tube=f"{do:g}/{di:g}", I=I, Z=Z, F_total_N=F_total_N, M_root_Nmm=M, sigma=M / Z,
                util=M / Z / s_allow, FoS_allow=s_allow / (M / Z), FoS_ult=s_ult / (M / Z),
                tip_defl=P * a**3 / (3 * E * I), tip_slope_deg=np.degrees(P * a**2 / (2 * E * I)),
                k_pair_N_per_mm=2 * 3 * E * I / a**3,
                mass_g_pole_to_pole=np.pi / 4 * (do**2 - di**2) * 580 * 1.55e-3)


def pole_strike(E_J, k_cap, axle_do, axle_di, a=250.0, E=100000.0):
    """Lateral (along-axle) strike on a pole hub: cap in series with the axle's axial stiffness."""
    A = np.pi / 4 * (axle_do**2 - axle_di**2)
    k_ax = E * A / a
    k = 1 / (1 / k_cap + 1 / k_ax)
    F = np.sqrt(2 * E_J * 1000 * k)
    return dict(k_series=k, F_N=F)


if __name__ == "__main__":
    import json
    print(json.dumps(propulsion(2.4), indent=1, default=float))
    print(json.dumps(arm_hand(2.85 * G0, [5, 20]), indent=1, default=float))
    print(json.dumps(arm_skfem(), indent=1))
