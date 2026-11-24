"""Companion device 2 - coherent ballistic fluxon router (dual-rail Mach-Zehnder for a flying quantum fluxon).

Physics (derived in NOVELTY/paper): the two rails of a qubit are the two rows of a Josephson ladder sharing a
middle rail. Where the middle rail contains junctions (beam-splitter sections, BS), the vortex hops between rows
by a quantum phase slip of a middle-rail junction, amplitude E_S (computed exactly here from the junction's
charge dispersion with scqubits: E_S = dispersion/4). Between the BSs the two paths enclose the middle-rail
island: a gate voltage sets its charge and hence the Aharonov-Casher phase chi between the paths.
Model: one fluxon coordinate x (relativistic E(k)) times a 2-level row index,
    H = E(k) + H_perp(x),   H_perp = [[eps/2, -t(x)], [-t*(x), -eps/2]],  t = E_S e^{i chi} in BS2.
Outputs: figures/companion2_router.png, results/companion2_router.json
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import plt, save_json, savefig, C_IND, C_MIX, C_TH, C_SIM  # noqa: E402
import scqubits as scq  # noqa: E402
from hardware.params import RailParams  # noqa: E402
from quantum.fluxon import FluxonModel  # noqa: E402

scq.settings.T1_DEFAULT_WARNING = False
rail = RailParams()
model = FluxonModel(rail)
res = {}

# ---------------------------------------------------------------- phase-slip amplitude of the middle-rail junction
def qps_amplitude(EJ, EC):
    t = scq.Transmon(EJ=EJ, EC=EC, ng=0.0, ncut=31, truncated_dim=2)
    e0 = t.eigenvals(evals_count=1)[0]
    t.ng = 0.5
    return abs(t.eigenvals(evals_count=1)[0] - e0) / 4


ratios = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
ES = {r: qps_amplitude(r * 8.0, 8.0) for r in ratios}
res["qps_amplitude_GHz_vs_EJ_over_EC"] = ES
EJM_EC = 2.0
tES = ES[EJM_EC]
print("E_S (E_J/E_C = 2, E_C = 8 GHz) =", tES, "GHz")


def bs_length(beta, t=tES):
    v = model.v_cells_per_ns(model.k_for_beta(beta))
    return v / (8 * t)                      # 2 pi t tau = pi/4  ->  50/50


# ---------------------------------------------------------------- transverse evolution for a fluxon of speed v
def transfer(beta, chi, L_bs, gap, t=tES, eps_phase=0.0, sigma_chi=0.0, rng=None, edge=2.0, dx=0.25):
    """2x2 row-space evolution along the path (straight-line motion, reflection negligible: t << KE)."""
    v = model.v_cells_per_ns(model.k_for_beta(beta))
    xs = np.arange(-10, 2 * L_bs + gap + 10, dx)
    w1 = 0.5 * (np.tanh((xs - 0) / edge) - np.tanh((xs - L_bs) / edge))
    w2 = 0.5 * (np.tanh((xs - L_bs - gap) / edge) - np.tanh((xs - 2 * L_bs - gap) / edge))
    ch = chi + (rng.normal(0, sigma_chi) if sigma_chi else 0.0)
    U = np.eye(2, dtype=complex)
    dt = dx / v
    for i in range(len(xs)):
        tt = t * (w1[i] + w2[i] * np.exp(1j * ch))
        eps = eps_phase * (1.0 if L_bs < xs[i] < L_bs + gap else 0.0)
        Hm = np.array([[eps / 2, -tt], [-np.conj(tt), -eps / 2]])
        e, V = np.linalg.eigh(Hm)
        U = (V * np.exp(-1j * 2 * math.pi * e * dt)) @ V.conj().T @ U
    return U


def p_row1(beta, chi, L_bs, gap, **kw):
    U = transfer(beta, chi, L_bs, gap, **kw)
    return abs(U[1, 0]) ** 2                 # launched in row 0


BETA = 0.45
L = bs_length(BETA)
GAP = 100.0
res["design"] = dict(beta=BETA, E_S_GHz=tES, EJ_M_over_EC_M=EJM_EC, bs_length_cells=L, bs_length_um=L * rail.pitch_um, gap_cells=GAP)
print("design", res["design"])

# single BS splitting ratio vs fluxon speed (rotation angle ~ 1/v)
betas = np.linspace(0.3, 0.6, 31)
split = [abs(transfer(b, 0.0, L, 0.0)[1, 0]) ** 2 for b in betas]

# Mach-Zehnder fringes
chis = np.linspace(0, 2 * math.pi, 73)
ideal = [p_row1(BETA, c, L, GAP) for c in chis]
rng = np.random.default_rng(1)


def thermal_avg(chi, T_K, n=200, sigma_chi=0.0):
    s = model.thermal_beta_spread(BETA, T_K) * BETA
    bs = BETA + s * rng.standard_normal(n)
    return float(np.mean([p_row1(b, chi, L, GAP, sigma_chi=sigma_chi, rng=rng) for b in bs]))


th20 = [thermal_avg(c, 0.02, n=60) for c in chis]
qn = [thermal_avg(c, 0.02, n=60, sigma_chi=2 * math.pi * 0.01) for c in chis]


def visibility(p):
    """fringe contrast max - min (the normalised visibility is blind here: at chi = pi the two beam splitters cancel
    exactly for every speed, so the minimum stays 0)"""
    return max(p) - min(p)


Ts = [0.01, 0.02, 0.05, 0.1, 0.2]
vis_T = {}
for b in (0.30, 0.45, 0.60):
    Lb = bs_length(b)
    vis_T[b] = []
    for T in Ts:
        s = model.thermal_beta_spread(b, T) * b
        bs = b + s * rng.standard_normal(80)
        pc = [float(np.mean([abs(transfer(bb, c, Lb, GAP)[1, 0]) ** 2 for bb in bs])) for c in (0.0, math.pi)]
        vis_T[b].append(abs(pc[1] - pc[0]))
res["fringes"] = dict(chi=chis, ideal=ideal, thermal_20mK=th20, thermal_plus_charge_noise_0p01e=qn,
                      contrast_ideal=visibility(ideal), contrast_20mK=visibility(th20), contrast_20mK_charge_noise=visibility(qn))
res["contrast_vs_T"] = {str(b): dict(T_K=Ts, contrast=v) for b, v in vis_T.items()}
print("contrasts", res["fringes"]["contrast_ideal"], res["fringes"]["contrast_20mK"], res["fringes"]["contrast_20mK_charge_noise"])

# ---------------------------------------------------------------- explicit wavepacket demonstration (split and recombine)
def wavepacket_run(chi, n=8192, dx=0.25, sig=12.0):
    x = (np.arange(n) - n // 2) * dx
    k = 2 * math.pi * np.fft.fftfreq(n, dx)
    E = model.energy(k)
    k0 = model.k_for_beta(BETA)
    v = model.v_cells_per_ns(k0)
    x_bs1 = 0.0
    w1 = 0.5 * (np.tanh((x - x_bs1) / 2) - np.tanh((x - x_bs1 - L) / 2))
    w2 = 0.5 * (np.tanh((x - L - GAP) / 2) - np.tanh((x - 2 * L - GAP) / 2))
    tt = tES * (w1 + w2 * np.exp(1j * chi))
    psi = np.zeros((2, n), complex)
    psi[0] = (2 * math.pi * sig ** 2) ** -0.25 * np.exp(-(x + 250) ** 2 / (4 * sig ** 2) + 1j * k0 * x)
    dt = 0.002
    T = (2 * L + GAP + 500) / v
    nst = int(T / dt)
    a = np.abs(tt)
    ph = np.angle(tt)
    th = 2 * math.pi * a * dt / 2
    c, s = np.cos(th), np.sin(th)
    kin = np.exp(-1j * 2 * math.pi * E * dt)
    frames = []
    for st in range(nst):
        p0, p1 = psi[0], psi[1]                        # exp(-i th (-cos ph sx - sin ph sy)) = c + i s (e^{-i ph} |0><1| + h.c.)
        psi = np.array([c * p0 + 1j * s * np.exp(1j * ph) * p1, c * p1 + 1j * s * np.exp(-1j * ph) * p0])
        psi = np.fft.ifft(kin * np.fft.fft(psi, axis=1), axis=1)
        p0, p1 = psi[0], psi[1]
        psi = np.array([c * p0 + 1j * s * np.exp(1j * ph) * p1, c * p1 + 1j * s * np.exp(-1j * ph) * p0])
        if st % max(1, nst // 160) == 0:
            frames.append(np.abs(psi) ** 2)
    out = np.sum(np.abs(psi) ** 2, axis=1) * dx
    return x, np.array(frames), T, out


x, F0, T0, out0 = wavepacket_run(0.0)
_, Fpi, _, outpi = wavepacket_run(math.pi)
res["wavepacket"] = dict(chi0_row_probabilities=out0, chi_pi_row_probabilities=outpi)
print("wavepacket outputs", out0, outpi)

fig, ax = plt.subplots(2, 3, figsize=(13.5, 7.0))
sl = slice(np.searchsorted(x, -330), np.searchsorted(x, 2 * L + GAP + 260))
for col, (Fr, lab) in enumerate(((F0, "chi = 0: exits in row 1"), (Fpi, "chi = pi: back to row 0"))):
    for row in range(2):
        a = ax[row, col]
        a.imshow(Fr[:, row, sl].T, origin="lower", aspect="auto", cmap="magma", extent=[0, T0, x[sl][0], x[sl][-1]])
        for y in (0, L, L + GAP, 2 * L + GAP):
            a.axhline(y, color="w", lw=0.5, ls=":")
        a.set(xlabel="time (ns)", ylabel="fluxon position (cells)", title=f"row {row}, {lab}")
        a.grid(False)
a = ax[0, 2]
a.plot(chis, ideal, "-", color=C_SIM, label=f"single speed, contrast {visibility(ideal):.4f}")
a.plot(chis, th20, "--", color=C_MIX, label=f"thermal launch 20 mK, contrast {visibility(th20):.4f}")
a.plot(chis, qn, ":", color=C_IND, label=f"+ 0.01e rms charge noise, contrast {visibility(qn):.4f}")
a.set(xlabel="Aharonov-Casher phase chi (gate voltage)", ylabel="P(exit in row 1)", title=f"Mach-Zehnder fringes, beta = {BETA}")
a.legend(fontsize=7.5)
a = ax[1, 2]
for b, v in vis_T.items():
    a.plot(np.array(Ts) * 1e3, v, "o-", label=f"beta = {b} (BS {bs_length(b):.0f} cells)")
a.set(xlabel="launch temperature (mK)", ylabel="fringe contrast (max - min)", title="Contrast vs launch temperature")
a.legend(fontsize=7.5)
savefig(fig, "companion2_router.png")
res["single_bs_splitting_vs_beta"] = dict(beta=betas, P_row1=split)
res["verdict"] = ("Simulated: a flying quantum fluxon is split by a phase-slip beam splitter, carried coherently on two "
                  "ladder rows and recombined; the exit row is set by the gate-voltage (Aharonov-Casher) phase - a "
                  "coherent fluxon router. Not demonstrated experimentally anywhere we found. Open requirements: "
                  "charge stability of the middle-rail island, E_S fabrication spread, reflection at BS boundaries "
                  "(estimated negligible, t << KE), vortex hopping beyond the single-junction QPS estimate.")
save_json("companion2_router.json", res)
print("done")
