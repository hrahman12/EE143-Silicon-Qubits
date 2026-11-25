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
W_PAD_CROSS = 0.25               # pad width of coupler 'cross' nodes (= granular-Al width: least capacitance)
W_GRAL = 0.25                    # granular-Al line width
GRAL_OV = 0.20                   # granular Al under the pads at each end (contact)
JJ_A = 0.20                      # AL1 finger width at the rail junction
JJ_AM = 0.11                     # AL1 finger width at the middle-rail junction (0.0129 um^2: 0.110 x 0.118)
J_RET = 0.65                     # junction centre from the return edge (the long rung lead is at node potential)
J_RET_BS = 0.75                  # same, beam-splitter rungs (from the island edge; >= 0.5 um from the island contact)
W_STRIP_X = 0.15                 # minimum strip width where the crossing lead passes under it (neck)
L_NECK = 0.55                    # neck length (crossing lead 0.15 + 2 x 0.20)
BRANCH = True                    # crossing-role capacitor lead branches off the rung finger (no second long lead)
E1 = 0.10                        # AL1 finger beyond the AL2 bar / AL2 bar beyond the AL1 finger
X_JJ = -0.55                     # rung AL1 finger centre, relative to the node
X_RET = 0.05                     # AL2 return lead centre
W_RET = 0.20                     # AL2 return lead width
S_RET = 1.40                     # pad edge to ground edge on the return side (plain cells)
S_FREE = 1.80                    # pad edge to ground edge on the free side (room for the trim capacitor)
S_FREE_L = 1.00                  # free gap of the launch row and of the row facing its control-line strip
X_TRIM = 0.05                    # trim capacitor on the free side (coupler, beam splitter), relative to the node
X_TRIM_R = 0.62                  # trim capacitor on the return side (plain cells), relative to the node
TRIM_WB, TRIM_WT = 0.50, 0.30    # trim AL1 plate width / AL2 ground-plate width (x)
LINE_SEP = 1.00                  # trap / accelerator line centre-to-centre distance in their shared slot
CONTACT = (1.0, 1.1)             # AL2-on-NB ground contact pad (x, y): 1.1 um^2
X_CAP = 0.60                     # coupling-capacitor leads, relative to the node
W_CL = 0.15                      # AL1 crossing lead / bottom plate width (crossing role)
DIEL_ENC = 0.25                  # dielectric enclosure of AL1 & AL2 overlaps (rule 0.20)
ISL_W, ISL_H = 0.70, 1.50        # middle-rail island stack (AL1 + AL2): 1.05 um^2
MARGIN = 120.0                   # block margin on all sides (fan-out of control, flux, gate and readout lines);
MARGIN_X = MARGIN_Y = MARGIN     # node 0 is at x = MARGIN, the rail of D_A at y = H - MARGIN (D_feasibility previews)
CPW_W, CPW_G = 0.5, 0.5          # in-block line CPW (NB): same as the in-strip lines; the floorplan tapers it
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
             shunt_M_fF=mj["shunt_fF"], C_island_geo_fF=mj.get("C_island_geo_fF", mj["shunt_fF"]),
             C_net_M_fF=mj.get("C_network_fF", 0.0), EJ_M_GHz=mj["EJ_GHz"], EC_M_GHz=mj["EC_GHz"], E_S_GHz=mj["E_S_GHz"],
             sections=arch.sections())
    lt = launcher_targets(arch)
    t["launcher"] = {r: {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in d.items()} for r, d in lt.items()}
    return t


def _key(t: dict) -> str:
    from hardware import extract as EX
    blob = json.dumps(dict(t=t, mat=EX.MATERIALS, geo=[ROW_PITCH, W_PAD, W_PAD_STACK, W_PAD_CROSS, W_GRAL, GRAL_OV, JJ_A, JJ_AM, J_RET, J_RET_BS, S_FREE, X_TRIM, X_TRIM_R, TRIM_WB, TRIM_WT, W_STRIP_X, L_NECK, S_FREE_L, LINE_SEP,
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


# ====================================================================================================================
# drawing
# ====================================================================================================================
def default_sizing(arch) -> dict:
    """first-guess sizing (used before extraction and as the starting point of the solve)"""
    t = targets(arch)
    p = t["pitch_um"]
    sq = (t["L_pH"] - 8.0) / 500.0
    return dict(s_free={}, l_gral={}, w_strip={}, cap={}, island={}, lines={}, trim={}, defaults=dict(
        s_free=S_FREE, l_gral=sq * W_GRAL, w_strip=0.25, cap_wt=0.20, cap_l=0.6, isl_ov=0.25, trim=0.0))


def _get(sz, key, *idx, default=None):
    d = sz.get(key, {})
    k = "|".join(str(i) for i in idx)
    if k in d:
        return d[k]
    return sz.get("defaults", {}).get(key, default) if default is None else default


class Block:
    """everything needed to draw and to extract: the plan, the sizing and the geometry"""

    def __init__(self, arch: Architecture, sizing: dict | None = None):
        self.arch = arch
        self.t = targets(arch)
        self.p = arch.rail.pitch_um
        self.N = arch.n_cells
        self.sz = sizing if sizing is not None else default_sizing(arch)
        self.A_jj = jj_area_for(arch.rail.EJ_GHz)
        self.A_jjM = jj_area_for(arch.EJ_M_GHz)
        self.x0 = MARGIN_X                                   # node 0
        self.W = 2 * MARGIN_X + (self.N - 1) * self.p
        self.H = 2 * MARGIN_Y + (len(ROWS) - 1) * ROW_PITCH
        self.y_top = self.H - MARGIN_Y                       # rail of D_A
        self.yc = {r: rail_y(r, self.y_top) for r in ROWS}
        self.ret = {r: [return_kind(arch, r, n) for n in range(self.N)] for r in ROWS}
        self.g = [_env(arch, n) for n in range(self.N)]
        self.bs = bs_sections(arch)
        self.lt = launcher_targets(arch)
        self.geo = Geo()

    # ---- helpers
    def xn(self, n):
        return self.x0 + n * self.p

    # ---- launcher spans: the launch row's lines run in the inner strip on its free side; there the launch row and
    # the row on the far side of that strip both get a 1.0 um free gap, and a dummy far row returns to the outer side
    def launch_spans(self):
        if hasattr(self, "_spans"):
            return self._spans
        sp = {}
        for row, tg in (self.lt or {}).items():
            act = [n for n in range(self.N - 1) if tg["acc"][n] > 0 or tg["trap"][n] > 0]
            if not act:
                continue
            if mirrored(row):
                cells = set(range(min(act) - 2, self.N))
            else:
                cells = set(range(0, max(act) + 3))
            df = -RUNG_DIR[row]["G"]
            far = [r for r in ROWS if abs(self.yc[r] - self.yc[row] - df * ROW_PITCH) < 1e-6]
            sp[row] = dict(cells=cells, far=far[0] if far else None, df=df)
        self._spans = sp
        return sp

    def rdir(self, row, n):
        """rung direction of (row, n): +1 up, -1 down. A dummy row returns to the outer side inside the launch span
        of its neighbour, so that the launch strip is bounded by two free sides (room for both control lines)."""
        k = self.ret[row][n]
        d = RUNG_DIR[row][k]
        if k == "G" and row in ("D_A", "D_B"):
            for lr, spn in self.launch_spans().items():
                if spn["far"] == row and n in spn["cells"]:
                    return -d
        return d

    def s_free(self, row, n):
        key = f"{row}|{n}"
        if key in self.sz.get("s_free", {}):
            return self.sz["s_free"][key]
        if self.ret[row][n] == "G":
            for lr, spn in self.launch_spans().items():
                if n in spn["cells"] and row in (lr, spn["far"]):
                    return S_FREE_L
        return _get(self.sz, "s_free", row, n)

    def l_gral(self, row, n):
        return _get(self.sz, "l_gral", row, n)

    def w_strip(self, pair, n):
        return _get(self.sz, "w_strip", pair, n)

    def neck_w(self, pair, n):
        """strip width under the crossing lead: half the strip width, >= W_STRIP_X (only where a capacitor is)"""
        ws = self.w_strip(pair, n)
        if self.strip_mat(pair, n) != "AL2" or not self.cap(pair, n):
            return ws
        return min(ws, max(W_STRIP_X, ws / 2))

    def strip_mat(self, pair, n):
        return self.sz.get("strip_mat", {}).get(f"{pair}|{n}", "AL2")

    def cap(self, pair, n):
        """(w_t, l_ov) of the coupling capacitor at node n, or None"""
        v = self.sz.get("cap", {}).get(f"{pair}|{n}", "default")
        if v == "default":
            if self.g[n] <= 0:
                return None
            d = self.sz["defaults"]
            return (d["cap_wt"], d["cap_l"] * self.g[n])
        return v

    def pad_w(self, row, n):
        if self.ret[row][n] == "S":
            return W_PAD_STACK if CPL_ROLE[row] == "plate" else W_PAD_CROSS
        return W_PAD

    def pad_extent(self, row, n):
        """(left, right) x-extent of node pad n: shared grAl gaps set by the meshes n-1 and n"""
        p = self.p
        xl = self.xn(n) - (p - (self.l_gral(row, n - 1) if n > 0 else self.l_gral(row, 0))) / 2
        xr = self.xn(n) + (p - (self.l_gral(row, n) if n < self.N - 1 else self.l_gral(row, n - 1))) / 2
        return xl, xr

    def strip_y(self, pair):
        a, b = PAIRS[pair]
        return 0.5 * (self.yc[a] + self.yc[b])

    def bs_y(self, q):
        a, b = QUBIT_ROWS[q]
        return 0.5 * (self.yc[a] + self.yc[b])

    def node(self, row, n):
        return f"{row}_{n}"

    # ---- openings: the y-intervals that are NOT ground in column n (merged for coupled / beam-splitter pairs)
    def openings(self, n):
        iv = []
        done = set()
        for row in ROWS:
            if row in done:
                continue
            yc, d, k = self.yc[row], self.rdir(row, n), self.ret[row][n]
            if k in ("S", "M"):
                partner = None
                if k == "S":
                    a, b = PAIRS[PAIR_OF[row]]
                else:
                    q = "A" if row in QUBIT_ROWS["A"] else "B"
                    a, b = QUBIT_ROWS[q]
                partner = b if row == a else a
                # merged opening from the upper row's free edge to the lower row's free edge
                up, dn = (a, b) if self.yc[a] > self.yc[b] else (b, a)
                y_hi = self.yc[up] + self.pad_w(up, n) / 2 + self.s_free(up, n)
                y_lo = self.yc[dn] - self.pad_w(dn, n) / 2 - self.s_free(dn, n)
                iv.append((y_lo, y_hi))
                done |= {row, partner}
            else:
                w = self.pad_w(row, n) / 2
                if d > 0:
                    iv.append((yc - w - self.s_free(row, n), yc + w + S_RET))
                else:
                    iv.append((yc - w - S_RET, yc + w + self.s_free(row, n)))
                done.add(row)
        return sorted(iv)

    # ---- draw everything
    def draw(self):
        g = self.geo
        p, N = self.p, self.N
        # ground plane by columns; row ends handled by end columns
        for n in range(N):
            xa, xb = self.xn(n) - p / 2, self.xn(n) + p / 2
            self._ground_column(xa, xb, self.openings(n))
        self._ends()
        for row in ROWS:
            for n in range(N):
                self._rail_node(row, n)
        for pair in PAIRS:
            self._coupler(pair)
        for q, sec, ns in self.bs:
            self._beam_splitter(q, sec, ns)
        self._launchers()
        self._straps()
        self._gates()
        self._fanout()
        self._labels()
        self._line_rects = [r for r in g.rects if r[6] == "line" and r[0] == L_NB and (r[4] - r[2]) < 1.5]
        return g

    def _ground_column(self, xa, xb, iv, net="G"):
        y = 0.0
        for (lo, hi) in iv:
            if lo > y:
                self.geo.add(L_NB, xa, y, xb, lo, net, "ground")
            y = max(y, hi)
        if y < self.H:
            self.geo.add(L_NB, xa, y, xb, self.H, net, "ground")

    # ---- rail node n of a row: pad, granular Al to node n+1, rung to its return
    def _rail_node(self, row, n):
        g, p = self.geo, self.p
        yc = self.yc[row]
        nd = self.node(row, n)
        k = self.ret[row][n]
        d = self.rdir(row, n)
        wp = self.pad_w(row, n)
        xl, xr = self.pad_extent(row, n)
        g.add(L_AL1, xl, yc - wp / 2, xr, yc + wp / 2, nd, "pad")
        if wp == W_PAD_STACK:
            g.add(L_AL2, xl, yc - wp / 2, xr, yc + wp / 2, nd, "pad_stack")
        if n < self.N - 1:
            xl2, _ = self.pad_extent(row, n + 1)
            g.add(L_GRAL, xr - GRAL_OV, yc - W_GRAL / 2, xl2 + GRAL_OV, yc + W_GRAL / 2, (nd, self.node(row, n + 1)),
                  "gral")
        # rung: AL1 finger from the pad across the AL2 bar, AL2 return lead to the return
        xn = self.xn(n)
        b = self.A_jj / JJ_A
        y_pe = yc + d * wp / 2
        y_edge = self._return_edge(row, n, d)
        y_j = y_edge - d * (J_RET_BS if k == "M" else J_RET)
        xf = xn + X_JJ
        g.add(L_AL1, xf - JJ_A / 2, y_pe - d * 0.05, xf + JJ_A / 2, y_j + d * (b / 2 + E1), nd, "jj_finger")
        xr_ = xn + X_RET
        rnet = self.ret_net(row, n)
        g.add(L_AL2, xf - JJ_A / 2 - E1, y_j - b / 2, xr_ + W_RET / 2, y_j + b / 2, rnet, "jj_bar")
        y_end = self._return_y(row, n, d)
        g.add(L_AL2, xr_ - W_RET / 2, y_j - d * b / 2, xr_ + W_RET / 2, y_end, rnet, "ret_lead")
        lt = self.trim(row, n)
        if k == "S":
            pk_ = PAIR_OF[row]
            nb_here = self.strip_mat(pk_, n) == "NB"
            nb_prev = n > 0 and self.g[n - 1] > 0 and self.strip_mat(pk_, n - 1) == "NB"
            if nb_here or nb_prev:
                ys_ = self.strip_y(pk_)
                if nb_here and nb_prev:
                    x0_, x1_ = xr_ - CONTACT[0] / 2, xr_ + CONTACT[0] / 2
                elif nb_here:
                    x0_, x1_ = xr_, xr_ + 1.1                      # segment n starts at the return lead
                else:
                    x0_, x1_ = xr_ - 1.1, xr_
                g.add(L_AL2, x0_, ys_ - CONTACT[1] / 2, x1_, ys_ + CONTACT[1] / 2, rnet, "contact")
        if k == "G":
            # shared ground contact (AL2 on NB) for the rung and the return-side trim capacitor
            x_hi = xn + X_TRIM_R + TRIM_WT / 2 if lt is not None else xr_ + CONTACT[0] / 2
            g.add(L_AL2, xr_ - CONTACT[0] / 2, y_edge + d * 0.15, x_hi, y_edge + d * (0.15 + CONTACT[1]), "G", "contact")
            if lt is not None:
                stack_next = n + 1 < self.N and self.pad_w(row, n + 1) == W_PAD_STACK
                self._trim(row, n, d, lt, xt=xn + X_TRIM_R - (0.10 if stack_next else 0.0), contact=False)
        elif lt is not None:
            # trim to ground on the free side (coupler and beam-splitter cells, whose return side is busy)
            self._trim(row, n, -d, lt)
        g.junctions = getattr(g, "junctions", [])
        g.junctions.append(dict(kind="rail", row=row, n=n, x=xf, y=y_j, area=JJ_A * b, a=nd, b=rnet,
                                box=(xf - JJ_A / 2, min(y_j - b / 2, y_j + b / 2), xf + JJ_A / 2, max(y_j - b / 2, y_j + b / 2))))

    def ret_net(self, row, n):
        k = self.ret[row][n]
        if k == "G":
            return "G"
        if k == "S":
            return f"S_{PAIR_OF[row]}"
        q = "A" if row in QUBIT_ROWS["A"] else "B"
        for qq, sec, ns in self.bs:
            if qq == q and n in ns:
                i = ns.index(n)
                return "G" if i in (0, len(ns) - 1) else f"M{q}_{n}"
        return "G"

    def is_strap(self, row, n):
        if not hasattr(self, "_strap_set"):
            self._strap_set = {(r, nn) for (_, r, nn) in self.strap_cells()}
        return (row, n) in self._strap_set

    def trim(self, row, n):
        """trim knob (um): > 0 overlap of the grounded AL2 plate over the node's AL1 trim plate; -0.3 .. 0 the AL2
        plate stops |value| short (in-plane gap; at -0.3 it has shrunk into the ground edge). None: no trim at all."""
        if self.is_strap(row, n):
            return None                                     # the strap crossing is this node's trim
        v = self.sz.get("trim", {}).get(f"{row}|{n}", self.sz.get("defaults", {}).get("trim", 0.0))
        return None if v is None else max(float(v), -0.30)

    def free_edge(self, row, n):
        d = self.rdir(row, n)
        return self.yc[row] - d * (self.pad_w(row, n) / 2 + self.s_free(row, n))

    def _trim(self, row, n, df, lov, xt=None, contact=True):
        """trim capacitor to ground: AL1 stub + plate from the pad toward the ground edge in direction df (free side,
        or return side for plain cells), AL2 plate from the ground (contact on NB) over it with overlap lov (y);
        SiNx between"""
        g = self.geo
        nd = self.node(row, n)
        yc, wp = self.yc[row], self.pad_w(row, n)
        xt = self.xn(n) + X_TRIM if xt is None else xt
        y_pe = yc + df * wp / 2
        d_ret = self.rdir(row, n)
        y_ge = self.free_edge(row, n) if df != d_ret else yc + d_ret * (wp / 2 + S_RET)
        y_p1 = y_ge - df * 0.40                             # AL1 plate ends 0.40 before the ground edge
        y_p0 = y_pe
        g.add(L_AL1, xt - 0.12 / 2, y_p0, xt + 0.12 / 2, y_p1, nd, "trim_stub")
        y_pl0 = y_p1 - df * (max(lov, 0.0) + 0.30)          # the AL1 plate extends 0.30 beyond the overlap
        if (y_pl0 - y_pe) * df < 0.25:                       # no notch narrower than the AL1 space rule
            y_pl0 = y_pe
        g.add(L_AL1, xt - TRIM_WB / 2, y_pl0, xt + TRIM_WB / 2, y_p1, nd, "trim_bottom")
        if contact:
            g.add(L_AL2, xt - CONTACT[0] / 2, y_ge + df * 0.15, xt + CONTACT[0] / 2, y_ge + df * (0.15 + 1.0),
                  "G", "contact")
        if lov > 0:
            y_ov0 = y_p1 - df * lov                          # AL2 overlaps the AL1 plate from y_p1 to y_ov0
            g.add(L_AL2, xt - TRIM_WT / 2, y_ov0, xt + TRIM_WT / 2, y_ge + df * 0.15, "G", "trim_top")
            lo, hi = sorted((y_ov0, y_p1))
            g.add(L_DIEL, xt - TRIM_WT / 2 - 0.22, lo - DIEL_ENC, xt + TRIM_WT / 2 + 0.22, hi + DIEL_ENC, None,
                  "diel_trim")
            g.caps = getattr(g, "caps", [])
            g.caps.append(dict(kind="trim", row=row, n=n, a=nd, b="G", w_x=TRIM_WT, w_y=hi - lo,
                               edges={"top_edge": 2 * (hi - lo) + TRIM_WT, "bottom_edge": TRIM_WT},
                               box=(xt - TRIM_WT / 2, lo, xt + TRIM_WT / 2, hi), drop="G"))
        elif lov > -0.30:
            # in-plane: the grounded AL2 tab reaches from the ground edge to |lov| short of the AL1 plate
            y_tab = y_p1 + df * (-lov)
            if (y_ge + df * 0.15 - y_tab) * df > 0.05:
                g.add(L_AL2, xt - TRIM_WT / 2, y_tab, xt + TRIM_WT / 2, y_ge + df * 0.15, "G", "trim_top")

    def _return_edge(self, row, n, d):
        """y of the return edge the junction sits next to: ground edge, strip edge or island edge"""
        k = self.ret[row][n]
        yc, wp = self.yc[row], self.pad_w(row, n)
        if k == "G":
            return yc + d * (wp / 2 + S_RET)
        if k == "S":
            pair = PAIR_OF[row]
            w = max(self.w_strip(pair, n), self.w_strip(pair, n - 1) if n > 0 and self.g[n - 1] > 0 else 0.0)
            return self.strip_y(pair) - d * w / 2
        q = "A" if row in QUBIT_ROWS["A"] else "B"
        return self.bs_y(q) - d * ISL_H / 2

    def _return_y(self, row, n, d):
        """y where the AL2 return lead ends (inside the ground contact, the strip, or the island)"""
        k = self.ret[row][n]
        yc, wp = self.yc[row], self.pad_w(row, n)
        if k == "G":
            return yc + d * (wp / 2 + S_RET + 0.15 + 0.5)
        if k == "S":
            return self.strip_y(PAIR_OF[row])
        q = "A" if row in QUBIT_ROWS["A"] else "B"
        return self.bs_y(q) - d * (ISL_H / 2 - 0.2)

    # ---- couplers: strip (AL2, or NB at the low-g ends) and coupling capacitors
    def _coupler(self, pair):
        g, p = self.geo, self.p
        ra, rb = PAIRS[pair]
        ys = self.strip_y(pair)
        ns = [n for n in range(self.N) if self.g[n] > 0]
        if not ns:
            return
        net = f"S_{pair}"
        for n in ns:
            ws = self.w_strip(pair, n)
            mat = self.strip_mat(pair, n)
            xa = self.xn(n) + X_RET
            xb = self.xn(n + 1) + X_RET if n + 1 <= ns[-1] else self.xn(n) + p / 2
            if n == ns[0]:
                xa = self.xn(n) - p / 2
            wn = self.neck_w(pair, n)
            if mat == "AL2" and wn < ws:
                xc = self.xn(n) + X_CAP
                for (u0, u1, w) in ((xa, xc - L_NECK / 2, ws), (xc - L_NECK / 2, xc + L_NECK / 2, wn),
                                    (xc + L_NECK / 2, xb, ws)):
                    g.add(L_AL2, u0, ys - w / 2, u1, ys + w / 2, net, "strip")
            else:
                g.add(L_NB if mat == "NB" else L_AL2, xa, ys - ws / 2, xb, ys + ws / 2, net, "strip")
        # strip ends: tie to the inner ground strips beyond the coupler (AL2 on NB contact, >= 1 um^2)
        for xe, sgn in ((self.xn(ns[0]) - p / 2, -1), (self.xn(ns[-1]) + p / 2, +1)):
            w0 = max(self.w_strip(pair, ns[0] if sgn < 0 else ns[-1]), 1.0)
            g.add(L_AL2, xe - sgn * 0.0, ys - w0 / 2, xe + sgn * 1.2, ys + w0 / 2, "G", "strip_end")
        # coupling capacitors
        for n in ns:
            c = self.cap(pair, n)
            if not c:
                continue
            wt, lov = c
            self._cap(pair, n, wt, lov)

    def _cap(self, pair, n, wt, lov):
        """coupling capacitor at node n: lov > 0 is the AL2/AL1 overlap length (parallel plate through SiNx);
        lov < 0 stops the AL2 lead |lov| short of the bottom plate (in-plane end gap, for the small taper values)"""
        g = self.geo
        ra, rb = PAIRS[pair]
        cross = ra if CPL_ROLE[ra] == "cross" else rb
        plate = rb if cross == ra else ra
        ys = self.strip_y(pair)
        ws = self.w_strip(pair, n)
        dc = +1 if self.yc[plate] > self.yc[cross] else -1       # direction from the cross row to the plate row
        xc = self.xn(n) + X_CAP
        wb = max(W_CL, wt + 0.10)                                 # bottom line width (encloses the top lead)
        # AL1 lead of the cross row: from its rung finger (branch) or its pad, under the strip, to the bottom plate
        y_cpad = self.yc[cross] + dc * W_PAD / 2
        wsx = self.neck_w(pair, n)
        y_bp0 = ys + dc * (wsx / 2 + 0.40)                        # bottom plate starts beyond the (narrowed) strip
        y_bp1 = y_bp0 + dc * (max(lov, 0.0) + 0.15)
        if BRANCH:
            b = self.A_jj / JJ_A
            y_j = self._return_edge(cross, n, dc) - dc * J_RET    # junction of the cross row (dc = its rung dir)
            y_br = y_j - dc * 0.45
            xf = self.xn(n) + X_JJ
            g.add(L_AL1, xf - JJ_A / 2, y_br - 0.06, xc + W_CL / 2, y_br + 0.06, self.node(cross, n), "cap_branch")
            g.add(L_AL1, xc - W_CL / 2, y_br, xc + W_CL / 2, y_bp0, self.node(cross, n), "cap_lead")
        else:
            g.add(L_AL1, xc - W_CL / 2, y_cpad - dc * 0.05, xc + W_CL / 2, y_bp0, self.node(cross, n), "cap_lead")
        g.add(L_AL1, xc - wb / 2, y_bp0, xc + wb / 2, y_bp1, self.node(cross, n), "cap_bottom")
        # AL2 top lead of the plate row: from its pad stack down to overlap lov with the bottom plate
        y_ppad = self.yc[plate] - dc * W_PAD_STACK / 2
        if lov > 0:
            y_ov0 = y_bp0 + dc * 0.15                             # top-lead end 0.15 inside the bottom plate
        else:
            y_ov0 = y_bp1 + dc * (-lov)                           # in-plane gap |lov| beyond the bottom plate
        if (y_ppad - y_ov0) * dc > 0.05:
            g.add(L_AL2, xc - wt / 2, y_ov0, xc + wt / 2, y_ppad + dc * 0.05, self.node(plate, n), "cap_top")
        # dielectric: the strip crossing (and the overlap)
        y_lo = ys - dc * (ws / 2 + DIEL_ENC)
        y_hi = (y_bp1 + dc * DIEL_ENC) if lov > 0 else (ys + dc * (wsx / 2 + DIEL_ENC))
        g.add(L_DIEL, xc - wb / 2 - DIEL_ENC, y_lo, xc + wb / 2 + DIEL_ENC, y_hi, None, "diel_cap")
        g.caps = getattr(g, "caps", [])
        if lov <= 0:
            g.caps.append(dict(kind="crossing", pair=pair, n=n, a=self.node(cross, n), b=f"S_{pair}",
                               w_x=W_CL, w_y=wsx, edges={"top_edge": 2 * W_CL, "bottom_edge": 2 * wsx},
                               box=(xc - W_CL / 2, ys - wsx / 2, xc + W_CL / 2, ys + wsx / 2),
                               drop=self.node(cross, n)))
            return
        yo0, yo1 = sorted((y_ov0, y_bp1))
        g.caps.append(dict(kind="coupler", pair=pair, n=n, a=self.node(cross, n), b=self.node(plate, n),
                           w_x=wt, w_y=lov, edges={"top_edge": 2 * lov + wt, "bottom_edge": wt},
                           box=(xc - wt / 2, yo0, xc + wt / 2, yo1), drop=self.node(plate, n)))
        g.caps.append(dict(kind="crossing", pair=pair, n=n, a=self.node(cross, n), b=f"S_{pair}",
                           w_x=W_CL, w_y=wsx, edges={"top_edge": 2 * W_CL, "bottom_edge": 2 * wsx},
                           box=(xc - W_CL / 2, ys - wsx / 2, xc + W_CL / 2, ys + wsx / 2), drop=self.node(cross, n)))

    # ---- beam splitters: middle-rail islands (AL1+AL2 stacks), series junctions, island shunt capacitors
    def _beam_splitter(self, q, sec, ns):
        g, p = self.geo, self.p
        ys = self.bs_y(q)
        bm = self.A_jjM / JJ_AM
        ov = _get(self.sz, "island", q, sec, default=self.sz["defaults"]["isl_ov"])
        for i, n in enumerate(ns):
            xn = self.xn(n)
            net = "G" if i in (0, len(ns) - 1) else f"M{q}_{n}"
            g.add(L_AL1, xn + X_RET - ISL_W / 2, ys - ISL_H / 2, xn + X_RET + ISL_W / 2, ys + ISL_H / 2, net, "island")
            g.add(L_AL2, xn + X_RET - ISL_W / 2, ys - ISL_H / 2, xn + X_RET + ISL_W / 2, ys + ISL_H / 2, net, "island")
            if i in (0, len(ns) - 1):                              # grounded end islands: NB tab under the stack
                sgn = -1 if i == 0 else +1
                g.add(L_NB, xn + X_RET - ISL_W / 2 - (0.0 if sgn > 0 else 1.5), ys - ISL_H / 2,
                      xn + X_RET + ISL_W / 2 + (1.5 if sgn > 0 else 0.0), ys + ISL_H / 2, "G", "ground")
            if i == len(ns) - 1:
                continue
            nxt = "G" if i + 1 == len(ns) - 1 else f"M{q}_{ns[i + 1]}"
            xr0 = xn + X_RET + ISL_W / 2                           # right edge of island n
            xl1 = self.xn(ns[i + 1]) + X_RET - ISL_W / 2           # left edge of island n+1
            # middle junction (upper half): AL1 finger from island n, AL2 finger hanging from island n+1
            yf = ys + 0.35
            xf = 0.5 * (xr0 + xl1) + 0.05
            g.add(L_AL1, xr0 - 0.05, yf - JJ_AM / 2, xf + bm / 2 + E1, yf + JJ_AM / 2, net, "mjj_finger")
            g.add(L_AL2, xf - bm / 2, yf - JJ_AM / 2 - E1, xf + bm / 2, ys + 0.75, nxt, "mjj_finger2")
            g.add(L_AL2, xf - bm / 2, ys + 0.60, xl1 + 0.05, ys + 0.75, nxt, "mjj_bar")
            g.junctions = getattr(g, "junctions", [])
            g.junctions.append(dict(kind="middle", q=q, sec=sec, n=n, x=xf, y=yf, area=JJ_AM * bm, a=net, b=nxt,
                                    box=(xf - bm / 2, yf - JJ_AM / 2, xf + bm / 2, yf + JJ_AM / 2)))
            # island shunt (lower half): AL1 plate from island n, AL2 plate from island n+1, dielectric between
            yb0, yb1 = ys - 0.70, ys - 0.15
            xm = 0.5 * (xr0 + xl1)
            if ov > 0:
                g.add(L_AL1, xr0 - 0.05, yb0, xm + ov / 2, yb1, net, "shunt_bottom")
                g.add(L_AL2, xm - ov / 2, yb0 + 0.10, xl1 + 0.05, yb1 - 0.10, nxt, "shunt_top")
                g.add(L_DIEL, xm - ov / 2 - DIEL_ENC, yb0 - 0.15, xm + ov / 2 + DIEL_ENC, yb1 + 0.15, None, "diel_shunt")
                g.caps = getattr(g, "caps", [])
                hy = (yb1 - 0.10) - (yb0 + 0.10)
                g.caps.append(dict(kind="island_shunt", q=q, sec=sec, n=n, a=net, b=nxt, w_x=ov, w_y=hy,
                                   edges={"top_edge": hy + 2 * ov, "bottom_edge": hy},
                                   box=(xm - ov / 2, yb0 + 0.10, xm + ov / 2, yb1 - 0.10), drop=nxt))

    # ---- CPW helper: a Manhattan centre line (NB) with its slot cut out of the ground (keep-out)
    def _cpw(self, pts, w, gap, net, role="line"):
        g = self.geo
        g.keepout = getattr(g, "keepout", [])
        for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
            if abs(ya - yb) < 1e-9:
                x1, x2 = sorted((xa, xb))
                g.add(L_NB, x1 - w / 2, ya - w / 2, x2 + w / 2, ya + w / 2, net, role)
                g.keepout.append((x1 - w / 2 - gap, ya - w / 2 - gap, x2 + w / 2 + gap, ya + w / 2 + gap))
            else:
                y1, y2 = sorted((ya, yb))
                g.add(L_NB, xa - w / 2, y1 - w / 2, xa + w / 2, y2 + w / 2, net, role)
                g.keepout.append((xa - w / 2 - gap, y1 - w / 2 - gap, xa + w / 2 + gap, y2 + w / 2 + gap))

    def _port(self, name, x, y, layer, width, direction, **kw):
        d = dict(name=name, x=round(x, 4), y=round(y, 4), layer=list(layer), width=width, direction=direction)
        d.update(kw)
        self.geo.ports.append(d)

    # ---- row ends: margin ground, load loops (launch end), catcher loops (other end)
    END_EXT = 14.0

    def _ends(self):
        g, p = self.geo, self.p
        xL = self.xn(0) - p / 2
        xR = self.xn(self.N - 1) + p / 2
        g.add(L_NB, 0.0, 0.0, xL, self.H, "G", "ground")
        g.add(L_NB, xR, 0.0, self.W, self.H, "G", "ground")
        g.keepout = getattr(g, "keepout", [])
        self.end_lines = {"L": [], "R": []}                # (y, net, kind, x_start) of lines leaving each end
        for row in ROWS:
            yc = self.yc[row]
            for side, n, xe, sgn in (("L", 0, xL, -1), ("R", self.N - 1, xR, +1)):
                iv = [o for o in self.openings(n) if o[0] - 1e-9 <= yc <= o[1] + 1e-9][0]
                launch = row in self.lt and ((side == "L") != mirrored(row))
                catch = (not row.startswith("D")) and ((side == "R") != mirrored(row))
                nd = self.node(row, n)
                xp0, xp1 = self.pad_extent(row, n)
                xedge = xp0 if side == "L" else xp1
                if not (launch or catch):
                    continue
                # loop: granular Al from the end node to a ground pad (AL1 on NB): load 1 nH = 2 sq (w 0.5),
                # catcher 20 nH = 40 sq (w 0.25, 10 um long)
                wl, sq = (0.30, 2.0) if launch else (0.25, 40.0)
                L = wl * sq
                xa, xb = sorted((xedge - sgn * GRAL_OV, xedge + sgn * L))
                g.add(L_GRAL, xa, yc - wl / 2, xb, yc + wl / 2, (nd, "G"), "load_loop" if launch else "catcher")
                xg = xedge + sgn * L                       # unshielded granular Al ends here
                ga, gb = sorted((xg - sgn * GRAL_OV, xg + sgn * 1.8))
                g.add(L_AL1, ga, yc - 0.6, gb, yc + 0.6, "G", "loop_gnd")
                x_open_end = xg + sgn * 0.6                # NB starts under the pad (contact 0.8 x 1.2 um)
                x0, x1 = sorted((xe, x_open_end))
                g.keepout.append((x0, iv[0], x1, iv[1]))
                # the line to the port starts beyond the loop ground, on the row axis (NB shorts it to ground
                # next to the loop: current-driven flux line / inductive readout coupling point)
                self.end_lines[side].append((yc, f"{'LOAD' if launch else 'RO'}_{row}", "load" if launch else "readout",
                                             x_open_end + sgn * 4.0))

    # ---- launcher control lines: NB lines in slots of the inner ground strip on the free side of each launch row
    W_LINE, G_LINE = 0.5, 0.5

    def strip_bounds(self, row, n, side):
        """(y_near, y_far) of the inner ground strip next to `row` on `side` (+1 above, -1 below) at column n"""
        iv = self.openings(n)
        yc = self.yc[row]
        mine = [o for o in iv if o[0] - 1e-9 <= yc <= o[1] + 1e-9][0]
        if side > 0:
            nxt = [o for o in iv if o[0] > mine[1] - 1e-9]
            return mine[1], (min(o[0] for o in nxt) if nxt else self.H)
        nxt = [o for o in iv if o[1] < mine[0] + 1e-9]
        return mine[0], (max(o[1] for o in nxt) if nxt else 0.0)

    def depth_min(self):
        return self.W_LINE / 2 + self.G_LINE + 0.40          # NB sliver >= 0.40 between the slot and the opening

    def depth_max(self, row, c, df):
        """deepest line centre (from the row's free edge) that keeps the slot >= 0.4 um clear of the far side of the
        strip, and >= 0.4 um clear of the far row's free-side contacts where it has them (coupler / BS cells)"""
        y_near, y_far = self.strip_bounds(row, c, df)
        width = abs(y_far - y_near)
        reserve = 0.40
        for other in ROWS:
            yo = self.yc[other]
            if other == row or not (min(y_near, y_far) - 3 < yo - 0 < max(y_near, y_far) + 3 or True):
                continue
        # the row on the far side of the strip
        far_rows = [r for r in ROWS if r != row and abs(self.yc[r] - self.yc[row]) == ROW_PITCH
                    and np.sign(self.yc[r] - self.yc[row]) == df]
        for r in far_rows:
            for cc in (max(c - 1, 0), c, min(c + 1, self.N - 1)):
                k = self.ret[r][cc]
                faces_return = self.rdir(r, cc) == -df         # the far row's return side faces this strip
                if k != "G" or faces_return:
                    reserve = 0.15 + CONTACT[1] + 0.40
        return width - reserve - self.W_LINE / 2 - self.G_LINE

    def line_depths(self, row):
        return self.sz.get("lines", {}).get(row, {})

    def line_cells(self, row, tag):
        """rail cells a control line passes through: from the launch end to one cell past its last active cell"""
        from hardware.extract import M_DRAW_MIN
        tg = self.lt[row]
        M = np.asarray(tg[tag])
        act = np.nonzero(M >= M_DRAW_MIN)[0]                 # truncated after the last drawable target
        if not len(act):
            return []
        if not mirrored(row):
            return list(range(0, act.max() + 2))
        return list(range(self.N - 2, act.min() - 2, -1))

    def line_y(self, row, tag, c):
        """centre y of a control line at cell c (depth from the row's free-side ground edge, quantized to 0.25 um
        and clamped to the strip)"""
        df = -RUNG_DIR[row]["G"]
        dep = self.line_depths(row).get(tag, {})
        y_near, _ = self.strip_bounds(row, c, df)
        dpt = dep.get(str(c), self.sz["defaults"].get(f"depth_{tag}", 1.5 if tag == "trap" else 3.0))
        dpt = min(max(dpt, self.depth_min()), self.depth_max(row, c, df))
        dpt = self.depth_min() + round((dpt - self.depth_min()) / 0.25) * 0.25
        return y_near + df * min(dpt, self.depth_max(row, c, df))

    def _launchers(self):
        if not self.lt or self.sz.get("no_lines"):
            return
        g = self.geo
        W, G = self.W_LINE, self.G_LINE
        for row, tg in self.lt.items():
            m = mirrored(row)
            df = -RUNG_DIR[row]["G"]
            ys = {}
            for tag in ("trap", "acc"):
                cells = [c for c in self.line_cells(row, tag) if 0 <= c <= self.N - 2]
                if not cells:
                    continue
                ys[tag] = {c: self.line_y(row, tag, c) for c in cells}
            for tag, yc_ in ys.items():
                cells = list(yc_.keys())
                pts = []
                for c in cells:
                    y = yc_[c]
                    xa = self.xn(c) if not m else self.xn(c + 1)
                    xb = self.xn(c + 1) if not m else self.xn(c)
                    if not pts or abs(pts[-1][1] - y) > 1e-9:
                        pts.append((xa, y))
                    pts.append((xb, y))
                net_l = f"{'TR' if tag == 'trap' else 'AC'}_{row}"
                self._cpw(pts, W, G, net_l)
                end = pts[-1]
                sgx = 1 if not m else -1
                xa, xb = sorted((end[0], end[0] + sgx * (W / 2 + G + 0.6)))
                g.add(L_NB, xa, end[1] - W / 2, xb, end[1] + W / 2, net_l, "short")      # shorted to the strip
                self._port(f"{'TRAP' if tag == 'trap' else 'ACC'}_{row}_SHORT", end[0], end[1], L_NB, W,
                           "E" if not m else "W", kind="internal_short",
                           note="line shorted to the inner ground strip here (inside the block; not routable)")
                side = "L" if not m else "R"
                self.end_lines[side].append((pts[0][1], f"{'TRAP' if tag == 'trap' else 'ACC'}_{row}", tag, pts[0][0]))
                g.lines = getattr(g, "lines", [])
                g.lines.append(dict(row=row, tag=tag, cells=cells, net=net_l))
            # one shared slot where both lines run (no Nb sliver between them)
            if "trap" in ys and "acc" in ys:
                for c in set(ys["trap"]) & set(ys["acc"]):
                    y1, y2 = sorted((ys["trap"][c], ys["acc"][c]))
                    x1, x2 = sorted((self.xn(c), self.xn(c + 1)))
                    g.keepout.append((x1, y1 - W / 2 - G, x2, y2 + W / 2 + G))

    # ---- ground straps over the outer rail of each qubit: the inner strip between the two beam splitters of a
    # qubit is otherwise a floating NB island (it is cut by both BS sections)
    def strap_cells(self):
        out = []
        for q in ("A", "B"):
            secs = [ns for (qq, sec, ns) in self.bs if qq == q]
            if len(secs) < 2:
                continue
            a, b = sorted(secs, key=lambda ns: ns[0])
            lo, hi = a[-1] + 1, b[0] - 1                   # floating piece spans these columns
            outer = "A0" if q == "A" else "B0"
            target = "DA" if q == "A" else "DB"
            cand = [n for n in range(lo + 2, hi - 2) if self.g[n] == 0 and self.ret[outer][n] == "G"]
            if cand:
                out.append((q, outer, cand[len(cand) // 4]))
        return out

    def _straps(self):
        g = self.geo
        self.straps = []
        for q, row, n in self.strap_cells():
            d = RUNG_DIR[row]["G"]                         # return side = the floating strip
            yc = self.yc[row]
            xs = self.xn(n) + 0.55
            w = 0.40
            y_ret = yc + d * (W_PAD / 2 + S_RET)
            y_free = self.free_edge(row, n)
            y0, y1 = sorted((y_ret + d * (0.15 + CONTACT[1]), y_free - d * (0.15 + CONTACT[1])))
            g.add(L_AL2, xs - w / 2, y0, xs + w / 2, y1, "G", "strap")
            g.add(L_AL2, xs - 0.5, y_free - d * 0.15, xs + 0.5, y_free - d * (0.15 + CONTACT[1]), "G", "contact")
            g.add(L_DIEL, xs - w / 2 - DIEL_ENC, yc - W_PAD / 2 - DIEL_ENC, xs + w / 2 + DIEL_ENC, yc + W_PAD / 2 + DIEL_ENC,
                  None, "diel_strap")
            g.caps = getattr(g, "caps", [])
            g.caps.append(dict(kind="strap", row=row, n=n, a=self.node(row, n), b="G", w_x=w, w_y=W_PAD,
                               edges={"top_edge": 2 * W_PAD, "bottom_edge": 2 * w},
                               box=(xs - w / 2, yc - W_PAD / 2, xs + w / 2, yc + W_PAD / 2), drop="G"))
            self.straps.append(dict(q=q, row=row, n=n))

    # ---- beam-splitter gate electrodes: a NB line in a slot along the inner strip from the nearest row end, ending
    # in a gate pad next to the first floating island of the section
    def _gates(self):
        self.gates = []
        for (q, sec, ns) in self.bs:
            r0, r1 = QUBIT_ROWS[q]
            ys = self.bs_y(q)
            name = f"GATE_BS{q}_{'PREP' if sec == 'BS_prep' else 'AN'}"
            left = ns[0] < self.N // 2
            x_strip_end = self.xn(ns[0]) - self.p / 2 if left else self.xn(ns[-1]) + self.p / 2
            gx = x_strip_end + (-1.0 - 1.2 - 2.4 if left else 1.0 + 1.2 + 2.4)   # keep-out ends 1.0 before the end
            xe = self.xn(0) - self.p / 2 if left else self.xn(self.N - 1) + self.p / 2
            pts = [(xe, ys), (gx, ys)]
            self._cpw(pts, 0.6, 0.6, name, "gate_line")
            self.geo.add(L_NB, gx - 0.6, ys - 0.6, gx + 0.6, ys + 0.6, name, "gate_pad")
            self.geo.keepout.append((gx - 1.2, ys - 1.2, gx + 1.2, ys + 1.2))
            self.end_lines["L" if left else "R"].append((ys, name, "gate", xe))
            self.gates.append(dict(name=name, q=q, sec=sec, x=gx, y=ys, island=f"M{q}_{ns[1] if left else ns[-2]}"))

    # ---- fan-out in the margins: every line leaving a row end is routed as a CPW to a port on the block edge
    def _fanout(self):
        for side in ("L", "R"):
            lines = sorted(self.end_lines.get(side, []), key=lambda t: -t[0])
            if not lines:
                continue
            nL = len(lines)
            ymid = 0.5 * self.H
            yports = [ymid + (nL - 1) / 2 * PORT_PITCH - i * PORT_PITCH for i in range(nL)]
            sgn = -1 if side == "L" else +1
            x_row = self.xn(0) - self.p / 2 if side == "L" else self.xn(self.N - 1) + self.p / 2
            x_edge = 0.0 if side == "L" else self.W
            up = [(i, l) for i, l in enumerate(lines) if yports[i] >= l[0]]
            dn = [(i, l) for i, l in enumerate(lines) if yports[i] < l[0]]
            turns = {}
            for k, (i, l) in enumerate(up):                 # topmost upward line turns first
                turns[i] = x_row + sgn * (self.END_EXT + 12.0 + 4.0 * k)
            for k, (i, l) in enumerate(reversed(dn)):       # bottommost downward line turns first
                turns[i] = x_row + sgn * (self.END_EXT + 12.0 + 4.0 * k)
            for i, (y0, net, kind, xstart) in enumerate(lines):
                xt = turns[i]
                pts = [(xstart, y0), (xt, y0), (xt, yports[i]), (x_edge, yports[i])]
                self._cpw(pts, CPW_W, CPW_G, net, "fanout")
                if kind in ("load", "readout"):
                    # short the line's inner end to the ground next to the loop (current-driven flux line)
                    xa, xb = sorted((xstart, xstart - sgn * (CPW_W / 2 + CPW_G + 0.6)))
                    self.geo.add(L_NB, xa, y0 - CPW_W / 2, xb, y0 + CPW_W / 2, net, "short")
                    self._port((net if kind == "load" else f"RO_CATCHER_{net[3:]}") + "_SHORT", xstart, y0, L_NB, CPW_W,
                               "E" if side == "L" else "W", kind="internal_short",
                               note="line shorted to ground next to the loop (inside the block; not routable)")
                self._port(net if kind != "readout" else f"RO_CATCHER_{net[3:]}", x_edge, yports[i], L_NB,
                           CPW_W, "W" if side == "L" else "E", gap=CPW_G,
                           kind={"load": "load_loop_flux_line", "trap": "trap_line_feed", "acc": "accelerator_line_feed",
                                 "readout": "catcher_readout_coupling", "gate": "bs_island_gate"}[kind])
        for nm, x, y, dr in (("GND_N", 0.5 * self.W, self.H, "N"), ("GND_S", 0.5 * self.W, 0.0, "S"),
                             ("GND_W_TOP", 0.0, self.H - 20.0, "W"), ("GND_E_TOP", self.W, self.H - 20.0, "E"),
                             ("GND_W_BOT", 0.0, 20.0, "W"), ("GND_E_BOT", self.W, 20.0, "E")):
            self._port(nm, x, y, L_NB, 40.0, dr, kind="ground")

    def _labels(self):
        g = self.geo
        for d in self.arch.sections():
            g.labels.append((d["name"], self.xn(d["start"]), self.H - MARGIN_Y / 2))
        for row in ROWS:
            g.labels.append((row, MARGIN_X / 4, self.yc[row]))


# ====================================================================================================================
# GDS
# ====================================================================================================================
def _merge_layer(rects, keepout=()):
    polys = [gdstk.rectangle((r[1], r[2]), (r[3], r[4])) for r in rects]
    if not polys:
        return []
    merged = gdstk.boolean(polys, [], "or", precision=1e-4)
    if keepout:
        ko = gdstk.boolean([gdstk.rectangle((a, b), (c, d)) for (a, b, c, d) in keepout], [], "or", precision=1e-4)
        merged = gdstk.boolean(merged, ko, "not", precision=1e-4)
    return merged


def build_block(arch: Architecture, sizing: dict | None = None, cell_name: str = "QBFX2_ROWS"):
    """the complete row block as a gdstk cell. Returns (library, cell, ports, block). ports: list of dicts
    {name, x, y, layer, width, direction, gap?, kind} in block coordinates (origin at the block's lower-left corner,
    the block is W x H um; every port lies on the block boundary)."""
    sz = sizing if sizing is not None else get_sizing(arch)
    blk = Block(arch, sz)
    geo = blk.draw()
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    cell = lib.new_cell(cell_name)
    keep = getattr(geo, "keepout", [])
    by_layer = {}
    for r in geo.rects:
        x1, y1, x2, y2 = max(r[1], 0.0), max(r[2], 0.0), min(r[3], blk.W), min(r[4], blk.H)
        if x2 - x1 > 1e-9 and y2 - y1 > 1e-9:
            by_layer.setdefault(r[0], []).append((r[0], x1, y1, x2, y2) + tuple(r[5:]))
    # NB: ground (with slots and openings cut) united with the line conductors drawn inside the slots
    nb_ground = [r for r in by_layer.get(L_NB, []) if r[6] in ("ground", "load_gnd_nb", "catch_gnd_nb")]
    nb_other = [r for r in by_layer.get(L_NB, []) if r[6] not in ("ground", "load_gnd_nb", "catch_gnd_nb")]
    nb = _merge_layer(nb_ground, keep) + _merge_layer(nb_other)
    nb = gdstk.boolean(nb, [], "or", precision=1e-4)
    for poly in nb:
        poly.layer, poly.datatype = L_NB
        cell.add(poly)
    for ly in (L_GRAL, L_AL1, L_AL2, L_DIEL):
        for poly in _merge_layer(by_layer.get(ly, [])):
            poly.layer, poly.datatype = ly
            cell.add(poly)
    for (txt, x, y) in geo.labels:
        cell.add(gdstk.Label(txt, (x, y), layer=L_TXT[0], texttype=L_TXT[1]))
    for pt in geo.ports:
        cell.add(gdstk.Label(pt["name"], (pt["x"], pt["y"]), layer=L_TXT[0], texttype=1))
    return lib, cell, geo.ports, blk


def build(arch: Architecture, path: str, sizing: dict | None = None):
    lib, cell, ports, blk = build_block(arch, sizing)
    lib.write_gds(path)
    geo = blk.geo
    jj = getattr(geo, "junctions", [])
    caps = getattr(geo, "caps", [])
    dims = dict(width_um=blk.W, height_um=blk.H, rows=len(ROWS), row_pitch_um=ROW_PITCH, pitch_um=blk.p,
                cells_per_row=blk.N, rail_junctions=sum(1 for j in jj if j["kind"] == "rail"),
                middle_junctions=sum(1 for j in jj if j["kind"] == "middle"),
                junction_area_um2=round(blk.A_jj, 5), middle_junction_area_um2=round(blk.A_jjM, 5),
                junction_cross_um=(JJ_A, round(blk.A_jj / JJ_A, 4)), middle_junction_cross_um=(JJ_AM, round(blk.A_jjM / JJ_AM, 4)),
                coupling_capacitors_drawn=sum(1 for c in caps if c["kind"] == "coupler"),
                island_shunts_drawn=sum(1 for c in caps if c["kind"] == "island_shunt"),
                trims_drawn=sum(1 for c in caps if c["kind"] == "trim"), straps=getattr(blk, "straps", []),
                gates=getattr(blk, "gates", []), control_lines=[dict(row=l["row"], tag=l["tag"], net=l["net"])
                                                                 for l in getattr(geo, "lines", [])],
                ports=ports, sizing_key=blk.sz.get("key"),
                status="PRELIMINARY - DRC + EM-extraction verified row block (hardware/drc.py, hardware/extract.py); "
                       "not a full die")
    return dims


def preview(gds_path: str, png_path: str, box=None, size=(1600, 700)):
    import klayout.db as db
    import klayout.lay as lay
    cols = {"1/0": (0x8a8f99, 9), "2/0": (0xff8c1a, 0), "3/0": (0x2f6bff, 0), "4/0": (0xff2aff, 0),
            "5/0": (0x8b4513, 0), "6/0": (0x22aa55, 0), "10/0": (0x111111, 0), "10/1": (0xaa0000, 0)}
    v = lay.LayoutView()
    v.load_layout(gds_path)
    v.max_hier()
    v.set_config("background-color", "#ffffff")
    v.set_config("grid-visible", "false")
    v.set_config("text-visible", "true")
    it = v.begin_layers()
    while not it.at_end():
        lp = it.current().dup()
        key = f"{lp.source_layer}/{lp.source_datatype}"
        c, dp = cols.get(key, (0x999999, 0))
        lp.fill_color = c
        lp.frame_color = c
        lp.dither_pattern = dp
        lp.transparent = key in ("1/0", "6/0")
        v.set_layer_properties(it, lp)
        it.next()
    if box:
        v.zoom_box(db.DBox(*box))
    else:
        v.zoom_fit()
    v.save_image(png_path, *size)
