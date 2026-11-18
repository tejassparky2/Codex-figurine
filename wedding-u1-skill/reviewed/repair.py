from pathlib import Path
import numpy as np,zipfile,re,json,trimesh,moderngl as gl
from PIL import Image,ImageDraw
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
def read(name):
 with zipfile.ZipFile(name) as z:
  xml=z.read('3D/3dmodel.model');pal=json.loads(z.read('Metadata/project_settings.config'))['filament_colour']
 labels=np.fromiter((codes[m[1]] for m in re.finditer(rb'paint_color="(\w+)"',xml)),dtype='u1')
 return xml,pal,labels
codes={b:i for i,b in enumerate([b'4',b'8',b'0C',b'1C',b'2C',b'3C',b'4C',b'5C'])}
src='Wedding-150mm-material-locked-finish.3mf'
s,pal,l=read(src)
v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>',s),'f4')
f=np.asarray(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',s),'i4')
from scipy.spatial import cKDTree
import pymeshlab as ml
from pymeshfix import _meshfix
m=trimesh.Trimesh(v,f,process=False);c=m.triangles_center;a,b=m.face_adjacency.T
# Mark interior faces only for simplification, so eye, lip and material contours stay dense.
rim=np.zeros(len(f),bool);cut=l[a]!=l[b];rim[a[cut]]=rim[b[cut]]=True
for _ in range(2):bad=rim[a]|rim[b];rim[a[bad]]=rim[b[bad]]=True
ms=ml.MeshSet();ms.add_mesh(ml.Mesh(vertex_matrix=v.astype(float),face_matrix=f,f_scalar_array=(~rim).astype(float)))
ms.compute_selection_by_condition_per_face(condselect='fq > 0.5')
print('selected',ms.current_mesh().selected_face_number(),flush=True)
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=650000,selected=True,preservetopology=True,preservenormal=True,optimalplacement=True)
mesh=ms.current_mesh();V=mesh.vertex_matrix();F=mesh.face_matrix()
print('simplified',len(F),flush=True)
fix=_meshfix.PyTMesh();fix.set_quiet(True);fix.load_array(V,F);fix.fix_connectivity();fix.remove_smallest_components();fix.fill_small_boundaries();fix.clean(max_iters=8);V,F=fix.return_arrays()
V=np.round(V,6);new=trimesh.Trimesh(V,F,process=True,validate=True)
print('repaired',len(new.faces),new.is_volume,new.is_watertight,new.is_winding_consistent,new.body_count,flush=True)
assert new.is_volume and new.is_watertight and new.is_winding_consistent and new.body_count==1 and len(new.faces)<1000000
V=new.vertices;F=new.faces;c2=new.triangles_center
d,ix=cKDTree(c).query(c2,k=6,workers=4);dot=np.einsum('ijk,ik->ij',m.face_normals[ix],new.face_normals);best=ix[np.arange(len(ix)),np.argmin(d+.28*(1-dot),axis=1)]
labels=l[best].copy()
# Fix the bride's upper rear flower strand and the tip of the groom's cuff.
x=216+c2[:,0]*4.608/1.25;y=564.48-c2[:,2]*4.608/1.25
flower=( ((x>148)&(x<203)&(y>287)&(y<313))|((x>204)&(x<246)&(y>405)&(y<422)) )&(labels==4)
# Nearby red/ivory seeds on the same sculpt surface classify the remaining neck/hand flecks.
nearwhite=cKDTree(c2[labels==2]).query(c2[flower],workers=4)[0]
idx=np.where(flower)[0];labels[idx[nearwhite<1.4]]=2
_,up,prior=read('Wedding-U1-150mm-material-locked.3mf')
u=prior[best].copy();u[labels!=l[best]]=2
np.savez('repaired-u1.npz',v=V,f=F,l=labels,u=u)
