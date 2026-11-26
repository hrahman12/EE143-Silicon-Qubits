"""Altium-style PCB-editor views of the QBF-X2 chip: the row block circuits/qbfx2_layout.gds (cell QBFX2_ROWS).

The chip is drawn the way Altium draws a board, layer by layer on a black canvas:
  Nb (1/0)    Top Layer, red. Wide Nb (ground plane and inner ground strips) is shown as a darker red polygon
              pour; thin Nb (the 0.5 um control, flux, gate and readout lines) as bright red tracks.
  grAl (2/0)  Mid-Layer 2, orange: the rail inductors.
  Al1 (3/0)   Bottom Layer, blue: junction base electrodes and node plates.
  Al2 (4/0)   Mid-Layer 1, teal: junction counter-electrodes and straps.
  SiNx (6/0)  Top Solder colour, purple outlines: crossover dielectric.
  JJ          white: Al1/Al2 overlap outside the SiNx, i.e. the tunnel junctions (computed from the two layers).
Net names come from the design, not from guesses. Thin Nb lines take the name of the block port they connect to
(circuits/block_ports.json). Rail node islands take the node names the netlist generator uses
(src/hardware/netlist.py): node "<row>_<n>" sits at x = MARGIN_X + n * pitch on rail <row>, and junction n of
that rail is "B<row>_<n>". The beam-splitter middle-rail junctions are "BM<q>_<a>". Block ports are drawn as silver
pin markers outside the block edge, numbered counter-clockwise from the top-left like an IC footprint; they are
markers, not drawn metal.  Output: circuits/views/altium_chip_*.png"""
import json
import math
import os
import sys

import gdstk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch, PathPatch, Rectangle
from matplotlib.path import Path
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "src"))
from hardware import layout as LY                                   # noqa: E402

GDS = os.path.join(ROOT, "circuits", "qbfx2_layout.gds")
PORTS = json.load(open(os.path.join(ROOT, "circuits", "block_ports.json")))
OUT = HERE

COL = dict(work="#2a2a2a", sub="#000000", pour="#7a0000", track="#ff1010", gral="#ff9a1a", al1="#3366ff",
           al2="#00d8b8", diel="#b040ff", jj="#ffffff", pin="#c0c0c0", silk="#ffff00", net="#f4f4f4")
LAYERS = {"nb": (1, 0), "gral": (2, 0), "al1": (3, 0), "al2": (4, 0), "diel": (6, 0)}

lib = gdstk.read_gds(GDS)
top = [c for c in lib.top_level() if c.name == PORTS["block_cell"]][0]
W, H = PORTS["width_um"], PORTS["height_um"]
X0N = LY.MARGIN_X
ROW_Y = {r: LY.rail_y(r, H - LY.MARGIN_Y) for r in LY.ROWS}
QUBIT_MID = {"A": (ROW_Y["A0"] + ROW_Y["A1"]) / 2, "B": (ROW_Y["B1"] + ROW_Y["B0"]) / 2}
PAIRS = {"DA": ("D_A", "A0"), "G": ("A1", "B1"), "DB": ("B0", "D_B")}   # as in src/hardware/netlist.py
try:
    from hardware.architecture import Architecture
    PITCH = Architecture().rail.pitch_um
except Exception:                                                   # pragma: no cover
    PITCH = 2.0
N_CELLS = int(round((W - 2 * X0N) / PITCH)) + 1                     # the drawn block (launchers included)
assert abs(2 * X0N + (N_CELLS - 1) * PITCH - W) < 1e-6, "pitch/cell count do not match the block width"

polys = {k: [p.points for p in top.get_polygons(layer=l, datatype=d)] for k, (l, d) in LAYERS.items()}
bbs = {k: np.array([[p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max()] for p in v]) for k, v in polys.items()}
texts = [(lb.text, lb.origin[0], lb.origin[1], lb.texttype) for lb in top.get_labels()]
SECTIONS = sorted([(x, t) for t, x, y, tt in texts if tt == 0 and abs(y - 230.0) < 1e-6])
RAILNAMES = {t: (x, y) for t, x, y, tt in texts if tt == 0 and t in ROW_Y}

# ---------------------------------------------------------------- Nb: split into pour (wide) and tracks (thin)
R_OPEN = 0.3                                                         # thinner than 0.6 um -> track (lines are 0.5)
nb_shapes = [Polygon(p).buffer(0) for p in polys["nb"]]
wide, thin = [], []
for P in nb_shapes:
    Wd = P.buffer(-R_OPEN, join_style=2).buffer(R_OPEN, join_style=2).intersection(P)
    Th = P.difference(Wd)
    wide.append(Wd)
    thin.append(Th)
NB_WIDE = unary_union(wide)
NB_THIN = unary_union([t for t in thin if not t.is_empty]).buffer(0)
thin_parts = [g for g in (NB_THIN.geoms if hasattr(NB_THIN, "geoms") else [NB_THIN]) if g.area > 0.08]

ext_ports = [p for p in PORTS["ports"] if p["kind"] != "internal_short"]
sig_ports = [p for p in ext_ports if p["kind"] != "ground"]
shorts = [p for p in PORTS["ports"] if p["kind"] == "internal_short"]


def _name_of(g):
    for p in sig_ports:
        if g.distance(Point(p["x"], p["y"])) < 0.3:
            return p["name"]
    for p in shorts:
        if g.distance(Point(p["x"], p["y"])) < 0.3:
            return p["name"].replace("_SHORT", "")
    return None


# thin pieces that do not touch a port inherit the name of a named thin piece they touch (through the line chain)
names = [_name_of(g) for g in thin_parts]
for _ in range(6):
    changed = False
    for i, g in enumerate(thin_parts):
        if names[i] is None:
            for j, h in enumerate(thin_parts):
                if names[j] and i != j and g.distance(h) < 0.05:
                    names[i], changed = names[j], True
                    break
    if not changed:
        break
TRACKS = [(g, n) for g, n in zip(thin_parts, names) if n]
NB_WIDE = unary_union([NB_WIDE] + [g for g, n in zip(thin_parts, names) if not n])
_gnd_pts = [Point(p["x"], p["y"]) for p in PORTS["ports"] if p["kind"] == "ground"]
GND_COMPS = [g for g in (NB_WIDE.geoms if hasattr(NB_WIDE, "geoms") else [NB_WIDE])
             if any(g.distance(q) < 0.3 for q in _gnd_pts) or g.distance(box(0, 0, W, H).exterior) < 0.05]


# pin numbering: counter-clockwise from the top-left (W side top -> bottom, S, E side bottom -> top, N)
def _pin_key(p):
    side = p["direction"]
    order = {"W": 0, "S": 1, "E": 2, "N": 3}[side]
    pos = -p["y"] if side == "W" else p["x"] if side == "S" else p["y"] if side == "E" else -p["x"]
    return order, pos


PINS = [(i + 1, p) for i, p in enumerate(sorted(ext_ports, key=_pin_key))]


# ------------------------------------------------------------------------------------------------- helpers
def as_path(g):
    verts, codes = [], []
    for poly in (g.geoms if hasattr(g, "geoms") else [g]):
        if poly.is_empty or poly.geom_type != "Polygon":
            continue
        for ring in [poly.exterior, *poly.interiors]:
            c = list(ring.coords)
            verts += c
            codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
    return Path(verts, codes) if verts else None


def in_box(k, bx, pad=0.0):
    x0, y0, x1, y1 = bx
    b = bbs[k]
    sel = (b[:, 2] >= x0 - pad) & (b[:, 0] <= x1 + pad) & (b[:, 3] >= y0 - pad) & (b[:, 1] <= y1 + pad)
    return [polys[k][i] for i in np.nonzero(sel)[0]]


def junctions(bx):
    """Al1 n Al2 outside the SiNx inside the box: (geometry, kind) with kind 'jj' (< 0.2 um^2) or 'contact'"""
    a1 = unary_union([Polygon(p).buffer(0) for p in in_box("al1", bx, 1)])
    a2 = unary_union([Polygon(p).buffer(0) for p in in_box("al2", bx, 1)])
    dl = unary_union([Polygon(p).buffer(0) for p in in_box("diel", bx, 1)])
    ov = a1.intersection(a2).difference(dl)
    out = []
    for g in (ov.geoms if hasattr(ov, "geoms") else [ov]):
        if g.geom_type == "Polygon" and g.area > 1e-4:
            out.append((g, "jj" if g.area < 0.2 else "contact"))
    return out


def jj_designator(g):
    """netlist designator of the junction g: BM<q>_<a> on a beam-splitter middle rail, else B<row>_<n>. In the
    coupler the rail junctions sit next to the shared strip of their pair; the rail is the one on the same side."""
    cx, cy = g.centroid.x, g.centroid.y
    sec = section_at(cx)
    if sec in ("BS_prep", "BS_analysis"):
        for q, ym in QUBIT_MID.items():
            if abs(cy - ym) < 1.5:
                return f"BM{q}_{int(math.floor((cx - X0N) / PITCH))}"
    row = None
    if sec in ("taper_in", "coupler", "taper_out"):
        for a_, b_ in PAIRS.values():
            ys = (ROW_Y[a_] + ROW_Y[b_]) / 2
            if abs(cy - ys) < 2.5:
                row = a_ if cy > ys else b_
    if row is None:
        row = min(ROW_Y, key=lambda r: abs(ROW_Y[r] - cy))
        if abs(ROW_Y[row] - cy) > 4.5:
            return None
    return f"B{row}_{int(round((cx - X0N) / PITCH))}"


def section_at(x):
    s = None
    for xs, t in SECTIONS:
        if x >= xs:
            s = t
    return s


def straight_runs(g, Lmin):
    """label anchors along the straight runs of a thin track: (x, y, angle) at edge midpoints moved to the centre"""
    out = []
    for poly in (g.geoms if hasattr(g, "geoms") else [g]):
        c = list(poly.exterior.coords)
        for (xa, ya), (xb, yb) in zip(c[:-1], c[1:]):
            L = math.hypot(xb - xa, yb - ya)
            if L < Lmin:
                continue
            nx, ny = -(yb - ya) / L, (xb - xa) / L
            mx, my = (xa + xb) / 2, (ya + yb) / 2
            for s in (1, -1):
                p = Point(mx + s * nx * 0.25, my + s * ny * 0.25)
                if poly.contains(p):
                    ang = math.degrees(math.atan2(yb - ya, xb - xa))
                    ang = ang + 180 if ang > 90 else ang - 180 if ang <= -90 else ang
                    out.append((p.x, p.y, ang, L))
                    break
    return out


def view(name, title, bx, width_in, *, node_labels=False, jj=False, designators=False, track_min=None,
         pin_scale=1.0, sections=True, rails=True, note=None, max_node_labels=60, pin_len=None):
    x0, y0, x1, y1 = bx
    span, hgt = x1 - x0, y1 - y0
    band = 0.10 * hgt if hgt / span > 0.3 else 0.30 * hgt                 # bottom band: scale bar + legend
    title_frac = 0.06 if hgt / span > 0.3 else 0.13
    fig_h = width_in * (hgt + band) / span / (1 - title_frac)
    fig = plt.figure(figsize=(width_in, fig_h), dpi=160, facecolor=COL["work"])
    ax = fig.add_axes([0, 0, 1, 1 - title_frac])
    ax.set_facecolor(COL["work"])
    pt = 72 * width_in / span                                       # points per um
    lw_min = 0.35 if span > 400 else 0.0                            # keep sub-pixel features visible when zoomed out
    clip = box(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    ax.add_patch(Rectangle((0, 0), W, H, facecolor=COL["sub"], edgecolor="#5a5a5a", lw=0.6, zorder=0.2))
    # Nb pour and tracks
    pth = as_path(NB_WIDE.intersection(clip))
    if pth is not None:
        ax.add_patch(PathPatch(pth, facecolor=COL["pour"], edgecolor=COL["pour"], lw=lw_min * 0.6, zorder=1))
    trk = unary_union([g for g, _ in TRACKS]).intersection(clip)
    pth = as_path(trk)
    if pth is not None:
        ax.add_patch(PathPatch(pth, facecolor=COL["track"], edgecolor=COL["track"], lw=max(lw_min, 0.0) * 2.2,
                               zorder=2))
    for k, z, fc, ec, alpha in (("gral", 3, COL["gral"], COL["gral"], 1.0), ("al1", 4, COL["al1"], COL["al1"], 1.0),
                                ("al2", 5, COL["al2"], COL["al2"], 0.92)):
        ps = in_box(k, bx, 1)
        if ps:
            ax.add_collection(PolyCollection(ps, facecolors=fc, edgecolors=ec, linewidths=lw_min, alpha=alpha,
                                             zorder=z))
    ps = in_box("diel", bx, 1)
    if ps:
        ax.add_collection(PolyCollection(ps, facecolors=(0.69, 0.25, 1.0, 0.16), edgecolors=COL["diel"],
                                         linewidths=0.5 if span < 120 else 0.25, zorder=6))
    njj = 0
    if jj:
        jjs = junctions(bx)
        njj = sum(1 for _, k in jjs if k == "jj")
        for g, k in jjs:
            if k != "jj":
                continue
            ax.add_patch(PathPatch(as_path(g), facecolor=COL["jj"], edgecolor="#000000", lw=0.3, zorder=7))
            if designators and k == "jj":
                d = jj_designator(g)
                if d and x0 < g.centroid.x < x1 and y0 < g.centroid.y < y1:
                    ax.text(g.centroid.x, g.centroid.y + 0.32, d, color=COL["silk"], ha="center", va="bottom",
                            fontsize=max(3.0, min(6.0, 0.55 * PITCH * pt / max(len(d), 1) * 1.5)), zorder=9,
                            family="DejaVu Sans Mono", weight="bold", clip_on=True)
    # net names on the thin Nb lines
    track_min = track_min if track_min is not None else span / 9
    placed = []
    for g, nm in TRACKS:
        if not nm or not g.intersects(clip):
            continue
        for (x, y, ang, L) in straight_runs(g.intersection(clip), track_min):
            if not (x0 < x < x1 and y0 < y < y1):
                continue
            if any(abs(x - px) < span / 10 and abs(y - py) < hgt / 40 and t == nm for px, py, t in placed):
                continue
            placed.append((x, y, nm))
            ax.text(x, y, nm, color=COL["net"], fontsize=max(3.4, min(7.0, 0.5 * pt * 0.95)), rotation=ang,
                    ha="center", va="center", zorder=8, family="DejaVu Sans Mono", clip_on=True,
                    bbox=dict(boxstyle="square,pad=0.1", fc="#000000", ec="none", alpha=0.6))
    # GND on the pour, a few times per view
    gp = []
    for g in GND_COMPS:
        gi = g.intersection(box(x0, y0, x1, y1))
        if gi.is_empty or gi.area < 0.01 * span * hgt:
            continue
        p = gi.representative_point()
        if all(math.hypot(p.x - a, p.y - b_) > span / 6 for a, b_ in gp):
            gp.append((p.x, p.y))
            ax.text(p.x, p.y, "GND", color="#ffb0b0", fontsize=max(3.4, min(8, 1.2 * pt)), ha="center",
                    va="center", zorder=8, family="DejaVu Sans Mono", alpha=0.85, clip_on=True)
    # rail node islands: net names as the netlist names them
    if node_labels:
        ns = [n for n in range(N_CELLS) if x0 + 0.3 < X0N + n * PITCH < x1 - 0.3]
        step = max(1, int(math.ceil(len(ns) / max_node_labels)))
        fs = max(3.0, min(6.5, 0.9 * PITCH * pt / 6.5 / 0.6))
        for row, yr in ROW_Y.items():
            if not (y0 < yr < y1):
                continue
            for n in ns[::step]:
                ax.text(X0N + n * PITCH, yr, f"{row}_{n}", color=COL["net"], fontsize=fs, ha="center", va="center",
                        zorder=8.5, family="DejaVu Sans Mono", clip_on=True,
                        bbox=dict(boxstyle="square,pad=0.06", fc="#000000", ec="none", alpha=0.55))
    if rails:
        for row, yr in ROW_Y.items():
            if y0 < yr < y1:
                right = x0 < X0N
                xl = x1 - 0.006 * span if right else x0 + 0.004 * span
                ax.text(xl, yr + 0.012 * hgt, f"rail {row}", color=COL["silk"], fontsize=6.4,
                        ha="right" if right else "left", va="bottom", zorder=9.6, weight="bold", clip_on=True,
                        bbox=dict(boxstyle="square,pad=0.12", fc="#000000", ec="none", alpha=0.7))
    # strip and middle-rail nodes (coupler strips S<pair>_<n>, beam-splitter middle rails M<q>_<n>)
    if node_labels:
        fs2 = max(3.0, min(6.5, 0.9 * PITCH * pt / 6.5 / 0.6))
        ns2 = [n for n in range(N_CELLS) if x0 + 0.3 < X0N + n * PITCH < x1 - 0.3]
        step2 = max(1, int(math.ceil(len(ns2) / max_node_labels)))
        for n in ns2[::step2]:
            xn = X0N + n * PITCH
            sec = section_at(xn)
            spots = []
            if sec in ("taper_in", "coupler", "taper_out"):
                spots = [(f"S{k}_{n}", (ROW_Y[a_] + ROW_Y[b_]) / 2) for k, (a_, b_) in PAIRS.items()]
            elif sec in ("BS_prep", "BS_analysis"):
                spots = [(f"M{q}_{n}", ym) for q, ym in QUBIT_MID.items()]
            for txt, ys in spots:
                if y0 < ys < y1:
                    ax.text(xn, ys, txt, color="#000000", fontsize=fs2, ha="center", va="center", zorder=8.6,
                            family="DejaVu Sans Mono", clip_on=True,
                            bbox=dict(boxstyle="square,pad=0.06", fc="#e8e8e8", ec="none", alpha=0.85))
    if sections:
        for xs, t in SECTIONS:
            if x0 <= xs <= x1:
                ax.plot([xs, xs], [y0 if y0 > 0 else 0, min(y1, H)], color=COL["silk"], lw=0.4, alpha=0.45,
                        zorder=8.8, ls=(0, (4, 4)))
                ax.text(xs + 0.004 * span, min(y1, H) - 0.02 * hgt, t, color=COL["silk"], fontsize=6.5,
                        ha="left", va="top", zorder=9, weight="bold", clip_on=True)
    # block pins (markers outside the block edge)
    plen = pin_len if pin_len else max(3.0, 0.035 * span) * pin_scale
    for num, p in PINS:
        px, py, side = p["x"], p["y"], p["direction"]
        wpin = p["width"] if p["kind"] == "ground" else max(0.5, 0.022 * span * pin_scale)
        if side in ("W", "E"):
            rx = px - plen if side == "W" else px
            rect = (rx, py - wpin / 2, plen, wpin)
            tx, ty = rx + plen / 2, py
            nx_, ha = (rx - 0.01 * span, "right") if side == "W" else (rx + plen + 0.01 * span, "left")
            ny_, va, rot = py, "center", 0
        else:
            ry = py if side == "N" else py - plen
            rect = (px - wpin / 2, ry, wpin, plen)
            tx, ty = px, ry + plen / 2
            nx_, ny_, ha = px, (ry + plen + 0.01 * hgt) if side == "N" else (ry - 0.01 * hgt), "center"
            va, rot = ("bottom" if side == "N" else "top"), 0
        if not (x0 - plen < px < x1 + plen and y0 - plen < py < y1 + plen):
            continue
        ax.add_patch(Rectangle(rect[:2], rect[2], rect[3], facecolor=COL["pin"], edgecolor="#ffffff", lw=0.4,
                               zorder=9))
        ax.text(tx, ty, str(num), color="#000000", fontsize=max(3.5, min(8, 0.6 * min(rect[2], rect[3]) * pt)),
                ha="center", va="center", zorder=9.5, weight="bold", clip_on=True)
        ax.text(nx_, ny_, p["name"], color=COL["net"], fontsize=max(4.0, min(7.5, 0.016 * span * pt)), ha=ha,
                va=va, rotation=rot, zorder=9.5, family="DejaVu Sans Mono", clip_on=True)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0 - band, y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.add_patch(Rectangle((x0, y0 - band), span, band, facecolor=COL["work"], edgecolor="none", zorder=10))
    fig.text(0.006, 0.985, "QBF-X2 chip, row block QBFX2_ROWS   |   " + title, color="#ffffff", fontsize=9, va="top")
    sub = (f"{W:.0f} x {H:.0f} um, {len(LY.ROWS)} rails x {N_CELLS} cells, {PITCH:g} um pitch. "
           + (note or ""))
    fig.text(0.006, 0.985 - 0.45 * title_frac, sub, color="#bdbdbd", fontsize=6.6, va="top")
    nice = min([0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500], key=lambda s_: abs(s_ - span / 7))
    yb = y0 - band * 0.55
    ax.plot([x0 + span * 0.02, x0 + span * 0.02 + nice], [yb, yb], color="white", lw=2.4, zorder=11,
            solid_capstyle="butt")
    ax.text(x0 + span * 0.02 + nice / 2, yb + band * 0.12, f"{nice:g} um", color="white", fontsize=7, ha="center",
            va="bottom", zorder=11)
    handles = [Patch(color=COL["track"], label="Top Layer  Nb lines (0.5 um)"),
               Patch(color=COL["pour"], label="Top Layer  Nb ground pour (GND)"),
               Patch(color=COL["al2"], label="Mid-Layer 1  Al2 counter-electrode"),
               Patch(color=COL["gral"], label="Mid-Layer 2  grAl rail inductor"),
               Patch(color=COL["al1"], label="Bottom Layer  Al1 base electrode"),
               Patch(facecolor=(0.69, 0.25, 1.0, 0.16), edgecolor=COL["diel"], label="SiNx crossover dielectric"),
               Patch(color=COL["jj"], label="Josephson junction (Al1 \u2229 Al2)"),
               Patch(color=COL["pin"], label="Block pin (marker) + net")]
    leg = ax.legend(handles=handles, loc="lower right", ncol=4, fontsize=5.8, facecolor="#141414",
                    edgecolor="#5a5a5a", labelcolor="white", framealpha=1.0, bbox_to_anchor=(1.0, 0.0),
                    borderaxespad=0.3)
    leg.set_zorder(12)
    path = os.path.join(OUT, f"altium_chip_{name}.png")
    fig.savefig(path, facecolor=COL["work"])
    plt.close(fig)
    print(f"wrote {os.path.relpath(path, ROOT)}" + (f"   ({njj} junctions in view)" if jj else ""))
    return path


if __name__ == "__main__":
    named = sorted({n for _, n in TRACKS if n})
    print(f"Nb: {len(nb_shapes)} shapes -> {len(thin_parts)} thin line pieces ({sum(1 for _, n in TRACKS if n)} named,"
          f" {len(named)} nets), pour area {NB_WIDE.area:.0f} um^2")
    which = sys.argv[1:] or ["full", "west", "launcher", "cells", "coupler", "beamsplitter"]
    if "full" in which:
        view("full", "whole block: 26 pins, fan-in lines, six rails, launchers at both ends, coupler in the middle",
             (-175, -48, W + 175, H + 48), 26, pin_scale=0.5, pin_len=28, track_min=60, rails=False,
             note="Pins are numbered counter-clockwise from the top-left, like an IC footprint.")
    if "west" in which:
        view("west", "west end: pins 1-12, the 0.5 um fan-in lines with their net names, launcher section",
             (-62, -6, 252, 296), 13, track_min=14, pin_scale=0.9, pin_len=12,
             note="Each line ends on the inner ground strip next to its rail (the *_SHORT points in block_ports.json).")
    if "launcher" in which:
        view("launcher", "launcher on rails D_A / A0 / A1: load loops, trap lines bending to the rail, node nets",
             (150, 140, 215, 177), 14, node_labels=True, track_min=5, max_node_labels=17,
             note="Node names are the netlist's: <rail>_<n> at x = 120 + 2n um.")
    if "cells" in which:
        view("cells", "junction cells on rails D_A and A0 (accelerate section): node nets, junction designators",
             (300.2, 154.2, 313.8, 172.0), 13, node_labels=True, jj=True, designators=True, track_min=3,
             note="White squares: Al1/Al2 overlaps outside the SiNx (the junctions); yellow: netlist designators.")
    if "coupler" in which:
        view("coupler", "gate coupler: rails A1 / B1 and the shared strip SG between them, junctions and nets",
             (896.2, 137.0, 912.2, 153.0), 12, node_labels=True, jj=True, designators=True, track_min=3,
             note="In the coupler the rail junctions return to the shared strip S<pair>_<n>, not to ground (netlist.py).")
    if "coupler_overview" in which or not sys.argv[1:]:
        view("coupler_overview", "coupler section with its tapers: all six rails, the three coupling strips",
             (800, 112, 1196, 178), 16, track_min=40,
             note="The envelope g(n) ramps the coupling up over taper_in and down over taper_out.")
    if "beamsplitter" in which:
        view("beamsplitter", "beam splitter (BS_prep) on qubit A: rails A0 / A1 and the middle rail with BM junctions",
             (640.2, 146.0, 656.2, 164.0), 12, node_labels=True, jj=True, designators=True, track_min=3,
             note="Middle-rail series junctions are BM<q>_<a> between nodes a and a+1 (netlist.py).")
