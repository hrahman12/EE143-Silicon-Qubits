"""Tests of the coherent single-fluxon launcher (hardware/launcher.py, scattering/launch.py)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hardware.params import RailParams                      # noqa: E402
from quantum.fluxon import FluxonModel                       # noqa: E402
from hardware.launcher import design, potential, LauncherDesign   # noqa: E402
from scattering.launch import quantum_launch, classical_launch    # noqa: E402

RAIL = RailParams()
MODEL = FluxonModel(RAIL)


def test_flux_gradient_is_a_uniform_force():
    """theta_n = theta' n  ->  U(X) = -2 pi E_J Lambda^2 theta' X  (independent of the kink shape)"""
    n_cells, slope = 200, 1e-3
    th = slope * (np.arange(n_cells) + 0.5)
    X = np.linspace(60, 140, 81)
    U = potential(th, X, RAIL)
    F = -np.polyfit(X, U, 1)[0]
    F_expected = 2 * math.pi * RAIL.EJ_GHz * RAIL.Lambda ** 2 * slope
    assert abs(F / F_expected - 1) < 1e-3


def test_trap_sized_for_ground_state_at_20mK():
    d = design(MODEL, 0.45)
    assert abs(d.notes["f_trap_check_GHz"] - d.f_trap_GHz) < 0.01
    kT = d.notes["kT_GHz_20mK"]
    assert d.f_trap_GHz / kT > 5                    # thermal occupation < 1e-2
    assert d.notes["trap_depth_GHz"] / kT > 30      # no thermal escape
    # the accelerator delivers the kinetic energy of the target speed
    KE = MODEL.kinetic_energy(0.45)
    N = int(d.x_d) + 20
    drop = float(potential(d.theta_acc_profile(N), [d.X0], RAIL)[0] - potential(d.theta_acc_profile(N), [0.5 * (d.x_b + d.x_c)], RAIL)[0])
    assert abs(drop / KE - 1) < 0.01


def test_quantum_launch_beats_thermal_source():
    d = design(MODEL, 0.45)
    r = quantum_launch(d, MODEL, T_K=0.020, n_states=2, keep=False)
    assert abs(r["beta_mean"] / 0.45 - 1) < 0.01
    assert r["dv_over_v"] < 0.5 * MODEL.thermal_beta_spread(0.45, 0.020)
    assert all(abs(s["norm"] - 1) < 1e-6 for s in r["per_state"])


def test_classical_launch_single_fluxon():
    d = design(MODEL, 0.45)
    r = classical_launch(d, RAIL, N=420, x_probe=280.0)
    assert abs(r["winding"] - 1) < 0.01
    assert abs(r["beta"] / 0.45 - 1) < 0.02          # untrimmed; the accelerator amplitude trims the rest
    assert r["radiation_GHz"] < 1e-2 * r["KE_GHz"]
    h = classical_launch(d, RAIL, N=300, hold_only=True)
    assert h["drift_cells"] < 0.01
