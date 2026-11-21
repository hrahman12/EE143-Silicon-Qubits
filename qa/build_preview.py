"""Build the web preview of the deck: every slide rendered by LibreOffice, with each embedded GIF composited
back into its slide position as an animated WebP, plus slides.json (titles, notes). Usage:
  python3 qa/build_preview.py <out_dir>"""
import sys, os, io, json, glob
from PIL import Image, ImageSequence
from pptx import Presentation
out = sys.argv[1]; os.makedirs(f"{out}/slides", exist_ok=True)
for f in glob.glob(f"{out}/slides/*"): os.remove(f)
p = Presentation("deck/atom_by_atom_silicon.pptx")
SW, SH = p.slide_width, p.slide_height
W = 1280
meta = []
for i, s in enumerate(p.slides, 1):
    base = Image.open(f"qa/render/s-{i:02d}.jpg").convert("RGB").resize((W, round(W * SH / SW)), Image.LANCZOS)
    gifs = []
    for sh in s.shapes:
        if sh.shape_type == 13 and sh.image.content_type == "image/gif":
            g = Image.open(io.BytesIO(sh.image.blob))
            box = (round(sh.left / SW * W), round(sh.top / SH * base.height), round(sh.width / SW * W), round(sh.height / SH * base.height))
            gifs.append(([fr.convert("RGB").resize(box[2:], Image.LANCZOS) for fr in ImageSequence.Iterator(g)], box, g.info.get("duration", 100)))
    texts = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    title = texts[1] if len(texts) > 1 and texts[0].startswith("ACT") else (texts[0] if texts else f"Slide {i}")
    if i == 1: title = "Atom-by-Atom Silicon (title)"
    act = texts[0].title() if texts and texts[0].startswith("ACT") else ""
    notes = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ""
    if gifs:
        n = max(len(fr) for fr, _, _ in gifs); dur = min(d for _, _, d in gifs)
        frames = []
        for k in range(n):
            im = base.copy()
            for fr, box, _ in gifs: im.paste(fr[k % len(fr)], box[:2])
            frames.append(im)
        fn = f"slides/s-{i:02d}.webp"
        frames[0].save(f"{out}/{fn}", save_all=True, append_images=frames[1:], duration=dur, loop=0, quality=72, method=4)
        frames[0].save(f"{out}/slides/s-{i:02d}-still.jpg", quality=82)
    else:
        fn = f"slides/s-{i:02d}.jpg"; base.save(f"{out}/{fn}", quality=82)
    meta.append(dict(n=i, title=title.replace("\n", " "), act=act, src=fn, animated=bool(gifs), notes=notes))
json.dump(meta, open(f"{out}/slides.json", "w"), ensure_ascii=False, indent=0)
tot = sum(os.path.getsize(f) for f in glob.glob(f"{out}/slides/*"))
print(len(meta), "slides,", sum(m["animated"] for m in meta), "animated,", f"{tot/1e6:.1f} MB")
