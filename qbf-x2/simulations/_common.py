"""Shared helpers for the simulation scripts: import path, output folders, JSON, plot style."""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
RESULTS = os.path.join(ROOT, "results")
FIGS = os.path.join(ROOT, "figures")
CIRCUITS = os.path.join(ROOT, "circuits")
for d in (RESULTS, FIGS, CIRCUITS):
    os.makedirs(d, exist_ok=True)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 150, "font.size": 9.5, "axes.titlesize": 10,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "figure.constrained_layout.use": True})
C_IND, C_MIX, C_TH, C_SIM = "#c2410c", "#1d4ed8", "#6b7280", "#111827"


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, complex):
        return dict(re=o.real, im=o.imag, abs=abs(o), arg=math.atan2(o.imag, o.real))
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return str(o)
    return o


def save_json(name: str, data: dict) -> str:
    path = os.path.join(RESULTS, name)
    data = dict(data)
    data["_generated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "w") as f:
        json.dump(_clean(data), f, indent=1)
    return path


def load_json(name: str) -> dict:
    with open(os.path.join(RESULTS, name)) as f:
        return json.load(f)


def savefig(fig, name: str) -> str:
    path = os.path.join(FIGS, name)
    fig.savefig(path)
    plt.close(fig)
    return path


def milestone(name: str, checks: list) -> dict:
    """checks: list of (description, passed: bool, detail). A milestone passes only if every check passes."""
    ok = all(bool(c[1]) for c in checks)
    print(f"\n=== Milestone {name}: {'PASS' if ok else 'NOT MET'} ===")
    for d, p, det in checks:
        print(f"  [{'x' if p else ' '}] {d}: {det}")
    return dict(milestone=name, passed=ok, checks=[dict(check=d, passed=bool(p), detail=det) for d, p, det in checks])
