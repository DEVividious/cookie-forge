"""Settings from the command line: cutter parameters and the options that define a project."""
from ..config import DEFAULTS, IMPRINT_DEPTH
from ..errors import fail


def params_from_args(args):
    p = dict(DEFAULTS)
    for key in DEFAULTS:
        v = getattr(args, key, None)
        if v is not None:
            p[key] = v
    p["imprint"] = args.imprint
    p["holes"] = args.holes
    p["no_bridges"] = args.no_bridges
    p["mirror"] = not args.no_mirror
    p["dough"] = args.dough
    p["simplify_level"] = args.simplify_level
    if args.dough is not None:
        # the ridge ends IMPRINT_DEPTH above the board when the cutter is pressed through the dough
        if args.imprint_drop is not None:
            fail("use either --dough or --imprint-drop")
        if args.dough <= IMPRINT_DEPTH:
            fail(f"the dough must be thicker than the imprint depth ({IMPRINT_DEPTH} mm)")
        p["imprint_drop"] = round(args.dough - IMPRINT_DEPTH, 3)
    if p["imprint_drop"] >= p["height"] - p["flange_thickness"] - 2.0:
        fail("the imprint ridge would be too low; check --dough / --imprint-drop against --height")
    if p["blade_angle"] <= 0 or p["blade_angle"] >= 60:
        fail("the blade angle should be within 1-59°")
    if p["blade"] >= p["wall"]:
        fail("the blade must be narrower than the wall")
    return p


def project_options(args):
    """Command-line choices that define the project (everything except names, output and language)."""
    size = args.size if args.size in (None, "original") else float(args.size)
    threshold = args.threshold if args.threshold == "auto" else float(args.threshold)
    return dict(size=size, mode=args.mode, split=args.split, scale=args.scale, threshold=threshold,
                invert=args.invert, dpi=args.dpi, holes=args.holes, imprint=args.imprint,
                imprint_seams=args.imprint_seams, rotate=args.rotate, mirror=not args.no_mirror,
                bridges=not args.no_bridges, dough=args.dough, simplify_level=args.simplify_level)
