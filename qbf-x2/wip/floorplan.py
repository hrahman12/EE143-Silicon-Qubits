"""QBF-X2 die floorplan: the 10 x 10 mm die around the frozen row block, with a die-level DRC and connectivity check.

Inputs (read only): circuits/qbfx2_layout.gds + circuits/block_ports.json (frozen row block and its port list) and
circuits/die_pads.json (chip-to-carrier contract: 24 launcher pads, positions and nets).  layout.py is never imported;
the process rules of hardware/drc.py are restated in RULES below (same values) so this file does not depend on a module
that is being edited.

    build_die(block_gds, block_ports_json, die_pads_json, out_gds) -> dict
    check_die(out_gds, die_pads_json, report_path) -> dict

Layers (mask layers are the block's; 100-104 are documentation layers that are not written to a mask)
    1/0  NB    150 nm Nb: ground plane with the flux-trapping hole array, CPW centre conductors, launchers, resonators,
               feedline, probe pads, alignment marks, orientation mark and chip label (etched into the ground plane)
    2/0  GRAL  granular Al: sheet-resistance test meander
    3/0  AL1   Al bottom electrode: test junction arrays, thin-Al strip test
    4/0  AL2   Al top electrode: ground straps across every CPW, signal crossovers (bridges), test structures
    6/0  DIEL  100 nm SiNx under every AL2 strap / bridge where it passes over Nb of another net
    10/0 text: launcher net names at the pad centres        10/1 text: block-port names on the die-level port conductor
    10/2 text: probe-pad names of the test structures         10/3 text: notes (crossover ids, mark names)
    100/0 die outline  101/0 dicing lane  102/0 launcher bond pads  102/1 probe pads  104/0 row-block outline

Ground-plane continuity ("airbridges") uses the existing process: AL2 straps on SiNx across the CPW (AL2 lands on the
ground on both sides through >= 1 um^2 Al-on-Nb contacts; DIEL covers the centre conductor and the gaps).  Under a
strap the 10 um centre conductor is necked to 2 um over 4 um, so a strap adds ~2.5 fF instead of ~12 fF.  Straps sit at
every bend (arc midpoint) and at most 300 um apart along every CPW; in the dense crossover fields next to the block
'bus straps' cross the whole 20 um-pitch bundle between crossover columns.

Topology of the pin map (why there are signal crossovers).  Seen from the block, the ports of a group leave the block
in the opposite cyclic order to the pads of die_pads.json, e.g. east edge top to bottom ACC_B1 (y=175), TRAP_B1 (155),
LOAD_B1 (135), but east pads top to bottom LOAD_B1 (y=8000), TRAP_B1 (6800), ACC_B1 (5600).  Curves joining the inner
boundary (block) to the outer boundary (pad ring) of an annulus without crossing keep their cyclic order, so these three
lines alone cannot be routed without a crossing; the same holds for the A1, A0 (+GATE_BSA_PREP) and B0 (+GATE_BSB_PREP)
groups.  Also, GATE_BSB_AN and GATE_BSB_PREP pads lie on the south edge between RO_IN and RO_OUT, so the RO_IN-RO_OUT
feedline separates them from the block: each crosses the feedline.  The readout catchers A0/A1 leave the top of the east
edge while the feedline runs south of the block.  A minimum-crossing search over windings and feedline orders gives 31
crossings in the annulus plus the 2 gate-feedline crossings = 33; this floorplan realises exactly that minimum.  Every
crossing is an insulated crossover (Nb lower line continuous, upper line on an AL2 bridge over SiNx); no two nets touch.
Bridging priority: gate lines bridge over everything; the readout lines bridge over flux lines (resonator current is
tiny); load lines bridge over trap/accelerator lines; trap (80 uA) bridges over accelerator (450 uA); the feedline and the
accelerator lines are never bridged in AL2.
"""
from __future__ import annotations

import json
import math
import os
import time

import numpy as np

# ===================================================================================================== layers / rules
L_NB, L_GRAL, L_AL1, L_AL2, L_DIEL = (1, 0), (2, 0), (3, 0), (4, 0), (6, 0)
L_TXT_PAD, L_TXT_PORT, L_TXT_TS, L_TXT_NOTE = (10, 0), (10, 1), (10, 2), (10, 3)
L_OUTLINE, L_DICING, L_PADMARK, L_TSPAD, L_BLOCKMARK = (100, 0), (101, 0), (102, 0), (102, 1), (104, 0)
MASK_LAYERS = dict(NB=L_NB, GRAL=L_GRAL, AL1=L_AL1, AL2=L_AL2, DIEL=L_DIEL)

# process rules: same values as hardware/drc.py RULES (restated, not imported)
RULES = dict(NB_W=0.40, NB_S=0.40, GRAL_W=0.20, GRAL_S=0.30, GRAL_C=0.15, AL1_W=0.10, AL1_S=0.20, AL2_W=0.10,
             AL2_S=0.20, JJ_TOL=0.05, CONTACT_MIN=1.00, JJ_W=0.10, JJ_S=0.50, CT_A=1.00, DIEL_W=0.50, DIEL_S=0.40,
             DIEL_EN=0.20, DIEL_SJ=0.20)
# die-level rules (this file)
DIE_RULES = dict(XO_ISO=0.50, STRAP_MAX=300.0, BEND_TOL=25.0, HOLE_KEEP=20.0, XSEC_TOL=0.010, DICING=100.0,
                 BLOCK_MARGIN=1.0)

# ===================================================================================================== die geometry
DIE = 10000.0
DICING = 100.0
W_CPW, G_CPW = 10.0, 6.0          # read back from die_pads.json at build time (asserted)
L_TAPER = 100.0                   # port geometry (0.5/0.5) -> 10/6 taper
R_SB, R_N, R_M, R_RES = 10.0, 20.0, 100.0, 50.0   # bend radii: crossover field, narrow fan-out, 10/6 routing, meanders
SB_L0, SB_LS = 14.0, 10.0         # crossover field: straight lead-in, straight between columns (bus strap in its middle)
Y_F = 3000.0                      # feedline y
CPL_STRIP = 5.0                   # ground strip between feedline and resonator coupler
CPL_LEN = 200.0                   # parallel coupling length
LAUNCH_GAP_SIDE, LAUNCH_GAP_END = 144.0, 60.0
HOLE, HOLE_PITCH = 2.0, 20.0
F_TARGET = {"RO_CATCHER_A0": 6.00, "RO_CATCHER_A1": 6.20, "RO_CATCHER_B0": 6.40, "RO_CATCHER_B1": 6.60}
EPS_SI, H_SUB = 11.45, 525.0
EPS_SIN, T_SIN = 7.0, 0.100       # SiNx eps_r, thickness (um)
EPS0 = 8.8541878128e-12
C_LIGHT = 299792458.0
LABEL = "QBF-X2 rev A 2026-11-25"

# strap / bridge geometry (um)
ST_W = dict(al2_w=2.0, diel_w=4.0, neck_w=2.0, land=2.0, contact=8.0)        # on 10/6 lines
ST_N = dict(al2_w=1.5, diel_w=3.0, land=1.0, contact=3.0)                   # on narrow lines
XB = dict(pad=2.0, pad_g=0.5, strip=1.5, al2_w=1.6, diel_w=2.6, diel_ov=0.30, al2_in=0.50)   # narrow crossover
XBIG = dict(strip=4.0, endgap=6.0, al2_w=2.0, diel_w=4.0, land=8.0, diel_ov=1.0)            # gate over feedline
BUS = dict(al2_w=2.0, diel_w=4.0, diel_hw=1.75, ext=15.0)

KIND = {"GATE": "dc_gate", "RO_C": "readout", "LOAD": "dc_ramp", "TRAP": "trap", "ACC_": "acc"}
BRIDGE_PRIO = {"dc_gate": 4, "readout": 3, "dc_ramp": 2, "trap": 1.5, "acc": 1, "feed": 0}


def line_kind(net):
    if net == "FEED":
        return "feed"
    return KIND[net[:4]]


# ===================================================================================================== path geometry
def _unit(v):
    v = np.asarray(v, float)
    return v / math.hypot(v[0], v[1])


class Path:
    """Polyline through corner points with circular fillets (radius per interior point)."""

    def __init__(self, pts, radii):
        pts = [np.array(p, float) for p in pts]
        if np.isscalar(radii):
            radii = [float(radii)] * (len(pts) - 2)
        assert len(radii) == len(pts) - 2, (len(radii), len(pts))
        self.pts, self.radii = pts, list(radii)
        prims, corner = [], [None] * len(pts)
        cur, s = pts[0].copy(), 0.0
        for i in range(1, len(pts) - 1):
            u1, u2 = _unit(pts[i] - pts[i - 1]), _unit(pts[i + 1] - pts[i])
            th = math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1 @ u2)
            if abs(th) < 1e-9:
                continue
            R = radii[i - 1]
            d = R * math.tan(abs(th) / 2)
            A, B = pts[i] - u1 * d, pts[i] + u2 * d
            L = (A - cur) @ u1
            if L < -1e-6:
                raise ValueError(f"fillet overlap before corner {i} {pts[i]} (straight {L:.3f})")
            if L > 1e-9:
                prims.append(("L", cur.copy(), A.copy(), s, s + L))
                s += L
            sg = 1.0 if th > 0 else -1.0
            C = A + np.array([-u1[1], u1[0]]) * sg * R
            a0 = math.atan2(A[1] - C[1], A[0] - C[0])
            la = R * abs(th)
            prims.append(("A", C, R, a0, sg, abs(th), s, s + la))
            corner[i] = (s, s + la, R, s + la / 2)
            s += la
            cur = B
        u = _unit(pts[-1] - cur) if np.linalg.norm(pts[-1] - cur) > 1e-12 else _unit(pts[-1] - pts[-2])
        L = (pts[-1] - cur) @ u
        if L < -1e-6:
            raise ValueError("fillet overlap at the end")
        if L > 1e-9:
            prims.append(("L", cur.copy(), pts[-1].copy(), s, s + L))
            s += L
        self.prims, self.corner, self.length = prims, corner, s
        self._starts = np.array([p[-2] for p in prims])

    def arcs(self):
        return [p for p in self.prims if p[0] == "A"]

    def _prim(self, s):
        i = int(np.searchsorted(self._starts, s, side="right") - 1)
        return self.prims[max(0, min(i, len(self.prims) - 1))]

    def at(self, s):
        p = self._prim(s)
        if p[0] == "L":
            u = _unit(p[2] - p[1])
            return p[1] + u * (s - p[3]), u
        _, C, R, a0, sg, th, s0, s1 = p
        phi = a0 + sg * (s - s0) / R
        P = C + R * np.array([math.cos(phi), math.sin(phi)])
        t = sg * np.array([-math.sin(phi), math.cos(phi)])
        return P, t

    def svals(self, sa, sb, extra=()):
        out = {sa, sb}
        for p in self.prims:
            s0, s1 = p[-2], p[-1]
            if s1 <= sa or s0 >= sb:
                continue
            out.update(v for v in (s0, s1) if sa < v < sb)
            if p[0] == "A":
                R = p[2]
                dth = min(math.radians(1.0), 2 * math.acos(max(-1.0, 1 - 0.002 / (R + 12.0))))
                n = max(1, int(math.ceil(p[5] / dth)))
                for k in range(1, n):
                    v = s0 + (s1 - s0) * k / n
                    if sa < v < sb:
                        out.add(v)
        out.update(v for v in extra if sa < v < sb)
        return sorted(out)

    def project(self, q):
        q = np.asarray(q, float)
        best = (1e18, None)
        for p in self.prims:
            if p[0] == "L":
                u = _unit(p[2] - p[1])
                t = min(max((q - p[1]) @ u, 0.0), p[4] - p[3])
                d = np.linalg.norm(p[1] + u * t - q)
                s = p[3] + t
            else:
                _, C, R, a0, sg, th, s0, s1 = p
                ang = math.atan2(q[1] - C[1], q[0] - C[0])
                dphi = ((ang - a0) * sg) % (2 * math.pi)
                if dphi > th:
                    dphi = th if dphi - th < 2 * math.pi - dphi else 0.0
                s = s0 + dphi * R
                d = np.linalg.norm(self.at(s)[0] - q)
            if d < best[0]:
                best = (d, s)
        return best[1], best[0]


# ===================================================================================================== CPW profile
class Profile:
    """Piecewise-linear (w, g) along s, with linear overrides (a, b, wa, wb, ga, gb) for necks and pads.  Every width
    change is a ramp, never a step: steps on arcs or 45-degree lines leave corners a hair below 90 degrees after the
    1 nm grid snap, which width/space checks flag."""

    def __init__(self, length, knots, overrides=()):
        self.L = length
        ov = []
        for o in overrides:
            ov.append((o[0], o[1], o[2], o[2], o[3], o[3]) if len(o) == 4 else tuple(o))
        bps = {0.0, length}
        bps.update(k[0] for k in knots if 0 < k[0] < length)
        for o in ov:
            bps.update(v for v in (o[0], o[1]) if 0 < v < length)
        self.bps = sorted(bps)
        self.knots = sorted(knots)
        self.ov = sorted(ov)

    def base(self, s):
        k = self.knots
        if s <= k[0][0]:
            return k[0][1], k[0][2]
        for (s0, w0, g0), (s1, w1, g1) in zip(k[:-1], k[1:]):
            if s0 <= s <= s1:
                f = 0.0 if s1 == s0 else (s - s0) / (s1 - s0)
                return w0 + f * (w1 - w0), g0 + f * (g1 - g0)
        return k[-1][1], k[-1][2]

    def at(self, s, side=0):
        """side=-1: limit from the left, +1: from the right, 0: interior."""
        eps = 1e-7 * side
        for (a, b, wa, wb, ga, gb) in self.ov:
            if a < s + eps < b:
                f = (s - a) / (b - a)
                return wa + f * (wb - wa), ga + f * (gb - ga)
        return self.base(s)

    def pieces(self):
        out = []
        for a, b in zip(self.bps[:-1], self.bps[1:]):
            wa, ga = self.at(a, +1)
            wb, gb = self.at(b, -1)
            out.append((a, b, wa, wb, ga, gb))
        return out


def cpw_polys(path, prof, sa, sb, cap_a=0.0, cap_b=0.0):
    """slot polygons, end caps and centre polygon of the CPW piece [sa, sb] (numpy arrays, um)."""
    ss = path.svals(sa, sb, prof.bps)
    rows = []
    for s in ss:
        if s == sa:
            rows.append((s,) + prof.at(s, +1))
        elif s == sb:
            rows.append((s,) + prof.at(s, -1))
        else:
            l, r = prof.at(s, -1), prof.at(s, +1)
            rows.append((s,) + l)
            if abs(l[0] - r[0]) > 1e-9 or abs(l[1] - r[1]) > 1e-9:
                rows.append((s,) + r)
    P = np.zeros((len(rows), 2))
    N = np.zeros((len(rows), 2))
    W = np.array([r[1] for r in rows])
    G = np.array([r[2] for r in rows])
    for i, r in enumerate(rows):
        p, t = path.at(r[0])
        P[i], N[i] = p, (-t[1], t[0])
    li, lo = P + N * (W / 2)[:, None], P + N * (W / 2 + G)[:, None]
    ri, ro = P - N * (W / 2)[:, None], P - N * (W / 2 + G)[:, None]
    slots = [np.vstack([lo, li[::-1]]), np.vstack([ri, ro[::-1]])]
    for s, cap, sgn in ((sa, cap_a, -1.0), (sb, cap_b, 1.0)):
        if cap > 0:
            p, t = path.at(s)
            n = np.array([-t[1], t[0]])
            w, g = prof.at(s, 1 if sgn < 0 else -1)
            h = w / 2 + g
            q = p + t * sgn * cap
            slots.append(np.array([p + n * h, q + n * h, q - n * h, p - n * h]))
    centre = np.vstack([li, ri[::-1]])
    return slots, centre


def rect_local(P, t, a0, a1, b0, b1):
    """rectangle a in [a0,a1] along t, b in [b0,b1] along the left normal, around P."""
    n = np.array([-t[1], t[0]])
    return np.array([P + t * a0 + n * b0, P + t * a1 + n * b0, P + t * a1 + n * b1, P + t * a0 + n * b1])


def rect_poly(db, P, t, a0, a1, b0, b1):
    """Exact-right-angle rectangle (klayout Polygon, 1 nm grid) for Manhattan or 45-degree orientations.  On 45 degrees
    the corners sit on the lattice P + I*(1,1) nm + J*(-1,1) nm, so all angles stay exactly 90 degrees after snapping."""
    t = np.asarray(t, float)
    Pi = (int(round(P[0] * 1000)), int(round(P[1] * 1000)))
    ax, ay = abs(t[0]), abs(t[1])
    if min(ax, ay) < 1e-9:                                  # Manhattan
        return db.Polygon([db.Point(int(round(x * 1000)), int(round(y * 1000)))
                           for x, y in rect_local(np.array(P, float), t, a0, a1, b0, b1)])
    if abs(ax - ay) > 1e-9:
        raise ValueError(f"rect_poly: orientation {t} is neither Manhattan nor 45 degrees")
    T = (int(np.sign(t[0])), int(np.sign(t[1])))
    N = (-T[1], T[0])
    q = lambda v: int(round(v * 1000 / math.sqrt(2)))
    pts = []
    for a, b in ((a0, b0), (a1, b0), (a1, b1), (a0, b1)):
        I, J = q(a), q(b)
        pts.append(db.Point(Pi[0] + I * T[0] + J * N[0], Pi[1] + I * T[1] + J * N[1]))
    return db.Polygon(pts)


def u_pieces(c, sgn, pieces):
    """map pieces given in u = distance from point c (u >= 0, direction sgn along s) to s-ordered overrides."""
    out = []
    for (u0, u1, w0, w1, g0, g1) in pieces:
        s0, s1 = c + sgn * u0, c + sgn * u1
        out.append((s0, s1, w0, w1, g0, g1) if s0 < s1 else (s1, s0, w1, w0, g1, g0))
    return out


def pad_overrides(c, sgn):
    """landing pad of a narrow crossover bridge next to the cut point c (pad on side sgn of c): end chamfer, 2 um pad,
    inner-edge ramp, outer-edge ramp back to the port geometry; the slot stays continuous and >= 0.5 um everywhere."""
    pw, pg, ch, rp = XB["pad"], XB["pad_g"], 0.30, 0.75
    h = pw / 2 + pg                                         # 1.5: outer edge along the pad
    return u_pieces(c, sgn, [
        (0.0, ch, pw - 2 * ch, pw, h - (pw - 2 * ch) / 2, pg),
        (ch, pw, pw, pw, pg, pg),
        (pw, pw + rp, pw, PW, pg, h - PW / 2),
        (pw + rp, pw + 2 * rp, PW, PW, h - PW / 2, PG)])


def neck_overrides(s):
    """2 um neck of the 10 um centre conductor under a ground strap (1 um ramps; the slot outer edge is unchanged)."""
    wn = ST_W["neck_w"]
    gn = G_CPW + (W_CPW - wn) / 2
    h, r = ST_W["diel_w"] / 2, 1.0
    return [(s - h - r, s - h, W_CPW, wn, G_CPW, gn), (s - h, s + h, wn, wn, gn, gn), (s + h, s + h + r, wn, W_CPW, gn, G_CPW)]


# ===================================================================================================== TL physics
def cpw_eps_z(w, g, h=H_SUB, er=EPS_SI):
    """quasi-static conformal mapping (CPW on a substrate of thickness h, no back metal): eps_eff, Z0."""
    from scipy.special import ellipk
    K = lambda k: float(ellipk(k * k))
    k0 = w / (w + 2 * g)
    k0p = math.sqrt(1 - k0 * k0)
    k1 = math.sinh(math.pi * w / (4 * h)) / math.sinh(math.pi * (w + 2 * g) / (4 * h))
    k1p = math.sqrt(1 - k1 * k1)
    eps = 1 + (er - 1) / 2 * (K(k1) / K(k1p)) * (K(k0p) / K(k0))
    Z = 30 * math.pi / math.sqrt(eps) * K(k0p) / K(k0)
    return eps, Z


def c_plate(area_um2):
    return EPS0 * EPS_SIN * area_um2 * 1e-12 / (T_SIN * 1e-6)


def tl_D(f, elems):
    """D element of the ABCD chain (open end -> short); the parallel resonance is D(f) = 0.  Matrices are kept in
    the real form [[a, jb], [jc, d]] (lossless)."""
    a, b, c, d = 1.0, 0.0, 0.0, 1.0
    w = 2 * math.pi * f
    for e in elems:
        if e[0] == "T":
            _, l, Z, eps = e
            th = w * math.sqrt(eps) / C_LIGHT * l * 1e-6
            ea, eb, ec, ed = math.cos(th), Z * math.sin(th), math.sin(th) / Z, math.cos(th)
        else:
            ea, eb, ec, ed = 1.0, 0.0, w * e[1], 1.0
        a, b, c, d = a * ea - b * ec, a * eb + b * ed, c * ea + d * ec, -c * eb + d * ed
    return d


def resonance(elems, f0):
    from scipy.optimize import brentq
    fs = np.linspace(0.25 * f0, 3.0 * f0, 600)          # lowest root = fundamental quarter-wave mode
    vals = [tl_D(f, elems) for f in fs]
    for i in range(len(fs) - 1):
        if vals[i] == 0 or vals[i] * vals[i + 1] < 0:
            return brentq(tl_D, fs[i], fs[i + 1], args=(elems,), xtol=1e2)
    raise RuntimeError("no resonance found")


# ===================================================================================================== routes
class Route:
    def __init__(self, net, pts, radii, kind=None):
        self.net, self.kind = net, kind or line_kind(net)
        self.pts, self.radii = [tuple(map(float, p)) for p in pts], list(radii)
        self.path = Path(self.pts, self.radii)
        self.s_taper = None
        self.cuts = []            # (s0, s1, cap) removed intervals (bridges): cap = end-gap length at both sides
        self.pads = []            # overrides (s0, s1, w, g)
        self.zones = []           # strap-forbidden intervals (s0, s1, covered?)
        self.bus = []             # s of bus straps (crossover field)
        self.straps = []          # s of individual ground straps
        self.cap_end = 0.0
        self.shunts = []          # (s, C_F, what) for the resonator model
        self.sb_exit = 0.0
        self.coupler = None

    def corner_end(self, idx, delta):
        c = self.path.corner[idx]
        assert c is not None, (self.net, idx)
        return c[1] + delta

    def base_knots(self):
        L = self.path.length
        if self.s_taper is None:
            return [(0.0, W_CPW, G_CPW), (L, W_CPW, G_CPW)]
        a = self.s_taper
        return [(0.0, PW, PG), (a, PW, PG), (a + L_TAPER, W_CPW, G_CPW), (L, W_CPW, G_CPW)]

    def is_wide(self, s):
        return self.s_taper is None or s > self.s_taper + L_TAPER + 1e-6

    def profile(self):
        ov = list(self.pads)
        for s in self.straps:
            if self.is_wide(s):
                ov += neck_overrides(s)
        return Profile(self.path.length, self.base_knots(), ov)


PW, PG = 0.5, 0.5   # overwritten from block_ports.json


def _sorting_network(cur, target):
    rank = {n: i for i, n in enumerate(target)}
    seq, cols, par = list(cur), [], 0
    for _ in range(4 * len(seq)):
        if all(rank[seq[i]] < rank[seq[i + 1]] for i in range(len(seq) - 1)):
            break
        sw = [i for i in range(par, len(seq) - 1, 2) if rank[seq[i]] > rank[seq[i + 1]]]
        par ^= 1
        if not sw:
            continue
        cols.append([(i, seq[i], seq[i + 1]) for i in sw])
        for i in sw:
            seq[i], seq[i + 1] = seq[i + 1], seq[i]
    assert seq == list(target)
    return cols


def crossover_field(side, cur, target, x_edge, ytr):
    """Adjacent-swap crossover field next to the block edge (odd-even transposition network).  Each swap is an X of two
    45-degree diagonals crossing at 90 degrees between neighbouring 20 um tracks."""
    dr = 1.0 if side == "E" else -1.0
    cols = _sorting_network(cur, target)
    p = abs(ytr[0] - ytr[1])
    d = R_SB * math.tan(math.radians(22.5))
    Lx = 2 * d + p
    wps = {n: [(x_edge, ytr[i])] for i, n in enumerate(cur)}
    pos = {n: i for i, n in enumerate(cur)}
    crossings, bus = [], [x_edge + dr * SB_L0 / 2]
    for c, sw in enumerate(cols):
        xc = x_edge + dr * (SB_L0 + c * (Lx + SB_LS))
        for (i, a, b) in sw:
            assert pos[a] == i and pos[b] == i + 1
            for n, k0, k1 in ((a, i, i + 1), (b, i + 1, i)):
                wps[n].append((xc + dr * d, ytr[k0]))
                wps[n].append((xc + dr * (d + p), ytr[k1]))
            pos[a], pos[b] = i + 1, i
            pa, pb = BRIDGE_PRIO[line_kind(a)], BRIDGE_PRIO[line_kind(b)]
            top = (a, b) if pa > pb or (pa == pb and True) else (b, a)
            crossings.append(dict(side=side, column=c, tracks=[i, i + 1], nets=[a, b], bridge=top[0],
                                  under=top[1], xy=[xc + dr * Lx / 2, (ytr[i] + ytr[i + 1]) / 2], kind="field"))
        bus.append(xc + dr * (Lx + SB_LS / 2))
    x_exit = x_edge + dr * (SB_L0 + len(cols) * (Lx + SB_LS))
    return dict(wps=wps, crossings=crossings, bus=bus, x_exit=x_exit, ncol=len(cols), final=list(target))


def meander_pts(xe, y1, n, span, dx, yc, cdir):
    """corners of an n-run meander (n even) hanging below (xe, y1); runs alternate away from / back to xe; then a
    vertical drop at xe to the coupler corner (xe, yc) and a coupler run in direction cdir."""
    pts, rad = [], []
    p = 2 * R_RES
    if n > 0:
        pts.append((xe, y1)); rad.append(R_RES)
        for k in range(n):
            y = y1 - k * p
            xfar = xe + dx * span
            if k % 2 == 0:
                pts += [(xfar, y), (xfar, y - p)]
            else:
                pts += [(xe, y), (xe, y - p)] if k < n - 1 else [(xe, y)]
            rad += [R_RES, R_RES] if (k % 2 == 0 or k < n - 1) else [R_RES]
    pts.append((xe, yc)); rad.append(R_RES)
    pts.append((xe + cdir * (R_RES + CPL_LEN), yc))
    return pts, rad


# ===================================================================================================== block inputs
def _load_inputs(block_gds, block_ports_json, die_pads_json):
    import klayout.db as db
    bp = json.load(open(block_ports_json))
    dp = json.load(open(die_pads_json))
    ly = db.Layout()
    ly.read(block_gds)
    cell = ly.cell(bp.get("block_cell", "QBFX2_ROWS")) or ly.top_cell()
    bb = cell.dbbox()
    assert abs(bb.width() - bp["width_um"]) < 1e-3 and abs(bb.height() - bp["height_um"]) < 1e-3, bb
    return bp, dp, ly, cell


def measure_block_junctions(ly, cell):
    """junction overlaps (AL1 & AL2 - DIEL < 1 um^2) of the frozen block, clustered by area (+-5 %)."""
    import klayout.db as db
    R = lambda l: db.Region(cell.begin_shapes_rec(ly.layer(*l))).merged()
    A1, A2, DI = R(L_AL1), R(L_AL2), R(L_DIEL)
    ov = (A1 & A2) - DI
    dbu = ly.dbu
    items = []
    for p in ov.each():
        a = p.area() * dbu * dbu
        if a < RULES["CONTACT_MIN"]:
            items.append((a, p.bbox()))
    items.sort(key=lambda t: t[0])
    clusters = []
    for a, b in items:
        if clusters and a <= clusters[-1][0][0] * (1 + RULES["JJ_TOL"]):
            clusters[-1].append((a, b))
        else:
            clusters.append([(a, b)])
    out = []
    for cl in clusters:
        areas = np.array([a for a, _ in cl])
        b = cl[len(cl) // 2][1]
        box = b.enlarged(80, 80)
        a1 = (A1 & db.Region(box)).bbox()
        # AL1 finger: the dimension of the junction along which AL1 does not extend
        if a1.height() <= b.height() + 2:
            w_al1, w_al2 = b.height() * dbu, b.width() * dbu
        else:
            w_al1, w_al2 = b.width() * dbu, b.height() * dbu
        out.append(dict(area_um2=float(np.median(areas)), count=len(cl), al1_um=round(w_al1, 4), al2_um=round(w_al2, 4)))
    out.sort(key=lambda d: -d["area_um2"])
    return out


# ===================================================================================================== test structures
def _ts_cells(ly, jj):
    """test-structure cells (local coordinates centred on the cell origin).  Returns {name: (cell, window_polys,
    pads[(pin,x,y)], info)}."""
    import klayout.db as db
    dbu = ly.dbu
    L = {k: ly.layer(*v) for k, v in dict(NB=L_NB, GRAL=L_GRAL, AL1=L_AL1, AL2=L_AL2, DIEL=L_DIEL, TS=L_TSPAD,
                                          TXT=L_TXT_TS).items()}

    def box(c, lay, x0, y0, x1, y1):
        c.shapes(L[lay]).insert(db.Box(int(round(min(x0, x1) / dbu)), int(round(min(y0, y1) / dbu)),
                                       int(round(max(x0, x1) / dbu)), int(round(max(y0, y1) / dbu))))

    def pad(c, name, pin, x, y, s=100.0):
        box(c, "NB", x - s / 2, y - s / 2, x + s / 2, y + s / 2)
        box(c, "TS", x - s / 2, y - s / 2, x + s / 2, y + s / 2)
        c.shapes(L["TXT"]).insert(db.Text(f"TS_{name}_{pin}", db.Trans(int(round(x / dbu)), int(round(y / dbu)))))
        return (pin, x, y)

    out = {}

    def window(bboxes, m=20.0):
        return [np.array([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)])
                for (x0, y0, x1, y1) in bboxes]

    # ---- series junction arrays (cross-type, zig-zag), 20 junctions
    def jj_array(name, a, b, n_jj=20):
        c = ly.create_cell(f"TS_{name}")
        E1, La, rs = 0.10, 3.0, 2.0
        P = La - 2 * E1 - b - 0.02
        M = n_jj // 2
        row = lambda k: 0.0 if k % 2 == 0 else rs
        x0 = -(M * P + La) / 2
        for k in range(M + 1):
            box(c, "AL1", x0 + k * P, row(k) - a / 2, x0 + k * P + La, row(k) + a / 2)
        for k in range(M):
            xr = x0 + k * P + La - E1
            ylo = min(row(k), row(k + 1)) - a / 2 - E1
            yhi = max(row(k), row(k + 1)) + a / 2 + E1
            box(c, "AL2", xr - b, ylo, xr, yhi)
        xl, xe = x0, x0 + M * P + La
        ye = row(M)
        # AL1 leads (1 um) to 10 x 10 contacts on the Nb pads at x = -150 / +150
        box(c, "AL1", -105.0, -0.5, xl, 0.5)
        box(c, "AL1", -112.0, -5.0, -102.0, 5.0)
        box(c, "AL1", xe, ye - 0.5, 105.0, ye + 0.5)
        box(c, "AL1", 102.0, ye - 5.0, 112.0, ye + 5.0)
        pads = [pad(c, name, "A", -150.0, 0.0), pad(c, name, "B", 150.0, ye)]
        win = window([(-200, -50, 200, 50 + ye)])
        RN1 = math.pi * 180e-6 / 2 / (2.1e-6 * a * b)          # Ambegaokar-Baratoff, Delta_Al = 180 ueV (assumed)
        info = dict(kind="series JJ array", n_junctions=n_jj, al1_um=a, al2_um=b, area_um2=round(a * b, 5),
                    Ic_nA_each=round(2.1 * a * b * 1e3, 2), RN_kohm_each_est=round(RN1 / 1e3, 3),
                    RN_kohm_total_est=round(n_jj * RN1 / 1e3, 1),
                    note="Jc = 2.1 uA/um^2 (drc.py process note); R_N from pi*Delta/(2e*Ic) with Delta = 180 ueV (assumed)")
        out[name] = (c, win, pads, info)

    jr = jj["rail"]
    jm = jj["middle"]
    jj_array("JJ_RAIL", jr["a"], jr["b"])
    jj_array("JJ_MID", jm["a"], jm["b"])

    # ---- granular-Al sheet-resistance meander (0.5 um line)
    c = ly.create_cell("TS_GRAL")
    wl, pitch, run, nrun = 0.5, 2.0, 60.0, 16
    x0, y0 = -run / 2, -(nrun - 1) * pitch / 2
    length = 0.0
    for k in range(nrun):
        y = y0 + k * pitch
        box(c, "GRAL", x0, y - wl / 2, x0 + run, y + wl / 2)
        length += run
        if k < nrun - 1:
            xs = x0 + run - wl if k % 2 == 0 else x0
            box(c, "GRAL", xs, y - wl / 2, xs + wl, y + pitch + wl / 2)
            length += pitch
    ylast = y0 + (nrun - 1) * pitch
    xend = x0 if (nrun - 1) % 2 == 1 else x0 + run
    box(c, "GRAL", -105.0, y0 - wl / 2, x0 + wl, y0 + wl / 2)
    box(c, "GRAL", -110.0, y0 - 2.5, -102.0, y0 + 2.5)
    box(c, "GRAL", xend - wl if xend > 0 else xend, ylast - wl / 2, 105.0, ylast + wl / 2)
    box(c, "GRAL", 102.0, ylast - 2.5, 110.0, ylast + 2.5)
    length += (x0 + 105.0) + (105.0 - xend)
    pads = [pad(c, "GRAL", "A", -150.0, y0), pad(c, "GRAL", "B", 150.0, ylast)]
    out["GRAL"] = (c, window([(-200, y0 - 50, 200, ylast + 50)]), pads,
                   dict(kind="granular-Al sheet-resistance meander", width_um=wl, length_um=round(length, 1),
                        squares=round(length / wl, 0), note="R = R_sq * squares (+ two GRAL/Nb contacts)"))

    # ---- thin-Al strips (AL1 and AL2), 1 um x 200 um
    for nm, lay in (("AL1_STRIP", "AL1"), ("AL2_STRIP", "AL2")):
        c = ly.create_cell(f"TS_{nm}")
        box(c, lay, -105.0, -0.5, 105.0, 0.5)
        box(c, lay, -112.0, -5.0, -102.0, 5.0)
        box(c, lay, 102.0, -5.0, 112.0, 5.0)
        pads = [pad(c, nm, "A", -150.0, 0.0), pad(c, nm, "B", 150.0, 0.0)]
        out[nm] = (c, window([(-200, -50, 200, 50)]), pads,
                   dict(kind=f"thin-Al strip ({lay}, 30 nm)", width_um=1.0, length_um=200.0, squares=200.0,
                        note="strip between the pad edges (x = +-100 um); 10 x 10 um Al-on-Nb contacts"))

    # ---- Nb continuity meander (2 um line)
    c = ly.create_cell("TS_NB_MEANDER")
    wl, pitch, run, nrun = 2.0, 6.0, 80.0, 16
    x0, y0 = -run / 2, -(nrun - 1) * pitch / 2
    length = 0.0
    for k in range(nrun):
        y = y0 + k * pitch
        box(c, "NB", x0, y - wl / 2, x0 + run, y + wl / 2)
        length += run
        if k < nrun - 1:
            xs = x0 + run - wl if k % 2 == 0 else x0
            box(c, "NB", xs, y - wl / 2, xs + wl, y + pitch + wl / 2)
            length += pitch
    ylast = y0 + (nrun - 1) * pitch
    xend = x0 if (nrun - 1) % 2 == 1 else x0 + run
    box(c, "NB", -100.0, y0 - wl / 2, x0 + wl, y0 + wl / 2)
    box(c, "NB", xend - wl if xend > 0 else xend, ylast - wl / 2, 100.0, ylast + wl / 2)
    length += (x0 + 100.0) + (100.0 - xend)
    pads = [pad(c, "NB_MEANDER", "A", -150.0, y0), pad(c, "NB_MEANDER", "B", 150.0, ylast)]
    out["NB_MEANDER"] = (c, window([(-200, y0 - 50, 200, ylast + 50)]), pads,
                         dict(kind="Nb continuity meander", width_um=wl, length_um=round(length, 1),
                              squares=round(length / wl, 0)))

    # ---- SiNx plate capacitor: Nb bottom plate (pad A), AL2 top plate (pad B)
    c = ly.create_cell("TS_SIN_CAP")
    box(c, "NB", -100.0, -10.0, -60.0, 10.0)               # neck from pad A to the plate
    box(c, "NB", -60.0, -75.0, 90.0, 75.0)                 # bottom plate 150 x 150
    box(c, "DIEL", -70.0, -85.0, 100.0, 85.0)
    box(c, "AL2", -55.0, -70.0, 85.0, 70.0)                # top plate 140 x 140
    box(c, "AL2", 85.0, -5.0, 120.0, 5.0)                  # lead over DIEL edge (x=100) onto pad B (x >= 110)
    box(c, "AL2", 110.0, -10.0, 130.0, 10.0)
    pads = [pad(c, "SIN_CAP", "A", -150.0, 0.0), pad(c, "SIN_CAP", "B", 160.0, 0.0)]
    Ccap = c_plate(140.0 * 140.0)
    out["SIN_CAP"] = (c, window([(-200, -95, 210, 95)]), pads,
                      dict(kind="SiNx plate capacitor (AL2 / 100 nm SiNx / Nb)", overlap_um2=140.0 * 140.0,
                           C_pF_est=round(Ccap * 1e12, 2), note="parallel plate, eps_r 7, 100 nm (no fringing)"))

    # ---- SiNx crossover chain: 12 AL2 bridges in series (pads A-B) over one Nb line (pad C)
    c = ly.create_cell("TS_XO_CHAIN")
    nbr, pit = 12, 25.0
    xs = [-((nbr - 1) * pit) / 2 + k * pit for k in range(nbr)]
    box(c, "NB", xs[0] - 30.0, -5.0, xs[-1] + 20.0, 5.0)            # crossed line (pad C)
    box(c, "NB", xs[0] - 30.0, -5.0, xs[0] - 20.0, 60.0)
    for k in range(0, nbr, 2):                                       # above segments: bridges k, k+1
        box(c, "NB", xs[k] - 6.0, 11.0, xs[k + 1] + 6.0, 21.0)
    for k in range(1, nbr - 1, 2):                                   # below segments: bridges k, k+1
        box(c, "NB", xs[k] - 6.0, -21.0, xs[k + 1] + 6.0, -11.0)
    box(c, "NB", -150.0, -21.0, xs[0] + 6.0, -11.0)                  # first below segment -> pad A
    box(c, "NB", xs[-1] - 6.0, -21.0, 150.0, -11.0)                  # last below segment -> pad B
    for x in xs:
        box(c, "AL2", x - 2.0, -19.0, x + 2.0, 19.0)
        box(c, "DIEL", x - 3.0, -12.0, x + 3.0, 12.0)
    pads = [pad(c, "XO_CHAIN", "A", -170.0, -60.0), pad(c, "XO_CHAIN", "B", 170.0, -60.0),
            pad(c, "XO_CHAIN", "C", xs[0] - 25.0, 110.0)]
    box(c, "NB", -150.0, -21.0, -120.0, -11.0)
    out["XO_CHAIN"] = (c, window([(-220, -110, 220, 21), (xs[0] - 75, -10, xs[0] + 25, 160)]), pads,
                       dict(kind="SiNx crossover chain (continuity A-B through 12 AL2 bridges, isolation to C)",
                            bridges=nbr, C_pF_est=round(nbr * c_plate(4.0 * 10.0) * 1e12, 4),
                            note="each bridge: 4 um AL2 over a 10 um Nb line on 100 nm SiNx"))
    return out


# ===================================================================================================== build
def build_die(block_gds, block_ports_json, die_pads_json, out_gds, previews: bool = True) -> dict:
    """Build the QBF-X2 die GDS around the frozen row block.  Writes out_gds and die_ports_asbuilt.json (same folder)
    and, if previews, die_preview_*.png (same folder).  Returns a summary dict."""
    import klayout.db as db
    import gdstk
    global PW, PG
    t_start = time.time()
    bp, dp, bly, bcell = _load_inputs(block_gds, block_ports_json, die_pads_json)
    L = dp["launcher"]
    assert (L["cpw_center_um"], L["cpw_gap_um"]) == (W_CPW, G_CPW)
    assert tuple(dp["die_size_um"]) == (DIE, DIE)
    BW, BH = bp["width_um"], bp["height_um"]
    cx, cy = dp.get("row_block_centre_um", [DIE / 2, DIE / 2])
    BX0, BY0 = cx - BW / 2, cy - BH / 2
    ports = {p["name"]: p for p in bp["ports"]}
    sig = {n: p for n, p in ports.items() if p["kind"] not in ("internal_short", "ground")}
    PW = sig["TRAP_A0"]["width"]
    PG = sig["TRAP_A0"]["gap"]
    assert all(abs(p["width"] - PW) < 1e-9 and abs(p.get("gap", PG) - PG) < 1e-9 for p in sig.values())
    die_xy = lambda p: (BX0 + p["x"], BY0 + p["y"])

    # ---------------------------------------------------------------- junction targets from the block
    jcl = measure_block_junctions(bly, bcell)
    assert len(jcl) >= 2, jcl
    jj = {}
    for key, cl in (("rail", jcl[0]), ("middle", jcl[1])):
        a, b = cl["al1_um"], cl["al2_um"]
        A = cl["area_um2"]
        if b < RULES["AL2_W"]:                      # keep the area, respect AL2.W
            b = RULES["AL2_W"]
            a = round(A / b, 3)
        jj[key] = dict(a=a, b=round(A / a, 4) if cl["al2_um"] >= RULES["AL2_W"] else b, area=A,
                       block_al1=cl["al1_um"], block_al2=cl["al2_um"], block_count=cl["count"])

    # ---------------------------------------------------------------- tracks and crossover fields
    def side_ports(edge_x):
        lst = [(p["y"], n) for n, p in sig.items() if abs(p["x"] - edge_x) < 1e-6]
        return [n for _, n in sorted(lst, reverse=True)]           # top -> bottom
    curE, curW = side_ports(BW), side_ports(0.0)
    ytr = [BY0 + sig[n]["y"] for n in curE]
    assert ytr == [BY0 + sig[n]["y"] for n in curW]
    tgtE = ["GATE_BSA_AN", "LOAD_B1", "TRAP_B1", "ACC_B1", "ACC_B0", "TRAP_B0", "LOAD_B0", "RO_CATCHER_A0",
            "RO_CATCHER_A1", "GATE_BSB_PREP"]
    tgtW = ["GATE_BSA_PREP", "LOAD_A0", "TRAP_A0", "ACC_A0", "ACC_A1", "TRAP_A1", "LOAD_A1", "RO_CATCHER_B1",
            "GATE_BSB_AN", "RO_CATCHER_B0"]
    fE = crossover_field("E", curE, tgtE, BX0 + BW, ytr)
    fW = crossover_field("W", curW, tgtW, BX0, ytr)
    XE, XW = fE["x_exit"], fW["x_exit"]
    y = ytr

    pads = {p["net"] if p["net"] != "GND" else f"GND_{p['id']}": p for p in dp["pads"]}
    def cpw_start(net):
        p = pads[net]
        c = np.array(p["pad_center_um"], float)
        u = np.array(p["outward"], float)
        return tuple(c - u * (L["pad_um"][0] / 2 + L["taper_len_um"]))

    # ---------------------------------------------------------------- post-field waypoints (see module docstring)
    N, M = R_N, R_M
    post = {
        # east
        "GATE_BSA_AN": ([(XE, y[0]), (XE + 20, y[0]), (XE + 20, 8900), (6800, 8900), cpw_start("GATE_BSA_AN")], [N, M, M], 1),
        "LOAD_B1": ([(XE, y[1]), (XE + 80, y[1]), (XE + 80, 5290), (7300, 5290), (7300, 8000), cpw_start("LOAD_B1")], [N, N, M, M], 2),
        "TRAP_B1": ([(XE, y[2]), (XE + 140, y[2]), (XE + 140, 5190), (7420, 5190), (7420, 6800), cpw_start("TRAP_B1")], [N, N, M, M], 2),
        "ACC_B1": ([(XE, y[3]), (XE + 200, y[3]), (XE + 200, 5090), (7540, 5090), (7540, 5600), cpw_start("ACC_B1")], [N, N, M, M], 2),
        "ACC_B0": ([(XE, y[4]), (XE + 320, y[4]), (XE + 320, 4910), (8540, 4910), (8540, 4400), cpw_start("ACC_B0")], [N, N, M, M], 2),
        "TRAP_B0": ([(XE, y[5]), (XE + 260, y[5]), (XE + 260, 4810), (8420, 4810), (8420, 3200), cpw_start("TRAP_B0")], [N, N, M, M], 2),
        "LOAD_B0": ([(XE, y[6]), (XE + 200, y[6]), (XE + 200, 4710), (8300, 4710), (8300, 2000), cpw_start("LOAD_B0")], [N, N, M, M], 2),
        "GATE_BSB_PREP": ([(XE, y[9]), (XE + 20, y[9]), (XE + 20, 4440), (6800, 4440), cpw_start("GATE_BSB_PREP")], [N, M, M], 1),
        # west
        "GATE_BSA_PREP": ([(XW, y[0]), (XW - 20, y[0]), (XW - 20, 8900), (3200, 8900), cpw_start("GATE_BSA_PREP")], [N, M, M], 1),
        "LOAD_A0": ([(XW, y[1]), (XW - 80, y[1]), (XW - 80, 5290), (3300, 5290), (3300, 8000), cpw_start("LOAD_A0")], [N, N, M, M], 2),
        "TRAP_A0": ([(XW, y[2]), (XW - 140, y[2]), (XW - 140, 5190), (3180, 5190), (3180, 6800), cpw_start("TRAP_A0")], [N, N, M, M], 2),
        "ACC_A0": ([(XW, y[3]), (XW - 200, y[3]), (XW - 200, 5090), (3060, 5090), (3060, 5600), cpw_start("ACC_A0")], [N, N, M, M], 2),
        "ACC_A1": ([(XW, y[4]), (XW - 320, y[4]), (XW - 320, 4910), (1460, 4910), (1460, 4400), cpw_start("ACC_A1")], [N, N, M, M], 2),
        "TRAP_A1": ([(XW, y[5]), (XW - 260, y[5]), (XW - 260, 4810), (1580, 4810), (1580, 3200), cpw_start("TRAP_A1")], [N, N, M, M], 2),
        "LOAD_A1": ([(XW, y[6]), (XW - 200, y[6]), (XW - 200, 4710), (1700, 4710), (1700, 2000), cpw_start("LOAD_A1")], [N, N, M, M], 2),
        "GATE_BSB_AN": ([(XW, y[8]), (XW - 80, y[8]), (XW - 80, 4440), (3200, 4440), cpw_start("GATE_BSB_AN")], [N, M, M], 1),
    }
    # resonator entries: (pre-meander points, radii, taper corner, xe, y1, dx, cdir, span_max)
    res_entry = {
        "RO_CATCHER_A0": ([(XE, y[7]), (XE + 140, y[7]), (XE + 140, 4560), (7480, 4560)], [N, M, M], 1, 7480.0, 4400.0, +1, +1, 8200.0 - 7480.0 - 11.0),
        "RO_CATCHER_A1": ([(XE, y[8]), (XE + 80, y[8]), (XE + 80, 4500), (6950, 4500)], [N, M, M], 1, 6950.0, 4340.0, +1, +1, 7418.0 - 6950.0 - 11.0),
        "RO_CATCHER_B0": ([(XW, y[9]), (XW - 20, y[9])], [N], 1, XW - 20.0, 4650.0, +1, +1, 6250.0 - (XW - 20.0)),
        "RO_CATCHER_B1": ([(XW, y[7]), (XW - 140, y[7]), (XW - 140, 4560), (3100, 4560)], [N, M, M], 1, 3100.0, 4400.0, -1, -1, 3100.0 - 2250.0),
    }
    y_c = Y_F + W_CPW / 2 + G_CPW + CPL_STRIP + G_CPW + W_CPW / 2

    fields = {"E": fE, "W": fW}
    side_of = {n: "E" for n in curE}
    side_of.update({n: "W" for n in curW})

    def full_route(net, post_pts, post_rad, taper_corner_k):
        # field waypoints, then the exit point (collinear with the last field segment, radius ignored), then the rest
        sbp = fields[side_of[net]]["wps"][net]
        pts = list(sbp) + [tuple(post_pts[0])] + [tuple(p) for p in post_pts[1:]]
        rad = [R_SB] * (len(sbp) - 1) + [R_SB] + list(post_rad)
        r = Route(net, pts, rad)
        r.sb_exit = r.path.project(post_pts[0])[0]
        r.s_taper = r.corner_end(len(sbp) + taper_corner_k, 20.0)   # taper starts 20 um after that corner's arc
        r.bus = bus_s(r, fields[side_of[net]]["bus"])
        return r

    # bus strap positions on each route: the line is on a straight track at every bus x (field part is x-monotonic)
    _bus_cache = {}
    def bus_s(route, xs):
        if route.net in _bus_cache:
            return list(_bus_cache[route.net])
        sgn = 1.0 if side_of[route.net] == "E" else -1.0
        ss = np.linspace(0.0, route.sb_exit, int(route.sb_exit / 0.25) + 2)
        xsamp = np.array([route.path.at(s)[0][0] for s in ss])
        out = []
        for xb in xs:
            i = int(np.argmin(np.abs(xsamp - xb)))
            out.append(float(ss[i] + (xb - xsamp[i]) * sgn))
        _bus_cache[route.net] = out
        return list(out)

    routes = {}
    for net, (pp, rr, tk) in post.items():
        routes[net] = full_route(net, pp, rr, tk)
    # feedline
    feed = Route("FEED", [cpw_start("RO_IN"), (2000.0, Y_F), (8000.0, Y_F), cpw_start("RO_OUT")], [M, M], kind="feed")
    feed.s_taper = None

    # ---------------------------------------------------------------- crossings
    crossings = fE["crossings"] + fW["crossings"]
    for g in ("GATE_BSB_AN", "GATE_BSB_PREP"):
        x = 3200.0 if g == "GATE_BSB_AN" else 6800.0
        crossings.append(dict(side="S", nets=[g, "FEED"], bridge=g, under="FEED", xy=[x, Y_F], kind="gate_over_feed"))

    def apply_field_bridges(r):
        r.pads, r.cuts, r.shunts_x = [], [], []
        for cx_ in crossings:
            if r.net not in cx_["nets"] or cx_["kind"] != "field":
                continue
            s, dd = r.path.project(cx_["xy"])
            assert dd < 1e-6, (r.net, cx_, dd)
            if cx_["bridge"] == r.net:
                a0 = XB["strip"] + PW / 2 + PG + XB["pad_g"]          # 0.75 + 1.5 + 0.5 = 2.75
                r.cuts.append((s - a0, s + a0, XB["pad_g"]))
                r.pads += pad_overrides(s - a0, -1) + pad_overrides(s + a0, +1)
            r.shunts_x.append((s, c_plate(XB["al2_w"] * PW), "crossover (%s over %s)" % (cx_["bridge"], cx_["under"])))
            cx_.setdefault("s", {})[r.net] = s

    def apply_big_bridges(r):
        for cx_ in crossings:
            if cx_["kind"] != "gate_over_feed" or r.net not in cx_["nets"]:
                continue
            s, dd = r.path.project(cx_["xy"])
            assert dd < 1e-6
            cx_.setdefault("s", {})[r.net] = s
            if cx_["bridge"] == r.net:
                h = W_CPW / 2 + G_CPW + XBIG["strip"] + XBIG["endgap"]
                r.cuts.append((s - h, s + h, XBIG["endgap"]))
            r.zones.append((s - 40.0, s + 40.0, False))

    for r in routes.values():
        apply_field_bridges(r)
        apply_big_bridges(r)
    apply_big_bridges(feed)

    # ---------------------------------------------------------------- straps
    def place_straps(r, extra_zones=(), start_cov=False):
        Lr = r.path.length
        zones = list(r.zones) + list(extra_zones)
        if r.s_taper is not None:
            zones.append((r.s_taper - 3.0, r.s_taper + L_TAPER + 3.0, False))
        if r.sb_exit > 0:
            zones.append((0.0, r.sb_exit + 6.0, True))
        for (a, b, cap) in r.cuts:
            zones.append((a - 8.0, b + 8.0, False))
        arcs = [(p[-2], p[-1], p[2], p[5]) for p in r.path.arcs()]
        mids = {round((a + b) / 2, 6) for (a, b, R, th) in arcs if R >= 15.0 and abs(th - math.pi / 2) < 1e-9}

        def free(s):
            # straps sit on straight (Manhattan / 45-degree) segments or exactly at the midpoint of a 90-degree arc
            if not (12.0 <= s <= Lr - 12.0) or any(a <= s <= b for (a, b, _) in zones):
                return False
            on_arc = any(a - 3.5 < s < b + 3.5 for (a, b, R, th) in arcs)
            return (not on_arc) or round(s, 6) in mids

        def nudge(s, lo, hi):
            for d in np.arange(0.0, 60.0, 0.5):
                for c_ in (s + d, s - d):
                    if lo < c_ < hi and free(c_):
                        return c_
            return None

        pos = []
        for (a, b, R, th) in arcs:
            m = round((a + b) / 2, 6)
            if m in mids and free(m):
                pos.append(m)
            elif R >= 15.0:
                c_ = nudge(m, a - 25.0, b + 25.0)
                if c_ is not None:
                    pos.append(c_)
        for (a, b, cov) in zones:
            if not cov:
                for c_, lo, hi in ((a - 1.0, a - 40.0, a), (b + 1.0, b, b + 40.0)):
                    c2 = nudge(c_, lo, hi)
                    if c2 is not None:
                        pos.append(c2)
        cover = sorted(set(r.bus)) + ([r.sb_exit + 6.0] if r.sb_exit > 0 else [])
        if r.sb_exit == 0:
            pos.append(15.0)
        if r.cap_end == 0:
            pos.append(Lr - 15.0)
        pos = sorted(set(round(p, 4) for p in pos))
        # fill gaps (zones without cover are bounded by straps at their ends)
        allp = sorted(set(pos + cover))
        add = []
        for a, b in zip(allp[:-1], allp[1:]):
            if b - a > 250.0 and not any(za < b and zb > a for (za, zb, _) in zones):
                n = int(math.ceil((b - a) / 250.0))
                for k in range(1, n):
                    c_ = nudge(a + (b - a) * k / n, a + 15.0, b - 15.0)
                    if c_ is not None:
                        add.append(c_)
        pos = sorted(pos + add)
        out = []
        for p in pos:
            if not out or p - out[-1] > 12.0:
                out.append(p)
        r.straps = out

    # feedline straps: avoid couplers later (zones added after resonators are placed)

    # ---------------------------------------------------------------- resonators (meander tuned to the target f)
    eps_w, Z_w = cpw_eps_z(W_CPW, G_CPW)
    eps_n, Z_n = cpw_eps_z(PW, PG)
    def inblock_len(net):
        p, q = ports[net], ports[net + "_SHORT"]
        return abs(p["x"] - q["x"]) + abs(p["y"] - q["y"])

    def tl_elems(r, Lib, lk=None):
        prof = r.profile()
        el = []
        def seg(l, w, g):
            eps, Z = cpw_eps_z(w, g)
            if lk is not None:
                Lp = Z * math.sqrt(eps) / C_LIGHT + lk / (w * 1e-6)
                Cp = math.sqrt(eps) / (Z * C_LIGHT)
                Z, eps = math.sqrt(Lp / Cp), (C_LIGHT ** 2) * Lp * Cp
            return ("T", l, Z, eps)
        shunts = []
        for s in r.straps:
            area = ST_W["al2_w"] * ST_W["neck_w"] if r.is_wide(s) else ST_N["al2_w"] * PW
            shunts.append((s, c_plate(area)))
        for s in r.bus:
            shunts.append((s, c_plate(BUS["al2_w"] * PW)))
        for (s, C, _) in r.shunts_x:
            shunts.append((s, C))
        bps = sorted(set(prof.bps) | {s for s, _ in shunts})
        pieces = []
        for a, b in zip(bps[:-1], bps[1:]):
            if b - a < 1e-9:
                continue
            w0, g0 = prof.at(a, +1)
            w1, g1 = prof.at(b, -1)
            nsub = 1 if (abs(w1 - w0) < 1e-9 and abs(g1 - g0) < 1e-9) else 10
            for k in range(nsub):
                f0, f1 = k / nsub, (k + 1) / nsub
                fm = (f0 + f1) / 2
                pieces.append((a + (b - a) * f0, a + (b - a) * f1, w0 + (w1 - w0) * fm, g0 + (g1 - g0) * fm))
        sh = sorted(shunts)
        j = len(sh) - 1
        # open end (s = L) -> port (s = 0) -> in-block line -> short
        for (a, b, w, g) in reversed(pieces):
            while j >= 0 and sh[j][0] >= b - 1e-9:
                el.append(("C", sh[j][1]))
                j -= 1
            el.append(seg(b - a, w, g))
        while j >= 0:
            el.append(("C", sh[j][1]))
            j -= 1
        el.append(seg(Lib, PW, PG))
        return el, shunts

    res_info = {}
    for net, (pp, rr, tk, xe, y1, dx, cdir, span_max) in res_entry.items():
        Lib = inblock_len(net)
        f_t = F_TARGET[net] * 1e9

        def make(n, span, lc=CPL_LEN):
            mp, mr = meander_pts(xe, y1, n, span, dx, y_c, cdir)
            mp[-1] = (xe + cdir * (R_RES + lc), y_c)
            pts = list(pp) + mp
            rad = list(rr) + mr
            r = full_route(net, pts, rad, tk)
            apply_field_bridges(r)
            r.cap_end = G_CPW
            # coupler: straight parallel run (no straps)
            s_cpl = r.path.length - lc
            r.zones.append((s_cpl - 1.0, r.path.length + 1.0, True))
            place_straps(r)
            r.coupler = dict(s0=s_cpl, x0=min(pts[-1][0], pts[-1][0] - cdir * lc), x1=max(pts[-1][0], pts[-1][0] - cdir * lc),
                             y=y_c, length=lc, dir=cdir)
            return r

        def freq(r):
            el, _ = tl_elems(r, Lib)
            return resonance(el, 6.3e9)

        chosen = None
        for n in (2, 4, 6, 8, 10):
            if y1 - (n - 1) * 2 * R_RES - 2 * R_RES < y_c + 2 * R_RES - 1e-9:
                break
            lo, hi = 2 * R_RES + 30.0, span_max
            flo, fhi = freq(make(n, lo)), freq(make(n, hi))
            if flo < f_t:
                raise RuntimeError(f"{net}: route too long for {F_TARGET[net]} GHz even with n={n}")
            if fhi > f_t:
                continue
            for _ in range(40):
                mid = (lo + hi) / 2
                if freq(make(n, mid)) > f_t:
                    lo = mid
                else:
                    hi = mid
            span = round(hi, 3)
            # strap insertion makes f(span) slightly discontinuous: finish with the coupler length (continuous)
            clo, chi = 140.0, 240.0
            if freq(make(n, span, clo)) >= f_t >= freq(make(n, span, chi)):
                for _ in range(30):
                    cm = (clo + chi) / 2
                    if freq(make(n, span, cm)) > f_t:
                        clo = cm
                    else:
                        chi = cm
                lc = round((clo + chi) / 2, 3)
            else:
                lc = CPL_LEN
            chosen = (n, span, lc)
            break
        assert chosen is not None, net
        r = make(*chosen)
        routes[net] = r
        el, shunts = tl_elems(r, Lib)
        f_model = resonance(el, f_t)
        Ls = 4e-7 * math.pi * 90e-9 / math.tanh(0.150 / 0.090)          # Nb, lambda_L = 90 nm (assumed), t = 150 nm
        el_k, _ = tl_elems(r, Lib, lk=Ls)
        f_lk = resonance(el_k, f_t)
        L_eff = C_LIGHT / (4 * f_t * math.sqrt(eps_w)) * 1e6
        res_info[net] = dict(port=net, f_target_GHz=F_TARGET[net], f_model_GHz=round(f_model / 1e9, 4),
                             f_with_Nb_kinetic_inductance_est_GHz=round(f_lk / 1e9, 4),
                             length_total_um=round(r.path.length + Lib, 1), length_die_um=round(r.path.length, 1),
                             length_inblock_um=round(Lib, 2), length_ideal_quarter_wave_10_6_um=round(L_eff, 1),
                             meander_runs=chosen[0], meander_span_um=chosen[1], n_straps=len(r.straps),
                             n_bus_straps=len(r.bus), n_crossings=len(r.shunts_x),
                             shunt_C_total_fF=round(sum(C for _, C in shunts) * 1e15, 2),
                             coupler=dict(x0=round(r.coupler["x0"], 1), x1=round(r.coupler["x1"], 1), y=y_c, dir=r.coupler["dir"],
                                          parallel_length_um=chosen[2], ground_strip_um=CPL_STRIP,
                                          type="elbow (parallel run above the feedline)"),
                             shorted_end="inside the block at %s_SHORT (catcher-loop side)" % net)

    # ---------------------------------------------------------------- straps on signal lines and feedline
    for net, r in routes.items():
        if net.startswith("RO_"):
            continue
        r.cap_end = 0.0
        place_straps(r)
    fz = []
    for net in res_entry:
        c_ = routes[net].coupler
        # arc side: the resonator bend comes within strap reach for ~26 um; open-end side: end gap + margin
        xa, xb = (c_["x0"] - 35.0, c_["x1"] + 12.0) if c_["dir"] > 0 else (c_["x0"] - 12.0, c_["x1"] + 35.0)
        s0 = feed.path.project((xa, Y_F))[0]
        s1 = feed.path.project((xb, Y_F))[0]
        fz.append((min(s0, s1), max(s0, s1), False))
    place_straps(feed, extra_zones=fz)

    # ---------------------------------------------------------------- geometry
    um = lambda v: int(round(v * 1000))
    def P_(arr):
        return db.Polygon([db.Point(um(x), um(y)) for x, y in arr])

    clear, al2, diel = db.Region(), db.Region(), db.Region()
    centres = {}
    route_list = list(routes.values()) + [feed]
    for r in route_list:
        prof = r.profile()
        Lr = r.path.length
        keep = []
        cuts = sorted(r.cuts)
        a = 0.0
        for (c0, c1, cap) in cuts:
            keep.append((a, c0, None if a == 0 else cap_prev, cap))
            cap_prev = cap
            a = c1
        keep.append((a, Lr, None if a == 0 else (cuts[-1][2] if cuts else None), r.cap_end))
        cpolys = []
        for (sa, sb, ca, cb) in keep:
            slots, centre = cpw_polys(r.path, prof, sa, sb, ca or 0.0, cb or 0.0)
            for sp in slots:
                clear.insert(P_(sp))
            cpolys.append(centre)
        centres[r.net] = cpolys
        # ground straps
        for s in r.straps:
            Pp, t = r.path.at(s)
            n = np.array([-t[1], t[0]])
            if r.is_wide(s):
                h = W_CPW / 2 + G_CPW
                hw, dw = ST_W["al2_w"] / 2, ST_W["diel_w"] / 2
                al2.insert(rect_poly(db, Pp, t, -hw, hw, -(h + ST_W["land"] + ST_W["contact"]), h + ST_W["land"] + ST_W["contact"]))
                diel.insert(rect_poly(db, Pp, t, -dw, dw, -(h + ST_W["land"]), h + ST_W["land"]))
            else:
                h = PW / 2 + PG
                hw, dw = ST_N["al2_w"] / 2, ST_N["diel_w"] / 2
                al2.insert(rect_poly(db, Pp, t, -hw, hw, -(h + ST_N["land"] + ST_N["contact"]), h + ST_N["land"] + ST_N["contact"]))
                diel.insert(rect_poly(db, Pp, t, -dw, dw, -(h + ST_N["land"]), h + ST_N["land"]))
    # bus straps over the crossover fields
    for f in (fE, fW):
        for xb in f["bus"]:
            al2.insert(P_([(xb - BUS["al2_w"] / 2, ytr[-1] - BUS["ext"]), (xb + BUS["al2_w"] / 2, ytr[-1] - BUS["ext"]),
                           (xb + BUS["al2_w"] / 2, ytr[0] + BUS["ext"]), (xb - BUS["al2_w"] / 2, ytr[0] + BUS["ext"])]))
            for yy in ytr:
                diel.insert(P_([(xb - BUS["diel_w"] / 2, yy - BUS["diel_hw"]), (xb + BUS["diel_w"] / 2, yy - BUS["diel_hw"]),
                                (xb + BUS["diel_w"] / 2, yy + BUS["diel_hw"]), (xb - BUS["diel_w"] / 2, yy + BUS["diel_hw"])]))
    # signal crossover bridges
    xo_list = []
    for k, cx_ in enumerate(crossings):
        rb = routes[cx_["bridge"]]
        s = cx_["s"][cx_["bridge"]]
        Pp, t = rb.path.at(s)
        if cx_["kind"] == "field":
            a0 = XB["strip"] + PW / 2 + PG + XB["pad_g"]
            ea = a0 + XB["pad"] - XB["al2_in"]
            al2.insert(rect_poly(db, Pp, t, -ea, ea, -XB["al2_w"] / 2, XB["al2_w"] / 2))
            dd = a0 + XB["diel_ov"]
            diel.insert(rect_poly(db, Pp, t, -dd, dd, -XB["diel_w"] / 2, XB["diel_w"] / 2))
        else:
            h = W_CPW / 2 + G_CPW + XBIG["strip"] + XBIG["endgap"]
            al2.insert(rect_poly(db, Pp, t, -(h + XBIG["land"]), h + XBIG["land"], -XBIG["al2_w"] / 2, XBIG["al2_w"] / 2))
            diel.insert(rect_poly(db, Pp, t, -(h + XBIG["diel_ov"]), h + XBIG["diel_ov"], -XBIG["diel_w"] / 2, XBIG["diel_w"] / 2))
        xo_list.append(dict(id=k + 1, kind=cx_["kind"], side=cx_["side"], bridge=cx_["bridge"], under=cx_["under"],
                            x=round(float(cx_["xy"][0]), 3), y=round(float(cx_["xy"][1]), 3)))

    # ---------------------------------------------------------------- launchers
    pad_marks, gnd_pads = [], []
    for nm, p in pads.items():
        c = np.array(p["pad_center_um"], float)
        u = np.array(p["outward"], float)
        tv = -u
        nv = np.array([-tv[1], tv[0]])
        hp = L["pad_um"][0] / 2
        loc = lambda tt, nn: c + tv * tt + nv * nn
        pad_marks.append((p, [loc(-hp, -hp), loc(hp, -hp), loc(hp, hp), loc(-hp, hp)]))
        if p["kind"] == "ground":
            gnd_pads.append(np.array([loc(-hp, -hp), loc(hp, -hp), loc(hp, hp), loc(-hp, hp)]))
            continue
        tl_ = L["taper_len_um"]
        hg = hp + LAUNCH_GAP_SIDE
        outer = [loc(-hp - LAUNCH_GAP_END, -hg), loc(hp, -hg), loc(hp + tl_, -(W_CPW / 2 + G_CPW)),
                 loc(hp + tl_, W_CPW / 2 + G_CPW), loc(hp, hg), loc(-hp - LAUNCH_GAP_END, hg)]
        cond = [loc(-hp, -hp), loc(hp, -hp), loc(hp + tl_, -W_CPW / 2), loc(hp + tl_, W_CPW / 2), loc(hp, hp), loc(-hp, hp)]
        clear.insert(db.Region(P_(outer)) - db.Region(P_(cond)))

    # ---------------------------------------------------------------- test structures, marks, label
    ly = db.Layout()
    ly.dbu = 0.001
    ly.read(block_gds)                                  # brings the frozen block cell (QBFX2_ROWS)
    bname = bp.get("block_cell", "QBFX2_ROWS")
    blk = ly.cell(bname)
    top = ly.create_cell("QBFX2_DIE")
    top.insert(db.CellInstArray(blk.cell_index(), db.Trans(db.Vector(um(BX0), um(BY0)))))
    ts = _ts_cells(ly, jj)
    ts_place = {"JJ_RAIL": (4500.0, 5800.0), "JJ_MID": (5500.0, 5800.0), "GRAL": (4500.0, 6450.0),
                "AL1_STRIP": (5500.0, 6450.0), "AL2_STRIP": (4500.0, 7050.0), "NB_MEANDER": (5500.0, 7050.0),
                "SIN_CAP": (4500.0, 7700.0), "XO_CHAIN": (5500.0, 7700.0)}
    windows = db.Region()
    ts_info = []
    for nm, (cell, win, tpads, info) in ts.items():
        ox, oy = ts_place[nm]
        top.insert(db.CellInstArray(cell.cell_index(), db.Trans(db.Vector(um(ox), um(oy)))))
        for w in win:
            windows.insert(P_(w + np.array([ox, oy])))
        ts_info.append(dict(name=nm, origin=[ox, oy], pads=[dict(pin=pn, x=round(ox + x, 3), y=round(oy + yy, 3),
                                                                  size_um=100.0) for (pn, x, yy) in tpads], **info))
    windows.merge()
    etch = db.Region()                                  # negative features etched into the ground plane
    marks = []
    for (mx, my, nm) in ((700.0, 700.0, "SW"), (9300.0, 700.0, "SE"), (700.0, 9300.0, "NW"), (9300.0, 9300.0, "NE")):
        for (x0, y0, x1, y1) in ((-150, -5, 150, 5), (-5, -150, 5, -10), (-5, 10, 5, 150)):
            etch.insert(db.Box(um(mx + x0), um(my + y0), um(mx + x1), um(my + y1)))
        for (ox, oy) in ((-80, -80), (80, -80), (-80, 80), (80, 80)):
            etch.insert(db.Box(um(mx + ox - 5), um(my + oy - 5), um(mx + ox + 5), um(my + oy + 5)))
        marks.append(dict(name=f"ALIGN_{nm}", x=mx, y=my, kind="etched cross 300 um x 10 um + 4 etched 10 um e-beam squares"))
    etch.insert(P_([(1050.0, 9550.0), (1400.0, 9550.0), (1050.0, 9200.0)]))
    marks.append(dict(name="ORIENTATION", x=1170.0, y=9430.0, kind="etched right triangle pointing to the NW corner"))
    # label: etched text; counters become islands -> stencil bars to the ground above the text
    tp = gdstk.text(LABEL, 50.0, (0.0, 0.0))
    allpts = np.concatenate([q.points for q in tp])
    lx0 = 5000.0 - (allpts[:, 0].max() + allpts[:, 0].min()) / 2
    ly0 = 8350.0
    lab = db.Region()
    for q in tp:
        lab.insert(P_(q.points + np.array([lx0, ly0])))
    lab.merge()
    patch = db.Region(lab.bbox().enlarged(um(30), um(30)))
    isl = (patch - lab).merged()
    bars = db.Region()
    pb = patch.bbox()
    for poly in isl.each():
        b = poly.bbox()
        if b.left > pb.left and b.right < pb.right and b.bottom > pb.bottom and b.top < pb.top:
            xm = (b.left + b.right) // 2
            bars.insert(db.Box(xm - um(1.5), (b.bottom + b.top) // 2, xm + um(1.5), lab.bbox().top + um(10)))
    lab = lab - bars
    etch += lab
    marks.append(dict(name="LABEL", text=LABEL, x=5000.0, y=ly0 + 22.0, kind="etched in Nb, 50 um font, stencil bars"))

    # ---------------------------------------------------------------- ground plane with flux-trapping holes
    chip = db.Region(db.Box(um(DICING), um(DICING), um(DIE - DICING), um(DIE - DICING)))
    blockbox = db.Region(db.Box(um(BX0), um(BY0), um(BX0 + BW), um(BY0 + BH)))
    clear.merge()
    gndpad_r = db.Region()
    for g in gnd_pads:
        gndpad_r.insert(P_(g))
    kh = um(DIE_RULES["HOLE_KEEP"])
    keep = (clear + windows + etch + blockbox + gndpad_r).merged().sized(kh) + (db.Region(db.Box(0, 0, um(DIE), um(DIE))) - chip).sized(kh)
    allowed = chip - keep
    hl = db.Layout()
    hl.dbu = ly.dbu
    hc = hl.create_cell("H")
    lh = hl.layer(1, 0)
    hc.shapes(lh).insert(db.Box(-um(HOLE / 2), -um(HOLE / 2), um(HOLE / 2), um(HOLE / 2)))
    tc = hl.create_cell("A")
    n_h = int((DIE - 2 * DICING) / HOLE_PITCH)
    tc.insert(db.CellInstArray(hc.cell_index(), db.Trans(db.Vector(um(DICING + HOLE_PITCH / 2), um(DICING + HOLE_PITCH / 2))),
                               db.Vector(um(HOLE_PITCH), 0), db.Vector(0, um(HOLE_PITCH)), n_h, n_h))
    cand = db.Region(tc.begin_shapes_rec(lh))
    holes = (cand & allowed).with_area(um(HOLE) * um(HOLE) - 10, None, False)
    nb = chip - clear - windows - etch - blockbox - holes

    # ---------------------------------------------------------------- write layout
    li = {k: ly.layer(*v) for k, v in dict(NB=L_NB, AL2=L_AL2, DIEL=L_DIEL, TP=L_TXT_PAD, TPO=L_TXT_PORT,
                                           TN=L_TXT_NOTE, OUT=L_OUTLINE, DIC=L_DICING, PM=L_PADMARK,
                                           BM=L_BLOCKMARK).items()}
    T = 500.0
    nt = int(math.ceil((DIE - 2 * DICING) / T))
    for i in range(nt):
        for j in range(nt):
            tb = db.Box(um(DICING + i * T), um(DICING + j * T), um(min(DICING + (i + 1) * T, DIE - DICING)),
                        um(min(DICING + (j + 1) * T, DIE - DICING)))
            top.shapes(li["NB"]).insert(nb & db.Region(tb))
    top.shapes(li["AL2"]).insert(al2.merged())
    top.shapes(li["DIEL"]).insert(diel.merged())
    top.shapes(li["OUT"]).insert(db.Box(0, 0, um(DIE), um(DIE)))
    top.shapes(li["DIC"]).insert(db.Region(db.Box(0, 0, um(DIE), um(DIE))) - chip)
    top.shapes(li["BM"]).insert(db.Box(um(BX0), um(BY0), um(BX0 + BW), um(BY0 + BH)))
    for p, corners in pad_marks:
        top.shapes(li["PM"]).insert(P_(corners))
        cxp, cyp = p["pad_center_um"]
        top.shapes(li["TP"]).insert(db.Text(p["net"], db.Trans(um(cxp), um(cyp))))
    port_rows = []
    for n, p in sig.items():
        x, yy = die_xy(p)
        dx_ = -0.25 if p["direction"] == "W" else 0.25
        top.shapes(li["TPO"]).insert(db.Text(n, db.Trans(um(x + dx_), um(yy))))
        port_rows.append(dict(name=n, x=round(x, 4), y=round(yy, 4), direction=p["direction"], kind=p["kind"],
                              probe=[round(x + dx_, 4), round(yy, 4)], width=p["width"], gap=p["gap"]))
    for n in ("GND_N", "GND_S", "GND_W_TOP", "GND_W_BOT", "GND_E_TOP", "GND_E_BOT"):
        p = ports[n]
        x, yy = die_xy(p)
        d = {"N": (0, 2), "S": (0, -2), "W": (-2, 0), "E": (2, 0)}[p["direction"]]
        top.shapes(li["TPO"]).insert(db.Text(n, db.Trans(um(x + d[0]), um(yy + d[1]))))
        port_rows.append(dict(name=n, x=x, y=yy, direction=p["direction"], kind="ground", probe=[x + d[0], yy + d[1]]))
    for xo in xo_list:
        top.shapes(li["TN"]).insert(db.Text(f"XO{xo['id']}:{xo['bridge']}/{xo['under']}", db.Trans(um(xo["x"]), um(xo["y"]))))
    for m in marks:
        top.shapes(li["TN"]).insert(db.Text(m["name"], db.Trans(um(m["x"]), um(m["y"]))))
    os.makedirs(os.path.dirname(os.path.abspath(out_gds)), exist_ok=True)
    ly.write(out_gds)

    # ---------------------------------------------------------------- as-built record
    def route_rec(r):
        prof = r.profile()
        return dict(net=r.net, kind=r.kind, length_um=round(r.path.length, 2), points=[list(map(float, p)) for p in r.pts],
                    radii=r.radii, s_taper=r.s_taper, cuts=[list(c) for c in r.cuts], straps=[round(s, 4) for s in r.straps],
                    bus=[round(s, 4) for s in r.bus], sb_exit=r.sb_exit, cap_end=r.cap_end,
                    profile=[list(map(float, pc)) for pc in prof.pieces()],
                    arcs=[[p[-2], p[-1], p[2]] for p in r.path.arcs()])
    nets_pad_port = {}
    for nm, p in pads.items():
        if p["kind"] == "ground":
            continue
        nets_pad_port[p["net"]] = dict(pad_id=p["id"], pad_center=p["pad_center_um"], side=p["side"],
                                       port=p["net"] if p["net"] in sig else None)
    asb = dict(
        die=dict(size_um=[DIE, DIE], dicing_lane_um=DICING, origin="bottom-left, y up", top_cell="QBFX2_DIE",
                 block=dict(cell=bname, origin_um=[BX0, BY0], orientation="R0 (rows along x)", size_um=[BW, BH],
                            source=os.path.relpath(block_gds, os.path.dirname(os.path.abspath(out_gds))))),
        layers=dict(mask={k: list(v) for k, v in MASK_LAYERS.items()},
                    text=dict(pad_nets=list(L_TXT_PAD), block_ports=list(L_TXT_PORT), test_pads=list(L_TXT_TS), notes=list(L_TXT_NOTE)),
                    documentation=dict(outline=list(L_OUTLINE), dicing=list(L_DICING), launcher_pads=list(L_PADMARK),
                                       probe_pads=list(L_TSPAD), block_outline=list(L_BLOCKMARK))),
        cpw=dict(main=dict(w=W_CPW, g=G_CPW, eps_eff=round(eps_w, 4), Z0_ohm=round(Z_w, 2)),
                 port=dict(w=PW, g=PG, eps_eff=round(eps_n, 4), Z0_ohm=round(Z_n, 2)), taper_um=L_TAPER,
                 bend_radius_um=dict(crossover_field=R_SB, narrow=R_N, main=R_M, meander=R_RES)),
        pads=[dict(id=p["id"], net=p["net"], side=p["side"], kind=p["kind"], center=p["pad_center_um"],
                   size=p["pad_size_um"], cpw_start=list(cpw_start(nm)) if p["kind"] != "ground" else None)
              for nm, p in sorted(pads.items(), key=lambda t: t[1]["id"])],
        block_ports=port_rows,
        nets=nets_pad_port,
        routes={r.net: route_rec(r) for r in route_list},
        crossovers=xo_list,
        crossover_fields={s: dict(x_exit=f["x_exit"], columns=f["ncol"], bus_x=f["bus"], order_out=f["final"])
                          for s, f in fields.items()},
        resonators=res_info,
        feedline=dict(nets=["RO_IN", "RO_OUT"], y_um=Y_F, length_um=round(feed.path.length, 1), n_straps=len(feed.straps)),
        junction_targets=dict(block_clusters=jcl, test_arrays=jj),
        test_structures=ts_info,
        marks=marks,
        holes=dict(size_um=HOLE, pitch_um=HOLE_PITCH, count=int(holes.count()), keepout_um=DIE_RULES["HOLE_KEEP"]),
        straps=dict(n_individual=int(sum(len(r.straps) for r in route_list)), n_bus=int(len(fE["bus"]) + len(fW["bus"])),
                    geometry=dict(wide=ST_W, narrow=ST_N, bus=BUS, crossover_narrow=XB, crossover_gate_feed=XBIG)),
    )
    asb_path = os.path.join(os.path.dirname(os.path.abspath(out_gds)), "die_ports_asbuilt.json")
    json.dump(asb, open(asb_path, "w"), indent=1, default=float)
    out = dict(gds=os.path.abspath(out_gds), asbuilt=asb_path, holes=int(holes.count()), crossovers=len(xo_list),
               resonators={k: v["f_model_GHz"] for k, v in res_info.items()}, build_s=round(time.time() - t_start, 1))
    if previews:
        out["previews"] = render_previews(out_gds, BX0, BY0, BW, BH, routes, res_info, pads, cpw_start)
    return out


# ===================================================================================================== previews
def render_previews(gds, BX0, BY0, BW, BH, routes, res_info, pads, cpw_start):
    import klayout.db as db
    import klayout.lay as lay
    d = os.path.dirname(os.path.abspath(gds))
    lv = lay.LayoutView()
    lv.set_config("background-color", "#ffffff")
    lv.set_config("grid-visible", "false")
    lv.set_config("text-visible", "true")
    lv.set_config("text-color", "#000000")
    lv.load_layout(gds, True)
    lv.max_hier()
    lv.clear_layers()
    spec = [(L_NB, "#3b5ba5", 0, "Nb"), (L_GRAL, "#2ca02c", 0, "grAl"), (L_AL1, "#ff7f0e", 0, "AL1"),
            (L_AL2, "#d62728", 0, "AL2"), (L_DIEL, "#e6c300", 5, "SiNx"), (L_TXT_PAD, "#000000", 1, "pad nets"),
            (L_PADMARK, "#000000", 1, "pads"), (L_BLOCKMARK, "#7f7f7f", 1, "block"), (L_TSPAD, "#000000", 1, "probe pads")]
    for (l, c, dith, nm) in spec:
        lp = lay.LayerPropertiesNode()
        lp.source = f"{l[0]}/{l[1]}@1"
        lp.fill_color = int(c[1:], 16)
        lp.frame_color = int(c[1:], 16)
        lp.dither_pattern = dith
        lp.name = nm
        lv.insert_layer(lv.end_layers(), lp)
    out = {}

    def shot(name, box, w=1600, h=1600):
        lv.zoom_box(db.DBox(*box))
        p = os.path.join(d, f"die_preview_{name}.png")
        lv.save_image(p, w, h)
        out[name] = p

    shot("full", (-100, -100, 10100, 10100), 2000, 2000)
    shot("block", (BX0 - 520, BY0 - 260, BX0 + BW + 520, BY0 + BH + 260), 2400, 900)
    c = np.array(pads["TRAP_A0"]["pad_center_um"])
    shot("launcher", (c[0] - 230, c[1] - 320, c[0] + 560, c[1] + 320), 1600, 1300)
    rc = res_info["RO_CATCHER_A0"]["coupler"]
    shot("coupler", (rc["x0"] - 150, Y_F - 90, rc["x1"] + 90, Y_F + 260), 1800, 1100)
    shot("crossovers", (BX0 + BW - 5, BY0 + 40, BX0 + BW + 170, BY0 + 250), 1600, 1900)
    return out


# ===================================================================================================== check
def check_die(out_gds, die_pads_json, report_path, max_examples: int = 5) -> dict:
    """Die-level DRC + connectivity + pad-spec + resonator report.  Reads die_ports_asbuilt.json next to out_gds."""
    import klayout.db as db
    t0 = time.time()
    asb = json.load(open(os.path.join(os.path.dirname(os.path.abspath(out_gds)), "die_ports_asbuilt.json")))
    dp = json.load(open(die_pads_json))
    ly = db.Layout()
    ly.read(out_gds)
    top = ly.cell(asb["die"]["top_cell"])
    dbu = ly.dbu
    um = lambda v: int(round(v * 1000))
    li = {k: ly.layer(*v) for k, v in dict(NB=L_NB, GRAL=L_GRAL, AL1=L_AL1, AL2=L_AL2, DIEL=L_DIEL).items()}

    def R(k):
        r = db.Region(top.begin_shapes_rec(li[k]))
        r.merged_semantics = True
        return r.merged()

    NB, GR, A1, A2, DI = R("NB"), R("GRAL"), R("AL1"), R("AL2"), R("DIEL")
    bx0, by0 = asb["die"]["block"]["origin_um"]
    bw, bh = asb["die"]["block"]["size_um"]
    bbox = db.Box(um(bx0), um(by0), um(bx0 + bw), um(by0 + bh))
    inner = bbox.enlarged(-um(DIE_RULES["BLOCK_MARGIN"]), -um(DIE_RULES["BLOCK_MARGIN"]))
    blockR = db.Region(bbox)
    res = dict(gds=os.path.abspath(out_gds), rules=RULES, die_rules=DIE_RULES, checks={}, block_internal={})

    def ex_edges(ep):
        out = []
        for i, e in enumerate(ep.each()):
            if i >= max_examples:
                break
            b = e.bbox()
            out.append([round(b.left * dbu, 3), round(b.bottom * dbu, 3), round(b.right * dbu, 3), round(b.top * dbu, 3)])
        return out

    def split(ep):
        die_, blk_ = db.EdgePairs(), db.EdgePairs()
        for e in ep.each():
            (blk_ if inner.contains(e.bbox().p1) and inner.contains(e.bbox().p2) else die_).insert(e)
        return die_, blk_

    def add(name, n, desc, examples=None):
        res["checks"][name] = dict(violations=int(n), rule=desc, examples=examples or [])

    # ------------------------------------------------ width / space (same rules as drc.py), die vs block interior
    for nm, r, w, s in (("NB", NB, RULES["NB_W"], RULES["NB_S"]), ("GRAL", GR, RULES["GRAL_W"], RULES["GRAL_S"]),
                        ("AL1", A1, RULES["AL1_W"], RULES["AL1_S"]), ("AL2", A2, RULES["AL2_W"], RULES["AL2_S"]),
                        ("DIEL", DI, RULES["DIEL_W"], RULES["DIEL_S"])):
        for ck, ep in ((f"{nm}.W", r.width_check(um(w))), (f"{nm}.S", r.space_check(um(s)))):
            d_, b_ = split(ep)
            add(ck, d_.count(), f"{nm} min {'width' if ck.endswith('W') else 'space'} {w if ck.endswith('W') else s} um", ex_edges(d_))
            res["block_internal"][ck] = int(b_.count())
    outside = lambda r: r.not_inside(db.Region(inner))
    gc = outside(GR & (A1 + NB))
    add("GRAL.C", gc.width_check(um(RULES["GRAL_C"])).count(), "granular Al contact overlap width >= 0.15 um")
    # ------------------------------------------------ junction classification (targets from the frozen block)
    ov_all = (A1 & A2) - DI
    ov_blk = ov_all.inside(db.Region(inner))
    ov = ov_all - ov_blk
    areas = sorted(p.area() * dbu * dbu for p in ov_blk.each() if p.area() * dbu * dbu < RULES["CONTACT_MIN"])
    clusters = []
    for a in areas:
        if clusters and a <= clusters[-1][0] * (1 + RULES["JJ_TOL"]):
            clusters[-1].append(a)
        else:
            clusters.append([a])
    targets = {}
    for nm_, cl in zip(("rail", "middle", "other1", "other2"), sorted(clusters, key=lambda c: -np.median(c))):
        targets[nm_] = float(np.median(cl))
    cls = dict(junction={k: 0 for k in targets}, contact=0, bad=[])
    jj_regions = db.Region()
    for poly in ov.each():
        a = poly.area() * dbu * dbu
        if a >= RULES["CONTACT_MIN"]:
            cls["contact"] += 1
            continue
        hit = [k for k, A in targets.items() if abs(a / A - 1) <= RULES["JJ_TOL"]]
        if hit:
            cls["junction"][hit[0]] += 1
            jj_regions.insert(poly)
        else:
            b = poly.bbox()
            cls["bad"].append(dict(area_um2=round(a, 5), bbox=[b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu]))
    add("JJ.CLASS", len(cls["bad"]), "die-level AL1&AL2-DIEL: junction within +-5 % of a block target or contact >= 1 um^2",
        cls["bad"][:max_examples])
    add("JJ.W", jj_regions.width_check(um(RULES["JJ_W"])).count(), "junction sides >= 0.10 um")
    other = ov - jj_regions
    ejs = (jj_regions.separation_check(other, um(RULES["JJ_S"])).count() if not other.is_empty() else 0) + \
        jj_regions.space_check(um(RULES["JJ_S"])).count()
    add("JJ.S", ejs, "junction to other junction/contact >= 0.50 um")
    n_exp = {k: sum(t["n_junctions"] for t in asb["test_structures"] if t["name"] == ("JJ_RAIL" if k == "rail" else "JJ_MID"))
             for k in ("rail", "middle")}
    bad_n = sum(1 for k in n_exp if cls["junction"].get(k, 0) != n_exp[k])
    add("JJ.N", bad_n, "die-level (test-array) junction counts equal the as-built arrays",
        [dict(found=cls["junction"], expected=n_exp)])
    res["junctions"] = dict(targets_um2_from_block=targets, die_level_found=cls["junction"], die_level_expected=n_exp,
                            die_level_contacts=cls["contact"],
                            block_found={k: sum(1 for p in ov_blk.each() if abs(p.area() * dbu * dbu / A - 1) <= RULES["JJ_TOL"])
                                         for k, A in targets.items()})
    # ------------------------------------------------ contacts, dielectric enclosure / keep-out
    ct = outside(((A1 & NB) + (A2 & NB)).merged() - DI)
    small = [p for p in ct.each() if p.area() * dbu * dbu < RULES["CT_A"]]
    add("CT.A", len(small), "Al-on-Nb contact regions >= 1.00 um^2",
        [[round(p.bbox().left * dbu, 3), round(p.bbox().bottom * dbu, 3), round(p.area() * dbu * dbu, 4)] for p in small[:max_examples]])
    cap = outside(A1 & A2 & DI)
    een = DI.enclosing_check(cap, um(RULES["DIEL_EN"]))
    add("DIEL.EN", een.count() + (cap - DI.sized(-um(RULES["DIEL_EN"]))).count(), "AL1&AL2&DIEL enclosed by DIEL >= 0.20 um")
    esj = DI.separation_check(ov, um(RULES["DIEL_SJ"])).count() + (DI & ov.sized(um(RULES["DIEL_SJ"]) - 1)).count()
    add("DIEL.SJ", esj, "DIEL to die-level junctions/contacts >= 0.20 um")
    # ------------------------------------------------ XO.ISO: Nb of another net under AL2 is inside DIEL by >= 0.5 um
    A2d = outside(A2)
    shr = DI.sized(-um(DIE_RULES["XO_ISO"]))
    bad_iso = []
    for s in A2d.each():
        b = s.bbox().enlarged(um(3), um(3))
        nbl = (db.Region(top.begin_shapes_rec_touching(li["NB"], b)) & db.Region(b)).merged()
        sr = db.Region(s)
        cont = (sr & nbl) - DI
        own = nbl.interacting(cont)
        foreign = (sr & nbl) - own
        if not (foreign - shr).is_empty():
            bb = s.bbox()
            bad_iso.append([round(bb.left * dbu, 2), round(bb.bottom * dbu, 2), round(bb.right * dbu, 2), round(bb.top * dbu, 2)])
    add("XO.ISO", len(bad_iso), "AL2 over Nb of another net lies on SiNx with >= 0.5 um enclosure", bad_iso[:max_examples])
    # ------------------------------------------------ dicing lane
    lane = db.Region(db.Box(0, 0, um(DIE), um(DIE))) - db.Region(db.Box(um(DICING), um(DICING), um(DIE - DICING), um(DIE - DICING)))
    inlane = sum((r & lane).count() for r in (NB, GR, A1, A2, DI))
    add("DIE.EDGE", inlane, "no mask shapes in the 100 um dicing lane")
    # ------------------------------------------------ flux-trapping holes: size and 20 um keep-out
    chipR = db.Region(db.Box(um(DICING), um(DICING), um(DIE - DICING), um(DIE - DICING)))
    gaps = (chipR - NB - blockR).merged()
    holes = gaps.with_area(um(HOLE) * um(HOLE) - 10, um(HOLE) * um(HOLE) + 10, False).with_bbox_width(um(HOLE), um(HOLE) + 1, False)
    feats = (gaps - holes) + blockR + lane + A2d + DI
    for p in dp["pads"]:
        if p["kind"] == "ground":
            cxp, cyp = p["pad_center_um"]
            feats.insert(db.Box(um(cxp - 120), um(cyp - 120), um(cxp + 120), um(cyp + 120)))
    feats = feats.merged()
    near = holes.interacting(feats.sized(um(DIE_RULES["HOLE_KEEP"]) - 2))
    add("HOLE.KEEP", near.count(), "flux holes >= 20 um from CPWs, resonators, pads, test structures, marks, block, lane",
        [[round(p.bbox().center().x * dbu, 2), round(p.bbox().center().y * dbu, 2)] for p in list(near.each())[:max_examples]])
    res["holes"] = dict(count=int(holes.count()), size_um=HOLE, pitch_um=HOLE_PITCH)

    # ------------------------------------------------ connectivity (die level: block interior removed)
    tl = db.Layout()
    tl.dbu = dbu
    tcell = tl.create_cell("DIE_LEVEL")
    tli = {k: tl.layer(*v) for k, v in dict(NB=L_NB, GRAL=L_GRAL, AL1=L_AL1, AL2=L_AL2, DIEL=L_DIEL).items()}
    T = 500.0
    nbd = NB - blockR
    nt = int(math.ceil(DIE / T))
    for i in range(nt):
        for j in range(nt):
            tb = db.Region(db.Box(um(i * T), um(j * T), um((i + 1) * T), um((j + 1) * T)))
            tcell.shapes(tli["NB"]).insert(nbd & tb)
    for k, r in (("GRAL", GR), ("AL1", A1), ("AL2", A2), ("DIEL", DI)):
        tcell.shapes(tli[k]).insert(r - blockR)

    def extract(layout, cell, lmap, use_gral):
        l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(layout, cell, []))
        nb_ = l2n.make_layer(lmap["NB"], "nb")
        a1_ = l2n.make_layer(lmap["AL1"], "al1")
        a2_ = l2n.make_layer(lmap["AL2"], "al2")
        di_ = l2n.make_layer(lmap["DIEL"], "diel")
        c1 = (a1_ & nb_) - di_
        c2 = (a2_ & nb_) - di_
        c12 = ((a1_ & a2_) - di_).with_area(um(1.0) * um(1.0), None, False)
        for nm_, lr in (("c1", c1), ("c2", c2), ("c12", c12)):
            l2n.register(lr, nm_)
        conds = [nb_, a1_, a2_, c1, c2, c12]
        if use_gral:
            gr_ = l2n.make_layer(lmap["GRAL"], "gral")
            cg = gr_ & (nb_ + a1_)
            l2n.register(cg, "cg")
            conds += [gr_, cg]
        for lr in conds:
            l2n.connect(lr)
        l2n.connect(nb_, c1); l2n.connect(a1_, c1)
        l2n.connect(nb_, c2); l2n.connect(a2_, c2)
        l2n.connect(a1_, c12); l2n.connect(a2_, c12)
        if use_gral:
            l2n.connect(gr_, cg); l2n.connect(nb_, cg); l2n.connect(a1_, cg)
        l2n.extract_netlist()
        return l2n, nb_

    t1 = time.time()
    l2n, nbL = extract(tl, tcell, tli, True)
    t_l2n = time.time() - t1

    def probe(x, yy):
        n = l2n.probe_net(nbL, db.DPoint(x, yy))
        return None if n is None else n.cluster_id

    gnd = probe(DICING + 5.0, DIE / 2)
    terms = {}                                    # cluster -> list of terminal names
    def term(name, x, yy):
        c = probe(x, yy)
        terms.setdefault(c, []).append(name)
        return c
    pad_net, port_net, ts_net = {}, {}, {}
    for p in dp["pads"]:
        nm_ = p["net"] if p["kind"] != "ground" else f"GND#{p['id']}"
        pad_net[p["id"]] = term(f"PAD:{nm_}", *p["pad_center_um"])
    for pr in asb["block_ports"]:
        port_net[pr["name"]] = term(f"PORT:{pr['name']}", *pr["probe"])
    for t in asb["test_structures"]:
        for pp in t["pads"]:
            ts_net[(t["name"], pp["pin"])] = term(f"TS:{t['name']}_{pp['pin']}", pp["x"], pp["y"])
    conn = {}
    ok_all = True
    for p in dp["pads"]:
        if p["kind"] == "ground":
            continue
        net = p["net"]
        c = pad_net[p["id"]]
        tl_ = terms.get(c, [])
        if net in ("RO_IN", "RO_OUT"):
            exp = {"PAD:RO_IN", "PAD:RO_OUT"}
            port = None
        else:
            exp = {f"PAD:{net}", f"PORT:{net}"}
            port = net
        ok = c is not None and c != gnd and set(tl_) == exp
        ok_all &= ok
        conn[net] = dict(pad_id=p["id"], port=port, reaches_port=(port is None or (port_net.get(port) == c and c is not None)),
                         terminals_on_net=sorted(tl_), shorted_to_ground=(c == gnd), ok=bool(ok))
    for pr in asb["block_ports"]:
        if pr["kind"] == "catcher_readout_coupling":
            c = port_net[pr["name"]]
            tl_ = terms.get(c, [])
            ok = c is not None and c != gnd and tl_ == [f"PORT:{pr['name']}"]
            ok_all &= ok
            conn[pr["name"]] = dict(port=pr["name"], kind="readout resonator (open end at the feedline coupler)",
                                    terminals_on_net=sorted(tl_), shorted_to_ground=(c == gnd), ok=bool(ok))
    gpads = {p["id"]: pad_net[p["id"]] == gnd for p in dp["pads"] if p["kind"] == "ground"}
    gports = {n: port_net[n] == gnd for n in port_net if n.startswith("GND_")}
    ok_g = all(gpads.values()) and all(gports.values())
    ok_all &= ok_g
    conn["GND"] = dict(pads_on_ground=gpads, block_ground_ports_on_ground=gports, ok=bool(ok_g))
    ts_ok = {}
    for t in asb["test_structures"]:
        cs = [ts_net[(t["name"], pp["pin"])] for pp in t["pads"]]
        iso = all(c is not None and c != gnd and all(x.startswith(f"TS:{t['name']}_") for x in terms[c]) for c in cs)
        ts_ok[t["name"]] = bool(iso)
    ok_all &= all(ts_ok.values())
    conn["TEST_STRUCTURES_isolated"] = ts_ok
    # shorts: any net carrying terminals of two different signal names
    shorts = []
    for c, tl_ in terms.items():
        names = {x.split(":", 1)[1] for x in tl_ if not x.startswith("TS:")}
        names = {("RO_FEED" if n in ("RO_IN", "RO_OUT") else n) for n in names if not n.startswith("GND")}
        if c == gnd and names:
            shorts.append(dict(net="GND", with_=sorted(names)))
        elif len(names) > 1:
            shorts.append(dict(net=c, with_=sorted(names)))
    ok_all &= not shorts
    # floating Nb (die level): every Nb polygon is on a net with a terminal or on ground
    floating = []
    tnets = set(terms) | {gnd}
    nbm = nbd.merged()
    big = [p for p in nbm.each() if p.bbox().width() > um(5000)]
    if len(big) != 1 or not big[0].inside(db.Point(um(DICING + 5.0), um(DIE / 2))):
        floating.append(dict(note="ground plane is not a single polygon", n_large=len(big)))
    for poly in nbm.each():
        if poly.bbox().width() > um(5000):
            continue
        pt = None
        for trp in db.Region(poly).decompose_trapezoids_to_region().each():
            bb = trp.bbox()
            pt = ((bb.left + bb.right) / 2 * dbu, (bb.bottom + bb.top) / 2 * dbu)
            break
        if probe(*pt) not in tnets:
            b = poly.bbox()
            floating.append([round(b.left * dbu, 2), round(b.bottom * dbu, 2), round(b.right * dbu, 2), round(b.top * dbu, 2)])
    add("NB.FLOAT", len(floating), "every die-level Nb piece reaches ground, a pad, a block port or a probe pad", floating[:max_examples])
    res["connectivity"] = dict(per_net=conn, shorts=shorts, all_ok=bool(ok_all and not floating),
                               method="klayout LayoutToNetlist on the die-level geometry (block interior removed): NB, AL1, "
                                      "AL2, GRAL conductors; Al-on-Nb and AL1/AL2 contacts >= 1 um^2 connect (outside SiNx); "
                                      "junction overlaps do not", l2n_s=round(t_l2n, 2))

    # ------------------------------------------------ through-block (informational): full die incl. the block
    full_l2n, nbF = extract(ly, top, li, False)
    def probeF(x, yy):
        n = full_l2n.probe_net(nbF, db.DPoint(x, yy))
        return None if n is None else n.cluster_id
    gF = probeF(DICING + 5.0, DIE / 2)
    thr = {}
    for p in dp["pads"]:
        if p["kind"] != "ground":
            thr[p["net"]] = "ground (shorted inside the block)" if probeF(*p["pad_center_um"]) == gF else "isolated from ground"
    for pr in asb["block_ports"]:
        if pr["kind"] == "catcher_readout_coupling":
            thr[pr["name"]] = "ground (shorted inside the block)" if probeF(*pr["probe"]) == gF else "isolated from ground"
    res["connectivity"]["through_block_info"] = thr

    # ------------------------------------------------ pads vs spec
    pm = db.Region(top.begin_shapes_rec(ly.layer(*L_PADMARK))).merged()
    texts = {}
    it = top.begin_shapes_rec(ly.layer(*L_TXT_PAD))
    while not it.at_end():
        sh = it.shape()
        if sh.is_text():
            tt = sh.text.transformed(it.trans())
            texts[(round(tt.x * dbu, 3), round(tt.y * dbu, 3))] = tt.string
        it.next()
    pad_rows, pads_ok = [], True
    for p in dp["pads"]:
        cxp, cyp = p["pad_center_um"]
        sx, sy = p["pad_size_um"]
        want = db.Box(um(cxp - sx / 2), um(cyp - sy / 2), um(cxp + sx / 2), um(cyp + sy / 2))
        mark = any(q.bbox() == want for q in pm.each())
        nbfull = (db.Region(want) - NB).is_empty()
        lab = texts.get((round(cxp, 3), round(cyp, 3)))
        on_net = (pad_net[p["id"]] == gnd) if p["kind"] == "ground" else (conn.get(p["net"], {}).get("ok", False))
        ok = mark and nbfull and lab == p["net"] and on_net
        pads_ok &= ok
        pad_rows.append(dict(id=p["id"], net=p["net"], center=[cxp, cyp], marker=mark, nb_pad_complete=nbfull, label=lab,
                             net_ok=bool(on_net), ok=bool(ok)))
    n_marks = pm.count()
    pads_ok &= (n_marks == len(dp["pads"]))
    res["pads_match_spec"] = bool(pads_ok)
    res["pads"] = dict(n_markers=int(n_marks), rows=pad_rows)

    # ------------------------------------------------ CPW cross-section and strap checks along every route
    xs_bad, xs_n = [], 0
    br_bad, bend_bad = [], []
    strap_rows = {}
    for net, rr in asb["routes"].items():
        path = Path(rr["points"], rr["radii"])
        pieces = rr["profile"]
        def wg(s):
            for (a, b, w0, w1, g0, g1) in pieces:
                if a <= s <= b:
                    f = 0.0 if b == a else (s - a) / (b - a)
                    return w0 + f * (w1 - w0), g0 + f * (g1 - g0), abs(w1 - w0) < 1e-9 and abs(g1 - g0) < 1e-9
            return None
        bps = sorted({p_[0] for p_ in pieces} | {p_[1] for p_ in pieces})
        avoid = [(a - 8, b + 8) for (a, b, _) in rr["cuts"]]
        for cx_ in asb["crossovers"]:
            if net in (cx_["bridge"], cx_["under"]) or (net == "FEED" and cx_["under"] == "FEED"):
                s_, dd = path.project((cx_["x"], cx_["y"]))
                if dd < 1.0:
                    avoid.append((s_ - 10, s_ + 10))
        Lr = rr["length_um"]
        samples = list(np.arange(3.0, Lr - 3.0, 150.0)) + [0.6, Lr - 0.6]
        for s in samples:
            if any(a <= s <= b for a, b in avoid) or any(abs(s - b) < 3.0 for b in bps[1:-1]):
                continue
            v = wg(s)
            if v is None or not v[2]:
                continue
            w, g, _ = v
            P, t = path.at(s)
            n = np.array([-t[1], t[0]])
            h = w / 2 + g + 4.0
            cut = rect_local(P, t, -0.005, 0.005, -h, h)
            cutR = db.Region(db.Polygon([db.Point(um(x), um(yy)) for x, yy in cut]))
            b = cutR.bbox().enlarged(um(1), um(1))
            loc = (db.Region(top.begin_shapes_rec_touching(li["NB"], b)) & db.Region(b)).merged() & cutR
            iv = []
            for q in loc.each():
                pts = np.array([[pt.x * dbu, pt.y * dbu] for pt in q.each_point_hull()])
                proj = (pts - P) @ n
                iv.append((proj.min(), proj.max()))
            iv.sort()
            xs_n += 1
            exp = [(-h, -(w / 2 + g)), (-w / 2, w / 2), (w / 2 + g, h)]
            good = len(iv) == 3 and all(abs(a - c) < DIE_RULES["XSEC_TOL"] + 0.006 and abs(b_ - d_) < DIE_RULES["XSEC_TOL"] + 0.006
                                        for (a, b_), (c, d_) in zip(iv, exp))
            if not good:
                xs_bad.append(dict(net=net, s=round(float(s), 2), xy=[round(float(P[0]), 2), round(float(P[1]), 2)],
                                   expected=[round(w, 3), round(g, 3)], measured=[[round(float(a), 3), round(float(b_), 3)] for a, b_ in iv]))
        # straps: verify each designed strap in the GDS (AL2 over the centre, SiNx under it, AL2 contacts on ground)
        found = []
        for kind_, slist in (("strap", rr["straps"]), ("bus", rr["bus"])):
            for s in slist:
                P, t = path.at(s)
                n = np.array([-t[1], t[0]])
                v = wg(min(max(s, 0.0), Lr))
                w, g = v[0], v[1]
                h = (w / 2 + g + (ST_W["land"] + ST_W["contact"] / 2 if w > 1.0 else ST_N["land"] + ST_N["contact"] / 2)) if kind_ == "strap" else 10.0
                pc = db.Box(um(P[0]) - 5, um(P[1]) - 5, um(P[0]) + 5, um(P[1]) + 5)
                has_al2 = not (A2 & db.Region(pc)).is_empty()
                has_di = not (DI & db.Region(pc)).is_empty()
                gnd_ok = True
                for sg in (-1, 1):
                    q = P + n * sg * h
                    qb = db.Box(um(q[0]) - 5, um(q[1]) - 5, um(q[0]) + 5, um(q[1]) + 5)
                    gnd_ok &= (not (A2 & db.Region(qb)).is_empty()) and (probe(q[0], q[1]) == gnd)
                if has_al2 and has_di and gnd_ok:
                    found.append(s)
                else:
                    br_bad.append(dict(net=net, s=round(float(s), 2), xy=[round(float(P[0]), 2), round(float(P[1]), 2)],
                                       al2=has_al2, diel=has_di, ground_both_sides=gnd_ok))
        found = sorted(found)
        ends = [0.0, Lr]
        cov = sorted(found + ends)
        gaps_ = [b - a for a, b in zip(cov[:-1], cov[1:])]
        mx = max(gaps_) if gaps_ else 0.0
        if mx > DIE_RULES["STRAP_MAX"] + 1e-6:
            i = int(np.argmax(gaps_))
            br_bad.append(dict(net=net, max_gap_um=round(mx, 1), between=[round(cov[i], 1), round(cov[i + 1], 1)]))
        nb_ = 0
        for (a, b, R_) in rr["arcs"]:
            nb_ += 1
            mid = (a + b) / 2
            if not any(abs(f - mid) <= (b - a) / 2 + DIE_RULES["BEND_TOL"] for f in found):
                bend_bad.append(dict(net=net, arc_s=[round(a, 1), round(b, 1)], radius=R_))
        strap_rows[net] = dict(straps_verified=len(found), max_spacing_um=round(mx, 1), bends=nb_)
    add("CPW.XSEC", len(xs_bad), "CPW cross-section (centre width and both gaps) equals the as-built profile within 10 nm "
        "(10/6 away from the block, port geometry at the block)", xs_bad[:max_examples])
    add("CPW.STRAP", len(br_bad), "ground strap present (AL2 on SiNx, AL2 contacts on ground both sides) and spaced <= 300 um "
        "along every CPW", br_bad[:max_examples])
    add("CPW.BEND", len(bend_bad), "a ground strap within 25 um of every bend", bend_bad[:max_examples])
    res["cpw"] = dict(cross_sections_checked=xs_n, straps=strap_rows)
    res["crossovers"] = dict(count=len(asb["crossovers"]), list=asb["crossovers"],
                             note="signal-signal crossings are insulated crossovers (AL2 bridge on SiNx); the pin map of "
                                  "die_pads.json is not planar with respect to the frozen block port order (see module "
                                  "docstring): 33 crossings is the minimum")
    res["resonators"] = asb["resonators"]
    res["violations_total"] = int(sum(c["violations"] for c in res["checks"].values()))
    res["summary"] = dict(
        violations_total=res["violations_total"], per_check={k: v["violations"] for k, v in res["checks"].items()},
        pads_match_spec=res["pads_match_spec"], connectivity_ok=res["connectivity"]["all_ok"],
        signal_nets=sum(1 for k in conn if k not in ("GND", "TEST_STRUCTURES_isolated")),
        crossovers=len(asb["crossovers"]), holes=res["holes"]["count"],
        resonators={k: v["f_model_GHz"] for k, v in asb["resonators"].items()},
        block_internal_violations=int(sum(res["block_internal"].values())),
        block_internal_note="width/space violations deep inside the frozen row block are the block's own (hardware/drc.py "
                            "owns them); they are reported here but not counted in violations_total",
        check_s=round(time.time() - t0, 1))
    os.makedirs(os.path.dirname(os.path.abspath(report_path)), exist_ok=True)
    json.dump(res, open(report_path, "w"), indent=1, default=float)
    return res


if __name__ == "__main__":
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    c = lambda f: os.path.join(root, "circuits", f)
    r = build_die(c("qbfx2_layout.gds"), c("block_ports.json"), c("die_pads.json"), c("qbfx2_die.gds"),
                  previews="--no-previews" not in sys.argv)
    print(json.dumps(r, indent=1))
    rep = check_die(c("qbfx2_die.gds"), c("die_pads.json"), c("die_drc_report.json"))
    print(json.dumps(rep["summary"], indent=1))
