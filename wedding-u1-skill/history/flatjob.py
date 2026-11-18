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
src='Wedding-150mm-finish-guide.3mf'
s,pal,l=read(src)
v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>',s),'f4')
f=np.asarray(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',s),'i4')
m=trimesh.Trimesh(v,f,process=False); c=m.triangles_center;x=216+c[:,0]*4.608/1.25;y=564.48-c[:,2]*4.608/1.25
a,b=m.face_adjacency.T;n=len(l);area=m.area_faces
# Propagate only across shared edges; protect facial details and true surface creases.
w=np.maximum(.08,np.exp(-np.square(m.face_adjacency_angles/.68))).astype('f4')
G=coo_matrix((np.r_[w,w],(np.r_[a,b],np.r_[b,a])),shape=(n,n)).tocsr()
geom=trimesh.load('source.glb',force='mesh',process=False);uv=geom.visual.uv[geom.faces].mean(1);im=np.asarray(geom.visual.material.baseColorTexture.convert('RGB'));hh,ww=im.shape[:2]
r,g,bb=im[np.clip(((1-uv[:,1])*hh).astype(int),0,hh-1),np.clip((uv[:,0]*ww).astype(int),0,ww-1)].astype('f4').T
# Recover the local hand surface from skin-tone seeds and flower/cuff neighbors
# without applying a front silhouette through to occluded geometry.
flower=((x>190)&(x<258)&(y>324)&(y<494))|((x<121)&(y>275)&(y<497))|((x>242)&(x<340)&(y>242)&(y<296))|((x>112)&(x<183)&(y>273)&(y<315))
hands=((x>182)&(x<263)&(y>342)&(y<411))|((x>199)&(x<235)&(y>289)&(y<324))
ivory=(r>110)&(g>.79*r)&(bb>.66*r);skin=(r>120)&(g<.80*r)&(g>.48*r)&(bb>.40*r)&(bb<.7*r)
l[flower&(l==4)&ivory]=2
handneighbors=G@(l==4).astype('f4')
l[hands&skin&(handneighbors>.65)&np.isin(l,[1,2,3])]=4
# Connected components: remove small, surrounded fragments; keep eyes and lips locked.
locked=(y<272)&(c[:,1]<0)
for _ in range(4):
 same=l[a]==l[b];nc,cc=connected_components(coo_matrix((np.ones(same.sum(),'u1'),(a[same],b[same])),shape=(n,n)),directed=False)
 sizes=np.bincount(cc,weights=area);u,t=a[~same],b[~same];votes=np.bincount(np.r_[cc[u]*7+l[t],cc[t]*7+l[u]],weights=np.r_[w[~same],w[~same]],minlength=nc*7).reshape(-1,7)
 small=(sizes[cc]<.75)&~locked&(votes.sum(1)[cc]>0)
 l[small]=votes.argmax(1)[cc[small]]
# Smooth only a narrow boundary band with repeated graph averaging. Interior labels are fixed.
edge=np.zeros(n,bool);dis=l[a]!=l[b];edge[a[dis]]=edge[b[dis]]=True
band=edge.copy()
for i in range(4):band|=(G@band.astype('f4'))>0
idx=np.where(band&~locked)[0]; sub=G[idx][:,idx];seed=np.eye(7,dtype='f4')[l];norm=np.asarray(G.sum(1)).ravel()[idx,None];base=seed[idx].copy();outside=G[idx]@seed-sub@base
q=base.copy()
for i in range(34):q=(sub@q+outside+.042*norm*base)/(norm*1.042+1e-8)
l[idx]=q.argmax(1)
# Inspecting the unlit views exposed a dark turban fold, flesh specks on
# ivory bands and a burgundy line along the groom's fingertips.
rear=c[:,1]>0
l[(x>214)&(y<160)&(l==5)&((r>1.55*g)|(rear&(y<141)))]=3
l[(x>240)&(y>305)&(y<466)&(l==2)&(r>2.2*g)&(g<80)]=3
from scipy.ndimage import minimum_filter
import cv2
ix=np.clip(np.round(x*2).astype(int),0,863);iy=np.clip(np.round(y*2).astype(int),0,1151)
depth=np.full((1152,864),np.inf);np.minimum.at(depth,(iy,ix),c[:,1]);visible=c[:,1]<minimum_filter(depth,3)[iy,ix]+1.8
def patch(points,slot,allowed):
 mask=np.zeros(depth.shape,'uint8');poly=np.array(points,np.int32)+[260,566];cv2.fillPoly(mask,[poly.astype('i4')],1)
 hit=(mask[iy,ix]>0)&visible&np.isin(l,allowed);l[hit]=slot
# Flower collars, wrist-adjacent flowers, cuff and individual hands.
patch([(0,0),(44,0),(80,8),(110,24),(121,34),(91,62),(48,39),(0,24)],2,[3,4])
patch([(128,135),(160,114),(179,95),(188,120),(180,133),(150,154),(140,157)],2,[4,3])
patch([(231,76),(272,74),(281,91),(272,112),(236,106),(221,95)],2,[4,3])
patch([(218,127),(252,128),(280,144),(317,180),(332,195),(303,205),(256,211),(248,184),(246,148)],2,[3,4])
patch([(148,188),(162,178),(180,156),(198,154),(211,145),(194,133),(198,127),(217,132),(244,144),(250,181),(237,198),(216,208),(198,205),(180,222),(161,215)],4,[1,2,3])
patch([(154,251),(180,255),(193,232),(207,216),(222,209),(237,207),(240,266),(213,265),(184,276),(153,280)],2,[4,3])
patch([(170,331),(234,329),(238,360),(221,367),(176,366)],2,[4,3])
del seed,q,G,geom
# Four-head physical schedule, retaining the previous paint-by-hand forehead regions.
_,up,previous=read('Wedding-U1-150mm-clean-gold.3mf')
h=c[:,2];u=np.array([0,1,2,3,0,1,0],dtype='u1')[l]
u[(l==0)&(h>=36)]=2;u[(l==4)&(h<36)]=2;u[(l==5)&(h<76)]=3;u[(l==1)&(h>=76)]=3
u[(y<182)&(previous==0)&(l==1)&(h>=76)]=0
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
save('Wedding-U1-150mm-flat.3mf',u,up);l=save('Wedding-150mm-flat-finish.3mf',l,pal)
exec(Path('/tmp/flatrender.py').read_text())
