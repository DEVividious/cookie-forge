# cookie-forge

A model-agnostic agent skill that turns an image or template into an STL file of a cookie /
gingerbread cutter sized for your 3D printer's bed. The agent leads the conversation (template → printer → size
→ summary → approval → STL), and the geometry is computed by `scripts/cookie_forge.py`.

The skill follows the user's language: ask in Polish ("Wygeneruj mi foremkę z tego pliku") and it
answers in Polish. The script prints its summaries in English or Polish (`--lang en|pl`, with the
matching decimal separator); for other languages the agent translates only the labels and never
changes the numbers.

## Examples

Cutters made by going through the whole skill (100 mm, Creality K1C): three outline only, two
with an imprint. Each directory holds one finished cutter: `cutter.stl`, `preview.png`,
`source.png` (the template used), `project.json` and `notes.md` (the skill itself puts the STL in
`generated/` and the rest in `.work/`, see "Output").

| Template | Result | Files |
|---|---|---|
| <img src="examples/reindeer/100mm/source.png" width="160"> | <img src="examples/reindeer/100mm/preview.png" width="480"> | [reindeer](examples/reindeer/100mm/) |
| <img src="examples/birthday-cake/100mm/source.png" width="160"> | <img src="examples/birthday-cake/100mm/preview.png" width="480"> | [birthday cake](examples/birthday-cake/100mm/) |
| <img src="examples/easter-bunny/100mm/source.png" width="160"> | <img src="examples/easter-bunny/100mm/preview.png" width="480"> | [Easter bunny](examples/easter-bunny/100mm/) |
| <img src="examples/birthday-cake-imprint/100mm/source.png" width="160"> | <img src="examples/birthday-cake-imprint/100mm/preview.png" width="480"> | [birthday cake with imprint](examples/birthday-cake-imprint/100mm/) |
| <img src="examples/easter-bunny-imprint/100mm/source.png" width="160"> | <img src="examples/easter-bunny-imprint/100mm/preview.png" width="480"> | [Easter bunny with imprint](examples/easter-bunny-imprint/100mm/) |

With an imprint the inner lines become ridges lower than the cutting edge: they press the
pattern about 1.5 mm into the dough (set from the dough thickness, `--dough 6` here) instead of
cutting it, and the lines stay slightly recessed after baking.
In these two templates the inner lines touched the outline, so the skill first ran `prepare`,
which writes a version where they stop 1 mm short of it (otherwise every line would be imprinted
twice).

The reindeer shows a real warning: a 1.4 mm notch by the ear, where the template's ear line ends
open. Dough may stick there; `--smooth 0.8` would close it.

## Installation

Requirements: an agent that supports `SKILL.md` skills and shell execution, preferably with an
image viewer; Python 3.10+ and [uv](https://docs.astral.sh/uv/)
(`curl -LsSf https://astral.sh/uv/install.sh | sh`). `uv` downloads the libraries (numpy, shapely,
OpenCV, manifold3d, trimesh, matplotlib, PyMuPDF, Pillow) by itself on the first run, which needs
network access and a writable uv cache. Use the host's permission flow when access is blocked.

Keep `SKILL.md`, `scripts/` and `references/` together when installing into your agent's skill
directory. Discovery locations and invocation syntax depend on the host application, not the
model. Examples for [Claude Code](https://claude.com/claude-code) and
[Codex](https://learn.chatgpt.com/docs/build-skills) are below; other compatible agents use the
same files in their own skill directories. Replace `<this-repository>` with this repository's
Git URL:

| Agent | Personal installation | Project installation | Explicit invocation |
|---|---|---|---|
| Claude Code | `~/.claude/skills/cookie-forge` | `.claude/skills/cookie-forge` | `/cookie-forge` |
| Codex CLI / IDE | `~/.agents/skills/cookie-forge` | `.agents/skills/cookie-forge` | `$cookie-forge` |

For example, for Codex:

```bash
mkdir -p "$HOME/.agents/skills"
git clone "<this-repository>" "$HOME/.agents/skills/cookie-forge"
```

To share an existing Claude Code installation with Codex on Linux or macOS, use a symlink
instead of a second clone (the destination must not already exist):

```bash
mkdir -p "$HOME/.agents/skills"
ln -s "$HOME/.claude/skills/cookie-forge" "$HOME/.agents/skills/cookie-forge"
```

Then ask the agent e.g. "make me a cookie cutter from this image", or use its explicit
invocation above. If the installed skill does not appear, restart the agent. Opening this
repository alone does not install its root `SKILL.md` into Codex's skill discovery locations.

The workflow uses whichever question and image-viewing tools the host provides. Without a
question tool it asks in the conversation; without an image viewer it asks you to inspect the
saved preview. It shows the summary and waits for your approval before building the STL.

## Using the script directly

These examples assume the current directory is this repository and the templates are there.
From another project, use the quoted absolute path to the installed `scripts/cookie_forge.py`
instead. Output is relative to the current directory, not the script's installation directory.

```bash
uv run scripts/cookie_forge.py printers "k1c"                                  # printer bed
uv run scripts/cookie_forge.py analyze cat.png --bed K1C --name cat           # reading + sizes
uv run scripts/cookie_forge.py build cat.png --size 80 --bed K1C --name cat --dry-run --preview-2d
uv run scripts/cookie_forge.py build cat.png --size 80 --bed K1C --name cat
uv run scripts/cookie_forge.py build sheet.pdf --split --size original --bed "Prusa MK4"
uv run scripts/cookie_forge.py build --mode merge "star.png@0,0,70" "donut.png@0,-40,36" --size 90
uv run scripts/cookie_forge.py build cat.png --size 80 --bed K1C --lang pl     # Polish output
uv run scripts/cookie_forge.py build cat.png --size 80 --imprint auto --dough 6 # with an imprint
uv run scripts/cookie_forge.py simplify cat.png --size 80 --name cat         # outline simplification variants
uv run scripts/cookie_forge.py build --from .work/cat/80mm --simplify-level medium  # change an existing project
uv run scripts/cookie_forge.py prepare cat.png --name cat --size 80          # detach inner lines
uv run scripts/cookie_forge.py paths --name cat                                # where files go
uv run scripts/cookie_forge.py build --help
```

## Output

Everything goes to the directory you run the script from (your project, not the skill
installation); `--output-dir DIR` puts it elsewhere.

```
generated/                    ready-to-print STL files only
└── 2026-12-01/               one folder per build day
    ├── cat-80mm.stl          <name>-<size>mm.stl
    ├── cat-80mm-v2.stl       same size, other settings (versions count across days)
    └── cat-100mm.stl         another size of the same cutter
.work/                        all working files
└── cat/                      safe slug of --name ("Mój kot" -> moj-kot, never translated)
    ├── source-original.png   template versions seen by `analyze` + reading.png, simplify.png
    ├── 80mm/                 one directory per size and version (80mm-v2 <-> cat-80mm-v2.stl)
    │   ├── preview.png       top view, wall cross-section, 3D model
    │   ├── source.png        exact copy of the template used (original format kept)
    │   ├── project.json      manifest (schema 1): options, parameters, results, checks, files
    │   └── dry-run.json      + dry-run-preview.png after a dry run
    └── 80mm-v2/
```

`--dry-run` builds no STL: it prints the summary (with the exact build command) and writes only
the dry-run files. Results are never replaced silently: identical settings → nothing is rebuilt;
other settings → a new version (`80mm-v2`, `cat-80mm-v2.stl`); `--overwrite` rebuilds in place and
`--new-version` always makes a new copy. A model that fails the check stays in its project
directory as `cutter-rejected.stl`. `--json` prints a machine-readable result.

## Tests

```bash
python3 -m unittest discover tests
```

The tests run the script with `uv run` on the simple templates in `tests/fixtures/` (drawn by
`make_fixtures.py`); a full run takes about a minute.

## Cutter standard

Flange 5 × 2 mm on the bed, wall 1.2 mm, height 18 mm, cutting edge 0.45 mm with a 10° outer
bevel and a vertical inner side, outline only by default; with `--imprint auto` the template's
inner lines become an imprint (1.5 mm deep with `--dough`, otherwise 3.5 mm below the cutting edge), loose parts joined with bridges, model
mirrored (the cookie looks like the template).
Details and reasoning: `references/geometry.md`.

## Repository layout

- `SKILL.md`: the model- and host-independent conversation flow.
- `scripts/cookie_forge.py`: the command-line entry point (`--help` lists everything); the code is
  in the `scripts/forge/` package, split by subdomain (dependencies only point downwards):

  ```
  forge/cli.py          argparse, error handling
  forge/commands/       one module per command: analyze, build, prepare, paths, printers
  forge/presentation/   dry-run summary, build report, PNG previews
  forge/project/        output layout and versions, manifest, settings from the command line
  forge/geometry/       2D outline, blade profile, cutter design, 3D solid and STL
  forge/template/       loading templates, contours -> shapes, collecting sources, prepare
  forge/printers.py, config.py, i18n.py (+ locale_pl.py), errors.py: shared basics
  ```

  User-facing text goes through `i18n.t()` / `Msg`; add the Polish version to `locale_pl.py`
  (the tests fail on a missing one). Library code raises `ForgeError` and never exits.
- `references/geometry.md`, `references/templates.md`, `references/printers.md`: profile
  standard, template tips and image-model prompts, printer bed table.
- `examples/`: results of the whole skill for three templates (see "Examples").
- `tests/`: end-to-end tests of the summary, output layout, versions and manifest;
  `tests/fixtures/` holds their templates.
- `CHANGELOG.md`: changes of behaviour between versions.
- `.gitignore`: a whitelist; only the entries above are tracked, so cutters you make while
  developing (`generated/`, `.work/`, templates, STL files) never end up in the repository. Add a new
  top-level file or directory to it on purpose.
