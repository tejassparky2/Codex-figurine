import bpy, numpy as np, zipfile, json,re
from mathutils import Vector
from pathlib import Path
d=Path('/dev/shm/photo-smile')
with zipfile.ZipFile(d/'Man-portrait-smile-220mm.3mf') as z:
 xml=z.read('3D/3dmodel.model'); pal=json.loads(z.read('Metadata/project_settings.config'))['filament_colour']+['#F1ECE1']
v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',xml),'f4')
f=np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',xml),'i4')
slots=np.array(re.findall(rb'paint_color="([^"]+)"',xml))
lab=np.zeros(len(f),'i4')
for k,c in enumerate([b'4',b'8',b'0C',b'1C']):lab[slots==c]=k
lab[(lab==3)&(v[f,2].min(1)>=120)]=4
bpy.ops.wm.read_factory_settings(use_empty=True)
m=bpy.data.meshes.new('U1 mesh');m.vertices.add(len(v));m.vertices.foreach_set('co',(v*.01).ravel());m.loops.add(f.size);m.loops.foreach_set('vertex_index',f.ravel());m.polygons.add(len(f));m.polygons.foreach_set('loop_start',np.arange(0,f.size,3,dtype='i4'));m.update(calc_edges=True)
def material(name,rgb,metal=0):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.59;return mat
for k,h in enumerate(pal):
 c=np.array([int(h[i:i+2],16)/255 for i in (1,3,5)]);m.materials.append(material(h,((c+.055)/1.055)**2.4,.24 if k==2 else 0))
m.polygons.foreach_set('material_index',lab);m.polygons.foreach_set('use_smooth',np.ones(len(f),bool))
sc=bpy.context.scene;obj=bpy.data.objects.new('Man with drink',m);sc.collection.objects.link(obj)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.001));bpy.context.object.data.materials.append(material('Slate',(.61,.54,.46)))
def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(-.9,-6.2,1.66));camera=bpy.context.object;aim(camera,(0,0,1.09));camera.data.type='ORTHO';camera.data.ortho_scale=2.47;sc.camera=camera
for loc,power,size in [((-3,-4,5),440,3),((2,-3,2.5),180,2.2),((1,2,4),560,2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,1))
sc.world=bpy.data.worlds.new('Studio');sc.world.color=(.33,.31,.29)
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-.5;sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=False;sc.render.resolution_x=800;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.render.filepath=str(d/'portrait-smile-hero.png');bpy.ops.render.render(write_still=True)

camera.location=(0,-6,1.54);aim(camera,(0,-.29,1.54));camera.data.ortho_scale=.41;sc.render.resolution_x=700;sc.render.resolution_y=320;sc.render.filepath=str(d/'mouth-front.png');bpy.ops.render.render(write_still=True)
