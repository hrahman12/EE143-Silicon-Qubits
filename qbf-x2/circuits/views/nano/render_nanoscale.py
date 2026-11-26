"""Nanoscale views of the QBF-X2 chip, from the drawn GDS (circuits/qbfx2_layout.gds) and the documented process.

Process stack (src/hardware/drc.py, in deposition order): Nb 150 nm (ground, lines) -> granular Al 20 nm (rail
inductors) -> Al1 30 nm (node plates, junction fingers) -> SiNx 100 nm (crossovers, trim capacitors) -> ion mill +
static oxidation (the AlOx tunnel barrier, ~1-2 nm, set by the dose to Jc = 2.1 uA/um^2; not drawn in the GDS) ->
Al2 30 nm (counter-electrodes, leads, contacts).

Outputs (circuits/views/nano/):
  nano_junction_top.png        a rail junction (cross-type overlap) with nm dimensions and its electrical values
  nano_middle_junction_top.png the beam-splitter middle junction as drawn (86 x 150 nm, below the 100 nm rule) and
                               the fix (114 x 114 nm square, same area)
  nano_cross_sections.png      to-scale cross-sections built by depositing the layers in process order over the drawn
                               polygons (conformal coverage); inset: the tunnel barrier
  nano_cell_mesh.json          the same stack in 3D (triangulated prisms per layer) for blender_nano.py
Run: python3 circuits/views/nano/render_nanoscale.py [--annotate]   (--annotate labels the Blender render)
"""
import json
import math
import os
import sys

import gdstk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch, Rectangle
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GDS = os.path.join(ROOT, "circuits", "qbfx2_layout.gds")
NM = 1e3                                                    # um -> nm

# process stack in deposition order: (key, GDS layer, thickness um, label, colour)
STACK = [("nb", (1, 0), 0.150, "Nb 150 nm (ground)", "#8a1c1c"),
         ("gral", (2, 0), 0.020, "granular Al 20 nm (rail inductor)", "#ff9a1a"),
         ("al1", (3, 0), 0.030, "Al1 30 nm (base electrode, node plate)", "#3366ff"),
         ("diel", (6, 0), 0.100, "SiNx 100 nm (crossover / trim capacitor)", "#b040ff"),
         ("barrier", None, 0.0015, "AlOx tunnel barrier ~1.5 nm (oxidation)", "#ffffff"),
         ("al2", (4, 0), 0.030, "Al2 30 nm (counter-electrode, leads)", "#00d8b8")]
COL = {k: c for k, _, _, _, c in STACK}
COL.update(sub="#1b2030", bg="#000000", work="#2a2a2a", dim="#ffff66", txt="#f2f2f2")
JC_UA_UM2 = 2.1
C_SPEC_FF_UM2 = 50.0
PHI0, H = 2.067833848e-15, 6.62607015e-34

lib = gdstk.read_gds(GDS)
TOP = [c for c in lib.top_level() if c.name == "QBFX2_ROWS"][0]
_cache = {}


def layer_geom(key, bx):
    """union of a layer's polygons inside the box (um)"""
    l_d = dict((k, ld) for k, ld, *_ in STACK)[key]
    B = box(*bx)
    out = []
    for p in TOP.get_polygons(layer=l_d[0], datatype=l_d[1]):
        xs, ys = p.points[:, 0], p.points[:, 1]
        if xs.max() < bx[0] or xs.min() > bx[2] or ys.max() < bx[1] or ys.min() > bx[3]:
            continue
        P = Polygon(p.points).buffer(0)
        if P.intersects(B):
            out.append(P.intersection(B))
    return unary_union(out) if out else Polygon()


def stack_geoms(bx):
    g = {k: layer_geom(k, bx) for k, ld, *_ in STACK if ld}
    small = []
    ov = g["al1"].intersection(g["al2"]).difference(g["diel"])
    for p in (ov.geoms if hasattr(ov, "geoms") else [ov]):
        if p.geom_type == "Polygon" and 1e-4 < p.area < 0.2:          # tunnel junctions (contacts >= 1 um^2 are shorts)
            small.append(p)
    g["barrier"] = unary_union(small) if small else Polygon()
    return g


def junction_values(area_um2):
    Ic = JC_UA_UM2 * area_um2 * 1e-6
    return dict(Ic_nA=Ic * 1e9, C_fF=C_SPEC_FF_UM2 * area_um2, EJ_GHz=Ic * PHI0 / (2 * math.pi * H) / 1e9)


# ------------------------------------------------------------------------------------------------ top views
def dim_h(ax, x0, x1, y, txt, above=True, col=None, fs=8):
    col = col or COL["dim"]
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<|-|>", color=col, lw=0.9, shrinkA=0, shrinkB=0),
                zorder=10)
    ax.text((x0 + x1) / 2, y + (0.012 if above else -0.012), txt, color=col, fontsize=fs, ha="center", zorder=11,
            va="bottom" if above else "top", family="DejaVu Sans Mono", weight="bold",
            bbox=dict(boxstyle="square,pad=0.12", fc="#000000", ec="none", alpha=0.9))


def dim_v(ax, y0, y1, x, txt, right=True, col=None, fs=8):
    col = col or COL["dim"]
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<|-|>", color=col, lw=0.9, shrinkA=0, shrinkB=0),
                zorder=10)
    ax.text(x + (0.012 if right else -0.012), (y0 + y1) / 2, txt, color=col, fontsize=fs, ha="left" if right else "right",
            zorder=11,
            va="center", family="DejaVu Sans Mono", weight="bold", rotation=0,
            bbox=dict(boxstyle="square,pad=0.12", fc="#000000", ec="none", alpha=0.9))


def draw_layers(ax, g, alpha=0.88):
    for key, ld, t, lab, c in STACK:
        if key == "barrier":
            continue
        geom = g[key]
        for p in (geom.geoms if hasattr(geom, "geoms") else [geom]):
            if p.is_empty or p.geom_type != "Polygon":
                continue
            xy = np.array(p.exterior.coords)
            if key == "diel":
                ax.add_patch(plt.Polygon(xy, closed=True, facecolor=(0.69, 0.25, 1.0, 0.16), edgecolor=c, lw=1.0, zorder=4))
            else:
                ax.add_patch(plt.Polygon(xy, closed=True, facecolor=c, edgecolor="none", alpha=alpha,
                                         zorder={"nb": 1, "gral": 2, "al1": 3, "al2": 5}[key]))
    b = g["barrier"]
    for p in (b.geoms if hasattr(b, "geoms") else [b]):
        if not p.is_empty and p.geom_type == "Polygon":
            ax.add_patch(plt.Polygon(np.array(p.exterior.coords), closed=True, facecolor="#ffffff", edgecolor="#000000",
                                     lw=0.8, zorder=6, hatch="////", alpha=0.95))


def nm_grid(ax, bx, step=0.05):
    x0, y0, x1, y1 = bx
    xs = np.arange(math.ceil(x0 / step) * step, x1, step)
    ys = np.arange(math.ceil(y0 / step) * step, y1, step)
    X, Y = np.meshgrid(xs, ys)
    ax.scatter(X.ravel(), Y.ravel(), s=0.6, c="#4a4a4a", zorder=0.5, linewidths=0)


def top_view(name, bx, title, note, annot, size_in=(11, 9.6)):
    g = stack_geoms(bx)
    fig = plt.figure(figsize=size_in, dpi=170, facecolor=COL["work"])
    ax = fig.add_axes([0.07, 0.07, 0.62, 0.82])
    ax.set_facecolor(COL["bg"])
    nm_grid(ax, bx)
    draw_layers(ax, g)
    annot(ax, g)
    x0, y0, x1, y1 = bx
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    tick = 0.1
    ax.set_xticks(np.arange(math.ceil(x0 / tick) * tick, x1 + 1e-9, tick))
    ax.set_yticks(np.arange(math.ceil(y0 / tick) * tick, y1 + 1e-9, tick))
    ax.set_xticklabels([f"{(v - x0) * NM:.0f}" for v in ax.get_xticks()], color="#cfcfcf", fontsize=7)
    ax.set_yticklabels([f"{(v - y0) * NM:.0f}" for v in ax.get_yticks()], color="#cfcfcf", fontsize=7)
    ax.set_xlabel(f"x (nm, from x = {x0:.2f} um in the row block)", color="#cfcfcf", fontsize=8)
    ax.set_ylabel(f"y (nm, from y = {y0:.2f} um)", color="#cfcfcf", fontsize=8)
    for s_ in ax.spines.values():
        s_.set_color("#555555")
    fig.text(0.015, 0.975, "QBF-X2 chip, nanoscale   |   " + title, color="white", fontsize=11, va="top")
    fig.text(0.015, 0.945, "Drawn geometry from circuits/qbfx2_layout.gds; dot grid 50 nm.", color="#bdbdbd", fontsize=7.5,
             va="top")
    fig.text(0.715, 0.885, note, color="#e6e6e6", fontsize=8.2, va="top", family="DejaVu Sans", linespacing=1.45,
             wrap=True)
    handles = [Patch(color=c, label=lab) for k, ld, t, lab, c in STACK if k not in ("barrier", "diel")]
    handles.insert(3, Patch(facecolor=(0.69, 0.25, 1.0, 0.16), edgecolor=COL["diel"], label=dict((k, l) for k, _, _, l, _ in STACK)["diel"]))
    handles.append(Patch(facecolor="#ffffff", edgecolor="#000000", hatch="////", label="Josephson junction: AlOx barrier on the overlap"))
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.705, 0.06), fontsize=7.4, facecolor="#141414",
               edgecolor="#5a5a5a", labelcolor="white", framealpha=1.0)
    path = os.path.join(HERE, f"{name}.png")
    fig.savefig(path, facecolor=COL["work"])
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


def rail_junction_view():
    xj, yj = 301.45, 159.075                                      # junction BA0_91 (rail A0, node 91)
    bx = (300.95, 158.55, 302.15, 159.75)

    def annot(ax, g):
        jj = [p for p in (g["barrier"].geoms if hasattr(g["barrier"], "geoms") else [g["barrier"]])][0]
        a0, b0, a1, b1 = jj.bounds
        dim_h(ax, a0, a1, b0 - 0.17, f"{(a1 - a0) * NM:.0f} nm", above=False)
        dim_v(ax, b0, b1, a1 + 0.05, f"{(b1 - b0) * NM:.0f} nm")
        dim_v(ax, b0 - 0.10, b0, a0 - 0.05, "100 nm", right=False, fs=7)          # Al1 tail below the Al2 bar
        dim_h(ax, a0 - 0.10, a0, b1 + 0.05, "100 nm", above=True, fs=7)            # Al2 bar tail left of the finger
        ax.annotate("Al1 finger from node plate A0_91", (a0 + 0.1, b1 + 0.38), (a0 + 0.45, b1 + 0.47), color=COL["txt"],
                    fontsize=7.6, arrowprops=dict(arrowstyle="->", color="#bbbbbb", lw=0.7))
        ax.annotate("Al2 bar: the junction's\nreturn lead to GND", (a1 + 0.25, (b0 + b1) / 2), (a1 + 0.2, b0 - 0.38),
                    color=COL["txt"], fontsize=7.6, arrowprops=dict(arrowstyle="->", color="#bbbbbb", lw=0.7))
        ax.annotate("junction BA0_91\n(AlOx barrier)", ((a0 + a1) / 2, (b0 + b1) / 2), (a0 + 0.02, b0 - 0.4),
                    color="white", fontsize=8, weight="bold", arrowprops=dict(arrowstyle="->", color="white", lw=0.9))
        ax.text(a0 - 0.2, b0 - 0.05, "Al1 tail\n(overlay margin)", color="#cfcfcf", fontsize=6.8, ha="right", va="center")
        ax.text(a0 - 0.05, b1 + 0.12, "Al2 tail", color="#cfcfcf", fontsize=6.8, ha="center", va="bottom")
    jv = junction_values(0.200 * 0.1917)
    note = (f"Cross-type overlap junction\n"
            f"Al1 finger 200 nm x Al2 bar 192 nm\n"
            f"area 0.0384 um^2 = 38 400 nm^2\n\n"
            f"Jc = {JC_UA_UM2} uA/um^2 (oxidation dose)\n"
            f"I_c = Jc x A = {jv['Ic_nA']:.1f} nA\n"
            f"E_J / h = {jv['EJ_GHz']:.1f} GHz\n"
            f"C_J = {jv['C_fF']:.2f} fF (50 fF/um^2)\n\n"
            f"Each finger runs 100 nm past the other,\n"
            f"so the area is the product of the two\n"
            f"drawn widths and does not change with\n"
            f"Al1/Al2 overlay error.\n\n"
            f"The AlOx barrier (~1-2 nm) covers the\n"
            f"whole overlap; SiNx keeps it off every\n"
            f"other Al1/Al2 crossing.")
    top_view("nano_junction_top", bx, "rail Josephson junction BA0_91 (rail A0, node 91), 1.2 x 1.2 um", note, annot)


def middle_junction_view():
    bx = (640.82, 155.06, 641.42, 155.66)

    def annot(ax, g):
        jj = [p for p in (g["barrier"].geoms if hasattr(g["barrier"], "geoms") else [g["barrier"]])
              if abs(p.centroid.x - 641.1) < 0.2][0]
        a0, b0, a1, b1 = jj.bounds
        dim_h(ax, a0, a1, b1 + 0.2, f"{(a1 - a0) * NM:.0f} nm  < 100 nm rule", above=True, col="#ff5c5c")
        ax.plot([a0, a0], [b1, b1 + 0.2], color="#ff5c5c", lw=0.5, ls=":", zorder=10)
        ax.plot([a1, a1], [b1, b1 + 0.2], color="#ff5c5c", lw=0.5, ls=":", zorder=10)
        dim_v(ax, b0, b1, a1 + 0.21, f"{(b1 - b0) * NM:.0f} nm")
        s = math.sqrt(jj.area)
        cx, cy = jj.centroid.x, jj.centroid.y
        ax.add_patch(Rectangle((cx - s / 2, cy - s / 2), s, s, fill=False, ec="#66ff66", lw=1.4, ls=(0, (4, 2)), zorder=7))
        ax.annotate(f"fix: {s * NM:.0f} x {s * NM:.0f} nm square\n(same area, same I_c)", (cx + s / 2, cy - s / 2),
                    (cx + 0.2, cy - 0.17), color="#66ff66", fontsize=7.8, ha="left", va="center", weight="bold", zorder=11,
                    arrowprops=dict(arrowstyle="->", color="#66ff66", lw=0.9),
                    bbox=dict(boxstyle="square,pad=0.15", fc="#000000", ec="none", alpha=0.9))
        ax.annotate("Al1 middle-rail finger (150 nm)", (a0 - 0.12, (b0 + b1) / 2), (a0 - 0.2, b1 + 0.17), color=COL["txt"],
                    fontsize=7.5, arrowprops=dict(arrowstyle="->", color="#bbbbbb", lw=0.7))
        ax.annotate("Al2 lead (86 nm wide: also < 100 nm)", (a0 + 0.04, b0 - 0.07), (a0 - 0.2, b0 - 0.2),
                    color=COL["txt"], fontsize=7.5, arrowprops=dict(arrowstyle="->", color="#bbbbbb", lw=0.7))
    jv = junction_values(0.0129)
    note = (f"Beam-splitter middle-rail junction\n"
            f"BMA_260 (qubit A, BS_prep)\n\n"
            f"Redesigned to E_J,M = 13.5 GHz:\n"
            f"area 0.0129 um^2, I_c = {jv['Ic_nA']:.1f} nA,\n"
            f"C_J = {jv['C_fF']:.2f} fF.\n\n"
            f"As drawn it is still a 150 nm finger,\n"
            f"so the other side is only 86 nm:\n"
            f"below the 100 nm junction and Al2\n"
            f"width rules. These 304 junctions are\n"
            f"the 608 DRC violations of the block.\n\n"
            f"Fix (green): draw it square,\n"
            f"114 x 114 nm, same area, same I_c.")
    top_view("nano_middle_junction_top", bx, "beam-splitter middle junction BMA_260 as drawn, and its fix", note, annot)


# ------------------------------------------------------------------------------------------------ cross-sections
def deposit_profile(g, p0, p1, n=4000):
    """layers deposited in process order along the cut p0 -> p1 (um). Each film follows the surface below it
    (dilation of the profile by the film thickness = conformal coverage, also on step walls) where its polygon is.
    Returns s (um), the list of (key, bottom, top, mask) and the final profile."""
    s = np.linspace(0.0, 1.0, n)
    xs = p0[0] + (p1[0] - p0[0]) * s
    ys = p0[1] + (p1[1] - p0[1]) * s
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    S = s * L
    ds = S[1] - S[0]
    h = np.zeros(n)
    films = []
    for key, ld, t, lab, c in STACK:
        geom = g[key]
        if geom.is_empty:
            continue
        mask = shapely.contains_xy(geom, xs, ys) | shapely.intersects_xy(geom.boundary, xs, ys)
        if not mask.any():
            continue
        k = max(1, int(round(t / ds)))
        top = h.copy()
        for u in range(-k, k + 1):                                    # dilation by a disk of radius t
            sh = np.roll(h, u)
            if u > 0:
                sh[:u] = h[0]
            elif u < 0:
                sh[u:] = h[-1]
            top = np.maximum(top, sh + math.sqrt(max(t * t - (u * ds) ** 2, 0.0)))
        new = np.where(mask, top, h)
        films.append((key, h.copy(), new.copy(), mask))
        h = new
    return S, films, h


def draw_section(ax, S, films, title, ex=1.0, label_films=True):
    ax.set_facecolor("#05070c")
    ax.fill_between(S * NM, -60, 0, color=COL["sub"], zorder=0)
    ax.text(S[2] * NM, -30, "Si substrate (high resistivity)", color="#8c96b0", fontsize=7, va="center")
    for key, bot, top, mask in films:
        c = COL[key]
        runs = np.flatnonzero(np.diff(np.r_[0, mask.astype(int), 0]))
        for a, b in zip(runs[::2], runs[1::2]):
            seg = slice(a, b)
            ax.fill_between(S[seg] * NM, bot[seg] * NM * ex, top[seg] * NM * ex, color=c,
                            alpha=0.55 if key == "diel" else 1.0, lw=0, zorder=2 + [k for k, *_ in STACK].index(key))
    ax.set_title(title, color="white", fontsize=9, loc="left")
    ax.tick_params(colors="#cfcfcf", labelsize=7)
    for s_ in ax.spines.values():
        s_.set_color("#555555")
    ax.set_xlabel("position along the cut (nm)", color="#cfcfcf", fontsize=7.5)
    ax.set_ylabel("height (nm)" + (f", vertical x{ex:g}" if ex != 1 else ""), color="#cfcfcf", fontsize=7.5)


def cross_sections():
    fig = plt.figure(figsize=(13, 11.5), dpi=170, facecolor=COL["work"])
    fig.text(0.012, 0.985, "QBF-X2 chip, nanoscale   |   to-scale cross-sections (1 nm = 1 nm in x and z), "
             "deposited in process order over the drawn polygons", color="white", fontsize=11, va="top")
    fig.text(0.012, 0.962, "Nb 150 -> granular Al 20 -> Al1 30 -> SiNx 100 -> ion mill + oxidation (AlOx barrier) -> "
             "Al2 30 nm.  Films follow the surface below them; walls are drawn vertical where a film is patterned.",
             color="#bdbdbd", fontsize=7.6, va="top")
    # (a) across the junction and the neighbouring trim capacitor
    bxa = (300.1, 158.4, 302.3, 159.8)
    ga = stack_geoms(bxa)
    p0, p1 = (300.25, 159.075), (302.15, 159.075)
    S, films, h = deposit_profile(ga, p0, p1)
    ax = fig.add_axes([0.06, 0.66, 0.64, 0.24])
    draw_section(ax, S, films, "(a) cut along x at y = 159.075 um: trim capacitor of node 90 (Al1 / SiNx / Al2),\n"
                                "then junction BA0_91 (Al1 / AlOx / Al2)")
    ax.set_xlim(0, S[-1] * NM)
    ax.set_ylim(-60, 260)
    ax.set_aspect("equal")
    xj0 = (301.35 - p0[0]) * NM
    xj1 = (301.55 - p0[0]) * NM
    ax.annotate("", (xj0, 70), (xj1, 70), arrowprops=dict(arrowstyle="<|-|>", color=COL["dim"], lw=0.9))
    ax.text((xj0 + xj1) / 2, 76, "junction 200 nm", color=COL["dim"], fontsize=7.5, ha="center", weight="bold")
    xc = (300.55 - p0[0]) * NM
    ax.annotate("trim capacitor: SiNx between the plates\n(no tunnelling; C to ground)", (xc + 120, 120),
                (xc + 230, 200), color=COL["txt"], fontsize=7.2, arrowprops=dict(arrowstyle="->", color="#bbbbbb", lw=0.7))
    ax.annotate("Al2 bar continues to the GND contact", (1700, 30), (1380, 150), color=COL["txt"], fontsize=7.2,
                arrowprops=dict(arrowstyle="->", color="#bbbbbb", lw=0.7))
    # inset: the barrier at 1:1 near the junction's left edge
    axi = fig.add_axes([0.76, 0.665, 0.21, 0.23])
    draw_section(axi, S, films, "")
    axi.set_xlim(xj0 - 25, xj0 + 55)
    axi.set_ylim(-8, 72)
    axi.set_aspect("equal")
    axi.set_title("zoom at the junction edge (1:1)", color="white", fontsize=7.5, loc="left")
    axi.text(xj0 + 18, 31.2, "AlOx ~1.5 nm", color="white", fontsize=7, va="bottom", weight="bold")
    axi.text(xj0 + 18, 14, "Al1 30 nm", color="white", fontsize=7, va="center")
    axi.text(xj0 + 18, 48, "Al2 30 nm", color="#00241f", fontsize=7, va="center", weight="bold")
    axi.set_xlabel("nm", color="#cfcfcf", fontsize=7)
    axi.set_ylabel("nm", color="#cfcfcf", fontsize=7)
    # (b) down the Al2 lead onto the Nb ground contact
    bxb = (301.0, 156.9, 302.9, 160.5)
    gb = stack_geoms(bxb)
    q0, q1 = (301.95, 157.0), (301.95, 160.4)
    S2, films2, h2 = deposit_profile(gb, q0, q1)
    ax2 = fig.add_axes([0.06, 0.37, 0.9, 0.22])
    draw_section(ax2, S2, films2, "(b) cut along y at x = 301.95 um: Al2 contact on the 150 nm Nb ground "
                                  "(ion-milled, >= 1 um^2, a short) -> Al2 lead -> junction bar -> node plate A0_91")
    ax2.set_xlim(0, S2[-1] * NM)
    ax2.set_ylim(-60, 300)
    ax2.set_aspect("equal")
    ax2.annotate("Al2 climbs the Nb step", ((158.4 - q0[1]) * NM, 160), ((158.4 - q0[1]) * NM + 250, 260),
                 color=COL["txt"], fontsize=7.2, arrowprops=dict(arrowstyle="->", color="#bbbbbb", lw=0.7))
    ax2.annotate("Al1 node plate A0_91 (rail A0)", ((160.0 - q0[1]) * NM, 35), ((160.0 - q0[1]) * NM - 700, 220),
                 color=COL["txt"], fontsize=7.2, arrowprops=dict(arrowstyle="->", color="#bbbbbb", lw=0.7))
    # (c) along the rail: granular-Al inductor under the node plates
    bxc = (300.3, 159.5, 302.0, 160.5)
    gc = stack_geoms(bxc)
    r0, r1 = (300.45, 160.0), (301.85, 160.0)
    S3, films3, h3 = deposit_profile(gc, r0, r1)
    ax3 = fig.add_axes([0.06, 0.08, 0.9, 0.22])
    draw_section(ax3, S3, films3, "(c) cut along the rail at y = 160.0 um: granular-Al inductor LA0_90 (20 nm) "
                                  "running under the Al1 node plates (200 nm contacts at each end)")
    ax3.set_xlim(0, S3[-1] * NM)
    ax3.set_ylim(-60, 160)
    ax3.set_aspect("equal")
    handles = [Patch(color=COL["sub"], label="Si substrate")] + [
        Patch(color=c, alpha=0.55 if k == "diel" else 1.0, label=lab) for k, ld, t, lab, c in STACK]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=7.4, facecolor="#141414", edgecolor="#5a5a5a",
               labelcolor="white", framealpha=1.0, bbox_to_anchor=(0.5, 0.0))
    path = os.path.join(HERE, "nano_cross_sections.png")
    fig.savefig(path, facecolor=COL["work"])
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


# ------------------------------------------------------------------------------------------------ 3D mesh export
def stack_3d(bx, origin, cutaway=None):
    """terraced conformal stack: each film sits on the highest surface below its footprint. Returns per-layer
    (vertices, faces) in um relative to `origin`. `cutaway`: a box removed from Al2 (to show the barrier)."""
    g = stack_geoms(bx)
    if cutaway is not None:
        g["al2"] = g["al2"].difference(box(*cutaway))
    patches = [(box(*bx), 0.0)]
    meshes = {}
    for key, ld, t, lab, c in STACK:
        geom = g[key]
        if geom.is_empty:
            continue
        newp = []
        for R, z in patches:
            inter = R.intersection(geom)
            rest = R.difference(geom)
            if not inter.is_empty and inter.area > 1e-8:
                add_prism(meshes.setdefault(key, ([], [])), inter, z, z + t, origin)
                newp.append((inter, z + t))
            if not rest.is_empty and rest.area > 1e-8:
                newp.append((rest, z))
        merged = {}
        for R, z in newp:
            merged.setdefault(round(z, 6), []).append(R)
        patches = [(unary_union(v), z) for z, v in merged.items()]
    sub = ([], [])
    add_prism(sub, box(*bx), -0.30, 0.0, origin)
    meshes["substrate"] = sub
    return g, meshes


def add_prism(mesh, geom, z0, z1, origin):
    V, F = mesh
    ox, oy = origin
    for poly in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        if poly.geom_type != "Polygon" or poly.area < 1e-8:
            continue
        tris = shapely.constrained_delaunay_triangles(poly)
        for tri in tris.geoms:
            pts = list(tri.exterior.coords)[:3]
            if Polygon(pts).area < 1e-10:
                continue
            for z, rev in ((z1, False), (z0, True)):
                i = len(V)
                V.extend([[p[0] - ox, p[1] - oy, z] for p in pts])
                F.append([i, i + 2, i + 1] if rev else [i, i + 1, i + 2])
        for ring in [poly.exterior, *poly.interiors]:
            cs = list(ring.coords)
            for (xa, ya), (xb, yb) in zip(cs[:-1], cs[1:]):
                i = len(V)
                V.extend([[xa - ox, ya - oy, z0], [xb - ox, yb - oy, z0], [xb - ox, yb - oy, z1], [xa - ox, ya - oy, z1]])
                F.append([i, i + 1, i + 2, i + 3])


def export_mesh():
    bx = (300.15, 156.9, 302.95, 160.55)
    origin = (301.55, 158.7)
    # cut away the half of the Al2 bar over the junction's left side, so the barrier and the sandwich show
    g, meshes = stack_3d(bx, origin, cutaway=(301.20, 158.90, 301.45, 159.25))
    jj = [p for p in (g["barrier"].geoms if hasattr(g["barrier"], "geoms") else [g["barrier"]])
          if abs(p.centroid.x - 301.45) < 0.1][0]
    ox, oy = origin
    anchors = {
        "junction": [jj.centroid.x - ox, jj.centroid.y - oy, 0.032],
        "al1_plate": [302.6 - ox, 160.0 - oy, 0.03],
        "gral": [301.05 - ox, 160.0 - oy, 0.02],
        "al2_lead": [301.80 - ox, 159.075 - oy, 0.03],
        "al2_contact": [301.95 - ox, 158.1 - oy, 0.18],
        "nb": [301.2 - ox, 158.2 - oy, 0.15],
        "diel": [302.28 - ox, 159.52 - oy, 0.10],
        "substrate": [301.78 - ox, 159.55 - oy, 0.0],
    }
    out = dict(units="um", origin_block_um=origin, window_block_um=bx,
               layers={k: dict(vertices=v[0], faces=v[1]) for k, v in meshes.items()}, anchors=anchors,
               thickness_um={k: t for k, ld, t, *_ in STACK})
    path = os.path.join(HERE, "nano_cell_mesh.json")
    json.dump(out, open(path, "w"))
    print("wrote", os.path.relpath(path, ROOT), {k: len(v[1]) for k, v in meshes.items()}, "faces")


def annotate_render():
    src = os.path.join(HERE, "nano_cell_3d_raw.png")
    proj = json.load(open(os.path.join(HERE, "nano_cell_3d_anchors.json")))
    img = plt.imread(src)
    h, w = img.shape[:2]
    fig = plt.figure(figsize=(w / 170, h / 170 + 0.55), dpi=170, facecolor=COL["work"])
    ax = fig.add_axes([0, 0, 1, h / (h + 0.55 * 170)])
    ax.imshow(img)
    ax.set_axis_off()
    jv = junction_values(0.0384)
    labels = {
        "junction": (f"Josephson junction BA0_91: Al1 / AlOx / Al2\n200 x 192 nm, I_c {jv['Ic_nA']:.0f} nA, "
                     f"E_J/h {jv['EJ_GHz']:.0f} GHz\n(Al2 cut away; the ~1.5 nm barrier glows)", (-0.17, 0.17)),
        "al1_plate": ("Al1 node plate A0_91 (30 nm)", (-0.12, -0.13)),
        "gral": ("granular-Al inductor LA0_90\n(20 nm, 0.65 nH)", (0.02, -0.17)),
        "al2_lead": ("Al2 bar and lead to GND (30 nm)", (0.12, -0.1)),
        "al2_contact": ("Al2-on-Nb ground contact\n(ion-milled, 1.0 x 1.1 um)", (-0.08, 0.18)),
        "nb": ("Nb ground plane (150 nm)", (-0.05, 0.16)),
        "diel": ("SiNx trim capacitor (100 nm)", (0.12, -0.16)),
        "substrate": ("Si substrate", (-0.02, -0.08)),
    }
    for key, (txt, (dx, dy)) in labels.items():
        if key not in proj:
            continue
        px, py = proj[key]
        tx, ty = px + dx * w, py + dy * h
        ax.annotate(txt, (px, py), (tx, ty), color="white", fontsize=7.6, ha="center", va="center",
                    arrowprops=dict(arrowstyle="-|>", color="white", lw=0.8),
                    bbox=dict(boxstyle="round,pad=0.25", fc="#000000", ec="#888888", alpha=0.72))
    fig.text(0.012, 0.99, "QBF-X2 chip, nanoscale   |   one rail cell in 3D at true film thickness (Blender Cycles), "
             "2.8 x 3.65 um window", color="white", fontsize=10, va="top")
    fig.text(0.012, 0.965, "Geometry: circuits/qbfx2_layout.gds. Heights: Nb 150, grAl 20, Al1 30, SiNx 100, Al2 30 nm, "
             "stacked in process order. The ~1.5 nm AlOx barrier is drawn glowing so it can be seen.",
             color="#bdbdbd", fontsize=7.2, va="top")
    path = os.path.join(HERE, "nano_cell_3d.png")
    fig.savefig(path, facecolor=COL["work"])
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    if "--annotate" in sys.argv:
        annotate_render()
    else:
        rail_junction_view()
        middle_junction_view()
        cross_sections()
        export_mesh()
