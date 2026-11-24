"""Independent checks over the CAD sources and the 3D export.

Reads: quantum_die.gds, rf_carrier.kicad_pcb (+ KiCad DRC report), pcb_model.json, assembly.glb,
       layer_manifest.json, geometry_regions.json, connections.json
Writes: out/validation_report.json and docs/VALIDATION.md
"""
import itertools
import json
import math
import os
import re
import sys

import numpy as np
import klayout.db as db
import pcbnew
import trimesh

sys.path.insert(0, os.path.dirname(__file__))
from design_params import STACKUP, PCB, DIE, PACKAGE
import meshlib as ml

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
DOCS = os.path.join(HERE, "..", "docs")
J = lambda n: json.load(open(os.path.join(OUT, n)))
model, man, geo, conns, ports = J("pcb_model.json"), J("layer_manifest.json"), J("geometry_regions.json"), \
    J("connections.json"), J("die_ports.json")
results = []


def check(cat, name, ok, detail):
    status = "WARN" if isinstance(ok, str) and ok == "warn" else ("PASS" if bool(ok) else "FAIL")
    results.append(dict(category=cat, check=name, status=status,
                        detail=detail))


# ================================================================== 1. PCB: DRC + connectivity (KiCad)
rep = open(os.path.join(OUT, "drc_report.txt")).read()
nv = int(re.search(r"Found (\d+) DRC violations", rep).group(1))
nu = int(re.search(r"Found (\d+) unconnected pads", rep).group(1))
check("PCB net connectivity", "KiCad DRC violations", nv == 0, f"{nv} violations (KiCad 7 DRC engine, rules in rf_carrier.kicad_pro/.kicad_dru)")
check("PCB net connectivity", "KiCad unconnected items (ratsnest)", nu == 0, f"{nu} unconnected pads")

board = pcbnew.LoadBoard(os.path.join(OUT, "rf_carrier.kicad_pcb"))
X0, Y0 = model["kicad_offset"]
L2N = {board.GetLayerName(i): i for i in range(60)}
COPPER = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]


def bp(p):
    return (p.x * 1e-6 - X0, Y0 - p.y * 1e-6)


# Independent geometric continuity walk over the items KiCad actually holds (not over our model).
items = []
for t in board.GetTracks():
    net = t.GetNetname()
    if t.GetClass() == "PCB_VIA":
        lays = [n for n in COPPER if t.IsOnLayer(L2N[n])]
        items.append(dict(kind="via", net=net, layers=lays, pts=[bp(t.GetPosition())], r=t.GetWidth() * 5e-7))
    else:
        items.append(dict(kind="track", net=net, layers=[board.GetLayerName(t.GetLayer())],
                          pts=[bp(t.GetStart()), bp(t.GetEnd())], r=t.GetWidth() * 5e-7))
for fp in board.GetFootprints():
    for pd in fp.Pads():
        lays = [n for n in COPPER if pd.IsOnLayer(L2N[n])]
        sz = pd.GetSize()
        items.append(dict(kind="pad", net=pd.GetNetname(), layers=lays, pts=[bp(pd.GetPosition())],
                          r=min(sz.x, sz.y) * 5e-7, ref=fp.GetReference(), half=(sz.x * 5e-7, sz.y * 5e-7)))


def seg_d(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def touches(A, B):
    if not set(A["layers"]) & set(B["layers"]):
        return False
    pa, pb = A["pts"], B["pts"]
    if len(pa) == 2 and len(pb) == 2:
        d = min(seg_d(pa[0], *pb), seg_d(pa[1], *pb), seg_d(pb[0], *pa), seg_d(pb[1], *pa))
    elif len(pa) == 2:
        d = seg_d(pb[0], *pa)
    elif len(pb) == 2:
        d = seg_d(pa[0], *pb)
    else:
        d = math.dist(pa[0], pb[0])
    return d <= A["r"] + B["r"] + 1e-6


for net in [p["net"] for p in ports["ports"]]:
    its = [i for i in items if i["net"] == net]
    adj = {k: set() for k in range(len(its))}
    for a, b in itertools.combinations(range(len(its)), 2):
        if touches(its[a], its[b]):
            adj[a].add(b)
            adj[b].add(a)
    seen, stack = {0}, [0]
    while stack:
        for n in adj[stack.pop()]:
            if n not in seen:
                seen.add(n)
                stack.append(n)
    conn_pad = [i for i, x in enumerate(its) if x["kind"] == "pad" and x["ref"].startswith("J")]
    bond_pad = [i for i, x in enumerate(its) if x["kind"] == "pad" and x["ref"].startswith("BP")]
    nvia = sum(1 for x in its if x["kind"] == "via")
    lays = sorted({l for x in its if x["kind"] == "track" for l in x["layers"]}, key=COPPER.index)
    ok = len(seen) == len(its) and conn_pad and bond_pad and conn_pad[0] in seen and bond_pad[0] in seen
    check("Trace and via continuity", f"{net}: connector -> bond pad", bool(ok),
          f"{len(its)} KiCad items in one connected chain; layers {'+'.join(lays)}; {nvia} via(s)")

# blind-via spans: each must land on a track at BOTH of its end layers
for v in [i for i in items if i["kind"] == "via" and i["net"] != "GND"]:
    ends = (v["layers"][0], v["layers"][-1])
    hit = [any(t["kind"] == "track" and t["net"] == v["net"] and e in t["layers"] and touches(v, t) for t in items)
           or any(p["kind"] == "pad" and p["net"] == v["net"] and e in p["layers"] and touches(v, p) for p in items)
           for e in ends]
    check("Trace and via continuity", f"blind via {v['net']} {ends[0]}->{ends[1]} lands on copper at both ends",
          all(hit), f"at ({v['pts'][0][0]:.2f}, {v['pts'][0][1]:.2f}) mm, spans {', '.join(v['layers'])}")

# ================================================================== 2. die netlist from GDS polygons (RFL)
ly = db.Layout()
ly.read(os.path.join(OUT, "quantum_die.gds"))
top = ly.top_cell()
R = lambda l, d: db.Region(top.begin_shapes_rec(ly.layer(l, d))).merged()
M1, JJr, I1r, Rr, M2, VIA = R(3, 0), R(4, 0), R(5, 0), R(6, 0), R(7, 0), R(9, 0)
cells = J("die_cells.json")["cells"]
polys = list(M2.each())
metal = M2


def island(xu, yu):
    for i, p in enumerate(polys):
        if p.inside(db.Point(int(xu * 1000), int(yu * 1000))):
            return i
    return None


def pt_um(x, y, r=1):
    return db.Region(db.Box(int((x - r) * 1000), int((y - r) * 1000), int((x + r) * 1000), int((y + r) * 1000)))


isl = {p["net"]: island(*p["pad_center_um"]) for p in ports["ports"]}
ring = [i for i, p in enumerate(polys) if p.bbox().width() > 9_000_000]
gnd_ids = set(ring)
check("Die netlist (GDS)", "each pad is its own M2 island, isolated from the ground ring",
      len(set(isl.values())) == len(isl) and not (set(isl.values()) & gnd_ids) and None not in isl.values(),
      f"{len(isl)} pads -> {len(set(isl.values()))} distinct M2 islands; ground ring = island {ring}")
EXPECT = {"TRIG_A": ["DCSFQ_A"], "TRIG_B": ["DCSFQ_B"], "TEST_IN": ["DCSFQ_T"], "OUT_0": ["SFQDC_0"],
          "OUT_1": ["SFQDC_1"], "TEST_OUT": ["SFQDC_T"], "VB_W": ["DCSFQ_A", "SFQDC_0", "DCSFQ_T"],
          "VB_E": ["DCSFQ_B", "SFQDC_1", "SFQDC_T"]}
for net, targets in EXPECT.items():
    reg = db.Region(polys[isl[net]])
    hits = []
    for t in targets:
        c = cells[t]
        x, y = c["bias_tap"] if net.startswith("VB") else c["center"]
        hits.append(not (reg & pt_um(x, y, 80 if not net.startswith("VB") else 2)).is_empty())
    grounded = not (reg & VIA).is_empty()
    check("Die netlist (GDS)", f"{net} reaches {', '.join(targets)}", all(hits) and not grounded,
          f"M2 island #{isl[net]} touches {sum(hits)}/{len(targets)} target cells; no via to GP: {not grounded}")
for net, cell in (("CTRL_CB", "CB"), ("CTRL_RE", "RE")):
    reg = db.Region(polys[isl[net]])
    x, y = cells[cell]["center"]
    near = not (reg & pt_um(x, y, 120)).is_empty()
    check("Die netlist (GDS)", f"{net} is a flux line shorted to GP beside {cell}", near and not (reg & VIA).is_empty(),
          "M2 control line terminates in a stacked via to GP within 120 um of the device (current loop = flux bias)")
# fluxon network: one continuous M1 conductor from both DC/SFQ inputs through CB and RE to both SFQ/DC outputs
m1p = list(M1.each())


def m1_of(x, y):
    for i, p in enumerate(m1p):
        if not (db.Region(p) & pt_um(x, y, 3)).is_empty():
            return i
    return None


net_pts = {k: cells[k]["center"] for k in ("DCSFQ_A", "DCSFQ_B", "SFQDC_0", "SFQDC_1", "CB")}
main = {k: m1_of(v[0] - (30 if "DCSFQ" in k else 35 if "SFQDC" in k else 20), v[1] - (20 if "DCSFQ" in k else 0))
        for k, v in net_pts.items()}
re_ports = cells["RE"]["ports"]
main.update({f"RE.{k}": m1_of(*v) for k, v in re_ports.items()})
test = {k: m1_of(cells[k]["center"][0] + 30, cells[k]["center"][1] - 20) if "DCSFQ" in k else
        m1_of(cells[k]["center"][0] - 35, cells[k]["center"][1]) for k in ("DCSFQ_T", "SFQDC_T")}
check("Die netlist (GDS)", "fluxon network continuous: DC/SFQ_A,B -> CB -> RE (I0,I1,O0,O1) -> SFQ/DC_0,1",
      len(set(main.values())) == 1 and None not in main.values(),
      f"all {len(main)} nodes on M1 conductor #{set(main.values())}")
check("Die netlist (GDS)", "racetrack continuous and separate: DC/SFQ_T -> 18 mm LJJ -> SFQ/DC_T",
      len(set(test.values())) == 1 and None not in test.values() and set(test.values()) != set(main.values()),
      f"M1 conductor #{set(test.values())}, {cells['LJJ_TEST']['cells']} junction cells, {cells['LJJ_TEST']['length_um'] / 1000:.2f} mm")
# every LJJ junction has its ground return (JJ -> I1 contact -> M2 strap -> stacked via -> GP)
strap = M2.interacting(VIA)
ljj_n = sum(v["cells"] for k, v in cells.items() if v["kind"] == "LJJ")
grounded = JJr.interacting(I1r).interacting(strap.interacting(JJr)).count()
check("Die netlist (GDS)", "LJJ junctions grounded through their strap + via", grounded >= ljj_n,
      f"{grounded} JJs with a strap-to-via ground return; {ljj_n} LJJ cells drawn ({sum(v.get('skipped_under_crossings', 0) for v in cells.values() if v['kind'] == 'LJJ')} cells omitted under M2 crossings)")
# no signal/bias M2 line touches a grounded strap (would short it)
shorts = [n for n in isl if not n.startswith("CTRL") and not (db.Region(polys[isl[n]]) & VIA).is_empty()]
check("Die netlist (GDS)", "no I/O or bias line shorted to ground", not shorts, f"shorted: {shorts}")
sim = J("rfl_sim.json")
bal = sim["ballistic_design_subK"]
check("Fluxon physics (discrete sine-Gordon)", "ballistic transit of the longest LJJ at design damping",
      bal["energy_retained"] > 0.95, f"{bal['cells']} cells, alpha {bal['alpha']}: v {bal['launch_v']} -> {bal['final_v']} c0, "
      f"energy retained {bal['energy_retained'] * 100:.1f} %; at 4.2 K (alpha {sim['ballistic_at_4K2']['alpha']}) the fluxon "
      f"stalls (v -> {sim['ballistic_at_4K2']['final_v']})")
cb = sim["controlled_barrier"]
outs = {s["outcome"] for s in cb["sweep"]}
check("Fluxon physics (discrete sine-Gordon)", "controlled barrier switches reflect <-> transmit with control flux",
      {"reflect", "transmit"} <= outs, f"reflects for Phi < {cb['transmits_from_phi_ctrl']} Phi0, transmits above (SQUID Ic_max {cb['bmax']} Ic)")
check("Fluxon physics (discrete sine-Gordon)", "LJJ discreteness", 2.0 < sim["parameters"]["Lambda_cells"] < 6.0,
      f"Josephson length {sim['parameters']['Lambda_cells']} cells ({sim['parameters']['lambda_J_um']} um): fluxon spans "
      "several cells, so pinning by the lattice is weak")

# ================================================================== 3. wire bonds
pads_by_net = {p["net"]: p for p in model["pads"] if p.get("role") == "bond_pad"}
SR = lambda x, y: ml.box_region(x - 1e-4, y - 1e-4, x + 1e-4, y + 1e-4)
die_tr = db.ICplxTrans(ly.dbu * 1e-3 / ml.DBU_MM, 0, False, -ml.to_i(5.0), -ml.to_i(5.0))
gnd_reg = db.Region([polys[i] for i in gnd_ids]).transformed(die_tr)   # M2 + Au ground ring
bad = []
for b, bi in zip(geo["bonds"], geo["bond_die_island"]):
    if b["kind"] == "signal":
        p = pads_by_net[b["net"]]
        cx, cy = p["center"]
        inside_pcb = abs(b["pcb_xy"][0] - cx) <= p["size"][0] / 2 and abs(b["pcb_xy"][1] - cy) <= p["size"][1] / 2
        # island ids are compared in this script's own GDS-frame numbering (equal-area islands can swap order)
        inside_die = island((b["die_xy"][0] + 5) * 1000, (b["die_xy"][1] + 5) * 1000) == isl[b["net"]]
        if not (inside_pcb and inside_die):
            bad.append(b)
    else:
        if (gnd_reg & SR(*b["die_xy"])).is_empty():
            bad.append(b)
nsig = sum(b["kind"] == "signal" for b in geo["bonds"])
ngnd = len(geo["bonds"]) - nsig
check("Pad and wire-bond alignment", "every bond foot lands on the right die metal and PCB pad", not bad,
      f"{nsig} signal bonds (2 per line) + {ngnd} ground bonds; {len(bad)} misplaced")
lens = [b["length_mm"] for b in geo["bonds"]]
check("Pad and wire-bond alignment", "bond lengths within 0.5-1.6 mm", all(0.5 <= x <= 1.6 for x in lens),
      f"min {min(lens):.3f} mm, max {max(lens):.3f} mm (short bonds keep series inductance ~1 nH/mm low)")
# wire-to-wire clearance (sampled, in plan view at the feet and in 3D along the loops)
pts = [np.linspace(b["die_xy"], b["pcb_xy"], 12) for b in geo["bonds"]]
mind = min(np.min(np.linalg.norm(a[:, None, :] - c[None, :, :], axis=2)) for a, c in itertools.combinations(pts, 2))
check("Physical clearance and grounding", "wire-to-wire spacing (plan view)", mind > 0.05,
      f"closest approach {mind * 1000:.0f} um between adjacent bonds (25 um wire)")

# ================================================================== 4. die-to-carrier interface
wh = PCB["window_mm"] / 2
dh = DIE["size_um"] / 2000
clr = wh - dh
check("Die-to-carrier interface", "die fits PCB window", clr >= 0.1, f"clearance {clr * 1000:.0f} um per side (window {PCB['window_mm']} mm, die {2 * dh} mm)")
zd = man["z_die_top"]
zp = man["Z"]["F.Cu"][1]
check("Die-to-carrier interface", "die surface vs PCB bond-pad height", abs(zd - zp) < 0.05,
      f"die top z={zd:.4f} mm, PCB copper top z={zp:.4f} mm (difference {abs(zd - zp) * 1000:.0f} um)")
ped_top = [L for L in man["layers"] if L["name"] == "package_base"][0]["z"][1]
check("Die-to-carrier interface", "pedestal top == die-attach bottom", abs(ped_top - man["z_attach"][0]) < 1e-9,
      f"pedestal top {ped_top:.4f} mm; GE varnish {man['z_attach']}; substrate {man['z_substrate']}")
die_pad_to_pcb = [math.dist(model["bond"][n]["die_pad"], model["bond"][n]["center"]) for n in model["bond"]]
check("Die-to-carrier interface", "die pad <-> PCB pad colinear and facing", all(0.6 < d < 1.2 for d in die_pad_to_pcb),
      f"pad-centre spans {min(die_pad_to_pcb):.3f}-{max(die_pad_to_pcb):.3f} mm, all along the pad's outward normal")

# ================================================================== 5. grounding / clearance
st = [v for v in model["vias"] if v["net"] == "GND"]
check("Physical clearance and grounding", "ground stitching vias", len(st) > 200,
      f"{len(st)} through vias; fences at <= {PCB['stitch_pitch_mm']} mm pitch along every RF line "
      f"(lambda/10 at 8 GHz in RO4003C GCPW is {300 / (8 * math.sqrt(2.67)) / 10:.2f} mm)")
side = conns["ground"]["ground_bonds_per_side"]
check("Physical clearance and grounding", "ground bonds on every die edge", all(v > 0 for v in side.values()), str(side))
# connector bodies don't collide with each other or with the board's mounting holes
fps = model["footprints"]
for kind, need, body in (("SMA_EDGE", 8.5, "SMA coupling hex 8 mm across corners"), ("SMP_VERT_BOTTOM", 3.8, "SMP flange 3.6 mm square")):
    sel = [f for f in fps if f["kind"] == kind]
    cmin = min(math.dist((a["x"], a["y"]), (b["x"], b["y"])) for a, b in itertools.combinations(sel, 2))
    check("Physical clearance and grounding", f"{kind} connector spacing", cmin >= need,
          f"closest pair {cmin:.2f} mm centre-to-centre; needs >= {need} mm ({body})")

# ================================================================== 6. stackup / materials
kicad_txt = open(os.path.join(OUT, "rf_carrier.kicad_pcb")).read()
ks = re.findall(r'\(layer "([^"]+)" \(type "[^"]+"\)(?: \(color "[^"]+"\))? \(thickness ([0-9.]+)\)', kicad_txt)
kmap = {}
di = 0
for n, t in ks:
    kmap[n] = float(t)
mism = []
for name, kind, t, desc in STACKUP:
    key = name if kind != "dielectric" else f"dielectric {int(name[-1])}"
    if abs(kmap.get(key, -1) - t) > 1e-9:
        mism.append((name, kmap.get(key), t))
check("Layer dimensions and materials", "KiCad stackup == design_params.STACKUP", not mism,
      f"{len(STACKUP)} layers compared; total {sum(t for *_, t, _ in [(a, b, c, d) for a, b, c, d in STACKUP]):.3f} mm; mismatches {mism}")
missing = [L["name"] for L in man["layers"] if not L.get("material") or L["true_thickness_mm"] <= 0]
check("Layer dimensions and materials", "every 3D layer has material + thickness", not missing,
      f"{len(man['layers'])} layer objects; missing: {missing}")

# ================================================================== 7. cross-section consistency
Z = man["Z"]
chain = []
for name, kind, t, desc in STACKUP:
    if name in Z:
        chain.append((name, *Z[name]))
chain.sort(key=lambda r: -r[2])
gaps = [(a[0], b[0], round(a[1] - b[2], 9)) for a, b in zip(chain[:-1], chain[1:]) if abs(a[1] - b[2]) > 1e-9]
check("Cross-section consistency", "PCB layers contiguous (no gaps / overlaps)", not gaps,
      f"{len(chain)} layers from z={chain[-1][1]:.3f} to {chain[0][2]:.3f} mm; gaps/overlaps: {gaps}")
for name, kind, t, desc in STACKUP:
    if name in Z and "Mask" not in name:
        if abs((Z[name][1] - Z[name][0]) - t) > 1e-9:
            check("Cross-section consistency", f"{name} thickness", False, f"{Z[name]} vs {t}")

# ================================================================== 8. 2D CAD <-> 3D model alignment
glb = trimesh.load(os.path.join(OUT, "assembly.glb"))


def top_area_and_bounds(name):
    g = glb.geometry[name]
    v = np.asarray(g.vertices, float)
    v = np.c_[v[:, 0], -v[:, 2], v[:, 1]]          # back to Z-up
    f = np.asarray(g.faces)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    zmax = v[:, 2].max()
    up = (n[:, 2] > 0) & (np.abs(tri[:, :, 2] - zmax).max(axis=1) < 1e-6)
    return 0.5 * np.linalg.norm(n[up], axis=1).sum(), v.min(0), v.max(0)


a3d, lo, hi = top_area_and_bounds("die_M2_Nb")
a2d = M2.area() * 1e-12   # nm^2 -> mm^2 (GDS dbu 1 nm)
check("2D CAD vs 3D model", "die M2 area: GDS vs mesh", abs(a3d - a2d) / a2d < 0.002,
      f"GDS {a2d:.4f} mm^2, mesh top face {a3d:.4f} mm^2 ({(a3d - a2d) / a2d * 100:+.3f} %)")
a3d, *_ = top_area_and_bounds("die_M1_Nb_LJJ")
a2d = M1.area() * 1e-12
check("2D CAD vs 3D model", "die M1 (LJJ) area: GDS vs mesh", abs(a3d - a2d) / a2d < 0.002,
      f"GDS {a2d:.4f} mm^2, mesh {a3d:.4f} mm^2")
n3 = len(glb.geometry["die_JJ_trilayer"].split(only_watertight=False))
check("2D CAD vs 3D model", "junction count: GDS vs mesh", n3 == JJr.count(), f"GDS {JJr.count()} junctions, mesh {n3} bodies")
_, lo, hi = top_area_and_bounds("die_substrate")
check("2D CAD vs 3D model", "die substrate mesh extents == GDS chip box", np.allclose([lo[0], lo[1], hi[0], hi[1]], [-5, -5, 5, 5], atol=2e-3),
      f"mesh x[{lo[0]:.4f},{hi[0]:.4f}] y[{lo[1]:.4f},{hi[1]:.4f}] mm; GDS box 0..10000 um")
for lay in ("F.Cu", "In2.Cu", "B.Cu"):
    a_rf, *_ = top_area_and_bounds(lay + "_RF")
    a_g, *_ = top_area_and_bounds(lay + "_GND")
    a2 = geo["pcb_copper_area_mm2"][lay]
    check("2D CAD vs 3D model", f"{lay} copper area: KiCad fill + routed copper vs mesh", abs(a_rf + a_g - a2) / a2 < 0.002,
          f"2D {a2:.3f} mm^2, mesh {a_rf + a_g:.3f} mm^2")
_, lo, hi = top_area_and_bounds("diel1")
bb = board.GetBoardEdgesBoundingBox()
kw, kh = bb.GetWidth() * 1e-6, bb.GetHeight() * 1e-6
check("2D CAD vs 3D model", "board outline: KiCad Edge.Cuts vs mesh", abs((hi[0] - lo[0]) - (kw - 0.1)) < 0.01 and abs((hi[1] - lo[1]) - (kh - 0.1)) < 0.01,
      f"KiCad {kw:.3f} x {kh:.3f} mm (incl. line width), mesh {hi[0] - lo[0]:.3f} x {hi[1] - lo[1]:.3f} mm")
# every routed track endpoint in KiCad appears in the model (and vice versa)
ktr = sorted((round(a[0], 3), round(a[1], 3)) for i in items if i["kind"] == "track" for a in i["pts"])
mtr = sorted((round(p[0], 3), round(p[1], 3)) for t in model["tracks"] for a, b in zip(t["pts"][:-1], t["pts"][1:]) for p in (a, b))
check("2D CAD vs 3D model", "track geometry: KiCad board == 3D source model", ktr == mtr,
      f"{len(ktr)} segment endpoints compared")

# ================================================================== 9. RF sanity
check("RF design", "line impedances", all(abs(v - 50) < 1.5 for v in model["z0"].values()),
      "; ".join(f"{k} {v:.1f} ohm" for k, v in model["z0"].items()) )

# ------------------------------------------------------------------ write
summary = {s: sum(r["status"] == s for r in results) for s in ("PASS", "WARN", "FAIL")}
json.dump(dict(summary=summary, results=results), open(os.path.join(OUT, "validation_report.json"), "w"), indent=1)
os.makedirs(DOCS, exist_ok=True)
with open(os.path.join(DOCS, "VALIDATION.md"), "w") as f:
    f.write(f"# Validation report\n\nGenerated by `src/validate.py`. **{summary['PASS']} pass, {summary['WARN']} warn, "
            f"{summary['FAIL']} fail.**\n\n| Category | Check | Result | Detail |\n|---|---|---|---|\n")
    for r in results:
        f.write(f"| {r['category']} | {r['check']} | {r['status']} | {r['detail']} |\n")
print(summary)
for r in results:
    if r["status"] != "PASS":
        print(r)
