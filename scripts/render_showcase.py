# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "trimesh", "matplotlib", "pillow"]
# ///
"""Render the README animation and gallery from the actual example STLs, without changing a mesh.

Run from any directory: uv run /path/to/scripts/render_showcase.py
Writes examples/showcase.gif, examples/showcase.png and examples/gallery-<example>.png.
No display or GPU needed.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from PIL import Image
import trimesh


BACKGROUND = "#fffaf2"
# Examples with an outline-only and an imprint build of the same template, for the README gallery.
GALLERY = ("easter-bunny", "birthday-cake")


def draw_mesh(ax, mesh, zoom=1):
    """Shade the mesh with one fixed light; the axes keep millimeters equal on all three axes."""
    vertices = mesh.vertices - mesh.bounds.mean(axis=0)
    light = np.array([.4, -.5, .75])
    light /= np.linalg.norm(light)
    shade = .58 + .42 * np.maximum(0, mesh.face_normals @ light)
    colors = np.column_stack((shade*.20, shade*.66, shade*.57, np.ones(len(shade))))
    ax.add_collection3d(Poly3DCollection(vertices[mesh.faces], facecolors=colors,
                                       edgecolors="none", linewidths=0))
    radius = max(mesh.extents[:2]) * .60
    ax.set(xlim=(-radius, radius), ylim=(-radius, radius), zlim=(-radius*.32, radius*.32))
    ax.set_box_aspect((1, 1, .64), zoom=zoom)
    ax.set_axis_off()


def render_gallery(root, name):
    """Template, outline-only STL and imprint STL of one example side by side."""
    fig = plt.figure(figsize=(12, 4.4), dpi=100, facecolor=BACKGROUND)
    source = fig.add_axes((.025, .06, .27, .74))
    with Image.open(root / f"examples/{name}/100mm/source.png") as im:
        source.imshow(im.copy())
    source.axis("off")
    panels = [(source, "TEMPLATE")]
    for left, variant, label in ((.31, name, "OUTLINE-ONLY STL"),
                                 (.655, f"{name}-imprint", "STL WITH IMPRINT")):
        ax = fig.add_axes((left, .0, .34, .86), projection="3d", facecolor=BACKGROUND)
        draw_mesh(ax, trimesh.load_mesh(root / f"examples/{variant}/100mm/cutter.stl"), zoom=1.35)
        # Seen from the template's bottom edge, so the shape stands upright like the template.
        ax.view_init(elev=65, azim=-90)
        panels.append((ax, label))
    for ax, label in panels:
        box = ax.get_position()
        fig.text(box.x0 + box.width/2, .89, label, ha="center", fontsize=20,
                 weight="bold", color="#5b706a")
    path = root / f"examples/gallery-{name}.png"
    fig.savefig(path, facecolor=BACKGROUND)
    plt.close(fig)
    print(path)


def main():
    root = Path(__file__).resolve().parents[1]
    example = root / "examples/reindeer/100mm"
    mesh = trimesh.load_mesh(example / "cutter.stl")
    fig = plt.figure(figsize=(8, 4.5), dpi=100, facecolor=BACKGROUND)
    fig.text(.06, .91, "A picture. A cutter. Your next batch.", fontsize=20,
             weight="bold", color="#293b39")
    fig.text(.06, .84, "cookie-forge  /  Image to STL", fontsize=11, color="#5b706a")
    source = fig.add_axes((.06, .20, .27, .57))
    with Image.open(example / "source.png") as im:
        source.imshow(im.copy())
    source.axis("off")
    source.set_title("YOUR TEMPLATE", fontsize=9, color="#5b706a", pad=12)
    ax = fig.add_axes((.36, .14, .61, .66), projection="3d", facecolor=BACKGROUND)
    draw_mesh(ax, mesh)
    fig.text(.52, .14, "100 mm  /  reindeer outline", fontsize=11, color="#293b39")
    fig.text(.06, .055, "Real STL geometry. Preview it, approve it, print it.",
             fontsize=11, color="#5b706a")
    frames = []
    # A gentle orbit keeps the outline recognizable; the final-to-first transition is continuous.
    for index in range(32):
        phase = 2*np.pi*index/32
        ax.view_init(elev=48+8*np.sin(phase), azim=-60+30*np.cos(phase))
        fig.canvas.draw()
        frame = Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert("RGB")
        if index == 0:
            frame.save(root / "examples/showcase.png")
        frames.append(frame)
    frames[0].save(root / "examples/showcase.gif", save_all=True, append_images=frames[1:],
                   duration=100, loop=0, optimize=True)
    plt.close(fig)
    print(root / "examples/showcase.gif")
    for name in GALLERY:
        render_gallery(root, name)


if __name__ == "__main__":
    main()
