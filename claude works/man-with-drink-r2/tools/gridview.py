"""Front orthographic render of per-face texture colours with a mm grid. usage: gridview.py x0 x1 z0 z1 ppm out.png [step]"""
import sys, numpy as np
from PIL import Image, ImageDraw
x0, x1, z0, z1, ppm = map(float, sys.argv[1:6]); out = sys.argv[6]; step = int(sys.argv[7]) if len(sys.argv) > 7 else 10
ids = None
import moderngl as gl
z = np.load('printable.npz'); V, F = z['v'], z['f']; rgb = np.load('face_rgb.npy')
W, H = int((x1-x0)*ppm), int((z1-z0)*ppm)
ctx = gl.create_standalone_context(backend='egl'); fb = ctx.simple_framebuffer((W, H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
p = ctx.program(vertex_shader="""#version 330
uniform vec4 B; in vec3 pos; in vec3 col; out vec3 c; void main(){gl_Position=vec4((pos.x-B.x)/(B.y-B.x)*2.-1.,(pos.z-B.z)/(B.w-B.z)*2.-1.,(pos.y+60.)/120.,1); c=col;}""",
fragment_shader="""#version 330
in vec3 c; out vec4 o; void main(){o=vec4(c,1);}""")
p['B'].value = (x0, x1, z0, z1)
vao = ctx.vertex_array(p, [(ctx.buffer(V[F].astype('f4').tobytes()), '3f', 'pos'), (ctx.buffer(np.repeat(rgb/255., 3, 0).astype('f4').tobytes()), '3f', 'col')])
fb.clear(1, 1, 1, 1, depth=1); vao.render()
im = Image.frombytes('RGB', (W, H), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM); d = ImageDraw.Draw(im)
for x in range(int(np.ceil(x0)), int(x1)+1):
    if x % step == 0:
        px = (x-x0)*ppm; d.line([(px, 0), (px, H)], fill=(0, 150, 255), width=1); d.text((px+2, 2), str(x), fill='blue')
for zz in range(int(np.ceil(z0)), int(z1)+1):
    if zz % step == 0:
        py = (z1-zz)*ppm; d.line([(0, py), (W, py)], fill=(0, 150, 255), width=1); d.text((2, py+2), str(zz), fill='blue')
im.save(out); print(W, H)
