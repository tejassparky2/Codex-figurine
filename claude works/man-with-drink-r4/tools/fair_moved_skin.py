"""Taubin-smooth only the front-facing skin that codex_mouth_formula.py moved (the stretched smile corners),
never the teeth, the lip slit or anything that did not move. Then confirm 0 self-intersections.
usage: fair_moved_skin.py base.npz moved.npz out.npz [iters]"""
import sys, numpy as np, pymeshlab
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree
b = np.load(sys.argv[1]); z = np.load(sys.argv[2]); V0, V, F, L = b['v'], z['v'].copy(), z['f'], z['l'].astype(int)
IT = int(sys.argv[4]) if len(sys.argv) > 4 else 10
n = np.cross(V[F][:, 1] - V[F][:, 0], V[F][:, 2] - V[F][:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
ok_face = (L == 0) & (n[:, 1] < -0.55)                         # skin facing the camera (-y)
bad_v = np.zeros(len(V), bool); bad_v[np.unique(F[~ok_face])] = True
teeth_v = np.unique(F[L == 3])
d_t, _ = cKDTree(V[teeth_v]).query(V, distance_upper_bound=1.2); near_teeth = np.isfinite(d_t)
moved = np.linalg.norm(V - V0, axis=1) > 0.05
ii = F[:, [0, 1, 2, 1, 2, 0]].ravel(); jj = F[:, [1, 2, 0, 0, 1, 2]].ravel()
A = coo_matrix((np.ones(len(ii)), (ii, jj)), shape=(len(V), len(V))).tocsr(); deg = np.asarray(A.sum(1)).ravel()
for _ in range(4): bad_v |= (A @ bad_v.astype(float)) > 0      # keep a margin from the lip slit / inner mouth
act = np.flatnonzero(moved & ~bad_v & ~near_teeth)
for _ in range(IT):
    for lam in (0.5, -0.53):
        V[act] += lam * ((A @ V)[act] / deg[act, None] - V[act])
ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(V, F)); ms.compute_selection_by_self_intersections_per_face()
si = ms.current_mesh().selected_face_number()
print('faired %d vertices, %d Taubin passes, max shift %.3f mm | self-intersecting faces %d' % (len(act), IT, np.linalg.norm(V - z['v'], axis=1).max(), si))
assert si == 0
np.savez(sys.argv[3], v=V, f=F, l=z['l'])
