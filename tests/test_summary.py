"""The dry-run summary: sections, language, values at model scale, the build command."""
import ast
import datetime
import glob
import os
import re
import unittest

from helpers import ROOT, project, run

SECTIONS_EN = ["Basics", "Size and printing", "Construction", "Geometry processing", "Checks",
               "Warnings and automatic fixes", "Planned files", "Build command"]
SECTIONS_PL = ["Podstawowe informacje", "Wymiary i druk", "Konstrukcja", "Przetwarzanie geometrii",
               "Diagnostyka", "Ostrzeżenia i automatyczne poprawki", "Planowane pliki", "Polecenie budowy"]


def prose(md):
    """Summary text without code blocks, backticked paths and file names."""
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    md = re.sub(r"`[^`]*`", "", md)
    return re.sub(r"\S+\.(png|stl|json|pdf)\b", "", md)


def row(md, label):
    m = re.search(rf"^\| {re.escape(label)} \| (.*) \|$", md, flags=re.M)
    if not m:
        raise AssertionError(f"no row {label!r} in:\n{md}")
    return m.group(1)


class DryRunSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proj = project("gingerbread.png")
        common = ["build", "gingerbread.png", "--size", "100", "--bed", "K1C", "--name", "man",
                  "--dry-run", "--preview-2d", "--smooth", "0.5"]
        cls.en = run(*common, cwd=cls.proj)
        cls.pl = run(*common, "--lang", "pl", cwd=cls.proj)

    def test_sections_in_order(self):
        for text, names in ((self.en, SECTIONS_EN), (self.pl, SECTIONS_PL)):
            self.assertEqual(re.findall(r"^### (.+)$", text, flags=re.M), names)

    def test_decimal_separator_follows_language(self):
        self.assertIsNone(re.search(r"\d,\d", prose(self.en)), "decimal comma in English output")
        self.assertIsNone(re.search(r"\d\.\d", prose(self.pl)), "decimal point in Polish output")

    def test_build_command_is_a_separate_runnable_block(self):
        cmd = re.search(r"### Build command\n\n```bash\n(.+)\n```", self.en).group(1)
        self.assertTrue(cmd.startswith("uv run "))
        for flag in ("--dry-run", "--preview-2d", "--json"):
            self.assertNotIn(flag, cmd)
        self.assertIn(" build gingerbread.png ", cmd)
        self.assertIn("--smooth 0.5", cmd)

    def test_smoothing_is_reported_at_model_scale(self):
        factor = float(row(self.en, "Size correction after smoothing").split("×")[1])
        smooth = row(self.en, "Outline smoothing radius")
        self.assertIn("(set: 0.5 mm)", smooth)
        eff = float(re.match(r"([\d.]+) mm at model scale", smooth).group(1))
        self.assertAlmostEqual(eff, round(0.5 * factor, 2), places=2)
        px = float(re.search(r"≈ ([\d.]+) template px", smooth).group(1))
        res = float(re.search(r"1 px = ([\d.]+) mm", row(self.en, "Template resolution at model scale")).group(1))
        self.assertAlmostEqual(px * res, eff, delta=0.05)

    def test_planned_and_created_files_are_distinguished(self):
        d = ".work/man/100mm/"
        stl = f"generated/{datetime.date.today().isoformat()}/man-100mm.stl"
        for f in (stl, d + "preview.png", d + "source.png", d + "project.json"):
            self.assertIn("will be created after approval", row(self.en, f"`{f}`"))
        for f in ("dry-run.json", "dry-run-preview.png"):
            self.assertIn("created by this dry run", row(self.en, f"`{d}{f}`"))
        self.assertIn("`.work/man/100mm/` (new project directory)", row(self.en, "Project directory"))

    def test_warnings_and_fixes_are_separate(self):
        block = self.en.split("### Warnings and automatic fixes")[1].split("### Planned files")[0]
        self.assertIn("**Warnings**", block)
        self.assertIn("**Automatic fixes**", block)

    def test_checks_report_measured_values(self):
        self.assertRegex(self.en, r"\| Thinnest cookie feature \| ≈ [\d.]+ mm \| ≥ 3\.0 mm \| \w+")
        self.assertRegex(self.en, r"\| Fits on the bed \| [\d.]+ × [\d.]+ mm in 200 × 200 mm \|")


class ImprintDepth(unittest.TestCase):
    def test_dough_sets_the_ridge_for_a_fixed_imprint_depth(self):
        proj = project("gingerbread.png")
        out = run("build", "gingerbread.png", "--size", "80", "--imprint", "auto", "--dough", "6", "--dry-run", cwd=proj)
        self.assertIn("| Imprint ridge height | 13.5 mm, 4.5 mm below the cutting edge |", out)
        self.assertIn("| Imprint depth | 1.5 mm in 6.0 mm dough (--dough 6) |", out)
        default = run("build", "gingerbread.png", "--size", "80", "--imprint", "auto", "--dry-run", cwd=proj)
        self.assertIn("| Imprint ridge height | 14.5 mm, 3.5 mm below the cutting edge |", default)
        self.assertIn("dough thickness minus 3.5 mm", default)

    def test_dough_and_imprint_drop_exclude_each_other(self):
        proj = project("gingerbread.png")
        out = run("build", "gingerbread.png", "--size", "80", "--dough", "6", "--imprint-drop", "3",
                  "--dry-run", cwd=proj, check=False)
        self.assertNotIn("Project summary", out)


    def test_outline_only_is_the_default(self):
        proj = project("gingerbread.png")
        out = run("build", "gingerbread.png", "--size", "80", "--dry-run", cwd=proj)
        self.assertIn("| Imprint | off (--imprint none) |", out)
        self.assertNotIn("Imprint ridge height", out)


class Translations(unittest.TestCase):
    def test_every_message_has_a_polish_version(self):
        keys, tables = set(), {}
        for path in glob.glob(os.path.join(ROOT, "scripts", "forge", "**", "*.py"), recursive=True):
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
            keys |= {n.args[0].value for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and getattr(n.func, "id", None) in ("t", "Msg")
                     and n.args and isinstance(n.args[0], ast.Constant)}
            tables.update({n.targets[0].id: n.value for n in tree.body
                           if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)})
        for name in ("DECISIONS", "ROLES", "STATUSES", "REPORT_ROLES"):
            keys |= set(ast.literal_eval(tables[name]).values())
        pl = ast.literal_eval(tables["PL"])
        self.assertEqual(keys - pl.keys(), set())
        self.assertEqual(pl.keys() - keys, set(), "unused Polish messages")
        for k, v in pl.items():
            self.assertEqual(set(re.findall(r"{(\w+)}", k)), set(re.findall(r"{(\w+)}", v)), k)


class OtherCommands(unittest.TestCase):
    def test_analyze_and_printers_in_both_languages(self):
        proj = project("sheet.png")
        for lang in ("en", "pl"):
            out = run("analyze", "sheet.png", "--split", "--bed", "K1C", "--lang", lang, cwd=proj)
            self.assertEqual(out.count("| MAX |"), 3)
            self.assertIn("Creality | K1C", run("printers", "k1c", "--lang", lang, cwd=proj))


if __name__ == "__main__":
    unittest.main()
