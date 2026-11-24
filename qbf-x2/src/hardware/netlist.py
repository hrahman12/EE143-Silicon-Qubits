"""Complete element-level netlist of QBF-X2 (JoSIM-style SPICE), generated from the architecture.

Node names: <row>_<n> for rail nodes, S<pair>_<n> for shared coupler strips, M<qubit>_<n> for beam-splitter middle
rails, 0 = ground plane. Junction model parameters are the proposed design values (architecture.py).
The netlist is a design document: it has not been simulated with JoSIM here (JoSIM was not installable in this
environment); its classical content is the circuit simulated by classical/sg.py.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

from hardware.architecture import Architecture

ROWS = ["D_A", "A0", "A1", "B1", "B0", "D_B"]
PAIRS = {"DA": ("D_A", "A0"), "G": ("A1", "B1"), "DB": ("B0", "D_B")}     # dummy, gate, dummy couplers
QUBIT_ROWS = {"A": ("A0", "A1"), "B": ("B1", "B0")}


def _env(arch: Architecture, n: int) -> float:
    s = {d["name"]: d for d in arch.sections()}
    t0, tp, t1 = s["taper_in"], s["coupler"], s["taper_out"]
    if t0["start"] <= n < t0["start"] + t0["cells"]:
        j = n - t0["start"]
        return 0.5 * (1 - math.cos(math.pi * (j + 0.5) / t0["cells"]))
    if tp["start"] <= n < tp["start"] + tp["cells"]:
        return 1.0
    if t1["start"] <= n < t1["start"] + t1["cells"]:
        j = n - t1["start"]
        return 0.5 * (1 + math.cos(math.pi * (j + 0.5) / t1["cells"]))
    return 0.0


def _in_section(arch: Architecture, n: int, name: str, mirrored: bool) -> bool:
    N = arch.n_cells
    m = N - 1 - n if mirrored else n
    for d in arch.sections():
        if d["name"] == name and d["start"] <= m < d["start"] + d["cells"]:
            return True
    return False


def build(arch: Architecture) -> tuple[str, dict]:
    ev = arch.element_values()
    r = arch.rail
    N = arch.n_cells
    L = r.L_cell_H
    Cj = 1.92e-15                                    # junction capacitance at Jc = 2.08 uA/um^2 (see FEASIBILITY)
    Csh = r.C_F - Cj                                 # node shunt, reduced by C_c inside couplers (compensation)
    lines = [f"* QBF-X2 two-flying-fluxon collision processor - PRELIMINARY design netlist (not fabrication-ready)",
             f"* rows {ROWS}; {N} cells per row, pitch {r.pitch_um} um; design speed beta = {arch.beta:.3f}",
             f"* coupler k = {arch.k:.5f} (L_s = {arch.k * L * 1e12:.2f} pH), c = {arch.c:.4f} (C_c = {arch.c * r.C_F * 1e15:.3f} fF)",
             f".model JJR jj(rtype=0, cap={Cj:.4g}, icrit={r.Ic_A:.4g})",
             f".model JJM jj(rtype=0, cap={ev['middle_rail_junction']['area_um2'] * 50e-15:.4g}, "
             f"icrit={ev['middle_rail_junction']['EJ_GHz'] * 1e9 * 6.62607015e-34 * 2 * math.pi / 2.067833848e-15:.4g})",
             f".model JJI jj(rtype=1, cap={2 * Cj:.4g}, icrit={2 * r.Ic_A:.4g}, rn=2k, r0=200k)"]
    count = Counter()
    pair_of = {row: key for key, (a, b) in PAIRS.items() for row in (a, b)}
    for row in ROWS:
        mirrored = row.startswith("B") or row == "D_B"            # B and its dummy run from the right
        qubit = "A" if row in QUBIT_ROWS["A"] else "B" if row in QUBIT_ROWS["B"] else None
        for n in range(N):
            g = _env(arch, n)
            node = f"{row}_{n}"
            # return terminal: coupler strip, BS middle rail or ground
            if g > 0:
                ret = f"S{pair_of[row]}_{n}"
            elif qubit and (_in_section(arch, n, "BS_prep", mirrored) or _in_section(arch, n, "BS_analysis", mirrored)):
                ret = f"M{qubit}_{n}"
            else:
                ret = "0"
            lines.append(f"B{row}_{n} {node} {ret} JJR area=1")
            count["junction (rail)"] += 1
            csh = Csh - arch.c * r.C_F * g
            lines.append(f"C{row}_{n} {node} 0 {csh:.4g}")
            count["capacitor (node shunt)"] += 1
            if n < N - 1:
                lser = L * (1 - arch.k * 0.5 * (g + _env(arch, n + 1)))
                lines.append(f"L{row}_{n} {node} {row}_{n + 1} {lser:.5g}")
                count["inductor (rail, granular Al)"] += 1
        # injector at the launch end, catcher loop at the far end
        start, end = (f"{row}_{N - 1}", f"{row}_0") if mirrored else (f"{row}_0", f"{row}_{N - 1}")
        if not row.startswith("D"):
            lines.append(f"BINJ_{row} {start} 0 JJI area=1")
            lines.append(f"IINJ_{row} 0 {start} pwl(0 0 20p 0 30p {1.2 * 2 * r.Ic_A:.4g} 50p 0)")
            lines.append(f"LCATCH_{row} {end} 0 20n")
            count["injector junction"] += 1
            count["injector pulse source"] += 1
            count["catcher loop inductor"] += 1
            for j in range(arch.n_inject, arch.n_inject + arch.n_accel):
                nn = N - 1 - j if mirrored else j
                lines.append(f"IACC_{row}_{j} 0 {row}_{nn} pwl(0 0 50p 0 60p {0.05 * r.Ic_A:.4g} 200p {0.05 * r.Ic_A:.4g} 210p 0)")
                count["accelerator bias source"] += 1
    # coupler strips (shared ground return) and coupling capacitors
    for key, (ra, rb) in PAIRS.items():
        nodes = [n for n in range(N) if _env(arch, n) > 0]
        for n in nodes:
            g = _env(arch, n)
            nxt = f"S{key}_{n + 1}" if n + 1 in nodes else "0"
            lines.append(f"LS{key}_{n} S{key}_{n} {nxt} {arch.k * L * g:.5g}")
            count["inductor (shared coupler strip)"] += 1
            lines.append(f"CC{key}_{n} {ra}_{n} {rb}_{n} {arch.c * r.C_F * g:.4g}")
            count["capacitor (coupler)"] += 1
        lines.append(f"LS{key}_entry S{key}_{nodes[0]} 0 1p")
    # beam-splitter middle rails: series junctions between consecutive middle-rail nodes
    for q, (r0, r1) in QUBIT_ROWS.items():
        mirrored = q == "B"
        for sec in ("BS_prep", "BS_analysis"):
            ns = [n for n in range(N) if _in_section(arch, n, sec, mirrored)]
            for a_, b_ in zip(ns[:-1], ns[1:]):
                lines.append(f"BM{q}_{a_} M{q}_{a_} M{q}_{b_} JJM area=1")
                count["junction (BS middle rail)"] += 1
            lines.append(f"LM{q}_{sec}_end M{q}_{ns[-1]} 0 1p")
            lines.append(f"LM{q}_{sec}_start M{q}_{ns[0]} 0 1p")
    lines += [".tran 0.1p 3000p 0 0.1p",
              ".print phase BA1_" + str(N // 2), ".print phase BB1_" + str(N // 2), ".end"]
    text = "\n".join(lines) + "\n"
    summary = dict(elements=dict(count), total_elements=sum(count.values()), cells_per_row=N, rows=ROWS,
                   junction_model_rail=dict(Ic_nA=r.Ic_A * 1e9, Cj_fF=Cj * 1e15, shunt_fF=Csh * 1e15),
                   source=arch.source)
    return text, summary


def parse(text: str) -> dict:
    """minimal parser used by the tests: element counts and node degrees."""
    deg = defaultdict(int)
    kinds = Counter()
    for ln in text.splitlines():
        if not ln or ln[0] in "*.":
            continue
        tok = ln.split()
        kinds[tok[0][0]] += 1
        for nd in tok[1:3]:
            deg[nd] += 1
    return dict(kinds=dict(kinds), nodes=len(deg), isolated=[n for n, d in deg.items() if d < 2 and n != "0"])
