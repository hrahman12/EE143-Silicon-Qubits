"""QBF-X2 preliminary architecture: sections along the fluxon paths and the element values of every cell type.

Topology (cross-section in the collision region, top to bottom):
    D_A | A0 | A1 || B1 | B0 | D_B
Each row is a discrete long Josephson junction to the ground plane: a junction (E_J, C) from every node to ground,
a granular-Al series inductor L between nodes. Couplers (A1-B1 gate coupler, D_A-A0 and B0-D_B dummy couplers): the
two rows' ground returns share a narrow strip of inductance L_s = k L per cell (series L reduced to (1-k) L so the
self-inductance is unchanged) and facing nodes are joined by a coupling capacitor C_c = c C (node capacitance
reduced by C_c). Beam-splitter (BS) sections: rows 0 and 1 of one qubit merge into a ladder whose middle rail
carries series junctions (E_J,M / E_C,M = 2); a vortex hops between the rows by a phase slip of a middle-rail
junction (amplitude E_S). Along x (fluxon A moves +x, B moves -x):
    [inj A | acc A | BS A-prep | gap | taper | coupler plateau | taper | gap | BS A-analysis | detectors A]
B mirrors this from the right. Everything here is a PROPOSAL: values marked 'validated' come from this repo's
simulations, the rest are design assumptions (see FEASIBILITY.md).
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field, asdict

from hardware.params import RailParams, CouplerParams, PHI0, H, E_CHARGE

JC_UA_PER_UM2 = 1.665          # same Al/AlOx/Al process as QFX-1 (quantum_chip/)
C_SPEC_FF_PER_UM2 = 50.0
GRAL_NH_PER_SQ = 0.5           # granular Al sheet kinetic inductance (assumption, typical 20 nm film)


def jj_area_for(EJ_GHz: float) -> float:
    Ic_uA = EJ_GHz * 1e9 * H * 2 * math.pi / PHI0 * 1e6
    return Ic_uA / JC_UA_PER_UM2


@dataclass
class Architecture:
    rail: RailParams = field(default_factory=RailParams)
    beta: float = 0.45
    k: float = 0.0
    c: float = 0.0
    E_S_GHz: float = 1.09
    EJ_M_GHz: float = 25.3
    EC_M_GHz: float = 12.7
    n_inject: int = 10
    n_accel: int = 40
    n_bs: int = 0
    n_gap: int = 20
    n_taper: int = 40
    n_plateau: int = 100
    n_detect: int = 10
    source: str = ""

    @classmethod
    def from_results(cls, root: str) -> "Architecture":
        """take the calibrated optimum from results/C_gate.json and the router's beam-splitter physics."""
        a = cls()
        try:
            C = json.load(open(os.path.join(root, "results", "C_gate.json")))
            o = C["optimum_validation"]
            a.beta, a.k, a.c = o["beta"], o["calibrated"]["k"], o["calibrated"]["c"]
            a.source = "results/C_gate.json optimum_validation (2D-calibrated)"
        except Exception:
            from classical.exact import coupler_for
            a.k, a.c = coupler_for(math.pi, a.beta, a.rail.Lambda, a.rail.EJ_over_hfp)
            a.source = "first-order design (C_gate.json not found)"
        try:
            R = json.load(open(os.path.join(root, "results", "companion2_router.json")))
            es8 = R["qps_amplitude_GHz_vs_EJ_over_EC"]["2.0"]           # computed at E_C = 8 GHz, scales with E_C
            a.E_S_GHz = es8 * a.EC_M_GHz / 8.0
        except Exception:
            pass
        from quantum.fluxon import FluxonModel
        m = FluxonModel(a.rail)
        v = m.v_cells_per_ns(m.k_for_beta(a.beta))
        a.n_bs = int(round(v / (8 * a.E_S_GHz)))                          # 50/50: 2 pi E_S tau = pi/4
        return a

    # ---- sections along x (cells)
    def sections(self):
        seq = [("inject", self.n_inject), ("accelerate", self.n_accel), ("BS_prep", self.n_bs), ("gap", self.n_gap),
               ("taper_in", self.n_taper), ("coupler", self.n_plateau), ("taper_out", self.n_taper), ("gap", self.n_gap),
               ("BS_analysis", self.n_bs), ("detect", self.n_detect)]
        out, x = [], 0
        for name, n in seq:
            out.append(dict(name=name, start=x, cells=n))
            x += n
        return out

    @property
    def n_cells(self) -> int:
        return sum(s["cells"] for s in self.sections())

    def element_values(self) -> dict:
        r = self.rail
        L = r.L_cell_H
        A = jj_area_for(r.EJ_GHz)
        AM = jj_area_for(self.EJ_M_GHz)
        return dict(
            rail_junction=dict(EJ_GHz=r.EJ_GHz, Ic_nA=r.Ic_A * 1e9, area_um2=A, C_fF=r.C_F * 1e15,
                               C_from_area_fF=A * C_SPEC_FF_PER_UM2, status="validated by simulation (design point)"),
            rail_inductor=dict(L_nH=L * 1e9, squares_grAl=L * 1e9 / GRAL_NH_PER_SQ, status="proposed (granular Al)"),
            coupler_shared_inductor=dict(L_s_pH=self.k * L * 1e12, k=self.k, status="validated value; geometry proposed"),
            coupler_capacitor=dict(C_c_fF=self.c * r.C_F * 1e15, c=self.c, status="validated value; geometry proposed"),
            compensated_series_L_nH=(1 - self.k) * L * 1e9,
            compensated_node_C_fF=(1 - self.c) * r.C_F * 1e15,
            middle_rail_junction=dict(EJ_GHz=self.EJ_M_GHz, EC_GHz=self.EC_M_GHz, area_um2=AM, E_S_GHz=self.E_S_GHz,
                                      status="E_S from exact charge dispersion (scqubits); vortex hopping = single-junction estimate"),
            injection_junction=dict(Ic_nA=2 * r.Ic_A * 1e9, area_um2=2 * A, status="UNRESOLVED: coherent single-fluxon launcher"),
            detector=dict(kind="fluxon catcher loop + dispersive lambda/4 readout (QFX-1 heritage)", status="proposed"),
        )

    def summary(self) -> dict:
        d = dict(beta=self.beta, k=self.k, c=self.c, E_S_GHz=self.E_S_GHz, n_bs=self.n_bs, n_cells_per_row=self.n_cells,
                 length_um=self.n_cells * self.rail.pitch_um, rows=["D_A", "A0", "A1", "B1", "B0", "D_B"],
                 sections=self.sections(), elements=self.element_values(), source=self.source)
        return d
