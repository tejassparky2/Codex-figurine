"""Decal refine: paint small traced features (irises, lash lines, eye whites) at sub-triangle resolution.

Why: a 1 M-triangle figurine has ~0.35 mm triangle edges. A 2.5-4 mm iris is then only ~8-12 triangles across, and
per-triangle voting plus contour_split turn its round sides into straight slanted lines (owner round 7, man-with-drink:
"make both sides of the pupil round as in the art"). Here the faces inside the given windows are refined (conforming
red-green midpoint subdivision, so no T-junctions and the surface is unchanged) and every sub-face takes the class of the
2-D design map at its own centroid, provided the front camera actually sees that face there (the ID map pixel equals
the sub-face's source face). Hidden sub-faces keep their label.

Inputs:
  mesh.npz  v, f, l and parent (the source printable face of each face; e.g. contour_split output)
  cls.npy   2-D class map from the front orthographic camera (-1 = no decision; other values = labels)
  ids.npy   same-size map of printable face IDs from that camera (-1 = background)
  --cam X0 Z1 PPM   camera mapping: col = (x - X0) * PPM, row = (Z1 - z) * PPM
  --win x0 x1 z0 z1 one or more windows (mm, front view) to refine and repaint
  --levels N        subdivision levels (2 -> edges /4, e.g. 0.35 -> 0.09 mm)
  --lock mask.npy   printable faces never repainted (e.g. the glasses frame)
  --min-mm2 A       islands under A mm2 inside the windows merge into their longest-border neighbour (default 0.08)
usage: decal_refine.py cs.npz views/face_cls.npy views/face_id.npy out.npz --cam -28 204 40 --win -21.5 -7.5 166.3 171.8 [--win ...]
Asserts: 0 open edges, surface area unchanged (1e-9 relative).
"""
import argparse
import numpy as np
import trimesh

p = argparse.ArgumentParser()
p.add_argument('mesh'); p.add_argument('cls'); p.add_argument('ids'); p.add_argument('out')
p.add_argument('--cam', type=float, nargs=3, required=True)
p.add_argument('--win', type=float, nargs=4, action='append', required=True)
p.add_argument('--levels', type=int, default=2)
p.add_argument('--lock')
p.add_argument('--min-mm2', type=float, default=.08, help='islands smaller than this inside the windows are merged')
A = p.parse_args()
z = np.load(A.mesh); v = np.asarray(z['v'], float); f = np.asarray(z['f'], np.int64)
l = np.asarray(z['l']).astype(np.int64); par = np.asarray(z['parent'] if 'parent' in z.files else np.arange(len(f)), np.int64)
cls = np.load(A.cls); ids = np.load(A.ids); H, W = ids.shape; X0, Z1, PPM = A.cam
lock = np.load(A.lock) if A.lock else None
area0 = trimesh.Trimesh(v, f, process=False).area
seen = np.zeros(int(max(par.max(), ids.max())) + 1, bool); seen[ids[ids >= 0]] = True


def in_win(pts):
    k = np.zeros(len(pts), bool)
    for x0, x1, z0, z1 in A.win:
        k |= (pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 2] >= z0) & (pts[:, 2] <= z1)
    return k


def refine(v, f, l, par, sel):
    """One conforming level: selected faces -> 4; faces with one split edge -> 2; closure so no face has 2+ split edges."""
    nf = len(f); e = np.sort(np.stack([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]], 1), axis=2)   # (nf, 3, 2)
    key = e[..., 0] * (len(v) + 1) + e[..., 1]
    uk, inv = np.unique(key.ravel(), return_inverse=True); inv = inv.reshape(nf, 3)
    while True:
        marked = np.zeros(len(uk), bool); marked[inv[sel].ravel()] = True
        cnt = marked[inv].sum(1); grow = ~sel & (cnt >= 2)
        if not grow.any():
            break
        sel = sel | grow
    ue = np.stack([uk // (len(v) + 1), uk % (len(v) + 1)], 1)
    mid = np.full(len(uk), -1, np.int64); mi = np.flatnonzero(marked)
    mid[mi] = len(v) + np.arange(len(mi)); v = np.r_[v, v[ue[mi]].mean(1)]
    a, b, c = f[:, 0], f[:, 1], f[:, 2]; mab, mbc, mca = mid[inv[:, 0]], mid[inv[:, 1]], mid[inv[:, 2]]
    out_f, out_i = [f[~sel & (cnt == 0)]], [np.flatnonzero(~sel & (cnt == 0))]
    s = np.flatnonzero(sel)
    for tri in ([a, mab, mca], [mab, b, mbc], [mca, mbc, c], [mab, mbc, mca]):
        out_f.append(np.stack([t[s] for t in tri], 1)); out_i.append(s)
    one = ~sel & (cnt == 1)
    for which, (m_, p0, p1, opp) in enumerate([(mab, a, b, c), (mbc, b, c, a), (mca, c, a, b)]):
        q = np.flatnonzero(one & (m_ >= 0))
        out_f += [np.stack([p0[q], m_[q], opp[q]], 1), np.stack([m_[q], p1[q], opp[q]], 1)]; out_i += [q, q]
    idx = np.concatenate(out_i)
    return v, np.concatenate(out_f), l[idx], par[idx]


for _ in range(A.levels):
    cen = v[f].mean(1); vis = seen[par] & in_win(cen)
    if lock is not None:
        vis &= ~lock[par]
    v, f, l, par = refine(v, f, l, par, vis)
cen = v[f].mean(1)
col = np.floor((cen[:, 0] - X0) * PPM).astype(int); row = np.floor((Z1 - cen[:, 2]) * PPM).astype(int)
ok = in_win(cen) & (col >= 0) & (col < W) & (row >= 0) & (row < H)
ok[ok] &= (ids[row[ok], col[ok]] == par[ok]) & (cls[row[ok], col[ok]] >= 0)
if lock is not None:
    ok &= ~lock[par]
new = l.copy(); new[ok] = cls[row[ok], col[ok]]
m = trimesh.Trimesh(v, f, process=False)
# Specks: pixel aliasing and hidden sub-faces at visibility edges leave islands of a few sub-faces. Inside the windows,
# every island under --min-mm2 takes the label it shares the longest border with (repeated until none is left).
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
fa, fb = m.face_adjacency.T; ev = m.face_adjacency_edges; EL = np.linalg.norm(v[ev[:, 0]] - v[ev[:, 1]], axis=1)
inw = in_win(cen); fixed = 0; K = int(new.max()) + 1
for _ in range(6):
    same = new[fa] == new[fb]
    nc, cc = connected_components(coo_matrix((np.ones(same.sum()), (fa[same], fb[same])), shape=(len(f),) * 2), directed=False)
    ar = np.bincount(cc, weights=m.area_faces, minlength=nc)
    win_cc = np.bincount(cc, weights=inw.astype(float), minlength=nc) > 0
    small = (ar < A.min_mm2) & win_cc
    if not small.any():
        break
    d = ~same; B = coo_matrix((np.r_[EL[d], EL[d]], (np.r_[cc[fa[d]], cc[fb[d]]], np.r_[new[fb[d]], new[fa[d]]])), shape=(nc, K)).toarray()
    tgt = B.argmax(1); chg = small[cc] & ~((lock[par]) if lock is not None else np.zeros(len(f), bool))
    fixed += chg.sum(); new[chg] = tgt[cc[chg]]
assert len(trimesh.grouping.group_rows(np.sort(m.edges, 1), require_count=1)) == 0, 'open edges'
assert abs(m.area - area0) / area0 < 1e-9, 'area changed'
np.savez(A.out, v=v, f=f, l=new.astype('u1'), parent=par)
print(f'decal refine: {len(z["f"])} -> {len(f)} faces | repainted {ok.sum()} sub-faces, labels changed {(new != l).sum()}, '
      f'{fixed} speck sub-faces merged | '
      f'watertight, area {m.area:.6f} = {area0:.6f} mm2')
