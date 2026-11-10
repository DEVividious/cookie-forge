"""PNG previews: the cutter (top view, cross-section, 3D), the template reading, prepare changes."""
import math
import textwrap

import numpy as np

from ..geometry.design import bed_share
from ..geometry.profile import bevel_height
from ..i18n import mm, num, pct, t, val

LEGEND_DROP = 36    # points from the bottom of the top view to its legend: below the tick and axis labels


def _wrap(text, width):
    """Text wrapped to `width` characters; a "red = cutting edge" pair is never split at the equals sign."""
    return textwrap.fill(text.replace(" = ", "\xa0=\xa0"), width).replace("\xa0", " ")


def draw_preview(pr, path, V=None, F=None):
    """Top view of the cookie with the bed, the wall cross-section and, with a mesh, the 3D model."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with_3d = V is not None and F is not None
    fig = plt.figure(figsize=(16 if with_3d else 12, 7), dpi=110)
    gs = fig.add_gridspec(1, 3 if with_3d else 2, width_ratios=[1.3, 1, 1.1] if with_3d else [1.3, 1])
    top, section = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    _draw_top_view(top, pr)
    _draw_cross_section(section, pr)
    if with_3d:
        _draw_model(fig.add_subplot(gs[2], projection="3d"), V, F)
    # The frames first, the scale after: a drawing with a fixed aspect would shrink inside its frame and
    # take its title and legend along, away from where the layout measured them.
    fig.tight_layout()
    _equal_scale(top)
    _fit_labels(section)
    fig.savefig(path)
    plt.close(fig)


def _draw_top_view(ax, pr):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch, PathPatch, Rectangle
    from matplotlib.path import Path
    from matplotlib.transforms import offset_copy
    from shapely import affinity
    p, k = pr.p, pr.shape
    flange = dict(facecolor="#d9d9d9", edgecolor="#8c8c8c", linewidth=0.8)
    wall = dict(facecolor="#9e9e9e", edgecolor="none")
    cookie = dict(facecolor="#fff3c4", edgecolor="#d62728", linewidth=1.6)
    imprint = dict(facecolor="#1f77b4", edgecolor="#1f77b4", linewidth=0.5)
    bridge = dict(facecolor="#8c8c8c", edgecolor="#555", linewidth=0.6, alpha=0.45, hatch="////")
    bed = dict(linestyle="--", color="#999", linewidth=0.8)
    margin = dict(linestyle=":", color="#bbb", linewidth=0.6)

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
    def view(g):
        return affinity.scale(g, -1, 1, origin=(0, 0)) if p.get("mirror", True) else g

    fl = view(pr.footprint)
    draw_geo(fl, **flange, zorder=1)
    draw_geo(view(k.body.buffer(p["wall"], join_style="round")), **wall, zorder=2)
    draw_geo(view(k.body), **cookie, zorder=3)
    for g in pr.ridges:
        draw_geo(view(g), **imprint, zorder=4)
    for b in pr.beams:
        draw_geo(view(b), **bridge, zorder=5)
    minx, miny, maxx, maxy = fl.bounds
    if pr.bed:
        sx, sy, m = pr.bed[0], pr.bed[1], p["margin"]
        cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
        ax.add_patch(Rectangle((cx - sx / 2, cy - sy / 2), sx, sy, fill=False, zorder=0, **bed))
        ax.add_patch(Rectangle((cx - sx / 2 + m, cy - sy / 2 + m), sx - 2 * m, sy - 2 * m, fill=False, zorder=0, **margin))
        ax.set_xlim(cx - sx / 2 - 5, cx + sx / 2 + 5)
        ax.set_ylim(cy - sy / 2 - 5, cy + sy / 2 + 5)
    else:
        ax.set_xlim(minx - 10, maxx + 10)
        ax.set_ylim(miny - 10, maxy + 10)
    ax.set_xlabel("mm")
    lin, area = bed_share(pr)
    title = _wrap(k.name, 70) + "\n" + t("cookie {w} × {h} mm, with flange {fw} × {fh} mm",
                              w=num(pr.cookie_dims[0]), h=num(pr.cookie_dims[1]),
                              fw=num(pr.footprint_dims[0]), fh=num(pr.footprint_dims[1]))
    if lin is not None:
        title += "\n" + t("{lin} of the longer bed side, {area} of the bed area (bed {x} × {y} mm)",
                          lin=pct(lin), area=pct(area), x=val(pr.bed[0], 0), y=val(pr.bed[1], 0))
    ax.set_title(title, fontsize=10)
    ax.grid(True, linewidth=0.3, alpha=0.5)
    # only what this drawing shows; below the axis label, so that nothing in the plot crosses it
    key = [Line2D([], [], color=cookie["edgecolor"], linewidth=cookie["linewidth"], label=t("cutting edge (cookie view)"))]
    if pr.ridges:
        key.append(Patch(**imprint, label=t("imprint")))
    key += [Patch(**wall, label=t("wall")), Patch(**flange, label=t("flange"))]
    if pr.beams:
        key.append(Patch(**bridge, label=t("bridges (above the dough)")))
    if pr.bed:
        key += [Line2D([], [], **bed, label=t("print bed")), Line2D([], [], **margin, label=t("bed margin"))]
    ax.legend(handles=key, loc="upper center", bbox_to_anchor=(0.5, 0), ncol=3, fontsize=8, frameon=False,
              bbox_transform=offset_copy(ax.transAxes, ax.figure, y=-LEGEND_DROP, units="points"))


def _draw_cross_section(ax, pr):
    """The wall profile with its dimensions. Every label keeps a distance in points from the point it
    describes, so the gaps are the same at every scale; `_fit_labels` then sets the scale and makes room."""
    from matplotlib.patches import Polygon as MplPoly
    from matplotlib.transforms import offset_copy
    p = pr.p
    H, FT, FW, W, B = p["height"], p["flange_thickness"], p["flange"], p["wall"], p["blade"]
    BH = bevel_height(p)

    def label(text, at, dx=0, dy=0, leader_to=None, **kw):
        """Text dx, dy points away from the point `at` (mm), optionally with a leader line to a point."""
        leader = dict(arrowstyle="-", color="#333", linewidth=0.5, shrinkA=2, shrinkB=0, relpos=(0, 0.5))
        return ax.annotate(text, leader_to or at, at, textcoords=offset_copy(ax.transData, ax.figure, dx, dy, units="points"),
                           arrowprops=leader if leader_to else None, in_layout=False, **{"fontsize": 8, **kw})

    ax.add_patch(MplPoly([(0, 0), (FW, 0), (FW, FT), (W, FT), (W, H - BH), (B, H), (0, H)],
                         closed=True, facecolor="#9e9e9e", edgecolor="#333", linewidth=1))
    # one column beside the wall; the wall label halfway between the bevel label and the flange, so
    # that a tall bevel (a short straight wall) does not push it onto the flange
    beside = dict(dx=18, va="center")
    bevel_z = H - BH / 2
    wall_z = (FT + bevel_z) / 2
    label(t("blade {v}", v=val(B)), (W, H), dy=14, leader_to=(B / 2, H), **beside)
    label(t("bevel {a}° ({h} mm)", a=val(p["blade_angle"], 0), h=num(BH)), (W, bevel_z),
          leader_to=((W + B) / 2, bevel_z), **beside)
    label(t("wall {v}", v=val(W)), (W, wall_z), leader_to=(W, min(wall_z, H - BH)), **beside)
    label(t("flange {w} × {h}", w=val(FW, 0), h=val(FT, 0)), (FW, 0), dx=8, dy=5, va="bottom")

    left = -6.0                                 # the dough side, left of the wall
    if pr.ridges:
        hr, w0, w1 = H - p["imprint_drop"], p["imprint_width"], p["imprint_tip"]
        gx = -max(4.0, w0 / 2 + 2)
        left = min(left, gx - w0 / 2 - 1)
        ax.add_patch(MplPoly([(gx - w0 / 2, 0), (gx + w0 / 2, 0), (gx + w1 / 2, hr), (gx - w1 / 2, hr)],
                             closed=True, facecolor="#1f77b4", edgecolor="#1f77b4"))
        label(t("imprint {d} mm lower", d=val(p["imprint_drop"])), (gx, 0), dy=-5, fontsize=7, color="#1f77b4",
              ha="center", va="top")
    ax.plot([left, 0], [H, H], color="#d62728", linewidth=2)
    label(t("dough ←"), (left, H), dy=4, color="#d62728", va="bottom")
    ax.annotate("", (left - 1, 0), (left - 1, H), arrowprops=dict(arrowstyle="<->", linewidth=0.6))
    label(f"{val(H, 0)} mm", (left - 1, H / 2), dx=-4, rotation=90, ha="right", va="center")
    ax.axhline(0, color="#777", linewidth=0.8, linestyle="--")
    # at the right edge of the frame, wherever the limits end up
    ax.annotate(t("print bed (z = 0)"), (1, 0), (-5, -5), xycoords=("axes fraction", "data"), textcoords="offset points",
                ha="right", va="top", fontsize=7, color="#555", in_layout=False)
    ax.set_xlim(left - 2, FW + 1)
    ax.set_ylim(-1, H + 1)
    ax.set_title(t("Wall cross-section (cutter as printed)"), fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])


def _equal_scale(ax):
    """Extend the limits to the shape of the frame, so that 1 mm is as long across as it is up."""
    w, h = ax.bbox.size
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    px_per_mm = min(w / (x1 - x0), h / (y1 - y0))
    dx, dy = (w / px_per_mm - (x1 - x0)) / 2, (h / px_per_mm - (y1 - y0)) / 2
    ax.set_xlim(x0 - dx, x1 + dx)
    ax.set_ylim(y0 - dy, y1 + dy)


def _fit_labels(ax, pad=8, rounds=6):
    """Equal scale with all texts of the drawing `pad` pixels inside the frame. Texts keep their size
    in points, so making room for them makes them larger in mm: repeat until it settles."""
    from matplotlib.transforms import Bbox
    renderer = ax.figure.canvas.get_renderer()
    _equal_scale(ax)
    for _ in range(rounds):
        need = Bbox.union([tx.get_window_extent(renderer) for tx in ax.texts]).padded(pad)
        (x0, y0), (x1, y1) = ax.transData.inverted().transform(need.get_points())
        (xa, xb), (ya, yb) = ax.get_xlim(), ax.get_ylim()
        if xa <= x0 and x1 <= xb and ya <= y0 and y1 <= yb:
            break
        ax.set_xlim(min(xa, x0), max(xb, x1))
        ax.set_ylim(min(ya, y0), max(yb, y1))
        _equal_scale(ax)


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
        # a long file name stays above its own drawing
        ax.set_aspect("equal"); ax.set_title(_wrap(title, 60), fontsize=9); ax.set_xticks([]); ax.set_yticks([])
    for ax in list(axes.flat)[n:]:
        ax.set_axis_off()
    # wrapped to the figure width, so the title is never cut off
    fig.suptitle(_wrap(t("Template reading: red = cutting edge, blue = imprint (view as in the image)"), 60 * cols), fontsize=10)
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
            # no frame: the frame of a narrow shape would cross the text
            ax.set_axis_off()
            ax.text(0.5, 0.5, _wrap(t("rejected: it would merge or split outlines or close a hole"), 28),
                    ha="center", va="center", transform=ax.transAxes, fontsize=10, color="#555555")
        ax.set_xlim(minx - m, maxx + m); ax.set_ylim(miny - m, maxy + m)
        ax.set_aspect("equal"); ax.set_title(title, fontsize=10); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(_wrap(t("{name}: outline simplification - red = cutting edge, grey = template outline", name=name),
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
