import numpy as np,moderngl as gl,zipfile,json,re
from PIL import Image
with zipfile.ZipFile('Wedding-U1-150mm-smooth.3mf') as z:
 assert z.testzip() is None
 s=z.read('3D/3dmodel.model');p=json.loads(z.read('Metadata/project_settings.config'))['filament_colour'];p=np.array([list(bytes.fromhex(c[1:])) for c in p])/255
v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>',s),'f4')
n=1974931;f=np.empty((n,3),'i4');l=np.empty(n,'u1');codes={s:i for i,s in enumerate([b'4',b'8',b'0C',b'1C',b'2C',b'3C',b'4C',b'5C'])}
for i,m in enumerate(re.finditer(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)" paint_color="(\w+)"/>',s)):
 f[i]=m.group(1,2,3);l[i]=codes[m[4]]
assert i+1==n
z=v[f,2].mean(1);v/=1.25
p=np.vstack([p,np.array([[246,188,162],[19,18,19]])/255])
l[(l==0)&(z>=36)]=4;l[(l==1)&(z>=76)]=5
with zipfile.ZipFile('Wedding-clean-details.3mf') as original:
 raw=original.read('3D/3dmodel.model')
 old=np.fromiter((codes[m[1]] for m in re.finditer(rb'paint_color="(\w+)"',raw)),dtype='u1')
assert len(old)==len(l)
l[(old==4)&(l==2)]=0
p=np.vstack([p,[.84,.24,.31]])
regions=np.load('detail-regions.npz')
for name in ['Bride mouth','Groom mouth']:
 ids=regions[name];l[ids[old[ids]==7]]=6
cen=v[f].mean(1);x=216+cen[:,0]*4.608;y=288-(cen[:,2]-60)*4.608
for cx,cy,rx,ry in [(175,174,4,6),(277,154,4,7)]:
 mark=(((x-cx)/rx)**2+((y-cy)/ry)**2<1)&(cen[:,1]<0)&np.isin(old,[2,3,7]);l[mark]=1
from scipy.spatial import cKDTree
import trimesh
m=trimesh.load('source.glb',force='mesh',process=False)
uv=m.visual.uv[m.faces].mean(1); img=np.asarray(m.visual.material.baseColorTexture.convert('RGB'))
rgb=img[np.clip(((1-uv[:,1])*img.shape[0]).astype(int),0,img.shape[0]-1),np.clip((uv[:,0]*img.shape[1]).astype(int),0,img.shape[1]-1)].astype(float)
r,g,b=rgb.T
# Reconstruct head ornament material from raised beads and gold neighbors in 3-D.
def ellipse(cx,cy,rx,ry):return ((x-cx)/rx)**2+((y-cy)/ry)**2<=1
gems=ellipse(163,148,7,8)|ellipse(108,275,10,17)|ellipse(284,111,14,18)|ellipse(298,77,8,8)
chain=(y<245)&(x<211)&(y>100)
tree=cKDTree(cen[l==0]);dist=tree.query(cen,k=1,workers=4)[0]
orn=(gems&(dist<1.18))|(chain&(dist<.46)&(r>90)&(g>r*.51)&(r>1.45*b))
l[orn]=0
# Neutral dark hair alongside the ornament, including the part at the crown.
hair=chain&(dist<1.1)&(r<90)&(g<78)&(b<81)&(z>76)&~gems
l[hair]=5
# The bride's textile and flower reds run all around her body. Keep the maroon coat across the overlap.
edge=np.interp(y,[285,310,340,365,400,450,510,570],[178,215,219,219,214,207,223,230])
dress=(y>287)&(x<edge)
l[dress&np.isin(l,[3,5])]=1
# Preserve small red garment parts across the swap plane for the hand paint guide.
l[(old==3)&dress]=1
# Remove skin/maroon shadows on ivory blossoms where the texture is light and low-chroma.
floral=((x<120)&(y>280)&(y<494))|((x>199)&(x<254)&(y>352)&(y<490))|((x>112)&(x<186)&(y>277)&(y<308))
l[floral&(r>132)&(g>.78*r)&(b>.64*r)&np.isin(l,[3,4,5])]=2
# Keep each visible finger skin-colored wherever the reference texture describes skin.
hand=ellipse(206,391,24,14)|ellipse(237,370,19,14)
l[hand&(cen[:,1]<0)&(r>150)&(g>.5*r)&(g<.87*r)&(b>.45*r)&(b<.79*r)&np.isin(l,[0,1,3,5])]=4
assert not np.any((l==5)&dress)
# Map finished materials to the two-swap U1 base or retain them separately in a finish master.
u=np.array([0,1,2,3,0,1,0],dtype='u1')[l]
u[(l==0)&(z>=36)]=2;u[(l==4)&(z<36)]=2;u[(l==5)&(z<76)]=3;u[(l==1)&(z>=76)]=3
for cx,cy,rx,ry in [(175,174,4,6),(277,154,4,7)]:
 u[ellipse(cx,cy,rx,ry)&(cen[:,1]<0)&(l==1)]=0
pal=['#EFC13A','#DE1508','#FFF9F0','#771020','#F6BCA2','#131213','#D63D4F']
def write(name,labels,palette):
 rev=list(codes)
 with zipfile.ZipFile('Wedding-U1-150mm-smooth.3mf') as src,zipfile.ZipFile(name,'w',zipfile.ZIP_DEFLATED) as out:
  for k in src.namelist():
   if k=='3D/3dmodel.model':
    it=iter(labels); data=re.sub(rb'paint_color="\w+"',lambda m:b'paint_color="'+rev[next(it)]+b'"',s);out.writestr(k,data)
   elif k.endswith('project_settings.config'):out.writestr(k,json.dumps({'filament_colour':palette}))
   else:out.writestr(k,src.read(k))
 with zipfile.ZipFile(name) as check:
  assert check.testzip() is None
  decoded=np.fromiter((codes[q[1]] for q in re.finditer(rb'paint_color="(\w+)"',check.read('3D/3dmodel.model'))),dtype='u1')
  assert np.array_equal(decoded,labels)
write('Wedding-U1-150mm-clean-gold.3mf',u,pal[:4]);write('Wedding-150mm-finish-guide.3mf',l,pal)

coords=v[f]; normals=np.cross(coords[:,1]-coords[:,0],coords[:,2]-coords[:,0]);normals/=np.maximum(1e-10,np.linalg.norm(normals,axis=1)[:,None]);shade=.79+.21*np.clip(normals@[-.3,-.85,.42],0,1)
ctx=gl.create_standalone_context(backend='egl');size=(2160,2880);fb=ctx.simple_framebuffer(size);fb.use();fb.clear(1,1,1,1,depth=1);ctx.enable(gl.DEPTH_TEST)
pr=ctx.program(vertex_shader="""#version 330
in vec3 pos;in vec3 rgb;out vec3 c;void main(){gl_Position=vec4(pos.x*1.28/60,(pos.z-60)*.96/60,pos.y/120,1);c=rgb;}""",fragment_shader="""#version 330
in vec3 c;out vec4 color;void main(){color=vec4(c,1);}""")
buf=ctx.buffer(coords.astype('f4').tobytes());col=ctx.buffer(np.repeat((p[l]*shade[:,None]).astype('f4'),3,axis=0).tobytes());ctx.vertex_array(pr,[(buf,'3f','pos'),(col,'3f','rgb')]).render()
im=Image.frombytes('RGB',size,fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);im.resize((1080,1440),Image.Resampling.LANCZOS).save('U1-clean-gold-finish.png')
im.crop((420,705,1710,1285)).save('U1-clean-gold-facial-detail.png')
