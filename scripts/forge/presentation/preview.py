"""PNG previews: the cutter (top view, cross-section, 3D), the template reading, prepare changes."""
import math
import textwrap

import numpy as np

from ..geometry.design import bed_share
from ..geometry.profile import bevel_height
from ..i18n import mm, num, pct, t, val


def draw_preview(pr, path, V=None, F=None):
    """Top view of the cookie with the bed, the wall cross-section and, with a mesh, the 3D model."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with_3d = V is not None and F is not None
    fig = plt.figure(figsize=(16 if with_3d else 12, 6.5), dpi=110)
    gs = fig.add_gridspec(1, 3 if with_3d else 2, width_ratios=[1.3, 1, 1.1] if with_3d else [1.3, 1])
    _draw_top_view(fig.add_subplot(gs[0]), pr)
    _draw_cross_section(fig.add_subplot(gs[1]), pr)
    if with_3d:
        _draw_model(fig.add_subplot(gs[2], projection="3d"), V, F)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _draw_top_view(ax, pr):
    from matplotlib.patches import Rectangle
    p, k = pr.p, pr.shape
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch

    def draw_geo(g, **kw):
        for poly in getattr(g, "geoms", [g]):
            if poly.geom_type != "Polygon" or poly.is_empty:
                continue
            verts, codes = [], []
            for ring in [poly.exterior] + list(poly.interiors):
                pts = np.asarray(ring.coords)
                verts.append(pts)
                codes.append([Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY])
            ax.add_patch(PathPatch(Path(np.vstack(verts), np.concatenate(codes)), **kw))

    # the preview shows the cookie as it comes out of the cutter (mirrored model)
    from shapely import affinity
    def view(g):
        return affinity.scale(g, -1, 1, origin=(0, 0)) if p.get("mirror", True) else g

    fl = view(pr.footprint)
    body = view(k.body)
    wall = view(k.body.buffer(p["wall"], join_style="round"))
    draw_geo(fl, facecolor="#d9d9d9", edgecolor="#8c8c8c", linewidth=0.8, zorder=1)
    draw_geo(wall, facecolor="#9e9e9e", edgecolor="none", zorder=2)
    draw_geo(body, facecolor="#fff3c4", edgecolor="#d62728", linewidth=1.6, zorder=3)
    for g in pr.ridges:
        draw_geo(view(g), facecolor="#1f77b4", edgecolor="#1f77b4", linewidth=0.5, zorder=4)
    for b in pr.beams:
        draw_geo(view(b), facecolor="#8c8c8c", edgecolor="#555", linewidth=0.6, alpha=0.45, hatch="////", zorder=5)
    minx, miny, maxx, maxy = fl.bounds
    if pr.bed:
        sx, sy = pr.bed[0], pr.bed[1]
        cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
        ax.add_patch(Rectangle((cx - sx / 2, cy - sy / 2), sx, sy, fill=False, linestyle="--", edgecolor="#999", linewidth=0.8, zorder=0))
        ax.add_patch(Rectangle((cx - sx / 2 + p["margin"], cy - sy / 2 + p["margin"]), sx - 2 * p["margin"], sy - 2 * p["margin"],
                               fill=False, linestyle=":", edgecolor="#bbb", linewidth=0.6, zorder=0))
        ax.set_xlim(cx - sx / 2 - 5, cx + sx / 2 + 5)
        ax.set_ylim(cy - sy / 2 - 5, cy + sy / 2 + 5)
    else:
        ax.set_xlim(minx - 10, maxx + 10)
        ax.set_ylim(miny - 10, maxy + 10)
    ax.set_aspect("equal")
    ax.set_xlabel("mm")
    lin, area = bed_share(pr)
    title = k.name + "\n" + t("cookie {w} × {h} mm, with flange {fw} × {fh} mm",
                              w=num(pr.cookie_dims[0]), h=num(pr.cookie_dims[1]),
                              fw=num(pr.footprint_dims[0]), fh=num(pr.footprint_dims[1]))
    if lin is not None:
        title += "\n" + t("{lin} of the longer bed side, {area} of the bed area (bed {x} × {y} mm)",
                          lin=pct(lin), area=pct(area), x=val(pr.bed[0], 0), y=val(pr.bed[1], 0))
    ax.set_title(title, fontsize=10)
    ax.grid(True, linewidth=0.3, alpha=0.5)
    ax.text(0.01, 0.01, textwrap.fill(t("red line = cutting edge (cookie view)   blue = imprint   grey = wall / flange   hatched = bridges (above the dough)"), 75),
            transform=ax.transAxes, fontsize=7, color="#444")


def _draw_cross_section(ax, pr):
    from matplotlib.patches import Polygon as MplPoly
    p = pr.p
    H, FT, FW, W, B = p["height"], p["flange_thickness"], p["flange"], p["wall"], p["blade"]
    BH = bevel_height(p)
    prof = [(0, 0), (FW, 0), (FW, FT), (W, FT), (W, H - BH), (B, H), (0, H)]
    ax.add_patch(MplPoly(prof, closed=True, facecolor="#9e9e9e", edgecolor="#333", linewidth=1))
    ax.plot([-6, 0], [H, H], color="#d62728", linewidth=2)   # dough on the left
    ax.text(-5.8, H + 0.4, t("dough ←"), color="#d62728", fontsize=8)
    if pr.ridges:
        hr = H - p["imprint_drop"]
        gx = -4.0
        ax.add_patch(MplPoly([(gx - p["imprint_width"] / 2, 0), (gx + p["imprint_width"] / 2, 0), (gx + p["imprint_tip"] / 2, hr), (gx - p["imprint_tip"] / 2, hr)],
                              closed=True, facecolor="#1f77b4", edgecolor="#1f77b4"))
        ax.annotate(t("imprint {d} mm lower", d=val(p["imprint_drop"])), (gx, hr), (gx - 1.5, hr - 2.2), fontsize=7, color="#1f77b4")
    ax.annotate("", (W, H - BH), (B, H), arrowprops=dict(arrowstyle="-", color="#000", linewidth=0.5))
    ax.text(W + 0.3, H - BH / 2, t("bevel {a}°\n({h} mm)", a=val(p["blade_angle"], 0), h=num(BH)), fontsize=8, va="center")
    ax.text(B + 0.2, H + 0.4, t("blade {v}", v=val(B)), fontsize=8)
    ax.text(W + 0.3, (FT + H - BH) / 2 - 2.5, t("wall {v}", v=val(W)), fontsize=8)
    ax.text(FW / 2, FT + 0.3, t("flange {w} × {h}", w=val(FW, 0), h=val(FT, 0)), fontsize=8, ha="center")
    ax.annotate("", (-7, 0), (-7, H), arrowprops=dict(arrowstyle="<->", linewidth=0.6))
    ax.text(-7.3, H / 2, f"{val(H, 0)} mm", rotation=90, va="center", ha="right", fontsize=8)
    ax.axhline(0, color="#777", linewidth=0.8, linestyle="--")
    ax.text(FW + 0.5, -1.2, t("print bed (z = 0)"), fontsize=7, color="#555")
    ax.set_xlim(-9, FW + 4)
    ax.set_ylim(-2.5, H + 3)
    ax.set_aspect("equal")
    ax.set_title(t("Wall cross-section (cutter as printed)"), fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])


def _draw_model(ax, V, F):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    Fv = F
    if len(F) > 250000:                      # a random subset leaves holes; only for huge meshes
        idx = np.random.default_rng(0).choice(len(F), 250000, replace=False)
        Fv = F[idx]
    tri = V[Fv]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    light = np.array([0.4, -0.5, 0.75]); light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
    colors = np.stack([shade * 0.95, shade * 0.55, shade * 0.25, np.ones_like(shade)], axis=1)
    pc = Poly3DCollection(tri, facecolors=colors, edgecolors="none")
    ax.add_collection3d(pc)
    mn, mx = V.min(axis=0), V.max(axis=0)
    c = (mn + mx) / 2
    r = (mx - mn).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(0, 2 * r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=35, azim=-60)
    ax.set_axis_off()
    ax.set_title(t("STL model (as on the bed)"), fontsize=10)


def draw_detection(sources_shapes, path, show_imprint=True):
    """Preview after analysis: what was read from each source."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPoly
    n = len(sources_shapes)
    cols = min(n, 3)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows), dpi=100, squeeze=False, layout="constrained")
    for ax, (title, k) in zip(axes.flat, sources_shapes):
        for poly in getattr(k.body, "geoms", [k.body]):
            ax.add_patch(MplPoly(np.asarray(poly.exterior.coords), closed=True, facecolor="#fff3c4", edgecolor="#d62728", linewidth=1.5))
            for r in poly.interiors:
                ax.add_patch(MplPoly(np.asarray(r.coords), closed=True, facecolor="white", edgecolor="#d62728", linewidth=1.5))
        # largest first, so small details inside an enclosed line (dots on an egg) stay visible
        imprints = sorted(k.imprints, key=lambda o: -(o[1] if isinstance(o, tuple) else o).area) if show_imprint else []
        for o in imprints:
            g = o[1] if isinstance(o, tuple) else o
            for poly in getattr(g, "geoms", [g]):
                if poly.geom_type != "Polygon":
                    continue
                ax.add_patch(MplPoly(np.asarray(poly.exterior.coords), closed=True, facecolor="#1f77b4" if not isinstance(o, tuple) else "none",
                                     edgecolor="#1f77b4", linewidth=1.2))
                for r in poly.interiors:            # white areas enclosed by a line (e.g. an egg)
                    ax.add_patch(MplPoly(np.asarray(r.coords), closed=True, facecolor="#fff3c4", edgecolor="#1f77b4", linewidth=1.2))
        minx, miny, maxx, maxy = k.body.bounds
        m = 0.05 * max(maxx - minx, maxy - miny)
        ax.set_xlim(minx - m, maxx + m); ax.set_ylim(miny - m, maxy + m)
        ax.set_aspect("equal"); ax.set_title(title, fontsize=9); ax.set_xticks([]); ax.set_yticks([])
    for ax in list(axes.flat)[n:]:
        ax.set_axis_off()
    # wrapped to the figure width, so the title is never cut off
    fig.suptitle(textwrap.fill(t("Template reading: red = cutting edge, blue = imprint (view as in the image)"), 60 * cols), fontsize=10)
    fig.savefig(path)
    plt.close(fig)


def draw_simplify(name, variants, path):
    """Preview of `simplify`: the current outline and every level side by side, over the template
    outline in grey, with the numbers that matter for choosing."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPoly
    from ..config import LEVEL_NAMES
    fig, axes = plt.subplots(1, len(variants), figsize=(4.6 * len(variants), 5.6), dpi=100, squeeze=False,
                             layout="constrained")
    ref = next(v for v in variants if v["ok"])
    minx, miny, maxx, maxy = ref["raw"].bounds
    m = 0.05 * max(maxx - minx, maxy - miny)
    for ax, v in zip(axes.flat, variants):
        title = t(LEVEL_NAMES[v["level"]])
        if v["ok"]:
            for poly in getattr(v["body"], "geoms", [v["body"]]):
                ax.add_patch(MplPoly(np.asarray(poly.exterior.coords), closed=True, facecolor="#fff3c4", edgecolor="#d62728", linewidth=1.5, zorder=1))
                for r in poly.interiors:
                    ax.add_patch(MplPoly(np.asarray(r.coords), closed=True, facecolor="white", edgecolor="#d62728", linewidth=1.5, zorder=1))
            for poly in getattr(v["raw"], "geoms", [v["raw"]]):
                for ring in [poly.exterior, *poly.interiors]:
                    x, y = ring.xy
                    ax.plot(x, y, color="#555555", linewidth=0.6, alpha=0.8, zorder=2)
            title += "\n" + t("deviation: mean {mean}, max {max}", mean=mm(v["mean"], 2), max=mm(v["max"], 1))
            title += "\n" + t("narrowest notch {gap} · {tri} triangles",
                               gap=mm(v["gap"], 1) if v["gap"] else "-", tri=num(v["triangles"], 0))
        else:
            ax.text(0.5, 0.5, textwrap.fill(t("rejected: it would merge or split outlines or close a hole"), 28),
                    ha="center", va="center", transform=ax.transAxes, fontsize=10, color="#555555")
        ax.set_xlim(minx - m, maxx + m); ax.set_ylim(miny - m, maxy + m)
        ax.set_aspect("equal"); ax.set_title(title, fontsize=10); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(textwrap.fill(t("{name}: outline simplification - red = cutting edge, grey = template outline", name=name),
                               55 * len(variants)), fontsize=11)
    fig.savefig(path)
    plt.close(fig)


def draw_prepare(gray, cut, path):
    """Preview of `prepare`: the template in grey with the cleared pixels in red, enlarged."""
    import cv2
    rgb = np.stack([gray] * 3, axis=-1).astype(np.uint8)
    marks = cv2.dilate(cut.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    rgb[marks] = (214, 39, 40)
    from PIL import Image
    Image.fromarray(rgb).save(path)
