"""Discrete sine-Gordon model of the RFL die's ballistic lines (no external simulator needed).

A discrete long Josephson junction (LJJ): series cell inductance L between nodes, each node shunted to
ground by an unbiased, unshunted JJ (critical current Ic, capacitance C). In units of the plasma time
1/omega_p and the Josephson length lambda_J (lambda_J = Lambda cells, Lambda^2 = L_J / L):

    phi_n'' + alpha phi_n' + b_n sin(phi_n) = (phi_{n+1} - 2 phi_n + phi_{n-1}) / a^2 ,   a = 1/Lambda

A fluxon is a 2*pi kink. Checks run here:
  1. ballistic propagation: fluxon launched at v = 0.6 c_0 keeps its speed and >98 % of its energy over the
     longest on-chip line (alpha from sub-gap quasiparticle loss).
  2. controlled barrier: node junction replaced by a symmetric dc SQUID, Ic_eff = b_max |cos(pi Phi/Phi0)|.
     The control flux switches the fluxon between transmission and reflection.
Writes out/rfl_sim.json and docs/rfl_sim.png.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from design_params import RFL

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
DOCS = os.path.join(HERE, "..", "docs")
PHI0 = 2.067833848e-15

Ic = RFL["jj_ic_uA"] * 1e-6
LJ = PHI0 / (2 * math.pi * Ic)
L = RFL["cell_L_pH"] * 1e-12
LAM = math.sqrt(LJ / L)                         # Josephson length in cells
C = RFL["jj_area_um2"] * RFL["jj_c_fF_per_um2"] * 1e-15
WP = math.sqrt(2 * math.pi * Ic / (PHI0 * C))    # plasma angular frequency
a = 1.0 / LAM
ALPHA = RFL["alpha_qp"]


def kink(n, x0, v, sign=1):
    x = n * a
    g = 1 / math.sqrt(1 - v * v)
    th = np.clip(sign * g * (x - x0), -60, 60)
    phi = 4 * np.arctan(np.exp(th))
    dphi = -4 * sign * g * v * np.exp(th) / (1 + np.exp(2 * th))
    return phi, dphi


def run(N, b, v0, T, alpha=ALPHA, dt=0.01, x0_cells=25, snap_every=50):
    n = np.arange(N)
    phi, dphi = kink(n, x0_cells * a, v0)
    snaps, centers, energy = [], [], []

    def acc(p, dp):
        lap = np.empty_like(p)
        lap[1:-1] = p[2:] - 2 * p[1:-1] + p[:-2]
        lap[0] = p[1] - p[0]
        lap[-1] = p[-2] - p[-1]
        return lap / a ** 2 - b * np.sin(p) - alpha * dp

    steps = int(T / dt)
    ac = acc(phi, dphi)
    for s in range(steps):
        phi = phi + dt * dphi + 0.5 * dt * dt * ac
        dhalf = dphi + 0.5 * dt * ac
        ac = acc(phi, dhalf)
        dphi = dhalf + 0.5 * dt * ac
        if s % snap_every == 0:
            snaps.append(phi.copy())
            # fluxon centre = where phi crosses pi (first crossing)
            idx = np.where((phi[:-1] - math.pi) * (phi[1:] - math.pi) <= 0)[0]
            centers.append((s * dt, float(idx[0]) if len(idx) else float("nan")))
            E = np.sum(0.5 * dphi ** 2 + b * (1 - np.cos(phi))) * a + np.sum(0.5 * (np.diff(phi) / a) ** 2) * a
            energy.append(E)
    return np.array(snaps), centers, energy, phi


results = {}
# ---------------- 1. ballistic propagation over the longest line, at the design temperature and at 4.2 K
N1 = RFL["longest_line_cells"]
v0 = 0.6
T1 = (N1 - 60) * a / v0
for label, alpha in (("design_subK", ALPHA), ("at_4K2", RFL["alpha_4K2"])):
    snaps, cen, E, _ = run(N1, np.ones(N1), v0, T1, alpha=alpha)
    ts = np.array([c[0] for c in cen])
    xs = np.array([c[1] for c in cen])
    ok = ~np.isnan(xs)
    vfin = np.polyfit(ts[ok][-len(ts[ok]) // 5:], xs[ok][-len(ts[ok]) // 5:] * a, 1)[0]
    results["ballistic_" + label] = dict(cells=N1, alpha=alpha, launch_v=v0, final_v=round(float(vfin), 4),
                                         energy_retained=round(float(E[-1] / E[0]), 4),
                                         sim_time_ps=round(T1 / WP * 1e12, 1))
    if label == "design_subK":
        snaps1, cen1, E1, vfit = snaps, cen, E, vfin
    else:
        E4 = E
# ---------------- 2. controlled barrier sweep
N2, mid, x0 = 260, 100, 40
sweep = []
bmax = RFL["barrier_bmax"]
t_end = (mid - x0 + 45) * a / v0 * 1.25
for f in np.linspace(0, 0.5, 26):
    b = np.ones(N2)
    b[mid] = bmax * abs(math.cos(math.pi * f))
    _, cen, _, phi = run(N2, b, v0, t_end, x0_cells=x0, snap_every=100)
    pos = int(np.argmax(np.abs(np.diff(phi))))
    state = "transmit" if pos > mid + 3 else ("reflect" if pos < mid - 3 else "pinned")
    sweep.append(dict(phi_ctrl_over_phi0=round(float(f), 3), ic_eff_over_ic=round(float(b[mid]), 3), outcome=state,
                      final_kink_cell=pos))
results["controlled_barrier"] = dict(bmax=bmax, launch_v=v0, sweep=sweep)
switch = [s for s in sweep if s["outcome"] == "transmit"]
results["controlled_barrier"]["transmits_from_phi_ctrl"] = switch[0]["phi_ctrl_over_phi0"] if switch else None

results["parameters"] = dict(Ic_uA=RFL["jj_ic_uA"], L_J_pH=round(LJ * 1e12, 3), cell_L_pH=RFL["cell_L_pH"],
                             Lambda_cells=round(LAM, 3), C_fF=round(C * 1e15, 2),
                             f_plasma_GHz=round(WP / 2 / math.pi / 1e9, 1),
                             lambda_J_um=round(LAM * RFL["cell_pitch_um"], 1),
                             fluxon_speed_um_per_ps=round(v0 * LAM * RFL["cell_pitch_um"] * WP * 1e-12, 3))
os.makedirs(OUT, exist_ok=True)
json.dump(results, open(os.path.join(OUT, "rfl_sim.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in results.items() if k != "controlled_barrier"}, indent=1))
print("barrier:", [(s["phi_ctrl_over_phi0"], s["outcome"]) for s in sweep])

# ---------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 3, figsize=(15, 4.6), dpi=130)
ax[0].imshow(np.sin(snaps1 / 2) ** 2, aspect="auto", origin="lower", cmap="magma",
             extent=[0, N1, 0, T1 / WP * 1e12])
ax[0].set(xlabel="LJJ cell", ylabel="time (ps)", title=f"Ballistic fluxon, {N1} cells (design alpha)")
tt = np.array([c[0] for c in cen1]) / WP * 1e12
ax[1].plot(tt, np.array(E1) / E1[0], color="#c8202a", label=f"alpha = {ALPHA:g} (design, < 1 K)")
ax[1].plot(tt, np.array(E4) / E4[0], color="#888888", label=f"alpha = {RFL['alpha_4K2']:g} (4.2 K)")
ax[1].set(xlabel="time (ps)", ylabel="E / E0", title="Fluxon energy along the line", ylim=(0, 1.05))
ax[1].legend()
fs = [s["phi_ctrl_over_phi0"] for s in sweep]
ax[2].step(fs, [1 if s["outcome"] == "transmit" else 0 for s in sweep], where="mid", color="#2f6bff")
ax[2].set(xlabel="control flux  Phi / Phi0", ylabel="0 = reflect, 1 = transmit",
          title=f"Controlled barrier (SQUID, Ic_max = {bmax} Ic)", yticks=[0, 1])
for a_ in ax:
    a_.grid(alpha=.25)
fig.tight_layout()
os.makedirs(DOCS, exist_ok=True)
fig.savefig(os.path.join(DOCS, "rfl_sim.png"))
