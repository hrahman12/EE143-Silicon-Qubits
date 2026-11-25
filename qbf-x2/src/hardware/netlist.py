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
    Cj = ev["rail_junction"]["Cj_fF"] * 1e-15        # junction capacitance (architecture: Jc, specific capacitance)
    Csh = ev["rail_junction"]["shunt_fF"] * 1e-15    # node shunt, reduced by C_c inside couplers (compensation)
    mj = ev["middle_rail_junction"]
    lines = [f"* QBF-X2 two-flying-fluxon collision processor - PRELIMINARY design netlist (not fabrication-ready)",
             f"* rows {ROWS}; {N} cells per row, pitch {r.pitch_um} um; design speed beta = {arch.beta:.3f}",
             f"* coupler k = {arch.k:.5f} (L_s = {arch.k * L * 1e12:.2f} pH), c = {arch.c:.4f} (C_c = {arch.c * r.C_F * 1e15:.3f} fF)",
             f".model JJR jj(rtype=0, cap={Cj:.4g}, icrit={r.Ic_A:.4g})",
             f".model JJM jj(rtype=0, cap={mj['Cj_fF'] * 1e-15:.4g}, "
             f"icrit={mj['EJ_GHz'] * 1e9 * 6.62607015e-34 * 2 * math.pi / 2.067833848e-15:.4g})",
             f".model JJI jj(rtype=1, cap={2 * Cj:.4g}, icrit={2 * r.Ic_A:.4g}, rn=2k, r0=200k)"]
    count = Counter()
    launcher_rows = []
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
        # launcher at the launch end (load loop + trap and accelerator control lines, mutual coupling only) and
        # catcher loop at the far end
        start, end = (f"{row}_{N - 1}", f"{row}_0") if mirrored else (f"{row}_0", f"{row}_{N - 1}")
        if not row.startswith("D"):
            lines.append(f"LCATCH_{row} {end} 0 20n")
            count["catcher loop inductor"] += 1
            launcher_rows.append((row, mirrored, start))
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
                if mj["shunt_fF"] > 0:
                    lines.append(f"CM{q}_{a_} M{q}_{a_} M{q}_{b_} {mj['shunt_fF'] * 1e-15:.4g}")
                    count["capacitor (BS middle-rail shunt)"] += 1
            lines.append(f"LM{q}_{sec}_end M{q}_{ns[-1]} 0 1p")
            lines.append(f"LM{q}_{sec}_start M{q}_{ns[0]} 0 1p")
    # launchers: rail-end load loop (flux ramp inserts one fluxon), trap line (DC while holding, off at release),
    # accelerator line (on at release, off at t_off). Control lines are chains of small inductors, each coupled (K) to
    # the series inductor of one rail cell: theta_n = 2 pi M_n I / Phi0 (targets from hardware/launcher.py).
    lv = ev["launcher"]
    T_REL = 20000.0                                              # ns: loading and relaxation (~us) happen before
    L_SEG = 2e-12
    phi0 = 2.067833848e-15
    tau = lv["tau_ps"] * 1e-3
    t_off = lv["t_off_ns"]
    for row, mirrored, start in launcher_rows:
        lines.append(f"LLOAD_{row} {start} 0 {lv['load_loop']['L_nH']}n")
        lines.append(f"ILOAD_{row} 0 {start} pwl(0 0 1000n {phi0 / (lv['load_loop']['L_nH'] * 1e-9):.4g})")
        count["launcher load loop inductor"] += 1
        count["launcher load flux source"] += 1
        for tag, key, wave in (("TR", "trap_line", f"pwl(0 0 1n {{I}} {T_REL:.0f}n {{I}} {T_REL + tau:.4f}n 0)"),
                               ("AC", "accelerator_line", f"pwl(0 0 {T_REL:.0f}n 0 {T_REL + tau:.4f}n {{I}} "
                                                          f"{T_REL + t_off:.4f}n {{I}} {T_REL + t_off + tau:.4f}n 0)")):
            line = lv[key]
            I = line["I_uA"] * 1e-6
            nodes = [f"{tag}{row}_{j}" for j in range(len(line["cells"]) + 1)]
            lines.append(f"I{tag}_{row} 0 {nodes[0]} " + wave.format(I=f"{I:.4g}"))
            count[f"{key.replace('_', ' ')} source"] += 1
            for j, (cell, M) in enumerate(zip(line["cells"], line["M_pH"])):
                rail_ind = f"L{row}_{N - 2 - cell}" if mirrored else f"L{row}_{cell}"
                lines.append(f"L{tag}{row}_{cell} {nodes[j]} {nodes[j + 1]} {L_SEG:.3g}")
                lser = L * (1 - arch.k * 0.5 * (_env(arch, N - 2 - cell if mirrored else cell)
                                                + _env(arch, N - 1 - cell if mirrored else cell + 1)))
                kc = M * 1e-12 / math.sqrt(L_SEG * lser)
                lines.append(f"K{tag}{row}_{cell} L{tag}{row}_{cell} {rail_ind} {kc:.4g}")
                count[f"{key.replace('_', ' ')} inductor"] += 1
                count[f"{key.replace('_', ' ')} coupling (K)"] += 1
            lines.append(f"L{tag}{row}_end {nodes[-1]} 0 {L_SEG:.3g}")
            count[f"{key.replace('_', ' ')} inductor"] += 1
    lines += [f"* release at t = {T_REL:.0f} ns; the transient below covers the launch and the gate",
              f".tran 0.1p {T_REL + 3:.0f}n {T_REL:.0f}n 0.1p",
              ".print phase BA1_" + str(N // 2), ".print phase BB1_" + str(N // 2), ".end"]
    text = "\n".join(lines) + "\n"
    summary = dict(elements=dict(count), total_elements=sum(count.values()), cells_per_row=N, rows=ROWS,
                   junction_model_rail=dict(Ic_nA=r.Ic_A * 1e9, Cj_fF=Cj * 1e15, shunt_fF=Csh * 1e15),
                   junction_model_middle_rail=dict(Ic_nA=mj["Ic_nA"], Cj_fF=mj["Cj_fF"], shunt_fF=mj["shunt_fF"]),
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
        if tok[0][0] == "K":                       # mutual inductance: references two inductors, not nodes
            continue
        for nd in tok[1:3]:
            deg[nd] += 1
    return dict(kinds=dict(kinds), nodes=len(deg), isolated=[n for n, d in deg.items() if d < 2 and n != "0"])
