"""First-order (eikonal / Born) two-fluxon S-matrix and the logical channel it induces.

For plane waves k_A, k_B on rails A1, B1 (signed velocities u_A, u_B in cells per 1/omega_p), the collision
multiplies the |11> amplitude by exp(i Delta) with
    Delta(k_A, k_B) = (E_J / h f_p) (2 pi)^2 [Lambda^2 k~ - c u_A u_B] / |u_A - u_B|  x  g(meeting point)
(the action of the first-order Lagrangian along the unperturbed paths). Reflection is exponentially small for a
smooth interaction (checked by the 2D propagation), so the outgoing |11> motional state is
chi_11(k_A, k_B) = chi_free(k_A, k_B) exp(i Delta). Overlaps with the free branches give the logical channel.
"""
from __future__ import annotations

import math

import numpy as np

from classical.exact import ktilde


def delta(model, cp, kA, kB, g=1.0):
    r = model.rail
    uA, uB = model.u(kA), model.u(kB)
    return (rail_prefactor(model) * (r.Lambda ** 2 * ktilde(cp.k) - cp.c * uA * uB) / np.abs(uA - uB)) * g


def rail_prefactor(model) -> float:
    return (2 * math.pi) ** 2 * model.rail.EJ_over_hfp


def gaussian_k(k, k0, sigma_k):
    return np.exp(-(k - k0) ** 2 / (2 * sigma_k ** 2))


def overlap_pure(model, cp, kA0, kB0, sigma_kA, sigma_kB, n=801, g=1.0):
    """<chi_free | chi_11> for Gaussian (pure) wavepackets with momentum widths sigma_k."""
    kA = kA0 + np.linspace(-6, 6, n) * sigma_kA
    kB = kB0 + np.linspace(-6, 6, n) * sigma_kB
    PA = gaussian_k(kA, kA0, sigma_kA)
    PB = gaussian_k(kB, kB0, sigma_kB)
    w = PA[:, None] * PB[None, :]
    w /= w.sum()
    D = delta(model, cp, kA[:, None], kB[None, :], g)
    return complex(np.sum(w * np.exp(1j * D)))


def overlap_thermal(model, cp, beta0, sigma_beta, n=801, g=1.0, beta0_B=None, sigma_beta_B=None):
    """ensemble average of exp(i Delta) over independent Gaussian velocity distributions of the two launchers."""
    bA = beta0 + np.linspace(-6, 6, n) * sigma_beta
    bB0 = beta0 if beta0_B is None else beta0_B
    sB = sigma_beta if sigma_beta_B is None else sigma_beta_B
    bB = bB0 + np.linspace(-6, 6, n) * sB
    bA, bB = bA[(bA > 0) & (bA < 0.99)], bB[(bB > 0) & (bB < 0.99)]
    kA = np.array([model.k_for_beta(b) for b in bA])
    kB = -np.array([model.k_for_beta(b) for b in bB])
    w = np.exp(-(bA - beta0) ** 2 / (2 * sigma_beta ** 2))[:, None] * np.exp(-(bB - bB0) ** 2 / (2 * sB ** 2))[None, :]
    w /= w.sum()
    D = delta(model, cp, kA[:, None], kB[None, :], g)
    return complex(np.sum(w * np.exp(1j * D)))
