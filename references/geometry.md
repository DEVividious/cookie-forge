# Cutter geometry: the standard and why

All dimensions in mm. Parameter names are script flags (`--height` etc.).

## Wall cross-section

```
          blade 0.45
   dough ─┐▁
          │ ╲  bevel BLADE_ANGLE = 10° (over a height of about 4.3 mm)
          │  ╲
          │   │ wall 1.2
          │   │
          │   │
          │   └──────┐ flange 5 × 2
   z = 0  └──────────┘  ← print bed
```

The cutter prints flange down on the bed, cutting edge up. To use it, flip it over: the flange
is then the top you press with your palm, and the cutting edge goes into the dough.

| Parameter | Default | Why |
|---|---|---|
| `--height` | 18 | Gingerbread and shortbread dough is 4-8 mm thick; 18 mm leaves room for fingers and keeps the flange off the dough. Fondant / sugar paste: 12-15 mm, because a lower cutter bends less. |
| `--wall` | 1.2 | Three 0.4 mm nozzle lines: stiff, prints without infill. |
| `--blade` | 0.45 | One nozzle line. The slicer may drop a narrower edge; a wider one squashes the dough instead of cutting it. |
| `--blade-angle` | 10° | Bevel on the outer side only. The inner side is vertical, so the cookie side is straight and even, and the wedge pushes the dough outwards, towards the scraps. For firm dough (gingerbread, shortbread) 10-12°; for soft and thick dough (fondant, sugar paste) 15-20°, because a smaller wedge is easier to pull out. Above 25° the edge stops being an edge. |
| `--flange`, `--flange-thickness` | 5 × 2 | Grip and stiffening, and at the same time a large first layer that holds the print on the bed without a brim. |
| `--imprint-width`, `--imprint-tip` | 1.0 → 0.6 | Ridge that presses the template lines; tapered over the last 2 mm so the imprint is crisp and the ridge does not break while printing. |
| `--dough` | – | Dough thickness. The ridge is set so that, with the cutter pressed down to the board, it presses 1.5 mm into the dough (`--imprint-drop` = dough − 1.5). Shallower imprints tend to disappear in the oven, deeper ones sink the pattern instead of marking it. |
| `--imprint-drop` | 3.5 | Without `--dough`: the ridge ends 3.5 mm below the cutting edge, so the imprint is the dough thickness minus 3.5 mm (1.5-2.5 mm in 5-6 mm dough). It presses the pattern but does not cut through the dough. |
| `--bridge-width` | 4 | 4 × 2 mm beams at flange level that join loose parts. |
| `--smooth` | 0.3 | Rounds off pixel steps and sharp corners with a 0.3 mm radius. For a poor image (photo, small file) 0.5-0.8. |
| `--simplify` | 0.08 | Outline simplification tolerance; smaller STL files with no visible change in shape. |
| `--step` | 0.2 | The bevel is built from steps one layer high: the slicer prints 0.2 mm layers anyway, so the steps are not visible in the print, and the solid is always valid (no loft between outlines with different vertex counts). |
| `--margin` | 10 | Distance from the bed edge when checking whether the cutter fits. |

## What the script does with the image

1. Grayscale image, upscaled to at least 2000 px, slightly blurred and thresholded (Otsu or
   `--threshold`). Dark = shape. If the image border is dark, the image is treated as a
   negative (`--invert` forces it). A transparent PNG background counts as background.
2. Contours with hierarchy. Every top-level contour is a separate shape. White holes in a black
   silhouette: a large hole (> 50 % of the area) means a contour drawing, and the black lines
   inside it are the imprint; a small hole follows `--holes` (default `imprint`: presses its
   outline; `cut`: a real hole with its own cutting wall; `ignore`).
3. Specks below 1 % of the largest shape are noise and are skipped (the `analyze` preview says
   how many).
4. Scaling to `--size` (longest side of the cookie), smoothing, then rescaling again so the size
   is exact after smoothing.
5. Imprint: thin black lines become ridges `--imprint-width` wide; thick blobs press only their
   outline (a solid blob would push the dough out).
6. Bridges: everything at flange level (flange, ridge feet, hole walls) is checked for
   connectivity. Every loose part gets a beam to its nearest neighbour; a part longer than
   24 mm gets a second beam from its other end. The beams lie on the bed while printing, and in
   use they are 16 mm above the cutting edge, so they do not touch the dough.
7. Solid: a union of slabs (flange, wall, bevel steps, ridges, beams) computed in manifold3d, so
   the STL is always watertight and a single body; the script checks this with trimesh anyway.

## Mirroring

The cutter works upside down, so the model is a mirror image of the template: this way **the
cookie looks like the template** (important for letters, logos, an animal facing left). The 2D
preview shows the cookie, the 3D preview shows the model. `--no-mirror` turns mirroring off
(e.g. when the user wants a stamp that presses a mirrored pattern into clay).

## Size and the bed

Percent of the longer bed side = longest side of the footprint (with flange) / longer bed side.
Percent of the bed area = footprint rectangle / bed area. "Does not fit" accounts for a 90°
rotation and the margin. MAX in the size table is the largest cookie whose footprint with the
flange fits within the margin.

## Printing

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

Elephant's foot (a flared first layer) does not matter, because the first layer is the flange.
Wash by hand in lukewarm water, not in the dishwasher (PLA softens at 60 °C).
