"""Differential (balanced) launcher control lines, rev B.

Each trap / accelerator line of a launch row is one floating Nb loop: it leaves the block edge as <NAME>_P, runs
along its rail in the launch strip, turns round at the far end and comes back as <NAME>_N, further from the rail.
No current returns through the ground, so the fast-line return no longer spreads through the shared ground strips
(cross-talk into the other rail of the qubit drops) and common-mode / ground-loop current cannot drive flux through
the loop.

Geometry (from the launch row outward, one shared slot, line centres >= PITCH_L apart):
    trap region   TRAP_P   TRAP_N   ACC_P   ACC_N(outermost track)
    acc region                       ACC_P   ACC_N(outermost track)       (after the trap pair has turned round)
The trap pair is never nested around the accelerator pair, so both loops close without crossing a line and the
four legs leave the strip in pair order (no air bridge anywhere).

Sizing: the pair mutual M_n = M(row ~ P) - M(row ~ N) per rail cell (2D cross-section, extract.column_inductance,
the same model the single-ended sizing used) is tabulated on the drawing's own 0.25 um depth grid, so the drawn
layout is exactly a table entry. Only the product M_n * I sets the flux (theta_n = 2 pi M_n I / Phi0), so each line
gets one uniform scale s <= 1 on its target profile and its drive current becomes I / s.
"""
import copy
import itertools
import math

import numpy as np

LINE_MODEL = "differential"
PITCH_L = 1.00                      # centre-to-centre of two lines in one slot (0.5 um line + 0.5 um gap)
Q = 0.25                            # depth grid of the drawing (Block.line_y)
TAGS = ("trap", "trap_N", "acc", "acc_N")
SHORT = {"trap": "TP", "trap_N": "TN", "acc": "AP", "acc_N": "AN"}
REP = {"A0": "A0", "A1": "A1", "B0": "A0", "B1": "A1"}      # rows with the same strip geometry share tables
C_REF = 30                                                  # reference column for the tables (launch strip)


def _nolines_block(arch, sz):
    from hardware import layout as LY
    s0 = copy.deepcopy(sz)
    s0["lines"] = {}
    s0["no_lines"] = True
    B = LY.Block(arch, s0)
    B.draw()
    return B


def depth_grid(B, row, c):
    """the drawable depths (line centre from the row's free-side ground edge, um) at column c"""
    from hardware import layout as LY
    df = -LY.RUNG_DIR[row]["G"]
    dmin, dmax = B.depth_min(), B.depth_max(row, c, df)
    k = int(math.floor((dmax - dmin) / Q + 1e-9))
    return [dmin + Q * i for i in range(k + 1)]


def line_mutuals(B, row, c, depths):
    """per-cell mutuals (pH) of the lines at `depths` {tag: depth} to every row's mesh at column c; pairs combine as
    P - N. Returns {"trap": {row: M}, "acc": {row: M}, "loops": M_trap_loop~acc_loop (pH per cell, geometric)}"""
    from hardware import layout as LY, extract as EX
    WL, GL = LY.Block.W_LINE, LY.Block.G_LINE
    df = -LY.RUNG_DIR[row]["G"]
    y_near, _ = B.strip_bounds(row, c, df)
    extra, ys = [], []
    for tag, d in depths.items():
        y = y_near + df * d
        extra.append((y - WL / 2, y + WL / 2, 0.0, SHORT[tag]))
        ys.append(y)
    slot = (min(ys) - WL / 2 - GL, max(ys) + WL / 2 + GL)
    strips, conds, ret, kin = EX.column_xsec(B, c, extra, [slot])
    L, names = EX.inductance_2d(strips, conds, "G")
    for nm, lk in kin.items():
        if nm in names:
            L[names.index(nm), names.index(nm)] += lk
    idx = {nm: i for i, nm in enumerate(names)}
    p = B.p

    def vec(pos, neg=None):
        e = np.zeros(len(names))
        e[idx[pos]] = 1.0
        if neg is not None and neg in idx:
            e[idx[neg]] -= 1.0
        return e
    mesh = {}
    for r, rc in ret.items():
        mesh[r] = vec(r, None if rc == "G" else rc)
    out = {}
    pairs = {}
    if "trap" in depths:
        pairs["trap"] = vec("TP", "TN" if "trap_N" in depths else None)
    if "acc" in depths:
        pairs["acc"] = vec("AP", "AN" if "acc_N" in depths else None)
    for k, e in pairs.items():
        out[k] = {r: float(p * mesh[r] @ L @ e) for r in mesh}
    if "trap" in pairs and "acc" in pairs:
        out["loops"] = float(p * pairs["trap"] @ L @ pairs["acc"])
    return out


def tables(arch, sz, say=print):
    """exact tables on the depth grid for the two strip types (A0-like, A1-like)"""
    from hardware import layout as LY
    B = _nolines_block(arch, sz)
    tabs = {}
    for row0 in ("A0", "A1"):
        grid = depth_grid(B, row0, C_REF)
        kmax = len(grid) - 1
        st = int(round(PITCH_L / Q))
        an = grid[kmax]
        quad = []                                           # trap region: (dTP, dTN, dAP), AN outermost
        for a, b, c in itertools.combinations_with_replacement(range(kmax - 3 * st + 1), 3):
            kTP, kTN, kAP = a, b + st, c + 2 * st
            if not (kTP + st <= kTN and kTN + st <= kAP and kAP + st <= kmax):
                continue
            dep = dict(trap=grid[kTP], trap_N=grid[kTN], acc=grid[kAP], acc_N=an)
            m = line_mutuals(B, row0, C_REF, dep)
            quad.append(dict(k=(kTP, kTN, kAP), d=dep, Mt=m["trap"][row0], Ma=m["acc"][row0], loops=m["loops"],
                             xt_t=m["trap"], xt_a=m["acc"]))
        pair = []                                           # acc region: AP and AN both free (AN = fine knob)
        for kAP in range(0, kmax - st + 1):
            for kAN in range(kAP + st, kmax + 1):
                dep = dict(acc=grid[kAP], acc_N=grid[kAN])
                m = line_mutuals(B, row0, C_REF, dep)
                pair.append(dict(k=(kAP, kAN), d=dep, Ma=m["acc"][row0], xt_a=m["acc"]))
        sgn = 1.0 if np.median([q["Mt"] for q in quad]) >= 0 else -1.0       # orientation of the mutuals
        for q in quad:
            q["Mt"] *= sgn
            q["Ma"] *= sgn
        for q in pair:
            q["Ma"] *= sgn
        tabs[row0] = dict(grid=grid, quad=quad, pair=pair, sign=sgn)
        say(f"diff tables {row0}: {len(quad)} four-line + {len(pair)} two-line cross-sections; trap pair M "
            f"{min(q['Mt'] for q in quad):.4f}..{max(q['Mt'] for q in quad):.4f} pH, acc pair (alone) "
            f"{min(q['Ma'] for q in pair):.4f}..{max(q['Ma'] for q in pair):.4f} pH")
    return B, tabs


def size_lines_diff(arch, sz, t=None, say=print):
    """per-cell depths of the four legs for every launch row + the uniform current scales (see module doc)"""
    from hardware import layout as LY
    lt = LY.launcher_targets(arch)
    if not lt:
        return sz, {}
    B, tabs = tables(arch, sz, say)
    lines, info, scale = {}, {}, {}
    for row, tg in lt.items():
        tb = tabs[REP[row]]
        m = LY.mirrored(row)
        Mt, Ma = np.asarray(tg["trap"]), np.asarray(tg["acc"])
        cells_t = [c for c in B.line_cells(row, "trap") if 0 <= c <= B.N - 2]
        cells_a = [c for c in B.line_cells(row, "acc") if 0 <= c <= B.N - 2]
        trap_set = set(cells_t)
        quad, pair = tb["quad"], tb["pair"]
        QT = np.array([q["Mt"] for q in quad])
        QA = np.array([q["Ma"] for q in quad])
        PA = np.array([q["Ma"] for q in pair])
        # uniform scales: accelerator from its strongest reachable coupling, trap from the trap region given the acc
        acc_only = [c for c in cells_a if c not in trap_set]
        need_a = max([Ma[c] for c in acc_only] or [0.0])
        s_a = min(1.0, 0.98 * PA.max() / need_a) if need_a > 0 else 1.0
        s_t = 1.0
        for c in cells_t:
            ok = QA >= s_a * Ma[c] - 0.02 * Ma.max()
            if not ok.any():
                s_a = min(s_a, 0.98 * QA.max() / max(Ma[c], 1e-12))
                ok = QA >= s_a * Ma[c] - 0.02 * Ma.max()
            if Mt[c] > 0.05 * Mt.max():
                s_t = min(s_t, 0.98 * QT[ok].max() / Mt[c])
        order = ("trap", "trap_N", "acc", "acc_N")             # from the row outward

        def clash(prev, cand):
            """two lines jog at the same x at a cell boundary: neighbouring lines need PITCH_L between the inner
            line's deeper position and the outer line's shallower position over both cells"""
            tags = [t for t in order if t in prev and t in cand]
            bad = 0.0
            for i, ti in enumerate(tags):
                for to in tags[i + 1:]:
                    gap = min(prev[to], cand[to]) - max(prev[ti], cand[ti])
                    bad += max(0.0, PITCH_L - gap - 1e-9)
            return bad
        dep = {k: {} for k in TAGS}
        resid = dict(trap=0.0, acc=0.0)
        prev = None
        for c in sorted(set(cells_t) | set(cells_a), reverse=m):     # launch end first
            tt, ta = s_t * Mt[c], s_a * Ma[c]
            if c in trap_set:
                cands, err = quad, np.abs(QT - tt) / (s_t * Mt.max()) + np.abs(QA - ta) / (s_a * Ma.max())
            else:
                cands, err = pair, np.abs(PA - ta) / (s_a * Ma.max())
            if prev is not None:
                err = err + 100.0 * np.array([clash(prev, q["d"]) for q in cands])
            q = cands[int(np.argmin(err))]
            if prev is not None and clash(prev, q["d"]) > 0:
                raise RuntimeError(f"{row} cell {c}: no jog-compatible line positions")
            for k_, v_ in q["d"].items():
                dep[k_][str(c)] = v_
            if c in trap_set:
                resid["trap"] = max(resid["trap"], abs(q["Mt"] - tt))
            resid["acc"] = max(resid["acc"], abs(q["Ma"] - ta))
            prev = dict(q["d"])
        lines[row] = dep
        scale[row] = dict(trap=s_t, acc=s_a, I_trap_uA=tg["trap_I_uA"] / s_t, I_acc_uA=tg["acc_I_uA"] / s_a)
        info[row] = dict(trap_cells=len(cells_t), acc_cells=len(cells_a), scale_trap=s_t, scale_acc=s_a,
                         drive_I_trap_uA=tg["trap_I_uA"] / s_t, drive_I_acc_uA=tg["acc_I_uA"] / s_a,
                         max_table_residual_pH=resid)
        say(f"diff lines {row}: s_trap {s_t:.3f} (I {tg['trap_I_uA'] / s_t:.1f} uA), s_acc {s_a:.3f} "
            f"(I {tg['acc_I_uA'] / s_a:.1f} uA), worst residual trap {resid['trap']:.4f} acc {resid['acc']:.4f} pH")
    sz["lines"] = lines
    sz["line_model"] = LINE_MODEL
    sz["line_scale"] = scale
    sz["line_tables_diff"] = {k: dict(grid=v["grid"], sign=v["sign"],
                                      quad=[dict(k=list(q["k"]), Mt=q["Mt"], Ma=q["Ma"], loops=q["loops"]) for q in v["quad"]],
                                      pair=[dict(k=list(q["k"]), Ma=q["Ma"]) for q in v["pair"]]) for k, v in tabs.items()}
    return sz, info


def as_drawn(arch, sz, stride=1, say=print):
    """the drawn legs (Block.line_y, exactly what is drawn) per cell: pair mutuals to every row, the trap-loop /
    acc-loop mutual, and the single-ended reference (the rev-A depths, same cross-section model) for comparison.
    Returns a dict ready for extraction.json['launcher_as_drawn'] (M referred to the design currents)."""
    from hardware import layout as LY
    B = _nolines_block(arch, sz)
    Bd = LY.Block(arch, sz)                                  # depths as drawn (line_y with the real sizing)
    lt = LY.launcher_targets(arch)
    out = {}
    for row, tg in lt.items():
        m = LY.mirrored(row)
        sc = sz["line_scale"][row]
        sgn = sz["line_tables_diff"][REP[row]]["sign"]
        cells_t = [c for c in Bd.line_cells(row, "trap") if 0 <= c <= Bd.N - 2]
        cells_a = [c for c in Bd.line_cells(row, "acc") if 0 <= c <= Bd.N - 2]
        allc = sorted(set(cells_t) | set(cells_a))
        allc = [c for i, c in enumerate(allc) if i % stride == 0 or c in cells_t]
        rec = []
        for c in allc:
            dep = {}
            if c in cells_t:
                dep["trap"] = Bd.line_y(row, "trap", c)
                dep["trap_N"] = Bd.line_y(row, "trap_N", c)
            if c in cells_a:
                dep["acc"] = Bd.line_y(row, "acc", c)
                dep["acc_N"] = Bd.line_y(row, "acc_N", c)
            df = -LY.RUNG_DIR[row]["G"]
            y_near, _ = B.strip_bounds(row, c, df)
            dep = {k: (v - y_near) * df for k, v in dep.items()}      # back to depths
            mm = line_mutuals(B, row, c, dep)
            r_ = dict(n=c, depths=dep)
            half = 0.5 if (c in cells_t and c == cells_t[-1]) else 1.0   # trap pair turns at mid-cell
            for key in ("trap", "acc"):
                if key in mm:
                    f_ = half if key == "trap" else 1.0
                    r_[key] = f_ * sgn * mm[key][row]
                    r_[key + "_xt"] = {o: f_ * sgn * v for o, v in mm[key].items() if o != row}
            if "loops" in mm:
                r_["loops_pH"] = mm["loops"]
            rec.append(r_)
        # design-current referred profiles for hardware.launcher.back_annotate (theta = 2 pi M I_design / Phi0)
        tr = [(r_["n"], r_["trap"] / sc["trap"]) for r_ in rec if "trap" in r_]
        ac = [(r_["n"], r_["acc"] / sc["acc"]) for r_ in rec if "acc" in r_]
        Mt, Ma = np.asarray(tg["trap"]), np.asarray(tg["acc"])
        dev_t = max(abs(M - Mt[n]) for n, M in tr) if tr else 0.0
        dev_a = max(abs(M - Ma[n]) for n, M in ac) if ac else 0.0
        q_other = [r for r in ("A0", "A1", "B1", "B0") if r != row and r[0] == row[0]][0]
        dummy = "D_A" if row[0] == "A" else "D_B"
        xt = crosstalk_metrics(rec, row, q_other, dummy)
        loops = max((abs(r_.get("loops_pH", 0.0)) for r_ in rec), default=0.0)
        out[row] = dict(coords="rail", line_model=LINE_MODEL,
                        trap=dict(cells=[n for n, _ in tr], M_pH=[M for _, M in tr]),
                        accelerator=dict(cells=[n for n, _ in ac], M_pH=[M for _, M in ac]),
                        drive_current_uA=dict(trap=sc["I_trap_uA"], accelerator=sc["I_acc_uA"]),
                        design_current_uA=dict(trap=tg["trap_I_uA"], accelerator=tg["acc_I_uA"]),
                        note="M_pH referred to the design currents: M_drawn * I_drive / I_design",
                        max_dev_from_target_pH=dict(trap=dev_t, accelerator=dev_a,
                                                    trap_peak=float(Mt.max()), accelerator_peak=float(Ma.max())),
                        crosstalk=xt,
                        trap_loop_to_acc_loop_mutual_pH_per_cell_max=loops,
                        profile=[{k: v for k, v in r_.items()} for r_ in rec])
        say(f"as drawn {row}: |M - target| max trap {dev_t:.4f} (peak {Mt.max():.4f}) acc {dev_a:.4f} "
            f"(peak {Ma.max():.4f}) pH at design current; peak-normalised cross-talk into {q_other}: "
            f"trap {100 * xt['trap']['other_rail_peak_norm']:.1f} %, acc {100 * xt['acc']['other_rail_peak_norm']:.1f} %")
    return out


def crosstalk_metrics(rec, row, other, dummy):
    """rec: per-cell dicts with '<line>' (own mutual) and '<line>_xt' {row: mutual}. Peak-normalised: the largest
    mutual into the victim anywhere along the line / the largest own mutual (what the victim feels relative to the
    launch row's peak flux). At-peak: victim / own over cells where the own mutual is >= 50 % of its peak."""
    out = {}
    for key in ("trap", "acc"):
        rr = [r_ for r_ in rec if key in r_]
        if not rr:
            continue
        own = np.array([abs(r_[key]) for r_ in rr])
        vic = np.array([abs(r_[key + "_xt"][other]) for r_ in rr])
        dum = np.array([abs(r_[key + "_xt"][dummy]) for r_ in rr])
        big = own >= 0.5 * own.max()
        out[key] = dict(other_rail=other, other_rail_peak_norm=float(vic.max() / own.max()),
                        other_rail_at_peak=float((vic[big] / own[big]).max()),
                        dummy=dummy, dummy_peak_norm=float(dum.max() / own.max()), own_peak_pH=float(own.max()))
    return out


def single_ended_reference(arch, sz_rev_a, rows=("A0", "A1"), stride=2):
    """the rev-A single-ended lines as drawn by their own sizing (both lines in their shared slot, current
    returning in the ground), same 2D model and the same metrics as as_drawn()"""
    from hardware import layout as LY
    B = _nolines_block(arch, sz_rev_a)
    Bd = LY.Block(arch, sz_rev_a)
    out = {}
    for row in rows:
        q_other = [r for r in ("A0", "A1", "B1", "B0") if r != row and r[0] == row[0]][0]
        dummy = "D_A" if row[0] == "A" else "D_B"
        cells_t = [c for c in Bd.line_cells(row, "trap") if 0 <= c <= Bd.N - 2]
        cells_a = [c for c in Bd.line_cells(row, "acc") if 0 <= c <= Bd.N - 2]
        df = -LY.RUNG_DIR[row]["G"]
        rec = []
        for c in sorted(set(cells_t) | set(cells_a))[::stride]:
            y_near, _ = B.strip_bounds(row, c, df)
            dep = {}
            if c in cells_t:
                dep["trap"] = (Bd.line_y(row, "trap", c) - y_near) * df
            if c in cells_a:
                dep["acc"] = (Bd.line_y(row, "acc", c) - y_near) * df
            mm = line_mutuals(B, row, c, dep)
            r_ = dict(n=c)
            for key in ("trap", "acc"):
                if key in mm:
                    r_[key] = mm[key][row]
                    r_[key + "_xt"] = {o: v for o, v in mm[key].items() if o != row}
            rec.append(r_)
        out[row] = crosstalk_metrics(rec, row, q_other, dummy)
    return out
