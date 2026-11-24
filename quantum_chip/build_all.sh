#!/usr/bin/env bash
# Rebuild the whole assembly from design_params.py. Each step reads only the previous steps' files.
#   ./build_all.sh            full pipeline incl. final renders (~25 min on 4 CPUs)
#   ./build_all.sh --quick    preview-quality renders
# Needs: python3 with klayout, matplotlib, (kqcircuits only for the legacy transmon die), gdstk, trimesh, scipy, pyyaml, cadquery-ocp, bpy (Blender 4.x/5.x module);
#        KiCad 7 (pcbnew python module + kicad-cli).
set -euo pipefail
cd "$(dirname "$0")"
python3 src/rfl_sim.py                # fluxon physics: ballistic LJJ + controlled barrier -> out/rfl_sim.json
python3 src/build_die.py              # RFL die (KLayout) -> out/quantum_die.gds, die_ports.json, die_cells.json
python3 src/preview_gds.py out/quantum_die.gds docs/die_preview.png "4750,6150,5250,6650" "3050,7450,3350,8400" "1550,5450,2100,5800"
# (legacy transmon die: python3 src/make_kqc_font.py && python3 src/build_die_transmon.py)
python3 src/build_pcb.py              # routed design -> rf_carrier_unfilled.kicad_pcb, pcb_model.json, rules
python3 src/finalize_pcb.py           # KiCad: zone fill, save rf_carrier.kicad_pcb, DRC report
mkdir -p out/gerbers out/svg
kicad-cli pcb export step --subst-models -f -o out/rf_carrier.step out/rf_carrier.kicad_pcb
kicad-cli pcb export gerbers -o out/gerbers/ -l F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts out/rf_carrier.kicad_pcb
kicad-cli pcb export drill -o out/gerbers/ out/rf_carrier.kicad_pcb
for L in F.Cu In2.Cu B.Cu; do kicad-cli pcb export svg --exclude-drawing-sheet --page-size-mode 2 -l $L,Edge.Cuts -o out/svg/$L.svg out/rf_carrier.kicad_pcb; done
python3 src/build_geometry.py         # GDS + KiCad -> per-layer meshes, out/assembly.glb, layer_manifest.json
python3 src/build_reports.py          # out/layer_stack.yaml, out/connections.json
python3 src/validate.py               # out/validation_report.json, docs/VALIDATION.md
python3 src/build_step.py && gzip -9 -c out/assembly.step > out/assembly.stpZ
python3 src/build_viewer.py           # out/interactive_3d_view.html (loads ./assembly.glb)
python3 src/render_blender.py -- ${1:-}   # Cycles renders -> renders/*.png, out/quantum_assembly.blend
