from pathlib import Path
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
src='Wedding-150mm-flat-finish.3mf'
s,pal,l=read(src)
v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>',s),'f4')
f=np.asarray(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',s),'i4')
m=trimesh.Trimesh(v,f,process=False);c=m.triangles_center;x=216+c[:,0]*4.608/1.25;y=564.48-c[:,2]*4.608/1.25
a,b=m.face_adjacency.T;n=len(l);same=l[a]==l[b]
nc,cc=connected_components(coo_matrix((np.ones(same.sum(),'u1'),(a[same],b[same])),shape=(n,n)),directed=False)
num=np.bincount(cc);areas=np.bincount(cc,weights=m.area_faces)
cx=np.bincount(cc,weights=x)/num;cy=np.bincount(cc,weights=y)/num;depth=np.bincount(cc,weights=c[:,1])/num
labs=np.zeros(nc,int);labs[cc]=l
from scipy.spatial import cKDTree
orig=l.copy()
# Material components: retain connected hands, arms and head skin; fill disconnected
# flesh flecks trapped in the flower bands from nearby red or ivory flower samples.
floral=((cx>176)&(cx<273)&(cy>286)&(cy<493))|((cx>111)&(cx<185)&(cy>273)&(cy<317))|((cx>260)&(cx<347)&(cy>242)&(cy<293))
flecks=(labs==4)&floral&(areas<45)
# Remove small gold specks on flowers, keeping the deliberate connected gold banding.
flecks|=(labs==0)&floral&(areas<9)
bad=flecks[cc]
votes=np.zeros((nc,7));edge=l[a]!=l[b]
for u,t in [(a[edge],b[edge]),(b[edge],a[edge])]:
 np.add.at(votes,(cc[u],l[t]),1)
votes[:,[0,3,4,5,6]]=0
l[bad]=np.where(votes[cc[bad],1]>votes[cc[bad],2],1,2)
# Back of hanging lower garland: between the joined hands and the lower red band.
strand=(x>210)&(x<248)&(y>405)&(y<419)
l[strand&(l==4)]=2
# Re-sample the original UV color for red versus maroon near the groom sleeve
# and the inside lower hem. Use the dark-colored fabric on all exposed depths.
g=trimesh.load('source.glb',force='mesh',process=False);uv=g.visual.uv[g.faces].mean(1);im=np.asarray(g.visual.material.baseColorTexture.convert('RGB'))
h,w=im.shape[:2];r,green,blue=im[np.clip(((1-uv[:,1])*h).astype(int),0,h-1),np.clip((uv[:,0]*w).astype(int),0,w-1)].astype(float).T
groom=(x>230)&(y>295)&(y<486)
redg=(l==1)&groom
seeds=redg&((r<155)&(green<.38*r)&(blue<.68*r))
# Component-wise locking for isolated scarlet fragments on the maroon coat.
numred=np.bincount(cc,weights=seeds,minlength=nc)
coat=(labs==1)&(cx>229)&(cy>295)&(cy<486)&(numred/num>.44)
l[(coat[cc]|seeds)&redg]=3
# Skin is one physical material, including both forehead/cheek components.
_,_,toolsold=read('Wedding-U1-150mm-flat.3mf')
skin=np.isin(cc,[30,367,498,403,415])&(orig==4)
print('skin head IDs before edit',np.unique(toolsold[skin],return_counts=True))
u=np.array([0,1,2,3,0,1,0],dtype='u1')[l];z=c[:,2]
u[(l==0)&(z>=36)]=2;u[(l==4)&(z<36)]=2;u[(l==5)&(z<76)]=3;u[(l==1)&(z>=76)]=3
u[(y<182)&(toolsold==0)&(l==1)&(z>=76)]=0
assert np.all(u[skin]==0)
print('flower and coat faces changed',int((orig!=l).sum()),'coat',int((redg&(l==3)).sum()))
def save(name,labels,colors):
 table=list(codes)
 with zipfile.ZipFile(src) as zz,zipfile.ZipFile(name,'w',zipfile.ZIP_DEFLATED) as out:
  for k in zz.namelist():
   if k.endswith('.model'):
    it=iter(labels);out.writestr(k,re.sub(rb'paint_color="\w+"',lambda m:b'paint_color="'+table[next(it)]+b'"',s))
   elif k.endswith('project_settings.config'):out.writestr(k,json.dumps({'filament_colour':colors}))
   else:out.writestr(k,zz.read(k))
 _,_,actual=read(name);assert np.array_equal(actual,labels)
 return actual
# Display swatches use the face-height colors. Lower tool IDs still refer to the starting spools.
save('Wedding-U1-150mm-material-locked.3mf',u,['#F6BCA2','#131213','#FFF9F0','#771020'])
save('Wedding-150mm-material-locked-finish.3mf',l,pal)
