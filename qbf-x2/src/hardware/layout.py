"""Preliminary QBF-X2 layout (gdstk), drawn to scale from the architecture. NOT fabrication-ready: no DRC, no
EM extraction, coupling-capacitor crossover process unverified (see FEASIBILITY.md).

Layers: 1/0 Nb ground plane and strips | 2/0 granular-Al rail inductors | 3/0 Al bottom electrode (+ thin-Al coupler
strips) | 4/0 Al top electrode | 5/0 Cu injector resistors | 6/0 crossover dielectric (coupling capacitors) |
10/0 annotation. Rows (top to bottom): D_A, A0, A1, B1, B0, D_B; each row is an opening in the ground plane with a
granular-Al signal line on its centre line and one junction rung per 2 um cell to the edge selected by the section.
Coupling capacitors (crossover dielectric) are drawn on all three couplers: the gate coupler A1-B1 and the dummy
couplers D_A-A0 and B0-D_B, which must match it. Junction overlaps follow the architecture (one Jc for the chip).
Not drawn: the node shunt capacitors (0.50 fF, reduced to 0.29 fF on the coupler plateaus) and the middle-rail
island shunts (0.31 fF); they are to come from the geometric capacitance of the node pads, lines and islands plus a
trim, fixed by EM extraction.
"""
from __future__ import annotations

import gdstk

from hardware.architecture import Architecture, jj_area_for
from hardware.netlist import PAIRS, ROWS, _env, _in_section

L_NB, L_GRAL, L_AL1, L_AL2, L_CU, L_DIEL, L_TXT = (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (10, 0)
ROW_H = 8.0          # opening height (um)
STRIP_W = 2.0        # Nb strip between rows
MARGIN = 60.0


def _rect(cell, x0, y0, x1, y1, layer):
    cell.add(gdstk.rectangle((x0, y0), (x1, y1), layer=layer[0], datatype=layer[1]))


def rung_direction(row: str, sec: str) -> int:
    """+1: rung goes up to the strip above, -1: down to the strip below"""
    table = {"D_A": {"cpl": -1, "bs": -1, "else": -1}, "A0": {"cpl": +1, "bs": -1, "else": -1},
             "A1": {"cpl": -1, "bs": +1, "else": +1}, "B1": {"cpl": +1, "bs": -1, "else": -1},
             "B0": {"cpl": -1, "bs": +1, "else": +1}, "D_B": {"cpl": +1, "bs": +1, "else": +1}}
    return table[row][sec]


def build(arch: Architecture, path: str):
    p = arch.rail.pitch_um
    N = arch.n_cells
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    top = lib.new_cell("QBFX2_PRELIM")
    W = N * p + 2 * MARGIN
    Hh = len(ROWS) * ROW_H + (len(ROWS) + 1) * STRIP_W + 2 * MARGIN
    ground = gdstk.rectangle((0, 0), (W, Hh), layer=1)
    holes = []
    yc = {}
    y = Hh - MARGIN - STRIP_W
    for row in ROWS:
        y0 = y - ROW_H
        holes.append(gdstk.rectangle((MARGIN - 4, y0), (MARGIN + N * p + 4, y), layer=1))
        yc[row] = 0.5 * (y0 + y)
        y = y0 - STRIP_W
    # isolated strips: coupler strips and BS middle rails are cut out of the ground plane (separate Nb pieces)
    cut, pieces = [], []
    def strip_between(r_up, r_dn):
        return yc[r_up] - ROW_H / 2 - STRIP_W, yc[r_up] - ROW_H / 2
    s_sec = {d["name"]: d for d in arch.sections()}
    cs = s_sec["taper_in"]["start"]
    ce = s_sec["taper_out"]["start"] + s_sec["taper_out"]["cells"]
    for (r_up, r_dn), kind in ((("D_A", "A0"), "cpl"), (("A1", "B1"), "cpl"), (("B0", "D_B"), "cpl")):
        ya, yb = strip_between(r_up, r_dn)
        x0, x1 = MARGIN + cs * p, MARGIN + ce * p
        cut.append(gdstk.rectangle((x0, ya - 0.2), (x1, yb + 0.2), layer=1))
        _rect(top, x0 + 1, ya + 0.8, x1 - 1, ya + 1.2, L_AL1)                 # thin-Al shared strip, 0.4 um wide
        _rect(top, x0 - 1, ya + 0.8, x0 + 1, ya + 1.2, L_AL1)                 # ends tied to ground
        _rect(top, x1 - 1, ya + 0.8, x1 + 1, ya + 1.2, L_AL1)
    AM = jj_area_for(arch.EJ_M_GHz)
    jm_w = 0.18                                                                    # middle-rail junction overlap width
    jm_l = AM / jm_w
    for q, (r_up, r_dn), mirrored in (("A", ("A0", "A1"), False), ("B", ("B1", "B0"), True)):
        ya, yb = strip_between(r_up, r_dn)
        for sec in ("BS_prep", "BS_analysis"):
            ns = [n for n in range(N) if _in_section(arch, n, sec, mirrored)]
            x0, x1 = MARGIN + ns[0] * p, MARGIN + (ns[-1] + 1) * p
            cut.append(gdstk.rectangle((x0, ya - 0.2), (x1, yb + 0.2), layer=1))
            for n in ns:                                                         # middle-rail islands + series junctions
                xa = MARGIN + n * p
                pieces.append(gdstk.rectangle((xa + 0.15, ya + 0.3), (xa + p - 0.35, yb - 0.3), layer=1))
                _rect(top, xa + p - 0.55, ya + 0.9, xa + p - 0.25 + jm_l, ya + 0.9 + jm_w, L_AL1)
                _rect(top, xa + p - 0.25, ya + 0.85, xa + p + 0.35, ya + 1.13, L_AL2)
    gp = gdstk.boolean(ground, holes + cut, "not", layer=1)
    for g in gp + pieces:
        top.add(g)
    # rows: node pads, granular-Al inductors, rungs with junctions
    A_rail = jj_area_for(arch.rail.EJ_GHz)
    jw = 0.20
    jl = A_rail / jw
    for row in ROWS:
        mirrored = row in ("B1", "B0", "D_B")
        for n in range(N):
            x = MARGIN + n * p
            y = yc[row]
            _rect(top, x - 0.3, y - 0.3, x + 0.3, y + 0.3, L_AL1)                          # node pad
            if n < N - 1:
                _rect(top, x + 0.3, y - 0.35, x + p - 0.3, y + 0.35, L_GRAL)               # 0.66 nH granular Al
            sec = "cpl" if _env(arch, n) > 0 else ("bs" if row in ("A0", "A1", "B1", "B0") and (
                _in_section(arch, n, "BS_prep", mirrored) or _in_section(arch, n, "BS_analysis", mirrored)) else "else")
            d = rung_direction(row, sec)
            edge = y + d * ROW_H / 2
            y_j = y + d * (ROW_H / 2 - 1.0)
            lo, hi = sorted((y + d * 0.3, y_j))
            _rect(top, x - jw / 2, lo, x + jw / 2, hi, L_AL1)                                # bottom electrode lead
            lo2, hi2 = sorted((y_j - d * jl, edge + d * 0.3))
            _rect(top, x - 0.3, lo2, x + 0.3, hi2, L_AL2)                                    # top electrode to return
    # coupling capacitors across the gate and dummy coupler strips (crossover dielectric, proposed)
    n_caps = 0
    for r_up, r_dn in PAIRS.values():
        for n in range(N):
            g = _env(arch, n)
            if g > 0:
                x = MARGIN + n * p
                ya = yc[r_up] - 0.3
                yb = yc[r_dn] + 0.3
                wcap = 0.15 + 0.5 * g
                _rect(top, x + 0.7, yb, x + 0.7 + wcap, ya, L_DIEL)
                n_caps += 1
    # injectors and catchers (blocks), labels
    for row in ("A0", "A1", "B1", "B0"):
        mirrored = row in ("B1", "B0")
        xs = MARGIN - 30 if not mirrored else MARGIN + N * p + 6
        _rect(top, xs, yc[row] - 2, xs + 24, yc[row] + 2, L_CU)
        top.add(gdstk.Label(f"INJ {row}" if not mirrored else f"INJ {row}", (xs, yc[row] + 2.5), layer=10))
        xe = MARGIN + N * p + 6 if not mirrored else MARGIN - 30
        _rect(top, xe, yc[row] - 3, xe + 24, yc[row] + 3, L_NB)
        top.add(gdstk.Label(f"CATCH {row}", (xe, yc[row] - 3.5), layer=10))
    for d in arch.sections():
        x = MARGIN + d["start"] * p
        top.add(gdstk.Label(d["name"], (x, Hh - MARGIN + 6), layer=10))
        _rect(top, x, Hh - MARGIN + 2, x + 0.5, Hh - MARGIN + 5, L_TXT)
    for row in ROWS:
        top.add(gdstk.Label(row, (MARGIN - 50, yc[row]), layer=10))
    lib.write_gds(path)
    dims = dict(width_um=W, height_um=Hh, rows=len(ROWS), row_opening_um=ROW_H, strip_um=STRIP_W, pitch_um=p,
                cells_per_row=N, junction_overlap_um=(jw, round(jl, 4)), junction_area_um2=round(A_rail, 4),
                middle_junction_overlap_um=(jm_w, round(jm_l, 4)), middle_junction_area_um2=round(AM, 4),
                coupling_capacitors_drawn=n_caps,
                coupler_span_um=(ce - cs) * p, bs_length_um=arch.n_bs * p, status="PRELIMINARY - not fabrication-ready")
    return dims


def preview(gds_path: str, png_path: str, box=None, size=(1600, 700)):
    import klayout.db as db
    import klayout.lay as lay
    cols = {"1/0": (0x8a8f99, 9), "2/0": (0xff8c1a, 0), "3/0": (0x2f6bff, 0), "4/0": (0xff2aff, 0),
            "5/0": (0x8b4513, 0), "6/0": (0x22aa55, 0), "10/0": (0x111111, 0)}
    v = lay.LayoutView()
    v.load_layout(gds_path)
    v.max_hier()
    v.set_config("background-color", "#ffffff")
    v.set_config("grid-visible", "false")
    v.set_config("text-visible", "true")
    it = v.begin_layers()
    while not it.at_end():
        lp = it.current().dup()
        key = f"{lp.source_layer}/{lp.source_datatype}"
        c, dp = cols.get(key, (0x999999, 0))
        lp.fill_color = c
        lp.frame_color = c
        lp.dither_pattern = dp
        lp.transparent = key == "1/0"
        v.set_layer_properties(it, lp)
        it.next()
    if box:
        v.zoom_box(db.DBox(*box))
    else:
        v.zoom_fit()
    v.save_image(png_path, *size)
