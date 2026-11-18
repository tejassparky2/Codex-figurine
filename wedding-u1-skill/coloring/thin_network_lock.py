"""Lock a thin wire-like part (glasses frames, wire jewellery, straps) to one colour by geometry.
Cone thickness: 9 inward rays (axis + 8 at 40 deg), shortest exit distance (embree). A free-standing or
half-buried wire exits within ~1.5x its diameter in some direction; skin over a skull does not.
The largest connected thin network(s) inside the box become the part.
usage: thin_network_lock.py mesh.npz x0 x1 y0 y1 z0 z1 max_mm min_faces out_mask.npy [labels_in.npy label labels_out.npy]
Apply the mask as the LAST step of a pipeline so later passes cannot paint over it."""
import sys, numpy as np, trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
mesh = sys.argv[1]; x0, x1, y0, y1, z0, z1, tmax = map(float, sys.argv[2:9]); nmin = int(sys.argv[9]); out = sys.argv[10]
z = np.load(mesh); m = trimesh.Trimesh(z['v'], z['f'], process=False); c = m.triangles_center; nrm = m.face_normals
reg = np.flatnonzero((c[:,0] > x0) & (c[:,0] < x1) & (c[:,1] > y0) & (c[:,1] < y1) & (c[:,2] > z0) & (c[:,2] < z1))
n = nrm[reg]; a_ = np.where(np.abs(n[:, :1]) < .9, [[1., 0, 0]], [[0, 1., 0]]); t1 = np.cross(n, a_); t1 /= np.linalg.norm(t1, axis=1, keepdims=True); t2 = np.cross(n, t1)
org = c[reg] - n*2e-3; best = np.full(len(reg), 99.)
for d in [-n] + [-(np.cos(np.deg2rad(40))*n + np.sin(np.deg2rad(40))*(np.cos(k)*t1 + np.sin(k)*t2)) for k in np.linspace(0, 2*np.pi, 8, endpoint=False)]:
    loc, ri, _ = m.ray.intersects_location(org, d, multiple_hits=False); np.minimum.at(best, ri, np.linalg.norm(loc - org[ri], axis=1))
thin = np.zeros(len(c), bool); thin[reg] = best < tmax
a, b = m.face_adjacency.T; e = thin[a] & thin[b]
nc, cc = connected_components(coo_matrix((np.ones(e.sum()), (a[e], b[e])), shape=(len(c),)*2), directed=False)
keep = np.bincount(cc[thin], minlength=nc) >= nmin; mask = thin & keep[cc]
np.save(out, mask); print('thin faces', int(thin.sum()), '| part faces', int(mask.sum()), '| networks kept', int(keep.sum()))
if len(sys.argv) > 13:
    lab = np.load(sys.argv[11]).copy(); k = int(sys.argv[12]); print('faces repainted', int((lab[mask] != k).sum())); lab[mask] = k; np.save(sys.argv[13], lab)
