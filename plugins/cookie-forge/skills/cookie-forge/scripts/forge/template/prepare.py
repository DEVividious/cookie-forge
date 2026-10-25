"""Template preparation: inner lines that touch the outline split the inside of a contour drawing
into many white areas, which are then read as holes (each line imprinted twice, plus a groove
along the wall). detach_lines finds where to cut so that those lines stop short of the outline."""
import os

import numpy as np


def detach_lines(black, gap_px):
    """Pixels to clear so that inner lines end gap_px before the outer outline. The outline
    thickness is measured locally, so thick and thin parts of the outline both stay whole."""
    import cv2
    h, w = black.shape
    fill = (1 - black).astype(np.uint8)
    cv2.floodFill(fill, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 2)
    shape = (fill != 2).astype(np.uint8)                   # the shape with its inside filled
    inner_white = (shape > 0) & (black == 0)
    d_out = cv2.distanceTransform(shape, cv2.DIST_L2, 5)   # distance from the background
    d_in = cv2.distanceTransform((~inner_white).astype(np.uint8), cv2.DIST_L2, 5)  # to the inner white
    core = (black > 0) & (d_out <= d_in)                   # outer half of the outline stroke
    half = cv2.dilate(np.where(core, d_out, 0).astype(np.float32),
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
    edge = 2 * half + 1.5                                  # local outline thickness
    return (black > 0) & (d_out > edge) & (d_out <= edge + gap_px)


def find_cuts(mask, gap_px):
    """(pixels to clear, number of places): detach_lines widened by the anti-aliased fringe."""
    import cv2
    cut = detach_lines(mask.astype(np.uint8), gap_px)
    places = cv2.connectedComponents(cut.astype(np.uint8))[0] - 1
    # the mask is blurred; widen the cut by the anti-aliased fringe, or grey pixels left at its
    # edge reconnect the line to the outline once analyze upscales the image
    cut = cv2.dilate(cut.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
    return cut, places


def apply_cuts(path, source, cut, dpi):
    """The template with the cut pixels cleared: (PIL image, file extension, save options).
    Keeps the format, colours, transparency and DPI; a PDF page becomes a PNG at its DPI."""
    from PIL import Image
    if path.lower().endswith(".pdf"):
        return Image.fromarray(source.gray), ".png", dict(dpi=(dpi, dpi))
    im = Image.open(path)
    info = {"dpi": im.info["dpi"]} if "dpi" in im.info else {}
    ext = os.path.splitext(path)[1].lower() or ".png"
    if source.alpha is not None and (source.alpha < 128).mean() > 0.05:
        arr = np.array(im.convert("RGBA"))
        arr[cut, 3] = 0                                # transparent background: clear to transparent
    else:
        arr = np.array(im.convert("RGB" if im.mode not in ("L", "1") else "L"))
        arr[cut] = 255
    if ext in (".jpg", ".jpeg"):                       # JPEG would blur the gaps again
        ext = ".png"
    return Image.fromarray(arr), ext, info
