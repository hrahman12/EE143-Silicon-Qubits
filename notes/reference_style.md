# Reference style (measured / adopted)

The `reference_decks/` folder was not supplied with this repo, so I could not open the .pptx files with python-pptx or render them.
The values below come from (a) the measurements recorded in the reference pack's "Reference decks" table and (b) the prompt's design defaults.
Re-run this step if the decks are added: `python3 -c "from pptx import Presentation; ..."` and update this file.

| Item | From the pack | Adopted |
|---|---|---|
| Slide size | 16:9 (Google Slides) | LAYOUT_16x9, 10 x 5.625 in |
| Slide count | image-heavy device decks 16-27; aim 20-24 | 26 + 1 backup |
| Pictures per slide | DMD 1.62, SC qubit 1.26 | >=1 figure on every content slide, ~half the slide |
| Picture area | DMD 37%, SC qubit 32% | ~45-60% (user asked for "as visual as possible") |
| Background | White (DMD) | #FFFFFF |
| Title | Short, top-left (DMD); claim-style "Step 8 · ..." (CMOS) | 26 pt bold Arial, x=0.5 in, y=0.3 in, ink #1F2A36 |
| Step tracker | Mask-step tracker top-right (DMD) | "Step n of 11" top-right, 11 pt |
| Body | 2-3 bullets beside figure | 14-15 pt, <=3 bullets, 25-40 words |
| Captions | Paper captions under SEM figures | 10 pt muted #5B6770 |
| Source line | Bottom-left (DMD) | 9 pt grey, y=5.25 in |
| Slide number | Bottom-right (DMD) | 9 pt, on master |
| Cross-sections | One material legend on all process slides | Fixed legend: Si #8C96A0, Si cap #C9D1D8, H #9CC8E6, P #D9731A, As #0F9FA0, Al #5E6A75, SiO2 #E3DDF0 |
| Title slide | Title, presenter, EE143, date + AI-use line (DMD) | Same, with figure F1 on the right |
| Ending | Summary/"what's next", then References/Works Cited | Takeaways, References, backup |
