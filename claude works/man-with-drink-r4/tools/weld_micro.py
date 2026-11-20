"""Merge vertex clusters closer than TOL mm (boolean micro-slivers) and drop the zero-area faces they leave, keeping
per-face labels; then require watertight, 2 faces per edge (also after verify_3mf's 1e-5 weld), 0 self-intersections.
usage: weld_micro.py in.npz out.npz [tol=1e-4]"""
import sys, numpy as np, trimesh, pymeshlab
src, dst = sys.argv[1], sys.argv[2]; TOL = float(sys.argv[3]) if len(sys.argv) > 3 else 1e-4
z = np.load(src); V, F, L = z['v'], z['f'], z['l'].astype(int)
from scipy.sparse.csgraph import connected_components
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree
pairs = np.array(sorted(cKDTree(V).query_pairs(TOL)))
if len(pairs):
    g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(V), len(V)))
    _, comp = connected_components(g, directed=False)
    rep = np.zeros(comp.max() + 1, int) - 1
    for i in range(len(V)):
        if rep[comp[i]] < 0: rep[comp[i]] = i
    remap = rep[comp]
else:
    remap = np.arange(len(V))
F2 = remap[F]
keep = (F2[:, 0] != F2[:, 1]) & (F2[:, 1] != F2[:, 2]) & (F2[:, 2] != F2[:, 0])
F2, L2 = F2[keep], L[keep]
used, inv = np.unique(F2, return_inverse=True); V2 = V[used]; F2 = inv.reshape(F2.shape)
print('clusters merged: %d vertex pairs < %g mm; dropped %d collapsed faces' % (len(pairs), TOL, (~keep).sum()))
m = trimesh.Trimesh(V2, F2, process=False)
cnt = np.bincount(m.edges_unique_inverse)
ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(V2, F2)); ms.compute_selection_by_self_intersections_per_face()
si = ms.current_mesh().selected_face_number()
key = np.round(V2, 5); _, wi = np.unique(key, axis=0, return_inverse=True); wf = np.asarray(wi).ravel()[F2]
es = np.sort(np.vstack([wf[:, [0, 1]], wf[:, [1, 2]], wf[:, [2, 0]]]), axis=1); _, wc = np.unique(es, axis=0, return_counts=True)
print('watertight', m.is_watertight, 'volume', m.is_volume, 'bodies', m.body_count, '| edges !=2: %d | after 1e-5 weld non-manifold %d open %d | self-int %d'
      % ((cnt != 2).sum(), (wc > 2).sum(), (wc == 1).sum(), si))
assert m.is_watertight and m.is_volume and m.body_count == 1 and (cnt == 2).all() and (wc == 2).all() and si == 0
np.savez(dst, v=V2, f=F2.astype('i4'), l=L2.astype('u1'))
