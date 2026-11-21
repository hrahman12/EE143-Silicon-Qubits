# Reference style (measured from the 30 EE143 tutorial decks, python-pptx + LibreOffice renders)

| Deck (top by pictures / charts) | Slides | Pics | Native charts | Words/slide | Picture area |
|---|---|---|---|---|---|
| DMD (Ferrell) | 16 | 26 | 0 | 37 | 37% |
| Superconducting Qubit Fab | 27 | 34 | 0 | 31 | 32% |
| Ziggy Gardiner, Micro Energy Harvesters | 22 | 24 | 0 | 30 | 37% |
| Li-Chun Lin, Moore's Law | 12 | 12 | 0 | 31 | 53% |
| Silicon Photonics | 39 | 41 | 0 | 16 | 29% |
| Sela Murphy, ALD | 15 | 19 | 0 | 31 | 33% |
| How a CMOS Image Sensor Pixel Is Made | 16 | 22 | 0 | 113 | 4% |

Findings:
- **No deck in the folder uses a native chart.** All 30 paste plots as images. Our deck uses native PowerPoint charts (column, bar on a log axis, line, scatter, 100% stacked bar, area) plus coded charts (dumbbell, dot plot with error bars, floating range, log dot plot, filled Gaussian profiles, heatmap, 3D surface).
- Best visual moves we adopted:
  - DMD: one material legend on every cross-section, a step tracker, a "why not the usual process" table.
  - SC qubit: one fab step per slide.
  - MBE: atom-level diagrams.
  - 4-point probe: derive the equations step by step.
  - Moore's Law: log-scale trend chart, timeline cards.
  - Ziggy: 3D surface.
  - ALD: pros/cons cards, linear growth plots.
- Slide size: 10 × 5.625 in (22 of 30 decks); 13.33 × 7.5 in for the rest. We use 10 × 5.625.
- Words per slide: median ≈31. Our content slides target 25–45.
- Titles: short, top-left, bold. Source lines bottom-left. Slide number bottom-right (DMD).
