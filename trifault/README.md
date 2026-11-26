# TriFault · "Does Lean say that?" (SF Lean Meetup, 60 min)

- `deck/index.html`: reveal.js deck, 51 slides (48 timed + 3 backup), 1920×1080, fully offline (reveal, model-viewer, fonts, Draco/KTX2 decoders vendored in `deck/vendor/`).
- `deck/present.sh`: serve + open. Unzips `../verdict-to-atom-3D.zip` into `deck/assets/` if it's next to `deck/`. Press **S** for speaker notes.
- `deck/deck.pdf`: decktape export (`?export` mode: 3D slides show their PNG posters, all fragments shown). Re-run `deck/build-pdf.sh` after adding assets.
- `deck/notes.md`: every slide's time, title and notes.
- `deck/lean/Witness.lean`: round 3 witness from the brief. **Not compiled** (no Lean here).

Each slide is `tools/slides/<name>.html`; order and talk seconds per slide live in `tools/order.txt` (the build stamps each note's [mm:ss–mm:ss] from it). Then `node tools/build.js`.
The four Lean blocks are injected from `tools/lean/*.lean`, so they stay byte for byte.
Checks (deck served on :8080): `node tools/shoot.js <outdir>` (screenshots + layout) and `node tools/check.js` (numbers vs brief, Lean bytes, banned words, timings, writes notes.md).
Setup: `npm install` in this folder (http-server, decktape; set `PUPPETEER_SKIP_DOWNLOAD=1` to reuse a local Chrome).
