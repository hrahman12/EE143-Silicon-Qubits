"""Simple, dimensionally plausible STEP models (OpenCascade via OCP) referenced by the footprints.

Model frame = KiCad footprint frame with y UP (KiCad flips the footprint y axis for 3D), z = 0 on the board top.
Envelopes only: body outline, height, pins. They are for collision / fit checks and renders, not for RF analysis.
"""
import math
import os

from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.IFSelect import IFSelect_RetDone
from OCP.Interface import Interface_Static
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDocStd import TDocStd_Document
from OCP.TopoDS import TopoDS_Compound
from OCP.XCAFDoc import XCAFDoc_ColorSurf, XCAFDoc_DocumentTool
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt

GOLD = (1.0, 0.78, 0.34)
SILVER = (0.80, 0.80, 0.82)
PTFE = (0.95, 0.95, 0.92)
BLACK = (0.12, 0.12, 0.13)
TAN = (0.72, 0.58, 0.40)
SI = (0.22, 0.24, 0.32)
AL = (0.86, 0.87, 0.90)
NB = (0.62, 0.66, 0.74)


def box(x0, y0, z0, x1, y1, z1):
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), gp_Pnt(x1, y1, z1)).Shape()


def cyl(x, y, z0, r, h, axis=(0, 0, 1)):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y, z0), gp_Dir(*axis)), r, h).Shape()


def cut(a, b):
    return BRepAlgoAPI_Cut(a, b).Shape()


def fuse(a, b):
    return BRepAlgoAPI_Fuse(a, b).Shape()


def compound(shapes):
    bb = BRep_Builder()
    c = TopoDS_Compound()
    bb.MakeCompound(c)
    for s in shapes:
        bb.Add(c, s)
    return c


def wire_tube(points, r):
    """bond wire as a chain of straight cylinders (robust; OCCT pipe sweeps crash on some loops)"""
    segs = []
    for a, b in zip(points[:-1], points[1:]):
        d = [b[i] - a[i] for i in range(3)]
        n = math.sqrt(sum(v * v for v in d))
        if n < 1e-6:
            continue
        segs.append(BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(*a), gp_Dir(*[v / n for v in d])), r, n).Shape())
    return compound(segs) if segs else None


def write_step(parts, path):
    """parts: [(name, shape, rgb)] -> one STEP (AP214) with named, coloured parts"""
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
    if w.Write(path) != IFSelect_RetDone:
        raise RuntimeError("STEP write failed: " + path)


def smp_jack(path):
    feet = [box(sx * 1.45 - 0.5, sy * 1.45 - 0.5, 0, sx * 1.45 + 0.5, sy * 1.45 + 0.5, 0.25)
            for sx in (-1, 1) for sy in (-1, 1)]
    flange = cyl(0, 0, 0.25, 2.095, 0.75)
    shell = cut(cyl(0, 0, 1.0, 1.65, 2.6), cyl(0, 0, 1.6, 1.3, 2.1))      # detent sleeve with bore
    groove = cut(cyl(0, 0, 2.9, 1.66, 0.25), cyl(0, 0, 2.85, 1.52, 0.4))
    shell = cut(shell, groove)
    diel = cut(cyl(0, 0, 1.0, 1.3, 0.6), cyl(0, 0, 0.9, 0.26, 0.9))
    pin = fuse(cyl(0, 0, 0.0, 0.25, 3.2), cyl(0, 0, 0.0, 0.32, 0.25))
    write_step([("SMP_body_BeCu_Au", compound(feet + [flange, shell]), GOLD), ("SMP_insulator_LCP", diel, PTFE),
                ("SMP_centre_pin_Au", pin, GOLD)], path)


def micro_d(path, md):
    """right-angle micro-D 15; footprint origin = row-1 centre; board edge at y = +7.0 (model frame, y up)"""
    p = md["pitch"]
    body = box(-9.0, -1.6, 0.0, 9.0, 5.8, 5.2)
    flange = box(-11.9, 5.0, 0.0, 11.9, 5.8, 5.6)
    shell = cut(box(-6.3, 5.8, 0.9, 6.3, 8.0, 4.4), box(-5.5, 6.0, 1.5, 5.5, 8.1, 3.8))
    insert = box(-5.5, 6.0, 1.5, 5.5, 7.6, 3.8)
    posts = [cyl(sx * md["mount_dx"], 5.8, 2.8, 0.75, 2.6, (0, 1, 0)) for sx in (-1, 1)]
    tails = [cyl(-3.5 * p + k * p, 0.0, -2.8, 0.255, 3.0) for k in range(8)] + \
            [cyl(-3.0 * p + k * p, md["row_dy"], -2.8, 0.255, 3.0) for k in range(7)]
    write_step([("MicroD_body_insulator", body, BLACK), ("MicroD_shell_flange", compound([flange, shell] + posts), SILVER),
                ("MicroD_insert", insert, BLACK), ("MicroD_tails_Cu_Au", compound(tails), GOLD)], path)


def chip(path, kind):
    if kind == "R":
        h, col = 0.45, BLACK
    else:
        h, col = 0.8, TAN
    body = box(-0.5, -0.4, 0.0, 0.5, 0.4, h)
    caps = compound([box(-0.8, -0.4, 0.0, -0.5, 0.4, h + 0.01), box(0.5, -0.4, 0.0, 0.8, 0.4, h + 0.01)])
    write_step([(f"{kind}0603_body", body, col), (f"{kind}0603_terminations_Cu_Sn", caps, SILVER)], path)


def die_bonded(path, die_pads, pcb_pads, die_size, die_t):
    """die (top flush with the board top, z = 0) + launcher pads + two Al-1%Si 25 um wedge bonds per launcher"""
    h = die_size / 2
    parts = [("QBFX2_die_Si_525um", box(-h, -h, -die_t, h, h, -0.002), SI),
             ("QBFX2_die_ground_plane_Nb", box(-h + 0.05, -h + 0.05, -0.002, h - 0.05, h - 0.05, 0.0), NB)]
    pads = [box(c[0] - 0.12, c[1] - 0.12, 0.0, c[0] + 0.12, c[1] + 0.12, 0.002) for c in die_pads.values()]
    parts.append(("QBFX2_launcher_pads", compound(pads), AL))
    wires = []
    for k, dc in die_pads.items():
        pc, u = pcb_pads[k]
        lat = (-u[1], u[0])
        for off in (-0.06, 0.06):
            a = (dc[0] + lat[0] * off + u[0] * 0.02, dc[1] + lat[1] * off + u[1] * 0.02, 0.003)
            b = (pc[0] - u[0] * 0.10 + lat[0] * off, pc[1] - u[1] * 0.10 + lat[1] * off, 0.036)
            pts = []
            for i in range(9):
                t = i / 8
                z = a[2] + (b[2] - a[2]) * t + 0.17 * math.sin(math.pi * min(1.0, t * 1.15))
                pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, z))
            w = wire_tube(pts, 0.0125)
            if w is not None:
                wires.append(w)
    parts.append((f"wire_bonds_Al1Si_25um ({len(wires)})", compound(wires), AL))
    write_step(parts, path)


def build_all(outdir, md, die_pads, pcb_pads, die_size, die_t):
    os.makedirs(outdir, exist_ok=True)
    smp_jack(os.path.join(outdir, "SMP_MSLD_PCS_NM.step"))
    micro_d(os.path.join(outdir, "MicroD_15P_RA.step"), md)
    chip(os.path.join(outdir, "R_0603.step"), "R")
    chip(os.path.join(outdir, "C_0603.step"), "C")
    die_bonded(os.path.join(outdir, "QBFX2_die_bonded.step"), die_pads, pcb_pads, die_size, die_t)
