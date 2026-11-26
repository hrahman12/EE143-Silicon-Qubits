"""Content of the fab-notes layer (Dwgs.User -> fabrication drawing) and of the assembly layer (Cmts.User).

Page: A3 landscape, board centre at carrier_params.BOARD['page_origin']. All numbers come from the build data.
"""
import math

import carrier_params as P

FAB, ASM = "Dwgs.User", "Cmts.User"


def fab_and_assembly(D, K, info):
    b = P.BOARD
    z0 = info["z"][0]
    W, R = info["W"], info["R"]
    tl, br = K((b["x_min"], b["y_max"])), K((b["x_max"], b["y_min"]))
    thick = sum(s[2] for s in P.STACKUP)

    # ------------------------------------------------------------------------------------- fabrication drawing
    D.text(FAB, f"FABRICATION DRAWING - {P.PROJECT['title']} rev {P.PROJECT['rev']} ({P.PROJECT['date']})",
           16, 16, 2.6, 0.4)
    D.text(FAB, f"6-layer Rogers RO4003C / RO4450F, {b['x_max'] - b['x_min']:.1f} x {b['y_max'] - b['y_min']:.1f} mm, "
                f"{thick:.2f} mm finished, Ni-free finish. Units mm. View from TOP.", 16, 21, 1.5)
    D.dimension(FAB, (tl[0], br[1]), (br[0], br[1]), 7.0, f"{b['x_max'] - b['x_min']:.2f}")
    D.dimension(FAB, (tl[0], tl[1]), (tl[0], br[1]), 7.0, f"{b['y_max'] - b['y_min']:.2f}")
    mh = P.MOUNT["holes"]
    a, c = K((mh[3][0], mh[3][1])), K((mh[2][0], mh[2][1]))
    D.dimension(FAB, a, c, -(a[1] - tl[1]) - 5.0, f"{mh[2][0] - mh[3][0]:.2f} (M2.5 x4)")
    wa, wb = K((-W, -W)), K((W, -W))
    D.dimension(FAB, wa, wb, 2.5, f"{2 * W:.2f} window")
    D.text(FAB, f"Die window {2 * W:.2f} x {2 * W:.2f} through-route, corner reliefs R{R:.2f}", br[0] + 3,
           K((0, 0))[1] - 1.5, 1.2)
    D.text(FAB, f"(die {info['die_size']:.1f} x {info['die_size']:.1f} mm on base pedestal)", br[0] + 3,
           K((0, 0))[1] + 0.7, 1.2)
    for i, (x, y) in enumerate(P.DOWELS["holes"]):
        k = K((x, y))
        D.text(FAB, f"NPTH {P.DOWELS['drill']:.2f} (dowel)", k[0] + (3.0 if x > 0 else -3.0), k[1] - 3.0, 1.0,
               justify="left" if x > 0 else "right")

    # stackup table
    rows = []
    for name, kind, t, mat, er, tand, note in P.STACKUP:
        rows.append([name, kind, mat, f"{t:.3f}", "" if er is None else f"{er:.2f}", "" if tand is None else f"{tand}",
                     note])
    rows.append(["TOTAL", "", "", f"{thick:.3f}", "", "", "finished thickness, tolerance +/-10 %"])
    y = D.table(FAB, 16, 166, [("Layer", 18), ("Type", 16), ("Material", 33), ("t (mm)", 15), ("er", 10),
                               ("tan d", 13), ("Function / note", 77)], rows, "STACKUP (top to bottom)", 1.25)
    D.text(FAB, "Cores RO4003C (Dk 3.38 process / 3.55 design), prepreg RO4450F; symmetric 3-core build, one lamination,"
                " through vias only.", 16, y + 3, 1.2)

    # fab notes (right column)
    notes = [
        "1  MATERIAL: Rogers RO4003C cores 0.203 / 0.508 / 0.203 mm, RO4450F prepreg 2 x 0.102 mm per opening. No FR-4.",
        f"2  THICKNESS {thick:.2f} mm +/-10 %. Outer Cu 1 oz finished (incl. plating), inner Cu 0.5 oz.",
        f"3  IMPEDANCE: F.Cu GCPW {P.GCPW['z_target']:.0f} ohm +/-5 % (w {P.GCPW['w']:.2f} / gap {P.GCPW['gap']:.2f} mm,"
        f" ref. In1, no mask, 35 um Cu). Fab may trim w by +/-0.02 mm with its field solver. TDR coupon + report.",
        f"   DIFF PAIRS (TRAP_*/ACC*_P/N): edge-coupled GCPW, Z_odd 50 ohm +/-5 % = Z_diff 100 ohm (w {P.DIFF['w']:.2f} /"
        f" P-N gap {P.DIFF['s']:.2f} / GND gap {P.DIFF['g']:.2f}); coupon pair + TDR (odd mode).",
        "4  FINISH: NICKEL-FREE. Preferred EPAG (electroless Pd 0.1-0.3 um + immersion Au 0.05-0.1 um) or",
        "   electrolytic soft Au >= 0.5 um directly on Cu. Acceptable: immersion Ag (bond within 4 weeks) or ENEPIG",
        "   with high-P Ni (P >= 10 %) <= 1 um. DO NOT use ENIG or HASL.",
        "   WHY: ENIG carries 3-6 um electroless Ni(P), ferromagnetic at low P content or after heat cycles. At 10 mK",
        "   next to a flux-based die it traps vortices, offsets the flux bias and adds loss/noise. HASL Sn/SnPb",
        "   is not wire-bondable. Au/Pd surfaces take Al-1%Si wedge bonds; Ag tarnishes (store dry, N2).",
        "5  SOLDER MASK: green LPI, both sides, 10-25 um. NO mask over the RF lines (trace + gaps, F.Mask openings), in",
        "   the die bond band and on pads. Min. mask dam 0.10 mm. B.Mask opened 2.0 mm along the outer edge (base contact).",
        "6  SILKSCREEN: white epoxy, top and bottom, never on pads or in the bond band.",
        f"7  VIAS: through only, finished {P.VIAS['stitch_drill']:.2f} mm (GND) and {P.VIAS['dc_drill']:.2f} mm (DC). "
        "Tented both sides. DC vias: non-functional inner pads removed.",
        f"8  DIE WINDOW: {2 * W:.2f} x {2 * W:.2f} mm routed through, +/-0.05 mm, corner reliefs R{R:.2f} (router <= 1.2 mm),",
        "   no burrs, wall NOT plated. Cu pull-back from the window: 0.10 mm top (bond pads), 0.30 mm inner/bottom.",
        f"9  OUTLINE {b['x_max'] - b['x_min']:.2f} x {b['y_max'] - b['y_min']:.2f} mm, R{b['corner_r']:.1f} corners, "
        "routed +/-0.10 mm. Cu pull-back 0.30 mm from the outer edge on all layers.",
        "10 HOLES per drill table: PTH +/-0.05 mm (vias +0.05/-0.10), NPTH dowel holes +/-0.03 mm.",
        "11 QUALITY: IPC-6012 class 2 (class 3 preferred), IPC-A-600 class 2. 100 % electrical test vs netlist.",
        "12 NON-MAGNETIC: no Ni underplate anywhere; report finish thicknesses (XRF) with the shipment.",
        "13 CLEANLINESS: ionic contamination < 1.56 ug/cm2 NaCl eq.; bake 2 h at 120 C; vacuum pack.",
        "14 DATA: Gerber X2 (fab/gerbers), Excellon PTH + NPTH (fab/drill), this drawing. Origin = board lower-left.",
        "15 Not supplied (KiCad 7 cannot write them): ODB++, IPC-2581. IPC-D-356 netlist on request.",
    ]
    yn = D.notes(FAB, 205, 13, "FAB NOTES", notes, 1.2, 1.78)

    # impedance table
    rf_note = "RO (2) and the split legs of the pairs, F.Cu"
    gc = P.GCPW
    fd = info["fd"]
    Dp, fdp, cfp = P.DIFF, info["fd_pair"], info["cf_pair"]
    cpad = 8.854e-12 * gc["er"] * (math.pi * 0.375 ** 2 - gc["w"] * 0.75) * 1e-6 / (gc["h"] * 1e-3)
    ok = lambda zz: "PASS" if abs(zz - 50) <= 2.5 else "FAIL"  # noqa: E731
    zrows = [["GCPW line, mask-free (" + rf_note + ")", "F.Cu", "In1", f"{gc['w']:.2f}", f"{gc['gap']:.2f}",
              f"{gc['h']:.3f}", f"{gc['er']:.2f}", f"{z0:.2f}", "50 +/-5 %", ok(z0)],
             [f"Diff pair routed, Z_odd formula / field (s = {Dp['s']:.2f})", "F.Cu", "In1", f"{Dp['w']:.2f}",
              f"{Dp['g']:.2f}", f"{gc['h']:.3f}", f"{gc['er']:.2f}",
              f"{cfp['']['z_odd']:.1f} / {fdp['']['z_odd']:.1f}", "50 +/-5 %",
              ok(cfp['']['z_odd']) if ok(cfp['']['z_odd']) == ok(fdp['']['z_odd']) else "FAIL"],
             [f"  same, Z_even / Z_diff / Z_cm, field solve (k = {fdp['']['k']:.3f})", "F.Cu", "In1", "", "", "", "",
              f"{fdp['']['z_even']:.1f}/{fdp['']['z_diff']:.0f}/{fdp['']['z_cm']:.1f}", "info", ""],
             [f"Diff pair breakout at the die (s = {Dp['s_bo']:.2f}), Z_odd field", "F.Cu", "In1", f"{Dp['w_bo']:.2f}",
              f"{Dp['g_bo']:.2f}", f"{gc['h']:.3f}", f"{gc['er']:.2f}", f"{fdp['_bo']['z_odd']:.1f}", "50 +/-5 %",
              ok(fdp['_bo']['z_odd'])],
             ["GCPW arc bends R 1.00 (same cross-section)", "F.Cu", "In1", f"{gc['w']:.2f}", f"{gc['gap']:.2f}",
              f"{gc['h']:.3f}", f"{gc['er']:.2f}", f"{z0:.2f}", "50 +/-5 %", ok(z0)],
             [f"Bond landing pad {gc['w']:.2f} x 0.60 (line start)", "F.Cu", "In1", f"{gc['w']:.2f}",
              f"{gc['gap']:.2f}", f"{gc['h']:.3f}", f"{gc['er']:.2f}", f"{z0:.2f}", "50 +/-5 %", ok(z0)],
             ["Cross-check: 2D field solve, 35 um Cu, mask on grounds", "F.Cu", "In1", f"{gc['w']:.2f}",
              f"{gc['gap']:.2f}", f"{gc['h']:.3f}", f"{gc['er']:.2f}", f"{fd['z0']:.2f}", "50 +/-5 %", ok(fd["z0"])],
             ["SMP launch pad dia 0.75, anti-pad dia 1.65", "F.Cu", "In1", "0.75", "0.45", f"{gc['h']:.3f}",
              f"{gc['er']:.2f}", f"lumped {cpad * 1e15:.0f} fF", "info", "n/a"]]
    y = D.table(FAB, 205, yn + 2, [("Segment type", 76), ("Layer", 12), ("Ref", 10), ("w", 10), ("gap", 10), ("h", 11),
                                   ("er", 10), ("Z0 (ohm)", 22), ("Target", 18), ("", 12)], zrows,
                "CONTROLLED IMPEDANCE (rf_calc.gcpw_z0: conductor-backed CPW, Ghione-Naldi conformal map, t = 0)", 1.2)

    # drill table
    use = {"0.20 PTH": "GND stitching / GCPW fences / launch cages", "0.25 PTH": "DC signal transitions F.Cu-In2",
           "0.70 PTH": "J11 micro-D tails (0.51 mm pins)", "1.20 PTH": "J11 mounting / shell (GND)",
           "2.70 PTH": "M2.5 mounting holes (GND)", "1.60 NPTH": "dowel holes (base alignment)"}
    drows = []
    for (d, kind), n in sorted(info["drills"].items(), key=lambda kv: (kv[0][1], kv[0][0])):
        key = f"{d:.2f} {kind}"
        drows.append([f"{d:.2f}", kind, str(n), use.get(key, "")])
    drows.append(["TOTAL", "", str(sum(info["drills"].values())), "see drill map (next page)"])
    y = D.table(FAB, 205, y + 4, [("Finished dia (mm)", 30), ("Plating", 18), ("Qty", 14), ("Use", 82)], drows,
                "DRILL TABLE", 1.2)

    # ------------------------------------------------------------------------------------- assembly drawing
    D.text(ASM, f"ASSEMBLY DRAWING (TOP) - {P.PROJECT['title']} rev {P.PROJECT['rev']} ({P.PROJECT['date']})",
           16, 16, 2.6, 0.4)
    D.text(ASM, "All parts on the top side. Bottom = continuous GND (contacts the Cu sample-holder base).", 16, 21, 1.5)
    an = [
        "1  SMT reflow, top side only: SAC305 (or Sn63Pb37), no-clean low-residue flux, then clean (IPA). No bottom parts.",
        "2  Use ONLY the BOM parts (non-magnetic): no Ni-barrier terminations, no X7R/X5R, no ferrite, no brass.",
        "3  J1-J10, J12-J19 SMP (18): reflow with the vendor land pattern; centre-pin coplanarity < 0.1 mm. The 16",
        "   fast-line jacks are 8 differential pairs (P / N side by side): connect both coax legs of a pair together.",
        "4  J11 micro-D: hand-solder after reflow. Its tails + fillets (DC signals) reach the bottom: the Cu base NEEDS a",
        f"   relief pocket >= 1.5 mm deep under the J11 tail field (x -11..+11, y +{P.MICROD['y_row1'] - 2:.0f}.."
        f"+{P.MICROD['y_row1'] + 4:.0f} mm from the die centre).",
        "5  Board to base: dowels in DW1/DW2, then 4 x M2.5 non-magnetic (brass / Ti) screws in H1-H4, 0.25 N m.",
        "6  Die U1 (customer supplied, after PCBA + cleaning): on the base pedestal, top flush with the PCB top",
        f"   (pedestal {thick - 0.525 - 0.02:.3f} mm above the base for 20 um varnish), GE 7031 varnish or Ag paint.",
        "   Orientation: die launcher 1 at the NW corner of the north row (dot on F.Fab), ids per die_pads.json.",
        "7  Wire bonds: Al-1%Si 25 um wedge, 2 per signal launcher, <= 1.0 mm long, straight (pads are aligned);",
        "   ground bonds from the die ground plane to the exposed GND band: >= 2 between launchers + 4 per corner.",
        "8  ESD: Josephson junctions - ground all SMP and J11 lines while bonding and handling.",
        "9  Fiducials FID1-FID3 (1.0 mm Cu, 2.0 mm mask opening). Placement origin = board lower-left corner.",
    ]
    yn = D.notes(ASM, 205, 13, "ASSEMBLY NOTES", an, 1.2, 1.78)
    groups = {}
    for ref, c in info["comps"].items():
        k = c["part"]
        groups.setdefault(k, []).append(ref)
    brows = []
    def ranges(refs):
        """J1,J2,...,J10,J12,...,J19 -> 'J1-J10,J12-J19'"""
        nums = [(r.rstrip("0123456789"), int("".join(ch for ch in r if ch.isdigit()) or 0)) for r in refs]
        out, i = [], 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1][0] == nums[i][0] and nums[j + 1][1] == nums[j][1] + 1:
                j += 1
            pre = nums[i][0]
            out.append(f"{pre}{nums[i][1]}" if j == i else f"{pre}{nums[i][1]}-{pre}{nums[j][1]}" if j > i + 1
                       else f"{pre}{nums[i][1]},{pre}{nums[j][1]}")
            i = j + 1
        return ",".join(out)
    for k, refs in groups.items():
        pt = P.PARTS[k]
        refs = sorted(refs, key=lambda r: (r.rstrip("0123456789"), int("".join(ch for ch in r if ch.isdigit()) or 0)))
        rs = ranges(refs) + (f" ({len(refs)})" if len(refs) > 6 else "")
        brows.append([rs, str(len(refs)), pt["value"], pt["mfr"], pt["mpn"], pt["status"]])
    y = D.table(ASM, 205, yn + 2, [("Ref", 44), ("Qty", 10), ("Value", 22), ("Manufacturer", 30), ("MPN", 42),
                                   ("Status", 28)], brows, "BOM SUMMARY (full BOM: fab/qbfx2_carrier_bom.csv)", 1.2)
    prow = [[str(k), P.MICROD_PINS[k] + "_IN", f"{P.MICROD_PINS[k]} (die)"] for k in range(1, 9)]
    prow.append(["9-15, SH", "GND", "returns + shell"])
    D.table(ASM, 16, 162, [("J11 pin", 16), ("Net (connector side)", 44), ("Filtered to", 40)], prow,
            "J11 MICRO-D PINOUT", 1.15)
    lrows = []
    L = info["lengths"]
    prs = info["pairs"]
    for name in P.FAST_PAIRS:
        pr = prs[name]
        lrows.append([name, f"{pr['L_P']:.3f}", f"{pr['L_N']:.3f}", f"{abs(pr['skew_mm']):.4f}", "<= 0.10 mm"])
    for a, bb in P.AB_PAIRS:
        ma = (prs[a]["L_P"] + prs[a]["L_N"]) / 2
        mb = (prs[bb]["L_P"] + prs[bb]["L_N"]) / 2
        lrows.append([f"{a} / {bb} (mean)", f"{ma:.3f}", f"{mb:.3f}", f"{abs(ma - mb):.4f}", "<= 0.20 mm"])
    lrows.append(["RO_IN / RO_OUT", f"{L['RO_IN']:.3f}", f"{L['RO_OUT']:.3f}", f"{abs(L['RO_IN'] - L['RO_OUT']):.4f}", "info"])
    D.table(ASM, 16, 200, [("Pair  (P / N, or A / B)", 40), ("P | A (mm)", 18), ("N | B (mm)", 18), ("|dL| (mm)", 18),
                           ("Limit", 20)], lrows,
            "RF TRACK LENGTHS (KiCad DRC skew + length rules, reports/length_report.txt)", 1.15)
    detail_view(D, info, (218.0, 178.0), 2.0)
    bonding_diagram(D, info, (352.0, 168.0), 5.0)


# ------------------------------------------------------------------------------------------------ scaled views
def _fp_to_board(lp, pos, rot):
    a = math.radians(rot)
    x, y = lp[0], -lp[1]
    return (pos[0] + x * math.cos(a) - y * math.sin(a), pos[1] + x * math.sin(a) + y * math.cos(a))


def detail_view(D, info, centre, scale, layer=ASM):
    """top assembly detail: board + window outline, F.Fab outlines of every footprint, reference designators"""
    cx, cy = centre

    def T(p):
        return (cx + p[0] * scale, cy - p[1] * scale)
    b = P.BOARD
    D.text(layer, f"TOP ASSEMBLY DETAIL, SCALE {scale:g}:1 (references on F.Fab)", cx - (b['x_max'] - b['x_min']) * scale / 2,
           cy - b["y_max"] * scale - 7.5, 1.6)
    corners = [(b["x_min"], b["y_min"]), (b["x_max"], b["y_min"]), (b["x_max"], b["y_max"]), (b["x_min"], b["y_max"])]
    for a, c in zip(corners, corners[1:] + corners[:1]):
        D.line(layer, T(a), T(c), 0.3)
    W = info["W"]
    wc = [(-W, -W), (W, -W), (W, W), (-W, W)]
    for a, c in zip(wc, wc[1:] + wc[:1]):
        D.line(layer, T(a), T(c), 0.25)
    for fp in info["fps"]:
        F, pos, rot = fp["fp"], fp["pos"], fp["rot"]
        for g in F.gfx:
            if g[1] != "F.Fab":
                continue
            if g[0] == "fp_rect":
                (x0, y0), (x1, y1) = g[2], g[3]
                pts = [_fp_to_board(q, pos, rot) for q in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
                for a, c in zip(pts, pts[1:] + pts[:1]):
                    D.line(layer, T(a), T(c), 0.15)
            elif g[0] == "fp_circle":
                if g[3] < 0.5:                       # skip pin markers: they collide with the designator text
                    continue
                D.circle(layer, T(_fp_to_board(g[2], pos, rot)), g[3] * scale, 0.15)
            elif g[0] == "fp_line":
                D.line(layer, T(_fp_to_board(g[2], pos, rot)), T(_fp_to_board(g[3], pos, rot)), 0.15)
            elif g[0] == "fp_poly":
                pts = [_fp_to_board(q, pos, rot) for q in g[2]]
                for a, c in zip(pts, pts[1:]):
                    D.line(layer, T(a), T(c), 0.15)
        ref = fp["ref"]
        small = F.name.startswith(("R_", "C_"))
        size = 1.05 if small else 1.4
        at = T(pos)
        if F.name.startswith("MicroD"):
            at = T((pos[0], pos[1] + 3.0))
        if F.name.startswith("QBFX2_DIE"):
            at = T((0, 1.5))
        D.text(layer, ref, at[0], at[1], size, justify="center", rot=90 if (small and rot % 180) else 0)
        if F.name.startswith("SMP"):
            nm = info["comps"][ref]["pins"]["1"]
            off = T((pos[0], pos[1] - 2.9))
            D.text(layer, nm, off[0], off[1], 1.0, justify="center")
    p1 = T((-3.5 * P.MICROD["pitch"] - 1.3, P.MICROD["y_row1"]))
    D.text(layer, "1", p1[0], p1[1], 1.2, justify="center")


def bonding_diagram(D, info, centre, scale, layer=ASM):
    """die pad -> PCB landing pad map (two Al wedge bonds per launcher), numbered per die_pads.json"""
    cx, cy = centre

    def T(p):
        return (cx + p[0] * scale, cy - p[1] * scale)
    h = info["die_size"] / 2
    W = info["W"]
    D.text(layer, f"WIRE-BOND DIAGRAM, SCALE {scale:g}:1", cx - 8.0 * scale, cy - 10.6 * scale, 1.6)
    D.text(layer, "die launcher ids = circuits/die_pads.json = U1 pad numbers", cx - 8.0 * scale, cy - 10.6 * scale + 2.6, 1.2)
    for (a, c, w) in (((-h, -h), (h, h), 0.3), ((-W, -W), (W, W), 0.15)):
        pts = [(a[0], a[1]), (c[0], a[1]), (c[0], c[1]), (a[0], c[1])]
        for p0, p1 in zip(pts, pts[1:] + pts[:1]):
            D.line(layer, T(p0), T(p1), w)
    D.text(layer, "QBF-X2 die", *T((0, 1.0)), 1.5, justify="center")
    D.text(layer, "10 x 10 mm, top view", *T((0, 0.0)), 1.2, justify="center")
    D.text(layer, f"window {2 * W:.2f} mm", *T((0, -1.0)), 1.2, justify="center")
    for pid, (pc, u) in info["pcb_pads"].items():
        dc = info["die_pads"][pid]
        net = info["pad_nets"][pid]
        sx, sy = (0.24, 0.24)
        lw = info.get("land_w", {}).get(pid, 0.39)
        for (c, (w_, h_)) in ((dc, (sx, sy)), (pc, ((0.6, lw) if u[0] else (lw, 0.6)))):
            pts = [(c[0] - w_ / 2, c[1] - h_ / 2), (c[0] + w_ / 2, c[1] - h_ / 2), (c[0] + w_ / 2, c[1] + h_ / 2),
                   (c[0] - w_ / 2, c[1] + h_ / 2)]
            for p0, p1 in zip(pts, pts[1:] + pts[:1]):
                D.line(layer, T(p0), T(p1), 0.15)
        lat = (-u[1], u[0])
        for off in (-0.06, 0.06):
            a = (dc[0] + lat[0] * off, dc[1] + lat[1] * off)
            b = (pc[0] - u[0] * 0.1 + lat[0] * off, pc[1] - u[1] * 0.1 + lat[1] * off)
            D.line(layer, T(a), T(b), 0.12)
        num = (dc[0] - u[0] * 0.55, dc[1] - u[1] * 0.55)
        D.text(layer, str(pid), *T(num), 1.15, justify="center")
        lab = (pc[0] + u[0] * 0.45, pc[1] + u[1] * 0.45)
        rot = 90 if u[1] else 0
        just = "left" if (u[0] > 0 or u[1] > 0) else "right"
        D.text(layer, net, *T(lab), 1.15, justify=just, rot=rot)
    for i, s_ in enumerate(("Lines: two 25 um Al-1%Si wedge bonds per launcher, straight (pads aligned).",
                            "Ground bonds: die ground plane to the exposed GND band",
                            "between the landing pads and at the four corners.")):
        D.text(layer, s_, cx - 8.0 * scale, cy + 9.0 * scale + 2.0 * i, 1.15)
