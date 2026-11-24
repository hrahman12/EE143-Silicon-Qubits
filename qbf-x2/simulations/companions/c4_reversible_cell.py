"""Companion device 4 - reversible quantum-fluxon logic cell: gate fidelity together with energy recovery.

1. Energy recovery, simulated on the circuit model (classical/sg.py): after the gate the fluxon enters a braking
   section where a bias current opposes its motion; the fluxon does work on the current source (energy returned to
   the supply) and comes to rest, still carrying its rest energy, ready to be re-launched by reversing the bias.
   Energy flow: kinetic -> source work + radiation + damping, measured from the simulation.
2. Energy budget per CZ operation of QBF-X2 under stated assumptions vs classical baselines (reversible fluxon
   logic gate, RSFQ switching event, Landauer limit). No thermodynamic advantage is claimed from unitarity.
Outputs: figures/companion4_reversible_cell.png, results/companion4_reversible_cell.json
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import plt, save_json, savefig, ROOT, C_IND, C_MIX, C_TH, C_SIM  # noqa: E402
from classical.sg import MultiRailSG, kink, kink_centres, rest_energy_numeric  # noqa: E402
from hardware.params import RailParams, H, PHI0, KB  # noqa: E402

rail = RailParams()
Lam = rail.Lambda
E0 = rest_energy_numeric(Lam)
EJ_J = rail.EJ_GHz * 1e9 * H
res = dict(E0_EJ=E0, EJ_joule=EJ_J)


def braking(beta, L_brake, gamma0, alpha=0.0, N=2400, ramp=None):
    """bias -gamma0 over [x1, x1 + L_brake] (smooth ramp in), fluxon launched at beta from x = 200."""
    n = np.arange(N)
    x1 = 400
    ramp = ramp or max(20, L_brake // 4)
    prof = 0.5 * (np.tanh((n - x1) / ramp) + 1) * (n < x1 + L_brake + 3 * ramp)
    sim = MultiRailSG(N, 1, Lam, alpha=alpha, sponge=60)
    sim.bias = (gamma0 * prof)[:, None]          # opposes a rising (0 -> 2 pi) kink moving to +x
    p, d = kink(n, 200.0, Lam, v=beta * Lam)
    phi, dphi = p[:, None], d[:, None]
    ke0 = E0 * (1 / math.sqrt(1 - beta ** 2) - 1)
    W = 0.0
    rec = []
    dt = 0.05
    T = (x1 + L_brake + 600) / (beta * Lam) * 1.5
    acc = sim.accel(phi, dphi)
    nst = int(T / dt)
    for s in range(nst):
        vh = dphi + 0.5 * dt * acc
        W += -np.sum(sim.bias * vh) * dt                                     # work done BY the fluxon ON the source
        phi = phi + dt * vh
        f = np.einsum("nij,nj->ni", sim.Minv, sim.force(phi))
        dphi = (vh + 0.5 * dt * f) / (1 + 0.5 * dt * sim.alpha[:, None])
        acc = f - sim.alpha[:, None] * dphi
        if s % 50 == 0:
            x = kink_centres(phi[:, 0])[0]
            rec.append((s * dt, x, W))
    x_end = kink_centres(phi[:, 0])[0]
    Wmax = max(r_[2] for r_ in rec)
    # the fluxon stops where the source has absorbed the most; a constant bias then pushes it back and returns the
    # energy (reversible). Capturing it at rest requires switching the bias off at that moment (control, not modelled).
    return dict(beta=beta, L_brake=L_brake, gamma0=gamma0, alpha=alpha, KE0=ke0, work_to_source_max=Wmax,
                efficiency=Wmax / ke0, work_final=W, x_end=x_end, trace=rec)


beta = 0.45
ke0 = E0 * (1 / math.sqrt(1 - beta ** 2) - 1)
# stopping distance for constant force 2 pi gamma0 (force on a fluxon from bias gamma: F = 2 pi gamma E_J/cell)
runs = []
for L_b in (40, 80, 160, 320, 640):
    g0 = ke0 / (2 * math.pi * L_b) * 1.0
    r = braking(beta, L_b, g0)
    runs.append(r)
    print({k: v for k, v in r.items() if k != "trace"})
res["braking"] = [{k: v for k, v in r.items() if k != "trace"} for r in runs]
damp_runs = [braking(beta, 320, ke0 / (2 * math.pi * 320), alpha=a) for a in (1e-6, 1e-5, 1e-4)]
res["braking_damping"] = [{k: v for k, v in r.items() if k != "trace"} for r in damp_runs]

# ---------------------------------------------------------------- energy per operation (assumptions stated)
GHz_J = H * 1e9
E0_J = E0 * EJ_J
KE_J = ke0 * EJ_J
C = json.load(open(os.path.join(ROOT, "results", "A_classical.json")))
rad = max(abs(p["conditional_radiation_EJ"]) for p in C["collision_scan"] if p["coupler"] == "mixed") * EJ_J
I_inj = 2 * rail.Ic_A
budget = {
    "fluxon rest energy (x2, dissipated at detection unless recycled)": 2 * E0_J,
    "fluxon kinetic energy (x2, recoverable by braking)": 2 * KE_J,
    "collision radiation (circuit simulation, worst case)": rad,
    "injection junction switching, I_inj Phi0 (x2, estimate)": 2 * I_inj * PHI0,
    "dispersive (non-latching) readout, ~10 photons at 7 GHz (x2)": 2 * 10 * H * 7e9,
    "latching detector alternative, 1 uA x 0.36 mV x 1 ns (x2)": 2 * 1e-6 * 0.36e-3 * 1e-9,
}
E_rfl_fluxon = 8 * (50e-6 * PHI0 / (2 * math.pi)) * 3.7
baselines = {
    "QBF-X2 CZ, dispersive readout, no recycling": sum(v for k, v in budget.items() if "latching" not in k),
    "QBF-X2 CZ, dispersive readout, kinetic energy recovered": sum(v for k, v in budget.items() if "latching" not in k and "kinetic" not in k),
    "QBF-X2 CZ, latching detectors": sum(v for k, v in budget.items() if "dispersive" not in k),
    "classical reversible fluxon gate (3 % of a 50 uA, Lambda 3.7 fluxon)": 0.03 * E_rfl_fluxon,
    "RSFQ switching event (I_c Phi0, I_c = 100 uA)": 100e-6 * PHI0,
    "Landauer limit kT ln2 at 20 mK": KB * 0.02 * math.log(2),
}
res["energy_per_operation_J"] = dict(components=budget, comparison=baselines,
                                     notes="estimates; control electronics, refrigeration and amplifiers excluded for every entry")
for k, v in baselines.items():
    print(f"{v:.2e} J  {k}")

fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.0))
for r in runs:
    t, x, W = zip(*r["trace"])
    ax[0].plot(np.array(t), np.array(W) / r["KE0"], label=f"braking length {r['L_brake']} cells")
ax[0].set(xlabel="time (1/omega_p)", ylabel="energy returned to the bias source / initial KE",
          title=f"(a) Regenerative braking of a fluxon (beta = {beta})")
ax[0].text(0.02, 0.02, "peak = fluxon at rest; a constant bias then pushes it back\nand returns the energy (reversible). Capture = bias off at the peak.",
           transform=ax[0].transAxes, fontsize=7)
ax[0].legend(fontsize=7.5)
ax[1].semilogx([r["L_brake"] for r in runs], [r["efficiency"] for r in runs], "o-", color=C_MIX, label="alpha = 0")
ax[1].semilogx([320] * 3, [r["efficiency"] for r in damp_runs], "s", color=C_IND, label="alpha = 1e-6, 1e-5, 1e-4 (320 cells)")
ax[1].set(xlabel="braking-section length (cells)", ylabel="kinetic energy recovered", title="(b) Recovery efficiency")
ax[1].set_xticks([40, 80, 160, 320, 640])
ax[1].set_xticklabels(["40", "80", "160", "320", "640"])
ax[1].minorticks_off()
ax[1].legend(fontsize=7.5)
names = list(baselines.keys())
ax[2].barh(range(len(names)), [baselines[k] for k in names], color=[C_MIX, C_MIX, C_MIX, C_TH, C_IND, "k"])
ax[2].set_yticks(range(len(names)))
ax[2].set_yticklabels([n.replace(", ", ",\n", 1) for n in names], fontsize=6.5)
ax[2].set_xscale("log")
ax[2].set(xlabel="energy per operation (J)", title="(c) Energy per operation (on-chip, estimates)")
savefig(fig, "companion4_reversible_cell.png")
res["verdict"] = ("Simulated, not measured: a collision CZ whose fluxons keep >99.99 % of their kinetic energy through the "
                  "gate, and a braking section that returns most of that kinetic energy to the bias supply. The per-gate "
                  "on-chip energy (~1e-21 J with dispersive readout) is set by creating and destroying two fluxons; "
                  "recycling the rest energy needs fluxon storage and re-launch, not demonstrated here. Unitarity alone "
                  "is not a thermodynamic advantage: measurement, reset and control dominate any real energy budget.")
save_json("companion4_reversible_cell.json", res)
print("done")
