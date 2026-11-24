#!/usr/bin/env bash
# Rebuild the QBF-X2 carrier from scratch: KiCad project, checks, fabrication and assembly outputs.
#   ./export_carrier.sh            everything (about 2-3 min on one CPU, plus the 3D render)
#   ./export_carrier.sh --no-render  skip the Blender render (keeps the existing PNGs)
# Needs KiCad 7.0.x (kicad-cli + pcbnew python module), python3 with shapely, numpy, pillow, pypdf, scipy, cadquery-ocp;
# poppler-utils (pdftoppm); optionally the bpy module (Blender 4.x/5.x) for the 3D render.
set -euo pipefail
cd "$(dirname "$0")"
PCB=qbfx2_carrier.kicad_pcb
SCH=qbfx2_carrier.kicad_sch
export OMP_NUM_THREADS=2   # keep CPU use moderate (shared machine)

KEEP=""
if [[ "${1:-}" == "--no-render" && -n "$(ls fab/previews/render_3d_*.png 2>/dev/null)" ]]; then
  KEEP=$(mktemp -d); cp fab/previews/render_3d_*.png "$KEEP"/     # keep the previous renders
fi
rm -rf fab reports
mkdir -p fab/gerbers fab/drill fab/assembly fab/previews reports
[[ -n "$KEEP" ]] && cp "$KEEP"/*.png fab/previews/ && rm -rf "$KEEP"

echo "== 1/5 generate the KiCad project"
python3 build_carrier.py > reports/build.log 2>&1 || { tail -30 reports/build.log; exit 1; }
grep -E "^board written|^  [A-Z]" reports/build.log

echo "== 2/5 zone fill + DRC (pcbnew)"
python3 finalize_carrier.py > reports/finalize.log 2>&1 || { cat reports/finalize.log; exit 1; }
grep -E '"drc_violations"|"unconnected_items"|"footprint_errors"' reports/drc_summary.json

echo "== 3/5 checks"
python3 check_carrier.py | tee reports/check.log

echo "== 4/5 fabrication + assembly exports (kicad-cli $(kicad-cli version))"
kicad-cli pcb export gerbers --use-drill-file-origin --subtract-soldermask \
  -l F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts,Dwgs.User \
  -o fab/gerbers/ "$PCB" > reports/gerbers.log
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th --drill-origin plot \
  --excellon-zeros-format decimal --generate-map --map-format pdf -o fab/drill/ "$PCB" > reports/drill.log
kicad-cli pcb export pos --format csv --units mm --side both --use-drill-file-origin \
  -o fab/assembly/qbfx2_carrier-pos.csv "$PCB" > reports/pos.log
kicad-cli sch export pdf -o fab/qbfx2_carrier-schematic.pdf "$SCH" > /dev/null
kicad-cli sch export netlist --format kicadsexpr -o fab/qbfx2_carrier.net "$SCH" > /dev/null
kicad-cli pcb export pdf --include-border-title --black-and-white -l Edge.Cuts,F.Fab,Cmts.User \
  -o fab/qbfx2_carrier-assembly.pdf "$PCB" > /dev/null
kicad-cli pcb export step --force --drill-origin -o fab/qbfx2_carrier.step "$PCB" > reports/step.log 2>&1
grep -E "created|Error" reports/step.log || true
python3 make_outputs.py all

echo "== 5/5 3D render"
if [[ "${1:-}" != "--no-render" ]]; then
  if python3 -c "import bpy" 2>/dev/null; then
    python3 render_3d.py > reports/render.log 2>&1 && tail -3 reports/render.log || { tail -20 reports/render.log; exit 1; }
  else
    echo "bpy not available: 3D render skipped"
  fi
fi
python3 make_outputs.py manifest
python3 make_readme.py
rm -f qbfx2_carrier.kicad_prl   # pcbnew's local UI-state file, not part of the design
python3 -c "import json; s=json.load(open('reports/check_summary.json')); print('ALL CHECKS PASSED' if s['all_passed'] else 'CHECKS FAILED'); raise SystemExit(0 if s['all_passed'] else 1)"
