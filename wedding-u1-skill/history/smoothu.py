from pathlib import Path
import trimesh
from scipy.sparse import coo_matrix
exec(Path('/tmp/afterpreview.py').read_text().split('coords=v[f]')[0])
v=(v*1.25).astype('f8')
# Include boundaries visible either before or after hand painting.
with zipfile.ZipFile('Wedding-U1-150mm-gaze-corrected.3mf') as zz:
 orig=np.fromiter((codes[m[1]] for m in re.finditer(rb'paint_color="(\w+)"',s)),dtype='u1')
m=trimesh.Trimesh(v,f,process=False);a,b=m.face_adjacency.T
ed=m.face_adjacency_edges[(l[a]!=l[b])|(orig[a]!=orig[b])]
idx=np.unique(ed); near=f[np.isin(f,idx).any(axis=1)]
idx=np.unique(near); n=len(idx);loc=np.searchsorted(idx,near)
e=np.searchsorted(idx,ed)
def adj(edges):
 a,b=edges.T
 mat=coo_matrix((np.ones(len(a)*2),(np.r_[a,b],np.r_[b,a])),shape=(n,n)).tocsr()
 mat.data[:]=1
 return mat
B=adj(e); A=adj(np.vstack([loc[:,[0,1]],loc[:,[1,2]],loc[:,[2,0]]]))
bd=B.getnnz(1);deg=A.getnnz(1);norm=m.vertex_normals[idx];base=v[idx].copy();cur=base.copy()
testmask=np.isin(f,idx).any(1); affected=f[testmask]
def crosses(vv):
 q=vv[affected];return np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0])
ref=crosses(v);area=(ref*ref).sum(1)
def rough(u):
 d=B@u/np.maximum(1,bd[:,None])-u
 return np.linalg.norm(d[bd==2],axis=1).mean()
print('before',rough(cur),flush=True)
for k in range(24):
 delta=B@cur/np.maximum(1,bd[:,None])-cur
 interior=bd==0
 delta[interior]=(A@(cur-base)/deg[:,None]-(cur-base))[interior]*.65
 delta[bd>2]=0
 delta-=norm*(delta*norm).sum(1)[:,None]
 step=cur+.45*delta-base
 step*=np.minimum(1,.28/np.maximum(1e-9,np.linalg.norm(step,axis=1)))[:,None]
 nxt=base+step
 fixed=(base[:,2]<.3)|(base[:,2]>149.7)|(np.abs(base[:,2]-36)<.4)|(np.abs(base[:,2]-76)<.4);nxt[fixed]=base[fixed]
 for _ in range(20):
  v[idx]=nxt;bad=((crosses(v)*ref).sum(1)<.17*area)&(area>1e-20)
  if not bad.any():break
  touched=np.intersect1d(idx,affected[bad]);ii=np.searchsorted(idx,touched);nxt[ii]=cur[ii]
 else:nxt=cur.copy()
 cur=nxt.copy()
v[idx]=cur
print('after',rough(cur),'max move',np.linalg.norm(cur-base,axis=1).max(),flush=True)
with zipfile.ZipFile('Wedding-U1-150mm-gaze-corrected.3mf') as zz,zipfile.ZipFile('Wedding-U1-150mm-smooth.3mf','w',zipfile.ZIP_DEFLATED) as out:
 for name in zz.namelist():
  if name!='3D/3dmodel.model':out.writestr(name,zz.read(name));continue
  with out.open(name,'w') as fp:
   fp.write(s[:s.index(b'<vertices>')]+b'<vertices>')
   for j in range(0,len(v),40000):fp.write(''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x,y,z in v[j:j+40000]).encode())
   fp.write(s[s.index(b'</vertices>'):])
