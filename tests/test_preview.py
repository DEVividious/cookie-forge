"""The cutter preview: no label on top of another label or of the drawing, nothing outside its frame
or the figure, for short and tall profiles, in English and in the longer Polish."""
import json
import os
import subprocess
import tempfile
import unittest

from helpers import FIXTURES, NO_PRINTERS, ROOT, SCRIPT, run

PROFILES = [
    [],
    ["--height", "12", "--blade-angle", "20"],                              # blade and bevel labels close together
    ["--height", "25", "--blade-angle", "5", "--wall", "2.4"],              # tall bevel, hardly any straight wall
    ["--wall", "0.8", "--blade", "0.3", "--flange", "2", "--flange-thickness", "1"],    # flange label near the bed line
    ["--height", "22.5", "--flange", "12.5", "--flange-thickness", "2.5", "--blade", "0.125",
     "--imprint-width", "6", "--imprint-tip", "3", "--imprint-drop", "10.25"],          # long numbers, wide ridge
]


class Layout(unittest.TestCase):
    def test_labels_overlap_nothing_and_stay_inside(self):
        tmp = tempfile.mkdtemp(prefix="cookie-forge-test-")
        run("--help", cwd=tmp)                      # makes sure the script's environment exists
        python = subprocess.run(["uv", "python", "find", "--script", SCRIPT], capture_output=True, text=True,
                                check=True).stdout.strip()
        man, star = os.path.join(FIXTURES, "gingerbread.png"), os.path.join(FIXTURES, "star.png")
        commands = []
        for lang in ("en", "pl"):
            commands += [["build", man, "--size", "80", "--bed", "220x220", "--imprint", "auto", "--dry-run", "--preview-2d",
                          "--lang", lang, *profile] for profile in PROFILES]
            commands.append(["build", star, "--size", "60", "--dry-run", "--preview-2d", "--lang", lang,
                             "--name", "a long cutter name that goes on and on for the grandchildren"])   # no bed
            commands.append(["build", star, "--size", "60", "--bed", "220x220", "--lang", lang])            # with the 3D model
        r = subprocess.run([python, os.path.join(ROOT, "tests", "preview_layout.py"), os.path.dirname(SCRIPT), tmp,
                            json.dumps(commands)], capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, COOKIE_FORGE_STRICT="1", COOKIE_FORGE_PRINTERS=NO_PRINTERS))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")



STUDIO = """
import json, sys
sys.path.insert(0, sys.argv[1])
import numpy as np, trimesh
from forge.presentation.studio import render_model
from forge.presentation.style import FLOOR_RGB
box = trimesh.creation.box((40, 30, 18)); box.apply_translation((0, 0, 9))
ring = trimesh.creation.annulus(r_min=30, r_max=32, height=18); ring.apply_translation((0, 0, 9))
out = {}
for name, m in (("box", box), ("ring", ring)):
    img = render_model(m.vertices, m.faces, 200, 160)
    again = render_model(m.vertices, m.faces, 200, 160)
    c = img[80, 100].astype(int)
    out[name] = dict(shape=list(img.shape), same=bool((img == again).all()), centre=c.tolist(),
                     corner=img[2, 2].astype(int).tolist(), floor=list(FLOOR_RGB))
print(json.dumps(out))
"""


class Studio(unittest.TestCase):
    """The 3D view: the mesh in orange plastic on the floor, at the asked size, the same every time."""

    def test_render(self):
        tmp = tempfile.mkdtemp(prefix="cookie-forge-test-")
        run("--help", cwd=tmp)
        python = subprocess.run(["uv", "python", "find", "--script", SCRIPT], capture_output=True, text=True,
                                check=True).stdout.strip()
        r = subprocess.run([python, "-c", STUDIO, os.path.dirname(SCRIPT)], capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        box, ring = out["box"], out["ring"]
        self.assertEqual(box["shape"], [160, 200, 3])
        self.assertTrue(box["same"] and ring["same"])
        red, green, blue = box["centre"]
        self.assertTrue(red > green + 40 > blue + 40, box["centre"])         # plastic orange on the model
        cr, cg, cb = ring["centre"]                                         # the floor shows through the ring
        self.assertTrue(abs(cr - cg) < 40 and cb > 120, ring["centre"])
        self.assertTrue(all(abs(a - b) < 60 for a, b in zip(box["corner"], box["floor"])), box["corner"])


if __name__ == "__main__":
    unittest.main()
