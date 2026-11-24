"""KLayout GDS inspection: render the die layout to PNG (full + zooms) and list layers."""
import sys, klayout.db as db, klayout.lay as lay
gds = sys.argv[1]; out = sys.argv[2]
ly = db.Layout(); ly.read(gds)
top = ly.top_cell()
for li in ly.layer_indexes():
    n = top.begin_shapes_rec(li); c = 0
    while not n.at_end(): c += 1; n.next()
    if c: print(ly.get_info(li), c)
v = lay.LayoutView(); v.load_layout(gds); v.max_hier(); v.set_config("background-color", "#ffffff")
v.set_config("grid-visible", "false"); v.set_config("text-visible", "false")
it = v.begin_layers()
while not it.at_end():
    lp = it.current().dup()
    name = lp.source
    if "130/1" in name or "base_metal_gap_wo_grid" in name: lp.fill_color = 0x3355aa; lp.frame_color = 0x3355aa; lp.dither_pattern = 0
    elif "225/" in name or "222/" in name or "133/" in name or "154/" in name or "135/" in name: lp.visible = False
    v.set_layer_properties(it, lp); it.next()
zooms = [None] + [tuple(map(float, z.split(","))) for z in sys.argv[3:]]
for i, z in enumerate(zooms):
    if z: v.zoom_box(db.DBox(*z))
    else: v.zoom_box(db.DBox(0, 0, 10000, 10000))
    v.save_image(out.replace(".png", f"_{i}.png") if i else out, 1600, 1600)
