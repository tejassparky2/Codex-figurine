"""Contour split: replace per-triangle sawtooth paint edges with smooth cuts through the triangles.
Ported from the local figurines session (projects/maroon_refine.py in tejassparky2/Figurine), vectorised.

Each filament's area-weighted share is averaged onto the vertices. Vertex colours (argmax) set the topology.
A smoother copy of the share field (T_ITER one-ring averages) places one cut point on every edge whose two ends
differ; the point is shared by both neighbouring triangles, so the mesh stays watertight and conforming and the
surface itself is unchanged. Two-colour triangles become 3 triangles; three-colour triangles get a centroid and 6.
Faces whose own colour is not among their corners' colours keep that colour (protects single-face dots).

usage: contour_split.py mesh.npz labels.npy out.npz [--iter 0] [--t-iter 4] [--protect-folds DEG] [--keep mask.npy]
--keep: faces whose edges are already exact (e.g. from split_planes) are left untouched; cuts are also blocked on
any edge a kept face touches, propagated until stable, so no T-junctions can form.
mesh.npz has v (mm) and f; out.npz has v, f, l (uint8 labels), parent (source face of each new face).
Regression (asserted): 0 open edges, same body count, surface area unchanged to 1e-6 (relative)."""
import argparse, numpy as np, trimesh
from scipy.sparse import coo_matrix, diags, identity
p = argparse.ArgumentParser(); p.add_argument('mesh'); p.add_argument('labels'); p.add_argument('out')
p.add_argument('--iter', type=int, default=0, help='smoothing of the vertex-colour field (0 keeps thin crescents)')
p.add_argument('--t-iter', type=int, default=4, help='smoothing used only for cut positions')
p.add_argument('--protect-folds', type=float, default=0, help='concave dihedral (deg); vertices on such folds are not smoothed for cut positions')
p.add_argument('--keep', help='bool face mask to leave untouched (exact plane-split boundaries)')
A = p.parse_args()
z = np.load(A.mesh); v = np.asarray(z['v'], float); f = np.asarray(z['f'], np.int64); lab = np.load(A.labels).astype(np.int64)
m0 = trimesh.Trimesh(v, f, process=False); area = m0.area_faces; nv, nf, K = len(v), len(f), int(lab.max()) + 1
# share of each label at each vertex (area weighted)
Fv = coo_matrix((np.repeat(area, 3), (f.ravel(), np.repeat(np.arange(nf), 3))), shape=(nv, nf)).tocsr()
Fv = diags(1/np.maximum(np.asarray(Fv.sum(1)).ravel(), 1e-30)) @ Fv
X = np.asarray(Fv @ np.eye(K)[lab])
e = np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]
Av = coo_matrix((np.ones(2*len(e)), (np.r_[e[:,0], e[:,1]], np.r_[e[:,1], e[:,0]])), shape=(nv, nv)).tocsr(); Av.data[:] = 1
Av = Av + identity(nv, format='csr'); Av = diags(1/np.asarray(Av.sum(1)).ravel()) @ Av
for _ in range(A.iter): X = Av @ X
Lv = X.argmax(1)
Xs = X.copy()
fold = np.zeros(nv, bool)
if A.protect_folds > 0:
    ang = np.degrees(m0.face_adjacency_angles); conc = ~m0.face_adjacency_convex & (ang > A.protect_folds)
    fold[m0.face_adjacency_edges[conc].ravel()] = True
for _ in range(A.t_iter):
    S = Av @ Xs; Xs = np.where(fold[:, None], Xs, S)
# one cut point per edge whose ends differ
ue = np.unique(np.sort(e, 1), axis=0); cut = ue[Lv[ue[:,0]] != Lv[ue[:,1]]]
a, b = cut[:,0], cut[:,1]; la, lb = Lv[a], Lv[b]
pa = Xs[a, la] - Xs[a, lb]; pb = Xs[b, la] - Xs[b, lb]
t = np.clip(pa / np.where(np.abs(pa - pb) < 1e-12, 1, pa - pb), .05, .95)
P = v[a]*(1-t)[:,None] + v[b]*t[:,None]
key = a*nv + b; order = np.argsort(key); key = key[order]; eid = nv + order   # new vertex id per cut edge
def epoint(x, y):
    lo, hi = np.minimum(x, y), np.maximum(x, y); k = lo*nv + hi; i = np.searchsorted(key, k); assert np.all(key[i] == k); return eid[i]
V = np.vstack([v, P]); L3 = Lv[f]; nlab = (L3[:,0] != L3[:,1]).astype(int) + (L3[:,1] != L3[:,2]) + (L3[:,0] != L3[:,2])
one = nlab == 0; three = nlab == 3; two = ~one & ~three
kept = np.load(A.keep).astype(bool) if A.keep else np.zeros(nf, bool)
if kept.any():
    # A face may only be split if none of its cut edges is shared with a kept face; iterate to a fixed point.
    fe = np.sort(np.stack([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]], 1), 2); fkey = fe[..., 0]*nv + fe[..., 1]
    diff = np.stack([L3[:,0] != L3[:,1], L3[:,1] != L3[:,2], L3[:,2] != L3[:,0]], 1)
    while True:
        blocked = np.unique(fkey[kept].ravel())
        need = (np.isin(fkey, blocked) & diff).any(1) & ~one & ~kept
        if not need.any(): break
        kept |= need
    one = one | kept; two &= ~kept; three &= ~kept
    print('kept faces (untouched):', int(kept.sum()))
own = (L3 == lab[:, None]).any(1)
outF, outL, outP = [f[one]], [np.where(kept[one] | (L3[one, 0] != lab[one]), lab[one], L3[one, 0])], [np.flatnonzero(one)]
# two-colour faces: rotate (never reorder) so the odd corner comes first
i2 = np.flatnonzero(two); c2 = f[i2]; l2 = L3[i2]
k = np.where(l2[:,1] == l2[:,2], 0, np.where(l2[:,0] == l2[:,2], 1, 2))
r = np.stack([np.take_along_axis(c2, ((k + j) % 3)[:, None], 1).ravel() for j in range(3)], 1)
pq, pr = epoint(r[:,0], r[:,1]), epoint(r[:,0], r[:,2]); lp, lq = Lv[r[:,0]], Lv[r[:,1]]
keep = ~own[i2]; lp = np.where(keep, lab[i2], lp); lq = np.where(keep, lab[i2], lq)
outF += [np.c_[r[:,0], pq, pr], np.c_[pq, r[:,1], r[:,2]], np.c_[pq, r[:,2], pr]]; outL += [lp, lq, lq]; outP += [i2]*3
# three-colour faces: centroid plus 6 triangles
i3 = np.flatnonzero(three); c3 = f[i3]; mid = len(V) + np.arange(len(i3)); V = np.vstack([V, v[c3].mean(1)])
e01, e12, e20 = epoint(c3[:,0], c3[:,1]), epoint(c3[:,1], c3[:,2]), epoint(c3[:,2], c3[:,0])
for c, en, ep in [(c3[:,0], e01, e20), (c3[:,1], e12, e01), (c3[:,2], e20, e12)]:
    outF += [np.c_[c, en, mid], np.c_[c, mid, ep]]; outL += [Lv[c]]*2; outP += [i3]*2
F = np.vstack(outF); L = np.concatenate(outL).astype(np.uint8); par = np.concatenate(outP)
used = np.zeros(len(V), bool); used[F.ravel()] = True; remap = np.cumsum(used) - 1; V = V[used]; F = remap[F]
m1 = trimesh.Trimesh(V, F, process=False)
edges = np.sort(m1.edges, 1); _, cnt = np.unique(edges, axis=0, return_counts=True)
assert np.all(cnt == 2), f'open or non-manifold edges: {(cnt != 2).sum()}'
assert m1.body_count == m0.body_count, (m1.body_count, m0.body_count)
assert abs(m1.area - m0.area) <= 1e-6*m0.area, (m1.area, m0.area)
assert m1.is_winding_consistent
print(f'contour split: {nf} -> {len(F)} faces, {len(cut)} cut edges, {len(i3)} three-colour faces | '
      f'watertight, {m1.body_count} body, area {m1.area:.6f} = {m0.area:.6f} mm2 | '
      f'faces whose label changed vs parent: {int((L != lab[par]).sum())}')
np.savez(A.out, v=V, f=F.astype(np.int32), l=L, parent=par.astype(np.int32))
