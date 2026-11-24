"""Split-operator propagation of one and two fluxon wavepackets (energies GHz*h, time ns, lengths cells).

Two-fluxon Hamiltonian (quantum/fluxon.py):  H = E(k_A) + E(k_B) - A O(r) g(x_m) + B * 1/2 {u_A u_B, O(r) g(x_m)}
r = X_A - X_B, x_m = (X_A + X_B)/2, g = coupler envelope. The velocity coupling is applied with a 4th-order
Taylor series inside a symmetric (Strang) splitting; its norm is small (B |u|^2 O << 1/dt), and the norm drift is
reported by every run.
"""
from __future__ import annotations

import math

import numpy as np
import scipy.fft as sfft

TWO_PI = 2 * math.pi


def kgrid(n, dx):
    return TWO_PI * sfft.fftfreq(n, d=dx)


def gaussian(x, x0, k0, sigma):
    return (2 * math.pi * sigma ** 2) ** -0.25 * np.exp(-(x - x0) ** 2 / (4 * sigma ** 2) + 1j * k0 * (x - x0))


def fft2(a):
    return sfft.fft2(a, norm="ortho", workers=-1)


def ifft2(a):
    return sfft.ifft2(a, norm="ortho", workers=-1)


class OneFluxonPropagator:
    def __init__(self, model, n=4096, dx=0.25, V=None):
        self.model, self.n, self.dx = model, n, dx
        self.x = (np.arange(n) - n // 2) * dx
        self.k = kgrid(n, dx)
        self.E = model.energy(self.k)
        self.V = np.zeros(n) if V is None else V

    def run(self, psi, t_end, dt, n_snap=0):
        kin = np.exp(-1j * TWO_PI * self.E * dt)
        half = np.exp(-1j * TWO_PI * self.V * dt / 2)
        snaps = []
        n_steps = int(round(t_end / dt))
        every = max(1, n_steps // n_snap) if n_snap else 0
        for s in range(n_steps):
            if every and s % every == 0:
                snaps.append((s * dt, np.abs(psi) ** 2))
            psi = half * sfft.ifft(kin * sfft.fft(half * psi, norm="ortho"), norm="ortho")
        snaps.append((n_steps * dt, np.abs(psi) ** 2))
        self.t_last = n_steps * dt
        return psi, snaps


class TwoFluxonPropagator:
    def __init__(self, model, coupler, n=512, dx=0.5, envelope=None, gamma=1.0, cross=True):
        """envelope: callable g(x_m) (None = uniform coupler)."""
        self.model, self.n, self.dx = model, n, dx
        self.x = (np.arange(n) - n // 2) * dx
        self.k = kgrid(n, dx)
        XA, XB = self.x[:, None], self.x[None, :]
        r = XA - XB
        rr = np.linspace(-80, 80, 3201)
        O = np.interp(r, rr, model.overlap(rr, gamma=gamma), left=0.0, right=0.0)
        g = np.ones_like(O) if envelope is None else envelope(0.5 * (XA + XB))
        self.A, self.B = model.interaction_coeffs(coupler)
        self.Og = O * g
        self.V = -self.A * self.Og
        self.W = self.B * self.Og if cross else None
        self.T = model.energy(self.k)[:, None] + model.energy(self.k)[None, :]
        self.uu = model.u(self.k)[:, None] * model.u(self.k)[None, :]

    def cross_apply(self, psi):
        a = ifft2(self.uu * fft2(self.W * psi))
        b = self.W * ifft2(self.uu * fft2(psi))
        return 0.5 * (a + b)

    def run(self, psi, t_end, dt, snap_times=()):
        kin = np.exp(-1j * TWO_PI * self.T * dt)
        vhalf = np.exp(-1j * TWO_PI * self.V * dt / 2)
        n_steps = int(round(t_end / dt))
        snap_steps = {int(round(t / dt)): t for t in snap_times}
        snaps = {}
        norm0 = float(np.sum(np.abs(psi) ** 2))
        for s in range(n_steps + 1):
            if s in snap_steps:
                snaps[snap_steps[s]] = psi.copy()
            if s == n_steps:
                break
            psi = vhalf * psi
            if self.W is not None:
                psi = self._cross_exp(psi, dt / 2)
            psi = ifft2(kin * fft2(psi))
            if self.W is not None:
                psi = self._cross_exp(psi, dt / 2)
            psi = vhalf * psi
        drift = float(np.sum(np.abs(psi) ** 2)) / norm0 - 1
        self.t_last = n_steps * dt                       # actual simulated time: use it for the free reference
        return psi, snaps, drift

    def _cross_exp(self, psi, tau):
        out, term = psi.copy(), psi
        for m in range(1, 5):
            term = (-1j * TWO_PI * tau / m) * self.cross_apply(term)
            out = out + term
        return out

    def free(self, psi0, t):
        return ifft2(np.exp(-1j * TWO_PI * self.T * t) * fft2(psi0))
