"""Milestone B - quantum ballistic physics in the collective-coordinate model (quantum/fluxon.py).

1. validity map: quantum sine-Gordon coupling, de Broglie wavelength, Peierls-Nabarro barrier, first-order accuracy
2. single quantum fluxon wavepacket: propagation and dispersion vs analytic (figure 2)
3. static check of the derived interaction against constrained relaxation of the full circuit
4. two-fluxon collision at the first-order sweet-spot design: joint probability, before/after (figures 3, 4)
5. convergence in time step, grid spacing (Hilbert-space cut-off), domain size and Taylor order
6. quantum vs classical: conditional phase, conditional shift and which-path overlap vs velocity (figure 9)
Writes results/B_quantum.json
"""
import math
import sys
import time

import numpy as np

from _common import plt, save_json, load_json, savefig, milestone, C_IND, C_MIX, C_TH, C_SIM
from classical import exact
from hardware.params import RailParams, CouplerParams
from quantum.fluxon import FluxonModel, relaxed_interaction
from scattering.wavepacket import OneFluxonPropagator, gaussian, fft2
from scattering.collide import run_collision
from scattering import eikonal

def evaluate(res, A):
    """milestone-B acceptance tests from the stored results (re-runnable: python B_quantum.py --evaluate-only)."""
    rail_ = RailParams()
    conv, qc, sw, base = res["convergence"], res["quantum_classical"], res["single_wavepacket"], res["sweet_spot_collision"]
    # sweet spots: zero crossing of the conditional delay, quantum (this script) vs classical circuit (A_classical)
    def zero_cross(pts, key):
        pts = sorted(pts, key=lambda p: p["beta"])
        for p1, p2 in zip(pts[:-1], pts[1:]):
            if p1[key] * p2[key] <= 0:
                return p1["beta"] - p1[key] * (p2["beta"] - p1["beta"]) / (p2[key] - p1[key])
        return None
    zq = zero_cross([p for p in qc if p["coupler"] == "mixed"], "dXA_quantum")
    zc = zero_cross([p for p in A["collision_scan"] if p["coupler"] == "mixed"], "dxA")
    # quantum corrections: quantum <dX_A> vs the classical limit of the same (first-order) model, in units of the
    # natural delay scale (inductive-coupler shift at the same speed)
    scale = {round(p["beta"], 3): abs(p["dX_first_order"]) for p in qc if p["coupler"] == "inductive"}
    qcorr = [abs(p["dXA_quantum"] - p["dX_first_order"]) / scale[round(p["beta"], 3)] for p in qc]
    ph_spread = max(c["phase"] for c in conv) - min(c["phase"] for c in conv)
    st = res["static_interaction"]
    v = res["validity"]
    checks = [
        ("unitarity: norm conserved", max(abs(c["norm_drift"]) for c in conv) < 1e-6, f"max drift {max(abs(c['norm_drift']) for c in conv):.1e}"),
        ("converged: phase within 0.01 rad under dt, dx (k cut-off), domain and Taylor-order changes", ph_spread < 0.01,
         f"phase spread {ph_spread:.4f} rad over {len(conv)} runs"),
        ("coherent single-fluxon propagation: group velocity and dispersion match the relativistic E(k)",
         abs(sw["v_group_fit"] / sw["v_group_theory"] - 1) < 0.01 and abs(sw["width_final_sim"] / sw["width_final_analytic"] - 1) < 0.02,
         f"v_g {sw['v_group_fit']:.2f} vs {sw['v_group_theory']:.2f} cells/ns, width {sw['width_final_sim']:.2f} vs {sw['width_final_analytic']:.2f} cells"),
        ("topological charge: the collision is reflectionless (both fluxons transmitted)", base["reflection"] < 1e-4,
         f"reflection {base['reflection']:.1e}"),
        ("quantum-classical correspondence: conditional-delay zero crossing, quantum vs classical circuit, within 0.02 in beta",
         zq is not None and zc is not None and abs(zq - zc) < 0.02, f"quantum {zq:.4f}, classical circuit {zc:.4f}"),
        ("quantum corrections to the classical limit of the same model < 10 % of the delay scale (all 10 points)",
         max(qcorr) < 0.10, f"worst {max(qcorr) * 100:.1f} %"),
        ("derived interaction: first-order potential vs constrained relaxation of the circuit within 5 % at contact",
         abs(st["rel_err_r0"]) < 0.05, f"{st['rel_err_r0'] * 100:+.2f} %"),
        ("effective-model regime: quantum (beta^2 ~ 0.5 < 8 pi), PN barrier << kinetic energy",
         rail_.beta2_qsg < 1 and v["peierls_nabarro_GHz"] < 0.01 * v["kinetic_energy_GHz"],
         f"beta^2 = {rail_.beta2_qsg:.3f}, PN = {v['peierls_nabarro_GHz']:.2e} GHz vs KE = {v['kinetic_energy_GHz']:.1f} GHz"),
    ]
    res["milestone_B"] = milestone("B (quantum ballistic physics)", checks)
    res["quantum_sweet_spot_beta"] = zq
    res["classical_sweet_spot_beta"] = zc
    res["superseded_check"] = ("An earlier correspondence test compared quantum and classical shifts only where both scans had "
                               "a point with |shift| > 0.05 cells: one point (5.8 %). Replaced by the two tests above.")
    res["first_order_phase_error_at_design"] = float((base["phase"] % (2 * math.pi) - math.pi) / math.pi)
    res["breakdown"] = dict(
        first_order_phase_vs_exact=f"exact phase exceeds the first-order design value by {(base['phase'] % (2 * math.pi) - math.pi):+.3f} rad "
                                   "(second order in the coupling): calibrated in C_gate.py",
        low_velocity="first-order classical shift overestimates by >10 % below beta ~ 0.22 (interaction no longer weak vs kinetic energy)",
        high_velocity="beyond beta ~ 0.35 lattice radiation and O(c^2) dragging corrections grow (A_classical first_order_accuracy)",
        neglected=["O(k^2, c^2) image terms (identical in all branches with dummy couplers)", "coupling to plasma modes beyond the "
                   "classical radiation estimate", "dissipation and 1/f noise (FEASIBILITY.md)", "quantum mass renormalisation "
                   f"~ beta^2/8pi = {rail_.beta2_qsg / (8 * math.pi):.3f}"])
    return res


if "--evaluate-only" in sys.argv:
    r_ = load_json("B_quantum.json")
    r_ = evaluate(r_, load_json("A_classical.json"))
    save_json("B_quantum.json", r_)
    raise SystemExit(0)


t_start = time.time()
rail = RailParams()
model = FluxonModel(rail)
BSTAR = 0.30
K, CC = exact.coupler_for(math.pi, BSTAR, rail.Lambda, rail.EJ_over_hfp)
CP_MIX, CP_IND = CouplerParams(k=K, c=CC), CouplerParams(k=K, c=0.0)
res = dict(design=dict(beta_star=BSTAR, k=K, c=CC))

# ---------------------------------------------------------------- 1. validity map
k0 = model.k_for_beta(BSTAR)
pn = model.peierls_nabarro_GHz()
validity = dict(beta2_quantum_sine_gordon=rail.beta2_qsg, soliton_over_plasmon=model.E0_GHz / rail.fp_GHz,
                mass_renormalisation_estimate=rail.beta2_qsg / (8 * math.pi),
                de_broglie_cells=model.de_broglie_cells(BSTAR), fluxon_size_cells=rail.Lambda,
                kinetic_energy_GHz=model.kinetic_energy(BSTAR), kT_GHz=rail.kT_GHz,
                peierls_nabarro_GHz=pn, interaction_depth_GHz=model.interaction_coeffs(CP_MIX)[0] * 3.19 * 2,
                thermal_velocity_spread_rel=model.thermal_beta_spread(BSTAR),
                passage_time_over_plasma_period=rail.Lambda / (2 * BSTAR * rail.Lambda) * 1.0)
res["validity"] = validity
print("validity", {k: round(v, 5) for k, v in validity.items()})

# ---------------------------------------------------------------- 2. single wavepacket
pr = OneFluxonPropagator(model, n=4096, dx=0.25)
sig0 = 3.0
psi = gaussian(pr.x, -300, k0, sig0)
t_end = 600 / model.v_cells_per_ns(k0)
psi_end, snaps = pr.run(psi, t_end, 0.002, n_snap=120)
ts = np.array([s[0] for s in snaps])
dens = np.array([s[1] for s in snaps])
mean = np.array([np.sum(pr.x * d) / np.sum(d) for d in dens])
width = np.array([math.sqrt(np.sum((pr.x - m) ** 2 * d) / np.sum(d)) for m, d in zip(mean, dens)])
d2 = (model.dEdk(k0 + 1e-4) - model.dEdk(k0 - 1e-4)) / 2e-4                       # E'' in GHz cell^2
w_an = np.sqrt(sig0 ** 2 + (2 * math.pi * d2 * ts / (2 * sig0)) ** 2)
vg_fit = np.polyfit(ts, mean, 1)[0]
res["single_wavepacket"] = dict(sigma0=sig0, v_group_fit=vg_fit, v_group_theory=model.v_cells_per_ns(k0),
                                width_final_sim=width[-1], width_final_analytic=w_an[-1],
                                norm_final=float(np.sum(np.abs(psi_end) ** 2) / np.sum(np.abs(psi) ** 2)))
print("single wavepacket", res["single_wavepacket"])
fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
ax[0].imshow(dens.T[1000:3400], origin="lower", aspect="auto", cmap="viridis",
             extent=[0, ts[-1], pr.x[1000], pr.x[3400]])
ax[0].set(xlabel="time (ns)", ylabel="fluxon centre X (cells)",
          title=f"(a) |psi(X,t)|^2 of one quantum fluxon, beta = {BSTAR}, sigma0 = {sig0} cells")
ax[0].grid(False)
ax[1].plot(ts, width, color=C_SIM, label="split-operator simulation")
ax[1].plot(ts, w_an, "--", color=C_MIX, label="analytic: sigma0^2 + (E'' t / 2 sigma0)^2 (relativistic E(k))")
ax[1].set(xlabel="time (ns)", ylabel="wavepacket width (cells)", title="(b) Coherent spreading of the fluxon wavepacket")
ax[1].legend()
savefig(fig, "fig02_single_wavepacket.png")

# ---------------------------------------------------------------- 3. static check of the interaction
r_list = [0, 1, 2, 3, 4, 6, 8, 10]
V_relaxed = relaxed_interaction(rail, CouplerParams(k=K, c=0.0), r_list)
A_ind, _ = model.interaction_coeffs(CP_IND)
V_rigid = -A_ind * model.overlap(np.array(r_list, float))
res["static_interaction"] = dict(r=r_list, V_relaxed_GHz=V_relaxed, V_first_order_GHz=V_rigid,
                                 rel_err_r0=float((V_relaxed[0] - V_rigid[0]) / V_rigid[0]))
print("static interaction", res["static_interaction"])

# ---------------------------------------------------------------- 4. sweet-spot collision with snapshots
base = run_collision(model, CP_MIX, BSTAR, sigma=10.0, snap_fracs=(0.0, 0.35, 0.5, 0.65), keep_states=True)
ind = run_collision(model, CP_IND, BSTAR, sigma=10.0, keep_states=True)
for r_ in (base, ind):
    print({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r_.items()
           if k in ("phase", "overlap_abs", "reflection", "norm_drift", "dXA_quantum", "motional_purity_out")})
x = base["x"]
fig, ax = plt.subplots(1, 4, figsize=(13, 3.5))
for a, (tt, ps) in zip(ax, sorted(base["snaps"].items())):
    a.imshow(np.abs(ps.T) ** 2, origin="lower", cmap="magma", extent=[x[0], x[-1], x[0], x[-1]])
    a.plot([x[0], x[-1]], [x[0], x[-1]], color="w", lw=0.6, ls=":")
    a.set(xlabel="X_A (cells)", ylabel="X_B (cells)", title=f"t = {tt:.3f} ns")
    a.grid(False)
ax[0].set_title("(a) |psi_11(X_A, X_B)|^2, t = 0")
ax[-1].contour(x, x, np.abs(base["free"].T) ** 2, levels=3, colors="c", linewidths=0.6)
ax[-1].set_title(f"after: |psi_11|^2 (map) vs free branch (cyan); overlap {base['overlap_abs']:.6f}")
savefig(fig, "fig03_joint_probability.png")

fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
for a, r_, lab in ((ax[0], base, "sweet-spot coupler (k, c)"), (ax[1], ind, "inductive-only coupler (k)")):
    pin = np.sum(np.abs(r_["psi0"]) ** 2, axis=1)
    pout = np.sum(np.abs(r_["psi"]) ** 2, axis=1)
    pfree = np.sum(np.abs(r_["free"]) ** 2, axis=1)
    a.plot(x, pin, color=C_TH, label="fluxon A before")
    a.plot(x, pfree, color="k", lw=2.2, alpha=0.35, label="A after, free branch (00/01/10)")
    a.plot(x, pout, "--", color=C_MIX if r_ is base else C_IND, label="A after, |11> branch")
    a.set(xlabel="X_A (cells)", ylabel="probability density", xlim=(-110, 110),
          title=f"{'(a)' if r_ is base else '(b)'} {lab}: shift {r_['dXA_quantum']:+.3f} cells")
    a.legend(fontsize=7.5)
# momentum-space conditional phase spectrum
for r_, col, lab in ((base, C_MIX, "sweet spot"), (ind, C_IND, "inductive only")):
    F11, F0 = fft2(r_["psi"]), fft2(r_["free"])
    kk = 2 * math.pi * np.fft.fftfreq(len(x), d=x[1] - x[0])
    iB = int(np.argmin(np.abs(kk + k0)))
    w = np.abs(F0[:, iB])
    sel = w > 0.05 * w.max()
    ph = np.unwrap(np.angle(F11[sel, iB] / F0[sel, iB]))
    i0 = int(np.argmin(np.abs(kk[sel] - k0)))
    ax[2].plot(kk[sel], ph - ph[i0], "o-", ms=2.5, color=col, label=f"{lab}: arg(chi_11/chi_free) at k_B = -k0")
    kks = np.linspace(kk[sel].min(), kk[sel].max(), 50)
    d_ = eikonal.delta(model, CP_MIX if r_ is base else CP_IND, kks, -k0)
    ax[2].plot(kks, d_ - float(eikonal.delta(model, CP_MIX if r_ is base else CP_IND, k0, -k0)), ":", color=col)
ax[2].set(xlabel="k_A (rad/cell)", ylabel="Delta(k_A) - Delta(k0) (rad)", title="(c) Phase dispersion: flat at the sweet spot")
ax[2].legend(fontsize=7.5)
savefig(fig, "fig04_scattering_before_after.png")
res["sweet_spot_collision"] = {k: v for k, v in base.items() if k not in ("psi", "free", "psi0", "x", "snaps")}
res["inductive_collision"] = {k: v for k, v in ind.items() if k not in ("psi", "free", "psi0", "x", "snaps")}

# ---------------------------------------------------------------- 5. convergence
conv = []
for label, kw in (("reference dt=2ps dx=0.5 n=512", dict()), ("dt = 1 ps", dict(dt=0.001)), ("dt = 0.5 ps", dict(dt=0.0005)),
                  ("dx = 0.25 (k cut-off x2), n = 1024", dict(dx=0.25, n=1024)), ("domain x1.25 (n = 640)", dict(n=640)),
                  ("Taylor order 6", dict(taylor=6))):
    t0 = time.time()
    r_ = run_collision(model, CP_MIX, BSTAR, sigma=10.0, **kw)
    conv.append(dict(case=label, phase=r_["phase"], overlap_abs=r_["overlap_abs"], reflection=r_["reflection"],
                     norm_drift=r_["norm_drift"], seconds=time.time() - t0))
    print("convergence", conv[-1])
res["convergence"] = conv

# ---------------------------------------------------------------- 6. quantum vs classical vs first order
qc = []
for beta in (0.24, 0.27, 0.30, 0.33, 0.36):
    for lab, cp in (("mixed", CP_MIX), ("inductive", CP_IND)):
        r_ = run_collision(model, cp, beta, sigma=10.0)
        qc.append(dict(coupler=lab, beta=beta, phase=r_["phase"], overlap_abs=r_["overlap_abs"],
                       dXA_quantum=r_["dXA_quantum"], reflection=r_["reflection"],
                       phase_first_order=float(eikonal.delta(model, cp, model.k_for_beta(beta), -model.k_for_beta(beta))),
                       dX_first_order=exact.shift_A_cells(beta, rail.Lambda, cp.k, cp.c, model.E0_GHz / rail.EJ_GHz)))
        print("q-c", qc[-1])
res["quantum_classical"] = qc
A = load_json("A_classical.json")
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
bb = np.linspace(0.22, 0.40, 100)
for lab, cp, col in (("mixed", CP_MIX, C_MIX), ("inductive", CP_IND, C_IND)):
    pts = [p for p in qc if p["coupler"] == lab]
    ph = np.unwrap([p["phase"] for p in pts])
    if lab == "mixed":
        ph = np.where(ph < 0, ph + 2 * math.pi, ph)
    ax[0].plot([p["beta"] for p in pts], ph, "o", color=col, label=f"2D quantum scattering, {lab}")
    ax[0].plot(bb, [eikonal.delta(model, cp, model.k_for_beta(b), -model.k_for_beta(b)) for b in bb], "-", color=col, alpha=0.6,
               label="first order (eikonal)")
    ax[1].plot([p["beta"] for p in pts], [p["dXA_quantum"] for p in pts], "o", color=col, label=f"quantum <dX_A>, {lab}")
    cl = [p for p in A["collision_scan"] if p["coupler"] == lab and 0.22 <= p["beta"] <= 0.4]
    ax[1].plot([p["beta"] for p in cl], [p["dxA"] for p in cl], "s", mfc="none", color=col, label=f"classical circuit field, {lab}")
    ax[1].plot(bb, [exact.shift_A_cells(b, rail.Lambda, cp.k, cp.c, model.E0_GHz / rail.EJ_GHz) for b in bb], "-", color=col, alpha=0.5)
    ax[2].semilogy([p["beta"] for p in pts], [max(1 - p["overlap_abs"], 1e-9) for p in pts], "o-", color=col, label=lab)
ax[0].axhline(math.pi, color="k", lw=0.7, ls=":")
ax[0].set(xlabel="beta = v/c0", ylabel="conditional phase Delta (rad)", title="(a) Conditional phase: stationary at beta* for (k, c)")
ax[1].axhline(0, color="k", lw=0.7)
ax[1].set(xlabel="beta = v/c0", ylabel="conditional shift of A (cells)", title="(b) Quantum <dX_A> = classical shift (correspondence)")
ax[2].set(xlabel="beta = v/c0", ylabel="1 - |<chi_free|chi_11>|", title="(c) Which-path distinguishability (sigma = 10 cells)")
for a in ax:
    a.legend(fontsize=7.5)
savefig(fig, "fig09_quantum_vs_classical.png")

# ---------------------------------------------------------------- milestone B
res["runtime_s_physics"] = time.time() - t_start
res = evaluate(res, load_json("A_classical.json"))
res["runtime_s"] = time.time() - t_start
save_json("B_quantum.json", res)
print(f"done in {res['runtime_s']:.0f} s")
