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
codes=np.array(['4','8','0C','1C','2C','3C','4C','5C'])
with zipfile.ZipFile('Wedding-full-color.3mf') as srczip, zipfile.ZipFile('Wedding-fine-paint.3mf','w',zipfile.ZIP_DEFLATED) as out:
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
