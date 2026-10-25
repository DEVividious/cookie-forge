"""Turns the sources of a command into shapes in mm, per mode (separate, split, merge)."""
from ..errors import fail
from ..i18n import t
from .shapes import Shape, contours_to_shapes, longest_side, merge_components, transform
from .sources import load_sources, mask_from_source


def collect_shapes(args):
    """Loads the sources and returns a list of shapes in mm (not smoothed yet), per mode."""
    raw = _read_sources(args)
    names = args.names.split(",") if args.names else []
    if args.mode == "merge":
        return [_imprint_from(args, _merged_shape(args, raw, names))]
    return _separate_shapes(args, raw, names)


def _read_sources(args):
    """[(Source, [Shape in px], upscale)] for every source file / PDF page."""
    raw = []
    for z in load_sources(args.sources, args.dpi):
        mask, up, th = mask_from_source(z, args.threshold, args.invert)
        comps = contours_to_shapes(mask, args.holes, z.name, z.path, (z.mm_per_px / up) if z.mm_per_px else None)
        if not comps:
            fail(f"no shape found in {z.path} (check --threshold / --invert)")
        for c in comps:
            c.px_size = up      # one template pixel = `up` mask pixels
            c.threshold = ("auto" if args.threshold == "auto" else "manual", float(th))
        raw.append((z, comps, up))
    return raw


def _imprint_from(args, k):
    """All black regions of the --imprint-from image as imprint, fitted into the cookie outline."""
    if not args.imprint_from:
        return k
    from shapely import affinity
    from shapely.ops import unary_union
    zo = load_sources([args.imprint_from], args.dpi)[0]
    mask, up, _ = mask_from_source(zo, args.threshold, args.invert)
    comps = contours_to_shapes(mask, "ignore", zo.name, zo.path, None, min_share=0.0)
    if not comps:
        fail(f"{args.imprint_from}: no imprint lines found")
    regions = [s.body for s in comps] + [o for s in comps for o in s.imprints if not isinstance(o, tuple)]
    u = unary_union(regions)
    bx = k.body.bounds
    ux = u.bounds
    sc = max(bx[2] - bx[0], bx[3] - bx[1]) / max(ux[2] - ux[0], ux[3] - ux[1])
    g = affinity.scale(u, sc, sc, origin=((ux[0] + ux[2]) / 2, (ux[1] + ux[3]) / 2))
    g = affinity.translate(g, (bx[0] + bx[2]) / 2 - (ux[0] + ux[2]) / 2, (bx[1] + bx[3]) / 2 - (ux[1] + ux[3]) / 2)
    k.imprints = list(k.imprints) + [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon"]
    k.source += t(" + imprint from {path}", path=zo.path)
    k.origin = dict(k.origin or {}, imprint_from=args.imprint_from)
    return k


def _scale_for(args, k_px, src, up):
    """px -> mm scale of a shape (None when the build has no size to go by)."""
    if args.size in (None, "original"):
        if src.mm_per_px:
            return src.mm_per_px / up
        if args.size == "original":
            fail(f"{src.path}: the file has no physical size (DPI); give --size in mm")
        if args.cmd == "analyze":           # a nominal scale is enough for the analysis
            return 100.0 / longest_side(k_px.body)
        return None
    return float(args.size) / longest_side(k_px.body)


def _merged_shape(args, raw, names):
    """--mode merge: every source placed at its offset and size, united into one shape."""
    from shapely.ops import unary_union
    parts = []
    for z, comps, up in raw:
        k = merge_components(comps, z.name)
        size = z.size
        if size is None:
            if z.mm_per_px:
                sc = z.mm_per_px / up
            else:
                fail(f"in merge mode give the size of each part: {z.path}@dx,dy,size_mm")
        else:
            sc = size / longest_side(k.body)
        parts.append(transform(k, sc, rotation=z.rotation, dx=z.dx, dy=z.dy))
    body = unary_union([c.body for c in parts])
    imp = sum((c.imprints for c in parts), [])
    if args.imprint_seams:
        # inner boundaries between the merged shapes as imprint
        seams = unary_union([c.body.boundary for c in parts]).difference(body.boundary.buffer(0.05))
        if not seams.is_empty:
            imp.append(seams.buffer(0.3))
    k = Shape(names[0] if names else (args.name or "merged"), body, imp,
              " + ".join(c.source for c in parts), None,
              origin=dict(files=[dict(path=z.file, page=z.page, placement=[z.dx, z.dy, z.size, z.rotation])
                                 for z, _, _ in raw]))
    if args.size not in (None, "original"):
        return transform(k, float(args.size) / longest_side(k.body))
    return transform(k, 1.0)


def _separate_shapes(args, raw, names):
    """Every source (with --split every shape in it) is a separate cutter."""
    result = []
    for z, comps, up in raw:
        group = comps if args.split else [merge_components(comps, z.name)]
        # shared scale within one source (a template sheet keeps its proportions)
        if args.size not in (None, "original") and args.scale == "shared" and len(group) > 1:
            largest = max(group, key=lambda k: longest_side(k.body))
            sc_shared = float(args.size) / longest_side(largest.body)
        else:
            sc_shared = None
        for i, k in enumerate(group):
            sc = sc_shared if sc_shared else _scale_for(args, k, z, up)
            if sc is None:
                fail("give --size (longest side of the cookie in mm) or --size original for a PDF")
            k.name = _cutter_name(args, names, len(result), len(raw), group, i, z)
            k.origin = dict(files=[dict(path=z.file, page=z.page)],
                            component=i + 1 if args.split and len(group) > 1 else None)
            k = transform(k, sc, rotation=args.rotate)
            result.append(_imprint_from(args, k))
    return result


def _cutter_name(args, names, counter, n_sources, group, i, z):
    """--names in order, else --name, else the source name (numbered for split sheets)."""
    if counter < len(names):
        return names[counter]
    if args.name and n_sources == 1 and len(group) == 1:
        return args.name
    if args.split and len(group) > 1:
        return f"{args.name or z.name}_{i + 1}"
    return args.name or z.name if n_sources == 1 else z.name
