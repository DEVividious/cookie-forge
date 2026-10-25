"""Default cutter parameters (mm) and the limits of the checks."""


DEFAULTS = dict(
    height=18.0,            # total cutter height
    wall=1.2,               # wall thickness (3 lines with a 0.4 nozzle)
    blade=0.45,             # width of the cutting edge
    blade_angle=10.0,       # outer bevel angle at the cutting edge (degrees from vertical)
    flange=5.0,             # flange width
    flange_thickness=2.0,   # flange thickness
    imprint_width=1.0,      # imprint ridge width at the base
    imprint_tip=0.6,        # imprint ridge width at the top
    imprint_drop=3.5,       # how much lower the imprint ridge is than the cutting edge (without --dough)
    bridge_width=4.0,       # width of the bridges joining loose parts (flange level)
    smooth=0.3,             # outline smoothing radius (removes pixel steps)
    simplify=0.08,          # outline simplification tolerance
    step=0.2,               # step height of the bevel (= print layer)
    margin=10.0,            # distance from the bed edge when checking the fit
)
PLA_DENSITY = 1.24  # g/cm3
SUGGESTED_SIZES = [("S", 60), ("M", 80), ("L", 100), ("XL", 120)]
THIN_MIN = 3.0          # thinner cookie features are delicate
THIN_CRITICAL = 2.0     # thinner cookie features break easily
GAP_MIN = 2.0           # narrower notches hold the dough
IMPRINT_DEPTH = 1.5     # imprint depth in the dough with --dough: deep enough to survive baking
THIN_SEARCH_MAX = 40.0  # search range of thinnest_feature / narrowest_gap
GAP_SEARCH_MAX = 30.0
# Outline simplification levels (--simplify-level), as a share of the longest side of the cookie, so
# a level means the same at 6 and at 15 cm: (contour averaging sigma, rounding radius).
SIMPLIFY_LEVELS = dict(light=(0.008, 0.012), medium=(0.018, 0.020), strong=(0.035, 0.032))
LEVEL_NAMES = {"none": "no simplification", "light": "light", "medium": "medium", "strong": "strong"}
COMPLEX_SHRINK = 0.08   # an outline is complex when the medium level shortens it by this share (or a notch is narrow)
