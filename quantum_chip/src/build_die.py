"""Reversible Fluxon Logic (RFL) test die, drawn with KLayout (positive Nb layers, SFQ-style process).

Circuit (see README):
  TRIG_A -> DC/SFQ_A -> LJJ_A -> controlled barrier CB (flux CTRL_CB) -> rotary element RE input I0
  TRIG_B -> DC/SFQ_B -> LJJ_B ------------------------------------------> RE input I1
  RE output O0 -> LJJ -> SFQ/DC_0 -> OUT_0          RE output O1 -> LJJ -> SFQ/DC_1 -> OUT_1
  RE state set/reset flux: CTRL_RE
  TEST_IN -> DC/SFQ_T -> 18 mm ballistic LJJ racetrack -> SFQ/DC_T -> TEST_OUT   (fluxon time-of-flight)
  VB_W / VB_E: DC bias for the converters only. The ballistic lines and gates are unpowered.

Outputs: out/quantum_die.gds (cell RFL_RE1), out/die_ports.json, out/die_cells.json
"""
import json
import math
import os
import sys

import klayout.db as db

sys.path.insert(0, os.path.dirname(__file__))
from design_params import DIE, LAUNCHER, LAUNCHER_NETS, RFL, RFL_STACK

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
S = DIE["size_um"]
ly = db.Layout()
ly.dbu = 0.001
top = ly.create_cell("RFL_RE1")
LI = {name: ly.layer(g[0], g[1], name) for name, g, _, _ in RFL_STACK}
CELLS = {}


def P(x, y):
    return db.DPoint(x, y)


def add(layer, shape):
    top.shapes(LI[layer]).insert(shape)


def box(layer, x0, y0, x1, y1):
    add(layer, db.DBox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))


def circle(layer, x, y, r, n=32):
    add(layer, db.DPolygon([P(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]))


def rounded(pts, r):
    """polyline with circular fillets of radius r at every interior corner"""
    out = [pts[0]]
    for a, b, c in zip(pts[:-2], pts[1:-1], pts[2:]):
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
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
        for i in range(n + 1):
            t = a0 + turn * ang * i / n
            out.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    out.append(pts[-1])
    return out


def path(layer, pts, w):
    add(layer, db.DPath([P(*p) for p in pts], w).polygon())


def plen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:]))


def ljj(name, pts, radius=120.0):
    """Discrete long Josephson junction: 10 um wide M1 strip over GP, one unshunted JJ per cell to ground
    (JJ on the strip, counter-electrode strapped on M2 to a stacked via into GP)."""
    pr = rounded(pts, radius)
    w = 10.0
    path("M1", pr, w)
    pitch = RFL["cell_pitch_um"]
    r_jj = math.sqrt(RFL["jj_area_um2"] / math.pi)
    L = plen(pr)
    n = int(L // pitch)
    seg = list(zip(pr[:-1], pr[1:]))
    acc, k, s_next = 0.0, 0, pitch / 2
    side, skipped = 1, 0
    for a, b in seg:
        l = math.dist(a, b)
        while s_next <= acc + l and k < n:
            t = (s_next - acc) / l
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            ux, uy = (b[0] - a[0]) / l, (b[1] - a[1]) / l
            nx, ny = -uy * side, ux * side
            sx, sy = x + nx * 9.5, y + ny * 9.5
            if near_m2(x, y, 14) or near_m2(sx, sy, 6):   # no grounded strap under a crossing M2 line
                skipped += 1
                k += 1
                s_next += pitch
                continue
            circle("JJ", x, y, r_jj, 16)
            box("I1", x - 0.6, y - 0.6, x + 0.6, y + 0.6)
            sx, sy = x + nx * 9.5, y + ny * 9.5
            path("M2", [(x, y), (sx, sy)], 2.5)
            box("VIA", sx - 1.6, sy - 1.6, sx + 1.6, sy + 1.6)
            side = -side
            k += 1
            s_next += pitch
        acc += l
    CELLS[name] = dict(kind="LJJ", cells=n - skipped, skipped_under_crossings=skipped, length_um=round(L, 1),
                       start=pr[0], end=pr[-1])
    return n - skipped


M2_LINES = []


def microstrip(pts, w=10.0, layer="M2", r=60.0):
    pr = rounded(pts, r) if r else list(pts)
    path(layer, pr, w)
    M2_LINES.append((pr, w))


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def near_m2(x, y, clr):
    return any(seg_dist((x, y), a, b) < w / 2 + clr for pts, w in M2_LINES for a, b in zip(pts[:-1], pts[1:]))


def gnd_via(x, y, s=4.0):
    box("VIA", x - s / 2, y - s / 2, x + s / 2, y + s / 2)


def jj(x, y, area, shunt=None):
    r = math.sqrt(area / math.pi)
    circle("JJ", x, y, r, 24)
    box("I1", x - r * 0.6, y - r * 0.6, x + r * 0.6, y + r * 0.6)
    if shunt:  # (dx, dy) direction of the shunt resistor to ground
        dx, dy = shunt
        box("R", x + dx * 4 - 3, y + dy * 4 - 3, x + dx * 18 + 3, y + dy * 18 + 3)
        gnd_via(x + dx * 22, y + dy * 22)


def dcsfq(name, cx, cy, bias_side):
    """DC/SFQ converter (2 JJs, shunted). Input from +y (north) or -x (west); fluxon out on M1 at south/east."""
    path("M1", [(cx - 30, cy + 20), (cx + 30, cy + 20), (cx + 30, cy - 20), (cx - 30, cy - 20), (cx - 30, cy + 20)], 6)
    jj(cx - 30, cy - 20, 1.6, (-1, 0))
    jj(cx + 30, cy - 20, 1.2, (1, 0))
    gnd_via(cx - 30, cy + 34)
    path("M1", [(cx - 30, cy + 20), (cx - 30, cy + 34)], 6)
    box("M2", cx - 22, cy + 10, cx + 22, cy + 30)          # input transformer primary over the loop
    bx = cx + (60 if bias_side == "E" else -60 if bias_side == "W" else 0)
    by = cy + (60 if bias_side == "N" else 0)
    box("R", min(cx, bx) - 4 if bias_side in "EW" else cx - 4, min(cy, by) - 4 if bias_side == "N" else cy - 4,
        max(cx, bx) + 4 if bias_side in "EW" else cx + 4, max(cy, by) + 4 if bias_side == "N" else cy + 4)
    box("M2", bx - 8, by - 8, bx + 8, by + 8)
    CELLS[name] = dict(kind="DC/SFQ", center=(cx, cy), jjs=2, bias_tap=(bx, by))
    return (bx, by)


def sfqdc(name, cx, cy, bias_side):
    """SFQ/DC converter (toggle flip-flop style, 3 shunted JJs)."""
    path("M1", [(cx - 35, cy - 25), (cx + 35, cy - 25), (cx + 35, cy + 25), (cx - 35, cy + 25), (cx - 35, cy - 25)], 6)
    jj(cx - 35, cy, 1.0, (0, 1))
    jj(cx + 35, cy, 1.0, (0, 1))
    box("I1", cx - 38, cy - 3, cx - 32, cy + 3)            # M1 node -> M2 output contact
    jj(cx, cy - 25, 1.4, (0, -1))
    bx = cx + (60 if bias_side == "E" else -60 if bias_side == "W" else 0)
    by = cy + (60 if bias_side == "N" else 0)
    box("R", cx - 4, cy + 25, cx + 4, by + 4)
    box("M2", bx - 8, by - 8, bx + 8, by + 8)
    CELLS[name] = dict(kind="SFQ/DC", center=(cx, cy), jjs=3, bias_tap=(bx, by))
    return (bx, by)


def barrier(name, cx, cy):
    """Controlled barrier: symmetric dc SQUID (2 x 4 Ic) replacing one LJJ node; control line couples flux."""
    a = RFL["barrier_bmax"] / 2 * RFL["jj_area_um2"]
    path("M1", [(cx - 20, cy - 15), (cx + 20, cy - 15), (cx + 20, cy + 15), (cx - 20, cy + 15), (cx - 20, cy - 15)], 5)
    jj(cx - 20, cy, a)
    jj(cx + 20, cy, a)
    for x in (cx - 20, cx + 20):
        path("M2", [(x, cy), (x + (-12 if x < cx else 12), cy)], 3)
        gnd_via(x + (-14 if x < cx else 14), cy, 3.2)
    CELLS[name] = dict(kind="controlled barrier (dc SQUID)", center=(cx, cy), jjs=2, ic_max_over_ic=RFL["barrier_bmax"])


def rotary(name, cx, cy, s=150.0):
    """Rotary element: LJJ ring with two stored-fluxon states, four LJJ ports at the corners, state flux bias."""
    ring = [(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy + s), (cx - s, cy + s), (cx - s, cy - s + 1)]
    n = ljj(name + "_ring", ring, radius=0.5)   # sharp corners: the four ports land on them
    # storage bar with two larger junctions (the two RE states)
    path("M1", [(cx - s, cy), (cx + s, cy)], 8)
    jj(cx - 40, cy, 2.0)
    jj(cx + 40, cy, 2.0)
    for x in (cx - 40, cx + 40):
        path("M2", [(x, cy), (x, cy - 14)], 3)
        gnd_via(x, cy - 16, 3.2)
    CELLS[name] = dict(kind="rotary element", center=(cx, cy), ring_cells=n, storage_jjs=2,
                       ports=dict(I0=(cx - s, cy + s), I1=(cx + s, cy + s), O0=(cx - s, cy - s), O1=(cx + s, cy - s)))
    return CELLS[name]["ports"]


# ------------------------------------------------------------------ ground plane, ILD sheets, frame
EDGE = 20.0
box("GP", EDGE, EDGE, S - EDGE, S - EDGE)
# (ILD sheets are not drawn in GDS; the 3D model adds them. I1 = M1/JJ->M2 contacts, VIA = stacked GP contacts)
# ground ring for ground bonds: M2 + Au over a fence of stacked vias into GP
for x0, y0, x1, y1 in ((40, 40, S - 40, 150), (40, S - 150, S - 40, S - 40), (40, 40, 150, S - 40), (S - 150, 40, S - 40, S - 40)):
    box("M2", x0, y0, x1, y1)
    box("PAD", x0 + 10, y0 + 10, x1 - 10, y1 - 10)
g = 70.0
while g < S - 70:
    for x, y in ((g, 95), (g, S - 95), (95, g), (S - 95, g)):
        gnd_via(x, y, 6)
    g += 50.0

# ------------------------------------------------------------------ pads (same positions as the carrier's bond pads)
n_side = {"N": 6, "E": 2, "S": 0, "W": 2}
ports = []
pitch = LAUNCHER["pitch"]
order = []
for side in ("N", "E", "S", "W"):
    k = n_side[side]
    for i in range(k):
        off = (i - (k - 1) / 2) * pitch
        if side == "N":
            order.append((side, S / 2 + off, None))
        elif side == "E":
            order.append((side, None, S / 2 - off))
        elif side == "W":
            order.append((side, None, S / 2 + off))
for pid, (side, x, y) in enumerate(order, start=1):
    net = LAUNCHER_NETS[pid]
    pad, taper, ind = LAUNCHER["width"], LAUNCHER["width"], LAUNCHER["indent"]
    if side == "N":
        c, port, u = (x, S - ind + taper + pad / 2), (x, S - ind), (0, 1)
    elif side == "E":
        c, port, u = (S - ind + taper + pad / 2, y), (S - ind, y), (1, 0)
    else:
        c, port, u = (ind - taper - pad / 2, y), (ind, y), (-1, 0)
    box("M2", c[0] - pad / 2, c[1] - pad / 2, c[0] + pad / 2, c[1] + pad / 2)
    box("PAD", c[0] - pad / 2 + 10, c[1] - pad / 2 + 10, c[0] + pad / 2 - 10, c[1] + pad / 2 - 10)
    # taper pad -> 10 um microstrip
    e = (c[0] - u[0] * pad / 2, c[1] - u[1] * pad / 2)
    vx, vy = -u[1], u[0]
    add("M2", db.DPolygon([P(e[0] + vx * pad / 2, e[1] + vy * pad / 2), P(e[0] - vx * pad / 2, e[1] - vy * pad / 2),
                           P(port[0] - vx * 5, port[1] - vy * 5), P(port[0] + vx * 5, port[1] + vy * 5)]))
    ports.append(dict(net=net, kqc_port_id=pid, side=side, port_um=list(port), outward=list(u),
                      pad_center_um=[round(c[0], 3), round(c[1], 3)], pad_size_um=[pad, pad]))
PT = {p["net"]: tuple(p["port_um"]) for p in ports}

# ------------------------------------------------------------------ circuit
ta = dcsfq("DCSFQ_A", 3200, 8250, "W")
tb = dcsfq("DCSFQ_B", 6800, 8250, "E")
tt = dcsfq("DCSFQ_T", 1700, 4400, "N")
s0 = sfqdc("SFQDC_0", 1700, 5600, "N")
s1 = sfqdc("SFQDC_1", 8300, 5600, "N")
st = sfqdc("SFQDC_T", 8300, 4400, "N")

# trigger + output microstrips (M2)
microstrip([PT["TRIG_A"], (3200, 8280)])
microstrip([PT["TRIG_B"], (6800, 8280)])
microstrip([PT["TEST_IN"], (1678, 4410)])
microstrip([(1665, 5600), PT["OUT_0"]])
microstrip([(8335, 5600), PT["OUT_1"]])
microstrip([(8335, 4400), PT["TEST_OUT"]])
# DC bias trees (M2, 6 um, square corners so the branches meet the trunk)
microstrip([PT["VB_W"], (2000, 8250), ta], 6, r=0)
microstrip([(2000, 8250), (2000, 5750), (1700, 5750), s0], 6, r=0)
microstrip([(2000, 5750), (2000, 4560), (1700, 4560), tt], 6, r=0)
microstrip([PT["VB_E"], (8000, 8250), tb], 6, r=0)
microstrip([(8000, 8250), (8000, 5750), (8300, 5750), s1], 6, r=0)
microstrip([(8000, 5750), (8000, 4560), (8300, 4560), st], 6, r=0)
# control lines: M2 loops shorted to GP next to the device they flux-bias
microstrip([PT["CTRL_CB"], (4400, 7660), (3245, 7660), (3245, 7550)], 8)
gnd_via(3245, 7550, 8)
microstrip([PT["CTRL_RE"], (5600, 6720), (5000, 6720), (5000, 6420)], 8)
gnd_via(5000, 6420, 8)
re = rotary("RE", 5000, 6400)     # after the M2 lines so its ring skips straps under CTRL_RE
barrier("CB", 3200, 7600)
# ballistic lines (M1 LJJs)
ljj("LJJ_A", [(3200, 8230), (3200, 7612)])
ljj("LJJ_A2", [(3200, 7588), (3200, re["I0"][1]), re["I0"]])
ljj("LJJ_B", [(6800, 8230), (6800, re["I1"][1]), re["I1"]])
ljj("LJJ_O0", [re["O0"], (4600, re["O0"][1]), (4600, 5600), (1735, 5600)])
ljj("LJJ_O1", [re["O1"], (5400, re["O1"][1]), (5400, 5600), (8265, 5600)])
ljj("LJJ_TEST", [(1730, 4400), (2300, 4400), (2300, 1300), (3700, 1300), (3700, 4000), (5100, 4000), (5100, 1300),
                 (6500, 1300), (6500, 4000), (7700, 4000), (7700, 4400), (8265, 4400)])
# labels on M2
gen = db.TextGenerator.default_generator()
for txt, x, y, h in (("RFL-RE1", 400, 9050, 220), ("EE143", 8700, 9050, 220), ("NB 10KA", 400, 300 + 300, 160)):
    r = gen.text(txt, ly.dbu, h / (gen.text("A", ly.dbu, 1).bbox().height() * ly.dbu))
    r.move(int(x / ly.dbu), int(y / ly.dbu))
    top.shapes(LI["M2"]).insert(r)

os.makedirs(OUT, exist_ok=True)
ly.write(os.path.join(OUT, "quantum_die.gds"))
njj = sum(1 for _ in top.shapes(LI["JJ"]).each())
json.dump(dict(ports=ports, refpoints={}), open(os.path.join(OUT, "die_ports.json"), "w"), indent=1)
json.dump(dict(cells=CELLS, total_jj=njj, stack=[dict(layer=n, gds=list(g), material=m, thickness_nm=t)
                                                 for n, g, m, t in RFL_STACK]),
          open(os.path.join(OUT, "die_cells.json"), "w"), indent=1, default=list)
print("wrote quantum_die.gds:", njj, "junctions;",
      {k: v.get("cells", v.get("jjs")) for k, v in CELLS.items()})
