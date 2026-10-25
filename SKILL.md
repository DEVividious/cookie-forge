---
name: cookie-forge
description: Guides the user step by step from an image or template to a ready-to-print STL cookie cutter (cookies, gingerbread, shortbread, fondant / sugar paste cutters), fitted to their 3D printer. Use it whenever the user mentions a cookie cutter, dough cutter, cookie stamp, gingerbread or fondant shapes, wants to "make a cutter from a picture / logo / letter / child's drawing", has templates in a PDF or several shapes on one sheet, or asks how to design a cutter for 3D printing, even without saying STL. The user may write in any language (e.g. Polish "foremka", "wykrawacz do ciastek", "pierniki"; German "Ausstecher"; Spanish "cortador de galletas"). Also for changes to a cutter made with this skill (another size, another printer, no imprint).
---

# cookie-forge: a cookie cutter from an image

The skill runs the conversation like a helpful friend with a 3D printer: one question at a time,
it shows what it understood, and it builds the STL only after approval. All geometry is computed
by `scripts/cookie_forge.py` in this skill's directory (below `$SKILL`; run it with `uv run`,
which fetches the libraries itself; if `uv` is missing, suggest
`curl -LsSf https://astral.sh/uv/install.sh | sh`). Always run it from the user's project
directory (never `cd` into `$SKILL`): ready STL files go to `./generated/<date>/` there and
working files to `./.work/`, see "Output files". When
you have a tool for multiple-choice questions (AskUserQuestion), use it to pick the printer and
the size; let the user give descriptions and templates in a normal message.

Don't: build the STL before the summary is approved (step 6), guess the printer or the size,
write your own geometry generator when the script handles the case, or make up file names and
paths: the script chooses them and prints the real ones; quote those.

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
uv run $SKILL/scripts/cookie_forge.py analyze template.png --name reindeer --imprint auto
```

The script prints where it saved the reading preview (`.work/<name>/reading.png`) and
keeps a copy of every distinct template it analysed (`.work/<name>/source-original.png`,
`source-v1.png`, ...). Look at the preview (with the Read tool) and tell the user what you see: red line = cutting
edge, blue = imprint, how many shapes, whether something was taken as noise. Ask them to open
the file too. If the reading is wrong, fix it: `--threshold 128` (manual black threshold),
`--invert` (light shape on a dark background), `--holes cut|imprint|ignore` (white holes in the
silhouette), `--split` (separate shapes on a sheet). For a photo or an image
with a background, suggest preparing a clean template first.

If the reading found inner lines (blue), ask what to do with them, as a choice (AskUserQuestion
when available), before going on. Outline only is the default and comes first:

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
uv run $SKILL/scripts/cookie_forge.py prepare template.png --name <name> --size <mm>
```

then look at `.work/<name>/prepare.png` (cleared spots in red) and analyze the new version it
printed (`.work/<name>/source-v1.png`); continue with that file once the reading is right. Lines that only run
close to the outline may get trimmed and a closed shape touching it (e.g. a nose) becomes an
open arc, so show both images to the user before going on.

### 2. Printer

Ask which printer they have. Bed sizes come from `references/printers.md`:

```bash
uv run $SKILL/scripts/cookie_forge.py printers "ender 3"
```

If the printer is not on the list, ask for the bed size (width × depth in mm; it is in the
manual or in the printer profile of the slicer) or look it up online and confirm with the user.
Then use `--bed "name"` or `--bed 220x220`.

### 3. Size

Show the size table from the script and let them choose, or accept the user's own dimensions:

```bash
uv run $SKILL/scripts/cookie_forge.py analyze template.png --bed K1C
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
uv run $SKILL/scripts/cookie_forge.py simplify template.png --size 80 --name cat
```

The first line says whether the outline is complex (a notch narrower than 2 mm, or many small
wiggles: the medium level shortens the outline by at least 8 %). If it says "simple" or
"simplification is not possible", don't mention simplification at all and go on. If it says
"complex", ask one plain question (AskUserQuestion when available): **simplify the outline?**

- **No, keep it as it is** (default, first).
- **Yes, show me the variants**: a smoother cutting edge that prints cleaner and holds less dough,
  but small details of the outline may disappear.

Only after a "yes", look at the preview it saved (`.work/<name>/simplify.png`: the current outline
and the light, medium and strong level side by side over the template outline in grey) and show
it with the table (mean and max deviation from the template, narrowest notch, triangles). Let
them choose one of four: light, medium, strong, or keep the original after all. Pass the choice as
`--simplify-level light|medium|strong` to the dry run and the build. The levels scale with the
cookie, so pick them after the size; a level that would merge or split outlines (the shared walls
of a grid) is rejected and never offered.

When the user asks to simplify an existing cutter ("uprość kontur Mikołaja"), skip the question:
run `simplify --from .work/<name>/<size>mm` (the template and settings of that project), show the
preview, and after the choice run the dry run and the build with
`build --from .work/<name>/<size>mm --simplify-level <level>`. The build becomes a new version
(`<size>mm-v2`, `<name>-<size>mm-v2.stl`); the original stays. `--from` works for any change to an
existing single-template project: only the options given on the command line change.

### 4. Blade profile and other parameters

The standard profile (described in `references/geometry.md`): height 18 mm, wall 1.2 mm,
cutting edge 0.45 mm with a 10° outer bevel (vertical inside, so the side of the cookie is
straight and the wedge pushes the dough outwards), flange 5 × 2 mm lying on the bed. Imprint
(only with `--imprint auto`) set by `--dough` (or 3.5 mm lower than the cutting edge). Don't ask about these parameters; show them in the summary and
change them only on request (`--blade-angle`, `--height`, `--wall`, `--flange`,
`--imprint-drop` etc., full list: `uv run $SKILL/scripts/cookie_forge.py build --help`). For
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
`uv run $SKILL/scripts/cookie_forge.py paths --name <name>`.

### 6. Summary and approval

Before building, run a dry run with a 2D preview:

```bash
uv run $SKILL/scripts/cookie_forge.py build template.png --size 80 --bed K1C --name cat \
    --dry-run --preview-2d
```

A dry run builds no STL: it writes only `dry-run.json` (the settings to approve) and
`dry-run-preview.png` in the project directory it will use (`.work/<name>/<size>mm/`). It prints the summary in the
standard format (below; one block per cutter). Look at the 2D preview, paste the summary to the
user in full and unchanged (for languages other than English and Polish, translate labels only,
as described in "Language"), add one sentence about what the preview shows, and ask plainly:
**do you approve, or do you have remarks / special wishes?** Build only after a "yes". Turn
every remark into a flag, repeat the dry run and show the changed rows of the new output.

The "Project directory" row says what the build will do: a new directory, a new version
(`80mm-v2` and `cat-80mm-v2.stl`, because a build of that size with other settings exists), or nothing at all
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
| `generated/2026-12-01/cat-80mm.stl` | STL model for printing | will be created after approval |
| `.work/cat/80mm/preview.png` | preview: top view, wall cross-section, 3D model | will be created after approval |
| `.work/cat/80mm/source.png` | template used (exact copy) | will be created after approval |
| `.work/cat/80mm/project.json` | project manifest: parameters, results, STL check | will be created after approval |
| `.work/cat/80mm/dry-run.json` | dry-run report with the settings to approve | created by this dry run |
| `.work/cat/80mm/dry-run-preview.png` | 2D preview from this dry run | created by this dry run |

### Build command
```bash
uv run …/scripts/cookie_forge.py build cat.png --size 80 --bed K1C --name cat
```
````

Status words in the Checks table (`OK`, `NARROW`, `DELICATE`, `TOO THIN`, `DOES NOT FIT`,
`TOO TALL`) are the ones to mention when you add your sentence. The build command in the last
section is exactly what step 7 runs: the same flags without `--dry-run` / `--preview-2d`.

### 7. Build, check, hand over

Run the command from the "Build command" section of the approved summary, unchanged, e.g.:

```bash
uv run $SKILL/scripts/cookie_forge.py build template.png --size 80 --bed K1C --name cat
```

The script checks the STL (it must be "OK": watertight, a single solid), writes it to
`generated/<date>/<name>-<size>mm.stl`, writes `preview.png` (top view, cross-section, 3D model),
the template copy `source.<ext>` and `project.json` to `.work/<name>/<size>mm/` and prints a short
report:

```
## Cutter reindeer: ready

- Cookie size: 88.2 × 100.0 mm
- Printer: Creality K1C (bed 220 × 220 × 250 mm)
- STL check: OK (watertight, 1 solid(s), 82522 triangles, 14.1 cm³ ≈ 18 g PLA)
- Warning: the narrowest notch is about 1.5 mm - dough may stick in the cutter (recommended ≥ 2.0 mm)

Files:

- `generated/2026-12-01/reindeer-100mm.stl`: 3D print model
- `.work/reindeer/100mm/preview.png`: cutter preview
- `.work/reindeer/100mm/source.png`: template used
- `.work/reindeer/100mm/project.json`: project parameters

Location: `.work/reindeer/100mm/`
```

A "Note: these settings were not shown in a dry run" line means the build skipped step 6;
that should not happen.

Look at `preview.png` first. If the check failed, the model stays in the project directory as
`cutter-rejected.stl` and never reaches `generated/`; don't hand it over; change the
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

The script owns names and locations; paths are relative to the directory it runs in (the
user's project), never to the skill installation. `--output-dir DIR` puts `generated/` and
`.work/` in DIR instead.

```
generated/                    ready-to-print STL files only
├── 2026-12-01/               one folder per build day (local date)
│   ├── reindeer-100mm.stl    <name>-<size>mm.stl
│   ├── reindeer-100mm-v2.stl same size, other settings
│   └── reindeer-80mm.stl     another size of the same cutter
└── 2026-12-02/
    └── reindeer-100mm-v3.stl versions count across days
.work/                        all working files
└── <name>/                   safe slug of the name: "Mój renifer" -> moj-renifer (not translated)
    ├── source-original.png   template versions (source-v1.png, ...), reading.png, prepare.png, simplify.png
    ├── 100mm/                one directory per size and version (100mm-v2 <-> reindeer-100mm-v2.stl)
    │   ├── preview.png       preview
    │   ├── source.png        exact copy of the template used (keeps its format: .jpg, .pdf, ...)
    │   ├── project.json      manifest: options, parameters, results, checks, files (with the STL path)
    │   ├── notes.md          your notes for the user
    │   └── dry-run.json      dry-run-preview.png too, after a dry run with --preview-2d
    └── 100mm-v2/
```

The version of a project directory and of its STL is the same, so the file name tells which
settings it was built with. Re-running is safe: a dry run only refreshes the dry-run files; a
build with settings identical to an existing build changes nothing (it reports the existing STL,
also from an earlier day); a build with other settings goes to a new version (`100mm-v2`,
`reindeer-100mm-v2.stl`) and leaves the earlier one untouched; `--overwrite` (rebuild in place: the
STL is written again to today's folder and the old file removed) and `--new-version` (always a new
copy) are used only when the user asks. Two cutters with the same name in one run get `name` and
`name-2`. Add `--json` to `build` for a machine-readable result (directories, files with their
status, warnings, and the summary or report text).

## Skill files

- `scripts/cookie_forge.py`: analysis, summary, STL build, preview, outline simplification, template preparation
  (`--help` lists everything); the code lives in `scripts/forge/`.
- `references/geometry.md`: the profile standard and why, imprint, bridges, mirroring, print
  settings. Read it when the user asks "why" or wants to change something.
- `references/templates.md`: how to get a good template, prompts for image models, typical
  reading problems.
- `references/printers.md`: bed table; add new printers in the same row format.
