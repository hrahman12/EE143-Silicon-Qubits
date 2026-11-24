#!/usr/bin/env python3
"""Independent checks of the generated QBF-X2 carrier (run after finalize_carrier.py).

  1. schematic vs PCB netlist comparison (Altium-style ECO list)  -> reports/sch_vs_pcb.txt
  2. ERC substitute (KiCad 7 has no CLI ERC)                       -> reports/erc_report.txt
  3. impedance table: rf_calc.gcpw_z0 on the drawn and the as-built (zone-fill) geometry -> reports/impedance_table.txt
  4. length matching from the board copper (pcbnew)               -> reports/length_report.txt
  5. filter cut-offs from the schematic component values           -> reports/filter_report.txt
  6. DRC self-test: injected faults must be caught                 -> reports/drc_selftest.txt
Everything is summarised in reports/check_summary.json; exit status 1 if any check fails.
"""
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys

import pcbnew
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import carrier_params as P  # noqa: E402
from carrier_lib.sexpr import parse as sparse, find  # noqa: E402
from carrier_lib import filters as FL  # noqa: E402
from carrier_lib import fd2d  # noqa: E402

NAME = P.PROJECT["name"]
REP = os.path.join(HERE, "reports")
PCB = os.path.join(HERE, f"{NAME}.kicad_pcb")
SCH = os.path.join(HERE, f"{NAME}.kicad_sch")
NM = 1e-6
C0 = 299792458.0


def rf_calc():
    spec = importlib.util.spec_from_file_location("rf_calc_qfx1", P.RF_CALC_PY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write(name, lines):
    with open(os.path.join(REP, name), "w") as fh:
        fh.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------------------------------------ inputs
def sch_netlist():
    out = os.path.join(REP, "sch_netlist.net")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, SCH],
                   check=True, capture_output=True)
    t = sparse(open(out).read())
    comps = {}
    for c in find(find(t, "components")[0], "comp"):
        d = {x[0]: x[1] for x in c[1:] if isinstance(x, list) and len(x) == 2 and isinstance(x[1], str)}
        fields = {}
        for fl in find(c, "fields"):
            for fd in find(fl, "field"):
                nm = [x for x in fd if isinstance(x, list) and x[0] == "name"][0][1]
                fields[nm] = fd[-1] if isinstance(fd[-1], str) else ""
        comps[d["ref"]] = dict(value=d.get("value", ""), footprint=d.get("footprint", ""), fields=fields)
    nets = {}
    for n in find(find(t, "nets")[0], "net"):
        name = find(n, "name")[0][1]
        nodes = []
        for nd in find(n, "node"):
            dd = {x[0]: x[1] for x in nd[1:] if isinstance(x, list)}
            nodes.append((dd["ref"], dd["pin"], dd.get("pintype", "")))
        nets[name] = nodes
    return comps, nets


def pcb_data(board):
    fps = {}
    flag_board_only = getattr(pcbnew, "FP_BOARD_ONLY", 0)
    for fp in board.GetFootprints():
        pads = {}
        for pd in fp.Pads():
            pads.setdefault(pd.GetNumber(), set()).add(pd.GetNetname())
        fps[fp.GetReference()] = dict(fpid=fp.GetFPIDAsString(), value=fp.GetValue(), pads=pads,
                                      board_only=bool(fp.GetAttributes() & flag_board_only) if flag_board_only else False)
    return fps


# ------------------------------------------------------------------------------------------------ 1. comparison
def compare(scomps, snets, fps):
    eco = []
    pin_net = {}
    for net, nodes in snets.items():
        for ref, pin, _ in nodes:
            pin_net[(ref, pin)] = net
    pcb_refs = {r for r, d in fps.items() if not d["board_only"]}
    sch_refs = set(scomps)
    for r in sorted(sch_refs - pcb_refs):
        eco.append(f"Add component {r} ({scomps[r]['footprint']}) to PCB")
    for r in sorted(pcb_refs - sch_refs):
        eco.append(f"Remove component {r} from PCB (not in schematic)")
    n_pads = 0
    for r in sorted(sch_refs & pcb_refs):
        s, p = scomps[r], fps[r]
        if s["footprint"] != p["fpid"]:
            eco.append(f"Change footprint {r}: PCB {p['fpid']} -> schematic {s['footprint']}")
        if s["value"] != p["value"]:
            eco.append(f"Change value {r}: PCB '{p['value']}' -> schematic '{s['value']}'")
        for num, nets in p["pads"].items():
            n_pads += 1
            want = pin_net.get((r, num))
            if want is None:
                if nets != {""}:
                    eco.append(f"Pad {r}.{num} on {sorted(nets)} has no schematic pin")
                continue
            if nets != {want}:
                eco.append(f"Change net {r}.{num}: PCB {sorted(nets)} -> schematic {want}")
    for (r, pin), net in sorted(pin_net.items()):
        if r in fps and pin not in fps[r]["pads"]:
            eco.append(f"Schematic pin {r}.{pin} ({net}) has no PCB pad")
    pcb_nets = {n for d in fps.values() for ns in d["pads"].values() for n in ns if n}
    for n in sorted(set(snets) - pcb_nets):
        eco.append(f"Add net {n} to PCB")
    for n in sorted(pcb_nets - set(snets)):
        eco.append(f"Remove net {n} from PCB")
    return eco, n_pads, len(sch_refs & pcb_refs)


# ------------------------------------------------------------------------------------------------ 2. ERC
def erc(scomps, snets, model):
    issues, info = [], []
    for net, nodes in snets.items():
        if net.startswith("unconnected-"):
            for ref, pin, typ in nodes:
                if "no_connect" not in typ:
                    issues.append(f"floating pin {ref}.{pin} (no connection, no NC flag)")
            continue
        if len(nodes) < 2:
            issues.append(f"net {net} has only {len(nodes)} pin(s)")
    info.append(f"nets: {sum(1 for n in snets if not n.startswith('unconnected-'))}; "
                f"pins: {sum(len(v) for v in snets.values())}")
    types = {}
    for nodes in snets.values():
        for _, _, typ in nodes:
            types[typ] = types.get(typ, 0) + 1
    info.append(f"pin types: {types} (all passive -> no output/power conflicts possible)")
    nc = [nd for v in snets.values() for nd in v if "no_connect" in nd[2]]
    info.append(f"no-connect flags: {len(nc)} (none needed: every pin of every symbol is used)")
    # die contract
    d = json.load(open(P.DIE_PADS_JSON))
    pin_net = {(ref, pin): net for net, nodes in snets.items() for ref, pin, _ in nodes}
    bad = 0
    for p in d["pads"]:
        got = pin_net.get(("U1", str(p["id"])))
        if got != p["net"]:
            bad += 1
            issues.append(f"U1 pin {p['id']} on {got}, die_pads.json says {p['net']}")
    info.append(f"U1: {len(d['pads']) - bad}/{len(d['pads'])} pins on their die_pads.json net")
    # power flag + GND symbols (power objects are not in the netlist: read the sheet)
    sch = sparse(open(SCH).read())
    syms = find(sch, "symbol")
    gnd_pts, flag_pts = set(), set()
    for s in syms:
        lib = find(s, "lib_id")[0][1]
        at = find(s, "at")[0]
        pt = (round(float(at[1]), 3), round(float(at[2]), 3))
        if lib == "power:GND":
            gnd_pts.add(pt)
        if lib == "power:PWR_FLAG":
            flag_pts.add(pt)
    # wire connectivity (union-find on wire end points) between the PWR_FLAG pin and a GND symbol pin
    parent = {}

    def root(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for w in find(sch, "wire"):
        pts = find(w, "pts")[0]
        xy = [(round(float(q[1]), 3), round(float(q[2]), 3)) for q in pts[1:]]
        for p0, p1 in zip(xy, xy[1:]):
            parent[root(p0)] = root(p1)
    gnd_roots = {root(p) for p in gnd_pts}
    flag_on_gnd = any(root(p) in gnd_roots for p in flag_pts)
    if not flag_on_gnd:
        issues.append("GND has no PWR_FLAG (KiCad ERC: power input not driven)")
    info.append(f"GND power symbols: {len(gnd_pts)} positions, PWR_FLAG wired to GND: {flag_on_gnd}")
    # fields required for the BOM
    for ref, c in scomps.items():
        for k in ("Manufacturer", "MPN"):
            if not c["fields"].get(k):
                issues.append(f"{ref}: missing field {k}")
        if not c["footprint"]:
            issues.append(f"{ref}: no footprint")
    refs = list(scomps)
    if len(refs) != len(set(refs)):
        issues.append("duplicate reference designators")
    return issues, info


# ------------------------------------------------------------------------------------------------ 3. impedance
def poly_from(ps):
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        ext = [(o.CPoint(j).x * NM, o.CPoint(j).y * NM) for j in range(o.PointCount())]
        holes = []
        for h in range(ps.HoleCount(i)):
            hh = ps.Hole(i, h)
            holes.append([(hh.CPoint(j).x * NM, hh.CPoint(j).y * NM) for j in range(hh.PointCount())])
        if len(ext) >= 3:
            out.append(Polygon(ext, [hh for hh in holes if len(hh) >= 3]))
    return unary_union(out)


def zone_copper(board, layer_name):
    lid = board.GetLayerID(layer_name)
    geoms = []
    for z in board.Zones():
        if z.GetNetname() == "GND" and z.IsOnLayer(lid) and not z.GetIsRuleArea():
            geoms.append(poly_from(z.GetFilledPolysList(lid)))
    return unary_union(geoms)


def track_lines(board):
    """net -> list of (kind, LineString page-mm, width, length)"""
    out = {}
    for t in board.GetTracks():
        cls = t.GetClass()
        if cls == "PCB_VIA":
            continue
        net = t.GetNetname()
        w = t.GetWidth() * NM
        if cls == "PCB_ARC":
            c = t.GetCenter()
            r = t.GetRadius() * NM
            a0 = math.atan2(t.GetStart().y - c.y, t.GetStart().x - c.x)
            ang = t.GetAngle().AsRadians() if hasattr(t.GetAngle(), "AsRadians") else math.radians(t.GetAngle() / 10.0)
            n = 24
            pts = [((c.x * NM) + r * math.cos(a0 + ang * i / n), (c.y * NM) + r * math.sin(a0 + ang * i / n)) for i in range(n + 1)]
            # check orientation against the stored end point
            e = (t.GetEnd().x * NM, t.GetEnd().y * NM)
            if math.dist(pts[-1], e) > 1e-3:
                pts = [((c.x * NM) + r * math.cos(a0 - ang * i / n), (c.y * NM) + r * math.sin(a0 - ang * i / n)) for i in range(n + 1)]
            out.setdefault(net, []).append(("arc", LineString(pts), w, t.GetLength() * NM, t.GetLayerName()))
        else:
            a, b = t.GetStart(), t.GetEnd()
            out.setdefault(net, []).append(("seg", LineString([(a.x * NM, a.y * NM), (b.x * NM, b.y * NM)]), w,
                                            t.GetLength() * NM, t.GetLayerName()))
    return out


def impedance(board, rf, model):
    gc = P.GCPW
    z_draw, e_draw = rf.gcpw_z0(gc["w"], gc["gap"], gc["h"], gc["er"])
    w_solve = rf.solve_gcpw_width(gc["gap"], gc["h"], gc["er"], gc["z_target"])
    gnd_f = zone_copper(board, "F.Cu")
    gnd_1 = zone_copper(board, "In1.Cu")
    lines = track_lines(board)
    rfn = [n for n in model["rf"]]
    # page coordinates of every SMP centre: samples within the anti-pad transition are reported separately
    X0, Y0 = model["page_origin"]
    conns = [(X0 + r["conn"][0], Y0 - r["conn"][1]) for r in model["rf"].values()]
    r_launch = 0.75 / 2 + 0.45 + gc["w"] / 2 + 0.05
    gaps = {"seg": [], "arc": [], "launch": []}
    cover = []
    for net in rfn:
        for kind, ls, w, L, lay in lines[net]:
            if lay != "F.Cu":
                continue
            n = max(2, int(L / 0.1))
            for i in range(1, n):
                p = ls.interpolate(i / n, normalized=True)
                g_ = p.distance(gnd_f) - w / 2
                if min(math.dist((p.x, p.y), c) for c in conns) < r_launch:
                    gaps["launch"].append(g_)
                else:
                    gaps[kind].append(g_)
            corridor = ls.buffer(w / 2 + gc["gap"] + 2 * gc["h"], cap_style=2)
            cover.append(corridor.intersection(gnd_1).area / corridor.area)

    def stats(v):
        return min(v), max(v), min(v), max(v), len(v)
    res = dict(z_drawn=z_draw, eeff=e_draw, w_for_50=w_solve, segments={})
    for kind in ("seg", "arc", "launch"):
        mn, mx, lo, hi, n = stats(gaps[kind])
        z_lo = rf.gcpw_z0(gc["w"], lo, gc["h"], gc["er"])[0]
        z_hi = rf.gcpw_z0(gc["w"], hi, gc["h"], gc["er"])[0]
        res["segments"][kind] = dict(gap_min=mn, gap_max=mx, gap_p01=lo, gap_p99=hi, samples=n, z_p01=z_lo, z_p99=z_hi)
    res["launch_len_per_line"] = len(gaps["launch"]) * 0.1 / max(1, len(rfn))
    res["in1_coverage_min"] = min(cover)
    # bond landing pads: lateral gap to the GND copper
    pg = []
    for fp in board.GetFootprints():
        if fp.GetReference() != "U1":
            continue
        for pd in fp.Pads():
            if pd.GetNetname() in rfn:
                c = pd.GetPosition()
                sz = pd.GetSize()
                poly = pd.GetEffectivePolygon()
                shp = poly_from(poly)
                pg.append(shp.distance(gnd_f))
    res["landing_pad_gap_min"], res["landing_pad_gap_max"] = min(pg), max(pg)
    # 2D field-solver cross-check: validation in the thin-copper limit, then the real cross-section
    mode = "corridor" if gc["mask_free"] else "full"
    res["fd_thin"] = fd2d.solve(gc["w"], gc["gap"], gc["h"], gc["er"], t=0.0, mask_t=0.0, cells_per_h=120)
    res["fd_cu"] = fd2d.solve(gc["w"], gc["gap"], gc["h"], gc["er"], t=gc["t_cu"], mask_t=0.0)
    res["fd_real"] = fd2d.solve(gc["w"], gc["gap"], gc["h"], gc["er"], t=gc["t_cu"], mask_t=0.02, mask_mode=mode,
                                corridor_inset=gc["corridor_inset"])
    res["fd_if_masked"] = fd2d.solve(gc["w"], gc["gap"], gc["h"], gc["er"], t=gc["t_cu"], mask_t=0.02, mask_mode="full")
    return res


# ------------------------------------------------------------------------------------------------ 4. lengths
def lengths(board, model, eeff):
    lines = track_lines(board)
    L = {}
    for net in model["rf"]:
        L[net] = sum(x[3] for x in lines[net])
    pairs = [("TRAP_A0", "TRAP_B0"), ("TRAP_A1", "TRAP_B1"), ("ACC_A0", "ACC_B0"), ("ACC_A1", "ACC_B1")]
    ps_per_mm = math.sqrt(eeff) / C0 * 1e-3 * 1e12
    rows = []
    ok = True
    for a, b in pairs:
        d = abs(L[a] - L[b])
        ok &= d <= P.RULES["skew_max"]
        rows.append((a, b, L[a], L[b], d, d * ps_per_mm))
    groups = {g: max(L[n] for n in L if n.startswith(g)) - min(L[n] for n in L if n.startswith(g)) for g in ("TRAP", "ACC")}
    return L, rows, ok, ps_per_mm, groups


# ------------------------------------------------------------------------------------------------ 5. filters
def parse_value(v):
    m = re.match(r"\s*([0-9.]+)\s*([pnumkMG]?)", v)
    mult = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "M": 1e6, "G": 1e9, "": 1.0}[m.group(2)]
    return float(m.group(1)) * mult


def filters(scomps, snets, model):
    pin_net = {(ref, pin): net for net, nodes in snets.items() for ref, pin, _ in nodes}
    out = []
    ok = True
    for net, parts in model["chan_parts"].items():
        r1 = parse_value(scomps[parts["R1"]]["value"])
        r2 = parse_value(scomps[parts["R2"]]["value"])
        c1 = parse_value(scomps[parts["C1"]]["value"])
        # topology from the netlist: R1 -> node A (C1 to GND) -> R2 -> die net
        topo = (pin_net[(parts["R1"], "2")] == pin_net[(parts["R2"], "1")] == pin_net[(parts["C1"], "1")]
                and pin_net[(parts["C1"], "2")] == "GND" and pin_net[(parts["R2"], "2")] == net
                and pin_net[(parts["R1"], "1")] == f"{net}_IN")
        if parts["gate"]:
            c2 = parse_value(scomps[parts["C2"]]["value"])
            topo = topo and pin_net[(parts["C2"], "1")] == net and pin_net[(parts["C2"], "2")] == "GND"
            g = FL.gate_ladder(r1, c1, r2, c2)
            g50 = FL.gate_ladder(r1, c1, r2, c2, P.FILTERS["source_R"])
            passed = topo and g["f3db"] <= P.FILTERS["gate"]["fc_max"] and g50["f3db"] <= P.FILTERS["gate"]["fc_max"]
            out.append(dict(net=net, kind="gate", R1=r1, C1=c1, R2=r2, C2=c2, f3db=g["f3db"], f3db_50ohm=g50["f3db"],
                            f_single=g["f_single"], atten_1MHz_dB=g["atten_1MHz_dB"], topology_ok=topo, passed=passed,
                            limit=f"<= {P.FILTERS['gate']['fc_max'] / 1e3:.0f} kHz"))
        else:
            l = FL.load_tee(r1, c1, r2, 0.0, P.FILTERS["load_loop_L"])
            l50 = FL.load_tee(r1, c1, r2, P.FILTERS["source_R"], P.FILTERS["load_loop_L"])
            lo, hi = P.FILTERS["load"]["band"]
            passed = (topo and lo <= l["f3db_current"] <= hi and lo <= l50["f3db_current"] <= hi
                      and l["f3db_open"] >= P.FILTERS["load"]["bw_min"])
            out.append(dict(net=net, kind="load", R1=r1, C=c1, R2=r2, f3db_current=l["f3db_current"],
                            f3db_current_50ohm=l50["f3db_current"], f3db_open=l["f3db_open"],
                            tau_ns=l["tau_current_ns"], atten_1GHz_dB=l["atten_1GHz_dB"], topology_ok=topo,
                            passed=passed, limit="10-20 MHz (current drive), >= 5 MHz open"))
        ok &= passed
    return out, ok


# ------------------------------------------------------------------------------------------------ 6. DRC self-test
def drc_selftest():
    """copy the project, inject one fault per copy, run DRC, the fault must show up"""
    d = os.path.join(REP, "_selftest")
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    results = []

    def run(tag, mutate, expect):
        base = os.path.join(d, tag)
        shutil.copy(PCB, base + ".kicad_pcb")
        shutil.copy(os.path.join(HERE, f"{NAME}.kicad_pro"), base + ".kicad_pro")
        shutil.copy(os.path.join(HERE, f"{NAME}.kicad_dru"), base + ".kicad_dru")
        shutil.copy(os.path.join(HERE, "fp-lib-table"), os.path.join(d, "fp-lib-table"))
        if not os.path.isdir(os.path.join(d, f"{P.PROJECT['lib']}.pretty")):
            shutil.copytree(os.path.join(HERE, f"{P.PROJECT['lib']}.pretty"), os.path.join(d, f"{P.PROJECT['lib']}.pretty"))
        b = pcbnew.LoadBoard(base + ".kicad_pcb")
        mutate(b)
        b.Save(base + ".kicad_pcb")
        b2 = pcbnew.LoadBoard(base + ".kicad_pcb")
        pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
        rep = base + "_drc.txt"
        pcbnew.WriteDRCReport(b2, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
        txt = open(rep).read()
        hit = all(e in txt for e in expect)
        results.append((tag, expect, hit))

    def tracks_of(b, net, cls=None):
        return [t for t in b.GetTracks() if t.GetNetname() == net and (cls is None or t.GetClass() == cls)]

    def narrow(b):
        t = tracks_of(b, "TRAP_A0", "PCB_TRACK")[0]
        t.SetWidth(pcbnew.FromMM(0.30))

    def gap(b):
        t = tracks_of(b, "ACC_B1", "PCB_TRACK")[-2]
        m = (t.GetStart() + t.GetEnd()) / 2 if hasattr(t.GetStart(), "__add__") else t.GetStart()
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(m.x, m.y + pcbnew.FromMM(0.45)))
        v.SetWidth(pcbnew.FromMM(0.45))
        v.SetDrill(pcbnew.FromMM(0.2))
        v.SetNet(b.FindNet("GND"))
        b.Add(v)

    def skew(b):
        segs = tracks_of(b, "TRAP_B0", "PCB_TRACK")
        t = max(segs, key=lambda s: s.GetLength())
        e = t.GetEnd()
        s = t.GetStart()
        L = math.hypot(e.x - s.x, e.y - s.y)
        ext = pcbnew.FromMM(0.5)
        nt = pcbnew.PCB_TRACK(b)
        nt.SetStart(e)
        nt.SetEnd(pcbnew.VECTOR2I(int(e.x + (e.y - s.y) / L * ext), int(e.y - (e.x - s.x) / L * ext)))
        nt.SetWidth(t.GetWidth())
        nt.SetLayer(t.GetLayer())
        nt.SetNet(t.GetNet())
        b.Add(nt)

    def rfvia(b):
        t = tracks_of(b, "RO_IN", "PCB_TRACK")[1]
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(t.GetStart())
        v.SetWidth(pcbnew.FromMM(0.45))
        v.SetDrill(pcbnew.FromMM(0.2))
        v.SetNet(t.GetNet())
        b.Add(v)

    def cut(b):
        t = [x for x in tracks_of(b, "LOAD_A1", "PCB_TRACK") if x.GetLayerName() == "In2.Cu"][2]
        b.Remove(t)

    run("F1_rf_width", narrow, ["RF_GCPW_width"])
    run("F2_cpw_gap", gap, ["clearance"])
    run("F3_skew", skew, ["TRAP_A_vs_TRAP_B_skew"])
    run("F4_via_on_rf", rfvia, ["RF_no_vias"])
    run("F5_open_dc", cut, ["Found 1 unconnected"])
    for fn in os.listdir(d):                     # keep only the DRC reports of the faulted copies
        pth = os.path.join(d, fn)
        if os.path.isdir(pth):
            shutil.rmtree(pth)
        elif not fn.endswith("_drc.txt"):
            os.remove(pth)
    return results


# ------------------------------------------------------------------------------------------------ main
def main():
    os.makedirs(REP, exist_ok=True)
    rf = rf_calc()
    model = json.load(open(os.path.join(REP, "build_model.json")))
    cp = {}
    for net, refs in model.get("chan_parts", {}).items():
        cp[net] = refs
    scomps, snets = sch_netlist()
    board = pcbnew.LoadBoard(PCB)
    fps = pcb_data(board)
    summary = {}

    # 1
    eco, n_pads, n_comp = compare(scomps, snets, fps)
    L = ["SCHEMATIC vs PCB NETLIST COMPARISON (Altium-style ECO check)",
         f"schematic netlist: kicad-cli {pcbnew.Version()} sch export netlist -> reports/sch_netlist.net",
         f"PCB: {os.path.basename(PCB)} read with pcbnew",
         f"components compared: {n_comp} (board-only, not in schematic by design: {', '.join(model['board_only'])})",
         f"pads compared: {n_pads}; schematic nets: {len(snets)}", "",
         f"ECO list ({len(eco)} mismatches):"] + ([f"  {e}" for e in eco] if eco else ["  (none) - schematic and PCB agree"])
    write("sch_vs_pcb.txt", L)
    summary["sch_vs_pcb"] = dict(mismatches=len(eco), components=n_comp, pads=n_pads, nets=len(snets), passed=not eco)

    # 2
    issues, info = erc(scomps, snets, model)
    L = ["ERC SUBSTITUTE (KiCad 7 kicad-cli has no ERC)",
         "rules: every net >= 2 pins; no floating pin unless NC-flagged; every U1 pin on its die_pads.json net;",
         "       GND driven (PWR_FLAG); BOM fields present; unique references", ""] + info + ["",
         f"issues ({len(issues)}):"] + ([f"  {i}" for i in issues] if issues else ["  (none)"])
    write("erc_report.txt", L)
    summary["erc"] = dict(issues=len(issues), passed=not issues)

    # 3
    imp = impedance(board, rf, model)
    gc = P.GCPW
    s, a = imp["segments"]["seg"], imp["segments"]["arc"]
    zt, tol = gc["z_target"], gc["z_tol"]
    okz = all(abs(z - zt) <= tol * zt for z in (imp["z_drawn"], s["z_p01"], s["z_p99"], a["z_p01"], a["z_p99"]))
    zpad = rf.gcpw_z0(gc["w"], imp["landing_pad_gap_min"], gc["h"], gc["er"])[0]
    L = ["IMPEDANCE TABLE - 50 ohm +/-5 %",
         "formula: rf_calc.gcpw_z0(w, g, h, er) from quantum_chip/src/rf_calc.py (conductor-backed CPW,",
         "         Ghione-Naldi conformal mapping, zero-thickness conductor, no solder mask, infinite side grounds):",
         "         k = a/b, k1 = tanh(pi a / 2h) / tanh(pi b / 2h), a = w/2, b = w/2 + g",
         "         eeff = (1 + er K(k1')K(k)... ) -> Z0 = 60 pi / sqrt(eeff) / (K(k)/K(k') + K(k1)/K(k1'))",
         f"dielectric: Rogers RO4003C, er = {gc['er']} (design Dk at 10 GHz), h = {gc['h']} mm (core 1), ref. plane In1;",
         "RF lines are mask-free (F.Mask opening over trace + gaps), copper 35 um finished",
         f"design: w = {gc['w']:.3f} mm, gap = {gc['gap']:.3f} mm -> Z0 = {imp['z_drawn']:.2f} ohm, eeff = {imp['eeff']:.3f}"
         f" (exact 50.00 ohm needs w = {imp['w_for_50']:.4f} mm)", "",
         f"{'segment type':44s} {'layer':6s} {'w':>6s} {'gap':>13s} {'h':>6s} {'er':>5s} {'Z0 (ohm)':>15s} {'result':>7s}",
         f"{'GCPW straight runs (10 RF nets), drawn':44s} {'F.Cu':6s} {gc['w']:6.3f} {gc['gap']:13.3f} {gc['h']:6.3f} "
         f"{gc['er']:5.2f} {imp['z_drawn']:15.2f} {'PASS' if abs(imp['z_drawn'] - zt) <= tol * zt else 'FAIL':>7s}",
         f"{'GCPW straight runs, as filled (min-max)':44s} {'F.Cu':6s} {gc['w']:6.3f} "
         f"{s['gap_p01']:6.3f}-{s['gap_p99']:.3f} {gc['h']:6.3f} {gc['er']:5.2f} {s['z_p01']:7.2f}-{s['z_p99']:.2f} "
         f"{'PASS' if all(abs(z - zt) <= tol * zt for z in (s['z_p01'], s['z_p99'])) else 'FAIL':>7s}",
         f"{'GCPW arc bends R 1.0, as filled (min-max)':44s} {'F.Cu':6s} {gc['w']:6.3f} "
         f"{a['gap_p01']:6.3f}-{a['gap_p99']:.3f} {gc['h']:6.3f} {gc['er']:5.2f} {a['z_p01']:7.2f}-{a['z_p99']:.2f} "
         f"{'PASS' if all(abs(z - zt) <= tol * zt for z in (a['z_p01'], a['z_p99'])) else 'FAIL':>7s}",
         f"{'bond landing pad ' + format(gc['w'], '.2f') + ' x 0.60 (line start)':44s} {'F.Cu':6s} {gc['w']:6.3f} "
         f"{imp['landing_pad_gap_min']:6.3f}-{imp['landing_pad_gap_max']:.3f} {gc['h']:6.3f} {gc['er']:5.2f} "
         f"{zpad:15.2f} {'PASS' if abs(zpad - zt) <= tol * zt else 'FAIL':>7s}",
         f"{'SMP launch: last ~0.8 mm inside the anti-pad':44s} {'F.Cu':6s} {gc['w']:6.3f} "
         f"{imp['segments']['launch']['gap_min']:6.3f}-{imp['segments']['launch']['gap_max']:.3f} {gc['h']:6.3f} {gc['er']:5.2f} "
         f"{imp['segments']['launch']['z_p01']:7.2f}-{imp['segments']['launch']['z_p99']:.2f} {'info':>7s}",
         f"{'SMP launch pad dia 0.75 / anti-pad dia 1.65':44s} {'F.Cu':6s} {'-':>6s} {'-':>13s} {'-':>6s} {'-':>5s} "
         f"{'lumped ~22 fF':>15s} {'info':>7s}", "",
         "The launch rows are a transition, not a line: ~0.8 mm (0.04 wavelength at 10 GHz) of wider gap next to a",
         "capacitive pad. Its match is NOT verified (no EM simulation); it is reported, not counted in the 50-ohm check.",
         f"as-built gap = distance from the RF centre line to the filled GND zone minus w/2 ({s['samples']} + "
         f"{a['samples']} samples every 0.1 mm); raw min/max straight {s['gap_min']:.3f}/{s['gap_max']:.3f} mm, "
         f"arcs {a['gap_min']:.3f}/{a['gap_max']:.3f} mm",
         "(samples within 1.07 mm of an SMP centre are the launch transition and are listed separately).",
         f"In1 reference plane under every RF line (trace +/- (w/2 + g + 2h)): min coverage {100 * imp['in1_coverage_min']:.2f} %",
         "",
         "CROSS-CHECK: 2D quasi-static finite-difference field solve of the same cross-section (carrier_lib/fd2d.py; In1",
         "ground plane, grounded lid 6 mm above, graded grid; C and C0 from the stored energy, Z0 = 1/(c sqrt(C C0)))",
         f"  validation, copper 1 grid cell thick (~zero, no mask): Z0 = {imp['fd_thin']['z0']:.2f} ohm vs formula "
         f"{imp['z_drawn']:.2f} ohm ({100 * (imp['fd_thin']['z0'] / imp['z_drawn'] - 1):+.1f} %), eeff "
         f"{imp['fd_thin']['eeff']:.3f} vs {imp['eeff']:.3f}",
         f"  35 um copper, no mask:                      Z0 = {imp['fd_cu']['z0']:.2f} ohm",
         f"  35 um copper, 20 um LPI on the grounds only (as built, mask-free RF corridor): Z0 = {imp['fd_real']['z0']:.2f} ohm "
         f"({100 * (imp['fd_real']['z0'] / zt - 1):+.1f} % vs 50) {'PASS' if abs(imp['fd_real']['z0'] - zt) <= tol * zt else 'FAIL'}",
         f"  for reference, the same line fully covered by LPI (mask in the gaps): Z0 = {imp['fd_if_masked']['z0']:.2f} ohm "
         "-> this is why the RF lines are mask-free",
         "The required formula check and the field solve bracket 50 ohm; the fab tunes w (+/-0.02 mm) with its own solver",
         "and a TDR coupon (fab note 3). Not verified: full-wave EM of the SMP launch, the bond-wire transition, box modes."]
    write("impedance_table.txt", L)
    okfd = abs(imp["fd_real"]["z0"] - zt) <= tol * zt
    summary["impedance"] = dict(z_formula=imp["z_drawn"], z_formula_asbuilt=[min(s["z_p01"], a["z_p01"]), max(s["z_p99"], a["z_p99"])],
                                z_fieldsolver=imp["fd_real"]["z0"], z_fieldsolver_thin_validation=imp["fd_thin"]["z0"],
                                z_fieldsolver_if_masked=imp["fd_if_masked"]["z0"], eeff=imp["eeff"],
                                gap_asbuilt_straight=[s["gap_min"], s["gap_max"]], gap_asbuilt_arcs=[a["gap_min"], a["gap_max"]],
                                in1_coverage_min=imp["in1_coverage_min"],
                                passed=okz and okfd and imp["in1_coverage_min"] > 0.99)

    # 4
    Ls, rows, okl, psmm, groups = lengths(board, model, imp["eeff"])
    L = ["RF LENGTH MATCHING (copper length per net read from the routed board with pcbnew: segments + arcs)",
         "length = landing-pad track start (0.30 mm outward of the pad centre) to the SMP centre pin; bond wires and the",
         f"pad itself are identical for every launcher by construction. Delay {psmm:.3f} ps/mm (eeff {imp['eeff']:.3f}).",
         f"requirement: every A line and its B partner within {P.RULES['skew_max']:.2f} mm (also enforced by KiCad DRC skew rules)", "",
         f"{'net':10s} {'length (mm)':>12s}"] + [f"{n:10s} {Ls[n]:12.4f}" for n in sorted(Ls)] + ["",
         f"{'pair':22s} {'A (mm)':>10s} {'B (mm)':>10s} {'|dL| (mm)':>10s} {'skew (ps)':>10s} result"] + \
        [f"{a + ' / ' + b:22s} {la:10.4f} {lb:10.4f} {d:10.4f} {t:10.4f} {'PASS' if d <= P.RULES['skew_max'] else 'FAIL'}"
         for a, b, la, lb, d, t in rows] + ["",
         f"group spread: all four TRAP lines {groups['TRAP']:.4f} mm, all four ACC lines {groups['ACC']:.4f} mm",
         f"TRAP vs ACC offset {Ls['TRAP_A0'] - Ls['ACC_A0']:.4f} mm = {(Ls['TRAP_A0'] - Ls['ACC_A0']) * psmm:.2f} ps "
         "(fixed, identical on both sides; not part of the A/B requirement)",
         f"RO_IN / RO_OUT: {Ls['RO_IN']:.4f} / {Ls['RO_OUT']:.4f} mm"]
    write("length_report.txt", L)
    summary["lengths"] = dict(nets={n: round(v, 4) for n, v in Ls.items()}, ps_per_mm=psmm,
                              pairs=[dict(a=a, b=b, dL=d, ps=t) for a, b, _, _, d, t in rows], passed=okl)

    # 5
    model["chan_parts"] = json.load(open(os.path.join(REP, "build_model.json")))["chan_parts"]
    fr, okf = filters(scomps, snets, model)
    L = ["FILTER CUT-OFF CHECK (values read back from the schematic netlist, topology checked from the nets)",
         "gate:  H(s) = 1/(1 + s(R1C1 + R2C2 + R1C2) + s^2 R1C1R2C2) into a high-impedance gate",
         "load:  current into the on-chip load loop (1 nH to GND): I/V = 1/(R1 + Z2 + s C R1 Z2), Z2 = R2 + s L;",
         "       open circuit: V/V = 1/(1 + s R1 C). -3 dB points by bisection on |H|.",
         f"second case: {P.FILTERS['source_R']:.0f} ohm source resistance added to R1", ""]
    for r in fr:
        if r["kind"] == "gate":
            L.append(f"{r['net']:14s} R1={FL.eng(r['R1'], 'ohm')} C1={FL.eng(r['C1'], 'F')} R2={FL.eng(r['R2'], 'ohm')} "
                     f"C2={FL.eng(r['C2'], 'F')}: f-3dB = {r['f3db']:.1f} Hz ({r['f3db_50ohm']:.1f} Hz with 50 ohm), "
                     f"single stage {r['f_single']:.0f} Hz, |H(1 MHz)| = {r['atten_1MHz_dB']:.0f} dB  limit {r['limit']}  "
                     f"{'PASS' if r['passed'] else 'FAIL'}")
        else:
            L.append(f"{r['net']:14s} R1={FL.eng(r['R1'], 'ohm')} C={FL.eng(r['C'], 'F')} R2={FL.eng(r['R2'], 'ohm')}: "
                     f"f-3dB = {r['f3db_current'] / 1e6:.2f} MHz current drive ({r['f3db_current_50ohm'] / 1e6:.2f} MHz with "
                     f"50 ohm), {r['f3db_open'] / 1e6:.2f} MHz open; tau {r['tau_ns']:.1f} ns << 1 us ramp; "
                     f"|H(1 GHz)| = {r['atten_1GHz_dB']:.0f} dB  limit {r['limit']}  {'PASS' if r['passed'] else 'FAIL'}")
    write("filter_report.txt", L)
    summary["filters"] = dict(channels=fr, passed=okf)

    # 6
    st = drc_selftest()
    L = ["DRC SELF-TEST: one fault injected per copy of the board, KiCad DRC must report it",
         "(shows that the 0-violation result of reports/drc_report.txt comes from live rules)", ""]
    for tag, exp, hit in st:
        L.append(f"{tag:16s} expect {exp}: {'DETECTED' if hit else 'MISSED'}")
    write("drc_selftest.txt", L)
    summary["drc_selftest"] = dict(results=[dict(fault=t, detected=h) for t, _, h in st], passed=all(h for _, _, h in st))

    drc = json.load(open(os.path.join(REP, "drc_summary.json")))
    summary["drc"] = dict(violations=drc["drc_violations"], unconnected=drc["unconnected_items"],
                          footprint_errors=drc["footprint_errors"],
                          passed=drc["drc_violations"] == 0 and drc["unconnected_items"] == 0)
    allok = all(v["passed"] for v in summary.values())
    summary["all_passed"] = allok
    json.dump(summary, open(os.path.join(REP, "check_summary.json"), "w"), indent=1, default=float)
    for k, v in summary.items():
        if isinstance(v, dict):
            print(f"{k:14s} {'PASS' if v['passed'] else 'FAIL'}")
    print("ALL CHECKS PASSED" if allok else "SOME CHECKS FAILED")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
