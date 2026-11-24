"""Simulations of the coherent single-fluxon launcher (hardware/launcher.py).

quantum_launch : the collective coordinate X of one quantum fluxon, H = E(k) + U(X, t), split-operator in 1D.
                 Initial state: the motional eigenstates of the trap, weighted thermally at T. Output: the launched
                 wavepacket, its velocity distribution (relative speed spread), length and arrival-time statistics.
classical_launch: the full discrete circuit (classical/sg.py, one rail) with the same time-dependent flux bias.
                 Output: kink trajectory, final speed, radiated energy, and how the arrival time responds to the
                 switching edge and to control-amplitude errors.
Units: GHz (energy / h), ns, cells (quantum); E_J, 1/omega_p, cells (classical, converted on output).
"""
from __future__ import annotations

import math

import numpy as np
import scipy.fft as sfft

from hardware.launcher import LauncherDesign, potential
from scattering.wavepacket import kgrid

TWO_PI = 2 * math.pi
KB_GHZ_PER_K = 1.380649e-23 / 6.62607015e-34 / 1e9


def _grid_potentials(d: LauncherDesign, model, x, n_cells):
    T = potential(d.theta_trap_profile(n_cells), x, model.rail)
    A = potential(d.theta_acc_profile(n_cells), x, model.rail)
    return T, A


def eigenstates(model, x, k, U, n_states=2, dtau=0.002, n_steps=3000):
    """lowest motional eigenstates of E(k) + U(x) by imaginary-time split-operator with Gram-Schmidt"""
    E = model.energy(k)
    dx = x[1] - x[0]
    kin = np.exp(-TWO_PI * E * dtau)
    half = np.exp(-TWO_PI * (U - U.min()) * dtau / 2)
    states = []
    for j in range(n_states):
        x0 = x[np.argmin(U)]
        psi = np.exp(-(x - x0) ** 2 / 4.0) * ((x - x0) ** j)
        psi = psi.astype(complex)
        for _ in range(n_steps):
            psi = half * sfft.ifft(kin * sfft.fft(half * psi))
            for s in states:
                psi -= s * np.vdot(s, psi) * dx
            psi /= math.sqrt(np.sum(np.abs(psi) ** 2) * dx)
        states.append(psi)
    energies = []
    for psi in states:
        pk = sfft.fft(psi)
        ekin = float(np.sum(E * np.abs(pk) ** 2) / np.sum(np.abs(pk) ** 2))
        energies.append(ekin + float(np.sum(U * np.abs(psi) ** 2) * dx))
    return states, energies


def velocity_stats(model, k, psi):
    """mean and rms speed (cells/ns) of a state from its momentum distribution"""
    pk = np.abs(sfft.fft(psi)) ** 2
    pk /= pk.sum()
    v = model.v_cells_per_ns(k)
    vm = float(np.sum(pk * v))
    return vm, float(math.sqrt(max(np.sum(pk * (v - vm) ** 2), 0.0)))


def quantum_launch(d: LauncherDesign, model, T_K=0.020, n=4096, dx=0.25, x_min=-64.0, dt=0.0005, x_ref=None,
                   x_far=None, n_states=2, keep=True):
    """launch the thermal mixture of trap eigenstates; follow each to x_ref (state handed to the 2D gate) and x_far
    (coupler centre). Returns statistics of the mixture and the launched ground-state packet."""
    x = x_min + np.arange(n) * dx
    k = kgrid(n, dx)
    n_cells = int(math.ceil(d.x_d)) + 20
    T, A = _grid_potentials(d, model, x, n_cells)
    U_hold = T                                                   # before release: trap only
    states, energies = eigenstates(model, x, k, U_hold, n_states=n_states)
    kT = T_K * KB_GHZ_PER_K
    w = np.exp(-(np.array(energies) - energies[0]) / kT)
    w /= w.sum()
    E = model.energy(k)
    kin = np.exp(-1j * TWO_PI * E * dt)
    x_ref = d.x_d + 1 if x_ref is None else x_ref
    x_far = x_ref + 150 if x_far is None else x_far
    out_states, stats = [], []
    for psi0 in states:
        psi = psi0.copy()
        t, rec_ref, rec_far = 0.0, None, None
        mean_x_prev = float(np.sum(x * np.abs(psi) ** 2) * dx)
        for step in range(200000):
            s_trap, s_acc = d.switches(t + dt / 2)
            Uh = np.exp(-1j * TWO_PI * (s_trap * T + s_acc * A) * dt / 2)
            psi = Uh * sfft.ifft(kin * sfft.fft(Uh * psi))
            t += dt
            rho = np.abs(psi) ** 2
            mx = float(np.sum(x * rho) * dx)
            if rec_ref is None and mx >= x_ref:
                rec_ref = (t, psi.copy(), mx)
            if mx >= x_far:
                rec_far = (t, psi.copy(), mx)
                break
            mean_x_prev = mx
        tr, pr, mr = rec_ref
        tf, pf, mf = rec_far
        vm, vs = velocity_stats(model, k, pr)
        sx_ref = float(math.sqrt(np.sum((x - mr) ** 2 * np.abs(pr) ** 2) * dx))
        sx_far = float(math.sqrt(np.sum((x - mf) ** 2 * np.abs(pf) ** 2) * dx))
        stats.append(dict(t_ref_ns=tr, x_ref=mr, t_far_ns=tf, x_far=mf, v_mean=vm, v_rms=vs, dv_over_v=vs / vm,
                          sigma_x_ref=sx_ref, sigma_x_far=sx_far, norm=float(np.sum(np.abs(pf) ** 2) * dx)))
        out_states.append(pr)
    # mixture statistics (velocity moments add with the thermal weights)
    vm = float(sum(wi * s["v_mean"] for wi, s in zip(w, stats)))
    v2 = float(sum(wi * (s["v_rms"] ** 2 + s["v_mean"] ** 2) for wi, s in zip(w, stats)))
    vs = math.sqrt(max(v2 - vm ** 2, 0.0))
    beta_mean = vm / (TWO_PI * model.hc0)
    res = dict(T_K=T_K, kT_GHz=kT, trap_energies_GHz=energies, thermal_weights=w.tolist(), per_state=stats,
               v_mean_cells_per_ns=vm, v_rms_cells_per_ns=vs, dv_over_v=vs / vm, beta_mean=beta_mean,
               sigma_x_at_ref=stats[0]["sigma_x_ref"], sigma_x_at_far=stats[0]["sigma_x_far"],
               t_ref_ns=stats[0]["t_ref_ns"], t_far_ns=stats[0]["t_far_ns"], x_ref=x_ref, x_far=x_far)
    if keep:
        res["x"] = x
        res["psi_ref"] = out_states[0]
        res["trap_states"] = states
    return res


# ---------------------------------------------------------------- classical circuit
def classical_launch(d: LauncherDesign, rail, N=420, t_after_off_ns=0.35, dt=0.05, scale_trap=1.0, scale_acc=1.0,
                     tau_ps=None, t_off_ns=None, alpha=0.0, x_probe=None, hold_only=False, with_kink=True):
    """full-circuit launch on one rail; returns trajectory and diagnostics (times in ns, energies in GHz)"""
    from classical.sg import MultiRailSG, kink, kink_centres
    Lam = rail.Lambda
    wp = TWO_PI * rail.fp_GHz                                      # 1/omega_p units per ns
    dd = LauncherDesign(**{k_: v_ for k_, v_ in d.__dict__.items() if k_ != "notes"})
    if tau_ps is not None:
        dd.tau_ps = tau_ps
    if t_off_ns is not None:
        dd.t_off_ns = t_off_ns
    th_t = dd.theta_trap_profile(N - 1) * scale_trap
    th_a = dd.theta_acc_profile(N - 1) * scale_acc
    sim = MultiRailSG(N, 1, Lam, theta=th_t[:, None].copy())
    n = np.arange(N)
    phi, dphi = kink(n, dd.X0, Lam)
    phi, dphi = phi[:, None].copy(), np.zeros((N, 1))
    if not with_kink:                                              # vacuum: radiation from the switching alone
        phi[:] = 0.0
    sim.alpha[:] = 0.5                                             # relax into the trap
    phi, dphi, _ = sim.run(phi, dphi, t_end=150.0, dt=dt)
    sim.alpha[:] = alpha
    X_start = kink_centres(phi[:, 0])[0] if with_kink else float("nan")

    def update(t, s):
        tn = t / wp
        if hold_only:
            s.theta[:, 0] = th_t
            return
        a_, b_ = dd.switches(tn)
        s.theta[:, 0] = a_ * th_t + b_ * th_a

    traj = []

    def cb(t, p, dp):
        traj.append((t / wp, kink_centres(p[:, 0])[0] if with_kink else 0.0))
        return None

    t_end_ns = (dd.t_off_ns + dd.tau_ps * 1e-3 + t_after_off_ns) if not hold_only else 1.0
    phi_f, dphi_f, _ = sim.run(phi, dphi, t_end=t_end_ns * wp, dt=dt, record_every=0.5, callback=cb, update=update)
    tr = np.array(traj)
    out = dict(X_start=X_start, t_ns=tr[:, 0], X=tr[:, 1])
    if not with_kink:
        out["E_total_GHz"] = sim.energy(phi_f, dphi_f) * rail.EJ_GHz
        return out
    if hold_only:
        out["drift_cells"] = float(np.max(np.abs(tr[:, 1] - X_start)))
        return out
    # final speed from the last 0.1 ns (accelerator off, free flight)
    sel = tr[:, 0] > tr[-1, 0] - 0.1
    v_ns = float(np.polyfit(tr[sel, 0], tr[sel, 1], 1)[0])
    c0 = TWO_PI * rail.Lambda * rail.fp_GHz                       # cells/ns
    beta = v_ns / c0
    g = 1 / math.sqrt(1 - beta ** 2)
    from classical.sg import rest_energy_numeric
    E0 = rest_energy_numeric(Lam) * rail.EJ_GHz
    E_tot = sim.energy(phi_f, dphi_f) * rail.EJ_GHz               # theta = 0 now: plain circuit energy
    ed = sim.energy_density(phi_f, dphi_f)[:, 0] * rail.EJ_GHz
    xk = kink_centres(phi_f[:, 0])[0]
    win = (n > xk - 15) & (n < xk + 16)
    E_kink_window = float(ed[win].sum())
    out.update(v_cells_per_ns=v_ns, beta=beta, KE_GHz=(g - 1) * E0, E_total_GHz=E_tot,
               radiation_GHz=float(E_tot - E_kink_window), E_kink_window_GHz=E_kink_window,
               winding=float((phi_f[-1, 0] - phi_f[0, 0]) / TWO_PI))
    if x_probe is not None:
        if tr[-1, 1] < x_probe:
            raise ValueError(f"probe at {x_probe} not reached (kink at {tr[-1, 1]:.1f} when the run ends)")
        i = int(np.argmax(tr[:, 1] >= x_probe))                    # first crossing (X is monotonic after release)
        out["t_arrival_ns"] = float(np.interp(x_probe, tr[i - 1:i + 1, 1], tr[i - 1:i + 1, 0]))
    return out
