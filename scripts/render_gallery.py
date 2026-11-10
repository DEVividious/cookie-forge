# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""Render the README gallery: each drawing next to its outline-only and its imprint cutter.

Run from any directory: uv run /path/to/scripts/render_gallery.py
Needs Blender 4.2 or later on PATH (or --blender /path/to/blender); a GPU is used when found.
Writes examples/gallery.webp and nothing else.

Blender renders one studio picture from the example STLs as they are (gallery_scene.py: the
studio, plastic and lights of the cutter that ends examples/showcase.webp). This script frames it
in a dark card with labels, in the look of that clip, so it sits well on light and dark pages.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

# Examples with an outline-only and an imprint build of the same drawing, far row first.
GALLERY = ("easter-bunny", "birthday-cake")
SIZE = "100mm"
LABELS = (("Drawing", "a closed black outline"),
          ("Outline only", "a smooth cookie, ready for icing"),
          ("With imprint", "inner lines pressed into the dough"))

# Pixels at 2x: GitHub shows the card about 840 px wide.
WIDTH = 1680
PAD = 28
CARD_RADIUS, RENDER_RADIUS = 24, 8
GROUND, EDGE, TEXT, MUTED = "#0d0d0d", "#262625", "#f0efec", "#98968f"
LABEL_SIZE, HINT_SIZE = 32, 25
LABEL_TOP, HINT_TOP, BOTTOM = 26, 70, 34   # below the render: label, hint, end of the card
WEBP_QUALITY = 95   # about 130 kB; lower leaves blocks in the soft shading of the floor


def gallery_row(root, name):
    """One drawing and its two cutters, with the box around the ink and the cookie size, so the
    scene can show the drawing at the size of the cookie."""
    outline = root / f"examples/{name}/{SIZE}"
    imprint = root / f"examples/{name}-imprint/{SIZE}"
    with Image.open(outline / "source.png") as im:
        size = im.size
        box = im.convert("L").point(lambda value: 255 if value < 128 else 0).getbbox()
    project = json.loads((outline / "project.json").read_text(encoding="utf-8"))
    return {"drawing": str(outline / "source.png"), "image_size": size, "drawing_box": box,
            "cookie_mm": max(project["result"]["cookie_mm"]),
            "outline_stl": str(outline / "cutter.stl"), "imprint_stl": str(imprint / "cutter.stl")}


def render_scene(root, work, blender, samples):
    job = {"rows": [gallery_row(root, name) for name in GALLERY],
           "width": WIDTH - 2 * PAD, "samples": samples,
           "render": str(work / "render.png"), "anchors": str(work / "anchors.json")}
    job_path = work / "job.json"
    job_path.write_text(json.dumps(job), encoding="utf-8")
    Path(job["anchors"]).unlink(missing_ok=True)
    scene = Path(__file__).with_name("gallery_scene.py")
    done = subprocess.run([blender, "-b", "--factory-startup", "-P", str(scene), "--",
                           str(job_path)], capture_output=True, text=True)
    if done.returncode or not Path(job["anchors"]).exists():
        raise SystemExit(f"Blender failed:\n{done.stdout[-2000:]}\n{done.stderr[-2000:]}")


def rounded(size, radius, box=None):
    """Antialiased rounded-rectangle mask."""
    scale = 4
    mask = Image.new("L", (size[0] * scale, size[1] * scale), 0)
    x0, y0, x1, y1 = box or (0, 0, *size)
    ImageDraw.Draw(mask).rounded_rectangle(
        (x0 * scale, y0 * scale, x1 * scale - 1, y1 * scale - 1), radius * scale, fill=255)
    return mask.resize(size, Image.LANCZOS)


def compose(work):
    """The render in a dark rounded card, a label and a hint under each column."""
    fonts = Path(__file__).with_name("fonts")
    label_font = ImageFont.truetype(str(fonts / "overpass-latin-800-normal.woff2"), LABEL_SIZE)
    hint_font = ImageFont.truetype(str(fonts / "overpass-latin-400-normal.woff2"), HINT_SIZE)
    render = Image.open(work / "render.png").convert("RGB")
    anchors = json.loads((work / "anchors.json").read_text(encoding="utf-8"))

    below = PAD + render.height
    height = below + HINT_TOP + HINT_SIZE + BOTTOM
    card = Image.new("RGB", (WIDTH, height), EDGE)
    card.paste(GROUND, mask=rounded(card.size, CARD_RADIUS - 2, (2, 2, WIDTH - 2, height - 2)))
    card.paste(render, (PAD, PAD), rounded(render.size, RENDER_RADIUS))
    draw = ImageDraw.Draw(card)
    for anchor, (label, hint) in zip(anchors, LABELS):
        x = PAD + anchor * render.width
        draw.text((x, below + LABEL_TOP), label, font=label_font, fill=TEXT, anchor="ma")
        draw.text((x, below + HINT_TOP), hint, font=hint_font, fill=MUTED, anchor="ma")
    card.putalpha(rounded(card.size, CARD_RADIUS))
    return card


def save_webp(card, path):
    """Lossy WebP from the full-color card, with the rounded corners in a lossless alpha plane."""
    card.save(path, "WEBP", quality=WEBP_QUALITY, alpha_quality=100, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--blender", default="blender", help="Blender executable")
    parser.add_argument("--samples", type=int, default=384, help="Cycles samples per pixel")
    parser.add_argument("--work", type=Path,
                        help="keep the raw render here; with --compose-only, reuse it")
    parser.add_argument("--compose-only", action="store_true",
                        help="skip Blender and redo only the card from --work")
    parser.add_argument("--out", type=Path, help="write the card here instead of examples/")
    args = parser.parse_args()
    if args.compose_only and not args.work:
        parser.error("--compose-only needs --work")
    root = Path(__file__).resolve().parents[1]
    path = args.out or root / "examples/gallery.webp"
    with tempfile.TemporaryDirectory() as temporary:
        work = (args.work or Path(temporary)).resolve()
        work.mkdir(parents=True, exist_ok=True)
        if not args.compose_only:
            render_scene(root, work, args.blender, args.samples)
        save_webp(compose(work), path)
    print(path)


if __name__ == "__main__":
    main()
