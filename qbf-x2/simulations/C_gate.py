"""Milestone C - a genuine entangling gate from the collision, its optimisation and robustness.

C1 calibrate the coupler (k, c) on the exact 2D quantum model: Delta(beta*) = pi and dDelta/dbeta = 0
C2 logical two-qubit metrics for |+>|+> (concurrence, entropy, Bell fidelity, CZ process fidelity, leakage,
   distinguishability, motional vs logical entanglement); control run with the coupler off
C3 thermal launch spread: sweet-spot coupler vs inductive-only coupler; two-velocity validation of the phase model
C4/C5 conditional phase and concurrence vs coupling strength (figures 5, 6)
C6 gate fidelity vs launch-timing mismatch on a finite coupler (figure 7)
C7 sensitivity to temperature, velocity mismatch, coupler errors, junction disorder, damping (figure 8)
C8 operating-point optimisation with the full error budget; circuit + 2D validation at the optimum
Writes results/C_gate.json
"""
import math
import time

import numpy as np

from _common import plt, save_json, load_json, savefig, milestone, C_IND, C_MIX, C_TH, C_SIM
from classical import exact
from classical.sg import MultiRailSG, Coupler, kink, kink_centres
from hardware.params import RailParams, CouplerParams, phase_prefactor
from quantum.fluxon import FluxonModel
from scattering.collide import run_collision
from scattering import eikonal
from gates.metrics import gram_from_overlap, gate_report, logical_rho, concurrence
from optimization import budget as B

t_start = time.time()
rail = RailParams()
model = FluxonModel(rail)
GAM = phase_prefactor(rail)
res = {}


def pos(ph):
    return ph % (2 * math.pi)


def kt_to_k(kt):
    return (-1 + math.sqrt(1 + 4 * kt * kt)) / (2 * kt) if kt > 0 else 0.0


def calibrate(beta, k, c, dbeta=0.02, iters=2, **kw):
    """Newton on (k~, c) with the first-order Jacobian; function values from exact 2D scattering."""
    hist = []
    kt = exact.ktilde(k)
    for it in range(iters + 1):
        cp = CouplerParams(k=kt_to_k(kt), c=c)
        ph = [pos(run_collision(model, cp, b, **kw)["phase"]) for b in (beta - dbeta, beta, beta + dbeta)]
        F1, F2 = ph[1] - math.pi, (ph[2] - ph[0]) / (2 * dbeta)
        hist.append(dict(iteration=it, k=cp.k, c=c, phase=ph[1], dphase_dbeta=F2, phases=ph))
        print("calibration", hist[-1], flush=True)
        if it == iters:
            break
        J = np.array([[GAM / beta, GAM * beta], [-GAM / beta ** 2, GAM]])
        dkt, dc = np.linalg.solve(J, [-F1, -F2])
        kt, c = kt + dkt, c + dc
    return CouplerParams(k=kt_to_k(kt), c=c), hist


# ---------------------------------------------------------------- C1 calibration at the reference speed
BSTAR = 0.30
k1, c1 = exact.coupler_for(math.pi, BSTAR, rail.Lambda, rail.EJ_over_hfp)
CP, cal_hist = calibrate(BSTAR, k1, c1)
res["calibration_reference"] = dict(beta_star=BSTAR, first_order=dict(k=k1, c=c1), calibrated=dict(k=CP.k, c=CP.c),
                                    history=cal_hist)
k_ind = kt_to_k(math.pi * BSTAR / GAM * (CP.k / k1))           # inductive-only coupler with the same Delta (same scale)
CP_IND = CouplerParams(k=k_ind, c=0.0)

# ---------------------------------------------------------------- C2 gate metrics (pure wavepackets)
run = run_collision(model, CP, BSTAR, sigma=10.0, keep_states=True)
G = gram_from_overlap(run["omega"], run["p11"])
rep = gate_report(G)
rep.update(motional_purity_out=run["motional_purity_out"], motional_purity_in=run["motional_purity_in"],
           reflection=run["reflection"], norm_drift=run["norm_drift"])
res["gate_pure"] = rep
print("gate (pure, sigma = 10 cells):", {k: round(v, 6) if isinstance(v, float) else v for k, v in rep.items()})
off = run_collision(model, CouplerParams(k=0.0, c=0.0), BSTAR, sigma=10.0)
res["control_coupler_off"] = gate_report(gram_from_overlap(off["omega"], off["p11"]))
naive = gate_report(gram_from_overlap(np.exp(1j * run["phase"])))           # if motion were ignored
res["naive_ignoring_motion"] = naive

# ---------------------------------------------------------------- C3 thermal launch + two-velocity check
th_sweet, om_sweet = B.gate_thermal_infidelity(model, CP, BSTAR)
th_ind, om_ind = B.gate_thermal_infidelity(model, CP_IND, BSTAR)
res["thermal_20mK"] = dict(velocity_spread_rel=model.thermal_beta_spread(BSTAR), sweet_spot_infidelity=th_sweet,
                           sweet_overlap=om_sweet, inductive_only_infidelity=th_ind, inductive_overlap=om_ind)
print("thermal 20 mK:", res["thermal_20mK"])
twov = []
for bB in (0.27, 0.33):
    r_ = run_collision(model, CP, BSTAR, beta_B=bB, sigma=10.0)
    kA, kB = model.k_for_beta(BSTAR), model.k_for_beta(bB)
    scale = math.pi / float(eikonal.delta(model, CP, kA, -kA))
    twov.append(dict(beta_A=BSTAR, beta_B=bB, phase_2D=pos(r_["phase"]),
                     phase_model=scale * float(eikonal.delta(model, CP, kA, -kB))))
    print("two-velocity check", twov[-1])
res["two_velocity_check"] = twov

# ---------------------------------------------------------------- C4/C5 phase and concurrence vs coupling strength
svals = [0.25, 0.5, 0.75, 1.0, 1.25]
sc_pts = []
for s in svals:
    r_ = run_collision(model, CouplerParams(k=CP.k * s, c=CP.c * s), BSTAR, sigma=10.0)
    Gs = gram_from_overlap(r_["omega"], r_["p11"])
    sc_pts.append(dict(s=s, phase=pos(r_["phase"]), concurrence=concurrence(logical_rho(Gs)), overlap_abs=r_["overlap_abs"]))
    print("strength", sc_pts[-1])
res["strength_scan"] = sc_pts
ss = np.linspace(0, 1.5, 61)
scale_ref = math.pi / float(eikonal.delta(model, CP, model.k_for_beta(BSTAR), -model.k_for_beta(BSTAR)))
sb = model.thermal_beta_spread(BSTAR) * BSTAR
conc_th, conc_ind, ph_lin = [], [], []
for s in ss:
    cps = CouplerParams(k=CP.k * s * scale_ref, c=CP.c * s * scale_ref)
    cpi = CouplerParams(k=kt_to_k(exact.ktilde(CP_IND.k) * s * math.pi / float(eikonal.delta(model, CP_IND, model.k_for_beta(BSTAR), -model.k_for_beta(BSTAR)))), c=0.0)
    om_s = eikonal.overlap_thermal(model, cps, BSTAR, sb) if s > 0 else 1.0
    om_i = eikonal.overlap_thermal(model, cpi, BSTAR, sb) if s > 0 else 1.0
    conc_th.append(concurrence(logical_rho(gram_from_overlap(om_s))))
    conc_ind.append(concurrence(logical_rho(gram_from_overlap(om_i))))
    ph_lin.append(s * math.pi)
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.8))
ax[0].plot(ss, ph_lin, "-", color=C_MIX, alpha=0.6, label="first order (eikonal), rescaled to the calibration")
ax[0].plot([p["s"] for p in sc_pts], [p["phase"] for p in sc_pts], "o", color=C_MIX, label="exact 2D quantum scattering")
ax[0].axhline(math.pi, color="k", ls=":", lw=0.8)
ax[0].set(xlabel="coupler strength s (k = s k_cal, c = s c_cal)", ylabel="conditional phase Delta (rad)",
          title="(a) Conditional phase vs coupling, beta* = 0.30")
ax[0].legend(fontsize=8)
ax[1].plot([p["s"] for p in sc_pts], [p["concurrence"] for p in sc_pts], "o", color=C_SIM, label="pure wavepackets, exact 2D")
ax[1].plot(ss, conc_th, "-", color=C_MIX, label="thermal launch 20 mK, sweet-spot coupler")
ax[1].plot(ss, conc_ind, "--", color=C_IND, label="thermal launch 20 mK, inductive-only coupler")
ax[1].set(xlabel="coupler strength s", ylabel="concurrence of the output from |+>|+>",
          title="(b) Logical entanglement vs interaction strength")
ax[1].legend(fontsize=8)
savefig(fig, "fig05_phase_vs_coupling.png")
fig, ax = plt.subplots(figsize=(5.6, 3.8))
ax.plot(ss, conc_th, "-", color=C_MIX, label="sweet-spot coupler (k, c), thermal 20 mK")
ax.plot(ss, conc_ind, "--", color=C_IND, label="inductive-only coupler (k), thermal 20 mK")
ax.plot([p["s"] for p in sc_pts], [p["concurrence"] for p in sc_pts], "o", color=C_SIM, label="exact 2D, pure wavepackets")
ax.set(xlabel="interaction strength s", ylabel="concurrence", title="Concurrence vs interaction strength")
ax.legend(fontsize=8)
savefig(fig, "fig06_concurrence_vs_strength.png")

# ---------------------------------------------------------------- C6 timing mismatch on a finite coupler
W, TT = 60, 20
env = lambda xm: np.where(np.abs(xm) <= W / 2, 1.0, np.where(np.abs(xm) <= W / 2 + TT,
                          0.5 * (1 + np.cos(np.pi * (np.abs(xm) - W / 2) / TT)), 0.0))
v_ns = model.v_cells_per_ns(model.k_for_beta(BSTAR))
timing = []
for dt_off in (0.0, 0.1, 0.2, 0.3, 0.38):
    r_ = run_collision(model, CP, BSTAR, sigma=10.0, n=768, x0=60.0, envelope=env, t_offset=dt_off)
    Gt = gram_from_overlap(r_["omega"], r_["p11"])
    rp = gate_report(Gt)
    timing.append(dict(t_offset_ns=dt_off, meeting_point=r_["meeting_point"], phase=pos(r_["phase"]),
                       avg_fidelity=rp["average_gate_fidelity_CZ"], concurrence=rp["concurrence"]))
    print("timing", timing[-1])
res["timing_2D"] = timing
fig, ax = plt.subplots(figsize=(6.2, 3.9))
dts = np.linspace(0, 1.2, 121)
for Wp, Tp, col in ((60, 20, C_SIM), (100, 40, C_MIX), (200, 40, "#7c3aed"), (400, 40, C_IND)):
    inf = [B.timing_infidelity(v_ns * d / 2, Wp, Tp, 10 / math.sqrt(2)) for d in dts]
    ax.semilogy(dts * 1e3, np.maximum(inf, 1e-7), "-", color=col, label=f"model, plateau {Wp} cells ({Wp * rail.pitch_um:.0f} um)")
ax.semilogy([t["t_offset_ns"] * 1e3 for t in timing], [max(1 - t["avg_fidelity"], 1e-7) for t in timing], "o", color=C_SIM,
            label="exact 2D with the 60-cell coupler")
ax.set(xlabel="launch-time mismatch (ps)", ylabel="1 - F_avg (CZ)", title="Gate fidelity vs timing mismatch (beta* = 0.30)")
ax.legend(fontsize=7.5)
savefig(fig, "fig07_fidelity_vs_timing.png")

# ---------------------------------------------------------------- C7 sensitivity
Ts = np.array([0.005, 0.01, 0.02, 0.04, 0.07, 0.1])
sens_T = [dict(T=T, sweet=B.gate_thermal_infidelity(model, CP, BSTAR, T)[0], inductive=B.gate_thermal_infidelity(model, CP_IND, BSTAR, T)[0])
          for T in Ts]
mism = np.linspace(-0.05, 0.05, 21)
sens_mis = []
for dbb in mism:
    kA, kB = model.k_for_beta(BSTAR), model.k_for_beta(BSTAR + dbb)
    d_s = scale_ref * float(eikonal.delta(model, CP, kA, -kB))
    sc_i = math.pi / float(eikonal.delta(model, CP_IND, kA, -kA))
    d_i = sc_i * float(eikonal.delta(model, CP_IND, kA, -kB))
    sens_mis.append(dict(dbeta=dbb, sweet=B.coupler_infidelity(d_s / math.pi - 1), inductive=B.coupler_infidelity(d_i / math.pi - 1)))
errs = np.linspace(-0.15, 0.15, 31)
sens_coup = [dict(err=e, uncorrected=B.coupler_infidelity(e)) for e in errs]
lengths = np.array([50, 100, 200, 300, 600, 1000])
sens_dis = {f"beta={b}_sigma={s}": [B.cz_infidelity_from_dephasing(B.disorder_dephasing(model, b, n, s, s, s)[0]) for n in lengths]
            for b in (0.3, 0.45, 0.6) for s in (0.01, 0.02)}
res["sensitivity"] = dict(temperature=sens_T, velocity_mismatch=sens_mis, coupler_error=sens_coup,
                          disorder=dict(lengths=lengths, curves=sens_dis))

# ---------------------------------------------------------------- C8 optimisation of the operating point
betas = np.round(np.arange(0.20, 0.71, 0.05), 3)
opt = [B.budget(model, None, b) for b in betas]
for o in opt:
    print(f"budget beta {o['beta']:.2f}: total {o['total']:.4f}  " + "  ".join(f"{k} {v:.1e}" for k, v in o["parts"].items()))
res["budget_scan_default"] = opt
valid = [o for o in opt if o["beta"] <= 0.45]                         # first-order circuit model trusted to ~15 % here
best = min(valid, key=lambda o: o["total"])
res["optimum"] = dict(chosen=best, note="search restricted to beta <= 0.45 where the collective-coordinate model "
                      "agrees with the circuit (A_classical); faster fluxons reduce disorder dephasing further but "
                      "need a full-circuit quantum treatment")
BOPT = best["beta"]
print("chosen operating point beta =", BOPT)
# circuit check of the sweet spot for the re-designed coupler + 2D calibration there
kO, cO = exact.coupler_for(math.pi, BOPT, rail.Lambda, rail.EJ_over_hfp)
N_ = 1400
n_ = np.arange(N_)
envc = np.array(CouplerParams(n_plateau=720, n_taper=40).envelope(N_, 300))
circ = []
for b in np.round(np.arange(BOPT - 0.06, BOPT + 0.061, 0.03), 3):
    xs = {}
    for cfg in ("11", "10"):
        sim = MultiRailSG(N_, 2, rail.Lambda, couplers=[Coupler(0, 1, kO, cO, envc)])
        phi, dphi = np.zeros((N_, 2)), np.zeros((N_, 2))
        phi[:, 0], dphi[:, 0] = kink(n_, 250.0, rail.Lambda, v=b * rail.Lambda)
        if cfg == "11":
            phi[:, 1], dphi[:, 1] = kink(n_, 1150.0, rail.Lambda, v=-b * rail.Lambda)
        pT, _, _ = sim.run(phi, dphi, t_end=880 / (b * rail.Lambda), dt=0.05)
        xs[cfg] = kink_centres(pT[:, 0])[0]
    circ.append(dict(beta=float(b), dxA=xs["11"] - xs["10"], theory=exact.shift_A_cells(b, rail.Lambda, kO, cO, model.E0_GHz / rail.EJ_GHz)))
    print("circuit check at optimum", circ[-1])
zc = None
for p1, p2 in zip(circ[:-1], circ[1:]):
    if p1["dxA"] * p2["dxA"] <= 0:
        zc = p1["beta"] - p1["dxA"] * (p2["beta"] - p1["beta"]) / (p2["dxA"] - p1["dxA"])
CPO, cal_opt = calibrate(BOPT, kO, cO)
run_o = run_collision(model, CPO, BOPT, sigma=10.0)
rep_o = gate_report(gram_from_overlap(run_o["omega"], run_o["p11"]))
bud_o = B.budget(model, None, BOPT)
res["optimum_validation"] = dict(beta=BOPT, first_order=dict(k=kO, c=cO), calibrated=dict(k=CPO.k, c=CPO.c),
                                 calibration=cal_opt, circuit_zero_crossing=zc, circuit_scan=circ, gate_pure=rep_o,
                                 budget=bud_o)

# figure 8
fig, ax = plt.subplots(2, 3, figsize=(13.5, 7.2))
a = ax[0, 0]
a.semilogy(Ts * 1e3, [s["sweet"] for s in sens_T], "o-", color=C_MIX, label="sweet-spot coupler")
a.semilogy(Ts * 1e3, [s["inductive"] for s in sens_T], "s--", color=C_IND, label="inductive-only coupler")
a.set(xlabel="launch temperature (mK)", ylabel="1 - F_avg", title="(a) Thermal launch-velocity spread")
a.legend(fontsize=8)
a = ax[0, 1]
a.semilogy(mism, np.maximum([s["sweet"] for s in sens_mis], 1e-9), "-", color=C_MIX, label="sweet-spot coupler")
a.semilogy(mism, np.maximum([s["inductive"] for s in sens_mis], 1e-9), "--", color=C_IND, label="inductive-only")
a.set(xlabel="beta_B - beta_A (systematic)", ylabel="1 - F_avg", title="(b) Launch-speed mismatch")
a.legend(fontsize=8)
a = ax[0, 2]
a.semilogy(errs * 100, np.maximum([s["uncorrected"] for s in sens_coup], 1e-9), "-", color=C_SIM)
a.set(xlabel="coupler strength error (%)", ylabel="1 - F_avg (uncalibrated)", title="(c) Coupler fabrication error (needs calibration)")
a = ax[1, 0]
for key, curve in sens_dis.items():
    b, s = key.split("_")
    a.loglog(lengths, np.maximum(curve, 1e-8), "o-" if "0.02" in s else "o:", label=key.replace("_", ", "))
a.set(xlabel="flight length per rail (cells)", ylabel="1 - F_avg", title="(d) Junction disorder -> rail dephasing (20 mK launch)")
a.legend(fontsize=7)
a = ax[1, 1]
parts = list(opt[0]["parts"].keys())
for p_ in parts:
    a.semilogy(betas, [max(o["parts"][p_], 1e-9) for o in opt], "o-", ms=3, label=p_)
a.semilogy(betas, [o["total"] for o in opt], "k-", lw=2, label="total")
a.axvline(BOPT, color="k", ls=":", lw=0.8)
a.set(xlabel="design speed beta*", ylabel="1 - F_avg", title="(e) Error budget vs design speed (300 cells, 2 % disorder)")
a.legend(fontsize=7)
a = ax[1, 2]
alphas = np.logspace(-7, -4, 13)
a.loglog(alphas, [B.cz_infidelity_from_dephasing(B.damping_decoherence(model, BOPT, 300, al)) for al in alphas], "o-", color=C_SIM)
a.set(xlabel="sub-gap damping alpha", ylabel="1 - F_avg (upper bound)", title=f"(f) Dissipation along a 300-cell flight, beta = {BOPT}")
savefig(fig, "fig08_noise_loss_sensitivity.png")

# ---------------------------------------------------------------- milestone C
checks = [
    ("nonlocal phase: Delta = pi +- 0.01 rad (exact 2D, calibrated)", abs(rep["conditional_phase_rad"] % (2 * math.pi) - math.pi) < 0.01,
     f"Delta = {rep['conditional_phase_rad'] % (2 * math.pi):.4f} rad"),
    ("entanglement from |+>|+>: concurrence > 0.99", rep["concurrence"] > 0.99, f"C = {rep['concurrence']:.6f}"),
    ("Bell-state fidelity > 0.99 (after a local Hadamard)", rep["bell_fidelity"] > 0.99, f"F_Bell = {rep['bell_fidelity']:.6f}"),
    ("CZ average gate fidelity > 0.99 (pure wavepackets)", rep["average_gate_fidelity_CZ"] > 0.99, f"F_avg = {rep['average_gate_fidelity_CZ']:.6f}"),
    ("logical, not motional, entanglement: motional Schmidt purity > 0.999, logical purity > 0.99",
     rep["motional_purity_out"] > 0.999 and rep["logical_purity"] > 0.99,
     f"motional purity {rep['motional_purity_out']:.6f}, logical purity {rep['logical_purity']:.6f}"),
    ("leakage (reflection / loss of a fluxon) < 1e-4", rep["leakage"] < 1e-4, f"{rep['leakage']:.1e}"),
    ("control: coupler off gives no entanglement", res["control_coupler_off"]["concurrence"] < 1e-6,
     f"C = {res['control_coupler_off']['concurrence']:.1e}"),
    ("thermal launch at 20 mK, sweet spot: intrinsic gate infidelity < 1e-2", th_sweet < 1e-2,
     f"{th_sweet:.1e} (inductive-only coupler: {th_ind:.1e})"),
    ("two-velocity phase model validated against 2D (|error| < 0.05 rad)", all(abs(t["phase_2D"] - t["phase_model"]) < 0.05 for t in twov),
     ", ".join(f"beta_B {t['beta_B']}: {t['phase_2D']:.3f} vs {t['phase_model']:.3f}" for t in twov)),
]
res["milestone_C"] = milestone("C (genuine quantum gate)", checks)
res["realistic_budget_at_optimum"] = dict(total_infidelity=bud_o["total"], parts=bud_o["parts"],
                                         assumptions="300 cells per rail, 2 % E_J/E_L/C disorder, 20 mK launch, alpha 2e-6, 10 ps jitter, 100-cell plateau")
res["runtime_s"] = time.time() - t_start
save_json("C_gate.json", res)
print(f"done in {res['runtime_s']:.0f} s")
