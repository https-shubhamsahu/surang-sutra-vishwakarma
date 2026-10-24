"""Geometrically nonlinear (co-rotational) 3D frame solver with unilateral floor contact.

- Element: 2-node Timoshenko beam, linear-elastic material, large rotations via a
  co-rotating chord frame (Crisfield-type mean-rotation triad).
- Residual is exact equilibrium in the deformed configuration; tangent is the
  updated-Lagrangian elastic + geometric (axial-force) stiffness in the current frame.
- Loading: a rigid frictionless floor is displaced by s toward the inner frame
  (displacement control). TPU caps are penalty springs at the hubs.
Units N, mm, MPa.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from frame3d import local_frames, k_local, kg_local, assemble

I3 = np.eye(3)


def skew(v):
    S = np.zeros(v.shape[:-1] + (3, 3))
    S[..., 0, 1] = -v[..., 2]; S[..., 0, 2] = v[..., 1]
    S[..., 1, 0] = v[..., 2]; S[..., 1, 2] = -v[..., 0]
    S[..., 2, 0] = -v[..., 1]; S[..., 2, 1] = v[..., 0]
    return S


def expm(v):
    th = np.linalg.norm(v, axis=-1)
    sm = th < 1e-7
    ths = np.where(sm, 1.0, th)
    a = np.where(sm, 1 - th**2 / 6, np.sin(ths) / ths)
    b = np.where(sm, 0.5 - th**2 / 24, (1 - np.cos(ths)) / ths**2)
    K = skew(v)
    return I3 + a[..., None, None] * K + b[..., None, None] * (K @ K)


def logm(R):
    tr = np.trace(R, axis1=-2, axis2=-1)
    th = np.arccos(np.clip((tr - 1) / 2, -1, 1))
    w = 0.5 * np.stack([R[..., 2, 1] - R[..., 1, 2], R[..., 0, 2] - R[..., 2, 0],
                        R[..., 1, 0] - R[..., 0, 1]], -1)
    sm = th < 1e-6
    f = np.where(sm, 1 + th**2 / 6, th / np.sin(np.where(sm, 1.0, th)))
    return w * f[..., None]


class Corot:
    def __init__(self, sysm, imperfection=1 / 500, seed=7, cap_k=3000.0, rod_k=1e4, cap_t=5.0,
                 cap_k1=None, cap_g1=0.0, friction=True):
        s = self.s = sysm
        X0 = s.X.copy()
        # strut bow imperfection (sinusoidal, random lateral direction per strut), amplitude L*imp
        if imperfection and s.n_sub > 1:
            rng = np.random.default_rng(seed)
            n = s.n_sub
            for k, (a, b) in enumerate(s.struts):
                d = s.hubs[b] - s.hubs[a]; L = np.linalg.norm(d); e = d / L
                v = rng.normal(size=3); v -= (v @ e) * e; v /= np.linalg.norm(v)
                elems = np.where(s.owner == k)[0]
                inner = [s.elems[ei, 1] for ei in elems[:-1]]
                for j, node in enumerate(inner, start=1):
                    X0[node] += imperfection * L * np.sin(np.pi * j / n) * v
        self.X0 = X0
        self.lam, self.L0 = local_frames(X0, s.elems, s.ref)
        g = lambda attr: np.array([getattr(sec, attr) for sec in s.secs])
        self.E, self.G, self.A, self.I, self.J = g("E"), g("G"), g("A"), g("I"), g("J")
        self.kap = np.array([sec.kappa for sec in s.secs]); self.c = g("c")
        self.kl = k_local(self.E, self.G, self.A, self.I, self.I, self.J, self.L0, self.kap)
        self.nn = len(X0); self.ndof = 6 * self.nn
        self.free = np.setdiff1d(np.arange(self.ndof), s.fixed)
        # contact candidates: all cage nodes (hubs carry TPU caps)
        ncage = s.n_hub + len(s.struts) * (s.n_sub - 1)
        self.cnodes = np.arange(ncage)
        self.c_off = np.where(self.cnodes < s.n_hub, cap_t, 0.0)
        self.c_k = np.where(self.cnodes < s.n_hub, cap_k, rod_k)
        self.rod_r = np.array([s.secs[np.where(s.owner >= 0)[0][0]].c])
        # bilinear cap law: soft k1 up to stroke g1, then k (bottomed-out TPU)
        self.cap_k1 = cap_k if cap_k1 is None else cap_k1
        self.cap_g1 = cap_g1
        self.friction = friction
        self.reset()

    def reset(self):
        self.x = self.X0.copy()
        self.Rn = np.tile(I3, (self.nn, 1, 1))
        self.anchor = {}            # stick-friction anchor (tangential position) per contacting node

    # ----------------------------------------------------------- element kinematics/forces
    def elem_forces(self, xi, xj, Ri, Rj):
        """Element end forces in global coords (ne x 12) from per-element end states."""
        d = xj - xi; l = np.linalg.norm(d, axis=1); e1 = d / l[:, None]
        dR = np.einsum("eji,ejk->eik", Ri, Rj)
        Rm = Ri @ expm(0.5 * logm(dR))
        q = np.einsum("eij,ej->ei", Rm, self.lam[:, 1, :])
        e3 = np.cross(e1, q); e3 /= np.linalg.norm(e3, axis=1)[:, None]
        e2 = np.cross(e3, e1)
        Rr = np.stack([e1, e2, e3], axis=2)                       # local -> global
        thi = logm(np.einsum("eji,ejk,elk->eil", Rr, Ri, self.lam))
        thj = logm(np.einsum("eji,ejk,elk->eil", Rr, Rj, self.lam))
        dl = np.zeros((len(l), 12))
        dl[:, 3:6] = thi; dl[:, 6] = l - self.L0; dl[:, 9:12] = thj
        f = np.einsum("eij,ej->ei", self.kl, dl)
        Mz = f[:, 5] + f[:, 11]; My = f[:, 4] + f[:, 10]
        f[:, 1] = Mz / l; f[:, 7] = -Mz / l; f[:, 2] = -My / l; f[:, 8] = My / l
        fg = np.concatenate([np.einsum("eij,ej->ei", Rr, f[:, 3 * b:3 * b + 3]) for b in range(4)], axis=1)
        return fg, dict(l=l, Rr=Rr, f=f, thi=thi, thj=thj)

    def _ends(self):
        ei, ej = self.s.elems[:, 0], self.s.elems[:, 1]
        return self.x[ei], self.x[ej], self.Rn[ei], self.Rn[ej]

    def elem_state(self):
        fg, st = self.elem_forces(*self._ends())
        st["fg"] = fg
        return st

    def internal(self, st):
        fg = st["fg"]
        Fi = np.zeros((self.nn, 6))
        np.add.at(Fi, self.s.elems[:, 0], fg[:, :6])
        np.add.at(Fi, self.s.elems[:, 1], fg[:, 6:])
        for a, b, dofs, k in self.s.springs:
            for dd in dofs:
                if dd < 3:
                    du = (self.x[a, dd] - self.X0[a, dd]) - (self.x[b, dd] - self.X0[b, dd])
                else:
                    du = logm(self.Rn[a])[dd - 3] - logm(self.Rn[b])[dd - 3]
                Fi[a, dd] += k * du; Fi[b, dd] -= k * du
        return Fi.ravel()

    def tangent(self, st, ht=1e-6, hr=1e-7):
        """Consistent element tangent by central differences (vectorised over elements)."""
        xi, xj, Ri, Rj = self._ends()
        ne = len(xi)
        ke = np.zeros((ne, 12, 12))
        for k in range(12):
            node, comp = divmod(k, 6)
            res = []
            for sgn in (+1, -1):
                a = [xi.copy(), xj.copy(), Ri, Rj]
                if comp < 3:
                    a[node][:, comp] += sgn * ht
                    h = ht
                else:
                    w = np.zeros((ne, 3)); w[:, comp - 3] = sgn * hr
                    a[2 + node] = expm(w) @ a[2 + node]
                    h = hr
                res.append(self.elem_forces(*a)[0])
            ke[:, :, k] = (res[0] - res[1]) / (2 * h)
        K, _ = assemble(ke, self.s.elems, 6, self.nn)
        rows, cols, vals = [], [], []
        for a, b, dofs, k in self.s.springs:
            for dd in dofs:
                ia, ib = 6 * a + dd, 6 * b + dd
                rows += [ia, ib, ia, ib]; cols += [ia, ib, ib, ia]; vals += [k, k, -k, -k]
        K = K + sp.coo_matrix((vals, (rows, cols)), shape=K.shape).tocsr()
        return K

    # ----------------------------------------------------------- contact
    def _normal_law(self, g, hub, k2):
        """Contact force and stiffness vs penetration g (>0)."""
        k1, g1 = self.cap_k1, self.cap_g1
        f = np.where(hub & (g > g1), k1 * g1 + k2 * (g - g1), np.where(hub, k1 * g, k2 * g))
        kt = np.where(hub & (g > g1), k2, np.where(hub, k1, k2))
        return f, kt

    def contact(self, s_floor, n0, R, commit=False):
        xc = self.x[self.cnodes]
        hub = self.cnodes < self.s.n_hub
        plane = R + self.c_off.max() - s_floor        # floor position along n0 (struck cap face at R+cap)
        g = xc @ n0 + self.c_off + np.where(hub, 0.0, self.rod_r[0]) - plane
        act = g > 0
        Fc = np.zeros((self.nn, 6))
        f, kn = self._normal_law(g[act], hub[act], self.c_k[act])
        nodes = self.cnodes[act]
        Fc[nodes, :3] = -f[:, None] * n0[None, :]
        P = np.eye(3) - np.outer(n0, n0)
        rows, cols, vals = [], [], []
        nn0 = np.outer(n0, n0)
        ftan_ratio = 0.0
        for node, k_n, fn in zip(nodes, kn, f):
            Kloc = k_n * nn0
            if self.friction:
                if node not in self.anchor:
                    self.anchor[node] = P @ self.x[node]
                kt = max(k_n, 50.0)
                ft = -kt * (P @ self.x[node] - self.anchor[node])
                Fc[node, :3] += ft
                Kloc = Kloc + kt * P
                ftan_ratio = max(ftan_ratio, np.linalg.norm(ft) / max(fn, 1e-9))
            for a in range(3):
                for b in range(3):
                    rows.append(6 * node + a); cols.append(6 * node + b); vals.append(Kloc[a, b])
        # release anchors of nodes that left contact
        for node in list(self.anchor):
            if node not in set(nodes.tolist()):
                del self.anchor[node]
        self.ftan_ratio = ftan_ratio
        Kc = sp.coo_matrix((vals, (rows, cols)), shape=(self.ndof, self.ndof)).tocsr()
        return Fc.ravel(), Kc, float(f.sum()), int((act & hub).sum())

    def update(self, du):
        du = du.reshape(-1, 6)
        self.x += du[:, :3]
        self.Rn = expm(du[:, 3:]) @ self.Rn

    def solve_floor(self, n0, R, s_max, ds0=0.2, ds_min=0.002, tol=1e-6, maxit=40, verbose=False,
                    record_every=1, stop_energy=None, extra_s=0.0):
        """Push a rigid floor (normal n0 = outward normal of struck point) inward by up to s_max.
        stop_energy(s, U) -> True stops the run (e.g. drop energy reached)."""
        hist = []
        s_cur, ds, U, F_prev = 0.0, ds0 / 20, 0.0, 0.0
        pred, pred_ds = None, 1.0
        k = 0
        stopped = False
        while s_cur < s_max - 1e-9:
            ds = min(ds, s_max - s_cur)
            x_bak, R_bak, A_bak = self.x.copy(), self.Rn.copy(), dict(self.anchor)
            s_new = s_cur + ds
            ok = False
            step_du = np.zeros(self.ndof)
            if pred is not None:                      # secant predictor along the equilibrium path
                p = pred * (ds / pred_ds)
                self.update(p); step_du += p
            for it in range(maxit):
                st = self.elem_state()
                Fint = self.internal(st)
                Fc, Kc, Fsum, nact = self.contact(s_new, n0, R)
                r = Fc - Fint
                rf = r[self.free]
                ref = max(1.0, Fsum)
                K = self.tangent(st) + Kc
                Kff = K[self.free][:, self.free].tocsc()
                try:
                    dv = spla.spsolve(Kff, rf)
                except Exception:
                    break
                if not np.all(np.isfinite(dv)):
                    break
                du = np.zeros(self.ndof); du[self.free] = dv
                # limit rotation increment for robustness
                mx = np.abs(du.reshape(-1, 6)[:, 3:]).max()
                if mx > 0.2:
                    du *= 0.2 / mx
                self.update(du); step_du += du
                if np.linalg.norm(rf) < 1e-4 * ref and np.abs(dv).max() < 1e-5:
                    ok = True
                    break
            if not ok:
                self.x, self.Rn, self.anchor = x_bak, R_bak, A_bak
                pred = None
                ds *= 0.5
                if ds < ds_min:
                    if verbose:
                        print(f"  !! no convergence at s={s_cur:.3f}, stopping")
                    break
                continue
            st = self.elem_state()
            Fc, Kc, Fsum, nact = self.contact(s_new, n0, R)
            pred, pred_ds = step_du, ds
            U += 0.5 * (Fsum + F_prev) * ds
            F_prev = Fsum
            s_cur = s_new
            k += 1
            rec = self.snapshot(st, s_cur, Fsum, U, nact)
            if k % record_every == 0 or True:
                hist.append(rec)
            if verbose and k % 10 == 0:
                print(f"  s={s_cur:7.2f} F={Fsum:8.1f} U={U/1000:6.2f}J sig_cage={rec['sig_cage']:7.1f} "
                      f"sig_axle={rec['sig_axle']:7.1f} ncontact={nact} it={it}")
            if stop_energy is not None and stop_energy(s_cur, U):
                stopped = True
                break
            if it < 6:
                ds = min(ds * 1.5, ds0)
        return hist, stopped

    def snapshot(self, st, s_cur, Fsum, U, nact):
        f = st["f"]
        N = f[:, 6]
        M = np.maximum(np.hypot(f[:, 4], f[:, 5]), np.hypot(f[:, 10], f[:, 11]))
        sig = np.abs(N) / self.A + M * self.c / self.I
        cage = self.s.owner >= 0
        ax = ~cage
        allow = np.array([sec.s_allow for sec in self.s.secs])
        xc = self.x[: self.s.n_hub]
        brg = []
        for a, b, dofs, k in self.s.springs:
            f = k * ((self.x[a] - self.X0[a]) - (self.x[b] - self.X0[b]))
            ey = np.array([0, 1.0, 0])
            ra = logm(self.Rn[a]); rb = logm(self.Rn[b])
            mis = ra - rb; mis -= (mis @ ey) * ey
            brg.append(dict(radial=float(np.linalg.norm(f - (f @ ey) * ey)), axial=float(abs(f @ ey)),
                            misalign_deg=float(np.degrees(np.linalg.norm(mis)))))
        return dict(s=s_cur, F=Fsum, U=U, nact=nact, ftan=getattr(self, "ftan_ratio", 0.0), bearing=brg,
                    sig_cage=float(sig[cage].max()), U_cage=float((sig / allow)[cage].max()),
                    sig_axle=float(sig[ax].max()) if ax.any() else 0.0,
                    Nmin=float(N[cage].min()), sig=sig.copy(), N=N.copy(), M=M.copy(),
                    x=self.x.copy())
