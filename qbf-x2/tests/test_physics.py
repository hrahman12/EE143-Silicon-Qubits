"""Physics regression tests: every test checks a law or an established result, not a stored number."""
import math

import numpy as np
import pytest

from classical import exact
from classical.sg import MultiRailSG, Coupler, kink, kink_centres, rest_energy_numeric
from hardware.params import RailParams, CouplerParams
from quantum.fluxon import FluxonModel
from scattering import eikonal
from scattering.wavepacket import OneFluxonPropagator, TwoFluxonPropagator, gaussian

RAIL = RailParams()


@pytest.fixture(scope="module")
def model():
    return FluxonModel(RAIL)


# ---------------------------------------------------------------- classical circuit model
def test_rest_energy_continuum_limit():
    assert abs(rest_energy_numeric(10.0) / 80.0 - 1) < 1e-3          # 8 Lambda E_J


def test_free_kink_energy_conservation_and_relativistic_energy():
    N, Lam, beta = 700, 2.5, 0.4
    sim = MultiRailSG(N, 1, Lam)
    p, d = kink(np.arange(N), 150.0, Lam, v=beta * Lam)
    p, d = p[:, None], d[:, None]
    e0 = sim.energy(p, d)
    pT, dT, _ = sim.run(p, d, t_end=200.0, dt=0.05)
    assert abs(sim.energy(pT, dT) - e0) / e0 < 1e-5
    assert abs(e0 / (rest_energy_numeric(Lam) / math.sqrt(1 - beta ** 2)) - 1) < 0.01


def test_exact_sine_gordon_kink_antikink_shift():
    L_, beta, N = 10.0, 0.3, 1400
    n = np.arange(N)
    sim = MultiRailSG(N, 1, L_)
    p1, d1 = kink(n, 500.0, L_, v=beta * L_, polarity=+1)
    p2, d2 = kink(n, 900.0, L_, v=-beta * L_, polarity=-1)
    T = 400 / (beta * L_)
    pT, _, _ = sim.run((p1 + p2 - 2 * np.pi)[:, None], (d1 + d2)[:, None], t_end=T, dt=0.05)
    c = kink_centres(pT[:, 0], 2)
    shift = 0.5 * ((c[1] - (500 + beta * L_ * T)) + ((900 - beta * L_ * T) - c[0]))
    assert abs(shift / exact.kink_antikink_shift_cells(beta, L_) - 1) < 0.03


def test_sweet_spot_conditional_shift_changes_sign():
    Lam, N = RAIL.Lambda, 1100
    k, c = exact.coupler_for(math.pi, 0.30, Lam, RAIL.EJ_over_hfp)
    n = np.arange(N)
    env = np.array(CouplerParams(n_plateau=500, n_taper=40).envelope(N, 260))
    shifts = []
    for beta in (0.24, 0.36):
        xs = []
        for both in (True, False):
            sim = MultiRailSG(N, 2, Lam, couplers=[Coupler(0, 1, k, c, env)])
            phi, dphi = np.zeros((N, 2)), np.zeros((N, 2))
            phi[:, 0], dphi[:, 0] = kink(n, 200.0, Lam, v=beta * Lam)
            if both:
                phi[:, 1], dphi[:, 1] = kink(n, 900.0, Lam, v=-beta * Lam)
            pT, _, _ = sim.run(phi, dphi, t_end=700 / (beta * Lam), dt=0.05)
            xs.append(kink_centres(pT[:, 0])[0])
        shifts.append(xs[0] - xs[1])
    assert shifts[0] > 0.05 and shifts[1] < -0.05                         # advance below, delay above beta*


def test_first_order_design_formula():
    k, c = exact.coupler_for(math.pi, 0.3, 2.5, RAIL.EJ_over_hfp)
    d = lambda b: exact.conditional_phase(b, 2.5, k, c, RAIL.EJ_over_hfp)
    assert abs(d(0.3) - math.pi) < 1e-9
    assert abs((d(0.301) - d(0.299)) / 0.002) < 1e-3                       # stationary
    assert abs(exact.shift_A_cells(0.3, 2.5, k, c, 20.0)) < 1e-9          # zero classical delay at the same point


# ---------------------------------------------------------------- quantum model
def test_overlap_integral_is_shape_independent(model):
    rr = np.linspace(-80, 80, 3201)
    for g in (1.0, 1.25):
        assert abs(np.trapezoid(model.overlap(rr, gamma=g), rr) / (2 * math.pi) ** 2 - 1) < 1e-6


def test_group_velocity_matches_beta(model):
    for beta in (0.2, 0.45):
        assert abs(model.u(model.k_for_beta(beta)) / (beta * RAIL.Lambda) - 1) < 1e-9


def test_free_wavepacket_unitary_and_moves_at_group_velocity(model):
    pr = OneFluxonPropagator(model, n=2048, dx=0.25)
    k0 = model.k_for_beta(0.3)
    psi = gaussian(pr.x, -100, k0, 5.0)
    out, _ = pr.run(psi, 0.5, 0.002)
    w = np.abs(out) ** 2
    assert abs(np.sum(w) / np.sum(np.abs(psi) ** 2) - 1) < 1e-10
    xm = np.sum(pr.x * w) / np.sum(w)
    assert abs((xm + 100) / (model.v_cells_per_ns(k0) * pr.t_last) - 1) < 2e-3


def test_two_fluxon_phase_equals_eikonal_in_weak_coupling(model):
    cp = CouplerParams(k=0.0012, c=0.0)
    pr = TwoFluxonPropagator(model, cp, n=512, dx=0.5, cross=False)
    k0 = model.k_for_beta(0.3)
    v = model.v_cells_per_ns(k0)
    x = pr.x
    psi0 = gaussian(x, -70, k0, 10.0)[:, None] * gaussian(x, 70, -k0, 10.0)[None, :]
    psi, _, drift = pr.run(psi0, 140 / v, 0.002)
    om = np.vdot(pr.free(psi0, pr.t_last), psi) / np.vdot(psi0, psi0)
    eik = eikonal.overlap_pure(model, cp, k0, -k0, 0.05, 0.05)
    assert abs(drift) < 1e-10
    assert abs(np.angle(om) / np.angle(eik) - 1) < 0.01


def test_eikonal_phase_stationary_at_designed_sweet_spot(model):
    k, c = exact.coupler_for(math.pi, 0.3, RAIL.Lambda, RAIL.EJ_over_hfp)
    cp = CouplerParams(k=k, c=c)
    d = lambda b: float(eikonal.delta(model, cp, model.k_for_beta(b), -model.k_for_beta(b)))
    assert abs(d(0.3) - math.pi) < 1e-6
    assert abs((d(0.302) - d(0.298)) / 0.004) < 0.02
