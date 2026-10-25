"""Design: the full data set of one cutter after scaling, with its checks."""
import math
from dataclasses import dataclass, field

from ..config import GAP_MIN, THIN_CRITICAL, THIN_MIN
from ..i18n import Msg, count, num, val
from ..template.shapes import Shape, longest_side, outline_counts, transform
from .outline import bridges, imprint_ridges, narrowest_gap, smooth_body, thinnest_feature


@dataclass
class Design:
    shape: Shape
    p: dict
    ridges: list
    beams: list
    footprint: object
    cookie_dims: tuple
    footprint_dims: tuple
    bed: tuple | None
    warnings: list
    fixes: list                    # automatic corrections made while loading and designing
    thinnest: float                # measured on the final cookie outline (mm)
    narrowest: float | None
    fits: bool                     # footprint fits on the bed with the margin (True without a bed)
    fits_height: bool
    rescale: float = 1.0           # scale applied after smoothing to hit the requested size
    size_note: str = ""
    index: int = 1
    total: int = 1
    # output (set by cmd_build)
    slug: str = ""
    size_txt: str = ""
    out_dir: str = ""
    decision: str = ""             # new | new_version | identical | overwrite
    sources: list = field(default_factory=list)
    fingerprint: str = ""
    files: list = field(default_factory=list)     # (path, role, status)


def design(k, p, bed, mirror=True, target=None):
    from shapely.ops import unary_union
    before = outline_counts(k.body)
    k = Shape(k.name, smooth_body(k.body, p["smooth"], p["simplify"]), k.imprints, k.source,
              k.mm_per_px, list(k.fixes), k.holes_cut, k.holes_imprint, k.px_size, k.threshold, k.origin)
    fixes = list(k.fixes)
    after = outline_counts(k.body)
    if after[0] != before[0]:
        fixes.append(Msg("smoothing changed the number of separate outlines from {a} to {b}", a=before[0], b=after[0]))
    if after[1] != before[1]:
        fixes.append(Msg("smoothing changed the number of through-holes from {a} to {b}", a=before[1], b=after[1]))
    rescale = 1.0
    if target:
        # smoothing trims the tips, so scale back to the requested size afterwards
        rescale = target / longest_side(k.body)
        k = transform(k, rescale, center=False)
        if abs(rescale - 1) >= 5e-5:
            fixes.append(Msg("after smoothing, scaled by × {f} so the longest side is exactly {size} mm",
                             f=lambda: num(rescale, 4), size=lambda: val(target)))
    if mirror:
        k = transform(k, 1.0, mirror=True, center=False)
    ridges = imprint_ridges(k, p) if p.get("imprint", "auto") != "none" else []
    flange = k.body.buffer(p["flange"], join_style="round")
    base = [flange.difference(k.body)] + ridges
    beams = bridges(base, p["bridge_width"]) if not p.get("no_bridges") else []
    footprint = unary_union([flange] + ridges + beams)
    cb = k.body.bounds
    fb = footprint.bounds
    cookie_dims = (cb[2] - cb[0], cb[3] - cb[1])
    footprint_dims = (fb[2] - fb[0], fb[3] - fb[1])

    warn = []
    thin = thinnest_feature(k.body)
    if thin < THIN_CRITICAL:
        warn.append(Msg("the thinnest cookie feature is about {v} mm - it breaks very easily (recommended ≥ {m} mm)",
                        v=lambda: num(thin), m=lambda: val(THIN_MIN)))
    elif thin < THIN_MIN:
        warn.append(Msg("the thinnest cookie feature is about {v} mm - delicate (recommended ≥ {m} mm)",
                        v=lambda: num(thin), m=lambda: val(THIN_MIN)))
    gap = narrowest_gap(k.body)
    if gap is not None and gap < GAP_MIN:
        warn.append(Msg("the narrowest notch is about {v} mm - dough may stick in the cutter (recommended ≥ {m} mm)",
                        v=lambda: num(gap), m=lambda: val(GAP_MIN)))
    fits = fits_height = True
    if bed:
        mx, my = bed[0] - 2 * p["margin"], bed[1] - 2 * p["margin"]
        w, h = footprint_dims
        fits = (w <= mx and h <= my) or (h <= mx and w <= my)
        if not fits:
            warn.append(Msg("the footprint {w} × {h} mm does not fit on the bed {bw} × {bh} mm (with a {m} mm margin)",
                            w=lambda: num(w), h=lambda: num(h), bw=lambda: val(bed[0], 0), bh=lambda: val(bed[1], 0),
                            m=lambda: val(p["margin"])))
        if bed[2] and p["height"] > bed[2]:
            fits_height = False
            warn.append(Msg("the cutter is taller than the build volume of the printer ({h} mm > {z} mm)",
                            h=lambda: val(p["height"]), z=lambda: val(bed[2], 0)))
    if beams:
        fixes.append(Msg("added {bridges} joining loose parts (imprint/holes) to the flange",
                         bridges=lambda: count(len(beams), "bridge")))
    return Design(k, p, ridges, beams, footprint, cookie_dims, footprint_dims, bed, warn, fixes,
                  thin, gap, fits, fits_height, rescale)


def bed_share(pr):
    if not pr.bed:
        return None, None
    w, h = pr.footprint_dims
    lin = max(w, h) / max(pr.bed[0], pr.bed[1]) * 100
    area = (w * h) / (pr.bed[0] * pr.bed[1]) * 100
    return lin, area


def max_size(k, p, bed):
    """Largest cookie size (longest side) whose footprint still fits on the bed."""
    if not bed:
        return None
    sx, sy = bed[0] - 2 * p["margin"], bed[1] - 2 * p["margin"]
    minx, miny, maxx, maxy = k.body.bounds
    w, h = maxx - minx, maxy - miny
    lng = max(w, h)
    sht = min(w, h)
    fl = 2 * p["flange"]
    # longer side along the longer side of the bed
    a = min(max(sx, sy) - fl, (min(sx, sy) - fl) * lng / sht) if sht > 0 else max(sx, sy) - fl
    return math.floor(a)
