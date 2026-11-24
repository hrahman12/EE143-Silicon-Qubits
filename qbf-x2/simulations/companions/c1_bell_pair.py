"""Companion device 1 - quantum vortex Bell-pair chip: entangle two independently controlled vortex qubits.

Uses the QFX-1 chip of this repository (quantum_chip/): two quantum-fluxon (Josephson-vortex) qubits, each a single
vortex in the double well of a 24-junction ring, at the double sweet spot f01 = 3.208 GHz, f12 = 17.19 GHz, coupled
by a shared bus inductance L_s: H_c = L_s I_1 I_2, J = L_s dI^2/4 (dI = 100 nA, from quantum_chip/out/qfx_sim.json).
Protocol (QuTiP master equation, 3 levels per qubit, RWA in the frame of qubit 1):
  idle: qubit 2 parked at barrier flux Phi_b (detuned, coupling effectively off)
  pi pulse on qubit 1 -> |10>;  flux step of qubit 2 into resonance for t = 1/(8 J) -> (|10> - i|01>)/sqrt2;  park.
Decoherence: T1 (assumed range), pure dephasing of qubit 2 while parked off its sweet spot from 1/f flux noise.
Outputs: figures/companion1_bell_pair.png, results/companion1_bell_pair.json
"""
import json
import math
import os
import sys

import numpy as np
import qutip as qt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import plt, save_json, savefig, ROOT, C_IND, C_MIX, C_TH, C_SIM  # noqa: E402

QFX = json.load(open(os.path.join(ROOT, "..", "quantum_chip", "out", "qfx_sim.json")))
op = QFX["operating_point"]
f01, f12 = op["f01_GHz"], op["f12_GHz"]
dI_nA = abs(QFX["coupling"]["delta_I_nA"])
J_per_pH = QFX["coupling"]["J_zz_MHz_vs_shared_L_pH"]["1"] * 1e-3            # GHz per pH
g12_ratio = abs(QFX["tilt"]["G12_GHz_per_Phi0"] / QFX["tilt"]["G01_GHz_per_Phi0"])
sweep = QFX["barrier_sweep"]
L_s = 5.0                                                                       # pH (proposed bus inductance)
J = J_per_pH * L_s
STAGGER = 0.40                                                                  # GHz: QF1 designed 0.4 GHz above QF2
f1 = f01 + STAGGER                                                              # QF1 at ITS sweet spot (smaller barrier JJ)
fs, phis = [s["f01_GHz"] for s in sweep], [s["phi_b"] for s in sweep]
PULSE = float(np.interp(f1, fs, phis))                                          # QF2 flux that reaches f1
slope = (np.interp(PULSE + 0.005, phis, fs) - np.interp(PULSE - 0.005, phis, fs)) / 0.01
A_flux = 2e-6                                                                   # Phi0 / sqrt(Hz), typical 1/f amplitude
Gphi_pulse = 2 * math.pi * abs(slope) * 1e9 * A_flux * math.sqrt(2 * math.log(1e6 / 1.0))   # 1/s (1 Hz - 1 MHz band)
res = dict(f01_QF2=f01, f01_QF1=f1, f12=f12, J_GHz=J, L_s_pH=L_s, stagger_GHz=STAGGER, QF2_pulse_flux=PULSE,
           slope_at_pulse_GHz_per_Phi0=slope, Gamma_phi_during_pulse_per_s=Gphi_pulse, g12_over_g01=g12_ratio,
           note="both qubits idle at their own double sweet spots (first-order flux-insensitive); QF2 leaves its "
                "sweet spot only during the 6.6 ns resonant exchange pulse")
print(res)

N = 3
a = qt.destroy(N)
I3 = qt.qeye(N)
Iop = qt.Qobj(np.array([[0, 1, 0], [1, 0, g12_ratio], [0, g12_ratio, 0]], complex))     # current, units dI/2
n1, n2 = qt.tensor(a.dag() * a, I3), qt.tensor(I3, a.dag() * a)
P2 = qt.Qobj(np.diag([0, 0, 1.0]))


def hamiltonian(delta2_t, omega_t, tlist):
    """frame rotating at f1 (QF1) on both qubits; RWA keeps only excitation-conserving coupling terms."""
    H0 = 2 * math.pi * (f12 - f01) * (qt.tensor(P2, I3) + qt.tensor(I3, P2))
    up = qt.Qobj(np.triu(Iop.full()))          # raising part of the current operator
    Hc = 2 * math.pi * J * (qt.tensor(up, up.dag()) + qt.tensor(up.dag(), up))
    Hd = 2 * math.pi * 0.5 * qt.tensor(a + a.dag(), I3)
    return [H0 + Hc, [2 * math.pi * n2, qt.coefficient(delta2_t, tlist=tlist)], [Hd, qt.coefficient(omega_t, tlist=tlist)]]


def protocol(T1_us, dt=0.02):
    t_pi, t_gap, t_swap = 20.0, 5.0, 1 / (8 * J)
    T = t_pi + t_gap + t_swap + 2 * t_gap + 20.0
    tl = np.arange(0, T, dt)
    sig = t_pi / 5
    om = np.exp(-0.5 * ((tl - t_pi / 2) / sig) ** 2)
    om *= 0.5 / (np.sum(om) * dt)                                  # area: Omega * t = 1/2 -> pi rotation
    t_on = t_pi + t_gap
    ramp = 0.5 * (np.tanh((tl - t_on) / 0.3) - np.tanh((tl - t_on - t_swap) / 0.3))
    d2 = -STAGGER * (1 - ramp)                                     # QF2 at its sweet spot except during the pulse
    gphi = np.sqrt(2 * Gphi_pulse * 1e-9 * ramp + 1e-30)
    cops = [math.sqrt(1 / (T1_us * 1e3)) * qt.tensor(a, I3), math.sqrt(1 / (T1_us * 1e3)) * qt.tensor(I3, a),
            [n2, qt.coefficient(gphi, tlist=tl)]]
    psi0 = qt.tensor(qt.basis(N, 0), qt.basis(N, 0))
    out = qt.mesolve(hamiltonian(d2, om, tl), psi0 * psi0.dag(), tl, c_ops=cops, options={"max_step": 0.05})
    return tl, out.states, t_on, t_swap


def two_qubit(rho):
    full = rho.full()
    idx = [0, 1, 3, 4]                                             # |00>,|01>,|10>,|11> in the 3x3 basis
    r = full[np.ix_(idx, idx)]
    return r


def metrics(rho2):
    pr = np.real(np.trace(rho2))
    best = 0
    for phi in np.linspace(0, 2 * math.pi, 181):
        tgt = np.array([0, np.exp(1j * phi), 1, 0]) / math.sqrt(2)
        best = max(best, float(np.real(tgt.conj() @ rho2 @ tgt)))
    C = float(qt.concurrence(qt.Qobj(rho2 / pr, dims=[[2, 2], [2, 2]])))
    return best, C, 1 - pr


rows = []
traces = {}
for T1 in (5.0, 20.0, 100.0, 1e6):
    tl, states, t_on, t_sw = protocol(T1)
    F = [metrics(two_qubit(s)) for s in states[::10]]
    traces[T1] = (tl[::10], F)
    Ff, Cf, leak = metrics(two_qubit(states[-1]))
    rows.append(dict(T1_us=T1, bell_fidelity=Ff, concurrence=Cf, leakage=leak, t_swap_ns=t_sw))
    print(rows[-1])
res["results"] = rows
res["protocol_ns"] = dict(pi_pulse=20.0, swap=1 / (8 * J))
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.8))
for T1, (tl, F) in traces.items():
    lab = "no decay" if T1 > 1e5 else f"T1 = {T1:g} us"
    ax[0].plot(tl, [f[1] for f in F], label=lab)
ax[0].axvspan(25, 25 + 1 / (8 * J), color=C_MIX, alpha=0.08)
ax[0].set(xlabel="time (ns)", ylabel="concurrence", title=f"(a) Two vortex qubits (QFX-1), J = {J * 1e3:.0f} MHz (L_s = {L_s:g} pH)")
ax[0].legend(fontsize=8)
ax[1].bar([("no decay" if r["T1_us"] > 1e5 else f"T1 {r['T1_us']:g} us") for r in rows], [1 - r["bell_fidelity"] for r in rows], color=C_MIX)
ax[1].set_yscale("log")
ax[1].set(ylabel="1 - Bell-state fidelity", title="(b) Bell-pair error (flux-pulse dephasing included)")
savefig(fig, "companion1_bell_pair.png")
res["verdict"] = ("Simulated Bell pair between two independently addressed quantum-fluxon (Josephson-vortex) qubits of the "
                  "QFX-1 design. Prior art: single vortex qubits (KIT 2023; grAl vortex qubits, Nambisan et al. Nature 2026 "
                  "with estimated 10-100 MHz vortex-vortex coupling); an addressable entangled two-vortex processor was not "
                  "found in the searched literature. T1 values are assumptions bracketing the reported range.")
save_json("companion1_bell_pair.json", res)
print("done")
