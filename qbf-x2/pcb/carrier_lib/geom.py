"""Plane geometry for the carrier generator: filleted polylines (track arcs), path sampling, lengths, distances.

All coordinates in the board frame (mm, y up). A *path* is a list of primitives
    ("seg", (x0, y0), (x1, y1))
    ("arc", (x0, y0), (xm, ym), (x1, y1), centre, radius, sweep_rad)   sweep > 0 = counter-clockwise
"""
import math


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, s):
    return (a[0] * s, a[1] * s)


def norm(a):
    return math.hypot(a[0], a[1])


def unit(a):
    n = norm(a)
    return (a[0] / n, a[1] / n)


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def rot(p, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def fillet(points, radius):
    """Polyline -> path with a tangent arc of `radius` at every interior vertex (no stubs, no mitres)."""
    pts = [tuple(map(float, p)) for p in points]
    out = []
    cur = pts[0]
    for i in range(1, len(pts) - 1):
        a, v, b = pts[i - 1], pts[i], pts[i + 1]
        d1, d2 = unit(sub(v, a)), unit(sub(b, v))
        turn = math.atan2(cross(d1, d2), dot(d1, d2))        # signed turning angle
        if abs(turn) < 1e-9:
            continue
        t = radius * math.tan(abs(turn) / 2)
        if t > norm(sub(v, a)) - 1e-6 or t > norm(sub(b, v)) - 1e-6:
            raise ValueError(f"fillet radius {radius} too large at vertex {v}")
        p0 = sub(v, mul(d1, t))
        p1 = add(v, mul(d2, t))
        left = (-d1[1], d1[0])
        side = 1.0 if turn > 0 else -1.0
        c = add(p0, mul(left, side * radius))
        a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
        am = a0 + turn / 2
        pm = (c[0] + radius * math.cos(am), c[1] + radius * math.sin(am))
        if norm(sub(p0, cur)) > 1e-9:
            out.append(("seg", cur, p0))
        out.append(("arc", p0, pm, p1, c, radius, turn))
        cur = p1
    if norm(sub(pts[-1], cur)) > 1e-9:
        out.append(("seg", cur, pts[-1]))
    return out


def polyline_path(points):
    pts = [tuple(map(float, p)) for p in points]
    return [("seg", a, b) for a, b in zip(pts[:-1], pts[1:]) if norm(sub(b, a)) > 1e-9]


def prim_length(p):
    if p[0] == "seg":
        return norm(sub(p[2], p[1]))
    return abs(p[5] * p[6])


def path_length(path):
    return sum(prim_length(p) for p in path)


def sample(path, step, include_end=True):
    """Points along a path every `step` (arc length), each with the unit tangent: [(pt, tangent, s)]."""
    L = path_length(path)
    n = max(1, int(round(L / step)))
    targets = [L * i / n for i in range(n + (1 if include_end else 0))]
    out, s0, k = [], 0.0, 0
    for p in path:
        lp = prim_length(p)
        while k < len(targets) and targets[k] <= s0 + lp + 1e-9:
            u = (targets[k] - s0) / lp if lp > 0 else 0.0
            out.append(point_on(p, u) + (targets[k],))
            k += 1
        s0 += lp
    return out


def point_on(p, u):
    if p[0] == "seg":
        a, b = p[1], p[2]
        d = unit(sub(b, a))
        return (add(a, mul(sub(b, a), u)), d)
    _, p0, _, _, c, r, sw = p
    a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
    a = a0 + sw * u
    pt = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
    tan = (-math.sin(a), math.cos(a)) if sw > 0 else (math.sin(a), -math.cos(a))
    return (pt, tan)


def dist_point_seg(p, a, b):
    d = sub(b, a)
    L2 = dot(d, d)
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, dot(sub(p, a), d) / L2))
    return norm(sub(p, add(a, mul(d, t))))


def dist_point_prim(p, pr):
    if pr[0] == "seg":
        return dist_point_seg(p, pr[1], pr[2])
    _, p0, _, p1, c, r, sw = pr
    a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
    a = math.atan2(p[1] - c[1], p[0] - c[0])
    rel = (a - a0) * (1 if sw > 0 else -1)
    rel %= 2 * math.pi
    if rel <= abs(sw) + 1e-12:
        return abs(norm(sub(p, c)) - r)
    return min(norm(sub(p, p0)), norm(sub(p, p1)))


def dist_point_path(p, path):
    return min(dist_point_prim(p, pr) for pr in path)


def mirror_x(path):
    """mirror a path in x (x -> -x); arcs keep their geometry, sweep sign flips"""
    out = []
    for p in path:
        if p[0] == "seg":
            out.append(("seg", (-p[1][0], p[1][1]), (-p[2][0], p[2][1])))
        else:
            _, a, m, b, c, r, sw = p
            out.append(("arc", (-a[0], a[1]), (-m[0], m[1]), (-b[0], b[1]), (-c[0], c[1]), r, -sw))
    return out


def path_to_polyline(path, arc_step=0.1):
    """dense polyline for shapely / plotting"""
    pts = []
    for p in path:
        if p[0] == "seg":
            if not pts:
                pts.append(p[1])
            pts.append(p[2])
        else:
            n = max(2, int(math.ceil(prim_length(p) / arc_step)))
            if not pts:
                pts.append(p[1])
            for i in range(1, n + 1):
                pts.append(point_on(p, i / n)[0])
    return pts


def circle_pts(c, r, n=48, a0=0.0, a1=2 * math.pi):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def rounded_rect(x0, y0, x1, y1, r, n=8):
    pts = []
    for cx, cy, a in ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)):
        for i in range(n + 1):
            t = math.radians(a + 90 * i / n)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts
