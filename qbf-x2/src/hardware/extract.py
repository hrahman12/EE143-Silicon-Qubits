"""EM extraction of the drawn QBF-X2 geometry: capacitance (3D and 2D boundary elements), inductance (kinetic square
counting + 2D cross-section geometric inductance + Grover/Ruehli partial inductances), the beam-splitter E_C,M and
E_S, and verify() which compares the extracted values with the architecture targets.

Conventions: lengths in um, capacitance in fF, inductance in pH, energies in GHz (h = 1).

Electrostatics (3D)
    All conductors are zero-thickness sheets in the vacuum/silicon interface plane. For a charge in that plane the
    half-space Green's function is G(r) = 1 / (2 pi eps0 (1 + eps_Si) r) = 1 / (4 pi eps0 eps_eff r),
    eps_eff = (1 + eps_Si) / 2, eps_Si = 11.45 (silicon at mK). The sheets are cut into rectangular panels with a
    uniform charge each; the potential coefficient P_ij (potential at the centroid of panel i from a unit charge
    spread over panel j) uses the closed-form potential of a uniformly charged rectangle for near pairs and the point
    charge for far pairs (centroid collocation). Conductors are equipotentials, except granular-Al inductors, whose
    potential is interpolated linearly between the two nodes they join (energy-consistent lumping of a distributed
    line). The capacitance matrix is C = W^T P^-1 W with W the panel-to-node weights.
    Crossover (parallel-plate) capacitors are not in the interface model; they are added analytically:
    C = eps0 eps_d A / d + (edge length) x (edge capacitance per length), the edge term computed once by a 2D finite
    difference solve of the real layer stack (crossover_edge_term()).
Electrostatics (2D)
    Coplanar strips in the interface plane (cross-sections): line-charge panels with the closed-form potential of a
    uniformly charged segment, total charge constrained to zero (2D log kernel). Used for the geometric inductance
    L' = mu0 eps0 C_vac'^-1 of the uniform multiconductor sections and validated against the exact conformal-mapping
    capacitance of a coplanar waveguide on a silicon half-space.
"""
from __future__ import annotations

import math

import numpy as np
import scipy.linalg as sla

EPS0 = 8.8541878128e-12          # F/m
MU0 = 1.25663706212e-6           # H/m
HBAR = 1.054571817e-34
KB = 1.380649e-23
E_CHARGE = 1.602176634e-19
EPS_SI = 11.45                   # silicon relative permittivity at mK
EPS0_FF_PER_UM = EPS0 * 1e-6 * 1e15   # eps0 in fF/um (8.854e-3)


# ====================================================================================================================
# materials (documented assumptions; the sensitivity study varies the uncertain ones)
# ====================================================================================================================
MATERIALS = dict(
    gral=dict(L_sq_pH=500.0, t_nm=20.0, note="granular Al sheet kinetic inductance (architecture GRAL_NH_PER_SQ)"),
    al=dict(R_sq_ohm=1.0, Tc_K=1.25, t_nm=30.0,
            note="thin e-beam-evaporated Al (Al1 and Al2 both 30 nm): rho(4 K) ~ 3 uOhm cm -> R_sq = 1.0 Ohm; "
                 "thin-film Tc = 1.25 K, Delta = 1.764 k_B Tc; L_sq = hbar R_sq / (pi Delta)"),
    nb=dict(lambda_nm=90.0, t_nm=150.0, note="sputtered Nb: L_sq = mu0 lambda coth(t / lambda)"),
    diel=dict(eps_r=7.0, d_nm=100.0, note="PECVD SiNx crossover dielectric, 100 nm, eps_r = 7.0 (mK)"),
    si=dict(eps_r=EPS_SI),
)


def al_Lsq_pH(R_sq_ohm=None, Tc_K=None) -> float:
    R = MATERIALS["al"]["R_sq_ohm"] if R_sq_ohm is None else R_sq_ohm
    Tc = MATERIALS["al"]["Tc_K"] if Tc_K is None else Tc_K
    delta = 1.764 * KB * Tc
    return HBAR * R / (math.pi * delta) * 1e12


def nb_Lsq_pH(lambda_nm=None, t_nm=None) -> float:
    lam = (MATERIALS["nb"]["lambda_nm"] if lambda_nm is None else lambda_nm) * 1e-9
    t = (MATERIALS["nb"]["t_nm"] if t_nm is None else t_nm) * 1e-9
    return MU0 * lam / math.tanh(t / lam) * 1e12


def gral_Lsq_pH() -> float:
    return MATERIALS["gral"]["L_sq_pH"]


def diel_fF_per_um2() -> float:
    return EPS0_FF_PER_UM * MATERIALS["diel"]["eps_r"] / (MATERIALS["diel"]["d_nm"] * 1e-3)


# ====================================================================================================================
# 3D interface-plane BEM
# ====================================================================================================================
def _F(u, v):
    """antiderivative of 1/sqrt(u^2 + v^2) in du dv: u asinh(v/|u|) + v asinh(u/|v|) (0 on the axes)"""
    au, av = np.abs(u), np.abs(v)
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = np.where(au > 0, u * np.arcsinh(v / np.where(au > 0, au, 1.0)), 0.0)
        t2 = np.where(av > 0, v * np.arcsinh(u / np.where(av > 0, av, 1.0)), 0.0)
    return t1 + t2


def rect_integral(x, y, x1, x2, y1, y2):
    """int over the rectangle [x1,x2]x[y1,y2] of dA' / |r - r'|, evaluated at (x, y) in the same plane (exact)"""
    return _F(x2 - x, y2 - y) - _F(x1 - x, y2 - y) - _F(x2 - x, y1 - y) + _F(x1 - x, y1 - y)


def _G4(u, v):
    """4th antiderivative of 1/sqrt(u^2+v^2) (d^2/du^2 d^2/dv^2 G = 1/r), even in u and v, C^1 across the axes"""
    au, av = np.abs(u), np.abs(v)
    r = np.sqrt(au * au + av * av)
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = np.where((au > 0) & (av > 0), 0.5 * au * au * av * np.arcsinh(av / np.where(au > 0, au, 1.0)), 0.0)
        t2 = np.where((au > 0) & (av > 0), 0.5 * au * av * av * np.arcsinh(au / np.where(av > 0, av, 1.0)), 0.0)
    return t1 + t2 - r ** 3 / 6.0


def rect_rect_integral(ax1, ax2, ay1, ay2, bx1, bx2, by1, by2):
    """int over rectangle a int over rectangle b of dA dA' / |r - r'| (coplanar, exact, Galerkin kernel)"""
    us = ((bx2 - ax1, 1.0), (bx2 - ax2, -1.0), (bx1 - ax1, -1.0), (bx1 - ax2, 1.0))
    vs = ((by2 - ay1, 1.0), (by2 - ay2, -1.0), (by1 - ay1, -1.0), (by1 - ay2, 1.0))
    tot = 0.0
    for uu, su in us:
        for vv, sv in vs:
            tot = tot + su * sv * _G4(uu, vv)
    return tot


def _grade(a, b, h0, hmax, growth=1.6, refine_lo=True, refine_hi=True):
    """1D partition of [a, b]: panels of size h0 at refined ends growing geometrically up to hmax"""
    L = b - a
    if L <= 0:
        return np.array([a, b])
    if L <= 2 * h0 or (not refine_lo and not refine_hi and L <= hmax):
        return np.array([a, b])

    def side():
        out, h, s = [], h0, 0.0
        while s + h < L / 2 and h < hmax:
            s += h
            out.append(s)
            h *= growth
        return out

    lo = side() if refine_lo else []
    hi = side() if refine_hi else []
    s_lo = lo[-1] if lo else 0.0
    s_hi = hi[-1] if hi else 0.0
    mid = L - s_lo - s_hi
    if mid < 0:                                     # both refined sides overlap: trim
        lo = [s for s in lo if s < L / 2]
        hi = [s for s in hi if s < L / 2]
        s_lo = lo[-1] if lo else 0.0
        s_hi = hi[-1] if hi else 0.0
        mid = L - s_lo - s_hi
    nm = max(1, int(math.ceil(mid / hmax - 1e-9)))
    pts = [0.0] + lo + [s_lo + mid * (i + 1) / nm for i in range(nm)] + [L - s for s in reversed(hi)]
    pts = np.unique(np.round(np.array(pts), 9))
    return a + pts


class Panels:
    """rectangular panels with node weights. Each entry: (x1, x2, y1, y2), and a weight row over the nodes."""

    def __init__(self):
        self.r = []          # rectangles
        self.w = []          # list of dict node -> weight
        self.tag = []

    def add_rect(self, x1, x2, y1, y2, weights, h0=0.05, hmax=0.5, growth=1.6, refine=(True, True, True, True),
                 tag=""):
        """mesh a rectangle; weights: dict node -> weight (constant) or ('lin', axis, node_a, node_b, s0, s1) for a
        potential interpolated linearly along axis between coordinate s0 (node_a) and s1 (node_b)"""
        xs = _grade(x1, x2, h0, hmax, growth, refine[0], refine[1])
        ys = _grade(y1, y2, h0, hmax, growth, refine[2], refine[3])
        for i in range(len(xs) - 1):
            for j in range(len(ys) - 1):
                self.r.append((xs[i], xs[i + 1], ys[j], ys[j + 1]))
                if isinstance(weights, tuple) and weights[0] == "lin":
                    _, axis, na, nb, s0, s1 = weights
                    c = 0.5 * (xs[i] + xs[i + 1]) if axis == "x" else 0.5 * (ys[j] + ys[j + 1])
                    t = min(max((c - s0) / (s1 - s0), 0.0), 1.0)
                    self.w.append({na: 1 - t, nb: t})
                else:
                    self.w.append(dict(weights))
                self.tag.append(tag)

    def __len__(self):
        return len(self.r)

    def arrays(self):
        R = np.array(self.r, float)
        return R[:, 0], R[:, 1], R[:, 2], R[:, 3]


def potential_matrix(panels: Panels, eps_eff: float, near=4.0, block=1500, galerkin=True):
    """P_ij in units of 1/(eps0 * um): potential at centroid i from a unit charge spread over panel j.
    Near pairs (|r_ij| < near * max(size_i, size_j)): exact panel-panel average (Galerkin, default) or the exact
    rectangle potential at the centroid (collocation); far pairs: point charges."""
    x1, x2, y1, y2 = panels.arrays()
    cx, cy = 0.5 * (x1 + x2), 0.5 * (y1 + y2)
    A = (x2 - x1) * (y2 - y1)
    size = np.maximum(x2 - x1, y2 - y1)
    n = len(cx)
    k = 1.0 / (4 * math.pi * eps_eff)
    P = np.empty((n, n))
    for i0 in range(0, n, block):
        i1 = min(n, i0 + block)
        dx = cx[i0:i1, None] - cx[None, :]
        dy = cy[i0:i1, None] - cy[None, :]
        r = np.hypot(dx, dy)
        with np.errstate(divide="ignore"):
            Pb = k / r
        lim = near * np.maximum(size[i0:i1, None], size[None, :])
        ii, jj = np.nonzero(r < lim)
        gi = ii + i0
        if galerkin:
            Pb[ii, jj] = k * rect_rect_integral(x1[gi], x2[gi], y1[gi], y2[gi], x1[jj], x2[jj], y1[jj], y2[jj]) \
                / (A[gi] * A[jj])
        else:
            Pb[ii, jj] = k * rect_integral(cx[gi], cy[gi], x1[jj], x2[jj], y1[jj], y2[jj]) / A[jj]
        P[i0:i1] = Pb
    return P


def potential_matrix_periodic(panels: Panels, eps_eff: float, T: float, K: int = 20, near=4.0, block=1200):
    """potential coefficients of an x-periodic sheet structure (period T): sum over images m = -K..K of the panel
    potential. Images m = -1, 0, +1 get the exact near-field (Galerkin) treatment, |m| >= 2 are point charges.
    The truncated lattice sum differs from the converged one by a constant common to all pairs (plus O((x/KT)^2)),
    which the neutrality constraint of periodic_charges() absorbs: an infinitely long structure has no net charge
    per period (its capacitance to infinity per unit length vanishes)."""
    x1, x2, y1, y2 = panels.arrays()
    cx, cy = 0.5 * (x1 + x2), 0.5 * (y1 + y2)
    A = (x2 - x1) * (y2 - y1)
    size = np.maximum(x2 - x1, y2 - y1)
    n = len(cx)
    k = 1.0 / (4 * math.pi * eps_eff)
    P = np.zeros((n, n))
    ms = np.arange(2, K + 1)
    for i0 in range(0, n, block):
        i1 = min(n, i0 + block)
        dy = cy[i0:i1, None] - cy[None, :]
        dy2 = dy * dy
        Pb = np.zeros((i1 - i0, n))
        lim = near * np.maximum(size[i0:i1, None], size[None, :])
        for m in (-1, 0, 1):
            dx = cx[i0:i1, None] - (cx[None, :] + m * T)
            r = np.sqrt(dx * dx + dy2)
            with np.errstate(divide="ignore"):
                Pm = k / r
            ii, jj = np.nonzero(r < lim)
            gi = ii + i0
            Pm[ii, jj] = k * rect_rect_integral(x1[gi], x2[gi], y1[gi], y2[gi], x1[jj] + m * T, x2[jj] + m * T,
                                                y1[jj], y2[jj]) / (A[gi] * A[jj])
            Pb += Pm
        dx0 = cx[i0:i1, None] - cx[None, :]
        for m in ms:
            Pb += k / np.sqrt((dx0 - m * T) ** 2 + dy2) + k / np.sqrt((dx0 + m * T) ** 2 + dy2)
        P[i0:i1] = Pb
    return P


def periodic_charges(panels: Panels, nodes: list, excitations: list, eps_eff: float, T: float, K: int = 20):
    """x-periodic interface BEM. excitations: list of dicts node -> potential (nodes not mentioned, and panels of
    nodes not in `nodes`, are at 0 V). Returns Q (n_exc x n_nodes) in fF*V: the charge per period on each node
    (charge of 'ground' = everything not in nodes is -sum). Neutrality per period is enforced."""
    P = potential_matrix_periodic(panels, eps_eff, T, K)
    W = weight_matrix(panels, nodes)
    n = len(panels)
    Vp = np.zeros((n, len(excitations)))
    for e, ex in enumerate(excitations):
        v = np.array([ex.get(nd, 0.0) for nd in nodes])
        Vp[:, e] = W @ v
    M = np.zeros((n + 1, n + 1))
    M[:n, :n] = P
    M[:n, n] = 1.0
    M[n, :n] = 1.0
    rhs = np.vstack([Vp, np.zeros((1, len(excitations)))])
    sol = sla.solve(M, rhs, overwrite_a=True, check_finite=False)
    q = sol[:n]
    Q = (W.T @ q).T * EPS0_FF_PER_UM
    return Q, dict(panels=n, total_charge=(q.sum(axis=0) * EPS0_FF_PER_UM).tolist())


def weight_matrix(panels: Panels, nodes: list):
    idx = {nd: i for i, nd in enumerate(nodes)}
    W = np.zeros((len(panels), len(nodes)))
    for p, wd in enumerate(panels.w):
        for nd, wv in wd.items():
            if nd in idx:
                W[p, idx[nd]] += wv
    return W


def capacitance_matrix(panels: Panels, nodes: list, eps_eff: float, columns=None, near=4.0, galerkin=True):
    """Maxwell capacitance matrix (fF) between the listed nodes; panels belonging to nodes not in the list are held
    at 0 V (ground). columns: subset of nodes for which the columns are computed (all if None). Returns (C, info)."""
    P = potential_matrix(panels, eps_eff, near=near, galerkin=galerkin)
    W = weight_matrix(panels, nodes)
    cols = list(range(len(nodes))) if columns is None else [nodes.index(c) for c in columns]
    lu = sla.lu_factor(P, overwrite_a=True, check_finite=False)
    q = sla.lu_solve(lu, W[:, cols], check_finite=False)
    C = W.T @ q * EPS0_FF_PER_UM                       # charge (eps0 um V) -> fF
    return C, dict(panels=len(panels), q=q)


# ====================================================================================================================
# 2D BEM: coplanar strips in the interface plane (cross-sections) and general horizontal segments (validation)
# ====================================================================================================================
def _seg_logint(t, h):
    """int ln sqrt(t^2 + h^2) dt (antiderivative)"""
    t = np.asarray(t, float)
    h = np.asarray(h, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        r2 = t * t + h * h
        lg = np.where(r2 > 0, 0.5 * np.log(np.where(r2 > 0, r2, 1.0)), 0.0)
        at = np.where(np.abs(h) > 0, h * np.arctan(t / np.where(np.abs(h) > 0, h, 1.0)), 0.0)
    return t * lg - t + at


def segments_2d(strips, h0=0.01, hmax=0.25, growth=1.5):
    """strips: list of (x_left, x_right, z, conductor). Returns panel arrays (a, b, z, cond)."""
    a, b, z, c = [], [], [], []
    for (xl, xr, zz, cond) in strips:
        xs = _grade(xl, xr, h0, hmax, growth)
        for i in range(len(xs) - 1):
            a.append(xs[i]); b.append(xs[i + 1]); z.append(zz); c.append(cond)
    return np.array(a), np.array(b), np.array(z), c


def capacitance_2d(strips, conductors, eps_eff=1.0, h0=0.01, hmax=0.25, growth=1.5):
    """per-unit-length Maxwell capacitance matrix (fF/um = nF/m) of horizontal strips in a homogeneous medium of
    relative permittivity eps_eff (for strips in the interface plane eps_eff = (1 + eps_sub)/2 is exact).
    Every strip belongs to a conductor in `conductors`; total charge is constrained to zero (2D log kernel), so the
    returned matrix has zero row sums (the full Maxwell matrix including the reference conductor)."""
    a, b, z, cond = segments_2d(strips, h0, hmax, growth)
    xc = 0.5 * (a + b)
    n = len(a)
    h = z[:, None] - z[None, :]
    # potential at centroid i from unit line charge density on segment j: -(1/(2 pi eps)) int ln r dx'
    P = -(_seg_logint(b[None, :] - xc[:, None], h) - _seg_logint(a[None, :] - xc[:, None], h)) / (2 * math.pi * eps_eff)
    P = P / (b - a)[None, :]                          # per unit total charge on the segment
    idx = {cnd: i for i, cnd in enumerate(conductors)}
    W = np.zeros((n, len(conductors)))
    for p, cnd in enumerate(cond):
        W[p, idx[cnd]] = 1.0
    M = np.zeros((n + 1, n + 1))
    M[:n, :n] = P
    M[:n, n] = 1.0                                     # unknown reference potential
    M[n, :n] = 1.0                                     # total charge zero
    rhs = np.vstack([W, np.zeros((1, len(conductors)))])
    sol = np.linalg.solve(M, rhs)
    q = sol[:n]
    C = W.T @ q * EPS0_FF_PER_UM                      # (eps0 * V) per um length -> fF/um
    return 0.5 * (C + C.T)


def cpw_exact_fF_per_um(w, s, wg=None, eps_r=EPS_SI):
    """exact conformal-mapping capacitance per length of a zero-thickness CPW on a substrate half-space:
    C' = 2 eps0 (eps_r + 1) K(k) / K(k'); finite ground width wg uses the standard three-edge mapping
    k = (a/b) sqrt((1 - b^2/c^2)/(1 - a^2/c^2)), a = w/2, b = w/2 + s, c = b + wg."""
    from scipy.special import ellipk
    a, b = w / 2, w / 2 + s
    if wg is None:
        k = a / b
    else:
        c = b + wg
        k = (a / b) * math.sqrt((1 - b * b / (c * c)) / (1 - a * a / (c * c)))
    m = k * k
    return 2 * EPS0_FF_PER_UM * (eps_r + 1) * ellipk(m) / ellipk(1 - m)


def square_plate_reference():
    """capacitance of a thin square plate of side a in vacuum, C = gamma 4 pi eps0 a.
    gamma = 0.3667874 (refined, extrapolated boundary-element value tabulated by Mukhopadhyay & Majumdar,
    arXiv:physics/0604034; numerical path integration gives 0.36684). The often-quoted 0.3607 (Reitan & Higgins
    1951, coarse subdivision) is about 1.7 % low: our Galerkin solution is a variational lower bound and already
    exceeds it at 400 panels."""
    return 0.3667874


# ====================================================================================================================
# crossover (parallel-plate) capacitor: edge term from a 2D finite-difference solve of the layer stack
# ====================================================================================================================
_EDGE_CACHE = {}


def _graded_axis(segments):
    """concatenate graded 1D partitions: segments = [(a, b, h_a, h_b)], sizes grow geometrically from h_a to h_b"""
    pts = []
    for a, b, ha, hb in segments:
        L = b - a
        n = max(2, int(math.ceil(2 * L / (ha + hb))))
        r = (hb / ha) ** (1.0 / max(n - 1, 1))
        s = ha * r ** np.arange(n)
        s = s / s.sum() * L
        p = a + np.concatenate([[0.0], np.cumsum(s)])
        pts.append(p if not pts else p[1:])
    return np.concatenate(pts)


def _merge_axis(a, tol=1e-6):
    """sorted grid coordinates with near-duplicates (closer than tol um) merged"""
    a = np.sort(np.asarray(a, float))
    out = [a[0]]
    for v in a[1:]:
        if v - out[-1] > tol:
            out.append(v)
        else:
            out[-1] = v if abs(v) < abs(out[-1]) or v in (0.0,) else out[-1]
    return np.array(out)


def fv_solve_2d(xs, zs, eps_cells, fixed, val):
    """finite-volume Laplace solve div(eps grad V) = 0 on a tensor grid (nodes xs x zs), cell permittivities
    eps_cells (len(xs)-1, len(zs)-1), Dirichlet nodes `fixed` with values `val`, Neumann outer boundary.
    Returns V and the function charge(mask) = outward flux (units eps0 * V) of the node set `mask`."""
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    nx, nz = len(xs), len(zs)
    dx, dz = np.diff(xs), np.diff(zs)
    E = np.zeros((nx, nz)); Wc = np.zeros((nx, nz)); Nn = np.zeros((nx, nz)); S = np.zeros((nx, nz))
    # coefficient between (i, j) and (i+1, j): sum over the two cells beside the face of eps * half-height / dx
    epad = np.zeros((nx + 1, nz + 1))
    epad[1:nx, 1:nz] = eps_cells
    hz = np.zeros(nz + 1); hz[1:nz] = dz
    hx = np.zeros(nx + 1); hx[1:nx] = dx
    # face between node i and i+1 (i = 0..nx-2): cells (i, j-1) and (i, j) -> epad[i+1, j] and epad[i+1, j+1]
    ax = (epad[1:nx, 0:nz] * hz[0:nz][None, :] / 2 + epad[1:nx, 1:nz + 1] * hz[1:nz + 1][None, :] / 2) / dx[:, None]
    az = (epad[0:nx, 1:nz] * hx[0:nx][:, None] / 2 + epad[1:nx + 1, 1:nz] * hx[1:nx + 1][:, None] / 2) / dz[None, :]
    id_ = np.arange(nx * nz).reshape(nx, nz)
    rows, cols, data = [], [], []
    diag = np.zeros((nx, nz))
    # x-faces
    i0 = id_[:-1, :].ravel(); i1 = id_[1:, :].ravel(); a = ax.ravel()
    rows += [i0, i1]; cols += [i1, i0]; data += [-a, -a]
    np.add.at(diag, (slice(0, nx - 1), slice(None)), ax)
    np.add.at(diag, (slice(1, nx), slice(None)), ax)
    # z-faces
    j0 = id_[:, :-1].ravel(); j1 = id_[:, 1:].ravel(); b_ = az.ravel()
    rows += [j0, j1]; cols += [j1, j0]; data += [-b_, -b_]
    np.add.at(diag, (slice(None), slice(0, nz - 1)), az)
    np.add.at(diag, (slice(None), slice(1, nz)), az)
    rows = np.concatenate(rows); cols = np.concatenate(cols); data = np.concatenate(data)
    fx = fixed.ravel()
    keep = ~fx[rows]
    A = sp.csr_matrix((np.concatenate([data[keep], diag.ravel()[~fx], np.ones(fx.sum())]),
                       (np.concatenate([rows[keep], id_.ravel()[~fx], id_.ravel()[fx]]),
                        np.concatenate([cols[keep], id_.ravel()[~fx], id_.ravel()[fx]]))), shape=(nx * nz, nx * nz))
    rhs = np.where(fx, val.ravel(), 0.0)
    V = spla.spsolve(A.tocsc(), rhs).reshape(nx, nz)

    def charge(mask):
        Q = 0.0
        # flux through x-faces leaving the mask
        m0, m1 = mask[:-1, :], mask[1:, :]
        Q += np.sum(ax[m0 & ~m1] * (V[:-1, :][m0 & ~m1] - V[1:, :][m0 & ~m1]))
        Q += np.sum(ax[m1 & ~m0] * (V[1:, :][m1 & ~m0] - V[:-1, :][m1 & ~m0]))
        m0, m1 = mask[:, :-1], mask[:, 1:]
        Q += np.sum(az[m0 & ~m1] * (V[:, :-1][m0 & ~m1] - V[:, 1:][m0 & ~m1]))
        Q += np.sum(az[m1 & ~m0] * (V[:, 1:][m1 & ~m0] - V[:, :-1][m1 & ~m0]))
        return Q

    return V, charge


def crossover_edge_term(kind="top_edge", eps_d=None, d_nm=None, enclosure_um=0.2, box_um=0.5, h_um=0.001,
                        homogeneous=False):
    """excess capacitance per unit edge length (fF/um) of a crossover edge, relative to eps0 eps_d (overlap)/d.

    2D finite-volume solve of the layer stack across the edge: silicon (eps_Si) below z = 0, bottom plate (Al1,
    zero thickness) at z = 0, dielectric slab (eps_d, thickness d) on top of it that extends `enclosure_um` beyond
    the overlap edge, top plate (Al2, zero thickness) at z = d, vacuum above. The overlap occupies x < 0.
      'top_edge'   : the top plate ends at x = 0, the bottom plate continues to the box edge (x = +box)
      'bottom_edge': the bottom plate ends at x = 0, the top plate continues over it
    The box (|x|, |z| <= box_um, Neumann walls) keeps the fringe that closes between the two plates within box_um of
    the edge; the field beyond it is the interface BEM's job (it sees the stack as one sheet). homogeneous=True puts
    eps_d everywhere (validation against the Schwarz-Christoffel edge solution)."""
    eps_d = MATERIALS["diel"]["eps_r"] if eps_d is None else eps_d
    d = (MATERIALS["diel"]["d_nm"] if d_nm is None else d_nm) * 1e-3
    key = (kind, round(eps_d, 6), round(d, 6), enclosure_um, box_um, h_um, homogeneous)
    if key in _EDGE_CACHE:
        return _EDGE_CACHE[key]
    B, h, hc = box_um, h_um, 0.05
    xs = _graded_axis([(-B, -3 * d, hc, h), (-3 * d, 3 * d, h, h), (3 * d, B, h, hc)])
    zs = _graded_axis([(-B, -d, hc, h), (-d, 2 * d, h, h), (2 * d, B, h, hc)])
    zs = _merge_axis(np.concatenate([zs, [0.0, d]]))
    xs = _merge_axis(np.concatenate([xs, [0.0]]))
    XC = 0.5 * (xs[1:] + xs[:-1])[:, None] * np.ones((1, len(zs) - 1))
    ZC = np.ones((len(xs) - 1, 1)) * 0.5 * (zs[1:] + zs[:-1])[None, :]
    if homogeneous:
        eps = np.full(XC.shape, eps_d)
    else:
        eps = np.ones(XC.shape)
        eps[ZC < 0] = EPS_SI
        eps[(ZC > 0) & (ZC < d) & (XC < enclosure_um)] = eps_d
    Xn, Zn = np.meshgrid(xs, zs, indexing="ij")
    on_top = np.isclose(Zn, d, atol=1e-12)
    on_bot = np.isclose(Zn, 0.0, atol=1e-12)
    if kind == "top_edge":
        top = on_top & (Xn <= 1e-12)
        bot = on_bot
    else:
        top = on_top
        bot = on_bot & (Xn <= 1e-12)
    fixed = top | bot
    val = np.where(top, 1.0, 0.0)
    V, charge = fv_solve_2d(xs, zs, eps, fixed, val)
    Q = charge(top)
    excess = (Q - eps_d * B / d) * EPS0_FF_PER_UM
    _EDGE_CACHE[key] = excess
    return excess


def crossover_capacitance(w_x, w_y, edges=None, eps_d=None, d_nm=None):
    """parallel-plate crossover capacitance (fF) of an overlap rectangle w_x by w_y (um).
    edges: dict with the edge lengths of each kind {'top_edge': L1, 'bottom_edge': L2}; default: a crossing of two
    lines (top line along x crosses a bottom line along y): two top-plate edges of length w_x... see layout."""
    eps_d = MATERIALS["diel"]["eps_r"] if eps_d is None else eps_d
    d = (MATERIALS["diel"]["d_nm"] if d_nm is None else d_nm) * 1e-3
    C = EPS0_FF_PER_UM * eps_d * w_x * w_y / d
    if edges is None:
        edges = {"top_edge": 2 * w_y, "bottom_edge": 2 * w_x}
    for kind, length in edges.items():
        C += length * crossover_edge_term(kind, eps_d=eps_d, d_nm=d * 1e3)
    return C


# ====================================================================================================================
# inductance: square counting, partial inductances, 2D cross-section L'
# ====================================================================================================================
def squares_fd(mask, terminals_a, terminals_b):
    """number of squares of a sheet region on a uniform grid (boolean mask, True = metal) between two terminal
    masks, from the 2D Laplace equation (unit sheet conductance): squares = 1 / (total current at unit voltage)."""
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    nx, ny = mask.shape
    idx = -np.ones((nx, ny), int)
    pts = np.argwhere(mask)
    idx[mask] = np.arange(len(pts))
    n = len(pts)
    rows, cols, data = [], [], []
    b = np.zeros(n)
    fixedA, fixedB = terminals_a & mask, terminals_b & mask
    for p, (i, j) in enumerate(pts):
        if fixedA[i, j] or fixedB[i, j]:
            rows.append(p); cols.append(p); data.append(1.0)
            b[p] = 1.0 if fixedA[i, j] else 0.0
            continue
        diag = 0
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ii, jj = i + di, j + dj
            if 0 <= ii < nx and 0 <= jj < ny and mask[ii, jj]:
                rows.append(p); cols.append(idx[ii, jj]); data.append(-1.0)
                diag += 1
        rows.append(p); cols.append(p); data.append(diag)
    A = sp.csr_matrix((data, (rows, cols)), shape=(n, n))
    V = spla.spsolve(A, b)
    I = 0.0
    for p, (i, j) in enumerate(pts):
        if fixedA[i, j]:
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii, jj = i + di, j + dj
                if 0 <= ii < nx and 0 <= jj < ny and mask[ii, jj] and not fixedA[ii, jj]:
                    I += V[p] - V[idx[ii, jj]]
    return 1.0 / I


def filament_mutual_pH(l_um, d_um):
    """mutual partial inductance of two parallel aligned filaments of length l at distance d (Grover, exact)"""
    l, d = l_um, d_um
    return MU0 / (2 * math.pi) * (l * math.asinh(l / d) - math.sqrt(l * l + d * d) + d) * 1e-6 * 1e12


def bar_self_partial_pH(l_um, w_um, t_um=0.0):
    """self partial inductance (uniform current) of a straight bar l x w x t: exact average of the filament mutual
    over the cross-section (t = 0: thin tape). Uses the difference-variable form of the 4D integral."""
    from scipy import integrate
    l, w, t = l_um, w_um, t_um
    if t <= 0:
        f = lambda s: filament_mutual_pH(l, max(s, 1e-12)) * (w - s)
        val, _ = integrate.quad(f, 0.0, w, limit=200, points=[1e-9 * w, 1e-3 * w])
        return 2.0 / (w * w) * val
    f = lambda sz, sx: filament_mutual_pH(l, max(math.hypot(sx, sz), 1e-12)) * (w - sx) * (t - sz)
    val, _ = integrate.dblquad(f, 0.0, w, 0.0, t, epsabs=1e-10, epsrel=1e-9)
    return 4.0 / (w * w * t * t) * val


def grover_bar_pH(l_um, w_um, t_um=0.0):
    """Grover's formula for a straight rectangular bar: L = (mu0/2pi) l [ln(2l/(w+t)) + 1/2 + 0.2235 (w+t)/l]"""
    l, s = l_um, w_um + t_um
    return MU0 / (2 * math.pi) * l * (math.log(2 * l / s) + 0.5 + 0.2235 * s / l) * 1e-6 * 1e12


def inductance_2d(strips, conductors, reference):
    """per-unit-length geometric inductance matrix (pH/um) of the conductors (reference excluded) from the vacuum
    capacitance: L' = mu0 eps0 C_vac'^-1 (TEM, perfect conductors)."""
    C = capacitance_2d(strips, conductors, eps_eff=1.0)            # fF/um, full Maxwell matrix
    sig = [i for i, c in enumerate(conductors) if c != reference]
    Cs = C[np.ix_(sig, sig)] * 1e-15 / 1e-6                       # F/m
    L = MU0 * EPS0 * np.linalg.inv(Cs)                            # H/m
    return L * 1e12 * 1e-6, [conductors[i] for i in sig]          # pH/um


# ====================================================================================================================
# beam splitter: E_C,M and E_S (same definition as simulations/companions/c2_router.py)
# ====================================================================================================================
def qps_amplitude_GHz(EJ_GHz, EC_GHz):
    """phase-slip amplitude E_S = (charge dispersion of the transmon ground state) / 4, scqubits, ncut = 31"""
    import scqubits as scq
    scq.settings.T1_DEFAULT_WARNING = False
    t = scq.Transmon(EJ=EJ_GHz, EC=EC_GHz, ng=0.0, ncut=31, truncated_dim=2)
    e0 = t.eigenvals(evals_count=1)[0]
    t.ng = 0.5
    return abs(t.eigenvals(evals_count=1)[0] - e0) / 4


def EC_GHz_from_fF(C_fF):
    return E_CHARGE ** 2 / (2 * C_fF * 1e-15) / 6.62607015e-34 / 1e9


# ====================================================================================================================
# layout-level extraction: periodic context windows taken from the drawn geometry (hardware/layout.py primitives)
# ====================================================================================================================
SIZING_VERSION = 11
G_NOCAP = 0.12                   # below this envelope value no coupling capacitor is drawn (target < 0.025 fF)
SIZING_MESH = dict(h0=0.04, hmax=0.40, hmax_ground=1.2)
MESH = dict(h0=0.03, hmax=0.30, hmax_ground=1.0, growth=1.6, ymargin=12.0, delta_jj=0.10, delta_cap=0.30, K=20)


def _parity_net(net, n0, P):
    """map a node label of cell m to its class in a period of P cells starting at n0 ('A1_17' -> 'A1|1')"""
    if net is None or net == "G" or net.startswith("S_"):
        return net
    head, _, idx = net.rpartition("_")
    if not idx.isdigit():
        return net
    return f"{head}|{(int(idx) - n0) % P}"


def context_panels(block, n0, P=2, rows=None, mesh=None):
    """Panels of the periodic window [x_n0 - p/2, x_n0 + (P - 1/2) p) of the drawn block. Node labels are folded to
    their class in the period; junction and crossover overlaps are excluded from the interface model (their
    capacitance is added analytically: Cj for junctions, crossover_capacitance() for plates and crossings)."""
    m = dict(MESH)
    if mesh:
        m.update(mesh)
    p = block.p
    xa = block.xn(n0) - p / 2
    xb = xa + P * p
    ys = [block.yc[r] for r in (rows or ROWS_ALL)]
    y_lo, y_hi = min(ys) - m["ymargin"], max(ys) + m["ymargin"]
    rects = [r for r in block.geo.window(xa, xb) if r[4] > y_lo and r[2] < y_hi]
    excl = []                                              # (x1, y1, x2, y2, net_to_drop)
    for j in getattr(block.geo, "junctions", []):
        bx = j["box"]
        dj = m["delta_jj"]
        excl.append((bx[0] - dj, bx[1] - dj, bx[2] + dj, bx[3] + dj, j["b"], "AL2"))
    caps = []
    for c in getattr(block.geo, "caps", []):
        bx = c["box"]
        if bx[2] <= xa or bx[0] >= xb:
            continue
        dc = m["delta_cap"]
        layer = "AL1" if c["kind"] == "crossing" else "AL2"
        excl.append((bx[0] - dc, bx[1] - dc, bx[2] + dc, bx[3] + dc, c["drop"], layer))
        caps.append(c)
    from hardware.layout import L_NB, L_AL1, L_AL2, L_GRAL
    lname = {L_NB: "NB", L_AL1: "AL1", L_AL2: "AL2", L_GRAL: "GRAL"}
    # merge each net's footprint per layer is not needed: overlapping rectangles of the SAME net would double-count
    # charge, so rectangles are first cut into non-overlapping pieces per net (grid decomposition)
    pieces = {}
    for (ly, x1, y1, x2, y2, net, role) in rects:
        if ly not in lname:
            continue
        y1c, y2c = max(y1, y_lo), min(y2, y_hi)
        if y2c <= y1c:
            continue
        if role == "gral":                                 # only the unshielded part (the ends are under the pads)
            from hardware.layout import GRAL_OV
            full = [r for r in block.geo.rects if r[6] == "gral" and r[5] == net]
            if full:
                fx1, fx2 = full[0][1] + GRAL_OV, full[0][3] - GRAL_OV
                x1, x2 = max(x1, fx1), min(x2, fx2)
                if x2 - x1 < 1e-6:
                    continue
        if isinstance(net, tuple):
            key = ("lin",) + tuple(_parity_net(nn, n0, P) for nn in net)
        else:
            key = _parity_net(net, n0, P)
        pieces.setdefault(key, []).append((x1, y1c, x2, y2c, lname[ly], role))
    pan = Panels()
    for key, rl in pieces.items():
        for (x1, y1, x2, y2, ly, role) in _disjoint(rl):
            # exclusion zones
            sub = [(x1, y1, x2, y2)]
            for (ex1, ey1, ex2, ey2, enet, elay) in excl:
                if _parity_net(enet, n0, P) != key or ly != elay:
                    continue
                sub = [s for r in sub for s in _subtract(r, (ex1, ey1, ex2, ey2))]
            for (a1, b1, a2, b2) in sub:
                if a2 - a1 < 1e-4 or b2 - b1 < 1e-4:
                    continue
                big = (a2 - a1) > 3 and (b2 - b1) > 3
                hm = m["hmax_ground"] if big or role == "ground" else m["hmax"]
                if isinstance(key, tuple):
                    w = ("lin", "x", key[1], key[2], a1 if False else None, None)
                    # linear potential along the inductor between its unshielded ends (the drawn rect minus the
                    # contact overlaps): s from 0 at x_left + GRAL_OV to 1 at x_right - GRAL_OV of the full rect
                    full = [r for r in rects if r[6] == "gral" and isinstance(r[5], tuple)
                            and abs(r[2] - b1) < 1e-6 and r[1] <= a1 + 1e-9 and r[3] >= a2 - 1e-9]
                    if full:
                        fx1, fx2 = full[0][1], full[0][3]
                    else:
                        fx1, fx2 = a1, a2
                    from hardware.layout import GRAL_OV
                    w = ("lin", "x", key[1], key[2], fx1 + GRAL_OV, fx2 - GRAL_OV)
                    pan.add_rect(a1, a2, b1, b2, w, h0=m["h0"], hmax=m["hmax"], growth=m["growth"], tag=role)
                else:
                    pan.add_rect(a1, a2, b1, b2, {key: 1.0} if key is not None else {}, h0=m["h0"], hmax=hm,
                                 growth=m["growth"], tag=role)
    return pan, caps, (xa, xb, y_lo, y_hi)


ROWS_ALL = ["D_A", "A0", "A1", "B1", "B0", "D_B"]


def _subtract(r, e):
    """rectangle r minus rectangle e -> list of rectangles"""
    x1, y1, x2, y2 = r
    ex1, ey1, ex2, ey2 = e
    if ex2 <= x1 or ex1 >= x2 or ey2 <= y1 or ey1 >= y2:
        return [r]
    out = []
    if ey1 > y1:
        out.append((x1, y1, x2, ey1))
    if ey2 < y2:
        out.append((x1, ey2, x2, y2))
    yy1, yy2 = max(y1, ey1), min(y2, ey2)
    if ex1 > x1:
        out.append((x1, yy1, ex1, yy2))
    if ex2 < x2:
        out.append((ex2, yy1, x2, yy2))
    return out


def _disjoint(rl):
    """cut a list of possibly overlapping rectangles (same net) into disjoint rectangles, keeping layer/role of the
    first rectangle covering each piece (grid decomposition on the rectangles' own coordinates)"""
    if len(rl) == 1:
        return rl
    xs = sorted(set([r[0] for r in rl] + [r[2] for r in rl]))
    ys = sorted(set([r[1] for r in rl] + [r[3] for r in rl]))
    out = []
    for i in range(len(xs) - 1):
        cx = 0.5 * (xs[i] + xs[i + 1])
        col = None
        for j in range(len(ys) - 1):
            cy = 0.5 * (ys[j] + ys[j + 1])
            hit = None
            for r in rl:
                if r[0] <= cx <= r[2] and r[1] <= cy <= r[3]:
                    hit = r
                    break
            if hit is None:
                col = None
                continue
            if col is not None and col[4] == hit[4] and col[5] == hit[5] and abs(col[3] - ys[j]) < 1e-12 \
                    and abs(col[0] - xs[i]) < 1e-12:
                col = (col[0], col[1], col[2], ys[j + 1], col[4], col[5])
                out[-1] = col
            else:
                col = (xs[i], ys[j], xs[i + 1], ys[j + 1], hit[4], hit[5])
                out.append(col)
    # merge horizontally adjacent identical columns
    out.sort(key=lambda r: (r[1], r[3], r[0]))
    merged = []
    for r in out:
        if merged and abs(merged[-1][1] - r[1]) < 1e-12 and abs(merged[-1][3] - r[3]) < 1e-12 \
                and abs(merged[-1][2] - r[0]) < 1e-12 and merged[-1][4] == r[4] and merged[-1][5] == r[5]:
            merged[-1] = (merged[-1][0], r[1], r[2], r[3], r[4], r[5])
        else:
            merged.append(r)
    return merged


def analytic_caps(caps, n0, P):
    """{(net_a, net_b): C} of the crossover capacitors in the window (folded labels)"""
    out = {}
    for c in caps:
        a, b = _parity_net(c["a"], n0, P), _parity_net(c["b"], n0, P)
        C = crossover_capacitance(c["w_x"], c["w_y"], edges=c["edges"])
        out[(a, b)] = out.get((a, b), 0.0) + C
    return out


def context_capacitance(block, n0, P=2, rows=None, mesh=None, islands=True, kpi=True):
    """periodic extraction around cell n0. Returns per-row quantities per node (fF):
    C0 (k = 0 node capacitance: to everything except the same row), Cpi (k = pi), cross[s] (k = 0 coupling to row s,
    summed over the cells of s), toS, C_gnd (= C0 - sum over other rails); for islands: diag, C_m (to one neighbour),
    C_2t (two-terminal across a middle junction, everything else grounded)."""
    rows = rows or ROWS_ALL
    pan, caps, box = context_panels(block, n0, P, rows, mesh)
    nets = sorted({k for w in pan.w for k in w.keys() if k not in ("G", None)})
    nodes = [nd for nd in nets]
    ex, tags = [], []
    for r in rows:
        cls = [f"{r}|{i}" for i in range(P)]
        if not all(c in nodes for c in cls):
            continue
        ex.append({c: 1.0 for c in cls}); tags.append(("k0", r))
        if kpi:
            ex.append({c: (1.0 if i % 2 == 0 else -1.0) for i, c in enumerate(cls)}); tags.append(("kpi", r))
    isl = [nd for nd in nodes if nd.startswith("M")]
    if islands and isl:
        ex.append({isl[0]: 1.0}); tags.append(("isl", isl[0]))
    m = dict(MESH)
    if mesh:
        m.update(mesh)
    Q, info = periodic_charges(pan, nodes, ex, (1 + EPS_SI) / 2, P * block.p, m["K"])
    an = analytic_caps(caps, n0, P)
    idx = {nd: i for i, nd in enumerate(nodes)}
    Can = np.zeros((len(nodes), len(nodes)))
    for (a, b), C in an.items():
        if a in idx:
            Can[idx[a], idx[a]] += C
        if b in idx:
            Can[idx[b], idx[b]] += C
        if a in idx and b in idx:
            Can[idx[a], idx[b]] -= C
            Can[idx[b], idx[a]] -= C
    out = dict(panels=info["panels"], rows={}, islands={}, analytic={f"{a}~{b}": C for (a, b), C in an.items()})
    for e, (kind, r) in enumerate(tags):
        v = np.array([ex[e].get(nd, 0.0) for nd in nodes])
        q = Q[e] + Can @ v
        if kind == "k0":
            cls = [f"{r}|{i}" for i in range(P)]
            d = out["rows"].setdefault(r, {})
            d["C0"] = float(sum(q[idx[c]] for c in cls) / P)
            d["C0_class"] = [float(q[idx[c]]) for c in cls]
            d["cross"] = {}
            for s in rows:
                if s == r:
                    continue
                cs = [f"{s}|{i}" for i in range(P) if f"{s}|{i}" in idx]
                if cs:
                    d["cross"][s] = float(-sum(q[idx[c]] for c in cs) / P)
            d["toS"] = {nd: float(-q[idx[nd]] / P) for nd in nodes if nd.startswith("S_")}
            d["toM"] = float(-sum(q[idx[nd]] for nd in isl) / P) if isl else 0.0
            d["C_gnd"] = d["C0"] - sum(d["cross"].values())
        elif kind == "kpi":
            cls = [f"{r}|{i}" for i in range(P)]
            out["rows"].setdefault(r, {})["Cpi"] = float(sum(q[idx[c]] * (1 if i % 2 == 0 else -1)
                                                            for i, c in enumerate(cls)) / P)
        else:
            i0 = r
            other = [nd for nd in isl if nd != i0]
            diag = float(q[idx[i0]])
            Cm = float(-sum(q[idx[o]] for o in other) / 2) if P == 2 else float(-q[idx[other[0]]])
            out["islands"] = dict(diag=diag, C_m=Cm, C_2t=0.5 * (diag + Cm) if P == 2 else None,
                                  to_rails={r: float(-sum(q[idx[f"{r}|{i}"]] for i in range(P)
                                                         if f"{r}|{i}" in idx)) for r in rows})
    return out


# ====================================================================================================================
# 2D cross-section of a layout column: geometric (and kinetic) inductance per unit length, mesh inductances
# ====================================================================================================================
def column_xsec(block, n, extra=None, extra_slots=()):
    """strips (y_lo, y_hi, 0, conductor) of the cross-section through column n (perpendicular to the rows) and the
    mesh return conductor of every row. Ground pieces: the outermost two are the reference 'G', the inner ones
    'I0', 'I1', ... (inner ground strips, connected to G only at the row ends, so they carry the local returns)."""
    from hardware.layout import ROWS, PAIR_OF, PAIRS, QUBIT_ROWS, RUNG_DIR, ISL_H, W_GRAL
    iv = block.openings(n)
    ground = []
    y = 0.0
    for (lo, hi) in iv:
        if lo > y:
            ground.append((y, lo))
        y = max(y, hi)
    if y < block.H:
        ground.append((y, block.H))
    # slots (control-line / gate keep-outs) crossing the column centre
    xc = block.xn(n) + block.p / 2
    slots = sorted([(ko[1], ko[3]) for ko in getattr(block.geo, "keepout", []) if ko[0] <= xc <= ko[2]]
                   + list(extra_slots))
    strips, kin = [], {}
    names = []
    for i, (a, b) in enumerate(ground):
        outer = i in (0, len(ground) - 1)
        cuts = [(lo, hi) for (lo, hi) in slots if lo < b and hi > a]
        if cuts:
            y = a
            for (lo, hi) in cuts:
                if lo > y:
                    strips.append((y, lo, 0.0, "G"))
                y = max(y, hi)
            if y < b:
                strips.append((y, b, 0.0, "G"))
            names.append("G")
            continue
        nm = "G" if outer else f"I{i - 1}"
        strips.append((a, b, 0.0, nm))
        names.append(nm)
        if nm != "G":
            kin[nm] = nb_Lsq_pH() / (b - a)
    p = block.p
    ret = {}
    for row in ROWS:
        yc = block.yc[row]
        l_g = block.l_gral(row, n) if n < block.N - 1 else block.l_gral(row, n - 1)
        w_eq = (l_g * W_GRAL + (p - l_g) * block.pad_w(row, n)) / p
        strips.append((yc - w_eq / 2, yc + w_eq / 2, 0.0, row))
        k = block.ret[row][n]
        d = block.rdir(row, n)
        if k == "S":
            ret[row] = f"S_{PAIR_OF[row]}"
        elif k == "M":
            ret[row] = "M_" + ("A" if row in QUBIT_ROWS["A"] else "B")
        else:
            # the ground piece on the return side
            y_edge = yc + d * (block.pad_w(row, n) / 2 + 1e-3)
            cand = [(a, b, nm) for (a, b, z, nm) in strips if nm.startswith(("G", "I")) and (a > yc if d > 0 else b < yc)]
            cand.sort(key=lambda t: abs((t[0] if d > 0 else t[1]) - yc))
            ret[row] = cand[0][2]
    for pair in PAIRS:
        if block.g[n] > 0:
            ws = block.w_strip(pair, n)
            ys = block.strip_y(pair)
            strips.append((ys - ws / 2, ys + ws / 2, 0.0, f"S_{pair}"))
            Lsq = nb_Lsq_pH() if block.strip_mat(pair, n) == "NB" else al_Lsq_pH()
            from hardware.layout import L_NECK
            wn = block.neck_w(pair, n)
            l_n = L_NECK if wn < ws else 0.0
            kin[f"S_{pair}"] = Lsq * ((block.p - l_n) / ws + l_n / wn) / block.p     # per unit length, neck included
    for q in ("A", "B"):
        if any(ret.get(r) == f"M_{q}" for r in ROWS):
            ys = block.bs_y(q)
            strips.append((ys - ISL_H / 2, ys + ISL_H / 2, 0.0, f"M_{q}"))
    for ln in getattr(block.geo, "lines", []):
        pass
    for (ly_, x1, y1, x2, y2, net, role) in getattr(block, "_line_rects", []):
        if x1 <= xc <= x2 and net not in [s_[3] for s_ in strips]:
            strips.append((y1, y2, 0.0, net))
    for s in (extra or []):
        strips.append(s)
    conds = []
    for s in strips:
        if s[3] not in conds:
            conds.append(s[3])
    return strips, conds, ret, kin


def column_inductance(block, n, extra=None, lines=(), extra_slots=()):
    """per-cell mesh inductances (pH) of column n from the 2D cross-section: geometric loop self-inductance of each
    row's mesh (rail -> its return conductor), mutuals between meshes, kinetic inductance of the shared/own return
    per cell, and mutuals to control lines (conductor names in `lines`, current returning in the ground)."""
    strips, conds, ret, kin = column_xsec(block, n, extra, extra_slots)
    L, names = inductance_2d(strips, conds, "G")
    for nm, lk in kin.items():
        if nm in names:
            i = names.index(nm)
            L[i, i] += lk                       # kinetic inductance per unit length of the return conductors
    idx = {nm: i for i, nm in enumerate(names)}
    p = block.p
    E = {}
    for row, rc in ret.items():
        e = np.zeros(len(names))
        e[idx[row]] = 1.0
        if rc != "G":
            e[idx[rc]] -= 1.0
        E[row] = e
    out = dict(self={}, mutual={}, ret=ret, lines={})
    rows = list(E)
    for i, r in enumerate(rows):
        out["self"][r] = float(p * E[r] @ L @ E[r])
        for s in rows[i + 1:]:
            out["mutual"][f"{r}~{s}"] = float(p * E[r] @ L @ E[s])
        for ln in lines:
            if ln in idx:
                el = np.zeros(len(names)); el[idx[ln]] = 1.0
                out["lines"][f"{r}~{ln}"] = float(p * E[r] @ L @ el)
    return out


def rail_kinetic_pH(block, row, n):
    """kinetic inductance of mesh n of a row along the rail: granular Al (unshielded squares) + AL1 pad paths from
    the rung finger to the granular-Al contact midpoint on both nodes"""
    from hardware.layout import X_JJ, GRAL_OV, W_GRAL
    p = block.p
    l_g = block.l_gral(row, n)
    sq_g = l_g / W_GRAL
    xl0, xr0 = block.pad_extent(row, n)
    xl1, xr1 = block.pad_extent(row, n + 1)
    path0 = (xr0 - GRAL_OV / 2) - (block.xn(n) + X_JJ)
    path1 = (block.xn(n + 1) + X_JJ) - (xl1 + GRAL_OV / 2)
    sq_al = path0 / block.pad_w(row, n) + path1 / block.pad_w(row, n + 1)
    return sq_g * gral_Lsq_pH() + sq_al * al_Lsq_pH(), dict(squares_gral=sq_g, squares_al=sq_al)


# ====================================================================================================================
# sizing: solve the layout knobs from the architecture targets (periodic BEM + 2D cross-sections)
# ====================================================================================================================
def _secant(f, x0, x1, target, lo, hi, tol, maxit=6, log=None):
    """solve f(x) = target on [lo, hi] (monotonic f) by secant steps; returns (x, f(x), history)"""
    hist = []
    f0 = f(x0); hist.append((x0, f0))
    if abs(f0 - target) <= tol:
        return x0, f0, hist
    f1 = f(x1); hist.append((x1, f1))
    for _ in range(maxit):
        if abs(f1 - target) <= tol:
            break
        if f1 == f0:
            break
        x2 = x1 + (target - f1) * (x1 - x0) / (f1 - f0)
        x2 = min(max(x2, lo), hi)
        if abs(x2 - x1) < 1e-4:
            break
        x0, f0, x1 = x1, f1, x2
        f1 = f(x1); hist.append((x1, f1))
    best = min(hist, key=lambda h: abs(h[1] - target))
    return best[0], best[1], hist


def _bracket_solve(f, lo, hi, x0, target, tol, maxit=7):
    """monotonic increasing f on [lo, hi]: regula falsi (Illinois) from x0; returns (x, f(x)) closest to target.
    Robust to a jump (e.g. a structure that appears at a knob threshold)."""
    pts = []
    f0 = f(x0); pts.append((x0, f0))
    if abs(f0 - target) <= tol:
        return x0, f0
    # bracket
    if f0 < target:
        a, fa = x0, f0
        b = min(hi, x0 + max(0.3, 0.3 * (hi - lo)))
        fb = f(b); pts.append((b, fb))
        while fb < target and b < hi - 1e-9:
            a, fa = b, fb
            b = min(hi, b + 0.5 * (hi - lo))
            fb = f(b); pts.append((b, fb))
    else:
        b, fb = x0, f0
        a = max(lo, x0 - max(0.3, 0.3 * (hi - lo)))
        fa = f(a); pts.append((a, fa))
        while fa > target and a > lo + 1e-9:
            b, fb = a, fa
            a = max(lo, a - 0.5 * (hi - lo))
            fa = f(a); pts.append((a, fa))
    if not (fa <= target <= fb):
        best = min(pts, key=lambda q: abs(q[1] - target))
        return best
    side = 0
    for _ in range(maxit):
        if fb == fa:
            break
        c = (a * (fb - target) - b * (fa - target)) / (fb - fa)
        if not (min(a, b) < c < max(a, b)):
            c = 0.5 * (a + b)
        fc = f(c); pts.append((c, fc))
        if abs(fc - target) <= tol:
            break
        if fc < target:
            a, fa = c, fc
            if side == -1:
                fb = target + (fb - target) / 2
            side = -1
        else:
            b, fb = c, fc
            if side == +1:
                fa = target + (fa - target) / 2
            side = +1
    best = min(pts, key=lambda q: abs(q[1] - target))
    return best


def _cap_from_model(res_g, gs_sorted, gv, Cc):
    """coupling-capacitor knob for a taper cell from the solved samples: C_c(g) = C_inplane(g) + c_ov(w_t) * l_ov,
    with the in-plane part C_inplane = C_c - c_ov l_ov inferred from every sample (interpolated in g) and
    c_ov = eps0 eps_d w_t / d + 2 x (top-edge term) per unit overlap length (l_ov < 0: in-plane end gap, where
    the sample's own l_ov is interpolated instead). Avoids clamping where the plate width changes."""
    wt = 0.20 if gv > 0.5 else 0.10
    e_top = crossover_edge_term("top_edge")

    def c_ov(w):
        return diel_fF_per_um2() * w + 2 * e_top
    xs, cin = [], []
    for x in gs_sorted:
        c = res_g[x]["cap"]
        if not c:
            continue
        w_, l_ = c
        xs.append(x)
        cin.append(res_g[x]["C_c"] - (c_ov(w_) * l_ if l_ > 0 else 0.0))
    if not xs:
        return None
    lo = [x for x in xs if x <= gv]
    hi = [x for x in xs if x >= gv]
    br = ([max(lo)] if lo else []) + ([min(hi)] if hi else [])
    if any(res_g[x]["cap"][1] <= 0 for x in br):
        # end-gap regime on either side: interpolate the knob itself between the bracketing samples
        if len(br) == 2 and br[0] != br[1]:
            l0, l1 = res_g[br[0]]["cap"][1], res_g[br[1]]["cap"][1]
            return (0.10, float(np.interp(gv, br, [l0, l1])))
        return tuple(res_g[br[0]]["cap"])
    Cin = float(np.interp(gv, xs, cin))
    need = Cc * gv - Cin
    if need > 0:
        return (wt, max(need / c_ov(wt), 0.02))
    # in-plane regime: interpolate the end gap of the samples that used one
    gx = [x for x in xs if res_g[x]["cap"][1] <= 0]
    if gx:
        return (0.10, float(np.interp(gv, gx, [res_g[x]["cap"][1] for x in gx])))
    return (wt, 0.02)


def _block(arch, sz):
    from hardware import layout as LY
    B = LY.Block(arch, sz)
    B.draw()
    return B


def size_layout(arch, t=None, verbose=True):
    """solve every sizing knob of hardware/layout.py from the targets. Knobs (all um):
      trim[row|n]   overlap of the trim capacitor to ground (plain cells: return side; coupler/BS: free side)
      s_free[row|n] free-side ground gap (raised above S_FREE when a node is over target without trim)
      w_strip, strip_mat [pair|n]  coupler strip width and material (AL2 or NB) per mesh n -> L_s (k)
      cap[pair|n]   (w_t, l_ov) of the coupling capacitor -> C_c
      island[q|sec] island shunt overlap -> C_M
      l_gral[row|n] unshielded granular-Al length of mesh n -> L per cell
    Taper cells are interpolated in g between solved samples; dummy couplers use the gate coupler's solution
    mirrored (their geometry is the mirror image)."""
    import copy
    import time as _time
    from hardware import layout as LY
    t = t or LY.targets(arch)
    T0 = _time.time()
    sz = LY.default_sizing(arch)
    N = t["N"]
    p = t["pitch_um"]
    secs = {}
    for d in t["sections"]:
        secs.setdefault(d["name"], d)
    shunt, Cc, Ls, Lt = t["shunt_fF"], t["C_c_fF"], t["L_s_pH"], t["L_pH"]
    tolC = 0.002                                            # fF, sizing tolerance (well inside +-5 %)
    log = dict(steps=[])

    def say(*a):
        if verbose:
            print(f"[size {(_time.time() - T0):6.1f}s]", *a, flush=True)

    rows_all = LY.ROWS
    # ---------------------------------------------------------------- 1. plain cells: return-side trim
    n_pl = secs["accelerate"]["start"] + secs["accelerate"]["cells"] // 2

    def plain_C(l):
        s = copy.deepcopy(sz); s["defaults"]["trim"] = l
        r = context_capacitance(_block(arch, s), n_pl, rows=["A0", "A1"], kpi=False, islands=False)
        return r["rows"]["A0"]["C_gnd"]
    l_pl, c_pl, h = _secant(plain_C, 0.2, 0.5, shunt, -0.3, 0.95, tolC)
    sz["defaults"]["trim"] = l_pl
    say(f"plain trim {l_pl:.3f} um -> C_gnd {c_pl:.4f} fF (target {shunt:.4f})")
    log["plain"] = dict(trim=l_pl, C_gnd=c_pl, history=h)
    # ---------------------------------------------------------------- 2. beam splitter: free-side trim + island shunt
    bs = LY.bs_sections(arch)
    q0, sec0, ns0 = bs[0]
    n_bs = ns0[len(ns0) // 2]
    rows_q = list(LY.QUBIT_ROWS[q0])

    def bs_eval(l, ov):
        s = copy.deepcopy(sz)
        for (q, sec, ns) in bs:
            s["island"][f"{q}|{sec}"] = ov
            for r_ in LY.QUBIT_ROWS[q]:
                for n in ns:
                    s["trim"][f"{r_}|{n}"] = l
        r = context_capacitance(_block(arch, s), n_bs, rows=rows_q, kpi=False)
        return r
    r0 = bs_eval(0.0, 0.0)
    Cgnd0, C2t0, Cm0 = r0["rows"][rows_q[0]]["C_gnd"], r0["islands"]["C_2t"], r0["islands"]["C_m"]
    tgtM = t["shunt_M_fF"]
    ov = 0.0
    if C2t0 < tgtM:
        ov, _, _ = _secant(lambda o: bs_eval(0.0, o)["islands"]["C_2t"], 0.1, 0.3, tgtM, 0.0, 0.6, tolC)
    l_bs, c_bs, h = _secant(lambda l: bs_eval(l, ov)["rows"][rows_q[0]]["C_gnd"], 0.2, 0.5, shunt, -0.3, 0.95, tolC)
    rb = bs_eval(l_bs, ov)
    say(f"BS: island shunt overlap {ov:.3f} (natural C_2t {C2t0:.4f}, C_m {Cm0:.4f}; target {tgtM:.4f}), "
        f"trim {l_bs:.3f} -> C_gnd {rb['rows'][rows_q[0]]['C_gnd']:.4f}, C_2t {rb['islands']['C_2t']:.4f}")
    log["bs"] = dict(island_overlap=ov, natural=r0["islands"], final=rb["islands"], trim=l_bs,
                     C_gnd=rb["rows"][rows_q[0]]["C_gnd"])
    for (q, sec, ns) in bs:
        sz["island"][f"{q}|{sec}"] = ov
        for r_ in LY.QUBIT_ROWS[q]:
            for n in ns:
                sz["trim"][f"{r_}|{n}"] = l_bs
    # ---------------------------------------------------------------- 3. couplers: samples in g
    g_all = [ _g for _g in (LY._env(arch, n) for n in range(N))]
    ncpl = [n for n in range(N) if g_all[n] > 0]
    n_plateau = secs["coupler"]["start"] + secs["coupler"]["cells"] // 2
    samples = [1.0, 0.8, 0.6, 0.4, 0.25, 0.15, 0.08, 0.04]
    pair, (ra, rb_) = "G", LY.PAIRS["G"]
    plate, cross = (ra, rb_) if LY.CPL_ROLE[ra] == "plate" else (rb_, ra)
    res_g = {}
    W_MAX = 6.0
    for gs in samples:
        # representative cell: plateau for g = 1, else the taper_in cell with the closest g
        if gs >= 1.0:
            nc = n_plateau
        else:
            nc = min(secs["taper_in"]["start"] + j for j in range(secs["taper_in"]["cells"])
                     ) if False else min(range(secs["taper_in"]["start"], secs["taper_in"]["start"] + secs["taper_in"]["cells"]),
                                         key=lambda n: abs(g_all[n] - gs))
        gc = g_all[nc]
        cells = [nc - 2, nc - 1, nc, nc + 1, nc + 2, nc + 3]
        # (a) strip width / material from the 2D cross-section: mutual(plate, cross) = k L g
        def M_of(w, mat):
            s = copy.deepcopy(sz)
            for n in cells:
                s["w_strip"][f"{pair}|{n}"] = w
                s["strip_mat"] = dict(s.get("strip_mat", {}))
                s["strip_mat"][f"{pair}|{n}"] = mat
            B = LY.Block(arch, s)
            return column_inductance(B, nc)["mutual"][f"{ra}~{rb_}"]
        tgtL = Ls * gc
        mat = "AL2"
        if M_of(W_MAX, "AL2") > tgtL:
            mat = "NB"
        f_log = lambda lw: M_of(math.exp(lw), mat)
        lw, Mv, _ = _secant(f_log, math.log(0.25), math.log(0.5), tgtL, math.log(0.12), math.log(W_MAX), 0.01 * Ls)
        w = math.exp(lw)
        # (b) capacitor (overlap > 0, or end gap < 0) and the two nodes' C_gnd: simultaneous secant with a diagonal
        # Jacobian (each target depends mainly on its own knob). Node knob u: u >= 0 -> trim overlap u at the
        # standard free gap; u < 0 -> no trim, free gap S_FREE - u (wider gap = less capacitance), u >= S_FREE - S_MAX
        tgtC = Cc * gc
        tgtG = shunt - Cc * gc
        wt = 0.20 if gc > 0.5 else 0.10
        S_MAX = 3.5                                        # keeps >= 2.6 um of inner ground between two free sides
        u_lo = -0.30 - (S_MAX - LY.S_FREE)                  # u in [-0.3, 0.95]: trim knob; below: wider free gap

        def knobs(x):
            lov, up, uc = x
            tr = lambda u: None if float(u) < -0.30 else max(float(u), -0.30)   # no trim structure below -0.3
            sf = lambda u: LY.S_FREE + max(0.0, -0.30 - float(u))
            return dict(cap=True, wt=wt, lov=float(lov), tp=tr(up), tc=tr(uc), sp=sf(up), sc=sf(uc))

        def ev(x):
            kb_ = knobs(x)
            s = copy.deepcopy(sz)
            s.setdefault("strip_mat", {})
            for n in cells:
                s["w_strip"][f"{pair}|{n}"] = w
                s["strip_mat"][f"{pair}|{n}"] = mat
                s["cap"][f"{pair}|{n}"] = (wt, kb_["lov"])
                s["trim"][f"{plate}|{n}"] = kb_["tp"]; s["trim"][f"{cross}|{n}"] = kb_["tc"]
                s["s_free"][f"{plate}|{n}"] = kb_["sp"]; s["s_free"][f"{cross}|{n}"] = kb_["sc"]
            r = context_capacitance(_block(arch, s), nc, rows=[plate, cross], kpi=False, islands=False,
                                    mesh=SIZING_MESH)
            return np.array([r["rows"][plate]["cross"][cross], r["rows"][plate]["C_gnd"], r["rows"][cross]["C_gnd"]])
        nocap = gc < G_NOCAP or mat == "NB"                 # no capacitor: |C_c - target| stays below 5 % of C_c
        if nocap:
            _ev_cap = ev

            def ev(x):
                s = copy.deepcopy(sz)
                kb_ = knobs(x)
                s.setdefault("strip_mat", {})
                for n in cells:
                    s["w_strip"][f"{pair}|{n}"] = w
                    s["strip_mat"][f"{pair}|{n}"] = mat
                    s["cap"][f"{pair}|{n}"] = None
                    s["trim"][f"{plate}|{n}"] = kb_["tp"]; s["trim"][f"{cross}|{n}"] = kb_["tc"]
                    s["s_free"][f"{plate}|{n}"] = kb_["sp"]; s["s_free"][f"{cross}|{n}"] = kb_["sc"]
                r = context_capacitance(_block(arch, s), nc, rows=[plate, cross], kpi=False, islands=False,
                                        mesh=SIZING_MESH)
                return np.array([r["rows"][plate]["cross"][cross], r["rows"][plate]["C_gnd"], r["rows"][cross]["C_gnd"]])
        x = [0.40 * gc if gc > 0.5 else -0.8, -0.3, -0.3]
        cache = {}

        def evc(xx):
            key = tuple(round(v, 4) for v in xx)
            if key not in cache:
                cache[key] = ev(list(xx))
            return cache[key]
        bounds = [(-2.5, 2.0), (u_lo, 0.95), (u_lo, 0.95)]
        tgt = np.array([tgtC, tgtG, tgtG])
        for sweep in range(2):
            for i in ((1, 2) if nocap else (0, 1, 2)):
                def f1(v, i=i):
                    xx = list(x); xx[i] = v
                    return float(evc(xx)[i])
                x[i], _ = _bracket_solve(f1, bounds[i][0], bounds[i][1], x[i], float(tgt[i]),
                                         tolC if i == 0 else 2 * tolC)
        fx = evc(x)
        cv, gpv, gcv = fx
        kb = knobs(x)
        if nocap:
            kb["cap"] = False
        res_g[gs] = dict(n=nc, g=gc, w_strip=w, mat=mat, M_pH=Mv, M_target=tgtL,
                         cap=(kb["wt"], kb["lov"]) if kb["cap"] else None,
                         trim_plate=kb["tp"], trim_cross=kb["tc"], s_plate=kb["sp"], s_cross=kb["sc"],
                         C_c=float(cv), C_c_target=tgtC, C_gnd_plate=float(gpv), C_gnd_cross=float(gcv), C_gnd_target=tgtG,
                         iters=len(cache))
        say(f"g={gc:.3f} n={nc}: strip {mat} {w:.3f} um (M {Mv:.2f}/{tgtL:.2f} pH), cap {res_g[gs]['cap']}, "
            f"C_c {cv:.4f}/{tgtC:.4f}, C_gnd plate {gpv:.4f} cross {gcv:.4f} / {tgtG:.4f} "
            f"(trim p {kb['tp']} c {kb['tc']}, s_free p {kb['sp']:.2f} c {kb['sc']:.2f})")
    log["coupler_samples"] = res_g
    sz = interpolate_coupler(arch, sz, res_g, Cc, W_MAX)
    say("coupler knobs interpolated over", len(ncpl), "cells")
    try:                                                    # checkpoint (lets the line / granular-Al steps rerun)
        import json as _json
        import tempfile as _tf
        log["coupler_samples"] = {str(k): v for k, v in log.get("coupler_samples", {}).items()}
        sz["log"] = log
        _json.dump(sz, open(os.path.join(_tf.gettempdir(), "qbfx2_layout_sizing_partial.json"), "w"), default=float)
    except Exception:
        pass
    # ---------------------------------------------------------------- 4. launcher control lines (if any)
    sz, linfo = size_lines(arch, sz, t, say)
    log["lines"] = linfo
    # ---------------------------------------------------------------- 5. granular-Al lengths: L per cell
    sz = size_gral(arch, sz, t, say)
    sz["log"] = log
    sz["targets"] = {k: v for k, v in t.items() if k not in ("launcher", "sections")}
    sz["runtime_s"] = _time.time() - T0
    return sz


def interpolate_coupler(arch, sz, res_g, Cc, W_MAX=6.0):
    """interpolate the solved coupler samples (strip width/material, capacitor, node knobs) over every coupler
    cell in g and mirror them to the dummy pairs (their geometry is the gate coupler's mirror image)"""
    from hardware import layout as LY
    res_g = {float(k): v for k, v in res_g.items()}
    N = arch.n_cells
    g_all = [LY._env(arch, n) for n in range(N)]
    ncpl = [n for n in range(N) if g_all[n] > 0]
    ra, rb_ = LY.PAIRS["G"]
    plate, cross = (ra, rb_) if LY.CPL_ROLE[ra] == "plate" else (rb_, ra)
    # interpolate the coupler knobs over all coupler cells (in g), and mirror to the dummy pairs
    gs_sorted = sorted(res_g)
    def interp(key, gv):
        xs = np.array(gs_sorted); ys = np.array([res_g[x][key] for x in gs_sorted], float)
        return float(np.interp(gv, xs, ys))
    mirror = {"G": {plate: plate, cross: cross}}
    for pk, (a, b) in LY.PAIRS.items():
        if pk == "G":
            continue
        mirror[pk] = {(a if LY.CPL_ROLE[a] == "plate" else b): plate, (a if LY.CPL_ROLE[a] == "cross" else b): cross}
    sz.setdefault("strip_mat", {})
    for n in ncpl:
        gv = g_all[n]
        # nearest-sample material, interpolated width (in log) and knobs
        gbelow = [x for x in gs_sorted if x <= gv + 1e-12]
        mat = res_g[min(gs_sorted, key=lambda x: abs(x - gv))]["mat"]
        mats_al = [x for x in gs_sorted if res_g[x]["mat"] == "AL2"]
        if mat == "AL2":
            xs = np.array(mats_al); ys = np.log([res_g[x]["w_strip"] for x in mats_al])
        else:
            nb_ = [x for x in gs_sorted if res_g[x]["mat"] == "NB"]
            xs = np.array(nb_); ys = np.log([res_g[x]["w_strip"] for x in nb_])
        w = float(np.exp(np.interp(gv, xs, ys))) if len(xs) > 1 else float(np.exp(ys[0]))
        capd = _cap_from_model(res_g, gs_sorted, gv, Cc) if (gv >= G_NOCAP and mat == "AL2") else None
        if mat == "NB":
            gmin = min(gs_sorted)
            if gv < gmin:                                  # coupler ends: widen the Nb strip toward W_MAX (L_s -> 0)
                w = float(np.exp(np.interp(gv, [0.0, gmin], [math.log(W_MAX), math.log(res_g[gmin]["w_strip"])])))
        for pk, (a, b) in LY.PAIRS.items():
            sz["w_strip"][f"{pk}|{n}"] = w
            sz["strip_mat"][f"{pk}|{n}"] = mat
            sz["cap"][f"{pk}|{n}"] = capd
            for row in (a, b):
                role = mirror[pk][row]
                key_t = "trim_plate" if role == plate else "trim_cross"
                nearest = sorted(gs_sorted, key=lambda x: abs(x - gv))[:2]
                if all(res_g[x][key_t] is None for x in nearest):
                    sz["trim"][f"{row}|{n}"] = None
                else:
                    xs_ = [x for x in gs_sorted if res_g[x][key_t] is not None]
                    sz["trim"][f"{row}|{n}"] = float(np.interp(gv, xs_, [res_g[x][key_t] for x in xs_]))
                sz["s_free"][f"{row}|{n}"] = interp("s_plate" if role == plate else "s_cross", gv)
    return sz


def resize_lines_and_gral(arch, sz, verbose=True):
    """re-run the launcher-line and granular-Al steps on an existing sizing"""
    import time as _time
    from hardware import layout as LY
    T0 = _time.time()
    say = (lambda *a: print(f"[resize {(_time.time() - T0):6.1f}s]", *a, flush=True)) if verbose else (lambda *a: None)
    t = LY.targets(arch)
    sz, linfo = size_lines(arch, sz, t, say)
    sz.setdefault("log", {})["lines"] = linfo
    sz = size_gral(arch, sz, t, say)
    return sz


def size_gral(arch, sz, t, say=print):
    """unshielded granular-Al length per mesh so that the extracted mesh self-inductance (kinetic rail + kinetic
    return + 2D geometric loop) equals L. Columns are grouped by signature (return kinds, g, strip, line positions)
    and the 2D solve is done once per group."""
    from hardware import layout as LY
    N, Lt = t["N"], t["L_pH"]
    B = LY.Block(arch, sz)
    sig_cache = {}
    loopL = {}
    for n in range(N - 1):
        sig = (tuple(B.ret[r][n] for r in LY.ROWS), round(B.g[n], 3),
               tuple(round(B.w_strip(pk, n), 4) for pk in LY.PAIRS) if B.g[n] > 0 else (),
               tuple(round(B.s_free(r, n), 3) for r in LY.ROWS))
        if sig not in sig_cache:
            sig_cache[sig] = column_inductance(B, n)["self"]
        loopL[n] = sig_cache[sig]
    say(f"granular Al: {len(sig_cache)} distinct column cross-sections")
    for it in range(3):
        newl = {}
        for row in LY.ROWS:
            for n in range(N - 1):
                Lk, info = rail_kinetic_pH(B, row, n)
                Lg = Lk - info["squares_gral"] * gral_Lsq_pH()
                need = Lt - loopL[n][row] - Lg
                newl[f"{row}|{n}"] = need / gral_Lsq_pH() * LY.W_GRAL
        sz["l_gral"] = newl
        B = LY.Block(arch, sz)
    return sz


M_DRAW_MIN = 0.018                # pH: smallest control-line mutual the strip geometry reaches (gating threshold)


def size_lines(arch, sz, t=None, say=print):
    """control-line depths (line centre from the launch row's free-side ground edge, um) per rail cell. Both lines
    run in one slot of the inner strip on the free side (trap on the inner track, accelerator on the outer track,
    >= LINE_SEP apart); the 2D cross-section mutual M_n (line -> cell loop, all four launch rows have the same strip
    geometry) is tabulated vs (d_trap, d_acc) and inverted per cell so that each line meets its target wherever the
    target is >= M_DRAW_MIN; where a target is smaller the line is pushed as deep as the other line allows (its
    as-drawn M_n is reported). Each line is truncated (shorted) one cell after its last cell >= M_DRAW_MIN.
    Valid for slowly varying depth (2D cross-section per cell)."""
    import copy
    from hardware import layout as LY
    lt = LY.launcher_targets(arch)
    if not lt:
        return sz, {}
    s0 = copy.deepcopy(sz)
    s0["lines"] = {}
    s0["no_lines"] = True
    B = LY.Block(arch, s0)
    B.draw()
    WL, GL, SEP = LY.Block.W_LINE, LY.Block.G_LINE, LY.LINE_SEP
    dmin = B.depth_min()
    row0 = "A1" if "A1" in lt else next(iter(lt))
    c0 = 30 if not LY.mirrored(row0) else B.N - 32
    df0 = -LY.RUNG_DIR[row0]["G"]
    dmax = B.depth_max(row0, c0, df0)

    def mutuals(dt, da):
        y_near, _ = B.strip_bounds(row0, c0, df0)
        extra, ys_ = [], []
        for nm, dpt in (("TRL", dt), ("ACL", da)):
            if dpt is None:
                continue
            y = y_near + df0 * dpt
            extra.append((y - WL / 2, y + WL / 2, 0.0, nm))
            ys_.append(y)
        slot = (min(ys_) - WL / 2 - GL, max(ys_) + WL / 2 + GL)
        r = column_inductance(B, c0, extra=extra, lines=("TRL", "ACL"), extra_slots=[slot])
        return abs(r["lines"].get(f"{row0}~TRL", 0.0)), abs(r["lines"].get(f"{row0}~ACL", 0.0))
    dts = np.linspace(dmin, dmax - SEP, 9)
    das = np.linspace(dmin + SEP, dmax, 9)
    T2t = np.full((len(dts), len(das)), np.nan); T2a = np.full_like(T2t, np.nan)
    for i, dt in enumerate(dts):
        for j, da in enumerate(das):
            if da - dt < SEP - 1e-9:
                continue
            T2t[i, j], T2a[i, j] = mutuals(dt, da)
    das1 = np.linspace(dmin, dmax, 12)
    T1 = np.array([mutuals(None, da)[1] for da in das1])
    say(f"line tables ({row0}, strip depth {dmin:.2f}..{dmax:.2f} um): trap (inner) {np.nanmin(T2t):.4f}..{np.nanmax(T2t):.4f} pH, "
        f"acc (outer) {np.nanmin(T2a):.4f}..{np.nanmax(T2a):.4f} pH, single line {T1.min():.4f}..{T1.max():.4f} pH")
    from scipy.interpolate import RegularGridInterpolator
    for T in (T2t, T2a):
        for i in range(T.shape[0]):
            row_ = T[i]
            good = ~np.isnan(row_)
            if good.any():
                row_[~good] = np.interp(np.nonzero(~good)[0], np.nonzero(good)[0], row_[good])
    ft = RegularGridInterpolator((dts, das), T2t, bounds_error=False, fill_value=None)
    fa = RegularGridInterpolator((dts, das), T2a, bounds_error=False, fill_value=None)
    grid = np.array([(dt, da) for dt in np.linspace(dts[0], dts[-1], 60) for da in np.linspace(das[0], das[-1], 60)
                     if da >= dt + SEP - 1e-9])
    GT, GA = ft(grid), fa(grid)
    lines, info = {}, {}
    for row, tg in lt.items():
        Mt, Ma = np.asarray(tg["trap"]), np.asarray(tg["acc"])
        Bm = LY.Block(arch, dict(s0, no_lines=False))
        cells_t = set(c for c in Bm.line_cells(row, "trap"))
        cells_a = set(c for c in Bm.line_cells(row, "acc"))
        dep = {"trap": {}, "acc": {}}
        for n in sorted(cells_a | cells_t):
            if n < 0 or n > B.N - 2:
                continue
            tt, ta = Mt[n], Ma[n]
            if n in cells_t and n in cells_a:
                sc = np.zeros(len(grid))
                sc += np.where(tt >= M_DRAW_MIN, np.abs(GT - tt) / max(tt, 1e-9), 0.2 * GT / M_DRAW_MIN)
                sc += np.where(ta >= M_DRAW_MIN, np.abs(GA - ta) / max(ta, 1e-9), 0.2 * GA / M_DRAW_MIN)
                k = int(np.argmin(sc))
                dep["trap"][str(n)] = float(grid[k, 0]); dep["acc"][str(n)] = float(grid[k, 1])
            elif n in cells_a:
                da = float(das1[-1]) if ta <= T1[-1] else float(np.interp(-ta, -T1, das1))
                dep["acc"][str(n)] = da
            else:
                dt = float(das1[-1]) if tt <= T1[-1] else float(np.interp(-tt, -T1, das1))
                dep["trap"][str(n)] = dt
        lines[row] = dep
        info[row] = dict(trap_cells=len(dep["trap"]), acc_cells=len(dep["acc"]))
    sz["lines"] = lines
    sz["line_tables"] = dict(row=row0, dts=dts.tolist(), das=das.tolist(), T2t=T2t.tolist(), T2a=T2a.tolist(),
                             das1=das1.tolist(), T1=T1.tolist(), sep=SEP)
    return sz, info


def interpolate_coupler(arch, sz, res_g, Cc, W_MAX=6.0):
    """interpolate the solved coupler samples (strip width/material, capacitor, node knobs) over every coupler
    cell in g and mirror them to the dummy pairs (their geometry is the gate coupler's mirror image)"""
    from hardware import layout as LY
    res_g = {float(k): v for k, v in res_g.items()}
    N = arch.n_cells
    g_all = [LY._env(arch, n) for n in range(N)]
    ncpl = [n for n in range(N) if g_all[n] > 0]
    ra, rb_ = LY.PAIRS["G"]
    plate, cross = (ra, rb_) if LY.CPL_ROLE[ra] == "plate" else (rb_, ra)
    # interpolate the coupler knobs over all coupler cells (in g), and mirror to the dummy pairs
    gs_sorted = sorted(res_g)
    def interp(key, gv):
        xs = np.array(gs_sorted); ys = np.array([res_g[x][key] for x in gs_sorted], float)
        return float(np.interp(gv, xs, ys))
    mirror = {"G": {plate: plate, cross: cross}}
    for pk, (a, b) in LY.PAIRS.items():
        if pk == "G":
            continue
        mirror[pk] = {(a if LY.CPL_ROLE[a] == "plate" else b): plate, (a if LY.CPL_ROLE[a] == "cross" else b): cross}
    sz.setdefault("strip_mat", {})
    for n in ncpl:
        gv = g_all[n]
        # nearest-sample material, interpolated width (in log) and knobs
        gbelow = [x for x in gs_sorted if x <= gv + 1e-12]
        mat = res_g[min(gs_sorted, key=lambda x: abs(x - gv))]["mat"]
        mats_al = [x for x in gs_sorted if res_g[x]["mat"] == "AL2"]
        if mat == "AL2":
            xs = np.array(mats_al); ys = np.log([res_g[x]["w_strip"] for x in mats_al])
        else:
            nb_ = [x for x in gs_sorted if res_g[x]["mat"] == "NB"]
            xs = np.array(nb_); ys = np.log([res_g[x]["w_strip"] for x in nb_])
        w = float(np.exp(np.interp(gv, xs, ys))) if len(xs) > 1 else float(np.exp(ys[0]))
        capd = _cap_from_model(res_g, gs_sorted, gv, Cc) if (gv >= G_NOCAP and mat == "AL2") else None
        if mat == "NB":
            gmin = min(gs_sorted)
            if gv < gmin:                                  # coupler ends: widen the Nb strip toward W_MAX (L_s -> 0)
                w = float(np.exp(np.interp(gv, [0.0, gmin], [math.log(W_MAX), math.log(res_g[gmin]["w_strip"])])))
        for pk, (a, b) in LY.PAIRS.items():
            sz["w_strip"][f"{pk}|{n}"] = w
            sz["strip_mat"][f"{pk}|{n}"] = mat
            sz["cap"][f"{pk}|{n}"] = capd
            for row in (a, b):
                role = mirror[pk][row]
                key_t = "trim_plate" if role == plate else "trim_cross"
                nearest = sorted(gs_sorted, key=lambda x: abs(x - gv))[:2]
                if all(res_g[x][key_t] is None for x in nearest):
                    sz["trim"][f"{row}|{n}"] = None
                else:
                    xs_ = [x for x in gs_sorted if res_g[x][key_t] is not None]
                    sz["trim"][f"{row}|{n}"] = float(np.interp(gv, xs_, [res_g[x][key_t] for x in xs_]))
                sz["s_free"][f"{row}|{n}"] = interp("s_plate" if role == plate else "s_cross", gv)
    return sz


def resize_lines_and_gral(arch, sz, verbose=True):
    """re-run the launcher-line and granular-Al steps on an existing sizing"""
    import time as _time
    from hardware import layout as LY
    T0 = _time.time()
    say = (lambda *a: print(f"[resize {(_time.time() - T0):6.1f}s]", *a, flush=True)) if verbose else (lambda *a: None)
    t = LY.targets(arch)
    sz, linfo = size_lines(arch, sz, t, say)
    sz.setdefault("log", {})["lines"] = linfo
    sz = size_gral(arch, sz, t, say)
    return sz


def size_gral(arch, sz, t, say=print):
    """unshielded granular-Al length per mesh so that the extracted mesh self-inductance (kinetic rail + kinetic
    return + 2D geometric loop) equals L. Columns are grouped by signature (return kinds, g, strip, line positions)
    and the 2D solve is done once per group."""
    from hardware import layout as LY
    N, Lt = t["N"], t["L_pH"]
    B = LY.Block(arch, sz)
    sig_cache = {}
    loopL = {}
    for n in range(N - 1):
        sig = (tuple(B.ret[r][n] for r in LY.ROWS), round(B.g[n], 3),
               tuple(round(B.w_strip(pk, n), 4) for pk in LY.PAIRS) if B.g[n] > 0 else (),
               tuple(round(B.s_free(r, n), 3) for r in LY.ROWS))
        if sig not in sig_cache:
            sig_cache[sig] = column_inductance(B, n)["self"]
        loopL[n] = sig_cache[sig]
    say(f"granular Al: {len(sig_cache)} distinct column cross-sections")
    for it in range(3):
        newl = {}
        for row in LY.ROWS:
            for n in range(N - 1):
                Lk, info = rail_kinetic_pH(B, row, n)
                Lg = Lk - info["squares_gral"] * gral_Lsq_pH()
                need = Lt - loopL[n][row] - Lg
                newl[f"{row}|{n}"] = need / gral_Lsq_pH() * LY.W_GRAL
        sz["l_gral"] = newl
        B = LY.Block(arch, sz)
    return sz


def size_lines(arch, sz, t=None, say=print):
    """control-line depths (line centre from the row's free-side ground edge, um) per rail cell so that the 2D
    cross-section mutual M_n (line -> cell loop) equals the launcher targets. The trap line runs on the inner track
    (closer to the rail) while both lines exist, the accelerator line on the outer track; after the trap line ends
    the accelerator line may use the whole strip. Tables M(depth) are computed for one row of each strip type (A0:
    strip between a return side and a free side; A1: strip between two free sides) and reused for the mirrored B
    rows. Valid for slowly varying depth (2D cross-section per cell)."""
    import copy
    from hardware import layout as LY
    lt = LY.launcher_targets(arch)
    if not lt:
        return sz, {}
    s0 = copy.deepcopy(sz)
    s0["lines"] = {}
    s0["no_lines"] = True                                   # tables: only the probe lines in the cross-section
    B = LY.Block(arch, s0)
    B.draw()
    WL, GL = LY.Block.W_LINE, LY.Block.G_LINE
    dmin = B.depth_min()
    tables = {}
    rep = {"A0": "A0", "A1": "A1", "B0": "A0", "B1": "A1"}
    info = {}

    def mutuals(row, c, dt, da):
        df = -LY.RUNG_DIR[row]["G"]
        y_near, _ = B.strip_bounds(row, c, df)
        extra, slots = [], []
        for nm, dpt in (("TRL", dt), ("ACL", da)):
            if dpt is None:
                continue
            y = y_near + df * dpt
            extra.append((y - WL / 2, y + WL / 2, 0.0, nm))
            slots.append((y - WL / 2 - GL, y + WL / 2 + GL))
        r = column_inductance(B, c, extra=extra, lines=("TRL", "ACL"), extra_slots=slots)
        return abs(r["lines"].get(f"{row}~TRL", 0.0)), abs(r["lines"].get(f"{row}~ACL", 0.0)), r
    for row0 in ("A0", "A1"):
        if row0 not in lt:
            continue
        c = 30
        df = -LY.RUNG_DIR[row0]["G"]
        dmax = B.depth_max(row0, c, df)
        sep = min(2.6, dmax - dmin)                         # line-to-line separation (>= 1 um of ground)
        dts = np.linspace(dmin, dmax - sep, 6)
        das2 = np.linspace(dmin + sep, dmax, 7)
        T2t = np.full((len(dts), len(das2)), np.nan); T2a = np.full_like(T2t, np.nan)
        for i, dt in enumerate(dts):
            for j, da in enumerate(das2):
                if da - dt < sep - 1e-9:
                    continue
                mt, ma, _ = mutuals(row0, c, dt, da)
                T2t[i, j], T2a[i, j] = mt, ma
        das1 = np.linspace(dmin, dmax, 9)
        T1 = np.array([mutuals(row0, c, None, da)[1] for da in das1])
        tables[row0] = dict(dts=dts, das2=das2, T2t=T2t, T2a=T2a, das1=das1, T1=T1, sep=sep)
        say(f"line tables {row0}: trap M {np.nanmin(T2t):.4f}..{np.nanmax(T2t):.4f} pH, acc M (both) "
            f"{np.nanmin(T2a):.4f}..{np.nanmax(T2a):.4f}, acc alone {T1.min():.4f}..{T1.max():.4f} pH")
    from scipy.interpolate import RegularGridInterpolator
    lines = {}
    for row, tg in lt.items():
        tb = tables[rep[row]]
        m = LY.mirrored(row)
        Mt, Ma = np.asarray(tg["trap"]), np.asarray(tg["acc"])
        act_t = np.nonzero(Mt > 1e-6 * Mt.max())[0]
        act_a = np.nonzero(Ma > 1e-6 * Ma.max())[0]
        # cells each line passes through: from the launch end to one cell beyond its last active cell
        if not m:
            cells_t = set(range(0, act_t.max() + 2)) if len(act_t) else set()
            cells_a = set(range(0, act_a.max() + 2)) if len(act_a) else set()
        else:
            cells_t = set(range(act_t.min() - 1, B.N - 1)) if len(act_t) else set()
            cells_a = set(range(act_a.min() - 1, B.N - 1)) if len(act_a) else set()
        dep = {"trap": {}, "acc": {}}
        T2t = tb["T2t"].copy(); T2a = tb["T2a"].copy()
        for T in (T2t, T2a):
            for i in range(T.shape[0]):
                row_ = T[i]
                good = ~np.isnan(row_)
                if good.any():
                    row_[~good] = np.interp(np.nonzero(~good)[0], np.nonzero(good)[0], row_[good])
        ft = RegularGridInterpolator((tb["dts"], tb["das2"]), T2t, bounds_error=False, fill_value=None)
        fa = RegularGridInterpolator((tb["dts"], tb["das2"]), T2a, bounds_error=False, fill_value=None)
        grid = [(dt, da) for dt in np.linspace(tb["dts"][0], tb["dts"][-1], 45)
                for da in np.linspace(tb["das2"][0], tb["das2"][-1], 45) if da >= dt + tb["sep"] - 1e-9]
        G = np.array(grid)
        GT, GA = ft(G), fa(G)
        for n in sorted(cells_a | cells_t):
            if n < 0 or n > B.N - 2:
                continue
            tgt_t, tgt_a = Mt[n], Ma[n]
            if n in cells_t:
                sc = np.abs(GT - tgt_t) / max(Mt.max(), 1e-9) + np.abs(GA - tgt_a) / max(Ma.max(), 1e-9)
                k = int(np.argmin(sc))
                dep["trap"][str(n)] = float(G[k, 0]); dep["acc"][str(n)] = float(G[k, 1])
            else:
                # T1 decreases with depth; below the deepest value the line sits at the deepest allowed depth
                if tgt_a <= tb["T1"][-1]:
                    da = float(tb["das1"][-1])
                else:
                    da = float(np.interp(-tgt_a, -np.asarray(tb["T1"]), tb["das1"]))
                dep["acc"][str(n)] = da
        # the accelerator line keeps the outer track for 3 cells beyond the trap line's end (its short and slot)
        if dep["trap"]:
            tcs = sorted(int(c) for c in dep["trap"])
            edge_c = tcs[-1] if not m else tcs[0]
            dt_edge = dep["trap"][str(edge_c)]
            for j in range(1, 4):
                c = edge_c + j if not m else edge_c - j
                if str(c) in dep["acc"]:
                    dep["acc"][str(c)] = max(dep["acc"][str(c)], dt_edge + tb["sep"])
        lines[row] = dep
        info[row] = dict(trap_cells=len(dep["trap"]), acc_cells=len(dep["acc"]),
                         residual_at_deepest_pH=dict(trap=float(np.min(GT)), acc_alone=float(np.min(tb["T1"]))))
    sz["lines"] = lines
    sz["line_tables"] = {k: {kk: (vv.tolist() if hasattr(vv, "tolist") else vv) for kk, vv in v.items()}
                         for k, v in tables.items()}
    return sz, info


# ====================================================================================================================
# verification: DRC + extraction of the drawn block vs the architecture targets
# ====================================================================================================================
TOL = 0.05


def _pf(val, tgt, tol=TOL, absolute=None):
    """pass/fail dict; absolute: tolerance in absolute units (for targets near zero)"""
    if absolute is not None:
        dev = val - tgt
        return dict(extracted=float(val), target=float(tgt), deviation=float(dev), tolerance_abs=float(absolute),
                    passed=bool(abs(dev) <= absolute))
    dev = (val - tgt) / tgt if tgt else float("nan")
    return dict(extracted=float(val), target=float(tgt), rel_dev=float(dev), passed=bool(abs(dev) <= tol))


def _inter_qubit(r, s):
    """True if the two rows belong to different qubits (A side: D_A, A0, A1; B side: B1, B0, D_B) and neither is a
    dummy: a coupling between them acts on the two-qubit state"""
    a = {"A0", "A1"}; b = {"B1", "B0"}
    return (r in a and s in b) or (r in b and s in a)


def gds_consistency(block, gds_path):
    """area per layer of the GDS on disk vs the primitives used for the extraction (same geometry check)"""
    import gdstk
    from hardware.layout import build_block, L_NB, L_GRAL, L_AL1, L_AL2, L_DIEL
    import tempfile

    def areas(path):
        lib = gdstk.read_gds(path)
        top = lib.top_level()[0]
        a = {}
        for poly in top.polygons:
            a[(poly.layer, poly.datatype)] = a.get((poly.layer, poly.datatype), 0.0) + poly.area()
        return a
    area = areas(gds_path)
    lib2, cell2, _, _ = build_block(block.arch, block.sz)
    with tempfile.TemporaryDirectory() as td:            # same 1 nm rounding as the file on disk
        p2 = os.path.join(td, "rebuilt.gds")
        lib2.write_gds(p2)
        area2 = areas(p2)
    out = {}
    for ly in (L_NB, L_GRAL, L_AL1, L_AL2, L_DIEL):
        a1, a2 = area.get(ly, 0.0), area2.get(ly, 0.0)
        out[f"{ly[0]}/{ly[1]}"] = dict(gds_um2=a1, primitives_um2=a2, match=bool(abs(a1 - a2) <= 1e-6 * max(a1, 1.0) + 1e-3))
    return out


def verify(arch, gds_path: str, out_dir: str | None = None, sizing: dict | None = None, fast: bool = False,
           verbose: bool = True) -> dict:
    """Run the DRC and the EM extraction of the drawn row block and compare every extracted quantity with the
    architecture target (+-5 %). Writes <out_dir>/extraction.json and <out_dir>/drc_report.json (out_dir defaults
    to the directory of gds_path). Returns the result dict; result['passed'] is the milestone-D layout check."""
    import time as _time
    from hardware import layout as LY
    from hardware import drc as DRC
    T0 = _time.time()
    out_dir = out_dir or os.path.dirname(os.path.abspath(gds_path))
    say = (lambda *a: print(f"[verify {(_time.time() - T0):6.1f}s]", *a, flush=True)) if verbose else (lambda *a: None)
    t = LY.targets(arch)
    sz = sizing if sizing is not None else LY.get_sizing(arch)
    B = LY.Block(arch, sz)
    B.draw()
    p, N = B.p, B.N
    res = dict(targets={k: v for k, v in t.items() if k not in ("launcher",)}, materials=MATERIALS,
               method=__doc__.split("Electrostatics (3D)")[1].strip() if "Electrostatics (3D)" in __doc__ else "",
               mesh=MESH, tolerance=TOL)
    # ---------------------------------------------------------------- DRC
    drc = DRC.run(gds_path, arch, report_path=os.path.join(out_dir, "drc_report.json"))
    res["drc"] = dict(violations_total=drc["violations_total"], summary=drc["summary"], junctions=drc["junctions"])
    say("DRC", drc["violations_total"], "violations")
    res["gds_consistency"] = gds_consistency(B, gds_path)
    secs = {}
    for d in arch.sections():
        secs.setdefault(d["name"], d)
    Cj, CjM = t["Cj_fF"], t["CjM_fF"]
    Cn, Cc, shunt = t["C_node_fF"], t["C_c_fF"], t["shunt_fF"]
    Lt, Ls = t["L_pH"], t["L_s_pH"]
    checks = []

    def chk(name, d, where="", informational=False):
        d = dict(d); d["quantity"] = name; d["where"] = where; d["informational"] = informational
        checks.append(d)
        return d
    # ---------------------------------------------------------------- capacitance at sampled contexts
    samples = []
    plain_n = next(n for n in range(N) if all(B.ret[r][n] == "G" for r in LY.ROWS) and B.g[n] == 0
                   and 60 < n < N - 60 and all(not B.is_strap(r, n) for r in LY.ROWS)
                   and not any(str(n) in B.sz.get("lines", {}).get(r, {}).get("acc", {}) for r in B.sz.get("lines", {})))
    samples.append(("plain (all rows ground return)", plain_n))
    for (q, sec, ns) in B.bs:
        samples.append((f"beam splitter {q} {sec}", ns[len(ns) // 2]))
        if fast:
            break
    samples.append(("coupler plateau", secs["coupler"]["start"] + secs["coupler"]["cells"] // 2))
    tin = secs["taper_in"]
    taper_cells = [tin["start"] + j for j in (range(0, tin["cells"], 5) if not fast else (10, 20, 30))]
    for n in taper_cells:
        samples.append((f"taper_in g={B.g[n]:.3f}", n))
    tout = secs["taper_out"]
    for j in ((5, 20, 35) if not fast else (20,)):
        samples.append((f"taper_out g={B.g[tout['start'] + j]:.3f}", tout["start"] + j))
    lt_rows = list(B.sz.get("lines", {}).keys())
    if lt_rows and not fast:
        samples.append(("launcher: trap + accelerator lines (A rows)", 30))
        samples.append(("launcher: accelerator plateau (A rows)", 180))
    strap_rows = {}
    if not fast:
        for (q, row, n) in B.strap_cells():
            samples.append((f"strap over {row} (special cell, 4-cell period)", n))
            strap_rows[n] = row
    ctx = {}
    for name, n0 in samples:
        P_ = 4 if n0 in strap_rows else 2
        r = context_capacitance(B, n0, P=P_, rows=LY.ROWS, kpi=True, islands=True)
        if n0 in strap_rows:
            # only the strap node (class 0) is special; report it alone
            rr = r["rows"][strap_rows[n0]]
            ctx[name] = dict(n=n0, g=0.0, **r)
            c_strap = rr["C0_class"][0]
            chk("node capacitance (Cj + geometric, k = 0)", _pf(Cj + c_strap, Cn), f"{strap_rows[n0]} n={n0} [{name}]")
            say(f"context {name}: strap node C0 = {c_strap:.4f} fF (neighbours {rr['C0_class'][1:]})")
            continue
        ctx[name] = dict(n=n0, g=B.g[n0], **r)
        say(f"context {name} (n={n0}, {r['panels']} panels)")
        for row in LY.ROWS:
            d = r["rows"][row]
            k = B.ret[row][n0]
            g = B.g[n0]
            partner = None
            if k == "S":
                a, b = LY.PAIRS[LY.PAIR_OF[row]]
                partner = b if row == a else a
            Ctot = Cj + d["C0"]
            chk("node capacitance (Cj + geometric, k = 0)", _pf(Ctot, Cn), f"{row} n={n0} [{name}]")
            tgt_sh = shunt - Cc * g if partner else shunt
            Cpart = d["cross"].get(partner, 0.0) if partner else 0.0
            chk("node shunt to ground/return (geometric, excl. coupled partner) [informational: the requirement "
                "is the total node capacitance]", _pf(d["C0"] - Cpart, tgt_sh), f"{row} n={n0} [{name}]",
                informational=True)
            if partner and LY.CPL_ROLE[row] == "plate":
                if g >= 0.999:
                    chk("C_c (coupling capacitance, k = 0 sum over partner nodes)", _pf(Cpart, Cc * g), f"{row}-{partner} n={n0}")
                else:
                    chk("C_c taper profile (|C_c - g C_c| <= 5 % of C_c)", _pf(Cpart, Cc * g, absolute=TOL * Cc),
                        f"{row}-{partner} n={n0} g={g:.3f}")
            # strays: couplings the model does not have. Between the two qubits (an A row and a B row) they add a
            # conditional phase -> budget 5 % of C_c; within a qubit or to a dummy they only shift single-rail
            # dynamics -> budget 5 % of the node capacitance
            for s_, v in d["cross"].items():
                if s_ == partner:
                    continue
                if _inter_qubit(row, s_):
                    chk("stray capacitance between the qubits (A row - B row) (<= 5 % of C_c)",
                        _pf(v, 0.0, absolute=TOL * Cc), f"{row}-{s_} n={n0} [{name}]")
                else:
                    chk("stray capacitance within a qubit / to a dummy (<= 5 % of C_node)",
                        _pf(v, 0.0, absolute=TOL * Cn), f"{row}-{s_} n={n0} [{name}]")
            d["C_across_L"] = (d.get("Cpi", d["C0"]) - d["C0"]) / 4
        if r.get("islands"):
            isl = r["islands"]
            ctx[name]["E"] = {}
    # ---------------------------------------------------------------- beam splitter: C_M, E_C,M, E_S
    bs_ctx = [v for k, v in ctx.items() if k.startswith("beam splitter")]
    if bs_ctx:
        isl = bs_ctx[0]["islands"]
        C_M = CjM + isl["C_2t"]
        EC = EC_GHz_from_fF(C_M)
        ES = qps_amplitude_GHz(t["EJ_M_GHz"], EC)
        chk("C_M = Cj,M + island two-terminal capacitance", _pf(C_M, t["C_M_fF"]), "beam-splitter middle junction")
        chk("E_C,M", _pf(EC, t["EC_M_GHz"]), "beam-splitter middle junction")
        chk("E_S (scqubits charge dispersion / 4, as companion 2)", _pf(ES, t["E_S_GHz"]), "beam-splitter middle junction")
        # model gap: rail-junction capacitances seen by the middle junction (not in the single-junction estimate)
        C_a = isl["diag"] - isl["C_m"] + 2 * Cj
        C_sig = CjM + isl["C_m"] + C_a / 2
        res["beam_splitter"] = dict(C_m_direct_fF=isl["C_m"], C_island_diag_fF=isl["diag"], C_2t_fF=isl["C_2t"],
                                    C_M_fF=C_M, EC_M_GHz=EC, E_S_GHz=ES,
                                    with_rail_junction_capacitances=dict(
                                        C_sigma_fF=C_sig, EC_GHz=EC_GHz_from_fF(C_sig),
                                        E_S_GHz=qps_amplitude_GHz(t["EJ_M_GHz"], EC_GHz_from_fF(C_sig)),
                                        note="if the two rail junctions (2 x Cj) on each island are counted as "
                                             "grounded capacitance; the architecture's single-junction estimate omits "
                                             "them (vortex hopping beyond the single-junction estimate is unresolved)"),
                                    gates=getattr(B, "gates", []))
    # ---------------------------------------------------------------- inductance: every column (2D), grouped
    sig_cache = {}
    L_rows = {r: [] for r in LY.ROWS}
    Ls_list = []
    strayM = []
    bs_ladder = []
    for n in range(N - 1):
        sig = (tuple(B.ret[r][n] for r in LY.ROWS), round(B.g[n], 4),
               tuple(round(B.w_strip(pk, n), 4) for pk in LY.PAIRS) if B.g[n] > 0 else (),
               tuple(round(B.s_free(r, n), 3) for r in LY.ROWS),
               tuple(sorted((round(k[1], 2), round(k[3], 2)) for k in getattr(B.geo, "keepout", [])
                            if k[0] <= B.xn(n) + p / 2 <= k[2])))
        if sig not in sig_cache:
            sig_cache[sig] = column_inductance(B, n)
        ci = sig_cache[sig]
        for r in LY.ROWS:
            Lk, _ = rail_kinetic_pH(B, r, n)
            L_rows[r].append(Lk + ci["self"][r])
        if B.g[n] > 0:
            for pk, (a, b) in LY.PAIRS.items():
                M = ci["mutual"].get(f"{a}~{b}", ci["mutual"].get(f"{b}~{a}"))
                Lk, _ = rail_kinetic_pH(B, a, n)
                Ls_list.append((pk, n, B.g[n], M, M / (Lk + ci["self"][a])))
        for key, M in ci["mutual"].items():
            a, b = key.split("~")
            if B.g[n] > 0 and {a, b} == set(LY.PAIRS[LY.PAIR_OF.get(a, "G")]) and B.ret[a][n] == "S":
                continue
            if B.ret[a][n] == "M" and B.ret[b][n] == "M":
                bs_ladder.append((key, n, M))              # rows of one beam splitter share the middle rail: designed
                continue
            strayM.append((key, n, M))
    say(f"inductance: {len(sig_cache)} distinct cross-sections over {N - 1} columns")
    Lall = np.array([v for r in LY.ROWS for v in L_rows[r]])
    i_worst = int(np.argmax(np.abs(Lall - Lt)))
    chk("L per cell (mesh self-inductance: kinetic + geometric), worst cell of all rows", _pf(Lall[i_worst], Lt),
        f"{LY.ROWS[i_worst // (N - 1)]} n={i_worst % (N - 1)}")
    pl = [x for x in Ls_list if x[2] >= 0.999]
    if pl:
        Mp = np.array([x[3] for x in pl]); kp = np.array([x[4] for x in pl])
        iw = int(np.argmax(np.abs(Mp - Ls)))
        chk("L_s (shared-return mutual incl. direct magnetic coupling), plateau worst cell", _pf(Mp[iw], Ls),
            f"{pl[iw][0]} n={pl[iw][1]}")
        iw = int(np.argmax(np.abs(kp - t["k"])))
        chk("k = M / L_self, plateau worst cell", _pf(kp[iw], t["k"]), f"{pl[iw][0]} n={pl[iw][1]}")
    tp = [x for x in Ls_list if x[2] < 0.999]
    if tp:
        dev = np.array([x[3] - Ls * x[2] for x in tp])
        iw = int(np.argmax(np.abs(dev)))
        chk("L_s taper profile (|M - g L_s| <= 5 % of L_s), worst cell", _pf(tp[iw][3], Ls * tp[iw][2], absolute=TOL * Ls),
            f"{tp[iw][0]} n={tp[iw][1]} g={tp[iw][2]:.3f}")
    # stray mutuals: between the qubits budget 5 % of L_s, within a qubit / to a dummy 5 % of L
    if strayM:
        Ms = np.array([abs(x[2]) for x in strayM])
        inter = [x for x in strayM if _inter_qubit(*x[0].split("~"))]
        intra = [x for x in strayM if not _inter_qubit(*x[0].split("~"))]
        if inter:
            w = max(inter, key=lambda x: abs(x[2]))
            chk("stray mutual inductance between the qubits (<= 5 % of L_s), worst", _pf(w[2], 0.0, absolute=TOL * Ls),
                f"{w[0]} n={w[1]}")
        if intra:
            w = max(intra, key=lambda x: abs(x[2]))
            chk("stray mutual inductance within a qubit / to a dummy (<= 5 % of L_s), worst",
                _pf(w[2], 0.0, absolute=TOL * Ls), f"{w[0]} n={w[1]}")
    res["inductance"] = dict(L_cell_pH=dict(min=float(Lall.min()), max=float(Lall.max()), mean=float(Lall.mean())),
                             L_s_plateau_pH=[float(x) for x in (Mp.min(), Mp.max())] if pl else None,
                             k_plateau=[float(x) for x in (kp.min(), kp.max())] if pl else None,
                             taper=[dict(pair=x[0], n=x[1], g=x[2], M_pH=x[3], target_pH=Ls * x[2]) for x in tp[::4]],
                             stray_max_pH=float(Ms.max()) if strayM else 0.0,
                             bs_ladder_shared_middle_rail_mutual_pH=float(max(abs(x[2]) for x in bs_ladder)) if bs_ladder else 0.0,
                             junction_lead_inductance_pH=junction_lead_inductance(B))
    # ---------------------------------------------------------------- launcher control lines
    if lt_rows:
        res["launcher"] = launcher_check(B, chk, say)
    # ---------------------------------------------------------------- sensitivity, convergence
    res["sensitivity"] = sensitivity(B, ctx, res, t)
    if not fast:
        res["convergence"] = convergence_study(B, secs["coupler"]["start"] + secs["coupler"]["cells"] // 2, say)
        mx = mesh_extrapolation(res["convergence"])
        res["mesh_extrapolation"] = mx
        # informational: plateau node capacitance and C_c with the mesh-converged estimate
        pl = ctx.get("coupler plateau")
        if pl and all("C_inf" in mx.get(k, {}) for k in ("C0_A1", "C0_B1", "C_c")):
            for row in LY.ROWS:
                role = LY.CPL_ROLE[row]
                f = mx["C0_A1"]["rel"] if role == "plate" else mx["C0_B1"]["rel"]
                chk("node capacitance, mesh-extrapolated [informational]", _pf(Cj + pl["rows"][row]["C0"] * (1 + f), Cn),
                    f"{row} coupler plateau", informational=True)
            a, b = LY.PAIRS["G"]
            plate = a if LY.CPL_ROLE[a] == "plate" else b
            cross = b if plate == a else a
            chk("C_c, mesh-extrapolated [informational]",
                _pf(pl["rows"][plate]["cross"][cross] * (1 + mx["C_c"]["rel"]), Cc), "coupler plateau", informational=True)
    # ---------------------------------------------------------------- summary
    res["contexts"] = {k: dict(n=v["n"], g=v["g"], panels=v["panels"], rows=v["rows"], islands=v.get("islands", {}),
                               analytic=v.get("analytic", {})) for k, v in ctx.items()}
    res["checks"] = checks
    groups = {}
    for c in checks:
        q = c["quantity"]
        g = groups.setdefault(q, dict(n=0, failed=0, worst=None))
        g["n"] += 1
        if not c["passed"]:
            g["failed"] += 1
        dev = abs(c.get("rel_dev", c.get("deviation", 0.0) / max(c.get("tolerance_abs", 1.0), 1e-12) * TOL))
        if g["worst"] is None or dev > g["worst"][0]:
            g["worst"] = (dev, c)
    res["summary"] = {q: dict(checked=g["n"], failed=g["failed"], worst=g["worst"][1],
                              informational=g["worst"][1].get("informational", False)) for q, g in groups.items()}
    res["drc_clean"] = drc["violations_total"] == 0
    res["passed"] = bool(res["drc_clean"] and all(c["passed"] for c in checks if not c.get("informational"))
                         and all(v["match"] for v in res["gds_consistency"].values()))
    res["runtime_s"] = _time.time() - T0
    json.dump(res, open(os.path.join(out_dir, "extraction.json"), "w"), indent=1, default=float)
    say("done:", "PASS" if res["passed"] else "FAIL")
    return res


import json  # noqa: E402
import os  # noqa: E402


def junction_lead_inductance(B):
    """kinetic + geometric (Grover) inductance of the rung leads in series with a rail junction, for a plain, a
    coupler and a beam-splitter cell: AL1 finger from the pad edge to the junction, AL2 bar and return lead"""
    from hardware import layout as LY
    out = {}
    Lsq = al_Lsq_pH()
    LJ = (2.067833848e-15 / (2 * math.pi)) ** 2 / (B.arch.rail.EJ_GHz * 1e9 * 6.62607015e-34) * 1e12
    secs = {d["name"]: d for d in B.arch.sections()}
    for name, n in (("plain", secs["accelerate"]["start"] + 60), ("coupler", secs["coupler"]["start"] + 50),
                    ("beam_splitter", secs["BS_prep"]["start"] + 20)):
        row = "A1"
        rects = [r for r in B.geo.rects if r[5] == B.node(row, n) and r[6] == "jj_finger"]
        bar = [r for r in B.geo.rects if r[6] == "jj_bar" and abs(r[1] - (B.xn(n) + LY.X_JJ - LY.JJ_A / 2 - LY.E1)) < 1e-6
               and abs((r[2] + r[4]) / 2 - [j for j in B.geo.junctions if j.get("row") == row and j["n"] == n][0]["y"]) < 1e-3]
        lead = [r for r in B.geo.rects if r[6] == "ret_lead" and abs((r[1] + r[3]) / 2 - (B.xn(n) + LY.X_RET)) < 1e-6
                and r[2] < B.yc[row] + 6 and r[4] > B.yc[row] - 6]
        Lk = 0.0; Lg = 0.0
        for (ly, x1, y1, x2, y2, *_ ) in rects + lead:
            l, w = (y2 - y1), (x2 - x1)
            Lk += Lsq * l / w
            Lg += grover_bar_pH(max(l, 2 * w), w, 0.03) if l > w else 0.0
        for (ly, x1, y1, x2, y2, *_ ) in bar:
            Lk += Lsq * (x2 - x1) / (y2 - y1) / 2
        out[name] = dict(kinetic_pH=Lk, geometric_pH=Lg, total_pH=Lk + Lg, fraction_of_LJ=(Lk + Lg) / LJ,
                         note="in series with the junction: effective E_J lowered by this fraction (not in the model)")
    return out


def launcher_check(B, chk, say, stride=2):
    """M_n (2D cross-section per cell) of the drawn control lines vs the targets; tolerance 5 % of each line's peak
    target (absolute; the profile tails are ~1e-5 pH). Also the cross-talk to the qubit's other rail and the dummy."""
    from hardware import layout as LY
    out = {}
    for row, tg in B.lt.items():
        m = LY.mirrored(row)
        Mt, Ma = np.asarray(tg["trap"]), np.asarray(tg["acc"])
        dep = B.sz.get("lines", {}).get(row, {})
        cells = sorted(set(int(c) for c in dep.get("trap", {})) | set(int(c) for c in dep.get("acc", {})))
        cells = [c for i, c in enumerate(cells) if (str(c) in dep.get("trap", {})) or i % stride == 0]
        rows_rec = []
        for c in cells:
            ci = column_inductance(B, c, lines=(f"TR_{row}", f"AC_{row}"))
            mt = abs(ci["lines"].get(f"{row}~TR_{row}", 0.0))
            ma = abs(ci["lines"].get(f"{row}~AC_{row}", 0.0))
            xt = {r: ci["lines"].get(f"{r}~AC_{row}", 0.0) for r in LY.ROWS if r != row}
            rows_rec.append((c, mt, Mt[c], ma, Ma[c], xt))
        dt = np.array([r[1] - r[2] for r in rows_rec]); da = np.array([r[3] - r[4] for r in rows_rec])
        it, ia = int(np.argmax(np.abs(dt))), int(np.argmax(np.abs(da)))
        chk(f"launcher trap-line M_n (|M - M_target| <= 5 % of peak)", _pf(rows_rec[it][1], rows_rec[it][2], absolute=TOL * Mt.max()),
            f"{row} cell n={rows_rec[it][0]}")
        chk(f"launcher accelerator-line M_n (|M - M_target| <= 5 % of peak)",
            _pf(rows_rec[ia][3], rows_rec[ia][4], absolute=TOL * Ma.max()), f"{row} cell n={rows_rec[ia][0]}")
        q_other = [r for r in ("A0", "A1", "B1", "B0") if r != row and r[0] == row[0]]
        xt_max = max(abs(r[5].get(q_other[0], 0.0)) for r in rows_rec) if q_other else 0.0
        out[row] = dict(cells_checked=len(rows_rec), trap_peak_target_pH=float(Mt.max()), acc_peak_target_pH=float(Ma.max()),
                        trap_max_dev_pH=float(dt[it]), acc_max_dev_pH=float(da[ia]),
                        crosstalk_to_other_rail_max_pH=float(xt_max),
                        profile=[dict(n=r[0], M_trap=r[1], target_trap=r[2], M_acc=r[3], target_acc=r[4]) for r in rows_rec[::3]])
        say(f"launcher {row}: trap dev {dt[it]:+.4f} pH (peak {Mt.max():.4f}), acc dev {da[ia]:+.4f} pH "
            f"(peak {Ma.max():.4f}), cross-talk to {q_other} {xt_max:.4f} pH")
    return out


def sensitivity(B, ctx, res, t):
    """material uncertainties (+-10 %) that the layout cannot remove; they need in-situ calibration (test
    structures on the same wafer, then a re-size of the granular-Al length / plate overlaps)"""
    out = {}
    Lt = t["L_pH"]
    # granular Al sheet inductance
    from hardware import layout as LY
    secs = {d["name"]: d for d in B.arch.sections()}
    n_pl = secs["accelerate"]["start"] + 60
    n_cp = secs["coupler"]["start"] + 50
    Lk, info = rail_kinetic_pH(B, "A1", n_pl)
    Lg = info["squares_gral"] * gral_Lsq_pH()
    ci_pl = column_inductance(B, n_pl)
    ci_cp = column_inductance(B, n_cp)
    Lk_c, info_c = rail_kinetic_pH(B, "A1", n_cp)
    L0 = Lk + ci_pl["self"]["A1"]
    Lc0 = Lk_c + ci_cp["self"]["A1"]
    M0 = ci_cp["mutual"].get("A1~B1")
    for f in (0.9, 1.1):
        L1 = L0 + (f - 1) * Lg
        Lc1 = Lc0 + (f - 1) * info_c["squares_gral"] * gral_Lsq_pH()
        out[f"grAl L_sq x{f}"] = dict(L_cell_rel=(L1 - Lt) / Lt, k_rel=(M0 / Lc1) / (M0 / Lc0) - 1,
                                      passed_5pct=bool(abs((L1 - Lt) / Lt) <= TOL))
    # thin-Al R_sq: strip kinetic inductance (and the AL1 pad paths)
    ws = B.w_strip("G", n_cp)
    Lkin_strip = al_Lsq_pH() * B.p / ws
    for f in (0.9, 1.1):
        M1 = M0 + (f - 1) * Lkin_strip
        Lc1 = Lc0 + (f - 1) * (Lkin_strip + info_c["squares_al"] * al_Lsq_pH())
        out[f"thin-Al R_sq x{f}"] = dict(L_s_rel=M1 / M0 - 1, k_rel=(M1 / Lc1) / (M0 / Lc0) - 1,
                                         passed_5pct=bool(abs(M1 / M0 - 1) <= TOL))
    # dielectric thickness: recompute the analytic crossover capacitors of the plateau and plain contexts
    d0 = MATERIALS["diel"]["d_nm"]
    for f in (0.9, 1.1):
        rec = {}
        for cname, v in ctx.items():
            if not (cname.startswith("coupler plateau") or cname.startswith("plain") or cname.startswith("beam")):
                continue
            n0 = v["n"]
            dC = {}
            _, caps, _ = context_panels(B, n0, 2, LY.ROWS)
            for c in caps:
                a, b = _parity_net(c["a"], n0, 2), _parity_net(c["b"], n0, 2)
                C0_ = crossover_capacitance(c["w_x"], c["w_y"], edges=c["edges"])
                C1_ = crossover_capacitance(c["w_x"], c["w_y"], edges=c["edges"], d_nm=d0 * f)
                dC[(a, b, c["kind"])] = dC.get((a, b, c["kind"]), 0.0) + (C1_ - C0_)
            # per node (average over the two classes): change of C0 and of C_c
            for row in LY.ROWS:
                dnode = sum(v_ for (a, b, k), v_ in dC.items() if a.startswith(row + "|") or b.startswith(row + "|")) / 2
                dcc = sum(v_ for (a, b, k), v_ in dC.items() if k == "coupler" and (a.startswith(row + "|") or b.startswith(row + "|"))) / 2
                d = v["rows"][row]
                rec[f"{cname}|{row}"] = dict(node_C_rel=dnode / (t["Cj_fF"] + d["C0"]),
                                             C_c_rel=(dcc / d["cross"][next(iter([s for s in d["cross"] if abs(d["cross"][s]) > 0.05]), row)]
                                                      if dcc and any(abs(x) > 0.05 for x in d["cross"].values()) else 0.0))
        worst_node = max(abs(x["node_C_rel"]) for x in rec.values())
        worst_cc = max(abs(x["C_c_rel"]) for x in rec.values())
        out[f"dielectric d x{f}"] = dict(node_C_rel_max=worst_node, C_c_rel_max=worst_cc,
                                         passed_5pct=bool(worst_node <= TOL and worst_cc <= TOL))
    out["note"] = ("material parameters (grAl sheet inductance, thin-Al R_sq and T_c, SiNx thickness and eps_r) are "
                   "process inputs: they must be calibrated in situ on test structures of the same wafer, after which "
                   "the granular-Al length, strip width and plate overlaps are re-sized by regenerating the layout "
                   "with the measured values (extract.MATERIALS)")
    return out


def mesh_extrapolation(conv):
    """Richardson-type estimate of the mesh-converged values from the three mesh levels of convergence_study
    (scale 1.5, 1.0, 0.6): fit C(h) = C_inf - a h^p. Returns {quantity: dict(p, C_base, C_inf, rel)}"""
    from scipy.optimize import brentq
    out = {}
    c15 = conv.get("mesh coarser (h0 x1.5, hmax x1.5)"); c10 = conv.get("base"); c06 = conv.get("mesh finer (h0 x0.6, hmax x0.6)")
    if not (c15 and c10 and c06):
        return out
    for k in ("C0_A1", "C0_B1", "C_c"):
        d1, d2 = c10[k] - c15[k], c06[k] - c10[k]
        if d1 <= 0 or d2 <= 0:
            out[k] = dict(note="non-monotone", C_base=c10[k])
            continue
        f = lambda p: (1.5 ** p - 1) / (1 - 0.6 ** p) - d1 / d2
        try:
            p = brentq(f, 0.05, 4.0)
        except ValueError:
            p = 1.0
        a = d2 / (1 - 0.6 ** p)
        out[k] = dict(p=p, C_base=c10[k], C_inf=c10[k] + a, rel=a / c10[k])
    return out


def convergence_study(B, n0, say):
    """plateau context: dependence of the extracted node capacitance and C_c on the numerical parameters"""
    from hardware import layout as LY
    rows = ["A0", "A1", "B1", "B0"]
    base = context_capacitance(B, n0, rows=rows, kpi=False, islands=False)
    def q(r):
        return dict(C0_A1=r["rows"]["A1"]["C0"], C0_B1=r["rows"]["B1"]["C0"], C_c=r["rows"]["A1"]["cross"]["B1"],
                    panels=r["panels"])
    out = dict(base=q(base))
    variants = [("mesh finer (h0 x0.6, hmax x0.6)", dict(h0=0.018, hmax=0.18, hmax_ground=0.6)),
                ("mesh coarser (h0 x1.5, hmax x1.5)", dict(h0=0.045, hmax=0.45, hmax_ground=1.5)),
                ("images K = 10", dict(K=10)), ("images K = 40", dict(K=40)),
                ("window margin 8 um", dict(ymargin=8.0)), ("window margin 20 um", dict(ymargin=20.0)),
                ("junction exclusion 0.05 um", dict(delta_jj=0.05)), ("junction exclusion 0.20 um", dict(delta_jj=0.20)),
                ("crossover exclusion 0.20 um", dict(delta_cap=0.20)), ("crossover exclusion 0.45 um", dict(delta_cap=0.45))]
    for name, mv in variants:
        r = context_capacitance(B, n0, rows=rows, mesh=mv, kpi=False, islands=False)
        out[name] = q(r)
        say(f"convergence: {name}: {out[name]}")
    r = context_capacitance(B, n0, P=4, rows=rows, kpi=False, islands=False)
    out["period 4 cells"] = q(r)
    # crossover edge-term box
    e0 = {k: crossover_edge_term(k) for k in ("top_edge", "bottom_edge")}
    e1 = {k: crossover_edge_term(k, box_um=0.8) for k in ("top_edge", "bottom_edge")}
    out["crossover edge term fF/um (box 0.5 / 0.8 um)"] = dict(box05=e0, box08=e1)
    b = out["base"]
    out["max_rel_change"] = {k: max(abs(v[k] / b[k] - 1) for kk, v in out.items()
                                    if isinstance(v, dict) and k in v and kk not in ("base",))
                             for k in ("C0_A1", "C0_B1", "C_c")}
    return out
