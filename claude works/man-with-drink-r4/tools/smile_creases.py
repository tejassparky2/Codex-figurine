"""Customer/owner (r4): the photo's smile corners curl up into short creases; add them "same as photo".
Each crease: a curve in front view (x, z) starting at the model's mouth corner, shaped by offsets measured on the
customer image (photo px / 7.135 px/mm x 1.0218): his right corner curls up and out, his left corner turns up.
Front-facing vertices near the curve are pushed in along -normal: depth D*(1-0.6t)*exp(-d^2/2sigma^2),
t = position along the curve (0 at the corner). Vertices only; labels unchanged.
usage: smile_creases.py in.npz out.npz [depth_mm] [sigma_mm]"""
import sys, numpy as np, trimesh
src, dst = sys.argv[1], sys.argv[2]; D = float(sys.argv[3]) if len(sys.argv) > 3 else 0.45; SG = float(sys.argv[4]) if len(sys.argv) > 4 else 0.28
z = np.load(src); V = z['v'].astype('f8').copy(); F = z['f']; L = z['l']
m = trimesh.Trimesh(V, F, process=False); vn = m.vertex_normals
k = 1.0218 * (float(sys.argv[5]) if len(sys.argv) > 5 else 1.0)   # optional length factor
CURVES = [(np.array([-9.86, 159.11]), np.array([(0, 0), (-1.40, 0.84), (-2.52, 1.68), (-2.94, 2.80)]) * k),
          (np.array([7.22, 161.36]),  np.array([(0, 0), (0.84, 0.56), (1.68, 1.54), (2.10, 2.66)]) * k)]
cand = np.flatnonzero((vn[:, 1] < -0.25) & (np.abs(V[:, 0]) < 20) & (V[:, 2] > 150) & (V[:, 2] < 172) & (V[:, 1] < -18))
P = V[cand][:, [0, 2]]; disp = np.zeros(len(cand))
for corner, offs in CURVES:
    pts = corner + offs
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]; ln = seg[-1]
    s = np.linspace(0, ln, 200); cur = np.c_[np.interp(s, seg, pts[:, 0]), np.interp(s, seg, pts[:, 1])]
    d2 = ((P[:, None, :] - cur[None, :, :]) ** 2).sum(2); j = d2.argmin(1); dmin = np.sqrt(d2[np.arange(len(P)), j]); t = s[j] / ln
    disp = np.maximum(disp, D * (1 - 0.6 * t) * np.exp(-dmin ** 2 / (2 * SG ** 2)) * (dmin < 3 * SG))
# keep clear of the mouth slot and teeth: fade the groove to zero within 1 mm of any non-skin mouth face vertex
from scipy.spatial import cKDTree
cf = V[F].mean(1); mouth = np.isin(L, [3, 5]) & (cf[:, 2] > 150) & (cf[:, 2] < 172) & (np.abs(cf[:, 0]) < 20)
dm = cKDTree(V[np.unique(F[mouth])]).query(V[cand])[0]
fade = np.clip((dm - 0.4) / 0.6, 0, 1); fade = fade * fade * (3 - 2 * fade); disp *= fade
V[cand] -= vn[cand] * disp[:, None]
# clean the groove: N rounds (default 2) of Laplacian smoothing on the moved vertices and one ring around them (rest fixed)
mv = np.zeros(len(V), bool); mv[cand[disp > 0.02]] = True
E = np.unique(np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1), axis=0)
ring = mv.copy(); hit = ring[E[:, 0]] | ring[E[:, 1]]; ring[E[hit].ravel()] = True
EE = E[ring[E[:, 0]] | ring[E[:, 1]]]
for _ in range(int(sys.argv[6]) if len(sys.argv) > 6 else 2):
    acc = np.zeros((len(V), 3)); cnt = np.zeros(len(V))
    np.add.at(acc, EE[:, 0], V[EE[:, 1]]); np.add.at(acc, EE[:, 1], V[EE[:, 0]]); np.add.at(cnt, EE[:, 0], 1); np.add.at(cnt, EE[:, 1], 1)
    sel = ring & (cnt > 0); V[sel] += 0.5 * (acc[sel] / cnt[sel, None] - V[sel])
t = trimesh.Trimesh(V, F, process=False)
print('crease depth %.2f sigma %.2f | moved vertices %d (max %.2f mm) | watertight %s winding %s volume %s bodies %d' % (D, SG, int((disp > 0.02).sum()), disp.max(), t.is_watertight, t.is_winding_consistent, t.is_volume, t.body_count))
import pymeshlab as ml
ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(vertex_matrix=V, face_matrix=F)); ms.compute_selection_by_self_intersections_per_face()
print('self-intersecting faces', int(ms.current_mesh().face_selection_array().sum()))
np.savez(dst, v=V, f=F, l=L)
