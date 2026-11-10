# Cookie cutter: Gingerbread man (140 mm)

Outline-only cookie cutter (no imprint: the inside of the cookie stays smooth), made with the cookie-forge skill from `source.png`, for a Bambu Lab P2S
(256 × 256 mm bed).

- Cookie size (cutting edge): 97.1 × 140.0 mm; with the flange 107.1 × 150.0 mm
- Profile: height 18.0 mm, wall 1.2 mm, cutting edge 0.45 mm with a 10° outer bevel, flange 5.0 × 2.0 mm
- STL check: OK (watertight, 1 solid, 45328 triangles, 15.8 cm³ ≈ 20 g PLA)

Warnings:

- none

## The conversation

Made in one short Claude Code session (the README's `showcase.webp` replays it):

1. "/cookie-forge Make a cutter from gingerbread-man.png, 140 x 97 mm, outline only."
2. The skill showed its reading of the template and asked which of the two saved printers to use: "Bambu Lab P2S."
3. It showed the approval card with the dry-run preview: "Yes, build it."

## Files

- `cutter.stl`: model for printing, already in print orientation
- `preview.png`: top view, wall cross-section, 3D model
- `source.png`: the template used
- `project.json`: all parameters, results and the STL check (file paths point to this folder)

## Command

```bash
uv run --locked scripts/cookie_forge.py build gingerbread-man.png --size 140 --bed 'Bambu Lab P2S' --name gingerbread-man
```

## Printing

Print it flange down on the bed, cutting edge up, without supports.

| Setting | Value |
|---|---|
| Orientation | as in the STL: flange on the bed, cutting edge up |
| Layer | 0.2 mm (first layer 0.2-0.25) |
| Perimeters | 3; the 1.2 mm wall then comes out solid, without infill |
| Infill | anything (the walls are solid); flange 15-20 % |
| Supports, brim | off (a 10° bevel is a 10° overhang, irrelevant) |
| Material | PLA (stiff, easy) or PETG (more resistant to washing). No carbon fibre and no glitter filaments; dough is never touched hot. |
| Seam | random or rear; not "nearest", so there is no bump on the cutting edge |

The cutter touches raw dough: use PLA or PETG and wash it by hand in lukewarm water, not in the
dishwasher (PLA softens at 60 °C).
