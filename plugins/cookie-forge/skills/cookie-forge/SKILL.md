---
name: cookie-forge
description: Create or revise 3D-printable cookie cutters from images, drawings or PDF templates, with an optional imprint. Guides template reading, printer fit, sizing, simplification, preview approval and STL generation. Use for cookie, gingerbread or fondant cutters (including Polish "foremka" and "wykrawacz") and edits to cutters made with this skill.
---

# cookie-forge: a cookie cutter from an image

The skill runs the conversation like a helpful friend with a 3D printer: one question at a time,
it shows what it understood, and it builds the STL only after approval. Reuse choices already
supplied by the user (name, printer, size, imprint); ask only for missing information. The workflow is
independent of the model and host application. All geometry is computed by `scripts/cookie_forge.py`.

Don't: build the STL before the summary is approved (step 6), guess the printer or the size,
write your own geometry generator when the script handles the case, or make up file names and
paths: the script chooses them and prints the real ones; quote those.

## Runtime and tools

Resolve this skill's directory from the actual location of the `SKILL.md` you read; resolve
`references/` and `scripts/` relative to it. Do not assume that the agent sets a skill-directory
environment variable. In the shell examples below, `COOKIE_FORGE_SKILL_DIR` is a variable you
must set to that absolute directory, replacing the example path:

```bash
COOKIE_FORGE_SKILL_DIR="/absolute/path/to/cookie-forge"
uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" --help
```

The examples use POSIX shell syntax; adapt quoting and variable syntax to the available shell.
If shell calls do not share variables, repeat the assignment in each call or use the quoted
absolute script path directly. Run commands from the user's project directory (set the shell
tool's working directory there); never change into the skill installation to run them. All
files go to `./cookie-forge-output/`, grouped by cutter, see "Output files".

Use Python 3.10+ and `uv run --locked`, which installs the exact library versions pinned in
`scripts/cookie_forge.py.lock`; keep the flag on every call. If `uv` is missing,
suggest `curl -LsSf https://astral.sh/uv/install.sh | sh` on Linux/macOS, or
`winget install --id=astral-sh.uv -e` in Windows PowerShell. Reopen the host if its PATH is stale.
The first run needs package-download access and a writable uv cache; follow the host's permission flow if access is blocked.

Use the host's available shell and image-viewing tools. Open PNG previews with an image-capable
tool, not a text-only file reader. If no image viewer is available, give the user the preview
path and ask them to inspect it; do not claim to have seen it. For choices such as printer and
size, use a multiple-choice question tool when available in the current mode; otherwise ask
the same question in the conversation and wait for the answer. Let the user give descriptions
and templates in a normal message. Keep the summary approval in step 6 in every host.

Native Windows has not been validated end to end. Printed build commands currently use POSIX
quoting: on another shell, preserve the exact argument values but adapt quoting and variable
syntax; do not execute POSIX escapes verbatim in PowerShell or cmd.exe.

## Language

Talk to the user in the language they write in, from the first reply on (a request like
"Wygeneruj mi foremkę z tego pliku" means the whole conversation is in Polish). The script
prints its tables, summary and preview labels in English by default; add `--lang pl` to every
`analyze` / `build` / `printers` call when the user writes Polish. For any other language run
with `--lang en` and translate only the labels and descriptions when you show the output: keep
every number, unit, file name and command exactly as printed, only switching the decimal
separator to the user's convention (e.g. a comma in German or French). Never round, re-estimate
or recalculate a value yourself. Notes you write for the user (`notes.md`) are also in their
language.

## Workflow

### 1. Image or template

Ask for a file: PNG/JPG/WEBP/PDF (or several). Explain briefly that the best result comes from a
**black-and-white contour template**: a closed black outline on a white background with an
empty inside and black detail lines inside (eyes, whiskers, buttons), because the outer outline
becomes the cutting edge and the inner lines become the imprint in the dough. Such an image is
also natural for people: it looks like the finished cookie. A filled black silhouette works just
as well but gives only the outline without an imprint; suggest it when the user explicitly wants
a cutter without details. A photo or an image with shadows, gradients or a background gives a
worse result, because thresholding has to guess what the shape is.

If the user only has an idea ("a kitten", "our logo", "a reindeer like in this photo"), suggest
generating a template with an image model (ChatGPT / DALL·E, Gemini / Imagen, Midjourney,
Ideogram, Adobe Firefly, Bing Image Creator) and give a ready prompt from
`references/templates.md` (the contour variant with details by default). You can also draw a
simple template yourself with a script (PIL) or assemble it from several images (see "Several
images").

Agree on a short name for the cutter now (the user's word, e.g. "renifer"; don't translate it)
and pass it as `--name` to every command, so all files of the cutter land in one directory.
Before going on, check the reading. The first reading uses `--imprint auto`, so inner lines show
up in blue and you can tell whether there is anything to imprint:

```bash
uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" analyze template.png --name reindeer --imprint auto
```

The script prints where it saved the reading preview (`cookie-forge-output/projects/<name>/previews/reading-*.png`) and
keeps a copy of every distinct template it analysed (`cookie-forge-output/projects/<name>/templates/source-original.png`,
`source-v1.png`, ...). Open the preview with an image-viewing tool and tell the user what you see:
red line = cutting edge, blue = imprint, how many shapes, whether something was taken as noise. Ask them to open
the file too. If the reading is wrong, fix it: `--threshold 128` (manual black threshold),
`--invert` (light shape on a dark background), `--holes cut|imprint|ignore` (white holes in the
silhouette), `--split` (separate shapes on a sheet). For a photo or an image
with a background, suggest preparing a clean template first.

If the reading found inner lines (blue), ask what to do with them, using a multiple-choice
question tool when available or the conversation otherwise, before going on. Outline only is
the default and comes first:

- **Outline only** (default, nothing to pass): the cutter follows the outer contour; the inside of
  the cookie stays smooth, ready for icing.
- **Outline + imprint** (`--imprint auto`): the inner lines become ridges lower than the cutting
  edge, so they don't cut through the dough but press the pattern into it; after baking the lines
  stay slightly recessed in the cookie.

Ask about the dough thickness only after the user has chosen the imprint, as a separate question;
never put it in the same batch as the imprint question, and never ask it for an outline-only
cutter (the thickness changes nothing there). Gingerbread is usually 4-6 mm, rolled sugar cookies
about 6 mm; pass `--dough <mm>`: the script sets the ridges to press 1.5 mm deep, enough to survive
baking without sinking the pattern too far. If they don't know, leave it out (ridges 3.5 mm below
the cutting edge: a 1.5-2.5 mm imprint in 5-6 mm dough).

With the imprint, pass `--imprint auto` (and `--dough`) to every later command (`analyze`, the dry
run, the build); for an outline-only cutter pass neither. If the user wants
the imprint and the reading shows inner lines doubled, or a blue line running along the red
cutting edge, the lines touch the outline: offer to prepare a version where they stop 1 mm short of it,

```bash
uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" prepare template.png --name cat --size 80
```

then look at `cookie-forge-output/projects/<name>/previews/prepare-*.png` (cleared spots in red) and analyze the new version it
printed (`cookie-forge-output/projects/<name>/templates/source-v1.png`); continue with that file once the reading is right. Lines that only run
close to the outline may get trimmed and a closed shape touching it (e.g. a nose) becomes an
open arc, so show both images to the user before going on.

### 2. Printer

Ask which printer they have. Bed sizes come from `references/printers.md`:

```bash
uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" printers "ender 3"
```

If the printer is not on the list, ask for the bed size (width × depth in mm; it is in the
manual or in the printer profile of the slicer) or look it up online and confirm with the user.
Then use `--bed "name"` or `--bed 220x220`.

### 3. Size

Show the size table from the script and let them choose, or accept the user's own dimensions:

```bash
uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" analyze template.png --bed K1C
```

The table has variants S/M/L/XL (60/80/100/120 mm longest side of the cookie), MAX (the largest
that fits with a 10 mm margin) and "original" for a PDF with a physical size. For each it gives
the size with the flange, **the percentage of the longer bed side and of the bed area**, the
thinnest cookie feature and the narrowest notch. Pass 3-4 variants to the user in one short
table and suggest which to pick: a typical cookie is 60-90 mm, a gingerbread ornament 70-100 mm,
a cutter over 150 mm is awkward and bends. Say the table warnings ("thin feature", "narrow
notch") plainly: thin cookie parts break, narrow notches hold the dough. The size is always the
longest side of the cookie (the cutting edge), without the flange.

### 3a. Simplify the outline (only for complex outlines)

Once the size is chosen, check the outline with the same flags you will build with:

```bash
uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" simplify template.png --size 80 --name cat
```

The first line says whether the outline is complex (a notch narrower than 2 mm, or many small
wiggles: the medium level shortens the outline by at least 8 %). If it says "simple" or
"simplification is not possible", don't mention simplification at all and go on. If it says
"complex", ask one plain question: **simplify the outline?** Use a multiple-choice question tool
when available or the conversation otherwise.

- **No, keep it as it is** (default, first).
- **Yes, show me the variants**: a smoother cutting edge that prints cleaner and holds less dough,
  but small details of the outline may disappear.

Only after a "yes", look at the numbered comparison preview it printed: the current outline
and the light, medium and strong level side by side over the template outline in grey. Show
it with the table (mean and max deviation from the template, narrowest notch, triangles). Let
them choose one of four: light, medium, strong, or keep the original after all. Pass the choice as
`--simplify-level light|medium|strong` to the dry run and the build. The levels scale with the
cookie, so pick them after the size; a level that would merge or split outlines (the shared walls
of a grid) is rejected and never offered.

When the user asks to simplify an existing cutter ("uprość kontur Mikołaja"), skip the question:
run `simplify --from cookie-forge-output/projects/<name>/builds/<size>mm-v1` (the template and settings of that project), show the
preview, and after the choice run the dry run and the build with
`build --from cookie-forge-output/projects/<name>/builds/<size>mm-v1 --simplify-level <level>`. The build becomes a new version
(`exports/<date>/<name>-<size>mm-v2.stl`); the original stays. `--from` works for any change to an
existing single-template project: only the options given on the command line change.

### 4. Blade profile and other parameters

The standard profile (described in `references/geometry.md`): height 18 mm, wall 1.2 mm,
cutting edge 0.45 mm with a 10° outer bevel (vertical inside, so the side of the cookie is
straight and the wedge pushes the dough outwards), flange 5 × 2 mm lying on the bed. Imprint
(only with `--imprint auto`) set by `--dough` (or 3.5 mm lower than the cutting edge). Don't ask about these parameters; show them in the summary and
change them only on request (`--blade-angle`, `--height`, `--wall`, `--flange`,
`--imprint-drop` etc., full list: `uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" build --help`). For
firm dough (gingerbread, shortbread) suggest 10-12°, for soft and thick dough (sugar paste,
fondant) 15-20° and a height of 12-15 mm.

### 5. Several images, sheets, PDF

- **Several files = several cutters**: pass all files at once, each gives a separate STL
  (`--names cat,dog,heart` names them in order).
- **Several templates on one image or page**: `--split` splits them into separate cutters in
  reading order (rows from the top, left to right). By default the scale is shared: the largest
  shape gets `--size`, the others keep their proportions from the sheet; `--scale separate` gives
  each the same longest side.
- **PDF**: every page is a source; `--size original` takes the physical size from the file.
- **Merging several images into one cutter** (`--mode merge`): each source gets a placement
  `file.png@dx,dy,size_mm[,rotation]` relative to a common center; the shapes are united into
  one outline, `--imprint-seams` imprints the seam lines. Agree on the placements with the user
  by eye, show the preview and adjust.
- **Borrowing from several images** (outline from one, details from another): `--imprint-from
  details.png` fits the black lines of the second image into the outline of the first. When the
  user wants something that flags can't do, draw a new PNG template with a simple PIL script
  (black on white, 1500-2000 px) and show it for approval before going on. Save drawn or edited
templates to the `next_template` path printed by
`uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" paths --name cat`.

### 6. Summary and approval

Before building, run a dry run with a 2D preview:

```bash
uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" build template.png --size 80 --bed K1C --name cat \
    --dry-run --preview-2d
```

A dry run builds no STL: it writes only `dry-run.json` (the settings to approve) and
a version-named PNG in the cutter's `previews/` folder; the JSON stays in the build directory. It prints the summary in the
standard format (below; one block per cutter). Look at the 2D preview, paste the summary to the
user in full and unchanged (for languages other than English and Polish, translate labels only,
as described in "Language"), add one sentence about what the preview shows, and ask plainly:
**do you approve, or do you have remarks / special wishes?** Build only after a "yes". Turn
every remark into a flag, repeat the dry run and show the changed rows of the new output.

The "Project directory" row says what the build will do: a new directory, a new version
(`builds/80mm-v2/` and `exports/<date>/cat-80mm-v2.stl`, because a build of that size with other settings exists), or nothing at all
(identical settings already built). Mention a new version or an identical build in your
sentence; don't ask anything extra.

The standard view (generated by the script; never retype or recompute it). Sections, abridged:

````
## Project summary: cat

### Basics
| Item | Value |
|---|---|
| Name | cat |
| Source | cat.png |
| Printer | Creality K1C (bed 220 × 220 × 250 mm) |
| Orientation | cookie = template (the STL model is mirrored, because the cutter is used upside down) |
| Stage | dry run: nothing built yet |

### Size and printing          cookie and footprint size, requested size, bed usage, height, step, margin
### Construction               wall, cutting edge, bevel, flange, imprint, holes, bridges
### Geometry processing        smoothing / simplification at model scale (and in template px), size correction, threshold
### Checks                     | Check | Result | Recommended | Status |: thinnest feature, narrowest notch, bed fit, height vs Z
### Warnings and automatic fixes
**Warnings**
- the narrowest notch is about 1.5 mm - dough may stick in the cutter (recommended ≥ 2.0 mm)
**Automatic fixes**
- added 4 bridges joining loose parts (imprint/holes) to the flange

### Planned files
| File | Contents | Status |
|---|---|---|
| `cookie-forge-output/exports/2026-12-01/cat-80mm-v1.stl` | STL model for printing | will be created after approval |
| `cookie-forge-output/projects/cat/previews/80mm-v1-model.png` | preview: top view, wall cross-section, 3D model | will be created after approval |
| `cookie-forge-output/projects/cat/builds/80mm-v1/source.png` | template used (exact copy) | will be created after approval |
| `cookie-forge-output/projects/cat/builds/80mm-v1/project.json` | project manifest: parameters, results, STL check | will be created after approval |
| `cookie-forge-output/projects/cat/builds/80mm-v1/dry-run.json` | dry-run report with the settings to approve | created by this dry run |
| `cookie-forge-output/projects/cat/previews/80mm-v1-dry-run.png` | 2D preview from this dry run | created by this dry run |

### Build command
```bash
uv run --locked …/scripts/cookie_forge.py build cat.png --size 80 --bed K1C --name cat
```
````

Status words in the Checks table (`OK`, `NARROW`, `DELICATE`, `TOO THIN`, `DOES NOT FIT`,
`TOO TALL`) are the ones to mention when you add your sentence. The build command in the last
section is exactly what step 7 runs: the same flags without `--dry-run` / `--preview-2d`.

### 7. Build, check, hand over

Run the command from the "Build command" section of the approved summary, preserving every
argument (adapt only shell quoting if needed), e.g.:

```bash
uv run --locked "${COOKIE_FORGE_SKILL_DIR}/scripts/cookie_forge.py" build template.png --size 80 --bed K1C --name cat
```

The script checks the STL (it must be "OK": watertight, a single solid), writes it to
`cookie-forge-output/exports/<date>/<name>-<size>mm-vN.stl`, writes a version-named PNG
in `previews/` (top view, cross-section, 3D model),
the template copy `source.<ext>` and `project.json` to `cookie-forge-output/projects/<name>/builds/<size>mm-v1/` and prints a short
report:

```
## Cutter reindeer: ready

- Cookie size: 88.2 × 100.0 mm
- Printer: Creality K1C (bed 220 × 220 × 250 mm)
- STL check: OK (watertight, 1 solid(s), 82522 triangles, 14.1 cm³ ≈ 18 g PLA)
- Warning: the narrowest notch is about 1.5 mm - dough may stick in the cutter (recommended ≥ 2.0 mm)

Files:

- `cookie-forge-output/exports/2026-12-01/reindeer-100mm-v1.stl`: 3D print model
- `cookie-forge-output/projects/reindeer/previews/100mm-v1-model.png`: cutter preview
- `cookie-forge-output/projects/reindeer/builds/100mm-v1/source.png`: template used
- `cookie-forge-output/projects/reindeer/builds/100mm-v1/project.json`: project parameters

Location: `cookie-forge-output/projects/reindeer/builds/100mm-v1/`
```

A "Note: these settings were not shown in a dry run" line means the build skipped step 6;
that should not happen.

Look at the printed model preview first. If the check failed, the model stays in the project directory as
`cutter-rejected.stl` and never reaches `exports/`; don't hand it over; change the
parameters (most often `--smooth 0.5` or `--no-bridges` plus a manual description of the
problem helps). Otherwise give the user this report in their language (with `--lang pl` it is
already Polish): keep the file names and paths exactly as printed, and make them clickable links
when your environment supports links to local files. If the report says "already built",
nothing was rebuilt; say so and offer `--overwrite` (rebuild in place) or `--new-version` (a
separate copy) only if the user wants a rebuild.

Then write `notes.md` into the printed location, in the user's language: the summary from
step 6, the command and the print settings from `references/geometry.md` (section "Printing").
Finish with a sentence about the orientation on the bed (flange down, no supports) and printing
tips. Remind them that the cutter touches raw dough: PLA or PETG, wash by hand in lukewarm
water, not in the dishwasher.

## Output files

The script owns names and locations; quote its actual paths. The default workspace has two main folders: `exports/` for daily STL batches and `projects/`
for all cutter sources, previews and settings. It is
`cookie-forge-output/` relative to the user's current project, never the skill installation.
`--output-dir DIR` replaces that root. Keep the output root consistent throughout the workflow.

```text
cookie-forge-output/projects/<name>/
  templates/source-original.png       template history: source-v1.png, ...
  previews/reading-001.png            numbered reading / preparation / simplification previews
  previews/100mm-simplify-001.png     another comparison gets 002, not an overwrite
  previews/100mm-v1-dry-run.png       preview for this version's latest dry run
  previews/100mm-v1-model.png         final model preview
  builds/100mm-v1/
    source.png                       exact template copy (original format retained)
    project.json                     schema 2, layout 3; relative file references
    dry-run.json                     approved settings, if a dry run was done
    notes.md                         your notes for the user
  builds/100mm-v2/                    changed settings, original retained
```

Printable STL files live only in `cookie-forge-output/exports/<local-build-date>/`, named
`<name>-<size>mm-vN.stl`. This gives the user one folder for a day's batch. Build manifests
point to those files with relative paths; never create duplicate copies in `builds/`.
Hand over the STL link and the daily folder link. Identical models stay under their original
date; `--overwrite` moves a rebuilt version to today's exports and removes its older STL.

Link previews directly. Reading, preparation and simplification previews are already preserved
with unique counters; do not make extra copies. Build previews share their build's version.
Never assume a wildcard path is a real filename: use the path printed by the command.
The whole workspace is persistent project data. Back it up or move it together; `--from`
infers the workspace from a schema-2 build's current location, unless `--output-dir` overrides it.

Identical settings with an existing STL are reused; changed settings create a new version.
A saved build whose STL is missing keeps its version reserved; rebuilding normally creates a
new version. Use `--overwrite` or `--new-version` only when requested. A failed mesh check
produces `cutter-rejected.stl` in the build directory, never a file in `exports/`.

## Skill files

- `scripts/cookie_forge.py`: analysis, summary, STL build, preview, outline simplification, template preparation
  (`--help` lists everything); the code lives in `scripts/forge/`.
- `references/geometry.md`: the profile standard and why, imprint, bridges, mirroring, print
  settings. Read it when the user asks "why" or wants to change something.
- `references/templates.md`: how to get a good template, prompts for image models, typical
  reading problems.
- `references/printers.md`: bed table; add new printers in the same row format.
