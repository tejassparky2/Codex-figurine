"""Owner: "match head shape with photo 1:1". Front-silhouette warp of the head onto the customer image.
Heights: piecewise-linear map through landmarks, scale fixed by eye line -> mouth line (photo 415 -> 552 px = model
175.2 -> 156.0 mm): hair top, eye line, mouth line and chin land where the photo has them. Widths: per row, the left and
right halves of the model silhouette are mapped linearly onto the photo silhouette at the matching row (silhouette
centre to centre), so ears, cheeks, jaw and hair outline follow the photo. The warp fades to zero between z 136 and
141 (neck and collar untouched). Depth (y) is unchanged. Finally the whole model is scaled back to 220 mm tall.
Vertices only; faces and labels unchanged. usage: match_head.py in.npz out.npz"""
import sys, numpy as np, trimesh, moderngl as gl
from PIL import Image
from scipy.ndimage import gaussian_filter1d
src, dst = sys.argv[1], sys.argv[2]
z = np.load(src); V = z['v'].astype('f8').copy(); F = z['f']; L = z['l']
# ---- photo silhouette (px) ----
a = np.asarray(Image.open('reference/photo-front.jpg').convert('RGB')).astype(int)
fg = ~((a.min(2) > 225) & (a.max(2) - a.min(2) < 25))
PEYE, PMOUTH, PTOP, PCHIN = 415.0, 552.0, 129.0, 653.0
MEYE, MMOUTH = 175.2, 156.0; S = (PMOUTH - PEYE) / (MEYE - MMOUTH)          # px per mm
XCP, XCM = 344.0, -2.08                                                         # eye midpoints, photo px / model mm
def prow(zt): return PEYE + (MEYE - zt) * S                                    # target z (mm) -> photo row
rows = np.arange(a.shape[0]); Lp = np.full(len(rows), np.nan); Rp = Lp.copy()
for y in range(int(PTOP), int(PCHIN) + 1):
    xs = np.flatnonzero(fg[y, 20:700]) + 20
    if len(xs): Lp[y] = (xs.min() - XCP) / S + XCM; Rp[y] = (xs.max() - XCP) / S + XCM
# ---- model silhouette (mm) from a front raster ----
X0, X1, Z0, Z1, PPM = -50, 50, 130, 222, 20; W, H = (X1 - X0) * PPM, (Z1 - Z0) * PPM
ctx = gl.create_standalone_context(); fb = ctx.simple_framebuffer((W, H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
p = ctx.program(vertex_shader="""#version 330
uniform vec4 B; in vec3 pos; void main(){gl_Position=vec4((pos.x-B.x)/(B.y-B.x)*2.-1.,(pos.z-B.z)/(B.w-B.z)*2.-1.,(pos.y+80.)/160.,1);}""",
fragment_shader="""#version 330
out vec4 o; void main(){o=vec4(1,1,1,1);}""")
p['B'].value = (X0, X1, Z0, Z1)
ctx.vertex_array(p, [(ctx.buffer(V[F].reshape(-1, 3).astype('f4').tobytes()), '3f', 'pos')]).render() if fb.clear(0, 0, 0, 1, depth=1) is None else None
sil = np.frombuffer(fb.read(), dtype='u1').reshape(H, W, 3)[::-1, :, 0] > 127
zr = Z1 - (np.arange(H) + .5) / PPM; Lm = np.full(H, np.nan); Rm = Lm.copy()
for r in range(H):
    xs = np.flatnonzero(sil[r])
    if len(xs): Lm[r] = X0 + xs.min() / PPM; Rm[r] = X0 + xs.max() / PPM
MTOP = zr[np.isfinite(Lm)].max(); MCHIN = 139.3
# ---- height map: model z -> target z ----
TT = PEYE - (PTOP - PEYE) * 0                                                 # (readability)
ZT_TOP = MEYE + (PEYE - PTOP) / S; ZT_CHIN = MEYE - (PCHIN - PEYE) / S
ZM = np.array([0.0, 136.0, MCHIN, MMOUTH, MEYE, MTOP, MTOP + 50])
ZTg = np.array([0.0, 136.0, ZT_CHIN, MMOUTH, MEYE, ZT_TOP, ZT_TOP + 50])
print('landmarks model -> target: chin %.2f->%.2f  mouth %.1f  eye %.1f  top %.2f->%.2f' % (MCHIN, ZT_CHIN, MMOUTH, MEYE, MTOP, ZT_TOP))
# ---- per-row width maps, smoothed ----
def smooth(v, sig):
    ok = np.isfinite(v); idx = np.arange(len(v)); w = np.interp(idx, idx[ok], v[ok]); return gaussian_filter1d(w, sig)
SIG = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
Lms, Rms = smooth(Lm, SIG * PPM), smooth(Rm, SIG * PPM)
Lps, Rps = smooth(Lp, SIG * S), smooth(Rp, SIG * S)
def model_ext(zz): r = np.clip(((Z1 - zz) * PPM).astype(int), 0, H - 1); return Lms[r], Rms[r]
def photo_ext(zt):
    y = np.clip(prow(zt), PTOP, PCHIN).astype(int); return Lps[y], Rps[y]
# Per-row width scale k(z), shift and silhouette centre, sampled every 1 mm and fitted with quartic polynomials.
# (Sampling the raster per vertex row made a step field and 932 self-intersecting faces in the hair and frames.)
zs = np.arange(138, 221, 1.0); K, SH, CM = [], [], []
for zz in zs:
    lm, rm = model_ext(np.array([zz])); ztt = np.interp(zz, ZM, ZTg); lp, rp = photo_ext(np.array([ztt]))
    K.append(((rp - lp) / (rm - lm))[0]); CM.append(((lm + rm) / 2)[0]); SH.append((((lp + rp) - (lm + rm)) / 2)[0])
pk, ps, pc = np.polyfit(zs, K, 4), np.polyfit(zs, SH, 4), np.polyfit(zs, CM, 4)
zc = np.clip(V[:, 2], 138, 220); k = np.polyval(pk, zc); sh = np.polyval(ps, zc); cmv = np.polyval(pc, zc)
head = V[:, 2] > 134.0
zt = np.interp(V[:, 2], ZM, ZTg)
xn = cmv + sh + (V[:, 0] - cmv) * k
w = np.clip((V[:, 2] - 134.0) / 8.0, 0, 1) * head                         # fade in over z 134..142
MODE = sys.argv[4] if len(sys.argv) > 4 else "xz"
V2 = V.copy()
if "x" in MODE: V2[:, 0] = V[:, 0] + w * (xn - V[:, 0])
if "z" in MODE: V2[:, 2] = V[:, 2] + (zt - V[:, 2]) * (V[:, 2] > 136.0)
print('width scale k(z): %.3f..%.3f, shift %.2f..%.2f mm' % (k[head].min(), k[head].max(), sh[head].min(), sh[head].max()))
# back to 220 mm tall, scaled about the feet centre
s = 220.0 / V2[:, 2].max(); cx = (V2[:, 0].max() + V2[:, 0].min()) / 2; cy = (V2[:, 1].max() + V2[:, 1].min()) / 2
V2[:, 0] = cx + (V2[:, 0] - cx) * s; V2[:, 1] = cy + (V2[:, 1] - cy) * s; V2[:, 2] *= s
t = trimesh.Trimesh(V2, F, process=False)
print('uniform rescale x%.4f | size %s | watertight %s winding %s volume %s bodies %d' % (s, np.round(t.extents, 2), t.is_watertight, t.is_winding_consistent, t.is_volume, t.body_count))
import pymeshlab as ml
ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(vertex_matrix=V2, face_matrix=F)); ms.compute_selection_by_self_intersections_per_face()
print('self-intersecting faces', int(ms.current_mesh().face_selection_array().sum()))
np.savez(dst, v=V2, f=F, l=L); np.save('views/match_scale.npy', np.array([s]))
