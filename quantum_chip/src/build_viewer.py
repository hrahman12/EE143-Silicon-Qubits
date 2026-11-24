"""Inject the layer manifest into the viewer template -> out/interactive_3d_view.html (loads ./assembly.glb).

The template carries the QFX-1 header and camera presets; for the legacy RFL die they are swapped here."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from design_params import ACTIVE_DIE  # noqa: E402

OUT = os.path.join(HERE, "..", "out")
man = json.load(open(os.path.join(OUT, "layer_manifest.json")))
html = open(os.path.join(HERE, "viewer_template.html")).read().replace("/*MANIFEST*/null", json.dumps(man, separators=(",", ":")))
if ACTIVE_DIE == "RFL":
    for a, b in (
        ("<title>Quantum Fluxon Explorer</title>", "<title>RFL Chip Explorer</title>"),
        ("<h1>QFX-1<span>·</span>Quantum fluxon</h1>", "<h1>RFL<span>·</span>RE1</h1>"),
        ('<span class="sub">2 quantum-fluxon qubits · heavy-fluxon kick line · 837 Al junctions · 6-layer carrier · 1 unit = 1 mm</span>',
         '<span class="sub">Reversible fluxon logic die · 3270 Nb junctions · 6-layer RO4003C carrier · 1 unit = 1 mm</span>'),
        ('''  "Qubit pair": [[0.0, 1.86, 0.34], [0, 1.456, -0.2]],
  "QF1 ring": [[-0.08, 1.56, -0.05], [-0.2, 1.456, -0.2]],
  "Kick line": [[0.4, 3.2, 1.6], [0, 1.456, -1.0]],''',
         '''  "Rotary element": [[0.5, 2.0, -0.6], [0, 1.46, -1.4]],
  "Barrier + DC/SFQ": [[-1.4, 1.9, -2.2], [-1.8, 1.46, -3.0]],'''),
        ('select("die_junctions_AlOx");', 'select("die_M1_Nb_LJJ");'),
    ):
        assert a in html, a[:40]
        html = html.replace(a, b)
open(os.path.join(OUT, "interactive_3d_view.html"), "w").write(html)
print("wrote interactive_3d_view.html", len(html), "bytes", "(die %s)" % ACTIVE_DIE)
