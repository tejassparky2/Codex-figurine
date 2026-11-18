import numpy as np,moderngl as gl,zipfile,json,re
from PIL import Image
with zipfile.ZipFile('Wedding-U1-150mm-gaze-corrected.3mf') as z:
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
coords=v[f]; normals=np.cross(coords[:,1]-coords[:,0],coords[:,2]-coords[:,0]);normals/=np.maximum(1e-10,np.linalg.norm(normals,axis=1)[:,None]);shade=.79+.21*np.clip(normals@[-.3,-.85,.42],0,1)
ctx=gl.create_standalone_context(backend='egl');size=(1080,1440);fb=ctx.simple_framebuffer(size);fb.use();fb.clear(1,1,1,1,depth=1);ctx.enable(gl.DEPTH_TEST)
pr=ctx.program(vertex_shader="""#version 330
in vec3 pos;in vec3 rgb;out vec3 c;void main(){gl_Position=vec4(pos.x*1.28/60,(pos.z-60)*.96/60,pos.y/120,1);c=rgb;}""",fragment_shader="""#version 330
in vec3 c;out vec4 color;void main(){color=vec4(c,1);}""")
buf=ctx.buffer(coords.astype('f4').tobytes());col=ctx.buffer(np.repeat((p[l]*shade[:,None]).astype('f4'),3,axis=0).tobytes());ctx.vertex_array(pr,[(buf,'3f','pos'),(col,'3f','rgb')]).render()
im=Image.frombytes('RGB',size,fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);im.save('U1-hand-painted.png')
im.crop((75,265,925,690)).save('U1-hand-painted-faces.png')
