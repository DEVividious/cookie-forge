"""Shared helpers: the script runs with `uv run --locked` (it installs the pinned dependencies)."""
import json
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "cookie-forge")
SKILL = os.path.join(PLUGIN, "skills", "cookie-forge")
SCRIPT = os.path.join(SKILL, "scripts", "cookie_forge.py")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
# the tests never read or change the user's own printers file
NO_PRINTERS = os.path.join(tempfile.mkdtemp(prefix="cookie-forge-printers-"), "printers.md")


def run(*args, cwd, check=True, env=None):
    env = dict(os.environ, COOKIE_FORGE_STRICT="1",   # a missing Polish message is an error
               COOKIE_FORGE_PRINTERS=NO_PRINTERS) | (env or {})
    r = subprocess.run(["uv", "run", "--quiet", "--locked", SCRIPT, *args], cwd=cwd, env=env,
                       capture_output=True, text=True, timeout=600)
    if check and r.returncode != 0:
        raise AssertionError(f"exit {r.returncode}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def run_json(*args, cwd, env=None):
    return json.loads(run(*args, "--json", cwd=cwd, env=env))


def project(*templates):
    """A fresh user project directory with copies of test templates."""
    d = tempfile.mkdtemp(prefix="cookie-forge-test-")
    for name in templates:
        shutil.copy(os.path.join(FIXTURES, name), d)
    return d


def tree(root):
    """All files below root, relative and sorted."""
    out = []
    for dirpath, _, files in os.walk(root):
        out += [os.path.relpath(os.path.join(dirpath, f), root) for f in files]
    return sorted(out)
