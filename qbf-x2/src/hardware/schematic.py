"""Unit-cell schematics of QBF-X2 drawn with schemdraw: rail cell, gate coupler cell, beam-splitter cell,
injector and catcher. Values are filled in from the architecture."""
from __future__ import annotations

import schemdraw
import schemdraw.elements as elm

from hardware.architecture import Architecture


def draw(arch: Architecture, path_png: str, path_svg: str):
    ev = arch.element_values()
    L = ev["rail_inductor"]["L_nH"]
    Ls = ev["coupler_shared_inductor"]["L_s_pH"]
    Cc = ev["coupler_capacitor"]["C_c_fF"]
    Ic = ev["rail_junction"]["Ic_nA"]
    Cn = ev["rail_junction"]["C_fF"]
    IcM = ev["middle_rail_junction"]["EJ_GHz"] * 2.0128
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=9, unit=2.2)
        # (a) rail cell
        d += elm.Label().label("(a) rail cell (one per 2 um)", fontsize=10).at((0, 2.6))
        d += (n0 := elm.Dot().at((0, 1)))
        d += elm.Inductor2(loops=3).right().label(f"L = {L:.2f} nH\n(granular Al)")
        d += (n1 := elm.Dot())
        d += elm.Josephson().down().at(n1.center).label(f"{Ic:.0f} nA\n{Cn:.2f} fF", loc="bottom")
        d += elm.Ground()
        # (b) coupler cell
        d += elm.Label().label("(b) gate coupler cell (A1-B1), x g(n)", fontsize=10).at((6.5, 2.6))
        d += (a0 := elm.Dot().at((6.5, 1)))
        d += elm.Inductor2(loops=3).right().label(f"(1-k) L", loc="top")
        d += (a1 := elm.Dot())
        d += elm.Label().at((a1.center[0] - 0.55, a1.center[1] - 0.45)).label("A1_n", fontsize=9)
        d += elm.Josephson().down().at(a1.center)
        d += (s := elm.Dot())
        d += elm.Label().at((s.center[0] - 0.65, s.center[1])).label("strip", fontsize=9)
        d += elm.Inductor2(loops=2).right().at(s.center).label(f"L_s = {Ls:.1f} pH", loc="top")
        d += elm.Ground()
        d += elm.Josephson().down().at(s.center).flip()
        d += (b1 := elm.Dot().label("B1_n", loc="left"))
        d += elm.Line().at(a1.center).right(0.9)
        d += elm.Capacitor().right(1.6).label(f"C_c = {Cc:.2f} fF", loc="top")
        d += elm.Line().down(4.4)
        d += elm.Line().left(2.5).to(b1.center)
        # (c) beam-splitter cell
        d += elm.Label().label("(c) beam-splitter cell (qubit A rows)", fontsize=10).at((0, -4.0))
        d += (u := elm.Dot().at((0, -5)).label("A0_n", loc="left"))
        d += elm.Josephson().down().label("rail JJ", loc="top")
        d += (m := elm.Dot().label("M_n", loc="left"))
        d += elm.Josephson().down().label("rail JJ", loc="top")
        d += elm.Dot().label("A1_n", loc="left")
        d += elm.Josephson().right(3.0).at(m.center)
        d += elm.Label().at((m.center[0] + 3.4, m.center[1] - 0.95)).label(f"middle-rail JJ: E_J/E_C = 2,\n{IcM:.0f} nA, E_S = {arch.E_S_GHz:.2f} GHz", fontsize=9)
        d += elm.Dot().label("M_n+1", loc="right")
        # (d) injector and catcher
        d += elm.Label().label("(d) injector / catcher (proposed)", fontsize=10).at((7.2, -4.0))
        d += (i0 := elm.Dot().at((6.5, -5)))
        d += elm.SourceI().down().label("pulse\n(UNRESOLVED:\ncoherent launch)", loc="bottom")
        d += elm.Ground()
        d += elm.Line().right(3.2).at(i0.center)
        d += (ij := elm.Dot().label("row start", loc="top"))
        d += elm.Josephson().down().at(ij.center).label("2 I_c", loc="bottom")
        d += elm.Ground()
        d += elm.Line().right(2.6).at(ij.center)
        d += elm.Inductor2(loops=4).down().label("catcher loop\n20 nH -> dispersive\nreadout (QFX-1)", loc="bottom")
        d += elm.Ground()
        d.save(path_png, dpi=170)
        d.save(path_svg)
