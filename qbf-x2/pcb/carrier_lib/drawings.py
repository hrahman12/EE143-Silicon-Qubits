"""Board-level drawing items (KiCad 7 s-expressions) in PAGE coordinates (mm, y down): text, tables, dimensions.

Used for the fab-notes layer (Dwgs.User -> fabrication drawing) and the assembly layer (Cmts.User -> assembly
drawing). KiCad 7 has no table object, so a table is a grid of gr_line plus one gr_text per cell.
"""


from carrier_lib.ids import U  # noqa: E402  (deterministic ids)


def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def esc(s):
    return str(s).replace("\\", "/").replace('"', "'")


class Drawing:
    def __init__(self):
        self.items = []

    def text(self, layer, s, x, y, size=1.5, thick=None, justify="left", rot=0, mirror=False):
        th = thick if thick is not None else round(size * 0.15, 3)
        j = []
        if justify != "center":
            j.append(justify)
        if mirror:
            j.append("mirror")
        js = f" (justify {' '.join(j)})" if j else ""
        r = f" {f(rot)}" if rot else ""
        self.items.append(f'  (gr_text "{esc(s)}" (at {f(x)} {f(y)}{r}) (layer "{layer}") (tstamp {U()}) '
                          f'(effects (font (size {f(size)} {f(size)}) (thickness {f(th)})){js}))')

    def line(self, layer, a, b, w=0.15):
        self.items.append(f'  (gr_line (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) '
                          f'(stroke (width {f(w)}) (type solid)) (layer "{layer}") (tstamp {U()}))')

    def rect(self, layer, a, b, w=0.15, fill=False):
        self.items.append(f'  (gr_rect (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) '
                          f'(stroke (width {f(w)}) (type solid)) (fill {"solid" if fill else "none"}) '
                          f'(layer "{layer}") (tstamp {U()}))')

    def circle(self, layer, c, r, w=0.15):
        self.items.append(f'  (gr_circle (center {f(c[0])} {f(c[1])}) (end {f(c[0] + r)} {f(c[1])}) '
                          f'(stroke (width {f(w)}) (type solid)) (fill none) (layer "{layer}") (tstamp {U()}))')

    def dimension(self, layer, a, b, height, text, size=1.2):
        """aligned dimension from a to b (page coords). KiCad offsets the dimension line by `height` along
        n = (-d_y, d_x), d = unit(b - a) (page frame, y down): for a -> b pointing right, height > 0 is below."""
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        L = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        n = (-d[1], d[0])
        off = height + (1.4 if height > 0 else -1.4)
        tx, ty = mx + n[0] * off, my + n[1] * off
        horiz = abs(a[1] - b[1]) < 1e-9
        rot = 0 if horiz else 90
        self.items.append(
            f'  (dimension (type aligned) (layer "{layer}") (tstamp {U()})\n'
            f'    (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])}))\n'
            f'    (height {f(height)})\n'
            f'    (gr_text "{text}" (at {f(tx)} {f(ty)}{" 90" if rot else ""}) (layer "{layer}") (tstamp {U()})\n'
            f'      (effects (font (size {f(size)} {f(size)}) (thickness {f(size * 0.15)})))\n'
            f'    )\n'
            f'    (format (prefix "") (suffix "") (units 2) (units_format 1) (precision 2))\n'
            f'    (style (thickness 0.15) (arrow_length 1.27) (text_position_mode 0) (extension_height 0.58642) '
            f'(extension_offset 0.5) keep_text_aligned)\n'
            f'  )')

    def table(self, layer, x0, y0, cols, rows, title=None, size=1.3, row_h=None, header=True):
        """cols: [(header, width_mm)], rows: [[cell, ...]]. Returns the y below the table."""
        rh = row_h or size * 2.0
        y = y0
        if title:
            self.text(layer, title, x0, y + size * 0.8, size * 1.25)
            y += size * 2.4
        widths = [w for _, w in cols]
        xs = [x0]
        for w in widths:
            xs.append(xs[-1] + w)
        allrows = ([[h for h, _ in cols]] if header else []) + rows
        top = y
        for i, r in enumerate(allrows):
            for j, cell in enumerate(r):
                self.text(layer, cell, xs[j] + 0.8, y + rh * 0.5, size, thick=round(size * (0.19 if (header and i == 0) else 0.14), 3))
            y += rh
        for k in range(len(allrows) + 1):
            yy = top + k * rh
            self.line(layer, (xs[0], yy), (xs[-1], yy), 0.25 if (k in (0, 1, len(allrows)) and header) else 0.12)
        for xx in xs:
            self.line(layer, (xx, top), (xx, y), 0.12)
        return y

    def notes(self, layer, x0, y0, title, lines, size=1.25, gap=1.75):
        self.text(layer, title, x0, y0 + size, size * 1.3)
        y = y0 + size * 2.9
        for s in lines:
            self.text(layer, s, x0, y, size)
            y += size * gap
        return y
