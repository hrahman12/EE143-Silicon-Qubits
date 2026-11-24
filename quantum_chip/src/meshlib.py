"""Small mesh toolkit: KLayout regions -> extruded triangle meshes, tubes, primitives.
All coordinates in mm, Z up. Regions are KLayout integer regions in units of DBU_MM."""
import math
import numpy as np
import klayout.db as db

DBU_MM = 1e-5            # 10 nm grid for all 2D work


def to_i(v):
    return int(round(v / DBU_MM))


def poly_from_pts(pts):
    return db.Polygon([db.Point(to_i(x), to_i(y)) for x, y in pts])


def region_from_pts(pts):
    return db.Region(poly_from_pts(pts))


def circle_pts(cx, cy, r, n=24):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def circle_region(cx, cy, r, n=24):
    return region_from_pts(circle_pts(cx, cy, r, n))


def box_region(x0, y0, x1, y1):
    return db.Region(db.Box(to_i(min(x0, x1)), to_i(min(y0, y1)), to_i(max(x0, x1)), to_i(max(y0, y1))))


def path_region(pts, w, round_ends=True):
    p = db.DPath([db.DPoint(x / DBU_MM, y / DBU_MM) for x, y in pts], w / DBU_MM, w / 2 / DBU_MM if round_ends else 0,
                 w / 2 / DBU_MM if round_ends else 0, round_ends)
    return db.Region(p.to_itype(1.0).polygon())


class Mesh:
    def __init__(self):
        self.v, self.f = [], []
        self.n = 0

    def add(self, verts, faces):
        verts = np.asarray(verts, float)
        faces = np.asarray(faces, np.int64) + self.n
        self.v.append(verts)
        self.f.append(faces)
        self.n += len(verts)

    def arrays(self):
        if not self.v:
            return np.zeros((0, 3)), np.zeros((0, 3), np.int64)
        return np.vstack(self.v), np.vstack(self.f)

    @property
    def empty(self):
        return self.n == 0


def extrude_region(region, z0, z1, mesh=None, walls=True):
    """Extrude a (merged) KLayout region between z0 and z1. Caps via constrained Delaunay."""
    m = mesh or Mesh()
    region = region.merged()
    for poly in region.each():
        tris = poly.delaunay() if hasattr(poly, "delaunay") else db.Region(poly).delaunay()
        tv, tf = [], []
        for t in tris.each():
            pts = [(p.x * DBU_MM, p.y * DBU_MM) for p in t.each_point_hull()]
            if len(pts) != 3:
                continue
            # orient CCW
            (ax, ay), (bx, by), (cx, cy) = pts
            if (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) < 0:
                pts = [pts[0], pts[2], pts[1]]
            base = len(tv)
            tv += [(x, y) for x, y in pts]
            tf.append((base, base + 1, base + 2))
        if not tf:
            continue
        tv = np.array(tv)
        tf = np.array(tf)
        top = np.c_[tv, np.full(len(tv), z1)]
        bot = np.c_[tv, np.full(len(tv), z0)]
        m.add(top, tf)
        m.add(bot, tf[:, ::-1])
        if walls:
            loops = [list(poly.each_point_hull())] + [list(poly.each_point_hole(h)) for h in range(poly.holes())]
            for li, loop in enumerate(loops):
                pts = np.array([(p.x * DBU_MM, p.y * DBU_MM) for p in loop])
                if len(pts) < 2:
                    continue
                nxt = np.roll(pts, -1, axis=0)
                k = len(pts)
                vv = np.vstack([np.c_[pts, np.full(k, z0)], np.c_[nxt, np.full(k, z0)],
                                np.c_[nxt, np.full(k, z1)], np.c_[pts, np.full(k, z1)]])
                idx = np.arange(k)
                ff = np.vstack([np.c_[idx, idx + k, idx + 2 * k], np.c_[idx, idx + 2 * k, idx + 3 * k]])
                # KLayout hulls are clockwise; holes counter-clockwise -> flip so normals point outward
                m.add(vv, ff[:, ::-1] if li == 0 else ff)
    return m


def tube(points, r, nseg=10, mesh=None, caps=True):
    """Sweep a circle of radius r along a 3D polyline (parallel-transport frames)."""
    m = mesh or Mesh()
    P = np.asarray(points, float)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    ref = np.array([0, 0, 1.0]) if abs(T[0][2]) < 0.9 else np.array([1.0, 0, 0])
    N = np.cross(T[0], ref)
    N /= np.linalg.norm(N)
    verts = []
    for i in range(len(P)):
        if i:
            N = N - np.dot(N, T[i]) * T[i]
            N /= np.linalg.norm(N)
        B = np.cross(T[i], N)
        for j in range(nseg):
            a = 2 * math.pi * j / nseg
            verts.append(P[i] + r * (math.cos(a) * N + math.sin(a) * B))
    faces = []
    for i in range(len(P) - 1):
        for j in range(nseg):
            a, b = i * nseg + j, i * nseg + (j + 1) % nseg
            c, d = a + nseg, b + nseg
            faces += [(a, b, d), (a, d, c)]
    verts = np.array(verts)
    if caps:
        n0 = len(verts)
        verts = np.vstack([verts, P[0], P[-1]])
        for j in range(nseg):
            faces.append((n0, (j + 1) % nseg, j))
            e = (len(P) - 1) * nseg
            faces.append((n0 + 1, e + j, e + (j + 1) % nseg))
    m.add(verts, faces)
    return m


def cylinder(cx, cy, z0, z1, r, n=24, mesh=None, r_in=None):
    """Solid cylinder (r_in None) or tube with wall (r_in) along Z."""
    m = mesh or Mesh()
    if r_in is None:
        reg = circle_region(cx, cy, r, n)
    else:
        reg = circle_region(cx, cy, r, n) - circle_region(cx, cy, r_in, n)
    return extrude_region(reg, z0, z1, m)


def transform(mesh_arrays, M):
    v, f = mesh_arrays
    vh = np.c_[v, np.ones(len(v))] @ M.T
    return vh[:, :3], f


def rot_z(deg, tx=0, ty=0, tz=0):
    a = math.radians(deg)
    M = np.eye(4)
    M[:2, :2] = [[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]
    M[:3, 3] = [tx, ty, tz]
    return M


def rot_x(deg):
    a = math.radians(deg)
    M = np.eye(4)
    M[1:3, 1:3] = [[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]
    return M


def revolve_z(profile, n=32, mesh=None):
    """Surface of revolution about the local Z axis from (r, z) profile points."""
    m = mesh or Mesh()
    prof = np.asarray(profile, float)
    verts = []
    for j in range(n):
        a = 2 * math.pi * j / n
        for r, z in prof:
            verts.append((r * math.cos(a), r * math.sin(a), z))
    k = len(prof)
    faces = []
    for j in range(n):
        j2 = (j + 1) % n
        for i in range(k - 1):
            a, b = j * k + i, j * k + i + 1
            c, d = j2 * k + i, j2 * k + i + 1
            faces += [(a, c, d), (a, d, b)]
    m.add(verts, faces)
    return m
