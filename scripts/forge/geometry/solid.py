"""3D solid (manifold3d) and STL: slices of the profile, writing and checking the mesh."""
import math
import struct

import numpy as np

from ..config import PLA_DENSITY
from ..errors import fail
from .profile import bevel_height


def cross_section(g):
    import manifold3d as m3
    rings = []
    for poly in getattr(g, "geoms", [g]):
        if poly.geom_type != "Polygon" or poly.is_empty:
            continue
        rings.append(np.asarray(poly.exterior.coords[:-1], dtype=np.float64))
        for r in poly.interiors:
            rings.append(np.asarray(r.coords[:-1], dtype=np.float64))
    rings = [r for r in rings if len(r) >= 3]
    if not rings:
        return None
    return m3.CrossSection(rings, fillrule=m3.FillRule.EvenOdd)


def slab(g, z0, z1):
    import manifold3d as m3
    cs = cross_section(g)
    if cs is None or cs.is_empty() or z1 - z0 <= 1e-6:
        return None
    return m3.Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def build_solid(pr):
    import manifold3d as m3
    p, k = pr.p, pr.shape
    body = k.body
    H, FT, FW = p["height"], p["flange_thickness"], p["flange"]
    BH = bevel_height(p)
    parts = []

    def add(m):
        if m is not None and not m.is_empty():
            parts.append(m)

    # flange
    add(slab(body.buffer(FW, join_style="round").difference(body), 0, FT))
    # wall
    add(slab(body.buffer(p["wall"], join_style="round").difference(body), FT, H - BH))
    # bevel up to the cutting edge - steps one layer high
    n = max(1, int(math.ceil(BH / p["step"])))
    for i in range(n):
        z0 = H - BH + i * BH / n
        z1 = H - BH + (i + 1) * BH / n
        zm = (z0 + z1) / 2
        d = p["blade"] + (p["wall"] - p["blade"]) * (H - zm) / BH
        add(slab(body.buffer(d, join_style="round").difference(body), z0, z1))
    # imprint ridges
    if pr.ridges:
        hr = H - p["imprint_drop"]
        taper = 2.0  # height of the ridge taper
        from shapely.ops import unary_union
        G = unary_union(pr.ridges)
        add(slab(G, 0, hr - taper))
        n = max(1, int(math.ceil(taper / p["step"])))
        for i in range(n):
            z0 = hr - taper + i * taper / n
            z1 = hr - taper + (i + 1) * taper / n
            zm = (z0 + z1) / 2
            width = p["imprint_tip"] + (p["imprint_width"] - p["imprint_tip"]) * (hr - zm) / taper
            Gz = G.buffer(-(p["imprint_width"] - width) / 2)
            if Gz.is_empty:
                Gz = G.buffer(-(p["imprint_width"] - p["imprint_tip"]) / 2 * 0.9)
            add(slab(Gz, z0, z1))
    # bridges
    for b in pr.beams:
        add(slab(b, 0, FT))

    solid = m3.Manifold.batch_boolean(parts, m3.OpType.Add)
    if solid.status() != m3.Error.NoError:
        fail(f"manifold: {solid.status()}")
    return solid


def save_stl(solid, path, name):
    mesh = solid.to_mesh()
    V = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    F = np.asarray(mesh.tri_verts, dtype=np.int64)
    tri = V[F]                                   # (n, 3, 3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(ln == 0, 1, ln)
    rec = np.zeros(len(F), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n.astype("<f4"), tri.astype("<f4")
    with open(path, "wb") as f:
        f.write(f"Cookie cutter {name}".encode("utf-8")[:80].ljust(80, b"\0"))
        f.write(struct.pack("<I", len(F)))
        f.write(rec.tobytes())
    return len(F), V, F


def check_stl(path):
    import trimesh
    m = trimesh.load(path, force="mesh")
    return dict(triangles=len(m.faces), watertight=bool(m.is_watertight), winding_consistent=bool(m.is_winding_consistent),
                volume_cm3=float(m.volume) / 1000, pla_mass_g=float(m.volume) / 1000 * PLA_DENSITY,
                extents=[float(x) for x in m.extents], bodies=len(m.split(only_watertight=False)))
