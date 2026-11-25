"""Design-rule check of the QBF-X2 row block (klayout.db Region checks) with a documented rule deck.

Assumed process (all lithography e-beam; a research process, not a foundry PDK):
  NB    150 nm sputtered Nb on high-resistivity Si, e-beam lithography (ZEP) + SF6/Ar RIE.
        Ground plane, inner ground strips, low-g coupler strip ends, control/flux/gate CPW lines.
  GRAL  20 nm granular Al (0.5 nH/sq), e-beam lift-off (PMMA), in-situ Ar mill of the Nb/Al contact areas.
  AL1   30 nm Al bottom electrode, e-beam lift-off (PMMA/MMA): node pads, junction fingers, bottom plates.
  DIEL  100 nm PECVD SiNx (eps_r 7), patterned by e-beam lithography + CF4 RIE; crossovers and plate capacitors.
  AL2   30 nm Al top electrode, second e-beam lift-off: in-situ Ar ion mill (cleans AL1 and Nb contact areas),
        static oxidation (sets Jc = 2.1 uA/um^2 on every AL1/AL2 overlap that is not under DIEL), evaporation.
  The coupling capacitors need a dielectric BETWEEN AL1 and AL2, which a single-mask double-angle (shadow)
  evaporation cannot provide; the junctions are therefore of the two-step overlap ("cross-type") kind: an AL1
  finger crossed by an AL2 finger, area = product of the two drawn widths, insensitive to overlay error.
Consequence for the rule deck: every AL1 & AL2 overlap outside DIEL is a tunnel junction with the chip-wide Jc, so
it must either be an intended junction (area within +-5 % of its architecture target) or a contact large enough to
act as a short (>= 1 um^2: I_c >= 2.1 uA >> 80 nA). The same oxidation also covers the ion-milled Nb under AL2 and
under AL1, so Al-on-Nb contacts obey the same >= 1 um^2 rule.

Rule deck (um):
  NB.W     min width                                   0.40   (e-beam + RIE of 150 nm Nb)
  NB.S     min space                                   0.40
  GRAL.W   min width                                   0.20   (20 nm film, lift-off)
  GRAL.S   min space                                   0.30
  GRAL.C   granular Al under AL1 or on NB: overlap width >= 0.15 at every contact
  AL1.W    min width                                   0.10   (junction fingers; lift-off of 30 nm Al)
  AL1.S    min space                                   0.20
  AL2.W    min width                                   0.10
  AL2.S    min space                                   0.20
  JJ.CLASS every AL1 & AL2 - DIEL region: junction (area within +-5 % of a target) or contact (>= 1.00 um^2)
  JJ.W     junction regions: both sides >= 0.10
  JJ.S     junction to any other AL1 & AL2 region >= 0.50 (neighbouring junctions/contacts do not merge)
  JJ.N     junction counts equal the netlist: 6 N rail junctions and (n_bs - 1) per beam splitter
  CT.A     AL1 & NB and AL2 & NB contact regions (outside DIEL) >= 1.00 um^2
  CT.I     contacts that carry a control-line DC current (the AL2 trap line's feed and end contacts):
           area >= 2 I / J_c (80 uA -> 76 um^2), checked by extract.verify from the drawn contact boxes
           (the contact barrier gets the junction oxidation, J_c = 2.1 uA/um^2)
  AL2 lines over Nb (the trap line outside its slot, its crossings over the accelerator line) lie on SiNx
           everywhere (DIEL enclosure 0.25 um); their only Nb contacts are the two CT.I contacts
  DIEL.W   min width                                   0.50
  DIEL.S   min space                                   0.40
  DIEL.EN  AL1 & AL2 & DIEL (capacitors, crossings) enclosed by DIEL by >= 0.20 (top plate never touches the
           bottom plate at the dielectric edge, overlay 0.05 + sidewall)
  DIEL.SJ  DIEL to junction / contact regions >= 0.20 (no dielectric residue on a tunnel barrier)
  NB.FLOAT every NB polygon reaches the ground net through NB or Al contacts, or is a line that leaves the block at
           a port (no floating Nb islands)
"""
from __future__ import annotations

import json
import os

RULES = dict(
    NB_W=0.40, NB_S=0.40, GRAL_W=0.20, GRAL_S=0.30, GRAL_C=0.15, AL1_W=0.10, AL1_S=0.20, AL2_W=0.10, AL2_S=0.20,
    JJ_TOL=0.05, CONTACT_MIN=1.00, JJ_W=0.10, JJ_S=0.50, CT_A=1.00, DIEL_W=0.50, DIEL_S=0.40, DIEL_EN=0.20,
    DIEL_SJ=0.20,
)


def run(gds_path: str, arch=None, report_path: str | None = None, max_examples: int = 5) -> dict:
    import klayout.db as db
    from hardware.architecture import jj_area_for
    ly = db.Layout()
    ly.read(gds_path)
    top = ly.top_cell()
    dbu = ly.dbu
    um = lambda v: int(round(v / dbu))

    def reg(l, d=0):
        li = ly.find_layer(l, d)
        if li is None:
            return db.Region()
        r = db.Region(top.begin_shapes_rec(li))
        r.merged_semantics = True
        return r.merged()

    NB, GRAL, AL1, AL2, DIEL = reg(1), reg(2), reg(3), reg(4), reg(6)
    res = dict(gds=os.path.abspath(gds_path), rules=RULES, checks={}, process=__doc__.split("Rule deck")[0].strip())

    def ep_examples(ep):
        out = []
        for i, e in enumerate(ep.each()):
            if i >= max_examples:
                break
            b = e.bbox()
            out.append([round(b.left * dbu, 3), round(b.bottom * dbu, 3), round(b.right * dbu, 3), round(b.top * dbu, 3)])
        return out

    def poly_examples(r):
        out = []
        for i, p in enumerate(r.each()):
            if i >= max_examples:
                break
            b = p.bbox()
            out.append([round(b.left * dbu, 3), round(b.bottom * dbu, 3), round(b.right * dbu, 3), round(b.top * dbu, 3)])
        return out

    def add(name, n, desc, examples=None):
        res["checks"][name] = dict(violations=int(n), rule=desc, examples=examples or [])

    for nm, r, w, s in (("NB", NB, RULES["NB_W"], RULES["NB_S"]), ("GRAL", GRAL, RULES["GRAL_W"], RULES["GRAL_S"]),
                        ("AL1", AL1, RULES["AL1_W"], RULES["AL1_S"]), ("AL2", AL2, RULES["AL2_W"], RULES["AL2_S"]),
                        ("DIEL", DIEL, RULES["DIEL_W"], RULES["DIEL_S"])):
        ew = r.width_check(um(w))
        es = r.space_check(um(s))
        add(f"{nm}.W", ew.count(), f"{nm} min width {w} um", ep_examples(ew))
        add(f"{nm}.S", es.count(), f"{nm} min space {s} um", ep_examples(es))
    # granular-Al contacts
    gc = GRAL & (AL1 + NB)
    egc = gc.width_check(um(RULES["GRAL_C"]))
    add("GRAL.C", egc.count(), f"granular Al contact overlap width >= {RULES['GRAL_C']} um", ep_examples(egc))
    # junction classification
    ov = (AL1 & AL2) - DIEL
    targets = {}
    if arch is not None:
        targets = dict(rail=jj_area_for(arch.rail.EJ_GHz), middle=jj_area_for(arch.EJ_M_GHz))
    cls = dict(junction={k: 0 for k in targets}, contact=0, bad=[])
    jj_regions = db.Region()
    for poly in ov.each():
        a = poly.area() * dbu * dbu
        if a >= RULES["CONTACT_MIN"]:
            cls["contact"] += 1
            continue
        hit = [k for k, A in targets.items() if abs(a / A - 1) <= RULES["JJ_TOL"]]
        if hit:
            cls["junction"][hit[0]] += 1
            jj_regions.insert(poly)
        else:
            b = poly.bbox()
            cls["bad"].append(dict(area_um2=round(a, 5), bbox=[b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu]))
    add("JJ.CLASS", len(cls["bad"]), "AL1&AL2-DIEL: junction within +-5 % of target or contact >= 1 um^2",
        cls["bad"][:max_examples])
    ejw = jj_regions.width_check(um(RULES["JJ_W"]))
    add("JJ.W", ejw.count(), f"junction sides >= {RULES['JJ_W']} um", ep_examples(ejw))
    ejs = jj_regions.separation_check(ov - jj_regions, um(RULES["JJ_S"])) if not (ov - jj_regions).is_empty() else db.EdgePairs()
    ejs2 = jj_regions.space_check(um(RULES["JJ_S"]))
    add("JJ.S", ejs.count() + ejs2.count(), f"junction to other junction/contact >= {RULES['JJ_S']} um",
        ep_examples(ejs) + ep_examples(ejs2))
    n_exp = {}
    if arch is not None:
        from hardware.layout import bs_sections
        n_exp = dict(rail=6 * arch.n_cells, middle=sum(len(ns) - 1 for (_, _, ns) in bs_sections(arch)))
        bad_n = sum(1 for k in n_exp if cls["junction"].get(k, 0) != n_exp[k])
        add("JJ.N", bad_n, "junction counts equal the netlist", [dict(found=cls["junction"], expected=n_exp)])
    res["junctions"] = dict(found=cls["junction"], expected=n_exp, contacts=cls["contact"], targets_um2=targets)
    # Al-on-Nb contacts
    ct = ((AL1 & NB) + (AL2 & NB)).merged() - DIEL
    small = [p for p in ct.each() if p.area() * dbu * dbu < RULES["CT_A"]]
    add("CT.A", len(small), f"Al-on-Nb contact regions >= {RULES['CT_A']} um^2",
        [[round(p.bbox().left * dbu, 3), round(p.bbox().bottom * dbu, 3), round(p.area() * dbu * dbu, 4)] for p in small[:max_examples]])
    # dielectric enclosure of capacitor / crossing overlaps and keep-out from junctions and contacts
    cap = AL1 & AL2 & DIEL
    een = DIEL.enclosing_check(cap, um(RULES["DIEL_EN"]))
    outside = cap - DIEL.sized(-um(RULES["DIEL_EN"]))
    add("DIEL.EN", een.count() + outside.count(), f"capacitor overlaps enclosed by DIEL >= {RULES['DIEL_EN']} um",
        ep_examples(een) + poly_examples(outside))
    esj = DIEL.separation_check(ov, um(RULES["DIEL_SJ"]))
    touch = DIEL & ov.sized(um(RULES["DIEL_SJ"]) - 1)
    add("DIEL.SJ", esj.count() + touch.count(), f"DIEL to junctions/contacts >= {RULES['DIEL_SJ']} um",
        ep_examples(esj) + poly_examples(touch))
    # floating Nb: connectivity extraction (LayoutToNetlist): NB, AL1, AL2 are conductors; they join through
    # Al-on-Nb contacts (outside DIEL) and through AL1/AL2 contacts >= 1 um^2 (junction overlaps do not join)
    l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly, top, []))
    nb_ = l2n.make_layer(ly.layer(1, 0), "nb")
    a1_ = l2n.make_layer(ly.layer(3, 0), "al1")
    a2_ = l2n.make_layer(ly.layer(4, 0), "al2")
    di_ = l2n.make_layer(ly.layer(6, 0), "diel")
    c1 = (a1_ & nb_) - di_
    c2 = (a2_ & nb_) - di_
    c12 = ((a1_ & a2_) - di_).with_area(um(1.0) * um(1.0), None, False)
    l2n.register(c1, "c1")
    l2n.register(c2, "c2")
    l2n.register(c12, "c12")
    for lyr in (nb_, a1_, a2_, c1, c2, c12):
        l2n.connect(lyr)
    l2n.connect(nb_, c1); l2n.connect(a1_, c1)
    l2n.connect(nb_, c2); l2n.connect(a2_, c2)
    l2n.connect(a1_, c12); l2n.connect(a2_, c12)
    l2n.extract_netlist()
    bbox = top.bbox()
    gnd_net = l2n.probe_net(nb_, db.DPoint(bbox.left * dbu + 1.0, bbox.bottom * dbu + 1.0))
    floating = []
    for p in NB.each():
        b = p.bbox()
        on_edge = b.left <= bbox.left + 1 or b.right >= bbox.right - 1 or b.bottom <= bbox.bottom + 1 or b.top >= bbox.top - 1
        if on_edge:
            continue
        # a point inside the polygon
        pt = None
        for tr in db.Region(p).decompose_trapezoids_to_region().each():
            bb = tr.bbox()
            pt = db.DPoint((bb.left + bb.right) / 2 * dbu, (bb.bottom + bb.top) / 2 * dbu)
            break
        net = l2n.probe_net(nb_, pt) if pt is not None else None
        same = net is not None and gnd_net is not None and net.cluster_id == gnd_net.cluster_id
        if not same:
            floating.append([round(b.left * dbu, 2), round(b.bottom * dbu, 2), round(b.right * dbu, 2), round(b.top * dbu, 2)])
    add("NB.FLOAT", len(floating), "no floating Nb pieces (ground net or a line to a port)", floating[:max_examples])
    res["violations_total"] = int(sum(c["violations"] for c in res["checks"].values()))
    res["summary"] = {k: v["violations"] for k, v in res["checks"].items()}
    if report_path:
        os.makedirs(os.path.dirname(os.path.abspath(report_path)), exist_ok=True)
        json.dump(res, open(report_path, "w"), indent=1)
    return res
