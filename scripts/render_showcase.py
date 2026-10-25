# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "trimesh", "matplotlib", "pillow"]
# ///
"""Render the README animation from the actual example STL, without changing the mesh.

Run from any directory: uv run /path/to/scripts/render_showcase.py
Writes examples/showcase.gif and examples/showcase.png. No display or GPU needed.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from PIL import Image
import trimesh


def main():
    root = Path(__file__).resolve().parents[1]
    example = root / "examples/reindeer/100mm"
    mesh = trimesh.load_mesh(example / "cutter.stl")
    vertices = mesh.vertices - mesh.bounds.mean(axis=0)
    fig = plt.figure(figsize=(8, 4.5), dpi=100, facecolor="#fffaf2")
    fig.text(.06, .91, "A picture. A cutter. Your next batch.", fontsize=20,
             weight="bold", color="#293b39")
    fig.text(.06, .84, "cookie-forge  /  Image to STL", fontsize=11, color="#5b706a")
    source = fig.add_axes((.06, .20, .27, .57))
    with Image.open(example / "source.png") as im:
        source.imshow(im.copy())
    source.axis("off")
    source.set_title("YOUR TEMPLATE", fontsize=9, color="#5b706a", pad=12)
    ax = fig.add_axes((.36, .14, .61, .66), projection="3d", facecolor="#fffaf2")
    light = np.array([.4, -.5, .75])
    light /= np.linalg.norm(light)
    shade = .58 + .42 * np.maximum(0, mesh.face_normals @ light)
    colors = np.column_stack((shade*.20, shade*.66, shade*.57, np.ones(len(shade))))
    ax.add_collection3d(Poly3DCollection(vertices[mesh.faces], facecolors=colors,
                                       edgecolors="none", linewidths=0))
    radius = max(mesh.extents[:2]) * .60
    ax.set(xlim=(-radius, radius), ylim=(-radius, radius), zlim=(-radius*.32, radius*.32))
    ax.set_box_aspect((1, 1, .64))
    ax.set_axis_off()
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


if __name__ == "__main__":
    main()
