#!/usr/bin/env bash
# Reproduce every result, figure, circuit file and the paper. ~45 min on 4 CPU cores.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -q -r requirements.txt
cd simulations
python3 A_classical.py              # milestone A: classical circuit model             -> results/A_classical.json, fig01
python3 B_quantum.py                # milestone B: quantum scattering model            -> results/B_quantum.json, fig02-04, fig09
python3 C_gate.py                   # milestone C: entangling gate, robustness, optimum -> results/C_gate.json, fig05-08
python3 companions/c2_router.py     # device 2: coherent fluxon router (beam splitter used by D)
python3 companions/c1_bell_pair.py  # device 1: vortex Bell pair (uses ../quantum_chip/out/qfx_sim.json)
python3 companions/c3_mediator.py   # device 3: reusable mediator gate (negative result)
python3 companions/c4_reversible_cell.py   # device 4: reversible cell, energy recovery
python3 companions/c5_qec.py        # device 5: fluxon syndrome-extraction cycle
python3 D_feasibility.py            # milestone D: netlist, schematic, layout, energy -> results/D_feasibility.json, fig10, circuits/
cd ..
python3 -m pytest
(cd paper && pdflatex -interaction=nonstopmode main.tex >/dev/null && pdflatex -interaction=nonstopmode main.tex >/dev/null && echo "paper/main.pdf built")
