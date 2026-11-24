"""CAD -> 3D: build every physical layer of the assembly as a separate mesh, straight from
  out/quantum_die.gds        (KQCircuits die)
  out/rf_carrier.kicad_pcb   (KiCad board, zones filled by KiCad)
  out/pcb_model.json         (the routed design written into that board)

Writes
  out/assembly.glb           one node per physical layer (Y-up glTF, 1 unit = 1 mm)
  out/layer_manifest.json    z-ranges, true & visual thickness, materials, colours, explode offsets
  out/geometry_regions.json  2D summary used by validate.py (bond feet, die islands ...)
"""
import json
import math
import os
import sys

import numpy as np
import klayout.db as db
import trimesh

sys.path.insert(0, os.path.dirname(__file__))
from design_params import DIE, STACKUP, PCB, PACKAGE, RFL_STACK
import meshlib as ml
from meshlib import Mesh, extrude_region, to_i, DBU_MM

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
model = json.load(open(os.path.join(OUT, "pcb_model.json")))
die_ports = json.load(open(os.path.join(OUT, "die_ports.json")))

# ------------------------------------------------------------------ z stack (true thicknesses, mm)
Z = {}
z = 0.0
for name, kind, t, desc in reversed(STACKUP):
    if name == "B.Mask":
        Z[name] = (-t, 0.0)
        continue
    if name == "F.Mask":
        continue
    Z[name] = (z, z + t)
    z += t
T = z                                      # top of F.Cu
Z["F.Mask"] = (T, T + dict((n, t) for n, _, t, _ in STACKUP)["F.Mask"])
MASK_T = Z["F.Mask"][1] - T
ENIG_T = 0.004                             # Ni 4 um + Au 0.08 um
FILM_TRUE = DIE["film_thickness_nm"] * 1e-6
FILM_VIS = 0.003                           # visual thickness for 200 nm films (documented exaggeration)
SUB_T = DIE["substrate_thickness_um"] * 1e-3
ATT_T = PACKAGE["die_attach_um"] * 1e-3
Z_DIE_TOP = T                              # die surface flush with top copper of the carrier
Z_SUB = (Z_DIE_TOP - SUB_T, Z_DIE_TOP)
Z_ATT = (Z_SUB[0] - ATT_T, Z_SUB[0])
BASE_T = PACKAGE["base_thickness_mm"]
Z_BASE = (Z["B.Mask"][0] - BASE_T, Z["B.Mask"][0])

layers = []          # (name, Mesh, meta)


def add_layer(name, mesh, group, material, eng, explode, z0, z1, true_t=None, note="", nets=None, opacity_eng=1.0):
    if mesh is None or mesh.empty:
        print("  (empty layer skipped)", name)
        return
    layers.append(dict(name=name, mesh=mesh, group=group, material=material, eng_color=eng, explode=explode,
                       z=[round(z0, 6), round(z1, 6)], true_thickness_mm=true_t if true_t is not None else round(z1 - z0, 6),
                       visual_thickness_mm=round(z1 - z0, 6), note=note, eng_opacity=opacity_eng))


# ------------------------------------------------------------------ 2D: PCB
def R(pts):
    return ml.region_from_pts(pts)


outline = R(model["outline"]) - R(model["window_outline"])
copper = {n: db.Region() for n in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu")}
order = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]

# zones: the real KiCad fill
import pcbnew
board = pcbnew.LoadBoard(os.path.join(OUT, "rf_carrier.kicad_pcb"))
X0, Y0 = model["kicad_offset"]


def kpt(p):
    return db.Point(to_i(p.x * 1e-6 - X0), to_i(Y0 - p.y * 1e-6))


for zn in board.Zones():
    lid = list(zn.GetLayerSet().Seq())[0]      # ZONE.GetLayer() is unreliable from Python in KiCad 7
    lay = board.GetLayerName(lid)
    sp = zn.GetFilledPolysList(lid)
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i)
        poly = db.Polygon([kpt(o.CPoint(j)) for j in range(o.PointCount())])
        for h in range(sp.HoleCount(i)):
            hh = sp.Hole(i, h)
            poly.insert_hole([kpt(hh.CPoint(j)) for j in range(hh.PointCount())])
        copper[lay].insert(poly)

for t in model["tracks"]:
    copper[t["layer"]] += ml.path_region(t["pts"], t["w"])


def pad_region(p, grow=0.0):
    cx, cy = p["center"]
    if p["shape"] == "circle":
        return ml.circle_region(cx, cy, p["size"][0] / 2 + grow, 32)
    sx, sy = p["size"][0] / 2 + grow, p["size"][1] / 2 + grow
    a = math.radians(p.get("rot", 0))
    pts = [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))
           for x, y in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy))]
    return R(pts)


for p in model["pads"]:
    copper[p["layer"]] += pad_region(p)


def span(v):
    a, b = order.index(v["layers"][0]), order.index(v["layers"][1])
    return order[min(a, b):max(a, b) + 1]


drills_by_layer = {n: db.Region() for n in order}
diel_names = [n for n, k, _, _ in STACKUP if k == "dielectric"]
drills_by_diel = {n: db.Region() for n in diel_names}
for v in model["vias"]:
    ring = ml.circle_region(v["x"], v["y"], v["size"] / 2, 20)
    hole = ml.circle_region(v["x"], v["y"], v["drill"] / 2, 16)
    sp = span(v)
    for lay in sp:
        copper[lay] += ring
        drills_by_layer[lay] += hole
    i0, i1 = order.index(sp[0]), order.index(sp[-1])
    for i in range(i0, i1):
        drills_by_diel[diel_names[i]] += hole
for mx, my in model["mounting_holes"]:
    for lay in order:
        copper[lay] += ml.circle_region(mx, my, 2.5, 48)
        drills_by_layer[lay] += ml.circle_region(mx, my, 1.35, 48)
    for d in diel_names:
        drills_by_diel[d] += ml.circle_region(mx, my, 1.35, 48)

for lay in order:
    copper[lay] = ((copper[lay] & outline) - drills_by_layer[lay]).merged()

# solder mask openings
open_F = db.Region()
open_B = db.Region()
for p in model["pads"]:
    (open_F if p["layer"] == "F.Cu" else open_B).insert(pad_region(p, 0.05))
for pts in model["mask_ring_openings"]:
    open_F += R(pts)
for mx, my in model["mounting_holes"]:
    open_F += ml.circle_region(mx, my, 2.55, 48)
    open_B += ml.circle_region(mx, my, 2.55, 48)
mask_F = (outline - open_F - ml.circle_region(0, 0, 0.001)).merged()
mask_B = (outline - open_B).merged()
for mx, my in model["mounting_holes"]:
    mask_F -= ml.circle_region(mx, my, 1.35, 48)
    mask_B -= ml.circle_region(mx, my, 1.35, 48)

# silkscreen from the same text records written to KiCad
gen = db.TextGenerator.default_generator()
silk_F, silk_B = db.Region(), db.Region()
for tx in model["texts"]:
    h_ref = gen.text("A", DBU_MM, 1.0).bbox().height()
    s = tx["size"] / (h_ref * DBU_MM)
    r = gen.text(tx["text"], DBU_MM, s)
    bb = r.bbox()
    r.move(-bb.center().x, -bb.center().y)
    if tx.get("mirror"):
        r.transform(db.Trans(db.Trans.M90))
    r.move(to_i(tx["x"]), to_i(tx["y"]))
    (silk_F if tx["layer"] == "F.SilkS" else silk_B).insert(r)
silk_F = (silk_F & mask_F).merged()
silk_B = (silk_B & mask_B).merged()

# ------------------------------------------------------------------ 3D: PCB layers
print("building PCB layers")
EXP = {  # explode offsets (mm) per layer
    "package_base": -16, "B.Silk": -9.6, "B.Mask": -9.5, "B.ENIG": -8.6, "B.Cu": -8.5, "diel5": -7.0, "In4.Cu": -5.8,
    "diel4": -4.6, "In3.Cu": -3.4, "diel3": -2.2, "In2.Cu": -1.0, "diel2": 0.2, "In1.Cu": 1.4, "diel1": 2.6,
    "F.Cu": 3.8, "F.ENIG": 3.8, "F.Mask": 5.2, "F.Silk": 5.3,
    "die_attach": 7.5, "die_substrate": 9.0, "die_GP_Nb": 10.0, "die_ILD0_SiO2": 10.6, "die_M1_Nb_LJJ": 11.2,
    "die_JJ_trilayer": 11.6, "die_vias_Nb": 10.6, "die_ILD1_SiO2": 12.2, "die_R_Mo": 12.6, "die_M2_Nb": 13.0,
    "die_pad_Au": 13.4, "wirebonds_signal": 15.0, "wirebonds_ground": 15.0,
}
ENG = {
    "F.Cu": "#ff2a2a", "B.Cu": "#2f6bff", "In2.Cu": "#22d07a", "In1.Cu": "#c9a227", "In3.Cu": "#c97a27",
    "In4.Cu": "#9a6bd6", "diel": "#e9dfc6", "mask": "#b3121b", "enig": "#ffd34d", "silk": "#ffffff",
    "via_t": "#ffe600", "via_b1": "#ff7bf2", "via_b2": "#00e5ff", "die_sub": "#3b4a63", "die_film": "#9fd8ff",
    "jj": "#ff40ff", "ox": "#ffffff", "ab": "#7fffd4", "bond_s": "#ff9b26", "bond_g": "#b0b0b0",
    "base": "#d9b45a", "sma": "#c0c4c8", "solder": "#d8dde0", "attach": "#f2f2f2",
}

# split every copper layer into its RF-signal conductors and its GND pour (same metal, separate objects)
sig_reg = {n: db.Region() for n in order}
for t in model["tracks"]:
    sig_reg[t["layer"]] += ml.path_region(t["pts"], t["w"])
for p in model["pads"]:
    if p["net"] != "GND":
        sig_reg[p["layer"]] += pad_region(p)
for v in model["vias"]:
    if v["net"] != "GND":
        for lay in span(v):
            sig_reg[lay] += ml.circle_region(v["x"], v["y"], v["size"] / 2, 20)
for name, kind, t, desc in STACKUP:
    if kind == "copper":
        z0, z1 = Z[name]
        sig = (copper[name] & sig_reg[name]).merged()
        gnd = (copper[name] - sig).merged()
        plane = name in ("In1.Cu", "In3.Cu", "In4.Cu")
        add_layer(name + "_GND", extrude_region(gnd, z0, z1), "pcb", "copper",
                  "#7a2a1a" if name == "F.Cu" else "#1a2f6a" if name == "B.Cu" else "#155c3a" if name == "In2.Cu" else ENG[name],
                  EXP[name], z0, z1, note=desc + " - GND pour / plane", opacity_eng=0.5 if plane else 0.55)
        if not sig.is_empty():
            add_layer(name + "_RF", extrude_region(sig, z0, z1), "pcb", "copper", ENG[name], EXP[name], z0, z1,
                      note=desc + " - RF signal conductors (tracks, pads, via lands)", opacity_eng=1.0)
    elif kind == "dielectric":
        z0 = Z[name][0] if name in Z else None
for i, dn in enumerate(diel_names):
    # dielectric i sits between copper order[i] (above) and order[i+1] (below)
    z1 = Z[order[i]][0]
    z0 = Z[order[i + 1]][1]
    Z[dn] = (z0, z1)
    desc = [d for n, k, t, d in STACKUP if n == dn][0]
    reg = (outline - drills_by_diel[dn]).merged()
    add_layer(dn, extrude_region(reg, z0, z1), "pcb", "rogers_ro4450f" if "RO4450F" in desc else "rogers_ro4003c",
              ENG["diel"], EXP[dn], z0, z1, note=desc, opacity_eng=0.18)

# ENIG on exposed copper
enig_F = (copper["F.Cu"] & open_F).merged()
enig_B = (copper["B.Cu"] & open_B).merged()
add_layer("F.ENIG", extrude_region(enig_F, T, T + ENIG_T), "pcb", "gold", ENG["enig"], EXP["F.ENIG"], T, T + ENIG_T,
          note="ENIG on exposed top copper (bond pads, bond ring, SMA pads)")
add_layer("B.ENIG", extrude_region(enig_B, -ENIG_T, 0.0), "pcb", "gold", ENG["enig"], EXP["B.ENIG"], -ENIG_T, 0.0,
          note="ENIG on exposed bottom copper (SMP pads, SMA ground pads)")
# Solder mask: conformal - higher over copper, lower over laminate
# split so the renderer can show copper "glowing" through the thinner mask over traces, as on real boards
add_layer("F.Mask", extrude_region((mask_F - copper["F.Cu"]).merged(), Z["diel1"][1], T + MASK_T * 0.6), "pcb",
          "soldermask_red", ENG["mask"], EXP["F.Mask"], Z["diel1"][1], T + MASK_T * 0.6, true_t=MASK_T,
          note="red LPI mask over laminate (fills between traces)", opacity_eng=0.35)
add_layer("F.Mask_over_Cu", extrude_region((mask_F & copper["F.Cu"]).merged(), T, T + MASK_T), "pcb",
          "soldermask_red_over_cu", ENG["mask"], EXP["F.Mask"], T, T + MASK_T, true_t=MASK_T,
          note="red LPI mask riding on top-copper traces and pour", opacity_eng=0.35)
add_layer("B.Mask", extrude_region((mask_B - copper["B.Cu"]).merged(), -MASK_T * 0.6, Z["B.Cu"][1]), "pcb",
          "soldermask_red", ENG["mask"], EXP["B.Mask"], -MASK_T * 0.6, Z["B.Cu"][1], true_t=MASK_T,
          note="red LPI mask over laminate", opacity_eng=0.35)
add_layer("B.Mask_over_Cu", extrude_region((mask_B & copper["B.Cu"]).merged(), -MASK_T, 0.0), "pcb",
          "soldermask_red_over_cu", ENG["mask"], EXP["B.Mask"], -MASK_T, 0.0, true_t=MASK_T,
          note="red LPI mask under bottom copper", opacity_eng=0.35)
add_layer("F.Silk", extrude_region(silk_F, T + MASK_T, T + MASK_T + 0.012), "pcb", "silkscreen", ENG["silk"],
          EXP["F.Silk"], T + MASK_T, T + MASK_T + 0.012)
add_layer("B.Silk", extrude_region(silk_B, -MASK_T - 0.012, -MASK_T), "pcb", "silkscreen", ENG["silk"],
          EXP["B.Silk"], -MASK_T - 0.012, -MASK_T)

# vias: plated barrels (25 um plating) + they already have annular rings in each copper layer
vt, vb1, vb2 = Mesh(), Mesh(), Mesh()
for v in model["vias"]:
    sp = span(v)
    z1 = Z[sp[0]][1]
    z0 = Z[sp[-1]][0]
    m = vt if v["kind"] == "through" else (vb1 if sp[0] == "F.Cu" else vb2)
    ml.cylinder(v["x"], v["y"], z0, z1, v["drill"] / 2, 16, m, r_in=v["drill"] / 2 - 0.025)
for mx, my in model["mounting_holes"]:
    ml.cylinder(mx, my, 0.0, T, 1.35, 48, vt, r_in=1.325)
add_layer("vias_through", vt, "vias", "copper", ENG["via_t"], 0.0, 0.0, T, note="PTH, 0.25 drill, 25 um plating, F.Cu-B.Cu")
add_layer("vias_blind_top", vb1, "vias", "copper", ENG["via_b1"], 0.0, Z["In2.Cu"][0], T,
          note="blind 0.15 drill F.Cu-In2.Cu (flux-line transition, bond pad side)")
add_layer("vias_blind_bottom", vb2, "vias", "copper", ENG["via_b2"], 0.0, 0.0, Z["In2.Cu"][1],
          note="blind 0.15 drill In2.Cu-B.Cu (flux-line transition, SMP side)")

# ------------------------------------------------------------------ die
print("building die layers")
ly = db.Layout()
ly.read(os.path.join(OUT, "quantum_die.gds"))
top = ly.top_cell()
g2b = db.ICplxTrans(ly.dbu * 1e-3 / DBU_MM, 0, False, -to_i(DIE["size_um"] / 2000), -to_i(DIE["size_um"] / 2000))


def G(l, d):
    return db.Region(top.begin_shapes_rec(ly.layer(l, d))).transformed(g2b).merged()


half = DIE["size_um"] / 2000
die_box = ml.box_region(-half, -half, half, half)
zf = Z_DIE_TOP
RL = {name: G(*g) for name, g, _, _ in RFL_STACK}
# junctions are 0.8 um discs drawn as 16-gons in the GDS; mesh them as octagons (same centre and area)
_oct = db.Region()
for p in RL["JJ"].each():
    c, rr = p.bbox().center(), math.sqrt(p.area() / (2 * math.sqrt(2)))
    _oct.insert(db.Polygon([db.Point(round(c.x + rr * math.cos(math.pi / 8 + i * math.pi / 4)),
                                     round(c.y + rr * math.sin(math.pi / 8 + i * math.pi / 4))) for i in range(8)]))
JJ_GDS = RL["JJ"]
RL["JJ"] = _oct
TRUE = {name: t * 1e-6 for name, _, _, t in RFL_STACK}
MAT = {name: m for name, _, m, _ in RFL_STACK}
# visual z-stack of the Nb process on top of the Si (true thicknesses in the manifest / STEP)
DZ = dict(GP=(0.0, 0.003), I0=(0.003, 0.005), M1=(0.005, 0.0075), JJ=(0.0075, 0.009), I1=(0.0075, 0.0095),
          R=(0.0095, 0.0105), M2=(0.0095, 0.0135), PAD=(0.0135, 0.015), VIA=(0.003, 0.0095))
add_layer("die_attach", extrude_region(die_box, *Z_ATT), "die", "ge_varnish", ENG["attach"], EXP["die_attach"], *Z_ATT,
          note=PACKAGE["die_attach"])
add_layer("die_substrate", extrude_region(die_box, *Z_SUB), "die", "silicon", ENG["die_sub"], EXP["die_substrate"],
          *Z_SUB, note=DIE["substrate"])
SPEC = [  # object name, region, stack key, material, eng colour
    ("die_GP_Nb", RL["GP"], "GP", "niobium", "#8b93a6"),
    ("die_ILD0_SiO2", die_box, "I0", "sio2", "#cfe8ff"),
    ("die_M1_Nb_LJJ", RL["M1"], "M1", "niobium", "#2f6bff"),
    ("die_JJ_trilayer", RL["JJ"], "JJ", "niobium_jj", "#ff2aff"),
    ("die_ILD1_SiO2", die_box, "I1", "sio2", "#cfe8ff"),
    ("die_R_Mo", RL["R"], "R", "molybdenum", "#22c060"),
    ("die_M2_Nb", RL["M2"], "M2", "niobium", "#ff3b3b"),
    ("die_pad_Au", RL["PAD"], "PAD", "gold", "#ffd34d"),
]
for name, reg, key, mat, col in SPEC:
    z0, z1 = zf + DZ[key][0], zf + DZ[key][1]
    add_layer(name, extrude_region(reg, z0, z1), "die", mat, col, EXP[name], z0, z1, true_t=TRUE[key],
              note=MAT[key] + f" ({TRUE[key] * 1e6:.0f} nm; drawn {(z1 - z0) * 1e6:.0f} nm)",
              opacity_eng=0.15 if key in ("I0", "I1") else 1.0)
vm = Mesh()
extrude_region(RL["VIA"], zf + DZ["VIA"][0], zf + DZ["VIA"][1], vm)
extrude_region(RL["I1"], zf + 0.009, zf + DZ["I1"][1], vm)
add_layer("die_vias_Nb", vm, "die", "niobium", "#ffe600", EXP["die_vias_Nb"], zf + DZ["VIA"][0], zf + DZ["VIA"][1],
          true_t=TRUE["VIA"], note="stacked GP contacts (JJ ground straps, resistor returns, ring fence) + I1 contacts")
die_metal = RL["M2"]                  # pad / wiring islands used for the bond + netlist checks
# ------------------------------------------------------------------ wire bonds
print("building wire bonds")
# Die ground = every large Al island (the edge-to-edge probe line splits the plane into a north and a
# south part; airbridges + ground bonds tie them together). Signal islands are all < 1 mm^2.
# Die ground for bonding = the M2 + Au ground ring around the die edge (stitched into GP by a via fence)
ground_reg = db.Region([p for p in die_metal.each() if p.bbox().width() * DBU_MM > 9.0])
gnd_F = db.Region()
for zn in board.Zones():
    pass
fcu_gnd_exposed = enig_F  # contains signal pads too; test against signal pads separately
sig_pads = {p["net"]: p for p in model["pads"] if p.get("role") == "bond_pad"}
WIRE_R = PACKAGE["wire_d_um"] * 1e-3 / 2
LOOP = PACKAGE["loop_height_um"] * 1e-3
Z_PCB_PAD = T + ENIG_T
Z_DIE_PAD = zf + DZ["PAD"][1]


def bond_curve(a, b, n=36):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    up = np.array([0, 0, 1.0])
    P = [a, a + up * LOOP * 1.25 + d * 0.08, b - d * 0.35 + up * LOOP * 0.85, b]
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * P[0] + 3 * ((1 - t) ** 2) * t * P[1] + 3 * (1 - t) * t * t * P[2] + t ** 3 * P[3]


def wedge(m, p, direction):
    dx, dy = direction[0], direction[1]
    L = math.hypot(dx, dy)
    dx, dy = dx / L, dy / L
    w, l, h = 0.045, 0.075, 0.010
    pts = [(p[0] + dx * l / 2 * sx - dy * w / 2 * sy, p[1] + dy * l / 2 * sx + dx * w / 2 * sy)
           for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    extrude_region(R(pts), p[2], p[2] + h, m)


def pt_in(region, x, y):
    return not (region & ml.box_region(x - 1e-4, y - 1e-4, x + 1e-4, y + 1e-4)).is_empty()


bonds = []
bs, bg = Mesh(), Mesh()
for p in die_ports["ports"]:
    net = p["net"]
    bd = model["bond"][net]
    ux, uy = bd["u"]
    dpx, dpy = bd["die_pad"]
    ppx, ppy = bd["center"]
    for k_, off in enumerate((-0.055, 0.055)):
        lx, ly_ = (-uy * off, ux * off)
        a = (dpx + lx, dpy + ly_, Z_DIE_PAD)
        b = (ppx + lx, ppy + ly_, Z_PCB_PAD)
        c = bond_curve(a, b)
        ml.tube(c, WIRE_R, 8, bs)
        wedge(bs, a, (b[0] - a[0], b[1] - a[1]))
        wedge(bs, b, (b[0] - a[0], b[1] - a[1]))
        L = float(np.sum(np.linalg.norm(np.diff(c, axis=0), axis=1)))
        bonds.append(dict(net=net, kind="signal", die_xy=a[:2], pcb_xy=b[:2], length_mm=round(L, 4)))

# ground bonds along each edge, away from signal pads
ring_mid = (model["bond_ring"]["inner"] + model["bond_ring"]["outer"]) / 2 + 0.05
for side, (ux, uy) in {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}.items():
    sig_lat = [(model["bond"][n]["die_pad"][0] if uy else model["bond"][n]["die_pad"][1])
               for n in model["bond"] if tuple(model["bond"][n]["u"]) == (ux, uy)]
    lat = -4.3
    while lat <= 4.3 + 1e-9:
        if all(abs(lat - s) > 0.50 for s in sig_lat):
            die_d = None
            for d_in in (half - 0.095,):
                x, y = (ux * d_in + (lat if uy else 0), uy * d_in + (lat if ux else 0))
                if pt_in(ground_reg, x, y):
                    die_d = (x, y)
                    break
            px, py = (ux * ring_mid + (lat if uy else 0), uy * ring_mid + (lat if ux else 0))
            if die_d and pt_in(enig_F, px, py):
                a = (die_d[0], die_d[1], Z_DIE_PAD)
                b = (px, py, Z_PCB_PAD)
                c = bond_curve(a, b)
                ml.tube(c, WIRE_R, 8, bg)
                wedge(bg, a, (b[0] - a[0], b[1] - a[1]))
                wedge(bg, b, (b[0] - a[0], b[1] - a[1]))
                L = float(np.sum(np.linalg.norm(np.diff(c, axis=0), axis=1)))
                bonds.append(dict(net="GND", kind="ground", side=side, die_xy=a[:2], pcb_xy=b[:2], length_mm=round(L, 4)))
        lat += 0.40
add_layer("wirebonds_signal", bs, "bonds", "aluminium_wire", ENG["bond_s"], EXP["wirebonds_signal"],
          Z_DIE_PAD, Z_DIE_PAD + LOOP * 1.3, true_t=WIRE_R * 2, note=PACKAGE["wirebond"] + " - signal, 2 per line")
add_layer("wirebonds_ground", bg, "bonds", "aluminium_wire", ENG["bond_g"], EXP["wirebonds_ground"],
          Z_DIE_PAD, Z_DIE_PAD + LOOP * 1.3, true_t=WIRE_R * 2, note="ground bonds: die ground plane -> PCB ENIG ring")

# ------------------------------------------------------------------ connectors + solder
print("building connectors and package")
sma_m, sma_pin, ptfe, smp_m, solder = Mesh(), Mesh(), Mesh(), Mesh(), Mesh()
Z_MID = T / 2
PIN_Z = T + 0.035 + 0.25


def add_tf(dst, arrays, M):
    v, f = ml.transform(arrays, M)
    dst.add(v, f)


def rev_y(profile, n=36):
    m = ml.revolve_z(profile, n)
    return ml.transform(m.arrays(), ml.rot_x(-90))


for f in model["footprints"]:
    if f["kind"] != "SMA_EDGE":
        continue
    M = ml.rot_z(f["rot"], f["x"], f["y"])
    parts = Mesh()
    # flange block (sits against the board edge, slotted for the board)
    fl = Mesh()
    extrude_region(ml.box_region(-3.2, 0.0, 3.2, 1.6), PIN_Z - 3.2, Z["B.Mask"][0] - 0.0, fl)
    extrude_region(ml.box_region(-3.2, 0.0, 3.2, 1.6), T + MASK_T, PIN_Z + 3.2, fl)
    extrude_region(ml.box_region(-3.2, 0.25, 3.2, 1.6), Z["B.Mask"][0], T + MASK_T, fl)
    # ground legs over the top and bottom ground pads (clamp the board)
    for sx in (-1, 1):
        extrude_region(ml.box_region(sx * 2.15 - 0.55, -2.9, sx * 2.15 + 0.55, 0.0), T + ENIG_T, T + ENIG_T + 0.3, fl)
        extrude_region(ml.box_region(sx * 2.15 - 0.55, -2.9, sx * 2.15 + 0.55, 0.0), Z["B.Mask"][0] - 0.3 - ENIG_T,
                       -ENIG_T, fl)
    add_tf(sma_m, fl.arrays(), M)
    # hex coupling body + threaded barrel (1/4-36 UNS), revolved about local +y at pin height
    hexm = Mesh()
    hexr = ml.region_from_pts(ml.circle_pts(0, 0, 4.0, 6))
    extrude_region(hexr, 1.6, 4.4, hexm)
    v, fc = hexm.arrays()
    v = v[:, [0, 2, 1]]
    v[:, 2] += PIN_Z
    sma_m.add(*ml.transform((v, fc[:, ::-1]), M))
    prof = [(0.0, 4.4), (3.0, 4.4)]
    zz = 4.4
    while zz < 9.6:
        prof += [(3.0, zz), (3.17, zz + 0.18), (3.0, zz + 0.35)]
        zz += 0.705
    prof += [(3.0, 9.8), (2.05, 9.8), (2.05, 9.5)]
    v, fc = rev_y(prof)
    v[:, 2] += PIN_Z
    sma_m.add(*ml.transform((v, fc), M))
    # PTFE dielectric face and gold centre pin
    v, fc = rev_y([(2.05, 9.5), (0.64, 9.5), (0.64, 9.45)])
    v[:, 2] += PIN_Z
    ptfe.add(*ml.transform((v, fc), M))
    v, fc = rev_y([(0.0, -2.3), (0.25, -2.25), (0.25, 1.6), (0.64, 1.6), (0.64, 9.3), (0.3, 9.4), (0.0, 9.4)], 24)
    v[:, 2] += PIN_Z
    sma_pin.add(*ml.transform((v, fc), M))

for f in model["footprints"]:
    if f["kind"] != "SMP_VERT_BOTTOM":
        continue
    zb = Z["B.Mask"][0] - ENIG_T
    body = Mesh()
    extrude_region(ml.box_region(-1.8, -1.8, 1.8, 1.8), zb - 0.9, zb, body)
    v, fc = ml.revolve_z([(0, -0.9), (1.75, -0.9), (1.75, -2.2), (1.55, -2.35), (1.55, -2.6), (1.75, -2.75),
                          (1.75, -4.2), (1.25, -4.2), (1.25, -1.2), (0, -1.2)], 36).arrays()
    v[:, 2] += zb
    body.add(v, fc)
    add_tf(smp_m, body.arrays(), ml.rot_z(0, f["x"], f["y"]))
    v, fc = ml.revolve_z([(0, 0), (0.25, 0), (0.25, -3.9), (0.15, -4.05), (0, -4.05)], 16).arrays()
    v[:, 2] += zb
    sma_pin.add(*ml.transform((v, fc), ml.rot_z(0, f["x"], f["y"])))

# solder fillets: one per connector pad (no others)
n_joints = 0
for p in model["pads"]:
    if p.get("role") not in ("sma_pin", "sma_gnd", "smp_pin", "smp_gnd"):
        continue
    sx, sy = p["size"][0] / 2 * 0.92, p["size"][1] / 2 * 0.92
    h = 0.16 if p["role"] != "sma_pin" else 0.28
    v, fc = ml.revolve_z([(0, h), (0.45, h * 0.85), (0.8, h * 0.5), (1.0, 0.0)], 24).arrays()
    v[:, 0] *= sx
    v[:, 1] *= sy
    if p["layer"] == "F.Cu":
        v[:, 2] += T + ENIG_T
    else:
        v[:, 2] = -v[:, 2] - ENIG_T
        fc = fc[:, ::-1]
    a = math.radians(p.get("rot", 0))
    Mr = ml.rot_z(p.get("rot", 0), p["center"][0], p["center"][1])
    solder.add(*ml.transform((v, fc), Mr))
    n_joints += 1

add_layer("sma_connectors", sma_m, "connectors", "stainless", ENG["sma"], EXP["F.Cu"], PIN_Z - 3.2, PIN_Z + 4.0,
          note="6x generic end-launch SMA, body passivated stainless (geometry representative)")
add_layer("connector_pins", sma_pin, "connectors", "gold", ENG["enig"], EXP["F.Cu"], -5, PIN_Z + 1,
          note="gold-plated BeCu centre contacts")
add_layer("connector_ptfe", ptfe, "connectors", "ptfe", "#ffffff", EXP["F.Cu"], PIN_Z - 2, PIN_Z + 2)
add_layer("smp_connectors", smp_m, "connectors", "gold", ENG["enig"], EXP["B.Cu"], -5.2, 0,
          note="4x generic vertical SMP (bottom side) for flux lines")
add_layer("solder_joints", solder, "connectors", "solder", ENG["solder"], 0.0, -0.3, T + 0.3,
          note=f"SAC305 fillets, one per connector pad ({n_joints})")

# package base (gold-plated OFHC copper) with die pedestal, SMA leg recesses, SMP pass-through holes
base_reg = ml.region_from_pts(model["outline"])
hole_reg = db.Region()
for f in model["footprints"]:
    if f["kind"] == "SMP_VERT_BOTTOM":
        hole_reg += ml.circle_region(f["x"], f["y"], 2.3, 40)
for mx, my in model["mounting_holes"]:
    hole_reg += ml.circle_region(mx, my, 1.05, 32)
recess = db.Region()
for f in model["footprints"]:
    if f["kind"] == "SMA_EDGE":
        a = math.radians(f["rot"])
        pts = [(f["x"] + x * math.cos(a) - y * math.sin(a), f["y"] + x * math.sin(a) + y * math.cos(a))
               for x, y in ((-3.5, -3.4), (3.5, -3.4), (3.5, 0.5), (-3.5, 0.5))]
        recess += R(pts)
bm = Mesh()
zb0, zb1 = Z_BASE
extrude_region((base_reg - hole_reg).merged(), zb0, zb1 - 0.8, bm)
extrude_region((base_reg - hole_reg - recess).merged(), zb1 - 0.8, zb1, bm)
ped = ml.box_region(-5.1, -5.1, 5.1, 5.1)
extrude_region(ped, zb1, Z_ATT[0], bm)
add_layer("package_base", bm, "package", "gold_plated_copper", ENG["base"], EXP["package_base"], zb0, Z_ATT[0],
          note=PACKAGE["base_material"] + "; raised pedestal carries the die through the PCB window")
# M2.5 pan-head screws
scr = Mesh()
for mx, my in model["mounting_holes"]:
    v, fc = ml.revolve_z([(0, 1.5), (1.8, 1.5), (2.2, 1.2), (2.25, 0.0), (1.25, 0.0), (1.25, -5.4), (0, -5.4)], 32).arrays()
    v[:, 2] += T + MASK_T
    scr.add(*ml.transform((v, fc), ml.rot_z(0, mx, my)))
add_layer("screws", scr, "package", "stainless", ENG["sma"], EXP["F.Mask"] + 1.0, T + MASK_T - 5.4, T + MASK_T + 1.5,
          note="4x M2.5 A2 stainless pan head, clamp carrier to base")

# ------------------------------------------------------------------ 2D cache for the STEP builder
def reg_json(r):
    out = []
    for p in r.merged().each():
        out.append([[[q.x * DBU_MM, q.y * DBU_MM] for q in p.each_point_hull()]] +
                   [[[q.x * DBU_MM, q.y * DBU_MM] for q in p.each_point_hole(h)] for h in range(p.holes())])
    return out


os.makedirs(os.path.join(OUT, "_cache"), exist_ok=True)
json.dump(dict(copper={k: reg_json(v) for k, v in copper.items()}, die={k: reg_json(v) for k, v in RL.items()},   # JJs as equal-area octagons
               enig_F=reg_json(enig_F), outline=reg_json(outline)),
          open(os.path.join(OUT, "_cache", "regions_2d.json"), "w"))
json.dump([dict(net=b["net"], kind=b["kind"]) for b in bonds], open(os.path.join(OUT, "_cache", "bond_meta.json"), "w"))
np.save(os.path.join(OUT, "_cache", "bond_curves.npy"),
        np.array([bond_curve((b["die_xy"][0], b["die_xy"][1], Z_DIE_PAD), (b["pcb_xy"][0], b["pcb_xy"][1], Z_PCB_PAD))
                  for b in bonds]))

# ------------------------------------------------------------------ export
print("exporting GLB")
scene = trimesh.Scene()
YUP = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
manifest = []
for L in layers:
    v, f = L["mesh"].arrays()
    v = v @ YUP.T
    tm = trimesh.Trimesh(vertices=v.astype(np.float32), faces=f, process=False)
    tm.merge_vertices(merge_tex=True, merge_norm=True, digits_vertex=6)
    col = L["eng_color"].lstrip("#")
    rgba = [int(col[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [1.0]
    tm.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name=L["material"], baseColorFactor=rgba, metallicFactor=0.3, roughnessFactor=0.5))
    scene.add_geometry(tm, node_name=L["name"], geom_name=L["name"])
    manifest.append({k: L[k] for k in L if k != "mesh"} | {"triangles": int(len(f))})
    print(f"  {L['name']:<20} tris={len(f):>8}  z=[{L['z'][0]:.4f},{L['z'][1]:.4f}]")
scene.export(os.path.join(OUT, "assembly.glb"), include_normals=False)
json.dump(dict(units="mm", z_reference="z=0 at bottom face of B.Cu; +z up; die surface flush with top copper",
               Z={k: list(v) for k, v in Z.items()}, z_die_top=Z_DIE_TOP, z_substrate=list(Z_SUB),
               z_attach=list(Z_ATT), z_base=list(Z_BASE), layers=manifest),
          open(os.path.join(OUT, "layer_manifest.json"), "w"), indent=1)

islands = []
for i, poly in enumerate(sorted(die_metal.each(), key=lambda p: -p.area())):
    bb = poly.bbox()
    islands.append(dict(id=i, area_mm2=poly.area() * DBU_MM ** 2,
                        bbox=[bb.left * DBU_MM, bb.bottom * DBU_MM, bb.right * DBU_MM, bb.top * DBU_MM]))


def island_of(x, y):
    for i, poly in enumerate(sorted(die_metal.each(), key=lambda p: -p.area())):
        if poly.inside(db.Point(to_i(x), to_i(y))):
            return i
    return None


json.dump(dict(bonds=bonds, die_islands=islands,
               bond_die_island=[dict(net=b["net"], kind=b["kind"], island=island_of(*b["die_xy"])) for b in bonds],
               pcb_copper_area_mm2={k: v.area() * DBU_MM ** 2 for k, v in copper.items()},
               enig_F_area_mm2=enig_F.area() * DBU_MM ** 2, n_solder_joints=n_joints),
          open(os.path.join(OUT, "geometry_regions.json"), "w"), indent=1)
print("bonds:", sum(b["kind"] == "signal" for b in bonds), "signal,", sum(b["kind"] == "ground" for b in bonds), "ground")
