"""Unlit textured orthographic close-up at a known scale. args: npz glb out cx cy halfwidth_mm px_per_mm [yaw]"""
import sys, numpy as np, trimesh, moderngl as gl
from PIL import Image, ImageDraw
npz,glb,out=sys.argv[1:4]; cx,cy,hw,ppm=map(float,sys.argv[4:8]); yaw=float(sys.argv[8]) if len(sys.argv)>8 else 0
z=np.load(npz); v=z['v']; f=z['f']; m=trimesh.load(glb,force='mesh',process=False); uv=np.asarray(m.visual.uv,'f4')
tex=m.visual.material.baseColorTexture.convert('RGB'); W=H=int(2*hw*ppm)
ctx=gl.create_standalone_context(backend='egl'); fb=ctx.simple_framebuffer((W,H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
t=ctx.texture(tex.size,3,tex.tobytes()); t.build_mipmaps(); t.use(0)
pr=ctx.program(vertex_shader="""#version 330
uniform mat3 R; uniform vec3 C; uniform float S; in vec3 pos; in vec2 uv; out vec2 t;
void main(){vec3 q=R*pos-C; gl_Position=vec4(q.x/S,q.y/S,-q.z/200.,1); t=uv;}""",fragment_shader="""#version 330
uniform sampler2D tex; in vec2 t; out vec4 o; void main(){o=vec4(texture(tex,vec2(t.x,1.-t.y)).rgb,1);}""")
a=np.deg2rad(yaw); R=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
pr['R'].write(R.T.astype('f4').tobytes()); pr['C'].value=(cx,cy,0); pr['S'].value=hw
vao=ctx.vertex_array(pr,[(ctx.buffer(v[f].reshape(-1,3).astype('f4').tobytes()),'3f','pos'),(ctx.buffer(uv[f].reshape(-1,2).tobytes()),'2f','uv')])
fb.clear(1,1,1,1,depth=1); vao.render(); im=Image.frombytes('RGB',(W,H),fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
d=ImageDraw.Draw(im)
for k in range(int(-hw),int(hw)+1):   # 1 mm ticks, labelled every 5 mm, along top/left edges
    x=(k+hw)*ppm; y=(hw-k)*ppm; L=12 if k%5==0 else 5
    d.line([(x,0),(x,L)],fill='red'); d.line([(0,y),(L,y)],fill='red')
    if k%5==0: d.text((x+2,L),f'{cx+k:.0f}',fill='red'); d.text((L+2,y),f'{cy+k:.0f}',fill='red')
im.save(out); print(out,W,H)
