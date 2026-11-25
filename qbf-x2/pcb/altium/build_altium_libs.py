"""Altium Designer native libraries for the QBF-X2 carrier, written with altium-designer-mcp.

Source of truth: the carrier's own KiCad libraries (pcb/qbfx2.pretty footprints, pcb/qbfx2.kicad_sym symbols, the
STEP models in pcb/3dmodels) and its BOM (pcb/fab/qbfx2_carrier_bom.csv). They are converted to Altium primitives
and written to .PcbLib / .SchLib by the altium-designer-mcp server
(https://github.com/embedded-society/altium-designer-mcp), driven over its MCP stdio transport (JSON-RPC 2.0).
The tool owns Altium's binary OLE format; this script does the engineering mapping.

Conventions:
- Footprints: KiCad is y-down, Altium y-up, so y is negated. The visual rotation is preserved and positions are mm.
- Symbols: KiCad symbol coordinates are y-up mm. Altium schematic units are 10 mil (1 unit = 0.254 mm).
  - A KiCad pin's (x, y) is its connection point, and its angle points towards the body.
  - An Altium pin's (x, y) is its body end, and its orientation points outwards.
- One Altium component per BOM line, carrying Manufacturer / Manufacturer Part Number / MPN status parameters and a
  footprint link. The die U1 and the mounting hole get symbols too.

Outputs in pcb/altium/:
- QBFX2_Carrier.PcbLib, QBFX2_Carrier.SchLib and QBFX2_Carrier.LibPkg;
- reports/altium_report.json (the tool's validation, round-trip comparison and component list);
- reports/previews.txt (the tool's ASCII renders).
Run: python3 pcb/altium/build_altium_libs.py [--bin PATH_TO_altium-designer-mcp]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.dirname(HERE)
OUT = HERE
REP = os.path.join(HERE, "reports")
DEFAULT_BIN = "/home/user/embedded-society/altium-designer-mcp/target/release/altium-designer-mcp"
LIBNAME = "QBFX2_Carrier"
SCH_UNIT_MM = 0.254


# ---------------------------------------------------------------- KiCad s-expressions
def parse_sexpr(text: str):
    tokens = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text)
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop()
            stack[-1].append(x)
        else:
            if t.startswith('"'):
                t = t[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            stack[-1].append(t)
    return stack[0][0]


def kids(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def kid(node, key):
    k = kids(node, key)
    return k[0] if k else None


def num(x):
    return float(x)


def stroke_width(node, default=0.12):
    s = kid(node, "stroke")
    if s is not None and kid(s, "width") is not None:
        return num(kid(s, "width")[1])
    w = kid(node, "width")
    return num(w[1]) if w is not None else default


LAYER_MAP = {"F.SilkS": "Top Overlay", "B.SilkS": "Bottom Overlay", "F.CrtYd": "Top Courtyard",
             "B.CrtYd": "Bottom Courtyard", "F.Fab": "Top Assembly", "B.Fab": "Bottom Assembly",
             "Dwgs.User": "Mechanical 1", "Cmts.User": "Mechanical 1"}


def arc_from_3pts(s, m, e):
    """centre, radius and CCW start/end angles (deg) of the arc start -> mid -> end (y-up coordinates)"""
    (x1, y1), (x2, y2), (x3, y3) = s, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a = lambda p: math.degrees(math.atan2(p[1] - uy, p[0] - ux)) % 360
    a1, a2, a3 = a(s), a(m), a(e)
    ccw = (a2 - a1) % 360 < (a3 - a1) % 360          # mid lies on the CCW sweep from start to end
    return (ux, uy, r, a1, a3) if ccw else (ux, uy, r, a3, a1)


# ---------------------------------------------------------------- footprints
def convert_footprint(path):
    fp = parse_sexpr(open(path).read())
    name = fp[1]
    descr = kid(fp, "descr")
    out = dict(name=name, description=(descr[1] if descr else name).replace("|", "/")[:250], pads=[], tracks=[], arcs=[],
               regions=[])
    notes = []
    for p in kids(fp, "pad"):
        des, typ, shape = p[1], p[2], p[3]
        at = kid(p, "at")
        size = kid(p, "size")
        layers = kid(p, "layers")[1:] if kid(p, "layers") is not None else []
        pad = dict(designator=des, x=num(at[1]), y=-num(at[2]), width=num(size[1]), height=num(size[2]),
                   rotation=num(at[3]) if len(at) > 3 else 0.0)
        pad["shape"] = {"rect": "rectangle", "circle": "round", "oval": "oval", "roundrect": "rounded_rectangle",
                        "trapezoid": "rectangle", "custom": "rectangle"}.get(shape, "rectangle")
        if shape == "roundrect" and kid(p, "roundrect_rratio") is not None:
            pad["corner_radius_percent"] = int(round(num(kid(p, "roundrect_rratio")[1]) * 200))
        if typ == "smd":
            pad["layer"] = "Top Layer" if any(l in ("F.Cu", "*.Cu") for l in layers) else "Bottom Layer"
        else:
            pad["layer"] = "Multi-Layer"
            dr = kid(p, "drill")
            if dr is not None:
                vals = [v for v in dr[1:] if not isinstance(v, list)]
                if vals and vals[0] == "oval":
                    pad["hole_size"] = min(num(vals[1]), num(vals[2]))
                    pad["hole_shape"] = "slot"
                    pad["hole_slot_length"] = max(num(vals[1]), num(vals[2]))
                else:
                    pad["hole_size"] = num(vals[0])
            pad["is_plated"] = typ != "np_thru_hole"
        has_paste = any(l.endswith(".Paste") for l in layers)
        if typ == "smd" and not has_paste:
            pad["paste_mask_expansion"] = -round(min(pad["width"], pad["height"]) / 2 + 0.05, 4)   # no stencil opening
            pad["paste_mask_expansion_mode"] = "manual"
        sm = kid(p, "solder_mask_margin")
        if sm is not None:
            pad["solder_mask_expansion"] = num(sm[1])
            pad["solder_mask_expansion_mode"] = "manual"
        if not any(l.endswith(".Mask") for l in layers) and typ != "np_thru_hole":
            pad["solder_mask_expansion"] = -round(min(pad["width"], pad["height"]) / 2, 4)   # tented
            pad["solder_mask_expansion_mode"] = "manual"
        if kid(p, "clearance") is not None:
            notes.append(f"pad {des}: local clearance {kid(p, 'clearance')[1]} mm (set a rule in Altium)")
        out["pads"].append(pad)
    for g in fp:
        if not (isinstance(g, list) and g and g[0] in ("fp_line", "fp_circle", "fp_arc", "fp_rect", "fp_poly")):
            continue
        lay = kid(g, "layer")[1] if kid(g, "layer") is not None else ""
        if lay not in LAYER_MAP:
            continue
        L, w = LAYER_MAP[lay], stroke_width(g)
        xy = lambda k: (num(kid(g, k)[1]), -num(kid(g, k)[2]))
        if g[0] == "fp_line":
            (x1, y1), (x2, y2) = xy("start"), xy("end")
            out["tracks"].append(dict(x1=x1, y1=y1, x2=x2, y2=y2, width=w, layer=L))
        elif g[0] == "fp_rect":
            (x1, y1), (x2, y2) = xy("start"), xy("end")
            fill = kid(g, "fill")
            if fill is not None and fill[1] in ("solid", "yes"):
                out["regions"].append(dict(layer=L, vertices=[dict(x=x1, y=y1), dict(x=x2, y=y1), dict(x=x2, y=y2), dict(x=x1, y=y2)]))
            else:
                for a, b in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
                    out["tracks"].append(dict(x1=a[0], y1=a[1], x2=b[0], y2=b[1], width=w, layer=L))
        elif g[0] == "fp_circle":
            (cx, cy), (ex, ey) = xy("center"), xy("end")
            out["arcs"].append(dict(x=cx, y=cy, radius=math.hypot(ex - cx, ey - cy), start_angle=0.0, end_angle=360.0,
                                    width=w, layer=L))
        elif g[0] == "fp_arc":
            cx, cy, r, a1, a2 = arc_from_3pts(xy("start"), xy("mid"), xy("end"))
            out["arcs"].append(dict(x=cx, y=cy, radius=r, start_angle=a1, end_angle=a2, width=w, layer=L))
        elif g[0] == "fp_poly":
            pts = [(num(q[1]), -num(q[2])) for q in kids(kid(g, "pts"), "xy")]
            fill = kid(g, "fill")
            if fill is not None and fill[1] in ("solid", "yes") or L in ("Top Courtyard",):
                out["regions"].append(dict(layer=L, vertices=[dict(x=a, y=b) for a, b in pts]))
            else:
                for a, b in zip(pts, pts[1:] + pts[:1]):
                    out["tracks"].append(dict(x1=a[0], y1=a[1], x2=b[0], y2=b[1], width=w, layer=L))
    m = kid(fp, "model")
    if m is not None:
        step = os.path.join(PCB, m[1].replace("${KIPRJMOD}/", ""))
        off = [num(v) for v in kid(kid(m, "offset"), "xyz")[1:]] if kid(m, "offset") is not None else [0, 0, 0]
        rot = [num(v) for v in kid(kid(m, "rotate"), "xyz")[1:]] if kid(m, "rotate") is not None else [0, 0, 0]
        if os.path.exists(step):
            out["step_model"] = dict(filepath=step, embed=True, x_offset=off[0], y_offset=-off[1], z_offset=off[2],
                                     rotation=rot[2])
        else:
            notes.append(f"STEP model {m[1]} not found")
    for k in ("tracks", "arcs", "regions"):
        if not out[k]:
            out.pop(k)
    return out, notes


# ---------------------------------------------------------------- symbols
ETYPE = {"input": "input", "output": "output", "bidirectional": "bidirectional", "tri_state": "hi_z",
         "passive": "passive", "free": "passive", "unspecified": "passive", "power_in": "power", "power_out": "power",
         "open_collector": "open_collector", "open_emitter": "open_emitter", "no_connect": "passive"}
OUTWARD = {0: "left", 90: "down", 180: "right", 270: "up"}          # KiCad angle points to the body


def u(mm):
    return round(mm / SCH_UNIT_MM, 2)


def convert_symbol_graphics(sym):
    pins, rects, polys, arcs = [], [], [], []
    for sub in kids(sym, "symbol"):
        for g in sub[2:]:
            if not isinstance(g, list) or not g:
                continue
            if g[0] == "pin":
                at, ln = kid(g, "at"), num(kid(g, "length")[1])
                x, y, ang = num(at[1]), num(at[2]), int(round(num(at[3]))) % 360
                bx, by = x + ln * math.cos(math.radians(ang)), y + ln * math.sin(math.radians(ang))
                nm = kid(g, "name")[1]
                no = kid(g, "number")[1]
                pins.append(dict(designator=no, name=(no if nm in ("~", "") else nm).replace("|", "/"),
                                 x=round(u(bx)), y=round(u(by)), length=max(1, round(u(ln))),
                                 orientation=OUTWARD[ang], electrical_type=ETYPE.get(g[1], "passive")))
            elif g[0] == "rectangle":
                s, e = kid(g, "start"), kid(g, "end")
                fill = kid(g, "fill")
                filled = fill is not None and kid(fill, "type") is not None and kid(fill, "type")[1] in ("background", "outline")
                xs, ys = sorted((u(num(s[1])), u(num(e[1])))), sorted((u(num(s[2])), u(num(e[2]))))
                rects.append(dict(x1=xs[0], y1=ys[0], x2=xs[1], y2=ys[1], filled=filled, fill_color=0xB0FFFF))
            elif g[0] == "polyline":
                pts = [dict(x=u(num(q[1])), y=u(num(q[2]))) for q in kids(kid(g, "pts"), "xy")]
                if len(pts) >= 2:
                    polys.append(dict(points=pts, line_width=1))
            elif g[0] == "circle":
                c, r = kid(g, "center"), num(kid(g, "radius")[1])
                arcs.append(dict(x=u(num(c[1])), y=u(num(c[2])), radius=u(r), start_angle=0, end_angle=360))
            elif g[0] == "arc":
                s, m, e = (tuple(num(v) for v in kid(g, k)[1:3]) for k in ("start", "mid", "end"))
                cx, cy, r, a1, a2 = arc_from_3pts(s, m, e)
                arcs.append(dict(x=u(cx), y=u(cy), radius=u(r), start_angle=round(a1, 2), end_angle=round(a2, 2)))
    return pins, rects, polys, arcs


def symbol_props(sym):
    return {p[1]: p[2] for p in kids(sym, "property")}


# ---------------------------------------------------------------- MCP client
class MCP:
    def __init__(self, binary, allow):
        self.p = subprocess.Popen([binary, "-q", "--allow", *allow], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, bufsize=1)
        self.i = 0
        info = self.request("initialize", dict(protocolVersion="2025-06-18", capabilities={},
                                               clientInfo=dict(name="qbfx2-altium-builder", version="1.0")))
        self.server = info.get("serverInfo", {})
        self.notify("notifications/initialized")

    def notify(self, method, params=None):
        msg = dict(jsonrpc="2.0", method=method)
        if params is not None:
            msg["params"] = params
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()

    def request(self, method, params):
        self.i += 1
        self.p.stdin.write(json.dumps(dict(jsonrpc="2.0", id=self.i, method=method, params=params)) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("server closed: " + self.p.stderr.read()[-2000:])
            msg = json.loads(line)
            if msg.get("id") == self.i:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg["result"]

    def call(self, tool, **args):
        r = self.request("tools/call", dict(name=tool, arguments=args))
        text = "".join(c.get("text", "") for c in r.get("content", []) if c.get("type") == "text")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = dict(text=text)
        if r.get("isError"):
            raise RuntimeError(f"{tool} failed: {text[:2000]}")
        return data

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=30)


# ---------------------------------------------------------------- build
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", default=os.environ.get("ALTIUM_MCP_BIN", DEFAULT_BIN))
    args = ap.parse_args()
    os.makedirs(REP, exist_ok=True)
    pcblib = os.path.join(OUT, f"{LIBNAME}.PcbLib")
    schlib = os.path.join(OUT, f"{LIBNAME}.SchLib")
    libpkg = os.path.join(OUT, f"{LIBNAME}.LibPkg")

    fps, fp_notes, src = [], {}, {}
    for f in sorted(os.listdir(os.path.join(PCB, "qbfx2.pretty"))):
        if f.endswith(".kicad_mod"):
            d, n = convert_footprint(os.path.join(PCB, "qbfx2.pretty", f))
            fps.append(d)
            fp_notes[d["name"]] = n
            src[d["name"]] = d

    kis = parse_sexpr(open(os.path.join(PCB, "qbfx2.kicad_sym")).read())
    syms_src = {s[1]: s for s in kids(kis, "symbol")}
    bom = list(csv.DictReader(open(os.path.join(PCB, "fab", "qbfx2_carrier_bom.csv"))))
    graphic_for = {"C_0603_1608Metric": "C", "R_0603_1608Metric": "R", "SMP_Amphenol_SMP-MSLD-PCS-NM": "SMP",
                   "MicroD_15P_Glenair_MWDM2L-15PCBRP": "MicroD_15P", "QBFX2_DIE_BONDPADS": "QBF-X2_die",
                   "MountingHole_2.7mm_M2.5_Pad": "MountingHole_Pad"}
    symbols = []
    for row in bom:
        fpname = row["Footprint"].split(":")[-1]
        gsym = syms_src[graphic_for[fpname]]
        pins, rects, polys, arcs = convert_symbol_graphics(gsym)
        props = symbol_props(gsym)
        prefix = re.sub(r"[^A-Za-z]", "", props.get("Reference", "U")) or "U"
        value = row["Value"]
        mpn = row["MPN"] if row["MPN"] not in ("-", "") else ""
        if prefix in ("R", "C"):
            raw = f"{graphic_for[fpname]}_{value}_0603"
        elif graphic_for[fpname] == "QBF-X2_die":
            raw = "QBF-X2_die"
        elif graphic_for[fpname] == "MountingHole_Pad":
            raw = f"MountingHole_{value}"
        else:
            raw = mpn or value
        name = re.sub(r"[^A-Za-z0-9_.+-]", "_", raw).strip("_")[:60]
        params = [dict(name="Value", value=value), dict(name="Manufacturer", value=row["Manufacturer"]),
                  dict(name="Manufacturer Part Number", value=mpn or "-"),
                  dict(name="MPN Status", value=row["MPN status"]), dict(name="QBF-X2 BOM item", value=row["Item"])]
        sym = dict(name=name, description=row["Description"].replace("|", "/")[:250], designator_prefix=prefix,
                   parameters=[{k: str(v).replace("|", "/") for k, v in p.items()} for p in params],
                   footprints=[dict(name=fpname, library_path=f"{LIBNAME}.PcbLib")], pins=pins)
        if rects:
            sym["rectangles"] = rects
        if polys:
            sym["polylines"] = polys
        if arcs:
            sym["arcs"] = arcs
        symbols.append(sym)

    mcp = MCP(args.bin, [OUT, PCB])
    report = dict(tool=dict(repository="https://github.com/embedded-society/altium-designer-mcp", server=mcp.server),
                  footprints=[], symbols=[])
    wp = mcp.call("write_pcblib", filepath=pcblib, footprints=fps, append=False, auto_designator=True)
    ws = mcp.call("write_schlib", filepath=schlib, symbols=symbols, append=False)
    wl = mcp.call("write_libpkg", filepath=libpkg, documents=[f"{LIBNAME}.SchLib", f"{LIBNAME}.PcbLib"])
    report["write"] = dict(pcblib={k: wp.get(k) for k in ("status", "warnings", "bodies") if k in wp},
                           schlib={k: ws.get(k) for k in ("status", "warnings") if k in ws},
                           libpkg={k: wl.get(k) for k in ("status",) if k in wl})
    report["validate"] = dict(pcblib=mcp.call("validate_library", filepath=pcblib),
                              schlib=mcp.call("validate_library", filepath=schlib))

    # round trip: read the written libraries back and compare with the KiCad source
    rp = mcp.call("read_pcblib", filepath=pcblib)
    back = {f["name"]: f for f in rp.get("footprints", [])}
    fp_ok = True
    for name, s in src.items():
        b = back.get(name)
        ok, worst = b is not None, 0.0
        if ok:
            bp = sorted(b.get("pads", []), key=lambda q: (q["designator"], round(q["x"], 3), round(q["y"], 3)))
            sp = sorted(s["pads"], key=lambda q: (q["designator"], round(q["x"], 3), round(q["y"], 3)))
            ok = len(bp) == len(sp)
            for a, c in zip(sp, bp):
                worst = max(worst, abs(a["x"] - c["x"]), abs(a["y"] - c["y"]), abs(a["width"] - c["width"]),
                            abs(a["height"] - c["height"]), abs(a.get("hole_size", 0) - c.get("hole_size", 0) or 0))
            ok = ok and worst < 1e-3
        has_step = bool(b and (b.get("step_model") or b.get("model_3d")))
        report["footprints"].append(dict(name=name, pads=len(s["pads"]), round_trip_ok=ok, max_dev_mm=worst,
                                         step_model_embedded=has_step, notes=fp_notes[name]))
        fp_ok &= ok
    rs = mcp.call("read_schlib", filepath=schlib)
    sback = {s["name"]: s for s in rs.get("symbols", [])}
    sym_ok = True
    for s in symbols:
        b = sback.get(s["name"])
        ok = b is not None and len(b.get("pins", [])) == len(s["pins"])
        report["symbols"].append(dict(name=s["name"], pins=len(s["pins"]), footprint=s["footprints"][0]["name"],
                                      mpn=next(p["value"] for p in s["parameters"] if p["name"] == "Manufacturer Part Number"),
                                      round_trip_ok=ok))
        sym_ok &= ok
    with open(os.path.join(REP, "previews.txt"), "w") as fh:
        for s in src:
            r = mcp.call("render_footprint", filepath=pcblib, component_name=s)
            fh.write(f"==== footprint {s}\n{r.get('rendering', r.get('ascii', r.get('text', json.dumps(r)[:3000])))}\n\n")
        for s in symbols:
            r = mcp.call("render_symbol", filepath=schlib, component_name=s["name"])
            fh.write(f"==== symbol {s['name']}\n{r.get('rendering', r.get('ascii', r.get('text', json.dumps(r)[:3000])))}\n\n")
    mcp.close()
    v_err = lambda v: [x for x in v.get("issues", v.get("errors", [])) if (x.get("severity", "error") if isinstance(x, dict) else "error") == "error"]
    report["summary"] = dict(footprints=len(src), symbols=len(symbols), round_trip_footprints_ok=fp_ok,
                             round_trip_symbols_ok=sym_ok,
                             validation_errors=dict(pcblib=len(v_err(report["validate"]["pcblib"])),
                                                    schlib=len(v_err(report["validate"]["schlib"]))),
                             files=[os.path.basename(x) for x in (pcblib, schlib, libpkg)])
    json.dump(report, open(os.path.join(REP, "altium_report.json"), "w"), indent=1, default=str)
    print(json.dumps(report["summary"], indent=1))
    return 0 if (fp_ok and sym_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
