"""Quantum collective-coordinate model of a light fluxon and of two fluxons on coupled rails.

Derivation (see paper Sec. 3): insert rigid, Lorentz-contracted kinks phi_r(n) = f(n - X_r) into the circuit
Lagrangian of classical/sg.py and keep terms to first order in the couplers (k, c):
    L = -E(X_A') - E(X_B') + E_J [Lambda^2 k~ + c X_A' X_B'] O(X_A - X_B) g((X_A+X_B)/2)
with E(.) the relativistic kink energy (rest energy E0 from the discrete lattice), O(r) = sum_n a(n-X_A) a(n-X_B)
the overlap of the two kinks' phase drops a(x) = f(x+1) - f(x) (sum over r of O = (2 pi)^2) and g the coupler
envelope. Canonical quantisation of X_A, X_B (momenta hbar k_A, hbar k_B), symmetric ordering of the velocity
coupling, gives (energies in GHz*h, lengths in cells, time in ns):
    H = E(k_A) + E(k_B) - E_J Lambda^2 k~ O g + c E_J * 1/2 {u_A u_B, O g}
    E(k) = sqrt(E0^2 + (Lambda f_p k)^2) - E0,      u(k) = (dE/dk)/f_p   (velocity in cells per 1/omega_p)
Omitted (documented in FEASIBILITY.md): O(k^2, c^2) image/renormalisation terms (identical in every logical
branch because of the dummy couplers), Peierls-Nabarro potential (checked numerically below), coupling to
plasma modes (checked with the classical field simulation), dissipation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from classical.exact import ktilde
from classical.sg import MultiRailSG, Coupler, kink, rest_energy_numeric
from hardware.params import RailParams, CouplerParams


@dataclass
class FluxonModel:
    rail: RailParams
    E0_GHz: float = 0.0          # filled from the discrete lattice

    def __post_init__(self):
        if not self.E0_GHz:
            self.E0_GHz = rest_energy_numeric(self.rail.Lambda) * self.rail.EJ_GHz

    # ---- single fluxon
    @property
    def hc0(self) -> float:          # GHz*cell
        return self.rail.Lambda * self.rail.fp_GHz

    def energy(self, k):
        return np.sqrt(self.E0_GHz ** 2 + (self.hc0 * k) ** 2) - self.E0_GHz

    def dEdk(self, k):
        return self.hc0 ** 2 * k / np.sqrt(self.E0_GHz ** 2 + (self.hc0 * k) ** 2)

    def u(self, k):
        """velocity in cells per (1/omega_p) = beta * Lambda"""
        return self.dEdk(k) / self.rail.fp_GHz

    def v_cells_per_ns(self, k):
        return 2 * math.pi * self.dEdk(k)

    def k_for_beta(self, beta: float) -> float:
        g = 1 / math.sqrt(1 - beta ** 2)
        return g * beta * self.E0_GHz / self.hc0

    def kinetic_energy(self, beta: float) -> float:
        return (1 / math.sqrt(1 - beta ** 2) - 1) * self.E0_GHz

    def mass_hbar2_over_2m(self) -> float:
        """non-relativistic hbar^2/(2m) in GHz*cell^2"""
        return self.hc0 ** 2 / (2 * self.E0_GHz)

    def de_broglie_cells(self, beta: float) -> float:
        return 2 * math.pi / self.k_for_beta(beta)

    def thermal_beta_spread(self, beta: float, T_K: float | None = None) -> float:
        """relative velocity spread of a fluxon launched from a source in thermal equilibrium at T
        (momentum variance m* k_B T, m* = gamma^3 m for longitudinal motion)."""
        kT = self.rail.kT_GHz if T_K is None else T_K * 1.380649e-23 / 6.62607015e-34 / 1e9
        g = 1 / math.sqrt(1 - beta ** 2)
        mv2 = self.E0_GHz * beta ** 2 * g ** 3          # m* v^2 in GHz
        return math.sqrt(kT / mv2)

    # ---- two fluxons
    def kink_drop(self, x, gamma=1.0):
        """phase drop across the cell [x, x+1] of a kink centred at 0 (rising 0 -> 2 pi)"""
        L = self.rail.Lambda
        f = lambda y: 4 * np.arctan(np.exp(np.clip(gamma * y / L, -60, 60)))
        return f(x + 1) - f(x)

    def overlap(self, r, gamma=1.0, n_half: int = 200):
        """O(r) = sum_n a(n - X_A) a(n - X_B), X_A - X_B = r, X_A + X_B = 0 (periodic PN modulation averaged)"""
        r = np.atleast_1d(np.asarray(r, float))
        n = np.arange(-n_half, n_half) + 0.5
        out = np.zeros_like(r)
        for s in (0.0, 0.25, 0.5, 0.75):                # average over the sub-cell position of the pair
            out += np.sum(self.kink_drop(n[None, :] - s - r[:, None] / 2, gamma) *
                          self.kink_drop(n[None, :] - s + r[:, None] / 2, gamma), axis=1)
        return out / 4

    def interaction_coeffs(self, cp: CouplerParams):
        """(A, B): H_int = -A O g + B 1/2{u_A u_B, O g}, both in GHz"""
        A = self.rail.EJ_GHz * self.rail.Lambda ** 2 * ktilde(cp.k)
        B = cp.c * self.rail.EJ_GHz
        return A, B

    # ---- checks of the effective model against the circuit
    def peierls_nabarro_GHz(self, n: int = 300) -> float:
        """energy difference between a kink centred on a node and between nodes (relaxed, pinned by symmetry)"""
        Lam = self.rail.Lambda
        es = []
        for X0 in (n / 2, n / 2 + 0.5):
            sim = MultiRailSG(n, 1, Lam, alpha=1.0)
            phi, _ = kink(np.arange(n), X0, Lam)
            phi = phi[:, None]
            phi, d, _ = sim.run(phi, np.zeros_like(phi), t_end=150.0, dt=0.05)
            es.append(sim.energy(phi, d))
        return abs(es[0] - es[1]) * self.rail.EJ_GHz


def relaxed_interaction(rail: RailParams, cp: CouplerParams, r_list, n: int = 240):
    """Static check of the inductive interaction: two kinks pinned (one node fixed at pi in each rail) at
    separation r on rails coupled uniformly by (k, 0); all other phases relaxed. Returns
    V_int(r) = E_AB - E_A - E_B + E_0 in GHz (E_A: only rail A carries a kink, rail B relaxes = image response)."""
    from scipy.optimize import minimize
    Lam = rail.Lambda
    env = np.ones(n)
    sim = MultiRailSG(n, 2, Lam, couplers=[Coupler(0, 1, cp.k, 0.0, env)])

    def relax(pins):
        nodes = np.arange(n)
        phi0 = np.zeros((n, 2))
        fixed = np.zeros((n, 2), bool)
        for rail_i, centre in pins:
            phi0[:, rail_i] = kink(nodes, centre, Lam)[0]
            fixed[int(centre), rail_i] = True
            phi0[int(centre), rail_i] = math.pi
        free = ~fixed

        def fun(x):
            p = phi0.copy()
            p[free] = x
            e = sim.energy(p, np.zeros_like(p))
            g = -sim.force(p)
            return e, g[free]
        res = minimize(fun, phi0[free], jac=True, method="L-BFGS-B", options=dict(maxiter=5000, gtol=1e-10))
        return res.fun
    c = n // 2
    out = []
    for r in r_list:
        xa, xb = c + int(round(r / 2)), c - int(round(r / 2)) + (int(round(r)) % 2 and 0)
        xb = xa - int(round(r))
        e_ab = relax([(0, xa), (1, xb)])
        e_a = relax([(0, xa)])
        e_b = relax([(1, xb)])
        out.append((e_ab - e_a - e_b) * rail.EJ_GHz)
    return np.array(out)
