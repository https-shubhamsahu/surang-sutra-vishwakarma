"""Minimal 3D frame (Timoshenko beam, 6 DOF/node) and truss solver in numpy/scipy.

Units: N, mm, MPa.  DOF order per node: ux, uy, uz, rx, ry, rz.
"""
from dataclasses import dataclass
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


@dataclass
class Section:
    name: str
    E: float          # MPa
    G: float          # MPa
    do: float         # outer diameter, mm
    di: float = 0.0   # inner diameter, mm (0 = solid rod)
    rho: float = 2.0e-3  # g/mm^3
    s_allow: float = 400.0  # MPa design allowable
    s_ult: float = 800.0    # MPa nominal strength

    @property
    def A(self):
        return np.pi / 4 * (self.do**2 - self.di**2)

    @property
    def I(self):
        return np.pi / 64 * (self.do**4 - self.di**4)

    @property
    def J(self):
        return 2 * self.I

    @property
    def c(self):
        return self.do / 2

    @property
    def kappa(self):  # Timoshenko shear coefficient
        return 0.9 if self.di == 0 else 0.5

    def Pcr(self, L, K=1.0):
        return np.pi**2 * self.E * self.I / (K * L) ** 2


# ---------------------------------------------------------------- mesh

def subdivide(nodes, struts, n):
    """Split every strut into n elements. Returns mesh nodes, elements (ne x 2), elem->strut map."""
    X = [p for p in nodes]
    elems, owner = [], []
    for s, (a, b) in enumerate(struts):
        chain = [a]
        for k in range(1, n):
            X.append(nodes[a] + (nodes[b] - nodes[a]) * k / n)
            chain.append(len(X) - 1)
        chain.append(b)
        for k in range(n):
            elems.append((chain[k], chain[k + 1]))
            owner.append(s)
    return np.array(X), np.array(elems), np.array(owner)


def local_frames(X, elems, ref_dirs):
    """Rotation matrices lam (ne x 3 x 3), rows = local x,y,z in global coords."""
    d = X[elems[:, 1]] - X[elems[:, 0]]
    L = np.linalg.norm(d, axis=1)
    e1 = d / L[:, None]
    r = ref_dirs - (np.sum(ref_dirs * e1, axis=1))[:, None] * e1
    bad = np.linalg.norm(r, axis=1) < 1e-8
    if bad.any():
        alt = np.tile([0.0, 0.0, 1.0], (bad.sum(), 1))
        r[bad] = alt - (np.sum(alt * e1[bad], axis=1))[:, None] * e1[bad]
    e3 = r / np.linalg.norm(r, axis=1)[:, None]
    e2 = np.cross(e3, e1)
    lam = np.stack([e1, e2, e3], axis=1)
    return lam, L


# ---------------------------------------------------------------- element matrices

def k_local(E, G, A, Iy, Iz, J, L, kappa):
    """Vectorised 12x12 Timoshenko local stiffness. Inputs are arrays (ne,)."""
    ne = len(L)
    k = np.zeros((ne, 12, 12))
    ea = E * A / L
    gj = G * J / L
    k[:, 0, 0] = k[:, 6, 6] = ea
    k[:, 0, 6] = k[:, 6, 0] = -ea
    k[:, 3, 3] = k[:, 9, 9] = gj
    k[:, 3, 9] = k[:, 9, 3] = -gj
    # bending about z (v, rz): dofs 1,5,7,11
    phy = 12 * E * Iz / (kappa * G * A * L**2)
    c = E * Iz / ((1 + phy) * L**3)
    idx = [1, 5, 7, 11]
    m = np.array([[12, 6, -12, 6], [6, 4, -6, 2], [-12, -6, 12, -6], [6, 2, -6, 4]], float)
    for a in range(4):
        for b in range(4):
            val = m[a, b] * np.ones(ne)
            if a in (1, 3) and b in (1, 3):
                val = val * L**2
                if a == b:
                    val = (4 + phy) * L**2
                else:
                    val = (2 - phy) * L**2
            elif a in (1, 3) or b in (1, 3):
                val = val * L
            k[:, idx[a], idx[b]] = c * val
    # bending about y (w, ry): dofs 2,4,8,10 ; sign flips on coupling terms
    phz = 12 * E * Iy / (kappa * G * A * L**2)
    c = E * Iy / ((1 + phz) * L**3)
    idx = [2, 4, 8, 10]
    m = np.array([[12, -6, -12, -6], [-6, 4, 6, 2], [-12, 6, 12, 6], [-6, 2, 6, 4]], float)
    for a in range(4):
        for b in range(4):
            val = m[a, b] * np.ones(ne)
            if a in (1, 3) and b in (1, 3):
                val = ((4 + phz) if a == b else (2 - phz)) * L**2
            elif a in (1, 3) or b in (1, 3):
                val = val * L
            k[:, idx[a], idx[b]] = c * val
    return k


def kg_local(P, L, A, J):
    """Vectorised 12x12 geometric stiffness for axial force P (tension +)."""
    ne = len(L)
    k = np.zeros((ne, 12, 12))
    f = P / (30 * L)
    for idx, s in (([1, 5, 7, 11], 1.0), ([2, 4, 8, 10], -1.0)):
        m = np.array([[36, 3 * s, -36, 3 * s], [3 * s, 4, -3 * s, -1],
                      [-36, -3 * s, 36, -3 * s], [3 * s, -1, -3 * s, 4]], float)
        for a in range(4):
            for b in range(4):
                val = m[a, b] * np.ones(ne)
                if a in (1, 3) and b in (1, 3):
                    val = val * L**2
                elif a in (1, 3) or b in (1, 3):
                    val = val * L
                k[:, idx[a], idx[b]] = f * val
    t = P * (J / A) / L
    k[:, 3, 3] += t
    k[:, 9, 9] += t
    k[:, 3, 9] -= t
    k[:, 9, 3] -= t
    return k


def big_T(lam):
    ne = lam.shape[0]
    T = np.zeros((ne, 12, 12))
    for b in range(4):
        T[:, 3 * b:3 * b + 3, 3 * b:3 * b + 3] = lam
    return T


def assemble(ke, elems, ndof_node, nn):
    ne = len(elems)
    nd = ke.shape[1] // 2
    dofs = np.concatenate([elems[:, [0]] * ndof_node + np.arange(nd)[None, :],
                           elems[:, [1]] * ndof_node + np.arange(nd)[None, :]], axis=1)
    rows = np.repeat(dofs, 2 * nd, axis=1).ravel()
    cols = np.tile(dofs, (1, 2 * nd)).ravel()
    K = sp.coo_matrix((ke.ravel(), (rows, cols)), shape=(nn * ndof_node,) * 2).tocsr()
    return K, dofs


# ---------------------------------------------------------------- frame model

class Frame:
    def __init__(self, X, elems, sec_of_elem, ref_dirs):
        self.X, self.elems = X, elems
        self.nn = len(X)
        self.ndof = 6 * self.nn
        self.lam, self.L = local_frames(X, elems, ref_dirs)
        E = np.array([s.E for s in sec_of_elem]); G = np.array([s.G for s in sec_of_elem])
        A = np.array([s.A for s in sec_of_elem]); I = np.array([s.I for s in sec_of_elem])
        J = np.array([s.J for s in sec_of_elem]); kap = np.array([s.kappa for s in sec_of_elem])
        self.E, self.G, self.A, self.I, self.J, self.kap = E, G, A, I, J, kap
        self.c = np.array([s.c for s in sec_of_elem])
        self.kl = k_local(E, G, A, I, I, J, self.L, kap)
        self.T = big_T(self.lam)
        ke = np.einsum("eji,ejk,ekl->eil", self.T, self.kl, self.T)
        self.K, self.dofs = assemble(ke, elems, 6, self.nn)

    def solve(self, F, fixed):
        free = np.setdiff1d(np.arange(self.ndof), fixed)
        u = np.zeros(self.ndof)
        Kff = self.K[free][:, free].tocsc()
        u[free] = spla.spsolve(Kff, F[free])
        Rxn = self.K @ u - F
        return u, Rxn

    def end_forces(self, u):
        ue = u[self.dofs]                                   # ne x 12 global
        ul = np.einsum("eij,ej->ei", self.T, ue)            # local
        f = np.einsum("eij,ej->ei", self.kl, ul)            # local end forces
        N = f[:, 6]                                         # tension +
        M1 = np.hypot(f[:, 4], f[:, 5]); M2 = np.hypot(f[:, 10], f[:, 11])
        Tq = f[:, 9]
        return N, M1, M2, Tq

    def stresses(self, u):
        N, M1, M2, Tq = self.end_forces(u)
        Mmax = np.maximum(M1, M2)
        sig = np.abs(N) / self.A + Mmax * self.c / self.I
        return dict(N=N, M=Mmax, sig=sig, sig_ax=N / self.A, sig_b=Mmax * self.c / self.I,
                    tau=np.abs(Tq) * self.c / self.J)

    def KG(self, N):
        kg = kg_local(N, self.L, self.A, self.J)
        ke = np.einsum("eji,ejk,ekl->eil", self.T, kg, self.T)
        K, _ = assemble(ke, self.elems, 6, self.nn)
        return K

    def buckling(self, N, fixed, k=6):
        """Smallest positive load factors lambda with (K + lambda KG) phi = 0."""
        free = np.setdiff1d(np.arange(self.ndof), fixed)
        Kff = self.K[free][:, free].tocsc()
        KG = self.KG(N)[free][:, free].tocsc()
        # (-KG) phi = mu K phi, mu = 1/lambda ; largest mu -> smallest positive lambda
        mu, vec = spla.eigsh(-KG, k=k, M=Kff, which="LA")
        order = np.argsort(-mu)
        mu, vec = mu[order], vec[:, order]
        lam = 1.0 / mu
        modes = np.zeros((self.ndof, len(mu)))
        modes[free] = vec
        return lam, modes


class Truss:
    def __init__(self, X, elems, sec_of_elem):
        self.X, self.elems, self.nn = X, elems, len(X)
        self.ndof = 3 * self.nn
        d = X[elems[:, 1]] - X[elems[:, 0]]
        self.L = np.linalg.norm(d, axis=1)
        self.e = d / self.L[:, None]
        self.A = np.array([s.A for s in sec_of_elem]); self.E = np.array([s.E for s in sec_of_elem])
        k = self.E * self.A / self.L
        ee = np.einsum("ei,ej->eij", self.e, self.e) * k[:, None, None]
        ke = np.zeros((len(elems), 6, 6))
        ke[:, :3, :3] = ee; ke[:, 3:, 3:] = ee; ke[:, :3, 3:] = -ee; ke[:, 3:, :3] = -ee
        self.K, self.dofs = assemble(ke, elems, 3, self.nn)

    def solve(self, F, fixed):
        free = np.setdiff1d(np.arange(self.ndof), fixed)
        u = np.zeros(self.ndof)
        u[free] = spla.spsolve(self.K[free][:, free].tocsc(), F[free])
        return u, self.K @ u - F

    def axial(self, u):
        ue = u[self.dofs]
        return self.E * self.A / self.L * np.sum((ue[:, 3:] - ue[:, :3]) * self.e, axis=1)
