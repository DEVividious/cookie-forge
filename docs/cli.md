# Cookie Forge on the command line

The skill is one Python script. You can run it without an agent; all you need is Git and
[uv](https://docs.astral.sh/uv/getting-started/installation/). Back to the
[README](../README.md) or the [guide](guide.md).

## Demo: the bundled reindeer

From a scratch folder, these commands work as-is in Bash and PowerShell:

```bash
git clone https://github.com/DEVividious/cookie-forge.git
cd cookie-forge
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build examples/reindeer/100mm/source.png --size 100 --bed K1C --name reindeer --output-dir demo --dry-run --preview-2d
```

This prints the approval card an agent would show you (add `--details` for the full summary)
and writes the 2D preview to `demo/projects/reindeer/previews/100mm-v1-dry-run.png`. The
narrow-notch warning is expected. Build the STL:

```bash
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build examples/reindeer/100mm/source.png --size 100 --bed K1C --name reindeer --output-dir demo
```

Find it in `demo/exports/<build-date>/reindeer-100mm-v1.stl`, with a rendered preview at
`demo/projects/reindeer/previews/100mm-v1-model.png`. Repeat the build to see that identical
settings reuse the existing model.

### Size table, simplification and a new version

See the size variants and the template reading:

```bash
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py analyze examples/reindeer/100mm/source.png --bed K1C --name reindeer --output-dir demo
```

Try a smoother outline without losing the original:

```bash
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py simplify --from demo/projects/reindeer/builds/100mm-v1
```

Open the comparison PNG printed by the command (for example,
`demo/projects/reindeer/previews/100mm-simplify-001.png`), compare the four variants, then try
your preferred level (shown here: `medium`):

```bash
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build --from demo/projects/reindeer/builds/100mm-v1 --simplify-level medium --dry-run --preview-2d
```

Inspect the new dry-run preview, then build when ready:

```bash
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build --from demo/projects/reindeer/builds/100mm-v1 --simplify-level medium
```

The result becomes `demo/exports/<build-date>/reindeer-100mm-v2.stl`; the original stays
available.

## Recipes

These assume you are in the repository and have supplied your own `cat.png`, `sheet.pdf`,
`star.png` and `donut.png`. From another project, use the quoted absolute path to
`plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py` in your clone instead. Output
is relative to the current directory, not the script's location; see
[where your files go](guide.md#where-your-files-go).

```bash
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py printers "k1c"                                  # printer bed
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py printers --add "Bambu Lab P2S" --note "AMS 2 Pro" # save your printer
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py printers --mine                                 # your saved printers
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py analyze cat.png --bed K1C --name cat           # reading + sizes
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build cat.png --size 80 --bed K1C --name cat --dry-run --preview-2d
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build cat.png --size 80 --bed K1C --name cat --dry-run --details  # full summary
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build cat.png --size 80 --bed K1C --name cat
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build sheet.pdf --split --size original --bed "Prusa MK4"
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build --mode merge "star.png@0,0,70" "donut.png@0,-40,36" --size 90
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build cat.png --size 80 --bed K1C --lang pl     # Polish output
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build cat.png --size 80 --imprint auto --dough 6 # with an imprint
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py simplify cat.png --size 80 --name cat         # outline simplification variants
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build --from cookie-forge-output/projects/cat/builds/80mm-v1 --simplify-level medium  # change an existing project
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py prepare cat.png --name cat --size 80          # detach inner lines
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py paths --name cat                                # where files go
uv run plugins/cookie-forge/skills/cookie-forge/scripts/cookie_forge.py build --help
```

`--help` on the script or any command lists every option.
