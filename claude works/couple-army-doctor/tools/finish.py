"""Finish labels from materials_e.npy: 0 skin, 1 black, 2 green, 3 white, 4 yellow, 5 gold, 6 red, 7 silver.
brown hair -> black (owner default: black hair); cream (her shoes, his shirt collar) -> white.
Islands under MIN mm2 merge into the neighbour with the longest shared edge (small detail labels 1, 3, 5, 6, 7 keep
islands down to DET mm2 so irises, buttons and stars survive). Writes final.npy."""
import sys, numpy as np, trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
MIN, DET = 0.6, 0.25
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False); area = m.area_faces; n = len(area)
mat = np.load('materials_e.npy').astype(int)
lab = np.array([0, 1, 2, 3, 4, 5, 6, 3, 1, 7])[mat]
ei, ej = m.face_adjacency.T; ev = m.face_adjacency_edges; L = np.linalg.norm(m.vertices[ev[:,0]] - m.vertices[ev[:,1]], axis=1)
K = 8
# his tie knot is a separate green island inside the white collar; the tie is black (art)
c = m.triangles_center; g = lab == 2; k = g[ei] & g[ej]
nc, comp = connected_components(coo_matrix((np.ones(k.sum()), (ei[k], ej[k])), shape=(n, n)), directed=False)
for i in np.unique(comp[g]):
    t = g & (comp == i); A = area[t].sum(); cc = c[t].mean(0)
    if A < 40 and -7.5 < cc[0] < -2 and 115.5 < cc[2] < 121.5 and cc[1] < -5:
        lab[t] = 1; print('tie knot green -> black: %.1f mm2' % A)
for _ in range(6):
    same = lab[ei] == lab[ej]; nc, comp = connected_components(coo_matrix((np.ones(same.sum()), (ei[same], ej[same])), shape=(n, n)), directed=False)
    ca = np.bincount(comp, weights=area, minlength=nc); cl = np.zeros(nc, int); cl[comp] = lab
    thr = np.where(np.isin(cl, [1, 3, 5, 6, 7]), DET, MIN); small = (ca < thr)[comp]
    d = ~same; a_, b_ = ei[d], ej[d]; rows = np.r_[comp[a_], comp[b_]]; nb = np.r_[lab[b_], lab[a_]]; ln = np.r_[L[d], L[d]]; k = small[np.r_[a_, b_]]
    M = coo_matrix((ln[k], (rows[k], nb[k])), shape=(nc, K)).toarray(); new = np.where(small & (M[comp].sum(1) > 0), M.argmax(1)[comp], lab)
    step = int((new != lab).sum()); lab = new
    print('island merge: %d faces changed' % step)
    if not step: break
np.save('final.npy', lab.astype('u1'))
N = ['skin', 'black', 'green', 'white', 'yellow', 'gold', 'red', 'silver']
for k in range(K): print('%-7s %8.1f mm2' % (N[k], area[lab == k].sum()))
