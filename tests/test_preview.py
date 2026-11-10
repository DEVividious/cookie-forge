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


if __name__ == "__main__":
    unittest.main()
