"""Loading template files (images, PDF pages) and thresholding them into a mask."""
import os
from dataclasses import dataclass

import numpy as np

from ..errors import fail
from ..i18n import t


@dataclass
class Source:
    name: str
    path: str
    gray: np.ndarray             # grayscale image, 0..255, dark shape
    alpha: np.ndarray | None     # alpha channel, if present
    mm_per_px: float | None      # physical pixel size, if known (PDF, DPI)
    dx: float = 0.0              # placement in "merge" mode
    dy: float = 0.0
    size: float | None = None
    rotation: float = 0.0
    file: str = ""               # the file as given (without placement)
    page: int | None = None      # PDF page number


def parse_source(spec):
    """file[@dx,dy[,size[,rotation]]]"""
    path, dx, dy, size, rot = spec, 0.0, 0.0, None, 0.0
    if "@" in spec:
        path, rest = spec.rsplit("@", 1)
        parts = [float(x) for x in rest.split(",")]
        dx, dy = parts[0], parts[1]
        if len(parts) > 2:
            size = parts[2]
        if len(parts) > 3:
            rot = parts[3]
    return path, dx, dy, size, rot


def load_sources(specs, dpi):
    sources = []
    for spec in specs:
        path, dx, dy, size, rot = parse_source(spec)
        if not os.path.exists(path):
            fail(f"file not found: {path}")
        base = os.path.splitext(os.path.basename(path))[0]
        if path.lower().endswith(".pdf"):
            import pymupdf
            doc = pymupdf.open(path)
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, alpha=False)
                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
                name = base if len(doc) == 1 else f"{base}_p{i + 1}"
                sources.append(Source(name, t("{path} (page {n})", path=path, n=i + 1), arr.copy(), None,
                                      25.4 / dpi, dx, dy, size, rot, path, i + 1))
        else:
            from PIL import Image
            im = Image.open(path)
            mm_per_px = None
            if "dpi" in im.info and im.info["dpi"][0] > 1:
                mm_per_px = 25.4 / float(im.info["dpi"][0])
            alpha = None
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                im = im.convert("RGBA")
                alpha = np.array(im)[:, :, 3]
            gray = np.array(im.convert("L"))
            sources.append(Source(base, path, gray, alpha, mm_per_px, dx, dy, size, rot, path))
    return sources


def mask_from_source(z, threshold, invert, min_width_px=2000):
    """Returns a binary mask (True = shape material), the upscale factor and the threshold used."""
    import cv2
    gray = z.gray
    if z.alpha is not None and (z.alpha < 128).mean() > 0.05:
        # transparent background: the shape is whatever is opaque
        gray = np.where(z.alpha > 128, np.minimum(gray, 100), 255).astype(np.uint8)
        # even if the opaque part is light (white shape), it is still the shape
    h, w = gray.shape
    up = 1.0
    if max(h, w) < min_width_px:
        up = min_width_px / max(h, w)
        gray = cv2.resize(gray, (int(round(w * up)), int(round(h * up))), interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (0, 0), 1.0)
    if threshold == "auto":
        th, bin_ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    else:
        th = float(threshold)
        _, bin_ = cv2.threshold(gray, th, 255, cv2.THRESH_BINARY)
    mask = bin_ < 128  # dark = shape
    # background: sample the image border; a dark border means the image is a negative
    border = np.concatenate([mask[0, :], mask[-1, :], mask[:, 0], mask[:, -1]])
    if border.mean() > 0.5:
        mask = ~mask
    if invert:
        mask = ~mask
    # small noise
    k = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)
    return mask, up, th
