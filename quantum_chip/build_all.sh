#!/usr/bin/env bash
# Rebuild the whole QFX-1 quantum-fluxon assembly from design_params.py. Each step reads only the previous steps' files.
#   ./build_all.sh            full pipeline incl. final renders (~30 min on 4 CPUs)
#   ./build_all.sh --quick    preview-quality renders
# Needs: python3 with klayout, matplotlib, scipy, numpy, gdstk, trimesh, pyyaml, cadquery-ocp, bpy (Blender 4.x/5.x module);
#        KiCad 7 (pcbnew python module + kicad-cli).
# ACTIVE_DIE in src/design_params.py selects the die: "QFX" (quantum fluxon, default), "RFL" (reversible fluxon logic).
set -euo pipefail
cd "$(dirname "$0")"
DIE=$(python3 -c "import sys; sys.path.insert(0,'src'); from design_params import ACTIVE_DIE; print(ACTIVE_DIE)")
if [ "$DIE" = "QFX" ]; then
  python3 src/qfx_sim.py              # quantum fluxon physics: string-method spectrum, kick gate, readout -> out/qfx_sim.json
  python3 src/build_die_qfx.py        # QFX-1 die (KLayout) -> out/quantum_die.gds, die_ports.json, die_cells.json
  python3 src/preview_gds.py out/quantum_die.gds docs/die_preview.png "4650,5050,5350,5400" "4700,5100,4900,5300" "3050,8150,3350,8350" "4100,4950,5900,5700"
else
  python3 src/rfl_sim.py              # classical fluxon physics: ballistic LJJ + controlled barrier -> out/rfl_sim.json
  python3 src/build_die.py            # RFL die (KLayout) -> out/quantum_die.gds, die_ports.json, die_cells.json
  python3 src/preview_gds.py out/quantum_die.gds docs/die_preview.png "4750,6150,5250,6650" "3050,7450,3350,8400" "1550,5450,2100,5800"
fi
# (legacy transmon die: python3 src/make_kqc_font.py && python3 src/build_die_transmon.py)
python3 src/build_pcb.py              # routed carrier -> rf_carrier_unfilled.kicad_pcb, pcb_model.json, rules
python3 src/finalize_pcb.py           # KiCad: zone fill, save rf_carrier.kicad_pcb, DRC report
mkdir -p out/gerbers out/svg
kicad-cli pcb export step --subst-models -f -o out/rf_carrier.step out/rf_carrier.kicad_pcb
kicad-cli pcb export gerbers -o out/gerbers/ -l F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts out/rf_carrier.kicad_pcb
kicad-cli pcb export drill -o out/gerbers/ out/rf_carrier.kicad_pcb
for L in F.Cu In2.Cu B.Cu; do kicad-cli pcb export svg --exclude-drawing-sheet --page-size-mode 2 -l $L,Edge.Cuts -o out/svg/$L.svg out/rf_carrier.kicad_pcb; done
python3 src/build_geometry.py         # GDS + KiCad -> per-layer meshes, out/assembly.glb, layer_manifest.json
python3 src/build_reports.py          # out/layer_stack.yaml, out/connections.json
python3 src/validate.py               # out/validation_report.json, docs/VALIDATION.md (exits non-zero on any FAIL)
python3 src/build_step.py && gzip -9 -c out/assembly.step > out/assembly.stpZ
python3 src/build_viewer.py           # out/interactive_3d_view.html (loads ./assembly.glb)
python3 src/render_blender.py -- ${1:-}   # Cycles renders -> renders/*.png, out/quantum_assembly.blend
