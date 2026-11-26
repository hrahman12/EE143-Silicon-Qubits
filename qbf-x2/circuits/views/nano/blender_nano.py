"""Blender (Cycles) render of one QBF-X2 rail cell at true film thickness (python3 blender_nano.py; needs bpy).
Reads nano_cell_mesh.json (render_nanoscale.py), writes nano_cell_3d_raw.png and the projected label anchors
nano_cell_3d_anchors.json; `render_nanoscale.py --annotate` adds the labels. 1 Blender unit = 1 um."""
import json
import math
import os

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "nano_cell_mesh.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

MATS = {
    "substrate": dict(color=(0.03, 0.035, 0.05), metallic=0.0, rough=0.4),
    "nb": dict(color=(0.36, 0.36, 0.41), metallic=0.85, rough=0.45),
    "gral": dict(color=(0.85, 0.48, 0.16), metallic=0.6, rough=0.45),
    "al1": dict(color=(0.38, 0.55, 1.0), metallic=0.75, rough=0.3),
    "al2": dict(color=(0.95, 0.95, 0.93), metallic=0.95, rough=0.2),
    "diel": dict(color=(0.62, 0.42, 0.95), metallic=0.0, rough=0.08, transmission=0.9, ior=2.0),
    "barrier": dict(color=(0.25, 1.0, 1.0), emission=(0.25, 1.0, 1.0), strength=25.0),
}


def material(name, spec):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*spec["color"], 1.0)
    b.inputs["Metallic"].default_value = spec.get("metallic", 0.0)
    b.inputs["Roughness"].default_value = spec.get("rough", 0.5)
    if "transmission" in spec:
        b.inputs["Transmission Weight"].default_value = spec["transmission"]
        b.inputs["IOR"].default_value = spec.get("ior", 1.45)
    if "emission" in spec:
        b.inputs["Emission Color"].default_value = (*spec["emission"], 1.0)
        b.inputs["Emission Strength"].default_value = spec["strength"]
    return m


for key, L in data["layers"].items():
    me = bpy.data.meshes.new(key)
    me.from_pydata([tuple(v) for v in L["vertices"]], [], [tuple(f) for f in L["faces"]])
    me.validate()
    me.update()
    ob = bpy.data.objects.new(key, me)
    sc.collection.objects.link(ob)
    ob.data.materials.append(material(key, MATS[key]))
    if key == "substrate":
        ob.scale = (1.0, 1.0, 1.0)

# camera: low oblique view onto the junction (the cut-away side), true scale
jx, jy, jz = data["anchors"]["junction"]
target = Vector((jx + 0.25, jy - 0.15, 0.02))
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 38
cam_data.clip_start = 0.001
cam_data.clip_end = 100
cam = bpy.data.objects.new("cam", cam_data)
sc.collection.objects.link(cam)
cam.location = target + Vector((-1.2, -1.85, 1.08))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam

# light: key sun + soft area fill + dim world
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 2.6
sun.data.angle = math.radians(6)
sun.rotation_euler = (math.radians(48), math.radians(-12), math.radians(-35))
sc.collection.objects.link(sun)
fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "AREA"))
fill.data.energy = 40.0
fill.data.size = 3.0
fill.location = (1.8, -1.5, 2.2)
fill.rotation_euler = (math.radians(50), 0, math.radians(40))
sc.collection.objects.link(fill)
world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.035, 0.04, 0.055, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
# overhead softbox: flat metal films only look like metal when they have something bright to reflect
box_ = bpy.data.objects.new("softbox", bpy.data.lights.new("softbox", "AREA"))
box_.data.energy = 85.0
box_.data.size = 9.0
box_.location = (0.4, 1.5, 4.0)
box_.rotation_euler = (math.radians(-18), 0, 0)
sc.collection.objects.link(box_)

sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 96
try:
    sc.cycles.use_denoising = True
except Exception:
    pass
sc.render.resolution_x, sc.render.resolution_y = 1800, 1150
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX" if "AgX" in [v.identifier for v in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
sc.render.filepath = os.path.join(HERE, "nano_cell_3d_raw.png")
if not os.environ.get("NANO_PROJECT_ONLY"):
    bpy.ops.render.render(write_still=True)

bpy.context.view_layer.update()                       # camera matrix also without a render
W, H = sc.render.resolution_x, sc.render.resolution_y
proj = {}
for k, p in data["anchors"].items():
    v = world_to_camera_view(sc, cam, Vector(p))
    proj[k] = [v.x * W, (1.0 - v.y) * H]
json.dump(proj, open(os.path.join(HERE, "nano_cell_3d_anchors.json"), "w"), indent=1)
print("rendered", sc.render.filepath)
