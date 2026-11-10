"""The 3D view of the STL, rendered like the studio shot in the README: orange plastic on a warm floor,
soft key light, ambient occlusion and a soft shadow. Pure numpy and OpenCV (no 3D library): a z-buffer
rasterizer at 2× the output size, shaded per sample and scaled down, which anti-aliases the edges.

Every triangle of the mesh is drawn as it is (back faces culled), so the picture is the STL itself."""
import numpy as np

from .style import FLOOR_RGB, PLASTIC_RGB

SUPERSAMPLE = 2
ELEVATION = 38.0        # degrees above the floor, as in the README render
YAW = -20.0             # the model turned a little, so its front is not flat on
FOV = 24.0              # vertical field of view (degrees): a long lens, little distortion
FILL = 0.86             # share of the frame the model may take
SHADOW_MM = 0.5         # resolution of the floor's shadow maps

# Directions from the surface towards each light (camera at -y looking at +y, z up).
KEY = np.array([-0.55, -0.40, 0.72])
FILL_LIGHT = np.array([0.80, -0.40, 0.30])
RIM = np.array([0.30, 0.85, 0.40])


def _unit(v):
    v = np.asarray(v, np.float32)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _lin(rgb):
    c = np.asarray(rgb, np.float32) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def _display_lut(n=4096, top=2.0):
    """Linear light 0 … top to sRGB 0 … 255: unchanged up to 0.8, then a soft shoulder, so highlights
    roll off instead of clipping."""
    x = np.linspace(0, top, n, dtype=np.float64)
    c = np.where(x < 0.8, x, 0.8 + 0.2 * (1 - np.exp(-(x - 0.8) / 0.2)))
    return (np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255).astype(np.float32)


_LUT = _display_lut()


def _display(lin):
    return _LUT[np.clip(lin * ((len(_LUT) - 1) / 2.0), 0, len(_LUT) - 1).astype(np.int32)]


def rasterize(px, py, inv, tris, W, H, depth=True):
    """Z-buffer of the triangles `tris` (rows of vertex indices) at pixel centres.

    px, py: screen coordinates of the vertices in pixels; inv: their inverse depth (linear on screen).
    Returns the nearest triangle per pixel (-1 where none) and its inverse depth (0 where none); with
    depth=False only a coverage mask. Triangles are grouped by the size of their bounding box and every
    group is evaluated on its box grid at once, without a Python loop over triangles."""
    x, y = px[tris].astype(np.float32), py[tris].astype(np.float32)
    area = (x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0])
    x0 = np.maximum(np.ceil(x.min(1) - 0.5), 0).astype(np.int32)
    x1 = np.minimum(np.floor(x.max(1) - 0.5), W - 1).astype(np.int32)
    y0 = np.maximum(np.ceil(y.min(1) - 0.5), 0).astype(np.int32)
    y1 = np.minimum(np.floor(y.max(1) - 0.5), H - 1).astype(np.int32)
    ok = (x1 >= x0) & (y1 >= y0) & (np.abs(area) > 1e-9)
    nxt, prv = [1, 2, 0], [2, 0, 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        A = (y[:, nxt] - y[:, prv]) / area[:, None]       # barycentric b_i = A_i x + B_i y + C_i
        B = (x[:, prv] - x[:, nxt]) / area[:, None]
        C = (x[:, nxt] * y[:, prv] - x[:, prv] * y[:, nxt]) / area[:, None]
    if depth:
        w = inv[tris].astype(np.float32)
        zA, zB, zC = (A * w).sum(1), (B * w).sum(1), (C * w).sum(1)
        zbuf = np.zeros(W * H, np.float32)
    else:
        mask = np.zeros(W * H, bool)
    # buckets of box sizes rounded up to powers of two (1, 2, 4, 8, … pixels across and down)
    kw = np.ceil(np.log2(np.maximum(x1 - x0 + 1, 1))).astype(np.int32)
    kh = np.ceil(np.log2(np.maximum(y1 - y0 + 1, 1))).astype(np.int32)
    bucket = np.where(ok, kw * 64 + kh, -1)
    found = []
    for k in np.unique(bucket[bucket >= 0]):
        sel = np.nonzero(bucket == k)[0]
        gw, gh = 1 << int(k // 64), 1 << int(k % 64)
        for part in np.array_split(sel, len(sel) * gw * gh // 2_000_000 + 1):
            cx = x0[part, None, None] + np.arange(gw, dtype=np.int32)[None, None, :]
            cy = y0[part, None, None] + np.arange(gh, dtype=np.int32)[None, :, None]
            fx, fy = cx.astype(np.float32) + 0.5, cy.astype(np.float32) + 0.5
            inside = (cx <= x1[part, None, None]) & (cy <= y1[part, None, None])
            for i in range(3):
                inside &= A[part, i, None, None] * fx + B[part, i, None, None] * fy + C[part, i, None, None] >= -1e-6
            pix = (cy * W + cx)[inside]
            if not depth:
                mask[pix] = True
                continue
            z = (zA[part, None, None] * fx + zB[part, None, None] * fy + zC[part, None, None])[inside]
            tri = np.broadcast_to(part[:, None, None], inside.shape)[inside]
            np.maximum.at(zbuf, pix, z)
            found.append((pix, z, tri))
    if not depth:
        return mask.reshape(H, W)
    ids = np.full(W * H, -1, np.int64)
    for pix, z, tri in found:
        win = z >= zbuf[pix]
        ids[pix[win]] = tri[win]
    return ids.reshape(H, W), zbuf.reshape(H, W)


def _camera(V, W, H):
    """Camera position, basis and focal length (pixels) that frame the model in W × H."""
    el = np.radians(ELEVATION)
    fwd = _unit([0, np.cos(el), -np.sin(el)])
    right = _unit(np.cross(fwd, [0, 0, 1]))
    up = np.cross(right, fwd)
    lo, hi = V.min(0), V.max(0)
    target = np.array([0, 0, (hi[2] - lo[2]) * 0.35], np.float32)
    dist = np.linalg.norm(hi - lo) / 2 / np.tan(np.radians(FOV) / 2) * 1.1
    cam = target - fwd * dist
    rel = V - cam
    zc = rel @ fwd
    u, v = (rel @ right) / zc, (rel @ up) / zc
    focal = FILL * min(W / (u.max() - u.min()), H / (v.max() - v.min()))
    off = (W / 2 - focal * (u.max() + u.min()) / 2, H / 2 + focal * (v.max() + v.min()) / 2)
    return cam.astype(np.float32), right, up, fwd, float(focal), off


def _floor_map(V, F, lo, hi, along=None, blur_mm=1.0):
    """A blurred silhouette on the floor (0 … 1) and its origin: the faces projected onto z = 0 along a
    light direction (a shadow) or straight down (`along` None: the footprint)."""
    import cv2
    xy = V[:, :2] if along is None else V[:, :2] - along[:2] * (V[:, 2:3] / along[2])
    lo = np.minimum(lo, xy.min(0)) - 4 * blur_mm
    hi = np.maximum(hi, xy.max(0)) + 4 * blur_mm
    W, H = np.ceil((hi - lo) / SHADOW_MM).astype(int)
    mask = rasterize((xy[:, 0] - lo[0]) / SHADOW_MM, (xy[:, 1] - lo[1]) / SHADOW_MM, None, F, W, H, depth=False)
    return cv2.GaussianBlur(mask.astype(np.float32), (0, 0), blur_mm / SHADOW_MM), lo


def _sample(m, lo, xy):
    """Bilinear lookup of a floor map at floor points xy (… × 2), 0 outside."""
    import cv2
    shape = xy.shape[:-1]
    n = int(np.prod(shape))
    rows = -(-n // 1024)            # OpenCV maps stay below 32767 in both directions
    u = np.zeros(rows * 1024, np.float32)
    v = np.zeros(rows * 1024, np.float32)
    u[:n] = ((xy[..., 0] - lo[0]) / SHADOW_MM).reshape(-1)
    v[:n] = ((xy[..., 1] - lo[1]) / SHADOW_MM).reshape(-1)
    s = cv2.remap(m, u.reshape(rows, 1024), v.reshape(rows, 1024), cv2.INTER_LINEAR,
                  borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return s.reshape(-1)[:n].reshape(shape)


def render_model(V, F, W, H):
    """RGB image (H × W × 3, uint8) of the mesh standing on the studio floor."""
    import cv2
    ss = SUPERSAMPLE
    Ws, Hs = W * ss, H * ss
    V = np.asarray(V, np.float32)
    lo, hi = V.min(0), V.max(0)
    V = V - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]], np.float32)
    yaw = np.radians(YAW)
    V = V @ np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]], np.float32).T
    F = np.asarray(F, np.int64)
    cam, right, up, fwd, focal, (ox, oy) = _camera(V, Ws, Hs)
    rel = V - cam
    zc = rel @ fwd
    px, py = ox + focal * (rel @ right) / zc, oy - focal * (rel @ up) / zc

    tri = V[F]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    front = np.einsum("ij,ij->i", n, cam - tri.mean(1)) > 0
    ids, zbuf = rasterize(px, py, 1 / zc, F[front], Ws, Hs)
    hit = ids >= 0
    key, fill, rim = _unit(KEY), _unit(FILL_LIGHT), _unit(RIM)
    lo2, hi2 = V[:, :2].min(0), V[:, :2].max(0)
    shadow, shadow_lo = _floor_map(V, F, lo2, hi2, along=key, blur_mm=2.4)
    contact, contact_lo = _floor_map(V, F[tri[:, :, 2].max(1) < 0.3], lo2, hi2, blur_mm=1.3)
    span = float((hi2 - lo2).max())

    # the floor, at the output size (it is smooth): key light with the shadow, ambient, a studio falloff
    gx, gy = np.meshgrid((np.arange(W, dtype=np.float32) * ss + ss / 2 - ox) / focal,
                         -(np.arange(H, dtype=np.float32) * ss + ss / 2 - oy) / focal)
    ray = fwd + gx[..., None] * right + gy[..., None] * up
    P = cam + ray * (-cam[2] / np.minimum(ray[..., 2], -1e-6))[..., None]
    r = np.hypot(P[..., 0], P[..., 1]) / (0.75 * span)
    light = ((0.78 * (1 - 0.72 * _sample(shadow, shadow_lo, P[..., :2])) + 0.30)
             * (1 - 0.45 * _sample(contact, contact_lo, P[..., :2])) * (1 - 0.18 * np.clip(r, 0, 2) ** 2 / 2))
    ground = _display(_lin(FLOOR_RGB) * light[..., None]).astype(np.float32)
    img = cv2.resize(ground, (Ws, Hs), interpolation=cv2.INTER_LINEAR)

    # the model, per covered sample
    at = np.flatnonzero(hit)
    if len(at):
        img = img.reshape(-1, 3)
        sx = (at % Ws).astype(np.float32) + 0.5
        sy = (at // Ws).astype(np.float32) + 0.5
        ray = fwd + ((sx - ox) / focal)[:, None] * right - ((sy - oy) / focal)[:, None] * up
        Pm = cam + ray / zbuf.reshape(-1)[at, None]
        normal = _soft_normals(n[front], ids, hit, ss)[at]
        view = _unit(cam - Pm)
        z = np.clip(Pm[:, 2], 0, None)
        ao = (1 - 0.5 * np.exp(-z / 2.2)) * _crease_ao(zbuf, hit, ss).reshape(-1)[at]
        shade = 1 - 0.7 * _sample(shadow, shadow_lo, Pm[:, :2] - key[:2] * (z / key[2])[:, None]) * np.exp(-z / 4)
        dif = (1.0 * np.clip(normal @ key, 0, 1) * shade + 0.20 * np.clip(normal @ fill, 0, 1)
               + 0.30 * np.clip(normal @ rim, 0, 1) ** 2)
        amb = 0.20 * (0.6 + 0.4 * normal[:, 2])
        col = _lin(PLASTIC_RGB) * ((dif * (0.55 + 0.45 * ao) + amb * ao)[:, None])
        half = _unit(key + view)
        nv = np.clip(np.einsum("ij,ij->i", normal, view), 0, 1)
        spec = 0.16 * np.clip(np.einsum("ij,ij->i", normal, half), 0, 1) ** 20 * shade
        col += (spec + 0.08 * (1 - nv) ** 4 * ao)[:, None]
        img[at] = _display(col)
        img = img.reshape(Hs, Ws, 3)
    return np.clip(cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA) + 0.5, 0, 255).astype(np.uint8)


def _soft_normals(n, ids, hit, ss):
    """Face normals per sample, softened over a pixel or so: thin facets do not shimmer, and edges catch
    a little light as on a real print (whose edges are never quite sharp)."""
    import cv2
    img = np.where(hit[..., None], n[np.maximum(ids, 0)], 0).astype(np.float32)
    img = cv2.GaussianBlur(img, (0, 0), 1.3 * ss)
    weight = cv2.GaussianBlur(hit.astype(np.float32), (0, 0), 1.3 * ss)[..., None]
    img = img / np.maximum(weight, 1e-6)
    return (img / (np.linalg.norm(img, axis=-1, keepdims=True) + 1e-9)).reshape(-1, 3)


def _crease_ao(zbuf, hit, ss):
    """Screen-space occlusion: a sample behind its neighbourhood (an inner corner, the inside of the
    cutter) gets darker. Large depth steps (a wall in front of the floor far behind) do not count."""
    import cv2
    depth = np.where(hit, 1 / np.maximum(zbuf, 1e-12), 0).astype(np.float32)
    far = float(depth[hit].max()) if hit.any() else 1.0
    depth = np.where(hit, depth, far)
    ao = np.ones_like(depth)
    near = float(depth[hit].min()) if hit.any() else 0.0
    unit = (far - near) * 0.02 + 1e-6
    for r, k in ((4 * ss, 0.35), (14 * ss, 0.35)):
        diff = (depth - cv2.blur(depth, (2 * r + 1, 2 * r + 1))) / unit
        ao *= 1 - k * np.clip(diff, 0, 1) * (diff < 4)
    return ao
