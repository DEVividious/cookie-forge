"""One look for every preview, shared with the README's studio render: orange plastic, a warm floor,
quiet ink. Colours are sRGB hex (matplotlib) or RGB tuples (the 3D renderer)."""

PAPER = "#f1ece4"          # the figure: a warm light card, calm on dark and light screens
PANEL = "#f8f5f0"          # a drawing's own area
INK = "#2d2925"            # titles
TEXT = "#4a443e"           # labels
MUTED = "#8a8279"          # ticks, notes
RULE = "#ddd5ca"           # grid, frames
BED = "#a59d93"            # print bed outline

PLASTIC = "#d9682c"        # the cutter: wall and profile
PLASTIC_EDGE = "#9c4519"
FLANGE = "#efc09d"
FLANGE_EDGE = "#c98a5f"
DOUGH = "#f6e5c4"          # the cookie
CUT = "#c3222f"            # red = cutting edge
IMPRINT = "#2c68ad"        # blue = imprint
BRIDGE = "#8f857a"

PLASTIC_RGB = (240, 124, 72)
FLOOR_RGB = (234, 229, 223)


def rc():
    """matplotlib settings for every preview figure."""
    return {
        "figure.facecolor": PAPER, "savefig.facecolor": PAPER,
        "axes.facecolor": PANEL, "axes.edgecolor": RULE, "axes.linewidth": 0.8,
        "axes.labelcolor": TEXT, "axes.titlecolor": INK, "axes.titleweight": "bold",
        "axes.titlepad": 8, "axes.spines.top": True, "axes.spines.right": True,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": MUTED, "ytick.labelcolor": MUTED,
        "xtick.major.size": 0, "ytick.major.size": 0, "xtick.major.pad": 5, "ytick.major.pad": 5,
        "grid.color": RULE, "grid.linewidth": 0.6, "text.color": TEXT,
        "legend.labelcolor": TEXT, "hatch.color": BRIDGE, "hatch.linewidth": 0.8,
        "font.family": "DejaVu Sans",
    }
