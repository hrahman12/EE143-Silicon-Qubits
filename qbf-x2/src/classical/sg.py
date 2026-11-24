"""Classical multi-rail discrete sine-Gordon model of coupled Josephson transmission lines.

Circuit (per rail r, node n): junction (E_J, C) to ground, series inductance L to node n+1.
Couplers between rails add a mutual inductance M = k L per cell (self-inductance compensated) and a coupling
capacitance C_c = c C between facing nodes (node capacitance compensated).

Lagrangian (units: energy E_J, time 1/omega_p, omega_p^2 = 2 e I_c / (hbar C)):
    L = sum_n [ 1/2 phidot_n^T Mt_n phidot_n  -  Lambda^2/2 a_n^T Kt_n a_n  -  sum_r (1 - cos phi_{r,n}) ]
    a_n = phi_{n+1} - phi_n                     (phase drop across the cell inductors, vector over rails)
    Mt_n = C-matrix / C,  Kt_n = L * (inductance matrix)^-1      (dimensionless)
Equations of motion:
    Mt_n phiddot_n = Lambda^2 (Kt_n a_n - Kt_{n-1} a_{n-1}) - sin phi_n - alpha_n phidot_n + gamma_n
Free (open) ends: no current flows out of the first/last cell.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Coupler:
    rail_i: int
    rail_j: int
    k: float                      # mutual inductance fraction
    c: float                      # coupling capacitance fraction
    envelope: np.ndarray          # per node, 0..1


class MultiRailSG:
    def __init__(self, n_nodes: int, n_rails: int, Lambda: float, alpha=0.0, couplers=(), bias=0.0,
                 sponge: int = 0, sponge_alpha: float = 0.2):
        self.N, self.R, self.Lam = n_nodes, n_rails, Lambda
        self.alpha = np.zeros(n_nodes) + alpha
        if sponge:
            ramp = np.linspace(1, 0, sponge) ** 2 * sponge_alpha
            self.alpha[:sponge] += ramp
            self.alpha[-sponge:] += ramp[::-1]
        self.bias = bias
        M = np.tile(np.eye(n_rails), (n_nodes, 1, 1))
        Lmat = np.tile(np.eye(n_rails), (n_nodes - 1, 1, 1))
        for cp in couplers:
            g = np.asarray(cp.envelope, float)
            gl = 0.5 * (g[:-1] + g[1:])                     # cell value = mean of its two nodes
            M[:, cp.rail_i, cp.rail_j] -= cp.c * g
            M[:, cp.rail_j, cp.rail_i] -= cp.c * g
            Lmat[:, cp.rail_i, cp.rail_j] += cp.k * gl
            Lmat[:, cp.rail_j, cp.rail_i] += cp.k * gl
        self.M = M
        self.Minv = np.linalg.inv(M)
        self.K = np.linalg.inv(Lmat)                        # Kt per cell

    # ------------------------------------------------------------ dynamics
    def force(self, phi: np.ndarray) -> np.ndarray:
        """phi: (N, R). returns generalized force (N, R) before the mass matrix."""
        a = phi[1:] - phi[:-1]                              # (N-1, R)
        Ka = np.einsum("nij,nj->ni", self.K, a)
        f = np.zeros_like(phi)
        f[:-1] += Ka
        f[1:] -= Ka
        return self.Lam ** 2 * f - np.sin(phi) + self.bias

    def accel(self, phi, dphi):
        return np.einsum("nij,nj->ni", self.Minv, self.force(phi) - self.alpha[:, None] * dphi)

    def energy(self, phi, dphi) -> float:
        a = phi[1:] - phi[:-1]
        kin = 0.5 * np.einsum("ni,nij,nj->", dphi, self.M, dphi)
        ind = 0.5 * self.Lam ** 2 * np.einsum("ni,nij,nj->", a, self.K, a)
        jos = np.sum(1 - np.cos(phi))
        return float(kin + ind + jos)

    def energy_density(self, phi, dphi) -> np.ndarray:
        """per node and rail (cross terms split evenly); used to locate kinks and radiation"""
        a = np.zeros_like(phi)
        a[:-1] = phi[1:] - phi[:-1]
        Kfull = np.concatenate([self.K, self.K[-1:]], axis=0)
        kin = 0.5 * dphi * np.einsum("nij,nj->ni", self.M, dphi)
        ind = 0.5 * self.Lam ** 2 * a * np.einsum("nij,nj->ni", Kfull, a)
        return kin + ind + (1 - np.cos(phi))

    def run(self, phi, dphi, t_end, dt=0.05, record_every=1.0, callback=None):
        """velocity Verlet; damping treated semi-implicitly. Returns (phi, dphi, records)."""
        n_steps = int(round(t_end / dt))
        rec_every = max(1, int(round(record_every / dt)))
        acc = self.accel(phi, dphi)
        records = []
        for s in range(n_steps + 1):
            if s % rec_every == 0 and callback is not None:
                records.append(callback(s * dt, phi, dphi))
            if s == n_steps:
                break
            vh = dphi + 0.5 * dt * acc
            phi = phi + dt * vh
            fnew = np.einsum("nij,nj->ni", self.Minv, self.force(phi))
            dphi = (vh + 0.5 * dt * fnew) / (1 + 0.5 * dt * self.alpha[:, None])
            acc = fnew - self.alpha[:, None] * dphi
        return phi, dphi, records


# ------------------------------------------------------------ kinks
def kink(n, X0, Lam, v=0.0, polarity=+1):
    """moving discrete-lattice kink: phi = 4 arctan exp(p gamma (n - X0)/Lambda) (+2pi*0), velocity v in cells
    per 1/omega_p (v = beta Lambda). polarity +1: phi rises 0 -> 2pi with n; -1: falls 2pi -> 0."""
    beta = v / Lam
    g = 1 / math.sqrt(1 - beta ** 2)
    x = g * (n - X0) / Lam
    phi = 4 * np.arctan(np.exp(np.clip(polarity * x, -60, 60)))
    dphi = -v * polarity * 2 * g / Lam / np.cosh(np.clip(x, -60, 60))
    return phi, dphi


def kink_centres(phi_r: np.ndarray, n_kinks: int = 1, min_sep: int = 6):
    """sub-cell centres of the n_kinks largest |phase-gradient| peaks of one rail (gradient-weighted centroid)."""
    a = np.abs(np.diff(phi_r))
    out = []
    a_work = a.copy()
    for _ in range(n_kinks):
        i = int(np.argmax(a_work))
        lo, hi = max(0, i - min_sep), min(len(a), i + min_sep + 1)
        w = a[lo:hi] ** 2
        out.append(float(np.sum(w * (np.arange(lo, hi) + 0.5)) / np.sum(w)))
        a_work[lo:hi] = 0.0
    return sorted(out)


def rest_energy_numeric(Lam: float, n: int = 400) -> float:
    """static discrete kink energy (relaxed), in E_J -> compare 8 Lambda (continuum)"""
    sim = MultiRailSG(n, 1, Lam)
    phi, _ = kink(np.arange(n), n / 2 + 0.3, Lam)
    phi = phi[:, None].copy()
    dphi = np.zeros_like(phi)
    # damped relaxation
    sim.alpha[:] = 1.0
    phi, dphi, _ = sim.run(phi, dphi, t_end=200.0, dt=0.05)
    return sim.energy(phi, dphi)
