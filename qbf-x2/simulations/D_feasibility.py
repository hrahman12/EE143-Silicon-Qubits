"""Milestone D - device feasibility: preliminary chip design, energy accounting and an experimentally testable plan.

D1 architecture at the optimised, 2D-calibrated operating point (results/C_gate.json) with the beam splitter of
   companion 2; complete netlist, unit-cell schematic, preliminary layout (circuits/)
D2 energy retention and dissipation of the collision gate on the circuit model (figure 10)
D3 coherence and fabrication constraints: flight time, disorder budget, damping; the launcher study
   (simulations/D_launcher.py -> results/D_launcher.json) supplies the launch speed spread, timing and the gate
   run with launched wavepackets
D4 layout verification: DRC and EM extraction of the drawn geometry (hardware/extract.py, hardware/drc.py)
D5 milestone-D checks (validated vs proposed vs unresolved, kept separate)
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
print("layout:", {k_: v_ for k_, v_ in dims.items() if k_ != "ports"})

# ---------------------------------------------------------------- D4 layout verification: DRC + EM extraction
from hardware import extract as EX
ver = EX.verify(arch, gds, fast=False, verbose=False)                 # writes circuits/extraction.json, drc_report.json
res["layout_verification"] = dict(passed=ver["passed"], drc_violations=ver["drc"]["violations_total"],
                                  junctions=ver["drc"]["junctions"], summary=ver["summary"],
                                  failed=[c_ for c_ in ver["checks"] if not c_["passed"] and not c_.get("informational")])
print("layout verification:", "PASS" if ver["passed"] else "FAIL", "| DRC violations", ver["drc"]["violations_total"])
pcb_sum_path = os.path.join(ROOT, "pcb", "reports", "check_summary.json")
pcb_sum = json.load(open(pcb_sum_path)) if os.path.exists(pcb_sum_path) else None
drc_txt = os.path.join(ROOT, "pcb", "reports", "drc_report.txt")
pcb_drc_clean = os.path.exists(drc_txt) and all(f"Found 0 {w}" in open(drc_txt).read()
                                                for w in ("DRC violations", "unconnected pads", "Footprint errors"))
die_drc_path = os.path.join(CIRCUITS, "die_drc_report.json")
die_drc = json.load(open(die_drc_path)) if os.path.exists(die_drc_path) else None

# ---------------------------------------------------------------- D2 energy retention through the gate (circuit model)
Lam = arch.rail.Lambda
E0 = rest_energy_numeric(Lam)
N = 1400
n = np.arange(N)
from hardware.params import CouplerParams
env = np.array(CouplerParams(n_plateau=720, n_taper=40).envelope(N, 300))
energy = []


def flight(beta, alpha, cfg, coupled):
    """cfg '11', '10', '01'; returns (kinetic in, kinetic out, dissipated) measured on the lattice, in E_J."""
    cps = [Coupler(0, 1, arch.k, arch.c, env)] if coupled else []
    sim = MultiRailSG(N, 2, Lam, alpha=alpha, couplers=cps)
    v = beta * Lam
    phi, dphi = np.zeros((N, 2)), np.zeros((N, 2))
    if cfg[0] == "1":
        phi[:, 0], dphi[:, 0] = kink(n, 250.0, Lam, v=v)
    if cfg[1] == "1":
        phi[:, 1], dphi[:, 1] = kink(n, 1150.0, Lam, v=-v)
    nk = cfg.count("1")
    e0 = sim.energy(phi, dphi)
    pT, dT, _ = sim.run(phi, dphi, t_end=880 / v, dt=0.05)
    ed = sim.energy_density(pT, dT)
    ek = 0.0
    for r_ in range(2):
        if cfg[r_] == "1":
            x = kink_centres(pT[:, r_])[0]
            ek += ed[int(x) - 20:int(x) + 21, r_].sum()
    return e0 - nk * E0, ek - nk * E0, e0 - sim.energy(pT, dT)


for beta in (0.30, arch.beta):
    for alpha in (0.0, 1e-6, 1e-5, 1e-4):
        kin_f, kout_f, _ = flight(beta, alpha, "11", False)              # free rails: launch transient + damping
        kin1, kout1, _ = flight(beta, alpha, "10", True)                 # single fluxons through the couplers
        kin2, kout2, _ = flight(beta, alpha, "01", True)
        kin, kout, diss = flight(beta, alpha, "11", True)                # the gate
        f_free = kout_f / kin_f
        traversal = (kout_f - (kout1 + kout2)) / kin_f                   # extra loss from passing the couplers
        collision = ((kout1 + kout2) - kout) / kin                       # loss caused by the collision itself
        energy.append(dict(beta=beta, alpha=alpha, kinetic_in_EJ=kin, kinetic_out_EJ=kout, dissipated_EJ=diss,
                           launch_and_flight_loss=1 - f_free, coupler_traversal_loss=traversal, collision_loss=collision,
                           gate_retention=1 - traversal - collision, retention_of_KE_absolute=kout / kin))
        print("energy", {k: round(v_, 6) for k, v_ in energy[-1].items()})
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
    ax[0].semilogx([max(e["alpha"], 1e-7) for e in pts], [e["gate_retention"] for e in pts], "o-", color=col, label=f"gate (couplers + collision), beta = {beta:.2f}")
    ax[0].semilogx([max(e["alpha"], 1e-7) for e in pts], [e["retention_of_KE_absolute"] for e in pts], "s:", color=col, alpha=0.6, label=f"whole flight incl. launch transient + damping")
ax[0].set(xlabel="sub-gap damping alpha (alpha = 0 plotted at 1e-7)", ylabel="kinetic energy retained",
          title="(a) Energy retention through the collision gate")
ax[0].legend(fontsize=8)
pts = [e for e in energy if e["beta"] == arch.beta]
lab = ["launch transient + damping", "coupler traversal", "collision"]
for i, e in enumerate(pts):
    vals = [max(e["launch_and_flight_loss"], 0), max(e["coupler_traversal_loss"], 0), max(e["collision_loss"], 0)]
    bottom = 0
    for j, (vv, c_) in enumerate(zip(vals, (C_TH, C_IND, "#7c3aed"))):
        ax[1].bar(i, vv, bottom=bottom, color=c_, label=lab[j] if i == 0 else None)
        bottom += vv
ax[1].set_yscale("log")
ax[1].set_ylim(1e-6, 1)
ax[1].set_xticks(range(len(pts)))
ax[1].set_xticklabels([f"alpha {e['alpha']:.0e}" for e in pts], fontsize=8)
ax[1].set(ylabel="fraction of kinetic energy lost", title=f"(b) Where the kinetic energy goes (beta = {arch.beta:.2f})")
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
Lr = load_json("D_launcher.json")                                     # launcher study (simulations/D_launcher.py)
ql, cl, tm = Lr["quantum_launch_20mK"], Lr["classical"], Lr["timing"]
s_launch = math.sqrt(ql["dv_over_v"] ** 2 + tm["classical_speed_spread_rel"] ** 2)
n_dual = sum(s_["cells"] for s_ in arch.sections()
             if s_["name"] in ("BS_prep", "gap", "taper_in", "coupler", "taper_out", "BS_analysis"))
for launch, spread in (("thermal source", None), ("launcher", s_launch)):
    for sig in (0.005, 0.01, 0.02):
        for ncell in (150, n_dual, 450):
            b_ = B.budget(model, None, arch.beta, n_cells=ncell, sigma_EJ=sig, sigma_EL=sig, sigma_C=sig,
                          velocity_spread_rel=spread, sigma=ql["sigma_x_at_far"] if spread else 10.0)
            scan_sigma.append(dict(launch=launch, sigma=sig, n_cells=ncell, total=b_["total"], parts=b_["parts"]))
bud_l = Lr["budget_launcher"]
res["constraints"] = dict(flight_time_ns=flight_ns, cells_per_row=arch.n_cells, dual_rail_cells=n_dual,
                          speed_cells_per_ns=v_ns, budget_thermal_source_C=bud, budget_launcher=bud_l,
                          budget_thermal_source_same_geometry=Lr["budget_thermal_source"],
                          launch_speed_spread=dict(launcher=s_launch, thermal_source=ql["thermal_source_spread_20mK"]),
                          disorder_length_scan=scan_sigma,
                          required_for_99pct=[s_ for s_ in scan_sigma if s_["total"] < 0.01])
print("flight", flight_ns, "ns; budget: launcher", bud_l["total"], "thermal source", bud["total"])

# ---------------------------------------------------------------- D4 milestone D
ev = arch.element_values()
checks = [
    ("circuit parameters inside demonstrated fabrication ranges (junction >= 0.01 um^2, C_c >= 0.1 fF, L_s >= 1 pH, granular Al >= 1 square)",
     ev["middle_rail_junction"]["area_um2"] >= 0.01 and ev["rail_junction"]["area_um2"] >= 0.01 and ev["coupler_capacitor"]["C_c_fF"] >= 0.1
     and ev["coupler_shared_inductor"]["L_s_pH"] >= 1 and ev["rail_inductor"]["squares_grAl"] >= 1,
     f"rail JJ {ev['rail_junction']['area_um2']:.3f} um^2, middle JJ {ev['middle_rail_junction']['area_um2']:.3f} um^2, "
     f"C_c {ev['coupler_capacitor']['C_c_fF']:.2f} fF, L_s {ev['coupler_shared_inductor']['L_s_pH']:.1f} pH, grAl {ev['rail_inductor']['squares_grAl']:.2f} sq"),
    ("complete netlist with no floating nodes; every logical row has a launcher (load loop, trap and accelerator flux lines) and a catcher",
     nsum["parse"]["isolated_nodes"] == 0 and nsum["elements"].get("launcher load loop inductor", 0) == 4
     and nsum["elements"].get("trap line source", 0) == 4 and nsum["elements"].get("accelerator line source", 0) == 4
     and nsum["elements"].get("catcher loop inductor", 0) == 4,
     f"{nsum['total_elements']} elements, {nsum['parse']['nodes']} nodes, isolated {nsum['parse']['isolated_nodes']}"),
    ("flight time << coherence times reported for vortex qubits (us range)", flight_ns < 50,
     f"{flight_ns:.2f} ns per pass"),
    ("energy: kinetic energy retained through the gate (couplers + collision) > 99.9 % without damping",
     min(e["gate_retention"] for e in energy if e["alpha"] == 0) > 0.999,
     ", ".join(f"beta {e['beta']:.2f}: gate {e['gate_retention']:.5f} (whole flight incl. launch transient {e['retention_of_KE_absolute']:.5f})"
               for e in energy if e["alpha"] == 0)),
    ("error budget at the optimum < 1 % with 2 % junction disorder, 20 mK launch, 10 ps jitter (realistic assumptions)",
     bud_l["total"] < 0.01,
     f"total {bud_l['total']:.4f} with the modelled launcher (rms dv/v {s_launch:.4f}, {n_dual} dual-rail cells): "
     + ", ".join(f"{k} {v:.1e}" for k, v in bud_l["parts"].items())
     + f"; a thermal-source launch (dv/v {ql['thermal_source_spread_20mK']:.4f}) would give {Lr['budget_thermal_source']['total']:.4f}"),
    ("coherent single-fluxon launcher derived (timing <= 10 ps, thermal-limited speed spread)",
     ql["dv_over_v"] <= ql["thermal_source_spread_20mK"] and tm["relative_jitter_ps"] <= 10.0
     and abs(cl["trimmed"]["winding"] - 1) < 0.01 and abs(cl["trimmed"]["beta"] / arch.beta - 1) < 0.005
     and cl["hold_drift_cells_1ns"] < 0.01 and Lr["gate_with_launched_packets"]["report"]["average_gate_fidelity_CZ"] > 0.999,
     f"flux-bias trap ({arch.launcher.f_trap_GHz:.1f} GHz) + flux-gradient accelerator, no bias taps: quantum launch at 20 mK "
     f"dv/v {ql['dv_over_v']:.4f} (thermal source {ql['thermal_source_spread_20mK']:.4f}), packet {ql['sigma_x_at_far']:.1f} cells; "
     f"circuit: one fluxon (winding {cl['trimmed']['winding']:.4f}), beta {cl['trimmed']['beta']:.4f} after a "
     f"{(cl['accelerator_trim'] - 1) * 100:.1f} % amplitude trim, radiation {cl['trimmed']['radiation_GHz']:.3f} GHz; "
     f"relative timing jitter {tm['relative_jitter_ps']:.1f} ps (assumed {tm['assumed_trigger_jitter_ps']:.0f} ps trigger); "
     f"2D gate with launched packets F_avg {Lr['gate_with_launched_packets']['report']['average_gate_fidelity_CZ']:.6f}"),
    ("layout verified (DRC, EM extraction of k, c, E_S)", ver["passed"],
     f"DRC {ver['drc']['violations_total']} violations ({ver['drc']['junctions']}); extraction: "
     + ", ".join(f"{q_}: {g_['failed']}/{g_['checked']} failed" for q_, g_ in ver["summary"].items())),
    ("die floorplan complete and DRC-clean (10 mm die: pads per circuits/die_pads.json, CPW routing, readout, frame)",
     bool(die_drc) and die_drc.get("violations_total", 1) == 0 and die_drc.get("pads_match_spec", False),
     ("die DRC " + str(die_drc.get("violations_total")) + " violations, pads match spec: " + str(die_drc.get("pads_match_spec")))
     if die_drc else "NOT DONE: die floorplan not built yet"),
    ("carrier PCB: DRC clean, schematic = PCB netlist, 50 ohm +-5 %, A/B timing pairs matched, filter cut-offs met",
     bool(pcb_sum) and pcb_drc_clean and pcb_sum["sch_vs_pcb"]["mismatches"] == 0 and pcb_sum["erc"]["passed"]
     and pcb_sum["impedance"]["passed"] and pcb_sum["lengths"]["passed"]
     and all(ch_["passed"] for ch_ in pcb_sum["filters"]["channels"]),
     (f"pcbnew DRC clean: {pcb_drc_clean}; sch-vs-PCB mismatches {pcb_sum['sch_vs_pcb']['mismatches']} "
      f"({pcb_sum['sch_vs_pcb']['components']} parts, {pcb_sum['sch_vs_pcb']['nets']} nets); "
      f"GCPW {pcb_sum['impedance']['z_formula']:.1f} ohm (formula) / {pcb_sum['impedance']['z_fieldsolver']:.1f} ohm (field solve); "
      f"max A/B skew {max(pp_['dL'] for pp_ in pcb_sum['lengths']['pairs']):.4f} mm") if pcb_sum else "NOT DONE"),
]
res["milestone_D"] = milestone("D (device feasibility)", checks)
res["parameter_status"] = dict(
    validated_by_simulation=["rail E_J, E_C, Lambda (quantum fluxon regime)", f"coupler k = {arch.k:.5f}, c = {arch.c:.4f} at beta = {arch.beta:.2f} (2D calibrated)",
                             "conditional phase pi, sweet spot, reflection < 1e-6", "energy retention through the gate",
                             "coherent launcher: quantum + circuit launch, timing, 2D gate with launched packets (results/D_launcher.json)"],
    validated_by_extraction=["drawn k, c, L, L_s, node capacitances, C_eff of the middle junction, E_S, strays (circuits/extraction.json)",
                             "DRC of the drawn row block (circuits/drc_report.json)"],
    proposed=["granular-Al rail inductors 0.65 nH/cell", "thin-Al shared strip", "AL1/SiNx/AL2 crossover coupling capacitors",
              "middle-rail junctions E_J/E_C,eff = 2 (network-loaded)", "catcher loops with dispersive readout", "dummy couplers",
              "flux-line control (trap / accelerator) with fast edges", "carrier PCB (pcb/)"],
    unknown_or_unresolved=["quasiparticle and dielectric damping alpha at 20 mK (needs <= 1.2e-5)",
                           "material parameters for the extraction (grAl and thin-Al sheet inductance, SiNx thickness): in-situ calibration",
                           "charge stability of beam-splitter islands", "vortex hopping beyond the single-junction phase-slip estimate",
                           "EM simulation of the PCB launches, wire bonds and package modes"])
res["runtime_s"] = time.time() - t0
save_json("D_feasibility.json", res)
print(f"done in {res['runtime_s']:.0f} s")
