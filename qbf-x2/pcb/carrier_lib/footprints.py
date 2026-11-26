"""Inline footprint definitions for the QBF-X2 carrier.

Each footprint is described once (KiCad local frame: mm, y DOWN, unrotated) and written twice:
  * into the project library  qbfx2.pretty/<name>.kicad_mod   (so KiCad's library-parity DRC test passes)
  * into the board, placed, with nets                           (board instance)
"""
import math

from . import geom as G


from carrier_lib.ids import U  # noqa: E402  (deterministic ids)


def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Footprint:
    def __init__(self, name, descr, tags, attr, layer="F.Cu"):
        self.name, self.descr, self.tags, self.attr, self.layer = name, descr, tags, attr, layer
        self.pads, self.gfx, self.texts, self.models, self.keepouts = [], [], [], [], []
        self.ref_at, self.ref_layer, self.ref_size = (0, -2), "F.SilkS", 0.8
        self.val_at = (0, 2)

    # --- builders (local KiCad coordinates, y down)
    def pad(self, num, kind, shape, at, size, layers, rot=0.0, drill=None, clearance=None, rratio=None,
            mask_margin=None, pintype="passive"):
        self.pads.append(dict(num=str(num), kind=kind, shape=shape, at=at, size=size, layers=layers, rot=rot,
                              drill=drill, clearance=clearance, rratio=rratio, mask_margin=mask_margin,
                              pintype=pintype))

    def line(self, layer, a, b, w):
        self.gfx.append(("fp_line", layer, a, b, w))

    def rect(self, layer, a, b, w, fill=False):
        self.gfx.append(("fp_rect", layer, a, b, w, fill))

    def circle(self, layer, c, r, w, fill=False):
        self.gfx.append(("fp_circle", layer, c, r, w, fill))

    def arc(self, layer, a, m, b, w):
        self.gfx.append(("fp_arc", layer, a, m, b, w))

    def poly(self, layer, pts, w=0.0, fill=True):
        self.gfx.append(("fp_poly", layer, pts, w, fill))

    def text(self, layer, s, at, size=0.6, thick=None, rot=0.0):
        self.texts.append((layer, s, at, size, thick or round(size * 0.15, 3), rot))

    def model(self, path, offset=(0, 0, 0), rotate=(0, 0, 0)):
        self.models.append((path, offset, rotate))

    # --- serialisation
    def _gfx_sexpr(self, g, ts):
        tag = f" (tstamp {U()})" if ts else ""
        k = g[0]
        if k == "fp_line":
            _, layer, a, b, w = g
            return (f'(fp_line (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) '
                    f'(stroke (width {f(w)}) (type solid)) (layer "{layer}"){tag})')
        if k == "fp_rect":
            _, layer, a, b, w, fill = g
            return (f'(fp_rect (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) (stroke (width {f(w)}) '
                    f'(type solid)) (fill {"solid" if fill else "none"}) (layer "{layer}"){tag})')
        if k == "fp_circle":
            _, layer, c, r, w, fill = g
            return (f'(fp_circle (center {f(c[0])} {f(c[1])}) (end {f(c[0] + r)} {f(c[1])}) (stroke (width {f(w)}) '
                    f'(type solid)) (fill {"solid" if fill else "none"}) (layer "{layer}"){tag})')
        if k == "fp_arc":
            _, layer, a, m, b, w = g
            return (f'(fp_arc (start {f(a[0])} {f(a[1])}) (mid {f(m[0])} {f(m[1])}) (end {f(b[0])} {f(b[1])}) '
                    f'(stroke (width {f(w)}) (type solid)) (layer "{layer}"){tag})')
        if k == "fp_poly":
            _, layer, pts, w, fill = g
            xy = " ".join(f"(xy {f(p[0])} {f(p[1])})" for p in pts)
            return (f'(fp_poly (pts {xy}) (stroke (width {f(w)}) (type solid)) (fill {"solid" if fill else "none"}) '
                    f'(layer "{layer}"){tag})')
        raise ValueError(k)

    def _pad_sexpr(self, p, rot_abs, net=None, ts=False):
        s = f'(pad "{p["num"]}" {p["kind"]} {p["shape"]} (at {f(p["at"][0])} {f(p["at"][1])}'
        a = (p["rot"] + rot_abs) % 360
        s += f' {f(a)})' if abs(a) > 1e-9 else ')'
        s += f' (size {f(p["size"][0])} {f(p["size"][1])})'
        if p["drill"] is not None:
            s += f' (drill {f(p["drill"])})'
        s += " (layers " + " ".join(f'"{l}"' for l in p["layers"]) + ")"
        if p["rratio"] is not None:
            s += f' (roundrect_rratio {f(p["rratio"])})'
        if net is not None and p["kind"] != "np_thru_hole":
            s += f' (net {net[0]} "{net[1]}")'
        if p["kind"] != "np_thru_hole" and ts:
            s += f' (pintype "{p["pintype"]}")'
        if p["mask_margin"] is not None:
            s += f' (solder_mask_margin {f(p["mask_margin"])})'
        if p["clearance"] is not None:
            s += f' (clearance {f(p["clearance"])})'
        if ts:
            s += f" (tstamp {U()})"
        return s + ")"

    def _keepout_sexpr(self, k, ts):
        layers, pts = k
        xy = " ".join(f"(xy {f(p[0])} {f(p[1])})" for p in pts)
        lay = " ".join(f'"{l}"' for l in layers)
        tag = f" (tstamp {U()})" if ts else ""
        return (f'(zone (net 0) (net_name "") (layers {lay}){tag} (hatch edge 0.5) (connect_pads (clearance 0)) '
                f'(min_thickness 0.25) (filled_areas_thickness no) (keepout (tracks allowed) (vias not_allowed) '
                f'(pads allowed) (copperpour not_allowed) (footprints allowed)) '
                f'(fill (thermal_gap 0.5) (thermal_bridge_width 0.5)) (polygon (pts {xy})))')

    def library_text(self, lib):
        L = [f'(footprint "{self.name}" (version 20221018) (generator pcbnew)', f'  (layer "{self.layer}")',
             f'  (descr "{self.descr}")', f'  (tags "{self.tags}")', f'  (attr {self.attr})']
        L.append(f'  (fp_text reference "REF**" (at {f(self.ref_at[0])} {f(self.ref_at[1])}) (layer "{self.ref_layer}") '
                 f'(effects (font (size {f(self.ref_size)} {f(self.ref_size)}) (thickness {f(self.ref_size * 0.15)}))))')
        L.append(f'  (fp_text value "{self.name}" (at {f(self.val_at[0])} {f(self.val_at[1])}) (layer "F.Fab") '
                 f'(effects (font (size 0.6 0.6) (thickness 0.09))))')
        for (layer, s, at, size, th, r) in self.texts:
            L.append(f'  (fp_text user "{s}" (at {f(at[0])} {f(at[1])}{(" " + f(r)) if r else ""}) (layer "{layer}") '
                     f'(effects (font (size {f(size)} {f(size)}) (thickness {f(th)}))))')
        for g in self.gfx:
            L.append("  " + self._gfx_sexpr(g, False))
        for k in self.keepouts:
            L.append("  " + self._keepout_sexpr(k, False))
        for p in self.pads:
            L.append("  " + self._pad_sexpr(p, 0.0))
        for (path, off, rr) in self.models:
            L.append(f'  (model "{path}" (offset (xyz {f(off[0])} {f(off[1])} {f(off[2])})) (scale (xyz 1 1 1)) '
                     f'(rotate (xyz {f(rr[0])} {f(rr[1])} {f(rr[2])})))')
        L.append(")")
        return "\n".join(L) + "\n"

    def board_text(self, lib, ref, value, at_kicad, rot, netmap, sym_uuid=None, sheetfile=None,
                   ref_visible=True, ref_at=None, ref_rot=None, ref_layer=None, ref_size=None):
        """netmap: pad number -> (net code, net name)"""
        r = rot % 360
        L = [f'  (footprint "{lib}:{self.name}" (layer "{self.layer}")', f'    (tstamp {U()})',
             f'    (at {f(at_kicad[0])} {f(at_kicad[1])}{(" " + f(r)) if r else ""})',
             f'    (descr "{self.descr}")', f'    (tags "{self.tags}")']
        if sheetfile:
            L.append(f'    (property "Sheetfile" "{sheetfile}")')
            L.append('    (property "Sheetname" "")')
        if sym_uuid:
            L.append(f'    (path "/{sym_uuid}")')
        L.append(f'    (attr {self.attr})')
        ra = ref_at if ref_at is not None else self.ref_at
        rr = (r if ref_rot is None else ref_rot) % 360
        hide = "" if ref_visible else " hide"
        rl = ref_layer or self.ref_layer
        rs = ref_size or self.ref_size
        L.append(f'    (fp_text reference "{ref}" (at {f(ra[0])} {f(ra[1])}{(" " + f(rr)) if rr else ""}) '
                 f'(layer "{rl}"){hide} (tstamp {U()}) (effects (font (size {f(rs)} '
                 f'{f(rs)}) (thickness {f(max(0.1, rs * 0.15))}))))')
        L.append(f'    (fp_text value "{value}" (at {f(self.val_at[0])} {f(self.val_at[1])}{(" " + f(r)) if r else ""}) '
                 f'(layer "F.Fab") (tstamp {U()}) (effects (font (size 0.6 0.6) (thickness 0.09))))')
        for (layer, s, at, size, th, tr) in self.texts:
            a = (tr + r) % 360
            L.append(f'    (fp_text user "{s}" (at {f(at[0])} {f(at[1])}{(" " + f(a)) if a else ""}) (layer "{layer}") '
                     f'(tstamp {U()}) (effects (font (size {f(size)} {f(size)}) (thickness {f(th)}))))')
        for g in self.gfx:
            L.append("    " + self._gfx_sexpr(g, True))
        for k in self.keepouts:
            L.append("    " + self._keepout_sexpr(k, True))
        for p in self.pads:
            L.append("    " + self._pad_sexpr(p, r, netmap.get(p["num"], (0, "")), ts=True))
        for (path, off, rr3) in self.models:
            L.append(f'    (model "{path}" (offset (xyz {f(off[0])} {f(off[1])} {f(off[2])})) (scale (xyz 1 1 1)) '
                     f'(rotate (xyz {f(rr3[0])} {f(rr3[1])} {f(rr3[2])})))')
        L.append("  )")
        return "\n".join(L)

    # geometry helpers in the board frame (y up) for clearance checks
    def pads_board(self, pos, rot):
        """[(num, centre_board, size_board_aabb, pad)] for clearance checks (axis-aligned bounding box)."""
        out = []
        for p in self.pads:
            lx, ly = p["at"]
            c = G.rot((lx, -ly), rot)
            c = (pos[0] + c[0], pos[1] + c[1])
            a = math.radians(p["rot"] + rot)
            sx, sy = p["size"]
            ex = abs(sx * math.cos(a)) + abs(sy * math.sin(a))
            ey = abs(sx * math.sin(a)) + abs(sy * math.cos(a))
            out.append((p["num"], c, (ex, ey), p))
        return out


MODEL_DIR = "${KIPRJMOD}/3dmodels"


# ------------------------------------------------------------------------------------------------ catalogue
def smp_jack():
    fp = Footprint("SMP_Amphenol_SMP-MSLD-PCS-NM",
                   "SMP straight PCB jack, surface mount, non-magnetic (Amphenol RF SMP-MSLD-PCS-NM). "
                   "Generic land pattern: confirm against the vendor drawing before release. GCPW enters from local -x.",
                   "SMP RF coax vertical non-magnetic cryogenic", "smd")
    fp.pad(1, "smd", "circle", (0, 0), (0.75, 0.75), ["F.Cu", "F.Paste", "F.Mask"], clearance=0.45)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fp.pad(2, "smd", "rect", (sx * 1.45, sy * 1.45), (1.1, 1.1), ["F.Cu", "F.Paste", "F.Mask"])
    fp.circle("F.Fab", (0, 0), 2.095, 0.1)
    fp.circle("F.Fab", (0, 0), 0.25, 0.05)
    rs = 3.05                                     # silk arc with a gap where the mask-free GCPW corridor enters (-x)
    a0, a1 = math.radians(220), math.radians(140)
    fp.arc("F.SilkS", (rs * math.cos(a0), rs * math.sin(a0)), (rs, 0.0), (rs * math.cos(a1), rs * math.sin(a1)), 0.12)
    fp.circle("F.CrtYd", (0, 0), 3.25, 0.05)
    fp.text("F.Fab", "${REFERENCE}", (0, -1.0), 0.5)
    fp.ref_at, fp.val_at, fp.ref_layer = (0, -3.9), (0, 2.6), "F.Fab"
    fp.model(f"{MODEL_DIR}/SMP_MSLD_PCS_NM.step")
    return fp


def micro_d(md):
    fp = Footprint("MicroD_15P_Glenair_MWDM2L-15PCBRP",
                   "Micro-D 15 pin plug, right-angle PCB (Glenair MWDM2L-15PCBRP-.110). Tails on a 2.54 mm grid, "
                   "2 rows (8+7). Land pattern and pin-to-tail map TO CONFIRM against the Glenair drawing.",
                   "micro-D MWDM 15 right-angle DC connector", "through_hole")
    p = md["pitch"]
    for k in range(1, 9):
        fp.pad(k, "thru_hole", "rect" if k == 1 else "circle", (-3.5 * p + (k - 1) * p, 0), (md["pad"], md["pad"]),
               ["*.Cu", "*.Mask"], drill=md["drill"])
    for k in range(9, 16):
        fp.pad(k, "thru_hole", "circle", (-3.0 * p + (k - 9) * p, -md["row_dy"]), (md["pad"], md["pad"]),
               ["*.Cu", "*.Mask"], drill=md["drill"])
    my = -(md["mount_y"] - md["y_row1"])
    for sx in (-1, 1):
        fp.pad("SH", "thru_hole", "circle", (sx * md["mount_dx"], my), (md["mount_pad"], md["mount_pad"]),
               ["*.Cu", "*.Mask"], drill=md["mount_drill"])
    x0, x1, yb, yf = -11.9, 11.9, 1.6, -8.0
    fp.rect("F.Fab", (x0, yf), (x1, yb), 0.1)
    fp.rect("F.Fab", (-7.4, yf - 0.0), (7.4, yf + 2.2), 0.1)
    fp.line("F.SilkS", (x0 - 0.15, yb + 0.15), (x1 + 0.15, yb + 0.15), 0.12)
    for sx in (-1, 1):
        fp.line("F.SilkS", (sx * (x1 + 0.15), yb + 0.15), (sx * (x1 + 0.15), -1.6), 0.12)
    fp.poly("F.SilkS", [(-3.5 * p - 0.3, 1.25), (-3.5 * p + 0.3, 1.25), (-3.5 * p, 0.85)], 0.1, True)  # pin 1
    fp.rect("F.CrtYd", (x0 - 0.5, yf - 0.3), (x1 + 0.5, yb + 0.5), 0.05)
    fp.text("F.Fab", "board edge", (0, -6.6), 0.5)
    fp.ref_at, fp.val_at, fp.ref_layer = (0, -6.0), (0, -3.6), "F.Fab"
    fp.model(f"{MODEL_DIR}/MicroD_15P_RA.step")
    return fp


def chip(name, kind):
    """IPC-7351 nominal 0603 land patterns (same numbers as the KiCad standard library)"""
    if kind == "R":
        padsz, px, descr = (0.8, 0.95), 0.825, "Resistor 0603 (1608 metric), thin film"
        model = "R_0603.step"
    else:
        padsz, px, descr = (0.9, 0.95), 0.775, "Capacitor 0603 (1608 metric), C0G"
        model = "C_0603.step"
    fp = Footprint(name, descr, "resistor 0603" if kind == "R" else "capacitor 0603", "smd")
    fp.pad(1, "smd", "roundrect", (-px, 0), padsz, ["F.Cu", "F.Paste", "F.Mask"], rratio=0.25)
    fp.pad(2, "smd", "roundrect", (px, 0), padsz, ["F.Cu", "F.Paste", "F.Mask"], rratio=0.25)
    fp.rect("F.Fab", (-0.8, -0.4), (0.8, 0.4), 0.1)
    fp.rect("F.CrtYd", (-1.48, -0.73), (1.48, 0.73), 0.05)
    fp.text("F.Fab", "${REFERENCE}", (0, 0), 0.4)
    fp.ref_size, fp.ref_at, fp.val_at, fp.ref_layer = 0.8, (0, -1.43), (0, 1.43), "F.Fab"
    fp.model(f"{MODEL_DIR}/{model}")
    return fp


def die_bondpads(pads_local, die_half, win_half, pin_marker):
    """U1: one PCB wire-bond landing pad per die pad (numbered as die_pads.json ids). The die itself is wire bonded."""
    fp = Footprint("QBFX2_DIE_BONDPADS",
                   f"QBF-X2 10 x 10 mm die in a {2 * win_half:.2f} mm through-window: {len(pads_local)} PCB wire-bond "
                   "landing pads (Cu, no paste) numbered as circuits/die_pads.json (rev B: 0.29 mm lands for the "
                   "differential pairs). Die rests on the sample-holder pedestal.",
                   "QBF-X2 die wirebond chip-on-board", "smd exclude_from_pos_files")
    for num, c, size in pads_local:
        fp.pad(num, "smd", "rect", c, size, ["F.Cu", "F.Mask"])
    h = die_half
    fp.rect("F.Fab", (-h, -h), (h, h), 0.1)
    fp.poly("F.Fab", [(-h, -h + 1.0), (-h, -h), (-h + 1.0, -h)], 0.1, False)
    fp.circle("F.Fab", pin_marker, 0.15, 0.05, True)
    fp.text("F.Fab", "QBF-X2 die", (0, -0.8), 0.8)
    fp.text("F.Fab", "${REFERENCE}", (0, 0.8), 0.8)
    c = win_half + 0.95
    fp.rect("F.CrtYd", (-c - 0.2, -c - 0.2), (c + 0.2, c + 0.2), 0.05)
    fp.ref_at, fp.val_at = (0, -(c + 1.2)), (0, 2.2)
    fp.ref_layer = "F.Fab"
    fp.model(f"{MODEL_DIR}/QBFX2_die_bonded.step")
    return fp


def mounting_hole(drill, pad):
    fp = Footprint("MountingHole_2.7mm_M2.5_Pad", "Mounting hole M2.5, plated, pad 5 mm, GND",
                   "mounting hole M2.5", "exclude_from_pos_files exclude_from_bom")
    fp.pad(1, "thru_hole", "circle", (0, 0), (pad, pad), ["*.Cu", "*.Mask"], drill=drill)
    fp.circle("F.Fab", (0, 0), pad / 2, 0.1)
    fp.circle("F.CrtYd", (0, 0), pad / 2 + 0.25, 0.05)
    fp.ref_layer, fp.ref_at, fp.val_at = "F.Fab", (0, -3.3), (0, 3.3)
    return fp


def fiducial():
    fp = Footprint("Fiducial_1.0mm_Mask2.0mm", "Fiducial 1.0 mm Cu dot, 2.0 mm mask opening",
                   "fiducial", "smd board_only exclude_from_bom")
    fp.pad("", "smd", "circle", (0, 0), (1.0, 1.0), ["F.Cu", "F.Mask"], mask_margin=0.5, clearance=0.6)
    fp.circle("F.CrtYd", (0, 0), 1.25, 0.05)
    fp.circle("F.Fab", (0, 0), 1.0, 0.1)
    fp.ref_layer, fp.ref_at, fp.val_at = "F.Fab", (0, -1.8), (0, 1.8)
    return fp


def dowel_hole(d):
    fp = Footprint("NPTH_Dowel_1.6mm", "Non-plated 1.6 mm hole for a 1.5 mm alignment dowel in the sample-holder base",
                   "NPTH dowel alignment", "board_only exclude_from_pos_files exclude_from_bom")
    fp.pad("", "np_thru_hole", "circle", (0, 0), (d, d), ["*.Cu", "*.Mask"], drill=d)
    fp.circle("F.CrtYd", (0, 0), d / 2 + 0.3, 0.05)
    fp.circle("F.Fab", (0, 0), d / 2, 0.1)
    fp.ref_layer, fp.ref_at, fp.val_at = "F.Fab", (0, -1.6), (0, 1.6)
    return fp
