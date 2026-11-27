#!/usr/bin/env python3
"""Package the committed QBF-X2 project into one zip, to hand to a reviewer (human or AI).

The bundle holds:
  START_HERE.md          the orientation file (moved from qbf-x2/ to the bundle root)
  BUNDLE_MANIFEST.json   commit, branch, and every file with its size and sha256
  qbf-x2/                exactly the files committed at HEAD
  quantum_chip/          the two files QBF-X2 reads from the earlier QFX-1 project

It refuses to run on uncommitted changes, so a bundle always matches a commit. File times are set to the commit
time, so the same commit gives the same archive.

    python3 tools/make_bundle.py        # -> dist/QBF-X2_bundle_<commit date>_<hash>.zip
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # qbf-x2/
SUPPORT = ["quantum_chip/out/qfx_sim.json",   # companions/c1_bell_pair.py
           "quantum_chip/src/rf_calc.py"]     # pcb/build_carrier.py, pcb/check_carrier.py (CPW impedance formula)
STORED = {".png", ".jpg", ".jpeg", ".pdf", ".zip", ".gz", ".stpz", ".glb"}   # already compressed


def git(*args: str, cwd: str = PROJ) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def main() -> None:
    ap = argparse.ArgumentParser(description="Package the committed QBF-X2 project into one zip.")
    ap.add_argument("--out", default=os.path.join(PROJ, "dist"), help="output folder (default: qbf-x2/dist)")
    ap.add_argument("--allow-dirty", action="store_true", help="bundle the working tree despite uncommitted changes")
    a = ap.parse_args()

    top = git("rev-parse", "--show-toplevel").strip()
    proj = os.path.relpath(PROJ, top)
    dirty = git("status", "--porcelain", "--untracked-files=no", "--", proj, *SUPPORT, cwd=top).strip()
    if dirty and not a.allow_dirty:
        sys.exit(f"uncommitted changes; commit them first (or pass --allow-dirty):\n{dirty}")
    missing = [s for s in SUPPORT if not os.path.isfile(os.path.join(top, s))]
    if missing:
        sys.exit(f"support files missing: {missing}")

    commit = git("rev-parse", "HEAD").strip()
    ctime = int(git("log", "-1", "--format=%ct").strip())
    stamp = time.gmtime(ctime)
    name = f"QBF-X2_bundle_{time.strftime('%Y-%m-%d', stamp)}_{commit[:7]}"
    files = sorted(f for f in git("ls-files", "-z", "--", proj, cwd=top).split("\0") if f)

    os.makedirs(a.out, exist_ok=True)
    zpath = os.path.join(a.out, name + ".zip")
    entries = []
    with zipfile.ZipFile(zpath, "w") as z:
        def add(arc: str, data: bytes, mode: int = 0o644) -> None:
            zi = zipfile.ZipInfo(f"{name}/{arc}", date_time=stamp[:6])
            zi.external_attr = mode << 16
            stored = os.path.splitext(arc)[1].lower() in STORED
            zi.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            z.writestr(zi, data, compresslevel=None if stored else 9)

        for f in files + SUPPORT:
            src = os.path.join(top, f)
            with open(src, "rb") as fh:
                data = fh.read()
            arc = "START_HERE.md" if f == f"{proj}/START_HERE.md" else f
            add(arc, data, 0o755 if os.access(src, os.X_OK) else 0o644)
            entries.append({"path": arc, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        manifest = {
            "bundle": name,
            "project": "QBF-X2: a collision entangling gate between two flying quantum fluxons "
                       "(theory, simulation and design; not fabricated or measured)",
            "read_first": "START_HERE.md",
            "git_commit": commit,
            "git_branch": git("rev-parse", "--abbrev-ref", "HEAD").strip(),
            "commit_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", stamp),
            "uncommitted_changes": bool(dirty),
            "contents": {
                "START_HERE.md": "orientation; moved here from qbf-x2/START_HERE.md",
                "qbf-x2/": "the project, every file committed at git_commit",
                "quantum_chip/": "two files from the earlier QFX-1 project that QBF-X2 reads (" + ", ".join(SUPPORT) + ")",
            },
            "files": len(entries),
            "total_bytes": sum(e["bytes"] for e in entries),
            "entries": entries,
        }
        add("BUNDLE_MANIFEST.json", (json.dumps(manifest, indent=1, ensure_ascii=False) + "\n").encode())
    print(f"{zpath}  {os.path.getsize(zpath) / 1048576:.1f} MB  {len(entries)} files + manifest")


if __name__ == "__main__":
    main()
