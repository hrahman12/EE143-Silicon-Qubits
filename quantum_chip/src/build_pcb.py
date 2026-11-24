"""Generate the 6-layer RF carrier PCB as a native KiCad 7 board, then let KiCad itself
fill zones, run DRC and export STEP / Gerber / drill / SVG.

Geometry is computed here in a Y-up, board-centred frame (mm) and written to
  out/pcb_model.json   (the routed design: pads, tracks, vias, connectors - used by the 3D pipeline)
  out/rf_carrier.kicad_pcb
"""
import json
import math
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from design_params import PCB, STACKUP, DIE
from rf_calc import solve_gcpw_width, gcpw_z0, solve_stripline_width, stripline_z0

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
X0, Y0 = 150.0, 100.0          # KiCad page offset of board centre

H_TOP = dict(STACKUP_ := {n: t for n, _, t, _ in STACKUP})["diel1"]
GAP = 0.20
W_RF = round(solve_gcpw_width(GAP, H_TOP, 3.55), 2)              # top + bottom GCPW
B_STRIP = STACKUP_["diel2"] + STACKUP_["In2.Cu"] + STACKUP_["diel3"]
W_SL = round(solve_stripline_width(STACKUP_["In2.Cu"], B_STRIP, 3.52), 2)
SL_CLR = 0.35                                                    # stripline to coplanar ground on In2
HALF = PCB["size_mm"] / 2
WIN = PCB["window_mm"] / 2


def U():
    return str(uuid.uuid4())


def k(x, y):
    """board frame (Y up, mm) -> KiCad page coordinates (Y down)"""
    return f"{X0 + x:.4f} {Y0 - y:.4f}"


# ------------------------------------------------------------------ nets
die = json.load(open(os.path.join(OUT, "die_ports.json")))
NETS = ["", "GND"] + [p["net"] for p in die["ports"]]
NETN = {n: i for i, n in enumerate(NETS)}
NET = {p["kqc_port_id"]: p["net"] for p in die["ports"]}   # routing is fixed per pad position

pads, tracks, vias, fps, mask_open, texts = [], [], [], [], [], []


def track(layer, net, w, pts):
    tracks.append(dict(layer=layer, net=net, w=w, pts=[list(map(float, p)) for p in pts]))


def via(x, y, net, kind="through", drill=None, size=None, layers=("F.Cu", "B.Cu")):
    if kind == "through":
        drill, size = drill or PCB["via_drill_mm"], size or PCB["via_pad_mm"]
    else:
        drill, size = drill or PCB["blind_drill_mm"], size or PCB["blind_pad_mm"]
    vias.append(dict(x=x, y=y, net=net, kind=kind, drill=drill, size=size, layers=list(layers)))


# ------------------------------------------------------------------ die-side bond pads
def die_to_board(p):
    return ((p[0] - DIE["size_um"] / 2) / 1000.0, (p[1] - DIE["size_um"] / 2) / 1000.0)


pad_in = WIN + PCB["bondpad_setback_mm"]
pad_out = pad_in + PCB["bondpad_len_mm"]
bond = {}
for p in die["ports"]:
    ux, uy = p["outward"]
    dx, dy = die_to_board(p["pad_center_um"])
    lat = dy if ux else dx                                  # lateral coordinate along die edge
    c = (pad_in + pad_out) / 2

    def at(s, lat=lat, ux=ux, uy=uy):
        return (ux * s + (0 if ux else lat), uy * s + (lat if ux else 0))

    bond[p["net"]] = dict(center=at(c), inner=at(pad_in), outer=at(pad_out), u=(ux, uy), lat=lat,
                          die_pad=(dx, dy), at=at)
    pads.append(dict(net=p["net"], layer="F.Cu", shape="rect", center=at(c),
                     size=(PCB["bondpad_len_mm"], W_RF) if ux else (W_RF, PCB["bondpad_len_mm"]),
                     role="bond_pad"))


# ------------------------------------------------------------------ connectors
def sma_edge(ref, net, x, y, rot):
    """Generic 4-ground-pad end-launch SMA (e.g. 0.062in board style). Local frame: mating axis to -y_local."""
    fps.append(dict(ref=ref, kind="SMA_EDGE", net=net, x=x, y=y, rot=rot))


def smp_vert(ref, net, x, y):
    fps.append(dict(ref=ref, kind="SMP_VERT_BOTTOM", net=net, x=x, y=y, rot=0))


E = HALF
EP = HALF - 1.35     # tracks end at the SMA pin-pad centre
# top-layer GCPW routes: (net, connector ref, path points in board frame)
b = bond
routes_top = {
    NET[10]: [b[NET[10]]["outer"], (-8.0, 0.6), (-13.4, 6.0), (-EP, 6.0)],
    NET[9]: [b[NET[9]]["outer"], (-8.0, -0.6), (-13.4, -6.0), (-EP, -6.0)],
    NET[7]: [b[NET[7]]["outer"], (8.0, 0.6), (13.4, 6.0), (EP, 6.0)],
    NET[8]: [b[NET[8]]["outer"], (8.0, -0.6), (13.4, -6.0), (EP, -6.0)],
    NET[2]: [b[NET[2]]["outer"], (-1.8, 9.0), (-6.0, 13.2), (-6.0, EP)],
    NET[5]: [b[NET[5]]["outer"], (1.8, 9.0), (6.0, 13.2), (6.0, EP)],
}
conn_of = {NET[10]: ("J1", -E, 6.0, 90), NET[9]: ("J2", -E, -6.0, 90),
           NET[7]: ("J3", E, 6.0, -90), NET[8]: ("J4", E, -6.0, -90),
           NET[2]: ("J5", -6.0, E, 0), NET[5]: ("J6", 6.0, E, 0)}
for net, pts in routes_top.items():
    track("F.Cu", net, W_RF, pts)
    ref, x, y, r = conn_of[net]
    sma_edge(ref, net, x, y, r)

# bottom-SMP nets (DC bias + control flux): bond pad -> blind via (F.Cu-In2.Cu) -> In2 stripline -> blind via (In2.Cu-B.Cu) -> B.Cu GCPW -> SMP
flux = {
    NET[1]: dict(path=[(-3.0, 7.0), (-7.5, 7.0), (-7.5, -11.5)], smp=(-7.5, -14.5), ref="J7"),
    NET[3]: dict(path=[(-0.6, 8.2), (-8.7, 8.2), (-8.7, -9.5), (-11.5, -12.3)], smp=(-11.5, -14.5), ref="J8"),
    NET[4]: dict(path=[(0.6, 8.2), (8.7, 8.2), (8.7, -9.5), (11.5, -12.3)], smp=(11.5, -14.5), ref="J9"),
    NET[6]: dict(path=[(3.0, 7.0), (7.5, 7.0), (7.5, -11.5)], smp=(7.5, -14.5), ref="J10"),
}
for net, f in flux.items():
    bb = bond[net]
    v1 = bb["at"](pad_out + 0.40)
    track("F.Cu", net, W_RF, [bb["outer"], v1])
    via(*v1, net, kind="blind", layers=("F.Cu", "In2.Cu"))
    sl = [v1] + f["path"]
    track("In2.Cu", net, W_SL, sl)
    v2 = f["path"][-1]
    via(*v2, net, kind="blind", layers=("In2.Cu", "B.Cu"))
    track("B.Cu", net, W_RF, [v2, f["smp"]])
    smp_vert(f["ref"], net, *f["smp"])
    f["v1"], f["v2"] = v1, v2

# ------------------------------------------------------------------ connector pad geometry
SMA = dict(pullback=0.15, sig=(0.60, 2.40), sig_off=-1.0, gnd=(1.40, 3.00), gnd_dx=2.15, gnd_off=-1.30)
SMP = dict(sig_d=0.90, gnd=(1.0, 1.0), gnd_d=1.30)


def rot_pt(lx, ly, rot, x, y):
    """local footprint frame (Y up) rotated CCW by rot deg, translated to (x,y)"""
    a = math.radians(rot)
    return (x + lx * math.cos(a) - ly * math.sin(a), y + lx * math.sin(a) + ly * math.cos(a))


for f in fps:
    if f["kind"] == "SMA_EDGE":
        # pads; local +y = into board? we define local -y = outward (mating) so pads at negative... use +y inward
        pads.append(dict(net=f["net"], layer="F.Cu", shape="rect", fp=f["ref"],
                         center=rot_pt(0, -SMA["sig"][1] / 2 - SMA["pullback"], f["rot"], f["x"], f["y"]),
                         size=SMA["sig"], rot=f["rot"], role="sma_pin"))
        for s in (-1, 1):
            for lay in ("F.Cu", "B.Cu"):
                pads.append(dict(net="GND", layer=lay, shape="rect", fp=f["ref"],
                                 center=rot_pt(s * SMA["gnd_dx"], -SMA["gnd"][1] / 2 - SMA["pullback"], f["rot"], f["x"], f["y"]),
                                 size=SMA["gnd"], rot=f["rot"], role="sma_gnd"))
    else:
        pads.append(dict(net=f["net"], layer="B.Cu", shape="circle", fp=f["ref"], center=(f["x"], f["y"]),
                         size=(SMP["sig_d"], SMP["sig_d"]), role="smp_pin"))
        for sx in (-1, 1):
            for sy in (-1, 1):
                pads.append(dict(net="GND", layer="B.Cu", shape="rect", fp=f["ref"],
                                 center=(f["x"] + sx * SMP["gnd_d"], f["y"] + sy * SMP["gnd_d"]),
                                 size=SMP["gnd"], role="smp_gnd"))


# NOTE on the SMA footprint frame: KiCad rotation is CCW; local "north" (+y board) is the mating
# side for rot=0, i.e. the connector at the top edge points up/outward. The signal pad spans
# [-2.4, 0] along local y, i.e. from the edge inward. Since the board frame here is Y-up and the
# footprint is placed at the edge, local -y points into the board for rot=0. Good.

# ------------------------------------------------------------------ ground ring + stitching
ring_in, ring_out = WIN + PCB["bondpad_setback_mm"], WIN + PCB["bondpad_setback_mm"] + PCB["gnd_ring_w_mm"]
mask_open.append(dict(outer=pad_out - 0.05, inner=WIN))   # opening stops just short of the RF tracks         # exposed ENIG band around window


def seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def clear_of_signals(x, y, r):
    for t in tracks:
        for a, b2 in zip(t["pts"][:-1], t["pts"][1:]):
            need = r + t["w"] / 2 + (GAP + 0.10 if t["layer"] != "In2.Cu" else SL_CLR + 0.05)
            if seg_dist(x, y, a, b2) < need:
                return False
    for p in pads:
        if p["net"] != "GND":
            if math.hypot(x - p["center"][0], y - p["center"][1]) < r + max(p["size"]) / 2 + GAP + 0.05:
                return False
    for v in vias:
        if v["net"] != "GND" and math.hypot(x - v["x"], y - v["y"]) < r + v["size"] / 2 + 0.25:
            return False
    for f in fps:                                      # keep stitching out of connector bodies
        if f["kind"] == "SMA_EDGE":
            lx = [rot_pt(sx, sy, f["rot"], f["x"], f["y"]) for sx, sy in ((-3.3, 0), (3.3, 0), (-3.3, -3.3), (3.3, -3.3))]
            xs, ys = [q[0] for q in lx], [q[1] for q in lx]
            if min(xs) - r < x < max(xs) + r and min(ys) - r < y < max(ys) + r:
                return False
        else:
            if abs(x - f["x"]) < 2.2 and abs(y - f["y"]) < 2.2:
                return False
    return True


MH = [(sx * 16.5, sy * 16.5) for sx in (-1, 1) for sy in (-1, 1)]
stitch = []


def try_via(x, y):
    r = PCB["via_pad_mm"] / 2
    if max(abs(x), abs(y)) < ring_out + 0.15 + r:          # not in window / bond ring
        return
    if max(abs(x), abs(y)) > HALF - 0.8:
        return
    if any(math.hypot(x - mx, y - my) < 2.6 for mx, my in MH):
        return
    if any(math.hypot(x - s[0], y - s[1]) < 0.75 for s in stitch):
        return
    if clear_of_signals(x, y, r):
        stitch.append((x, y))


# 1) fence along both sides of every RF track (all layers), pitch 1.0 mm
for t in tracks:
    off = t["w"] / 2 + (GAP if t["layer"] != "In2.Cu" else SL_CLR) + 0.40
    for a, b2 in zip(t["pts"][:-1], t["pts"][1:]):
        L = math.hypot(b2[0] - a[0], b2[1] - a[1])
        if L < 1e-6:
            continue
        ux, uy = (b2[0] - a[0]) / L, (b2[1] - a[1]) / L
        n = max(1, int(L / PCB["stitch_pitch_mm"]))
        for i in range(n + 1):
            s = i * L / n
            for side in (-1, 1):
                try_via(a[0] + ux * s - side * uy * off, a[1] + uy * s + side * ux * off)
# 2) ring of vias just outside the exposed bond ring
r0 = ring_out + 0.55
n = int(8 * r0 / 0.8)
for i in range(n):
    s = i / n * 8 * r0
    side, d = divmod(s, 2 * r0)
    d -= r0
    x, y = [(d, r0), (r0, -d), (-d, -r0), (-r0, d)][int(side)]
    try_via(x, y)
# 3) background grid
g = -HALF + 1.5
while g < HALF:
    h = -HALF + 1.5
    while h < HALF:
        try_via(round(g, 3), round(h, 3))
        h += 2.0
    g += 2.0
for (x, y) in stitch:
    via(x, y, "GND")

# ------------------------------------------------------------------ silkscreen labels
labels = {f["ref"]: f["net"].replace("_", " ") for f in fps}
for f in fps:
    if f["kind"] == "SMA_EDGE":
        x, y = rot_pt(0, -5.0, f["rot"], f["x"], f["y"])
        texts.append(dict(layer="F.SilkS", text=f"{f['ref']} {labels[f['ref']]}", x=x, y=y, rot=0, size=0.8))
    else:
        texts.append(dict(layer="B.SilkS", text=f"{f['ref']} {labels[f['ref']]}", x=f["x"], y=f["y"] + 2.4, rot=0,
                          size=0.8, mirror=True))
texts.append(dict(layer="F.SilkS", text="RFL-RE1 CARRIER rev B  6L RO4003C", x=0, y=-17.6, rot=0, size=0.9))
texts.append(dict(layer="F.SilkS", text="EE143", x=-13.5, y=17.6, rot=0, size=1.0))

# ------------------------------------------------------------------ write KiCad board
LAYERS = [(0, "F.Cu", "signal"), (1, "In1.Cu", "power"), (2, "In2.Cu", "signal"), (3, "In3.Cu", "power"),
          (4, "In4.Cu", "power"), (31, "B.Cu", "signal"), (32, "B.Adhes", "user"), (33, "F.Adhes", "user"),
          (34, "B.Paste", "user"), (35, "F.Paste", "user"), (36, "B.SilkS", "user"), (37, "F.SilkS", "user"),
          (38, "B.Mask", "user"), (39, "F.Mask", "user"), (40, "Dwgs.User", "user"), (41, "Cmts.User", "user"),
          (44, "Edge.Cuts", "user"), (45, "Margin", "user"), (46, "B.CrtYd", "user"), (47, "F.CrtYd", "user"),
          (48, "B.Fab", "user"), (49, "F.Fab", "user")]


def stackup_sexpr():
    out = ['    (stackup', '      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))',
           '      (layer "F.Paste" (type "Top Solder Paste"))']
    di = 0
    for name, kind, t, desc in STACKUP:
        if kind == "soldermask":
            side = "Top" if name.startswith("F") else "Bottom"
            out.append(f'      (layer "{name}" (type "{side} Solder Mask") (color "Red") (thickness {t}) '
                       f'(material "LPI") (epsilon_r 3.8) (loss_tangent 0.025))')
        elif kind == "copper":
            out.append(f'      (layer "{name}" (type "copper") (thickness {t}))')
        else:
            di += 1
            mat = "RO4003C" if "RO4003C" in desc else "RO4450F"
            er = 3.55 if mat == "RO4003C" else 3.52
            typ = "core" if mat == "RO4003C" else "prepreg"
            out.append(f'      (layer "dielectric {di}" (type "{typ}") (thickness {t}) (material "{mat}") '
                       f'(epsilon_r {er}) (loss_tangent 0.0027))')
    out += ['      (layer "B.Paste" (type "Bottom Solder Paste"))',
            '      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))',
            '      (copper_finish "ENIG")', '      (dielectric_constraints yes)', '    )']
    return "\n".join(out)


def pad_sexpr(p, fp):
    """pad relative to footprint origin (KiCad local coords, Y down, unrotated)"""
    a = math.radians(fp["rot"])
    dx, dy = p["center"][0] - fp["x"], p["center"][1] - fp["y"]
    lx = dx * math.cos(a) + dy * math.sin(a)
    ly = -dx * math.sin(a) + dy * math.cos(a)
    lay = p["layer"]
    side = "F" if lay == "F.Cu" else "B"
    shape = "circle" if p["shape"] == "circle" else "rect"
    num = "1" if p["net"] != "GND" else "2"
    return (f'    (pad "{num}" smd {shape} (at {lx:.4f} {-ly:.4f} {fp["rot"]}) (size {p["size"][0]} {p["size"][1]}) '
            f'(layers "{lay}" "{side}.Mask") (net {NETN[p["net"]]} "{p["net"]}") (tstamp {U()}))')


def fp_sexpr(f):
    side_layer = "F.Cu" if f["kind"] == "SMA_EDGE" else "B.Cu"
    silk = "F.SilkS" if side_layer == "F.Cu" else "B.SilkS"
    fab = "F.Fab" if side_layer == "F.Cu" else "B.Fab"
    crt = "F.CrtYd" if side_layer == "F.Cu" else "B.CrtYd"
    lines = [f'  (footprint "Q4Carrier:{f["kind"]}" (layer "{side_layer}") (tstamp {U()}) (at {k(f["x"], f["y"])} {f["rot"]})',
             f'    (attr smd)',
             f'    (fp_text reference "{f["ref"]}" (at 0 0 {f["rot"]}) (layer "{fab}") (tstamp {U()})'
             f' (effects (font (size 0.6 0.6) (thickness 0.1)){" (justify mirror)" if silk == "B.SilkS" else ""}))',
             f'    (fp_text value "{f["kind"]}" (at 0 1 {f["rot"]}) (layer "{fab}") (tstamp {U()})'
             f' (effects (font (size 0.5 0.5) (thickness 0.08)){" (justify mirror)" if silk == "B.SilkS" else ""}))']
    if f["kind"] == "SMA_EDGE":
        # courtyard covering pads, inboard of the edge (body overhangs the edge by design)
        lines.append(f'    (fp_rect (start -3.2 0) (end 3.2 3.4) (stroke (width 0.05) (type solid)) (fill none) (layer "{crt}") (tstamp {U()}))')
        lines.append(f'    (fp_line (start -3.3 3.6) (end 3.3 3.6) (stroke (width 0.15) (type solid)) (layer "{silk}") (tstamp {U()}))')
    else:
        lines.append(f'    (fp_circle (center 0 0) (end 2.3 0) (stroke (width 0.15) (type solid)) (fill none) (layer "{silk}") (tstamp {U()}))')
        lines.append(f'    (fp_rect (start -2.0 -2.0) (end 2.0 2.0) (stroke (width 0.05) (type solid)) (fill none) (layer "{crt}") (tstamp {U()}))')
    for p in pads:
        if p.get("fp") == f["ref"]:
            lines.append(pad_sexpr(p, f))
    lines.append("  )")
    return "\n".join(lines)


def bondpad_fp_sexpr(p, i):
    lay = "F.Cu"
    return "\n".join([
        f'  (footprint "Q4Carrier:BOND_PAD" (layer "{lay}") (tstamp {U()}) (at {k(*p["center"])} 0)',
        '    (attr smd exclude_from_bom)',
        f'    (fp_text reference "BP{i}" (at 0 0) (layer "F.Fab") hide (tstamp {U()}) (effects (font (size 0.3 0.3) (thickness 0.05))))',
        f'    (fp_text value "BOND_PAD" (at 0 0) (layer "F.Fab") hide (tstamp {U()}) (effects (font (size 0.3 0.3) (thickness 0.05))))',
        f'    (pad "1" smd rect (at 0 0) (size {p["size"][0]} {p["size"][1]}) (layers "F.Cu" "F.Mask") '
        f'(net {NETN[p["net"]]} "{p["net"]}") (tstamp {U()}))',
        "  )"])


def rect_poly(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rounded_square(h, r, n=6):
    pts = []
    for cx, cy, a0 in ((h - r, h - r, 0), (-h + r, h - r, 90), (-h + r, -h + r, 180), (h - r, -h + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def poly_sexpr(pts, layer, width=0.05, fill="none"):
    xy = " ".join(f"(xy {k(*p)})" for p in pts)
    return (f'  (gr_poly (pts {xy}) (stroke (width {width}) (type solid)) (fill {fill}) (layer "{layer}") (tstamp {U()}))')


def zone_sexpr(net, layer, outline, clearance, name):
    xy = " ".join(f"(xy {k(*p)})" for p in outline)
    return (f'  (zone (net {NETN[net]}) (net_name "{net}") (layer "{layer}") (tstamp {U()}) (name "{name}") (hatch edge 0.5)\n'
            f'    (connect_pads yes (clearance {clearance}))\n'
            f'    (min_thickness 0.15) (filled_areas_thickness no)\n'
            f'    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3) (island_removal_mode 1) (island_area_min 0.3))\n'
            f'    (polygon (pts {xy}))\n  )')


board_outline = rounded_square(HALF, 1.0)
window = rounded_square(WIN, 0.4)

L = []
L.append('(kicad_pcb (version 20221018) (generator pcbnew)')
L.append('  (general (thickness %.3f))' % sum(t for _, _, t, _ in STACKUP if True))
L.append('  (paper "A4")')
L.append('  (title_block (title "RFL-RE1 reversible fluxon logic RF carrier") (rev "B") (company "EE143")'
         ' (comment 1 "6-layer Rogers RO4003C/RO4450F, ENIG, red LPI mask") (comment 2 "Generated by src/build_pcb.py"))')
L.append('  (layers')
for num, name, typ in LAYERS:
    L.append(f'    ({num} "{name}" {typ})')
L.append('  )')
L.append('  (setup')
L.append(stackup_sexpr())
L.append('    (pad_to_mask_clearance 0.05)')
L.append('    (allow_soldermask_bridges_in_footprints no)')
L.append('    (pcbplotparams (layerselection 0x00010fc_ffffffff) (plot_on_all_layers_selection 0x0000000_00000000)'
         ' (disableapertmacros false) (usegerberextensions false) (usegerberattributes true)'
         ' (usegerberadvancedattributes true) (creategerberjobfile true) (dashed_line_dash_ratio 12.000000)'
         ' (dashed_line_gap_ratio 3.000000) (svgprecision 4) (plotframeref false) (viasonmask false) (mode 1)'
         ' (useauxorigin false) (hpglpennumber 1) (hpglpenspeed 20) (hpglpendiameter 15.000000) (dxfpolygonmode true)'
         ' (dxfimperialunits true) (dxfusepcbnewfont true) (psnegative false) (psa4output false) (plotreference true)'
         ' (plotvalue true) (plotinvisibletext false) (sketchpadsonfab false) (subtractmaskfromsilk false)'
         ' (outputformat 1) (mirror false) (drillshape 0) (scaleselection 1) (outputdirectory "gerbers/"))')
L.append('  )')
for i, n in enumerate(NETS):
    L.append(f'  (net {i} "{n}")')
for f in fps:
    L.append(fp_sexpr(f))
for i, p in enumerate([p for p in pads if p.get("role") == "bond_pad"]):
    L.append(bondpad_fp_sexpr(p, i + 1))
# mounting holes (plated, GND)
for i, (mx, my) in enumerate(MH):
    L.append("\n".join([
        f'  (footprint "Q4Carrier:MountingHole_2.7mm_M2.5_Pad" (layer "F.Cu") (tstamp {U()}) (at {k(mx, my)})',
        '    (attr exclude_from_pos_files exclude_from_bom)',
        f'    (fp_text reference "H{i+1}" (at 0 -3) (layer "F.Fab") hide (tstamp {U()}) (effects (font (size 0.6 0.6) (thickness 0.1))))',
        f'    (fp_text value "M2.5" (at 0 3) (layer "F.Fab") hide (tstamp {U()}) (effects (font (size 0.6 0.6) (thickness 0.1))))',
        f'    (pad "1" thru_hole circle (at 0 0) (size 5.0 5.0) (drill 2.7) (layers "*.Cu" "*.Mask") (net 1 "GND") (tstamp {U()}))',
        "  )"]))
# edges
L.append(poly_sexpr(board_outline, "Edge.Cuts", 0.1))
L.append(poly_sexpr(window, "Edge.Cuts", 0.1))
# exposed ground ring (mask opening) = square band; use filled poly on F.Mask with a hole cut via two polys
mo = mask_open[0]
import klayout.db as kdb
_S = 10000  # 0.1 um grid
reg = kdb.Region(kdb.Polygon([kdb.Point(round(x * _S), round(y * _S)) for x, y in rounded_square(mo["outer"], 0.3)]))
for p in pads:
    if p.get("role") == "bond_pad":
        cx, cy = p["center"]
        sx, sy = p["size"][0] / 2 + 0.15, p["size"][1] / 2 + 0.15
        reg -= kdb.Region(kdb.Box(round((cx - sx) * _S), round((cy - sy) * _S), round((cx + sx) * _S), round((cy + sy) * _S)))
mask_ring_polys = []
for poly in reg.each():
    pts = [(pt.x / _S, pt.y / _S) for pt in poly.each_point_hull()]
    mask_ring_polys.append(pts)
    L.append(poly_sexpr(pts, "F.Mask", 0.0, "solid"))
# tracks
for t in tracks:
    for a, b2 in zip(t["pts"][:-1], t["pts"][1:]):
        L.append(f'  (segment (start {k(*a)}) (end {k(*b2)}) (width {t["w"]}) (layer "{t["layer"]}") '
                 f'(net {NETN[t["net"]]}) (tstamp {U()}))')
for v in vias:
    kind = " blind" if v["kind"] == "blind" else ""
    L.append(f'  (via{kind} (at {k(v["x"], v["y"])}) (size {v["size"]}) (drill {v["drill"]}) '
             f'(layers "{v["layers"][0]}" "{v["layers"][1]}") (net {NETN[v["net"]]}) (tstamp {U()}))')
# zones: GND on every copper layer, outline = board minus 0.3 mm edge margin (window handled by Edge.Cuts)
zo = rounded_square(HALF - 0.3, 0.8)
for lay in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"):
    clr = SL_CLR if lay == "In2.Cu" else GAP
    L.append(zone_sexpr("GND", lay, zo, clr, f"GND_{lay}"))
for t in texts:
    just = " (justify mirror)" if t.get("mirror") else ""
    L.append(f'  (gr_text "{t["text"]}" (at {k(t["x"], t["y"])} {t["rot"]}) (layer "{t["layer"]}") (tstamp {U()})'
             f' (effects (font (size {t["size"]} {t["size"]}) (thickness 0.15)){just}))')
L.append(')')

os.makedirs(OUT, exist_ok=True)
raw = os.path.join(OUT, "rf_carrier_unfilled.kicad_pcb")
open(raw, "w").write("\n".join(L))

model = dict(units="mm, Y-up, origin = board centre = die centre", kicad_offset=[X0, Y0],
             board_size=PCB["size_mm"], window=PCB["window_mm"], w_rf=W_RF, gap=GAP, w_stripline=W_SL,
             stripline_clearance=SL_CLR,
             z0=dict(gcpw_top=gcpw_z0(W_RF, GAP, H_TOP, 3.55)[0], gcpw_bottom=gcpw_z0(W_RF, GAP, STACKUP_["diel5"], 3.55)[0],
                     stripline=stripline_z0(W_SL, STACKUP_["In2.Cu"], B_STRIP, 3.52)),
             pads=pads, tracks=tracks, vias=vias, footprints=fps, mounting_holes=MH,
             bond_ring=dict(inner=ring_in, outer=ring_out),
             bond={n: dict(center=v["center"], outer=v["outer"], inner=v["inner"], u=v["u"], die_pad=v["die_pad"])
                   for n, v in bond.items()},
             flux={n: dict(v1=f["v1"], v2=f["v2"], smp=f["smp"], ref=f["ref"]) for n, f in flux.items()},
             connectors={net: dict(ref=r, x=x, y=y, rot=a) for net, (r, x, y, a) in conn_of.items()},
             texts=texts, sma=SMA, smp=SMP, mask_ring_openings=mask_ring_polys, outline=board_outline, window_outline=window)
json.dump(model, open(os.path.join(OUT, "pcb_model.json"), "w"), indent=1)
print(f"W_RF={W_RF} mm  W_SL={W_SL} mm  vias={len(vias)} (stitch {len(stitch)})  tracks={len(tracks)}")
print("Z0:", model["z0"])

# ------------------------------------------------------------------ KiCad project with the design rules
pro = {
  "board": {"design_settings": {
     "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2},
     "rules": {"min_clearance": 0.15, "min_track_width": 0.1, "min_via_diameter": 0.3, "min_via_annular_width": 0.09,
               "min_through_hole_diameter": 0.15, "min_hole_to_hole": 0.25, "min_hole_clearance": 0.2,
               "min_copper_edge_clearance": 0.08, "min_silk_clearance": 0.0, "min_microvia_diameter": 0.2,
               "min_microvia_drill": 0.1, "allow_blind_buried_vias": True, "allow_microvias": False,
               "solder_mask_clearance": 0.05, "solder_mask_min_width": 0.1},
     "rule_severities": {"silk_over_copper": "ignore", "silk_overlap": "ignore", "silk_edge_clearance": "ignore",
                         "lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
                         "text_height": "ignore", "text_thickness": "ignore"}}},
  "net_settings": {"classes": [{"name": "Default", "clearance": GAP, "track_width": W_RF, "via_diameter": 0.5,
                                 "via_drill": 0.25, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                                 "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "wire_width": 6, "bus_width": 12,
                                 "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)"}],
                   "meta": {"version": 3}},
  "meta": {"filename": "rf_carrier.kicad_pro", "version": 1},
}
for nm in ("rf_carrier_unfilled.kicad_pro", "rf_carrier.kicad_pro"):
    json.dump(pro, open(os.path.join(OUT, nm), "w"), indent=2)
dru = """(version 1)
# Wire-bond pads sit 0.10 mm from the milled die window by design.
(rule "bondpad_to_window"
  (constraint edge_clearance (min 0.05mm))
  (condition "A.Type == 'Pad' && A.Pad_Type == 'SMD' && A.Width < 0.5mm"))
# Stripline on In2: wider coplanar clearance.
(rule "stripline_clearance"
  (constraint clearance (min %.2fmm))
  (layer "In2.Cu")
  (condition "A.NetName != 'GND' || B.NetName != 'GND'"))
""" % SL_CLR
for nm in ("rf_carrier_unfilled.kicad_dru", "rf_carrier.kicad_dru"):
    open(os.path.join(OUT, nm), "w").write(dru)
