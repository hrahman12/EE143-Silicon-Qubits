#!/usr/bin/env python3
"""3D renders of the assembled carrier for the README (Blender Cycles on the CPU, 2 threads).

Geometry: fab/qbfx2_carrier.step, i.e. KiCad's own STEP export (board body + the OCP component models referenced by the
footprints), tessellated with OpenCascade. The board top / bottom faces get textures built from the KiCad layer plots
(make_outputs.py textures()), so copper, mask openings and silkscreen appear as fabricated.
Outputs: fab/previews/render_3d_top.png, fab/previews/render_3d_die_closeup.png
"""
import math
import os
import sys
import time

import numpy as np
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.Quantity import Quantity_Color
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDF import TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TDocStd import TDocStd_Document
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS
from OCP.XCAFDoc import XCAFDoc_ColorGen, XCAFDoc_ColorSurf, XCAFDoc_ColorTool, XCAFDoc_DocumentTool
from OCP.collections import Sequence_TDF_Label as Seq

HERE = os.path.dirname(os.path.abspath(__file__))
STEP = os.path.join(HERE, "fab", "qbfx2_carrier.step")
PREV = os.path.join(HERE, "fab", "previews")
THREADS = 2


# ------------------------------------------------------------------------------------------------ STEP -> triangles
def load_parts():
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    r = STEPCAFControl_Reader()
    r.SetColorMode(True)
    r.SetNameMode(True)
    r.ReadFile(STEP)
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def name(l):
        n = TDataStd_Name()
        return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), n) else ""

    def colour(l):
        c = Quantity_Color()
        for t in (XCAFDoc_ColorSurf, XCAFDoc_ColorGen):
            if XCAFDoc_ColorTool.GetColor_s(l, t, c):
                return (c.Red(), c.Green(), c.Blue())
        sub = Seq()
        st.GetSubShapes_s(l, sub)
        for i in range(1, sub.Length() + 1):
            for t in (XCAFDoc_ColorSurf, XCAFDoc_ColorGen):
                if XCAFDoc_ColorTool.GetColor_s(sub.Value(i), t, c):
                    return (c.Red(), c.Green(), c.Blue())
        return None

    parts = []

    def walk(l, loc, owner):
        if st.IsAssembly_s(l):
            comps = Seq()
            st.GetComponents_s(l, comps)
            for i in range(1, comps.Length() + 1):
                c = comps.Value(i)
                ref = TDF_Label()
                st.GetReferredShape_s(c, ref)
                walk(ref, loc.Multiplied(st.GetLocation_s(c)), owner or name(c))
        else:
            shp = st.GetShape_s(l).Moved(loc)
            parts.append(dict(name=name(l), owner=owner, colour=colour(l), shape=shp))

    free = Seq()
    st.GetFreeShapes(free)
    for i in range(1, free.Length() + 1):
        walk(free.Value(i), TopLoc_Location(), "")
    return parts


def triangles(shape, defl=0.02):
    BRepMesh_IncrementalMesh(shape, defl, False, 0.35, True)
    V, F = [], []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            tr = loc.Transformation()
            base = len(V)
            for i in range(1, tri.NbNodes() + 1):
                p = tri.Node(i).Transformed(tr)
                V.append((p.X(), p.Y(), p.Z()))
            rev = face.Orientation() == TopAbs_REVERSED
            for i in range(1, tri.NbTriangles() + 1):
                a, b, c = tri.Triangle(i).Get()
                F.append((base + a - 1, base + c - 1, base + b - 1) if rev else (base + a - 1, base + b - 1, base + c - 1))
        exp.Next()
    return np.array(V, float), np.array(F, int)


# ------------------------------------------------------------------------------------------------ Blender
def main():
    import bpy
    t0 = time.time()
    parts = load_parts()
    print("STEP parts:", len(parts))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.93, 0.95, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.55

    mats = {}

    def mat(key, rgb, metal=0.0, rough=0.5, spec=0.5):
        if key in mats:
            return mats[key]
        m = bpy.data.materials.new(key)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Metallic"].default_value = metal
        b.inputs["Roughness"].default_value = rough
        mats[key] = m
        return m

    def board_mat(side):
        m = bpy.data.materials.new(f"board_{side}")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(os.path.join(PREV, f"_tex_{side}.png"))
        tex.interpolation = "Cubic"
        met = nt.nodes.new("ShaderNodeTexImage")
        met.image = bpy.data.images.load(os.path.join(PREV, f"_tex_{side}_metal.png"))
        met.image.colorspace_settings.name = "Non-Color"
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(met.outputs["Color"], b.inputs["Metallic"])
        rough = nt.nodes.new("ShaderNodeMapRange")
        rough.inputs["To Min"].default_value = 0.42
        rough.inputs["To Max"].default_value = 0.22
        nt.links.new(met.outputs["Color"], rough.inputs["Value"])
        nt.links.new(rough.outputs["Result"], b.inputs["Roughness"])
        return m

    def add_mesh(name, V, F, material, uv_box=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], F.tolist())
        me.update()
        if uv_box is not None:
            x0, y0, x1, y1 = uv_box
            uv = me.uv_layers.new(name="uv")
            loops = np.zeros(len(me.loops) * 2)
            vi = np.zeros(len(me.loops), int)
            me.loops.foreach_get("vertex_index", vi)
            loops[0::2] = (V[vi, 0] - x0) / (x1 - x0)
            loops[1::2] = (V[vi, 1] - y0) / (y1 - y0)
            uv.data.foreach_set("uv", loops)
        ob = bpy.data.objects.new(name, me)
        ob.data.materials.append(material)
        sc.collection.objects.link(ob)
        for p in me.polygons:
            p.use_smooth = False
        return ob

    GOLD, AL = (1.0, 0.76, 0.33), (0.86, 0.87, 0.90)
    board_box = None
    for k, p in enumerate(parts):
        V, F = triangles(p["shape"], 0.01 if "wire" in p["name"] else 0.03)
        if len(F) == 0:
            continue
        nm, rgb = p["name"], p["colour"]
        is_board = ("PCB" in nm.upper()) or (p["owner"] == "" and V[:, 0].ptp() > 40)
        if is_board:
            x0, y0, x1, y1 = V[:, 0].min(), V[:, 1].min(), V[:, 0].max(), V[:, 1].max()
            board_box = (x0, y0, x1, y1, V[:, 2].min(), V[:, 2].max())
            n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
            n /= np.linalg.norm(n, axis=1)[:, None] + 1e-15
            top, bot = n[:, 2] > 0.9, n[:, 2] < -0.9
            add_mesh("board_top", V, F[top], board_mat("F"), (x0, y0, x1, y1))
            add_mesh("board_bottom", V, F[bot], board_mat("B"), (x0, y0, x1, y1))
            add_mesh("board_sides", V, F[~top & ~bot], mat("laminate", (0.80, 0.74, 0.58), 0, 0.6))
            continue
        rgb = rgb or (0.6, 0.6, 0.6)
        key = nm.split(" ")[0]
        if abs(rgb[0] - 1.0) < 0.05 and rgb[1] > 0.7 and rgb[2] < 0.4:
            m = mat("gold", GOLD, 1.0, 0.22)
        elif "wire" in nm or "launcher" in nm or "ground_plane" in nm:
            m = mat("aluminium", AL, 1.0, 0.25)
        elif "Si_" in nm:
            m = mat("silicon", (0.10, 0.11, 0.16), 0.2, 0.15)
        elif rgb[0] > 0.78 and rgb[0] < 0.85:
            m = mat("silver", (0.80, 0.80, 0.82), 1.0, 0.3)
        else:
            m = mat(key, rgb, 0.0, 0.45)
        add_mesh(f"{p['owner']}_{nm}"[:60], V, F, m)
    print("meshes built in", round(time.time() - t0, 1), "s; board box", board_box)
    x0, y0, x1, y1, z0, z1 = board_box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    def light(kind, loc, rot, energy, size=None):
        ld = bpy.data.lights.new(kind + str(len(bpy.data.lights)), kind)
        ld.energy = energy
        if size and kind == "AREA":
            ld.size = size
        if kind == "SUN":
            ld.angle = math.radians(8)
        lo = bpy.data.objects.new(ld.name, ld)
        lo.location, lo.rotation_euler = loc, rot
        sc.collection.objects.link(lo)
    light("SUN", (0, 0, 100), (math.radians(35), math.radians(10), math.radians(-30)), 3.2)
    light("SUN", (0, 0, 100), (math.radians(-50), math.radians(-25), math.radians(120)), 0.9)

    cam_d = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.clip_start, cam_d.clip_end = 0.5, 2000

    def look(loc, target, lens):
        from mathutils import Vector
        cam.location = loc
        d = Vector(target) - Vector(loc)
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cam_d.lens = lens

    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.render.threads_mode = "FIXED"
    sc.render.threads = THREADS
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"

    shots = [("render_3d_top", (cx - 62, cy - 78, z1 + 92), (cx, cy + 1.5, z1), 50, 1700, 1250, 64),
             ("render_3d_die_closeup", (cx - 9.5, cy - 13.0, z1 + 11.5), (cx + 0.2, cy + 0.6, z1), 50, 1500, 1050, 64)]
    for name, loc, tgt, lens, w, h, spp in shots:
        look(loc, tgt, lens)
        sc.render.resolution_x, sc.render.resolution_y = w, h
        sc.cycles.samples = spp
        sc.render.filepath = os.path.join(PREV, name + ".png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"rendered {name}.png in {time.time() - t:.0f} s")
    print("total", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
