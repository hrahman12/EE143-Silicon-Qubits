#!/usr/bin/env python3
"""Fill every zone with KiCad's own filler, save the board, and write the DRC report (pcbnew), as QFX-1's
finalize_pcb.py does. Writes reports/drc_report.txt (KiCad's text report) and reports/drc_summary.json.
Exit status 1 if there is any DRC violation or unconnected item."""
import json
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import carrier_params as P  # noqa: E402

NAME = P.PROJECT["name"]
board_path = os.path.join(HERE, f"{NAME}.kicad_pcb")
rep = os.path.join(HERE, "reports", "drc_report.txt")

b = pcbnew.LoadBoard(board_path)
print("loaded:", len(b.GetFootprints()), "footprints,", len(b.GetTracks()), "tracks/vias,",
      b.GetCopperLayerCount(), "copper layers,", b.GetNetCount(), "nets")
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(board_path)
b2 = pcbnew.LoadBoard(board_path)
ok = pcbnew.WriteDRCReport(b2, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
txt = open(rep).read()
viol = int(re.search(r"Found (\d+) DRC violations", txt).group(1))
unc = int(re.search(r"Found (\d+) unconnected pads", txt).group(1))
fpe = int(re.search(r"Found (\d+) Footprint errors", txt).group(1))
kinds = {}
for m in re.finditer(r"^\[(\w+)\]: (.*)$", txt, re.M):
    kinds.setdefault(m.group(1), [0, m.group(2)])
    kinds[m.group(1)][0] += 1
sev = {}
for m in re.finditer(r"Severity: (\w+)", txt):
    sev[m.group(1)] = sev.get(m.group(1), 0) + 1
summary = dict(report=os.path.relpath(rep, HERE), drc_violations=viol, unconnected_items=unc, footprint_errors=fpe,
               by_severity=sev, by_type={k: v[0] for k, v in kinds.items()},
               examples={k: v[1] for k, v in kinds.items()}, kicad=pcbnew.Version(), written=bool(ok))
json.dump(summary, open(os.path.join(HERE, "reports", "drc_summary.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
sys.exit(0 if (viol == 0 and unc == 0 and fpe == 0) else 1)
