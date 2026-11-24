"""Write layer_stack.yaml and connections.json from the CAD sources (not from the renders)."""
import json
import math
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from design_params import DIE, STACKUP, PCB, PACKAGE, READOUT_F_GHZ, QUBIT_X, QUBIT_Y
from rf_calc import cpw_z0

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
model = json.load(open(os.path.join(OUT, "pcb_model.json")))
man = json.load(open(os.path.join(OUT, "layer_manifest.json")))
geo = json.load(open(os.path.join(OUT, "geometry_regions.json")))
die_ports = json.load(open(os.path.join(OUT, "die_ports.json")))

# ------------------------------------------------------------------ layer_stack.yaml
stack = dict(
    units="mm (thin films also given in nm)",
    z_reference=man["z_reference"],
    assembly_order_top_to_bottom=[],
    pcb=dict(name="rf_carrier.kicad_pcb", size_mm=[PCB["size_mm"], PCB["size_mm"]], window_mm=PCB["window_mm"],
             total_thickness_mm=round(sum(t for _, _, t, _ in STACKUP), 4), finish="ENIG (Ni 4 um / Au 0.08 um)",
             layers=[]),
    die=dict(name="quantum_die.gds", size_mm=[DIE["size_um"] / 1000] * 2, layers=[]),
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
GDS_LAYERS = {
    "die_Al_film": "KQC 130/1 base_metal_gap_wo_grid (inverted) + 131/1 base_metal_addition - 158/1 dicing",
    "jj_bottom_Al": "KQC 136/1 SIS_junction", "jj_top_Al": "KQC 139/1 SIS_junction_2",
    "jj_AlOx": "overlap 136/1 AND 139/1", "airbridges_Al": "KQC 146/1 airbridge_pads + 147/1 airbridge_flyover",
    "die_substrate": "chip box", "die_attach": "chip box",
}
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
FUNC = {
    "Q1_DRIVE": ("XY drive", "QB1", "DL_Q1_DRIVE: open-ended charge line, capacitive coupling to the QB1 island"),
    "Q2_DRIVE": ("XY drive", "QB2", "DL_Q2_DRIVE: open-ended charge line, capacitive coupling to the QB2 island"),
    "Q3_DRIVE": ("XY drive", "QB3", "DL_Q3_DRIVE: open-ended charge line, capacitive coupling to the QB3 island"),
    "Q4_DRIVE": ("XY drive", "QB4", "DL_Q4_DRIVE: open-ended charge line, capacitive coupling to the QB4 island"),
    "Q1_FLUX": ("Z flux bias", "QB1", "FL1: CPW shorted to ground next to the QB1 SQUID loop (mutual inductance)"),
    "Q2_FLUX": ("Z flux bias", "QB2", "FL2: CPW shorted to ground next to the QB2 SQUID loop"),
    "Q3_FLUX": ("Z flux bias", "QB3", "FL3: CPW shorted to ground next to the QB3 SQUID loop"),
    "Q4_FLUX": ("Z flux bias", "QB4", "FL4: CPW shorted to ground next to the QB4 SQUID loop"),
    "PROBE_IN": ("readout probe line in", "QB1-QB4",
                 "PL_IN -> tees PLT1..4 -> interdigital caps RRC1..4 -> lambda/2 resonators RR1..4 -> QBn readout couplers"),
    "PROBE_OUT": ("readout probe line out", "QB1-QB4", "PL_OUT: same continuous probe-line conductor as PROBE_IN"),
}
z0_die = cpw_z0(DIE["cpw_a"], DIE["cpw_b"], DIE["substrate_eps_r"])[0]


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
    path.append(dict(stage="die_launcher_pad", kqc_port_id=p["kqc_port_id"], side=p["side"],
                     center_um=p["pad_center_um"], size_um=p["pad_size_um"], metal="Al 200 nm"))
    path.append(dict(stage="die_cpw", centre_um=DIE["cpw_a"], gap_um=DIE["cpw_b"], z0_ohm=round(float(z0_die), 1),
                     structure=die_desc))
    path.append(dict(stage="quantum_device", target=qb,
                     qubit_positions_um={f"QB{i+1}": [QUBIT_X[i], QUBIT_Y] for i in range(4)} if qb == "QB1-QB4" else
                     [QUBIT_X[int(qb[-1]) - 1], QUBIT_Y]))
    entry = dict(net=net, function=func, path=path)
    if net.startswith("PROBE"):
        entry["readout_resonators"] = [dict(name=f"RR{i+1}", f_design_GHz=f, qubit=f"QB{i+1}") for i, f in
                                       enumerate(READOUT_F_GHZ)]
    conns["signal_nets"].append(entry)
gb = [b for b in geo["bonds"] if b["kind"] == "ground"]
conns["ground"] = dict(
    die_ground_plane="largest Al island (ground plane) - flux lines terminate into it at each SQUID",
    ground_wire_bonds=len(gb), ground_bonds_per_side={s: sum(1 for b in gb if b["side"] == s) for s in "NESW"},
    pcb_ground_ring="exposed ENIG ring around the die window, F.Cu GND",
    stitching_vias=sum(1 for v in model["vias"] if v["net"] == "GND"),
    planes=["F.Cu pour", "In1.Cu plane", "In2.Cu coplanar pour", "In3.Cu plane", "In4.Cu plane", "B.Cu pour"],
    package_return="B.Cu pour contacts the gold-plated base; M2.5 screws through plated mounting holes",
)
json.dump(conns, open(os.path.join(OUT, "connections.json"), "w"), indent=1)
print("wrote layer_stack.yaml and connections.json")
