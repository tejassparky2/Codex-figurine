import numpy as np,moderngl as gl,zipfile,json,re
from PIL import Image
with zipfile.ZipFile('Wedding-clean-details.3mf') as z:
 assert z.testzip() is None
 s=z.read('3D/3dmodel.model');p=json.loads(z.read('Metadata/project_settings.config'))['filament_colour'];p=np.array([list(bytes.fromhex(c[1:])) for c in p])/255
v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>',s),'f4')
n=1974931;f=np.empty((n,3),'i4');l=np.empty(n,'u1');codes={s:i for i,s in enumerate([b'4',b'8',b'0C',b'1C',b'2C',b'3C',b'4C',b'5C'])}
for i,m in enumerate(re.finditer(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)" paint_color="(\w+)"/>',s)):
 f[i]=m.group(1,2,3);l[i]=codes[m[4]]
assert i+1==n
for name,ids in np.load('detail-regions.npz').items():
 allowed=[6,7] if 'mouth' in name else [1,6];assert set(np.unique(l[ids]))==set(allowed);print(name,len(ids),flush=True)
coords=v[f]; normals=np.cross(coords[:,1]-coords[:,0],coords[:,2]-coords[:,0]);normals/=np.maximum(1e-10,np.linalg.norm(normals,axis=1)[:,None]);shade=.79+.21*np.clip(normals@[-.3,-.85,.42],0,1)
ctx=gl.create_standalone_context(backend='egl');size=(1080,1440);fb=ctx.simple_framebuffer(size);fb.use();fb.clear(1,1,1,1,depth=1);ctx.enable(gl.DEPTH_TEST)
pr=ctx.program(vertex_shader="""#version 330
in vec3 pos;in vec3 rgb;out vec3 c;void main(){gl_Position=vec4(pos.x*1.28/60,(pos.z-60)*.96/60,pos.y/120,1);c=rgb;}""",fragment_shader="""#version 330
in vec3 c;out vec4 color;void main(){color=vec4(c,1);}""")
buf=ctx.buffer(coords.astype('f4').tobytes());col=ctx.buffer(np.repeat((p[l]*shade[:,None]).astype('f4'),3,axis=0).tobytes());ctx.vertex_array(pr,[(buf,'3f','pos'),(col,'3f','rgb')]).render()
im=Image.frombytes('RGB',size,fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);im.save('Clean-front.png');im.crop((288,376,837,562)).save('Clean-eyes.png');im.resize((432,576)).save('wpaintsm.png')
