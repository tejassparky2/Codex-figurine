"""Measure head yaw/roll of a Y-up textured GLB from its pupils on a straight-front orthographic render.
usage: head_pose.py model.glb out_prefix
Front = +Z (as in texview.py). Writes <out_prefix>-front.png and -face.png with the detected pupils marked."""
import sys
import numpy as np, trimesh, moderngl as gl, cv2
from PIL import Image, ImageDraw

path, out = sys.argv[1], sys.argv[2]
s = trimesh.load(path, process=False); m = s.to_geometry() if isinstance(s, trimesh.Scene) else s
v = np.asarray(m.vertices, 'f4'); f = np.asarray(m.faces, 'i4'); uv = np.asarray(m.visual.uv, 'f4')
tex = m.visual.material.baseColorTexture.convert('RGB')
lo, hi = v.min(0), v.max(0); H = 3000; W = int(H * (hi[0] - lo[0]) / (hi[1] - lo[1])) + 2
ctx = gl.create_standalone_context(backend='egl')
col = ctx.texture((W, H), 3); posT = ctx.texture((W, H), 3, dtype='f4'); dep = ctx.depth_renderbuffer((W, H))
fbo = ctx.framebuffer([col, posT], dep); fbo.use(); ctx.enable(gl.DEPTH_TEST)
t = ctx.texture(tex.size, 3, tex.tobytes()); t.build_mipmaps(); t.filter = (gl.LINEAR_MIPMAP_LINEAR, gl.LINEAR); t.use(0)
pr = ctx.program(vertex_shader="""#version 330
uniform vec3 lo; uniform vec3 hi; in vec3 pos; in vec2 uv; out vec2 t; out vec3 P;
void main(){ gl_Position=vec4((pos.x-lo.x)/(hi.x-lo.x)*2.-1.,(pos.y-lo.y)/(hi.y-lo.y)*2.-1.,-(pos.z-lo.z)/(hi.z-lo.z)*2.+1.,1); t=uv; P=pos; }""",
    fragment_shader="""#version 330
uniform sampler2D tex; in vec2 t; in vec3 P; layout(location=0) out vec4 o; layout(location=1) out vec3 q;
void main(){ o=vec4(texture(tex,vec2(t.x,1.-t.y)).rgb,1); q=P; }""")
pr['tex'].value = 0; pr['lo'].value = tuple(lo); pr['hi'].value = tuple(hi)
vao = ctx.vertex_array(pr, [(ctx.buffer(v[f].reshape(-1, 3).tobytes()), '3f', 'pos'), (ctx.buffer(uv[f].reshape(-1, 2).tobytes()), '2f', 'uv')])
fbo.clear(1, 1, 1, 1, depth=1); vao.render()
img = np.frombuffer(col.read(), 'u1').reshape(H, W, 3)[::-1]
P = np.frombuffer(posT.read(), 'f4').reshape(H, W, 3)[::-1]
Image.fromarray(img).save(out + '-front.png')
# Eye band: 0.72-0.81 of the height from the feet (eyes sit near 0.77 on these caricatures).
y0, y1 = int(H * (1 - .81)), int(H * (1 - .72))
band = img[y0:y1].astype('f4'); lum = band.mean(2)
dark = ((lum < 60) & (band.max(2) - band.min(2) < 60)).astype('u1')
dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3), 'u1'))
n, cc, st, cen = cv2.connectedComponentsWithStats(dark, 8)
cands = sorted([(st[i, cv2.CC_STAT_AREA], i) for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 40], reverse=True)[:8]
blobs = []
for area, i in cands:
    ys, xs = np.nonzero(cc == i); p3 = P[y0 + ys, xs].mean(0)
    asp = st[i, cv2.CC_STAT_WIDTH] / max(1, st[i, cv2.CC_STAT_HEIGHT])
    blobs.append((area, (xs.mean(), y0 + ys.mean()), p3, asp))
# Pupils: the two largest roughly round dark blobs on the front of the face (largest z), one each side.
front = sorted([b for b in blobs if .4 < b[3] < 2.5], key=lambda b: -b[2][2])[:6]
front = sorted(front, key=lambda b: -b[0])
pair = None
for i in range(len(front)):
    for j in range(i + 1, len(front)):
        a, b = front[i], front[j]
        if abs(a[1][0] - b[1][0]) > W * .12 and abs(a[1][1] - b[1][1]) < H * .03:
            pair = (a, b); break
    if pair: break
if not pair:
    sys.exit('pupils not found; candidates: ' + str([(b[0], b[1], b[2].round(4)) for b in blobs]))
L, R = sorted(pair, key=lambda b: b[1][0])
d = R[2] - L[2]
H_m = hi[1] - lo[1]
scale = 220.0 / H_m                                  # report in mm at the 220 mm print height
yaw = np.degrees(np.arctan2(d[2], d[0]))             # + : viewer-right eye nearer the camera -> face turned to viewer's left
roll = np.degrees(np.arctan2(d[1], d[0]))            # + : viewer-right eye higher
mid = (L[2] + R[2]) / 2
body_x = (lo[0] + hi[0]) / 2
print(f'pupils at {L[1][0]:.0f},{L[1][1]:.0f} and {R[1][0]:.0f},{R[1][1]:.0f} px')
print(f'yaw {yaw:+.1f} deg | roll {roll:+.1f} deg | eye midpoint offset from model centre x {(mid[0] - body_x) * scale:+.1f} mm')
im = Image.fromarray(img); dr = ImageDraw.Draw(im)
for b in (L, R):
    x, y = b[1]; dr.ellipse([x - 14, y - 14, x + 14, y + 14], outline=(255, 0, 0), width=4)
top = int(H * (1 - .99)); bot = int(H * (1 - .60))
im.crop((0, top, W, bot)).save(out + '-face.png')
# --- 2-D metrics comparable with a photo: eye-line tilt and nose-tip offset from the eye midpoint (per eye spacing)
(lx, ly), (rx, ry) = L[1], R[1]
ipd = rx - lx
yy0, yy1 = int(max(ly, ry) + .15 * ipd), int(max(ly, ry) + .75 * ipd)
xx0, xx1 = int(lx - .1 * ipd), int(rx + .1 * ipd)
zwin = P[yy0:yy1, xx0:xx1, 2].copy(); zwin[(img[yy0:yy1, xx0:xx1] == 255).all(2)] = -9
iy, ix = np.unravel_index(np.argmax(zwin), zwin.shape)
nx = xx0 + ix
tilt2d = np.degrees(np.arctan2(ly - ry, rx - lx))
print(f'2-D: eye-line tilt {tilt2d:+.1f} deg | nose tip offset from eye midpoint {(nx - (lx + rx) / 2) / ipd * 100:+.1f} % of eye spacing')
