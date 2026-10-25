# Cookie cutter: Easter bunny (imprint) (100 mm)

Cookie cutter with an imprint: the inner lines of the template are ridges that press the pattern into the dough, made with the cookie-forge skill from `source.png`, for a Creality K1C
(220 × 220 mm bed).

- Cookie size (cutting edge): 73.5 × 100.0 mm; with the flange 83.5 × 110.0 mm
- Profile: height 18.0 mm, wall 1.2 mm, cutting edge 0.45 mm with a 10° outer bevel, flange 5.0 × 2.0 mm
- Imprint: 15 ridges, 1.0 → 0.6 mm wide, ending 4.5 mm below the cutting edge, so in 6 mm dough they press 1.5 mm deep: a clear pattern that survives baking, without cutting the dough
- Bridges: 17 at flange level hold the ridges (they stay above the dough)
- Template: `source.png` is the original drawing after `prepare`: the inner lines stop 1 mm short of the outline, so each line becomes a single ridge
- STL check: OK (watertight, 1 solid, 150336 triangles, 18.7 cm³ ≈ 23 g PLA)

Warnings:

- none

## Files

- `cutter.stl`: model for printing, already in print orientation
- `preview.png`: top view, wall cross-section, 3D model
- `source.png`: the template used
- `project.json`: all parameters, results and the STL check

## Command

```bash
uv run scripts/cookie_forge.py build examples/easter-bunny-imprint/.work/source-v1.png --size 100 --bed K1C --name 'Easter bunny (imprint)' --dough 6 --output-dir examples
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
| Time | about 30-60 min, 8-15 g for an 80 mm cutter |

The cutter touches raw dough: use PLA or PETG and wash it by hand in lukewarm water, not in the
dishwasher (PLA softens at 60 °C).
