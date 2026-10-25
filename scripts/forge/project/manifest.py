"""project.json and .work/dry-run.json: what a project is made of, its identity and results."""
import hashlib
import json
import os
import time

from .. import VERSION
from ..config import DEFAULTS
from ..geometry.design import bed_share
from ..geometry.profile import bevel_height
from ..i18n import english
from ..template.shapes import outline_counts
from .layout import portable, sha256_file


MANIFEST_SCHEMA = 1


def source_records(k):
    """The source files of a cutter, with the names of their copies in the project directory."""
    files = (k.origin or {}).get("files", [])
    recs = []
    for i, f in enumerate(files):
        ext = os.path.splitext(f["path"])[1].lower() or ".png"
        rec = dict(role="source", file=f"source{ext}" if len(files) == 1 else f"source-{i + 1}{ext}",
                   original=portable(f["path"]), sha256=sha256_file(f["path"]), page=f.get("page"))
        if k.origin.get("component"):
            rec["component"] = k.origin["component"]
        if f.get("placement"):
            rec["placement"] = dict(zip(("dx", "dy", "size", "rotation"), f["placement"]))
        recs.append((f["path"], rec))
    imp = (k.origin or {}).get("imprint_from")
    if imp:
        ext = os.path.splitext(imp)[1].lower() or ".png"
        recs.append((imp, dict(role="imprint_source", file=f"imprint-source{ext}", original=portable(imp),
                               sha256=sha256_file(imp))))
    return recs


def printer_info(bed, p):
    if not bed:
        return None
    return dict(name=bed[3], bed_mm=[bed[0], bed[1], bed[2]], margin_mm=p["margin"])


IMPRINT_PARAMETERS = ("imprint_width", "imprint_tip", "imprint_drop")
IMPRINT_OPTIONS = ("dough", "imprint_seams")


def fingerprint(sources, options, p, bed):
    """Identity of a project: source contents and every setting that changes the result.
    Without an imprint (--imprint none) the imprint settings change nothing, so they don't count;
    without simplification the option is left out, so builds made before it existed stay identical."""
    parameters = {k: p[k] for k in DEFAULTS}
    if options.get("simplify_level", "none") == "none":
        options = {k: v for k, v in options.items() if k != "simplify_level"}
    if options.get("imprint") == "none":
        parameters = {k: v for k, v in parameters.items() if k not in IMPRINT_PARAMETERS}
        options = {k: v for k, v in options.items() if k not in IMPRINT_OPTIONS}
    data = dict(sources=[{k: v for k, v in r.items() if k not in ("original", "file")} for _, r in sources],
                options=options, parameters=parameters,
                bed=[bed[0], bed[1], bed[2]] if bed else None)
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def manifest(pr, stage, options, extra=None):
    """project.json (stage built) and .work/dry-run.json (stage dry-run). Paths are relative to the
    project directory; `original` paths are relative to the directory the generator ran from."""
    p, k = pr.p, pr.shape
    lin, area = bed_share(pr)
    n_out, n_holes = outline_counts(k.body)
    with english():
        warnings, fixes = [str(m) for m in pr.warnings], [str(m) for m in pr.fixes]
    m = dict(
        schema="cookie-forge/project", schema_version=MANIFEST_SCHEMA,
        generator=dict(name="cookie-forge", version=VERSION),
        id=pr.slug, name=k.name, stage=stage, updated=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        fingerprint=pr.fingerprint,
        sources=[r for _, r in pr.sources],
        options=options,
        parameters={key: p[key] for key in DEFAULTS},
        printer=printer_info(pr.bed, p),
        result=dict(
            cookie_mm=[round(v, 3) for v in pr.cookie_dims],
            footprint_mm=[round(v, 3) for v in pr.footprint_dims],
            bed_share_pct=dict(longer_side=round(lin, 1), area=round(area, 1)) if lin is not None else None,
            bevel_height_mm=round(bevel_height(p), 3),
            smoothing=dict(radius_mm=round(p["smooth"] * pr.rescale, 4), simplify_mm=round(p["simplify"] * pr.rescale, 4),
                           rescale=round(pr.rescale, 6),
                           template_px_mm=round(k.px_size, 5) if k.px_size else None,
                           threshold=dict(mode=k.threshold[0], value=k.threshold[1]) if k.threshold else None),
            imprint=dict(ridges=len(pr.ridges), holes_cut=k.holes_cut, holes_imprint=k.holes_imprint,
                         depth_mm=round(p["dough"] - p["imprint_drop"], 2) if p.get("dough") and pr.ridges else None),
            bridges=dict(count=len(pr.beams)),
            simplification=dict(level=pr.simplified[0], sigma_mm=round(pr.simplified[1] * pr.rescale, 3),
                                radius_mm=round(pr.simplified[2] * pr.rescale, 3)) if pr.simplified else None,
            checks=dict(thinnest_mm=round(pr.thinnest, 2), narrowest_mm=round(pr.narrowest, 2) if pr.narrowest else None,
                        fits_bed=pr.fits, fits_height=pr.fits_height, outlines=n_out, through_holes=n_holes),
        ),
        warnings=warnings, fixes=fixes,
        files=[dict(path=os.path.relpath(path, pr.out_dir), role=role, status=status) for path, role, status in pr.files],
    )
    m.update(extra or {})
    return m
