# cookie-forge

**Turn a picture into a cookie cutter you can 3D print.**

Give your agent a template, choose your printer and cookie size, then approve the preview.
Cookie Forge creates an STL with a sharp cutting edge, a sturdy grip and an optional imprint.
No CAD experience needed.

![A reindeer template beside an animated view of its actual 100 mm cookie cutter STL](examples/showcase.gif)

[Install](#installation) · [Make your first cutter](#make-your-first-cutter) · [Try the demo](#try-it-without-an-agent) · [Example files](#examples)

[Still image of the animation](examples/showcase.png) · [Download the featured STL](examples/reindeer/100mm/cutter.stl)

## Installation

You need **Git**, **Python 3.10+**, [uv](https://docs.astral.sh/uv/getting-started/installation/),
and an agent that supports `SKILL.md` files and shell execution. The first run downloads the
geometry and image libraries (potentially hundreds of MB); allow network access and a writable
uv cache. Later runs reuse them.

Install uv if needed:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows PowerShell
winget install --id=astral-sh.uv -e
```

Choose **one** installation below. These are personal installations available across your local
projects. The Windows commands are a setup starting point; see [compatibility](#compatibility).

<details open>
<summary><strong>Claude Code</strong></summary>

macOS / Linux:

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/DEVividious/cookie-forge.git "$HOME/.claude/skills/cookie-forge"
uv run "$HOME/.claude/skills/cookie-forge/scripts/cookie_forge.py" --help
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME/.claude/skills" | Out-Null
git clone https://github.com/DEVividious/cookie-forge.git "$HOME/.claude/skills/cookie-forge"
uv run "$HOME/.claude/skills/cookie-forge/scripts/cookie_forge.py" --help
```

</details>

<details>
<summary><strong>Codex</strong></summary>

macOS / Linux:

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/DEVividious/cookie-forge.git "$HOME/.agents/skills/cookie-forge"
uv run "$HOME/.agents/skills/cookie-forge/scripts/cookie_forge.py" --help
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME/.agents/skills" | Out-Null
git clone https://github.com/DEVividious/cookie-forge.git "$HOME/.agents/skills/cookie-forge"
uv run "$HOME/.agents/skills/cookie-forge/scripts/cookie_forge.py" --help
```

</details>

The check should list `analyze`, `build`, `simplify`, `prepare`, `paths` and `printers`.
Restart your agent if it does not discover the new skill.

For a project-only installation, use `.claude/skills/cookie-forge` or
`.agents/skills/cookie-forge` inside that project. Other compatible hosts need the same
`SKILL.md`, `scripts/` and `references/` together in their own skill directory.
Discovery details: [Claude Code skills](https://code.claude.com/docs/en/skills) and
[Codex skills](https://learn.chatgpt.com/docs/build-skills).

## Make your first cutter

1. Open your agent in a folder where you want to keep your cutters, separate from the skill installation.
2. Attach a PNG, JPG, WEBP or PDF template. A closed black outline on white works best;
   inner lines can become an imprint. A filled silhouette works for outline-only cutters.
3. Send one of these prompts in the **agent chat**, not the terminal:

   **Claude Code:** `/cookie-forge Make a 100 mm cutter from this image for my Creality K1C. Outline only.`

   **Codex:** `$cookie-forge Make a 100 mm cutter from this image for my Creality K1C. Outline only.`

   **Po polsku:** „Zrób foremkę z tego obrazka: 100 mm, Creality K1C, sam obrys. Nazwij ją renifer.”

The agent checks the image, asks for missing choices, shows the dimensions and preview,
and waits for your approval before creating the STL. Already supplied choices should not
need repeating. Size means the **longest side of the cookie**, excluding the grip flange.

You receive links to the STL and preview, plus saved settings for later edits. Import the STL
into your slicer with the flange down. To iterate, ask: “Simplify this cutter and show me the
variants” or “Make the same cutter 80 mm wide on its longest side.” Changed settings create a
new version. The agent follows your language; script output supports English and Polish.

Only have an idea? Ask the agent to help prepare a template first; see [template prompts](references/templates.md).

## Try it without an agent

This self-contained demo uses a template included in the repository. Run it from a scratch
folder. It works with the same single-line commands in Bash and PowerShell once Git and uv are installed:

```bash
git clone https://github.com/DEVividious/cookie-forge.git
cd cookie-forge
uv run scripts/cookie_forge.py analyze examples/reindeer/100mm/source.png --bed K1C --name reindeer --output-dir demo
uv run scripts/cookie_forge.py build examples/reindeer/100mm/source.png --size 100 --bed K1C --name reindeer --output-dir demo --dry-run --preview-2d
```

Open `demo/projects/reindeer/previews/100mm-v1-dry-run.png` and read the summary. The reindeer
has a narrow notch near its ear; the warning is expected. If you like the result, build it:

```bash
uv run scripts/cookie_forge.py build examples/reindeer/100mm/source.png --size 100 --bed K1C --name reindeer --output-dir demo
```

Find the STL in `demo/exports/<build-date>/reindeer-100mm-v1.stl` and the rendered preview at
`demo/projects/reindeer/previews/100mm-v1-model.png`. Repeat the build to see that identical settings reuse
the existing model.

Try a smoother outline without losing the original:

```bash
uv run scripts/cookie_forge.py simplify --from demo/projects/reindeer/builds/100mm-v1
```

Open the comparison PNG printed by the command (for example,
`demo/projects/reindeer/previews/100mm-simplify-001.png`), compare the four variants, then try your preferred
level (shown here: `medium`):

```bash
uv run scripts/cookie_forge.py build --from demo/projects/reindeer/builds/100mm-v1 --simplify-level medium --dry-run --preview-2d
```

Inspect the new dry-run preview, then build when ready:

```bash
uv run scripts/cookie_forge.py build --from demo/projects/reindeer/builds/100mm-v1 --simplify-level medium
```

The result becomes
`demo/exports/<build-date>/reindeer-100mm-v2.stl`; the original stays available.

## Examples

<details>
<summary>Browse all five templates, previews and downloadable STL files</summary>

Cutters made by going through the whole skill (100 mm, Creality K1C): three outline only, two
with an imprint. Each directory holds one finished cutter: `cutter.stl`, `preview.png`,
`source.png` (the template used), `project.json` and `notes.md` (the skill itself puts the STL in
a visible workspace with separate builds, previews and templates, see "Output").

| Template | Result | Files |
|---|---|---|
| <img alt="Cookie cutter example" src="examples/reindeer/100mm/source.png" width="160"> | <img alt="Cookie cutter example" src="examples/reindeer/100mm/preview.png" width="480"> | [reindeer](examples/reindeer/100mm/) |
| <img alt="Cookie cutter example" src="examples/birthday-cake/100mm/source.png" width="160"> | <img alt="Cookie cutter example" src="examples/birthday-cake/100mm/preview.png" width="480"> | [birthday cake](examples/birthday-cake/100mm/) |
| <img alt="Cookie cutter example" src="examples/easter-bunny/100mm/source.png" width="160"> | <img alt="Cookie cutter example" src="examples/easter-bunny/100mm/preview.png" width="480"> | [Easter bunny](examples/easter-bunny/100mm/) |
| <img alt="Cookie cutter example" src="examples/birthday-cake-imprint/100mm/source.png" width="160"> | <img alt="Cookie cutter example" src="examples/birthday-cake-imprint/100mm/preview.png" width="480"> | [birthday cake with imprint](examples/birthday-cake-imprint/100mm/) |
| <img alt="Cookie cutter example" src="examples/easter-bunny-imprint/100mm/source.png" width="160"> | <img alt="Cookie cutter example" src="examples/easter-bunny-imprint/100mm/preview.png" width="480"> | [Easter bunny with imprint](examples/easter-bunny-imprint/100mm/) |

With an imprint the inner lines become ridges lower than the cutting edge: they press the
pattern about 1.5 mm into the dough (set from the dough thickness, `--dough 6` here) instead of
cutting it, with the aim of keeping the pattern visible after baking; the result depends on the dough.
In these two templates the inner lines touched the outline, so the skill first ran `prepare`,
which writes a version where they stop 1 mm short of it (otherwise every line would be imprinted
twice).

The reindeer shows a real warning: a 1.4 mm notch by the ear, where the template's ear line ends
open. Dough may stick there; `--smooth 0.8` would close it.

</details>

<details>
<summary>Advanced command-line recipes</summary>

## Using the script directly

These optional recipes assume you are in the repository and have supplied your own `cat.png`,
`sheet.pdf`, `star.png` and `donut.png`. For a runnable first example, use the demo above.
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
uv run scripts/cookie_forge.py build --from cookie-forge-output/projects/cat/builds/80mm-v1 --simplify-level medium  # change an existing project
uv run scripts/cookie_forge.py prepare cat.png --name cat --size 80          # detach inner lines
uv run scripts/cookie_forge.py paths --name cat                                # where files go
uv run scripts/cookie_forge.py build --help
```

</details>

## Output

By default, everything lives in **`cookie-forge-output/` in your current project**.
`--output-dir DIR` replaces that workspace root (for example, `--output-dir demo` writes
`demo/projects/reindeer/…`, without an extra `cookie-forge-output` level).

```text
cookie-forge-output/
├── exports/                         open this folder for printing
│   └── 2026-10-25/
│       ├── reindeer-100mm-v1.stl
│       ├── reindeer-100mm-v2.stl
│       └── birthday-cake-80mm-v1.stl
└── projects/                        sources, previews and edit history
    └── reindeer/
        ├── templates/
        │   └── source-original.png
        ├── previews/
        │   ├── reading-001.png
        │   ├── 100mm-simplify-001.png
        │   ├── 100mm-simplify-002.png
        │   ├── 100mm-v1-dry-run.png
        │   └── 100mm-v1-model.png
        └── builds/
            ├── 100mm-v1/
            │   ├── source.png
            │   ├── project.json
            │   └── dry-run.json
            └── 100mm-v2/
                └── …
```

Open **`projects/<name>/previews/`** to compare outlines and inspect the model. Reading, preparation and
simplification previews get a new numbered filename on each run; earlier comparisons stay.
Model and dry-run previews are named after their build version. Repeating a dry run for the
same version refreshes that version's dry-run report and preview.

Print from **`exports/<build-date>/`**: all cutters built that day are together, named
`<name>-<size>mm-vN.stl`. These are the **only printable STL files**, not extra copies.
Each build's `project.json` points to its STL using a relative path. `builds/` keeps sources
and settings; it does not keep a second STL. Back up or move the **whole workspace**, including previews and templates; `--from`
infers the output root from the build's new location. The agent also writes `notes.md` there.
Size is rounded to whole millimeters in directory names; exact dimensions are in the manifest.

A dry run writes no STL. Identical settings reuse an existing STL; changed settings create a
new version. Reusing an identical model keeps its original export date and creates no copy.
`--overwrite` explicitly rebuilds the same version into today's folder and removes its old
STL if the date changed; `--new-version` requests a separate version. If a previous STL was deleted, its saved project still reserves that version, and a
normal rebuild creates a new version. Failed checks leave `cutter-rejected.stl`, never a
file in `exports/`. `--json` provides structured results with actual paths.

## Troubleshooting

| Symptom | What to do |
|---|---|
| Skill does not appear | Check that `SKILL.md`, `scripts/` and `references/` are together in the host's skill folder; restart the agent. Opening this repo alone does not install it. |
| `uv` is not found | Install uv and reopen the terminal or agent so it sees the updated PATH. |
| First run stalls or downloads fail | Allow package downloads through the host's permission flow and use a writable uv cache. Subsequent cached runs need no downloads. |
| Outline is wrong | Use a clean black outline on white; inspect the reading before building. See [template tips](references/templates.md). |
| Preview is missing from the chat | Open the printed PNG path. A host without an image viewer cannot inspect it for you. |
| Model looks reversed | The STL is mirrored deliberately: the cutter is flipped when pressed into dough. |
| Need to edit an older cutter | Keep its workspace and use `--from`; an STL alone does not retain the source settings. |

## Compatibility

The workflow is designed for Claude Code, Codex and other agents that can load skills and run
local commands. The **host's tools and permissions**, not a particular model name, determine
whether it can execute the full workflow. An image viewer improves the experience; without one,
the agent asks you to inspect saved previews. No model API key is needed by the geometry script.

Native Windows support is **not yet verified end to end**. The Python code already uses path
joining and avoids common reserved filenames, but that is not a Windows test. In particular,
auto-generated build commands currently use POSIX quoting; ask the agent to adapt quoting to
PowerShell while preserving all arguments. Native Windows still needs automated tests for
installation, generation and workspaces with spaces or non-ASCII paths.

## Maintaining the showcase

Run `uv run scripts/render_showcase.py` to regenerate the README GIF and still image from
`examples/reindeer/100mm/cutter.stl`. This renders the actual mesh without altering the model.

## Tests

```bash
python3 -m unittest discover tests
```

The tests run the script with `uv run` on the simple templates in `tests/fixtures/` (drawn by
`make_fixtures.py`); a full run takes about 1–2 minutes, depending on the machine and cached dependencies.

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
  developing (`cookie-forge-output/`, legacy `generated/` and `.work/`, templates, STL files) never end up in the repository. Add a new
  top-level file or directory to it on purpose.
