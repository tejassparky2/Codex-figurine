"""Owner (r4): "eyebrows not good". Replace the brows with clean shapes traced on the customer image
(renders/photo-brows-grid.png): thick at the inner end, tapering to the outer tip. Photo px -> model mm with the
head-match transform (eye line 415 px = 175.2 mm, 7.135 px/mm, x centre 344 px = -2.08 mm, x1.0218 rescale), then
shifted by DX/DZ per brow if needed. Old brow black (above z 182.6) becomes skin; front-facing faces inside the new
outline (smoothed curve, sampled finely) become black. Frame/silver faces are never touched.
usage: redraw_brows.py in.npz out.npz [dx_mm dz_mm] [scale]"""
import sys, numpy as np, trimesh
from matplotlib.path import Path as MPath
src, dst = sys.argv[1], sys.argv[2]
DX = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0; DZ = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0; SC = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
z = np.load(src); V, F, L = z['v'], z['f'], z['l'].astype(int).copy()
m = trimesh.Trimesh(V, F, process=False); c = m.triangles_center; n = m.face_normals
S, XCM, s = 137 / 19.2, -2.08, 1.0218
def to_mm(p): p = np.asarray(p, float); return np.c_[((p[:, 0] - 344) / S + XCM) * s, (175.2 - (p[:, 1] - 415) / S) * s]
# traced outlines (photo px), closed loops: top edge outer->inner, then bottom edge inner->outer
BROW_R = [(223,388),(240,368),(260,361),(280,360),(298,360),(306,364),(304,369),(280,370),(260,373),(240,380),(226,386)]
BROW_L = [(363,353),(372,346),(400,345),(430,349),(448,356),(454,360),(440,359),(410,355),(380,357),(363,360)]
def smooth_loop(pts, k=12):
    P = np.asarray(pts, float); out = []
    for i in range(len(P)):                                   # Catmull-Rom through the traced points
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % len(P)], P[(i + 2) % len(P)]
        for t in np.linspace(0, 1, k, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)
old = (L == 1) & (c[:, 2] > 182.6) & (c[:, 1] < -10) & (np.abs(c[:, 0]) < 30)
L[old] = 0
win = (c[:, 2] > 178) & (c[:, 2] < 198) & (np.abs(c[:, 0]) < 30) & (c[:, 1] < -12) & (n[:, 1] < -0.15) & (L == 0)
new = np.zeros(len(F), bool); outl = []
for pts in (BROW_R, BROW_L):
    q = to_mm(smooth_loop(pts)); cen = q.mean(0); q = cen + (q - cen) * SC + [DX, DZ]; outl.append(q)
    new |= win & MPath(q).contains_points(c[:, [0, 2]])
L[new] = 1
area = m.area_faces
print('old brow faces -> skin %d (%.1f mm2); new brows %d faces (%.1f mm2)' % (old.sum(), area[old].sum(), new.sum(), area[new].sum()))
for nm, q in zip(('his right', 'his left'), outl): print(nm, 'brow x %.1f..%.1f z %.1f..%.1f' % (q[:, 0].min(), q[:, 0].max(), q[:, 1].min(), q[:, 1].max()))
np.savez(dst, v=V, f=F, l=L.astype('u1')); np.save('views/brow_outlines.npy', np.array(outl, dtype=object), allow_pickle=True)
