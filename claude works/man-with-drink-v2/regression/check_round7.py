"""Regression test for owner review round 7 (2026-11-19): "hand still there and make both sides of the pupil round as in
the art photo".

Reads an exported finish guide (Orca paint 3MF) and checks:
  1. little finger under the glass: up-facing faces below the glass underside plane (z < GB, inside r+0.6 mm) carry
     no orange/silver (the glass has no up-facing surface there; those faces are the top of the little finger);
  2. round irises: a front orthographic render of the painted labels (silver hidden so the glasses do not occlude) is
     taken over each eye. The iris (black with white on both sides on the same row, so the lash line is excluded) must
     be widest between 20 % and 80 % of its height and at least 2 % narrower in both its top and bottom quarters (convex
     sides). A bowl (widest at the top lid, the delivered round-6 shape) or a straight bar fails.
Exit 0 = PASS, 1 = FAIL. Run from the job folder (needs glass_axis.npy).
usage: check_round7.py out/Man-with-drink-220mm-finish-guide.3mf [--save crops.png]
"""
import re
import sys
import zipfile

import moderngl as gl
import numpy as np
import trimesh
from scipy import ndimage

CODES = ['4', '8', '0C', '1C', '2C']          # finish slots: skin, black, silver, orange, white
SKIN, BLACK, SILVER, ORANGE, WHITE = range(5)
with zipfile.ZipFile(sys.argv[1]) as zf:
    s = zf.read('3D/3dmodel.model')
v = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', s), float)
f = np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), int)
lab = np.array([CODES.index(c.decode()) for c in re.findall(rb'paint_color="([^"]+)"', s)])
m = trimesh.Trimesh(v, f, process=False); c, n, A = m.triangles_center, m.face_normals, m.area_faces
# The 3MF sits on the bed; bring it back to model coordinates (x, y centred on the body, z from 0).
lo, hi = v.min(0), v.max(0); off = np.r_[(lo[:2] + hi[:2]) / 2, lo[2]]
P = np.load('printable.npz')['v']; off -= np.r_[(P[:, :2].min(0) + P[:, :2].max(0)) / 2, P[:, 2].min()]
v = v - off; c = c - off
ax = np.load('glass_axis.npy'); r = ax[2]
vv = c[:, :2] - ax[:2]; rad = np.linalg.norm(vv, axis=1); radial = (vv * n[:, :2]).sum(1) / np.maximum(rad, 1e-9)
wall = c[(np.abs(rad - r) < .25) & (radial > .6) & (c[:, 2] > 80) & (c[:, 2] < 112), 2]
GB = np.percentile(wall, 1)
ok = True
finger = (rad < r + .6) & (c[:, 2] < GB - .05) & (c[:, 2] > GB - 4) & (n[:, 2] > .2)
leak = A[finger & np.isin(lab, [SILVER, ORANGE])].sum()
print(f'1. little finger under the glass: orange/silver {leak:.3f} mm2 (limit 0.05)'); ok &= leak < .05

X0, X1, Z0, Z1, PPM = -28, 28, 140, 204, 40; W, H = (X1 - X0) * PPM, (Z1 - Z0) * PPM
ctx = gl.create_standalone_context(backend='egl'); fb = ctx.simple_framebuffer((W, H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
prog = ctx.program(vertex_shader="""#version 330
uniform vec4 B; in vec3 pos; in float lb; flat out int l;
void main(){gl_Position=vec4((pos.x-B.x)/(B.y-B.x)*2.-1.,(pos.z-B.z)/(B.w-B.z)*2.-1.,(pos.y+60.)/120.,1); l=int(lb);}""",
                   fragment_shader="""#version 330
flat in int l; out vec4 o; void main(){o=vec4(float(l+1)/255.,0,0,1);}""")
prog['B'].value = (X0, X1, Z0, Z1)
k = np.flatnonzero((lab != SILVER) & (c[:, 2] > 140))
tri = v[f[k]].astype('f4').reshape(-1, 3); lb = np.repeat(lab[k], 3).astype('f4')
vao = ctx.vertex_array(prog, [(ctx.buffer(tri.tobytes()), '3f', 'pos'), (ctx.buffer(lb.tobytes()), '1f', 'lb')])
fb.clear(); vao.render()
img = np.frombuffer(fb.read(), 'u1').reshape(H, W, 3)[::-1, :, 0].astype(int) - 1
EYES = {'his right': (-21.5, -7.5, 166.6, 171.4), 'his left': (1.5, 13.4, 169.4, 173.6)}
crops = []
for nm, (x0, x1, z0, z1) in EYES.items():
    sub = img[int((Z1 - z1) * PPM):int((Z1 - z0) * PPM), int((x0 - X0) * PPM):int((x1 - X0) * PPM)]; crops.append(sub)
    # Iris = black pixels with white both to their left and right on the same row (this drops the lash line along the
    # lid, which has skin on one side), largest connected blob; width per row = its pixel count on that row.
    wh = sub == WHITE
    wl = np.maximum.accumulate(wh, axis=1); wr = np.maximum.accumulate(wh[:, ::-1], axis=1)[:, ::-1]
    lb_, nb = ndimage.label((sub == BLACK) & wl & wr)
    if nb == 0:
        print(f'2. {nm}: no iris with white on both sides -> FAIL'); ok = False; continue
    blob = lb_ == (1 + int(np.argmax(ndimage.sum(np.ones_like(lb_), lb_, range(1, nb + 1)))))
    prof = blob.sum(1).astype(float); prof = prof[prof > 0]; h = len(prof) - 1
    if "--debug" in sys.argv: print(nm, prof.astype(int).tolist())
    sm = np.convolve(np.pad(prof, 2, mode='edge'), np.ones(5) / 5, mode='valid') if len(prof) > 5 else prof; mx = sm.max()
    at = int(np.argmax(sm)) / max(h, 1); q = max(1, len(sm) // 4)
    top, bot = sm[:q].min() / mx, sm[-q:].min() / mx
    good = (.2 <= at <= .8) and top < .98 and bot < .98
    print(f'2. {nm} iris: widest at {at:.2f} of its height (0.2-0.8), narrowest in top quarter {top:.3f} and bottom '
          f'quarter {bot:.3f} of max (< 0.98) -> {"ok" if good else "FAIL"}')
    ok &= good
if '--save' in sys.argv:
    from PIL import Image
    pal = np.array([(230, 186, 168), (14, 14, 16), (140, 151, 157), (249, 168, 0), (241, 236, 225), (255, 255, 255)], 'u1')
    hh = max(x.shape[0] for x in crops); row = np.full((hh, sum(x.shape[1] for x in crops) + 20), 5)
    row[:crops[0].shape[0], :crops[0].shape[1]] = crops[0]; row[:crops[1].shape[0], crops[0].shape[1] + 20:] = crops[1]
    Image.fromarray(pal[np.where(row < 0, 5, row)]).save(sys.argv[sys.argv.index('--save') + 1])
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
