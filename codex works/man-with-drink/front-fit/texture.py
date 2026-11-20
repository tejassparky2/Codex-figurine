from start import *
import trimesh
from scipy.ndimage import distance_transform_edt
from trimesh.visual.texture import TextureVisuals
from trimesh.visual.material import PBRMaterial
from trimesh.exchange.gltf import load_glb
original_front=render(cam)[1]
new=np.load(D/'fitted.npz')['v']; camera=json.loads((D/'camera.json').read_text())
ids=Raster(new,f).ids(camera,(W,H))
fg=foreground(ref,None,None); near=distance_transform_edt(~fg,return_distances=False,return_indices=True)
tex=ref[near[0],near[1]]
uvmap=np.load(D/'mapping.npz');uv=np.column_stack([uvmap['u']/W,1-uvmap['vv']/H])
seen=np.zeros(len(f),bool);seen[np.unique(ids[ids>=0])]=True
# Include subpixel facets inside a contiguous visible surface if their depth agrees with the z-buffer.
centers=new[f].mean(1); xy=np.mean(uv[f],axis=1)
ix=np.clip((xy[:,0]*W).astype(int),0,W-1);iy=np.clip(((1-xy[:,1])*H).astype(int),0,H-1)
hit=ids[iy,ix]
norm=np.cross(new[f[:,1]]-new[f[:,0]],new[f[:,2]]-new[f[:,0]])
seen|=(hit>=0)&(np.abs(centers[:,1]-centers[hit,1])<0.75)&(norm[:,1]<0)
# A white backdrop along the antialiased edge is extended from the subject.
fg=cv2.erode(fg.astype('uint8'),np.ones((3,3),'uint8')).astype(bool)
near=distance_transform_edt(~fg,return_distances=False,return_indices=True)
tex=ref[tuple(near)]
scene=trimesh.Scene()
mat=PBRMaterial(name='Customer portrait',baseColorTexture=Image.fromarray(tex),metallicFactor=0.,roughnessFactor=1.0)
pos=np.column_stack([new[:,0],new[:,2],-new[:,1]])*.001
def group(name,mask,material,uvs=None):
 ff=f[mask];used,inverse=np.unique(ff.ravel(),return_inverse=True)
 mesh=trimesh.Trimesh(vertices=pos[used],faces=inverse.reshape(-1,3),process=False)
 mesh.visual=TextureVisuals(uv=uvs[used] if uvs is not None else None,material=material)
 scene.add_geometry(mesh,geom_name=name,node_name=name)
group('Approved front',seen,mat,uv)
for k,name in enumerate(['Skin','Clothing and dark details','Hair frames and tumbler','Drink','White details']):
 mask=(~seen)&(l==k)
 if mask.any():group(name,mask,PBRMaterial(name=name,baseColorFactor=[*map(int,pal[k]),255],metallicFactor=0.,roughnessFactor=.9))
file=D/'Man-with-drink-photo-study.glb';file.write_bytes(scene.export(file_type='glb'))
reload=trimesh.load(file,force='scene')
assert sum(len(g.faces) for g in reload.geometry.values())==len(f)
assert abs(reload.extents[1]-.22)<1e-5
# Independent front render uses geometry, UVs, material and image read back from the GLB.
# Orthographic front projection interpolates UVs linearly across projected triangles.
front=np.full((H,W,3),255,'uint8')
allv=[];allf=[];parts=[];off=0
for name,g in reload.geometry.items():
 verts=g.vertices[:,[0,2,1]].copy()*1000;verts[:,1]*=-1
 allv.append(verts);allf.append(g.faces+off);off+=len(verts);parts.append(g)
verts=np.vstack(allv); faces=np.vstack(allf); actual=Raster(verts,faces).ids(camera,(W,H))
offset=0
for g in parts:
 yy,xx=np.where((actual>=offset)&(actual<offset+len(g.faces)))
 tri=g.faces[actual[yy,xx]-offset]; material=g.visual.material
 if material.baseColorTexture is None: front[yy,xx]=material.baseColorFactor[:3]
 else:
  coords=g.vertices[:,[0,1]]*1000
  coords-=((verts.min(0)+verts.max(0))/2)[[0,2]]
  coords*=np.array([camera['s'],-camera['s']]);coords+=[camera['tx'],camera['ty']]
  a,b,c=coords[tri].transpose(1,0,2);p=np.c_[xx+.5,yy+.5]-a
  ba=b-a;ca=c-a
  det=ba[:,0]*ca[:,1]-ba[:,1]*ca[:,0]
  wb=(p[:,0]*ca[:,1]-p[:,1]*ca[:,0])/det;wc=(ba[:,0]*p[:,1]-ba[:,1]*p[:,0])/det
  u,vv,w=g.visual.uv[tri].transpose(1,0,2)
  points=u+(vv-u)*wb[:,None]+(w-u)*wc[:,None]
  data=np.array(material.baseColorTexture.convert('RGB'))
  front[yy,xx]=data[np.clip(((1-points[:,1])*H).astype(int),0,H-1),np.clip((points[:,0]*W).astype(int),0,W-1)]
 offset+=len(g.faces)
Image.fromarray(front).save(D/'front.png')
can=Image.new('RGB',(855,670),'white')
for i,(name,im) in enumerate([('Customer portrait',ref),('Original, four-head materials',original_front),('Photo-textured 3D study',front)]):
 can.paste(Image.fromarray(im).resize((285,640),Image.Resampling.LANCZOS),(285*i,25));ImageDraw.Draw(can).text((285*i+8,6),name,fill='black')
can.save(D/'comparison.jpg',quality=94)
print('Reopened GLB:',len(f),'triangles,',seen.sum(),'front-textured, dimensions (m)',reload.extents,'bytes',file.stat().st_size)
