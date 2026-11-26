# QBF-X2 carrier: native Altium Designer libraries

This folder holds Altium Designer's own binary library formats for every part on the QBF-X2 carrier board. The files
were written with **[altium-designer-mcp](https://github.com/embedded-society/altium-designer-mcp)** (v1.4.0). That
MCP server reads and writes Altium's OLE-format `.PcbLib`/`.SchLib` without Altium itself. It was driven over its
stdio MCP transport (JSON-RPC 2.0) by `build_altium_libs.py`.

| File | What it is |
|---|---|
| `QBFX2_Carrier.PcbLib` | 8 footprints. STEP models are **embedded** for the SMP, micro-D, 0603 R/C and the die/bond-pad footprint |
| `QBFX2_Carrier.SchLib` | 8 components, one per BOM line. Each has a footprint link and the parameters Value, Manufacturer, Manufacturer Part Number, MPN Status and BOM item |
| `QBFX2_Carrier.LibPkg` | Library package with both libraries. In Altium: *Project > Compile Integrated Library* gives `QBFX2_Carrier.IntLib` |
| `reports/altium_report.json` | The tool's validation results, the read-back comparison, and the component list |
| `reports/previews.txt` | The tool's ASCII renders of every footprint and symbol |

## Where the data comes from (no second, hand-made copy)

The libraries are converted from the board's own KiCad libraries: `../qbfx2.pretty`, `../qbfx2.kicad_sym`, the STEP
models in `../3dmodels`, and `../fab/qbfx2_carrier_bom.csv`. The Altium parts are therefore exactly the parts the
board was routed, DRC-checked and compared against.

**Footprints**
- Coordinates: KiCad's y-down coordinates are mirrored to Altium's y-up. Positions are in mm, and the visual rotation
  is kept.
- Pad shapes: rect → rectangle, circle → round, oval → oval.
- Pads and masks:
  - SMD pads go on *Top Layer*; plated and non-plated holes go on *Multi-Layer*.
  - Pads without paste in KiCad get a negative paste expansion, so they have no stencil opening.
  - Per-pad solder-mask margins are kept.
- Graphics layers: silkscreen → *Top Overlay*, courtyard → *Top Courtyard*, fab → *Top Assembly*.

**Symbols**
- KiCad mm are converted to Altium's 10-mil schematic units.
- A KiCad pin's connection point plus its angle (which points to the body) become an Altium body end plus an outward
  orientation.
- Pin types are mapped too, for example power_in → power.

## Checks (from the last run)

**Write and validate (the tool's `validate_library`)**
- `.PcbLib`: 0 errors. Three warnings, all intended:
  - the fiducial and the dowel hole have no pad designator, which is correct for those;
  - the SMP's four ground legs share designator `2`;
  - the micro-D's two shell lugs share `SH`.

  Altium joins pads that share a designator into one pin, which is what both connectors need.
- `.SchLib`: 0 errors, 0 warnings.

**Read-back round trip**
- Both libraries were read back through the tool. Every pad's position, size and hole matches the KiCad source to
  better than 10⁻³ mm (worst 10⁻⁶ mm).
- Every component has the right pin count, and all STEP models are present as embedded models.

**Local pad clearances**
- KiCad's per-pad clearances on the SMP signal pad (0.45 mm) and the fiducial (0.6 mm) have no Altium footprint
  field.
- Enter them as Altium clearance rules, scoped `InComponentClass`/`IsPad`; they are listed in `altium_report.json`
  under each footprint's notes.

## Using them in Altium

1. **Board and schematic:** *File > Import Wizard > KiCad Design Files*, using `../qbfx2_carrier.kicad_pro`.
   altium-designer-mcp writes libraries only, not `.PcbDoc`/`.SchDoc`, so the documents come in through Altium's KiCad
   importer.
2. **Library:** open `QBFX2_Carrier.LibPkg` and compile it to an IntLib, or use the two libraries directly.
3. **Managed components:** in the imported schematic, *Tools > Update From Libraries* (or *Component Links*) pointed at
   `QBFX2_Carrier`. Every component then carries its MPN and an embedded STEP model.
4. **Rules:** re-enter the design rules from `../README.md`, because KiCad's custom `.kicad_dru` rules are not
   translated. These are the CPW gap and width; the 8 differential pairs (`<name>_P` / `<name>_N`, define them in the
   differential-pair editor) with their routed width/gap (0.39 / 0.65 mm) and breakout width/gap at the die
   (0.29 / 0.21 mm); matched length within each pair (|L_P - L_N| <= 0.10 mm) and between A/B pairs (0.20 mm); and
   the two local pad clearances above.

Not tested here: opening the files in Altium Designer itself, which does not run on Linux. The tool's maintainers
verify the format against Altium in their CI. Here the evidence is the validator plus the exact read-back.

## PCB-editor views

`render_altium_style.py` draws the routed board in Altium's 2D colours: Top Layer red (GND pour darker),
Mid-Layer 2 (the In2 DC stripline) orange, Multi-Layer pads and vias silver, Top Overlay yellow, Top Solder purple and
the outline magenta. Net names are printed on the tracks and pads, pad numbers on the pads and designators in the
overlay colour. Every shape is read from `../qbfx2_carrier.kicad_pcb` through pcbnew. KiCad 7.0's bindings do not
wrap the `ERROR_LOC` argument of `TransformShapeToPolygon`, so the script rebuilds tracks, arcs, vias and silkscreen
from their primitives. Pads use `GetEffectivePolygon` and zones use their filled polygons.

| View | What it shows |
|---|---|
| `views/altium_style_board.png` | The whole board, with the inner GND planes hidden |
| `views/altium_style_die_window.png` | The die cavity, the 32 bond lands (numbers and nets; 8 P/N pairs on the 0.5 mm die pitch), the GCPW fan-out and the via fence |
| `views/altium_style_smp_launch.png` | The J1 SMP launch (TRAP_A0_P): centre land, ground legs, via cage, silkscreen designator and net |
| `views/altium_style_diff_pair.png` | Close-up of the ACC_A0 differential pair: both legs with their net names, the breakout at the die pad pitch, the concentric bends B1/B2, the opening to the routed spacing and the tuning bumps on the shorter leg next to each bend (call-outs from `../reports/build_model.json`) |
| `views/altium_style_dc_filters.png` | The 0603 RC filter bank between micro-D J11 and the gate and load lines |

The chip has its own views in the same colours: `../../circuits/views/altium_chip_*.png`.

## Rebuild

```bash
git clone https://github.com/embedded-society/altium-designer-mcp && cd altium-designer-mcp && cargo build --release
ALTIUM_MCP_BIN=$PWD/target/release/altium-designer-mcp python3 /path/to/qbf-x2/pcb/altium/build_altium_libs.py
```

`../export_carrier.sh` runs this step automatically when the binary exists.
