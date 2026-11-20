"""Transplant Codex's mouth (codex/figurine-evidence-sprint, portrait-smile) onto our model.

Codex started from our cs_match10.npz (identical triangles and paint), then re-fitted the whole figure and
sculpted the smile (refined-smile/revise.py + portrait-smile/revise.py). Only the mouth is wanted, so:
  1. fit an affine map Codex -> ours on a ring of face vertices around the mouth (both meshes agree there
     up to Codex's smooth global reshape),
  2. inside the mouth ellipse use the affine-mapped Codex vertex, fading to our own vertex at the ring.
Topology and labels are ours (cs_match10), so the result is watertight by construction.

usage: codex_mouth.py ours.npz codex_portrait.npz out.npz [up_mm] [smooth_iter]
"""
import sys, numpy as np
ours, codex, out = sys.argv[1:4]
z = np.load(ours); V, F, L = z['v'], z['f'], z['l'].astype(int)
C = np.load(codex)['v']
assert C.shape == V.shape and np.array_equal(np.load(codex)['f'], F), 'Codex mesh is not cs_match10 topology'

c = V[F].mean(1)
teeth = (L == 3) & (c[:, 2] > 140) & (c[:, 2] < 165) & (c[:, 1] < -10)
tv = V[np.unique(F[teeth])]
mx, mz = (tv[:, 0].min() + tv[:, 0].max()) / 2, np.median(tv[:, 2])
AX = 26.0                                                    # mouth ellipse (mm): smile corners
AZU = float(sys.argv[4]) if len(sys.argv) > 4 else 6.0      # upward: stop under the nose/glasses (Codex's face fairing crosses the rims there)
AZD = 14.0                                                   # downward: lower lip + chin top
x, y, zz = V.T
r = np.sqrt(((x - mx) / AX) ** 2 + ((zz - mz) / np.where(zz > mz, AZU, AZD)) ** 2)
front = y < np.percentile(tv[:, 1], 50) + 14                 # the face, never the back of the head
def smooth(q): q = np.clip(q, 0, 1); return q * q * (3 - 2 * q)
w = smooth((1.0 - r) / 0.35) * front                          # 1 inside r<0.65, 0 at r>=1
ring = front & (r > 1.0) & (r < 1.45)
A = np.c_[C[ring], np.ones(ring.sum())]
M = np.linalg.lstsq(A, V[ring], rcond=None)[0]
mapped = np.c_[C, np.ones(len(C))] @ M
res = np.linalg.norm(mapped[ring] - V[ring], axis=1)
print('mouth centre x %.2f z %.2f | ring %d verts, affine residual mean %.3f p95 %.3f mm' % (mx, mz, ring.sum(), res.mean(), np.percentile(res, 95)))
print('linear part', np.round(M[:3], 3).tolist())
D = w[:, None] * (mapped - V)
# Codex's file is crinkly at triangle level (hidden by its smooth-shaded render, visible in flat previews and in print).
# Keep its shape, not its noise: diffuse the displacement over the mesh (umbrella smoothing of D, region only).
ITER = int(sys.argv[5]) if len(sys.argv) > 5 else 60
from scipy.sparse import coo_matrix
ii = F[:, [0, 1, 2, 1, 2, 0]].ravel(); jj = F[:, [1, 2, 0, 0, 1, 2]].ravel()
Adj = coo_matrix((np.ones(len(ii)), (ii, jj)), shape=(len(V), len(V))).tocsr(); deg = np.asarray(Adj.sum(1)).ravel()
act = np.flatnonzero(w > 0)
for _ in range(ITER):
    avg = (Adj @ D) / deg[:, None]
    D[act] += 0.6 * (avg[act] - D[act])
D *= smooth((1.0 - r) / 0.12)[:, None] * front[:, None]       # exactly ours outside the ellipse
NV = V + D
d = np.linalg.norm(NV - V, axis=1)
print('moved %d verts, max %.2f mm, mean (w>0) %.3f mm' % ((d > 1e-6).sum(), d.max(), d[w > 0].mean()))
np.savez(out, v=NV, f=F, l=z['l'])
