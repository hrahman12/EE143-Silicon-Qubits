# Q4-FLUX: superconducting quantum die on a 6-layer RF carrier

A four-qubit, flux-tunable transmon die (KQCircuits → GDSII) wire-bonded into a red-mask, 6-layer Rogers RF carrier
(KiCad 7), on a gold-plated copper package. Every 3D layer is extruded from the exported CAD polygons, then
rendered in Blender Cycles and explorable in a browser. One parameter file drives the whole thing:
`src/design_params.py` → `./build_all.sh`.

![assembled](renders/assembled_chip.png)

## Deliverables

| Requested | File | Made by |
|---|---|---|
| quantum_die.gds | `out/quantum_die.gds` | KQCircuits 4.9 PCell `Q4FluxTransmon` (`src/build_die.py`), checked in KLayout (`docs/die_preview*.png`) |
| rf_carrier.kicad_pcb | `out/rf_carrier.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, Gerbers, drill, SVG) | generated S-expression, zones filled + DRC by KiCad 7 itself |
| assembly.step | `out/assembly.stpZ` (gzip STEP AP214, 28 named and coloured parts, true thicknesses) and `out/rf_carrier.step` (KiCad board body) | OpenCascade (`src/build_step.py`) |
| quantum_assembly.blend | `out/quantum_assembly.blend` | Blender 5.3 (bpy), one object per layer, grouped in collections; explode offsets stored as custom properties |
| layer_stack.yaml | `out/layer_stack.yaml` | `src/build_reports.py` |
| connections.json | `out/connections.json` | `src/build_reports.py` (from the KiCad routes, die ports and bond geometry) |
| assembled_chip.png | `renders/assembled_chip.png` | Cycles |
| red_pcb_view.png | `renders/red_pcb_view.png` | Cycles |
| exploded_layers.png | `renders/exploded_layers.png` | Cycles |
| internal_trace_cutaway.png | `renders/internal_trace_cutaway.png` | Cycles (stepped peel-back that exposes the In2 striplines) |
| wirebond_macro.png | `renders/wirebond_macro.png` | Cycles |
| (extra) qubit macro, technical CAD view | `renders/qubit_macro.png`, `renders/technical_cad_view.png` | Cycles |
| interactive_3d_view.html | `out/interactive_3d_view.html` + `out/assembly.glb` | three.js; real layer visibility, Fabrication/Engineering modes, explode, section cut, click-to-inspect |
| validation | `docs/VALIDATION.md`, `out/validation_report.json` | `src/validate.py`: **54 checks, 54 pass** |

Open the viewer by serving the folder (`cd out && python3 -m http.server`, then open `interactive_3d_view.html`);
opened straight from disk it asks you to pick `assembly.glb`.

## The hardware

**Die (10 × 10 mm, 525 µm high-ρ Si, 200 nm Al).** Four Swissmon transmons in a chain, each with a Manhattan-junction
SQUID (flux-tunable), so each qubit has an XY charge line and a Z flux line. Nearest neighbours share a floating CPW bus
coupler. Each qubit has its own λ/2 readout resonator (design 6.8 / 7.0 / 7.2 / 7.4 GHz, lengths from ε_eff = (ε_r+1)/2)
hanging off one probe line through an interdigital capacitor. Ten launchers: six north, two east, two west. CPWs are
10/6 µm (≈51 Ω), with Al airbridges tying the ground plane across lines.

**Carrier (40 × 40 mm, 1.496 mm, ENIG, red LPI mask).**

| Layer | Thickness | Job |
|---|---|---|
| F.Cu | 35 µm | GCPW drive + probe lines (w 0.43 / g 0.20 mm, 49.9 Ω), bond pads, exposed bond ring |
| RO4003C | 203 µm | |
| In1.Cu | 18 µm | solid GND |
| RO4450F | 200 µm | |
| In2.Cu | 18 µm | flux lines as stripline (w 0.19 mm, 49.3 Ω); they cross under the top-layer lines |
| RO4450F | 200 µm | |
| In3.Cu | 18 µm | solid GND |
| RO4003C | 508 µm | |
| In4.Cu | 18 µm | GND reference for the bottom routing |
| RO4003C | 203 µm | |
| B.Cu | 35 µm | short GCPW stubs to the bottom SMPs, GND pour |

Blind vias (0.15 mm) are used only where a flux line changes layer: F.Cu→In2 next to its bond pad and In2→B.Cu next
to its SMP. No buried vias: no route needs an inner-to-inner transition. 324 through vias stitch the grounds, fenced
at 1 mm pitch along every RF line.

**Package.** The die sits on GE varnish on a pedestal of the gold-plated copper base that rises through the 10.3 mm
PCB window, so the die surface is flush with the PCB copper. 20 Al wedge bonds carry signals (2 per line) and 67 more
tie the die ground to the ENIG ring. Six edge-launch SMAs (drive, probe) on top, four vertical SMPs (flux) underneath
through holes in the base, four M2.5 screws.

**Signal path (every net is listed in full in `connections.json`):**
SMA/SMP → solder joint → GCPW (or B.Cu stub → blind via → In2 stripline → blind via) → ENIG bond pad →
2 × Al wire bond → Al launcher pad → on-chip CPW → charge line / flux line / probe line → qubit.

## Engineering vs fabrication colours

Fabrication mode uses physical materials: copper, ENIG gold, red mask (darker over laminate and brighter over copper,
so traces read through it), Si, Al. Engineering mode is a convention: top copper red, In2 green, bottom blue, planes
translucent, vias yellow (through) / magenta and cyan (blind). The red is a display colour; the metal is copper.

## What is not settled (read before fabricating)

- **No EM simulation was run.** Resonator lengths come from a closed-form ε_eff; qubit frequency, E_J/E_C, couplings
  and package/box modes are unverified. Run Sonnet, HFSS or Palace on `quantum_die.gds` and the carrier first.
- **Line impedances** use closed-form GCPW/stripline formulas that ignore the solder mask over the lines. Many
  cryogenic carriers leave RF lines unmasked; the mask here follows the requested look.
- **ENIG contains nickel**, which is magnetic and lossy near qubits. For a real cryogenic build use a Ni-free finish
  (immersion silver or direct gold) and a non-magnetic base finish.
- **Connectors are generic**: footprints and 3D bodies are representative, not vendor parts. Swap in the real part's
  footprint and STEP model before ordering.
- **Fab-house inputs still needed**: stackup confirmation and impedance-control tolerance, blind-via aspect ratio
  approval (0.15 mm drill through 0.44 mm), via fill/tenting choice, panelisation, edge plating at the SMA edges.
- **Display exaggeration**: films under 3 µm are drawn thicker in the GLB and .blend so they can be seen. `assembly.stpZ`
  uses the true thicknesses. XY geometry is never changed.
- KQC's vortex-pinning ground grid is turned off (it would add ~250k holes to every mesh). Turn on `with_grid` for tape-out.
- Request wording said "fluxon"; the spec asked for SQUID transmons, so the qubits are flux-tunable transmons. A fluxonium
  variant would swap the Swissmon element for a junction-array qubit.

## Further reading

- S. Huang et al., "Microwave Package Design for Superconducting Quantum Processors", PRX Quantum 2, 020306 (2021), arXiv:2012.01438.
- "Identification and Mitigation of Conducting Package Losses for Quantum Superconducting Devices", arXiv:2304.08629 (2023).
- "High-Throughput Microwave Package for Precise Superconducting Device Measurement", arXiv:2512.18198 (2025).

## Tools

KQCircuits 4.9 + KLayout 0.30 (die), KiCad 7.0 (board, DRC, Gerber, STEP), OpenCascade/OCP (assembly STEP),
trimesh (GLB), Blender 5.3 Cycles via `bpy` (renders), three.js 0.160 (viewer). The KQC pip wheel is missing its label font;
`src/make_kqc_font.py` regenerates it.
