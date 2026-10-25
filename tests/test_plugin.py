"""The plugin manifests that let Claude Code and Codex install the skill from this repository."""
import json
import os
import re
import unittest

from helpers import PLUGIN, ROOT, SKILL


def manifest(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return json.load(f)


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


class PluginManifest(unittest.TestCase):
    def test_version_matches_the_script(self):
        # Installed copies only update when this version changes, so it moves with the script.
        version = re.search(r'^VERSION = "(.+)"$', read(SKILL, "scripts", "forge", "__init__.py"),
                            flags=re.M).group(1)
        self.assertEqual(manifest(PLUGIN, ".claude-plugin", "plugin.json")["version"], version)

    def test_marketplace_lists_the_plugin_folder(self):
        entry, = manifest(ROOT, ".claude-plugin", "marketplace.json")["plugins"]
        self.assertEqual(entry["name"], manifest(PLUGIN, ".claude-plugin", "plugin.json")["name"])
        self.assertEqual(os.path.normpath(os.path.join(ROOT, entry["source"])), PLUGIN)

    def test_skill_name_matches_its_directory(self):
        frontmatter = read(SKILL, "SKILL.md").split("---")[1]
        self.assertIn(f"\nname: {os.path.basename(SKILL)}\n", frontmatter)

    def test_installs_carry_the_license_and_a_readme(self):
        # An install copies only the plugin folder; the directory wants 40+ words outside code.
        self.assertEqual(read(PLUGIN, "LICENSE"), read(ROOT, "LICENSE"))
        prose = re.sub(r"```.*?```", "", read(PLUGIN, "README.md"), flags=re.S)
        self.assertGreaterEqual(len(prose.split()), 40)
