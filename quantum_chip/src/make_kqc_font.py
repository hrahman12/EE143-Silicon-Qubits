"""KQCircuits' pip wheel omits util/font_polygons.oas (used for chip labels).
Regenerate it from KLayout's built-in text generator in the layout KQC expects."""
import os, kqcircuits.util.label_polygons as lp
import klayout.db as db
ly = db.Layout(); ly.dbu = lp.OAS_DBU
top = ly.create_cell("FONT"); li = ly.layer(129, 1)
gen = db.TextGenerator.default_generator()
for i, ch in enumerate(lp.OAS_LETTERS):
    if not ch.isalnum():
        continue
    r = gen.text(ch, ly.dbu, 1.0)
    h = gen.text("A", ly.dbu, 1.0).bbox().height()
    s = 0.7 * lp.OAS_TEXT_MAGNIFICATION / (h * ly.dbu)
    r = gen.text(ch, ly.dbu, s)
    b = r.bbox()
    r.move(int(i * lp.OAS_TEXT_MAGNIFICATION / ly.dbu) - b.left + 20000, -b.bottom)
    top.shapes(li).insert(r)
for p in {lp.OAS_PATH, os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(lp.__file__)), "font_polygons.oas"))}:
    os.makedirs(os.path.dirname(p), exist_ok=True); ly.write(p); print("wrote", p)
