"""Render the QBF-X2 row block (circuits/qbfx2_layout.gds) as layer-coloured layout views (KLayout), with title,
legend and scale bar. Output: circuits/views/chip_view_*.png and chip_views_sheet.png."""
import os, sys, json
import numpy as np
import klayout.db as db
import klayout.lay as lay
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "src"))
from hardware.architecture import Architecture
GDS = os.path.join(ROOT, "circuits", "qbfx2_layout.gds")
LAYERS = {"1/0": ("Nb (ground, strips, CPW)", 0x9aa3b5, 0.55), "2/0": ("granular Al (rail inductors)", 0xff9f1c, 0.9),
          "3/0": ("Al1 (junction base / plates)", 0x2e86ff, 0.9), "4/0": ("Al2 (junction top / straps)", 0xff3cac, 0.85),
          "6/0": ("SiNx (crossover dielectric)", 0x2ecc71, 0.55), "10/0": ("labels", 0xffffff, 1.0)}
BG = "#0b0f17"

arch = Architecture.from_results(ROOT)
p, M = arch.rail.pitch_um, 120.0
sec = {s["name"]: s for s in arch.sections()}
X = lambda n: M + n * p
cx = X(sec["coupler"]["start"] + sec["coupler"]["cells"] / 2)
ly = db.Layout(); ly.read(GDS)
top = ly.top_cell(); bb = top.dbbox()
ymid = 0.5 * (bb.bottom + bb.top)

def render(box, path, w=2000, h=1000):
    v = lay.LayoutView()
    v.load_layout(GDS)
    v.max_hier()
    v.set_config("background-color", BG)
    v.set_config("grid-visible", "false")
    v.set_config("text-visible", "true")
    v.set_config("text-color", "#ffffff")
    it = v.begin_layers()
    while not it.at_end():
        lp = it.current().dup()
        key = f"{lp.source_layer}/{lp.source_datatype}"
        name, col, _ = LAYERS.get(key, ("?", 0x777777, 0.5))
        lp.fill_color = col
        lp.frame_color = col
        lp.dither_pattern = 1 if key in ("1/0",) else (5 if key == "6/0" else 0)
        lp.transparent = key in ("1/0", "6/0")
        lp.width = 1
        v.set_layer_properties(it, lp)
        it.next()
    v.zoom_box(db.DBox(*box))
    v.save_image(path, w, h)

views = [
    ("full", "Row block: 6 rails, 878 cells each (1.99 x 0.29 mm). Launchers at both ends, beam splitters, gate coupler at the centre",
     (bb.left, bb.bottom, bb.right, bb.top), (2400, 520)),
    ("launcher", "Qubit A launch end: load loops, trap and accelerator flux lines in slots of the ground strip",
     (X(-8), ymid - 40, X(120), ymid + 40), (2000, 1000)),
    ("beam_splitter", "Beam splitter (qubit A): middle-rail islands joined by series junctions between rows A0 and A1",
     (X(sec["BS_prep"]["start"] - 4), ymid - 30, X(sec["BS_prep"]["start"] + 36), ymid + 30), (2000, 1000)),
    ("coupler_taper", "Gate coupler taper: shared Al2 strip narrowing with g(n), crossover coupling capacitors (SiNx)",
     (X(sec["taper_in"]["start"] - 2), ymid - 30, X(sec["taper_in"]["start"] + 38), ymid + 30), (2000, 1000)),
    ("coupler_plateau", "Gate coupler plateau: rows A1 / B1 share the strip (L_s 11.6 pH); C_c 0.21 fF plates per cell",
     (cx - 14, ymid - 22, cx + 14, ymid + 22), (2000, 1000)),
    ("junction_cell", "Coupler cells close up (2 um pitch): grAl inductors, Al1/Al2 cross junctions, SiNx crossovers",
     (cx - 3.2, ymid - 7.0, cx + 3.2, ymid + 7.0), (1400, 1100)),
]
out = []
for key, title, box, (w, h) in views:
    raw = os.path.join(HERE, f"_raw_{key}.png")
    render(box, raw, w, h)
    img = plt.imread(raw)
    fw = max(box[2] - box[0], (box[3] - box[1]) * w / h)   # KLayout widens the box to the image aspect ratio
    fig = plt.figure(figsize=(w / 200, h / 200 + 0.55), dpi=200, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, h / (h + 110)])
    ax.imshow(img); ax.set_axis_off()
    # scale bar: a round length near 1/5 of the view width
    target = fw / 5
    nice = min([0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500], key=lambda s_: abs(s_ - target))
    px = nice / fw * w
    ax.plot([w * 0.04, w * 0.04 + px], [h * 0.93, h * 0.93], color="white", lw=3)
    ax.text(w * 0.04 + px / 2, h * 0.90, f"{nice:g} um", color="white", ha="center", va="bottom", fontsize=9)
    fig.text(0.01, 0.985, f"QBF-X2  |  {title}", color="white", fontsize=9.5, va="top", ha="left", family="DejaVu Sans")
    handles = [Patch(facecolor="#%06x" % LAYERS[k][1], edgecolor="none", label=LAYERS[k][0]) for k in ("1/0", "2/0", "3/0", "4/0", "6/0")]
    leg = ax.legend(handles=handles, loc="upper right", fontsize=7, facecolor="#141b29", edgecolor="#3a4660", labelcolor="white", framealpha=0.9)
    path = os.path.join(HERE, f"chip_view_{key}.png")
    fig.savefig(path, facecolor=BG); plt.close(fig)
    os.remove(raw)
    out.append(path)
    print("wrote", path)
