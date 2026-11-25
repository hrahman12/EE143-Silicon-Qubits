"""Native Altium libraries of the carrier (pcb/altium), written with altium-designer-mcp. Skipped when the tool's
binary is not built (it is an external project: https://github.com/embedded-society/altium-designer-mcp)."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
BIN = os.environ.get("ALTIUM_MCP_BIN", "/home/user/embedded-society/altium-designer-mcp/target/release/altium-designer-mcp")


@pytest.mark.skipif(not os.access(BIN, os.X_OK), reason="altium-designer-mcp binary not built")
def test_altium_libraries_write_validate_and_round_trip():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "pcb", "altium", "build_altium_libs.py"), "--bin", BIN],
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    rep = json.load(open(os.path.join(ROOT, "pcb", "altium", "reports", "altium_report.json")))
    s = rep["summary"]
    assert s["round_trip_footprints_ok"] and s["round_trip_symbols_ok"]
    assert s["validation_errors"] == {"pcblib": 0, "schlib": 0}
    # every BOM line is a component, and every footprint of the board is in the PcbLib
    assert s["symbols"] == 8 and s["footprints"] == 8
    steps = {f["name"]: f["step_model_embedded"] for f in rep["footprints"]}
    assert all(steps[n] for n in ("SMP_Amphenol_SMP-MSLD-PCS-NM", "MicroD_15P_Glenair_MWDM2L-15PCBRP",
                                  "R_0603_1608Metric", "C_0603_1608Metric", "QBFX2_DIE_BONDPADS"))
