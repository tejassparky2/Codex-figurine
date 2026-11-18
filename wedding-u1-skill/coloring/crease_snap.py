"""Snap existing paint boundaries onto sculpted creases without any texture: faces in a band of `rings` around
label boundaries may change label; each change costs `prior` x area, each boundary edge costs length x crease weight
(concave sigma 14 deg, convex 45 deg). Protected faces (optional bool mask) never change.
usage: crease_snap.py mesh.npz labels_in.npy labels_out.npy [rings=6] [prior=0.35] [--protect mask.npy] [--only a,b,...]"""
import sys, argparse, numpy as np, trimesh, maxflow
from scipy.sparse import coo_matrix
p = argparse.ArgumentParser(); p.add_argument('mesh'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('rings', nargs='?', type=int, default=6)
p.add_argument('prior', nargs='?', type=float, default=.35); p.add_argument('--protect'); p.add_argument('--only', help='labels allowed to move, e.g. 0,1,2')
A = p.parse_args(); z = np.load(A.mesh); m = trimesh.Trimesh(z['v'], z['f'], process=False); n = len(m.faces); area = m.area_faces
lab = np.load(A.src).astype(int); K = lab.max()+1; movable = np.isin(lab, [int(x) for x in A.only.split(',')]) if A.only else np.ones(n, bool)
if A.protect: movable &= ~np.load(A.protect)
a, b = m.face_adjacency.T; G = coo_matrix((np.ones(2*len(a)), (np.r_[a, b], np.r_[b, a])), shape=(n, n)).tocsr()
band = np.zeros(n, bool); d = lab[a] != lab[b]; band[a[d]] = band[b[d]] = True
for _ in range(A.rings): band |= (G @ band.astype('f4')) > 0
band &= movable; labels = np.unique(lab[band]) if band.any() else []
U = np.full((n, K), 1e9); U[np.arange(n), lab] = 0
for k in labels: U[band, k] = np.where(lab[band] == k, 0, A.prior*area[band])
ev = m.face_adjacency_edges; L = np.linalg.norm(m.vertices[ev[:,0]] - m.vertices[ev[:,1]], axis=1); ang = np.degrees(m.face_adjacency_angles)
w = L * np.where(m.face_adjacency_convex, np.exp(-(ang/45.)**2), np.exp(-(ang/14.)**2)); cur = lab.copy()
for it in range(4):
    ch = 0
    for al in labels:
        li, lj = cur[a], cur[b]; Aa = w*(li != lj); B = w*(li != al); C = w*(lj != al)
        lin = U[:, al] - U[np.arange(n), cur]; np.add.at(lin, a, C-Aa); np.add.at(lin, b, -C)
        g = maxflow.Graph[float](n, len(a)); g.add_nodes(n); g.add_edges(a, b, B+C-Aa, np.zeros(len(a)))
        g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
        new = np.where(g.get_grid_segments(np.arange(n)), al, cur); ch += int((new != cur).sum()); cur = new
    if not ch: break
print('band', int(band.sum()), 'faces changed', int((cur != lab).sum())); np.save(A.dst, cur.astype('u1'))
