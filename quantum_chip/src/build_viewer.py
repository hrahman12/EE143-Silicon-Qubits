"""Inject the layer manifest into the viewer template -> out/interactive_3d_view.html (loads ./assembly.glb)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
man = json.load(open(os.path.join(OUT, "layer_manifest.json")))
html = open(os.path.join(HERE, "viewer_template.html")).read().replace("/*MANIFEST*/null", json.dumps(man, separators=(",", ":")))
open(os.path.join(OUT, "interactive_3d_view.html"), "w").write(html)
print("wrote interactive_3d_view.html", len(html), "bytes")
