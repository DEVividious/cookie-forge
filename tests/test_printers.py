"""The user's own printers file: listing, adding, removing, and --bed resolving it."""
import json
import os
import tempfile
import unittest

from helpers import project, run, run_json


class UserPrinters(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="cookie-forge-printers-")
        self.file = os.path.join(self.dir, "sub", "printers.md")
        self.env = dict(COOKIE_FORGE_PRINTERS=self.file)

    def printers(self, *args):
        return run("printers", *args, cwd=self.dir, env=self.env)

    def read(self):
        with open(self.file, encoding="utf-8") as f:
            return f.read()

    def test_empty_list_names_the_file(self):
        self.assertIn(self.file, self.printers("--mine"))
        self.assertFalse(os.path.exists(self.file))

    def test_add_takes_the_size_from_the_table_and_keeps_the_note(self):
        out = self.printers("--add", "Bambu Lab P2S", "--note", "AMS 2 Pro")
        self.assertIn("Added Bambu Lab P2S", out)
        self.assertIn("| Bambu Lab | P2S | 256 × 256 × 256 | AMS 2 Pro |", self.read())
        self.printers("--add", "k1c")
        mine = self.printers("--mine")
        self.assertIn("| Creality | K1C | 220 × 220 × 250 | |", mine)
        self.assertLess(mine.index("P2S"), mine.index("K1C"))   # in the order they were added

    def test_exact_name_wins_over_a_longer_one(self):
        self.printers("--add", "Creality K1")
        self.assertIn("| Creality | K1 | 220 × 220 × 250 | |", self.read())

    def test_adding_again_updates_the_note_only(self):
        self.printers("--add", "P2S")
        self.assertIn("already", self.printers("--add", "Bambu Lab P2S"))
        self.assertIn("Updated", self.printers("--add", "p2s", "--note", "AMS 2 Pro"))
        self.assertEqual(self.read().count("P2S"), 1)
        self.assertIn("AMS 2 Pro", self.read())

    def test_printer_outside_the_table_needs_a_bed(self):
        with self.assertRaisesRegex(AssertionError, "--bed WIDTHxDEPTH"):
            self.printers("--add", "Workshop Box")
        self.printers("--add", "Workshop Box", "--bed", "350x350x340")
        self.assertIn("| Workshop | Box | 350 × 350 × 340 | |", self.read())
        self.assertIn("Workshop | Box", self.printers("workshop"))

    def test_remove(self):
        self.printers("--add", "K1C")
        self.printers("--add", "P2S")
        self.assertIn("Removed Creality K1C", self.printers("--remove", "K1C"))
        self.assertNotIn("K1C", self.read())
        self.assertIn("P2S", self.read())

    def test_hand_written_rows_and_polish(self):
        os.makedirs(os.path.dirname(self.file))
        with open(self.file, "w", encoding="utf-8") as f:
            f.write("My notes.\n\n| Maker | Model | X × Y × Z | Notes |\n|---|---|---|---|\n"
                    "| Prusa | MK4 | | textured sheet |\n| Custom | Box | 300 x 200 | |\n| Odd | One | | |\n")
        mine = self.printers("--mine", "--lang", "pl")
        self.assertIn("Twoje drukarki", mine)
        self.assertIn("| Prusa | MK4 | 250 × 210 × 220 | textured sheet |", mine)
        self.assertIn("| Custom | Box | 300 × 200 | |", mine)
        self.assertIn("| Odd | One | ? | |", mine)
        self.printers("--add", "K1C")
        text = self.read()
        self.assertTrue(text.startswith("My notes."))
        self.assertLess(text.index("Odd"), text.index("K1C"))

    def test_bed_resolves_the_users_printers_first(self):
        self.printers("--add", "Workshop Box", "--bed", "350x350x340")
        self.printers("--add", "Creality K1C", "--note", "x")
        proj = project("star.png")

        def dry_run(bed, out, env):
            m = run_json("build", "star.png", "--size", "60", "--bed", bed, "--name", "s", "--dry-run",
                         "--output-dir", out, cwd=proj, env=env)
            with open(os.path.join(proj, m["cutters"][0]["dir"], "dry-run.json"), encoding="utf-8") as f:
                return json.load(f)

        m = dry_run("Workshop", "a", self.env)
        self.assertEqual(m["printer"]["name"], "Workshop Box")
        self.assertEqual(m["printer"]["bed_mm"][:2], [350, 350])
        # a saved printer from the table keeps its name and size, so its builds stay identical
        mine, table = dry_run("K1C", "b", self.env), dry_run("K1C", "c", None)
        self.assertEqual(mine["printer"]["name"], "Creality K1C")
        self.assertEqual(mine["fingerprint"], table["fingerprint"])


if __name__ == "__main__":
    unittest.main()
