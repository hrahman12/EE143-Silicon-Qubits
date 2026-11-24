"""2D quasi-static finite-difference cross-check of the GCPW cross-section (cross-check only; the pass/fail impedance
check uses rf_calc.gcpw_z0 as required).

Laplace equation div(eps grad V) = 0 on a uniform grid over half of the symmetric cross-section (Neumann at the symmetry
plane x = 0 and at the far side, ground plane In1 at y = 0, grounded lid far above). Conductors are Dirichlet nodes
(signal 1 V, coplanar grounds 0 V). The capacitance per unit length follows from the stored energy,
    C = eps0 * sum_edges eps_edge * dV^2      (V = 1, both halves)
solved once with the dielectrics (C) and once in vacuum (C0):  Z0 = 1 / (c sqrt(C C0)),  eeff = C / C0.
"""
import math

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

EPS0 = 8.8541878128e-12
C0 = 299792458.0


def solve(w, g, h, er, t=0.035, mask_t=0.0, mask_er=3.8, half_width=1.5, top=6.0, cells_per_h=80, growth=1.12,
          mask_mode="full", corridor_inset=0.01):
    """uniform x grid (dx = h / cells_per_h); y uniform up to 0.15 mm above the copper, then geometric growth to `top`
    (a grounded lid far above approximates open space)"""
    dx = h / cells_per_h
    nx = int(round(half_width / dx))
    jh = cells_per_h                                  # dielectric top (node row)
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
    y = np.array(y)
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
    # dual-cell widths: x-edges (i,j)-(i+1,j) carry flux through a height ly[j]; y-edges through a width lx[i]
    ly = np.zeros(ny + 1)
    ly[:-1] += hy / 2
    ly[1:] += hy / 2
    lx = np.full(nx + 1, dx)
    lx[0] = lx[-1] = dx / 2

    def capacitance(with_diel):
        e = np.ones((nx, ny))
        if with_diel:
            e = eps_cells.copy()
            e[mask_region] = mask_er
        # x-edge (i,j)-(i+1,j): cells (i,j-1) [height hy[j-1]] and (i,j) [height hy[j]], weighted by height
        num = np.zeros((nx, ny + 1))
        num[:, 1:] += e * (hy / 2)[None, :]
        num[:, :-1] += e * (hy / 2)[None, :]
        gx = num / dx                                 # conductance of x-edges
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
        W = (gx * np.diff(V, axis=0) ** 2).sum() + (gy * np.diff(V, axis=1) ** 2).sum()
        return 2 * EPS0 * W                           # both halves of the symmetric section

    C = capacitance(True)
    Cv = capacitance(False)
    z = 1.0 / (C0 * math.sqrt(C * Cv))
    return dict(z0=z, eeff=C / Cv, C_pF_per_m=C * 1e12, grid_um=dx * 1e3, nodes=(nx + 1) * (ny + 1))
