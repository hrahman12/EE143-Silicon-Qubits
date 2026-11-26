"""Rev B differential launcher lines (hardware/diffpairs.py, hardware/layout.py, hardware/netlist.py).

The claim to protect: every trap / accelerator line is ONE floating Nb loop between its _P and _N pins. It touches
no ground and no other line, so no fast-line current can return through the ground, in the drawn GDS and in the
circuit netlist. Plus: the sizing is the pair model, and the drawn pair couplings meet the (scaled) targets."""
import os

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def block():
    from hardware.architecture import Architecture
    from hardware import layout as LY
    arch = Architecture.from_results(ROOT)
    lib, cell, ports, blk = LY.build_block(arch)
    return arch, cell, ports, blk


def test_sizing_is_differential(block):
    arch, cell, ports, blk = block
    from hardware.diffpairs import LINE_MODEL
    assert blk.sz.get("line_model") == LINE_MODEL
    for row, sc in blk.sz["line_scale"].items():
        assert 0.5 < sc["trap"] <= 1.0 and 0.5 < sc["acc"] <= 1.0, (row, sc)       # drive current <= 2x design


def test_pins_come_in_pairs(block):
    arch, cell, ports, blk = block
    pairs = {}
    for p in ports:
        if p.get("pair"):
            pairs.setdefault(p["pair"], set()).add(p["polarity"])
    assert len(pairs) == 8 and all(v == {"P", "N"} for v in pairs.values()), pairs
    assert not [p for p in ports if p.get("kind") == "internal_short" and p["name"].startswith(("TRAP", "ACC"))]


def test_every_pair_is_one_floating_loop(block):
    """on the drawn polygons: P and N are the same Nb piece, and that piece carries no other pin (no ground)"""
    from shapely.geometry import Polygon, Point
    from shapely.ops import unary_union
    arch, cell, ports, blk = block
    nb = unary_union([Polygon(p.points).buffer(0) for p in cell.get_polygons(layer=1, datatype=0)])
    comps = list(nb.geoms) if hasattr(nb, "geoms") else [nb]

    def comp(p):
        pt = Point(p["x"], p["y"])
        return [i for i, c in enumerate(comps) if c.distance(pt) < 0.05]
    ext = [p for p in ports if p.get("kind") != "internal_short"]
    for p in ports:
        if p.get("polarity") != "P":
            continue
        n = next(q for q in ports if q.get("pair") == p["pair"] and q.get("polarity") == "N")
        cp, cn = comp(p), comp(n)
        assert len(cp) == 1 and cp == cn, f"{p['pair']}: P and N are not one piece"
        others = [q["name"] for q in ext if q["name"] not in (p["name"], n["name"]) and comp(q) == cp]
        assert not others, f"{p['pair']} loop also touches {others}"


def test_netlist_control_lines_are_floating():
    """in the circuit netlist no control-line node is tied to ground except through the 1 GOhm DC bleed"""
    from hardware.architecture import Architecture
    from hardware import netlist as NL
    arch = Architecture.from_results(ROOT)
    text, _ = NL.build(arch)
    for ln in text.splitlines():
        tok = ln.split()
        if not tok or tok[0][0] not in "LRI" or not tok[0][1:3] in ("TR", "AC"):
            continue
        if tok[0].startswith(("RTR", "RAC")):
            assert tok[3] == "1e9", ln
            continue
        assert "0" not in tok[1:3], f"control line element to ground: {ln}"


def test_drawn_pairs_meet_targets():
    """per-cell pair mutuals of the drawn legs vs the targets (at the design current): within 5 % of the peak
    except at the launch-end tail, where even the deepest compact pair leaves a residual (documented)"""
    from hardware.architecture import Architecture
    from hardware import layout as LY
    from hardware.diffpairs import as_drawn
    arch = Architecture.from_results(ROOT)
    sz = LY.get_sizing(arch)
    lt = LY.launcher_targets(arch)
    ad = as_drawn(arch, sz, stride=3, say=lambda *a: None)
    for row in ("A0", "A1"):
        Mt, Ma = np.asarray(lt[row]["trap"]), np.asarray(lt[row]["acc"])
        for key, M, cells, vals in (("trap", Mt, ad[row]["trap"]["cells"], ad[row]["trap"]["M_pH"]),
                                    ("acc", Ma, ad[row]["accelerator"]["cells"], ad[row]["accelerator"]["M_pH"])):
            dev = np.array([abs(v - M[c]) for c, v in zip(cells, vals) if M[c] > 0.15 * M.max()])
            assert dev.max() <= 0.05 * M.max() + 1e-12, (row, key, dev.max() / M.max())
