"""Write notes/speaker_notes_final.json into the final .pptx and regenerate notes/speaker_notes_final.md."""
import json
from pptx import Presentation
P = "deck/atom_by_atom_silicon_final.pptx"
d = json.load(open("notes/speaker_notes_final.json"))
p = Presentation(P)
titles = []
for i, s in enumerate(p.slides, 1):
    s.notes_slide.notes_text_frame.text = d[str(i)]
    t = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    titles.append("Title" if i == 1 else (t[1] if len(t) > 1 and t[0].startswith("ACT") else t[0]).replace("\n", " "))
p.save(P)
# python-pptx can drop the jpg Default content type; restore it so the package validates
import zipfile, shutil, re
tmp = P + ".tmp"
with zipfile.ZipFile(P) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for it in zin.infolist():
        data = zin.read(it.filename)
        if it.filename == "[Content_Types].xml" and 'Extension="jpg"' not in data.decode():
            data = data.decode().replace("<Default ", '<Default Extension="jpg" ContentType="image/jpeg"/><Default ', 1).encode()
        zout.writestr(it, data)
shutil.move(tmp, P)
main = lambda t: t.split("\n\nIf asked:")[0]
words = sum(len(main(d[str(i)]).split()) for i in range(1, 30))
md = ["# Speaker notes: Atom-by-Atom Silicon (final deck, 33 slides)", "",
      "Same text as the speaker notes inside atom_by_atom_silicon_final.pptx. Written to be read aloud: every number and equation is spelled out the way you say it. Lines starting with **If asked** are for Q&A, not the talk.", "",
      "## 15-minute timing plan", "",
      f"The talk script for slides 1–29 (without the If asked lines) is about {words:,} words: about {words/150:.0f} minutes at a relaxed 150 words a minute, or {words/200:.0f} minutes at a brisk 200.", "",
      "| Slides | Block | Target |", "|---|---|---|",
      "| 1–2 | Title, the story in four acts | 0:45 |",
      "| 3–8 | Act 1: why single atoms | 2:30 |",
      "| 9–15 | Act 2: how it's built | 3:30 |",
      "| 16–24 | Act 3: does it work? | 5:00 |",
      "| 25–28 | Act 4: how it scales | 2:15 |",
      "| 29 | Takeaways | 0:30 |",
      "| 30–33 | Q&A equation sheets and backup (not presented) | – |",
      "| **Total** | | **14:30** |", ""]
for i, t in enumerate(titles, 1):
    body = d[str(i)].replace("\n\nIf asked:", "\n\n**If asked:**")
    md += [f"## Slide {i}: {t}", "", body, ""]
open("notes/speaker_notes_final.md", "w").write("\n".join(md))
print("applied", len(titles), "notes;", words, "words on slides 1-29")
