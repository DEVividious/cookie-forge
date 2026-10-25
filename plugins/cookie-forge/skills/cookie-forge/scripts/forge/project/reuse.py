"""--from DIR: run a command with the settings of an existing project, changing only what is given."""
import json
import os
from pathlib import Path

from ..errors import fail

BUILD_ONLY = ("--no-3d", "--overwrite", "--new-version")


def expand_from(argv, parser):
    """argv with `--from DIR` replaced by the project's build arguments: its template copies as the
    sources, then its options, then the options of this call (later options win)."""
    i = argv.index("--from")
    if i + 1 >= len(argv):
        fail("--from needs a project directory, e.g. cookie-forge-output/projects/cat/builds/80mm-v1")
    d = argv[i + 1]
    cmd, rest = argv[0], argv[1:i] + argv[i + 2:]
    m = _read(d, "project.json") or _read(d, "dry-run.json") or fail(f"{d}: no project.json or dry-run.json")
    base = m.get("build_args") or (_read(d, "dry-run.json") or {}).get("build_args")
    if not base:
        fail(f"{d}: the project does not record its build arguments; run the build command again instead")
    ns = parser.parse_args(base)
    if ns.mode == "merge":
        fail("--from does not work with merged sources; run the build command again instead")
    copies = [os.path.join(d, r["file"].replace("\\", "/")) for r in m["sources"] if r["role"] == "source"]
    if len(copies) != len(ns.sources) or not all(os.path.exists(c) for c in copies):
        fail(f"{d}: the template copies do not match the recorded sources")
    tokens = list(base[1:])
    for src in ns.sources:
        tokens.remove(src)
    imprint = [os.path.join(d, r["file"].replace("\\", "/")) for r in m["sources"] if r["role"] == "imprint_source"]
    if imprint and "--imprint-from" in tokens:
        tokens[tokens.index("--imprint-from") + 1] = imprint[0]
    if not ns.name and not ns.names and len(copies) == 1 and not ns.split and m.get("name"):
        # The saved source is called source.png, not the original template filename.
        tokens += ["--name", m["name"]]
    if cmd != "build":
        tokens = [x for x in tokens if x not in BUILD_ONLY]
    if m.get("layout_version") == 3:
        # Saved command paths may refer to the old machine or workspace location.
        # The build's current location is authoritative, with an explicit override last.
        for flag in ("--output-dir", "--out-dir"):
            while flag in tokens:
                j = tokens.index(flag)
                del tokens[j:j + 2]
        tokens = [t for t in tokens if not t.startswith(("--output-dir=", "--out-dir="))]
        tokens += ["--output-dir", str(Path(d).resolve().parents[3])]
    return [cmd, *copies, *tokens, *rest]


def _read(d, name):
    try:
        with open(os.path.join(d, name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None
