# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "trimesh", "matplotlib"]
# ///
"""Render the plugin icon from the reindeer example STL, without changing the mesh.

Run from any directory: uv run /path/to/scripts/render_icon.py
Writes plugins/cookie-forge/.claude-plugin/icon.png and nothing else; --out PATH writes the
picture there instead, to compare before replacing the icon. No display or GPU needed.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh


BACKGROUND = "#fffaf2"


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


def render_icon(root, path):
    """Square directory icon: the reindeer cutter seen from above, legible at small sizes."""
    fig = plt.figure(figsize=(10.24, 10.24), dpi=100, facecolor=BACKGROUND)
    ax = fig.add_axes((0, 0, 1, 1), projection="3d", facecolor=BACKGROUND)
    draw_mesh(ax, trimesh.load_mesh(root / "examples/reindeer/100mm/cutter.stl"), zoom=1.7)
    ax.view_init(elev=89, azim=-90)
    fig.savefig(path, facecolor=BACKGROUND)
    plt.close(fig)
    print(path)


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, metavar="PATH",
                        default=root / "plugins/cookie-forge/.claude-plugin/icon.png",
                        help="write the PNG here instead of the plugin icon")
    render_icon(root, parser.parse_args().out)


if __name__ == "__main__":
    main()
