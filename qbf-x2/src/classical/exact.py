"""Closed-form results used to validate the numerics.

1. Exact continuum sine-Gordon kink-antikink collision (textbook breather-free scattering solution)
       phi = 4 arctan[ sinh(gamma beta t) / (beta cosh(gamma x)) ]      (x in lambda_J, t in 1/omega_p)
   each soliton emerges advanced by  dx = (2/gamma) ln(1/beta)  lambda_J.
2. First-order (in the couplers) collective-coordinate action of two kinks on different rails passing each other,
   derived from the circuit Lagrangian in classical/sg.py with rigid kink profiles:
       L_int = [Lambda^2 k~ + c v_A v_B] O(X_A - X_B),   sum over r of O = (2 pi)^2   (shape independent)
       dS(v_A, v_B) = (2 pi)^2 (Lambda^2 k~ + c v_A v_B) / (v_A + v_B)        [units E_J / omega_p]
   k~ = k/(1-k^2). Quantum conditional phase: Delta = dS * E_J/(h f_p). Classical position shift of fluxon A
   (Hamilton-Jacobi): dX_A = - (d dS / d v_A) / (m gamma_A^3),  m = E0 / c0^2.
   Both vanish-or-extremise at the same velocity:  v*^2 = Lambda^2 k~ / c  (beta*^2 = k~/c).
"""
from __future__ import annotations

import math


def kink_antikink_shift_cells(beta: float, Lam: float) -> float:
    g = 1 / math.sqrt(1 - beta ** 2)
    return 2 / g * math.log(1 / beta) * Lam


def ktilde(k: float) -> float:
    return k / (1 - k * k)


def action_first_order(vA: float, vB: float, Lam: float, k: float, c: float) -> float:
    """vA, vB: speeds (cells per 1/omega_p), counter-propagating. Returns dS in E_J/omega_p."""
    return (2 * math.pi) ** 2 * (Lam ** 2 * ktilde(k) + c * vA * vB) / (vA + vB)


def conditional_phase(beta: float, Lam: float, k: float, c: float, EJ_over_hfp: float) -> float:
    v = beta * Lam
    return action_first_order(v, v, Lam, k, c) * EJ_over_hfp


def shift_A_cells(beta: float, Lam: float, k: float, c: float, E0_EJ: float) -> float:
    """predicted classical position shift of fluxon A after the collision (positive = advanced)."""
    v = beta * Lam
    g = 1 / math.sqrt(1 - beta ** 2)
    m = E0_EJ / Lam ** 2
    dSdvA = (2 * math.pi) ** 2 * (c * v * v - Lam ** 2 * ktilde(k)) / (2 * v) ** 2
    return -dSdvA / (m * g ** 3)


def sweet_spot_beta(k: float, c: float) -> float:
    return math.sqrt(ktilde(k) / c)


def coupler_for(delta: float, beta_star: float, Lam: float, EJ_over_hfp: float):
    """(k, c) such that the conditional phase is stationary at beta_star and equals delta there."""
    gam = 2 * math.pi ** 2 * Lam * EJ_over_hfp            # Delta = gam (k~/beta + c beta)
    c = delta / (2 * gam * beta_star)
    kt = c * beta_star ** 2
    k = (-1 + math.sqrt(1 + 4 * kt * kt)) / (2 * kt)       # invert k~ = k/(1-k^2)
    return k, c
