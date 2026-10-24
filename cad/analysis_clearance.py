"""Clearance + puck-exit analysis for SURANG (numpy). Writes cad/analysis.json.

Everything here is a geometric CALCULATION on the design model, not a measurement.
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geodesic import geodesic_2v
from params import P

R = P['cage_R']
hubs, struts, faces, kind = geodesic_2v(R)
H = np.array(hubs)
S = np.array(struts)
A, B = H[S[:, 0]], H[S[:, 1]]
rr = P['strut_d'] / 2


def seg_dist(Q, A, B):
    """Q (n,3), A,B (m,3) -> (n,m) distances point-segment."""
    AB = B - A
    L2 = (AB ** 2).sum(1)
    AQ = Q[:, None, :] - A[None, :, :]
    t = np.clip((AQ * AB[None]).sum(2) / L2[None], 0, 1)
    C = A[None] + t[..., None] * AB[None]
    return np.linalg.norm(Q[:, None, :] - C, axis=2)


def hub_dist(Q, centres, r_in, r_out, rad):
    """Distance from Q to radial cylinders (axis along centre direction)."""
    n = centres / np.linalg.norm(centres, axis=1)[:, None]
    proj = Q @ n.T                                    # (q,h) along-axis coord from origin
    perp = np.sqrt(np.maximum((Q ** 2).sum(1)[:, None] - proj ** 2, 0))
    da = np.maximum(np.maximum(r_in - proj, proj - r_out), 0)
    dr = np.maximum(perp - rad, 0)
    return np.sqrt(da ** 2 + dr ** 2)


out = {}
# ---- cage geometry facts
chords = np.linalg.norm(A - B, axis=1)
out['chords_mm'] = sorted(set(np.round(chords, 1).tolist()))
F = np.array(faces)
fp = []
inr = []
for a, b, c in F:
    pa, pb, pc = H[a], H[b], H[c]
    nrm = np.cross(pb - pa, pc - pa); nrm /= np.linalg.norm(nrm)
    fp.append(abs(pa @ nrm))
    la, lb, lc = np.linalg.norm(pb - pc), np.linalg.norm(pa - pc), np.linalg.norm(pa - pb)
    s = (la + lb + lc) / 2
    area = math.sqrt(s * (s - la) * (s - lb) * (s - lc))
    inr.append(area / s)
fp = np.array(fp); inr = np.array(inr)
out['face_plane_dist_min_mm'] = float(fp.min())
out['face_plane_dist_max_mm'] = float(fp.max())
out['face_centroid_ratio_min'] = float(fp.min() / R)
out['strut_mid_dist_min_mm'] = float(np.linalg.norm((A + B) / 2, axis=1).min())
out['cage_inner_hull_min_mm'] = float(fp.min() - rr)
out['face_inradius_mm'] = [float(inr.min()), float(inr.max())]
out['face_clear_incircle_dia_mm'] = [float(2 * (inr.min() - rr)), float(2 * (inr.max() - rr))]

# ---- prop tip clearance, swept over full cage rotation about Y
cx = P['frame_diag'] / 2 / math.sqrt(2)
tipR = P['prop_d'] / 2
phi = np.radians(np.arange(0, 360, 0.5))
res = []
for zt in (P['prop_z'] - P['prop_blade_half_t'], P['prop_z'], P['prop_z'] + P['prop_blade_half_t']):
    tips = np.stack([cx + tipR * np.cos(phi), cx + tipR * np.sin(phi), np.full_like(phi, zt)], 1)
    yv = tips[:, 1]; rv = np.hypot(tips[:, 0], tips[:, 2]); a0 = np.arctan2(tips[:, 2], tips[:, 0])
    best = (1e9, None)
    for th in np.radians(np.arange(0, 72, 0.25)):      # 5-fold symmetry about Y
        Q = np.stack([rv * np.cos(a0 + th), yv, rv * np.sin(a0 + th)], 1)
        d_rod = seg_dist(Q, A, B).min() - rr
        d_hub = hub_dist(Q, H, R - P['hub_h'] / 2, R + P['hub_h'] / 2, P['hub_d'] / 2).min()
        d = min(d_rod, d_hub)
        if d < best[0]:
            best = (d, float(np.degrees(th)))
    res.append({'tip_z': zt, 'min_clear_to_rod_or_hub_mm': float(best[0]), 'at_cage_angle_deg': best[1]})
tip_r3d = math.sqrt((cx * math.sqrt(2) + tipR) ** 2 + (P['prop_z'] + P['prop_blade_half_t']) ** 2)
out['prop_tip_envelope_plan_mm'] = cx * math.sqrt(2) + tipR
out['prop_tip_max_dist_from_centre_mm'] = tip_r3d
out['prop_clear_vs_inner_hull_mm'] = float(fp.min() - rr - tip_r3d)
out['prop_clear_vs_face_centroid_mm'] = float(fp.min() - tip_r3d)
out['prop_clear_swept_rods_hubs'] = res

# ---- puck exit: vertical drop cylinder at (0, y0) below the tube exit
pr = P['puck_d'] / 2
# sample rods densely, hubs as short radial cylinders (hub + TPU cap)
ts = np.linspace(0, 1, 120)
def lower_cage(theta_deg):
    h2, s2, _, _ = geodesic_2v(R, theta_deg)
    h2 = np.array(h2); s2 = np.array(s2)
    pts = (h2[s2[:, 0]][:, None, :] * (1 - ts)[None, :, None] + h2[s2[:, 1]][:, None, :] * ts[None, :, None]).reshape(-1, 3)
    n = h2 / R
    hs = np.concatenate([h2 + n * s for s in np.linspace(-P['hub_h'] / 2, P['hub_h'] / 2 + P['cap_h'], 7)])
    return pts, hs
zc = P['cassette_exit_z']
def clearance_2d(pts, hs, y0):
    p = pts[pts[:, 2] < zc]; h = hs[hs[:, 2] < zc]
    dr = np.hypot(p[:, 0], p[:, 1] - y0).min() - rr
    dh = np.hypot(h[:, 0], h[:, 1] - y0).min() - P['hub_d'] / 2
    return min(dr, dh)
thetas = np.arange(0, 72, 0.25)
cages = [lower_cage(t) for t in thetas]
sweep = []
for y0 in range(0, 141, 2):
    gaps = np.array([clearance_2d(p, h, y0) for p, h in cages])
    sweep.append({'y0': y0, 'max_gap': float(gaps.max() - pr),
                  'frac_open_m0': float((gaps >= pr).mean()),
                  'frac_open_m3': float((gaps >= pr + 3).mean()),
                  'frac_open_m5': float((gaps >= pr + 5).mean()),
                  'best_theta': float(thetas[gaps.argmax()])})
out['puck_drop_sweep'] = sweep
c0 = [s for s in sweep if s['y0'] == 0][0]
out['puck_drop_centreline'] = c0
best = max(sweep, key=lambda s: (s['frac_open_m3'], s['max_gap']))
out['puck_drop_best'] = best
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analysis.json'), 'w'), indent=1)
for k, v in out.items():
    if k != 'puck_drop_sweep':
        print(k, v)
print('y0  maxgap  open@0  open@3  open@5  bestθ')
for s in sweep[::3]:
    print(f"{s['y0']:4d} {s['max_gap']:7.1f} {s['frac_open_m0']:6.2f} {s['frac_open_m3']:6.2f} {s['frac_open_m5']:6.2f} {s['best_theta']:6.1f}")

# ---- chosen cassette offset: window detail + roll-over check
y0 = P['cassette_y']
g = np.array([clearance_2d(p, h, y0) for p, h in cages]) - pr
det = {'y0': y0, 'max_gap_mm': float(g.max()), 'gap_at_model_phase_mm': float(g[np.argmin(abs(thetas - (P['cage_phase'] % 72)))])}
for m in (0, 3, 5, 10):
    o = g >= m
    e = np.flatnonzero(np.diff(np.r_[0, o.astype(int), 0]))
    det[f'windows_deg_margin{m}'] = [[float(thetas[e[i]]), float(thetas[e[i + 1] - 1])] for i in range(0, len(e), 2)]
    det[f'open_deg_per_72_margin{m}'] = float(o.mean() * 72)
# equator rest poses: two equatorial hubs straddle the bottom when phase = 18 + 36k
det['rest_pose_phases_deg'] = [18 + 36 * k for k in range(10)]
det['gap_at_rest_poses_mm'] = [float(g[np.argmin(abs(thetas - (t % 72)))]) for t in (18, 54)]
out['puck_drop_cassette'] = det
g0 = np.array([clearance_2d(p, h, 0.0) for p, h in cages]) - pr
out['gap_curve'] = {'theta_deg': thetas.tolist(), 'y0_0': g0.tolist(), 'y0_cassette': g.tolist()}
# roll-over: puck (h=20) lying on the floor in the band y0 +/- pr; cage rests on equatorial caps
r_contact = R + P['hub_h'] / 2 + P['cap_h']
axle_h_min = r_contact * math.cos(math.radians(18))
pts = (A[:, None, :] * (1 - ts)[None, :, None] + B[:, None, :] * ts[None, :, None]).reshape(-1, 3)
band = (pts[:, 1] > y0 - pr - rr) & (pts[:, 1] < y0 + pr + rr)
r_rod = (np.hypot(pts[band, 0], pts[band, 2]) + rr).max() if band.any() else 0
hb = np.abs(H[:, 1] - y0) < pr + P['hub_d'] / 2
r_hub = (np.linalg.norm(H[hb], axis=1) * 0 + np.hypot(H[hb, 0], H[hb, 2]) + P['hub_h'] / 2 + P['cap_h']).max() if hb.any() else 0
out['rollover'] = {'axle_height_rest_mm': axle_h_min, 'axle_height_on_one_hub_mm': r_contact,
                   'cage_max_radial_in_puck_band_mm': float(max(r_rod, r_hub)),
                   'puck_top_below_axle_at_rest_mm': axle_h_min - P['puck_h'],
                   'clear_mm': float(axle_h_min - P['puck_h'] - max(r_rod, r_hub))}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analysis.json'), 'w'), indent=1)
print('cassette drop', det)
print('rollover', out['rollover'])
