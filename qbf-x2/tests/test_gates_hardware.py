"""Tests of the logical-gate metrics and of the hardware generators."""
import math
import os

import numpy as np

from gates.metrics import (gram_from_overlap, gate_report, logical_rho, concurrence, conditional_phase,
                           best_process_fidelity)
from optimization import budget as B
from hardware.architecture import Architecture
from hardware import netlist as NL
from hardware import layout as LY
from hardware.params import RailParams
from quantum.fluxon import FluxonModel

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_ideal_cz_is_maximally_entangling():
    r = gate_report(gram_from_overlap(-1.0))
    assert abs(r["concurrence"] - 1) < 1e-6                       # QuTiP sqrt-of-eigenvalue precision ~1e-8
    assert abs(r["bell_fidelity"] - 1) < 1e-6
    assert abs(r["process_fidelity_CZ"] - 1) < 1e-9
    assert abs(abs(r["conditional_phase_rad"]) - math.pi) < 1e-9


def test_no_interaction_no_entanglement():
    assert concurrence(logical_rho(gram_from_overlap(1.0))) < 1e-6


def test_which_path_distinguishability_reduces_entanglement():
    c1 = concurrence(logical_rho(gram_from_overlap(-0.95)))
    c2 = concurrence(logical_rho(gram_from_overlap(-0.80)))
    assert 0 < c2 < c1 < 1


def test_local_phases_are_free_but_conditional_phase_is_not():
    # optimal local Z phases absorb part of a conditional-phase error, but never all of it
    F = [best_process_fidelity(gram_from_overlap(np.exp(1j * (math.pi + d))))[0] for d in (0.0, 0.2, 0.4, 0.6)]
    assert abs(F[0] - 1) < 1e-9 and F[0] > F[1] > F[2] > F[3]
    assert F[3] < 0.98
    G = gram_from_overlap(np.exp(1j * (math.pi + 0.3)))
    assert abs(conditional_phase(G) - (math.pi + 0.3 - 2 * math.pi)) < 1e-9


def test_dephasing_infidelity_monotonic():
    a, b = B.cz_infidelity_from_dephasing(0.01), B.cz_infidelity_from_dephasing(0.05)
    assert 0 < a < b


def test_disorder_dephasing_falls_with_speed():
    m = FluxonModel(RailParams())
    d3 = B.disorder_dephasing(m, 0.3, 300, 0.02, 0.02, 0.02)[0]
    d6 = B.disorder_dephasing(m, 0.6, 300, 0.02, 0.02, 0.02)[0]
    assert d6 < d3


def test_netlist_complete_and_connected():
    arch = Architecture.from_results(ROOT)
    text, summ = NL.build(arch)
    p = NL.parse(text)
    assert not p["isolated"]
    assert summ["elements"]["launcher load loop inductor"] == 4 and summ["elements"]["catcher loop inductor"] == 4
    assert summ["elements"]["trap line source"] == 4 and summ["elements"]["accelerator line source"] == 4
    assert summ["elements"]["junction (rail)"] == 6 * arch.n_cells


def test_layout_builds(tmp_path):
    arch = Architecture.from_results(ROOT)
    dims = LY.build(arch, str(tmp_path / "t.gds"))
    assert os.path.getsize(tmp_path / "t.gds") > 10000
    assert dims["cells_per_row"] == arch.n_cells and dims["status"].startswith("PRELIMINARY")


def test_rows_symmetric_about_the_coupler():
    """B rows mirror A's section list; the coupler must therefore be centred so B meets it after its BS_prep"""
    arch = Architecture.from_results(ROOT)
    rep = arch.symmetry_report()
    assert rep["symmetric"] and rep["B_BS_prep_after_coupler"]
    for n in range(arch.n_cells):
        assert abs(NL._env(arch, n) - NL._env(arch, arch.n_cells - 1 - n)) < 1e-12
