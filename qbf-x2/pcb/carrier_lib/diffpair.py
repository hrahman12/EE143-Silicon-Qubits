"""Edge-coupled differential pair routing for the carrier (fast flux lines, rev B).

A pair is described by its centre line (polyline + fillet radius per vertex) and a list of events placed on the
straight runs. Both legs and the centre line are built with a turtle, so every leg is tangent-continuous and made of
straight segments and tangent arcs only:

* bend      the centre line turns by theta with radius R; the legs follow CONCENTRIC arcs of radius R -/+ c/2,
            so the pair stays symmetric and the leg on the inside of the turn is shorter by c * |theta|;
* open      symmetric transition from the breakout spacing c0 to the routed spacing c1: each leg makes a mirror-image
            S-jog (two arcs) outward by (c1 - c0) / 2, so both legs gain exactly the same length;
* bump      tuning bump on ONE leg (arcs +a, -2a, +a of radius r, bulging away from the partner): extra length
            4 r (a - sin a) for a longitudinal span of 4 r sin a; the partner leg runs straight past it;
* split     at the end of the coupled section each leg turns away from the partner (mirror-image 45-degree jogs)
            towards its own SMP jack.

Coordinates in the board frame (mm, y up). Paths use carrier_lib.geom primitives ("seg", a, b) and
("arc", p0, pm, p1, centre, radius, sweep); every primitive carries a width in the parallel list `widths`.

KiCad 7.0 note (checked on 7.0.11): its diff-pair coupling test calls a straight segment "uncoupled" whenever one of
its end points touches an arc or a pad of the pair (the "nothing in between" probe does not exclude the pair's own
arcs and pads). Every straight run that ends at an arc or a pad therefore starts / ends with a short separate
straight "coupling stub" (STUB mm), so KiCad measures the coupled runs correctly.
"""
import math

from . import geom as G

STUB = 0.25


class Turtle:
    """tags: "run" = straight meant to be coupled with the partner leg, "station" = stub-length straight around a bump,
    "span" = straight opposite the partner's bump, "stub" (added by add_stubs), "arc" """
    def __init__(self, p, heading):
        self.p = (float(p[0]), float(p[1]))
        self.h = heading                       # radians
        self.path, self.widths, self.tags = [], [], []

    def straight(self, L, w, tag="run"):
        if L < 1e-9:
            return
        q = (self.p[0] + L * math.cos(self.h), self.p[1] + L * math.sin(self.h))
        self.path.append(("seg", self.p, q))
        self.widths.append(w)
        self.tags.append(tag)
        self.p = q

    def arc(self, r, theta, w):
        """theta > 0: left (counter-clockwise) turn"""
        if abs(theta) < 1e-12:
            return
        s = 1.0 if theta > 0 else -1.0
        c = (self.p[0] - s * r * math.sin(self.h), self.p[1] + s * r * math.cos(self.h))
        a0 = math.atan2(self.p[1] - c[1], self.p[0] - c[0])
        q = (c[0] + r * math.cos(a0 + theta), c[1] + r * math.sin(a0 + theta))
        m = (c[0] + r * math.cos(a0 + theta / 2), c[1] + r * math.sin(a0 + theta / 2))
        self.path.append(("arc", self.p, m, q, c, r, theta))
        self.widths.append(w)
        self.tags.append("arc")
        self.p = q
        self.h += theta


def bump_shape(extra, r):
    """arc angle a of an arcs-only bump (+a, -2a, +a, radius r) with the given extra length; span and height"""
    lo, hi = 1e-4, math.pi / 2
    if 4 * r * (hi - math.sin(hi)) < extra - 1e-12:
        raise ValueError(f"bump of radius {r} cannot add {extra} mm (max {4 * r * (hi - 1):.3f}): use more bumps")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 4 * r * (mid - math.sin(mid)) < extra:
            lo = mid
        else:
            hi = mid
    a = 0.5 * (lo + hi)
    return dict(alpha=a, span=4 * r * math.sin(a), height=2 * r * (1 - math.cos(a)), extra=4 * r * (a - math.sin(a)),
                r=r)


def build_pair(start, heading, segments, c0, w0, c1, w1, split=None, w_split=None):
    """segments: list of straight runs and bends of the CENTRE line, in order:
         ("straight", L, events)  events = [(position_along_run, kind, params)], kinds:
                                  "open"  params = dict(r=jog radius)          (spacing c0 -> c1, width w0 -> w1)
                                  "bump"  params = dict(leg="L"/"R", extra=..., r=..., n=...)
         ("bend", R, theta)
       split: dict(R=..., targets={"L": (x, y), "R": (x, y)}) - each leg jogs (45 deg) to the y (or x) of its target
       and runs straight into it (targets are reached along the final heading).
       Returns dict(L=..., R=..., C=...) of turtles plus bookkeeping (coupled ranges, bump records, events)."""
    c, w = c0, w0
    hl = (-math.sin(heading), math.cos(heading))
    T = dict(C=Turtle(start, heading),
             L=Turtle((start[0] + hl[0] * c / 2, start[1] + hl[1] * c / 2), heading),
             R=Turtle((start[0] - hl[0] * c / 2, start[1] - hl[1] * c / 2), heading))
    log = dict(bumps=[], opens=[], bends=[], running=[])
    opened = False

    def all_straight(L, tag="run"):
        T["C"].straight(L, w, tag)
        T["L"].straight(L, w, tag)
        T["R"].straight(L, w, tag)

    def mark():
        log["running"].append(tuple(G.path_length(T[k].path) for k in ("C", "L", "R")))
    mark()

    for sgm in segments:
        if sgm[0] == "bend":
            _, R, th = sgm
            s = 1.0 if th > 0 else -1.0
            T["C"].arc(R, th, w)
            T["L"].arc(R - s * c / 2, th, w)
            T["R"].arc(R + s * c / 2, th, w)
            log["bends"].append(dict(R=R, theta_deg=math.degrees(th), c=c, inner="L" if th > 0 else "R",
                                     mismatch=c * abs(th)))
            mark()
            continue
        _, L, events = sgm
        pos = 0.0
        for at, kind, prm in sorted(events, key=lambda e: e[0]):
            if at < pos - 1e-9:
                raise ValueError(f"event {kind} at {at} overlaps the previous event (ends at {pos})")
            if kind == "bump":                          # leading stub station on every leg (see the bump branch)
                if at - pos < STUB - 1e-9:
                    raise ValueError("no room for the stub before a bump")
                all_straight(at - pos - STUB)
                all_straight(STUB, "station")
            else:
                all_straight(at - pos)
            pos = at
            mark()
            if kind == "open":
                d = (c1 - c0) / 2
                rj = prm["r"]
                beta = math.acos(1 - d / (2 * rj))
                span = 2 * rj * math.sin(beta)
                T["C"].straight(span, w)
                T["L"].arc(rj, beta, w)
                T["L"].arc(rj, -beta, w)
                T["R"].arc(rj, -beta, w)
                T["R"].arc(rj, beta, w)
                c, w, opened = c1, w1, True
                log["opens"].append(dict(at=at, span=span, beta_deg=math.degrees(beta), r=rj, d=d))
                pos += span
            elif kind == "bump":
                leg, other = prm["leg"], ("R" if prm["leg"] == "L" else "L")
                n = prm.get("n", 1)
                gap = prm.get("gap", 2 * STUB + 0.1)
                if gap < 2 * STUB + 0.05:
                    raise ValueError("bump gap too short for the coupling stubs")
                shp = bump_shape(prm["extra"] / n, prm["r"])
                sgn = 1.0 if leg == "L" else -1.0          # bulge away from the partner
                a = shp["alpha"]
                # every leg is split at the coupling-stub stations around each bump, so that every straight of one leg
                # faces exactly one straight of the other (KiCad 7 couples a segment with ONE partner segment only)
                for k in range(n):
                    if k:
                        all_straight(STUB, "station")
                        all_straight(gap - 2 * STUB)
                        all_straight(STUB, "station")
                        pos += gap
                        mark()
                    T["C"].straight(shp["span"], w)
                    T[other].straight(shp["span"], w, "span")
                    T[leg].arc(shp["r"], sgn * a, w)
                    T[leg].arc(shp["r"], -2 * sgn * a, w)
                    T[leg].arc(shp["r"], sgn * a, w)
                    pos += shp["span"]
                    mark()                                  # running skew after every single bump
                all_straight(STUB, "station")               # trailing stub station
                pos += STUB
                log["bumps"].append(dict(leg=leg, n=n, at=at, extra_total=prm["extra"], each=shp,
                                         after_bend=len(log["bends"])))
            else:
                raise ValueError(kind)
            mark()
        all_straight(L - pos)
        mark()
        if L - pos < -1e-9:
            raise ValueError(f"events overrun the straight run ({pos:.3f} > {L:.3f})")
    if not opened and c0 != c1:
        raise ValueError("pair never opened from the breakout to the routed spacing")
    coupled_end = {k: len(T[k].path) for k in ("L", "R", "C")}
    if split:
        Rs = split["R"]
        for leg, sgn in (("L", 1.0), ("R", -1.0)):          # L jogs to its left, R to its right
            t = T[leg]
            tx, ty = split["targets"][leg]
            hv = (math.cos(t.h), math.sin(t.h))
            nl = (-hv[1], hv[0])
            lat = (tx - t.p[0]) * nl[0] + (ty - t.p[1]) * nl[1]            # signed lateral offset to the target
            if lat * sgn <= 0:
                raise ValueError(f"split target of leg {leg} is on the wrong side")
            th = math.radians(45.0)
            ld = (abs(lat) - 2 * Rs * (1 - math.cos(th))) / math.sin(th)
            if ld < 2 * STUB:
                raise ValueError(f"split jog too short for leg {leg}: {ld:.3f}")
            t.arc(Rs, sgn * th, w_split or w)
            t.straight(ld, w_split or w)
            t.arc(Rs, -sgn * th, w_split or w)
            along = (tx - t.p[0]) * hv[0] + (ty - t.p[1]) * hv[1]
            if along < 2 * STUB:
                raise ValueError(f"split target of leg {leg} too close: {along:.3f}")
            t.straight(along, w_split or w)
    out = dict(T=T, log=log, coupled_end=coupled_end, c_final=c, w_final=w)
    return out


def add_stubs(path, widths, tags, pad_ends=(True, True), stub=STUB):
    """split every straight segment whose end touches an arc (or a pad at the path ends) so that a separate straight
    stub of `stub` mm sits next to the arc / pad (see the KiCad 7.0 note in the module docstring)"""
    out, ow, ot, src = [], [], [], []
    n = len(path)
    for i, (pr, w, tg) in enumerate(zip(path, widths, tags)):
        if pr[0] != "seg":
            out.append(pr)
            ow.append(w)
            ot.append(tg)
            src.append(i)
            continue
        a, b = pr[1], pr[2]
        L = G.norm(G.sub(b, a))
        prev_arc = (i == 0 and pad_ends[0]) or (i > 0 and path[i - 1][0] == "arc")
        next_arc = (i == n - 1 and pad_ends[1]) or (i < n - 1 and path[i + 1][0] == "arc")
        need = stub * (prev_arc + next_arc)
        if L < need + 0.05:
            out.append(pr)
            ow.append(w)
            ot.append(tg if tg != "run" else "stub")
            src.append(i)
            continue
        d = G.unit(G.sub(b, a))
        pts, pt_tags = [a], []
        if prev_arc:
            pts.append(G.add(a, G.mul(d, stub)))
            pt_tags.append("stub")
        if next_arc:
            pts.append(G.sub(b, G.mul(d, stub)))
            pt_tags.append(tg)
            pt_tags.append("stub")
        else:
            pt_tags.append(tg)
        pts.append(b)
        for (p, q), t_ in zip(zip(pts[:-1], pts[1:]), pt_tags):
            out.append(("seg", p, q))
            ow.append(w)
            ot.append(t_)
            src.append(i)
    return out, ow, ot, src


def transform(path, sx=1, sy=1):
    """mirror a path: x -> sx x, y -> sy y (an odd number of mirrors flips the arc sweep)"""
    flip = sx * sy < 0
    out = []
    for p in path:
        if p[0] == "seg":
            out.append(("seg", (sx * p[1][0], sy * p[1][1]), (sx * p[2][0], sy * p[2][1])))
        else:
            _, a, m, b, c, r, sw = p
            out.append(("arc", (sx * a[0], sy * a[1]), (sx * m[0], sy * m[1]), (sx * b[0], sy * b[1]),
                        (sx * c[0], sy * c[1]), r, -sw if flip else sw))
    return out


def running_skew(log):
    """[(centre-line station s, L - R)] at every command boundary of the coupled section (the turtles advance in
    lockstep, so equal stations are equal positions along the pair)"""
    return [(c, l - r) for c, l, r in log["running"]]


def quadrant_pair(x_start, yc, y_target, x_conn, jacks, cfg, D):
    """canonical pair of the WEST-TOP quadrant: starts at the land edge (x = -x_start) on the centre line y = yc,
    heading -x; bend B1 (cfg theta, radius R1) towards +y at x = -x_b1 with the breakout spacing, opening to the
    routed spacing, diagonal up to y = y_target, bend B2 back to -x (radius R2), straight to x = -x_split, split to the
    jacks at (-x_conn, jacks[0]) [left leg L = inner, towards the die axis] and (-x_conn, jacks[1]) [right leg R =
    outer]. Tuning bumps: outer leg (R) right after the opening for B1 (R is on the inside of B1, short by c0 theta);
    inner leg (L) next to B2 (L is on the inside of B2, short by c1 theta): cfg b2_before = the bumps end that far
    before B2, cfg b2_after = they start that far after B2."""
    c0, w0 = D["w_bo"] + D["s_bo"], D["w_bo"]
    c1, w1 = D["w"] + D["s"], D["w"]
    th = math.atan2(cfg["lattice"][1], cfg["lattice"][0])      # diagonal direction (-dx, +dy) on the integer lattice
    start = (-x_start, yc)
    V1 = (-cfg["x_b1"], yc)
    d = (y_target - yc) / math.sin(th)
    V2 = (V1[0] - d * math.cos(th), y_target)
    V3 = (-cfg["x_split"], y_target)
    t1, t2 = cfg["R1"] * math.tan(th / 2), cfg["R2"] * math.tan(th / 2)
    L0 = abs(V1[0] - start[0]) - t1
    L1 = d - t1 - t2
    L2 = abs(V3[0] - V2[0]) - t2
    beta = math.acos(1 - (c1 - c0) / 2 / (2 * D["open_r"]))
    open_span = 2 * D["open_r"] * math.sin(beta)
    ev1 = [(cfg["open_at"], "open", dict(r=D["open_r"])),
           (cfg["open_at"] + open_span + cfg["b1_gap"], "bump",
            dict(leg="R", extra=c0 * th, r=D["bump_r"], n=cfg["n1"], gap=D["bump_gap"]))]
    b2 = dict(leg="L", extra=c1 * th, r=D["bump_r"], n=cfg["n2"], gap=D["bump_gap"])
    ev2 = []
    if "b2_before" in cfg:
        n = cfg["n2"]
        span = n * bump_shape(b2["extra"] / n, D["bump_r"])["span"] + (n - 1) * D["bump_gap"]
        ev1.append((L1 - cfg["b2_before"] - span, "bump", b2))
    else:
        ev2 = [(cfg["b2_after"], "bump", b2)]
    segs = [("straight", L0, []), ("bend", cfg["R1"], -th), ("straight", L1, ev1), ("bend", cfg["R2"], th),
            ("straight", L2, ev2)]
    targets = {"L": (-x_conn, jacks[0]), "R": (-x_conn, jacks[1])}
    r = build_pair(start, math.pi, segs, c0, w0, c1, w1, split=dict(R=D["split_r"], targets=targets))
    r["vertices"] = [start, V1, V2, V3]
    r["straights"] = dict(L0=L0, L1=L1, L2=L2, open_span=open_span)
    return r


LATTICE = [(1, 0), (0, 1), (1, 1), (4, 7), (7, 4)]


def snap_nm(path, origin, tags=None, lattice=LATTICE, nudge=10):
    """board-frame path (mm, y up) -> KiCad page coordinates in integer nm (y down), every straight segment snapped so
    that its vector is an exact integer multiple of a lattice direction. KiCad 7's coupled-segment test
    (SEG::ApproxParallel) allows 1 nm of non-parallelism, so the two legs of a pair are only recognised as coupled if
    their straights are exactly parallel in the file's integer nm coordinates. Arc ends are rounded to 1 nm and the
    next primitive starts exactly where the previous one ended. Lengths change by << 0.1 um.
    KiCad 7 couples a straight with ONE partner straight (the closest parallel one with a common projection): the
    coupling stubs / bump stations ("stub", "station") are therefore tilted by `nudge` nm at their end away from the
    coupled run, so they are never parallel to anything and every "run" has exactly one candidate partner."""
    X0, Y0 = round(origin[0] * 1e6), round(origin[1] * 1e6)
    tags = tags or ["run"] * len(path)

    def pg(p):
        return (X0 + round(p[0] * 1e6), Y0 - round(p[1] * 1e6))
    dirs = []
    for a, b in lattice:
        for sa in (1, -1):
            for sb in (1, -1):
                v = (sa * a, sb * b)
                if v not in dirs:
                    dirs.append(v)
    out = []
    ex = pg(path[0][1])                 # exact (un-nudged) lattice position
    cur = ex                            # drawn position (= ex, or ex + a nudge)
    for i, pr in enumerate(path):
        if pr[0] == "arc":
            m, e = pg(pr[2]), pg(pr[3])
            out.append(("arc", cur, m, e))
            cur = ex = e
            continue
        d = (pr[2][0] - pr[1][0], -(pr[2][1] - pr[1][1]))
        L = math.hypot(*d) * 1e6

        def adiff(v):
            return abs((math.atan2(v[1], v[0]) - math.atan2(d[1], d[0]) + math.pi) % (2 * math.pi) - math.pi)
        best = min(dirs, key=adiff)
        if adiff(best) > 1e-6:
            raise ValueError(f"segment direction {d} is not a lattice direction {lattice}")
        ln = math.hypot(*best)
        n = round(L / ln)
        ex_end = (ex[0] + n * best[0], ex[1] + n * best[1])
        nxt = tags[i + 1] if i + 1 < len(path) else None
        if tags[i] == "run":
            if cur != ex:
                raise ValueError("a coupled run must start on the exact lattice")
            end = ex_end
        else:                                           # stub / station / span: never parallel to anything
            dn = (round(-best[1] / ln * nudge), round(best[0] / ln * nudge))
            if nxt == "run":                            # end exact (the run starts there) -> start must be nudged
                if cur == ex:
                    if out and tags[i - 1] == "run":
                        raise ValueError("stub between two coupled runs")
                    cur = (ex[0] + dn[0], ex[1] + dn[1])
                    if out:                             # move the previous primitive's end with it
                        out[-1] = out[-1][:-1] + (cur,)
                end = ex_end
            else:                                       # end nudged, opposite to the start's nudge if it had one
                o = (cur[0] - ex[0], cur[1] - ex[1])
                if o == (0, 0):
                    o_e = dn
                else:
                    o_e = (-o[0], -o[1])
                end = (ex_end[0] + o_e[0], ex_end[1] + o_e[1])
        out.append(("seg", cur, end))
        cur, ex = end, ex_end
    return out


def nm_length(prims):
    """length (mm) of a snap_nm path (arcs from their three points)"""
    tot = 0.0
    for pr in prims:
        if pr[0] == "seg":
            tot += math.hypot(pr[2][0] - pr[1][0], pr[2][1] - pr[1][1])
            continue
        (x1, y1), (x2, y2), (x3, y3) = pr[1], pr[2], pr[3]
        d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
        uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
        r = math.hypot(x1 - ux, y1 - uy)
        a1, a2, a3 = (math.atan2(y - uy, x - ux) for x, y in ((x1, y1), (x2, y2), (x3, y3)))
        sw = (a3 - a1) % (2 * math.pi)
        if (a2 - a1) % (2 * math.pi) > sw:
            sw = 2 * math.pi - sw
        tot += r * sw
    return tot * 1e-6


def coupled_region(path_l, path_r, n_l, n_r, step=0.02):
    """polygon between the centre lines of the two legs over their coupled part (first n_l / n_r primitives)"""
    from shapely.geometry import Polygon
    a = G.path_to_polyline(path_l[:n_l], step)
    b = G.path_to_polyline(path_r[:n_r], step)
    poly = Polygon(a + b[::-1])
    return poly.buffer(0)
