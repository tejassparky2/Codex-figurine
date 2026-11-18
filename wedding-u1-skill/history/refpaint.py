import sys,zipfile,re,json
import numpy as np,trimesh
from scipy.spatial import cKDTree
from pathlib import Path
sys.path.insert(0,'/workspace/figurine-colorize/scripts')
from render_3mf import load_colored_3mf
src=trimesh.load('source.glb',force='mesh',process=False)
v=src.vertices.copy();v-=src.bounds.mean(0);v*=120/src.extents[1];v=np.stack([v[:,0],-v[:,2],v[:,1]+60],1)
f=src.faces; cen=v[f].mean(1);x=216+cen[:,0]*4.608;y=288-(cen[:,2]-60)*4.608
old,c,pal=load_colored_3mf(Path('wedding.3mf'));tree=cKDTree(old.triangles_center);labels=tree.query(cen,workers=4)[1];lab=np.argmin(abs(c-pal[0]).sum(1)) if False else np.zeros(len(c),'u1')
for i,col in enumerate(pal):lab[(c==col).all(1)]=i
lab=lab[labels]
uv=src.visual.uv[f].mean(1); im=np.asarray(src.visual.material.baseColorTexture.convert('RGB'));h,w=im.shape[:2];rgb=im[np.clip(((1-uv[:,1])*h).astype(int),0,h-1),np.clip((uv[:,0]*w).astype(int),0,w-1)].astype(float)
r,g,b=rgb.T
face=(((x>72)&(x<229)&(y>147)&(y<281))|((x>239)&(x<376)&(y>138)&(y<257)))&(cen[:,1]<0)
eyes=np.zeros(len(f),bool)
for cx,cy,rx,ry in [(148,210,19,13),(198,199,12,12),(260,180,14,12),(304,177,17,12)]:
 eyes|=((x-cx)/rx)**2+((y-cy)/ry)**2<1.12
eye=face&eyes
lab[eye]=0;lab[eye&(r<134)&(g<91)]=6;lab[eye&((r<55)|(g<32))]=1;lab[eye&(g>130)&(r-g<38)&(g-b<36)]=5
mouth=face&((((x-186)/23)**2+((y-247)/11)**2<1)|(((x-284)/23)**2+((y-221)/13)**2<1))
lab[mouth]=0;lab[mouth&(r-g>52)&(g<149)&(b>g*.68)]=7;lab[mouth&(r<95)&(g<50)]=1;lab[mouth&(g>144)&(r-g<44)&(g-b<40)]=5
other=face&~(eye|mouth)&np.isin(lab,[0,1,6]);lab[other]=0;lab[other&(r<118)&(g<79)]=1
# Re-evaluate the red/gold interfaces from the native texture.
border=np.isin(lab,[2,3,4])&(cen[:,2]<66)
lab[border&(g>105)&(r>1.6*b)&(g>1.5*b)]=4
cloth=(lab==4)&(g<92)&(r>1.8*g);lab[cloth]=np.where(x[cloth]<253,3,2)
# Consolidate isolated paint islands on the welded surface before adding fine eye details.
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
V,inv=np.unique(np.round(v,5),axis=0,return_inverse=True)
mesh=trimesh.Trimesh(V,inv[f],process=False); a,d=mesh.face_adjacency.T
lab[(lab==6)&~eye]=1
for iteration in range(3):
 same=lab[a]==lab[d]; n,cc=connected_components(coo_matrix((np.ones(same.sum(),dtype=bool),(a[same],d[same])),shape=(len(f),len(f))),directed=False)
 size=np.bincount(cc,weights=mesh.area_faces); boundary=~same
 u,t=a[boundary],d[boundary]; comp=np.r_[cc[u],cc[t]]; neighbor=np.r_[lab[t],lab[u]]
 votes=np.bincount(comp*8+neighbor,minlength=n*8).reshape(n,8); small=(size[cc]<.22)&(votes.sum(1)[cc]>0)
 print('island cleanup',iteration,int(small.sum()),flush=True); lab[small]=votes.argmax(1)[cc[small]]
# Restore scarlet flowers throughout the hanging central garland.
garland=(x>201)&(x<253)&(y>300)&(y<492)&(cen[:,1]<0)
lab[garland&(lab==2)&(r>90)&(r>2.6*g)]=3
# Treat the original brown slot as a dedicated white for the four eyes.
lab[eye]=0
lab[eye&(r<144)&(g<98)]=6
lab[eye&((r<65)|(g<35))]=1
lab[eye&(g>130)&(r-g<38)&(g-b<36)]=5
from PIL import Image
ref=np.array(Image.open('reference/0.png').convert('RGB').resize((1213,425)))
for slot,box in [(2,(204,242,223,274)),(3,(81,363,108,393)),(0,(84,183,102,193)),(4,(190,355,228,358))]:
 x1,y1,x2,y2=box;pal[slot]=np.median(ref[y1:y2,x1:x2].reshape(-1,3),axis=0)
print('reference palette',pal,flush=True)
# Rear jasmine follows the long braid behind the bride.
edge=np.interp(y,[222,245,275,310,350,407,470,497],[110,129,132,124,125,129,124,114])
braid=(cen[:,1]>0)&(y>222)&(y<497)&(x<edge)&(x>65)
lab[braid&np.isin(lab,[0,4,7])]=5
# Cloth and gold edging retain their material colour through occluded folds.
coat=(x>272)&(y>291)&(y<469)
lab[coat&(lab==1)]=2
lab[(x>215)&(y<128)&(lab==1)]=2
codes=np.array(['4','8','0C','1C','2C','3C','4C','5C'])
with zipfile.ZipFile('Wedding-full-color.3mf') as srczip, zipfile.ZipFile('Wedding-reference-paint.3mf','w',zipfile.ZIP_DEFLATED) as out:
 for k in ['[Content_Types].xml','_rels/.rels']:out.writestr(k,srczip.read(k))
 xml=srczip.read('3D/3dmodel.model'); vert=xml[xml.index(b'<vertices>'):xml.index(b'</vertices>')+11];V,inv=np.unique(np.round(v,5),axis=0,return_inverse=True)
 # maintain exactly the same vertex indexing as the welded texture model
 vert=("<vertices>"+"".join(f'<vertex x="{a}" y="{b}" z="{c}"/>' for a,b,c in V)+"</vertices>").encode()
 with out.open('3D/3dmodel.model','w') as fp:
  fp.write(b'<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="1" type="model"><mesh>'+vert+b'<triangles>')
  for start in range(0,len(f),30000):
   chunk=f[start:start+30000];fp.write(''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{s}"/>' for (a,b,c),s in zip(inv[chunk],codes[lab[start:start+len(chunk)]])).encode())
  fp.write(b'</triangles></mesh></object></resources><build><item objectid="1"/></build></model>')
 out.writestr('Metadata/project_settings.config',json.dumps({'filament_colour':['#%02X%02X%02X'%tuple(v) for v in pal.astype(int)]}))
