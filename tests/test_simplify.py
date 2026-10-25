"""Outline simplification: the variants of `simplify`, the complexity verdict, --simplify-level in
a build, the guard against merging outlines, and --from for an existing project."""
import json
import os
import re
import unittest

from helpers import project, run, run_json


def manifest(proj, d):
    with open(os.path.join(proj, d, "project.json"), encoding="utf-8") as f:
        return json.load(f)


def notch(md):
    return float(re.search(r"\| Narrowest notch \| ≈ ([\d.]+) mm", md).group(1))


class Variants(unittest.TestCase):
    def test_complex_outline_gets_three_levels_and_a_preview(self):
        proj = project("gingerbread.png")
        out = run("simplify", "gingerbread.png", "--size", "80", "--name", "man", cwd=proj)
        self.assertIn("complex (", out)
        self.assertIn(": offer simplification", out)
        rows = re.findall(r"^\| (no simplification|light|medium|strong)\b", out, flags=re.M)
        self.assertEqual(rows, ["no simplification", "light", "medium", "strong"])
        self.assertTrue(os.path.exists(os.path.join(proj, "cookie-forge-output/projects/man/previews/80mm-simplify-001.png")))
        self.assertFalse(os.path.exists(os.path.join(proj, "generated")))

    def test_repeated_comparisons_keep_previous_preview(self):
        proj = project("star.png")
        run("simplify", "star.png", "--size", "60", cwd=proj)
        first = os.path.join(proj, "cookie-forge-output/projects/star/previews/60mm-simplify-001.png")
        with open(first, "rb") as f:
            original = f.read()
        run("simplify", "star.png", "--size", "60", cwd=proj)
        with open(first, "rb") as f:
            self.assertEqual(f.read(), original)
        self.assertTrue(os.path.isfile(os.path.join(proj,
            "cookie-forge-output/projects/star/previews/60mm-simplify-002.png")))

    def test_simple_outline_is_not_offered(self):
        proj = project("star.png")
        out = run("simplify", "star.png", "--size", "60", cwd=proj)
        self.assertIn("simple (", out)

    def test_levels_that_merge_outlines_are_rejected(self):
        proj = project("grid.png")
        out = run("simplify", "grid.png", "--size", "original", "--smooth", "0", cwd=proj)
        self.assertEqual(out.count("rejected"), 3)
        self.assertIn("simplification is not possible", out)
        res = run("build", "grid.png", "--size", "original", "--smooth", "0", "--simplify-level", "light",
                  "--dry-run", cwd=proj, check=False)
        self.assertNotIn("Project summary", res)


class Build(unittest.TestCase):
    def test_level_goes_to_the_summary_and_makes_a_new_version(self):
        proj = project("gingerbread.png")
        base = ["build", "gingerbread.png", "--size", "80", "--name", "man", "--no-3d"]
        plain = run(*base, "--dry-run", cwd=proj)
        self.assertIn("| Outline simplification level | off (--simplify-level none) |", plain)
        run(*base, cwd=proj)
        self.assertEqual(run_json(*base, "--simplify-level", "none", cwd=proj)["cutters"][0]["decision"], "identical")
        medium = run(*base, "--simplify-level", "medium", "--dry-run", cwd=proj)
        self.assertRegex(medium, r"\| Outline simplification level \| medium: wiggles averaged over [\d.]+ mm")
        self.assertIn("cookie-forge-output/projects/man/builds/80mm-v2/", medium)
        self.assertGreater(notch(medium), notch(plain))
        run(*base, "--simplify-level", "medium", cwd=proj)
        self.assertEqual(manifest(proj, "cookie-forge-output/projects/man/builds/80mm-v2")["result"]["simplification"]["level"], "medium")


class FromProject(unittest.TestCase):
    def test_from_reuses_the_template_and_settings(self):
        proj = project("gingerbread.png")
        run("build", "gingerbread.png", "--size", "80", "--name", "man", "--bed", "K1C", "--no-3d", cwd=proj)
        os.remove(os.path.join(proj, "gingerbread.png"))            # the copy in the project is enough
        out = run("simplify", "--from", "cookie-forge-output/projects/man/builds/80mm-v1", cwd=proj)
        self.assertIn("## Outline simplification: man", out)
        res = run_json("build", "--from", "cookie-forge-output/projects/man/builds/80mm-v1", "--simplify-level", "light", cwd=proj)["cutters"][0]
        self.assertEqual(res["dir"], "cookie-forge-output/projects/man/builds/80mm-v2/")
        m = manifest(proj, "cookie-forge-output/projects/man/builds/80mm-v2")
        self.assertEqual(m["printer"]["name"], "Creality K1C")
        self.assertEqual(m["options"]["simplify_level"], "light")
        self.assertIn("--simplify-level", m["build_args"])
        self.assertEqual(m["sources"][0]["original"], "cookie-forge-output/projects/man/builds/80mm-v1/source.png")


if __name__ == "__main__":
    unittest.main()
