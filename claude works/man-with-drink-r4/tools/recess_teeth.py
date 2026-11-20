"""Owner 2026-11-20: "the photo has depth of mouth but the model don't have it". The teeth sat ~1 mm behind the
upper lip, nearly flush. Push the teeth back (+y) by DEPTH mm so the lips frame them: tooth vertices move fully,
the fall-off reaches 0 within FADE mm of the teeth, and only material at or behind the tooth face moves (lips and
cheeks in front never move). Then relax any self-intersections back toward the original.
usage: recess_teeth.py in.npz out.npz [depth=1.2] [fade=1.0]"""
import sys, numpy as np, pymeshlab
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
src, dst = sys.argv[1], sys.argv[2]
DEPTH = float(sys.argv[3]) if len(sys.argv) > 3 else 1.2; FADE = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
z = np.load(src); V, F, L = z['v'], z['f'], z['l'].astype(int)
c = V[F].mean(1)
tf = (L == 3) & (c[:, 1] < -15) & (c[:, 2] > 150) & (c[:, 2] < 170)
tv = np.unique(F[tf]); T = V[tv]
yfront = np.percentile(T[:, 1], 5)
d, _ = cKDTree(T).query(V, distance_upper_bound=FADE + 0.5)
def sm(q): q = np.clip(q, 0, 1); return q * q * (3 - 2 * q)
w = sm(1 - np.nan_to_num(d, posinf=99) / FADE) * sm((V[:, 1] - (yfront - 0.3)) / 0.4)     # behind the tooth face only
w[tv] = 1.0
D = np.zeros_like(V); D[:, 1] = DEPTH * w
ii = F[:, [0, 1, 2, 1, 2, 0]].ravel(); jj = F[:, [1, 2, 0, 0, 1, 2]].ravel()
A = coo_matrix((np.ones(len(ii)), (ii, jj)), shape=(len(V), len(V))).tocsr()
for it in range(40):
    ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(V + D, F)); ms.compute_selection_by_self_intersections_per_face()
    bad_f = ms.current_mesh().face_selection_array()
    print('pass %d: self-intersecting faces %d' % (it, bad_f.sum()))
    if not bad_f.any(): break
    bad = np.zeros(len(V), bool); bad[np.unique(F[bad_f])] = True
    for _ in range(2): bad |= (A @ bad.astype(float)) > 0
    D[bad] *= 0.7
assert not bad_f.any()
print('teeth: %d vertices, front y %.2f -> %.2f; moved %d vertices, mean tooth recess %.2f mm' % (
    len(tv), yfront, np.percentile((V + D)[tv, 1], 5), (D[:, 1] > 1e-6).sum(), D[tv, 1].mean()))
np.savez(dst, v=V + D, f=F, l=z['l'])
