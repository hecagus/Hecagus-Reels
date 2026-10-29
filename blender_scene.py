#!/usr/bin/env python3
"""HEC REELS: objetos 3D procedurales según el director de escenas.

No usa servicios externos ni ejecuta instrucciones del usuario. Cada escena
se renderiza por separado y luego se compone con la duración real de Piper.
"""
import json
import math
import os
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(os.getenv("HEC_3D_FRAMES","output/3d_frames"))
TEST=os.getenv("HEC_3D_TEST")=="1"
PLAN=os.getenv("HEC_3D_PLAN")
ALLOWED={"payment","network","food","motorcycle","cloud","generic"}
LABELS={
  "payment":"PAGO CON TARJETA","network":"REDES Y CONEXIONES",
  "food":"COMIDA Y COCINA","motorcycle":"MOTOCICLETA",
  "cloud":"SERVICIOS EN NUBE","generic":"HEC REELS 3D"
}
if PLAN:
    data=json.loads(Path(PLAN).read_text(encoding="utf-8"))
    shots=data["scenes"]
    if not 1<=len(shots)<=12 or any(
      not isinstance(s,dict) or
      s.get("kind") not in ALLOWED or
      s.get("index")!=i+1 or
      not isinstance(s.get("duration"),(int,float)) or
      not 0.1<=s["duration"]<=180
      for i,s in enumerate(shots)):
        raise ValueError("Plan 3D inválido.")
else:
    shots=[{"index":1,"kind":"generic","duration":2.0}]
if TEST: shots=shots[:2]
ROOT.mkdir(parents=True,exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine="CYCLES"
sc.cycles.device="CPU"
sc.cycles.samples=2 if TEST else 4
sc.render.resolution_x=120 if TEST else 360
sc.render.resolution_y=214 if TEST else 640
sc.render.resolution_percentage=100
sc.render.fps=12
sc.frame_start=1
sc.frame_end=2 if TEST else 12
sc.render.image_settings.file_format="PNG"
sc.render.image_settings.color_mode="RGB"
for layer in sc.view_layers:
    if hasattr(layer,"cycles"):
        layer.cycles.use_denoising=False
if hasattr(sc.cycles,"use_denoising"): sc.cycles.use_denoising=False
world=sc.world or bpy.data.worlds.new("Fondo HEC")
sc.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.008,.016,.038,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.7

def material(name,c,metal=0,glow=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*c,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*c,1)
    p.inputs["Metallic"].default_value=metal
    p.inputs["Roughness"].default_value=.48
    if glow and p.inputs.get("Emission Color"):
        p.inputs["Emission Color"].default_value=(*c,1)
        p.inputs["Emission Strength"].default_value=glow
    return m

dark=material("Acero azul",(.025,.09,.15),.5)
black=material("Negro",(.015,.018,.025),.2)
cyan=material("Turquesa",(.06,.82,.86),.1,.8)
amber=material("Naranja",(.96,.38,.06),.25,.5)
white=material("Blanco",(.86,.96,.99),.1,.2)
skin=material("Piel canela",(.41,.25,.18))
green=material("Verde",(.12,.75,.44),.1,.7)
red=material("Rojo",(.78,.12,.15))
materials={"dark":dark,"black":black,"cyan":cyan,"amber":amber,"white":white,"skin":skin,"green":green,"red":red}
temporary=[]

def register(obj,name,mat):
    obj.name=name
    if mat:obj.data.materials.append(mat)
    temporary.append(obj)
    return obj

def box(name,loc,dimensions,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=register(bpy.context.object,name,mat)
    ob.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return ob

def ball(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,location=loc)
    ob=register(bpy.context.object,name,mat)
    ob.scale=scale
    return ob

def cyl(name,loc,radius,depth,mat,rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=depth,location=loc)
    ob=register(bpy.context.object,name,mat)
    if rotation:ob.rotation_euler=rotation
    return ob

def label(text,loc=(0,-.35,4.28),size=.39,mat=white):
    bpy.ops.object.text_add(location=loc,rotation=(math.pi/2,0,0))
    ob=register(bpy.context.object,"Texto "+text,mat)
    ob.data.body=text
    ob.data.align_x="CENTER"
    ob.data.size=size
    ob.data.extrude=.015
    return ob

def link(a,b,radius,mat,name="conexion"):
    delta=Vector(b)-Vector(a)
    mid=(Vector(a)+Vector(b))*.5
    ob=cyl(name,mid,radius,delta.length,mat)
    ob.rotation_euler=delta.to_track_quat("Z","Y").to_euler()
    return ob

def payment():
    # Terminal POS con pantalla, lector y tarjeta separada.
    box("terminal",(0,0,2.0),(2.1,.55,2.5),dark)
    box("pantalla",(0,-.30,2.5),(1.55,.08,.72),cyan)
    for row in range(3):
        for col in range(3):
            box("tecla",(-.53+col*.53,-.34,1.82-row*.28),(.28,.09,.17),white)
    box("tarjeta",(1.9,-.6,2.2),(1.15,.07,.72),amber)
    box("chip",(1.65,-.68,2.27),(.24,.02,.2),white)

def network():
    pts=[(-1.75,0,2.2),(0,0,3.05),(1.75,0,2.2),
         (-.8,0,1.25),(.8,0,1.25)]
    for a,b in [(0,1),(1,2),(0,3),(3,4),(4,2),(1,4)]:
        link(pts[a],pts[b],.06,cyan)
    for n,p in enumerate(pts):
        ball("nodo "+str(n),p,(.35,.35,.35),amber if n==1 else white)

def food():
    cyl("plato",(0,0,1.15),2.1,.13,white)
    cyl("base",(0,0,1.28),1.55,.18,dark)
    for i in range(10):
        a=i*2*math.pi/10
        ball("ingrediente",(1.0*math.cos(a),.8*math.sin(a),1.54),(.32,.26,.20),green if i%3==0 else amber)
    for i in range(6):
        a=i*2*math.pi/6
        cyl("pasta",(.45*math.cos(a),.45*math.sin(a),1.65),.13,.55,amber,rotation=(.4,0,a))

def motorcycle():
    for x in (-1.35,1.35):
        cyl("rueda",(x,0,1.02),.77,.38,black,(math.pi/2,0,0))
        cyl("eje",(x,-.23,1.02),.38,.04,cyan,(math.pi/2,0,0))
    link((-1.35,0,1.02),(.1,0,2.15),.12,amber)
    link((.1,0,2.15),(1.35,0,1.02),.12,amber)
    link((-1.35,0,1.02),(.55,0,1.12),.12,amber)
    box("tanque",(-.1,-.2,2.24),(1.25,.66,.52),red)
    box("asiento",(-.9,-.2,2.6),(1.0,.6,.18),black)
    link((1.35,0,1.02),(1.5,0,2.65),.08,cyan)
    link((1.1,0,2.65),(2,0,2.65),.07,white)

def cloud():
    for x,y,z,r in [(-.9,0,2.35,.72),(0,0,2.8,.9),(.9,0,2.4,.8),(0,0,2.1,.8)]:
        ball("nube",(x,y,z),(r,r*.7,r*.8),white)
    for x in (-1.5,0,1.5):
        box("servidor",(x,-.2,.95),(1.0,.60,1.15),dark)
        for row in range(3):
            box("LED",(x-.23,-.55,.6+row*.32),(.13,.08,.09),green)
    for x in (-1.5,0,1.5):
        link((x,0,1.5),(x*.5,0,2.05),.036,cyan)

def generic():
    box("concepto",(0,0,2.0),(1.7,1.7,1.7),dark)
    frame=box("aristas",(0,0,2.0),(1.95,1.95,1.95),cyan)
    frame.modifiers.new("malla","WIREFRAME").thickness=.04
    ball("centro",(0,-1,2.0),(.40,.40,.40),amber)

BUILDERS={
    "payment":payment,"network":network,"food":food,
    "motorcycle":motorcycle,"cloud":cloud,"generic":generic,
}

# Fixed world floor and studio lights are shared across every shot.
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=3.15,depth=.20,location=(0,0,-.10))
bpy.context.object.name="Tarima"
bpy.context.object.data.materials.append(dark)
bpy.ops.object.camera_add(location=(0,-12.7,4.55))
camera=bpy.context.object
sc.camera=camera
camera.data.type="ORTHO"
camera.data.ortho_scale=7.4
camera.rotation_euler=(Vector((0,0,2.1))-camera.location).to_track_quat("-Z","Y").to_euler()
for place,power,rgb in [((-3,-4,7),1300,(1,.94,.84)),((3,1,6),850,(.2,.9,1))]:
    bpy.ops.object.light_add(type="AREA",location=place)
    lamp=bpy.context.object
    lamp.data.energy=power
    lamp.data.color=rgb
    lamp.data.shape="DISK"
    lamp.data.size=5
    lamp.rotation_euler=(Vector((0,0,2))-lamp.location).to_track_quat("-Z","Y").to_euler()

for shot in shots:
    kind=shot["kind"]
    label(LABELS[kind])
    label("ESCENA %02d"%shot["index"],loc=(0,-.3,3.77),size=.18,mat=cyan)
    BUILDERS[kind]()
    # Real camera motion; visible geometry is different for each category.
    for f,x in [(1,-.12),(sc.frame_end,.12)]:
        camera.location.x=x
        camera.keyframe_insert(data_path="location",frame=f)
    folder=ROOT/("scene_%02d"%shot["index"])
    folder.mkdir(parents=True,exist_ok=True)
    sc.render.filepath=str(folder.resolve())+"/"
    sc.frame_set(1)
    print("RENDER 3D",shot["index"],kind,str(folder),flush=True)
    bpy.ops.render.render(animation=True)
    for obj in temporary:
        bpy.data.objects.remove(obj,do_unlink=True)
    temporary.clear()
