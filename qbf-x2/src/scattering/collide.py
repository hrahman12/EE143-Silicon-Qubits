"""One quantum two-fluxon collision on rails A1/B1, analysed against the free (non-interacting) branches.

Branches 00, 01, 10 propagate freely (dummy couplers make their single-particle physics identical to the coupled
rails), branch 11 propagates with the interaction. Both are evolved from the same product wavepacket.
"""
from __future__ import annotations

import math

import numpy as np

from scattering.wavepacket import TwoFluxonPropagator, gaussian
from gates.metrics import motional_schmidt


def run_collision(model, cp, beta, sigma=10.0, n=512, dx=0.5, dt=0.002, x0=70.0, envelope=None,
                  t_offset=0.0, beta_B=None, snap_fracs=(), taylor=4, cross=True, keep_states=False):
    """Fluxon A starts at -x0 moving right, B at +x0 moving left. t_offset > 0 launches B later (its start is
    moved back along its path by v_B t_offset). Returns metrics of the |11> branch relative to the free branch."""
    kA = model.k_for_beta(beta)
    kB = model.k_for_beta(beta if beta_B is None else beta_B)
    vA, vB = model.v_cells_per_ns(kA), model.v_cells_per_ns(kB)
    prop = TwoFluxonPropagator(model, cp, n=n, dx=dx, envelope=envelope, cross=cross and cp.c > 0)
    if taylor != 4:
        prop._cross_exp = _taylor(prop, taylor)
    x = prop.x
    xB0 = x0 + vB * t_offset
    psi0 = gaussian(x, -x0, kA, sigma)[:, None] * gaussian(x, xB0, -kB, sigma)[None, :]
    psi0 /= math.sqrt(np.sum(np.abs(psi0) ** 2))
    T = (x0 + xB0) / (vA + vB) * 2.0
    snaps = [f * T for f in snap_fracs]
    psi, sn, drift = prop.run(psi0, T, dt, snap_times=snaps)
    t = prop.t_last
    free = prop.free(psi0, t)
    meet = -x0 + vA * (x0 + xB0) / (vA + vB)                  # classical meeting point
    XA, XB = x[:, None], x[None, :]
    P = (XA > meet) & (XB < meet)                             # both transmitted past each other
    omega = complex(np.vdot(free[P], psi[P]))
    p11 = float(np.sum(np.abs(psi[P]) ** 2))
    pA = np.sum(np.abs(psi) ** 2, axis=1)
    pA0 = np.sum(np.abs(free) ** 2, axis=1)
    dXA = float(np.sum(x * pA) - np.sum(x * pA0))
    pur, sch = motional_schmidt(psi, dx)
    pur0, _ = motional_schmidt(psi0, dx)
    out = dict(beta=beta, beta_B=beta if beta_B is None else beta_B, sigma=sigma, n=n, dx=dx, dt=dt, t_final=t,
               omega=omega, phase=float(np.angle(omega)), overlap_abs=abs(omega), p11=p11, reflection=1 - p11,
               norm_drift=drift, dXA_quantum=dXA, motional_purity_out=pur, motional_purity_in=pur0,
               schmidt_top=sch.tolist(), meeting_point=meet)
    if keep_states:
        out.update(psi=psi, free=free, psi0=psi0, x=x, snaps=sn, T=T)
    return out


def _taylor(prop, order):
    def f(psi, tau):
        out, term = psi.copy(), psi
        for m in range(1, order + 1):
            term = (-1j * 2 * math.pi * tau / m) * prop.cross_apply(term)
            out = out + term
        return out
    return f

def run_collision_states(model, cp, psiA, psiB, n=1024, dx=0.5, dt=0.002, envelope=None, T=None, keep_states=False):
    """Collision of two arbitrary single-fluxon states psiA(x), psiB(x) given on the propagator grid
    x = (arange(n) - n/2) dx (A moving +x, B moving -x), e.g. the wavepackets produced by the launcher.
    Same analysis as run_collision: the |11> branch against the freely evolved product state."""
    prop = TwoFluxonPropagator(model, cp, n=n, dx=dx, envelope=envelope, cross=cp.c > 0)
    x = prop.x
    nA = math.sqrt(np.sum(np.abs(psiA) ** 2))
    nB = math.sqrt(np.sum(np.abs(psiB) ** 2))
    psi0 = (psiA / nA)[:, None] * (psiB / nB)[None, :]
    rhoA, rhoB = np.abs(psiA / nA) ** 2, np.abs(psiB / nB) ** 2
    xA, xB = float(np.sum(x * rhoA)), float(np.sum(x * rhoB))
    k = prop.k
    vk = model.v_cells_per_ns(k)
    vA = float(np.sum(vk * np.abs(np.fft.fft(psiA)) ** 2) / np.sum(np.abs(np.fft.fft(psiA)) ** 2))
    vB = float(np.sum(vk * np.abs(np.fft.fft(psiB)) ** 2) / np.sum(np.abs(np.fft.fft(psiB)) ** 2))
    t_meet = (xB - xA) / (vA - vB)
    meet = xA + vA * t_meet
    T = 2.0 * t_meet if T is None else T
    psi, _, drift = prop.run(psi0, T, dt)
    t = prop.t_last
    free = prop.free(psi0, t)
    XA, XB = x[:, None], x[None, :]
    P = (XA > meet) & (XB < meet)
    omega = complex(np.vdot(free[P], psi[P]))
    p11 = float(np.sum(np.abs(psi[P]) ** 2))
    pA = np.sum(np.abs(psi) ** 2, axis=1)
    pA0 = np.sum(np.abs(free) ** 2, axis=1)
    dXA = float(np.sum(x * pA) - np.sum(x * pA0))
    pur, sch = motional_schmidt(psi, dx)
    pur0, _ = motional_schmidt(psi0, dx)
    out = dict(n=n, dx=dx, dt=dt, t_final=t, x_A0=xA, x_B0=xB, v_A=vA, v_B=vB, meeting_point=meet,
               omega=omega, phase=float(np.angle(omega)), overlap_abs=abs(omega), p11=p11, reflection=1 - p11,
               norm_drift=drift, dXA_quantum=dXA, motional_purity_out=pur, motional_purity_in=pur0,
               schmidt_top=sch.tolist())
    if keep_states:
        out.update(psi=psi, free=free, psi0=psi0, x=x)
    return out
