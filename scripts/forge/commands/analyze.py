"""analyze: read the template(s), propose sizes, keep template versions."""
import os

from ..config import GAP_MIN, SUGGESTED_SIZES, THIN_CRITICAL, THIN_MIN
from ..geometry.design import bed_share, design, max_size
from ..geometry.outline import smooth_body
from ..i18n import mm, num, pct, t
from ..presentation.preview import draw_detection
from ..printers import parse_bed
from ..project.layout import READING_FILE, WORK_DIR, record_template, show, slugify
from ..project.settings import params_from_args
from ..template.collect import collect_shapes
from ..template.shapes import Shape, outline_counts, transform
from ..template.sources import parse_source


def cmd_analyze(args):
    bed = parse_bed(args.bed)
    p = params_from_args(args)
    shapes = collect_shapes(args)
    print(t("# Analysis: {n} cutter(s) from {m} source(s)", n=len(shapes), m=len(args.sources)) + "\n")
    for k in shapes:
        _print_shape(args, k, p, bed)
    _save_reading(args, shapes)


def _print_shape(args, k, p, bed):
    """What was read from one template, and the table of proposed sizes."""
    ks = smooth_body(k.body, p["smooth"], p["simplify"])
    minx, miny, maxx, maxy = ks.bounds
    w, h = maxx - minx, maxy - miny
    n_parts, n_holes = outline_counts(ks)
    print(f"## {k.name}  ({k.source})")
    print("- " + t("aspect ratio W:H = {r}, {parts} part(s), {holes} through-hole(s), {imp} imprint region(s), {himp} hole(s) as imprint",
                   r=num(w / h, 2), parts=n_parts, holes=n_holes, imp=len(k.imprints), himp=k.holes_imprint))
    if k.mm_per_px:
        print("- " + t("physical size in the file: {w} × {h} mm", w=num(w, 0), h=num(h, 0)))
    for u in k.fixes:
        print("- " + t("note: {text}", text=u))
    print()
    header = [t("Variant"), t("Cookie (mm)"), t("With flange (mm)")]
    if bed:
        header += [t("% of longer bed side"), t("% of bed area")]
    header += [t("Thinnest feature"), t("Narrowest notch"), t("Notes")]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for name, size in _size_variants(args, k, p, bed, max(w, h)):
        kk = transform(Shape(k.name, ks, k.imprints, k.source, k.mm_per_px), size / max(w, h), center=False)
        pr = design(kk, {**p, "smooth": 0, "simplify": 0}, bed, mirror=False)
        print("| " + " | ".join(str(c) for c in _size_row(name, pr, bed)) + " |")
    print()


def _size_variants(args, k, p, bed, longest):
    """S/M/L/XL, the chosen size, the largest that fits the bed and the size in the file."""
    variants = list(SUGGESTED_SIZES)
    if args.size not in (None, "original"):
        variants.append((t("chosen"), float(args.size)))
    ms = max_size(k, p, bed)
    if ms:
        variants.append(("MAX", ms))
    if k.mm_per_px:
        variants.append((t("original"), longest))
    return variants


def _size_row(name, pr, bed):
    notes = []
    if pr.thinnest < THIN_MIN:
        notes.append(t("thin feature") if pr.thinnest >= THIN_CRITICAL else t("TOO thin feature"))
    if pr.narrowest is not None and pr.narrowest < GAP_MIN:
        notes.append(t("narrow notch"))
    if not pr.fits:
        notes.append(t("DOES NOT FIT"))
    row = [name, f"{num(pr.cookie_dims[0], 0)} × {num(pr.cookie_dims[1], 0)}",
           f"{num(pr.footprint_dims[0], 0)} × {num(pr.footprint_dims[1], 0)}"]
    if bed:
        lin, area = bed_share(pr)
        row += [pct(lin), pct(area)]
    row += [mm(pr.thinnest, 1), mm(pr.narrowest, 1) if pr.narrowest else "-", ", ".join(notes) if notes else "OK"]
    return row


def _save_reading(args, shapes):
    """The reading preview and, for a single template, its copy in the template history."""
    first = parse_source(args.sources[0])[0]
    work = os.path.join(args.output_dir, slugify(args.name or os.path.splitext(os.path.basename(first))[0]), WORK_DIR)
    preview = args.preview or os.path.join(work, READING_FILE)
    os.makedirs(os.path.dirname(os.path.abspath(preview)), exist_ok=True)
    draw_detection([(f"{k.name}", k) for k in shapes], preview, show_imprint=args.imprint != "none")
    print(t("Template reading preview: {path}", path=show(preview)))
    if len(args.sources) == 1 and args.mode != "merge":
        copy, new = record_template(work, first)
        print(t("Template version: {path} (new copy)", path=show(copy)) if new
              else t("Template version: {path} (already recorded)", path=show(copy)))
