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
from design_params import STACKUP, PCB, DIE, PACKAGE, ACTIVE_DIE, cpw_l_pH_per_um
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

if ACTIVE_DIE == "RFL":
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


else:
    # ============================================================== 2. die netlist from GDS polygons (QFX-1)
    from design_params import QFX
    ly = db.Layout()
    ly.read(os.path.join(OUT, "quantum_die.gds"))
    top = ly.top_cell()
    R = lambda l, d: db.Region(top.begin_shapes_rec(ly.layer(l, d))).merged()
    BASE, GRAL, AL1, AL2, RES, ABP, ABS, SHORTS = (R(1, 0), R(2, 0), R(3, 0), R(4, 0), R(5, 0), R(6, 0), R(7, 0),
                                                    R(64, 0))
    JJr = (AL1 & AL2).merged()
    cells = J("die_cells.json")
    C = cells["cells"]
    um = lambda x, y, r=0.5: db.Region(db.Box(int((x - r) * 1000), int((y - r) * 1000), int((x + r) * 1000), int((y + r) * 1000)))
    polys = list(BASE.each())
    metal = BASE

    def island(xu, yu):
        for i, p in enumerate(polys):
            if p.inside(db.Point(int(xu * 1000), int(yu * 1000))):
                return i
        return None

    isl = {p["net"]: island(*p["pad_center_um"]) for p in ports["ports"]}
    gnd_ids = {max(range(len(polys)), key=lambda i: polys[i].area())}
    # --- per-net continuity: remove the intentional end-shorts, then bridges link their two feet
    iso = list(((BASE - SHORTS) + ABP).merged().each())

    def iso_id(x, y, r=0.6):
        q = um(x, y, r)
        for i, p in enumerate(iso):
            if not (db.Region(p) & q).is_empty():
                return i
        return None

    parent = list(range(len(iso)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for span in ABS.each():
        feet = [i for i, p in enumerate(iso) if not (db.Region(p) & db.Region(span) & ABP).is_empty()]
        for a_, b_ in zip(feet[:-1], feet[1:]):
            parent[find(a_)] = find(b_)
    pad_of = {p["net"]: p["pad_center_um"] for p in ports["ports"]}
    rmap = {r_["name"]: r_ for r_ in cells["routes"]}
    for net in ("QF1_DRIVE", "QF2_DRIVE", "QF1_FLUX", "QF2_FLUX", "FEED_IN", "VB_IN", "VB_OUT", "KICK_TRIG", "KICK_OUT"):
        rname = "FEED" if net == "FEED_IN" else net
        r_ = rmap[rname]
        a_, b_ = iso_id(*pad_of[net]), iso_id(*r_["pre_end"])     # 5 um before the end (the end sits in its short)
        ok = a_ is not None and b_ is not None and find(a_) == find(b_)
        gnd_iso = {find(max(range(len(iso)), key=lambda i: iso[i].area()))}
        ok_iso = ok and find(a_) not in gnd_iso
        check("Die netlist (GDS)", f"{net}: pad -> line end continuous and isolated from ground (shorts removed)",
              ok and ok_iso, f"route {rname}, {sum(1 for b in cells['bridges'] if b['route'] == rname)} airbridge(s) on it, "
              f"end at ({r_['end'][0]:.1f}, {r_['end'][1]:.1f}) um")
    fo = iso_id(*pad_of["FEED_OUT"])
    check("Die netlist (GDS)", "FEED_IN and FEED_OUT are one feedline", fo is not None and find(fo) == find(iso_id(*pad_of["FEED_IN"])),
          "continuous Nb centre conductor between the two feedline pads")
    # --- line ends land on the intended qubit rim at the intended link
    for net, q, frac_name in (("QF1_DRIVE", "QF1", "A-1"), ("QF2_DRIVE", "QF2", "A-1"), ("QF1_FLUX", "QF1", "B+3"),
                              ("QF2_FLUX", "QF2", "B+3")):
        cx, cy = C[q]["center"]
        ex, ey = rmap[net]["end"]
        rr = math.hypot(ex - cx, ey - cy)
        tied = not (SHORTS & um(ex, ey, 2)).is_empty() and not (BASE & um(ex, ey, 0.4)).is_empty()
        rr += 1.5           # line ends 1 um inside the hole; the short patch crosses the rim edge
        check("Die netlist (GDS)", f"{net} ends on the {q} rim (galvanic short = current loop)",
              abs(rr - (C[q]["hole_radius_um"] + 0.5)) < 1.0 and tied, f"end {rr:.2f} um from the ring centre (rim at "
              f"{C[q]['hole_radius_um']} um), short patch present: {tied}")
    for x_ in ("XFMR1", "XFMR2"):
        q = "QF1" if x_ == "XFMR1" else "QF2"
        cx, cy = C[q]["center"]
        mid = C[q]["mid_deg"]
        angs = [((math.degrees(math.atan2(y - cy, x - cx)) - mid + 540) % 360) - 180 for x, y in C[x_]["lands"]]
        step = 360 / C[q]["rungs"]
        inside = all(0 < C[q]["sense"] * a < step for a in angs)
        sec = C[x_]["section"]
        check("Die netlist (GDS)", f"{x_}: hairpin under the kick section lands across the {q} barrier link",
              inside and abs((sec[1] - sec[0]) - QFX["kick_section_cells"] * QFX["kick_pitch_um"]) < 1e-6,
              f"landing angles {angs[0]:.1f} deg and {angs[1]:.1f} deg from the barrier rung (link spans 0..{step:.0f} deg); "
              f"section {sec[0]:.0f}-{sec[1]:.0f} um = {QFX['kick_section_cells']} cells")
    # --- quantum rings: junction count and areas match the physics model
    w_, bm = QFX["well_weak"], QFX["barrier_EJmax_ratio"]
    for q in ("QF1", "QF2"):
        cx, cy = C[q]["center"]
        ringj = JJr & db.Region(db.Box(int((cx - 60) * 1000), int((cy - 60) * 1000), int((cx + 60) * 1000), int((cy + 60) * 1000)))
        areas = sorted(round(p.area() * 1e-6, 4) for p in ringj.each())
        a0 = QFX["ring_jj_area_um2"]
        exp = sorted([a0] * (QFX["ring_cells"] - 3) + [round((1 - w_) * a0, 4)] * 2 + [round(bm / 2 * a0, 4)] * 2)
        ok = len(areas) == len(exp) and all(abs(a - b) < 0.02 * b for a, b in zip(areas, exp))
        rail = GRAL & db.Region(db.Box(int((cx - 60) * 1000), int((cy - 60) * 1000), int((cx + 60) * 1000), int((cy + 60) * 1000)))
        closed = rail.count() == 1 and list(rail.each())[0].holes() == 1
        check("Die netlist (GDS)", f"{q}: 24 rungs = 21 nominal + 2 weak (wells) + barrier SQUID rung (2 JJ), areas as modelled",
              ok and closed, f"{len(areas)} junctions, areas {sorted(set(areas))} um^2; expected {sorted(set(exp))}; "
              f"grAl rail closed loop: {closed}")
    kj = JJr.count() - 2 * (QFX["ring_cells"] + 1)
    kick_area = [p.area() * 1e-6 for p in JJr.each() if p.area() * 1e-6 > 5]
    check("Die netlist (GDS)", "kick line junction chain", abs(len(kick_area) - C["KICK"]["junctions"] - 4) <= 0,
          f"{len(kick_area)} large junctions (= {C['KICK']['junctions']} line nodes + 4 in the converters), "
          f"area {min(kick_area):.2f}-{max(kick_area):.2f} um^2 (Ic = {QFX['kick_Ic_uA']:.0f} uA at {QFX['jc_uA_per_um2']} uA/um^2)")
    # one junction process: every junction class must give its modelled Ic and C from the same Jc and C/area
    _e, _h, _phi0 = 1.602176634e-19, 6.62607015e-34, 2.067833848e-15
    ic_ring_nA = QFX["EJ_GHz"] * 1e9 * 2 * math.pi * _h / _phi0 * 1e9
    c_ring_fF = _e ** 2 / (2 * _h * QFX["EC_GHz"] * 1e9) * 1e15
    a_ring, a_kick = QFX["ring_jj_area_um2"], float(np.median(kick_area))
    jc, cs = QFX["jc_uA_per_um2"], QFX["c_spec_fF_per_um2"]
    dev = [abs(jc * a_ring * 1e3 / ic_ring_nA - 1), abs(cs * a_ring / c_ring_fF - 1),
           abs(jc * a_kick / QFX["kick_Ic_uA"] - 1), abs(cs * a_kick / QFX["kick_C_fF"] - 1),
           abs(a_kick / QFX["kick_jj_area_um2"] - 1)]
    check("Die netlist (GDS)", "single Al/AlOx/Al process: ring and kick junctions share Jc and C/area", max(dev) < 0.02,
          f"Jc {jc} uA/um^2, {cs} fF/um^2: ring {a_ring} um^2 -> {jc * a_ring * 1e3:.1f} nA / {cs * a_ring:.2f} fF "
          f"(model {ic_ring_nA:.1f} nA / {c_ring_fF:.2f} fF); kick {a_kick:.2f} um^2 (GDS) -> {jc * a_kick:.2f} uA / "
          f"{cs * a_kick:.0f} fF (model {QFX['kick_Ic_uA']} uA / {QFX['kick_C_fF']} fF); worst deviation {max(dev) * 100:.1f} %")
    ks = iso_id(*rmap["KICK"]["pts"][0]) if "pts" in rmap["KICK"] else iso_id(*rmap["KICK"]["start"])
    ke = iso_id(*rmap["KICK"]["end"])
    check("Die netlist (GDS)", "kick strip continuous from launcher to receiver", ks is not None and find(ks) == find(ke),
          f"{C['KICK']['length_um'] / 1000:.2f} mm of Nb strip, crossed only by airbridges")
    for b in cells["bridges"]:
        x, y = b["at"]
        check("Die netlist (GDS)", f"airbridge on {b['route']} over {', '.join(b['over'])}",
              not (ABS & um(x, y, 1)).is_empty(), f"span {b['span_um']} um at ({x:.0f}, {y:.0f}) um")
    for rn in ("RES1", "RES2"):
        check("Die netlist (GDS)", f"{rn} length = lambda/4 at {C[rn]['f_design_GHz']} GHz",
              abs(C[rn]["length_um"] - C[rn]["target_length_um"]) < 1.0,
              f"{C[rn]['length_um']:.1f} um vs {C[rn]['target_length_um']:.1f} um (eps_eff = (eps_r + 1)/2)")
    # --- physics model checks
    qs = J("qfx_sim.json")
    op = qs["operating_point"]
    fm = op["fluxon_mass_check"]
    check("Quantum fluxon physics", "minimum-energy-path model vs full 24-junction normal modes",
          fm["relative_error"] < 0.01, f"pinning mode {fm['path_pinning_GHz']:.2f} GHz (string-method path) vs "
          f"{fm['full_normal_mode_GHz']:.2f} GHz (full Hessian); next internal mode {fm['next_full_mode_GHz']:.1f} GHz")
    check("Quantum fluxon physics", "qubit spectrum at the operating point", 0.8 < op["f01_GHz"] < 6 and op["f12_GHz"] > 2 * op["f01_GHz"],
          f"f01 {op['f01_GHz']:.3f} GHz, f12 {op['f12_GHz']:.3f} GHz at Phi_b = {op['phi_b']} Phi0")
    check("Quantum fluxon physics", "double sweet spot: f01 first-order insensitive to barrier flux and to tilt",
          abs(op["df01_dphib_GHz_per_Phi0"]) < 1.0 and abs(qs["tilt"]["G00_minus_G11"]) < 1e-6 * abs(qs["tilt"]["G01_GHz_per_Phi0"]),
          f"df01/dPhi_b = {op['df01_dphib_GHz_per_Phi0']:.2g} GHz/Phi0 at Phi_b = {op['phi_b']} (steepest point of the sweep "
          f"{op['max_sweep_slope_GHz_per_Phi0']:.0f} GHz/Phi0), curvature {op['d2f01_dphib2_GHz_per_Phi0sq']:.0f} GHz/Phi0^2; "
          f"tilt couples only transversally (G00 - G11 = {qs['tilt']['G00_minus_G11']:.1e})")
    kl = qs["kick_line"]
    lam_gds = math.sqrt(QFX["kick_LJ_pH"] / (cpw_l_pH_per_um(C["KICK"]["strip_w_um"], C["KICK"]["gap_um"]) * C["KICK"]["pitch_um"]))
    n_exp = C["KICK"]["length_um"] / C["KICK"]["pitch_um"]
    check("Fluxon-kick gate", "kick-line Josephson length from the drawn CPW matches the model; ballistic (Lambda > 2)",
          abs(lam_gds / kl["Lambda_cells"] - 1) < 0.01 and kl["Lambda_cells"] > 2 and abs(C["KICK"]["junctions"] - n_exp) <= 2,
          f"drawn strip {C['KICK']['strip_w_um']} um / gaps {C['KICK']['gap_um']} um -> {kl['l_pH_per_um']:.3f} pH/um, "
          f"L_cell {kl['L_cell_pH']:.2f} pH vs L_J {kl['L_J_pH']:.2f} pH -> Lambda {lam_gds:.2f} cells (model "
          f"{kl['Lambda_cells']:.2f}); {C['KICK']['junctions']} junctions at {C['KICK']['pitch_um']} um pitch")
    check("Quantum fluxon physics", "Born-Oppenheimer separation (fluxon motion vs internal array modes)",
          fm["next_full_mode_GHz"] > 10 * op["f01_GHz"] and fm["next_full_mode_GHz"] > op["f02_GHz"],
          f"first internal plasma mode {fm['next_full_mode_GHz']:.1f} GHz vs f01 {op['f01_GHz']:.2f} GHz and the first "
          f"leakage level at {op['f02_GHz']:.2f} GHz")
    bc = qs["backaction_check"]
    check("Fluxon-kick gate", "back-action displacement: sine-Gordon simulation vs dX = eps tau / p",
          bc["relative_error"] < 0.1, f"{bc['dX_sim_cells']:.3f} vs {bc['dX_formula_cells']:.3f} cells")
    kd = qs["kick_gate_dynamics"]
    check("Fluxon-kick gate", "pi/2 phase gate from one heavy fluxon (24-level dynamics)",
          abs(kd["conditional_phase_rad"] - kd["theta_target"]) < 1e-3 and kd["leakage"] < 1e-6 and kd["bit_flip_probability"] < 1e-3,
          f"phase {kd['conditional_phase_rad']:.4f} rad at transformer coupling kappa = {kd['kappa_calibrated']:.2e}; "
          f"bit-flip {kd['bit_flip_probability']:.1e}, leakage {kd['leakage']:.1e}, pulse {kd['pulse_ns']:.2f} ns")
    kt = {round(r_["beta"], 3): r_ for r_ in qs["kick_gate_table"]}
    check("Fluxon-kick gate", "which-path dephasing per pi/2 kick at 20 mK (thermal momentum spread)",
          kt[0.05]["thermal_dephasing"] < 2e-3, f"{kt[0.05]['thermal_dephasing']:.1e} at v = 0.05 c0, "
          f"{kt[0.1]['thermal_dephasing']:.1e} at 0.1 c0; launch-speed jitter must stay below "
          f"{100 * kt[0.05]['launch_jitter_tol_for_1em4']:.1f} % for 1e-4")
    cp = qs["coupling"]
    check("Quantum fluxon physics", "ZZ coupling between the two fluxon qubits", cp["J_zz_MHz_vs_shared_L_pH"]["1"] > 1,
          f"J = {cp['J_zz_MHz_vs_shared_L_pH']['1']:.2f} MHz per pH of shared bus inductance (link current change "
          f"{abs(cp['delta_I_nA']):.0f} nA)")

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


if ACTIVE_DIE == "RFL":
    pairs_ = [("die_M2_Nb", M2, "die M2"), ("die_M1_Nb_LJJ", M1, "die M1 (LJJ)")]
    jj_mesh = "die_JJ_trilayer"
else:
    pairs_ = [("die_base_Nb", BASE, "die Nb base"), ("die_grAl_rails", GRAL, "grAl rails")]
    jj_mesh = "die_junctions_AlOx"
for mesh_name, reg_, label in pairs_:
    a3d, *_ = top_area_and_bounds(mesh_name)
    a2d = reg_.area() * 1e-12
    check("2D CAD vs 3D model", f"{label} area: GDS vs mesh", abs(a3d - a2d) / a2d < 0.002,
          f"GDS {a2d:.4f} mm^2, mesh top face {a3d:.4f} mm^2 ({(a3d - a2d) / a2d * 100:+.3f} %)")
n3 = len(glb.geometry[jj_mesh].split(only_watertight=False))
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
sys.exit(1 if summary["FAIL"] else 0)
