# Changelog

## 1.1.0

- Results go to `./output/<name>/<size>mm/` relative to the current directory (the user's
  project) with fixed file names: `cutter.stl`, `preview.png`, `source.<ext>` (exact copy of the
  template used), `project.json` (manifest, schema 1). Helper files live in `.work/`.
  Previously: flat `cutter_<name>_<size>mm.{stl,png,json}` in `--out-dir` (default `.`).
- `--output-dir` replaces `--out-dir` (still accepted as an alias); the default is `output`.
- `--dry-run` writes only `.work/dry-run.json` and, with `--preview-2d`,
  `.work/dry-run-preview.png`; it no longer writes `<name>.png` next to the results.
- Existing builds are never replaced silently: identical settings → nothing is rebuilt, other
  settings → a new version directory `<size>mm-vN`; new flags `--overwrite` and `--new-version`.
  With `--imprint none` the imprint settings (`--imprint-width/-tip/-drop`, `--dough`,
  `--imprint-seams`) do not count as a change.
- `build` prints a short report with the real paths instead of the full summary; `--json` gives a
  machine-readable result.
- `analyze` writes its reading preview to `output/<name>/.work/reading.png` by default and keeps
  every distinct template (`source-original.*`, `source-vN.*`); new `paths` command.
- The skill asks whether inner lines should be imprinted or left out (outline only,
  `--imprint none`); with `--imprint none` the reading preview shows no imprint and the summary
  reports template holes as left out.
- The reading preview title wraps instead of being cut off; enclosed white areas in imprint
  lines are drawn; the preview legend wraps.
- `examples/` now holds complete skill results (reindeer, birthday cake, Easter bunny outline
  only; birthday cake and Easter bunny with an imprint); the test templates moved to
  `tests/fixtures/`.
- The 3D view in `preview.png` draws all triangles up to 250k (it used to draw a random 40k,
  which left holes in detailed models).
- New `prepare` command: a new template version where inner lines that touch the outline stop
  short of it (`--gap`, 1 mm at the cookie size), with a preview of the changes.
- Imprint depth: new `--dough MM` sets the ridges to press 1.5 mm into dough of that thickness
  (the skill asks for it when the user wants an imprint). **Changed default:** without `--dough`
  the ridges end 3.5 mm below the cutting edge (was 3 mm), i.e. a shallower imprint.
- The single 2000-line script is now the `scripts/forge/` package, split by subdomain (template,
  geometry, project, presentation, commands) with short single-purpose functions; library code
  raises `ForgeError` instead of exiting. Same command line; the output of every command and the
  generated files are byte-identical to before the split.
- Otherwise geometry and default parameters are unchanged (outline meshes are byte-identical to
  1.0.0).

## 1.0.0

- English repository and CLI (`analyze`, `build`, `printers`), `--lang en|pl` output, dry-run
  summary in sections with values at model scale.
