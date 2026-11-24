"""Error budget of the QBF-X2 collision gate and the optimisation of its operating point.

Error channels (all evaluated for the input |+>|+>, reported as infidelity contributions):
  gate_thermal   : launch velocity spread (thermal at T) averages exp(i Delta(v_A, v_B)); suppressed to second
                   order at the sweet spot (eikonal model, validated by 2D propagation)
  disorder       : static junction disorder gives each rail a random phase phi_r ~ 1/v; the two rails of a qubit
                   differ by phi_01, whose velocity dependence turns the launch spread into dephasing
                   (static phi_01 is a calibratable single-qubit phase)
  damping        : energy dissipated along the flight, counted in plasma quanta; each emitted quantum can reveal
                   the rail (upper-bound estimate of which-rail decoherence)
  timing         : launch-time mismatch moves the meeting point; outside the coupler plateau Delta is lost
  coupler        : fabrication error of the coupler strength scales Delta (needs calibration or tuning)
"""
from __future__ import annotations

import math

import numpy as np

from scattering import eikonal


def per_cell_disorder_phase(model, beta, sigma_EJ, sigma_EL=0.0, sigma_C=0.0):
    """rms phase picked up from one cell's random E_J, E_L, C errors by a fluxon at speed beta (rad).
    Kink energy split (relativistic): Josephson 4 Lambda / gamma, inductive 4 Lambda gamma,
    kinetic 4 Lambda gamma beta^2 (units E_J); an error delta in one cell shifts the energy by delta x (share)."""
    L = model.rail.Lambda
    g = 1 / math.sqrt(1 - beta ** 2)
    v = model.v_cells_per_ns(model.k_for_beta(beta))
    EJ = model.rail.EJ_GHz
    w = math.sqrt((4 * L / g * sigma_EJ) ** 2 + (4 * L * g * sigma_EL) ** 2 + (4 * L * g * beta ** 2 * sigma_C) ** 2)
    # integrating one cell's energy share over the fluxon position X gives the kink's total share (units E_J*cell)
    return 2 * math.pi * EJ * w / v


def disorder_dephasing(model, beta, n_cells, sigma_EJ, sigma_EL=0.0, sigma_C=0.0, T_K=None, spread_rel=None):
    """spread_rel: relative launch-speed spread (rms dv/v); default = launch from a thermal source at T_K"""
    s_cell = per_cell_disorder_phase(model, beta, sigma_EJ, sigma_EL, sigma_C)
    Phi2 = 2 * n_cells * s_cell ** 2                                   # two independent rails of n_cells each
    s = model.thermal_beta_spread(beta, T_K) if spread_rel is None else spread_rel
    return 1 - 1 / math.sqrt(1 + Phi2 * s * s), math.sqrt(Phi2)


def damping_decoherence(model, beta, n_cells, alpha):
    """number of plasma quanta radiated into the dissipative bath along the flight (upper bound on which-rail
    information): P = alpha v^2 int phi'^2 = alpha v^2 8 gamma/Lambda (E_J omega_p), time n/v."""
    L = model.rail.Lambda
    g = 1 / math.sqrt(1 - beta ** 2)
    v = beta * L
    dE_EJ = alpha * v * 8 * g / L * n_cells
    return min(1.0, dE_EJ * model.rail.EJ_GHz / model.rail.fp_GHz)


def gate_thermal_infidelity(model, cp, beta, T_K=None, delta_target=math.pi, scale_to_target=True, spread_rel=None):
    """infidelity (1 - F_avg of CZ after best local phases) from thermal launch spread, for a coupler cp whose
    first-order phase is rescaled so that Delta(beta, beta) = delta_target (calibration)."""
    from gates.metrics import gram_from_overlap, best_process_fidelity, average_gate_fidelity
    from hardware.params import CouplerParams
    k0 = model.k_for_beta(beta)
    d0 = float(eikonal.delta(model, cp, k0, -k0))
    s = delta_target / d0 if scale_to_target else 1.0
    cps = CouplerParams(k=cp.k * s, c=cp.c * s)
    sb = (model.thermal_beta_spread(beta, T_K) if spread_rel is None else spread_rel) * beta
    om = eikonal.overlap_thermal(model, cps, beta, sb)
    G = gram_from_overlap(om)
    F, _ = best_process_fidelity(G)
    return 1 - average_gate_fidelity(F), om


def timing_infidelity(delta_x_meet, plateau, taper, sigma_meet, delta=math.pi):
    """meeting point offset (cells) -> conditional-phase error, averaged over the wavepacket overlap region."""
    xs = delta_x_meet + np.linspace(-4, 4, 161) * sigma_meet
    w = np.exp(-0.5 * ((xs - delta_x_meet) / sigma_meet) ** 2)
    w /= w.sum()
    half = plateau / 2
    g = np.where(np.abs(xs) <= half, 1.0,
                 np.where(np.abs(xs) <= half + taper, 0.5 * (1 + np.cos(math.pi * (np.abs(xs) - half) / taper)), 0.0))
    om = np.sum(w * np.exp(1j * delta * g))
    from gates.metrics import gram_from_overlap, best_process_fidelity, average_gate_fidelity
    F, _ = best_process_fidelity(gram_from_overlap(om))
    return 1 - average_gate_fidelity(F)


def cz_infidelity_from_dephasing(p_dephase_A, p_dephase_B=None):
    """average-gate infidelity added by independent dephasing of the two dual-rail qubits (coherence 1 - p)."""
    from gates.metrics import gram_from_overlap, best_process_fidelity, average_gate_fidelity
    pB = p_dephase_A if p_dephase_B is None else p_dephase_B
    cA, cB = 1 - p_dephase_A, 1 - pB
    G = np.ones((4, 4), complex)
    for x in range(4):
        for y in range(4):
            ax, bx, ay, by = x >> 1, x & 1, y >> 1, y & 1
            G[x, y] = (cA if ax != ay else 1) * (cB if bx != by else 1)
    G[3, :3] *= -1
    G[:3, 3] *= -1
    F, _ = best_process_fidelity(G)
    return 1 - average_gate_fidelity(F)


def coupler_infidelity(rel_error):
    """uncorrected relative error of the coupler strength -> conditional phase pi (1 + err)."""
    if not rel_error:
        return 0.0
    from gates.metrics import gram_from_overlap, best_process_fidelity, average_gate_fidelity
    F, _ = best_process_fidelity(gram_from_overlap(np.exp(1j * math.pi * (1 + rel_error))))
    return 1 - average_gate_fidelity(F)


def budget(model, cp_design, beta, n_cells=300, sigma_EJ=0.02, sigma_EL=0.02, sigma_C=0.02, alpha=2e-6,
           T_K=None, jitter_ps=10.0, plateau=100, taper=40, sigma=10.0, coupler_error=0.0, velocity_spread_rel=None):
    """total error budget at speed beta for a coupler redesigned to have its sweet spot at beta.
    velocity_spread_rel: rms dv/v of the launched fluxon (from a launcher model); None = thermal source at T_K.
    sigma: wavepacket length (cells) at the coupler, which sets the spread of meeting points."""
    from classical.exact import coupler_for
    from hardware.params import CouplerParams
    k, c = coupler_for(math.pi, beta, model.rail.Lambda, model.rail.EJ_over_hfp)
    cp = CouplerParams(k=k, c=c)
    e_gate, om = gate_thermal_infidelity(model, cp, beta, T_K, spread_rel=velocity_spread_rel)
    p_dis, phi01 = disorder_dephasing(model, beta, n_cells, sigma_EJ, sigma_EL, sigma_C, T_K, velocity_spread_rel)
    e_dis = cz_infidelity_from_dephasing(p_dis)
    p_damp = damping_decoherence(model, beta, n_cells, alpha)
    e_damp = cz_infidelity_from_dephasing(p_damp)
    v = model.v_cells_per_ns(model.k_for_beta(beta))
    dx_meet = v * jitter_ps * 1e-3 / 2 * math.sqrt(2)              # rms meeting-point shift (two launchers)
    e_time = timing_infidelity(dx_meet, plateau, taper, sigma / math.sqrt(2))
    e_coup = coupler_infidelity(coupler_error)
    parts = dict(gate_thermal=e_gate, disorder_dephasing=e_dis, damping=e_damp, timing=e_time, coupler=e_coup)
    return dict(beta=beta, k=k, c=c, parts=parts, total=sum(parts.values()), phi01_rms_rad=phi01,
                p_dephase_disorder=p_dis, p_dephase_damping=p_damp, thermal_overlap=om,
                velocity_spread_rel=(model.thermal_beta_spread(beta, T_K) if velocity_spread_rel is None
                                     else velocity_spread_rel), v_cells_per_ns=v,
                launch_model="thermal source" if velocity_spread_rel is None else "launcher model")
