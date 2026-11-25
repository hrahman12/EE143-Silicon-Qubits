"""Coherent single-fluxon launcher for QBF-X2: a flux-bias trap plus a flux-gradient accelerator.

How the control lines act on the fluxon
---------------------------------------
External flux threading rail cell n gives it an external phase theta_n = 2 pi Phi_ext,n / Phi0. The cell's inductive
energy is then (Phi0/2pi)^2 (a_n - theta_n)^2 / 2L, where a_n is the phase drop across the cell. Take a kink at X with
phase drops a_n(X) (summing to 2 pi). To first order in theta it sees the potential

    U(X) = - E_J Lambda^2 sum_n a_n(X) theta_n        [E_J Lambda^2 = (Phi0/2pi)^2 / L = 250 GHz h]

- A theta that grows linearly along the rail exerts a uniform force F = 2 pi E_J Lambda^2 dtheta/dn.
- A localised theta bump makes a potential well.
- Both profiles come from control lines coupled by mutual inductance only. Galvanic bias taps would not work: a
  resistive tap damps the fluxon and adds noise, and an inductive tap to a common bus traps a flux quantum each time
  the fluxon passes.

Launch sequence (per launch row)
--------------------------------
1. Load (microseconds before the gate). A slow flux ramp of the rail-end loop inserts one fluxon. Intrinsic damping
   lets it relax into the trap, where it thermalises at 20 mK. Because the trap frequency is well above k_B T / h, it
   ends up in the motional ground state.
2. Release (t = 0). The trap line is switched off and the accelerator line switched on, both with edge time tau. The
   accelerator profile ramps linearly over L_tilt cells, then stays flat on a plateau.
3. Before the fluxon reaches the return ramp (where the control line leaves the rail), the accelerator is switched off
   while the fluxon is on the plateau. There theta is uniform, so switching it off exerts no force.

Phase-space picture: the linear potential turns the position spread of the trap ground state into an energy spread,
delta E ~ F sigma_x0. It turns the momentum spread into an arrival-time spread, delta t ~ delta p0 / F. Liouville fixes
the product, so the trap and L_tilt set a tradeoff between the relative speed spread and the wavepacket length. That
spread is not tied to k_B T at the launch temperature, unlike a launch from a thermal source.
Units: GHz (energy / h), ns, cells.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict

import numpy as np

from hardware.params import PHI0

TWO_PI = 2 * math.pi


def _smoothstep(u):
    """raised-cosine step from 0 (u <= 0) to 1 (u >= 1)"""
    u = np.clip(u, 0.0, 1.0)
    return 0.5 * (1 - np.cos(math.pi * u))


def edge(t, t_start, tau):
    """0 -> 1 between t_start and t_start + tau (raised cosine); tau = 0 is a hard step"""
    if tau <= 0:
        return np.where(np.asarray(t) >= t_start, 1.0, 0.0)
    return _smoothstep((np.asarray(t) - t_start) / tau)


@dataclass
class LauncherDesign:
    """Geometry in cells from the rail start (node 0); cell n lies between nodes n and n+1 (centre n + 0.5)."""
    beta: float = 0.45                 # target speed (operating point)
    f_trap_GHz: float = 3.0            # trap frequency (>> k_B T/h = 0.42 GHz at 20 mK)
    w_trap: float = 6.0                # Gaussian width of the theta bump (cells)
    n_load: int = 10                   # load section (rail-end loop)
    n_launch: int = 40                 # launch section: trap centre in its middle
    pre_tilt: float = 20.0             # linear flux ramp starts this far behind the trap centre, so that
                                       # backward zero-point components (to ~5.6 sigma_k) are turned round
    L_tilt: float = 86.0               # trap centre -> start of the plateau (cells): sets F = KE / L_tilt
    corner: float = 4.0                # smoothing of the ramp corners (cells)
    n_plateau: int = 120               # uniform-theta plateau, longer than the packet (+-4 sigma): switched off here
    n_return: int = 16                 # the accelerator line leaves the rail (theta back to 0)
    tau_ps: float = 20.0               # switching edge time of both control lines
    I_trap_uA: float = 80.0             # control-line currents (set the mutual-inductance targets); chosen so
    I_acc_uA: float = 450.0             # the targets fall in the drawable 0.018-0.084 pH per cell (extraction)
    acc_floor: float = 0.30             # uniform theta (no force) from acc_start to the ramp: keeps every coupled
    acc_start: float = 2.0              # cell above the drawable minimum mutual; the step at acc_start lies behind
                                       # the trap, in the load section, where the fluxon never goes
    theta_trap: float = 0.0            # filled by design(): bump amplitude for f_trap
    theta_max: float = 0.0             # filled by design(): plateau value for the target kinetic energy
    t_off_ns: float = 0.0              # filled by design(): accelerator switch-off time (fluxon mid-plateau)
    notes: dict = field(default_factory=dict)
    theta_trap_drawn: object = None    # back-annotation: per-cell external phase of the as-drawn trap line
    theta_acc_drawn: object = None     # back-annotation: per-cell external phase of the as-drawn accelerator line

    # ---- geometry
    @property
    def X0(self) -> float:
        return self.n_load + self.n_launch / 2

    @property
    def x_a(self) -> float:
        return self.X0 - self.pre_tilt

    @property
    def x_b(self) -> float:
        return self.X0 + self.L_tilt

    @property
    def x_c(self) -> float:
        return self.x_b + self.n_plateau

    @property
    def x_d(self) -> float:
        return self.x_c + self.n_return

    @property
    def n_end(self) -> int:
        """first cell after the launcher (start of BS_prep)"""
        return int(math.ceil(self.x_d))

    @property
    def n_accel(self) -> int:
        return self.n_end - self.n_load - self.n_launch

    # ---- flux profiles (per cell, length n_cells)
    def theta_trap_profile(self, n_cells: int) -> np.ndarray:
        if self.theta_trap_drawn is not None:
            return _fit(self.theta_trap_drawn, n_cells)
        xc = np.arange(n_cells) + 0.5
        return self.theta_trap * np.exp(-0.5 * ((xc - self.X0) / self.w_trap) ** 2)

    def acc_shape(self, x):
        """dimensionless accelerator profile s(x): 0 before acc_start, a uniform floor up to x_a, a linear ramp to 1 at
        x_b (corners smoothed over `corner` cells), a plateau, then a raised-cosine return to 0 between x_c and x_d"""
        x = np.asarray(x, float)
        fine = np.linspace(self.x_a - 2 * self.corner, self.x_b + 2 * self.corner, 20001)
        slope = (_smoothstep((fine - (self.x_a - self.corner / 2)) / self.corner)
                 - _smoothstep((fine - (self.x_b - self.corner / 2)) / self.corner))
        ramp = np.concatenate([[0.0], np.cumsum(0.5 * (slope[1:] + slope[:-1]) * np.diff(fine))])
        ramp /= ramp[-1]
        s = self.acc_floor + (1 - self.acc_floor) * np.interp(x, fine, ramp, left=0.0, right=1.0)
        s = np.where(x >= self.acc_start, s, 0.0)
        ret = 1 - _smoothstep((x - self.x_c) / max(self.n_return, 1e-9))
        return s * ret

    def theta_acc_profile(self, n_cells: int) -> np.ndarray:
        if self.theta_acc_drawn is not None:
            return _fit(self.theta_acc_drawn, n_cells)
        return self.theta_max * self.acc_shape(np.arange(n_cells) + 0.5)

    def switches(self, t_ns):
        """(trap amplitude, accelerator amplitude) at time t (ns); release at t = 0"""
        tau = self.tau_ps * 1e-3
        s_trap = 1 - edge(t_ns, 0.0, tau)
        s_acc = edge(t_ns, 0.0, tau) * (1 - edge(t_ns, self.t_off_ns, tau))
        return s_trap, s_acc

    # ---- control-line targets: theta_n = 2 pi M_n I / Phi0
    def mutual_targets_pH(self, n_cells: int) -> dict:
        tt = self.theta_trap_profile(n_cells)
        ta = self.theta_acc_profile(n_cells)
        Mt = tt * PHI0 / (TWO_PI * self.I_trap_uA * 1e-6) * 1e12
        Ma = ta * PHI0 / (TWO_PI * self.I_acc_uA * 1e-6) * 1e12
        return dict(trap=Mt, accelerator=Ma)

    def summary(self) -> dict:
        d = asdict(self)
        for k_ in ("theta_trap_drawn", "theta_acc_drawn"):
            d[k_] = None if d[k_] is None else "as-drawn profile (back-annotated)"
        d.update(X0=self.X0, x_a=self.x_a, x_b=self.x_b, x_c=self.x_c, x_d=self.x_d, n_end=self.n_end,
                 n_accel=self.n_accel)
        return d


# ---------------------------------------------------------------- collective-coordinate potential
def kink_drops(X, n_cells: int, Lam: float, gamma: float = 1.0):
    """a_n(X) for every cell n (rows) and kink position X (columns): f(n+1-X) - f(n-X), f = 4 atan exp(gamma x/Lam)"""
    X = np.atleast_1d(np.asarray(X, float))
    n = np.arange(n_cells)[:, None]
    f = lambda y: 4 * np.arctan(np.exp(np.clip(gamma * y / Lam, -60, 60)))
    return f(n + 1 - X[None, :]) - f(n - X[None, :])


def potential(theta_cells, X, rail, gamma: float = 1.0):
    """U(X) = -E_J Lambda^2 sum_n a_n(X) theta_n  (GHz), for a +2pi kink (phase rising with n)"""
    a = kink_drops(X, len(theta_cells), rail.Lambda, gamma)
    return -rail.EJ_GHz * rail.Lambda ** 2 * (np.asarray(theta_cells)[:, None] * a).sum(axis=0)


def trap_frequency(design: LauncherDesign, model, n_cells: int = 200) -> float:
    """small-oscillation frequency (GHz) of the trap alone, from the curvature of U at its minimum and the rest mass"""
    th = design.theta_trap_profile(n_cells)
    X = design.X0 + np.linspace(-1.5, 1.5, 61)
    U = potential(th, X, model.rail)
    curv = np.polyfit(X - design.X0, U, 4)[-3] * 2            # d2U/dX2 (GHz/cell^2)
    m = model.E0_GHz / (TWO_PI * model.hc0) ** 2              # GHz ns^2 / cell^2  (v in cells/ns)
    return math.sqrt(max(curv, 0.0) / m) / TWO_PI


def design(model, beta: float = 0.45, **kw) -> LauncherDesign:
    """size the trap (f_trap) and the accelerator (kinetic energy for beta) for this rail"""
    d = LauncherDesign(beta=beta, **kw)
    d.theta_trap = 1.0
    f1 = trap_frequency(d, model)
    d.theta_trap = (d.f_trap_GHz / f1) ** 2                   # curvature is linear in the amplitude
    KE = model.kinetic_energy(beta)
    F_per_theta = TWO_PI * model.rail.EJ_GHz * model.rail.Lambda ** 2      # GHz per cell per (rad/cell)
    # energy gained from the trap centre to the plateau = F_per_theta * (theta(x_b) - theta(X0)), theta(x_b) = theta_max
    d.theta_max = 1.0
    frac = 1.0 - float(d.acc_shape(d.X0))
    d.theta_max = KE / (F_per_theta * frac)
    F = F_per_theta * d.theta_max * (1 - d.acc_floor) / (d.x_b - d.x_a)     # the floor exerts no force
    # switch-off time: classical relativistic motion under F from rest at X0 until the plateau middle
    m = model.E0_GHz
    xs, t, v, p = d.X0, 0.0, 0.0, 0.0
    dt = 1e-4
    target = 0.5 * (d.x_b + d.x_c)
    while xs < target:
        Fx = F if xs < d.x_b else 0.0
        p += TWO_PI * Fx * dt                                   # dk/dt = 2 pi F (k in rad/cell, F in GHz/cell)
        v = model.v_cells_per_ns(p)
        xs += v * dt
        t += dt
    d.t_off_ns = t
    sp = model.rail
    d.notes = dict(F_GHz_per_cell=F, KE_GHz=KE, theta_slope_rad_per_cell=d.theta_max / (d.x_b - d.x_a),
                   trap_depth_GHz=float(-potential(d.theta_trap_profile(200), [d.X0], sp)[0]),
                   f_trap_check_GHz=trap_frequency(d, model), kT_GHz_20mK=0.020 * 1.380649e-23 / 6.62607015e-34 / 1e9)
    return d


def _fit(arr, n_cells):
    a = np.zeros(n_cells)
    v = np.asarray(arr, float)
    a[:min(n_cells, len(v))] = v[:n_cells]
    return a


def back_annotate(d: LauncherDesign, cells_trap, M_trap_pH, cells_acc, M_acc_pH, n_cells: int) -> LauncherDesign:
    """a copy of the design whose flux profiles come from as-drawn mutual inductances (launcher cell coordinates):
    theta_n = 2 pi M_n I / Phi0 with the design currents. Timing (t_off, tau) is kept."""
    import copy
    dd = copy.deepcopy(d)
    tt, ta = np.zeros(n_cells), np.zeros(n_cells)
    for c, M in zip(cells_trap, M_trap_pH):
        if 0 <= int(c) < n_cells:
            tt[int(c)] = TWO_PI * M * 1e-12 * d.I_trap_uA * 1e-6 / PHI0
    for c, M in zip(cells_acc, M_acc_pH):
        if 0 <= int(c) < n_cells:
            ta[int(c)] = TWO_PI * M * 1e-12 * d.I_acc_uA * 1e-6 / PHI0
    dd.theta_trap_drawn, dd.theta_acc_drawn = tt, ta
    return dd


def accelerator_trim(d: LauncherDesign, model, n_cells: int) -> float:
    """amplitude factor on the accelerator current that restores the design kinetic energy (energy gained from the
    trap centre to the plateau centre); this is the in-situ calibration of the launch speed"""
    th = d.theta_acc_profile(n_cells)
    U = potential(th, [d.X0, 0.5 * (d.x_b + d.x_c)], model.rail)
    return model.kinetic_energy(d.beta) / float(U[0] - U[1])
