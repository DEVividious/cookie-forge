"""Cookie cutter generator: image (PNG/JPG/PDF) -> STL (dimensions in mm).

Usage:
  uv run cookie_forge.py analyze  SOURCES... [--bed 220x220] [--split] [--preview file.png]
  uv run cookie_forge.py build    SOURCES... --size 80 [--bed 220x220] [--name cat] [--dry-run] ...
  uv run cookie_forge.py simplify SOURCES... --size 80 --name cat   (outline simplification variants)
  uv run cookie_forge.py build --from .work/cat/80mm --simplify-level medium   (change an existing project)
  uv run cookie_forge.py printers [phrase]
  uv run cookie_forge.py prepare SOURCE --name cat [--size 80] [--gap 1.0]
  uv run cookie_forge.py paths --name cat
Output language: --lang en (default) or --lang pl.

Results go below ROOT (--output-dir, default: the current directory, i.e. the user's project):
generated/<date>/<cutter>-<size>mm.stl for every STL that passed the check, and .work/<cutter>/
for the working files (template versions, reading preview, <size>mm/ with preview.png,
source.<ext>, project.json and the dry-run files). A dry run writes only the dry-run files. An
existing build is never replaced silently: identical settings -> nothing is rebuilt, different
settings -> a new version <size>mm-v2 (<cutter>-<size>mm-v2.stl), --overwrite / --new-version on
explicit request.

A SOURCE is a PNG/JPG/BMP/WEBP/PDF file. Black (dark) pixels are the shape, white is background.
In "merge" mode a source may carry a placement: file.png@dx,dy[,size_mm[,rotation_deg]].

Cutter profile (the flange lies on the print bed, the cutting edge is on top; flip it to use):
  z = 0 .. FLANGE_THICKNESS      flange FLANGE wide (grip + stiffening)
  z = .. HEIGHT - BEVEL_HEIGHT   wall WALL thick
  z = .. HEIGHT                  taper to BLADE at BLADE_ANGLE (outer bevel, vertical inside,
                                 so the sides of the cookie are straight)
With --imprint auto the lines inside the template become the imprint: a ridge IMPRINT_DROP lower
than the cutting edge that only presses the pattern into the dough. Every loose part (imprint,
hole wall, separate shape) is joined by bridges at flange level, so the print is a single solid."""
import argparse
import sys

from . import i18n
from .commands.analyze import cmd_analyze
from .commands.build import cmd_build
from .commands.paths import cmd_paths
from .commands.prepare import cmd_prepare
from .commands.printers import cmd_printers
from .commands.simplify import cmd_simplify
from .config import DEFAULTS, IMPRINT_DEPTH
from .errors import ForgeError, fail
from .project.reuse import expand_from


def main():
    try:
        argv = sys.argv[1:]
        if "--from" in argv and argv and argv[0] in ("analyze", "build", "simplify"):
            # the expanded arguments are what this run does, so the build command shows them all
            argv = expand_from(argv, build_parser())
            sys.argv[1:] = argv
    except ForgeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    args = build_parser().parse_args(argv)
    i18n.set_language(args.lang)
    try:
        check_args(args)
        args.fn(args)
    except ForgeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="read the template(s) and propose sizes")
    add_source_options(a)
    a.add_argument("--preview", help="PNG with the shape as read; default .work/<name>/reading.png")
    a.set_defaults(fn=cmd_analyze)

    b = sub.add_parser("build", help="build the STL (or only the summary with --dry-run)")
    add_source_options(b)
    b.add_argument("--dry-run", action="store_true", help="only the project summary and dry-run files, no STL")
    b.add_argument("--preview-2d", action="store_true", help="with --dry-run also save dry-run-preview.png")
    b.add_argument("--no-3d", action="store_true", help="skip the 3D view in the preview (faster)")
    b.add_argument("--overwrite", action="store_true", help="rebuild in place: replace the identical or latest build of this size")
    b.add_argument("--new-version", action="store_true", help="always write a new version directory (<size>mm-vN)")
    b.add_argument("--json", action="store_true", help="print a machine-readable result (with the summary/report text)")
    b.set_defaults(fn=cmd_build)

    sm = sub.add_parser("simplify", help="outline simplification variants side by side, and whether the outline is complex")
    add_source_options(sm)
    sm.set_defaults(fn=cmd_simplify)

    pr = sub.add_parser("prepare", help="new template version with inner lines detached from the outline (for an imprint)")
    pr.add_argument("source", metavar="SOURCE", help="PNG/JPG/one-page PDF")
    pr.add_argument("--name", help="cutter name (its directory is a safe slug of it)")
    pr.add_argument("--output-dir", "--out-dir", dest="output_dir", default=".")
    pr.add_argument("--size", help="cookie size in mm (longest side) the gap is measured at, or 'original'; default 100")
    pr.add_argument("--gap", type=float, default=1.0, help="gap between the inner lines and the outline in mm; default 1.0")
    pr.add_argument("--threshold", default="auto", help="black threshold 0-255 or auto (Otsu)")
    pr.add_argument("--invert", action="store_true", help="invert: light = shape")
    pr.add_argument("--dpi", type=int, default=200, help="PDF rendering resolution")
    add_lang(pr)
    pr.set_defaults(fn=cmd_prepare)

    pa = sub.add_parser("paths", help="print where the files of a cutter go (JSON)")
    pa.add_argument("--name", required=True)
    pa.add_argument("--output-dir", "--out-dir", dest="output_dir", default=".")
    pa.add_argument("--ext", default="png", help="extension of the next template version")
    pa.set_defaults(fn=cmd_paths, lang="en")

    d = sub.add_parser("printers", help="look up a printer and its bed size")
    d.add_argument("phrase", nargs="*")
    add_lang(d)
    d.set_defaults(fn=cmd_printers)
    return ap


def add_lang(s):
    s.add_argument("--lang", choices=["en", "pl"], default="en",
                   help="language of the output (summary, tables, previews); default en")


def add_source_options(s):
    """Options shared by analyze and build: sources, scale, reading, imprint, parameters."""
    s.add_argument("sources", nargs="+", metavar="SOURCE", help="PNG/JPG/PDF; in merge mode: file@dx,dy[,size[,rotation]]")
    s.add_argument("--bed", help="WIDTHxDEPTH[xHEIGHT] in mm or a printer name, e.g. 220x220 or 'K1C'")
    s.add_argument("--size", help="longest side of the cookie in mm (e.g. 80) or 'original' (size from PDF/DPI)")
    s.add_argument("--mode", choices=["auto", "separate", "merge"], default="auto",
                   help="separate: every source is a separate cutter; merge: sources combined into one shape")
    s.add_argument("--split", action="store_true", help="every separate shape in an image/page is a separate cutter")
    s.add_argument("--scale", choices=["shared", "separate"], default="shared",
                   help="with --split: shared scale (largest shape = --size) or every shape = --size")
    s.add_argument("--name", help="cutter name (its directory is a safe slug of it)")
    s.add_argument("--output-dir", "--out-dir", dest="output_dir", default=".",
                   help="where generated/ (ready STL files) and .work/ (working files) go; default: the current directory")
    s.add_argument("--names", help="comma-separated names of consecutive cutters")
    s.add_argument("--threshold", default="auto", help="black threshold 0-255 or auto (Otsu)")
    s.add_argument("--invert", action="store_true", help="invert: light = shape")
    s.add_argument("--dpi", type=int, default=200, help="PDF rendering resolution")
    s.add_argument("--holes", choices=["imprint", "cut", "ignore"], default="imprint",
                   help="what to do with white holes inside a black silhouette")
    s.add_argument("--imprint", choices=["auto", "none"], default="none",
                   help="auto: inner lines of the template become an imprint; default none: outline only")
    s.add_argument("--dough", type=float, metavar="MM",
                   help=f"dough thickness; the imprint ridge is set to press {IMPRINT_DEPTH} mm deep (instead of --imprint-drop)")
    s.add_argument("--imprint-seams", action="store_true", help="in merge mode: imprint the seams between merged shapes")
    s.add_argument("--imprint-from", metavar="FILE", help="separate image with imprint lines (black lines), fitted into the cookie outline")
    s.add_argument("--rotate", type=float, default=0.0, help="rotate the shape, in degrees")
    s.add_argument("--no-mirror", action="store_true", help="do not mirror the model (the cookie comes out mirrored)")
    s.add_argument("--no-bridges", action="store_true")
    s.add_argument("--simplify-level", choices=["none", "light", "medium", "strong"], default="none",
                   help="simplify the outline: even out small wiggles and round narrow notches and tips "
                        "(scaled to the cookie size); default none")
    s.add_argument("--from", dest="from_project", metavar="DIR",
                   help="use the template and settings of an existing project (e.g. .work/cat/80mm); "
                        "options given here change them")
    for key, v in DEFAULTS.items():
        s.add_argument("--" + key.replace("_", "-"), type=float, default=None, help=f"default {v}")
    add_lang(s)


def check_args(args):
    """Checks across options that argparse cannot express."""
    if getattr(args, "overwrite", False) and args.new_version:
        fail("use either --overwrite or --new-version")
    if args.cmd in ("analyze", "build", "simplify", "prepare") and args.size not in (None, "original"):
        try:
            float(args.size)
        except ValueError:
            fail("--size is a number in mm or 'original'")
