# PLAN: Atom-by-Atom Silicon (EE143 device profile, 15 min)

## Inputs found
- `notes/reference_pack.pdf` (uploaded), transcribed to `REFERENCES.md` with DOIs pulled from its hyperlinks.
- `reference_decks/` is **not in the repo** (the zip wasn't uploaded). Style comes from the measurements the pack records for those decks (see `notes/reference_style.md`). Logged in `qa/open_items.md`.

## Figures
- F-figures: CC BY copies from the PMC Open Access S3 bucket (`figures/src/fetch_pmc.py`), the arXiv copy of Schofield2025 and UCL Discovery's copy of DAnna2023. Licences checked in each article's XML: all CC BY 4.0, Stock2020 (ACS AuthorChoice CC-BY) and Tseng2023 included, so F11 and F17 can be used.
- O-figures + original "prototype" visuals: `figures/src/make_figures.py` (matplotlib, Liberation Sans = Arial metrics). 3D renders: Si(001):H surface with P/As windows, prototype 2x2 As register, array-yield surface p^n.
- Native pptx charts: O6 (array yield), O8 (write speed, log), Poisson ion statistics, thermal budget.
- No NC-ND or paywalled figure is embedded; Schofield2003/Fuechsle2012/Kane1998/He2019/Koch2019 get original "Schematic after" drawings.

## Deck (26 slides + 1 backup, ~35 s per content slide)
1 Title · 2 Device at a glance · 3 Timeline · 4 Why a donor · 5 Why not implantation · 6 Neil Curson ·
7 Process flow (11 steps + EE143 module per step) · 8 Steps 1-3 · 9 Step 4 · 10 Step 5 · 11 Step 6 · 12 Steps 7-8 · 13 Steps 9-11 ·
14 Did it work (+ EE143 sheet-resistance check) · 15 Landmarks · 16 Yield problem (+ Monte Carlo) · 17 Arsenic fix · 18 Beyond Si:P ·
19 Processors · 20 Simulator · 21 Throughput wall · 22 EUV scaling · 23 Our prototype (3D + yield model) · 24 Prototype traveler mapped to EE143 ·
25 Takeaways · 26 References · Backup: alternate titles
- Deviation from the ~24-slide outline: +2 prototype slides (user asked for "our own prototypes" and course tie-backs); references fit on one slide.

## Order of work
1. Figures → 2. slides 1-8, render, check → 3. remaining slides → 4. full QA (render, text dump, fact check, manifest) → 5. README, commit, push.
