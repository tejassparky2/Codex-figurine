from render import *
from scipy.spatial import cKDTree
import re,zipfile
g=trimesh.load('source.glb',force='mesh',process=False);print('bounds',g.bounds, m.bounds,len(g.faces),flush=True)
with zipfile.ZipFile('Wedding-150mm-material-locked-finish.3mf') as zz:s=zz.read('3D/3dmodel.model')
vv=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>',s),'f4')
ff=np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',s),'i4')
print('f',len(ff),flush=True)
uv=g.visual.uv[g.faces].mean(1);tex=np.asarray(g.visual.material.baseColorTexture.convert('RGB'));H,W=tex.shape[:2];rgb=tex[np.clip(((1-uv[:,1])*H).astype(int),0,H-1),np.clip((uv[:,0]*W).astype(int),0,W-1)]
_,ix=cKDTree(vv[ff].mean(1)).query(c,workers=4);rgb=rgb[ix];np.save(D/'rgb',rgb)
for i in [0,4]:
 j=np.load(D/f'id{i}.npy');Image.fromarray(np.vstack([rgb,[211,215,219]]).astype('u1')[j]).resize((600,900)).save(D/f'raw{i}.jpg')
