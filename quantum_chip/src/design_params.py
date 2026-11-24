"""Single source of truth for the Q4 flux-tunable transmon assembly.

All lengths in micrometres unless the name ends in _mm.
Edit values here and re-run `make all` (see README) to regenerate every output.
"""

# ---------------------------------------------------------------- die (KQCircuits)
DIE = dict(
    size_um=10000.0,            # 10 x 10 mm die (KQC standard)
    substrate="high-resistivity Si(100), >10 kOhm.cm",
    substrate_thickness_um=525.0,
    substrate_eps_r=11.45,
    film="Al",                  # base metal film
    film_thickness_nm=200.0,
    jj_bottom_nm=40.0,          # Al, first evaporation (Manhattan double-angle)
    jj_oxide_nm=1.5,            # AlOx tunnel barrier (nominal)
    jj_top_nm=80.0,             # Al, second evaporation
    airbridge_thickness_nm=600.0,
    airbridge_height_um=3.0,
    cpw_a=10.0, cpw_b=6.0,      # KQC default CPW centre / gap (~50 ohm on Si)
)

# 4 qubits in a linear chain. x positions (die coordinates 0..10000 um)
QUBIT_Y = 6000.0
QUBIT_X = [2600.0, 4200.0, 5800.0, 7400.0]
# Design-intent readout frequencies (GHz) -> half-wave resonator lengths.
READOUT_F_GHZ = [6.8, 7.0, 7.2, 7.4]
FEEDLINE_Y = 2600.0

# Launcher pads per side (N, E, S, W) and their nets, KQC clockwise port ids.
LAUNCHERS_PER_SIDE = (6, 2, 0, 2)
LAUNCHER = dict(width=240.0, gap=179.0, indent=680.0, pitch=1200.0)
# port id -> net name. N: 1..6 left->right, E: 7 (upper), 8 (lower), W: 9 (lower), 10 (upper)
TRANSMON_LAUNCHER_NETS = {
    1: "Q1_FLUX", 2: "Q2_DRIVE", 3: "Q2_FLUX", 4: "Q3_FLUX", 5: "Q3_DRIVE", 6: "Q4_FLUX",
    7: "Q4_DRIVE", 8: "PROBE_OUT", 9: "PROBE_IN", 10: "Q1_DRIVE",
}

# ---------------------------------------------------------------- RF carrier PCB
PCB = dict(
    size_mm=40.0,
    window_mm=10.30,            # through-window for the die (150 um clearance per side)
    bondpad_len_mm=0.60, bondpad_w_mm=0.40,
    bondpad_setback_mm=0.10,    # PCB pad inner edge to window edge
    gnd_ring_w_mm=0.70,         # exposed ENIG ground ring around window (gnd bonds)
    stitch_pitch_mm=1.0,
    via_drill_mm=0.25, via_pad_mm=0.50,
    blind_drill_mm=0.15, blind_pad_mm=0.35,
)

# Physical stackup, top to bottom. thickness in mm.
STACKUP = [
    ("F.Mask",  "soldermask", 0.020, "LPI solder mask, red, eps_r 3.8"),
    ("F.Cu",    "copper",     0.035, "1 oz Cu + ENIG on exposed pads (Ni 4 um / Au 0.08 um)"),
    ("diel1",   "dielectric", 0.203, "Rogers RO4003C core, eps_r 3.55, tan_d 0.0027"),
    ("In1.Cu",  "copper",     0.018, "0.5 oz Cu - solid GND plane"),
    ("diel2",   "dielectric", 0.200, "Rogers RO4450F prepreg, eps_r 3.52"),
    ("In2.Cu",  "copper",     0.018, "0.5 oz Cu - flux-line stripline routing"),
    ("diel3",   "dielectric", 0.200, "Rogers RO4450F prepreg, eps_r 3.52"),
    ("In3.Cu",  "copper",     0.018, "0.5 oz Cu - solid GND plane"),
    ("diel4",   "dielectric", 0.508, "Rogers RO4003C core, eps_r 3.55"),
    ("In4.Cu",  "copper",     0.018, "0.5 oz Cu - GND reference plane for bottom routing"),
    ("diel5",   "dielectric", 0.203, "Rogers RO4003C core, eps_r 3.55"),
    ("B.Cu",    "copper",     0.035, "1 oz Cu - SMP launch routing + GND pour"),
    ("B.Mask",  "soldermask", 0.020, "LPI solder mask, red"),
]

PACKAGE = dict(
    base_material="OFHC copper, 2 um Au over 2 um Ni (non-magnetic would use Ag)",
    base_thickness_mm=4.0,
    die_attach="GE 7031 varnish, 20 um",
    die_attach_um=20.0,
    wirebond="Al-1%Si wedge bond, 25 um",
    wire_d_um=25.0,
    loop_height_um=180.0,
    bonds_per_signal=2,
)

# ---------------------------------------------------------------- Reversible Fluxon Logic die (active design)
# Ballistic RFL (Wustmann & Osborn, LPS; Frank et al., Sandia ABRC): unpowered, undamped discrete LJJs
# carry fluxons between gates; only the DC/SFQ inputs and SFQ/DC outputs need bias.
RFL = dict(
    process="Nb/AlOx/Nb trilayer, 2 Nb wiring layers over Nb ground plane (SFQ5ee-like, simplified)",
    jc_kA_cm2=10.0,
    jj_ic_uA=50.0,             # LJJ node junctions, area 0.5 um^2 at 10 kA/cm^2
    jj_area_um2=0.5,
    jj_c_fF_per_um2=50.0,
    cell_pitch_um=10.0,        # one JJ per 10 um of 10 um wide M1 strip
    cell_L_pH=0.48,            # ~1 square of Nb microstrip over GP (mu0 (d + 2 lambda_L))
    alpha_qp=1e-4,             # design: sub-gap damping at T < 1 K (R_sg > 150 kOhm); alpha = 1/(w_p R_sg C)
    alpha_4K2=0.03,            # same junctions at 4.2 K (R_sg ~ 15 R_n ~ 500 Ohm)
    barrier_bmax=8.0,          # controlled-barrier SQUID Ic_max / Ic (two 200 uA JJs)
    longest_line_cells=1800,   # TEST racetrack (~18 mm meander)
)
RFL_STACK = [  # (layer, gds, material, true thickness nm)
    ("GP", (1, 0), "Nb ground plane M0", 200),
    ("I0", (2, 0), "SiO2 ILD (sheet) / via GP-M1", 200),
    ("M1", (3, 0), "Nb M1: LJJ strips, JJ base electrode", 150),
    ("JJ", (4, 0), "AlOx barrier + Nb counter-electrode", 100),
    ("I1", (5, 0), "SiO2 ILD (sheet) / via M1-M2", 200),
    ("R", (6, 0), "Mo resistor, 2 ohm/sq", 40),
    ("M2", (7, 0), "Nb M2: I/O microstrip, bias lines, pads, JJ straps", 300),
    ("PAD", (8, 0), "Ti/Au bond-pad metallisation", 100),
    ("VIA", (9, 0), "stacked Nb vias (I0+I1 contacts)", 400),
]
LAUNCHER_NETS = {
    1: "VB_W", 2: "TRIG_A", 3: "CTRL_CB", 4: "CTRL_RE", 5: "TRIG_B", 6: "VB_E",
    7: "OUT_1", 8: "TEST_OUT", 9: "TEST_IN", 10: "OUT_0",
}
