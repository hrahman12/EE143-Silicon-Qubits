"""Closed-form transmission-line impedance used to size the PCB and die lines.

GCPW: conductor-backed coplanar waveguide (Ghione & Naldi conformal mapping, zero-thickness).
Stripline: symmetric stripline, IPC-2141 approximation (thickness included).
CPW on die: infinitely thick substrate CPW (KQC a/b on Si).
"""
import math
from scipy.special import ellipk
from scipy.optimize import brentq


def _kr(k):
    """K(k)/K(k') with modulus k (scipy uses parameter m = k^2)."""
    return ellipk(k * k) / ellipk(1 - k * k)


def gcpw_z0(w, g, h, er):
    a, b = w / 2, w / 2 + g
    k = a / b
    k1 = math.tanh(math.pi * a / (2 * h)) / math.tanh(math.pi * b / (2 * h))
    r, r1 = _kr(k), _kr(k1)
    eeff = (1 + er * r1 / r) / (1 + r1 / r)
    z0 = 60 * math.pi / math.sqrt(eeff) / (r + r1)
    return z0, eeff


def cpw_z0(w, g, er):
    k = w / (w + 2 * g)
    eeff = (er + 1) / 2
    return 30 * math.pi / math.sqrt(eeff) / _kr(k), eeff


def stripline_z0(w, t, b, er):
    return 60 / math.sqrt(er) * math.log(4 * b / (0.67 * math.pi * (0.8 * w + t)))


def solve_gcpw_width(g, h, er, z=50.0):
    return brentq(lambda w: gcpw_z0(w, g, h, er)[0] - z, 0.02, 3.0)


def solve_stripline_width(t, b, er, z=50.0):
    return brentq(lambda w: stripline_z0(w, t, b, er) - z, 0.02, 2.0)


if __name__ == "__main__":
    w = solve_gcpw_width(0.20, 0.203, 3.55)
    print("GCPW w for 50 ohm (g=0.2, h=0.203, RO4003C):", round(w, 3), gcpw_z0(round(w, 2), 0.2, 0.203, 3.55))
    print("stripline w:", solve_stripline_width(0.018, 0.418, 3.52))
    print("die CPW 10/6 on Si:", cpw_z0(10, 6, 11.45))
