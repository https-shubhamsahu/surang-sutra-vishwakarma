"""Linear static + linear buckling analysis of the SURANG cage/axle system."""
import numpy as np
import scipy.sparse.linalg as spla

from frame3d import Frame, Truss, subdivide
from cage_model import spring_matrix, build, R_CAGE
from geodesic import geodesic_2v


class Linear:
    def __init__(self, sysm, anchor_hub=None, k_anchor=1e6):
        """anchor_hub: hub whose two tangential translations are restrained (floor friction at the
        contact point). Without it the cage has a spurious 'roll-off' spin mode under a dead radial load."""
        self.s = sysm
        self.fr = Frame(sysm.X, sysm.elems, sysm.secs, sysm.ref)
        self.K = self.fr.K + spring_matrix(sysm)
        if anchor_hub is not None:
            import scipy.sparse as sp
            n = sysm.hubs[anchor_hub] / np.linalg.norm(sysm.hubs[anchor_hub])
            P = k_anchor * (np.eye(3) - np.outer(n, n))
            r = np.repeat(np.arange(3), 3) + 6 * anchor_hub; c = np.tile(np.arange(3), 3) + 6 * anchor_hub
            self.K = self.K + sp.coo_matrix((P.ravel(), (r, c)), shape=self.K.shape).tocsr()
        self.anchor = anchor_hub
        self.ndof = self.fr.ndof
        self.free = np.setdiff1d(np.arange(self.ndof), sysm.fixed)
        self._lu = spla.splu(self.K[self.free][:, self.free].tocsc())

    def solve(self, F):
        u = np.zeros(self.ndof)
        u[self.free] = self._lu.solve(F[self.free])
        return u

    def hub_load(self, hub, Fmag):
        """Radial inward point load of magnitude Fmag at a hub."""
        n = self.s.hubs[hub] / np.linalg.norm(self.s.hubs[hub])
        F = np.zeros(self.ndof)
        F[6 * hub:6 * hub + 3] = -Fmag * n
        return F, n

    def results(self, u, hub=None):
        s = self.s
        st = self.fr.stresses(u)
        cage = s.owner >= 0
        out = dict(u=u, st=st)
        # per strut: axial force (mean over its elements), max moment, max combined stress
        ns = len(s.struts)
        N = np.zeros(ns); M = np.zeros(ns); sig = np.zeros(ns)
        np.add.at(N, s.owner[cage], st["N"][cage])
        N /= s.n_sub
        np.maximum.at(M, s.owner[cage], st["M"][cage])
        np.maximum.at(sig, s.owner[cage], st["sig"][cage])
        allow = np.array([sec.s_allow for sec in s.strut_secs])
        Pp = np.array([sec.Pcr(L, 1.0) for sec, L in zip(s.strut_secs, s.strut_L)])
        comp = np.maximum(-N, 0)
        out.update(N=N, M=M, sig=sig, U_sig=sig / allow, U_buck_pin=comp / Pp, U_buck_fix=comp / (4 * Pp),
                   Pcr_pin=Pp)
        disp = u.reshape(-1, 6)[:, :3]
        out["disp"] = disp
        out["max_disp"] = float(np.linalg.norm(disp[: s.n_hub], axis=1).max())
        if hub is not None:
            n = s.hubs[hub] / np.linalg.norm(s.hubs[hub])
            out["hub_defl"] = float(-disp[hub] @ n)            # inward +
            # cage-only deflection: hub minus mean pole displacement along n
            pole_mean = 0.5 * (disp[s.poles[0]] + disp[s.poles[1]])
            out["hub_defl_cage"] = float(-(disp[hub] - pole_mean) @ n)
        if s.axle is not None:
            ax = s.owner < 0
            out["axle_sig"] = float(st["sig"][ax].max())
            out["axle_M"] = float(st["M"][ax].max())
            tips = [s.axle_nodes[+1][-1], s.axle_nodes[-1][-1]]
            out["axle_tip_defl"] = [float(np.linalg.norm(disp[t])) for t in tips]
            # bearing radial loads = spring forces
            bl = []
            for a, b, dofs, k in s.springs:
                f = k * (disp[a] - disp[b])
                ey = np.array([0, 1.0, 0])
                fr_ = f - (f @ ey) * ey
                bl.append(dict(radial=float(np.linalg.norm(fr_)), axial=float(abs(f @ ey))))
            out["bearing"] = bl
        return out

    def buckling(self, N_elem, k=6):
        return self._buck(N_elem, k)

    def _buck(self, N_elem, k):
        free = self.free
        Kff = self.K[free][:, free].tocsc()
        KG = self.fr.KG(N_elem)[free][:, free].tocsc()
        mu, vec = spla.eigsh(-KG, k=k, M=Kff, which="LA")
        order = np.argsort(-mu)
        mu, vec = mu[order], vec[:, order]
        modes = np.zeros((self.ndof, len(mu)))
        modes[free] = vec
        return 1.0 / mu, modes


def truss_case(strut_secs, hub, Fmag, R=R_CAGE):
    """Pinned-joint (truss) variant with rigid axle: poles fixed in translation."""
    nodes, struts, faces, val, cls = geodesic_2v(R)
    if not isinstance(strut_secs, list):
        strut_secs = [strut_secs] * len(struts)
    tr = Truss(nodes, struts, strut_secs)
    pP = int(np.argmax(nodes[:, 1])); pM = int(np.argmin(nodes[:, 1]))
    # rigid-body spin about Y: restrain the tangential dof of one ring hub next to +Y pole
    ring = [i for i in range(len(nodes)) if any((a == pP and b == i) or (b == pP and a == i) for a, b in struts)][0]
    t = np.cross([0, 1.0, 0], nodes[ring]); t /= np.linalg.norm(t)
    # add penalty spring along t at ring node
    import scipy.sparse as sp
    Kpen = sp.lil_matrix(tr.K.shape)
    Kpen[3 * ring:3 * ring + 3, 3 * ring:3 * ring + 3] = 1e6 * np.outer(t, t)
    tr.K = tr.K + Kpen.tocsr()
    fixed = np.array([3 * pP, 3 * pP + 1, 3 * pP + 2, 3 * pM, 3 * pM + 1, 3 * pM + 2])
    n = nodes[hub] / np.linalg.norm(nodes[hub])
    F = np.zeros(tr.ndof); F[3 * hub:3 * hub + 3] = -Fmag * n
    u, Rx = tr.solve(F, fixed)
    N = tr.axial(u)
    A = np.array([s.A for s in strut_secs])
    L = np.linalg.norm(nodes[struts[:, 1]] - nodes[struts[:, 0]], axis=1)
    Pp = np.array([s.Pcr(l) for s, l in zip(strut_secs, L)])
    return dict(N=N, sig=np.abs(N) / A, U_buck_pin=np.maximum(-N, 0) / Pp,
                hub_defl=float(-u[3 * hub:3 * hub + 3] @ n), u=u)
