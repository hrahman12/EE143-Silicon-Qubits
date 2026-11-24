"""Write layer_stack.yaml and connections.json from the CAD sources (not from the renders)."""
import json
import math
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from design_params import DIE, STACKUP, PCB, PACKAGE, READOUT_F_GHZ, QUBIT_X, QUBIT_Y, ACTIVE_DIE
from rf_calc import cpw_z0

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
model = json.load(open(os.path.join(OUT, "pcb_model.json")))
man = json.load(open(os.path.join(OUT, "layer_manifest.json")))
geo = json.load(open(os.path.join(OUT, "geometry_regions.json")))
die_ports = json.load(open(os.path.join(OUT, "die_ports.json")))
cells = json.load(open(os.path.join(OUT, "die_cells.json")))

# ------------------------------------------------------------------ layer_stack.yaml
stack = dict(
    units="mm (thin films also given in nm)",
    z_reference=man["z_reference"],
    assembly_order_top_to_bottom=[],
    pcb=dict(name="rf_carrier.kicad_pcb", size_mm=[PCB["size_mm"], PCB["size_mm"]], window_mm=PCB["window_mm"],
             total_thickness_mm=round(sum(t for _, _, t, _ in STACKUP), 4), finish="ENIG (Ni 4 um / Au 0.08 um)",
             layers=[]),
    die=dict(name="quantum_die.gds (cell " + ("RFL_RE1" if ACTIVE_DIE == "RFL" else "QFX1") + ")", size_mm=[DIE["size_um"] / 1000] * 2, layers=[]),
    package=dict(base=PACKAGE["base_material"], base_thickness_mm=PACKAGE["base_thickness_mm"],
                 die_attach=PACKAGE["die_attach"], wirebond=PACKAGE["wirebond"],
                 wire_diameter_um=PACKAGE["wire_d_um"], loop_height_um=PACKAGE["loop_height_um"]),
    visual_exaggeration_note=("Films thinner than 3 um are drawn thicker in the 3D model so they are visible; "
                              "true_thickness is the fabrication value, visual_thickness the mesh value. "
                              "XY geometry is never altered."),
)
Z = man["Z"]
for name, kind, t, desc in STACKUP:
    stack["pcb"]["layers"].append(dict(name=name, kind=kind, thickness_mm=t, z_mm=[round(v, 4) for v in Z[name]],
                                       material=desc))
GDS_LAYERS_QFX = {"die_base_Nb": "1/0 BASE", "die_grAl_rails": "2/0 GRAL", "die_Al_bottom": "3/0 AL1",
                  "die_junctions_AlOx": "3/0 AND 4/0", "die_Al_top": "4/0 AL2", "die_Cu_res_traps": "5/0 RES",
                  "die_airbridge_feet": "6/0 ABP", "die_airbridge_spans": "7/0 ABS", "die_substrate": "chip box",
                  "die_attach": "chip box"}
GDS_LAYERS = {"die_GP_Nb": "1/0 GP", "die_ILD0_SiO2": "sheet (not drawn)", "die_M1_Nb_LJJ": "3/0 M1",
              "die_JJ_trilayer": "4/0 JJ", "die_ILD1_SiO2": "sheet (5/0 = contacts)", "die_R_Mo": "6/0 R",
              "die_M2_Nb": "7/0 M2", "die_pad_Au": "8/0 PAD", "die_vias_Nb": "9/0 VIA + 5/0 I1",
              "die_substrate": "chip box", "die_attach": "chip box"}
stack["die"]["process"] = ("Nb/AlOx/Nb trilayer, GP + 2 wiring layers (SFQ5ee-like, simplified)" if ACTIVE_DIE == "RFL"
                           else "Nb base + granular-Al superinductors + Al/AlOx/Al double-angle junctions + Cu + Al airbridges")
stack["die"]["junctions"] = cells["total_jj"]
if ACTIVE_DIE == "QFX":
    GDS_LAYERS = GDS_LAYERS_QFX
for L in man["layers"]:
    if L["group"] == "die":
        stack["die"]["layers"].append(dict(name=L["name"], source=GDS_LAYERS.get(L["name"], ""), material=L["note"],
                                           true_thickness_mm=L["true_thickness_mm"],
                                           true_thickness_nm=round(L["true_thickness_mm"] * 1e6, 2),
                                           visual_thickness_mm=L["visual_thickness_mm"], z_mm=L["z"]))
for L in sorted(man["layers"], key=lambda L: -L["z"][1]):
    stack["assembly_order_top_to_bottom"].append(f'{L["name"]}  z=[{L["z"][0]:.4f}, {L["z"][1]:.4f}]  ({L["group"]})')
yaml.safe_dump(stack, open(os.path.join(OUT, "layer_stack.yaml"), "w"), sort_keys=False, width=120)

# ------------------------------------------------------------------ connections.json
from design_params import ACTIVE_DIE
FUNC_QFX = {
    "FEED_IN": ("readout feedline in", "RES1, RES2", "Nb CPW feedline -> lambda/4 resonators RES1 (7.0 GHz), RES2 (7.4 GHz)"),
    "FEED_OUT": ("readout feedline out", "RES1, RES2", "same continuous feedline"),
    "QF1_DRIVE": ("fast tilt / microwave drive", "QF1", "Nb CPW shorted onto the QF1 rim on link 10->11 (next to well A)"),
    "QF2_DRIVE": ("fast tilt / microwave drive", "QF2", "Nb CPW shorted onto the QF2 rim on link 10->11"),
    "QF1_FLUX": ("dc flux: fluxon trapping + barrier SQUID bias", "QF1", "Nb line (airbridge over the kick line) shorted "
                 "onto the QF1 rim on link 16->17"),
    "QF2_FLUX": ("dc flux: fluxon trapping + barrier SQUID bias", "QF2", "same for QF2"),
    "KICK_TRIG": ("heavy-fluxon trigger", "KICK line", "DC/SFQ launcher -> 7.8 mm ballistic line of 392 Al junctions"),
    "KICK_OUT": ("heavy-fluxon arrival", "KICK line", "SFQ/DC receiver at the far end of the kick line"),
    "VB_IN": ("dc bias, launcher", "DCSFQ_IN", "Nb line -> Cu bias resistor"),
    "VB_OUT": ("dc bias, receiver", "SFQDC_OUT", "Nb line -> Cu bias resistor"),
}
FUNC = {
    "TRIG_A": ("fluxon trigger A", "RE input I0 via controlled barrier",
               "M2 microstrip -> DCSFQ_A (2 JJ) -> LJJ_A -> controlled barrier CB -> LJJ_A2 -> rotary element port I0"),
    "TRIG_B": ("fluxon trigger B", "RE input I1", "M2 microstrip -> DCSFQ_B -> LJJ_B -> rotary element port I1"),
    "OUT_0": ("fluxon output 0", "RE output O0", "RE port O0 -> LJJ_O0 -> SFQDC_0 (3 JJ) -> M2 microstrip -> pad"),
    "OUT_1": ("fluxon output 1", "RE output O1", "RE port O1 -> LJJ_O1 -> SFQDC_1 -> M2 microstrip -> pad"),
    "TEST_IN": ("racetrack input", "LJJ_TEST", "M2 microstrip -> DCSFQ_T -> 18 mm ballistic LJJ racetrack"),
    "TEST_OUT": ("racetrack output", "LJJ_TEST", "LJJ_TEST -> SFQDC_T -> M2 microstrip -> pad"),
    "CTRL_CB": ("barrier control flux", "CB SQUID", "M2 line shorted to GP beside the CB SQUID loop (sets Ic_eff)"),
    "CTRL_RE": ("rotary-element state flux", "RE storage loop", "M2 line shorted to GP inside the RE ring (set/reset)"),
    "VB_W": ("DC bias, west converters", "DCSFQ_A, SFQDC_0, DCSFQ_T", "M2 bias tree -> Mo bias resistors"),
    "VB_E": ("DC bias, east converters", "DCSFQ_B, SFQDC_1, SFQDC_T", "M2 bias tree -> Mo bias resistors"),
}


if ACTIVE_DIE == "QFX":
    FUNC = FUNC_QFX


def plen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:]))


conns = dict(
    description="Every electrical path from RF connector to quantum device. Coordinates: mm, board frame, Y up, "
                "origin = board centre = die centre. Die coordinates also given in um in the GDS frame (0..10000).",
    signal_nets=[], ground=dict())
for p in die_ports["ports"]:
    net = p["net"]
    func, qb, die_desc = FUNC[net]
    path = []
    fp = [f for f in model["footprints"] if f["net"] == net][0]
    cpads = [q for q in model["pads"] if q.get("fp") == fp["ref"] and q["net"] == net][0]
    path.append(dict(stage="rf_connector", ref=fp["ref"],
                     type="end-launch SMA (top side)" if fp["kind"] == "SMA_EDGE" else "vertical SMP (bottom side)",
                     at_mm=[round(fp["x"], 4), round(fp["y"], 4)], signal_pad_layer=cpads["layer"],
                     solder_joint=True))
    tr = [t for t in model["tracks"] if t["net"] == net]
    vs = [v for v in model["vias"] if v["net"] == net]
    # order: connector-side layer first
    layer_order = ["F.Cu"] if fp["kind"] == "SMA_EDGE" else ["B.Cu", "In2.Cu", "F.Cu"]
    for lay in layer_order:
        for t in tr:
            if t["layer"] != lay:
                continue
            zt = {"F.Cu": model["z0"]["gcpw_top"], "B.Cu": model["z0"]["gcpw_bottom"], "In2.Cu": model["z0"]["stripline"]}[lay]
            path.append(dict(stage="pcb_trace", layer=lay,
                             geometry="grounded CPW" if lay != "In2.Cu" else "symmetric stripline (In1/In3 GND)",
                             width_mm=t["w"], gap_mm=model["gap"] if lay != "In2.Cu" else model["stripline_clearance"],
                             z0_ohm=round(float(zt), 2), length_mm=round(plen(t["pts"]), 3),
                             points_mm=[[round(a, 4), round(b, 4)] for a, b in t["pts"]]))
        for v in vs:
            if (lay == "B.Cu" and v["layers"] == ["In2.Cu", "B.Cu"]) or (lay == "In2.Cu" and v["layers"] == ["F.Cu", "In2.Cu"]):
                path.append(dict(stage="via", kind="blind", layers=v["layers"], drill_mm=v["drill"], pad_mm=v["size"],
                                 at_mm=[round(v["x"], 4), round(v["y"], 4)]))
    bd = model["bond"][net]
    path.append(dict(stage="pcb_bond_pad", layer="F.Cu + ENIG", center_mm=[round(c, 4) for c in bd["center"]],
                     size_mm=[q["size"] for q in model["pads"] if q.get("role") == "bond_pad" and q["net"] == net][0]))
    wb = [b for b in geo["bonds"] if b["net"] == net]
    path.append(dict(stage="wire_bonds", count=len(wb), material=PACKAGE["wirebond"],
                     lengths_mm=[b["length_mm"] for b in wb]))
    path.append(dict(stage="die_bond_pad", pad_index=p["kqc_port_id"], side=p["side"],
                     center_um=p["pad_center_um"], size_um=p["pad_size_um"], metal="Nb M2 300 nm + Ti/Au 100 nm"))
    path.append(dict(stage="die_wiring", structure=die_desc))
    path.append(dict(stage="fluxon_device", target=qb))
    entry = dict(net=net, function=func, path=path)
    conns["signal_nets"].append(entry)
gb = [b for b in geo["bonds"] if b["kind"] == "ground"]
conns["ground"] = dict(
    die_ground_plane=("Nb GP (M0) under the whole circuit; M2+Au bond ring stitched to it by a via fence; "
                      "every LJJ junction returns to GP through its own stacked via") if ACTIVE_DIE == "RFL" else
                     "Nb base-layer ground plane; each qubit sits in a 100 um hole whose rim is one rail of the fluxon ring",
    ground_wire_bonds=len(gb), ground_bonds_per_side={s: sum(1 for b in gb if b["side"] == s) for s in "NESW"},
    pcb_ground_ring="exposed ENIG ring around the die window, F.Cu GND",
    stitching_vias=sum(1 for v in model["vias"] if v["net"] == "GND"),
    planes=["F.Cu pour", "In1.Cu plane", "In2.Cu coplanar pour", "In3.Cu plane", "In4.Cu plane", "B.Cu pour"],
    package_return="B.Cu pour contacts the gold-plated base; M2.5 screws through plated mounting holes",
)
json.dump(conns, open(os.path.join(OUT, "connections.json"), "w"), indent=1)
print("wrote layer_stack.yaml and connections.json")
