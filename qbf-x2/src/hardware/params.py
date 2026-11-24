"""Physical parameters of QBF-X2 and the quantities derived from them.

Every number that is a *design proposal* (not measured, not taken from a foundry) is marked HYPOTHETICAL.
Units used across the code:
  classical model : time in 1/omega_p, energy in E_J, length in cells (dimensionless sine-Gordon units)
  quantum model   : time in ns, energy in GHz*h, length in cells (one cell = one junction of the array)
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

H = 6.62607015e-34
HBAR = H / (2 * math.pi)
E_CHARGE = 1.602176634e-19
PHI0 = H / (2 * E_CHARGE)
KB = 1.380649e-23


@dataclass
class RailParams:
    """One rail = discrete long Josephson junction (parallel array): a junction (E_J, C) to ground at every node,
    a series superinductance L between neighbouring nodes. HYPOTHETICAL values, chosen to make the fluxon light
    (quantum) while keeping the Peierls-Nabarro barrier negligible (Lambda >= 2.5)."""
    EJ_GHz: float = 40.0          # small Al/AlOx/Al junction, I_c = 80 nA
    EC_GHz: float = 8.0           # C = 2.42 fF (junction + local stray)
    Lambda: float = 2.5           # Josephson length in cells: L_J / L = Lambda^2 -> L = 0.66 nH (granular Al)
    pitch_um: float = 2.0         # array period
    alpha: float = 0.0            # sub-gap damping G/(C omega_p); ~1e-6 or below for Al at 20 mK (see FEASIBILITY)
    T_K: float = 0.020

    # ---- circuit elements
    @property
    def Ic_A(self) -> float:
        return self.EJ_GHz * 1e9 * H * 2 * math.pi / PHI0

    @property
    def C_F(self) -> float:
        return E_CHARGE ** 2 / (2 * self.EC_GHz * 1e9 * H)

    @property
    def LJ_H(self) -> float:
        return (PHI0 / (2 * math.pi)) ** 2 / (self.EJ_GHz * 1e9 * H)

    @property
    def L_cell_H(self) -> float:
        return self.LJ_H / self.Lambda ** 2

    # ---- sine-Gordon scales
    @property
    def fp_GHz(self) -> float:
        return math.sqrt(8 * self.EJ_GHz * self.EC_GHz)

    @property
    def E0_GHz(self) -> float:
        """continuum fluxon rest energy 8 E_J Lambda"""
        return 8 * self.EJ_GHz * self.Lambda

    @property
    def hc0_GHz_cell(self) -> float:
        """hbar * c0 expressed in GHz*h*cell (c0 = Lambda * omega_p cells per second)"""
        return self.Lambda * self.fp_GHz

    @property
    def c0_cells_per_ns(self) -> float:
        return self.Lambda * 2 * math.pi * self.fp_GHz

    @property
    def beta2_qsg(self) -> float:
        """quantum sine-Gordon coupling beta^2 = 8 hbar omega_p / E0 (semiclassical limit beta^2 -> 0)"""
        return 8 * self.fp_GHz / self.E0_GHz

    @property
    def EJ_over_hfp(self) -> float:
        return self.EJ_GHz / self.fp_GHz

    @property
    def kT_GHz(self) -> float:
        return KB * self.T_K / H / 1e9

    def summary(self) -> dict:
        d = asdict(self)
        d.update(Ic_nA=self.Ic_A * 1e9, C_fF=self.C_F * 1e15, LJ_nH=self.LJ_H * 1e9, L_cell_nH=self.L_cell_H * 1e9,
                 fp_GHz=self.fp_GHz, E0_GHz=self.E0_GHz, hc0_GHz_cell=self.hc0_GHz_cell,
                 c0_um_per_ns=self.c0_cells_per_ns * self.pitch_um, beta2_qsg=self.beta2_qsg,
                 soliton_over_plasmon=self.E0_GHz / self.fp_GHz, kT_GHz=self.kT_GHz)
        return d


@dataclass
class CouplerParams:
    """Collision coupler between rails A1 and B1 (and identical dummy couplers on A0 and B0).
    k : mutual-inductance fraction M/L of a shared inductor L_s = k L per cell, self-inductance compensated
    c : coupling capacitance C_c / C between facing nodes, node capacitance compensated
    HYPOTHETICAL design values; k and c are the knobs the optimiser sets."""
    k: float = 0.0121
    c: float = 0.134
    n_plateau: int = 400          # cells with full coupling
    n_taper: int = 40             # raised-cosine ramp at each end (keeps single-fluxon reflection negligible)

    def envelope(self, n_total: int, start: int) -> "list[float]":
        g = [0.0] * n_total
        for i in range(n_total):
            j = i - start
            if 0 <= j < self.n_taper:
                g[i] = 0.5 * (1 - math.cos(math.pi * (j + 0.5) / self.n_taper))
            elif self.n_taper <= j < self.n_taper + self.n_plateau:
                g[i] = 1.0
            elif self.n_taper + self.n_plateau <= j < 2 * self.n_taper + self.n_plateau:
                jj = j - self.n_taper - self.n_plateau
                g[i] = 0.5 * (1 + math.cos(math.pi * (jj + 0.5) / self.n_taper))
        return g


def phase_prefactor(rail: RailParams) -> float:
    """Gamma in  Delta(beta) = Gamma (k~/beta + c beta),  Gamma = 2 pi^2 Lambda E_J / (h f_p)."""
    return 2 * math.pi ** 2 * rail.Lambda * rail.EJ_over_hfp


def circuit_values(rail: RailParams, cp: CouplerParams) -> dict:
    """Coupler element values in SI-friendly units."""
    return dict(L_s_pH=cp.k * rail.L_cell_H * 1e12, C_c_fF=cp.c * rail.C_F * 1e15,
                series_L_in_coupler_pH=(1 - cp.k) * rail.L_cell_H * 1e12,
                node_C_in_coupler_fF=(1 - cp.c) * rail.C_F * 1e15)


DEFAULT_RAIL = RailParams()
DEFAULT_COUPLER = CouplerParams()
