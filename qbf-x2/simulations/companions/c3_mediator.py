"""Companion device 3 - reusable fluxon quantum gate: can ONE passing fluxon entangle two stationary qubits and
leave them, disentangled, to be reused?

Model: a mediator fluxon (coordinate x, relativistic E(k)) passes two stationary qubits that shift its energy
dispersively, U_s(x) = s1 w1(x) + s2 w2(x), s_i = +-1 (qubit Z eigenvalues; this is the coupling of the QFX-1
fluxon-kick gate, linear in each qubit's Z). For each of the four qubit basis states the mediator scatters off
U_s; its outgoing states chi_s give the two-qubit channel G[s, s'] = <chi_s'|chi_s> (mediator traced out).
Because U_s is linear in s, a conditional phase can only come from the nonlinearity of scattering in U
(second order, needs w1 w2 to overlap); the first-order single-qubit phases leave which-qubit information in the
mediator's timing unless it is heavy. We compute both, exactly, for a light (QBF-X2 rail) and a heavy (QFX-1
kick line) mediator, for separated and overlapping coupling regions.
Outputs: figures/companion3_mediator.png, results/companion3_mediator.json
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import plt, save_json, savefig, C_IND, C_MIX, C_TH, C_SIM  # noqa: E402
from hardware.params import RailParams  # noqa: E402
from quantum.fluxon import FluxonModel  # noqa: E402
from gates.metrics import gate_report  # noqa: E402

light = FluxonModel(RailParams())
heavy = FluxonModel(RailParams(EJ_GHz=9934.0, EC_GHz=0.03228, Lambda=2.68), E0_GHz=213096.5)   # QFX-1 kick line
res = {}


def branch_states(model, beta, theta, overlap, L=120.0, sigma=15.0, n=16384, dx=0.25):
    """single-qubit kick phase theta per region (first order); overlap = 0 separated, 1 fully overlapping."""
    x = (np.arange(n) - n // 2) * dx
    k0 = model.k_for_beta(beta)
    q = 2 * math.pi * np.fft.fftfreq(n, dx)
    E = model.energy(k0 + q)                      # envelope representation psi = exp(i k0 x) phi(x): exact for any k0
    v = model.v_cells_per_ns(k0)
    w = lambda c: 0.5 * (np.tanh((x - c + L / 2) / 8) - np.tanh((x - c - L / 2) / 8))
    c1, c2 = -(1 - overlap) * (L / 2 + 20), (1 - overlap) * (L / 2 + 20)
    amp = theta * v / (2 * math.pi * np.trapezoid(w(0), x))     # GHz: theta = 2 pi int w dx / v
    W1, W2 = amp * w(c1), amp * w(c2)
    psi0 = (2 * math.pi * sigma ** 2) ** -0.25 * np.exp(-(x + 1200) ** 2 / (4 * sigma ** 2)) + 0j
    T = 2400 / v
    dt = min(0.004, 0.02 / max(amp, 1e-9))
    nst = int(T / dt)
    kin = np.exp(-1j * 2 * math.pi * E * dt)
    states = []
    for s1, s2 in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        U = s1 * W1 + s2 * W2
        half = np.exp(-1j * 2 * math.pi * U * dt / 2)
        p = psi0.copy()
        for _ in range(nst):
            p = half * np.fft.ifft(kin * np.fft.fft(half * p))
        states.append(p)
    free = np.fft.ifft(np.exp(-1j * 2 * math.pi * E * nst * dt) * np.fft.fft(psi0))
    return states, free, dx


def channel(states, dx):
    # order |00>,|01>,|10>,|11>  <->  s = (+1,+1), (+1,-1), (-1,+1), (-1,-1)
    G = np.array([[np.vdot(states[y], states[x]) * dx for y in range(4)] for x in range(4)])
    return G


rows = []
for name, model, beta in (("light quantum fluxon (QBF-X2 rail)", light, 0.45), ("heavy classical fluxon (QFX-1 kick line)", heavy, 0.05)):
    for overlap in (0.0, 1.0):
        for theta in (math.pi / 4, math.pi / 2, math.pi):
            st, free, dx = branch_states(model, beta, theta, overlap)
            G = channel(st, dx)
            rep = gate_report(G)
            ph = [np.angle(np.vdot(free, s) * dx) for s in st]
            delta_med = (ph[0] - ph[1] - ph[2] + ph[3] + math.pi) % (2 * math.pi) - math.pi
            rows.append(dict(mediator=name, beta=beta, overlap=overlap, theta=theta, conditional_phase=delta_med,
                             concurrence=rep["concurrence"], cz_avg_fidelity=rep["average_gate_fidelity_CZ"],
                             coherence_single_qubit=float(abs(G[0, 2])), logical_purity=rep["logical_purity"]))
            print(rows[-1])
res["scan"] = rows
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
for (name, ov), mk in zip([(r["mediator"], r["overlap"]) for r in rows[::3]], ["o", "s", "^", "D"]):
    pts = [r for r in rows if r["mediator"] == name and r["overlap"] == ov]
    lab = f"{name.split(' (')[0]}, {'overlapping' if ov else 'separated'}"
    ax[0].plot([p["theta"] for p in pts], [abs(p["conditional_phase"]) for p in pts], mk + "-", label=lab)
    ax[1].plot([p["theta"] for p in pts], [p["coherence_single_qubit"] for p in pts], mk + "-", label=lab)
    ax[2].plot([p["theta"] for p in pts], [p["concurrence"] for p in pts], mk + "-", label=lab)
ax[0].set(xlabel="single-qubit kick phase per region (rad)", ylabel="|conditional phase| (rad)", yscale="log",
          title="(a) Mediated conditional phase")
ax[1].set(xlabel="single-qubit kick phase per region (rad)", ylabel="qubit coherence after the pass", title="(b) Which-qubit information left in the mediator")
ax[2].set(xlabel="single-qubit kick phase per region (rad)", ylabel="concurrence from |+>|+>", title="(c) Entanglement delivered")
for a in ax:
    a.legend(fontsize=7)
savefig(fig, "companion3_mediator.png")
best = max(rows, key=lambda r: r["concurrence"])
res["best"] = best
res["verdict"] = ("Negative result (as modelled): with couplings linear in each qubit's Z, a single passing fluxon gives a "
                  "conditional phase only at second order and only where the two coupling regions overlap. A light mediator "
                  "carries away which-qubit timing information that destroys the coherence it would entangle; a heavy one "
                  f"keeps coherence but delivers a negligible conditional phase. Best concurrence found: {best['concurrence']:.3f} "
                  f"({best['mediator']}, overlap {best['overlap']}, theta {best['theta']:.2f}). A reusable entangler needs a "
                  "coupling nonlinear in the qubit operators, a velocity-compensated (sweet-spot) mediator coupling, or a "
                  "mediator that is itself a qubit - which is what the QBF-X2 collision gate does.")
save_json("companion3_mediator.json", res)
print("done")
