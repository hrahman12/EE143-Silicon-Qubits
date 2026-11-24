"""Milestone D - device feasibility: preliminary chip design, energy accounting and an experimentally testable plan.

D1 architecture at the optimised, 2D-calibrated operating point (results/C_gate.json) with the beam splitter of
   companion 2; complete netlist, unit-cell schematic, preliminary layout (circuits/)
D2 energy retention and dissipation of the collision gate on the circuit model (figure 10)
D3 coherence and fabrication constraints: flight time, disorder budget, damping, launcher requirements
D4 milestone-D checks (validated vs proposed vs unresolved, kept separate)
Writes results/D_feasibility.json, circuits/*
"""
import json
import math
import os
import time

import numpy as np

from _common import plt, save_json, load_json, savefig, milestone, ROOT, CIRCUITS, C_IND, C_MIX, C_TH, C_SIM
from classical.sg import MultiRailSG, Coupler, kink, kink_centres, rest_energy_numeric
from hardware.architecture import Architecture
from hardware import netlist as NL
from hardware import layout as LY
from hardware import schematic as SC
from hardware.params import H, PHI0, KB
from quantum.fluxon import FluxonModel
from optimization import budget as B

t0 = time.time()
arch = Architecture.from_results(ROOT)
model = FluxonModel(arch.rail)
res = dict(architecture=arch.summary())
print("architecture:", {k: v for k, v in arch.summary().items() if k not in ("sections", "elements")})

# ---------------------------------------------------------------- D1 netlist, schematic, layout
text, nsum = NL.build(arch)
with open(os.path.join(CIRCUITS, "qbfx2_netlist.cir"), "w") as f:
    f.write(text)
parsed = NL.parse(text)
nsum["parse"] = dict(kinds=parsed["kinds"], nodes=parsed["nodes"], isolated_nodes=len(parsed["isolated"]))
json.dump(nsum, open(os.path.join(CIRCUITS, "netlist_summary.json"), "w"), indent=1)
res["netlist"] = nsum
print("netlist:", nsum["total_elements"], "elements", nsum["parse"])
SC.draw(arch, os.path.join(CIRCUITS, "schematic_unit_cells.png"), os.path.join(CIRCUITS, "schematic_unit_cells.svg"))
gds = os.path.join(CIRCUITS, "qbfx2_layout.gds")
dims = LY.build(arch, gds)
json.dump(dims, open(os.path.join(CIRCUITS, "layout_dimensions.json"), "w"), indent=1)
res["layout"] = dims
p = arch.rail.pitch_um
secs = {d["name"]: d for d in arch.sections()}
LY.preview(gds, os.path.join(CIRCUITS, "layout_overview.png"), size=(2000, 520))
xc = LY.MARGIN + secs["coupler"]["start"] * p
LY.preview(gds, os.path.join(CIRCUITS, "layout_zoom_coupler.png"), box=(xc - 10, LY.MARGIN - 5, xc + 40, dims["height_um"] - LY.MARGIN + 12), size=(1400, 900))
xb = LY.MARGIN + secs["BS_prep"]["start"] * p
LY.preview(gds, os.path.join(CIRCUITS, "layout_zoom_beamsplitter.png"), box=(xb - 10, LY.MARGIN - 5, xb + 40, dims["height_um"] - LY.MARGIN + 12), size=(1400, 900))
print("layout:", dims)

# ---------------------------------------------------------------- D2 energy retention through the gate (circuit model)
Lam = arch.rail.Lambda
E0 = rest_energy_numeric(Lam)
N = 1400
n = np.arange(N)
from hardware.params import CouplerParams
env = np.array(CouplerParams(n_plateau=720, n_taper=40).envelope(N, 300))
energy = []
for beta in (0.30, arch.beta):
    for alpha in (0.0, 1e-6, 1e-5, 1e-4):
        sim = MultiRailSG(N, 2, Lam, alpha=alpha, couplers=[Coupler(0, 1, arch.k, arch.c, env)])
        v = beta * Lam
        phi, dphi = np.zeros((N, 2)), np.zeros((N, 2))
        phi[:, 0], dphi[:, 0] = kink(n, 250.0, Lam, v=v)
        phi[:, 1], dphi[:, 1] = kink(n, 1150.0, Lam, v=-v)
        e0 = sim.energy(phi, dphi)
        pT, dT, _ = sim.run(phi, dphi, t_end=880 / v, dt=0.05)
        ed = sim.energy_density(pT, dT)
        xa, xb = kink_centres(pT[:, 0])[0], kink_centres(pT[:, 1])[0]
        ek = ed[int(xa) - 20:int(xa) + 21, 0].sum() + ed[int(xb) - 20:int(xb) + 21, 1].sum()
        e1 = sim.energy(pT, dT)
        ke0 = 2 * E0 * (1 / math.sqrt(1 - beta ** 2) - 1)
        energy.append(dict(beta=beta, alpha=alpha, E_in_EJ=e0, kinetic_in_EJ=ke0, kinetic_out_EJ=ek - 2 * E0,
                           radiated_EJ=e1 - ek, dissipated_EJ=e0 - e1, retention_of_KE=(ek - 2 * E0) / ke0))
        print("energy", {k: round(vv, 6) for k, vv in energy[-1].items()})
res["energy_retention"] = energy
EJ_J = arch.rail.EJ_GHz * 1e9 * H
try:
    c4 = load_json("companion4_reversible_cell.json")
    per_op = c4["energy_per_operation_J"]["comparison"]
except Exception:
    per_op = {}
fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.9))
for beta, col in ((0.30, C_SIM), (arch.beta, C_MIX)):
    pts = [e for e in energy if e["beta"] == beta]
    ax[0].semilogx([max(e["alpha"], 1e-7) for e in pts], [e["retention_of_KE"] for e in pts], "o-", color=col, label=f"beta = {beta:.2f}")
ax[0].set(xlabel="sub-gap damping alpha (alpha = 0 plotted at 1e-7)", ylabel="kinetic energy retained after the gate",
          title="(a) Energy retention through the collision gate")
ax[0].legend(fontsize=8)
pts = [e for e in energy if e["beta"] == arch.beta]
lab = ["radiated", "dissipated", "kinetic out"]
for i, e in enumerate(pts):
    vals = [max(e["radiated_EJ"], 0), max(e["dissipated_EJ"], 0), e["kinetic_out_EJ"]]
    bottom = 0
    for j, (vv, c_) in enumerate(zip(vals, (C_IND, "#7c3aed", C_MIX))):
        ax[1].bar(i, vv / e["kinetic_in_EJ"], bottom=bottom, color=c_, label=lab[j] if i == 0 else None)
        bottom += vv / e["kinetic_in_EJ"]
ax[1].set_xticks(range(len(pts)))
ax[1].set_xticklabels([f"alpha {e['alpha']:.0e}" for e in pts], fontsize=8)
ax[1].set(ylabel="fraction of incoming kinetic energy", title=f"(b) Where the energy goes (beta = {arch.beta:.2f})")
ax[1].legend(fontsize=8)
if per_op:
    names = list(per_op.keys())
    ax[2].barh(range(len(names)), [per_op[k] for k in names], color=[C_MIX, C_MIX, C_MIX, C_TH, C_IND, "k"][:len(names)])
    ax[2].set_yticks(range(len(names)))
    ax[2].set_yticklabels([nm.replace(", ", ",\n", 1) for nm in names], fontsize=6.5)
    ax[2].set_xscale("log")
    ax[2].set(xlabel="energy per operation (J)", title="(c) Launch, gate and reset costs vs baselines")
savefig(fig, "fig10_energy_budget.png")

# ---------------------------------------------------------------- D3 coherence and fabrication constraints
C = load_json("C_gate.json")
bud = C["optimum_validation"]["budget"]
v_ns = model.v_cells_per_ns(model.k_for_beta(arch.beta))
flight_ns = arch.n_cells / v_ns
scan_sigma = []
for sig in (0.005, 0.01, 0.02):
    for ncell in (150, 300, arch.n_cells):
        b_ = B.budget(model, None, arch.beta, n_cells=ncell, sigma_EJ=sig, sigma_EL=sig, sigma_C=sig)
        scan_sigma.append(dict(sigma=sig, n_cells=ncell, total=b_["total"], parts=b_["parts"]))
res["constraints"] = dict(flight_time_ns=flight_ns, cells_per_row=arch.n_cells, speed_cells_per_ns=v_ns,
                          budget_at_optimum=bud, disorder_length_scan=scan_sigma,
                          required_for_99pct=[s for s in scan_sigma if s["total"] < 0.01])
print("flight", flight_ns, "ns; budget total", bud["total"])

# ---------------------------------------------------------------- D4 milestone D
ev = arch.element_values()
checks = [
    ("circuit parameters inside demonstrated fabrication ranges (junction >= 0.01 um^2, C_c >= 0.1 fF, L_s >= 1 pH, granular Al >= 1 square)",
     ev["middle_rail_junction"]["area_um2"] >= 0.01 and ev["rail_junction"]["area_um2"] >= 0.01 and ev["coupler_capacitor"]["C_c_fF"] >= 0.1
     and ev["coupler_shared_inductor"]["L_s_pH"] >= 1 and ev["rail_inductor"]["squares_grAl"] >= 1,
     f"rail JJ {ev['rail_junction']['area_um2']:.3f} um^2, middle JJ {ev['middle_rail_junction']['area_um2']:.3f} um^2, "
     f"C_c {ev['coupler_capacitor']['C_c_fF']:.2f} fF, L_s {ev['coupler_shared_inductor']['L_s_pH']:.1f} pH, grAl {ev['rail_inductor']['squares_grAl']:.2f} sq"),
    ("complete netlist with no floating nodes; every logical row has an injector and a catcher",
     nsum["parse"]["isolated_nodes"] == 0 and nsum["elements"].get("injector junction", 0) == 4 and nsum["elements"].get("catcher loop inductor", 0) == 4,
     f"{nsum['total_elements']} elements, {nsum['parse']['nodes']} nodes, isolated {nsum['parse']['isolated_nodes']}"),
    ("flight time << coherence times reported for vortex qubits (us range)", flight_ns < 50,
     f"{flight_ns:.2f} ns per pass"),
    ("energy: kinetic energy retained through the gate > 99.9 % without damping", min(e["retention_of_KE"] for e in energy if e["alpha"] == 0) > 0.999,
     ", ".join(f"beta {e['beta']:.2f}: {e['retention_of_KE']:.5f}" for e in energy if e["alpha"] == 0)),
    ("error budget at the optimum < 1 % with 2 % junction disorder, 20 mK launch, 10 ps jitter (realistic assumptions)",
     bud["total"] < 0.01, f"total {bud['total']:.4f}: " + ", ".join(f"{k} {v:.1e}" for k, v in bud["parts"].items())),
    ("coherent single-fluxon launcher derived (timing <= 10 ps, thermal-limited speed spread)", False,
     "UNRESOLVED: injector pulse + accelerator proposed, motional-state preparation not modelled"),
    ("layout verified (DRC, EM extraction of k, c, E_S)", False, "NOT DONE: preliminary layout only"),
]
res["milestone_D"] = milestone("D (device feasibility)", checks)
res["parameter_status"] = dict(
    validated_by_simulation=["rail E_J, E_C, Lambda (quantum fluxon regime)", f"coupler k = {arch.k:.5f}, c = {arch.c:.4f} at beta = {arch.beta:.2f} (2D calibrated)",
                             "conditional phase pi, sweet spot, reflection < 1e-6", "energy retention through the gate"],
    proposed=["granular-Al rail inductors 0.66 nH/cell", "thin-Al shared strip", "crossover coupling capacitors",
              "middle-rail junctions E_J/E_C = 2", "catcher loops with dispersive readout", "dummy couplers"],
    unknown_or_unresolved=["coherent single-fluxon launcher (motional state, timing)", "junction disorder below 1 %",
                           "charge stability of beam-splitter islands", "quasiparticle and dielectric damping alpha at 20 mK",
                           "EM-extracted k, c, E_S of the drawn geometry", "vortex hopping beyond the single-junction phase-slip estimate"])
res["runtime_s"] = time.time() - t0
save_json("D_feasibility.json", res)
print(f"done in {res['runtime_s']:.0f} s")
