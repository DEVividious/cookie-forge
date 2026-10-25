# Changelog

## Unreleased

- Organize `cookie-forge-output/` into `exports/<date>/` for each day's STL batch and
  `projects/<name>/` for templates, previews and build history. Store each printable STL once.
- Preserve numbered comparison previews and reference STL files through relative manifest paths.
  Keep projects editable with `--from` after moving the complete workspace.
- Improve installation instructions, first-use prompts and the bundled demo for Claude Code
  and Codex; document PowerShell setup and the limits of native Windows verification.
- Add an animated reindeer showcase, a still-image alternative and a reproducible renderer.


- Made the skill model-agnostic, with host-specific installation and invocation examples in
  the README.
- Skill commands use an explicitly initialized, quoted skill-directory variable; scripts and
  references resolve from the loaded `SKILL.md`, while output stays in the user's project.
- Questions and preview inspection use the host's available tools, with conversation fallbacks;
  summary approval is still required before building the STL.

## 1.3.0

- Outline simplification: `--simplify-level light|medium|strong` (default `none`) evens out small
  wiggles along the outline and rounds narrow notches and tips; the strength scales with the
  cookie size. A level that would merge or split outlines or close a hole is refused. The summary
  has an "Outline simplification level" row; `project.json` records it under
  `result.simplification`. Builds without simplification keep their fingerprint.
- New `simplify` command: the current outline and the three levels side by side
  (`.work/<name>/simplify.png`) with mean and max deviation from the template, narrowest notch and
  triangle count, and a verdict whether the outline is complex enough to offer simplification
  (a notch under 2 mm, or the medium level shortening the outline by at least 8 %).
- `--from DIR` for `build`, `simplify` and `analyze`: reuse the template copy and the settings of
  an existing project; options given on the command line change them. `project.json` now records
  `build_args`.
- The skill asks "simplify the outline?" only for complex outlines, and shows the variants only
  after a yes.

## 1.2.0

- New layout without `output/`: ready STL files go to `generated/<date>/<name>-<size>mm.stl`
  (another version of the same size: `<name>-<size>mm-v2.stl`, ...; versions count across days
  and match the project directory), all working files to `.work/<name>/` (template versions,
  `reading.png`, `prepare.png`) and `.work/<name>/<size>mm[-vN]/` (`preview.png`, `source.*`,
  `project.json`, `dry-run.json`, `dry-run-preview.png`; no nested `.work/` any more).
  `--output-dir` (default: the current directory) holds both. A model that fails the check is
  kept as `cutter-rejected.stl` in its project directory and never reaches `generated/`.
  `project.json` lists the STL with its path relative to the project directory.
  `--overwrite` writes the STL again to today's folder and removes the old file.
- Outline only is the default: `--imprint` defaults to `none`; `--imprint auto` turns the inner
  lines into an imprint. The skill asks about the dough thickness only after the imprint was
  chosen, never together with the imprint question.
- `paths` prints `generated_dir`; `work_dir` is gone (`cutter_dir` is the working directory).
- Fixed a crash of `analyze` (and of `build` summaries) when a template note was printed:
  `t()` took its own `text` argument for the `{text}` placeholder.

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
