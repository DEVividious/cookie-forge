"""Layout check of the cutter preview, run by test_preview.py with the interpreter of the script's
environment (it needs matplotlib): `python preview_layout.py SCRIPTS_DIR OUT_DIR COMMANDS_JSON`.

Every command line in COMMANDS_JSON runs in-process. Each figure is examined just before it is
saved, and one line is printed per problem: a text of the cross-section on top of another text or
of a drawn shape or outside its frame, a legend on the plot, anything outside the figure."""
import contextlib
import io
import itertools
import json
import os
import sys

scripts, out, commands = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
sys.path.insert(0, scripts)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.text import Text  # noqa: E402
from shapely.geometry import LineString, Polygon, box  # noqa: E402

from forge.cli import main  # noqa: E402

GAP = 2     # pixels that must stay free around a text
problems = []


def text_box(text, renderer):
    """The text alone: the extent of an annotation would include its leader line."""
    return box(*Text.get_window_extent(text, renderer).extents)


def drawn_shapes(ax):
    for patch in ax.patches:
        if patch.get_fill():
            yield Polygon(patch.get_transform().transform(patch.get_path().vertices)).buffer(0)
    for line in ax.lines:
        yield LineString(line.get_transform().transform(line.get_xydata()))


def check(fig):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    figure = box(0, 0, *fig.bbox.size)
    titles = []
    for ax in fig.axes:
        frame = box(*ax.get_window_extent(r).extents)
        outside = [(a.get_text(), text_box(a, r)) for a in (ax.title, ax.xaxis.label) if a.get_text()]
        titles.append(outside[0])
        legend = ax.get_legend()
        if legend is not None:
            key = box(*legend.get_window_extent(r).extents)
            outside.append(("legend", key))
            if key.intersects(frame) or any(key.intersects(b) for _, b in outside[:-1]):
                problems.append("the legend covers the plot or its labels")
        for name, b in outside:
            if not figure.contains(b):
                problems.append(f"{name!r} leaves the figure")
    section = fig.axes[1]
    frame = box(*section.get_window_extent(r).extents)
    labels = [(tx.get_text(), text_box(tx, r)) for tx in section.texts if tx.get_text()]
    for name, b in labels:
        if not frame.contains(b.buffer(GAP)):
            problems.append(f"{name!r} leaves the frame")
        if any(shape.intersects(b.buffer(GAP)) for shape in drawn_shapes(section)):
            problems.append(f"{name!r} is on top of the drawing")
    for (n1, b1), (n2, b2) in itertools.chain(itertools.combinations(labels, 2), itertools.combinations(titles, 2)):
        if b1.buffer(GAP).intersects(b2):
            problems.append(f"{n1!r} overlaps {n2!r}")


def checked_savefig(fig, *args, **kw):
    check(fig)
    return savefig(fig, *args, **kw)


savefig, Figure.savefig = Figure.savefig, checked_savefig
for i, argv in enumerate(commands):
    sys.argv = ["cookie_forge.py", *argv, "--output-dir", os.path.join(out, str(i))]
    with contextlib.redirect_stdout(io.StringIO()):     # the command's own report is not of interest here
        main()
    case = " ".join(a for a in argv if not os.path.isabs(a))
    for problem in problems:
        print(f"{case}: {problem}")
    problems.clear()
