"""Family finish labels from materials_e.npy: 0 skin, 1 black, 2 white, 3 navy, 4 light blue, 5 red, 6 royal blue, 7 gold.
brown hair -> black (owner default: black hair); cream (her shoes, his shirt collar) -> white.
Islands under MIN mm2 merge into the neighbour with the longest shared edge (small detail labels 1, 3, 5, 6, 7 keep
islands down to DET mm2 so irises, buttons and stars survive). Writes final.npy."""
import sys, numpy as np, trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
MIN, DET = 0.6, 0.25
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False); area = m.area_faces; n = len(area)
mat = np.load('materials_e.npy').astype(int)
lab = mat.copy()
ei, ej = m.face_adjacency.T; ev = m.face_adjacency_edges; L = np.linalg.norm(m.vertices[ev[:,0]] - m.vertices[ev[:,1]], axis=1)
K = 8
for _ in range(6):
    same = lab[ei] == lab[ej]; nc, comp = connected_components(coo_matrix((np.ones(same.sum()), (ei[same], ej[same])), shape=(n, n)), directed=False)
    ca = np.bincount(comp, weights=area, minlength=nc); cl = np.zeros(nc, int); cl[comp] = lab
    thr = np.where(np.isin(cl, [1, 2, 5, 6, 7]), DET, MIN); small = (ca < thr)[comp]
    d = ~same; a_, b_ = ei[d], ej[d]; rows = np.r_[comp[a_], comp[b_]]; nb = np.r_[lab[b_], lab[a_]]; ln = np.r_[L[d], L[d]]; k = small[np.r_[a_, b_]]
    M = coo_matrix((ln[k], (rows[k], nb[k])), shape=(nc, K)).toarray(); new = np.where(small & (M[comp].sum(1) > 0), M.argmax(1)[comp], lab)
    step = int((new != lab).sum()); lab = new
    print('island merge: %d faces changed' % step)
    if not step: break
np.save('final.npy', lab.astype('u1'))
N = ['skin', 'black', 'white', 'navy', 'lightblue', 'red', 'royalblue', 'gold']
for k in range(K): print('%-7s %8.1f mm2' % (N[k], area[lab == k].sum()))
