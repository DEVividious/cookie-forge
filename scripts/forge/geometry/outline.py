"""2D geometry in mm: smoothing, imprint ridges, bridges, measurements."""
import math

import numpy as np

from ..config import GAP_SEARCH_MAX, THIN_SEARCH_MAX


def smooth_body(body, r, tol):
    from shapely.ops import unary_union
    g = body
    if r > 0:
        g = g.buffer(r, join_style="round").buffer(-2 * r, join_style="round").buffer(r, join_style="round")
    if tol > 0:
        g = g.simplify(tol, preserve_topology=True)
    g = g.buffer(0)
    if g.is_empty:
        return body
    if g.geom_type == "MultiPolygon":
        # smoothing may have cut off specks - keep everything above 1 mm2
        g = unary_union([p for p in g.geoms if p.area > 1.0])
    # closing a narrow notch must not create a new hole in the cookie:
    # only holes that existed in the original stay
    from shapely.geometry import Polygon
    orig_holes = [Polygon(r) for p in getattr(body, "geoms", [body]) for r in p.interiors]
    new = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type != "Polygon":
            continue
        holes = [r for r in p.interiors if any(Polygon(r).intersects(o) for o in orig_holes)]
        new.append(Polygon(p.exterior, holes))
    g = unary_union(new) if new else body
    return g


def imprint_ridges(k, p):
    """Turns imprinted regions into ridge footprints (IMPRINT_WIDTH wide)."""
    from shapely.ops import unary_union
    out = []
    inside = k.body.buffer(-p["blade"])
    for o in k.imprints:
        if isinstance(o, tuple):            # ("outline", hole) - imprint only the hole outline
            g = o[1].boundary.buffer(p["imprint_width"] / 2, join_style="round")
        else:
            reg = o.buffer(0)
            if reg.is_empty:
                continue
            thick = 2 * reg.area / max(reg.length, 1e-9)   # approximate line thickness
            if thick < 2 * p["imprint_width"]:
                g = reg.buffer(max(0.0, (p["imprint_width"] - thick) / 2), join_style="round")
            else:                                          # blob: imprint only its outline
                g = reg.boundary.buffer(p["imprint_width"] / 2, join_style="round")
        g = g.simplify(p["simplify"], preserve_topology=True).intersection(inside)
        if g.is_empty:
            continue
        for part in getattr(g, "geoms", [g]):
            if part.geom_type == "Polygon" and part.area >= 1.0:
                out.append(part)
    if not out:
        return []
    u = unary_union(out)
    return [g for g in getattr(u, "geoms", [u]) if g.geom_type == "Polygon"]


def bridges(base_parts, width):
    """Joins disconnected parts (list of polygons at flange level) with beams.
    Returns a list of beam polygons."""
    from shapely.geometry import Point
    from shapely.ops import unary_union, nearest_points
    beams = []
    parts_in = list(base_parts)
    for _ in range(200):
        u = unary_union(parts_in + beams)
        parts = list(getattr(u, "geoms", [u]))
        if len(parts) <= 1:
            break
        parts.sort(key=lambda g: -g.area)
        main, rest = parts[0], parts[1:]
        # join the part closest to the main one
        nearest = min(rest, key=lambda g: g.distance(main))
        rest_u = unary_union([main] + [g for g in rest if g is not nearest])
        p1, p2 = nearest_points(nearest, rest_u)
        beams.append(beam(p1, p2, width))
        # a long part gets a second bridge from its far end
        if nearest.length > 12 * 2:
            pts = np.array(nearest.exterior.coords)
            d = np.hypot(pts[:, 0] - p1.x, pts[:, 1] - p1.y)
            far = Point(pts[int(d.argmax())])
            if far.distance(p1) > 10:
                q1, q2 = nearest_points(far.buffer(0.01), rest_u)
                beams.append(beam(q1, q2, width))
    return beams


def beam(p1, p2, width, extra=1.5):
    from shapely.geometry import LineString
    dx, dy = p2.x - p1.x, p2.y - p1.y
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return p1.buffer(width / 2)
    ux, uy = dx / L, dy / L
    a = (p1.x - ux * extra, p1.y - uy * extra)
    b = (p2.x + ux * extra, p2.y + uy * extra)
    return LineString([a, b]).buffer(width / 2, cap_style="flat")


def thinnest_feature(g, share=0.02, lo=0.2, hi=THIN_SEARCH_MAX):
    """Smallest width w for which a morphological opening with diameter w removes at least
    `share` of the area. Approximates the thinnest significant feature of the cookie."""
    A = g.area
    if A <= 0:
        return 0.0

    def loss(w):
        o = g.buffer(-w / 2).buffer(w / 2)
        return (A - o.area) / A

    if loss(lo) >= share:
        return lo
    if loss(hi) < share:
        return hi
    for _ in range(18):
        mid = (lo + hi) / 2
        if loss(mid) >= share:
            hi = mid
        else:
            lo = mid
    return hi


def narrowest_gap(g, min_area_mm2=4.0, lo=0.3, hi=GAP_SEARCH_MAX):
    """Narrowest gap between parts of the cookie (a notch the wall has to fit into)."""
    minx, miny, maxx, maxy = g.bounds
    from shapely.geometry import box
    comp = box(minx - 5, miny - 5, maxx + 5, maxy + 5).difference(g)

    def loss(w):
        o = comp.buffer(-w / 2).buffer(w / 2)
        return comp.area - o.area

    if loss(lo) >= min_area_mm2:
        return lo
    if loss(hi) < min_area_mm2:
        return None
    for _ in range(18):
        mid = (lo + hi) / 2
        if loss(mid) >= min_area_mm2:
            hi = mid
        else:
            lo = mid
    return hi
