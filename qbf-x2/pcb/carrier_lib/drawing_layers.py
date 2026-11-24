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
        f" ref. In1). Fab may trim w by +/-0.02 mm. TDR coupon + report required.",
        "4  FINISH: NICKEL-FREE. Preferred EPAG (electroless Pd 0.1-0.3 um + immersion Au 0.05-0.1 um) or",
        "   electrolytic soft Au >= 0.5 um directly on Cu. Acceptable: immersion Ag (bond within 4 weeks) or ENEPIG",
        "   with high-P Ni (P >= 10 %) <= 1 um. DO NOT use ENIG or HASL.",
        "   WHY: ENIG carries 3-6 um electroless Ni(P), ferromagnetic at low P content or after heat cycles. At 10 mK",
        "   next to a flux-based die it traps vortices, offsets the flux bias and adds loss/noise. HASL Sn/SnPb",
        "   is not wire-bondable. Au/Pd surfaces take Al-1%Si wedge bonds; Ag tarnishes (store dry, N2).",
        "5  SOLDER MASK: green LPI, both sides, 10-25 um. NO mask in the die bond band (F.Mask openings) and on pads.",
        "   Min. mask dam 0.10 mm. B.Mask opened 2.0 mm along the outer edge (GND contact to the Cu base).",
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
    rf_note = "TRAP/ACC (8) and RO (2), all F.Cu"
    cpad = 8.854e-12 * P.GCPW["er"] * (math.pi * 0.375 ** 2 - P.GCPW["w"] * 0.75) * 1e-6 / (P.GCPW["h"] * 1e-3)
    zrows = [["GCPW line (" + rf_note + ")", "F.Cu", "In1", f"{P.GCPW['w']:.2f}", f"{P.GCPW['gap']:.2f}",
              f"{P.GCPW['h']:.3f}", f"{P.GCPW['er']:.2f}", f"{z0:.2f}", "50 +/-5 %", "PASS" if abs(z0 - 50) <= 2.5 else "FAIL"],
             ["GCPW arc bends R 1.00 (same cross-section)", "F.Cu", "In1", f"{P.GCPW['w']:.2f}", f"{P.GCPW['gap']:.2f}",
              f"{P.GCPW['h']:.3f}", f"{P.GCPW['er']:.2f}", f"{z0:.2f}", "50 +/-5 %", "PASS" if abs(z0 - 50) <= 2.5 else "FAIL"],
             ["Bond landing pad 0.40 x 0.60 (line start, no mask)", "F.Cu", "In1", f"{P.GCPW['w']:.2f}",
              f"{P.GCPW['gap']:.2f}", f"{P.GCPW['h']:.3f}", f"{P.GCPW['er']:.2f}", f"{z0:.2f}", "50 +/-5 %",
              "PASS" if abs(z0 - 50) <= 2.5 else "FAIL"],
             ["SMP launch pad dia 0.75, anti-pad dia 1.65", "F.Cu", "In1", "0.75", "0.45", f"{P.GCPW['h']:.3f}",
              f"{P.GCPW['er']:.2f}", f"lumped {cpad * 1e15:.0f} fF", "info", "n/a"]]
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
        "3  J1-J10 SMP: reflow with the land pattern of the vendor drawing; check centre-pin coplanarity < 0.1 mm.",
        "4  J11 micro-D: hand-solder after reflow; trim tails to <= 0.3 mm below the board (or relieve the base).",
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
    for k, refs in groups.items():
        pt = P.PARTS[k]
        refs = sorted(refs, key=lambda r: (r.rstrip("0123456789"), int("".join(ch for ch in r if ch.isdigit()) or 0)))
        rs = ",".join(refs) if len(refs) <= 6 else f"{refs[0]}...{refs[-1]} ({len(refs)})"
        brows.append([rs, str(len(refs)), pt["value"], pt["mfr"], pt["mpn"], pt["status"]])
    y = D.table(ASM, 205, yn + 2, [("Ref", 44), ("Qty", 10), ("Value", 22), ("Manufacturer", 30), ("MPN", 42),
                                   ("Status", 28)], brows, "BOM SUMMARY (full BOM: fab/qbfx2_carrier_bom.csv)", 1.2)
    prow = [[str(k), P.MICROD_PINS[k] + "_IN", f"{P.MICROD_PINS[k]} (die)"] for k in range(1, 9)]
    prow.append(["9-15, SH", "GND", "returns + shell"])
    D.table(ASM, 16, 166, [("J11 pin", 18), ("Net (connector side)", 44), ("Filtered to", 40)], prow,
            "J11 MICRO-D PINOUT", 1.2)
    lrows = []
    L = info["lengths"]
    for a, bb in (("TRAP_A0", "TRAP_B0"), ("TRAP_A1", "TRAP_B1"), ("ACC_A0", "ACC_B0"), ("ACC_A1", "ACC_B1")):
        lrows.append([f"{a} / {bb}", f"{L[a]:.3f}", f"{L[bb]:.3f}", f"{abs(L[a] - L[bb]):.4f}", "<= 0.20 mm"])
    lrows.append(["RO_IN / RO_OUT", f"{L['RO_IN']:.3f}", f"{L['RO_OUT']:.3f}", f"{abs(L['RO_IN'] - L['RO_OUT']):.4f}", "info"])
    D.table(ASM, 16, 200, [("Pair (A / B)", 38), ("A (mm)", 18), ("B (mm)", 18), ("|dL| (mm)", 18), ("Limit", 22)], lrows,
            "RF TRACK LENGTHS, landing-pad centre to SMP pin (KiCad DRC skew rule + reports/length_report.txt)", 1.2)
