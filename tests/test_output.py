"""Output layout: directories, names, versions and conflicts, manifest, several cutters."""
import hashlib
import json
import os
import unittest

from helpers import project, run, run_json, tree

STAR = ["build", "star.png", "--size", "60", "--name", "Gwiazdka", "--no-3d"]


def manifest(proj, d):
    with open(os.path.join(proj, d, "project.json"), encoding="utf-8") as f:
        return json.load(f)


class Layout(unittest.TestCase):
    def test_default_output_dir_is_relative_to_the_project(self):
        proj = project("star.png")
        res = run_json(*STAR, cwd=proj)
        self.assertEqual(res["cutters"][0]["dir"], "output/gwiazdka/60mm/")
        self.assertEqual(tree(os.path.join(proj, "output")),
                         ["gwiazdka/60mm/cutter.stl", "gwiazdka/60mm/preview.png",
                          "gwiazdka/60mm/project.json", "gwiazdka/60mm/source.png"])

    def test_custom_output_dir_and_old_alias(self):
        proj = project("star.png")
        run(*STAR, "--output-dir", "prints", cwd=proj)
        run(*STAR, "--out-dir", "prints2", cwd=proj)
        self.assertTrue(os.path.exists(os.path.join(proj, "prints/gwiazdka/60mm/cutter.stl")))
        self.assertTrue(os.path.exists(os.path.join(proj, "prints2/gwiazdka/60mm/cutter.stl")))
        self.assertFalse(os.path.exists(os.path.join(proj, "output")))

    def test_slug_keeps_the_name_untranslated(self):
        proj = project()
        for name, slug in (("renifer", "renifer"), ("Mój Renifer!", "moj-renifer"), ("Łoś  2", "los-2"),
                           ("Кот", "кот"), ("../x", "x"), ("con", "con-cutter")):
            self.assertEqual(json.loads(run("paths", "--name", name, cwd=proj))["id"], slug)

    def test_sizes_get_separate_directories(self):
        proj = project("star.png")
        run("build", "star.png", "--size", "60", "--name", "star", "--no-3d", cwd=proj)
        run("build", "star.png", "--size", "80", "--name", "star", "--no-3d", cwd=proj)
        self.assertEqual(sorted(os.listdir(os.path.join(proj, "output/star"))), ["60mm", "80mm"])

    def test_paths_do_not_depend_on_the_language(self):
        a, b = project("star.png"), project("star.png")
        en = run_json(*STAR, "--dry-run", "--preview-2d", cwd=a)
        pl = run_json(*STAR, "--dry-run", "--preview-2d", "--lang", "pl", cwd=b)
        self.assertEqual([f["path"] for f in en["cutters"][0]["files"]], [f["path"] for f in pl["cutters"][0]["files"]])
        self.assertEqual(tree(a), tree(b))


class DryRunAndManifest(unittest.TestCase):
    def test_dry_run_writes_only_work_files(self):
        proj = project("star.png")
        res = run_json(*STAR, "--dry-run", "--preview-2d", cwd=proj)
        self.assertEqual(tree(os.path.join(proj, "output")),
                         ["gwiazdka/60mm/.work/dry-run-preview.png", "gwiazdka/60mm/.work/dry-run.json"])
        statuses = {f["path"]: f["status"] for f in res["cutters"][0]["files"]}
        self.assertEqual(statuses["output/gwiazdka/60mm/cutter.stl"], "planned")
        self.assertEqual(statuses["output/gwiazdka/60mm/.work/dry-run.json"], "created")
        self.assertIn("### Planned files", res["cutters"][0]["summary_md"])

    def test_manifest_and_its_update_after_the_build(self):
        proj = project("star.png")
        run(*STAR, "--dry-run", "--bed", "K1C", cwd=proj)
        with open(os.path.join(proj, "output/gwiazdka/60mm/.work/dry-run.json"), encoding="utf-8") as f:
            dry = json.load(f)
        self.assertEqual(dry["stage"], "dry-run")
        self.assertEqual(dry["build_args"][:2], ["build", "star.png"])
        run(*STAR, "--bed", "K1C", cwd=proj)
        m = manifest(proj, "output/gwiazdka/60mm")
        self.assertEqual((m["schema"], m["schema_version"], m["stage"]), ("cookie-forge/project", 1, "built"))
        self.assertEqual((m["id"], m["name"]), ("gwiazdka", "Gwiazdka"))
        self.assertEqual(m["fingerprint"], dry["fingerprint"])
        self.assertTrue(m["matches_dry_run"])
        self.assertTrue(m["stl_check"]["ok"])
        self.assertEqual(m["sources"][0]["file"], "source.png")
        self.assertEqual(m["sources"][0]["original"], "star.png")
        self.assertEqual(m["printer"]["name"], "Creality K1C")
        self.assertEqual(m["parameters"]["smooth"], 0.3)
        self.assertIn("radius_mm", m["result"]["smoothing"])
        self.assertEqual([f["path"] for f in m["files"]], ["cutter.stl", "preview.png", "source.png", "project.json"])
        with open(os.path.join(proj, "output/gwiazdka/60mm/cutter.stl"), "rb") as f:
            self.assertEqual(m["stl_sha256"], hashlib.sha256(f.read()).hexdigest())
        self.assertNotIn(proj, json.dumps(m), "absolute path in the manifest")

    def test_build_without_dry_run_is_noted(self):
        proj = project("star.png")
        out = run(*STAR, cwd=proj)
        self.assertIn("not shown in a dry run", out)
        self.assertFalse(manifest(proj, "output/gwiazdka/60mm")["matches_dry_run"])


class Conflicts(unittest.TestCase):
    def test_versioning_policy(self):
        proj = project("star.png")
        d = os.path.join(proj, "output/gwiazdka")
        first = run_json(*STAR, cwd=proj)["cutters"][0]
        self.assertEqual(first["decision"], "new")
        stl = os.path.join(d, "60mm/cutter.stl")
        mtime = os.path.getmtime(stl)

        again = run_json(*STAR, cwd=proj)["cutters"][0]             # same settings: nothing rebuilt
        self.assertEqual(again["decision"], "identical")
        self.assertEqual(os.path.getmtime(stl), mtime)

        dry = run_json(*STAR, "--wall", "1.6", "--dry-run", cwd=proj)["cutters"][0]
        self.assertEqual((dry["decision"], dry["dir"]), ("new_version", "output/gwiazdka/60mm-v2/"))
        changed = run_json(*STAR, "--wall", "1.6", cwd=proj)["cutters"][0]  # other settings: new version
        self.assertEqual(changed["dir"], "output/gwiazdka/60mm-v2/")
        self.assertEqual(os.path.getmtime(stl), mtime, "the first build was touched")

        over = run_json(*STAR, "--overwrite", cwd=proj)["cutters"][0]      # explicit overwrite
        self.assertEqual((over["decision"], over["dir"]), ("overwrite", "output/gwiazdka/60mm/"))
        self.assertNotEqual(os.path.getmtime(stl), mtime)

        new = run_json(*STAR, "--new-version", cwd=proj)["cutters"][0]     # explicit copy
        self.assertEqual(new["dir"], "output/gwiazdka/60mm-v3/")
        self.assertEqual(sorted(n for n in os.listdir(d) if n != ".work"), ["60mm", "60mm-v2", "60mm-v3"])

    def test_imprint_settings_do_not_count_without_an_imprint(self):
        proj = project("star.png")
        run(*STAR, "--imprint", "none", cwd=proj)
        same = run_json(*STAR, "--imprint", "none", "--imprint-drop", "5", cwd=proj)["cutters"][0]
        self.assertEqual(same["decision"], "identical")
        self.assertEqual(run_json(*STAR, "--imprint", "none", "--dough", "6", cwd=proj)["cutters"][0]["decision"], "identical")
        other = run_json(*STAR, "--imprint-drop", "5", cwd=proj)["cutters"][0]       # with an imprint it counts
        self.assertEqual(other["decision"], "new_version")

    def test_foreign_files_are_never_replaced(self):
        proj = project("star.png")
        os.makedirs(os.path.join(proj, "output/gwiazdka/60mm"))
        with open(os.path.join(proj, "output/gwiazdka/60mm/cutter.stl"), "w") as f:
            f.write("mine")
        res = run_json(*STAR, cwd=proj)["cutters"][0]
        self.assertEqual(res["dir"], "output/gwiazdka/60mm-v2/")
        with open(os.path.join(proj, "output/gwiazdka/60mm/cutter.stl")) as f:
            self.assertEqual(f.read(), "mine")

    def test_overwrite_and_new_version_exclude_each_other(self):
        proj = project("star.png")
        out = run(*STAR, "--overwrite", "--new-version", cwd=proj, check=False)
        self.assertFalse(os.path.exists(os.path.join(proj, "output")), out)


class SeveralCutters(unittest.TestCase):
    def test_sheet_gives_one_directory_per_cutter(self):
        proj = project("sheet.png")
        res = run_json("build", "sheet.png", "--split", "--size", "80", "--names", "Serce,Koło,Gwiazdka",
                       "--dry-run", cwd=proj)
        self.assertEqual([c["dir"] for c in res["cutters"]],
                         ["output/serce/80mm/", "output/kolo/74mm/", "output/gwiazdka/58mm/"])

    def test_same_name_in_one_run_does_not_collide(self):
        proj = project("star.png", "donut.png")
        res = run_json("build", "star.png", "donut.png", "--names", "x,x", "--size", "60", "--no-3d", cwd=proj)
        self.assertEqual([c["dir"] for c in res["cutters"]], ["output/x/60mm/", "output/x-2/60mm/"])
        self.assertTrue(any("same name" in w for w in res["cutters"][1]["warnings"]))

    def test_merged_sources_are_numbered(self):
        proj = project("star.png", "donut.png")
        run("build", "--mode", "merge", "star.png@0,0,70", "donut.png@0,-40,36", "--size", "90", "--name", "z",
            "--no-3d", cwd=proj)
        m = manifest(proj, "output/z/90mm")
        self.assertEqual([s["file"] for s in m["sources"]], ["source-1.png", "source-2.png"])
        self.assertEqual(m["sources"][1]["placement"], {"dx": 0.0, "dy": -40.0, "size": 36.0, "rotation": 0.0})


class Prepare(unittest.TestCase):
    def test_detaches_lines_that_touch_the_outline(self):
        proj = project("badge.png")
        self.assertIn("2 hole(s) as imprint", run("analyze", "badge.png", "--name", "badge", cwd=proj))
        out = run("prepare", "badge.png", "--name", "badge", "--size", "80", cwd=proj)
        self.assertIn("output/badge/.work/source-v1.png (new version)", out)
        self.assertIn("2 place(s), gap 1.0 mm at a cookie size of 80 mm", out)
        self.assertEqual(tree(os.path.join(proj, "output/badge/.work")),
                         ["prepare.png", "reading.png", "source-original.png", "source-v1.png"])
        after = run("analyze", "output/badge/.work/source-v1.png", "--name", "badge", cwd=proj)
        self.assertIn("2 imprint region(s), 0 hole(s) as imprint", after)

    def test_nothing_to_detach_writes_nothing(self):
        proj = project("gingerbread.png")
        out = run("prepare", "gingerbread.png", cwd=proj)
        self.assertIn("Nothing to detach", out)
        self.assertFalse(os.path.exists(os.path.join(proj, "output")))


class TemplateHistory(unittest.TestCase):
    def test_analyze_keeps_distinct_template_versions(self):
        proj = project("star.png", "donut.png")
        run("analyze", "star.png", "--name", "shape", cwd=proj)
        run("analyze", "star.png", "--name", "shape", cwd=proj)
        run("analyze", "donut.png", "--name", "shape", cwd=proj)
        self.assertEqual(tree(os.path.join(proj, "output/shape")),
                         [".work/reading.png", ".work/source-original.png", ".work/source-v1.png"])
        paths = json.loads(run("paths", "--name", "shape", cwd=proj))
        self.assertEqual(paths["next_template"], "output/shape/.work/source-v2.png")


if __name__ == "__main__":
    unittest.main()
