"""Cut-off frequencies of the on-board DC filters, computed from the component values (no fitting).

Gate lines  (into a high-impedance gate electrode):  V_in -[R1]-+-[R2]-+- gate
                                                                 C1     C2
    H(s) = 1 / (1 + s (R1 C1 + R2 C2 + R1 C2) + s^2 R1 C1 R2 C2)          (R1 includes the source resistance)

Load lines  (R-C-R T-section):                        V_in -[R1]-+-[R2]- load
                                                                  C
    current into an on-chip short (load loop, L ~ 1 nH):  I/V = 1 / (R1 + Z2 + s C R1 Z2),  Z2 = R2 + s L
    voltage into a high-impedance load:                   V/V = 1 / (1 + s R1 C)

-3 dB points are found by bisection on |H(j 2 pi f)| / |H(0)| = 1/sqrt(2).
"""
import math


def _f3db(mag, f_lo=1e-3, f_hi=1e12):
    h0 = mag(f_lo)
    target = h0 / math.sqrt(2)
    lo, hi = math.log10(f_lo), math.log10(f_hi)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mag(10 ** mid) > target:
            lo = mid
        else:
            hi = mid
    return 10 ** (0.5 * (lo + hi))


def gate_ladder(R1, C1, R2, C2, Rs=0.0):
    R1e = R1 + Rs

    def mag(f):
        s = 2j * math.pi * f
        return abs(1 / (1 + s * (R1e * C1 + R2 * C2 + R1e * C2) + s * s * R1e * C1 * R2 * C2))
    return dict(f3db=_f3db(mag), f_single=1 / (2 * math.pi * R1 * C1),
                atten_1MHz_dB=20 * math.log10(mag(1e6) / mag(1e-3)))


def load_tee(R1, C, R2, Rs=0.0, L=0.0):
    R1e = R1 + Rs

    def mag_i(f):
        s = 2j * math.pi * f
        z2 = R2 + s * L
        return abs(1 / (R1e + z2 + s * C * R1e * z2))

    def mag_v(f):
        s = 2j * math.pi * f
        return abs(1 / (1 + s * R1e * C))
    fi, fv = _f3db(mag_i), _f3db(mag_v)
    return dict(f3db_current=fi, f3db_open=fv,
                formula_current=1 / (2 * math.pi * C * (R1e * R2 / (R1e + R2))),
                formula_open=1 / (2 * math.pi * R1e * C),
                tau_current_ns=1e9 / (2 * math.pi * fi), tau_open_ns=1e9 / (2 * math.pi * fv),
                atten_1GHz_dB=20 * math.log10(mag_i(1e9) / mag_i(1e-3)))


def all_cutoffs(F):
    g, l, Rs, L = F["gate"], F["load"], F["source_R"], F["load_loop_L"]
    return dict(
        gate=gate_ladder(g["R1"], g["C1"], g["R2"], g["C2"]),
        gate_50ohm=gate_ladder(g["R1"], g["C1"], g["R2"], g["C2"], Rs),
        load=load_tee(l["R1"], l["C"], l["R2"], 0.0, L),
        load_50ohm=load_tee(l["R1"], l["C"], l["R2"], Rs, L),
    )


def eng(v, unit):
    for k, p in ((1e9, "G"), (1e6, "M"), (1e3, "k"), (1, ""), (1e-3, "m"), (1e-6, "u"), (1e-9, "n"), (1e-12, "p")):
        if abs(v) >= k:
            return f"{v / k:.3g} {p}{unit}"
    return f"{v:.3g} {unit}"
