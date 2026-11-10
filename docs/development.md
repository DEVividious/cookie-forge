# Developing Cookie Forge

Back to the [README](../README.md).

## Tests

```bash
python3 -m unittest discover tests
```

The tests run the script with `uv run` on the simple templates in `tests/fixtures/` (drawn by
`make_fixtures.py`); a full run takes about 1–2 minutes, depending on the machine and cached
dependencies.

To try your working copy, start Claude Code with `claude --plugin-dir plugins/cookie-forge`.
Before you push, run `claude plugin validate .` for the marketplace and
`claude plugin validate plugins/cookie-forge` for the plugin.

## Dependencies

The script's libraries are pinned in `cookie_forge.py.lock` next to it, and the tests run with
`--locked`, so a stale lockfile fails them. After changing the dependencies in the script
header, run `uv lock --script plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py`;
add `--upgrade` to move the pins to newer versions.

## Releases

Change `VERSION` in `forge/__init__.py` and `version` in
`plugins/cookie-forge/.claude-plugin/plugin.json` together: installed plugins update only when
that version changes, and a test checks that both match.

## README images

- **Hero:** `examples/showcase.webp` and its still, `examples/showcase.png`, are made with
  ReplayViz from a real Claude Code session, the one that built
  [`examples/gingerbread-man/140mm/`](../examples/gingerbread-man/140mm/) (its `notes.md` has the
  conversation). They are not rendered by a script in this repository. The README shows only the
  animation (an animated WebP, about a quarter of a GIF's size); the still is for places that
  cannot play it.
- **Gallery:** `examples/gallery.webp` is rendered from the actual example meshes, without
  altering them:

  ```bash
  uv run scripts/render_gallery.py
  ```

  It needs Blender 4.2 or later on `PATH` (or `--blender /path/to/blender`; made with 5.2) and
  writes only that file. Blender runs `scripts/gallery_scene.py`: each drawing on a sheet of
  paper next to its two cutters, in the studio of the hero's last scene (same plastic, floor
  and lights). The script then frames the render in a dark card with labels, in the look of
  the clip, and saves a lossy WebP with transparent corners. The labels are set in Overpass,
  bundled in `scripts/fonts/` under the SIL Open Font License. `--work DIR` keeps the raw
  render and `--compose-only` redoes the card from it; `GALLERY` in the script lists the
  examples shown. A re-render looks the same but is not byte-identical (render noise).
- **Plugin icon:** `uv run scripts/render_icon.py` renders
  `plugins/cookie-forge/.claude-plugin/icon.png` from the reindeer mesh and writes only that
  file; `--out PATH` writes it somewhere else, to compare first.

## Repository layout

- `.claude-plugin/marketplace.json`: makes this repository a marketplace that lists the plugin,
  so Claude Code and Codex can install it straight from GitHub.
- `plugins/cookie-forge/`: the plugin, the only folder an install copies. It holds
  `.claude-plugin/plugin.json` with the directory icon, a short `README.md`, a copy of `LICENSE`
  and the skill in `skills/cookie-forge/`.
- `plugins/cookie-forge/skills/cookie-forge/SKILL.md`: the model- and host-independent
  conversation flow.
- `plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py`: the command-line entry
  point (`--help` lists everything), with `cookie_forge.py.lock` pinning its libraries; the code
  is in the `forge/` package next to it, split by subdomain (dependencies only point downwards):

  ```
  forge/cli.py          argparse, error handling
  forge/commands/       one module per command: analyze, build, simplify, prepare, paths, printers
  forge/presentation/   dry-run summary, build report, PNG previews
  forge/project/        output layout and versions, manifest, settings from the command line
  forge/geometry/       2D outline, blade profile, cutter design, 3D solid and STL
  forge/template/       loading templates, contours -> shapes, collecting sources, prepare
  forge/printers/       built-in bed table, your printers file, --bed
  forge/config.py, i18n.py (+ locale_pl.py), errors.py: shared basics
  ```

  User-facing text goes through `i18n.t()` / `Msg`; add the Polish version to `locale_pl.py`
  (the tests fail on a missing one). Library code raises `ForgeError` and never exits.
- `plugins/cookie-forge/skills/cookie-forge/references/`: `geometry.md`, `templates.md` and
  `printers.md`: profile standard, template tips and image-model prompts, printer bed table.
- `scripts/render_gallery.py`: renders the README gallery from the example STLs, with Blender
  (`gallery_scene.py`) and the label font in `scripts/fonts/`.
- `scripts/render_icon.py`: renders the plugin icon from the reindeer STL.
- `examples/`: results of the whole skill, six cutters from four templates (see the
  [README](../README.md#one-drawing-two-cutters)), plus the README showcase and gallery image.
- `docs/`: the [guide](guide.md), the [command-line reference](cli.md) and this file.
- `tests/`: end-to-end tests of the summary, output layout, versions and manifests;
  `tests/fixtures/` holds their templates.
- `CHANGELOG.md`: changes of behaviour between versions.
- `LICENSE`: the MIT license.
- `.gitignore`: a whitelist; only the entries above are tracked, so cutters you make while
  developing (`cookie-forge-output/`, legacy `generated/` and `.work/`, templates, STL files)
  never end up in the repository. Add a new top-level file or directory to it on purpose.
