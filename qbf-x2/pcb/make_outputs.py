#!/usr/bin/env python3
"""Post-process the kicad-cli exports (run by export_carrier.sh after the kicad-cli steps):

  fab/qbfx2_carrier_bom.csv            BOM grouped by part, from `kicad-cli sch export python-bom` XML
  fab/qbfx2_carrier-fab_drawing.pdf    page 1 = Edge.Cuts + fab-notes layer (title block), then KiCad's drill maps
  fab/previews/*.png                   layer previews cropped to the board (rasterised from kicad-cli PDF plots)
  fab/previews/_tex_*.png              board textures for render_3d.py
  reports/outputs_manifest.json        every output file with its size
"""
import csv
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import carrier_params as P  # noqa: E402

NAME = P.PROJECT["name"]
PCB = os.path.join(HERE, f"{NAME}.kicad_pcb")
FAB = os.path.join(HERE, "fab")
PREV = os.path.join(FAB, "previews")
REP = os.path.join(HERE, "reports")
X0, Y0 = P.BOARD["page_origin"]
BX0, BX1, BY0, BY1 = P.BOARD["x_min"], P.BOARD["x_max"], P.BOARD["y_min"], P.BOARD["y_max"]


def run(*args):
    r = subprocess.run(list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{r.stdout}\n{r.stderr}")
    return r.stdout


# ------------------------------------------------------------------------------------------------ BOM
FITTED = {"R": "SMT reflow (PCBA)", "C": "SMT reflow (PCBA)", "J": "SMT reflow (PCBA)", "U": "customer: die attach + wire bond",
          "H": "board feature, not purchased"}


def bom():
    xml = os.path.join(REP, "bom_intermediate.xml")
    run("kicad-cli", "sch", "export", "python-bom", "-o", xml, os.path.join(HERE, f"{NAME}.kicad_sch"))
    root = ET.parse(xml).getroot()
    groups = {}
    for c in root.find("components"):
        ref = c.get("ref")
        fl = c.find("fields")
        f = {fd.get("name"): (fd.text or "") for fd in (list(fl) if fl is not None else [])}
        key = (c.findtext("value"), c.findtext("footprint"), f.get("MPN", ""))
        g = groups.setdefault(key, dict(refs=[], fields=f, value=key[0], footprint=key[1]))
        g["refs"].append(ref)

    def rk(r):
        pre = "".join(ch for ch in r if not ch.isdigit())
        num = "".join(ch for ch in r if ch.isdigit())
        return (pre, int(num or 0))
    rows = []
    for (val, fp, mpn), g in sorted(groups.items(), key=lambda kv: rk(sorted(kv[1]["refs"], key=rk)[0])):
        refs = sorted(g["refs"], key=rk)
        f = g["fields"]
        pre = refs[0].rstrip("0123456789")
        fitted = FITTED.get(pre, "")
        if refs[0] == "J11":
            fitted = "hand solder after reflow (PCBA)"
        rows.append(dict(Qty=len(refs), References=" ".join(refs), Value=val, Description=f.get("Description", ""),
                         Footprint=fp, Manufacturer=f.get("Manufacturer", ""), MPN=mpn,
                         MPN_status=f.get("MPN status", ""), Fitted=fitted, Note=f.get("Note", "")))
    path = os.path.join(FAB, f"{NAME}_bom.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Item", "Qty", "References", "Value", "Description", "Footprint", "Manufacturer", "MPN",
                    "MPN status", "Fitted by", "Note"])
        for i, r in enumerate(rows, 1):
            w.writerow([i, r["Qty"], r["References"], r["Value"], r["Description"], r["Footprint"], r["Manufacturer"],
                        r["MPN"], r["MPN_status"], r["Fitted"], r["Note"]])
    summ = dict(lines=len(rows), parts=sum(r["Qty"] for r in rows),
                pcba_parts=sum(r["Qty"] for r in rows if "PCBA" in r["Fitted"]),
                to_confirm=[r["MPN"] for r in rows if r["MPN_status"] == "to confirm"],
                missing_mpn=[r["References"] for r in rows if not r["MPN"]])
    json.dump(dict(rows=rows, summary=summ), open(os.path.join(REP, "bom_summary.json"), "w"), indent=1)
    print(f"BOM: {summ['lines']} lines, {summ['parts']} parts ({summ['pcba_parts']} on the PCBA), "
          f"to confirm: {summ['to_confirm']}")
    return summ


# ------------------------------------------------------------------------------------------------ drawings
def fab_drawing():
    p1 = os.path.join(FAB, "_fab_page1.pdf")
    run("kicad-cli", "pcb", "export", "pdf", "--include-border-title", "--black-and-white", "-l", "Edge.Cuts,Dwgs.User",
        "-o", p1, PCB)
    out = PdfWriter()
    for pg in PdfReader(p1).pages:
        out.add_page(pg)
    maps = sorted(f for f in os.listdir(os.path.join(FAB, "drill")) if f.endswith("drl_map.pdf"))
    for m in maps:
        for pg in PdfReader(os.path.join(FAB, "drill", m)).pages:
            out.add_page(pg)
    dst = os.path.join(FAB, f"{NAME}-fab_drawing.pdf")
    with open(dst, "wb") as fh:
        out.write(fh)
    os.remove(p1)
    print("fab drawing:", os.path.basename(dst), "pages:", 1 + len(maps))


# ------------------------------------------------------------------------------------------------ previews
def crop_pdf(pdf, png_base, dpi, region=None, mirror=False):
    """rasterise the board region (page mm) of a kicad-cli PDF"""
    x0, y0, x1, y1 = region or (X0 + BX0 - 1.5, Y0 - BY1 - 1.5, X0 + BX1 + 1.5, Y0 - BY0 + 1.5)
    if mirror:
        x0, x1 = 420.0 - x1, 420.0 - x0
    k = dpi / 25.4
    run("pdftoppm", "-r", str(dpi), "-x", str(int(x0 * k)), "-y", str(int(y0 * k)), "-W", str(int((x1 - x0) * k)),
        "-H", str(int((y1 - y0) * k)), "-png", "-singlefile", pdf, png_base)
    return png_base + ".png"


def previews():
    os.makedirs(PREV, exist_ok=True)
    tmp = os.path.join(PREV, "_tmp.pdf")
    specs = [("top_view", "F.Cu,F.Mask,F.SilkS,Edge.Cuts", False), ("layer_F_Cu", "F.Cu,Edge.Cuts", False),
             ("layer_In1_Cu", "In1.Cu,Edge.Cuts", False), ("layer_In2_Cu", "In2.Cu,Edge.Cuts", False),
             ("layer_In3_Cu", "In3.Cu,Edge.Cuts", False), ("layer_In4_Cu", "In4.Cu,Edge.Cuts", False),
             ("layer_B_Cu", "B.Cu,Edge.Cuts", False), ("bottom_view_mirrored", "B.Cu,B.Mask,B.SilkS,Edge.Cuts", True)]
    made = []
    for name, layers, mir in specs:
        args = ["kicad-cli", "pcb", "export", "pdf", "-l", layers, "-o", tmp, PCB]
        if mir:
            args.insert(4, "--mirror")
        run(*args)
        made.append(crop_pdf(tmp, os.path.join(PREV, name), 500, mirror=mir))
    run("kicad-cli", "pcb", "export", "pdf", "-l", "F.Cu,F.Mask,F.SilkS,Edge.Cuts", "-o", tmp, PCB)
    made.append(crop_pdf(tmp, os.path.join(PREV, "die_area_top"), 1200, (X0 - 8.5, Y0 - 8.5, X0 + 8.5, Y0 + 8.5)))
    run("kicad-cli", "pcb", "export", "pdf", "-l", "In2.Cu,Edge.Cuts", "-o", tmp, PCB)
    made.append(crop_pdf(tmp, os.path.join(PREV, "die_area_In2_dc_routing"), 800, (X0 - 15, Y0 - 12, X0 + 15, Y0 + 12)))
    os.remove(tmp)
    # whole-page thumbnails of the drawings and the schematic
    for pdf, name in ((f"{NAME}-schematic.pdf", "schematic"), (f"{NAME}-fab_drawing.pdf", "fab_drawing_p1"),
                      (f"{NAME}-assembly.pdf", "assembly_drawing")):
        run("pdftoppm", "-r", "110", "-f", "1", "-l", "1", "-png", "-singlefile", os.path.join(FAB, pdf),
            os.path.join(PREV, name))
        made.append(os.path.join(PREV, name + ".png"))
    print("previews:", len(made))


def textures(px_per_mm=60):
    """realistic top / bottom textures from black-and-white layer plots (used by render_3d.py)"""
    dpi = int(round(px_per_mm * 25.4))
    region = (X0 + BX0, Y0 - BY1, X0 + BX1, Y0 - BY0)
    tmp = os.path.join(PREV, "_tex.pdf")

    def mask(layer, mirror=False):
        run("kicad-cli", "pcb", "export", "pdf", "--black-and-white", "-l", layer, "-o", tmp, PCB)
        png = crop_pdf(tmp, os.path.join(PREV, "_m"), dpi, region)
        a = np.asarray(Image.open(png).convert("L")) < 128
        os.remove(png)
        return a
    out = {}
    for side in ("F", "B"):
        cu, op, sk = mask(f"{side}.Cu"), mask(f"{side}.Mask"), mask(f"{side}.SilkS")
        h, w = cu.shape
        img = np.zeros((h, w, 3), np.uint8)
        img[:] = (214, 204, 176)                              # bare RO4003C
        img[~op & cu] = (46, 120, 64)                         # mask over copper
        img[~op & ~cu] = (30, 92, 50)                         # mask over laminate
        img[op & cu] = (226, 182, 86)                         # exposed copper with Au / Pd-Au finish
        img[op & ~cu] = (205, 195, 165)
        img[sk & ~op] = (236, 236, 230)
        p = os.path.join(PREV, f"_tex_{side}.png")
        Image.fromarray(img).save(p)
        Image.fromarray(((op & cu) * 255).astype(np.uint8)).save(os.path.join(PREV, f"_tex_{side}_metal.png"))
        out[side] = p
    os.remove(tmp)
    print("textures:", out)
    return out


def manifest():
    files = []
    for base in ("fab", "reports"):
        for dp, dn, fn in os.walk(os.path.join(HERE, base)):
            for f in sorted(fn):
                if "_selftest" in dp:
                    continue
                pth = os.path.join(dp, f)
                files.append(dict(path=os.path.relpath(pth, HERE), bytes=os.path.getsize(pth)))
    json.dump(files, open(os.path.join(REP, "outputs_manifest.json"), "w"), indent=1)
    print("manifest:", len(files), "files")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("all", "bom"):
        bom()
    if step in ("all", "drawings"):
        fab_drawing()
    if step in ("all", "previews"):
        previews()
        textures()
    if step in ("all", "manifest"):
        manifest()
