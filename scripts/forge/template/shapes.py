"""From a mask to shapes (shapely): cookie body, imprint regions, transforms."""
from dataclasses import dataclass, field

import numpy as np

from ..i18n import Msg, count, unique_msgs


@dataclass
class Shape:
    name: str
    body: object                        # shapely (Multi)Polygon - cookie area (holes = through-holes)
    imprints: list = field(default_factory=list)  # imprinted regions (shapely Polygon, mm after scaling)
    source: str = ""
    mm_per_px: float | None = None
    fixes: list = field(default_factory=list)     # automatic corrections, for the summary
    holes_cut: int = 0
    holes_imprint: int = 0
    px_size: float | None = None        # size of one template pixel in the current units
    threshold: tuple | None = None      # ("auto"|"manual", value) used for this template
    origin: dict | None = None          # source files, page, component, placement (for the manifest)


def contours_to_shapes(mask, holes_policy, name, source_desc, mm_per_px, min_share=0.01):
    """Builds shapes from the contour hierarchy. Returns a list of components (each = one
    top-level contour) as Shape in pixels (y up)."""
    import cv2
    from shapely.geometry import Polygon
    from shapely.validation import make_valid

    cont, hier = cv2.findContours(mask.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    if hier is None or len(cont) == 0:
        return []
    hier = hier[0]
    H = mask.shape[0]

    def poly(i):
        pts = cont[i][:, 0, :].astype(float)
        if len(pts) < 3:
            return None
        pts[:, 1] = H - pts[:, 1]
        p = Polygon(pts)
        if not p.is_valid:
            p = make_valid(p)
            if p.geom_type != "Polygon":
                # take the largest polygon
                parts = [g for g in getattr(p, "geoms", [p]) if g.geom_type == "Polygon"]
                p = max(parts, key=lambda g: g.area) if parts else None
        return p

    def children(i):
        j = hier[i][2]
        while j != -1:
            yield j
            j = hier[j][0]

    def all_black_inside(i_hole):
        """All black regions inside hole i (recursively), as polygons with their holes."""
        result = []
        for w in children(i_hole):              # w = island (black)
            pw = poly(w)
            if pw is None or pw.area < 4:
                continue
            island_holes = []
            for d in children(w):               # d = hole in the island (white)
                pd = poly(d)
                if pd is not None and pd.area > 4:
                    island_holes.append(pd)
                result.extend(all_black_inside(d))
            reg = pw
            for pd in island_holes:
                reg = reg.difference(pd)
            result.append(reg)
        return result

    components = []
    top = [i for i in range(len(cont)) if hier[i][3] == -1]
    areas = {i: cv2.contourArea(cont[i]) for i in top}
    largest = max(areas.values()) if areas else 0
    dropped = 0
    for i in top:
        if areas[i] < min_share * largest or areas[i] < 25:
            dropped += 1
            continue
        outer = poly(i)
        if outer is None:
            continue
        body = outer
        imprints = []
        n_cut = n_imp = 0
        for d in children(i):
            pd = poly(d)
            if pd is None or pd.area < 4:
                continue
            if pd.area > 0.5 * outer.area:
                # inside of a contour drawing: the black lines inside are the imprint
                imprints.extend(all_black_inside(d))
            else:
                islands = all_black_inside(d)
                if holes_policy == "cut":
                    body = body.difference(pd)
                    n_cut += 1
                    # black islands inside a cut-out hole make no sense - skip them
                elif holes_policy == "imprint":
                    imprints.append(("outline", pd))
                    imprints.extend(islands)
                    n_imp += 1
                else:
                    imprints.extend(islands)
        k = Shape(name, body, imprints, source_desc, mm_per_px)
        k.holes_cut, k.holes_imprint = n_cut, n_imp
        if dropped:
            k.fixes.append(Msg("ignored {specks} (noise)", specks=lambda n=dropped: count(n, "speck")))
        components.append(k)
    # reading order: rows from the top, left to right within a row
    if components:
        hgt = max(k.body.bounds[3] - k.body.bounds[1] for k in components)
        components.sort(key=lambda k: (-round((k.body.bounds[1] + k.body.bounds[3]) / 2 / (0.6 * hgt)), k.body.bounds[0]))
    return components


def merge_components(components, name):
    """Several top-level contours in one image -> one shape (separate walls,
    shared flange and bridges)."""
    from shapely.ops import unary_union
    body = unary_union([k.body for k in components])
    imprints = sum((k.imprints for k in components), [])
    first = components[0]
    k = Shape(name, body, imprints, first.source, first.mm_per_px, px_size=first.px_size, threshold=first.threshold,
              origin=first.origin)
    k.holes_cut = sum(s.holes_cut for s in components)
    k.holes_imprint = sum(s.holes_imprint for s in components)
    k.fixes = unique_msgs(sum((s.fixes for s in components), []))
    if len(components) > 1:
        k.fixes.append(Msg("the image contains {shapes}; merged them into one cutter (use --split to get separate files)",
                           shapes=lambda n=len(components): count(n, "separate shape")))
    return k


def transform(k, scale, rotation=0.0, mirror=False, dx=0.0, dy=0.0, center=True):
    """Scales (px -> mm), rotates, mirrors and moves a shape."""
    from shapely import affinity

    def tr(g):
        if center:
            minx, miny, maxx, maxy = k.body.bounds
            g = affinity.translate(g, -(minx + maxx) / 2, -(miny + maxy) / 2)
        g = affinity.scale(g, scale, scale, origin=(0, 0))
        if rotation:
            g = affinity.rotate(g, rotation, origin=(0, 0))
        if mirror:
            g = affinity.scale(g, -1, 1, origin=(0, 0))
        if dx or dy:
            g = affinity.translate(g, dx, dy)
        return g

    imp = []
    for o in k.imprints:
        if isinstance(o, tuple):
            imp.append((o[0], tr(o[1])))
        else:
            imp.append(tr(o))
    return Shape(k.name, tr(k.body), imp, k.source, k.mm_per_px, list(k.fixes), k.holes_cut, k.holes_imprint,
                 k.px_size * scale if k.px_size else None, k.threshold, k.origin)


def longest_side(g):
    minx, miny, maxx, maxy = g.bounds
    return max(maxx - minx, maxy - miny)


def outline_counts(g):
    """(separate outlines, through-holes) of a cookie body."""
    polys = [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon"]
    return len(polys), sum(len(p.interiors) for p in polys)
