# Printers and bed sizes

Dimensions are the build volume X × Y × Z in mm (width × depth × height). The script
`cookie_forge.py` reads this table (`--bed "name"` and `printers phrase`), so add new printers
using the same row format. If a printer is not listed, ask the user for the bed size (it is in
the manual or in the printer profile of their slicer) or look it up online.

The cutter has to fit in the area reduced by a margin (10 mm on each side by default): the bed
is often less level near the edges, the brim starts there, and glass clips or sensors often
take up a strip of the bed.

| Maker | Model | X × Y × Z | Notes |
|---|---|---|---|
| Creality | K1 | 220 × 220 × 250 | |
| Creality | K1C | 220 × 220 × 250 | |
| Creality | K1 SE | 220 × 220 × 250 | |
| Creality | K1 Max | 300 × 300 × 300 | |
| Creality | K2 Plus | 350 × 350 × 350 | |
| Creality | Ender-3 | 220 × 220 × 250 | also Pro, V2, Neo |
| Creality | Ender-3 V2 | 220 × 220 × 250 | |
| Creality | Ender-3 V3 SE | 220 × 220 × 250 | |
| Creality | Ender-3 V3 KE | 220 × 220 × 240 | |
| Creality | Ender-3 V3 | 220 × 220 × 250 | |
| Creality | Ender-3 S1 | 220 × 220 × 270 | also S1 Pro |
| Creality | Ender-3 Max | 300 × 300 × 340 | |
| Creality | Ender-5 | 220 × 220 × 300 | also Pro |
| Creality | Ender-5 S1 | 220 × 220 × 280 | |
| Creality | Ender-5 Plus | 350 × 350 × 400 | |
| Creality | CR-10 | 300 × 300 × 400 | also V2, V3, Smart |
| Creality | CR-10 SE | 220 × 220 × 265 | |
| Creality | Hi | 260 × 260 × 300 | |
| Bambu Lab | A1 mini | 180 × 180 × 180 | |
| Bambu Lab | A1 | 256 × 256 × 256 | |
| Bambu Lab | P1P | 256 × 256 × 256 | |
| Bambu Lab | P1S | 256 × 256 × 256 | |
| Bambu Lab | P2S | 256 × 256 × 256 | |
| Bambu Lab | X1C | 256 × 256 × 256 | also X1, X1E |
| Bambu Lab | H2D | 350 × 320 × 325 | less in X with two nozzles |
| Bambu Lab | H2S | 340 × 320 × 325 | |
| Prusa | MINI | 180 × 180 × 180 | also MINI+ |
| Prusa | MK3S | 250 × 210 × 210 | also MK3S+ |
| Prusa | MK4 | 250 × 210 × 220 | also MK4S, MK3.5 |
| Prusa | Core One | 250 × 220 × 270 | |
| Prusa | XL | 360 × 360 × 360 | |
| Anycubic | Kobra 2 | 220 × 220 × 250 | also Kobra 2 Neo |
| Anycubic | Kobra 2 Pro | 220 × 220 × 250 | |
| Anycubic | Kobra 2 Max | 420 × 420 × 500 | |
| Anycubic | Kobra 3 | 250 × 220 × 260 | also Kobra 3 Combo |
| Anycubic | Kobra S1 | 250 × 250 × 250 | |
| Anycubic | Kobra 3 Max | 420 × 420 × 500 | |
| Anycubic | Vyper | 245 × 245 × 260 | |
| Anycubic | i3 Mega | 210 × 210 × 205 | |
| Elegoo | Neptune 3 | 220 × 220 × 280 | |
| Elegoo | Neptune 3 Pro | 225 × 225 × 280 | |
| Elegoo | Neptune 4 | 225 × 225 × 265 | also Neptune 4 Pro |
| Elegoo | Neptune 4 Plus | 320 × 320 × 385 | |
| Elegoo | Neptune 4 Max | 420 × 420 × 480 | |
| Elegoo | Centauri Carbon | 256 × 256 × 256 | also Centauri |
| Flashforge | Adventurer 5M | 220 × 220 × 220 | also 5M Pro |
| Flashforge | AD5X | 220 × 220 × 220 | |
| Flashforge | Adventurer 3 | 150 × 150 × 150 | |
| Qidi | Q1 Pro | 245 × 245 × 240 | |
| Qidi | Plus 4 | 305 × 305 × 280 | |
| Qidi | X-Plus 3 | 280 × 280 × 270 | |
| Qidi | X-Max 3 | 325 × 325 × 315 | |
| Sovol | SV06 | 220 × 220 × 250 | also SV06 Plus: 300 × 300 × 340 |
| Sovol | SV07 | 220 × 220 × 250 | |
| Sovol | SV08 | 350 × 350 × 345 | |
| Artillery | Sidewinder X2 | 300 × 300 × 400 | also X1, X3 |
| Artillery | Genius | 220 × 220 × 250 | also Genius Pro |
| AnkerMake | M5 | 235 × 235 × 250 | also M5C |
| Voron | 2.4 250 | 250 × 250 × 250 | |
| Voron | 2.4 300 | 300 × 300 × 300 | |
| Voron | 2.4 350 | 350 × 350 × 350 | |
| Voron | 0.2 | 120 × 120 × 120 | |
| Kingroon | KP3S | 180 × 180 × 180 | |
| Snapmaker | A350 | 320 × 350 × 330 | |
| Ultimaker | S5 | 330 × 240 × 300 | |
| Ultimaker | 2+ | 223 × 223 × 205 | |
| Toybox | Toybox | 70 × 80 × 90 | |
