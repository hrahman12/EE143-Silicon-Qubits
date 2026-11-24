"""QBF-X2 row-block layout (gdstk), drawn to scale from the architecture and sized by EM extraction.

Process and layers (rule deck: hardware/drc.py)
    1/0  NB    150 nm Nb: ground plane, inner ground strips between rows, the low-g ends of the coupler strips,
                control/flux/gate lines (CPW in the ground plane)
    2/0  GRAL  20 nm granular Al: rail inductors, load and catcher loops
    3/0  AL1   30 nm Al bottom electrode: rail node pads, junction fingers, bottom capacitor plates, island bottoms
    4/0  AL2   30 nm Al top electrode: junction fingers and return leads, coupler strips, top capacitor plates,
               island tops, ground contacts, crossover straps
    6/0  DIEL  100 nm SiNx crossover dielectric between AL1 and AL2 (coupling capacitors, island shunts, crossings)
    10/0 TEXT  labels
Every AL1 & AL2 overlap without DIEL is a tunnel junction (rail or middle-rail target area) or a contact
(>= 1 um^2); with DIEL it is a capacitor or a crossing.

Rows (top to bottom) D_A, A0, A1, B1, B0, D_B, 10 um apart. Each rail node is an AL1 pad on the row centre line,
joined to the next by a granular-Al line; one junction rung per 2-um cell goes to the row's return: the ground edge
(plain cells), the coupler strip (gate and dummy couplers) or a middle-rail island (beam splitters), exactly as in
hardware/netlist.py. The ground-edge gap on the free side of each rail is the node-capacitance trim; the strip width
sets L_s (k); the crossover overlap sets C_c; the island shunt overlap sets C_M. All of them are solved from the
architecture targets by extract.size_layout() (periodic boundary-element solves) and cached in
circuits/layout_sizing.json keyed by the targets, so a change of targets re-sizes the layout on the next build.
"""
from __future__ import annotations

import hashlib
import json
import math
import os

import gdstk
import numpy as np

from hardware.architecture import Architecture, jj_area_for
from hardware.netlist import PAIRS, ROWS, QUBIT_ROWS, _env, _in_section

L_NB, L_GRAL, L_AL1, L_AL2, L_CU, L_DIEL, L_TXT = (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (10, 0)
LAYERS = dict(NB=L_NB, GRAL=L_GRAL, AL1=L_AL1, AL2=L_AL2, DIEL=L_DIEL, TEXT=L_TXT)

# ---------------------------------------------------------------- fixed geometry (um)
ROW_PITCH = 10.0                 # rail-to-rail distance
W_PAD = 0.35                     # node pad width (AL1)
W_PAD_STACK = 0.70               # pad width of coupler 'plate' nodes (AL1 + AL2 stack >= 1 um^2)
W_GRAL = 0.25                    # granular-Al line width
GRAL_OV = 0.20                   # granular Al under the pads at each end (contact)
JJ_A = 0.20                      # AL1 finger width at the rail junction
JJ_AM = 0.15                     # AL1 finger width at the middle-rail junction
J0 = 0.45                        # junction centre from the pad edge
E1 = 0.10                        # AL1 finger beyond the AL2 bar / AL2 bar beyond the AL1 finger
X_JJ = -0.55                     # rung AL1 finger centre, relative to the node
X_RET = 0.05                     # AL2 return lead centre
W_RET = 0.20                     # AL2 return lead width
S_RET = 1.20                     # pad edge to ground edge on the return side (plain cells)
CONTACT = (1.0, 1.1)             # AL2-on-NB ground contact pad (x, y): 1.1 um^2
X_CAP = 0.60                     # coupling-capacitor leads, relative to the node
W_CL = 0.15                      # AL1 crossing lead / bottom plate width (crossing role)
DIEL_ENC = 0.25                  # dielectric enclosure of AL1 & AL2 overlaps (rule 0.20)
ISL_W, ISL_H = 0.70, 1.50        # middle-rail island stack (AL1 + AL2): 1.05 um^2
MARGIN_X = 160.0                 # block margin left/right (fan-out of control, flux, gate and readout lines)
MARGIN_Y = 120.0                 # block margin top/bottom
CPW_W, CPW_G = 2.0, 2.0          # in-block control-line CPW (NB), tapered to the die CPW by the floorplan
PORT_PITCH = 20.0


def rail_y(row: str, y_top: float) -> float:
    return y_top - ROWS.index(row) * ROW_PITCH


# ====================================================================================================================
# geometry container
# ====================================================================================================================
class Geo:
    """rectangles with layer, net and role. net: node label for extraction; for granular-Al inductors a tuple
    (net_a, net_b) (linear potential between the two nodes)."""

    def __init__(self):
        self.rects = []          # (layer_key, x1, y1, x2, y2, net, role)
        self.labels = []
        self.ports = []

    def add(self, layer, x1, y1, x2, y2, net=None, role=""):
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        if x2 - x1 > 1e-9 and y2 - y1 > 1e-9:
            self.rects.append((layer, float(x1), float(y1), float(x2), float(y2), net, role))

    def window(self, x0, x1):
        """rectangles intersecting [x0, x1), clipped"""
        out = []
        for (ly, a, b, c, d, net, role) in self.rects:
            if c <= x0 or a >= x1:
                continue
            out.append((ly, max(a, x0), b, min(c, x1), d, net, role))
        return out


# ====================================================================================================================
# cell plan: what every (row, n) is, from the architecture and the netlist rules
# ====================================================================================================================
def mirrored(row: str) -> bool:
    return row.startswith("B") or row == "D_B"


def return_kind(arch, row, n):
    """'S' (coupler strip), 'M' (beam-splitter island) or 'G' (ground): same rule as netlist.build"""
    qubit = "A" if row in QUBIT_ROWS["A"] else "B" if row in QUBIT_ROWS["B"] else None
    if _env(arch, n) > 0:
        return "S"
    m = mirrored(row)
    if qubit and (_in_section(arch, n, "BS_prep", m) or _in_section(arch, n, "BS_analysis", m)):
        return "M"
    return "G"


RUNG_DIR = {"D_A": {"S": -1, "M": -1, "G": -1}, "A0": {"S": +1, "M": -1, "G": -1},
            "A1": {"S": -1, "M": +1, "G": +1}, "B1": {"S": +1, "M": -1, "G": -1},
            "B0": {"S": -1, "M": +1, "G": +1}, "D_B": {"S": +1, "M": +1, "G": +1}}
PAIR_OF = {row: key for key, (a, b) in PAIRS.items() for row in (a, b)}
# coupler roles: 'plate' rows get an AL1/AL2 pad stack and an AL2 top-plate lead; 'cross' rows send an AL1 lead under
# the strip to a bottom plate on the partner's side. Dummies mirror the gate coupler (A0 ~ A1, B0 ~ B1).
CPL_ROLE = {"A1": "plate", "B1": "cross", "A0": "plate", "D_A": "cross", "B0": "cross", "D_B": "plate"}


def bs_sections(arch):
    """list of (qubit, section, [cells])"""
    N = arch.n_cells
    out = []
    for q in ("A", "B"):
        for sec in ("BS_prep", "BS_analysis"):
            ns = [n for n in range(N) if _in_section(arch, n, sec, q == "B")]
            if ns:
                out.append((q, sec, ns))
    return out


def launcher_targets(arch):
    """per launch row: {'trap': array M_pH per rail cell index n (absolute), 'acc': ...} or {} if no launcher"""
    try:
        lv = arch.element_values().get("launcher", {})
    except Exception:
        return {}
    if not lv or "trap_line" not in lv:
        return {}
    N = arch.n_cells
    out = {}
    for row in lv.get("rows", []):
        m = row in lv.get("mirrored_rows", [])
        d = {}
        for key, tag in (("trap_line", "trap"), ("accelerator_line", "acc")):
            M = np.zeros(N - 1)
            for c, v in zip(lv[key]["cells"], lv[key]["M_pH"]):
                n = N - 2 - c if m else c                  # cell c from the launch end -> rail cell index n
                if 0 <= n < N - 1:
                    M[n] = v
            d[tag] = M
            d[tag + "_I_uA"] = lv[key]["I_uA"]
        out[row] = d
    return out


# ====================================================================================================================
# targets and sizing cache
# ====================================================================================================================
def targets(arch: Architecture) -> dict:
    ev = arch.element_values()
    rj, mj = ev["rail_junction"], ev["middle_rail_junction"]
    t = dict(pitch_um=arch.rail.pitch_um, N=arch.n_cells, L_pH=ev["rail_inductor"]["L_nH"] * 1e3,
             C_node_fF=rj["C_fF"], Cj_fF=rj["Cj_fF"], shunt_fF=rj["shunt_fF"], C_c_fF=ev["coupler_capacitor"]["C_c_fF"],
             L_s_pH=ev["coupler_shared_inductor"]["L_s_pH"], k=arch.k, c=arch.c,
             A_jj_um2=rj["area_um2"], A_jjM_um2=mj["area_um2"], C_M_fF=mj["C_fF"], CjM_fF=mj["Cj_fF"],
             shunt_M_fF=mj["shunt_fF"], EJ_M_GHz=mj["EJ_GHz"], EC_M_GHz=mj["EC_GHz"], E_S_GHz=mj["E_S_GHz"],
             sections=arch.sections())
    lt = launcher_targets(arch)
    t["launcher"] = {r: {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in d.items()} for r, d in lt.items()}
    return t


def _key(t: dict) -> str:
    from hardware import extract as EX
    blob = json.dumps(dict(t=t, mat=EX.MATERIALS, geo=[ROW_PITCH, W_PAD, W_PAD_STACK, W_GRAL, GRAL_OV, JJ_A, JJ_AM, J0,
                                                          E1, X_JJ, X_RET, W_RET, S_RET, CONTACT, X_CAP, W_CL,
                                                          DIEL_ENC, ISL_W, ISL_H, EX.SIZING_VERSION]),
                      sort_keys=True, default=float)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


SIZING_CACHE = os.path.join(os.path.dirname(__file__), "..", "..", "circuits", "layout_sizing.json")


def get_sizing(arch: Architecture, cache_path: str | None = None, force: bool = False) -> dict:
    from hardware import extract as EX
    t = targets(arch)
    key = _key(t)
    path = os.path.abspath(cache_path or SIZING_CACHE)
    if not force and os.path.exists(path):
        try:
            s = json.load(open(path))
            if s.get("key") == key:
                return s
        except Exception:
            pass
    s = EX.size_layout(arch, t)
    s["key"] = key
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(s, open(path, "w"), indent=1)
    except OSError:
        pass
    return s
