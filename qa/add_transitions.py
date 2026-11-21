"""Post-process: add a fade transition to every slide (pptxgenjs has no transition API)."""
import sys, zipfile, re, shutil, os
src = sys.argv[1]; tmp = src + ".tmp"
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
            x = data.decode("utf-8")
            if "<p:transition" not in x:
                x = x.replace("</p:clrMapOvr>", '</p:clrMapOvr><p:transition spd="med"><p:fade/></p:transition>', 1)
            data = x.encode("utf-8")
        if not item.filename.endswith("/"):
            zout.writestr(item, data)
shutil.move(tmp, src); print("transitions added")
