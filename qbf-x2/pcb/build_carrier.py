#!/usr/bin/env python3
"""Write the complete QBF-X2 carrier KiCad 7 project from scratch.

Inputs : carrier_params.py (all design choices), ../circuits/die_pads.json (chip-to-board contract),
         ../../quantum_chip/src/rf_calc.py (impedance formulas, read only).
Outputs: qbfx2_carrier.kicad_sch, .kicad_pcb (zones unfilled), .kicad_pro, .kicad_dru,
         qbfx2.kicad_sym, qbfx2.pretty/, sym-lib-table, fp-lib-table, 3dmodels/*.step,
         reports/build_model.json (design intent for check_carrier.py), reports/sch_netlist.net
Flow   : connectivity model -> schematic -> KiCad netlister (kicad-cli) -> net names -> routed board.
"""
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys

from shapely.geometry import LineString, Point, Polygon, box as sbox
from shapely.ops import unary_union
from shapely.prepared import prep

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import carrier_params as P  # noqa: E402
from carrier_lib import geom as G  # noqa: E402
from carrier_lib import footprints as FPL  # noqa: E402
from carrier_lib import schematic as SC  # noqa: E402
from carrier_lib import drawings as DW  # noqa: E402
from carrier_lib import filters as FL  # noqa: E402
from carrier_lib import diffpair as DP  # noqa: E402
from carrier_lib.sexpr import parse as sparse  # noqa: E402

NAME = P.PROJECT["name"]
LIB = P.PROJECT["lib"]
REPORTS = os.path.join(HERE, "reports")
X0, Y0 = P.BOARD["page_origin"]


from carrier_lib.ids import U  # noqa: E402  (deterministic ids)


def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def K(p):
    """board frame (y up) -> KiCad page (y down)"""
    return (X0 + p[0], Y0 - p[1])


def load_rf_calc():
    spec = importlib.util.spec_from_file_location("rf_calc_qfx1", P.RF_CALC_PY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# =============================================================================================== A. die contract
def load_die():
    d = json.load(open(P.DIE_PADS_JSON))
    sx, sy = d["die_size_um"]
    assert abs(sx - sy) < 1e-9, "square die expected"
    size = sx / 1000.0
    pads = []
    for p in d["pads"]:
        c = (p["pad_center_um"][0] / 1000.0 - size / 2, p["pad_center_um"][1] / 1000.0 - size / 2)
        u = (int(p["outward"][0]), int(p["outward"][1]))
        pads.append(dict(id=int(p["id"]), net=p["net"], kind=p["kind"], side=p["side"], c=c, u=u,
                         lat=c[1] if u[0] else c[0], size_um=tuple(p["pad_size_um"]), pair=p.get("pair"),
                         polarity=p.get("polarity")))
    kinds = {}
    for p in pads:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    assert kinds == d["counts"], f"die_pads.json counts mismatch {kinds} vs {d['counts']}"
    assert sorted(p["id"] for p in pads) == list(range(1, len(pads) + 1)), "die pad ids must be 1..N"
    assert len(pads) == 32, "die_pads.json rev B (32 launchers) expected"
    return d, size, pads


def side_lists(pads):
    S = {}
    for s in "NESW":
        L = [p for p in pads if p["side"] == s]
        L.sort(key=(lambda p: p["c"][0]) if s in "NS" else (lambda p: -p["c"][1]))
        S[s] = L
    return S


def side_pairs(L):
    """fast-line pads of one W/E side (top -> bottom) grouped as [(pair, P pad, N pad)]"""
    fast = [p for p in L if p["kind"] == "rf_fast_diff"]
    out = []
    for a, b in zip(fast[0::2], fast[1::2]):
        out.append((a["pair"], a, b))
    return out


def check_topology(S, die):
    """the routing topology below is designed for this arrangement; fail loudly if the contract changes"""
    want = {"N": ["ground", "dc_gate", "ground", "ground", "dc_gate", "ground"],
            "S": ["rf_readout", "dc_gate", "ground", "ground", "dc_gate", "rf_readout"],
            "W": ["dc_ramp"] + ["rf_fast_diff"] * 8 + ["dc_ramp"],
            "E": ["dc_ramp"] + ["rf_fast_diff"] * 8 + ["dc_ramp"]}
    for s, w in want.items():
        got = [p["kind"] for p in S[s]]
        assert got == w, f"side {s}: launcher kinds {got} differ from the routed topology {w}"
    for s in "NS":
        lats = [p["lat"] for p in S[s]]
        for a, b in zip(lats, lats[1:]):
            assert abs(abs(a - b) - 1.2) < 1e-6, "1.2 mm launcher pitch expected on the N / S rows"
    dp = die["diff_pair"]
    intra, pitch = dp["intra_pair_pitch_um"] / 1000.0, dp["pair_centre_pitch_um"] / 1000.0
    assert abs(P.DIFF["w_bo"] + P.DIFF["s_bo"] - intra) < 1e-9, "breakout leg pitch must equal the die pad pitch"
    for s, names in (("W", P.FAST_PAIRS[:4]), ("E", P.FAST_PAIRS[4:])):
        prs = side_pairs(S[s])
        assert [q[0] for q in prs] == names, f"side {s}: pair order {[q[0] for q in prs]} != {names}"
        for name, a, b in prs:
            assert (a["polarity"], b["polarity"]) == ("P", "N") and a["pair"] == b["pair"] == name
            assert (a["net"], b["net"]) == (f"{name}_P", f"{name}_N"), f"{name}: nets must be <pair>_P / <pair>_N"
            assert abs(a["lat"] - b["lat"] - intra) < 1e-9, f"{name}: P above N, {intra} mm apart expected"
        cs = [(a["lat"] + b["lat"]) / 2 for _, a, b in prs]
        assert all(abs(c0 - c1 - pitch) < 1e-9 for c0, c1 in zip(cs, cs[1:])), "pair centre pitch"
        assert abs(cs[0] + cs[3]) < 1e-9 and abs(cs[1] + cs[2]) < 1e-9, "pairs symmetric about the die axis"
        assert S[s][0]["kind"] == S[s][-1]["kind"] == "dc_ramp" and abs(S[s][0]["lat"] + S[s][-1]["lat"]) < 1e-9
    for a, b in zip(S["W"], S["E"]):
        assert abs(a["lat"] - b["lat"]) < 1e-9, "W and E rows must be mirror images"
    chans = [S["W"][0]["net"], S["W"][-1]["net"], S["S"][1]["net"], S["N"][1]["net"],
             S["N"][4]["net"], S["S"][4]["net"], S["E"][-1]["net"], S["E"][0]["net"]]
    assert chans == P.FILTER_BANK["channels"], f"filter channel order must be {chans} (planar routing)"
    assert [P.MICROD_PINS[k] for k in range(1, 9)] == chans, "J11 pins 1..8 must follow the channel order"
    assert sorted(P.SMP_REFS) == sorted(p["net"] for p in pads_all if p["kind"].startswith("rf_"))
    assert len(P.SMP_DESIGNATORS) == len(P.SMP_REFS) and "J11" not in P.SMP_DESIGNATORS
    return chans


# =============================================================================================== B. connectivity
def build_model(pads, chans):
    comps = {}

    def comp(ref, key, value, fp, part, pins, extra=None):
        comps[ref] = dict(ref=ref, sym=key, value=value, footprint=fp, part=part, pins=pins, extra=extra or {})

    comp("U1", "DIE", "QBF-X2", P.PARTS["DIE"]["footprint"], "DIE", {str(p["id"]): p["net"] for p in pads})
    for ref, net in zip(P.SMP_DESIGNATORS, P.SMP_REFS):
        comp(ref, "SMP", "SMP-MSLD-PCS-NM", P.PARTS["SMP"]["footprint"], "SMP", {"1": net, "2": "GND"})
    jp = {str(k): f"{P.MICROD_PINS[k]}_IN" for k in range(1, 9)}
    jp.update({str(k): "GND" for k in range(9, 16)})
    jp["SH"] = "GND"
    comp("J11", "MICROD", "MWDM2L-15PCBRP-.110", P.PARTS["MICROD"]["footprint"], "MICROD", jp)
    rn = cn = 0
    chan_parts = {}
    F = P.FILTERS
    for net in chans:
        gate = net.startswith("GATE_")
        rn += 1
        ra = f"R{rn}"
        rn += 1
        rb = f"R{rn}"
        cn += 1
        ca = f"C{cn}"
        a = f"{net}_NA"
        if gate:
            comp(ra, "R", "10k", P.PARTS["R10K"]["footprint"], "R10K", {"1": f"{net}_IN", "2": a})
            comp(ca, "C", "10n C0G", P.PARTS["C10N"]["footprint"], "C10N", {"1": a, "2": "GND"})
            comp(rb, "R", "10k", P.PARTS["R10K"]["footprint"], "R10K", {"1": a, "2": net})
            cn += 1
            cb = f"C{cn}"
            comp(cb, "C", "10n C0G", P.PARTS["C10N"]["footprint"], "C10N", {"1": net, "2": "GND"})
            chan_parts[net] = dict(gate=True, R1=ra, C1=ca, R2=rb, C2=cb)
        else:
            comp(ra, "R", "1k", P.PARTS["R1K"]["footprint"], "R1K", {"1": f"{net}_IN", "2": a})
            comp(ca, "C", "18p C0G", P.PARTS["C18P"]["footprint"], "C18P", {"1": a, "2": "GND"})
            comp(rb, "R", "1k", P.PARTS["R1K"]["footprint"], "R1K", {"1": a, "2": net})
            chan_parts[net] = dict(gate=False, R1=ra, C1=ca, R2=rb)
    assert abs(F["gate"]["R1"] - 10e3) < 1 and abs(F["gate"]["C1"] - 10e-9) < 1e-12, "values / BOM mismatch"
    assert abs(F["load"]["R1"] - 1e3) < 1 and abs(F["load"]["C"] - 18e-12) < 1e-15, "values / BOM mismatch"
    for i in range(4):
        comp(f"H{i + 1}", "MH", "M2.5", P.PARTS["MH"]["footprint"], "MH", {"1": "GND"})
    nets = {}
    for c in comps.values():
        for pin, n in c["pins"].items():
            nets.setdefault(n, set()).add((c["ref"], pin))
    return comps, nets, chan_parts


# =============================================================================================== C. schematic
def write_schematic(comps, chans, chan_parts, side):
    g = SC.g
    die_pins = []
    for s in "NESW":
        for k, p in enumerate(side[s]):
            die_pins.append((p["id"], p["net"], s, k))
    md_names = {k: (P.MICROD_PINS[k] if k <= 8 else "GND") for k in range(1, 16)}
    S = SC.library(LIB, die_pins, md_names)
    sh = SC.Sheet(NAME, "A3")
    uuids = {}

    def fields(c):
        pt = P.PARTS[c["part"]]
        return {"Manufacturer": pt["mfr"], "MPN": pt["mpn"], "MPN status": pt["status"],
                "Description": pt["descr"], "Note": pt["note"]}

    def fpid(c):
        return f"{LIB}:{c['footprint']}"

    # --- J11 micro-D (left)
    j = comps["J11"]
    pos = (g(22), g(80))
    pins, uuids["J11"] = sh.place(S["MICROD"], "J11", j["value"], pos, 0, fields(j), fpid(j),
                                  ref_off=(-g(3), -g(19.5)), val_off=(-g(3), -g(17.5)))
    for k in range(1, 9):
        a = pins[str(k)]
        b = (a[0] + g(4), a[1])
        sh.wire(a, b)
        sh.glabel(f"{P.MICROD_PINS[k]}_IN", b, 0)
    bus_x = pins["9"][0] + g(3)
    ys = [pins[str(k)][1] for k in range(9, 16)]
    for k in range(9, 16):
        a = pins[str(k)]
        sh.wire(a, (bus_x, a[1]))
    for y0, y1 in zip(ys, ys[1:]):
        sh.wire((bus_x, y0), (bus_x, y1))
    for y in ys[1:-1]:
        sh.junction((bus_x, y))
    gnd_pt = (bus_x, ys[-1] + g(4))
    sh.wire((bus_x, ys[-1]), gnd_pt)
    sh.junction((bus_x, ys[-1]))
    sh.gnd(S, gnd_pt)
    flag_pt = (bus_x + g(4), gnd_pt[1])
    sh.wire(gnd_pt, flag_pt)
    sh.flag(S, flag_pt)
    sh.gnd(S, pins["SH"])
    sh.text("J11: DC input, Glenair MWDM2L-15PCBRP-.110\nmicro-D 15P right angle (non-magnetic shell\nfinish to confirm). "
            "Pins 1-8 = filtered DC,\n9-15 + shell = GND returns.", (g(10), g(110)), 1.27)

    # --- filter bank (middle)
    co = FL.all_cutoffs(P.FILTERS)
    y = g(34)
    for net in chans:
        cp = chan_parts[net]
        gate = cp["gate"]
        if gate:
            ttl = (f"{net}: 2-stage RC, R = 10 kOhm, C = 10 nF C0G  ->  f(-3 dB) = {co['gate']['f3db']:.0f} Hz "
                   f"(single stage 1/2piRC = {co['gate']['f_single'] / 1e3:.2f} kHz)")
        else:
            ttl = (f"{net}: R-C-R tee, R1 = R2 = 1.0 kOhm, C = 18 pF C0G  ->  f(-3 dB) = "
                   f"{co['load']['f3db_current'] / 1e6:.1f} MHz into the on-chip load loop (current), "
                   f"{co['load']['f3db_open'] / 1e6:.2f} MHz open")
        sh.text(ttl, (g(64), y - g(5)), 1.27)
        sh.glabel(f"{net}_IN", (g(64), y), 180)
        ra = comps[cp["R1"]]
        pr, uuids[cp["R1"]] = sh.place(S["R"], cp["R1"], ra["value"], (g(73), y), 0, fields(ra), fpid(ra))
        sh.wire((g(64), y), pr["1"])
        na = (g(82), y)
        sh.wire(pr["2"], na)
        c1 = comps[cp["C1"]]
        pc, uuids[cp["C1"]] = sh.place(S["C"], cp["C1"], c1["value"], (na[0], y + g(6)), 0, fields(c1), fpid(c1),
                                       ref_off=(g(1.6), -g(0.8)), val_off=(g(1.6), g(1.2)), justify="left")
        sh.wire(na, pc["1"])
        sh.gnd(S, pc["2"])
        rb = comps[cp["R2"]]
        pr2, uuids[cp["R2"]] = sh.place(S["R"], cp["R2"], rb["value"], (g(91), y), 0, fields(rb), fpid(rb))
        sh.wire(na, pr2["1"])
        sh.junction(na)
        if gate:
            nb = (g(100), y)
            sh.wire(pr2["2"], nb)
            c2 = comps[cp["C2"]]
            pc2, uuids[cp["C2"]] = sh.place(S["C"], cp["C2"], c2["value"], (nb[0], y + g(6)), 0, fields(c2), fpid(c2),
                                            ref_off=(g(1.6), -g(0.8)), val_off=(g(1.6), g(1.2)), justify="left")
            sh.wire(nb, pc2["1"])
            sh.gnd(S, pc2["2"])
            sh.wire(nb, (g(108), y))
            sh.junction(nb)
        else:
            sh.wire(pr2["2"], (g(108), y))
        sh.glabel(net, (g(108), y), 0)
        y += g(18)
    sh.box((g(60), g(26)), (g(150), y - g(6)))
    sh.text("ON-BOARD DC FILTERS (top side, next to J11; routed to the die on In2 between GND planes)",
            (g(60), g(23)), 1.5, True)

    # --- U1 die (right)
    u = comps["U1"]
    cpos = (g(192), g(98))
    pu, uuids["U1"] = sh.place(S["DIE"], "U1", "QBF-X2", cpos, 0, fields(u), fpid(u),
                               ref_off=(g(23), g(-25)), val_off=(g(23), g(-23.5)), justify="left")
    for s in "NESW":
        for p in side[s]:
            a = pu[str(p["id"])]
            d = {"N": (0, -g(2)), "S": (0, g(2)), "W": (-g(2), 0), "E": (g(2), 0)}[s]
            b = (a[0] + d[0], a[1] + d[1])
            sh.wire(a, b)
            if p["net"] == "GND":
                sh.gnd(S, b, 180 if s == "N" else 0)
            else:
                sh.glabel(p["net"], b, {"N": 90, "S": 270, "W": 180, "E": 0}[s])
    sh.text(f"U1 = QBF-X2 die (10 x 10 x 0.525 mm), wire bonded to the {len(side['N']) + len(side['E']) + len(side['S']) + len(side['W'])}"
            " PCB landing pads; pin = die_pads.json id", (g(160), g(148)), 1.27)
    sh.text("Every U1 pin net and number follows circuits/die_pads.json rev B (checked in reports/erc_report.txt)",
            (g(160), g(150)), 1.27)

    # --- SMP connectors (far right): west pairs, east pairs, readout
    for i, (ref, net) in enumerate(zip(P.SMP_DESIGNATORS, P.SMP_REFS)):
        col, row = (0, i) if i < 8 else (1, i - 8) if i < 16 else (i - 16, 8)   # west pairs + RO_IN | east + RO_OUT
        cx = g(252) + col * g(40)
        cy = g(32) + row * g(12) + (row // 2) * g(3)
        c = comps[ref]
        pp, uuids[ref] = sh.place(S["SMP"], ref, c["value"], (cx, cy), 0, fields(c), fpid(c),
                                  ref_off=(g(2), -g(2)), val_off=(g(2), g(1)), justify="left")
        a = pp["1"]
        b = (a[0] - g(3), a[1])
        sh.wire(a, b)
        sh.glabel(net, b, 180)
        sh.gnd(S, pp["2"])
    sh.text("RF: 18 non-magnetic SMP jacks (Amphenol RF SMP-MSLD-PCS-NM); J11 is the DC micro-D, so J1-J10, J12-J19",
            (g(226), g(20)), 1.27)
    sh.text("Fast flux lines = 8 differential pairs <name>_P / <name>_N, one 50-ohm coax per leg (Z_odd 50, Z_diff 100)",
            (g(226), g(22)), 1.27)
    sh.text("Intra-pair skew <= 0.10 mm; A/B partner pairs matched <= 0.20 mm (reports/length_report.txt)",
            (g(226), g(24)), 1.27)

    # --- mounting holes
    for i in range(4):
        ref = f"H{i + 1}"
        c = comps[ref]
        pm, uuids[ref] = sh.place(S["MH"], ref, "M2.5", (g(240) + i * g(10), g(162)), 0, fields(c), fpid(c),
                                  ref_off=(g(1.5), -g(0.5)), val_off=(g(1.5), g(1)), justify="left")
        sh.gnd(S, pm["1"])
    sh.text("H1-H4: M2.5 plated mounting holes to the Cu sample-holder base (GND)", (g(236), g(156)), 1.27)

    # --- notes
    gq = co["gate"]
    lq = co["load"]
    notes = [
        "DESIGN NOTES",
        f"1. Gate lines GATE_BS*: static gate voltages. 2-stage RC ladder R1 = R2 = 10 kOhm, C1 = C2 = 10 nF C0G: "
        f"H(s) = 1/(1 + s(R1C1 + R2C2 + R1C2) + s^2 R1C1R2C2) -> f(-3 dB) = {gq['f3db']:.0f} Hz (limit <= 10 kHz).",
        f"2. Load lines LOAD_*: flux ramp 0 -> Phi0 in ~1 us into a 1 nH load loop shorted on chip (current drive). "
        f"Tee R1 = R2 = 1.0 kOhm, C = 18 pF: I/V = 1/(R1 + R2 + sC R1 R2) -> f(-3 dB) = 1/(2 pi C R1||R2) = "
        f"{lq['f3db_current'] / 1e6:.1f} MHz (target 10-20 MHz);",
        f"   into a high-impedance load 1/(2 pi R1 C) = {lq['f3db_open'] / 1e6:.2f} MHz. Both pass the 1 us ramp "
        f"(bandwidth >= 5 MHz; tau = {lq['tau_current_ns']:.1f} ns).",
        "3. Parts for 10 mK: thin-film non-magnetic resistors (Vishay PNM), C0G/NP0 non-magnetic MLCC (Vishay VJ "
        "Non-Magnetic, Cu barrier), non-magnetic SMP. No ferrite, no X7R, no Ni-barrier terminations.",
        "4. RF lines are DC-coupled, no on-board components on RF nets. Rev B: each fast flux line is a differential "
        "pair <name>_P / <name>_N = the two ends of ONE floating on-chip loop (no ground return), driven by "
        "complementary AWG outputs,",
        "   one 50-ohm coax per leg: loosely coupled edge-coupled GCPW, Z_odd 50 ohm (Z_diff 100 ohm), Z_even close "
        "to 50 ohm; intra-pair skew <= 0.10 mm (~0.5 ps). KiCad recognises the _P / _N suffix as a differential pair.",
        "5. Net names = circuits/die_pads.json (rev B, 32 pads). Generated by pcb/build_carrier.py from "
        "pcb/carrier_params.py - edit the parameters, not this sheet.",
    ]
    yy = g(196)
    for n in notes:
        sh.text(n, (g(14), yy), 1.27, n == "DESIGN NOTES")
        yy += g(2.4)
    tb = {"title": P.PROJECT["title"], "date": P.PROJECT["date"], "rev": P.PROJECT["rev"],
          "company": P.PROJECT["author"], "comment1": f"Author: {P.PROJECT['author']}",
          "comment2": "Rev B: die U1, 8 diff. fast-flux pairs + 2 readout on 18 SMP, 8 DC on J11",
          "comment3": f"6-layer Rogers RO4003C / RO4450F, {P.BOARD['x_max'] - P.BOARD['x_min']:.0f} x "
                      f"{P.BOARD['y_max'] - P.BOARD['y_min']:.0f} mm",
          "comment4": "Generated by pcb/build_carrier.py (carrier_params.py = single source of truth)"}
    sh.write(os.path.join(HERE, f"{NAME}.kicad_sch"), tb)
    with open(os.path.join(HERE, f"{LIB}.kicad_sym"), "w") as fh:
        fh.write(SC.symbol_library_text(S))
    return uuids, S


def kicad_netlist():
    out = os.path.join(REPORTS, "sch_netlist.net")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out,
                    os.path.join(HERE, f"{NAME}.kicad_sch")], check=True, capture_output=True)
    tree = sparse(open(out).read())
    nets = {}
    for net in [n for n in tree if isinstance(n, list) and n and n[0] == "nets"][0][1:]:
        name = [x for x in net if isinstance(x, list) and x[0] == "name"][0][1]
        nodes = set()
        for nd in net:
            if isinstance(nd, list) and nd[0] == "node":
                d = {x[0]: x[1] for x in nd[1:] if isinstance(x, list)}
                nodes.add((d["ref"], d["pin"]))
        nets[name] = nodes
    return nets


# =============================================================================================== D. board geometry
class Board:
    def __init__(self):
        self.tracks = []        # dict(layer, net, w, path)
        self.vias = []          # dict(at, net, drill, size, kind)
        self.fps = []           # dict(ref, fp, pos, rot, value, netmap)
        self.gfx = DW.Drawing()
        self.rf = {}            # net -> dict(path, conn, rot)


def diff_routes(B, side):
    """8 fast-line differential pairs: the W-top pair of each kind (TRAP, ACC) is built once by
    carrier_lib.diffpair.quadrant_pair; the other quadrants are its mirror images. Canonical legs: R = outer (away from
    the die axis), L = inner. Top quadrants: outer = P; bottom quadrants (mirror in y): outer = N."""
    W = HALF + P.WINDOW["clearance"]
    x_start = W + P.BONDPAD["setback"] + P.BONDPAD["length"] / 2 + P.BOARD["track_start_in_pad"]
    D, F = P.DIFF, P.FAST
    pairs = {s: side_pairs(side[s]) for s in "WE"}
    canon = {}
    for kind in ("TRAP", "ACC"):
        name, a, b = [q for q in pairs["W"] if q[0].startswith(kind) and q[1]["lat"] > 0][0]
        yc = (a["lat"] + b["lat"]) / 2
        jk = F["y_jacks"][kind]
        canon[kind] = DP.quadrant_pair(x_start, yc, sum(jk) / 2, F["x_conn"], jk, F[kind], D)
    B.pairs = {}
    for s in "WE":
        sx = 1 if s == "W" else -1                      # canonical frame is the west side
        for name, a, b in pairs[s]:
            sy = 1 if a["lat"] > 0 else -1
            kind = "TRAP" if name.startswith("TRAP") else "ACC"
            cp = canon[kind]
            outer, inner = (a, b) if abs(a["lat"]) > abs(b["lat"]) else (b, a)
            legs = {}
            for leg, pad in (("R", outer), ("L", inner)):
                t = cp["T"][leg]
                path = DP.transform(t.path, sx, sy)
                n_c = cp["coupled_end"][leg]
                full, ws, tags, src = DP.add_stubs(path, t.widths, t.tags, pad_ends=(True, True))
                n_cp = sum(1 for k in src if k < n_c)              # primitives of the coupled section
                nm = DP.snap_nm(full, (X0, Y0), tags)
                legs[pad["polarity"]] = dict(net=pad["net"], leg=leg, path=full, widths=ws, tags=tags,
                                            n_coupled=n_cp, role="outer" if leg == "R" else "inner", nm=nm)
                B.rf[pad["net"]] = dict(points=[full[0][1], full[-1][2]], path=full, conn=full[-1][2],
                                        rot=180 if s == "W" else 0, side=s, pair=name, widths=ws,
                                        n_coupled=n_cp, nm=nm)
            centre = DP.transform(cp["T"]["C"].path, sx, sy)
            # region between the leg centre lines over the coupled part: no ground copper, no vias (F.Cu keepout)
            region = DP.coupled_region(DP.transform(cp["T"]["L"].path, sx, sy), DP.transform(cp["T"]["R"].path, sx, sy),
                                       cp["coupled_end"]["L"], cp["coupled_end"]["R"])
            B.pairs[name] = dict(kind=kind, side=s, sx=sx, sy=sy, legs=legs, centre=centre, region=region,
                                 log=cp["log"], vertices=[(sx * v[0], sy * v[1]) for v in cp["vertices"]],
                                 straights=cp["straights"])
            for pol in ("P", "N"):
                lg = legs[pol]
                k = 0
                while k < len(lg["path"]):                     # one track per run of equal width
                    j = k
                    while j + 1 < len(lg["path"]) and abs(lg["widths"][j + 1] - lg["widths"][k]) < 1e-9:
                        j += 1
                    B.tracks.append(dict(layer="F.Cu", net=lg["net"], w=lg["widths"][k], path=lg["path"][k:j + 1],
                                         kind="rf", pair=name, nm=lg["nm"][k:j + 1]))
                    k = j + 1


def rf_routes(B, side):
    W = HALF + P.WINDOW["clearance"]
    rc = W + P.BONDPAD["setback"] + P.BONDPAD["length"] / 2 + P.BOARD["track_start_in_pad"]
    R = P.READOUT
    diff_routes(B, side)
    for p in side["S"]:
        if p["kind"] != "rf_readout":
            continue
        x0 = p["lat"]
        sg = 1 if x0 > 0 else -1
        xc = sg * R["x_conn"]
        yb = -R["y_bend"]
        pts = [(x0, -rc), (x0, yb), (xc, yb - abs(xc - x0)), (xc, R["y_conn"])]
        B.rf[p["net"]] = dict(points=pts, path=G.fillet(pts, P.GCPW["bend_r"]), conn=pts[-1], rot=270, side="S")
        B.tracks.append(dict(layer="F.Cu", net=p["net"], w=P.GCPW["w"], path=B.rf[p["net"]]["path"], kind="rf"))


def dc_routes(B, side, chans):
    """F.Cu stubs from the bond pads to vias, In2 routing to the filter bank (planar, see README)"""
    W = HALF + P.WINDOW["clearance"]
    rc = W + P.BONDPAD["setback"] + P.BONDPAD["length"] / 2 + P.BOARD["track_start_in_pad"]
    D = P.DC
    o1, o2 = D["corridor"]
    j = D["jog"]
    ji, jo = D["corner_jog"]
    eyi, eyo = D["exit_y"]
    xin = abs(side["N"][1]["lat"])
    pitch = P.FILTER_BANK["pitch"]
    xch = [-(xin + 3 * pitch), -(xin + 2 * pitch), -(xin + pitch), -xin, xin, xin + pitch, xin + 2 * pitch, xin + 3 * pitch]
    yv = P.FILTER_BANK["y_out_via"]
    B.chan_x = dict(zip(chans, xch))
    dvia = dict(drill=P.VIAS["dc_drill"], size=P.VIAS["dc_pad"], kind="dc")
    wf, wi = D["fcu_width"], D["in2_width"]
    B.dc_paths = {}
    for s in "WE":
        sx = -1 if s == "W" else 1
        top, bot = side[s][0], side[s][-1]
        for p in (top, bot):
            y0 = p["lat"]
            sg = 1 if y0 > 0 else -1
            v = (sx * D["via_r_from_die"], y0 + sg * D["load_via_dy"])
            stub = [(sx * rc, y0), (sx * (D["via_r_from_die"] - D["load_via_dy"]), y0), v]
            B.tracks.append(dict(layer="F.Cu", net=p["net"], w=wf, path=G.polyline_path(stub), kind="dc"))
            B.vias.append(dict(at=v, net=p["net"], **dvia))
            xc = B.chan_x[p["net"]]
            if p is top:
                pts = [v, (xc, v[1] + abs(xc - v[0])), (xc, yv)]
            else:       # rev B: join the outer corridor with a 45-degree diagonal towards the die axis, so the join
                #           stays clear of the GATE_BSB detour around the window corner (LOAD vias at |y| = 4.0)
                pts = [v, (sx * o2, v[1] + (abs(v[0]) - o2)), (sx * o2, W - jo), (sx * (o2 + j), W - jo + j),
                       (sx * (o2 + j), eyo), (xc, eyo + abs(xc - sx * (o2 + j))), (xc, yv)]
            B.tracks.append(dict(layer="In2.Cu", net=p["net"], w=wi, path=G.polyline_path(pts), kind="dc"))
            B.dc_paths[p["net"]] = pts
    for p in (side["N"][1], side["N"][4]):
        x0 = p["lat"]
        v = (x0, P.DC["gate_via_r"])
        B.tracks.append(dict(layer="F.Cu", net=p["net"], w=wf, path=G.polyline_path([(x0, rc), v]), kind="dc"))
        B.vias.append(dict(at=v, net=p["net"], **dvia))
        pts = [v, (B.chan_x[p["net"]], yv)]
        B.tracks.append(dict(layer="In2.Cu", net=p["net"], w=wi, path=G.polyline_path(pts), kind="dc"))
        B.dc_paths[p["net"]] = pts
    for p in (side["S"][1], side["S"][4]):
        x0 = p["lat"]
        sx = -1 if x0 < 0 else 1
        v = (x0, -P.DC["gate_via_r"])
        B.tracks.append(dict(layer="F.Cu", net=p["net"], w=wf, path=G.polyline_path([(x0, -rc), v]), kind="dc"))
        B.vias.append(dict(at=v, net=p["net"], **dvia))
        xc = B.chan_x[p["net"]]
        pts = [v, (x0, -o1), (sx * (W - ji), -o1), (sx * (W - ji + j), -(o1 + j)), (sx * (o1 + j), -(o1 + j)),
               (sx * (o1 + j), -(W - ji + j)), (sx * o1, -(W - ji)), (sx * o1, W - ji), (sx * (o1 + j), W - ji + j),
               (sx * (o1 + j), eyi), (xc, eyi + abs(xc - sx * (o1 + j))), (xc, yv)]
        B.tracks.append(dict(layer="In2.Cu", net=p["net"], w=wi, path=G.polyline_path(pts), kind="dc"))
        B.dc_paths[p["net"]] = pts
    return xch


def filter_bank(B, comps, chans, chan_parts, netof, fpl):
    """F.Cu: each channel a vertical chain (input at the top, J11 side); shunt C column outboard"""
    FB = P.FILTER_BANK
    yv = FB["y_out_via"]
    cdx = FB["cap_dx"]
    gdx = FB["cap_via_dx"]
    wf = P.DC["fcu_width"]
    rw = FB["rows"]
    y_r1, y_r2, y_c1, y_c2 = yv + rw["R1"], yv + rw["R2"], yv + rw["C1"], yv + rw["C2"]
    md = P.MICROD
    pin_x = {k: -3.5 * md["pitch"] + (k - 1) * md["pitch"] for k in range(1, 9)}
    levels = FB["fanin_levels"]
    gvia = dict(drill=P.VIAS["stitch_drill"], size=P.VIAS["stitch_pad"], kind="gnd_cap")
    for i, net in enumerate(chans):
        xc = B.chan_x[net]
        sgn = -1 if xc < 0 else 1
        cp = chan_parts[net]
        place = [(cp["R1"], (xc, y_r1)), (cp["R2"], (xc, y_r2)), (cp["C1"], (xc + sgn * cdx, y_c1))]
        if cp["gate"]:
            place.append((cp["C2"], (xc + sgn * cdx, y_c2)))
        for ref, pos in place:
            c = comps[ref]
            B.fps.append(dict(ref=ref, fp=fpl[c["footprint"]], pos=pos, rot=270, value=c["value"], comp=c))
        pr1 = y_r1 + 0.825
        pr1b = y_r1 - 0.825
        pr2a, pr2b = y_r2 + 0.825, y_r2 - 0.825
        pc1a, pc1b = y_c1 + 0.775, y_c1 - 0.775
        n_in, n_a = netof(cp["R1"], "1"), netof(cp["R1"], "2")
        n_out = netof(cp["R2"], "2")
        k = i + 1
        lv = levels[i]
        tr = [(n_in, [(xc, pr1), (xc, lv), (pin_x[k], lv), (pin_x[k], md["y_row1"])]),
              (n_a, [(xc, pr1b), (xc, pr2a)]), (n_a, [(xc, pr1b), (xc + sgn * cdx, pc1a)]),
              (n_out, [(xc, pr2b), (xc, yv)]),
              ("GND", [(xc + sgn * cdx, pc1b), (xc + sgn * gdx, pc1b)])]
        B.vias.append(dict(at=(xc + sgn * gdx, pc1b), net="GND", **gvia))
        if cp["gate"]:
            pc2a, pc2b = y_c2 + 0.775, y_c2 - 0.775
            tr.append((n_out, [(xc, pr2b), (xc + sgn * cdx, pc2a)]))
            tr.append(("GND", [(xc + sgn * cdx, pc2b), (xc + sgn * gdx, pc2b)]))
            B.vias.append(dict(at=(xc + sgn * gdx, pc2b), net="GND", **gvia))
        for n, pts in tr:
            pts = [q for q in pts]
            B.tracks.append(dict(layer="F.Cu", net=n, w=wf if n != "GND" else 0.3, path=G.polyline_path(pts),
                                 kind="dc" if n != "GND" else "gnd"))
        B.vias.append(dict(at=(xc, yv), net=n_out, drill=P.VIAS["dc_drill"], size=P.VIAS["dc_pad"], kind="dc"))


# =============================================================================================== E. vias
def stitching(B, window_poly, board_poly, pad_geoms, no_via=()):
    """GND vias: bond-strip row, SMP launch cages, GCPW fences, hole rings, edge row, background grid.
    no_via: extra areas kept free of stitching vias (the board-level silkscreen texts)"""
    V = P.VIAS
    r = V["stitch_pad"] / 2
    eps = 0.005
    forbid = [q.buffer(r + 0.02) for q in no_via]
    for t in B.tracks:
        line = LineString(G.path_to_polyline(t["path"], 0.05))
        if t["net"] == "GND":
            continue
        clr = P.GCPW["gap"] if t["kind"] == "rf" else P.DC["clearance"]
        forbid.append(line.buffer(t["w"] / 2 + clr + r + eps))
    for v in B.vias:
        if v["net"] == "GND":
            continue
        forbid.append(Point(v["at"]).buffer(v["size"] / 2 + P.DC["clearance"] + r + eps))
    for pg in pad_geoms:
        if pg["net"] == "GND":
            margin = r + 0.05 if not pg["th"] else max(r + 0.05, (pg["drill"] or 0) / 2 + P.RULES["min_hole_to_hole"] + 0.1)
        elif pg["net"] == "":
            margin = r + (0.3 if pg["npth"] else 0.6)
        else:
            margin = pg["clearance"] + r + eps
        forbid.append(pg["poly"].buffer(margin))
    forbid.append(window_poly.buffer(P.RULES["via_edge_clearance"] + r + eps))
    Wb = HALF + P.WINDOW["clearance"] + P.BONDPAD["ring_open_out"] + 0.2
    forbid.append(sbox(-Wb, -Wb, Wb, Wb))
    for pr in getattr(B, "pairs", {}).values():                 # no vias between P and N of a coupled pair
        forbid.append(pr["region"].buffer(r + eps))
    forbid.append(board_poly.difference(board_poly.buffer(-(P.RULES["via_edge_clearance"] + r + eps))))
    smp_bodies = [Point(rr["conn"]).buffer(2.45) for rr in B.rf.values()]
    hard = prep(unary_union(forbid))
    soft = prep(unary_union(smp_bodies))
    placed = [v["at"] for v in B.vias]
    stitch = []

    def ok(pt, allow_body=False):
        if hard.contains(Point(pt)) or (not allow_body and soft.contains(Point(pt))):
            return False
        return all(math.hypot(pt[0] - q[0], pt[1] - q[1]) >= V["min_spacing"] for q in placed)

    def take(pt, allow_body=False, tag="grid"):
        pt = (round(pt[0], 4), round(pt[1], 4))
        if ok(pt, allow_body):
            placed.append(pt)
            stitch.append((pt, tag))
            return True
        return False

    W = HALF + P.WINDOW["clearance"]
    # 1. bond strips: between adjacent landing pads, in front of GND pads, corner bands
    rs = P.VIA_FENCE["start_r"]
    for s in "NESW":
        u = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}[s]
        if s in "NS":
            lat = [-4.8, -4.2, -3.6, -2.4, -1.2, 0.0, 1.2, 2.4, 3.6, 4.2, 4.8]
        else:       # rev B rows: between the pairs (rejected while the breakout strips are too narrow), TRAP | LOAD
            lat = [-4.8, -4.2, -2.95, -1.4, 0.0, 1.4, 2.95, 4.2, 4.8]
        for rr in (rs, rs + 0.7):
            for t in lat:
                take((u[0] * rr + (0 if u[0] else t), u[1] * rr + (t if u[0] else 0)), tag="bond")
        for t in (-3.0, -0.6, 0.6, 3.0):
            take((u[0] * (rs - 0.05) + (0 if u[0] else t), u[1] * (rs - 0.05) + (t if u[0] else 0)), tag="bond")
    for cx in (-1, 1):
        for cy in (-1, 1):
            for d in (rs, rs + 0.7):
                take((cx * d, cy * d), tag="bond")
    # 2. SMP launch cages
    for net, rr in B.rf.items():
        c, rot = rr["conn"], rr["rot"]
        loc = [(0, 1.45), (0, -1.45), (1.45, 0)] + [(2.9 * math.cos(math.radians(a)), 2.9 * math.sin(math.radians(a)))
                                                     for a in (0, 30, -30, 60, -60, 90, -90, 120, -120)]
        for lp in loc:
            q = G.rot(lp, rot)
            take((c[0] + q[0], c[1] + q[1]), allow_body=True, tag="launch")
    # 3. GCPW fences: single-ended lines on both sides; pair legs on the outside of the pair only while coupled,
    #    on both sides after the split (offset = w/2 + gap + via radius + 0.035, i.e. 0.625 mm for w = 0.39)
    off = P.VIA_FENCE["offset"]
    for net, rr in B.rf.items():
        if "pair" not in rr:
            parts = [(rr["path"], [P.GCPW["w"]] * len(rr["path"]), (1, -1), None)]
        else:
            nc = rr["n_coupled"]
            cl = LineString(G.path_to_polyline(B.pairs[rr["pair"]]["centre"], 0.05))
            parts = [(rr["path"][:nc], rr["widths"][:nc], "outer", cl), (rr["path"][nc:], rr["widths"][nc:], (1, -1), None)]
        for path, widths, sides, cl in parts:
            if not path:
                continue
            for pt, tan, s_ in G.sample(path, P.VIA_FENCE["pitch"]):
                nrm = (-tan[1], tan[0])
                k_near = min(range(len(path)), key=lambda i: G.dist_point_prim(pt, path[i]))
                o = off - (P.GCPW["w"] - widths[k_near]) / 2           # width of the primitive under this sample
                if sides == "outer":
                    qa = (pt[0] + nrm[0] * o, pt[1] + nrm[1] * o)
                    qb = (pt[0] - nrm[0] * o, pt[1] - nrm[1] * o)
                    cand = [qa if cl.distance(Point(qa)) > cl.distance(Point(qb)) else qb]
                else:
                    cand = [(pt[0] + sd * nrm[0] * o, pt[1] + sd * nrm[1] * o) for sd in sides]
                for q in cand:
                    if max(abs(q[0]), abs(q[1])) < rs - 0.01:
                        continue
                    take(q, tag="fence")
    # 4. rings around mounting holes
    for (mx, my) in P.MOUNT["holes"]:
        for k in range(8):
            a = 2 * math.pi * k / 8 + math.pi / 8
            take((mx + 3.3 * math.cos(a), my + 3.3 * math.sin(a)), tag="ring")
    # 5. edge row
    inset = V["edge_row_inset"]
    x0, x1 = P.BOARD["x_min"] + inset, P.BOARD["x_max"] - inset
    y0, y1 = P.BOARD["y_min"] + inset, P.BOARD["y_max"] - inset
    for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L / V["edge_row_pitch"])
        for i in range(n + 1):
            take((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n), tag="edge")
    # 6. background grid
    gstep = V["grid"]
    x = P.BOARD["x_min"] + 1.0
    while x < P.BOARD["x_max"]:
        y = P.BOARD["y_min"] + 1.0
        while y < P.BOARD["y_max"]:
            if not take((x, y), tag="grid"):
                for dx, dy in ((0.5, 0), (-0.5, 0), (0, 0.5), (0, -0.5)):
                    if take((x + dx, y + dy), tag="grid"):
                        break
            y += gstep
        x += gstep
    for pt, tag in stitch:
        B.vias.append(dict(at=pt, net="GND", drill=V["stitch_drill"], size=V["stitch_pad"], kind="stitch", tag=tag))
    return stitch


def place_silk_refs(B, pad_geoms, openings, silk_boxes, board_poly, win):
    """auto-position the silkscreen reference designators of the filter passives: candidate spots around each part,
    rejected if the (conservative) text box comes within 0.1 mm of a pad, a mask opening, an edge or other silk"""
    from shapely.geometry import box as sb
    keep = 0.10
    obst = [pg["poly"] for pg in pad_geoms] + list(openings)
    hard = unary_union([o.buffer(keep) for o in obst] + [win.buffer(0.3)] +
                       [board_poly.difference(board_poly.buffer(-0.4))])
    placed = [bx.buffer(keep) for bx in silk_boxes]
    out, missed = {}, []
    for fp in B.fps:
        if not fp["fp"].name.startswith(("R_", "C_")):
            continue
        ref, (x, y) = fp["ref"], fp["pos"]
        found = None
        for size in (0.6, 0.5):
            wd, ht = len(ref) * 0.82 * size + 0.12, size + 0.12
            cands = [((x, y - 1.55), 0), ((x, y + 1.55), 0), ((x - 1.0, y), 90), ((x + 1.0, y), 90),
                     ((x, y - 1.75), 0), ((x, y + 1.75), 0), ((x - 1.1, y - 0.4), 90), ((x + 1.1, y - 0.4), 90),
                     ((x - 1.1, y + 0.4), 90), ((x + 1.1, y + 0.4), 90), ((x - 1.05, y), 90), ((x + 1.05, y), 90),
                     ((x - 1.0, y - 0.7), 90), ((x + 1.0, y - 0.7), 90), ((x - 1.0, y + 0.7), 90), ((x + 1.0, y + 0.7), 90),
                     ((x - 0.8, y - 1.6), 0), ((x + 0.8, y - 1.6), 0), ((x - 0.8, y + 1.6), 0), ((x + 0.8, y + 1.6), 0),
                     ((x - 1.3, y), 90), ((x + 1.3, y), 90), ((x, y - 2.0), 0), ((x, y + 2.0), 0)]
            for (cx, cy), r in cands:
                bx = sb(cx - wd / 2, cy - ht / 2, cx + wd / 2, cy + ht / 2) if r == 0 else \
                    sb(cx - ht / 2, cy - wd / 2, cx + ht / 2, cy + wd / 2)
                if bx.intersects(hard) or any(bx.buffer(0.05).intersects(pp) for pp in placed):
                    continue
                found = ((cx, cy), r, size, bx)
                break
            if found:
                break
        if found is None:
            missed.append(ref)
            continue
        (cx, cy), r, size, bx = found
        placed.append(bx.buffer(keep))
        d = G.rot((cx - x, cy - y), -fp["rot"])
        out[ref] = dict(local=(d[0], -d[1]), rot=r, size=size)
    return out, missed


# =============================================================================================== E2. pair bookkeeping
def pair_report(B, lengths):
    """per differential pair: leg lengths, skew, the mismatch of every bend and the bumps that compensate it, the
    running skew along the coupled section (P - N at every command boundary) and the coupled / split lengths"""
    out = {}
    for name, pr in B.pairs.items():
        legs = pr["legs"]
        p_is = legs["P"]["leg"]                            # canonical leg (R = outer, L = inner) carrying P
        sgn = -1.0 if p_is == "R" else 1.0                 # running skew is logged as L - R
        rs = [(s, sgn * k) for s, k in DP.running_skew(pr["log"])]
        # longest stretch of the pair (centre-line station) with |P - N| > 0.1 mm; between two marks the difference
        # changes linearly (bends, single bumps) or not at all (straights), so interpolate linearly
        longest, cur = 0.0, 0.0
        for (s0, k0), (s1, k1) in zip(rs, rs[1:]):
            ds = s1 - s0
            if ds <= 0:
                continue
            a0, a1 = abs(k0) > 0.1, abs(k1) > 0.1
            if a0 and a1 and k0 * k1 > 0:
                part, ends_low = ds, False
            elif not a0 and not a1:
                part, ends_low = 0.0, True
            else:                                           # crosses the 0.1 mm level inside the interval
                lev = 0.1 if (k1 if a1 else k0) > 0 else -0.1
                t = (lev - k0) / (k1 - k0) if k1 != k0 else 0.0
                part, ends_low = (ds * (1 - t), False) if a1 else (ds * t, True)
            cur += part
            longest = max(longest, cur)
            if ends_low:
                cur = 0.0
        leg_net = {legs[pol]["leg"]: legs[pol]["net"] for pol in ("P", "N")}
        bends = [dict(b, inner_net=leg_net[b["inner"]]) for b in pr["log"]["bends"]]
        bumps = [dict(leg=leg_net[b["leg"]], n=b["n"], extra_total=b["extra_total"], extra_each=b["each"]["extra"],
                      height=b["each"]["height"], span=b["each"]["span"], arc_deg=math.degrees(b["each"]["alpha"]),
                      r=b["each"]["r"], after_bend=b["after_bend"]) for b in pr["log"]["bumps"]]
        LP, LN = lengths[legs["P"]["net"]], lengths[legs["N"]["net"]]
        leg_geo = {}
        for pol in ("P", "N"):
            lg = legs[pol]
            nc = lg["n_coupled"]
            leg_geo[pol] = dict(
                net=lg["net"], role=lg["role"],
                runs=[[q[1][0], q[1][1], q[2][0], q[2][1], w] for q, w, tg in
                      zip(lg["path"][:nc], lg["widths"][:nc], lg["tags"][:nc]) if q[0] == "seg" and tg == "run"],
                coupled_polyline=[list(p_) for p_ in G.path_to_polyline(lg["path"][:nc], 0.05)],
                split_polyline=[list(p_) for p_ in G.path_to_polyline(lg["path"][nc:], 0.05)],
                n_primitives=len(lg["path"]), n_arcs=sum(1 for q in lg["path"] if q[0] == "arc"))
        out[name] = dict(kind=pr["kind"], side=pr["side"], P=legs["P"]["net"], N=legs["N"]["net"], legs=leg_geo,
                         outer=[pol for pol in ("P", "N") if legs[pol]["role"] == "outer"][0],
                         L_P=LP, L_N=LN, skew_mm=LP - LN,
                         coupled_len={pol: G.path_length(legs[pol]["path"][:legs[pol]["n_coupled"]]) for pol in "PN"},
                         split_len={pol: G.path_length(legs[pol]["path"][legs[pol]["n_coupled"]:]) for pol in "PN"},
                         bends=bends, bumps=bumps, running_skew=rs,
                         running_skew_max=max(abs(k) for _, k in rs), running_skew_end=rs[-1][1],
                         longest_run_over_0p1mm=longest, vertices=pr["vertices"], straights=pr["straights"])
    return out


def bond_report(pads, pcb_pad_board):
    """wire-bond geometry: die pad centre -> bond foot on the PCB land (0.10 mm inside the land's inner half)"""
    rows = []
    for p in pads:
        pc, u = pcb_pad_board[p["id"]]
        foot = (pc[0] - u[0] * 0.10, pc[1] - u[1] * 0.10)
        d = G.sub(foot, p["c"])
        radial = abs(d[0] * u[0] + d[1] * u[1])
        lateral = abs(d[0] * u[1] - d[1] * u[0])
        rows.append(dict(id=p["id"], net=p["net"], span=math.hypot(*d), radial=radial, lateral=lateral,
                         angle_deg=math.degrees(math.atan2(lateral, radial))))
    return dict(per_pad=rows, span_min=min(r["span"] for r in rows), span_max=max(r["span"] for r in rows),
                angle_max_deg=max(r["angle_deg"] for r in rows),
                note="two 25 um Al-1%Si wedge bonds per land, 0.12 mm apart; lands aligned with the die pads")


# =============================================================================================== F. writers
def stackup_sexpr():
    out = ['    (stackup', '      (layer "F.SilkS" (type "Top Silk Screen"))', '      (layer "F.Paste" (type "Top Solder Paste"))']
    di = 0
    for name, kind, t, mat, er, tand, note in P.STACKUP:
        if kind == "mask":
            sd = "Top" if name.startswith("F") else "Bottom"
            out.append(f'      (layer "{name}" (type "{sd} Solder Mask") (color "Green") (thickness {t}) (material "LPI") '
                       f'(epsilon_r {er}) (loss_tangent {tand}))')
        elif kind == "copper":
            out.append(f'      (layer "{name}" (type "copper") (thickness {t}))')
        else:
            di += 1
            m = mat.replace("Rogers ", "")
            out.append(f'      (layer "dielectric {di}" (type "{kind}") (thickness {t}) (material "{m}") '
                       f'(epsilon_r {er}) (loss_tangent {tand}))')
    out += ['      (layer "B.Paste" (type "Bottom Solder Paste"))', '      (layer "B.SilkS" (type "Bottom Silk Screen"))',
            f'      (copper_finish "{P.FINISH}")', '      (dielectric_constraints yes)', '    )']
    return "\n".join(out)


LAYERS = [(0, "F.Cu", "signal"), (1, "In1.Cu", "power"), (2, "In2.Cu", "signal"), (3, "In3.Cu", "power"),
          (4, "In4.Cu", "power"), (31, "B.Cu", "power"), (32, "B.Adhes", "user", "B.Adhesive"),
          (33, "F.Adhes", "user", "F.Adhesive"), (34, "B.Paste", "user"), (35, "F.Paste", "user"),
          (36, "B.SilkS", "user", "B.Silkscreen"), (37, "F.SilkS", "user", "F.Silkscreen"), (38, "B.Mask", "user"),
          (39, "F.Mask", "user"), (40, "Dwgs.User", "user", "User.Drawings"), (41, "Cmts.User", "user", "User.Comments"),
          (42, "Eco1.User", "user", "User.Eco1"), (43, "Eco2.User", "user", "User.Eco2"), (44, "Edge.Cuts", "user"),
          (45, "Margin", "user"), (46, "B.CrtYd", "user", "B.Courtyard"), (47, "F.CrtYd", "user", "F.Courtyard"),
          (48, "B.Fab", "user"), (49, "F.Fab", "user")]

PLOTPARAMS = ('    (pcbplotparams (layerselection 0x00010fc_ffffffff) (plot_on_all_layers_selection 0x0000000_00000000) '
              '(disableapertmacros false) (usegerberextensions false) (usegerberattributes true) '
              '(usegerberadvancedattributes true) (creategerberjobfile true) (dashed_line_dash_ratio 12.000000) '
              '(dashed_line_gap_ratio 3.000000) (svgprecision 4) (plotframeref false) (viasonmask false) (mode 1) '
              '(useauxorigin true) (hpglpennumber 1) (hpglpenspeed 20) (hpglpendiameter 15.000000) (dxfpolygonmode true) '
              '(dxfimperialunits false) (dxfusepcbnewfont true) (psnegative false) (psa4output false) (plotreference true) '
              '(plotvalue true) (plotinvisibletext false) (sketchpadsonfab false) (subtractmaskfromsilk true) '
              '(outputformat 1) (mirror false) (drillshape 0) (scaleselection 1) (outputdirectory "fab/gerbers/"))')


def edge_items(D, W, R):
    """outer rounded rectangle + die window with 270-degree corner reliefs (Edge.Cuts)"""
    b = P.BOARD
    cr = b["corner_r"]
    x0, y0, x1, y1 = b["x_min"], b["y_min"], b["x_max"], b["y_max"]
    lay = "Edge.Cuts"
    segs = [((x0 + cr, y1), (x1 - cr, y1)), ((x1, y1 - cr), (x1, y0 + cr)), ((x1 - cr, y0), (x0 + cr, y0)),
            ((x0, y0 + cr), (x0, y1 - cr))]
    for a, c in segs:
        D.line(lay, K(a), K(c), 0.1)
    s2 = math.sqrt(0.5)
    for (cx, cy, a0) in ((x1 - cr, y1 - cr, 0), (x1 - cr, y0 + cr, 270), (x0 + cr, y0 + cr, 180), (x0 + cr, y1 - cr, 90)):
        st = (cx + cr * math.cos(math.radians(a0)), cy + cr * math.sin(math.radians(a0)))
        md = (cx + cr * math.cos(math.radians(a0 + 45)), cy + cr * math.sin(math.radians(a0 + 45)))
        en = (cx + cr * math.cos(math.radians(a0 + 90)), cy + cr * math.sin(math.radians(a0 + 90)))
        D.items.append(f'  (gr_arc (start {f(K(st)[0])} {f(K(st)[1])}) (mid {f(K(md)[0])} {f(K(md)[1])}) '
                       f'(end {f(K(en)[0])} {f(K(en)[1])}) (stroke (width 0.1) (type solid)) (layer "{lay}") (tstamp {U()}))')
    for a, c in (((-W + R, W), (W - R, W)), ((W, W - R), (W, -W + R)), ((W - R, -W), (-W + R, -W)), ((-W, -W + R), (-W, W - R))):
        D.line(lay, K(a), K(c), 0.1)
    for cx, cy in ((W, W), (W, -W), (-W, -W), (-W, W)):
        sx, sy = (1 if cx > 0 else -1), (1 if cy > 0 else -1)
        st = (cx - sx * R, cy) if sx * sy > 0 else (cx, cy - sy * R)
        en = (cx, cy - sy * R) if sx * sy > 0 else (cx - sx * R, cy)
        md = (cx + sx * R * s2, cy + sy * R * s2)
        D.items.append(f'  (gr_arc (start {f(K(st)[0])} {f(K(st)[1])}) (mid {f(K(md)[0])} {f(K(md)[1])}) '
                       f'(end {f(K(en)[0])} {f(K(en)[1])}) (stroke (width 0.1) (type solid)) (layer "{lay}") (tstamp {U()}))')


def zone_sexpr(net_code, net, layer, outline, clearance, name, priority=0):
    xy = " ".join(f"(xy {f(K(p)[0])} {f(K(p)[1])})" for p in outline)
    return (f'  (zone (net {net_code}) (net_name "{net}") (layer "{layer}") (tstamp {U()}) (name "{name}") (hatch edge 0.5)\n'
            f'    (priority {priority})\n'
            f'    (connect_pads thru_hole_only (clearance {clearance}))\n'
            f'    (min_thickness 0.12) (filled_areas_thickness no)\n'
            f'    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.3) (island_removal_mode 0))\n'
            f'    (polygon (pts {xy}))\n  )')


def keepout_sexpr(layers, outline, name, tracks=False, vias=False):
    xy = " ".join(f"(xy {f(K(p)[0])} {f(K(p)[1])})" for p in outline)
    lay = " ".join(f'"{l}"' for l in layers)
    return (f'  (zone (net 0) (net_name "") (layers {lay}) (tstamp {U()}) (name "{name}") (hatch edge 0.5)\n'
            f'    (connect_pads (clearance 0))\n    (min_thickness 0.25) (filled_areas_thickness no)\n'
            f'    (keepout (tracks {"allowed" if tracks else "not_allowed"}) (vias {"allowed" if vias else "not_allowed"}) '
            f'(pads allowed) (copperpour not_allowed) (footprints allowed))\n'
            f'    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))\n    (polygon (pts {xy}))\n  )')


def track_sexpr(t, code):
    out = []
    if "nm" in t:                        # differential-pair legs: exact integer-nm page coordinates (diffpair.snap_nm)
        def fn(v):
            return f"{v / 1e6:.6f}".rstrip("0").rstrip(".")
        for pr in t["nm"]:
            if pr[0] == "seg":
                a, b = pr[1], pr[2]
                out.append(f'  (segment (start {fn(a[0])} {fn(a[1])}) (end {fn(b[0])} {fn(b[1])}) (width {f(t["w"])}) '
                           f'(layer "{t["layer"]}") (net {code}) (tstamp {U()}))')
            else:
                a, m, b = pr[1], pr[2], pr[3]
                out.append(f'  (arc (start {fn(a[0])} {fn(a[1])}) (mid {fn(m[0])} {fn(m[1])}) (end {fn(b[0])} '
                           f'{fn(b[1])}) (width {f(t["w"])}) (layer "{t["layer"]}") (net {code}) (tstamp {U()}))')
        return out
    for pr in t["path"]:
        if pr[0] == "seg":
            a, b = K(pr[1]), K(pr[2])
            out.append(f'  (segment (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) (width {f(t["w"])}) '
                       f'(layer "{t["layer"]}") (net {code}) (tstamp {U()}))')
        else:
            a, m, b = K(pr[1]), K(pr[2]), K(pr[3])
            out.append(f'  (arc (start {f(a[0])} {f(a[1])}) (mid {f(m[0])} {f(m[1])}) (end {f(b[0])} {f(b[1])}) '
                       f'(width {f(t["w"])}) (layer "{t["layer"]}") (net {code}) (tstamp {U()}))')
    return out


def via_sexpr(v, code):
    a = K(v["at"])
    rm = " (remove_unused_layers)" if v["net"] != "GND" else ""
    return (f'  (via (at {f(a[0])} {f(a[1])}) (size {f(v["size"])}) (drill {f(v["drill"])}) (layers "F.Cu" "B.Cu")'
            f'{rm} (net {code}) (tstamp {U()}))')


def poly_ring_sexpr(pts, layer):
    xy = " ".join(f"(xy {f(K(p)[0])} {f(K(p)[1])})" for p in pts)
    return f'  (gr_poly (pts {xy}) (stroke (width 0) (type solid)) (fill solid) (layer "{layer}") (tstamp {U()}))'


# =============================================================================================== main
pads_all = []
HALF = 5.0


def main():
    global pads_all, HALF
    os.makedirs(REPORTS, exist_ok=True)
    rf = load_rf_calc()
    die, die_size, pads = load_die()
    pads_all = pads
    HALF = die_size / 2
    side = side_lists(pads)
    chans = check_topology(side, die)
    comps, lnets, chan_parts = build_model(pads, chans)

    # --- schematic + KiCad's own netlist -> net names for the board
    uuids, SYM = write_schematic(comps, chans, chan_parts, side)
    knets = kicad_netlist()
    name_of = {}
    for ln, nodes in lnets.items():
        hits = [kn for kn, kn_nodes in knets.items() if kn_nodes == nodes]
        assert len(hits) == 1, f"schematic connectivity differs from the model for {ln}: {nodes}"
        name_of[ln] = hits[0]
    extra = set(knets) - set(name_of.values())
    assert not extra, f"unexpected schematic nets {extra}"

    def netof(ref, pin):
        return name_of[comps[ref]["pins"][pin]]

    # --- footprint catalogue + project libraries
    W = HALF + P.WINDOW["clearance"]
    R = P.WINDOW["relief_r"]
    rc = W + P.BONDPAD["setback"] + P.BONDPAD["length"] / 2
    bp_local, pcb_pad_board, die_pad_board = [], {}, {}
    for p in pads:
        u = p["u"]
        c = (u[0] * rc + (0 if u[0] else p["lat"]), u[1] * rc + (p["lat"] if u[0] else 0))
        bw = P.BONDPAD["width_diff"] if p["kind"] == "rf_fast_diff" else P.BONDPAD["width"]
        size = (P.BONDPAD["length"], bw) if u[0] else (bw, P.BONDPAD["length"])
        bp_local.append((p["id"], (c[0], -c[1]), size))
        pcb_pad_board[p["id"]] = (c, u)
        die_pad_board[p["id"]] = p["c"]
    p1 = [p for p in pads if p["id"] == 1][0]
    fpl = {
        P.PARTS["SMP"]["footprint"]: FPL.smp_jack(),
        P.PARTS["MICROD"]["footprint"]: FPL.micro_d(P.MICROD),
        P.PARTS["R10K"]["footprint"]: FPL.chip(P.PARTS["R10K"]["footprint"], "R"),
        P.PARTS["C10N"]["footprint"]: FPL.chip(P.PARTS["C10N"]["footprint"], "C"),
        P.PARTS["DIE"]["footprint"]: FPL.die_bondpads(bp_local, HALF, W, (p1["c"][0], -p1["c"][1])),
        P.PARTS["MH"]["footprint"]: FPL.mounting_hole(P.MOUNT["drill"], P.MOUNT["pad"]),
        "Fiducial_1.0mm_Mask2.0mm": FPL.fiducial(),
        "NPTH_Dowel_1.6mm": FPL.dowel_hole(P.DOWELS["drill"]),
    }
    pretty = os.path.join(HERE, f"{LIB}.pretty")
    if os.path.isdir(pretty):
        shutil.rmtree(pretty)
    os.makedirs(pretty)
    for name, fp in fpl.items():
        with open(os.path.join(pretty, f"{name}.kicad_mod"), "w") as fh:
            fh.write(fp.library_text(LIB))
    with open(os.path.join(HERE, "fp-lib-table"), "w") as fh:
        fh.write(f'(fp_lib_table\n  (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.pretty")'
                 f'(options "")(descr "QBF-X2 carrier footprints (generated)"))\n)\n')
    with open(os.path.join(HERE, "sym-lib-table"), "w") as fh:
        fh.write(f'(sym_lib_table\n  (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")'
                 f'(options "")(descr "QBF-X2 carrier symbols (generated)"))\n)\n')

    # --- 3D models
    from carrier_lib import models3d as M3
    M3.build_all(os.path.join(HERE, "3dmodels"), P.MICROD, die_pad_board,
                 {k: v for k, v in pcb_pad_board.items()}, die_size, die["die_thickness_um"] / 1000.0)

    # --- routing
    B = Board()
    rf_routes(B, side)
    dc_routes(B, side, chans)
    smp_ref = dict(zip(P.SMP_REFS, P.SMP_DESIGNATORS))
    for net, r in B.rf.items():
        ref = smp_ref[net]
        # the designator + net are in the silkscreen beside each jack and ${REFERENCE} is inside the body on F.Fab, so
        # the footprint's own reference field (F.Fab, 3.9 mm off-centre = next to the neighbouring jack) is hidden
        B.fps.append(dict(ref=ref, fp=fpl[P.PARTS["SMP"]["footprint"]], pos=r["conn"], rot=r["rot"],
                          value=comps[ref]["value"], comp=comps[ref], ref_visible=False))
    B.fps.append(dict(ref="U1", fp=fpl[P.PARTS["DIE"]["footprint"]], pos=(0.0, 0.0), rot=0, value="QBF-X2",
                      comp=comps["U1"]))
    B.fps.append(dict(ref="J11", fp=fpl[P.PARTS["MICROD"]["footprint"]], pos=(P.MICROD["x"], P.MICROD["y_row1"]), rot=0,
                      value=comps["J11"]["value"], comp=comps["J11"]))
    for i, h in enumerate(P.MOUNT["holes"]):
        B.fps.append(dict(ref=f"H{i + 1}", fp=fpl[P.PARTS["MH"]["footprint"]], pos=h, rot=0, value="M2.5",
                          comp=comps[f"H{i + 1}"]))
    for i, h in enumerate(P.FIDUCIALS):
        B.fps.append(dict(ref=f"FID{i + 1}", fp=fpl["Fiducial_1.0mm_Mask2.0mm"], pos=h, rot=0, value="Fiducial", comp=None))
    for i, h in enumerate(P.DOWELS["holes"]):
        B.fps.append(dict(ref=f"DW{i + 1}", fp=fpl["NPTH_Dowel_1.6mm"], pos=h, rot=0, value="Dowel 1.6", comp=None))
    filter_bank(B, comps, chans, chan_parts, netof, fpl)

    # rename logical nets on tracks / vias to KiCad names
    for t in B.tracks:
        t["net"] = name_of.get(t["net"], t["net"])
    for v in B.vias:
        v["net"] = name_of.get(v["net"], v["net"])

    # --- pad geometry (board frame) for clearance work
    pad_geoms = []
    for fp in B.fps:
        comp = fp["comp"]
        for num, c, (ex, ey), pd in fp["fp"].pads_board(fp["pos"], fp["rot"]):
            net = "" if (comp is None or pd["kind"] == "np_thru_hole") else name_of[comp["pins"][num]]
            if pd["shape"] == "circle":
                poly = Point(c).buffer(pd["size"][0] / 2, 32)
            else:
                poly = sbox(c[0] - ex / 2, c[1] - ey / 2, c[0] + ex / 2, c[1] + ey / 2)
            cls = P.GCPW["gap"] if net.startswith(("TRAP", "ACC", "RO_")) else P.DC["clearance"]
            if pd["clearance"] is not None:
                cls = max(cls, pd["clearance"])
            pad_geoms.append(dict(ref=fp["ref"], num=num, net=net, poly=poly, th=pd["kind"] != "smd",
                                  npth=pd["kind"] == "np_thru_hole", drill=pd["drill"], clearance=cls))
    win = sbox(-W, -W, W, W).union(unary_union([Point(cx, cy).buffer(R, 64) for cx in (-W, W) for cy in (-W, W)]))
    bd = P.BOARD
    board_poly = Polygon(G.rounded_rect(bd["x_min"], bd["y_min"], bd["x_max"], bd["y_max"], bd["corner_r"], 16))
    # board-level silkscreen texts (drawn below); stitching vias stay out from under them
    silk = []
    for net, r in B.rf.items():
        ref = smp_ref[net]
        c = r["conn"]
        if r["side"] in "WE":           # two vertical lines outboard of the jack: designator, then the net name
            sg = -1 if r["side"] == "W" else 1
            silk.append((ref, (c[0] + sg * 3.7, c[1]), 90))
            silk.append((net, (c[0] + sg * 4.75, c[1]), 90))
        else:
            silk.append((f"{ref} {net}", (c[0], c[1] - 3.75), 0))
    silk.append(("J11 DC", (-15.2, P.MICROD["y_row1"] + 0.6), 0))
    silk.append(("1", (P.MICROD["x"] - 3.5 * P.MICROD["pitch"] - 1.75, P.MICROD["y_row1"] + 0.0), 0))
    yt = P.BOARD["y_min"] + 3.4
    silk.append((P.PROJECT["board_text"], (0, yt), 0))
    silk.append(("6L RO4003C/RO4450F 1.50MM  NI-FREE AU", (0, yt - 1.4), 0))
    jrefs = set(smp_ref.values())

    def silk_size(s_):
        return 1.0 if s_ == P.PROJECT["board_text"] else 0.65 if s_ in B.rf else 0.75 if s_ in jrefs else 0.8

    def text_box(s_, at, rot, grow=0.15):
        size = silk_size(s_)
        wd, ht = len(s_) * 0.82 * size + grow, size + grow
        return (sbox(at[0] - wd / 2, at[1] - ht / 2, at[0] + wd / 2, at[1] + ht / 2) if rot == 0 else
                sbox(at[0] - ht / 2, at[1] - wd / 2, at[0] + ht / 2, at[1] + wd / 2))
    stitch = stitching(B, win, board_poly, pad_geoms, no_via=[text_box(s_, at, rot) for s_, at, rot in silk])

    # --- nets (KiCad codes)
    allnets = sorted(set(name_of.values()))
    allnets.remove("GND")
    netlist = ["", "GND"] + allnets
    code = {n: i for i, n in enumerate(netlist)}

    # --- mask openings: exposed bond band (GND copper only) and bottom perimeter frame (GND only)
    ro = W + P.BONDPAD["ring_open_out"]
    band = sbox(-ro, -ro, ro, ro).difference(win)
    m = P.BONDPAD["gnd_open_margin"]
    for p in pads:
        if p["net"] == "GND":
            continue
        c, u = pcb_pad_board[p["id"]]
        hw = (P.BONDPAD["width_diff"] if p["kind"] == "rf_fast_diff" else P.BONDPAD["width"]) / 2 + m
        if u[0]:
            band = band.difference(sbox(min(u[0] * (W - 0.2), u[0] * (ro + 0.3)), p["lat"] - hw,
                                        max(u[0] * (W - 0.2), u[0] * (ro + 0.3)), p["lat"] + hw))
        else:
            band = band.difference(sbox(p["lat"] - hw, min(u[1] * (W - 0.2), u[1] * (ro + 0.3)),
                                        p["lat"] + hw, max(u[1] * (W - 0.2), u[1] * (ro + 0.3))))
    # mask-free RF corridors: trace + gaps open, ending corridor_inset short of the ground copper (signal net only).
    # Differential pairs: one corridor per leg (KiCad flags an aperture that exposes two nets), separated by a mask web
    # of DIFF["web"] centred on the pair centre line: the routed inner gap keeps 0.16 mm bare next to each leg (the
    # middle 0.33 mm is masked), the breakout gap 0.035 mm.
    corridors = []
    if P.GCPW["mask_free"]:
        ci = P.GCPW["corridor_inset"]
        webs = {}
        for name, pr in B.pairs.items():
            cpts = G.path_to_polyline(pr["centre"], 0.02)
            d0 = G.unit(G.sub(cpts[0], cpts[1]))
            cpts = [G.add(cpts[0], G.mul(d0, 0.8))] + cpts          # web also between the two lands
            webs[name] = LineString(cpts).buffer(P.DIFF["web"] / 2, 16, cap_style=2)
        for net, r in B.rf.items():
            if "pair" not in r:
                hw = P.GCPW["w"] / 2 + P.GCPW["gap"] - ci
                corridors.append(LineString(G.path_to_polyline(r["path"], 0.02)).buffer(hw, 32))
                continue
            g_ = P.DIFF["g"]
            parts = [LineString(G.path_to_polyline([q], 0.02)).buffer(w_ / 2 + g_ - ci, 32)
                     for q, w_ in zip(r["path"], r["widths"])]
            cor = unary_union(parts).difference(webs[r["pair"]])
            if cor.geom_type != "Polygon":                             # keep the piece that carries the leg
                cor = max(cor.geoms, key=lambda q: q.area)
            corridors.append(cor)
        band = band.difference(unary_union(corridors).buffer(P.RULES["mask_min_web"] + 0.005, 32))
    band_polys = [band] if band.geom_type == "Polygon" else list(band.geoms)
    # drop openings too narrow to land a ground bond (between the differential pairs the ground strip is 0.27 mm)
    band_polys = [bp.simplify(0.002) for bp in band_polys if bp.area > 0.01 and not bp.buffer(-0.08).is_empty]
    fw = 2.0
    frame = [sbox(bd["x_min"] - 0.5, bd["y_min"] - 0.5, bd["x_max"] + 0.5, bd["y_min"] + fw),
             sbox(bd["x_min"] - 0.5, bd["y_max"] - fw, bd["x_max"] + 0.5, bd["y_max"] + 0.5),
             sbox(bd["x_min"] - 0.5, bd["y_min"] + fw, bd["x_min"] + fw, bd["y_max"] - fw),
             sbox(bd["x_max"] - fw, bd["y_min"] + fw, bd["x_max"] + 0.5, bd["y_max"] - fw)]

    # --- silkscreen and drawings
    D = B.gfx
    edge_items(D, W, R)
    for s, at, rot in silk:
        size = silk_size(s)
        D.text("F.SilkS", s, *K(at), size, round(size * 0.15, 3), "center", rot)
    bl = [f"QBF-X2 CARRIER REV {P.PROJECT['rev']}  (BOTTOM = GND, BASE CONTACT)", "J11 MICRO-D PINOUT:"] + \
         [f"{k} {P.MICROD_PINS[k]}" for k in range(1, 9)] + ["9-15, SHELL: GND"]
    yb = -7.6
    for s in bl:
        D.text("B.SilkS", s, *K((0, yb)), 0.8, 0.12, "center", 0, mirror=True)
        yb -= 1.3

    # silkscreen reference designators of the filter passives (auto-positioned, see place_silk_refs)
    from shapely.geometry import box as sb_
    silk_boxes = []
    for s_, at, rot in silk:
        size = silk_size(s_)
        wd, ht = len(s_) * 0.82 * size + 0.15, size + 0.15
        silk_boxes.append(sb_(at[0] - wd / 2, at[1] - ht / 2, at[0] + wd / 2, at[1] + ht / 2) if rot == 0 else
                          sb_(at[0] - ht / 2, at[1] - wd / 2, at[0] + ht / 2, at[1] + wd / 2))
    for r in B.rf.values():
        c = Point(r["conn"])
        silk_boxes.append(c.buffer(3.12).difference(c.buffer(2.98)))
    jx, jy = P.MICROD["x"], P.MICROD["y_row1"]
    silk_boxes += [sb_(jx - 12.2, jy - 1.9, jx + 12.2, jy - 1.6), sb_(jx - 12.2, jy - 1.9, jx - 11.9, jy + 1.7),
                   sb_(jx + 11.9, jy - 1.9, jx + 12.2, jy + 1.7)]
    silk_refs, silk_missed = place_silk_refs(B, pad_geoms, band_polys + corridors, silk_boxes, board_poly, win)
    if silk_missed:
        print("silk designators not placed (kept on F.Fab only):", silk_missed)

    # fab + assembly drawings (built in drawing_layers.py from the same data)
    from carrier_lib.drawing_layers import fab_and_assembly
    co = FL.all_cutoffs(P.FILTERS)
    z = rf.gcpw_z0(P.GCPW["w"], P.GCPW["gap"], P.GCPW["h"], P.GCPW["er"])
    from carrier_lib import fd2d
    gc = P.GCPW
    fd = fd2d.solve(gc["w"], gc["gap"], gc["h"], gc["er"], t=gc["t_cu"], mask_t=0.02,
                    mask_mode="corridor" if gc["mask_free"] else "full", corridor_inset=gc["corridor_inset"])
    Dp = P.DIFF
    fd_pair = {k: fd2d.solve_coupled(Dp[f"w{k}"], Dp[f"s{k}"], Dp[f"g{k}"], gc["h"], gc["er"], t=gc["t_cu"], mask_t=0.02,
                                     mask_mode="corridor", corridor_inset=gc["corridor_inset"]) for k in ("", "_bo")}
    cf_pair = {k: fd2d.closed_form_coupled(Dp[f"w{k}"], Dp[f"s{k}"], Dp[f"g{k}"], gc["h"], gc["er"]) for k in ("", "_bo")}
    lengths = {n: (DP.nm_length(r["nm"]) if "nm" in r else G.path_length(r["path"])) for n, r in B.rf.items()}
    pairs_model = pair_report(B, lengths)
    drills = {}
    for v in B.vias:
        key = (round(v["drill"], 3), "PTH")
        drills[key] = drills.get(key, 0) + 1
    for pg in pad_geoms:
        if pg["th"]:
            key = (round(pg["drill"], 3), "NPTH" if pg["npth"] else "PTH")
            drills[key] = drills.get(key, 0) + 1
    info = dict(z=z, fd=fd, lengths=lengths, drills=drills, cutoffs=co, comps=comps, chans=chans, chan_parts=chan_parts,
                W=W, R=R, die_size=die_size, fps=B.fps, pcb_pads=pcb_pad_board, die_pads=die_pad_board,
                pad_nets={p["id"]: p["net"] for p in pads}, fd_pair=fd_pair, cf_pair=cf_pair, pairs=pairs_model,
                smp_ref=smp_ref, land_w={p["id"]: (P.BONDPAD["width_diff"] if p["kind"] == "rf_fast_diff"
                                                   else P.BONDPAD["width"]) for p in pads})
    fab_and_assembly(D, K, info)

    # --- write the board
    L = ['(kicad_pcb (version 20221018) (generator pcbnew)',
         f'  (general (thickness {sum(s[2] for s in P.STACKUP):.3f}))', f'  (paper "{P.BOARD["page"]}")',
         f'  (title_block (title "{P.PROJECT["title"]}") (date "{P.PROJECT["date"]}") (rev "{P.PROJECT["rev"]}") '
         f'(company "{P.PROJECT["author"]}") (comment 1 "6-layer Rogers RO4003C/RO4450F, 1.50 mm, Ni-free finish '
         f'(EPAG or soft Au)") (comment 2 "Author: {P.PROJECT["author"]}") (comment 3 "Generated by pcb/build_carrier.py from '
         f'carrier_params.py") (comment 4 "Units mm; origin (drill/place) = board lower-left corner"))',
         '  (layers']
    for lyr in LAYERS:
        L.append(f'    ({lyr[0]} "{lyr[1]}" {lyr[2]}' + (f' "{lyr[3]}"' if len(lyr) > 3 else "") + ")")
    L.append('  )')
    ox, oy = K((bd["x_min"], bd["y_min"]))
    L += ['  (setup', stackup_sexpr(), '    (pad_to_mask_clearance 0.05)', '    (solder_mask_min_width 0.1)',
          '    (allow_soldermask_bridges_in_footprints no)', f'    (aux_axis_origin {f(ox)} {f(oy)})',
          f'    (grid_origin {f(ox)} {f(oy)})', PLOTPARAMS, '  )']
    for i, n in enumerate(netlist):
        L.append(f'  (net {i} "{n}")')
    for fp in B.fps:
        comp = fp["comp"]
        netmap = {}
        if comp is not None:
            for num, ln in comp["pins"].items():
                kn = name_of[ln]
                netmap[num] = (code[kn], kn)
        sr = silk_refs.get(fp["ref"])
        if sr:
            L.append(fp["fp"].board_text(LIB, fp["ref"], fp["value"], K(fp["pos"]), fp["rot"], netmap,
                                         uuids.get(fp["ref"]), f"{NAME}.kicad_sch" if comp else None,
                                         ref_at=sr["local"], ref_rot=sr["rot"], ref_layer="F.SilkS", ref_size=sr["size"]))
        else:
            L.append(fp["fp"].board_text(LIB, fp["ref"], fp["value"], K(fp["pos"]), fp["rot"], netmap,
                                         uuids.get(fp["ref"]), f"{NAME}.kicad_sch" if comp else None,
                                         ref_visible=fp.get("ref_visible", True)))
    L += D.items
    for bp in band_polys:
        L.append(poly_ring_sexpr(list(bp.exterior.coords)[:-1], "F.Mask"))
    for cp_ in corridors:
        L.append(poly_ring_sexpr(list(cp_.simplify(0.002).exterior.coords)[:-1], "F.Mask"))
    for fr in frame:
        L.append(poly_ring_sexpr(list(fr.exterior.coords)[:-1], "B.Mask"))
    for t in B.tracks:
        L += track_sexpr(t, code[t["net"]])
    for v in B.vias:
        L.append(via_sexpr(v, code[v["net"]]))
    zo = G.rounded_rect(bd["x_min"] + P.BOARD["zone_inset"], bd["y_min"] + P.BOARD["zone_inset"],
                        bd["x_max"] - P.BOARD["zone_inset"], bd["y_max"] - P.BOARD["zone_inset"],
                        max(0.2, bd["corner_r"] - P.BOARD["zone_inset"]), 6)
    for lay in P.COPPER_LAYERS:
        L.append(zone_sexpr(1, "GND", lay, zo, P.RULES["min_clearance"], f"GND_{lay}"))
    kw = win.buffer(P.BOARD["inner_window_pullback"], 32).simplify(0.002)
    L.append(keepout_sexpr(["In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"], list(kw.exterior.coords)[:-1],
                           "window_pullback_inner"))
    for name, pr in B.pairs.items():        # between the legs of a coupled pair: no ground pour, no vias (F.Cu only)
        reg = pr["region"].simplify(0.003)
        L.append(keepout_sexpr(["F.Cu"], list(reg.exterior.coords)[:-1], f"DIFF_{name}_no_gnd_no_via", tracks=True))
    L.append(')')
    with open(os.path.join(HERE, f"{NAME}.kicad_pcb"), "w") as fh:
        fh.write("\n".join(L) + "\n")

    write_project(uuids_root=None)
    write_dru(pairs_model)

    # --- design intent for the checks
    model = dict(
        units="mm, board frame (y up, origin = die centre)", page_origin=[X0, Y0],
        die=dict(size=die_size, window_half=W, relief_r=R, landing_pad_centre_r=rc),
        u1_pads={str(k): dict(pcb=list(v[0]), die=list(die_pad_board[k]), outward=list(v[1]),
                              net=[p["net"] for p in pads if p["id"] == k][0]) for k, v in pcb_pad_board.items()},
        rf={n: dict(points=r["points"], length=lengths[n], conn=list(r["conn"]), rot=r["rot"],
                    n_arcs=sum(1 for q in r["path"] if q[0] == "arc"),
                    n_segs=sum(1 for q in r["path"] if q[0] == "seg"),
                    bend_turns_deg=[round(math.degrees(q[6]), 3) for q in r["path"] if q[0] == "arc"])
            for n, r in B.rf.items()},
        dc_in2={n: p for n, p in B.dc_paths.items()}, chan_x=B.chan_x, chan_parts=chan_parts,
        name_of=name_of, comps={k: dict(v, pins=v["pins"]) for k, v in comps.items()},
        board_only=[fp["ref"] for fp in B.fps if fp["comp"] is None],
        silk_designators=dict(placed=sorted(silk_refs), missed=silk_missed),
        vias=dict(total=len(B.vias), stitch=len(stitch),
                  by_tag={t: sum(1 for _, tg in stitch if tg == t) for t in sorted(set(tg for _, tg in stitch))},
                  dc=sum(1 for v in B.vias if v["kind"] == "dc"), cap_gnd=sum(1 for v in B.vias if v["kind"] == "gnd_cap")),
        drills={f"{k[0]:.2f} {k[1]}": n for k, n in sorted(drills.items())},
        gcpw=dict(P.GCPW), gcpw_fd_crosscheck=fd, stackup=P.STACKUP, filters=P.FILTERS, cutoffs=co,
        bond_band_openings=len(band_polys),
        diff=dict(params=P.DIFF, fast=P.FAST, fd_pair=fd_pair, closed_form_pair=cf_pair, pairs=pairs_model,
                  smp_designators=smp_ref, ab_pairs=P.AB_PAIRS),
        bonds=bond_report(pads, pcb_pad_board),
    )
    with open(os.path.join(REPORTS, "build_model.json"), "w") as fh:
        json.dump(model, fh, indent=1, default=lambda o: list(o) if isinstance(o, (set, tuple)) else str(o))
    print(f"board written: {len(B.fps)} footprints, {len(B.tracks)} tracks, {len(B.vias)} vias "
          f"({len(stitch)} GND stitching), {len(netlist) - 1} nets")
    for n in sorted(lengths):
        print(f"  {n:8s} {lengths[n]:.4f} mm")


def write_project(uuids_root=None):
    sch = open(os.path.join(HERE, f"{NAME}.kicad_sch")).read()
    root = sch.split("(uuid ", 1)[1].split(")", 1)[0]
    rules = P.RULES
    nc_common = dict(diff_pair_gap=0.25, diff_pair_via_gap=0.25, diff_pair_width=0.2, line_style=0, microvia_diameter=0.3,
                     microvia_drill=0.1, pcb_color="rgba(0, 0, 0, 0.000)", schematic_color="rgba(0, 0, 0, 0.000)",
                     wire_width=6, bus_width=12)
    pro = {
        "board": {
            "3dviewports": [],
            "design_settings": {
                "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.0,
                             "copper_text_size_v": 1.0, "copper_text_thickness": 0.15, "other_line_width": 0.15,
                             "silk_line_width": 0.12, "silk_text_size_h": 0.8, "silk_text_size_v": 0.8,
                             "silk_text_thickness": 0.12, "fab_line_width": 0.1, "fab_text_size_h": 0.8,
                             "fab_text_size_v": 0.8, "fab_text_thickness": 0.12,
                             "pads": {"drill": 0.7, "height": 1.1, "width": 1.1}, "zones": {"min_clearance": 0.15}},
                "rules": {"allow_blind_buried_vias": False, "allow_microvias": False, "max_error": 0.005,
                          "min_clearance": rules["min_clearance"], "min_connection": 0.12,
                          "min_copper_edge_clearance": rules["copper_edge_clearance"],
                          "min_hole_clearance": rules["min_hole_clearance"], "min_hole_to_hole": rules["min_hole_to_hole"],
                          "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "min_resolved_spokes": 2,
                          "min_silk_clearance": 0.0, "min_text_height": 0.5, "min_text_thickness": 0.08,
                          "min_through_hole_diameter": rules["min_via_drill"], "min_track_width": rules["min_track"],
                          "min_via_annular_width": rules["min_annular"], "min_via_diameter": rules["min_via_diam"],
                          "solder_mask_clearance": 0.05, "solder_mask_min_width": rules["mask_min_web"],
                          "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True},
                "track_widths": [0.0, P.GCPW["w"], P.DC["fcu_width"], P.DC["in2_width"], 0.3],
                "via_dimensions": [{"diameter": 0.0, "drill": 0.0},
                                   {"diameter": P.VIAS["stitch_pad"], "drill": P.VIAS["stitch_drill"]},
                                   {"diameter": P.VIAS["dc_pad"], "drill": P.VIAS["dc_drill"]}],
                "diff_pair_dimensions": [{"gap": 0.0, "via_gap": 0.0, "width": 0.0}],
                "drc_exclusions": [],
                "meta": {"version": 2},
                "rule_severities": {},
                "teardrop_options": [{"td_allow_use_two_tracks": True, "td_curve_segcount": 5,
                                      "td_on_pad_in_zone": False, "td_onpadsmd": True, "td_onroundshapesonly": False,
                                      "td_ontrackend": False, "td_onviapad": True}],
                "teardrop_parameters": [],
                "zones_allow_external_fillets": False,
            },
            "layer_presets": [], "viewports": []},
        "boards": [],
        "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": f"{NAME}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [
                dict(nc_common, name="Default", clearance=rules["min_clearance"], track_width=0.25, via_diameter=P.VIAS["stitch_pad"],
                     via_drill=P.VIAS["stitch_drill"]),
                dict(nc_common, name="RF_50", clearance=P.GCPW["gap"], track_width=P.GCPW["w"], via_diameter=P.VIAS["stitch_pad"],
                     via_drill=P.VIAS["stitch_drill"]),
                dict(nc_common, name="RF_DIFF", clearance=P.DIFF["g"], track_width=P.DIFF["w"],
                     via_diameter=P.VIAS["stitch_pad"], via_drill=P.VIAS["stitch_drill"], diff_pair_width=P.DIFF["w"],
                     diff_pair_gap=P.DIFF["s"], diff_pair_via_gap=P.DIFF["s"]),
                dict(nc_common, name="DC", clearance=P.DC["clearance"], track_width=P.DC["fcu_width"], via_diameter=P.VIAS["dc_pad"],
                     via_drill=P.VIAS["dc_drill"]),
            ],
            "meta": {"version": 3},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": [{"netclass": "RF_DIFF", "pattern": p} for p in ("TRAP_*", "ACC_*")] +
                                 [{"netclass": "RF_50", "pattern": "RO_*"}] +
                                 [{"netclass": "DC", "pattern": p} for p in ("LOAD_*", "GATE_*", "Net-*")],
        },
        "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "specctra_dsn": "", "step": "", "vrml": ""},
                   "page_layout_descr_file": ""},
        "schematic": {"drawing": {"default_line_thickness": 6.0, "default_text_size": 50.0, "label_size_ratio": 0.375,
                                  "pin_symbol_size": 25.0, "text_offset_ratio": 0.15},
                      "legacy_lib_dir": "", "legacy_lib_list": [], "meta": {"version": 1}, "net_format_name": "",
                      "page_layout_descr_file": "", "plot_directory": "", "spice_current_sheet_as_root": False,
                      "spice_external_command": "spice \"%I\"", "spice_model_current_sheet_as_root": True,
                      "spice_save_all_currents": False, "spice_save_all_voltages": False, "subpart_first_id": 65,
                      "subpart_id_separator": 0},
        "sheets": [[root, ""]],
        "text_variables": {},
    }
    with open(os.path.join(HERE, f"{NAME}.kicad_pro"), "w") as fh:
        json.dump(pro, fh, indent=2)


def write_dru(pairs):
    rl, gc, D = P.RULES, P.GCPW, P.DIFF
    rf = "(A.NetClass == 'RF_50' || A.NetClass == 'RF_DIFF')"
    wcut = (D["w"] + D["w_bo"]) / 2
    nominal = {k: sum(pr[f"L_{pol}"] for pr in pairs.values() if pr["kind"] == k for pol in "PN") /
               sum(2 for pr in pairs.values() if pr["kind"] == k) for k in ("TRAP", "ACC")}
    half_ab = rl["skew_max"] / 2
    skew_rules = "\n".join(
        f'(rule "{n}_intra_pair_skew"\n  (condition "A.inDiffPair(\'{n}\')")\n'
        f'  (constraint skew (max {D["skew_max"] / 2:.3f}mm)))' for n in P.FAST_PAIRS)
    txt = f"""(version 1)
# QBF-X2 carrier design rules, rev {P.PROJECT['rev']} (generated by build_carrier.py from carrier_params.py).
# Board-level minima live in qbfx2_carrier.kicad_pro (clearance {rl['min_clearance']}, track {rl['min_track']},
# via {rl['min_via_diam']}/{rl['min_via_drill']}, annular {rl['min_annular']}, hole-hole {rl['min_hole_to_hole']},
# copper-edge {rl['copper_edge_clearance']} for the wire-bond landing pads at the die window).
# Rule order matters: when two rules give the same constraint, the later one wins (RF rules after the DC rules).

# --- DC lines: stripline on In2 between the In1 / In3 GND planes
(rule "DC_In2_width"
  (layer "In2.Cu")
  (condition "A.NetClass == 'DC' && A.Type == 'Track'")
  (constraint track_width (min {P.DC['in2_width']:.2f}mm)))
(rule "DC_clearance"
  (condition "A.NetClass == 'DC'")
  (constraint clearance (min {P.DC['clearance']:.2f}mm)))

# --- 50-ohm GCPW on F.Cu (readout lines RF_50; also every leg of the fast pairs RF_DIFF): w = {gc['w']} mm,
#     gap = {gc['gap']} mm over {gc['h']} mm RO4003C (In1 = reference)
(rule "RF_GCPW_width"
  (layer "F.Cu")
  (condition "A.NetClass == 'RF_50' && (A.Type == 'Track' || A.Type == 'Arc')")
  (constraint track_width (min {gc['w'] - 0.01:.2f}mm) (opt {gc['w']:.2f}mm) (max {gc['w'] + 0.01:.2f}mm)))
(rule "RF_GCPW_gap"
  (condition "{rf} && B.NetName == 'GND'")
  (constraint clearance (min {gc['gap']:.2f}mm)))
(rule "RF_to_other_signals"
  (condition "{rf} && B.NetName != 'GND' && A.NetName != B.NetName && !AB.isCoupledDiffPair()")
  (constraint clearance (min 0.40mm)))
(rule "RF_top_layer_only"
  (layer inner)
  (condition "A.NetClass == 'RF_50' || A.NetClass == 'RF_DIFF'")
  (constraint disallow track via))
(rule "RF_no_vias"
  (condition "{rf} && A.Type == 'Via'")
  (constraint disallow via))

# --- fast flux lines: 8 edge-coupled GCPW differential pairs <name>_P / <name>_N (KiCad pairs them by the suffix).
#     Routed: w {D['w']} / gap {D['s']} (P-N) / {D['g']} to GND -> Z_odd 50 ohm, loosely coupled.
#     Breakout at the die: w {D['w_bo']} / gap {D['s_bo']} (leg pitch {D['w_bo'] + D['s_bo']:.2f} mm = die pad pitch).
#     Width and gap are checked per section (the two widths are the two allowed bands). Between the legs: no ground
#     pour and no vias (F.Cu keepouts "DIFF_<pair>_no_gnd_no_via"). KiCad 7 measures the coupled length on straight
#     segments only; every straight next to an arc or a pad begins with a {DP.STUB} mm coupling stub (diffpair.py).
(rule "DIFF_intra_pair_clearance"
  (condition "A.inDiffPair('*') && AB.isCoupledDiffPair()")
  (constraint clearance (min {D['s_bo'] - 0.01:.2f}mm)))
(rule "DIFF_routed"
  (layer "F.Cu")
  (condition "A.inDiffPair('*') && (A.Type == 'Track' || A.Type == 'Arc') && A.Width >= {wcut:.2f}mm")
  (constraint track_width (min {D['w'] - 0.01:.2f}mm) (opt {D['w']:.2f}mm) (max {D['w'] + 0.01:.2f}mm))
  (constraint diff_pair_gap (min {D['s'] - 0.01:.2f}mm) (opt {D['s']:.2f}mm) (max {D['s'] + 0.01:.2f}mm))
  (constraint diff_pair_uncoupled (max {D['uncoupled_max']:.2f}mm)))
(rule "DIFF_breakout"
  (layer "F.Cu")
  (condition "A.inDiffPair('*') && (A.Type == 'Track' || A.Type == 'Arc') && A.Width < {wcut:.2f}mm")
  (constraint track_width (min {D['w_bo'] - 0.01:.2f}mm) (opt {D['w_bo']:.2f}mm) (max {D['w_bo'] + 0.01:.2f}mm))
  (constraint diff_pair_gap (min {D['s_bo'] - 0.01:.2f}mm) (opt {D['s_bo']:.2f}mm) (max {D['s_bo'] + 0.01:.2f}mm))
  (constraint diff_pair_uncoupled (max {D['uncoupled_max_bo']:.2f}mm)))

# --- intra-pair skew |L_P - L_N| <= {D['skew_max']:.2f} mm (~0.5 ps). KiCad 7 defines skew as the net length minus the
#     average length of the nets matched by the rule, so for two nets max {D['skew_max'] / 2:.3f} mm here means
#     |L_P - L_N| <= {D['skew_max']:.2f} mm. One rule per pair, so each pair is its own group.
{skew_rules}

# --- A/B matching: every TRAP leg within +/-{half_ab:.2f} mm of the TRAP nominal and every ACC leg within
#     +/-{half_ab:.2f} mm of the ACC nominal, so corresponding A and B pairs agree within {rl['skew_max']:.2f} mm
#     (a length rule, because each net can belong to only one skew rule)
(rule "TRAP_A_vs_B_length"
  (condition "A.inDiffPair('TRAP_*')")
  (constraint length (min {nominal['TRAP'] - half_ab:.3f}mm) (max {nominal['TRAP'] + half_ab:.3f}mm)))
(rule "ACC_A_vs_B_length"
  (condition "A.inDiffPair('ACC_*')")
  (constraint length (min {nominal['ACC'] - half_ab:.3f}mm) (max {nominal['ACC'] + half_ab:.3f}mm)))

# --- vias (single through-via process, aspect ratio <= 7.5)
(rule "via_geometry"
  (condition "A.Type == 'Via'")
  (constraint via_diameter (min {rl['min_via_diam']:.2f}mm))
  (constraint hole_size (min {rl['min_via_drill']:.2f}mm))
  (constraint annular_width (min {rl['min_annular']:.3f}mm)))

# --- edges: only the wire-bond landing pads / bond ring may approach the die window
(rule "tracks_vias_from_edges"
  (condition "A.Type == 'Track' || A.Type == 'Arc' || A.Type == 'Via'")
  (constraint edge_clearance (min {rl['track_edge_clearance']:.2f}mm)))
# inner layers keep 0.30 mm from the die window through the keepout area "window_pullback_inner"
"""
    with open(os.path.join(HERE, f"{NAME}.kicad_dru"), "w") as fh:
        fh.write(txt)


if __name__ == "__main__":
    main()
