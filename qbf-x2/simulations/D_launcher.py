"""Milestone D, launcher study: a coherent single-fluxon launcher (flux-bias trap + flux-gradient accelerator), its
quantum and classical simulation, the timing budget, and the collision gate run with the launched wavepackets.

L1 design (hardware/launcher.py): trap frequency, depth, accelerator force, switch-off time, control-line targets
L2 quantum launch at 20 mK: thermal mixture of trap eigenstates -> launched wavepacket, rms dv/v, length
L3 dependence on temperature and on the switching edge (vs a launch from a thermal source)
L4 full classical circuit: hold, launch, final speed, radiation, one fluxon; timing sensitivities; switching-only
   radiation; trimming of the accelerator amplitude to the target speed
L5 timing jitter budget (assumed trigger and amplitude noise) and loading time (intrinsic damping)
L6 exact 2D collision of two launched wavepackets on the calibrated finite coupler (gate metrics)
L7 error budget with the launcher's speed spread and packet length, against the thermal-source budget
Writes results/D_launcher.json and figures/fig11_launcher.png.
"""
import math
import time

import numpy as np

from _common import plt, save_json, load_json, savefig, ROOT, C_IND, C_MIX, C_TH, C_SIM
from hardware.params import RailParams, CouplerParams
from hardware.architecture import Architecture
from hardware.launcher import design, potential
from quantum.fluxon import FluxonModel
from scattering.launch import quantum_launch, classical_launch
from scattering.collide import run_collision_states
from gates.metrics import gram_from_overlap, gate_report
from optimization import budget as B

t0 = time.time()
arch = Architecture.from_results(ROOT)
rail = arch.rail
model = FluxonModel(rail)
BETA = arch.beta
d = arch.launcher
res = dict(design=d.summary())
print("design:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.summary().items() if k != "notes"})
print("notes:", {k: round(v, 4) for k, v in d.notes.items()})

# ---------------------------------------------------------------- L2 quantum launch at 20 mK
secs = {s["name"]: s for s in arch.sections()}
x_coupler = secs["coupler"]["start"] + secs["coupler"]["cells"] / 2          # rail coordinate of the coupler centre
X_START_2D = 150.0                                                         # packets start 150 cells from the centre
q = quantum_launch(d, model, T_K=0.020, n_states=2, x_ref=x_coupler - X_START_2D, x_far=x_coupler)
thermal_src = model.thermal_beta_spread(BETA, 0.020)
res["quantum_launch_20mK"] = {k: v for k, v in q.items() if k not in ("x", "psi_ref", "trap_states")}
res["quantum_launch_20mK"]["thermal_source_spread_20mK"] = thermal_src
print(f"quantum launch 20 mK: beta {q['beta_mean']:.4f}, dv/v {q['dv_over_v']:.5f} (thermal source {thermal_src:.4f}), "
      f"sigma_x {q['sigma_x_at_ref']:.2f} -> {q['sigma_x_at_far']:.2f} cells, weights {q['thermal_weights']}")

# ---------------------------------------------------------------- L3 temperature and edge-time dependence
tscan = []
for T in (0.010, 0.020, 0.050, 0.100):
    r_ = quantum_launch(d, model, T_K=T, n_states=4, x_ref=x_coupler - X_START_2D, x_far=x_coupler, keep=False)
    tscan.append(dict(T_K=T, dv_over_v=r_["dv_over_v"], thermal_source=model.thermal_beta_spread(BETA, T),
                      weights=r_["thermal_weights"]))
    print("T", T, "launcher", round(r_["dv_over_v"], 5), "thermal source", round(tscan[-1]["thermal_source"], 5))
res["temperature_scan"] = tscan
escan = []
for tau in (0.0, 20.0, 50.0, 100.0):
    dd = design(model, BETA, tau_ps=tau)
    r_ = quantum_launch(dd, model, T_K=0.020, n_states=1, x_ref=x_coupler - X_START_2D, x_far=x_coupler, keep=False)
    escan.append(dict(tau_ps=tau, dv_over_v=r_["dv_over_v"], beta_mean=r_["beta_mean"], sigma_x=r_["sigma_x_at_ref"]))
    print("tau", tau, {k: round(v, 5) for k, v in escan[-1].items()})
res["edge_time_scan"] = escan

# ---------------------------------------------------------------- L4 classical circuit
hold = classical_launch(d, rail, N=300, hold_only=True)
x_probe = 280.0                                    # past the launcher, reached before the run ends
c0 = classical_launch(d, rail, N=420, x_probe=x_probe)
trim = model.kinetic_energy(BETA) / c0["KE_GHz"]                          # accelerator amplitude trim to the target
c1 = classical_launch(d, rail, N=420, x_probe=x_probe, scale_acc=trim)
sens = {}
for name, kw in (("acc_plus_0p1pct", dict(scale_acc=trim * 1.001)), ("acc_minus_0p1pct", dict(scale_acc=trim * 0.999)),
                 ("tau_10ps", dict(scale_acc=trim, tau_ps=10.0)), ("tau_30ps", dict(scale_acc=trim, tau_ps=30.0)),
                 ("t_off_minus_30ps", dict(scale_acc=trim, t_off_ns=d.t_off_ns - 0.03)),
                 ("t_off_plus_30ps", dict(scale_acc=trim, t_off_ns=d.t_off_ns + 0.03))):
    r_ = classical_launch(d, rail, N=420, x_probe=x_probe, **kw)
    sens[name] = dict(t_arrival_ns=r_["t_arrival_ns"], beta=r_["beta"])
vac = classical_launch(d, rail, N=420, scale_acc=trim, with_kink=False)
dt_dacc = (sens["acc_plus_0p1pct"]["t_arrival_ns"] - sens["acc_minus_0p1pct"]["t_arrival_ns"]) / 0.002   # ns per unit
dbeta_dacc = (sens["acc_plus_0p1pct"]["beta"] - sens["acc_minus_0p1pct"]["beta"]) / 0.002
dt_dtau = (sens["tau_30ps"]["t_arrival_ns"] - sens["tau_10ps"]["t_arrival_ns"]) / 20.0                  # ns per ps
res["classical"] = dict(hold_drift_cells_1ns=hold["drift_cells"],
                        untrimmed=dict(beta=c0["beta"], KE_GHz=c0["KE_GHz"], radiation_GHz=c0["radiation_GHz"],
                                       winding=c0["winding"], t_arrival_ns=c0["t_arrival_ns"]),
                        accelerator_trim=trim,
                        trimmed=dict(beta=c1["beta"], KE_GHz=c1["KE_GHz"], radiation_GHz=c1["radiation_GHz"],
                                     winding=c1["winding"], t_arrival_ns=c1["t_arrival_ns"]),
                        switching_only_radiation_GHz=vac["E_total_GHz"], sensitivities=sens,
                        dt_arrival_per_relative_amplitude_ns=dt_dacc, dbeta_per_relative_amplitude=dbeta_dacc,
                        dt_arrival_per_ps_edge_ns=dt_dtau, x_probe=x_probe,
                        trajectory=dict(t_ns=c1["t_ns"][::8], X=c1["X"][::8]))
print("classical:", {k: v for k, v in res["classical"].items() if k not in ("trajectory", "sensitivities")})

# ---------------------------------------------------------------- L5 timing jitter and loading
TRIG_PS, AMP_REL, EDGE_PS = 2.0, 1e-3, 2.0          # assumptions: trigger jitter, shot-to-shot amplitude, edge spread
j_single = math.sqrt(TRIG_PS ** 2 + (abs(dt_dacc) * AMP_REL * 1e3) ** 2 + (abs(dt_dtau) * EDGE_PS * 1e3) ** 2)
j_rel = math.sqrt(2) * j_single                     # independent A and B launchers
dv_classical = abs(dbeta_dacc) * AMP_REL / BETA     # shot-to-shot speed spread from amplitude noise
alpha = 2e-6
tau_E_us = 1 / (2 * alpha * 2 * math.pi * rail.fp_GHz * 1e9) * 1e6
n_start = abs(d.notes["trap_depth_GHz"]) / (q["trap_energies_GHz"][1] - q["trap_energies_GHz"][0])
nbar = q["thermal_weights"][1] / q["thermal_weights"][0]
t_load_us = tau_E_us * math.log(n_start / max(nbar, 1e-12))
res["timing"] = dict(assumed_trigger_jitter_ps=TRIG_PS, assumed_amplitude_noise_rel=AMP_REL, assumed_edge_spread_ps=EDGE_PS,
                     single_launcher_jitter_ps=j_single, relative_jitter_ps=j_rel, requirement_ps=10.0,
                     classical_speed_spread_rel=dv_classical)
res["loading"] = dict(alpha=alpha, energy_relaxation_time_us=tau_E_us, start_quanta=n_start, thermal_nbar_20mK=nbar,
                      time_to_thermalise_us=t_load_us,
                      method="flux insertion through the rail-end loop (slow ramp), relaxation into the trap by "
                             "intrinsic damping; thermal occupation from the computed trap levels")
print("timing:", res["timing"], "loading:", {k: v for k, v in res["loading"].items() if k != "method"})

# ---------------------------------------------------------------- L6 2D collision of two launched wavepackets
C = load_json("C_gate.json")
cal = C["optimum_validation"]["calibrated"]
cp = CouplerParams(k=cal["k"], c=cal["c"])
W, TT = arch.n_plateau, arch.n_taper
env = lambda xm: np.where(np.abs(xm) <= W / 2, 1.0, np.where(np.abs(xm) <= W / 2 + TT,
                          0.5 * (1 + np.cos(np.pi * (np.abs(xm) - W / 2) / TT)), 0.0))
n2, dx2 = 1024, 0.5
x2 = (np.arange(n2) - n2 // 2) * dx2
x1 = q["x"]
idx = np.rint((x2 + x_coupler - x1[0]) / (x1[1] - x1[0])).astype(int)       # the 2D grid is a subgrid of the 1D one
psiA = q["psi_ref"][idx]
psiB = psiA[::-1].copy()                                                   # mirrored launcher on the B side
psiB = np.roll(psiB, 1)                                                    # x -> -x on the (n/2-centred) grid
g2 = run_collision_states(model, cp, psiA, psiB, n=n2, dx=dx2, dt=0.002, envelope=env)
Gl = gram_from_overlap(g2["omega"], g2["p11"])
rep = gate_report(Gl)
res["gate_with_launched_packets"] = dict(coupler=dict(k=cp.k, c=cp.c, plateau=W, taper=TT),
                                        **{k: (v if not isinstance(v, complex) else dict(re=v.real, im=v.imag))
                                           for k, v in g2.items() if k not in ("schmidt_top",)},
                                        report=rep)
print("2D gate with launched packets:", {k: (round(v, 7) if isinstance(v, float) else v) for k, v in rep.items()
                                          if isinstance(v, (float, int))}, "phase", round(g2["phase"], 5),
      "|omega|", round(g2["overlap_abs"], 7), "reflection", g2["reflection"], "drift", g2["norm_drift"])

# ---------------------------------------------------------------- L7 error budget: launcher vs thermal source
s_total = math.sqrt(q["dv_over_v"] ** 2 + dv_classical ** 2)
n_dual = sum(s["cells"] for s in arch.sections()
             if s["name"] in ("BS_prep", "gap", "taper_in", "coupler", "taper_out", "BS_analysis"))
b_launch = B.budget(model, None, BETA, n_cells=n_dual, velocity_spread_rel=s_total, sigma=q["sigma_x_at_far"],
                    plateau=W, taper=TT, jitter_ps=10.0)
b_thermal = B.budget(model, None, BETA, n_cells=n_dual, plateau=W, taper=TT, jitter_ps=10.0)
gate_motional = 1 - rep["average_gate_fidelity_CZ"] if "average_gate_fidelity_CZ" in rep else 0.0
b_launch["parts"]["launched_packet_2D"] = max(gate_motional, 0.0)            # exact 2D gate error with these packets
b_launch["total"] = sum(b_launch["parts"].values())
res["budget_launcher"] = b_launch
res["budget_thermal_source"] = b_thermal
res["budget_assumptions"] = (f"{n_dual} dual-rail cells per rail, 2 % E_J/E_L/C disorder, 20 mK, alpha 2e-6, 10 ps jitter, "
                             f"{W}-cell plateau with {TT}-cell tapers; speed spread {s_total:.4f} (launcher, quantum + "
                             f"classical amplitude noise) vs {b_thermal['velocity_spread_rel']:.4f} (thermal source)")
print("budget launcher:", round(b_launch["total"], 5), {k: f"{v:.2e}" for k, v in b_launch["parts"].items()})
print("budget thermal source:", round(b_thermal["total"], 5))

# ---------------------------------------------------------------- figure
fig, ax = plt.subplots(2, 3, figsize=(14.5, 7.6))
a = ax[0, 0]
X = np.linspace(0, d.x_d + 20, 1200)
N_ = int(d.x_d) + 25
a.plot(X, potential(d.theta_trap_profile(N_), X, rail), color=C_IND, label="trap (hold)")
a.plot(X, potential(d.theta_acc_profile(N_), X, rail), color=C_MIX, label="accelerator (after release)")
a.axvline(d.X0, color="k", lw=0.6, ls=":")
a.set(xlabel="fluxon position X (cells)", ylabel="U(X) (GHz)", title="(a) Launcher potentials from the control lines")
a.legend(fontsize=8)
a = ax[0, 1]
kk = np.fft.fftfreq(len(q["x"]), q["x"][1] - q["x"][0]) * 2 * math.pi
pk = np.abs(np.fft.fft(q["psi_ref"])) ** 2
vv = model.v_cells_per_ns(kk)
o = np.argsort(vv)
vm = q["v_mean_cells_per_ns"]
a.plot(vv[o] / vm - 1, pk[o] / pk.max(), color=C_SIM, label=f"launched (quantum), rms {q['dv_over_v'] * 100:.2f} %")
gg = np.linspace(-0.15, 0.15, 400)
a.plot(gg, np.exp(-0.5 * (gg / thermal_src) ** 2), "--", color=C_TH, label=f"thermal source 20 mK, {thermal_src * 100:.2f} %")
a.set(xlim=(-0.15, 0.15), xlabel="v / <v> - 1", ylabel="probability (normalised)", title="(b) Launch speed distribution")
a.legend(fontsize=8)
a = ax[0, 2]
a.plot([t["T_K"] * 1e3 for t in tscan], [t["dv_over_v"] * 100 for t in tscan], "o-", color=C_SIM, label="launcher (quantum sim)")
a.plot([t["T_K"] * 1e3 for t in tscan], [t["thermal_source"] * 100 for t in tscan], "s--", color=C_TH, label="thermal source")
a.set(xlabel="temperature (mK)", ylabel="rms dv/v (%)", title="(c) Speed spread vs temperature")
a.legend(fontsize=8)
a = ax[1, 0]
tr = res["classical"]["trajectory"]
a.plot(tr["t_ns"], tr["X"], color=C_MIX)
a.axvline(0, color="k", lw=0.6, ls=":")
a.axvline(d.t_off_ns, color="k", lw=0.6, ls="--")
a.set(xlabel="time after release (ns)", ylabel="kink centre (cells)",
      title=f"(d) Full circuit: beta {c1['beta']:.4f}, radiation {c1['radiation_GHz']:.3f} GHz")
a = ax[1, 1]
ref = C["optimum_validation"]["gate_pure"]
keys = [("concurrence", True), ("bell_fidelity", True), ("average_gate_fidelity_CZ", True), ("leakage", False)]
labs = ["1 - concurrence", "1 - Bell fidelity", "1 - F_avg (CZ)", "leakage"]
val = lambda r_, k_, inv: max((1 - r_[k_]) if inv else r_[k_], 1e-10)
xs = np.arange(len(keys))
a.bar(xs - 0.2, [val(ref, k_, inv) for k_, inv in keys], 0.4, color=C_TH, label="Gaussian packets (sigma 10), uniform coupler (C)")
a.bar(xs + 0.2, [val(rep, k_, inv) for k_, inv in keys], 0.4, color=C_SIM, label=f"launched packets, finite coupler ({W}+2x{TT} cells)")
a.set_yscale("log")
a.set_ylim(1e-10, 1e-4)
a.set_xticks(xs)
a.set_xticklabels(labs, fontsize=7.5)
a.set(ylabel="error", title=f"(e) Exact 2D gate: Delta = {abs(g2['phase']):.5f} rad with launched packets")
a.legend(fontsize=7)
a = ax[1, 2]
names = ["disorder_dephasing", "damping", "gate_thermal", "timing"]
xs = np.arange(len(names))
a.bar(xs - 0.2, [max(b_thermal["parts"][n_], 1e-9) for n_ in names], 0.4, color=C_TH, label=f"thermal source: {b_thermal['total'] * 100:.2f} %")
a.bar(xs + 0.2, [max(b_launch["parts"][n_], 1e-9) for n_ in names], 0.4, color=C_SIM, label=f"launcher: {b_launch['total'] * 100:.2f} %")
a.set_yscale("log")
a.set_ylim(1e-9, 0.1)
a.set_xticks(xs)
a.set_xticklabels(["disorder", "damping", "thermal gate", "timing"], fontsize=8)
a.set(ylabel="CZ infidelity", title="(f) Error budget (2 % disorder, 20 mK, 10 ps)")
a.legend(fontsize=8)
savefig(fig, "fig11_launcher.png")

res["runtime_s"] = time.time() - t0
save_json("D_launcher.json", res)
print(f"done in {res['runtime_s']:.0f} s")
