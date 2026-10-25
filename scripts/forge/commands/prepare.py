"""prepare: a new template version with the inner lines detached from the outline."""
import os

import numpy as np

from ..errors import fail
from ..i18n import mm, num, t
from ..presentation.preview import draw_prepare
from ..project.layout import PREPARE_FILE, cutter_dir, next_template, record_template, show, slugify
from ..template.prepare import apply_cuts, find_cuts
from ..template.sources import load_sources, mask_from_source


def cmd_prepare(args):
    """New template version with the inner lines detached from the outline (see detach_lines)."""
    z = _single_source(args)
    work = cutter_dir(args.output_dir, slugify(args.name or z.name))
    mask, _, _ = mask_from_source(z, args.threshold, args.invert, min_width_px=0)
    longest_px = _longest_side_px(args, mask)
    mm_per_px = _mm_per_px(args, z, longest_px)
    gap_px = args.gap / mm_per_px
    cut, places = find_cuts(mask, gap_px)
    if not places:
        print(t("Nothing to detach: no inner line touches the outline. Keep using {path}.", path=show(args.source)))
        return
    image, ext, save_options = apply_cuts(args.source, z, cut, args.dpi)
    record_template(work, args.source)                     # the template before the change
    dest = next_template(work, ext)
    image.save(dest, **save_options)
    preview = os.path.join(work, PREPARE_FILE)
    draw_prepare(z.gray, cut, preview)
    print(t("Prepared template: {path} (new version)", path=show(dest)))
    print(t("Inner lines detached in {n} place(s), gap {gap} at a cookie size of {size} ({px} px).",
            n=places, gap=mm(args.gap), size=mm(longest_px * mm_per_px, 0), px=num(gap_px, 0)))
    print(t("Changes (red): {path}", path=show(preview)))
    print(t("Check the reading of the new version with analyze before going on."))


def _single_source(args):
    sources = load_sources([args.source], args.dpi)
    if len(sources) != 1:
        fail("prepare takes one image or a one-page PDF")
    return sources[0]


def _longest_side_px(args, mask):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        fail(f"no shape found in {args.source} (check --threshold / --invert)")
    return max(xs.max() - xs.min(), ys.max() - ys.min()) + 1


def _mm_per_px(args, z, longest_px):
    """Scale at the cookie size the gap is measured at (--size, default 100 mm, or the file's)."""
    if args.size == "original":
        if not z.mm_per_px:
            fail(f"{args.source}: the file has no physical size (DPI); give --size in mm")
        return z.mm_per_px
    return float(args.size or 100) / longest_px
