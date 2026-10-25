# Templates: how to get a good image

The script sees only two things: black (shape) and white (background). Everything else has to be
guessed by thresholding. That is why the best input is:

- **a contour drawing** (the default suggestion): a closed black outline with an empty inside
  plus black lines inside it that become the imprint (eyes, buttons, leaf veins, lettering).
  Lines 2-4 % of the image width; thinner ones disappear after scaling, thicker ones press only
  their outline. The outline must be closed and the details must not touch it, otherwise the
  script takes everything for one silhouette. Such an image looks like the finished cookie, so
  it is easy to judge;
- **a silhouette**: a solid black shape on a white background, when only the outline is wanted,
  with no imprint.

Good proportions: the shape fills 70-90 % of the image, file 1000-3000 px, PNG or PDF. Photos,
shadows, gradients, surrounding text, watermarks and a non-white background make the reading
worse.

## Prompts for image models

Suggest generating the template in ChatGPT (DALL·E / GPT Image), Gemini (Imagen), Midjourney,
Ideogram, Adobe Firefly or Bing Image Creator. An English prompt works best, whatever language
the conversation is in.

Contour with imprint details (default):

```
Cookie cutter template with imprint lines: a [cat sitting, side view] drawn as a single thick
black closed outline on a pure white background, empty white inside, with a few simple black
inner lines for details ([eye, ear, whiskers]). Flat vector line art, uniform line thickness,
no fill, no shading, no gradients, no text, no watermark, centered, fills most of the square
image. The outline must be one connected closed shape with no parts thinner than 1/20 of its
width; inner details must not touch the outline.
```

Silhouette (outline only, no imprint):

```
Cookie cutter template: solid black silhouette of a [cat sitting, side view] on a pure white
background. Flat vector style, thick simplified outline, no inner details, no shading, no
gradients, no text, no watermark, centered, fills most of the square image. The shape must be
one connected piece with no parts thinner than 1/20 of its width.
```

Notes on the prompt:
- "one connected piece" prevents separate parts (e.g. a kitten and a separate ball), which the
  script joins with bridges anyway, but they look worse;
- "no parts thinner than..." protects against tails and whiskers that break in the dough;
- generators often mangle lettering; letters are better drawn with a script (PIL + a system
  font).

## Drawing a template with a script

When the user describes a shape in words or wants to combine something the flags cannot do,
draw a PNG with PIL (black on white, 2000 px, `ImageDraw.polygon/ellipse/rounded_rectangle/text`)
and show it for approval. Letters: `ImageFont.truetype` with a font from `/usr/share/fonts`
(DejaVu Sans Bold is almost always there). Remember that the script mirrors the model itself,
so draw the letter normally.

## Common reading problems

| Symptom in the reading preview (`analyze`) | Cause | What to do |
|---|---|---|
| the shape is a rectangle of the whole image | dark or grey background | `--invert` or `--threshold 100` |
| part of the shape is missing | light grey elements | `--threshold 200` |
| lots of small shapes | photo, noise, JPG | ask for a clean template; `--smooth 0.8` |
| inner lines are red (they cut) but should imprint | the outline is not closed, the lines touch the outline | close the outline in the image; `--imprint-from` with a separate file for the details |
| a white hole is cut instead of imprinted | `--holes cut` | default `--holes imprint` |
| inner lines doubled (blue on both sides) and a blue line along the whole cutting edge | the inner lines touch the outline, so the inside is read as many separate holes | `prepare` writes a version where the inner lines stop 1 mm short of the outline (`--gap`), or leave the gap in the drawing yourself, or choose outline only (`--imprint none`) |
| two shapes from a sheet merged into one cutter | no `--split` | `--split`, names via `--names` |
| a letter comes out mirrored in the 3D preview | this is correct: the model is mirrored, cookie = template | nothing; `--no-mirror` only on explicit request |
