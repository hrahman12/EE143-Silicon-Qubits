"""Physics of the QFX-1 quantum-fluxon chip.

A. Quantum fluxon qubit. One Josephson vortex in an annular parallel array of N small Al junctions
   (E_J, E_C) joined by grAl cell inductors (E_L = Lambda^2 E_J). Two weakened junctions make a double
   well; the junction between them is a dc SQUID whose flux sets the tunnelling barrier.
   Reduction: the minimum-energy path between the two wells (string method in mass-weighted phases
   q_i = phi_i / sqrt(8 E_C)), then a 1D Schroedinger equation H = -1/2 d^2/ds^2 + U(s) along its arc
   length s. Cross-checked against the full N-junction normal modes (pinning frequency in a well, and the
   next transverse mode for the Born-Oppenheimer separation).
B. Two-qubit coupling through a shared inductor: L_s I1 I2 = J tz(x)tz in the fluxon-position basis
   (a transverse XX coupling in the energy basis at the sweet spot), J = L_s dI^2 / 4.
C. Fluxon-kick gate. A heavy classical fluxon in a Nb ballistic line passes a line section that is
   flux-coupled (fraction kappa) to the qubit's tilt. While the fluxon is inside the section the section
   holds one Phi0, so the qubit sees a smooth plateau tilt eps for tau = n_c / v and picks up
   theta = eps tau / hbar.  Back-action: the line fluxon is displaced by dX = hbar theta / p, so the
   gate dephases by 1 - exp(-theta^2 (sigma_p/p)^2 / 2). Checked with (i) multilevel qubit dynamics and
   (ii) a classical discrete sine-Gordon run of the line with the qubit-dependent interaction.
Writes out/qfx_sim.json and docs/qfx_*.png
"""
import json
import math
import os
import sys

import numpy as np
from scipy.optimize import minimize
from scipy.linalg import eigh, eigh_tridiagonal, expm

sys.path.insert(0, os.path.dirname(__file__))
from design_params import QFX

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
DOCS = os.path.join(HERE, "..", "docs")
h = 6.62607015e-34
hbar = h / (2 * math.pi)
kB = 1.380649e-23
PHI0 = 2.067833848e-15
TWO_PI = 2 * math.pi

# ============================================================ A. quantum fluxon qubit
N = QFX["ring_cells"]
EJ, EC, LAM = QFX["EJ_GHz"], QFX["EC_GHz"], QFX["Lambda"]
EL = LAM ** 2 * EJ
A = N // 2 - 1                      # first pinning junction
B = A + QFX["well_sep"]             # second pinning junction
MID = A + 1                         # barrier SQUID
W = QFX["well_weak"]
BMAX = QFX["barrier_EJmax_ratio"]


def junctions(phib):
    ej = np.full(N, EJ)
    ec = np.full(N, EC)
    for k in (A, B):
        ej[k] *= (1 - W)
        ec[k] /= (1 - W)            # smaller area -> smaller C
    ej[MID] = BMAX * EJ * abs(math.cos(math.pi * phib))
    ec[MID] = EC / BMAX
    return ej, ec


def links(phi):
    d = np.empty(N)
    d[:-1] = phi[1:] - phi[:-1]
    d[-1] = phi[0] + TWO_PI - phi[-1]
    return d


def energy(phi, ej, f):
    d = links(phi) - TWO_PI * f
    return np.sum(ej * (1 - np.cos(phi))) + 0.5 * EL * np.sum(d * d)


def grad(phi, ej, f):
    d = links(phi) - TWO_PI * f
    g = ej * np.sin(phi)
    g += EL * (np.roll(d, 1) - d)
    return g


def centre(phi):
    return np.sum(1 - phi / TWO_PI) - 0.5


def kink(x0, n=None, lam=LAM):
    n = np.arange(N) if n is None else n
    return 4 * np.arctan(np.exp((n - x0) / lam))


def hessian(phi, ej):
    Hs = np.diag(ej * np.cos(phi) + 2 * EL)
    idx = np.arange(N)
    Hs[idx, (idx + 1) % N] -= EL
    Hs[(idx + 1) % N, idx] -= EL
    return Hs


A_VEC = np.full(N, -1.0 / TWO_PI)          # d(centre)/d(phi_n): the centre constraint is linear


def relax(x0, ej, f, guess, tol=1e-11, maxit=60):
    """Exact constrained minimum of U at fixed fluxon centre: Newton on the KKT system
    [H a; a^T 0][dphi; lam] = [-g; x0 - centre(phi)], with a backtracking step on |KKT residual|."""
    phi = guess.copy()
    phi += A_VEC * (x0 - centre(phi)) / (A_VEC @ A_VEC)          # project onto the constraint
    K = np.zeros((N + 1, N + 1))
    K[:N, N] = A_VEC
    K[N, :N] = A_VEC
    lam = 0.0
    for _ in range(maxit):
        g = grad(phi, ej, f)
        r = np.concatenate([g + lam * A_VEC, [centre(phi) - x0]])
        if np.max(np.abs(r)) < tol:
            break
        K[:N, :N] = hessian(phi, ej)
        try:
            step = np.linalg.solve(K, -r)
        except np.linalg.LinAlgError:
            K[:N, :N] += 1e-6 * np.eye(N)
            step = np.linalg.solve(K, -r)
        t = 1.0
        n0 = np.linalg.norm(r)
        while t > 1e-4:
            p2, l2 = phi + t * step[:N], lam + t * step[N]
            r2 = np.concatenate([grad(p2, ej, f) + l2 * A_VEC, [centre(p2) - x0]])
            if np.linalg.norm(r2) < n0 or t < 2e-4:
                break
            t *= 0.5
        phi, lam = p2, l2
    return phi


def landscape(phib, ft=0.0, xs=None):
    """U(X), phases(X) and kinetic coefficient K(X) = hbar^2/2M (GHz cell^2)."""
    ej, ec = junctions(phib)
    f = np.zeros(N)
    f[A] += ft                      # gradiometric tilt flux (Phi0) on the two links around the barrier
    f[MID] -= ft
    xs = np.arange(A - 3.0, B + 3.0 + 1e-9, 0.02) if xs is None else xs
    U, P = [], []
    g = kink(xs[0])
    for x in xs:
        g = relax(x, ej, f, g)
        P.append(g.copy())
        U.append(energy(g, ej, f))
    P = np.array(P)
    dP = np.gradient(P, xs, axis=0)
    S = np.sum(dP ** 2 / ec, axis=1)
    return xs, np.array(U), P, 4.0 / S, ej, ec, f


def schrodinger(xs, U, Kc, nlev=8):
    hx = xs[1] - xs[0]
    Km = 0.5 * (Kc[1:] + Kc[:-1])
    diag = U.copy()
    diag[1:-1] += (Km[1:] + Km[:-1]) / hx ** 2
    diag[0] += Km[0] / hx ** 2
    diag[-1] += Km[-1] / hx ** 2
    off = -Km / hx ** 2
    E, V = eigh_tridiagonal(diag, off, select="i", select_range=(0, nlev - 1))
    return E, V / math.sqrt(hx)


def normal_modes(phi, ej, ec):
    Hs = hessian(phi, ej)
    D = np.diag(np.sqrt(8 * ec))
    w2 = np.linalg.eigvalsh(D @ Hs @ D)
    return np.sqrt(np.clip(w2, 0, None))        # GHz



def grad_all(Phi, ej, f):
    """gradient of U for a stack of configurations Phi (M x N)"""
    d = np.empty_like(Phi)
    d[:, :-1] = Phi[:, 1:] - Phi[:, :-1]
    d[:, -1] = Phi[:, 0] + TWO_PI - Phi[:, -1]
    d -= TWO_PI * f
    return ej * np.sin(Phi) + EL * (np.roll(d, 1, axis=1) - d)


def energy_all(Phi, ej, f):
    d = np.empty_like(Phi)
    d[:, :-1] = Phi[:, 1:] - Phi[:, :-1]
    d[:, -1] = Phi[:, 0] + TWO_PI - Phi[:, -1]
    d -= TWO_PI * f
    return np.sum(ej * (1 - np.cos(Phi)), axis=1) + 0.5 * EL * np.sum(d * d, axis=1)


def mep(phib, ft=0.0, M=161, iters=6000, xspan=2.5):
    """Minimum-energy path of the fluxon from the outer wall left of well A to the wall right of well B
    (string method in mass-weighted coordinates q = phi / sqrt(8 E_C)). Returns arc length s
    (GHz^-1/2), U(s) (GHz), configurations, and the f-vector used."""
    ej, ec = junctions(phib)
    f = np.zeros(N)
    f[A] += ft
    f[MID] -= ft
    w = np.sqrt(8 * ec)
    # initial path: constrained continuation from both sides, met at the barrier
    xl = np.linspace(A - xspan, MID, (M + 1) // 2)
    xr = np.linspace(B + xspan, MID, (M + 1) // 2)
    P = []
    g = kink(xl[0])
    for x in xl:
        g = relax(x, ej, f, g)
        P.append(g.copy())
    Pr = []
    g = kink(xr[0])
    for x in xr:
        g = relax(x, ej, f, g)
        Pr.append(g.copy())
    Phi = np.array(P + Pr[::-1][1:])
    Q = Phi / w
    dt = 0.5 / (np.max(np.abs(ej)) * 8 * np.max(ec) + 4 * EL * 8 * np.max(ec))
    for it in range(iters):
        G = grad_all(Q * w, ej, f) * w
        Q[1:-1] -= dt * G[1:-1]
        # reparametrise to equal arc length (mass-weighted metric)
        seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
        sc = np.concatenate([[0], np.cumsum(seg)])
        tgt = np.linspace(0, sc[-1], M)
        Q = np.array([np.interp(tgt, sc, Q[:, k]) for k in range(N)]).T
    seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    sarc = np.concatenate([[0], np.cumsum(seg)])
    Phi = Q * w
    return sarc, energy_all(Phi, ej, f), Phi, ej, ec, f


def links_all(Phi):
    d = np.empty_like(Phi)
    d[:, :-1] = Phi[:, 1:] - Phi[:, :-1]
    d[:, -1] = Phi[:, 0] + TWO_PI - Phi[:, -1]
    return d


def schrodinger_s(s, U, nlev=8, npts=1500):
    """H = -1/2 d^2/ds^2 + U(s) on the string (Dirichlet at the outer walls)."""
    sg = np.linspace(s[0], s[-1], npts)
    Ug = np.interp(sg, s, U)
    hs = sg[1] - sg[0]
    diag = Ug + 1.0 / hs ** 2
    off = np.full(npts - 1, -0.5 / hs ** 2)
    E, V = eigh_tridiagonal(diag, off, select="i", select_range=(0, nlev - 1))
    return sg, Ug, E, V / math.sqrt(hs)


res = {"parameters": dict(N=N, EJ_GHz=EJ, EC_GHz=EC, EL_GHz=EL, Lambda=LAM, EJ_over_EC=EJ / EC, pinning=[A, B],
                          barrier=MID, well_weak=W, barrier_EJmax_ratio=BMAX)}
L_cell_nH = (PHI0 / TWO_PI) ** 2 / (EL * 1e9 * h) * 1e9
Ic_nA = EJ * 1e9 * h * TWO_PI / PHI0 * 1e9
res["parameters"].update(L_cell_nH=round(L_cell_nH, 4), Ic_nA=round(Ic_nA, 2),
                         C_fF=round((1.602176634e-19) ** 2 / (2 * EC * 1e9 * h) * 1e15, 3))
print(f"cell L = {L_cell_nH:.3f} nH (grAl), Ic = {Ic_nA:.1f} nA")

# --- spectrum vs barrier flux (minimum-energy path + 1D Schroedinger along it)
sweep = []
for phib in np.round(np.arange(0.0, 0.4801, 0.02), 4):
    s_, U_, Phi_, *_ = mep(phib, iters=3000)
    sg, Ug, E_, V_ = schrodinger_s(s_, U_ - U_.min(), nlev=4)
    imid = len(s_) // 2
    sweep.append(dict(phi_b=float(phib), f01_GHz=float(E_[1] - E_[0]), f12_GHz=float(E_[2] - E_[1]),
                      anharm_GHz=float(E_[2] - 2 * E_[1] + E_[0]), barrier_GHz=float(U_[imid] - U_.min())))
    print(f"  Phi_b={phib:.3f}  f01={sweep[-1]['f01_GHz']:7.3f}  f12={sweep[-1]['f12_GHz']:7.3f} GHz  "
          f"barrier={sweep[-1]['barrier_GHz']:.2f} GHz", flush=True)
res["barrier_sweep"] = sweep
PHIB = QFX["phi_b_op"]            # zero SQUID flux: f01 is even in Phi_b, so df01/dPhi_b = 0 here (barrier sweet spot)
op = min(sweep, key=lambda x: abs(x["phi_b"] - PHIB))
assert op["barrier_GHz"] > 2 * op["f01_GHz"] and op["f12_GHz"] > 3 * op["f01_GHz"], op
s_, U_, Phi_, ej, ec, f = mep(PHIB)
Umin = U_.min()
sg, Ug, E, V = schrodinger_s(s_, U_ - Umin)
# wells and barrier along the path
half = len(s_) // 2
iL = int(np.argmin(U_[:half]))
iR = half + int(np.argmin(U_[half:]))
modes = normal_modes(Phi_[iL], ej, ec)
d2 = np.gradient(np.gradient(U_, s_), s_)
f_path = math.sqrt(max(d2[iL], 0))
res["operating_point"] = dict(phi_b=PHIB, f01_GHz=float(E[1] - E[0]), f12_GHz=float(E[2] - E[1]),
                              f02_GHz=float(E[2] - E[0]), levels_GHz=[float(e - E[0]) for e in E],
                              barrier_GHz=float(U_[half] - Umin), well_asymmetry_GHz=float(U_[iR] - U_[iL]),
                              wells_centre_X=[float(centre(Phi_[iL])), float(centre(Phi_[iR]))],
                              fluxon_mass_check=dict(path_pinning_GHz=f_path, full_normal_mode_GHz=float(modes[0]),
                                                     next_full_mode_GHz=float(modes[1]),
                                                     relative_error=float(abs(f_path - modes[0]) / modes[0])))
# flux sensitivity of f01 to the barrier SQUID (central differences) here and at the steepest point of the sweep
_d = 0.005
_f = []
for _pb in (PHIB - _d, PHIB, PHIB + _d):
    _s, _U, *_r = mep(abs(_pb), iters=3000)
    _E = schrodinger_s(_s, _U - _U.min(), nlev=3)[2]
    _f.append(float(_E[1] - _E[0]))
_slopes = [abs(b["f01_GHz"] - a["f01_GHz"]) / (b["phi_b"] - a["phi_b"]) for a, b in zip(sweep[:-1], sweep[1:])]
res["operating_point"]["df01_dphib_GHz_per_Phi0"] = (_f[2] - _f[0]) / (2 * _d)
res["operating_point"]["d2f01_dphib2_GHz_per_Phi0sq"] = (_f[2] - 2 * _f[1] + _f[0]) / _d ** 2
res["operating_point"]["max_sweep_slope_GHz_per_Phi0"] = max(_slopes)
print("operating point", res["operating_point"])

# --- tilt operator: dU/dft = -2 pi E_L (d_A - d_MID) (Hellmann-Feynman), in the qubit eigenbasis
dlk = links_all(Phi_)
g_s = -TWO_PI * EL * (dlk[:, A] - dlk[:, MID])
gX = np.interp(sg, s_, g_s)
hs = sg[1] - sg[0]
G = V.T @ (gX[:, None] * V) * hs
eps_per_phi0 = float(g_s[iR] - g_s[iL])
G01_link = {}
for n in range(N):
    gn = np.interp(sg, s_, -TWO_PI * EL * dlk[:, n])
    G01_link[n] = float((V[:, 0] * gn * V[:, 1]).sum() * hs)
res["single_link_G01_GHz_per_Phi0"] = {f"{n}->{(n + 1) % N}": G01_link[n] for n in range(N)}
res["tilt"] = dict(d_eps_d_ft_GHz_per_Phi0=eps_per_phi0, G01_GHz_per_Phi0=float(G[0, 1]),
                   G12_GHz_per_Phi0=float(G[1, 2]), G02_GHz_per_Phi0=float(G[0, 2]),
                   G00_minus_G11=float(G[0, 0] - G[1, 1]))
print("tilt", res["tilt"])

# --- link currents in the two wells (coupler / readout design)
I_unit = (PHI0 / TWO_PI) / (L_cell_nH * 1e-9)
dI_links = (dlk[iR] - dlk[iL]) * I_unit
res["link_current_difference_nA"] = {f"link {n}->{(n + 1) % N}": float(dI_links[n] * 1e9) for n in range(N)}
dI = float(dI_links[A])                       # link A->MID: shared with the ZZ bus in the layout
Ls = np.array([0.5, 1.0, 2.0, 5.0]) * 1e-12
res["coupling"] = dict(bus_link=f"{A}->{MID}", delta_I_nA=dI * 1e9,
                       J_zz_MHz_vs_shared_L_pH={f"{l * 1e12:g}": float(l * dI ** 2 / 4 / h / 1e6) for l in Ls})
print("coupling", res["coupling"])
dI_ro = float(dI_links[B + 1])                 # readout resonator lands on link B+1 -> B+2 in the layout
fr, Zr = 7.0e9, 50.0
I_zpf = math.sqrt(hbar * TWO_PI * fr / (2 * (Zr * 4 / (math.pi * TWO_PI * fr))))
Lsr = 40e-12
g_ro = Lsr * abs(dI_ro) * I_zpf / (2 * h)
res["readout"] = dict(resonator_GHz=fr / 1e9, link=f"{B + 1}->{B + 2}", delta_I_nA=dI_ro * 1e9, shared_L_pH=Lsr * 1e12,
                      I_zpf_nA=I_zpf * 1e9, g_MHz=g_ro / 1e6,
                      chi_MHz_est=float((g_ro ** 2 / (fr - (E[1] - E[0]) * 1e9)) / 1e6))
print("readout", res["readout"])

# ============================================================ C. fluxon-kick gate
Ick = QFX["kick_Ic_uA"] * 1e-6
EJk = Ick * PHI0 / TWO_PI                         # J
ECk = (1.602176634e-19) ** 2 / (2 * QFX["kick_C_fF"] * 1e-15)
LAMk = QFX["kick_Lambda"]
wpk = math.sqrt(8 * EJk * ECk) / hbar              # rad/s
c0 = LAMk * wpk                                    # cells / s
E0k = 8 * EJk * LAMk                               # fluxon rest energy (J)
Mk = hbar ** 2 / (LAMk * ECk)                      # kg cell^2 (cells as length unit)
kT = kB * QFX["T_mK"] * 1e-3
nc = QFX["kick_section_cells"]
nt = QFX["kick_taper_cells"]
# transformer coupling weight of each line cell (link k -> k+1) of the section: raised-cosine ramps at both ends
WK = np.ones(nc)
ramp = 0.5 * (1 - np.cos(math.pi * (np.arange(nt) + 0.5) / nt))
WK[:nt], WK[nc - nt:] = ramp, ramp[::-1]
SW, SW2 = float(WK.sum()), float((WK ** 2).sum())     # effective section lengths for eps*tau and eps^2*tau
res["kick_line"] = dict(Ic_uA=Ick * 1e6, EJ_GHz=EJk / h / 1e9, EC_GHz=ECk / h / 1e9, f_plasma_GHz=wpk / TWO_PI / 1e9,
                        c0_um_per_ps=c0 * QFX["kick_pitch_um"] * 1e-12, rest_energy_GHz=E0k / h / 1e9,
                        Lambda_cells=LAMk, strip_w_um=QFX["kick_strip_w_um"], gap_um=QFX["kick_gap_um"],
                        pitch_um=QFX["kick_pitch_um"], l_pH_per_um=QFX["kick_l_pH_per_um"],
                        L_cell_pH=QFX["kick_l_pH_per_um"] * QFX["kick_pitch_um"], L_J_pH=QFX["kick_LJ_pH"],
                        section_cells=nc, taper_cells=nt, effective_cells=SW)


F01 = res["operating_point"]["f01_GHz"]
G01 = abs(G01_link[MID])          # the kick transformer lands on the barrier link MID -> B


def kick_numbers(beta, theta):
    """Adiabatic fluxon-kick phase gate at the qubit sweet spot. While the heavy fluxon is inside the section
    the qubit sees a transverse tilt eps; the eigen-splitting grows to sqrt(f01^2 + eps^2) and the qubit
    picks up theta = 2 pi tau (sqrt(f01^2 + eps^2) - f01). The heavy fluxon sees a qubit-state-dependent
    potential difference with the same time integral, hence the back-action displacement dX = hbar theta / p."""
    v = beta * c0
    gam = 1 / math.sqrt(1 - beta ** 2)
    p = gam * Mk * v
    KE = (gam - 1) * E0k
    tau = SW / v                                                                 # coupling-weighted dwell time
    tau2 = SW2 / v                                                               # eps^2-weighted (dispersive phase)
    eps = math.sqrt((F01 + theta / (TWO_PI * tau2 * 1e9)) ** 2 - F01 ** 2)       # GHz, plateau value
    dX = theta * hbar / p
    sig2 = gam * kT / (Mk * v ** 2)
    deph_T = 1 - math.exp(-theta ** 2 * sig2 / 2)
    return dict(beta=beta, v_um_per_ps=v * QFX["kick_pitch_um"] * 1e-12, tau_ps=tau * 1e12, eps_plateau_GHz=eps,
                kappa=eps / (2 * G01), kinetic_energy_GHz=KE / h / 1e9, dX_cells=dX, thermal_dephasing=deph_T,
                launch_jitter_tol_for_1em4=math.sqrt(2e-4) / theta / gam ** 2)


res["kick_gate_table"] = [kick_numbers(b, math.pi / 2) for b in (0.01, 0.02, 0.05, 0.1, 0.2)]
for r in res["kick_gate_table"]:
    print("kick", {k: round(v, 5) for k, v in r.items()})

# --- (i) multilevel qubit dynamics under the actual kink-shaped tilt pulse (pi/2 kick at beta = 0.05)
BETA, THETA = 0.05, math.pi / 2
kn = kick_numbers(BETA, THETA)
kappa = kn["kappa"]
v = BETA * c0
gam = 1 / math.sqrt(1 - BETA ** 2)
s0, s1 = 0.0, float(nc)
t = np.linspace(-6 * LAMk / v / gam - 0, (nc + 6 * LAMk / gam) / v, 6000)
Xk = v * t                                          # fluxon centre (cells) relative to section start


def stepf(xrel):  # fraction of 2pi behind the fluxon: phi(n)/2pi for n behind -> 1
    return (2 / math.pi) * np.arctan(np.exp(np.clip(gam * xrel / LAMk, -50, 50)))


# coupled flux = sum over section links of weight x (fraction of the fluxon's 2pi in that link): 0 -> 1 -> 0
S = sum(WK[k] * (stepf(Xk - k) - stepf(Xk - k - 1)) for k in range(nc))
nl = len(E)
H0 = np.diag(E - E[0])                              # GHz
G = V.T @ (np.interp(sg, s_, -TWO_PI * EL * dlk[:, MID])[:, None] * V) * hs   # transformer -> link MID
dt = (t[1] - t[0]) * 1e9                           # ns


def propagate(kap):
    Ut = np.eye(nl, dtype=complex)
    ft_t = kap * S
    for k in range(len(t) - 1):
        Hk = H0 + 0.5 * (ft_t[k] + ft_t[k + 1]) * G
        Ut = expm(-1j * TWO_PI * Hk * dt) @ Ut
    Ufree = np.diag(np.exp(-1j * TWO_PI * np.diag(H0) * (t[-1] - t[0]) * 1e9))
    return Ufree.conj().T @ Ut, ft_t


kap_lo, kap_hi = 0.5 * kappa, 1.6 * kappa          # bisection on the transformer coupling for theta = pi/2
for _ in range(14):
    kap_mid = 0.5 * (kap_lo + kap_hi)
    Uint, ft_t = propagate(kap_mid)
    ph = abs(float(np.angle(Uint[1, 1] / Uint[0, 0])))
    if ph < THETA:
        kap_lo = kap_mid
    else:
        kap_hi = kap_mid
kappa = kap_mid
leak = 1 - np.sum(np.abs(Uint[:2, :2]) ** 2, axis=0).min()
flip = abs(Uint[1, 0]) ** 2
phase = float(np.angle(Uint[1, 1] / Uint[0, 0]))
theta_formula = float(TWO_PI * np.sum((np.sqrt(F01 ** 2 + (2 * G01 * ft_t) ** 2) - F01)) * dt)
res["kick_gate_dynamics"] = dict(beta=BETA, theta_target=THETA, kappa_calibrated=kappa, kappa_plateau_estimate=kn["kappa"], pulse_ns=float((t[-1] - t[0]) * 1e9),
                                 eps_plateau_GHz=kn["eps_plateau_GHz"], conditional_phase_rad=abs(phase),
                                 theta_two_level_formula_rad=theta_formula, bit_flip_probability=float(flip),
                                 leakage=float(leak),
                                 note="adiabatic dispersive Z gate at the sweet spot; heavy fluxon exits with its energy")
print("kick dynamics", res["kick_gate_dynamics"])

# --- (ii) classical check of the back-action displacement dX = hbar theta / p
Ns = 900
x_in = 150


def run_line(sign, eps_J, beta=BETA, T=None):
    """discrete sine-Gordon of the kick line (units: E_J, 1/w_p, cells) with qubit-dependent energy
    U_int = -sign * (eps/2) * sum_k w_k (phi_k+1 - phi_k)/(2 pi) on the section links [x_in, x_in + nc)"""
    lam2 = LAMk ** 2
    c = sign * 0.5 * eps_J / EJk / TWO_PI
    n = np.arange(Ns)
    g = 1 / math.sqrt(1 - beta ** 2)
    x0 = 60.0
    th = np.clip(g * (x0 - n) / LAMk, -60, 60)
    phi = 4 * np.arctan(np.exp(th))
    dphi = 4 * g * beta * np.exp(th) / (1 + np.exp(2 * th))   # phi increases as the kink passes
    dt_ = 0.02
    T = T or (x_in + nc + 150 - x0) / (beta * LAMk)
    def acc(p):
        lap = np.zeros_like(p)
        lap[1:-1] = p[2:] - 2 * p[1:-1] + p[:-2]
        lap[0] = p[1] - p[0]
        lap[-1] = p[-2] - p[-1]
        a_ = lam2 * lap - np.sin(p)
        a_[x_in:x_in + nc + 1] += c * (np.r_[0.0, WK] - np.r_[WK, 0.0])   # -dU_int/dphi_n = c (w_n-1 - w_n)
        return a_
    a_ = acc(phi)
    for _ in range(int(T / dt_)):
        phi = phi + dt_ * dphi + 0.5 * dt_ ** 2 * a_
        dh = dphi + 0.5 * dt_ * a_
        a_ = acc(phi)
        dphi = dh + 0.5 * dt_ * a_
    return np.sum(phi / TWO_PI) - 0.5          # centre (cells): number of sites behind the kink


# use a test coupling with steps of +-2 % of the fluxon kinetic energy (linear regime, shift >> grid noise)
KE_J = (gam - 1) * E0k
eps_test = 0.04 * KE_J
xp, xm = run_line(+1, eps_test), run_line(-1, eps_test)
p_cl = gam * Mk * v
res["backaction_check"] = dict(eps_test_GHz=eps_test / h / 1e9, dX_sim_cells=float(abs(xm - xp)),
                               dX_formula_cells=float(eps_test * (SW / v) / p_cl),
                               note="branches differ by eps on the weighted section; dX = (time integral of the energy "
                                    "difference) / p = hbar theta / p")
res["backaction_check"]["relative_error"] = float(abs(res["backaction_check"]["dX_sim_cells"] -
                                                      res["backaction_check"]["dX_formula_cells"]) /
                                                  res["backaction_check"]["dX_formula_cells"])
print("backaction", res["backaction_check"])

os.makedirs(OUT, exist_ok=True)
json.dump(res, open(os.path.join(OUT, "qfx_sim.json"), "w"), indent=1, default=float)

# ============================================================ figures
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 3, figsize=(16, 4.8), dpi=130)
ax[0].plot(sg, Ug, color="#222", lw=2, label="U(s) along the minimum-energy path")
for k in range(4):
    ax[0].plot(sg, E[k] + 5 * V[:, k] ** 2 / np.max(V[:, k] ** 2), lw=1.3, label=f"|{k}>  {E[k] - E[0]:.2f} GHz")
    ax[0].axhline(E[k], color="#999", lw=.5)
ax[0].set(xlabel="mass-weighted path length s (GHz^-1/2)", ylabel="energy (GHz)",
          title=f"Quantum fluxon double well (Phi_b = {PHIB} Phi0)", ylim=(0, max(45, E[4] * 1.1)))
ax[0].legend(fontsize=8)
ax[1].plot([x["phi_b"] for x in sweep], [x["f01_GHz"] for x in sweep], "o-", color="#c8202a", label="f01")
ax[1].plot([x["phi_b"] for x in sweep], [x["f12_GHz"] for x in sweep], "s-", color="#2f6bff", label="f12")
ax[1].plot([x["phi_b"] for x in sweep], [x["barrier_GHz"] for x in sweep], "--", color="#888", label="barrier")
ax[1].set(xlabel="barrier SQUID flux Phi_b / Phi0", ylabel="GHz", title="Tunnelling tuned by the barrier SQUID")
ax[1].legend()
bs = np.linspace(0.005, 0.3, 80)
for th, col in ((math.pi / 4, "#22a060"), (math.pi / 2, "#2f6bff"), (math.pi, "#c8202a")):
    ax[2].semilogy(bs, [kick_numbers(b, th)["thermal_dephasing"] for b in bs], color=col, label=f"theta = {th / math.pi:.2g} pi")
ax[2].set(xlabel="kick fluxon speed v / c0", ylabel="which-path dephasing per kick",
          title=f"Fluxon-kick gate back-action at {QFX['T_mK']:.0f} mK (Ic = {QFX['kick_Ic_uA']:.0f} uA)")
ax[2].legend()
for a_ in ax:
    a_.grid(alpha=.25)
fig.tight_layout()
os.makedirs(DOCS, exist_ok=True)
fig.savefig(os.path.join(DOCS, "qfx_sim.png"))
print("done")
