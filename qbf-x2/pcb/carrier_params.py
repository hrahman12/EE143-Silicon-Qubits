"""QBF-X2 cryogenic RF carrier PCB: single source of truth for every generated file.

Edit a value here and run ./export_carrier.sh: the schematic, the board, the design rules, all checks and all
fabrication / assembly outputs are rebuilt from scratch.

Conventions
-----------
* Lengths in millimetres unless the name ends in _um, _nH, _pF, ...
* Board frame: origin at the die centre (= centre of the die window), x to the right, y UP (as die_pads.json).
  The writer converts to KiCad page coordinates (y down) with PAGE_ORIGIN.
* The chip-to-board interface is read from ../circuits/die_pads.json (the contract) and is never copied here.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
QBFX2_ROOT = os.environ.get("QBFX2_ROOT", os.path.abspath(os.path.join(HERE, "..")))
DIE_PADS_JSON = os.environ.get("QBFX2_DIE_PADS", os.path.join(QBFX2_ROOT, "circuits", "die_pads.json"))
# closed-form impedance formulas of the QFX-1 carrier (read-only reference implementation)
RF_CALC_PY = os.environ.get("QBFX2_RF_CALC",
                            os.path.abspath(os.path.join(QBFX2_ROOT, "..", "quantum_chip", "src", "rf_calc.py")))

# ------------------------------------------------------------------------------------------------ project
PROJECT = dict(
    name="qbfx2_carrier",
    title="QBF-X2 carrier",
    rev="A",
    date="2026-11-24",
    author="QBF-X2 project",
    lib="qbfx2",                     # project-local symbol + footprint library nickname
    board_text="QBF-X2 CARRIER  REV A  2026-11-24",
)

# ------------------------------------------------------------------------------------------------ board
BOARD = dict(
    x_min=-26.0, x_max=26.0, y_min=-26.0, y_max=26.0,   # 52 x 52 mm, die centred
    corner_r=1.0,
    page="A3",                      # fab / assembly drawings are plotted from the board page
    page_origin=(85.0, 128.0),      # KiCad page position of the die centre (mm, y down)
    zone_inset=0.30,                # copper pour pull-back from the outer routed edge
    inner_window_pullback=0.30,     # inner-layer copper pull-back from the die window
    top_window_pullback=0.10,       # top copper (bond ring / bond pads) to the die-window edge
    track_start_in_pad=0.30,        # tracks start this far outward of the landing-pad centre (end cap >= 0.3 mm from edge)
)

# die window (through-cut; the die sits on a pedestal of the sample-holder base, top flush with the PCB top)
WINDOW = dict(
    clearance=0.15,                 # die edge to window edge, each side
    relief_r=0.60,                  # corner relief radius (router <= 1.2 mm), clears the die corners
)

# PCB wire-bond pads (footprint U1 = the 24 landing pads, numbered as die_pads.json ids)
BONDPAD = dict(
    setback=0.10,                   # window edge -> pad inner edge
    length=0.60,                    # radial
    width=0.39,                     # lateral (= GCPW centre conductor, so the line starts at the pad)
    mask_expansion=0.05,
    gnd_open_margin=0.27,           # exposed-ground (bond landing) openings keep this far from signal copper
    ring_open_out=0.95,             # exposed bond band: window edge -> outer edge of the mask opening
)

# ------------------------------------------------------------------------------------------------ stackup
# (name, kind, thickness mm, material, eps_r, loss tangent, note); top to bottom. Symmetric 3-core build.
STACKUP = [
    ("F.Mask", "mask", 0.020, "LPI solder mask", 3.8, 0.025, "green LPI; open over RF lines + bond band"),
    ("F.Cu", "copper", 0.035, "Cu 1 oz (finished)", None, None, "RF GCPW, bond pads, parts, GND pour"),
    ("diel1", "core", 0.203, "Rogers RO4003C", 3.55, 0.0027, "core 1 (8 mil); GCPW dielectric"),
    ("In1.Cu", "copper", 0.018, "Cu 0.5 oz", None, None, "solid GND: GCPW reference plane"),
    ("diel2", "prepreg", 0.203, "Rogers RO4450F", 3.52, 0.004, "2 x 4 mil plies"),
    ("In2.Cu", "copper", 0.018, "Cu 0.5 oz", None, None, "DC routing (stripline between In1/In3) + GND fill"),
    ("diel3", "core", 0.508, "Rogers RO4003C", 3.55, 0.0027, "core 2 (20 mil)"),
    ("In3.Cu", "copper", 0.018, "Cu 0.5 oz", None, None, "solid GND"),
    ("diel4", "prepreg", 0.203, "Rogers RO4450F", 3.52, 0.004, "2 x 4 mil plies"),
    ("In4.Cu", "copper", 0.018, "Cu 0.5 oz", None, None, "solid GND"),
    ("diel5", "core", 0.203, "Rogers RO4003C", 3.55, 0.0027, "core 3 (8 mil)"),
    ("B.Cu", "copper", 0.035, "Cu 1 oz (finished)", None, None, "solid GND; contacts the sample-holder base"),
    ("B.Mask", "mask", 0.020, "LPI solder mask", 3.8, 0.025, "opened along the board perimeter (base contact)"),
]
COPPER_LAYERS = [s[0] for s in STACKUP if s[1] == "copper"]
FINISH = "EPAG (Ni-free Pd-Au)"          # stackup copper_finish -> Gerber job file; see fab note 4

# ------------------------------------------------------------------------------------------------ RF lines
# 50-ohm grounded CPW on F.Cu over the In1 plane. Required check: rf_calc.gcpw_z0 (Ghione-Naldi conformal mapping,
# zero thickness, no mask) within +/-5 %. Cross-check: 2D field solve with 35 um copper (carrier_lib/fd2d.py).
# The zero-thickness formula reads ~8 % high for a 35 um / 0.15 mm-gap line and LPI mask in the gaps costs another
# ~8 %, so the RF lines are mask-free and w/gap sit between the two models (formula +4 %, field solve -4.5 %).
# Design eps_r 3.55 = Rogers RO4003C "design Dk" at 10 GHz.
GCPW = dict(
    layer="F.Cu", w=0.39, gap=0.17, h=0.203, er=3.55, z_target=50.0, z_tol=0.05, t_cu=0.035,
    bend_r=1.00,                    # every bend is a tangent arc (R / w = 2.6): no mitres, no stubs
    mask_free=True,                 # F.Mask opening over trace + gaps (stops 0.01 mm short of the ground copper)
    corridor_inset=0.01,
)
VIA_FENCE = dict(pitch=1.00, offset=0.625, start_r=6.50)   # offset from line centre; first row radius at the die

# fast flux lines: connector columns west (A lines) and east (B lines), 7 mm pitch
FAST = dict(
    x_conn=18.0,                    # |x| of the SMP column
    y_conn_acc=3.5,                 # |y| of the ACC connectors (inner pair)
    y_conn_trap=10.5,               # |y| of the TRAP connectors (outer pair)
    x_bend_trap=7.4,                # |x| where the TRAP lines leave the die-normal direction (45 deg)
    x_bend_acc=8.4,                 # |x| where the ACC lines bend (diagonals 1.56 mm apart)
)
READOUT = dict(
    x_conn=7.0, y_conn=-18.0,       # RO_IN at (-x, y), RO_OUT at (+x, y)
    y_bend=7.5,                     # |y| where the readout lines turn 45 deg away from the die axis
)

# ------------------------------------------------------------------------------------------------ DC lines
DC = dict(
    fcu_width=0.20,                 # F.Cu stubs and filter wiring
    in2_width=0.15,                 # In2 stripline routing
    clearance=0.20,
    via_r_from_die=7.10,            # LOAD-line via |x| (W/E rows); GATE-line via |y| (N/S rows) = gate_via_r
    gate_via_r=7.00,
    load_via_dy=0.50,               # LOAD vias sit 0.5 mm further from the die axis than the pad (corner side)
    corridor=(5.55, 5.95),          # In2 corridor under the bond pads (|offset| from die centre), inner/outer
    corner_jog=(1.15, 1.75),        # inner/outer track leaves the corridor this far before the window corner
    jog=0.60,                       # 45-degree jog out of the corridor around the corner relief
    exit_y=(6.5, 5.6),              # inner/outer track: |y| where the corner detour ends (N side)
    corner_clear=0.975,             # In2 track centre to window-corner relief centre (0.6 + 0.3 + w/2)
)
# filter bank (top side, between the die and the DC connector); channel order is fixed by the planar routing
FILTER_BANK = dict(
    pitch=3.5,
    y_out_via=9.0,                  # die-side via of every channel (F.Cu <-> In2)
    cap_dx=1.5,                     # shunt capacitor column offset (>= 0603 courtyard width 1.46 mm)
    rows=dict(R1=6.3, C1=4.7, R2=3.3, C2=1.7),   # part centres above the output via (courtyards 2.96 mm long)
    cap_via_dx=2.45,                # cap GND via offset from the resistor column
    fanin_levels=[18.1, 17.65, 17.2, 16.85, 16.85, 17.2, 17.65, 18.1],  # J11 fan-in jog heights
    channels=["LOAD_A0", "LOAD_A1", "GATE_BSB_AN", "GATE_BSA_PREP",
              "GATE_BSA_AN", "GATE_BSB_PREP", "LOAD_B0", "LOAD_B1"],
)
# component values. Gate lines: 2-stage RC ladder into a high-impedance gate. Load lines: R-C-R T-section, sized
# for the real load (1 nH load loop shorted to ground on chip -> current drive) and also checked open-circuit.
FILTERS = dict(
    gate=dict(topology="RC-RC ladder", R1=10e3, C1=10e-9, R2=10e3, C2=10e-9, fc_max=10e3),
    load=dict(topology="R-C-R T-section", R1=1.0e3, C=18e-12, R2=1.0e3, band=(10e6, 20e6), bw_min=5e6),
    source_R=50.0,                  # AWG / DAC through the fridge wiring (50-ohm coax), used as a second case
    load_loop_L=1e-9,               # QBF-X2 load loop (src/hardware/architecture.py launcher_values)
)

# ------------------------------------------------------------------------------------------------ vias, rules
VIAS = dict(
    stitch_drill=0.20, stitch_pad=0.45,     # GND stitching / fences (aspect ratio 1.50 / 0.20 = 7.5)
    dc_drill=0.25, dc_pad=0.50,             # DC-signal transitions (F.Cu -> In2), unused-layer pads removed
    grid=2.0,                               # background stitching grid
    edge_row_inset=1.0, edge_row_pitch=1.5,  # stitching row along the outer edge
    min_spacing=0.70,                       # centre-centre between stitching vias
)
RULES = dict(
    min_clearance=0.15, min_track=0.12, min_via_diam=0.45, min_via_drill=0.20, min_annular=0.125,
    min_hole_to_hole=0.25, min_hole_clearance=0.20, copper_edge_clearance=0.10, via_edge_clearance=0.30,
    track_edge_clearance=0.30, silk_clearance=0.10, mask_min_web=0.10, skew_max=0.20,
)

# ------------------------------------------------------------------------------------------------ mechanics
MOUNT = dict(holes=[(-22.5, -22.5), (22.5, -22.5), (22.5, 22.5), (-22.5, 22.5)], drill=2.7, pad=5.0,
             screw="M2.5 brass or Ti (non-magnetic) into the Cu sample-holder base")
DOWELS = dict(holes=[(-12.5, -21.0), (16.5, 21.5)], drill=1.60, note="NPTH, for 1.5 mm dowel pins in the base")
FIDUCIALS = [(-17.5, -23.5), (17.5, -23.5), (-23.5, 16.5)]
# DC connector (right-angle micro-D on the north edge). Land pattern drawn from typical data: TO CONFIRM.
MICROD = dict(x=0.0, y_row1=19.0, pitch=2.54, row_dy=2.54, drill=0.70, pad=1.10,
              mount_dx=12.6, mount_y=23.2, mount_drill=1.20, mount_pad=2.0)
# J11 pin assignment (pins 1..8 = filtered DC inputs, row 1; 9..15 = GND returns, row 2)
MICROD_PINS = {1: "LOAD_A0", 2: "LOAD_A1", 3: "GATE_BSB_AN", 4: "GATE_BSA_PREP",
               5: "GATE_BSA_AN", 6: "GATE_BSB_PREP", 7: "LOAD_B0", 8: "LOAD_B1"}

# RF connector reference designators (J1..J10) in schematic order
SMP_REFS = ["TRAP_A0", "ACC_A0", "ACC_A1", "TRAP_A1", "TRAP_B1", "ACC_B1", "ACC_B0", "TRAP_B0", "RO_IN", "RO_OUT"]

# ------------------------------------------------------------------------------------------------ parts (BOM)
# status: "confirmed" = part number seen in distributor / manufacturer listings during design (2026-11);
#         "to confirm" = series confirmed, exact ordering code built from the series scheme and not yet checked.
PARTS = dict(
    SMP=dict(value="SMP jack", mfr="Amphenol RF", mpn="SMP-MSLD-PCS-NM", status="confirmed",
             descr="SMP straight PCB jack, surface mount, limited detent, non-magnetic (BeCu/Au, LCP)",
             footprint="SMP_Amphenol_SMP-MSLD-PCS-NM",
             note="non-magnetic; land pattern generic - confirm against the Amphenol drawing"),
    MICROD=dict(value="MWDM 15P R/A", mfr="Glenair", mpn="MWDM2L-15PCBRP-.110", status="confirmed",
                descr="Micro-D 15-pin plug, condensed right-angle PCB, jackposts",
                footprint="MicroD_15P_Glenair_MWDM2L-15PCBRP",
                note="land pattern + shell finish TO CONFIRM (ask for a non-magnetic shell finish)"),
    R10K=dict(value="10k", mfr="Vishay Dale Thin Film", mpn="PNM0603E1002BST5", status="confirmed",
              descr="Thin-film resistor 10 kOhm 0.1 % 25 ppm 0603, non-magnetic (PNM series)",
              footprint="R_0603_1608Metric", note="distributor listing: 10 kOhm 0.1 % 0603 non-magnetic"),
    R1K=dict(value="1k", mfr="Vishay Dale Thin Film", mpn="PNM0603E1001BST5", status="confirmed",
             descr="Thin-film resistor 1 kOhm 0.1 % 25 ppm 0603, non-magnetic (PNM series)",
             footprint="R_0603_1608Metric", note="distributor listing found; same series as the 10 kOhm part"),
    C10N=dict(value="10n C0G", mfr="Vishay Vitramon", mpn="VJ0603A103JCAAJ", status="to confirm",
              descr="MLCC 10 nF 5 % 50 V C0G (NP0) 0603, VJ Non-Magnetic series (termination C = Cu barrier)",
              footprint="C_0603_1608Metric",
              note="code built from the VJ Non-Magnetic ordering scheme, not seen listed; if 10 nF/0603 is not "
                   "offered use 1 nF (gate f-3dB 5.96 kHz, still <= 10 kHz) or a Knowles Syfer non-magnetic C0G"),
    C18P=dict(value="18p C0G", mfr="Vishay Vitramon", mpn="VJ0603A180JCAAJ", status="to confirm",
              descr="MLCC 18 pF 5 % 50 V C0G (NP0) 0603, VJ Non-Magnetic series (termination C = Cu barrier)",
              footprint="C_0603_1608Metric",
              note="code built from the VJ Non-Magnetic ordering scheme, not seen listed (W1BC parts have Ni barrier)"),
    DIE=dict(value="QBF-X2", mfr="QBF-X2 project", mpn="QBF-X2 die rev per circuits/", status="customer supplied",
             descr="QBF-X2 superconducting die 10 x 10 x 0.525 mm, wire-bonded (24 launchers)",
             footprint="QBFX2_DIE_BONDPADS", note="not part of PCBA; die attach + Al wedge bonding after assembly"),
    MH=dict(value="M2.5", mfr="-", mpn="-", status="mechanical", descr="Mounting hole 2.7 mm plated, GND",
            footprint="MountingHole_2.7mm_M2.5_Pad", note="board feature, not purchased"),
)
