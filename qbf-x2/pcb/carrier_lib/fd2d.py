"""2D quasi-static finite-difference field solver for the carrier's GCPW cross-sections (cross-check of the closed-form
impedance formulas; the single-line pass/fail check uses rf_calc.gcpw_z0 as required).

Laplace equation div(eps grad V) = 0 on a graded grid over HALF of a cross-section that is symmetric about x = 0:
In1 ground plane at y = 0, grounded lid far above, Neumann at the far side. Conductors are Dirichlet nodes.
The capacitance per unit length follows from the stored energy, W = sum_edges eps_edge * dV^2 (V = 1):

* solve()          single GCPW line centred on x = 0 (Neumann at the symmetry plane): C = 2 eps0 W (both halves)
* solve_coupled()  edge-coupled GCPW pair (two signal strips w, inner gap s, outer ground gap g), one strip per half:
                   odd mode  = electric wall (V = 0) at x = 0, even mode = magnetic wall (Neumann) at x = 0;
                   per-line mode capacitance C_m = eps0 W (half domain = one line of the pair).
Each case is solved once with the dielectrics (C) and once in vacuum (Ca): Z = 1 / (c sqrt(C Ca)), eeff = C / Ca.
Coupled pair: Z_diff = 2 Z_odd, Z_cm = Z_even / 2, coupling coefficient k = (Z_even - Z_odd) / (Z_even + Z_odd).

closed_form_coupled() is the matching zero-thickness conformal-mapping estimate (partial capacitances, magnetic walls at
the slot interfaces): air half space mapped with w = z^2 (quarter plane -> half plane), the conductor-backed substrate
slab mapped with t = cosh(pi z / h) (half strip -> half plane); each half plane is a two-conductor problem on the real
axis whose capacitance is eps K(k)/K(k') with k from the cross ratio of the four conductor edges. In the limit s -> 0
the even mode reduces exactly to rf_calc.gcpw_z0 of a 2w strip (Ghione-Naldi CB-CPW).
"""
import math

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.special import ellipk

EPS0 = 8.8541878128e-12
C0 = 299792458.0
ETA0 = 376.730313668


def _grid_y(h, t, mask_t, dx, top, growth):
    """node rows: uniform up to 0.15 mm above the copper, then geometric growth to `top` (grounded lid)"""
    jh = int(round(h / dx))                           # dielectric top (node row)
    jt = jh + max(1, int(round(t / dx)))              # copper top
    jm = jt + int(round(mask_t / dx))                 # mask top above the copper
    y = list(np.arange(0, jt + 1) * dx)
    j_uni = jt + int(round(0.15 / dx))
    while len(y) <= j_uni:
        y.append(y[-1] + dx)
    step = dx
    while y[-1] < top:
        step *= growth
        y.append(y[-1] + step)
    return np.array(y), jh, jt, jm


def _energy(e, fixed, val, dx, hy):
    """solve div(e grad V) = 0 with Dirichlet nodes `fixed`/`val` (Neumann elsewhere); return sum eps dV^2"""
    nx, ny = e.shape
    # x-edge (i,j)-(i+1,j): cells (i,j-1) [height hy[j-1]] and (i,j) [height hy[j]], weighted by height
    num = np.zeros((nx, ny + 1))
    num[:, 1:] += e * (hy / 2)[None, :]
    num[:, :-1] += e * (hy / 2)[None, :]
    gx = num / dx                                     # conductance of x-edges
    # y-edge (i,j)-(i,j+1): cells (i-1,j) and (i,j), each dx/2 wide, over the length hy[j]
    num = np.zeros((nx + 1, ny))
    num[1:, :] += e * dx / 2
    num[:-1, :] += e * dx / 2
    gy = num / hy[None, :]
    free = ~fixed
    idx = -np.ones((nx + 1, ny + 1), int)
    idx[free] = np.arange(free.sum())
    I, J = np.nonzero(free)
    k = idx[I, J]
    rows, cols, data = [k], [k], []
    diag = np.zeros(len(k))
    b = np.zeros(len(k))
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ii, jj = I + di, J + dj
        ok = (ii >= 0) & (ii <= nx) & (jj >= 0) & (jj <= ny)        # outside the domain -> Neumann
        ee = np.zeros(len(k))
        if di == 1:
            ee[ok] = gx[I[ok], J[ok]]
        elif di == -1:
            ee[ok] = gx[I[ok] - 1, J[ok]]
        elif dj == 1:
            ee[ok] = gy[I[ok], J[ok]]
        else:
            ee[ok] = gy[I[ok], J[ok] - 1]
        diag += ee
        nbf = np.zeros(len(k), bool)
        nbf[ok] = free[ii[ok], jj[ok]]
        rows.append(k[nbf])
        cols.append(idx[ii[nbf], jj[nbf]])
        data.append(-ee[nbf])
        nfx = ok & ~nbf
        np.add.at(b, k[nfx], ee[nfx] * val[ii[nfx], jj[nfx]])
    data = [diag] + data
    A = coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
                   shape=(len(k), len(k))).tocsr()
    V = val.copy()
    V[free] = spsolve(A, b)
    return (gx * np.diff(V, axis=0) ** 2).sum() + (gy * np.diff(V, axis=1) ** 2).sum()


def solve(w, g, h, er, t=0.035, mask_t=0.0, mask_er=3.8, half_width=1.5, top=6.0, cells_per_h=80, growth=1.12,
          mask_mode="full", corridor_inset=0.01):
    """single GCPW line. uniform x grid (dx = h / cells_per_h); y uniform up to 0.15 mm above the copper, then geometric
    growth to `top` (a grounded lid far above approximates open space)"""
    dx = h / cells_per_h
    nx = int(round(half_width / dx))
    y, jh, jt, jm = _grid_y(h, t, mask_t, dx, top, growth)
    ny = len(y) - 1
    hy = np.diff(y)                                   # (ny,) cell heights
    iw = int(round(w / 2 / dx))                       # signal half width (nodes 0..iw)
    ig = int(round((w / 2 + g) / dx))                 # first ground node
    eps_cells = np.ones((nx, ny))
    eps_cells[:, :jh] = er
    mask_region = np.zeros((nx, ny), bool)
    if mask_t > 0 and mask_mode == "full":
        mask_region[:, jt:jm] = True
        mask_region[iw:ig, jh:jt] = True              # LPI fills the gaps up to the copper height
    elif mask_t > 0 and mask_mode == "corridor":        # mask-free corridor: mask only on the coplanar grounds
        ic = int(round((w / 2 + g - corridor_inset) / dx))
        mask_region[max(ic, ig):, jt:jm] = True
    fixed = np.zeros((nx + 1, ny + 1), bool)
    val = np.zeros((nx + 1, ny + 1))
    fixed[:, 0] = True                                # In1 plane
    fixed[:, ny] = True                               # far lid
    fixed[:iw + 1, jh:jt + 1] = True
    val[:iw + 1, jh:jt + 1] = 1.0
    fixed[ig:, jh:jt + 1] = True

    def capacitance(with_diel):
        e = np.ones((nx, ny))
        if with_diel:
            e = eps_cells.copy()
            e[mask_region] = mask_er
        return 2 * EPS0 * _energy(e, fixed, val, dx, hy)    # both halves of the symmetric section

    C = capacitance(True)
    Cv = capacitance(False)
    z = 1.0 / (C0 * math.sqrt(C * Cv))
    return dict(z0=z, eeff=C / Cv, C_pF_per_m=C * 1e12, grid_um=dx * 1e3, nodes=(nx + 1) * (ny + 1))


def solve_coupled(w, s, g, h, er, t=0.035, mask_t=0.0, mask_er=3.8, ground_w=1.2, top=6.0, cells_per_h=80,
                  growth=1.12, mask_mode="full", corridor_inset=0.01, inner_web=0.0):
    """edge-coupled GCPW pair: strips of width w, inner gap s (no ground between them), outer ground gap g, coplanar
    ground `ground_w` wide outside each strip, In1 plane at depth h. Returns odd / even mode impedances, eeff, Z_diff,
    Z_cm and the coupling coefficient. mask_mode: "full" = LPI over everything (gaps filled to copper height),
    "corridor" = mask-free over both strips and all three gaps (mask only on the outer grounds); inner_web > 0 adds
    an LPI strip of that half-width on the pair centre line (each leg has its own mask aperture)."""
    dx = h / cells_per_h
    x1, x2, x3 = s / 2, s / 2 + w, s / 2 + w + g
    nx = int(round((x3 + ground_w) / dx))
    y, jh, jt, jm = _grid_y(h, t, mask_t, dx, top, growth)
    ny = len(y) - 1
    hy = np.diff(y)
    i1, i2, i3 = (int(round(x / dx)) for x in (x1, x2, x3))
    eps_cells = np.ones((nx, ny))
    eps_cells[:, :jh] = er
    mask_region = np.zeros((nx, ny), bool)
    if mask_t > 0 and mask_mode == "full":
        mask_region[:, jt:jm] = True
        mask_region[:i1, jh:jt] = True                # inner gap (between the two strips) filled to copper height
        mask_region[i2:i3, jh:jt] = True              # outer ground gap
    elif mask_t > 0 and mask_mode == "corridor":
        ic = int(round((x3 - corridor_inset) / dx))
        mask_region[max(ic, i3):, jt:jm] = True
        if inner_web > 0:                             # web on the centre line: laminate surface to above the copper
            iweb = min(int(round(inner_web / dx)), i1)
            mask_region[:iweb, jh:jm] = True
    out = dict(w=w, s=s, g=g, h=h, er=er, t=t, mask_t=mask_t, mask_mode=mask_mode, grid_um=dx * 1e3,
               inner_web=inner_web)
    for mode in ("odd", "even"):
        fixed = np.zeros((nx + 1, ny + 1), bool)
        val = np.zeros((nx + 1, ny + 1))
        fixed[:, 0] = True                            # In1 plane
        fixed[:, ny] = True                           # far lid
        fixed[i1:i2 + 1, jh:jt + 1] = True            # signal strip (this half's line of the pair)
        val[i1:i2 + 1, jh:jt + 1] = 1.0
        fixed[i3:, jh:jt + 1] = True                  # outer coplanar ground
        if mode == "odd":
            fixed[0, :] = True                        # electric wall: the other line is at -1 V
            val[0, :] = 0.0

        def capacitance(with_diel):
            e = np.ones((nx, ny))
            if with_diel:
                e = eps_cells.copy()
                e[mask_region] = mask_er
            return EPS0 * _energy(e, fixed, val, dx, hy)       # per line of the pair

        C = capacitance(True)
        Cv = capacitance(False)
        out[f"z_{mode}"] = 1.0 / (C0 * math.sqrt(C * Cv))
        out[f"eeff_{mode}"] = C / Cv
        out[f"C_{mode}_pF_per_m"] = C * 1e12
    out["z_diff"] = 2 * out["z_odd"]
    out["z_cm"] = out["z_even"] / 2
    out["k"] = (out["z_even"] - out["z_odd"]) / (out["z_even"] + out["z_odd"])
    out["nodes"] = (nx + 1) * (ny + 1)
    return out


# ------------------------------------------------------------------------------------------------ closed form
def _kk(k):
    """K(k)/K(k') with modulus k (scipy uses the parameter m = k^2)"""
    return ellipk(k * k) / ellipk(1 - k * k)


def _cross(xa, xb, xc, xd):
    """modulus of the two-conductor half-plane problem: conductor [xb, xc] against (-inf, xa] U [xd, inf)
    (xa = -inf: against [xd, inf) only); capacitance = eps K(k)/K(k')"""
    if xa == -math.inf:
        return math.sqrt((xc - xb) / (xd - xb))
    return math.sqrt((xc - xb) * (xd - xa) / ((xd - xb) * (xc - xa)))


def closed_form_coupled(w, s, g, h, er):
    """zero-thickness, mask-free edge-coupled conductor-backed CPW (see module docstring). Returns the same keys as
    solve_coupled()."""
    x1, x2, x3 = s / 2, s / 2 + w, s / 2 + w + g
    ch = [math.cosh(math.pi * x / h) for x in (x1, x2, x3)]
    k_up = dict(even=_cross(-math.inf, x1 ** 2, x2 ** 2, x3 ** 2), odd=_cross(0.0, x1 ** 2, x2 ** 2, x3 ** 2))
    k_lo = dict(even=_cross(-1.0, *ch), odd=_cross(1.0, *ch))
    out = dict(w=w, s=s, g=g, h=h, er=er, moduli=dict(up=k_up, low=k_lo))
    for mode in ("odd", "even"):
        ru, rl = _kk(k_up[mode]), _kk(k_lo[mode])
        out[f"z_{mode}"] = ETA0 / math.sqrt((ru + rl) * (ru + er * rl))
        out[f"eeff_{mode}"] = (ru + er * rl) / (ru + rl)
    out["z_diff"] = 2 * out["z_odd"]
    out["z_cm"] = out["z_even"] / 2
    out["k"] = (out["z_even"] - out["z_odd"]) / (out["z_even"] + out["z_odd"])
    return out
