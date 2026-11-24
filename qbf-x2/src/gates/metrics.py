"""Logical two-qubit metrics of the collision gate.

The rail indices are conserved by the collision, so the logical channel is a Schur (element-wise) multiplier:
    rho_out[x, y] = rho_in[x, y] * G[x, y],   G[x, y] = <chi_y | P | chi_x>
where chi_x is the outgoing motional (two-fluxon) state of logical branch x in {00, 01, 10, 11} and P projects
onto 'both fluxons transmitted into their output ports' (the computational subspace). Everything that is not a
logical phase - wavepacket distinguishability, reflection, loss - shows up in G.
"""
from __future__ import annotations

import math

import numpy as np
import qutip as qt

H1 = np.array([[1, 1], [1, -1]]) / math.sqrt(2)
PHI_PLUS = np.array([1, 0, 0, 1]) / math.sqrt(2)
THETA_CZ = np.array([0.0, 0.0, 0.0, math.pi])


def gram_from_overlap(omega: complex, p11: float = 1.0, single=(1.0, 1.0, 1.0)) -> np.ndarray:
    """dummy couplers make the 00, 01, 10 motional states identical; omega = <chi_free|P|chi_11>."""
    G = np.ones((4, 4), complex)
    G[3, :3] = omega
    G[:3, 3] = np.conj(omega)
    G[3, 3] = p11
    return G


def gram_from_states(states, projector=None) -> np.ndarray:
    """states: list of 4 arrays (same shape); projector: boolean mask of the transmitted region."""
    P = np.ones_like(states[0], bool) if projector is None else projector
    G = np.zeros((4, 4), complex)
    for x in range(4):
        for y in range(4):
            G[x, y] = np.vdot(states[y][P], states[x][P])
    return G


def logical_rho(G, amps=(0.5, 0.5, 0.5, 0.5)) -> np.ndarray:
    a = np.asarray(amps, complex)
    return np.outer(a, a.conj()) * G


def _q(rho):
    return qt.Qobj(rho, dims=[[2, 2], [2, 2]])


def concurrence(rho) -> float:
    tr = np.real(np.trace(rho))
    return float(qt.concurrence(_q(rho / tr))) if tr > 0 else 0.0


def entanglement_of_formation(C: float) -> float:
    x = (1 + math.sqrt(max(0.0, 1 - C * C))) / 2
    return 0.0 if x >= 1 else float(-x * math.log2(x) - (1 - x) * math.log2(1 - x))


def entropy_A(rho) -> float:
    """von Neumann entropy (bits) of qubit A's reduced state; an entanglement measure only for pure rho."""
    r = _q(rho / np.real(np.trace(rho)))
    return float(qt.entropy_vn(r.ptrace(0), base=2))


def purity(rho) -> float:
    r = rho / np.real(np.trace(rho))
    return float(np.real(np.trace(r @ r)))


def bell_fidelity(rho, optimise_local_z=True) -> float:
    """fidelity with |Phi+> after a Hadamard on qubit B (CZ|++> -> Phi+), optionally after the best local Z
    rotations (single-qubit phases are calibratable and not part of the entangling capability)."""
    U = np.kron(np.eye(2), H1)
    best = 0.0
    grid = np.linspace(0, 2 * math.pi, 73) if optimise_local_z else [0.0]
    for a in grid:
        for b in grid:
            Z = np.diag(np.exp(1j * np.array([0, b, a, a + b])))
            r = U @ Z @ rho @ Z.conj().T @ U.conj().T
            best = max(best, float(np.real(PHI_PLUS.conj() @ r @ PHI_PLUS)))
    return best


def process_fidelity(G, theta=THETA_CZ) -> float:
    ph = np.exp(-1j * (theta[:, None] - theta[None, :]))
    return float(np.real(np.sum(G * ph)) / 16)


def best_process_fidelity(G) -> tuple[float, np.ndarray]:
    """maximise over local Z corrections (theta = a x_A + b x_B + pi x_A x_B)."""
    best, arg = -1.0, None
    for a in np.linspace(0, 2 * math.pi, 145):
        for b in np.linspace(0, 2 * math.pi, 145):
            th = np.array([0.0, b, a, a + b + math.pi])
            f = process_fidelity(G, th)
            if f > best:
                best, arg = f, th
    return best, arg


def average_gate_fidelity(F_pro: float, d: int = 4) -> float:
    return (d * F_pro + 1) / (d + 1)


def conditional_phase(G) -> float:
    """Delta = phi11 - phi10 - phi01 + phi00 read from the off-diagonal overlaps."""
    return float(np.angle(G[3, 0] * G[0, 0] / (G[2, 0] * G[1, 0])))


def gate_report(G) -> dict:
    rho = logical_rho(G)
    C = concurrence(rho)
    F_pro, th = best_process_fidelity(G)
    return dict(conditional_phase_rad=conditional_phase(G), overlap_abs=float(abs(G[3, 0])),
                leakage=float(1 - np.real(G[3, 3])), concurrence=C, entanglement_of_formation=entanglement_of_formation(C),
                entropy_A_bits=entropy_A(rho), logical_purity=purity(rho), bell_fidelity=bell_fidelity(rho),
                process_fidelity_CZ=F_pro, average_gate_fidelity_CZ=average_gate_fidelity(F_pro),
                distinguishability=float(1 - abs(G[3, 0]) / math.sqrt(max(np.real(G[3, 3]), 1e-300))))


def motional_schmidt(chi2d, dx: float):
    """Schmidt coefficients of a two-coordinate motional state (position-position entanglement between the two
    fluxons' centre coordinates). Purity 1 = product state."""
    s = np.linalg.svd(chi2d * dx, compute_uv=False)
    p = s ** 2 / np.sum(s ** 2)
    return float(np.sum(p ** 2)), p[:5]
