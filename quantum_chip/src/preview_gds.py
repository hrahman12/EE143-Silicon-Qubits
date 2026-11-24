"""KLayout GDS inspection: render the die to PNG (full + zoom boxes in um) and list layer shape counts."""
import sys, klayout.db as db, klayout.lay as lay
gds, out = sys.argv[1], sys.argv[2]
ly = db.Layout(); ly.read(gds); top = ly.top_cell()
for li in ly.layer_indexes():
    print(ly.get_info(li), top.shapes(li).size())
COL = {"1/0": (0x8a8f99, 0), "2/0": (0, -1), "5/0": (0, -1), "3/0": (0x2f6bff, 0), "4/0": (0xff2aff, 0),
       "6/0": (0x22aa55, 0), "7/0": (0xe03030, 0), "8/0": (0xe2b54a, 2), "9/0": (0x111111, 0)}
v = lay.LayoutView(); v.load_layout(gds); v.max_hier()
v.set_config("background-color", "#ffffff"); v.set_config("grid-visible", "false")
it = v.begin_layers()
while not it.at_end():
    lp = it.current().dup()
    key = f"{lp.source_layer}/{lp.source_datatype}"
    c, dp = COL.get(key, (0x999999, 0))
    if dp == -1: lp.visible = False
    else: lp.fill_color = c; lp.frame_color = c; lp.dither_pattern = dp; lp.transparent = key == "1/0"
    if key == "1/0": lp.dither_pattern = 9
    v.set_layer_properties(it, lp); it.next()
for i, z in enumerate([None] + [tuple(map(float, s.split(","))) for s in sys.argv[3:]]):
    v.zoom_box(db.DBox(*z) if z else db.DBox(0, 0, 10000, 10000))
    v.save_image(out.replace(".png", f"_{i}.png") if i else out, 1400, 1400)
