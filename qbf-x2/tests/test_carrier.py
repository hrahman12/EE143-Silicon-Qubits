"""Fast end-to-end test of the QBF-X2 carrier generator (pcb/).

The generator, zone fill + DRC and all checks run on a temporary copy of the generator sources, so the committed KiCad
project and fabrication outputs are not touched. Needs KiCad 7 (kicad-cli + the pcbnew module), cadquery-ocp and
shapely; the test is skipped when they are missing.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(ROOT, "pcb")
SOURCES = ("carrier_params.py", "build_carrier.py", "finalize_carrier.py", "check_carrier.py")


def _have_tools():
    for mod in ("pcbnew", "OCP", "shapely", "scipy"):
        try:
            __import__(mod)
        except Exception:
            return False
    return shutil.which("kicad-cli") is not None


@pytest.mark.skipif(not _have_tools(), reason="KiCad 7 / OCP / shapely not available")
def test_carrier_builds_drc_clean_and_passes_checks(tmp_path):
    work = tmp_path / "pcb"
    work.mkdir()
    for f in SOURCES:
        shutil.copy(os.path.join(PCB, f), work / f)
    shutil.copytree(os.path.join(PCB, "carrier_lib"), work / "carrier_lib",
                    ignore=shutil.ignore_patterns("__pycache__"))
    env = dict(os.environ, QBFX2_ROOT=ROOT, OMP_NUM_THREADS="1")
    for step in SOURCES[1:]:
        r = subprocess.run([sys.executable, step], cwd=work, env=env, capture_output=True, text=True, timeout=900)
        assert r.returncode == 0, f"{step} failed:\n{r.stdout[-4000:]}\n{r.stderr[-4000:]}"

    for f in ("qbfx2_carrier.kicad_pro", "qbfx2_carrier.kicad_sch", "qbfx2_carrier.kicad_pcb", "qbfx2_carrier.kicad_dru"):
        assert (work / f).stat().st_size > 1000, f
    drc = json.load(open(work / "reports" / "drc_summary.json"))
    assert drc["drc_violations"] == 0 and drc["unconnected_items"] == 0 and drc["footprint_errors"] == 0

    s = json.load(open(work / "reports" / "check_summary.json"))
    assert s["all_passed"], s
    assert s["sch_vs_pcb"]["mismatches"] == 0
    assert s["erc"]["issues"] == 0
    assert all(r["detected"] for r in s["drc_selftest"]["results"])
    assert abs(s["impedance"]["z_formula"] - 50.0) <= 2.5
    assert abs(s["impedance"]["z_fieldsolver"] - 50.0) <= 2.5
    pairs = {(p["a"], p["b"]): p["dL"] for p in s["lengths"]["pairs"]}
    assert set(pairs) == {("TRAP_A0", "TRAP_B0"), ("TRAP_A1", "TRAP_B1"), ("ACC_A0", "ACC_B0"), ("ACC_A1", "ACC_B1")}
    assert max(pairs.values()) <= 0.2
    for ch in s["filters"]["channels"]:
        if ch["kind"] == "gate":
            assert ch["f3db"] <= 10e3
        else:
            assert 10e6 <= ch["f3db_current"] <= 20e6 and ch["f3db_open"] >= 5e6

    # U1 pins follow the chip-to-board contract
    pads = json.load(open(os.path.join(ROOT, "circuits", "die_pads.json")))["pads"]
    model = json.load(open(work / "reports" / "build_model.json"))
    for p in pads:
        u1 = model["u1_pads"][str(p["id"])]
        assert u1["net"] == p["net"]
        die = (p["pad_center_um"][0] / 1000 - 5.0, p["pad_center_um"][1] / 1000 - 5.0)
        if p["outward"][0] == 0:        # N/S launchers: landing pad aligned in x (straight bond)
            assert abs(u1["pcb"][0] - die[0]) < 1e-6
        else:                           # E/W launchers: aligned in y
            assert abs(u1["pcb"][1] - die[1]) < 1e-6
