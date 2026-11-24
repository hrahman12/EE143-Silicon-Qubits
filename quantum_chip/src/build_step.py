"""Geometry-preserving STEP of the full assembly (OpenCascade / XCAF), with a named, coloured
part per physical layer. True thicknesses are used here (no visual exaggeration).

Inputs: out/rf_carrier.step (board body from KiCad), out/_cache/* (2D regions from build_geometry.py),
        out/layer_manifest.json, out/pcb_model.json
Output: out/assembly.step
"""
import json
import math
import os
import sys

import numpy as np
from OCP.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf
from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeEdge,
                                BRepBuilderAPI_MakeWire, BRepBuilderAPI_Transform)
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipe
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.collections import Array1_gp_Pnt as TColgp_Array1OfPnt
from OCP.Approx import Approx_ParametrizationType
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.STEPControl import STEPControl_Reader, STEPControl_AsIs
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf
from OCP.TDataStd import TDataStd_Name
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.IFSelect import IFSelect_RetDone
from OCP.Interface import Interface_Static

sys.path.insert(0, os.path.dirname(__file__))
from design_params import DIE, PACKAGE

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
reg = json.load(open(os.path.join(OUT, "_cache", "regions_2d.json")))
man = json.load(open(os.path.join(OUT, "layer_manifest.json")))
model = json.load(open(os.path.join(OUT, "pcb_model.json")))
curves = np.load(os.path.join(OUT, "_cache", "bond_curves.npy"))
Z = man["Z"]
T = Z["F.Cu"][1]
FILM = DIE["film_thickness_nm"] * 1e-6


def wire(loop, z):
    mp = BRepBuilderAPI_MakePolygon()
    last = None
    for x, y in loop:
        if last is not None and math.dist(last, (x, y)) < 1e-6:
            continue
        mp.Add(gp_Pnt(x, y, z))
        last = (x, y)
    mp.Close()
    return mp.Wire()


def extrude(polys, z0, z1):
    b = BRep_Builder()
    comp = TopoDS_Compound()
    b.MakeCompound(comp)
    n = 0
    for poly in polys:
        mf = BRepBuilderAPI_MakeFace(wire(poly[0], z0), True)
        for h in poly[1:]:
            w = wire(h, z0)
            w.Reverse()
            mf.Add(w)
        if not mf.IsDone():
            continue
        pr = BRepPrimAPI_MakePrism(mf.Face(), gp_Vec(0, 0, z1 - z0))
        b.Add(comp, pr.Shape())
        n += 1
    return comp, n


def box(x0, y0, z0, x1, y1, z1):
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), gp_Pnt(x1, y1, z1)).Shape()


def cyl(x, y, z0, r, h, axis=(0, 0, 1)):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y, z0), gp_Dir(*axis)), r, h).Shape()


parts = []    # (name, shape, rgb)

# board body from KiCad
rd = STEPControl_Reader()
if rd.ReadFile(os.path.join(OUT, "rf_carrier.step")) == IFSelect_RetDone:
    rd.TransferRoots()
    shp = rd.OneShape()
    # KiCad places the board at page coordinates with z=0 at the bottom; move board centre to origin
    tr = gp_Trsf()
    X0, Y0 = model["kicad_offset"]
    tr.SetTranslation(gp_Vec(-X0, Y0, Z["B.Mask"][0]))   # KiCad body: z=0 at bottom mask face
    shp = BRepBuilderAPI_Transform(shp, tr, True).Shape()
    parts.append(("PCB_body_RO4003C_stack (from KiCad)", shp, (0.85, 0.80, 0.70)))

for lay, col in (("F.Cu", (0.95, 0.2, 0.2)), ("In1.Cu", (0.8, 0.6, 0.2)), ("In2.Cu", (0.2, 0.8, 0.45)),
                 ("In3.Cu", (0.8, 0.5, 0.2)), ("In4.Cu", (0.6, 0.4, 0.8)), ("B.Cu", (0.2, 0.4, 1.0))):
    s, n = extrude(reg["copper"][lay], *Z[lay])
    parts.append((f"PCB_copper_{lay}", s, col))
s, _ = extrude(reg["enig_F"], T, T + 0.004)
parts.append(("PCB_ENIG_top", s, (1.0, 0.8, 0.3)))
# die
zs = man["z_substrate"]
parts.append(("die_Si_substrate_525um", box(-5, -5, zs[0], 5, 5, zs[1]), (0.2, 0.22, 0.28)))
za = man["z_attach"]
parts.append(("die_attach_GE7031", box(-5, -5, za[0], 5, 5, za[1]), (0.66, 0.4, 0.12)))
s, n = extrude(reg["die_metal"], T, T + FILM)
parts.append(("die_Al_200nm (GDS base metal)", s, (0.85, 0.87, 0.9)))
s, _ = extrude(reg["jj1"], T, T + DIE["jj_bottom_nm"] * 1e-6)
parts.append(("die_JJ_bottom_Al_40nm", s, (1, 0.25, 1)))
s, _ = extrude(reg["jj2"], T + DIE["jj_bottom_nm"] * 1e-6, T + (DIE["jj_bottom_nm"] + DIE["jj_top_nm"]) * 1e-6)
parts.append(("die_JJ_top_Al_80nm", s, (1, 0.5, 1)))
hab = DIE["airbridge_height_um"] * 1e-3
s, _ = extrude(reg["ab_pad"], T + FILM, T + FILM + hab)
parts.append(("die_airbridge_posts", s, (0.5, 1, 0.85)))
s, _ = extrude(reg["ab_fly"], T + FILM + hab, T + FILM + hab + DIE["airbridge_thickness_nm"] * 1e-6)
parts.append(("die_airbridge_spans", s, (0.5, 1, 0.85)))

# wire bonds: circular section swept along the same Bezier loop as the mesh
bb = BRep_Builder()
wb = TopoDS_Compound()
bb.MakeCompound(wb)
r = PACKAGE["wire_d_um"] * 1e-3 / 2
for c in curves:
    arr = TColgp_Array1OfPnt(1, len(c))
    for i, p in enumerate(c):
        arr.SetValue(i + 1, gp_Pnt(*map(float, p)))
    spl = GeomAPI_PointsToBSpline(arr, Approx_ParametrizationType.Approx_ChordLength, 3, 8).Curve()
    path = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(spl).Edge()).Wire()
    d = c[1] - c[0]
    d /= np.linalg.norm(d)
    circ = gp_Circ(gp_Ax2(gp_Pnt(*map(float, c[0])), gp_Dir(*map(float, d))), r)
    prof = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(circ).Edge()).Wire()
    face = BRepBuilderAPI_MakeFace(prof).Face()
    pipe = BRepOffsetAPI_MakePipe(path, face)
    if pipe.IsDone():
        bb.Add(wb, pipe.Shape())
parts.append((f"wire_bonds_Al_25um ({len(curves)})", wb, (0.75, 0.75, 0.78)))

# package base with pedestal and SMP / screw holes
zb0, zb1 = man["z_base"]
base = box(-20, -20, zb0, 20, 20, zb1)
for f in model["footprints"]:
    if f["kind"] == "SMP_VERT_BOTTOM":
        base = BRepAlgoAPI_Cut(base, cyl(f["x"], f["y"], zb0 - 1, 2.3, 10)).Shape()
for mx, my in model["mounting_holes"]:
    base = BRepAlgoAPI_Cut(base, cyl(mx, my, zb0 - 1, 1.05, 10)).Shape()
parts.append(("package_base_Au_on_OFHC", base, (1.0, 0.78, 0.4)))
parts.append(("package_pedestal", box(-5.1, -5.1, zb1, 5.1, 5.1, za[0]), (1.0, 0.78, 0.4)))
# connectors (envelope bodies at true positions; detailed meshes live in the GLB / .blend)
PIN_Z = T + 0.035 + 0.25
for f in model["footprints"]:
    if f["kind"] == "SMA_EDGE":
        a = math.radians(f["rot"])
        ox, oy = -math.sin(a), math.cos(a)            # local +y (mating axis) in board frame
        body = cyl(f["x"], f["y"], 0, 3.15, 9.8, (ox, oy, 0))
        tr = gp_Trsf()
        tr.SetTranslation(gp_Vec(0, 0, PIN_Z))
        body = BRepBuilderAPI_Transform(body, tr, True).Shape()
        parts.append((f"{f['ref']}_SMA_end_launch_{f['net']}", body, (0.66, 0.65, 0.62)))
    else:
        parts.append((f"{f['ref']}_SMP_vertical_{f['net']}", cyl(f["x"], f["y"], -4.2, 1.75, 4.2), (1, 0.78, 0.35)))

# XCAF document with names + colours
doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
for name, shp, rgb in parts:
    lab = st.AddShape(shp, False)
    TDataStd_Name.Set_s(lab, TCollection_ExtendedString(name))
    ct.SetColor(lab, Quantity_Color(*rgb, Quantity_TOC_RGB), XCAFDoc_ColorSurf)
Interface_Static.SetCVal_s("write.step.unit", "MM")
Interface_Static.SetCVal_s("write.step.schema", "AP214IS")
w = STEPCAFControl_Writer()
w.SetNameMode(True)
w.SetColorMode(True)
w.Transfer(doc, STEPControl_AsIs)
w.Write(os.path.join(OUT, "assembly.step"))
print("wrote assembly.step with", len(parts), "named parts")
