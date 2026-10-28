#!/usr/bin/env python3
"""Escena 3D procedural vertical para HEC REELS, sin modelos ni APIs externos.

Renderiza 72 PNG en Cycles CPU. El workflow repite el clip y une
el audio generado por Piper; la escena 3D es demostrativa.
"""
import math
import os
from pathlib import Path
import bpy
from mathutils import Vector

out = Path(os.getenv("HEC_3D_FRAMES", "output/3d_frames"))
out.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 8
sc.render.resolution_x = 360
sc.render.resolution_y = 640
sc.render.resolution_percentage = 100
sc.render.fps = 12
sc.frame_start = 1
sc.frame_end = 72
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.render.filepath = str(out.resolve()) + "/"
sc.render.film_transparent = False
if os.getenv("HEC_3D_TEST") == "1":
    sc.render.resolution_x = 120
    sc.render.resolution_y = 214
    sc.cycles.samples = 2
    sc.frame_end = 2


world = sc.world or bpy.data.worlds.new("Azul nocturno")
sc.world = world
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (.007, .015, .034, 1)
background.inputs["Strength"].default_value = .6

def mat(name, rgba, metallic=0.0, emission=0.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = rgba
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = rgba
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = .5
    if emission:
        if shader.inputs.get("Emission Color"):
            shader.inputs["Emission Color"].default_value = rgba
        if shader.inputs.get("Emission Strength"):
            shader.inputs["Emission Strength"].default_value = emission
    return material

navy = mat("azul acero", (.025, .06, .12, 1), .35)
black = mat("negro camiseta", (.01, .012, .025, 1))
skin = mat("piel canela", (.45, .24, .15, 1))
cyan = mat("neon turquesa", (.04, .85, .9, 1), .2, 1.2)
orange = mat("naranja", (1, .35, .05, 1), .2, .7)
white = mat("letras", (.86, .96, 1, 1), 0, .5)

def sphere(name, position, size, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.data.materials.append(material)
    return obj

def cube(name, position, size, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    obj.data.materials.append(material)
    return obj

def cylinder(name, position, radius, depth, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

cylinder("base", (0, 0, -.15), 3.4, .25, navy)
avatar = bpy.data.objects.new("HecAgus pivot", None)
sc.collection.objects.link(avatar)
figure = [
    sphere("camiseta negra", (-1.1, 0, 1.55), (.68, .5, .79), black),
    sphere("cabeza", (-1.1, -.04, 2.70), (.51, .49, .59), skin),
    sphere("cabello", (-1.1, .045, 3.05), (.52, .48, .23), black),
    sphere("ojo izquierdo", (-1.28, -.49, 2.77), (.057, .052, .067), black),
    sphere("ojo derecho", (-.92, -.49, 2.77), (.057, .052, .067), black),
    sphere("brazo izquierdo", (-1.84, 0, 1.65), (.21, .26, .57), black),
    sphere("brazo derecho", (-.39, 0, 1.65), (.21, .26, .57), black),
    cube("pierna izquierda", (-1.35, .03, .52), (.3, .38, 1.0), black),
    cube("pierna derecha", (-.87, .03, .52), (.3, .38, 1.0), black),
    cube("detalle camiseta", (-1.1, -.51, 1.65), (.47, .04, .08), cyan),
]
# Parent the meshes while retaining their world transforms.
bpy.context.view_layer.update()
for obj in figure:
    world_transform = obj.matrix_world.copy()
    obj.parent = avatar
    obj.matrix_world = world_transform

rotator = bpy.data.objects.new("Cubo animado pivot", None)
sc.collection.objects.link(rotator)
rotator.location = (1.16, 0, 2.15)
box = cube("Cubo físico", (1.16, 0, 2.15), (1.2, 1.2, 1.2), navy)
edge = cube("Aristas geométricas", (1.16, 0, 2.15), (1.4, 1.4, 1.4), cyan)
mod = edge.modifiers.new("Wireframe", "WIREFRAME")
mod.thickness = .04
center = sphere("Centro naranja", (1.16, 0, 2.15), (.30, .30, .30), orange)
bpy.context.view_layer.update()
for obj in [box, edge, center]:
    w = obj.matrix_world.copy()
    obj.parent = rotator
    obj.matrix_world = w

for f, angle in [(1, 0), (72, math.pi * 4)]:
    rotator.rotation_euler = (angle * .2, angle * .65, angle)
    rotator.keyframe_insert(data_path="rotation_euler", frame=f)
for f, z in [(1, 0), (36, .1), (72, 0)]:
    avatar.location.z = z
    avatar.keyframe_insert(data_path="location", frame=f)

bpy.ops.object.text_add(location=(0, 0, 4.25), rotation=(math.pi/2, 0, 0))
title = bpy.context.object
title.name = "Texto 3D HEC REELS"
title.data.body = "HEC REELS"
title.data.align_x = "CENTER"
title.data.size = .58
title.data.extrude = .028
title.data.materials.append(white)

bpy.ops.object.camera_add(location=(0, -12.5, 4.8))
camera = bpy.context.object
sc.camera = camera
camera.data.type = "ORTHO"
camera.data.ortho_scale = 7.0
aim = Vector((0, 0, 2.1))
camera.rotation_euler = (aim - camera.location).to_track_quat("-Z", "Y").to_euler()
for frame, x in [(1, -.15), (72, .15)]:
    camera.location.x = x
    camera.keyframe_insert(data_path="location", frame=frame)

for name, point, power, color in [
    ("frontal", (-3, -4, 7), 1000, (1, .96, .90)),
    ("neón", (3, 1, 5), 700, (.2, .9, 1)),
]:
    bpy.ops.object.light_add(type="AREA", location=point)
    light = bpy.context.object
    light.name = name
    light.data.energy = power
    light.data.color = color
    light.data.shape = "DISK"
    light.data.size = 5
    light.rotation_euler = (Vector((0, 0, 2)) - light.location).to_track_quat("-Z", "Y").to_euler()

sc.frame_set(1)
print("RENDER 3D:", out, sc.frame_end, "fotogramas")
bpy.ops.render.render(animation=True)
