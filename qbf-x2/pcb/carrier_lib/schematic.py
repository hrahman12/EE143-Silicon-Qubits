"""KiCad 7 schematic writer (format 20230121) with embedded lib_symbols.

Symbol library coordinates are y-up; schematic coordinates are y-down (mm). A pin at library (lx, ly) of a symbol
placed at (X, Y) with rotation r (counter-clockwise on screen) lands at
    (X, Y) + R(r) . (lx, -ly),   R(r) (x, y) = (x cos r + y sin r, -x sin r + y cos r)
Everything is kept on the 1.27 mm grid.
"""
import math
import uuid

GRID = 1.27


def U():
    return str(uuid.uuid4())


def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def g(n):
    """grid units -> mm"""
    return round(n * GRID, 4)


FONT = "(effects (font (size 1.27 1.27)))"
FONT_H = "(effects (font (size 1.27 1.27)) hide)"


def _pin(num, name, x, y, ang, length, typ="passive", hide=False):
    return (f'(pin {typ} line (at {f(x)} {f(y)} {ang}) (length {f(length)}){" hide" if hide else ""} '
            f'(name "{name}" {FONT}) (number "{num}" {FONT}))')


class SymbolDef:
    def __init__(self, lib_id, ref_prefix, value, pins, body, opts="", ref_at=(0, 3.81), val_at=(0, -3.81),
                 power=False, descr=""):
        self.lib_id, self.ref_prefix, self.value = lib_id, ref_prefix, value
        self.pins = pins            # [(num, name, x, y, ang, length, type, hide)]
        self.body, self.opts, self.ref_at, self.val_at, self.power, self.descr = body, opts, ref_at, val_at, power, descr

    def pin_xy(self, num):
        for p in self.pins:
            if p[0] == str(num):
                return p[2], p[3]
        raise KeyError(num)

    def sexpr(self):
        name = self.lib_id.split(":")[1]
        pw = " (power)" if self.power else ""
        L = [f'(symbol "{self.lib_id}"{pw} {self.opts} (in_bom yes) (on_board yes)',
             f'  (property "Reference" "{self.ref_prefix}" (at {f(self.ref_at[0])} {f(self.ref_at[1])} 0) '
             f'{FONT_H if self.power else FONT})',
             f'  (property "Value" "{self.value}" (at {f(self.val_at[0])} {f(self.val_at[1])} 0) {FONT})',
             f'  (property "Footprint" "" (at 0 0 0) {FONT_H})',
             f'  (property "Datasheet" "" (at 0 0 0) {FONT_H})']
        if self.descr:
            L.append(f'  (property "ki_description" "{self.descr}" (at 0 0 0) {FONT_H})')
        L.append(f'  (symbol "{name}_0_1" ' + " ".join(self.body) + ")")
        L.append(f'  (symbol "{name}_1_1" ' + " ".join(_pin(*p) for p in self.pins) + ")")
        L.append(")")
        return "\n".join(L)


def stroke(w=0.254):
    return f"(stroke (width {f(w)}) (type default))"


def rect(x0, y0, x1, y1, fill="none", w=0.254):
    return f"(rectangle (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) {stroke(w)} (fill (type {fill})))"


def pline(pts, w=0.254, fill="none"):
    return "(polyline (pts " + " ".join(f"(xy {f(a)} {f(b)})" for a, b in pts) + f") {stroke(w)} (fill (type {fill})))"


def circ(x, y, r, w=0.254, fill="none"):
    return f"(circle (center {f(x)} {f(y)}) (radius {f(r)}) {stroke(w)} (fill (type {fill})))"


def stext(s, x, y, size=1.27):
    return f'(text "{s}" (at {f(x)} {f(y)} 0) (effects (font (size {f(size)} {f(size)}))))'


# ------------------------------------------------------------------------------------------------ symbol library
def library(lib, die_pins, microd_names):
    S = {}
    S["R"] = SymbolDef(f"{lib}:R", "R", "R", [("1", "~", -3.81, 0, 0, 1.27, "passive", False),
                                               ("2", "~", 3.81, 0, 180, 1.27, "passive", False)],
                       [rect(-2.54, 1.016, 2.54, -1.016)], "(pin_numbers hide) (pin_names (offset 0) hide)",
                       (0, 2.54), (0, -2.54), descr="Resistor (thin film)")
    S["C"] = SymbolDef(f"{lib}:C", "C", "C", [("1", "~", 0, 3.81, 270, 3.302, "passive", False),
                                               ("2", "~", 0, -3.81, 90, 3.302, "passive", False)],
                       [pline([(-1.524, 0.508), (1.524, 0.508)], 0.3048), pline([(-1.524, -0.508), (1.524, -0.508)], 0.3048)],
                       "(pin_numbers hide) (pin_names (offset 0.254) hide)", (2.54, 1.27), (2.54, -1.27),
                       descr="Capacitor (C0G)")
    S["SMP"] = SymbolDef(f"{lib}:SMP", "J", "SMP", [("1", "In", -5.08, 0, 0, 3.302, "passive", False),
                                                     ("2", "Ext", 0, -5.08, 90, 3.302, "passive", False)],
                         [circ(0, 0, 1.778, 0.254), circ(0, 0, 0.508, 0.254, "outline"),
                          pline([(-1.778, 0), (-0.508, 0)])],
                         "(pin_numbers hide) (pin_names (offset 1.016) hide)", (0, 3.302), (3.81, -2.54),
                         descr="SMP coaxial connector (centre = pin 1, shield = pin 2)")
    md_pins = [(str(k), microd_names[k], 10.16, 17.78 - 2.54 * (k - 1), 180, 5.08, "passive", False) for k in range(1, 16)]
    md_pins.append(("SH", "SHELL", 0, -27.94, 90, 5.08, "passive", False))
    S["MICROD"] = SymbolDef(f"{lib}:MicroD_15P", "J", "MicroD_15P", md_pins,
                            [rect(-5.08, 20.32, 5.08, -22.86, "background")], "(pin_names (offset 1.016))",
                            (0, 21.59), (0, -24.13), descr="Micro-D 15-pin connector with shell")
    die = []
    for num, name, side, k in die_pins:            # k = 0..5 along the side in die_pads order
        t = -12.7 + 5.08 * k
        if side == "N":
            die.append((str(num), name, t, 25.4, 270, 5.08, "passive", False))
        elif side == "S":
            die.append((str(num), name, t, -25.4, 90, 5.08, "passive", False))
        elif side == "W":
            die.append((str(num), name, -25.4, -t, 0, 5.08, "passive", False))
        else:
            die.append((str(num), name, 25.4, -t, 180, 5.08, "passive", False))
    S["DIE"] = SymbolDef(f"{lib}:QBF-X2_die", "U", "QBF-X2", die,
                         [rect(-20.32, 20.32, 20.32, -20.32, "background"), rect(-7.62, 7.62, 7.62, -7.62, "none", 0.152)],
                         "(pin_names (offset 1.016))", (0, 29.21), (0, -29.21),
                         descr="QBF-X2 superconducting die, 24 launchers (circuits/die_pads.json)")
    S["MH"] = SymbolDef(f"{lib}:MountingHole_Pad", "H", "MountingHole", [("1", "1", 0, -2.54, 90, 1.27, "passive", False)],
                        [circ(0, 0, 1.27, 0.508)], "(pin_numbers hide) (pin_names (offset 1.016) hide)",
                        (2.54, 0.635), (2.54, -1.27), descr="Mounting hole, plated, GND")
    S["GND"] = SymbolDef("power:GND", "#PWR", "GND", [("1", "GND", 0, 0, 270, 0, "power_in", True)],
                         [pline([(0, 0), (0, -1.27), (1.27, -1.27), (0, -2.54), (-1.27, -1.27), (0, -1.27)], 0)],
                         "(pin_names (offset 0))", (0, -6.35), (0, -3.81), power=True, descr="Power symbol: GND")
    S["FLAG"] = SymbolDef("power:PWR_FLAG", "#FLG", "PWR_FLAG", [("1", "pwr", 0, 0, 90, 0, "power_out", False)],
                          [pline([(0, 0), (0, 1.27), (-1.016, 1.905), (0, 2.54), (1.016, 1.905), (0, 1.27)], 0)],
                          "(pin_numbers hide) (pin_names (offset 0) hide)", (0, 1.905), (0, 3.81), power=True,
                          descr="Marks the GND net as driven (ERC)")
    return S


# ------------------------------------------------------------------------------------------------ sheet
class Sheet:
    def __init__(self, project, paper="A3"):
        self.project, self.paper = project, paper
        self.root = U()
        self.items, self.symbols, self.used = [], [], {}
        self.pwr_n = 0
        self.flg_n = 0

    @staticmethod
    def xform(pos, rot, lx, ly):
        x, y = lx, -ly
        r = math.radians(rot)
        return (round(pos[0] + x * math.cos(r) + y * math.sin(r), 4), round(pos[1] - x * math.sin(r) + y * math.cos(r), 4))

    def place(self, sdef, ref, value, pos, rot=0, fields=None, footprint="", ref_off=None, val_off=None,
              hide_value=False):
        """returns {pin: (x, y)} and the symbol uuid"""
        self.used[sdef.lib_id] = sdef
        uid = U()
        ra = ref_off if ref_off is not None else self.xform((0, 0), 0, *sdef.ref_at)
        va = val_off if val_off is not None else self.xform((0, 0), 0, *sdef.val_at)
        power = sdef.power
        props = [(
            "Reference", ref, (pos[0] + ra[0], pos[1] + ra[1]), power),
            ("Value", value, (pos[0] + va[0], pos[1] + va[1]), hide_value),
            ("Footprint", footprint, pos, True), ("Datasheet", "", pos, True)]
        for k, v in (fields or {}).items():
            props.append((k, v, pos, True))
        L = [f'(symbol (lib_id "{sdef.lib_id}") (at {f(pos[0])} {f(pos[1])} {rot}) (unit 1)',
             '  (in_bom yes) (on_board yes) (dnp no)', f'  (uuid {uid})']
        for name, val, at, hide in props:
            L.append(f'  (property "{name}" "{val}" (at {f(at[0])} {f(at[1])} 0) {FONT_H if hide else FONT})')
        for p in sdef.pins:
            L.append(f'  (pin "{p[0]}" (uuid {U()}))')
        L.append(f'  (instances (project "{self.project}" (path "/{self.root}" (reference "{ref}") (unit 1))))')
        L.append(")")
        self.symbols.append("\n".join(L))
        return {p[0]: self.xform(pos, rot, p[2], p[3]) for p in sdef.pins}, uid

    def gnd(self, S, at, rot=0):
        self.pwr_n += 1
        self.place(S["GND"], f"#PWR{self.pwr_n:02d}", "GND", at, rot)

    def flag(self, S, at):
        self.flg_n += 1
        self.place(S["FLAG"], f"#FLG{self.flg_n:02d}", "PWR_FLAG", at, 0)

    def wire(self, a, b):
        self.items.append(f'(wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) '
                          f'(stroke (width 0) (type default)) (uuid {U()}))')

    def wires(self, pts):
        for a, b in zip(pts[:-1], pts[1:]):
            self.wire(a, b)

    def junction(self, at):
        self.items.append(f'(junction (at {f(at[0])} {f(at[1])}) (diameter 0) (color 0 0 0 0) (uuid {U()}))')

    def no_connect(self, at):
        self.items.append(f'(no_connect (at {f(at[0])} {f(at[1])}) (uuid {U()}))')

    def glabel(self, name, at, ang):
        just = {0: "left", 90: "left", 180: "right", 270: "right"}[ang]
        self.items.append(
            f'(global_label "{name}" (shape passive) (at {f(at[0])} {f(at[1])} {ang}) (fields_autoplaced) '
            f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {U()}) '
            f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {f(at[0])} {f(at[1])} 0) {FONT_H}))')

    def text(self, s, at, size=1.27, bold=False):
        s = s.replace('"', "'").replace("\n", "\\n")
        b = " bold" if bold else ""
        self.items.append(f'(text "{s}" (at {f(at[0])} {f(at[1])} 0) (effects (font (size {f(size)} {f(size)}){b}) '
                          f'(justify left top)) (uuid {U()}))')

    def box(self, a, b):
        self.items.append(f'(polyline (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])}) '
                          f'(xy {f(a[0])} {f(b[1])}) (xy {f(a[0])} {f(a[1])})) (stroke (width 0.254) (type dash)) '
                          f'(uuid {U()}))')

    def write(self, path, title_block):
        tb = " ".join(f'({k} "{v}")' if not k.startswith("comment") else f'(comment {k[7:]} "{v}")'
                      for k, v in title_block.items())
        out = [f'(kicad_sch (version 20230121) (generator eeschema)', f'  (uuid {self.root})',
               f'  (paper "{self.paper}")', f'  (title_block {tb})', '  (lib_symbols']
        for sdef in self.used.values():
            out.append("    " + sdef.sexpr().replace("\n", "\n    "))
        out.append("  )")
        out += ["  " + s for s in self.items]
        out += ["  " + s.replace("\n", "\n  ") for s in self.symbols]
        out.append('  (sheet_instances (path "/" (page "1")))')
        out.append(")")
        with open(path, "w") as fh:
            fh.write("\n".join(out) + "\n")


def symbol_library_text(S):
    out = ['(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)']
    for key in ("R", "C", "SMP", "MICROD", "DIE", "MH"):
        sd = S[key]
        name = sd.lib_id.split(":")[1]
        txt = sd.sexpr().replace(f'(symbol "{sd.lib_id}"', f'(symbol "{name}"', 1)
        out.append("  " + txt.replace("\n", "\n  "))
    out.append(")")
    return "\n".join(out) + "\n"
