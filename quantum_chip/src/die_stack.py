"""Per-die 3D layer description shared by build_geometry.py, build_step.py, build_reports.py, render and viewer.

Each entry: object name, GDS layer key, material key (render), engineering colour, visual z-range above the
substrate surface (um, exaggerated so thin films are visible), true z-range (nm, used by the STEP), note.
Derived bodies: 'JJ' = AL1 AND AL2 (the tunnel junctions), sheets are drawn as full-die slabs.
"""
from design_params import ACTIVE_DIE, RFL_STACK, QFX_STACK

RFL = [
    ("die_GP_Nb", "GP", "niobium", "#8b93a6", (0.0, 3.0), (0, 200), "Nb ground plane M0"),
    ("die_ILD0_SiO2", "SHEET", "sio2", "#cfe8ff", (3.0, 5.0), (200, 400), "SiO2 ILD"),
    ("die_M1_Nb_LJJ", "M1", "niobium", "#2f6bff", (5.0, 7.5), (400, 550), "Nb M1: LJJ strips, JJ base electrode"),
    ("die_JJ_trilayer", "JJ", "niobium_jj", "#ff2aff", (7.5, 9.0), (550, 650), "AlOx barrier + Nb counter-electrode"),
    ("die_ILD1_SiO2", "SHEET", "sio2", "#cfe8ff", (7.5, 9.5), (550, 750), "SiO2 ILD"),
    ("die_R_Mo", "R", "molybdenum", "#22c060", (9.5, 10.5), (750, 790), "Mo resistor"),
    ("die_M2_Nb", "M2", "niobium", "#ff3b3b", (9.5, 13.5), (750, 1050), "Nb M2 wiring, pads, JJ straps"),
    ("die_pad_Au", "PAD", "gold", "#ffd34d", (13.5, 15.0), (1050, 1150), "Ti/Au bond metallisation"),
    ("die_vias_Nb", "VIA", "niobium", "#ffe600", (3.0, 9.5), (200, 750), "stacked Nb vias"),
]
QFX = [
    ("die_base_Nb", "BASE", "niobium", "#8b93a6", (0.0, 3.0), (0, 150),
     "Nb 150 nm: ground plane, feedline, resonators, lines, kick strip, pads"),
    ("die_grAl_rails", "GRAL", "gral", "#ff8c1a", (0.0, 1.5), (0, 20), "granular Al 20 nm superinductor rails"),
    ("die_Al_bottom", "AL1", "aluminium", "#2f6bff", (0.0, 1.5), (0, 30), "Al 30 nm bottom electrodes / leads"),
    ("die_junctions_AlOx", "JJ", "alox_jj", "#ff2aff", (1.5, 2.1), (30, 32), "AlOx tunnel junctions (AL1 AND AL2)"),
    ("die_Al_top", "AL2", "aluminium", "#9fd8ff", (2.1, 4.1), (32, 92), "Al 60 nm top electrodes"),
    ("die_Cu_res_traps", "RES", "copper_film", "#b8572a", (0.0, 1.5), (0, 50), "Cu resistors + quasiparticle traps"),
    ("die_airbridge_feet", "ABP", "aluminium", "#22c060", (3.0, 6.0), (150, 3150), "Al airbridge feet (3 um posts)"),
    ("die_airbridge_spans", "ABS", "aluminium", "#e03030", (6.0, 7.2), (3150, 3550), "Al airbridge spans"),
]
STACK = {"RFL": RFL, "QFX": QFX}[ACTIVE_DIE]
GDS = {name: gds for name, gds, _, _ in (RFL_STACK if ACTIVE_DIE == "RFL" else QFX_STACK)}
EXPLODE = {name: 10.0 + 0.6 * i for i, (name, *_rest) in enumerate(STACK)}
TOP_UM = max(z[1] for *_a, z, _t, _n in STACK)        # visual top of the die stack (um)
