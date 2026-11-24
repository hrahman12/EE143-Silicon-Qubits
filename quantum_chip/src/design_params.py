"""Single source of truth for the assembly: die (QFX-1 quantum fluxon by default; RFL and the 4-transmon die are
kept), RF carrier, package and process stacks.

All lengths in micrometres unless the name ends in _mm.
Edit values here and re-run ./build_all.sh to regenerate every output.
"""
import math

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

# ---------------------------------------------------------------- QFX-1: quantum-fluxon processor (active design)
# Qubit = one Josephson vortex (fluxon) in a double well of a discrete annular LJJ made of small Al/AlOx/Al
# junctions and granular-aluminium (grAl) cell inductors. Classical heavy fluxons in a Nb ballistic line act on it.
QFX = dict(
    ring_cells=24,             # junctions around the annular array (winding number 1 = one trapped fluxon)
    EJ_GHz=39.7,               # small Al junction, Ic = 80 nA (Wolfram-checked)
    EC_GHz=8.07,               # C = 2.4 fF (Wolfram-checked)
    Lambda=1.0,                # Josephson length in cells -> E_L = Lambda^2 E_J (grAl cell inductor ~4.1 nH)
    well_weak=0.70,            # pinning junctions: E_J (1 - w)
    well_sep=2,                # cells between the two pinning junctions
    barrier_EJmax_ratio=1.35,  # barrier dc-SQUID, total E_J,max / E_J: f01 = 3.2 GHz at zero flux, tunable upward
    phi_b_op=0.0,              # operate at zero SQUID flux: df01/dPhi_b = 0 (and eps = 0) -> double sweet spot
    T_mK=20.0,
    # one Al/AlOx/Al junction process for the whole die: Jc and the specific capacitance tie area, Ic and C together
    jc_uA_per_um2=1.665,       # 166.5 A/cm^2
    c_spec_fF_per_um2=50.0,    # Al/AlOx/Al
    ring_jj_area_um2=0.048,    # 80 nA, 2.40 fF  (-> E_J 39.7 GHz, E_C 8.07 GHz above)
    # classical "kick" line: Nb coplanar strip, one large Al junction per cell to the ground (heavy fluxon)
    kick_Ic_uA=20.0, kick_jj_area_um2=12.0, kick_C_fF=600.0,   # 12 um^2 at the same Jc and C/area
    kick_strip_w_um=20.0, kick_gap_um=1.0, kick_pitch_um=10.0,  # low-inductance CPW -> Lambda from geometry below
    kick_section_cells=120,    # 1.2 mm section seen by each qubit's flux transformer
    kick_taper_cells=20,       # flared pickup ends: coupling ramps up/down over 200 um (adiabatic gate edges)
)


def cpw_l_pH_per_um(w_um, gap_um, t_nm=150.0, lambda_nm=90.0):
    """CPW inductance per length: conformal-mapping geometric part mu0/4 K(k')/K(k) + Nb strip kinetic part."""
    def K(m):                                   # complete elliptic integral of the 1st kind, modulus m (AGM)
        a, b = 1.0, math.sqrt(1 - m * m)
        for _ in range(40):
            a, b = (a + b) / 2, math.sqrt(a * b)
        return math.pi / (2 * a)
    k = w_um / (w_um + 2 * gap_um)
    geo = 4e-7 * math.pi / 4 * K(math.sqrt(1 - k * k)) / K(k) * 1e6                    # pH/um
    lk_sq = 4e-7 * math.pi * lambda_nm * 1e-9 / math.tanh(t_nm / lambda_nm) * 1e12      # pH/square
    return geo + lk_sq / w_um


QFX["kick_l_pH_per_um"] = cpw_l_pH_per_um(QFX["kick_strip_w_um"], QFX["kick_gap_um"])
QFX["kick_LJ_pH"] = 2.067833848e-15 / (2 * math.pi * QFX["kick_Ic_uA"] * 1e-6) * 1e12
QFX["kick_Lambda"] = math.sqrt(QFX["kick_LJ_pH"] / (QFX["kick_l_pH_per_um"] * QFX["kick_pitch_um"]))   # cells
QFX_STACK = [  # (layer, gds, material, true thickness nm)
    ("BASE", (1, 0), "Nb base: ground plane, feedline, resonators, drive/flux lines, kick strip, pads", 150),
    ("GRAL", (2, 0), "granular Al superinductor rail of each fluxon ring (~2 nH/sq)", 20),
    ("AL1", (3, 0), "Al bottom electrode (1st evaporation)", 30),
    ("AL2", (4, 0), "Al top electrode (2nd evaporation); AL1 AND AL2 = AlOx junction", 60),
    ("RES", (5, 0), "Cu: converter resistors and quasiparticle traps", 50),
    ("ABP", (6, 0), "Al airbridge feet", 400),
    ("ABS", (7, 0), "Al airbridge spans", 400),
]
QFX_LAUNCHER_NETS = {
    1: "VB_IN", 2: "KICK_TRIG", 3: "QF1_FLUX", 4: "QF2_FLUX", 5: "KICK_OUT", 6: "VB_OUT",
    7: "QF2_DRIVE", 8: "FEED_OUT", 9: "FEED_IN", 10: "QF1_DRIVE",
}
ACTIVE_DIE = "QFX"
