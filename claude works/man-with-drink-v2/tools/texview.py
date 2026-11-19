"""Unlit textured orthographic turnaround of a Y-up GLB: front, 45, side, back, top."""
import sys, numpy as np, trimesh, moderngl as gl
from PIL import Image, ImageDraw
path,out=sys.argv[1],sys.argv[2]; W,H=(int(sys.argv[3]),int(sys.argv[4])) if len(sys.argv)>4 else (900,800)
s=trimesh.load(path,process=False); m=s.to_geometry() if isinstance(s,trimesh.Scene) else s
v=np.asarray(m.vertices,'f4'); f=np.asarray(m.faces,'i4'); uv=np.asarray(m.visual.uv,'f4')
tex=m.visual.material.baseColorTexture.convert('RGB')
c=(v.max(0)+v.min(0))/2; r=np.linalg.norm(v-c,axis=1).max()
ctx=gl.create_standalone_context(backend='egl'); fb=ctx.simple_framebuffer((W,H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
t=ctx.texture(tex.size,3,tex.tobytes()); t.build_mipmaps(); t.filter=(gl.LINEAR_MIPMAP_LINEAR,gl.LINEAR); t.use(0)
pr=ctx.program(vertex_shader="""#version 330
uniform mat3 R; uniform vec3 C; uniform float S; uniform vec2 A; in vec3 pos; in vec2 uv; out vec2 t;
void main(){vec3 q=R*(pos-C); gl_Position=vec4(q.x/S*A.x,q.y/S*A.y,-q.z/S*.5,1); t=uv;}""",
fragment_shader="""#version 330
uniform sampler2D tex; in vec2 t; out vec4 o; void main(){o=vec4(texture(tex,vec2(t.x,1.-t.y)).rgb,1);}""")
pr['tex'].value=0; pr['C'].value=tuple(c); pr['S'].value=float(r*1.02); pr['A'].value=(min(W,H)/W,min(W,H)/H)
vb=ctx.buffer(v[f].reshape(-1,3).tobytes()); ub=ctx.buffer(uv[f].reshape(-1,2).tobytes())
vao=ctx.vertex_array(pr,[(vb,'3f','pos'),(ub,'2f','uv')])
def rot(yaw,pitch=0):
    a,b=np.deg2rad([yaw,pitch]); Ry=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]]); Rx=np.array([[1,0,0],[0,np.cos(b),-np.sin(b)],[0,np.sin(b),np.cos(b)]]); return Rx@Ry
views=[('front',0,0),('right 45',-45,0),('side 90',-90,0),('back',180,0),('left 90',90,0),('top',0,70)]
ims=[]
for name,yaw,pitch in views:
    pr['R'].write(rot(yaw,pitch).T.astype('f4').tobytes()); fb.clear(1,1,1,1,depth=1); vao.render()
    im=Image.frombytes('RGB',(W,H),fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    if name=='front': im.save(out.replace('.png','-front.png'))
    ImageDraw.Draw(im).text((8,6),name,fill='black'); ims.append(im)
sheet=Image.new('RGB',(W*3,H*2),'white')
for i,im in enumerate(ims): sheet.paste(im,((i%3)*W,(i//3)*H))
sheet.save(out); print(out,len(f),'faces')
