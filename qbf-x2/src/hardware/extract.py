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


def crossover_edge_term(kind="top_edge", eps_d=None, d_nm=None, enclosure_um=0.2, box_um=0.5, h_um=0.0025,
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
    zs = np.unique(np.concatenate([zs, [0.0, d]]))
    xs = np.unique(np.concatenate([xs, [0.0]]))
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
