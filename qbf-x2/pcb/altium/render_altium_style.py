"""Altium-style PCB-editor views of the QBF-X2 carrier, drawn from the routed KiCad board (pcbnew API).

Colours follow Altium's default 2D scheme: black board area on a dark-grey workspace, Top Layer red, Mid-Layer 2
(the In2 DC stripline) orange, Multi-Layer pads and vias silver with dark drill holes, Top Overlay yellow, Top Solder
openings purple, board outline magenta. Net names are printed along the tracks and on the pads, pad numbers on the
pads, designators in the overlay colour, as Altium shows them at working zoom.

Every shape comes from the board file: tracks and arcs (buffered to their width), pad polygons, filled zones, vias,
footprint silkscreen and the board's own silkscreen text. KiCad 7.0's Python bindings do not wrap the ERROR_LOC enum
that TransformShapeToPolygon needs, so tracks, arcs, vias and silkscreen are rebuilt here from their primitives.
The inner ground planes (In1, In3, In4, the In2 pour) and the bottom-side ground pour are hidden, as one would hide
them in Altium to look at the routing.  Output: pcb/altium/views/altium_style_*.png"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Patch, PathPatch, Circle
from matplotlib.path import Path
import pcbnew
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union, polygonize

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(os.path.dirname(HERE), "qbfx2_carrier.kicad_pcb")
sys.path.insert(0, os.path.dirname(HERE))
import carrier_params as CP  # noqa: E402  (revision letter, pair names)
OUT = os.path.join(HERE, "views")
os.makedirs(OUT, exist_ok=True)
MM = 1e-6

COL = dict(work="#2a2a2a", board="#000000", top="#ff0000", top_edge="#ff6060", pour="#7c0000", pour_edge="#d01818",
           mid2="#ff9a1a", multi="#c0c0c0", multi_edge="#ffffff", hole="#3a3a3a", hole_edge="#808080",
           silk="#ffff00", mask="#b040ff", edge="#ff00ff", net="#f2f2f2", padnum="#ffffff")

b = pcbnew.LoadBoard(BOARD)
L_F, L_IN2 = b.GetLayerID("F.Cu"), b.GetLayerID("In2.Cu")
L_SILK, L_EDGE, L_MASK = b.GetLayerID("F.SilkS"), b.GetLayerID("Edge.Cuts"), b.GetLayerID("F.Mask")


def xy(v):                                           # KiCad (nm, y down) -> mm, y up
    return v.x * MM, -v.y * MM


def arc_points(s, m, e, n=48):
    """points on the circular arc start -> mid -> end"""
    (x1, y1), (x2, y2), (x3, y3) = s, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        return [s, e]
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1, a2, a3 = (math.atan2(y - uy, x - ux) for x, y in (s, m, e))

    def ccw(a, b_):
        return (b_ - a) % (2 * math.pi)
    sweep = ccw(a1, a3)
    if ccw(a1, a2) > sweep:                          # the mid point is on the other side: go clockwise
        sweep = sweep - 2 * math.pi
    pts = [(ux + r * math.cos(a1 + sweep * k / n), uy + r * math.sin(a1 + sweep * k / n)) for k in range(n + 1)]
    pts[0], pts[-1] = s, e                           # exact end points, so outlines close
    return pts


def thick(points, w):
    return LineString(points).buffer(w / 2, quad_segs=8) if len(points) > 1 else Polygon()


def polyset(ps, offset=None, rot_deg=0.0):
    """SHAPE_POLY_SET -> shapely geometry (outlines with holes); optional footprint-local -> board transform"""
    c, s_ = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))

    def tr(p):
        x, y = p.x, p.y
        if offset is not None:                       # KiCad RotatePoint convention (y down), then translate
            x, y = x * c + y * s_, -x * s_ + y * c
            x, y = x + offset.x, y + offset.y
        return x * MM, -y * MM
    polys = []
    for i in range(ps.OutlineCount()):
        ol = ps.Outline(i)
        shell = [tr(ol.CPoint(j)) for j in range(ol.PointCount())]
        holes = [[tr(ps.Hole(i, h).CPoint(j)) for j in range(ps.Hole(i, h).PointCount())] for h in range(ps.HoleCount(i))]
        if len(shell) >= 3:
            polys.append(Polygon(shell, [hh for hh in holes if len(hh) >= 3]).buffer(0))
    return unary_union(polys) if polys else Polygon()


def shape_geom(g, fp=None):
    """board or footprint graphic (segment/arc/circle/rect/poly) -> stroked shapely geometry"""
    w = max(g.GetWidth() * MM, 0.08)
    st = g.GetShape()
    if st == pcbnew.SHAPE_T_SEGMENT:
        return thick([xy(g.GetStart()), xy(g.GetEnd())], w)
    if st == pcbnew.SHAPE_T_ARC:
        return thick(arc_points(xy(g.GetStart()), xy(g.GetArcMid()), xy(g.GetEnd())), w)
    if st == pcbnew.SHAPE_T_CIRCLE:
        cx, cy = xy(g.GetCenter())
        r = g.GetRadius() * MM
        ring = [(cx + r * math.cos(2 * math.pi * k / 64), cy + r * math.sin(2 * math.pi * k / 64)) for k in range(65)]
        return thick(ring, w)
    if st == pcbnew.SHAPE_T_RECT:
        (x0, y0), (x1, y1) = xy(g.GetStart()), xy(g.GetEnd())
        return thick([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], w)
    if st == pcbnew.SHAPE_T_POLY:
        if fp is not None:
            geo = polyset(g.GetPolyShape(), fp.GetPosition(), fp.GetOrientationDegrees())
        else:
            geo = polyset(g.GetPolyShape())
        return geo.buffer(w / 2) if g.IsFilled() else geo.boundary.buffer(w / 2)
    return Polygon()


# ------------------------------------------------------------------------------------------- collect the board once
tracks = {"F": [], "IN2": []}
labels = []                                          # (x, y, angle, text, kind, size, width)
for t in b.GetTracks():
    cls = t.GetClass()
    if cls == "PCB_VIA":
        continue
    key = "F" if t.GetLayer() == L_F else "IN2" if t.GetLayer() == L_IN2 else None
    if key is None:
        continue
    w = t.GetWidth() * MM
    if cls == "PCB_ARC":
        pts = arc_points(xy(t.GetStart()), xy(t.GetMid()), xy(t.GetEnd()))
    else:
        pts = [xy(t.GetStart()), xy(t.GetEnd())]
    tracks[key].append(thick(pts, w))
    if t.GetNetname() and cls == "PCB_TRACK":
        (x0, y0), (x1, y1) = pts
        L = math.hypot(x1 - x0, y1 - y0)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        ang = ang + 180 if ang > 90 else ang - 180 if ang <= -90 else ang
        labels.append(((x0 + x1) / 2, (y0 + y1) / 2, ang, t.GetNetname(), "track_" + key, L, w))
geo = {k: unary_union(v) for k, v in tracks.items()}

pour = Polygon()
for z in b.Zones():
    if z.IsOnLayer(L_F) and z.GetNetname():
        pour = unary_union([pour, polyset(z.GetFilledPolysList(L_F))])

smd, multi, holes, npth = [], [], [], []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        attr = pad.GetAttribute()
        p = xy(pad.GetPosition())
        size = min(pad.GetSize().x, pad.GetSize().y) * MM
        if attr == pcbnew.PAD_ATTRIB_NPTH:
            npth.append((p[0], p[1], pad.GetDrillSize().x * MM / 2))
            continue
        g = polyset(pad.GetEffectivePolygon())
        (multi if attr == pcbnew.PAD_ATTRIB_PTH else smd).append(g)
        bx0, by0, bx1, by1 = g.bounds
        if pad.GetDrillSize().x > 0:
            holes.append((p[0], p[1], pad.GetDrillSize().x * MM / 2))
        if pad.GetNumber():
            labels.append((p[0], p[1], 0, pad.GetNumber(), "padnum", size, 0))
        if pad.GetNetname():
            labels.append((p[0], p[1], 0, pad.GetNetname(), "padnet", size, (bx1 - bx0, by1 - by0)))
    if fp.Reference().IsVisible():                   # hidden references (SMP jacks: designator is in the silk)
        labels.append((*xy(fp.Reference().GetPosition()), 0, fp.GetReference(), "ref", 0, 0))
vias = [(*xy(t.GetPosition()), t.GetWidth() * MM / 2, t.GetDrillValue() * MM / 2)
        for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]

silk, edge, mask, silk_text = [], [], [], []
for fp in b.GetFootprints():
    for g in fp.GraphicalItems():
        if g.GetLayer() == L_SILK and g.GetClass() in ("MGRAPHIC", "FP_SHAPE"):
            silk.append(shape_geom(g, fp))
for d in b.GetDrawings():
    lay = d.GetLayer()
    if d.GetClass() == "PCB_SHAPE":
        if lay == L_EDGE:
            st = d.GetShape()
            pts = (arc_points(xy(d.GetStart()), xy(d.GetArcMid()), xy(d.GetEnd())) if st == pcbnew.SHAPE_T_ARC
                   else [xy(d.GetStart()), xy(d.GetEnd())])
            edge.append(LineString(pts))
        elif lay == L_SILK:
            silk.append(shape_geom(d))
        elif lay == L_MASK and d.GetShape() == pcbnew.SHAPE_T_POLY:
            mask.append(polyset(d.GetPolyShape()))
    elif d.GetClass() == "PCB_TEXT" and lay == L_SILK:
        silk_text.append((*xy(d.GetPosition()), d.GetTextAngleDegrees(), d.GetText(), d.GetTextHeight() * MM))
silk = unary_union(silk)
outline = unary_union(edge)
faces = sorted(polygonize(outline), key=lambda g: -g.area)          # outer board shape first, then any cut-outs
board_area = faces[0].difference(unary_union(faces[1:])) if len(faces) > 1 else faces[0]
edge_geo = outline.buffer(0.07)


# ---------------------------------------------------------------------------------------------------- drawing helpers
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


def fill(ax, g, fc, ec="none", lw=0.0, z=1, clip=None, alpha=1.0):
    if g is None or g.is_empty:
        return
    if clip is not None:
        g = g.intersection(clip)
        if g.is_empty:
            return
    pth = as_path(g)
    if pth is not None:
        ax.add_patch(PathPatch(pth, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z, alpha=alpha))


def view(name, title, bx, width_in, padnets=False, track_min=None, ref_size=6.5, show_track_labels=True,
         padnum_min=None, notes=None, annot=None):
    """annot: [(x, y, dx, dy, text)] call-outs (arrow from (x + dx, y + dy) to (x, y)) in board coordinates"""
    x0, y0, x1, y1 = bx
    span, hgt = x1 - x0, y1 - y0
    band = 0.075 * hgt
    title_frac = 0.045
    figsize = (width_in, width_in * (hgt + band) / span / (1 - title_frac))
    clip = box(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5)
    fig = plt.figure(figsize=figsize, dpi=170, facecolor=COL["work"])
    ax = fig.add_axes([0, 0, 1, 1 - title_frac])
    ax.set_facecolor(COL["work"])
    fill(ax, board_area, COL["board"], z=0.5, clip=clip)
    fill(ax, pour, COL["pour"], ec=COL["pour_edge"], lw=0.35, z=2, clip=clip)
    fill(ax, geo["IN2"], COL["mid2"], ec=COL["mid2"], lw=0.2, z=2.5, clip=clip, alpha=0.88)
    fill(ax, geo["F"], COL["top"], z=3, clip=clip)
    fill(ax, unary_union(smd), COL["top"], ec=COL["top_edge"], lw=0.4, z=3.2, clip=clip)
    fill(ax, unary_union(multi), COL["multi"], ec=COL["multi_edge"], lw=0.3, z=4, clip=clip)
    vis = [(cx, cy, r, d) for cx, cy, r, d in vias if x0 - 1 < cx < x1 + 1 and y0 - 1 < cy < y1 + 1]
    ax.add_collection(PatchCollection([Circle((cx, cy), r) for cx, cy, r, d in vis], facecolor=COL["multi"],
                                      edgecolor="none", zorder=4.2))
    hl = [(cx, cy, r) for cx, cy, r in holes if x0 - 3 < cx < x1 + 3 and y0 - 3 < cy < y1 + 3]
    hl += [(cx, cy, d) for cx, cy, r, d in vis]
    ax.add_collection(PatchCollection([Circle((cx, cy), r) for cx, cy, r in hl], facecolor=COL["hole"],
                                      edgecolor=COL["hole_edge"], linewidth=0.25, zorder=4.4))
    np_ = [(cx, cy, r) for cx, cy, r in npth if x0 - 3 < cx < x1 + 3 and y0 - 3 < cy < y1 + 3]
    ax.add_collection(PatchCollection([Circle((cx, cy), r) for cx, cy, r in np_], facecolor="#151515",
                                      edgecolor=COL["multi"], linewidth=0.8, zorder=4.4))
    for m in mask:
        fill(ax, m.boundary.buffer(span / 2500), COL["mask"], z=4.6, clip=clip, alpha=0.9)
    fill(ax, silk, COL["silk"], z=5, clip=clip)
    fill(ax, edge_geo, COL["edge"], z=5.2, clip=clip)
    pt = 72 * figsize[0] / span                      # points per mm on this figure
    for (x, y, ang, txt, h) in silk_text:
        if x0 < x < x1 and y0 < y < y1:
            ax.text(x, y, txt, color=COL["silk"], fontsize=max(3.0, h * pt * 0.72), rotation=ang, ha="center",
                    va="center", zorder=6, family="DejaVu Sans Mono", weight="bold")
    track_min = track_min if track_min is not None else span / 14
    for (x, y, ang, txt, kind, size, w) in labels:
        if not (x0 < x < x1 and y0 < y < y1):
            continue
        if kind.startswith("track") and show_track_labels and size >= track_min:
            fs = max(3.2, min(6.5, w * pt * 0.62))
            ax.text(x, y, txt, color=COL["net"], fontsize=fs, rotation=ang, ha="center", va="center", zorder=7,
                    family="DejaVu Sans Mono", clip_on=True,
                    bbox=dict(boxstyle="square,pad=0.08", fc="#000000", ec="none", alpha=0.55))
        elif kind == "padnum" and size >= (padnum_min if padnum_min is not None else span / 160):
            ax.text(x - (size * 0.0 if True else 0), y + (size * 0.16 if padnets else 0), txt, color=COL["padnum"],
                    fontsize=max(3.4, min(9, size * pt * 0.42)), ha="center", va="center", zorder=8, weight="bold",
                    clip_on=True)
        elif kind == "padnet" and padnets and size >= span / 160:
            pw, ph = w
            tall = ph > 1.3 * pw
            long_pt = (ph if tall else pw) * pt
            fs = max(2.4, min(5.5, 0.92 * long_pt / (0.62 * max(len(txt), 1))))
            off = (0, 0) if tall else (0, -size * 0.22)
            ax.text(x + (size * 0.18 if tall else 0), y + off[1], txt, color="#f4f4f4", fontsize=fs,
                    rotation=90 if tall else 0, ha="center", va="center", zorder=8, clip_on=True,
                    family="DejaVu Sans Mono")
        elif kind == "ref":
            ax.text(x, y, txt, color=COL["silk"], fontsize=ref_size, ha="center", va="center", zorder=8,
                    weight="bold", clip_on=True)
    for (ax_, ay_, dx_, dy_, txt) in (annot or []):
        ax.annotate(txt, xy=(ax_, ay_), xytext=(ax_ + dx_, ay_ + dy_), color="#00e5ff", fontsize=6.8, zorder=9,
                    ha="center", va="center", family="DejaVu Sans",
                    bbox=dict(boxstyle="round,pad=0.25", fc="#0b1a22", ec="#00e5ff", lw=0.6, alpha=0.92),
                    arrowprops=dict(arrowstyle="-|>", color="#00e5ff", lw=0.8, shrinkA=2, shrinkB=1))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0 - band, y1)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.add_patch(plt.Rectangle((x0, y0 - band), span, band, facecolor=COL["work"], edgecolor="none", zorder=10))
    fig.text(0.008, 0.992, f"QBF-X2 carrier rev {CP.PROJECT['rev']}   |   " + title, color="#ffffff", fontsize=8.8,
             va="top")
    if notes:
        fig.text(0.008, 0.992 - 0.5 * title_frac, notes, color="#bdbdbd", fontsize=6.4, va="top")
    handles = [Patch(color=COL["top"], label="Top Layer (F.Cu): RF GCPW, gate/DC lines, lands"),
               Patch(color=COL["pour"], label="Top Layer GND polygon pour"),
               Patch(color=COL["mid2"], label="Mid-Layer 2 (In2): DC stripline"),
               Patch(color=COL["multi"], label="Multi-Layer: TH pads, vias"),
               Patch(color=COL["silk"], label="Top Overlay"),
               Patch(color=COL["mask"], label="Top Solder (mask openings)"),
               Patch(color=COL["edge"], label="Board outline")]
    leg = ax.legend(handles=handles, loc="lower right", ncol=4, fontsize=5.8, facecolor="#141414",
                    edgecolor="#5a5a5a", labelcolor="white", framealpha=1.0, borderaxespad=0.3)
    leg.set_zorder(12)
    nice = min([0.2, 0.5, 1, 2, 5, 10], key=lambda s_: abs(s_ - span / 7))
    yb = y0 - band * 0.6
    ax.plot([x0 + span * 0.02, x0 + span * 0.02 + nice], [yb, yb], color="white", lw=2.4, zorder=11,
            solid_capstyle="butt")
    ax.text(x0 + span * 0.02 + nice / 2, yb + band * 0.14, f"{nice:g} mm", color="white", fontsize=7,
            ha="center", va="bottom", zorder=11)
    path = os.path.join(OUT, f"altium_style_{name}.png")
    fig.savefig(path, facecolor=COL["work"])
    plt.close(fig)
    print("wrote", os.path.relpath(path, os.path.dirname(HERE)))
    return path


def fp_pos(ref):
    return xy(next(f for f in b.GetFootprints() if f.GetReference() == ref).GetPosition())


if __name__ == "__main__":
    X0, Y0, X1, Y1 = board_area.bounds
    cx, cy = fp_pos("U1")
    view("board", "Top view (Top Layer + Mid-Layer 2 + Multi-Layer + Top Overlay); inner GND planes hidden",
         (X0 - 1.5, Y0 - 1.5, X1 + 1.5, Y1 + 1.5), 11, track_min=4.0, ref_size=6.0, padnum_min=1.0)
    n_lands = sum(1 for f in b.GetFootprints() if f.GetReference() == "U1" for _ in f.Pads())
    view("die_window", f"Die window around U1: {n_lands} bond lands (8 P/N pairs on the 0.5 mm die pitch), GCPW "
         "fan-out, GND ring, stitching vias", (cx - 7.5, cy - 7.5, cx + 7.5, cy + 7.5), 11, padnets=True,
         track_min=1.0, padnum_min=0.25)
    jx, jy = fp_pos("J1")
    view("smp_launch", "J1 SMP launch (TRAP_A0_P): centre land, 4 GND legs, via cage, via fence along the GCPW",
         (jx - 5.6, jy - 3.4, jx + 4.2, jy + 4.2), 9, padnets=True, track_min=0.5, padnum_min=0.2)

    # close-up of one differential pair (ACC_A0): breakout, bend B1, opening, bump on the outer leg, diagonal,
    # bend B2 and the bumps on the inner leg; call-outs from the build model (reports/build_model.json)
    model = json.load(open(os.path.join(os.path.dirname(HERE), "reports", "build_model.json")))
    pr = model["diff"]["pairs"]["ACC_A0"]
    V = [(cx + v[0], cy + v[1]) for v in pr["vertices"]]
    br = CP.DIFF["bump_r"]
    arcs = []                                       # bump arcs of this pair: radius = bump_r, middle arc of 3
    for t in b.GetTracks():
        if t.GetClass() == "PCB_ARC" and t.GetNetname() in (pr["P"], pr["N"]) and \
                abs(t.GetRadius() * MM - br) < 0.002 and abs(abs(t.GetAngle().AsDegrees()) - 2 * [
                    q["arc_deg"] for q in pr["bumps"] if q["leg"] == t.GetNetname()][0]) < 0.5:
            arcs.append((xy(t.GetMid()), t.GetNetname()))
    extra = {q["leg"]: (q["extra_each"], q["n"]) for q in pr["bumps"]}
    ann = []
    for net in sorted({n_ for _, n_ in arcs}):     # one call-out per bumped leg, arrow to its first bump
        pts = [p_ for p_, n_ in arcs if n_ == net]
        e_, n_b = extra[net]
        (mx, my) = min(pts, key=lambda q: -q[0])
        lbl = (f"tuning bump on {net}\n+{e_:.3f} mm" if n_b == 1 else
               f"{n_b} tuning bumps on {net}\n+{e_:.3f} mm each")
        ann.append((mx, my, -2.4, -1.3) + (lbl,) if net.endswith("_P") else (mx, my, -0.6, -1.9) + (lbl,))
    bends = pr["bends"]
    ann.append((V[1][0], V[1][1] + 0.3, -1.6, -1.5, f"B1 {bends[0]['theta_deg']:+.0f} deg at pitch {bends[0]['c']:.2f}\n"
                f"{bends[0]['inner_net']} -{bends[0]['mismatch']:.3f} mm"))
    ann.append((V[2][0], V[2][1], 1.9, 1.3, f"B2 {bends[1]['theta_deg']:+.0f} deg at pitch {bends[1]['c']:.2f}\n"
                f"{bends[1]['inner_net']} -{bends[1]['mismatch']:.3f} mm"))
    xs_ = [v[0] for v in V[1:4]]
    ys_ = [v[1] for v in V[:4]]
    lp = model["rf"][pr["P"]]["length"]
    ln_ = model["rf"][pr["N"]]["length"]
    view("diff_pair", f"Differential pair ACC_A0: {pr['P']} / {pr['N']}, edge-coupled GCPW, no GND between the legs, "
         "tuning bumps next to each bend",
         (min(xs_) - 3.9, min(ys_) - 2.4, max(xs_) + 3.4, max(ys_) + 2.4), 11, padnets=False, track_min=0.9,
         notes=(f"breakout w {CP.DIFF['w_bo']:.2f} / gap {CP.DIFF['s_bo']:.2f} mm (die pad pitch) -> opening -> routed "
                f"w {CP.DIFF['w']:.2f} / gap {CP.DIFF['s']:.2f} mm; concentric bends; "
                f"L_P {lp:.4f} mm, L_N {ln_:.4f} mm"), annot=ann)
    xs = [fp_pos(r)[0] for r in ("J11", "R1", "R16", "C1", "C12")]
    ys = [fp_pos(r)[1] for r in ("J11", "R1", "R16", "C1", "C12")]
    view("dc_filters", "DC filter bank: 0603 thin-film R and C0G C ladders between micro-D J11 and the gate/load lines",
         (min(xs) - 3.5, min(ys) - 3.5, max(xs) + 3.5, max(ys) + 3.5), 12, padnets=True, track_min=0.6,
         padnum_min=0.2)
