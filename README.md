# Atom-by-Atom Silicon: Building Quantum Processors from Single Dopant Atoms

EE143 (Microfabrication Technology) tutorial deck, 15 min. A device profile of STM-patterned P and As dopant qubits, featuring the work of Neil J. Curson (UCL).

- **Deck:** `deck/atom_by_atom_silicon.pptx` (editable, 16:9, 10 × 5.625 in) and `deck/atom_by_atom_silicon.pdf`
- **Speaker notes:** in the .pptx and in `notes/speaker_notes.md` (with a 15-minute timing plan)
- **Facts:** every number comes from `REFERENCES.md` (transcribed from `notes/reference_pack.pdf`); see `qa/fact_check.md`

## Rebuild

```bash
npm install                                  # pptxgenjs 3.12.0, image-size 1.1.1
pip install matplotlib numpy pillow pymupdf  # figure scripts
python3 figures/src/make_figures.py          # crops + original diagrams -> figures/final/
npm run build                                # node build_deck.js, strip zip folder entries, export PDF (needs LibreOffice)
```

QA render: `pdftoppm -jpeg -r 110 deck/atom_by_atom_silicon.pdf qa/render/s` (renders are git-ignored).

### Re-downloading raw figures
`python3 figures/src/fetch_pmc.py` pulls figure images, article XML (licence text) and metadata from the PMC Open Access bucket. The article PDFs are git-ignored to keep the repo small; the images extracted from them (`figures/raw/*/pdfimg/`, `page*_300dpi.png`) are committed. To re-extract, download:
- PMC PDFs: `https://pmc-oa-opendata.s3.amazonaws.com/<PMCID>.1/<PMCID>.1.pdf`
- Schofield2025: `https://arxiv.org/pdf/2501.04535v2`
- DAnna2023: UCL Discovery 10167842 (CC BY published version)

## Layout system
`build_deck.js` defines the theme once (Arial; ink #1F2A36, muted #5B6770, P #D9731A, As #0F9FA0, fixed material legend) and eight slide masters (TITLE, SECTION, TITLE_ONLY, FIG_TEXT, TWO_FIG, TABLE, PROCESS, REFS) with named `title` and `src` placeholders, footer and slide number. Sections: Intro, Motivation, Process, Results, Scaling, Prototype, Wrap-up, Backup. Charts (array yield, write speed on a log axis, Poisson ion statistics, thermal budget) are native PowerPoint charts.

## Slides (26 + 1 backup)
1 Title · 2 Device at a glance · 3 Timeline · 4 Why a donor · 5 Why not implantation · 6 Neil J. Curson · 7 11-step process flow (EE143 module per step) · 8–13 Steps 1–11 (cross-section + legend + step tracker) · 14 Did it work (+ EE143 sheet-resistance check) · 15 Landmarks · 16 Yield problem (+ Monte Carlo) · 17 Arsenic fix · 18 Beyond Si:P · 19 Processors · 20 Simulator · 21 Throughput wall · 22 EUV scaling · **23 Our prototype (3D render + yield model)** · **24 Prototype traveler mapped to EE143** · 25 Takeaways · 26 References · Backup: alternate titles

Slides 23–24 go beyond the outline: an original 2×2 As register design and its traveler, built only from published recipes.

## Reproduced vs original images
**Reproduced (CC BY 4.0, credited on the slide):** Stock2024 Figs. 1, 3; Schofield2025 §2.2, §2.4, §3.2, §4.1, §5.3 figures; Constantinou2024 Fig. 5; Constantinou2023 Fig. 2; D'Anna2023 Fig. 2; Stock2020 Figs. 3, 4; Hofmann2023 Fig. 1a; Lundgren2023 Fig. 1; Thorvaldson2025 Fig. 4b; Edlbauer2025 Fig. 1a,b; Wang2022 Fig. 1. Licences were checked in each article's own XML; Stock2020 (ACS AuthorChoice CC-BY) and Tseng2023 (CC BY 4.0) included.

**Original (code in `figures/src/make_figures.py`, or native shapes and charts):** Kane-style cross-section (after Kane1998), 3D Si(001):H surface renders, step cross-sections, process icons, overgrowth temperature program, spin-level diagram, 2003/2012 landmark schematics (after Schofield2003 / Fuechsle2012), Monte Carlo array outcomes, 3D yield surface, prototype 3D render, timelines, all charts. No paywalled or CC BY-NC-ND figure is embedded, and no micrograph or data plot is generated. Full list: `figures/manifest.csv`.

## QA status
- Rendered with LibreOffice and checked slide by slide (overflow, overlaps, margins, title position).
- Anthropic pptx-skill `validate.py`: all validations passed.
- Speaker notes: 98–130 words on every slide.
- `qa/fact_check.md`: every number on the slides mapped to its Key-numbers row and key; derived values marked.
- `qa/text_dump.txt`: full text and notes dump via python-pptx.

## Open items
See `qa/open_items.md`. Main ones: the `reference_decks/` folder wasn't supplied, so style comes from the measurements in the reference pack; confirm the talk date (shown as "Fall 2026"); and a few outline items had no source and were left off.
