"""QBF-X2 preliminary architecture: sections along the fluxon paths and the element values of every cell type.

Topology (cross-section in the collision region, top to bottom):
    D_A | A0 | A1 || B1 | B0 | D_B
Launch rows (A0, A1 from the left; B1, B0 mirrored from the right) start with a coherent launcher
(hardware/launcher.py): rail-end load loop, a flux-bias trap and a flux-gradient accelerator, both driven by control
lines coupled by mutual inductance only.
Each row is a discrete long Josephson junction to the ground plane: a junction (E_J, C) from every node to ground,
a granular-Al series inductor L between nodes. Couplers (A1-B1 gate coupler, D_A-A0 and B0-D_B dummy couplers): the
two rows' ground returns share a narrow strip of inductance L_s = k L per cell (series L reduced to (1-k) L so the
self-inductance is unchanged) and facing nodes are joined by a coupling capacitor C_c = c C (node capacitance
reduced by C_c). Beam-splitter (BS) sections: rows 0 and 1 of one qubit merge into a ladder whose middle rail
carries series junctions (E_J,M / E_C,M = 2); a vortex hops between the rows by a phase slip of a middle-rail
junction (amplitude E_S). Along x (fluxon A moves +x, B moves -x):
    [load | launch (trap) | accelerate | BS A-prep | gap | taper | coupler plateau | taper | gap | BS A-analysis | idle | detect]
B rows are the mirror image (n -> N-1-n). The idle stretch makes every row symmetric about the coupler centre, so
the coupler (whose envelope is not mirrored) is at the same cells for A and B, and B's launcher and BS_prep lie on
the far side of the coupler, mirroring A's.
B mirrors this from the right. Everything here is a PROPOSAL: values marked 'validated' come from this repo's
simulations, the rest are design assumptions (see FEASIBILITY.md).
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field, asdict

import numpy as np

from hardware.params import RailParams, CouplerParams, PHI0, H, E_CHARGE

JC_UA_PER_UM2 = 2.1            # one Al/AlOx/Al oxidation for every junction on the chip. Higher than QFX-1's
                               # 1.665 uA/um^2, so each junction carries less capacitance than its node needs and
                               # the rest is an explicit shunt: the couplers compensate C_c by reducing that shunt
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
    E_S_GHz: float = 0.58                 # set by design_middle_junction()
    EJ_M_GHz: float = 13.47
    EC_M_GHz: float = 6.74                # effective, network-loaded charging energy of the middle junction
    EJ_over_EC_M: float = 2.0             # beam-splitter design point (companion 2)
    C_island_geo_fF: float = 0.31         # island two-terminal geometric capacitance (layout target, from extraction)
    n_load: int = 10
    n_launch: int = 40
    n_accel: int = 40
    n_bs: int = 0
    n_gap: int = 20
    n_taper: int = 40
    n_plateau: int = 100
    n_detect: int = 10
    n_idle: int = 0                  # set in from_results: symmetry about the coupler centre
    source: str = ""
    launcher: object = None          # hardware.launcher.LauncherDesign (sized in from_results)

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
        a.design_middle_junction()
        from quantum.fluxon import FluxonModel
        m = FluxonModel(a.rail)
        v = m.v_cells_per_ns(m.k_for_beta(a.beta))
        a.n_bs = int(round(v / (8 * a.E_S_GHz)))                          # 50/50: 2 pi E_S tau = pi/4
        from hardware.launcher import design
        a.launcher = design(m, a.beta)
        a.n_load, a.n_launch, a.n_accel = a.launcher.n_load, a.launcher.n_launch, a.launcher.n_accel
        a.n_idle = a.n_load + a.n_launch + a.n_accel - a.n_detect             # post-coupler = pre-coupler length
        assert a.n_idle >= 0
        return a

    # ---- sections along x (cells)
    def sections(self):
        seq = [("load", self.n_load), ("launch", self.n_launch), ("accelerate", self.n_accel), ("BS_prep", self.n_bs),
               ("gap", self.n_gap),
               ("taper_in", self.n_taper), ("coupler", self.n_plateau), ("taper_out", self.n_taper), ("gap", self.n_gap),
               ("BS_analysis", self.n_bs), ("idle", self.n_idle), ("detect", self.n_detect)]
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
        C_node = r.C_F * 1e15                                             # total node capacitance (sets E_C)
        Cj = A * C_SPEC_FF_PER_UM2
        C_c = self.c * C_node
        CjM = AM * C_SPEC_FF_PER_UM2
        C_net = Cj                                                        # rail-junction network seen across it
        C_M = CjM + self.C_island_geo_fF + C_net                          # effective, network-loaded
        return dict(
            rail_junction=dict(EJ_GHz=r.EJ_GHz, Ic_nA=r.Ic_A * 1e9, area_um2=A, C_fF=C_node, Cj_fF=Cj,
                               shunt_fF=C_node - Cj, shunt_on_coupler_plateau_fF=C_node - Cj - C_c,
                               status="validated by simulation (design point); node shunt = geometric node "
                                      "capacitance + trim, to be set by EM extraction"),
            rail_inductor=dict(L_nH=L * 1e9, squares_grAl=L * 1e9 / GRAL_NH_PER_SQ, status="proposed (granular Al)"),
            coupler_shared_inductor=dict(L_s_pH=self.k * L * 1e12, k=self.k, status="validated value; geometry proposed"),
            coupler_capacitor=dict(C_c_fF=self.c * r.C_F * 1e15, c=self.c, status="validated value; geometry proposed"),
            compensated_series_L_nH=(1 - self.k) * L * 1e9,
            compensated_node_C_fF=(1 - self.c) * r.C_F * 1e15,
            middle_rail_junction=dict(EJ_GHz=self.EJ_M_GHz, EC_GHz=self.EC_M_GHz, Ic_nA=AM * JC_UA_PER_UM2 * 1e3,
                                      area_um2=AM, Cj_fF=CjM, C_island_geo_fF=self.C_island_geo_fF, C_network_fF=C_net,
                                      C_fF=C_M, shunt_fF=0.0, E_S_GHz=self.E_S_GHz, EJ_over_EC=self.EJ_M_GHz / self.EC_M_GHz,
                                      status="E_C,eff counts the rail-junction network (each island couples to both rails "
                                             "through rail junctions); E_S = charge dispersion / 4 (scqubits); vortex "
                                             "hopping itself is still the single-junction phase-slip estimate"),
            launcher=self.launcher_values(),
            detector=dict(kind="fluxon catcher loop + dispersive lambda/4 readout (QFX-1 heritage)", status="proposed"),
        )

    def summary(self) -> dict:
        d = dict(beta=self.beta, k=self.k, c=self.c, E_S_GHz=self.E_S_GHz, n_bs=self.n_bs, n_cells_per_row=self.n_cells,
                 length_um=self.n_cells * self.rail.pitch_um, rows=["D_A", "A0", "A1", "B1", "B0", "D_B"],
                 sections=self.sections(), elements=self.element_values(), source=self.source)
        return d

    def launcher_values(self) -> dict:
        """targets for the launch rows: control-line mutual inductances per rail cell (pH), currents, load loop"""
        if self.launcher is None:
            return dict(status="not sized")
        d = self.launcher
        n_cells = self.n_cells
        M = d.mutual_targets_pH(n_cells)
        cells_t = [int(i) for i in np.nonzero(M["trap"] > 1e-4 * M["trap"].max())[0]]
        cells_a = [int(i) for i in np.nonzero(M["accelerator"] > 1e-4 * M["accelerator"].max())[0]]
        return dict(rows=["A0", "A1", "B1", "B0"], mirrored_rows=["B1", "B0"],
                    trap_line=dict(I_uA=d.I_trap_uA, cells=cells_t, M_pH=[float(M["trap"][i]) for i in cells_t],
                                   waveform="DC while loading/holding; off at release (edge tau)"),
                    accelerator_line=dict(I_uA=d.I_acc_uA, cells=cells_a, M_pH=[float(M["accelerator"][i]) for i in cells_a],
                                          waveform="on at release (edge tau), off at t_off while the fluxon is on the plateau"),
                    load_loop=dict(L_nH=1.0, flux_ramp="0 -> Phi0 in about 1 us (inserts one fluxon adiabatically)"),
                    tau_ps=d.tau_ps, t_off_ns=d.t_off_ns, trap_frequency_GHz=d.f_trap_GHz,
                    trap_depth_GHz=d.notes.get("trap_depth_GHz"), force_GHz_per_cell=d.notes.get("F_GHz_per_cell"),
                    status="proposed; sized by simulation (simulations/D_launcher.py)")

    def symmetry_report(self) -> dict:
        """the coupler must sit at the row centre so that mirrored B rows meet it after their own BS_prep"""
        s = {d["name"]: d for d in self.sections()}
        N = self.n_cells
        c0 = s["taper_in"]["start"]
        c1 = s["taper_out"]["start"] + s["taper_out"]["cells"]
        pre, post = c0, N - c1
        b_prep = (N - (s["BS_prep"]["start"] + s["BS_prep"]["cells"]), N - s["BS_prep"]["start"])   # B's BS_prep range
        return dict(n_cells=N, coupler_cells=[c0, c1], pre_coupler=pre, post_coupler=post, symmetric=pre == post,
                    B_BS_prep_cells=list(b_prep), B_BS_prep_after_coupler=b_prep[0] >= c1)

    def design_middle_junction(self):
        """Size the beam-splitter middle-rail junction so that E_J,M / E_C,eff = EJ_over_EC_M, where the effective
        capacitance across it is network-loaded: C_eff = Cj,M + C_island_geo + Cj,rail. Each island couples to both rails
        through a rail junction, and the two islands of a middle junction act in series, which puts about Cj,rail across
        it; the EM extraction found this term. Leaving it out over-estimates E_S about 8x (0.14 GHz instead of 1.1 GHz
        for the earlier 25.3 GHz junction). E_S = charge dispersion / 4 (scqubits), as in companion 2."""
        import scqubits as scq
        scq.settings.T1_DEFAULT_WARNING = False
        e2_2h = E_CHARGE ** 2 / (2 * H) * 1e15 / 1e9                     # GHz * fF
        alpha = jj_area_for(1.0) * C_SPEC_FF_PER_UM2                      # junction fF per GHz of E_J
        b = jj_area_for(self.rail.EJ_GHz) * C_SPEC_FF_PER_UM2 + self.C_island_geo_fF
        c = -self.EJ_over_EC_M * e2_2h
        self.EJ_M_GHz = (-b + math.sqrt(b * b - 4 * alpha * c)) / (2 * alpha)
        self.EC_M_GHz = e2_2h / (b + alpha * self.EJ_M_GHz)
        t = scq.Transmon(EJ=self.EJ_M_GHz, EC=self.EC_M_GHz, ng=0.0, ncut=31, truncated_dim=2)
        e0 = t.eigenvals(evals_count=1)[0]
        t.ng = 0.5
        self.E_S_GHz = abs(t.eigenvals(evals_count=1)[0] - e0) / 4
