"""Blender scene for the README gallery: one row per drawing, with the drawing on a sheet of
paper, its outline-only cutter and its imprint cutter, in the same studio as the cutter that ends
examples/showcase.webp.

Run by render_gallery.py, not by hand:
blender -b --factory-startup -P gallery_scene.py -- <job.json>

The job lists the rows (drawing, where the ink sits in it, the two STLs), the render width and
the output paths. Meshes are imported as they are: 1 mm = 0.01 scene units, flange down.
"""
import json
import math
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

PLASTIC = "D0601C"   # the orange PLA of the hero cutter
STUDIO = "E6D8C2"    # floor and backdrop
PAPER = "FFFFFF"
GAP = 0.34           # floor between neighbouring columns and rows
MARGIN = 0.25        # floor left around the objects
# Each sheet lies a little differently: turn in degrees, the corner that curls up, how much.
SHEETS = ((-3.0, (1, 1), 1.3), (2.5, (-1, 1), 1.0))
ELEVATION = 52       # camera, degrees above the floor: high enough to see the ridges inside
LENS, SENSOR = 110, 36


def srgb(code):
    channels = [int(code[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)


def material(name, color, roughness, subsurface=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*srgb(color), 1)
    shader.inputs["Roughness"].default_value = roughness
    if subsurface:
        shader.inputs["Subsurface Weight"].default_value = subsurface
        shader.inputs["Subsurface Radius"].default_value = (0.3, 0.12, 0.06)
        shader.inputs["Subsurface Scale"].default_value = 0.02
    return mat


def add_cutter(path, plastic):
    """The STL as built, standing on its flange, centered on its bounding box."""
    bpy.ops.wm.stl_import(filepath=path)
    cutter = bpy.context.selected_objects[0]
    cutter.scale = (0.01, 0.01, 0.01)
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    cutter.location = (0, 0, 0)
    bpy.context.view_layer.update()
    cutter.location.z -= min((cutter.matrix_world @ Vector(c)).z for c in cutter.bound_box)
    cutter.data.materials.append(plastic)
    for polygon in cutter.data.polygons:
        polygon.use_smooth = False
    return cutter


def add_paper(row, turn, corner, curl):
    """The drawing at the cutters' scale on a sheet with a margin, a little askew, one far
    corner lifting off the floor."""
    width, height = row["image_size"]
    left, top, right, bottom = row["drawing_box"]
    unit = row["cookie_mm"] * 0.01 / max(right - left, bottom - top)   # scene units per pixel
    margin = 0.11
    sheet_w = (right - left) * unit + 2 * margin
    sheet_h = (bottom - top) * unit + 2 * margin
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=48, y_subdivisions=48, size=1)
    paper = bpy.context.active_object
    # UVs reach past the image by the margin; outside it the texture is clipped to plain paper.
    for loop in paper.data.loops:
        co = paper.data.vertices[loop.vertex_index].co
        paper.data.uv_layers.active.data[loop.index].uv = (
            ((left + right) / 2 + co.x * sheet_w / unit) / width,
            1 - ((top + bottom) / 2 - co.y * sheet_h / unit) / height)
    for vertex in paper.data.vertices:
        vertex.co.x *= sheet_w
        vertex.co.y *= sheet_h
        # The corner curls up: height grows with the square of the distance past a diagonal
        # fold line.
        past = corner[0] * vertex.co.x / sheet_w + corner[1] * vertex.co.y / sheet_h - 0.62
        vertex.co.z = 0.004 + (curl * past ** 2 if past > 0 else 0)
    for polygon in paper.data.polygons:
        polygon.use_smooth = True
    paper.rotation_euler.z = math.radians(turn)
    solid = paper.modifiers.new("thickness", "SOLIDIFY")
    solid.thickness = 0.004

    mat = material("paper", PAPER, 0.8)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.15
    image = nodes.new("ShaderNodeTexImage")
    image.image = bpy.data.images.load(row["drawing"])
    image.extension = "CLIP"
    image.interpolation = "Cubic"
    # Ink: the darker the pixel, the more ink over the paper color.
    luminance = nodes.new("ShaderNodeRGBToBW")
    ink = nodes.new("ShaderNodeMath")
    ink.operation = "MULTIPLY"
    invert = nodes.new("ShaderNodeMath")
    invert.operation = "SUBTRACT"
    invert.inputs[0].default_value = 1
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*srgb(PAPER), 1)
    mix.inputs["B"].default_value = (*srgb("141312"), 1)
    links.new(image.outputs["Color"], luminance.inputs["Color"])
    links.new(luminance.outputs["Val"], invert.inputs[1])
    links.new(invert.outputs["Value"], ink.inputs[0])
    links.new(image.outputs["Alpha"], ink.inputs[1])
    links.new(ink.outputs["Value"], mix.inputs["Factor"])
    links.new(mix.outputs["Result"], nodes["Principled BSDF"].inputs["Base Color"])
    paper.data.materials.append(mat)
    return paper


def add_light(scene, name, location, size, energy, color=(1, 1, 1)):
    light = bpy.data.lights.new(name, "AREA")
    light.size, light.energy, light.color = size, energy, color
    lamp = bpy.data.objects.new(name, light)
    scene.collection.objects.link(lamp)
    lamp.location = location
    aim = Vector((0, 0, 0.1)) - Vector(location)
    lamp.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()


def main():
    with open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8") as handle:
        job = json.load(handle)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    plastic = material("pla", PLASTIC, 0.32, subsurface=0.08)
    rows = [[add_paper(row, *SHEETS[index % len(SHEETS)]),
             add_cutter(row["outline_stl"], plastic), add_cutter(row["imprint_stl"], plastic)]
            for index, row in enumerate(job["rows"])]
    # A grid with the same floor between neighbours: each column as wide as its widest object,
    # each row as deep as its deepest; the first row is the farthest.
    bpy.context.view_layer.update()
    widths = [max(row[column].dimensions.x for row in rows) for column in range(3)]
    depths = [max(obj.dimensions.y for obj in row) for row in rows]
    columns, x = [], -(sum(widths) + GAP * 2) / 2
    for width in widths:
        columns.append(x + width / 2)
        x += width + GAP
    y = (sum(depths) + GAP * (len(rows) - 1)) / 2
    for row, depth in zip(rows, depths):
        for obj, column in zip(row, columns):
            obj.location.x, obj.location.y = column, y - depth / 2
        y -= depth + GAP

    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(material("floor", STUDIO, 0.9))
    world = scene.world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (*srgb(STUDIO), 1)
    background.inputs["Strength"].default_value = 0.35

    # The hero's three lights, moved out and enlarged by `reach` so one rig covers the whole grid
    # with the same shadow softness; energy grows with the square of the distance.
    reach = 1.9
    for name, location, size, energy, color in (
            ("key", (-1.8, -1.5, 2.6), 1.6, 330, (1.0, 0.96, 0.9)),
            ("fill", (2.4, -1.4, 1.4), 2.5, 70, (0.9, 0.95, 1.0)),
            ("rim", (0.6, 2.4, 1.6), 1.2, 220, (1, 1, 1))):
        add_light(scene, name, tuple(c * reach for c in location), size * reach,
                  energy * reach ** 2, color)

    camera_data = bpy.data.cameras.new("camera")
    camera_data.lens, camera_data.sensor_width = LENS, SENSOR
    camera = bpy.data.objects.new("camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    # Looking down at ELEVATION. Frame the grid with MARGIN of floor around it: aim at the middle
    # of what the lens sees, step back until it fits the width, and make the picture as tall as
    # it needs. Near objects look larger, so a few rounds settle it.
    elevation = math.radians(ELEVATION)
    toward = Vector((0, math.cos(elevation), -math.sin(elevation)))
    right, up = Vector((1, 0, 0)), Vector((0, math.sin(elevation), math.cos(elevation)))
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ Vector(corner) for row in rows for obj in row[1:]
              for corner in obj.bound_box]
    points += [row[0].matrix_world @ vertex.co for row in rows for vertex in row[0].data.vertices]
    half_view = SENSOR / 2 / LENS
    position = -toward * 12
    for _ in range(6):
        seen = [(point - position) for point in points]
        xs = [v.dot(right) / v.dot(toward) for v in seen]
        ys = [v.dot(up) / v.dot(toward) for v in seen]
        distance = -position.dot(toward)
        edge = MARGIN / distance
        position += (right * (min(xs) + max(xs)) / 2 + up * (min(ys) + max(ys)) / 2) * distance
        position -= toward * distance * ((max(xs) - min(xs)) / 2 + edge - half_view) / half_view
    camera.location = position
    camera.rotation_euler = toward.to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = job["width"]
    scene.render.resolution_y = round(job["width"] * (max(ys) - min(ys) + 2 * edge) / (2 * half_view))
    scene.render.resolution_percentage = 100

    scene.render.engine = "CYCLES"
    preferences = bpy.context.preferences.addons["cycles"].preferences
    for device in ("OPTIX", "CUDA", "METAL", "HIP", "ONEAPI"):
        try:
            preferences.compute_device_type = device
            preferences.get_devices()
            for found in preferences.devices:
                found.use = True
            scene.cycles.device = "GPU"
            break
        except Exception:      # this backend is not on the machine: try the next, or stay on CPU
            continue
    scene.cycles.samples = job["samples"]
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = job["render"]
    bpy.ops.render.render(write_still=True)

    # Where each column lands across the picture (0..1), so the labels can sit under it.
    bpy.context.view_layer.update()
    anchors = [world_to_camera_view(scene, camera, Vector((column, 0, 0))).x for column in columns]
    with open(job["anchors"], "w", encoding="utf-8") as handle:
        json.dump(anchors, handle)


main()
