import numpy as np,cv2,zipfile,io,moderngl as gl,trimesh
from PIL import Image
ref=np.asarray(Image.open('reference/0.png').convert('RGB').resize((1213,425)))
def sample(boxes):
 a=np.concatenate([ref[y:Y,x:X].reshape(-1,3) for x,y,X,Y in boxes]); a=a[(a[:,0].astype(float)>2.8*(a[:,1].astype(float)+1))&(a[:,0]>80)]
 return a[np.argsort(a[:,0])][np.round(np.linspace(0,len(a)-1,101)).astype(int)]
target=sample([(155,82,180,113),(203,243,224,276),(460,68,480,91),(680,80,732,121),(684,265,720,308),(1083,80,1123,115),(1064,255,1095,282)])
print('groom red',target[50],flush=True)
m=trimesh.load('source.glb',force='mesh',process=False);im=np.asarray(m.visual.material.baseColorTexture.convert('RGB'));h,w=im.shape[:2]
v=m.vertices.copy();v-=m.bounds.mean(0);v/=m.extents[1]/2
# The groom occupies the right half, with his sleeve reaching toward the joined hands.
ctx=gl.create_standalone_context(backend='egl');fb=ctx.simple_framebuffer((w,h));fb.use();fb.clear()
pr=ctx.program(vertex_shader="""#version 330
in vec3 p;in vec2 uv;out vec3 xyz;void main(){xyz=p;gl_Position=vec4(uv*2.-1.,0,1);}""",fragment_shader="""#version 330
in vec3 xyz;out vec4 c;void main(){float b=mix(.05,-.005,smoothstep(.1,.48,xyz.y));float g=smoothstep(b-.015,b+.015,xyz.x);c=vec4(g,g,g,1);}""")
buf=ctx.buffer(np.c_[v,m.visual.uv].astype('f4').tobytes());idx=ctx.buffer(m.faces.astype('i4').tobytes());ctx.vertex_array(pr,[(buf,'3f 2f','p','uv')],idx).render()
mask=np.frombuffer(fb.read(components=1),np.uint8).reshape(h,w)[::-1];mask=cv2.dilate(mask,np.ones((5,5),'u1'))
r,g,b=[im[:,:,i].astype('float32') for i in range(3)];valid=(mask>245)&(r>45)&(r<160)&(g<.26*r)&(b<.60*r)
src=np.percentile(r[valid],np.arange(101));src=np.r_[0,src,240,255]; dst=np.vstack([[12,2,4],target,[249,58,52],[255,78,70]])
alpha=(mask.astype('f4')/255)*np.clip((r-g-17)/27,0,1)*np.clip((r*.60-g)/(.22*r+1),0,1)*np.clip((r*.72-b)/(.20*r+1),0,1)*np.clip((195-r)/30,0,1)
out=im.copy()
for i in range(3):
 corrected=np.interp(r,src,dst[:,i]);out[:,:,i]=np.round(im[:,:,i]*(1-alpha)+alpha*corrected).astype('u1')
tex=Image.fromarray(out);tex.save('/tmp/reftex.png')
with zipfile.ZipFile('Wedding-full-color.3mf') as old,zipfile.ZipFile('Wedding-reference-texture.3mf','w',zipfile.ZIP_DEFLATED) as new:
 for k in old.namelist():
  if k.endswith('texture.png'):new.write('/tmp/reftex.png',k)
  else:new.writestr(k,old.read(k))
