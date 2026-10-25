# cookie-forge

A Claude Code skill that turns an image or template into an STL file of a cookie / gingerbread
cutter sized for your 3D printer's bed. Claude leads the conversation (template → printer → size
→ summary → approval → STL), and the geometry is computed by `scripts/cookie_forge.py`.

The skill follows the user's language: ask in Polish ("Wygeneruj mi foremkę z tego pliku") and it
answers in Polish. The script prints its summaries in English or Polish (`--lang en|pl`, with the
matching decimal separator); for other languages Claude translates only the labels and never
changes the numbers.

## Examples

Cutters made by going through the whole skill (100 mm, Creality K1C): three outline only, two
with an imprint. Each directory holds what the skill produces: `cutter.stl`, `preview.png`,
`source.png` (the template used), `project.json` and `notes.md`.

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

Requirements: [Claude Code](https://claude.com/claude-code), Python 3.10+ and [uv](https://docs.astral.sh/uv/)
(`curl -LsSf https://astral.sh/uv/install.sh | sh`). `uv` downloads the libraries (numpy, shapely,
OpenCV, manifold3d, trimesh, matplotlib, PyMuPDF) by itself on the first run.

```bash
git clone <this-repository> ~/.claude/skills/cookie-forge
```

or for a single project: `.claude/skills/cookie-forge`. Then in Claude Code write e.g.
"make me a cookie cutter from this image" or `/cookie-forge`.

## Using the script without Claude

```bash
uv run scripts/cookie_forge.py printers "k1c"                                  # printer bed
uv run scripts/cookie_forge.py analyze cat.png --bed K1C --name cat           # reading + sizes
uv run scripts/cookie_forge.py build cat.png --size 80 --bed K1C --name cat --dry-run --preview-2d
uv run scripts/cookie_forge.py build cat.png --size 80 --bed K1C --name cat
uv run scripts/cookie_forge.py build sheet.pdf --split --size original --bed "Prusa MK4"
uv run scripts/cookie_forge.py build --mode merge "star.png@0,0,70" "donut.png@0,-40,36" --size 90
uv run scripts/cookie_forge.py build cat.png --size 80 --bed K1C --lang pl     # Polish output
uv run scripts/cookie_forge.py prepare cat.png --name cat --size 80          # detach inner lines
uv run scripts/cookie_forge.py paths --name cat                                # where files go
uv run scripts/cookie_forge.py build --help
```

## Output

Results go to `./output/` in the directory you run the script from (your project, not the
skill installation); `--output-dir DIR` puts them elsewhere.

```
output/
└── cat/                      safe slug of --name ("Mój kot" -> moj-kot, never translated)
    ├── .work/                template versions seen by `analyze` + reading.png
    └── 80mm/                 one directory per size
        ├── cutter.stl        model for printing
        ├── preview.png       top view, wall cross-section, 3D model
        ├── source.png        exact copy of the template used (original format kept)
        ├── project.json      manifest (schema 1): options, parameters, results, checks, files
        └── .work/            dry-run.json, dry-run-preview.png
```

`--dry-run` builds no STL: it prints the summary (with the exact build command) and writes only
`.work/` files. Results are never replaced silently: identical settings → nothing is rebuilt;
other settings → a new version directory (`80mm-v2`); `--overwrite` rebuilds in place and
`--new-version` always makes a new copy. `--json` prints a machine-readable result.

## Tests

```bash
python3 -m unittest discover tests
```

The tests run the script with `uv run` on the simple templates in `tests/fixtures/` (drawn by
`make_fixtures.py`); a full run takes about a minute.

## Cutter standard

Flange 5 × 2 mm on the bed, wall 1.2 mm, height 18 mm, cutting edge 0.45 mm with a 10° outer
bevel and a vertical inner side, imprint from the template's inner lines (1.5 mm deep with
`--dough`, otherwise 3.5 mm below the cutting edge), loose parts joined with bridges, model
mirrored (the cookie looks like the template).
Details and reasoning: `references/geometry.md`.

## Repository layout

- `SKILL.md`: the conversation flow Claude follows.
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
  developing (`output/`, templates, STL files) never end up in the repository. Add a new
  top-level file or directory to it on purpose.
