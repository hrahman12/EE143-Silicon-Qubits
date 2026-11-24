"""Blender (Cycles) assembly + renders.

    blender -b -P src/render_blender.py -- [--quick] [--only name1,name2]

Imports out/assembly.glb (one object per physical layer), assigns physically based materials,
builds the scene, saves out/quantum_assembly.blend and renders the views into renders/.
"""
import json
import math
import re
import os
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
QUICK = "--quick" in ARGS
ONLY = None
if "--only" in ARGS:
    ONLY = ARGS[ARGS.index("--only") + 1].split(",")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from design_params import ACTIVE_DIE  # noqa: E402
OUT = os.path.join(HERE, "..", "out")
REN = os.path.join(HERE, "..", "renders")
os.makedirs(REN, exist_ok=True)
man = json.load(open(os.path.join(OUT, "layer_manifest.json")))
LAY = {L["name"]: L for L in man["layers"]}
ZD = man["z_die_top"]

# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, "assembly.glb"))
# 1 Blender unit = 1 mm (set after import so the importer does not rescale)
sc.unit_settings.system = "METRIC"
sc.unit_settings.scale_length = 0.001
sc.unit_settings.length_unit = "MILLIMETERS"
objs = {}
for o in list(sc.objects):
    if o.type == "MESH":
        name = re.sub(r"\.\d{3}$", "", o.name)
        objs[name] = o
        o["layer"] = name
        o.data.name = name
        for p in o.data.polygons:
            p.use_smooth = False
# smooth shading only for round things
for n in ("wirebonds_signal", "wirebonds_ground", "sma_connectors", "connector_pins", "smp_connectors",
          "solder_joints", "screws", "connector_ptfe"):
    if n in objs:
        for p in objs[n].data.polygons:
            p.use_smooth = True
        mod = objs[n].modifiers.new("ws", "WEIGHTED_NORMAL") if hasattr(bpy.types, "WeightedNormalModifier") else None

print("DIMS", {n: tuple(round(x, 3) for x in objs[n].dimensions) for n in ("F.Cu", "die_substrate") if n in objs})
# collections per group
for L in man["layers"]:
    g = L["group"]
    col = bpy.data.collections.get(g) or bpy.data.collections.new(g)
    if col.name not in sc.collection.children:
        sc.collection.children.link(col)
    o = objs.get(L["name"])
    if o:
        for c in o.users_collection:
            c.objects.unlink(o)
        col.objects.link(o)
        o["explode_mm"] = L["explode"]
        o["true_thickness_mm"] = L["true_thickness_mm"]
        o["z_range_mm"] = L["z"]


# ------------------------------------------------------------------ materials
def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def principled(name, color, metallic=0.0, rough=0.5, coat=0.0, trans=0.0, ior=1.45, alpha=1.0, emission=None,
               aniso=0.0, sss=0.0):
    m, N, Lk = node_mat(name)
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = ior
    for k in ("Coat Weight", "Clearcoat"):
        if k in b.inputs:
            b.inputs[k].default_value = coat
    for k in ("Transmission Weight", "Transmission"):
        if k in b.inputs:
            b.inputs[k].default_value = trans
    if "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = aniso
    b.inputs["Alpha"].default_value = alpha
    if emission is not None:
        for k in ("Emission Color", "Emission"):
            if k in b.inputs:
                b.inputs[k].default_value = (*emission, 1)
        if "Emission Strength" in b.inputs:
            b.inputs["Emission Strength"].default_value = 0.6
    if alpha < 1:
        try:
            m.blend_method = "BLEND"
        except Exception:
            pass
    return m


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


REAL = {
    "copper": principled("Cu", (0.955, 0.638, 0.538), 1.0, 0.28),
    "gold": principled("Au_ENIG", (1.0, 0.766, 0.336), 1.0, 0.22),
    "soldermask_red": principled("Mask_red", srgb("#3c0407"), 0.0, 0.35, coat=0.25),
    "soldermask_red_over_cu": principled("Mask_red_over_Cu", srgb("#a3141a"), 0.25, 0.28, coat=0.25),
    "rogers_ro4003c": principled("RO4003C", srgb("#d9cfb6"), 0.0, 0.7),
    "rogers_ro4450f": principled("RO4450F", srgb("#cfc3a6"), 0.0, 0.75),
    "silkscreen": principled("Silk", (0.9, 0.9, 0.88), 0.0, 0.6),
    "silicon": principled("Si", srgb("#1a1e27"), 0.35, 0.07, coat=0.4),
    "aluminium": principled("Al_film", (0.913, 0.922, 0.924), 1.0, 0.16),
    "alox": principled("AlOx", (0.8, 0.85, 1.0), 0.0, 0.1, trans=0.6, ior=1.7),
    "aluminium_wire": principled("Al_wire", (0.80, 0.81, 0.82), 1.0, 0.38),
    "ge_varnish": principled("GE7031", srgb("#a8651e"), 0.0, 0.35, coat=0.5),
    "stainless": principled("SS303", (0.66, 0.65, 0.62), 1.0, 0.24, aniso=0.4),
    "ptfe": principled("PTFE", (0.92, 0.92, 0.9), 0.0, 0.5, sss=0.3),
    "solder": principled("SAC305", (0.82, 0.83, 0.84), 1.0, 0.18),
    "gold_plated_copper": principled("Au_on_OFHC", (1.0, 0.78, 0.40), 1.0, 0.32),
    "niobium": principled("Nb", (0.62, 0.63, 0.68), 1.0, 0.22),
    "niobium_jj": principled("Nb_JJ", (0.72, 0.62, 0.78), 1.0, 0.18),
    "sio2": principled("SiO2_ILD", (0.85, 0.9, 0.95), 0.0, 0.05, trans=0.97, ior=1.46),
    "molybdenum": principled("Mo_R", (0.55, 0.55, 0.58), 1.0, 0.3),
    "gral": principled("grAl", (0.78, 0.72, 0.62), 0.85, 0.32),
    "alox_jj": principled("AlOx_junction", (0.55, 0.45, 0.85), 0.6, 0.2),
    "copper_film": principled("Cu_film", (0.955, 0.638, 0.538), 1.0, 0.3),
}
ENGM = {}


def eng_mat(L):
    key = (L["eng_color"], L["eng_opacity"])
    if key not in ENGM:
        a = L["eng_opacity"] if L["group"] != "pcb" or L["eng_opacity"] > 0.3 else 0.08
        ENGM[key] = principled(f"ENG_{L['eng_color']}_{a}", srgb(L["eng_color"]), 0.0, 0.45, alpha=a,
                               emission=srgb(L["eng_color"]) if L["group"] in ("pcb", "vias") and a == 1 else None)
    return ENGM[key]


def apply_mode(mode):
    for n, o in objs.items():
        L = LAY.get(n)
        if not L:
            continue
        mat = REAL[L["material"]] if mode == "real" else eng_mat(L)
        o.data.materials.clear()
        o.data.materials.append(mat)


# ------------------------------------------------------------------ world + lights
world = bpy.data.worlds.new("studio")
sc.world = world
world.use_nodes = True
wn = world.node_tree.nodes
bg = wn["Background"]
grad = wn.new("ShaderNodeTexGradient")
coord = wn.new("ShaderNodeTexCoord")
ramp = wn.new("ShaderNodeValToRGB")
mapn = wn.new("ShaderNodeMapping")
mapn.inputs["Rotation"].default_value = (0, math.radians(90), 0)
world.node_tree.links.new(coord.outputs["Generated"], mapn.inputs["Vector"])
world.node_tree.links.new(mapn.outputs["Vector"], grad.inputs["Vector"])
world.node_tree.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
world.node_tree.links.new(ramp.outputs["Color"], bg.inputs["Color"])
ramp.color_ramp.elements[0].color = (0.02, 0.022, 0.028, 1)
ramp.color_ramp.elements[1].color = (0.30, 0.32, 0.36, 1)
bg.inputs["Strength"].default_value = 0.9


def area(name, loc, size, energy, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA")
    l.size = size
    l.energy = energy
    l.color = color
    o = bpy.data.objects.new(name, l)
    sc.collection.objects.link(o)
    o.location = loc
    d = Vector((0, 0, 1.5)) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


area("key", (-60, -70, 110), 70, 2.6e5)
area("fill", (90, -30, 60), 60, 0.9e5, (0.9, 0.95, 1.0))
area("rim", (10, 110, 70), 50, 1.4e5, (1.0, 0.95, 0.9))
area("top", (0, 0, 150), 90, 0.8e5)

# ground plane (seamless lab-bench backdrop)
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, man["z_base"][0] - 0.01))
floor = bpy.context.active_object
floor.name = "bench"
floor.data.materials.append(principled("bench", (0.035, 0.037, 0.042), 0.0, 0.55))

# ------------------------------------------------------------------ cameras
cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
cam_data.clip_start = 0.002
cam_data.clip_end = 2000


def look(loc, target, lens=50, ortho=None, dof=None, fstop=4.0):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho
    else:
        cam_data.type = "PERSP"
        cam_data.lens = lens
    cam_data.dof.use_dof = dof is not None
    if dof is not None:
        cam_data.dof.focus_distance = dof
        cam_data.dof.aperture_fstop = fstop


# ------------------------------------------------------------------ render settings
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 24 if QUICK else 64
sc.cycles.use_denoising = True
try:
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
sc.cycles.max_bounces = 8
sc.cycles.transparent_max_bounces = 128
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.render.resolution_x = 960 if QUICK else 1920
sc.render.resolution_y = 600 if QUICK else 1200
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in
                                                      bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
try:
    sc.view_settings.look = "AgX - Medium High Contrast" if sc.view_settings.view_transform == "AgX" else "Medium High Contrast"
except Exception:
    pass


def show_all():
    for o in objs.values():
        o.hide_render = False
        o.hide_viewport = False
        o.location = (0, 0, 0)


def hide(*names):
    for n in names:
        if n in objs:
            objs[n].hide_render = True


def explode(f):
    for n, o in objs.items():
        o.location = (0, 0, LAY[n]["explode"] * f if n in LAY else 0)


def cutaway(names, x_lt=None, y_gt=None, x_gt=None, y_lt=None):
    """Remove the part of the listed objects inside the box {x<x_lt, y>y_gt, ...} by switching their
    (per-object copied) material to transparent there. Geometry is untouched."""
    for n in names:
        o = objs.get(n)
        if o is None or not o.data.materials:
            continue
        m = o.data.materials[0].copy()
        m.name = f"{m.name}_cut_{n}"
        o.data.materials[0] = m
        N, Lk = m.node_tree.nodes, m.node_tree.links
        out = N.get("Material Output")
        src = out.inputs["Surface"].links[0].from_socket
        sep = N.new("ShaderNodeSeparateXYZ")
        Lk.new(N.new("ShaderNodeNewGeometry").outputs["Position"], sep.inputs["Vector"])
        acc = None
        for axis, op, val in (("X", "LESS_THAN", x_lt), ("Y", "GREATER_THAN", y_gt), ("X", "GREATER_THAN", x_gt),
                              ("Y", "LESS_THAN", y_lt)):
            if val is None:
                continue
            c = N.new("ShaderNodeMath")
            c.operation = op
            c.inputs[1].default_value = val
            Lk.new(sep.outputs[axis], c.inputs[0])
            if acc is None:
                acc = c
            else:
                mn = N.new("ShaderNodeMath")
                mn.operation = "MINIMUM"
                Lk.new(acc.outputs[0], mn.inputs[0])
                Lk.new(c.outputs[0], mn.inputs[1])
                acc = mn
        mix = N.new("ShaderNodeMixShader")
        Lk.new(acc.outputs[0], mix.inputs["Fac"])
        Lk.new(src, mix.inputs[1])
        Lk.new(N.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[2])
        Lk.new(mix.outputs[0], out.inputs["Surface"])


def render(name):
    if ONLY and name not in ONLY:
        return
    sc.render.filepath = os.path.join(REN, name + ".png")
    print("RENDER", name)
    bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------ shots
apply_mode("real")
show_all()
# 1. assembled hardware, hero 3/4 view
look((-44, -62, 50), (0, 0, 0.0), lens=50, dof=math.dist((-44, -62, 50), (0, 0, 1)), fstop=11)
render("assembled_chip")

# 2. angled PCB view, low raking light across the red mask
look((30, -36, 16), (-1, 2, 0.5), lens=70, dof=math.dist((30, -36, 16), (0, 0, 1)), fstop=5.6)
render("red_pcb_view")

# 3. exploded layer stack
explode(2.2)
hide("screws")
look((-80, -102, 68), (0, 0, 7.0), lens=58)
render("exploded_layers")
show_all()

# 4. stepped cutaway: everything above In2 peeled back in the NW quadrant (reveals the In2 flux
#    striplines running under the top-layer GCPW lines), In3 and below peeled further out.
above = ["F.Silk", "F.Mask", "F.Mask_over_Cu", "F.ENIG", "F.Cu_GND", "F.Cu_RF", "diel1", "In1.Cu_GND", "diel2"]
below = ["diel3", "In3.Cu_GND", "diel4", "In4.Cu_GND", "diel5", "B.Cu_GND", "B.Cu_RF", "B.Mask", "B.Mask_over_Cu",
         "B.ENIG", "B.Silk", "package_base", "vias_through", "vias_blind_top", "vias_blind_bottom", "solder_joints"]
cutaway(above, x_lt=-2.0, y_gt=-14.0)
cutaway(["In2.Cu_GND"], x_lt=-12.5, y_gt=-14.0)
cutaway(below, x_lt=-12.5, y_gt=-14.0)
hide("screws", "sma_connectors", "connector_pins", "connector_ptfe")
look((-40, 22, 26), (-7, -1, 0.5), lens=50)
render("internal_trace_cutaway")
show_all()
apply_mode("real")

# 5. macro close-up of the die's active element
if ACTIVE_DIE == "QFX":
    # quantum fluxon ring QF1 (24 Al/AlOx/Al rungs on grAl rails, barrier SQUID, flux-transformer and
    # bus landings). QF1 centre = die (4800, 5200) um -> board (-0.2, 0.2) mm.
    QF1 = (-0.2, 0.2, ZD)
    CAM5 = (-0.2 + 0.16, 0.2 - 0.30, ZD + 0.30)
    look(CAM5, QF1, lens=100, dof=math.dist(CAM5, QF1), fstop=11)
    render("quantum_fluxon_macro")
else:
    # RFL rotary element at board (0, 1.4)
    look((0.55, 0.55, ZD + 0.55), (0.0, 1.4, ZD), lens=100, dof=math.dist((0.55, 0.55, ZD + 0.55), (0.0, 1.4, ZD)), fstop=16)
    render("fluxon_gate_macro")

# 6. bond pads + wire bonds (north edge of die, Q2 drive / flux pads)
look((-1.5, 7.9, ZD + 1.7), (-1.2, 4.95, ZD + 0.05), lens=85,
     dof=math.dist((-1.5, 7.9, ZD + 1.7), (-1.2, 4.95, ZD)), fstop=8)
render("wirebond_macro")

# 7. technical CAD view, engineering colours (red top / green stripline / blue bottom)
apply_mode("eng")
hide("F.Mask", "F.Mask_over_Cu", "B.Mask", "B.Mask_over_Cu", "F.Silk", "B.Silk", "screws", "package_base",
     "F.ENIG", "B.ENIG", "In1.Cu_GND", "In3.Cu_GND", "In4.Cu_GND", "die_attach", "die_ILD0_SiO2", "die_ILD1_SiO2")
explode(0.8)
floor.hide_render = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
look((-26, -40, 52), (0, 0, 0), lens=50)
render("technical_cad_view")
floor.hide_render = False
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
show_all()
apply_mode("real")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "quantum_assembly.blend"), compress=True)
print("saved blend")
