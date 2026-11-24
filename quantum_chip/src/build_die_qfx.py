"""QFX-1: quantum-fluxon processor die (KLayout, positive layers).

  QF1, QF2   quantum fluxon qubits: annular parallel arrays of 24 small Al/AlOx/Al junctions (rungs) between
             a granular-Al inner rail (cell superinductors) and the Nb ground-plane rim. Two weakened rungs
             (A, B) are the wells; the rung between them is a dc SQUID (tunnelling barrier).
  KICK line  heavy-fluxon ballistic line: low-inductance Nb CPW (20 um strip, 1 um gaps) with a 12 um^2 Al
             junction from the strip edge to ground every 10 um; launched by a DC/SFQ converter, read by an
             SFQ/DC converter. Two 1.2 mm sections feed hairpin flux transformers (flared ends = tapered
             coupling) that land on each qubit's barrier link: a passing fluxon applies the "fluxon-kick" gate.
  BUS        galvanic coupler between the two qubits' barrier links (ZZ).
  Readout    lambda/4 resonators (7.0 / 7.4 GHz) on a common feedline; fast drive and dc flux lines.
Crossings are bridged with Al airbridges. Outputs: out/quantum_die.gds, out/die_ports.json, out/die_cells.json
Documentation layer 63/0 holds each route's centre-line polygon (used by validate.py for continuity).
"""
import json
import math
import os
import sys

import klayout.db as db

sys.path.insert(0, os.path.dirname(__file__))
from design_params import DIE, LAUNCHER, QFX, QFX_STACK, QFX_LAUNCHER_NETS

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
S = DIE["size_um"]
DBU = 0.001
ly = db.Layout()
ly.dbu = DBU
top = ly.create_cell("QFX1")
LI = {name: ly.layer(g[0], g[1], name) for name, g, _, _ in QFX_STACK}
LROUTE = ly.layer(63, 0, "ROUTES")
LSHORT = ly.layer(64, 0, "SHORTS")
I = lambda v: int(round(v / DBU))
CELLS, ROUTES, BRIDGES = {}, [], []

sig = db.Region()        # BASE conductors that are not ground
keep = db.Region()       # extra ground-plane openings
shorts = db.Region()     # BASE patches that tie a line end to ground
layers = {k: db.Region() for k in LI}


def P(x, y):
    return db.Point(I(x), I(y))


def poly(pts):
    return db.Region(db.Polygon([P(x, y) for x, y in pts]))


def box(x0, y0, x1, y1):
    return db.Region(db.Box(I(min(x0, x1)), I(min(y0, y1)), I(max(x0, x1)), I(max(y0, y1))))


def circle(x, y, r, n=64):
    return poly([(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)])


def path(pts, w):
    return db.Region(db.DPath([db.DPoint(x / DBU, y / DBU) for x, y in pts], w / DBU, 0, 0).to_itype(1).polygon())


def rounded(pts, r):
    out = [pts[0]]
    for a, b, c in zip(pts[:-2], pts[1:-1], pts[2:]):
        v1, v2 = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        u1, u2 = (v1[0] / l1, v1[1] / l1), (v2[0] / l2, v2[1] / l2)
        ang = math.acos(max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1])))
        if ang < 1e-6:
            out.append(b)
            continue
        rr = min(r, 0.45 * l1, 0.45 * l2)
        d = rr * math.tan(ang / 2)
        p1 = (b[0] - u1[0] * d, b[1] - u1[1] * d)
        turn = 1 if u1[0] * u2[1] - u1[1] * u2[0] > 0 else -1
        cx, cy = p1[0] - u1[1] * rr * turn, p1[1] + u1[0] * rr * turn
        a0 = math.atan2(p1[1] - cy, p1[0] - cx)
        n = max(4, int(ang / (math.pi / 24)))
        out += [(cx + rr * math.cos(a0 + turn * ang * i / n), cy + rr * math.sin(a0 + turn * ang * i / n))
                for i in range(n + 1)]
    out.append(pts[-1])
    return out


def radial_short(pt, w):
    """patch from a line end just inside a qubit hole across the rim edge (documented on SHORTS)"""
    for q, c in CELLS.items():
        if c.get("kind") == "quantum fluxon ring":
            cx, cy = c["center"]
            if abs(math.hypot(pt[0] - cx, pt[1] - cy) - (R_HOLE - 1.0)) < 0.3:
                a = math.atan2(pt[1] - cy, pt[0] - cx)
                ca, sa = math.cos(a), math.sin(a)
                return poly([(cx + r * ca - sa * s_ * w / 2, cy + r * sa + ca * s_ * w / 2)
                             for r, s_ in ((R_HOLE - 1.6, -1), (R_HOLE + 2.0, -1), (R_HOLE + 2.0, 1), (R_HOLE - 1.6, 1))])
    x, y = pt
    return box(x - w / 2, y - w / 2, x + w / 2, y + w / 2)


def route(name, pts, w=10.0, gap=6.0, r=60.0, bridge=False, net=None, end_short=None):
    """CPW-like BASE line: centre conductor w, ground clearance gap. bridge=True: this line hops over any
    route it crosses using an airbridge. end_short=(x,y): extra patch tying the end to the ground plane."""
    pr = rounded(pts, r) if r else list(pts)
    ROUTES.append(dict(name=name, net=net, pts=pr, w=w, gap=gap, bridge=bridge))
    if end_short:
        shorts.insert(radial_short(end_short, w))
    return pr


# ------------------------------------------------------------------ pads (same positions as the carrier bond pads)
n_side = {"N": 6, "E": 2, "W": 2}
order = []
pitch = LAUNCHER["pitch"]
for side in ("N", "E", "W"):
    k = n_side[side]
    for i in range(k):
        off = (i - (k - 1) / 2) * pitch
        order.append((side, S / 2 + off) if side == "N" else (side, S / 2 - off) if side == "E" else (side, S / 2 + off))
ports = []
for pid, (side, t) in enumerate(order, start=1):
    net = QFX_LAUNCHER_NETS[pid]
    pad, taper, ind = LAUNCHER["width"], LAUNCHER["width"], LAUNCHER["indent"]
    if side == "N":
        c, port, u = (t, S - ind + taper + pad / 2), (t, S - ind), (0, 1)
    elif side == "E":
        c, port, u = (S - ind + taper + pad / 2, t), (S - ind, t), (1, 0)
    else:
        c, port, u = (ind - taper - pad / 2, t), (ind, t), (-1, 0)
    sig.insert(box(c[0] - pad / 2, c[1] - pad / 2, c[0] + pad / 2, c[1] + pad / 2))
    e = (c[0] - u[0] * pad / 2, c[1] - u[1] * pad / 2)
    vx, vy = -u[1], u[0]
    sig.insert(poly([(e[0] + vx * pad / 2, e[1] + vy * pad / 2), (e[0] - vx * pad / 2, e[1] - vy * pad / 2),
                     (port[0] - vx * 5, port[1] - vy * 5), (port[0] + vx * 5, port[1] + vy * 5)]))
    xs_ = [c[0] - pad / 2, c[0] + pad / 2, port[0]]
    ys_ = [c[1] - pad / 2, c[1] + pad / 2, port[1]]
    keep.insert(box(min(xs_) - 80, min(ys_) - (80 if u[1] != 1 else 0), max(xs_) + 80, max(ys_) + (80 if u[1] != -1 else 0))
                if u[1] else box(min(xs_) - (80 if u[0] != 1 else 0), min(ys_) - 80, max(xs_) + (80 if u[0] != -1 else 0),
                                 max(ys_) + 80))
    ports.append(dict(net=net, kqc_port_id=pid, side=side, port_um=list(port), outward=list(u),
                      pad_center_um=[round(c[0], 3), round(c[1], 3)], pad_size_um=[pad, pad]))
PT = {p["net"]: tuple(p["port_um"]) for p in ports}

# ------------------------------------------------------------------ quantum fluxon rings
NR = QFX["ring_cells"]
MID = NR // 2
A_, B_ = MID - 1, MID + 1
R_HOLE, R_RAIL, RAIL_W = 50.0, 37.5, 1.2
JJ_A = QFX["ring_jj_area_um2"]                # um^2 (80 nA at 1.665 uA/um^2, 2.4 fF at 50 fF/um^2)
LEAD_W, OVL = 0.20, 0.24                       # AL1 lead width, AL1/AL2 overlap length -> 0.048 um^2
WEAK_W = WEAK_OVL = math.sqrt((1 - QFX["well_weak"]) * JJ_A)   # pinning junctions ~120 x 120 nm (not a 60 nm lead)
KJ = math.sqrt(QFX["kick_jj_area_um2"])        # kick-line and converter junctions: KJ x KJ overlap


def ring(q, cx, cy, mid_deg, s):
    """s = +1: rung index increases counter-clockwise; s = -1 mirrored."""
    keep.insert(circle(cx, cy, R_HOLE, 96))
    rail = circle(cx, cy, R_RAIL + RAIL_W / 2, 128) - circle(cx, cy, R_RAIL - RAIL_W / 2, 128)
    layers["GRAL"].insert(rail)
    jj = []

    def rung(ang, width, lateral=0.0, ovl=OVL):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        ox, oy = -sa * lateral, ca * lateral
        r0, r1 = R_RAIL - 0.4, R_HOLE - 0.8          # AL1 lead from the rail to just inside the rim
        pts = lambda ra, rb, wd: [(cx + ox + ra * ca - sa * wd / 2, cy + oy + ra * sa + ca * wd / 2),
                                  (cx + ox + rb * ca - sa * wd / 2, cy + oy + rb * sa + ca * wd / 2),
                                  (cx + ox + rb * ca + sa * wd / 2, cy + oy + rb * sa - ca * wd / 2),
                                  (cx + ox + ra * ca + sa * wd / 2, cy + oy + ra * sa - ca * wd / 2)]
        layers["AL1"].insert(poly(pts(r0, r1, width)))
        layers["AL2"].insert(poly(pts(r1 - ovl, R_HOLE + 1.5, 0.8)))     # top electrode onto the Nb rim
        jj.append(dict(angle=ang, area_um2=round(width * ovl, 4), lateral=lateral))

    for n in range(NR):
        ang = mid_deg + s * (n - MID) * 360.0 / NR
        if n == MID:                                                     # barrier dc SQUID
            wsq = QFX["barrier_EJmax_ratio"] / 2 * LEAD_W
            for lat in (-1.6, 1.6):
                rung(ang, wsq, lat)
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            layers["AL1"].insert(poly([(cx + (R_RAIL - 0.4) * ca - sa * 1.9, cy + (R_RAIL - 0.4) * sa + ca * 1.9),
                                       (cx + (R_RAIL + 0.6) * ca - sa * 1.9, cy + (R_RAIL + 0.6) * sa + ca * 1.9),
                                       (cx + (R_RAIL + 0.6) * ca + sa * 1.9, cy + (R_RAIL + 0.6) * sa - ca * 1.9),
                                       (cx + (R_RAIL - 0.4) * ca + sa * 1.9, cy + (R_RAIL - 0.4) * sa - ca * 1.9)]))
        elif n in (A_, B_):
            rung(ang, WEAK_W, ovl=WEAK_OVL)
        else:
            rung(ang, LEAD_W)
    rim = lambda deg: (cx + (R_HOLE - 1.0) * math.cos(math.radians(deg)), cy + (R_HOLE - 1.0) * math.sin(math.radians(deg)))
    link = lambda n0, frac=0.5: mid_deg + s * (n0 + frac - MID) * 360.0 / NR   # angle inside link n0 -> n0+1
    out = lambda deg, r=90.0: (cx + r * math.cos(math.radians(deg)), cy + r * math.sin(math.radians(deg)))
    CELLS[q] = dict(kind="quantum fluxon ring", center=(cx, cy), junctions=jj, rungs=NR, mid_deg=mid_deg, sense=s,
                    hole_radius_um=R_HOLE, rail_radius_um=R_RAIL)
    return rim, link, out


rim1, link1, out1 = ring("QF1", 4800.0, 5200.0, 0.0, +1)
rim2, link2, out2 = ring("QF2", 5200.0, 5200.0, 180.0, -1)

# ------------------------------------------------------------------ kick line (heavy ballistic fluxons)
KY, KX0, KX1, KTOP = 6000.0, 3200.0, 6800.0, 8180.0
kick_pts = rounded([(KX0, KTOP), (KX0, KY), (KX1, KY), (KX1, KTOP)], 150.0)
KW, KG = QFX["kick_strip_w_um"], QFX["kick_gap_um"]
ROUTES.append(dict(name="KICK", net="kick", pts=kick_pts, w=KW, gap=KG, bridge=False))


def kick_junctions(pts, pitch_um, start=10.0):
    seg = list(zip(pts[:-1], pts[1:]))
    acc, nxt, side, n = 0.0, start, 1, 0
    for a, b in seg:
        L = math.dist(a, b)
        while nxt <= acc + L:
            t = (nxt - acc) / L
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            nx, ny = -uy * side, ux * side
            q = lambda r0, r1, wd: [(x + nx * r0 - ux * wd / 2, y + ny * r0 - uy * wd / 2),
                                    (x + nx * r1 - ux * wd / 2, y + ny * r1 - uy * wd / 2),
                                    (x + nx * r1 + ux * wd / 2, y + ny * r1 + uy * wd / 2),
                                    (x + nx * r0 + ux * wd / 2, y + ny * r0 + uy * wd / 2)]
            h_ = KW / 2                                         # strip edge
            layers["AL1"].insert(poly(q(h_ - KJ - 1.5, h_ + 0.5, KJ)))   # on the strip, wraps its edge (0.5 um into the gap)
            layers["AL2"].insert(poly(q(h_ + 0.5 - KJ, h_ + KG + 2.0, KJ)))  # over the gap onto ground; overlap KJ x KJ
            side, n, nxt = -side, n + 1, nxt + pitch_um
        acc += L
    return n


n_kick = kick_junctions(kick_pts, QFX["kick_pitch_um"])
L_kick = sum(math.dist(a, b) for a, b in zip(kick_pts[:-1], kick_pts[1:]))
SEC = QFX["kick_section_cells"] * QFX["kick_pitch_um"]
TS1 = (3500.0, 3500.0 + SEC)
TS2 = (6500.0 - SEC, 6500.0)
CELLS["KICK"] = dict(kind="heavy-fluxon ballistic line", junctions=n_kick, length_um=round(L_kick, 1),
                     junction_area_um2=round(KJ * KJ, 2), sections={"QF1": TS1, "QF2": TS2},
                     strip_w_um=KW, gap_um=KG, pitch_um=QFX["kick_pitch_um"],
                     taper_um=QFX["kick_taper_cells"] * QFX["kick_pitch_um"])

# converters at the line ends (bias resistors and shunts in Cu, quasiparticle traps next to them)


def converter(name, cx, cy, kind, tap=+1):
    keep.insert(box(cx - 90, cy - 60, cx + 90, cy + 60))                                         # clearance
    sig.insert(box(cx - 40, cy - 30, cx + 40, cy + 30) - box(cx - 32, cy - 22, cx + 32, cy + 22))   # storage loop
    shorts.insert(box(cx - 6 * tap - 4, cy - 60, cx - 6 * tap + 4, cy - 30))   # inductive return to ground (bottom)
    for dx in (-24, 24):
        layers["AL1"].insert(box(cx + dx - KJ / 2, cy - 30, cx + dx + KJ / 2, cy - 24))
        layers["AL2"].insert(box(cx + dx - KJ / 2, cy - 30 + KJ, cx + dx + KJ / 2, cy - 40))   # KJ x KJ junction
        layers["RES"].insert(box(cx + dx - 3, cy - 52, cx + dx + 3, cy - 42))   # shunt resistor
    layers["RES"].insert(box(cx + tap * 44, cy - 6, cx + tap * 66, cy + 6))   # bias resistor (overlaps both ends)
    for k in range(4):                                                         # Cu quasiparticle traps on GP
        layers["RES"].insert(box(cx - 120 + 60 * k, cy + 70, cx - 90 + 60 * k, cy + 100))
    sig.insert(box(cx + tap * 40, cy - 3, cx + tap * 46, cy + 3))            # loop -> resistor contact
    CELLS[name] = dict(kind=kind, center=(cx, cy), bias_tap=(cx + tap * 64, cy))


converter("DCSFQ_IN", KX0, KTOP + 60, "DC/SFQ launcher", tap=-1)
converter("SFQDC_OUT", KX1, KTOP + 60, "SFQ/DC receiver", tap=+1)
# kick strip into the converters
ROUTES.append(dict(name="KICK_IN_STUB", net="kick", pts=[(KX0, KTOP), (KX0, KTOP + 30)], w=KW, gap=KG, bridge=False))
ROUTES.append(dict(name="KICK_OUT_STUB", net="kick", pts=[(KX1, KTOP), (KX1, KTOP + 30)], w=KW, gap=KG, bridge=False))

# ------------------------------------------------------------------ flux transformers (kick section -> qubit link)


def transformer(name, xs, land_a, land_b, far_end_left, out_a, out_b):
    y1, y2 = KY - 26.0, KY - 34.0                  # hairpin under the kick strip
    xa, xb = xs
    near, far = (xb, xa) if far_end_left else (xa, xb)
    sg = 1.0 if near > far else -1.0
    T, D = QFX["kick_taper_cells"] * QFX["kick_pitch_um"], 60.0   # flare: 60 um away from the strip over 200 um
    # hairpin along the section, flared at both ends (coupling ramps over T), + descending pair to the rim
    oa, ob = out_a, out_b
    pr = [land_a, oa, (near, y2 - D), (near - sg * T, y2), (far + sg * T, y2), (far, y2 - D),
          (far, y1 - D), (far + sg * T, y1), (near - sg * T, y1), (near, y1 - D), ob, land_b]
    route(name, pr, w=3.0, gap=2.5, r=0, end_short=land_b, net=name)
    shorts.insert(radial_short(land_a, 3.0))
    CELLS[name] = dict(kind="flux transformer", section=xs, lands=(land_a, land_b))


transformer("XFMR1", TS1, rim1(link1(MID, 0.2)), rim1(link1(MID, 0.8)), True, out1(link1(MID, 0.2)), out1(link1(MID, 0.8)))
transformer("XFMR2", TS2, rim2(link2(MID, 0.2)), rim2(link2(MID, 0.8)), False, out2(link2(MID, 0.2)), out2(link2(MID, 0.8)))

# ------------------------------------------------------------------ ZZ bus between the barrier links (A side)
b1, b2 = rim1(link1(A_, 0.5)), rim2(link2(A_, 0.5))
route("BUS", [b1, out1(link1(A_, 0.5)), out2(link2(A_, 0.5)), b2], w=2.0, gap=2.0, r=0, end_short=b2, net="BUS")
shorts.insert(radial_short(b1, 2.0))
CELLS["BUS"] = dict(kind="galvanic ZZ coupler", lands=(b1, b2))

# ------------------------------------------------------------------ feedline, resonators, drive and flux lines
FY = 3000.0
route("FEED", [PT["FEED_IN"], (1500, PT["FEED_IN"][1]), (1500, FY), (8500, FY), (8500, PT["FEED_OUT"][1]),
               PT["FEED_OUT"]], net="FEED")


def resonator(name, x0, xr, deg_out, land, f_ghz, mirror):
    """lambda/4: capacitive elbow at the feedline, meander centred at x0, riser at xr, radial approach."""
    lam4 = 299792458 / (4 * f_ghz * 1e9 * math.sqrt((11.45 + 1) / 2)) * 1e6
    y0 = FY + 20.0
    head = [(x0 - 150 * mirror, y0), (x0, y0)]
    tail = [(x0, 4950.0), (xr, 4950.0), (xr, deg_out[1]), deg_out, land]
    best = None
    for nmean in range(0, 40):
        pts = list(head)
        y, d = y0, 1
        for _ in range(nmean):
            pts += [(x0 + 120 * d, y), (x0 + 120 * d, y + 100), (x0, y + 100)]
            y += 100
            d = -d
        if y > 4700:
            break
        trial = pts + tail
        Lr = sum(math.dist(a, b) for a, b in zip(rounded(trial, 20.0)[:-1], rounded(trial, 20.0)[1:]))
        if Lr <= lam4:
            best = (pts, Lr)
    pts, Lr = best
    deficit = lam4 - Lr                     # trim with a side jog on the meander-to-riser leg
    jog = deficit / 2
    ymid = 4950.0 - 60
    trial_tail = [(x0, ymid - 15), (x0 - 140 * mirror - 0, ymid - 15)] if False else None
    tail = [(x0, ymid - 20), (x0 - mirror * jog, ymid - 20), (x0 - mirror * jog, ymid + 20), (x0, ymid + 20)] + tail
    for _ in range(40):
        trial = pts + tail
        Lr = sum(math.dist(a, b) for a, b in zip(rounded(trial, 20.0)[:-1], rounded(trial, 20.0)[1:]))
        if abs(lam4 - Lr) < 0.3:
            break
        jog += (lam4 - Lr) / 2
        tail[1] = (x0 - mirror * jog, ymid - 20)
        tail[2] = (x0 - mirror * jog, ymid + 20)
    pr = route(name, pts + tail, w=10.0, gap=6.0, r=20.0, end_short=land, net=name, bridge=True)
    CELLS[name] = dict(kind="lambda/4 readout resonator", f_design_GHz=f_ghz, length_um=round(
        sum(math.dist(a, b) for a, b in zip(pr[:-1], pr[1:])), 1), target_length_um=round(lam4, 1))


resonator("RES1", 4300.0, 4950.0, out1(link1(B_ + 1, 0.5)), rim1(link1(B_ + 1, 0.5)), 7.0, -1)
resonator("RES2", 5700.0, 5050.0, out2(link2(B_ + 1, 0.5)), rim2(link2(B_ + 1, 0.5)), 7.4, +1)

d1, o1 = rim1(link1(A_ - 1, 0.5)), out1(link1(A_ - 1, 0.5))
route("QF1_DRIVE", [PT["QF1_DRIVE"], (1500, PT["QF1_DRIVE"][1]), (1500, 5085), (o1[0], 5085), o1, d1], w=6.0, gap=4.0,
      r=0, bridge=True, end_short=d1, net="QF1_DRIVE")
d2, o2 = rim2(link2(A_ - 1, 0.5)), out2(link2(A_ - 1, 0.5))
route("QF2_DRIVE", [PT["QF2_DRIVE"], (8500, PT["QF2_DRIVE"][1]), (8500, 5085), (o2[0], 5085), o2, d2], w=6.0, gap=4.0,
      r=0, bridge=True, end_short=d2, net="QF2_DRIVE")
f1, of1 = rim1(link1(B_ + 3, 0.5)), out1(link1(B_ + 3, 0.5))
route("QF1_FLUX", [PT["QF1_FLUX"], (4400, 5700), (of1[0], 5700), of1, f1], w=6.0, gap=4.0, r=0, bridge=True,
      end_short=f1, net="QF1_FLUX")
f2, of2 = rim2(link2(B_ + 3, 0.5)), out2(link2(B_ + 3, 0.5))
route("QF2_FLUX", [PT["QF2_FLUX"], (5600, 5700), (of2[0], 5700), of2, f2], w=6.0, gap=4.0, r=0, bridge=True,
      end_short=f2, net="QF2_FLUX")
# converter I/O and bias
route("KICK_TRIG", [PT["KICK_TRIG"], (KX0, KTOP + 82)], net="KICK_TRIG")
route("KICK_OUT", [PT["KICK_OUT"], (KX1, KTOP + 82)], net="KICK_OUT")
route("VB_IN", [PT["VB_IN"], (2000, KTOP + 60), (KX0 - 64, KTOP + 60)], w=6.0, gap=6.0, r=0, net="VB_IN")
route("VB_OUT", [PT["VB_OUT"], (8000, KTOP + 60), (KX1 + 64, KTOP + 60)], w=6.0, gap=6.0, r=0, net="VB_OUT")
# converter input transformers / outputs connect to the loops
sig.insert(box(KX0 - 12, KTOP + 74, KX0 + 12, KTOP + 92))
sig.insert(box(KX1 - 12, KTOP + 74, KX1 + 12, KTOP + 92))

# ------------------------------------------------------------------ crossings -> airbridges


def seg_intersections(p, q):
    hits = []
    for a, b in zip(p[:-1], p[1:]):
        for c, d in zip(q[:-1], q[1:]):
            den = (b[0] - a[0]) * (d[1] - c[1]) - (b[1] - a[1]) * (d[0] - c[0])
            if abs(den) < 1e-12:
                continue
            t = ((c[0] - a[0]) * (d[1] - c[1]) - (c[1] - a[1]) * (d[0] - c[0])) / den
            u = ((c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])) / den
            if 0 < t < 1 and 0 < u < 1:
                hits.append(((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), (b[0] - a[0], b[1] - a[1])))
    return hits


cuts = {r["name"]: db.Region() for r in ROUTES}
for r in ROUTES:
    if not r["bridge"]:
        continue
    hits = []
    for o in ROUTES:
        if o is r:
            continue
        for (x, y), (dx, dy) in seg_intersections(r["pts"], o["pts"]):
            L = math.hypot(dx, dy)
            hits.append(dict(x=x, y=y, ux=dx / L, uy=dy / L, half=o["w"] / 2 + o["gap"] + 6.0, over=o["name"]))
    # merge crossings closer than 40 um into one bridge
    hits.sort(key=lambda h: (h["x"], h["y"]))
    groups = []
    for hh in hits:
        if groups and math.dist((hh["x"], hh["y"]), (groups[-1][-1]["x"], groups[-1][-1]["y"])) < 40:
            groups[-1].append(hh)
        else:
            groups.append([hh])
    for g_ in groups:
        ux, uy = g_[0]["ux"], g_[0]["uy"]
        proj = [hh["x"] * ux + hh["y"] * uy for hh in g_]
        lo = min(p - hh["half"] for p, hh in zip(proj, g_))
        hi = max(p + hh["half"] for p, hh in zip(proj, g_))
        cx_, cy_ = g_[0]["x"], g_[0]["y"]
        p0 = cx_ * ux + cy_ * uy
        a_ = (cx_ + ux * (lo - p0), cy_ + uy * (lo - p0))
        b_ = (cx_ + ux * (hi - p0), cy_ + uy * (hi - p0))
        cuts[r["name"]].insert(path([a_, b_], r["w"] + 2 * r["gap"] + 1))
        for (fx, fy), sgn in ((a_, -1), (b_, 1)):
            fx, fy = fx + sgn * ux * 4, fy + sgn * uy * 4
            layers["ABP"].insert(box(fx - 4, fy - 4, fx + 4, fy + 4))
        layers["ABS"].insert(path([(a_[0] - ux * 7, a_[1] - uy * 7), (b_[0] + ux * 7, b_[1] + uy * 7)], max(6.0, r["w"])))
        BRIDGES.append(dict(route=r["name"], over=sorted({hh["over"] for hh in g_}), at=(round(cx_, 2), round(cy_, 2)),
                            span_um=round(hi - lo + 14, 1)))

# ------------------------------------------------------------------ assemble BASE
for r in ROUTES:
    line = path(r["pts"], r["w"])
    clear = path(r["pts"], r["w"] + 2 * r["gap"])
    if cuts[r["name"]].count():
        line -= cuts[r["name"]].sized(I(-0.0))
        # keep the airbridge feet as metal on the line
        line += (layers["ABP"] & path(r["pts"], r["w"] + 2 * r["gap"]))
        # the bridged line keeps its ground clearance everywhere, so its cut ends stay isolated
    sig.insert(line)
    keep.insert(clear)
    top.shapes(LROUTE).insert(path(r["pts"], max(0.5, r["w"] * 0.25)))
chip = box(20, 20, S - 20, S - 20)
gp = chip - keep
# labels are etched into the ground plane only (never into a signal line)
gen = db.TextGenerator.default_generator()
for txt, x, y, hgt in (("QFX-1  QUANTUM FLUXON", 400, 1700, 200), ("EE143", 8300, 1700, 200),
                       ("AL-ALOX-AL + GRAL + NB", 400, 450, 140)):
    t = gen.text(txt, DBU, hgt / (gen.text("A", DBU, 1).bbox().height() * DBU))
    t.move(I(x), I(y))
    gp -= t
base = (gp + sig + shorts).merged() & chip
layers["BASE"] = base
for name, reg in layers.items():
    top.shapes(LI[name]).insert(reg.merged())
top.shapes(LSHORT).insert(shorts.merged())

os.makedirs(OUT, exist_ok=True)
ly.write(os.path.join(OUT, "quantum_die.gds"))
jj = (layers["AL1"] & layers["AL2"]).merged()
json.dump(dict(ports=ports, refpoints={}), open(os.path.join(OUT, "die_ports.json"), "w"), indent=1)
def before_end(pts, dist=5.0):
    (x1, y1), (x0, y0) = pts[-1], pts[-2]
    L = math.hypot(x1 - x0, y1 - y0)
    return (x1 - (x1 - x0) / L * min(dist, 0.9 * L), y1 - (y1 - y0) / L * min(dist, 0.9 * L))


json.dump(dict(design="QFX-1", cells=CELLS, routes=[dict(name=r["name"], net=r["net"], w=r["w"], gap=r["gap"],
                                                           start=r["pts"][0], end=r["pts"][-1], pre_end=before_end(r["pts"]))
                                                      for r in ROUTES],
               bridges=BRIDGES, total_jj=jj.count(),
               stack=[dict(layer=n, gds=list(g), material=m, thickness_nm=t) for n, g, m, t in QFX_STACK]),
          open(os.path.join(OUT, "die_cells.json"), "w"), indent=1, default=list)
print("QFX-1:", jj.count(), "junction overlaps,", len(BRIDGES), "airbridges, kick junctions", n_kick)
for b in BRIDGES:
    print("  bridge", b)
