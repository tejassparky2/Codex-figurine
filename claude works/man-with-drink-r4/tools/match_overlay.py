"""Overlay the customer image's head outline (red) on a front render of a model npz. usage: match_overlay.py mesh.npz out.png"""
import sys, numpy as np, moderngl as gl, cv2
from PIL import Image, ImageDraw
mesh, out = sys.argv[1], sys.argv[2]
s = float(np.load('views/match_scale.npy')[0])
PEYE, PMOUTH = 415.0, 552.0; MEYE, MMOUTH = 175.2, 156.0; S = (PMOUTH - PEYE) / (MEYE - MMOUTH); XCP, XCM = 344.0, -2.08
a = np.asarray(Image.open('reference/photo-front.jpg').convert('RGB')).astype(int)
fg = (~((a.min(2) > 225) & (a.max(2) - a.min(2) < 25))).astype('u1'); fg[655:] = 0
cs, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
c = c[c[:, 1] < 650]
px_mm = ((c[:, 0] - XCP) / S + XCM) * s; pz_mm = (MEYE - (c[:, 1] - PEYE) / S) * s
z = np.load(mesh); V, F, L = z['v'], z['f'], z['l']
PAL = np.array([[222,164,133],[14,14,16],[140,151,157],[241,236,225],[249,168,0],[242,179,192]], 'f4') / 255
X0, X1, Z0, Z1, PPM = -45, 45, 135, 225, 10; W, H = (X1-X0)*PPM, (Z1-Z0)*PPM
n = np.cross(V[F][:,1]-V[F][:,0], V[F][:,2]-V[F][:,0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
shade = .72 + .28*np.clip(-n[:,1]*.8 + n[:,2]*.4 - n[:,0]*.2, 0, 1)
ctx = gl.create_standalone_context(); fb = ctx.simple_framebuffer((W, H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
p = ctx.program(vertex_shader="""#version 330
uniform vec4 B; in vec3 pos; in vec3 col; out vec3 c; void main(){gl_Position=vec4((pos.x-B.x)/(B.y-B.x)*2.-1.,(pos.z-B.z)/(B.w-B.z)*2.-1.,(pos.y+80.)/160.,1); c=col;}""",
fragment_shader="""#version 330
in vec3 c; out vec4 o; void main(){o=vec4(c,1);}""")
p['B'].value = (X0, X1, Z0, Z1)
fb.clear(1, 1, 1, 1, depth=1)
ctx.vertex_array(p, [(ctx.buffer(V[F].reshape(-1,3).astype('f4').tobytes()), '3f', 'pos'), (ctx.buffer(np.repeat(PAL[L]*shade[:,None], 3, 0).astype('f4').tobytes()), '3f', 'col')]).render()
im = Image.frombytes('RGB', (W, H), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM); d = ImageDraw.Draw(im)
pts = [((x - X0)*PPM, (Z1 - zz)*PPM) for x, zz in zip(px_mm, pz_mm)]
d.line(pts, fill=(230, 20, 20), width=3); d.text((10, 10), 'red = customer image head outline (scaled on eyes/mouth)', fill='black')
im.save(out)
