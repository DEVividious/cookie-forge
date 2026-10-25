"""build: the dry run (summary, .work/ files) and the build itself (STL, preview, manifest)."""
import json
import os
import re
import shlex
import shutil
import sys
import time

from ..geometry.design import design
from ..geometry.solid import build_solid, check_stl, save_stl
from ..i18n import Msg
from ..presentation.preview import draw_preview
from ..presentation.report import build_report, cutter_result
from ..presentation.summary import size_note, summary_md
from ..printers import parse_bed
from ..project.layout import (DRY_RUN_FILE, DRY_RUN_PREVIEW_FILE, MANIFEST_FILE, PREVIEW_FILE, STL_FILE, WORK_DIR,
                              built_manifest, choose_target, planned_files, sha256_file, slugify, write_json)
from ..project.manifest import fingerprint, manifest, source_records
from ..project.settings import params_from_args, project_options
from ..template.collect import collect_shapes


def build_args():
    """Arguments that build exactly what this run describes (without the dry-run flags)."""
    return [a for a in sys.argv[1:] if a not in ("--dry-run", "--preview-2d", "--json")]


def build_command():
    return "uv run " + shlex.join([sys.argv[0]] + build_args())


def cmd_build(args):
    options = project_options(args)
    designs = _plan(args, options)
    if args.dry_run:
        _dry_run(args, designs, options)
    else:
        _build(args, designs, options)


def _plan(args, options):
    """Designs every cutter of the run and decides where each one goes."""
    bed = parse_bed(args.bed)
    p = params_from_args(args)
    shapes = collect_shapes(args)
    target = _target_size(args)
    designs, taken = [], set()
    for i, k in enumerate(shapes):
        pr = design(k, p, bed, mirror=p["mirror"], target=target)
        pr.size_note = size_note(args, target)
        pr.index, pr.total = i + 1, len(shapes)
        pr.size_txt = f"{max(pr.cookie_dims):.0f}"
        _assign_slug(pr, k.name, taken)
        pr.sources = source_records(k)
        pr.fingerprint = fingerprint(pr.sources, options, p, bed)
        pr.out_dir, pr.decision = choose_target(os.path.join(args.output_dir, pr.slug), pr.size_txt, pr.fingerprint,
                                                args.overwrite, args.new_version)
        designs.append(pr)
    return designs


def _target_size(args):
    """The exact longest side to scale to after smoothing; None where the scale comes from elsewhere
    (merged parts, a shared sheet scale, the physical size of the file)."""
    if args.size in (None, "original") or args.mode == "merge" or (args.split and args.scale == "shared"):
        return None
    return float(args.size)


def _assign_slug(pr, name, taken):
    """Two cutters of one run never share a directory: the second one gets name-2."""
    base = slugify(name)
    pr.slug, n = base, 2
    while (pr.slug, pr.size_txt) in taken:
        pr.slug, n = f"{base}-{n}", n + 1
    if pr.slug != base:
        pr.warnings.append(Msg("another cutter in this run has the same name; this one is saved as {slug}", slug=pr.slug))
    taken.add((pr.slug, pr.size_txt))


def _dry_run(args, designs, options):
    """Summary and .work/ files only: the dry-run report, optionally the 2D preview."""
    command = build_command()
    results = []
    for pr in designs:
        work = os.path.join(pr.out_dir, WORK_DIR)
        os.makedirs(work, exist_ok=True)
        if args.preview_2d:
            draw_preview(pr, os.path.join(work, DRY_RUN_PREVIEW_FILE))
        pr.files = planned_files(pr, args.preview_2d)
        write_json(os.path.join(work, DRY_RUN_FILE),
                   manifest(pr, "dry-run", options, dict(decision=pr.decision, build_args=build_args())))
        md = summary_md(pr, command)
        results.append(dict(cutter_result(pr), summary_md=md))
        if not args.json:
            print(md + "\n")
    if args.json:
        print(json.dumps(dict(stage="dry-run", cutters=results), ensure_ascii=False, indent=2))


def _build(args, designs, options):
    """Builds every cutter that is not already built with identical settings, then reports."""
    results = []
    for pr in designs:
        if pr.decision == "identical":
            ok, chk, matches = _existing_build(pr)
        else:
            ok, chk, matches = build_into(pr, args, options)
        md = build_report(pr, chk, ok, matches)
        results.append(dict(cutter_result(pr), stl_check=chk, report_md=md))
        if not args.json:
            print(md + "\n")
        if not ok:
            print("WARNING: the model failed the check (it should be a single watertight solid).", file=sys.stderr)
    if args.json:
        print(json.dumps(dict(stage="built", cutters=results), ensure_ascii=False, indent=2))


def _existing_build(pr):
    """The result of the identical build already in pr.out_dir: (check ok, STL check, None)."""
    m = built_manifest(pr.out_dir)
    chk = m.get("stl_check")
    pr.files = [(os.path.join(pr.out_dir, f["path"]), f["role"], "exists") for f in m.get("files", [])]
    return bool(chk and chk.get("ok")), chk, None


def build_into(pr, args, options):
    """Builds one cutter into pr.out_dir; returns (check ok, STL check, matches the last dry run)."""
    d = pr.out_dir
    os.makedirs(d, exist_ok=True)
    manifest_path = os.path.join(d, MANIFEST_FILE)
    if os.path.exists(manifest_path):           # --overwrite: the old manifest goes first, so an
        os.remove(manifest_path)                # interrupted rebuild never looks like a finished one
    t0 = time.time()
    solid = build_solid(pr)
    stl = os.path.join(d, STL_FILE)
    n, V, F = save_stl(solid, stl + ".tmp", pr.shape.name)
    os.replace(stl + ".tmp", stl)
    chk = check_stl(stl)
    ok = chk["watertight"] and chk["winding_consistent"] and chk["bodies"] == 1
    chk = dict(chk, ok=ok, seconds=round(time.time() - t0, 1))
    preview = os.path.join(d, PREVIEW_FILE)
    draw_preview(pr, preview, None if args.no_3d else V, None if args.no_3d else F)
    keep = {r["file"] for _, r in pr.sources}
    for f in os.listdir(d):                     # copies of an earlier template in another format
        if re.fullmatch(r"(source(-\d+)?|imprint-source)\.[A-Za-z0-9]+", f) and f not in keep:
            os.remove(os.path.join(d, f))
    for path, r in pr.sources:
        shutil.copyfile(path, os.path.join(d, r["file"]))
    pr.files = [(stl, "stl", "created"), (preview, "preview", "created")]
    pr.files += [(os.path.join(d, r["file"]), r["role"], "created") for _, r in pr.sources]
    pr.files.append((manifest_path, "manifest", "created"))
    try:
        with open(os.path.join(d, WORK_DIR, DRY_RUN_FILE), encoding="utf-8") as f:
            matches = json.load(f).get("fingerprint") == pr.fingerprint
    except (OSError, ValueError):
        matches = False
    extra = dict(stl_check=chk, matches_dry_run=matches, stl_sha256=sha256_file(stl))
    write_json(manifest_path, manifest(pr, "built", options, extra))
    return ok, chk, matches
