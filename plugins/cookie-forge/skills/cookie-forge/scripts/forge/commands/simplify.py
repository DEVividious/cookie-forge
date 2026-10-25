"""simplify: the outline at three simplification levels next to the current one, with numbers, and
whether the outline is complex enough to offer simplification at all."""
import os

from ..config import COMPLEX_SHRINK, GAP_MIN, LEVEL_NAMES
from ..errors import ForgeError
from ..geometry.design import design
from ..geometry.solid import build_solid
from ..i18n import mm, num, pct, t
from ..presentation.preview import draw_simplify
from ..printers import parse_bed
from ..project.layout import comparison_preview, cutter_dir, show, slugify
from ..project.settings import params_from_args
from ..template.collect import collect_shapes
from ..template.shapes import longest_side, transform
from .build import _target_size

LEVELS = ("light", "medium", "strong")


def cmd_simplify(args):
    bed = parse_bed(args.bed)
    p = params_from_args(args)
    target = _target_size(args)
    for k in collect_shapes(args):
        variants = simplify_variants(k, p, bed, target)
        path = comparison_preview(cutter_dir(args.output_dir, slugify(k.name)), "simplify", args.size)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        draw_simplify(k.name, variants, path)
        print(simplify_md(k.name, variants, path) + "\n")


def simplify_variants(k, p, bed, target):
    """The current outline and every level: dict(level, ok, body, raw, mean, max, gap, triangles)."""
    out = []
    for level in (p.get("simplify_level", "none"), *[lv for lv in LEVELS if lv != p.get("simplify_level")]):
        v = dict(level=level, ok=False)
        try:
            pr = design(k, dict(p, simplify_level=level), bed, mirror=False, target=target)
        except ForgeError:
            out.append(v)
            continue
        raw = transform(k, target / longest_side(k.body), center=False).body if target else k.body
        v.update(ok=True, body=pr.shape.body, raw=raw, gap=pr.narrowest,
                 mean=pr.shape.body.symmetric_difference(raw).area / raw.boundary.length,
                 max=pr.shape.body.boundary.hausdorff_distance(raw.boundary),
                 triangles=len(build_solid(pr).to_mesh().tri_verts))
        out.append(v)
    return out


def complexity(variants):
    """(complex, narrowest notch now, share the medium level shortens the outline by, any level possible)."""
    cur = variants[0]
    medium = next((v for v in variants[1:] if v["level"] == "medium" and v["ok"]), None)
    shrink = 1 - medium["body"].boundary.length / cur["body"].boundary.length if medium else 0.0
    possible = any(v["ok"] for v in variants[1:])
    narrow = cur["gap"] is not None and cur["gap"] < GAP_MIN
    return possible and (narrow or shrink >= COMPLEX_SHRINK), cur["gap"], shrink, possible


def simplify_md(name, variants, path):
    is_complex, gap, shrink, possible = complexity(variants)
    facts = t("narrowest notch {gap} (recommended ≥ {m}), the medium level shortens the outline by {s}",
              gap=mm(gap, 1) if gap else "-", m=mm(GAP_MIN, 1), s=pct(shrink * 100))
    if not possible:
        verdict = t("no level keeps the separate outlines and holes: simplification is not possible, don't offer it")
    elif is_complex:
        verdict = t("complex ({facts}): offer simplification", facts=facts)
    else:
        verdict = t("simple ({facts}): no need to offer simplification", facts=facts)
    out = [t("## Outline simplification: {name}", name=name), "", f"- {t('Outline')}: {verdict}", "",
           "| " + " | ".join([t("Variant"), t("Mean deviation from the template"), t("Max deviation"),
                              t("Narrowest notch"), t("Triangles"), t("Status")]) + " |",
           "|---|---|---|---|---|---|"]
    for i, v in enumerate(variants):
        label = t(LEVEL_NAMES[v["level"]]) + ("" if v["level"] == "none" else f" (`--simplify-level {v['level']}`)")
        if not v["ok"]:
            out.append(f"| {label} | - | - | - | - | {t('rejected: it would merge or split outlines or close a hole')} |")
            continue
        status = t("current settings") if i == 0 else "OK"
        out.append(f"| {label} | {mm(v['mean'], 2)} | {mm(v['max'], 1)} | {mm(v['gap'], 1) if v['gap'] else '-'} "
                   f"| {num(v['triangles'], 0)} | {status} |")
    out += ["", t("Variants preview: {path}", path=show(path))]
    return "\n".join(out)
