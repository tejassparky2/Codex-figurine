"""Front orthographic face camera at 40 px/mm over x[-28,28], z[148,204] (220 mm model).
Writes views/face_id.npy (printable-mesh triangle IDs, glasses frames hidden), renders/face-tex.png (source texture,
frames hidden via nearest-face mapping) and renders/face-tex-grid.png (with mm grid)."""
import numpy as np, trimesh, moderngl as gl
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
X0, X1, Z0, Z1, PPM = -30, 30, 140, 204, 40; W, H = (X1-X0)*PPM, (Z1-Z0)*PPM
z = np.load('printable.npz'); V, F = z['v'], z['f']; c = V[F].mean(1); lab = np.load('broad.npy')
frame = np.load('frame_full.npy'); np.save('frame_mask.npy', frame)
ctx = gl.create_standalone_context(backend='egl'); fb = ctx.simple_framebuffer((W, H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
vs = """#version 330
uniform vec4 B; in vec3 pos; %s void main(){gl_Position=vec4((pos.x-B.x)/(B.y-B.x)*2.-1.,(pos.z-B.z)/(B.w-B.z)*2.-1.,(pos.y+60.)/120.,1); %s}"""
pid = ctx.program(vertex_shader=vs % ('flat out int id;', 'id=gl_VertexID/3+1;'), fragment_shader="""#version 330
flat in int id; out vec4 o; void main(){o=vec4(float(id&255),float((id>>8)&255),float(id>>16),255)/255.;}""")
pid['B'].value = (X0, X1, Z0, Z1)
keep = np.flatnonzero(~frame); order = keep  # draw only non-frame faces; IDs remapped below
vao = ctx.vertex_array(pid, [(ctx.buffer(V[F[keep]].astype('f4').tobytes()), '3f', 'pos')]); fb.clear(); vao.render()
pix = np.frombuffer(fb.read(), dtype='u1').reshape(H, W, 3)[::-1].astype('i4') @ np.array([1,256,65536]) - 1
ids = np.where(pix >= 0, keep[np.clip(pix, 0, None)], -1); np.save('views/face_id.npy', ids)
# Source texture with the same camera; hide source faces that map to the printable frame.
src = trimesh.load('inputs-raw/man-with-drink.glb', force='mesh', process=False)
sv = np.asarray(src.vertices, float); sv = np.c_[sv[:,0], -sv[:,2], sv[:,1]]
sv -= [(sv[:,0].max()+sv[:,0].min())/2, (sv[:,1].max()+sv[:,1].min())/2, sv[:,2].min()]; sv *= V[:,2].max()/sv[:,2].max()
sf = src.faces; sc = sv[sf].mean(1)
near = cKDTree(c).query(sc, workers=4)[1]; sk = np.flatnonzero(~frame[near])
uv = np.asarray(src.visual.uv, 'f4'); tex = src.visual.material.baseColorTexture.convert('RGB')
t = ctx.texture(tex.size, 3, tex.tobytes()); t.build_mipmaps(); t.use(0)
pt = ctx.program(vertex_shader=vs % ('in vec2 uv; out vec2 tc;', 'tc=uv;'), fragment_shader="""#version 330
uniform sampler2D tex; in vec2 tc; out vec4 o; void main(){o=vec4(texture(tex,vec2(tc.x,1.-tc.y)).rgb,1);}""")
pt['B'].value = (X0, X1, Z0, Z1)
vao = ctx.vertex_array(pt, [(ctx.buffer(sv[sf[sk]].astype('f4').tobytes()), '3f', 'pos'), (ctx.buffer(uv[sf[sk]].tobytes()), '2f', 'uv')])
fb.clear(1,1,1,1, depth=1); vao.render(); im = Image.frombytes('RGB', (W, H), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM); im.save('renders/face-tex.png')
d = ImageDraw.Draw(im)
for x in range(X0, X1+1):
    px = (x-X0)*PPM; d.line([(px,0),(px,H)], fill=(0,170,255) if x%5==0 else (190,225,255), width=2 if x%5==0 else 1)
    if x%5==0: d.text((px+3, 3), str(x), fill='blue')
for zz in range(Z0, Z1+1):
    py = (Z1-zz)*PPM; d.line([(0,py),(W,py)], fill=(0,170,255) if zz%5==0 else (190,225,255), width=2 if zz%5==0 else 1)
    if zz%5==0: d.text((3, py+3), str(zz), fill='blue')
im.save('renders/face-tex-grid.png'); print(W, H, 'frame faces', frame.sum())
