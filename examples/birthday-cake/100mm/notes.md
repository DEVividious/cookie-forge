# Cookie cutter: Birthday cake (100 mm)

Outline-only cookie cutter (no imprint: the inside of the cookie stays smooth), made with the cookie-forge skill from `source.png`, for a Creality K1C
(220 × 220 mm bed).

- Cookie size (cutting edge): 97.4 × 100.0 mm; with the flange 107.4 × 110.0 mm
- Profile: height 18.0 mm, wall 1.2 mm, cutting edge 0.45 mm with a 10° outer bevel, flange 5.0 × 2.0 mm
- STL check: OK (watertight, 1 solid, 44150 triangles, 11.7 cm³ ≈ 15 g PLA)

Warnings:

- none

## Files

- `cutter.stl`: model for printing, already in print orientation
- `preview.png`: top view, wall cross-section, 3D model
- `source.png`: the template used
- `project.json`: all parameters, results and the STL check

## Command

```bash
uv run scripts/cookie_forge.py build examples/birthday-cake/.work/source-original.png --size 100 --bed K1C --name 'Birthday cake' --imprint none --output-dir examples
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
