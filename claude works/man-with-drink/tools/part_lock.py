"""Part lock: separate a thin part from the thick body it touches by geometry, not texture.
Cone thickness (9 inward rays, shortest exit, embree) inside a box; in a band of `rings` around the current boundary
between THIN_LABEL and THICK_LABEL, faces thinner than `thin_mm` cost nothing as the thin label, faces thicker than
`thick_mm` cost nothing as the thick label, and an alpha-expansion with a strong concave-crease prior places the edge.
usage: part_lock.py in.npy out.npy  x0 x1 y0 y1 z0 z1  thin_label thick_label thin_mm thick_mm [rings] [lam]"""
import sys, numpy as np, trimesh, maxflow
from scipy.sparse import coo_matrix
src, dst = sys.argv[1:3]; x0, x1, y0, y1, z0, z1 = map(float, sys.argv[3:9]); tl, kl = int(sys.argv[9]), int(sys.argv[10])
thin_mm, thick_mm = float(sys.argv[11]), float(sys.argv[12]); rings = int(sys.argv[13]) if len(sys.argv) > 13 else 6; lam = float(sys.argv[14]) if len(sys.argv) > 14 else 2.0
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False); c = m.triangles_center; nrm = m.face_normals; n = len(c); area = m.area_faces
lab = np.load(src).astype(int)
box = (c[:,0] > x0) & (c[:,0] < x1) & (c[:,1] > y0) & (c[:,1] < y1) & (c[:,2] > z0) & (c[:,2] < z1)
reg = np.flatnonzero(box); nn = nrm[reg]; a_ = np.where(np.abs(nn[:, :1]) < .9, [[1., 0, 0]], [[0, 1., 0]])
t1 = np.cross(nn, a_); t1 /= np.linalg.norm(t1, axis=1, keepdims=True); t2 = np.cross(nn, t1); org = c[reg] - nn*2e-3
th = np.full(len(reg), 99.)
for d in [-nn] + [-(np.cos(.7)*nn + np.sin(.7)*(np.cos(k)*t1 + np.sin(k)*t2)) for k in np.linspace(0, 2*np.pi, 8, endpoint=False)]:
    loc, ri, _ = m.ray.intersects_location(org, d, multiple_hits=False); np.minimum.at(th, ri, np.linalg.norm(loc - org[ri], axis=1))
thick = np.full(n, 99.); thick[reg] = th
a, b = m.face_adjacency.T; G = coo_matrix((np.ones(2*len(a)), (np.r_[a, b], np.r_[b, a])), shape=(n, n)).tocsr()
bd = np.zeros(n, bool); d = ((lab[a] == tl) & (lab[b] == kl)) | ((lab[a] == kl) & (lab[b] == tl)); bd[a[d]] = bd[b[d]] = True
band = bd.copy()
for _ in range(rings): band |= (G @ band.astype('f4')) > 0
band &= box & np.isin(lab, [tl, kl])
U = np.full((n, 2), 1e9); cur = (lab == kl).astype(int)               # 0 = thin label, 1 = thick label
U[band, 0] = area[band]*(thick[band] > thick_mm); U[band, 1] = area[band]*(thick[band] < thin_mm)
U[~band, :] = 1e9; U[~band, cur[~band]] = 0
ev = m.face_adjacency_edges; Ln = np.linalg.norm(m.vertices[ev[:,0]] - m.vertices[ev[:,1]], axis=1); ang = np.degrees(m.face_adjacency_angles)
w = lam * Ln * np.where(m.face_adjacency_convex, np.exp(-(ang/45.)**2), np.exp(-(ang/14.)**2))
# binary labelling: one exact min-cut
lin = U[:, 1] - U[:, 0]
g = maxflow.Graph[float](n, len(a)); g.add_nodes(n); g.add_edges(a, b, w, w)
g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
new = g.get_grid_segments(np.arange(n)).astype(int)
out = lab.copy(); out[band] = np.where(new[band] == 1, kl, tl)
print(f'part lock: band {band.sum()} faces, changed {int((out != lab).sum())} '
      f'({int(((out == tl) & (lab == kl)).sum())} -> thin label, {int(((out == kl) & (lab == tl)).sum())} -> thick label)')
np.save(dst, out.astype('u1'))
