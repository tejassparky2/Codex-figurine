"""Shaded close-up with ambient occlusion (48 rays, 8 mm) around a box, to show creases and the mouth slot as they
will read on a print. usage: ao_closeup.py mesh.npz out.png cx cz half_mm [yaw] [elev] [ppm]"""
import sys, numpy as np, trimesh, moderngl as gl
from PIL import Image
a = sys.argv; z = np.load(a[1]); V, F, L = z['v'], z['f'], z['l']; cx, cz, hw = map(float, a[3:6])
yaw = float(a[6]) if len(a) > 6 else 0; el = float(a[7]) if len(a) > 7 else 0; ppm = float(a[8]) if len(a) > 8 else 50
m = trimesh.Trimesh(V, F, process=False); c = m.triangles_center; n = m.face_normals
box = (np.abs(c[:, 0] - cx) < hw + 4) & (np.abs(c[:, 2] - cz) < hw + 4) & (c[:, 1] < -10)
ids = np.flatnonzero(box); rng = np.random.default_rng(0); dirs = rng.normal(size=(48, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
occ = np.zeros(len(ids))
for d in dirs:
    dd = np.where((n[ids] @ d)[:, None] < 0, -d, d); org = c[ids] + n[ids] * 2e-3
    loc, ri, _ = m.ray.intersects_location(org, dd, multiple_hits=False)
    hit = np.zeros(len(ids), bool); hit[ri[np.linalg.norm(loc - org[ri], axis=1) < 8.0]] = True; occ += hit
ao = np.ones(len(F)); ao[ids] = 1 - 0.85 * occ / len(dirs)
PAL = np.array([[222,164,133],[14,14,16],[140,151,157],[241,236,225],[249,168,0],[242,179,192]], 'f4') / 255
ar, e = np.deg2rad([yaw, el]); right = np.array([np.cos(ar), -np.sin(ar), 0]); fwd = np.array([np.sin(ar)*np.cos(e), np.cos(ar)*np.cos(e), -np.sin(e)]); up = np.cross(right, fwd)
Ld = -(fwd*.8 - up*.5 + right*.2); Ld /= np.linalg.norm(Ld)
col = PAL[L] * ((.35 + .65*np.clip(n @ Ld, 0, 1)) * ao)[:, None]
S = int(2*hw*ppm); ctx = gl.create_standalone_context(); fb = ctx.simple_framebuffer((S, S)); fb.use(); ctx.enable(gl.DEPTH_TEST)
p = ctx.program(vertex_shader="""#version 330
uniform vec3 r; uniform vec3 u; uniform vec3 d; uniform vec3 C; uniform float h; in vec3 pos; in vec3 col; out vec3 c;
void main(){vec3 q=pos-C; gl_Position=vec4(dot(q,r)/h,dot(q,u)/h,dot(q,d)/200.,1); c=col;}""", fragment_shader="""#version 330
in vec3 c; out vec4 o; void main(){o=vec4(c,1);}""")
p['r'].value = tuple(right); p['u'].value = tuple(up); p['d'].value = tuple(fwd); p['C'].value = (cx, -30, cz); p['h'].value = hw
fb.clear(.92, .9, .87, 1, depth=1)
ctx.vertex_array(p, [(ctx.buffer(V[F].reshape(-1,3).astype('f4').tobytes()), '3f', 'pos'), (ctx.buffer(np.repeat(col, 3, 0).astype('f4').tobytes()), '3f', 'col')]).render()
Image.frombytes('RGB', (S, S), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(a[2])
