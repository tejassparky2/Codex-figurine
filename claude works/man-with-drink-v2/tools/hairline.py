"""Hairline lock (owner round 6: "hair edges not coloured").

The texture paints fine grey strokes over skin along the hairline, so per-face colour calls the sculpted hair strands
skin. Shape decides instead: hair strands are ridged at sub-millimetre scale, forehead skin is smooth. Skin faces close
to the hair whose normals deviate strongly from their 0.7 mm neighbourhood are strands -> silver; then whole strands are
grown and tiny islands cleaned. The glasses frame is untouched (it stays locked silver) and the face centre below the
brows is excluded (nose bridge, eyes).

usage: hairline.py final.npy final.npy [--center-x -3.5] [--half-width 16] [--brow-z 182]
"""
import argparse
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

p = argparse.ArgumentParser()
p.add_argument('src'); p.add_argument('dst')
p.add_argument('--center-x', type=float, default=-3.5, help='face centre x (midpoint of the eyes)')
p.add_argument('--half-width', type=float, default=16.0, help='below brow-z, only |x - centre| beyond this is checked (temples)')
p.add_argument('--brow-z', type=float, default=182.0)
p.add_argument('--near-mm', type=float, default=1.8)
p.add_argument('--rough-deg', type=float, default=6.0)
A = p.parse_args()
SKIN, SILVER = 0, 2
d = np.load('printable.npz'); m = trimesh.Trimesh(d['v'], d['f'], process=False)
c, nrm, area = m.triangles_center, m.face_normals, m.area_faces
lab = np.load(A.src).astype(int); frame = np.load('frame_full.npy'); n = len(c)
hair = (lab == SILVER) & ~frame & (c[:, 2] > 150)
skin = (lab == SKIN) & (c[:, 2] > 150)
dist = np.full(n, 99.0); dist[skin] = cKDTree(c[hair]).query(c[skin], workers=4)[0]
region = skin & (dist < A.near_mm + 1.0) & ((c[:, 2] > A.brow_z) | (np.abs(c[:, 0] - A.center_x) > A.half_width))
tree = cKDTree(c)
idx = np.flatnonzero(region)
rough = np.zeros(n)
for s in range(0, len(idx), 20000):
    sl = idx[s:s + 20000]
    for f, ns in zip(sl, tree.query_ball_point(c[sl], r=.7, workers=4)):
        mn = (nrm[ns] * area[ns, None]).sum(0); mn /= np.linalg.norm(mn) + 1e-12
        rough[f] = np.degrees(np.arccos(np.clip(nrm[f] @ mn, -1, 1)))
# Smooth the roughness over 0.5 mm so single creased triangles do not decide on their own.
rs = rough.copy()
for f, ns in zip(idx, tree.query_ball_point(c[idx], r=.5, workers=4)):
    rs[f] = (rough[ns] * area[ns]).sum() / area[ns].sum()
strand = region & (dist < A.near_mm) & (rs > A.rough_deg)
a, b = m.face_adjacency.T
for _ in range(2):                                   # grow along each strand
    nb = np.bincount(a[strand[b] | hair[b]], minlength=n) + np.bincount(b[strand[a] | hair[a]], minlength=n)
    strand |= region & (nb >= 2) & (dist < A.near_mm + .4) & (rs > A.rough_deg * .6)
out = lab.copy(); out[strand] = SILVER
# Clean-up near the hairline: small skin islands mostly enclosed by silver -> silver; tiny silver specks -> skin.
ev = m.face_adjacency_edges; L = np.linalg.norm(m.vertices[ev[:, 0]] - m.vertices[ev[:, 1]], axis=1)
def comps(l):
    same = l[a] == l[b]
    nc, cc = connected_components(coo_matrix((np.ones(same.sum()), (a[same], b[same])), shape=(n, n)), directed=False)
    return nc, cc, np.bincount(cc, weights=area, minlength=nc)
nc, cc, ar = comps(out); dif = out[a] != out[b]
border = coo_matrix((np.r_[L[dif], L[dif]], (np.r_[cc[a[dif]], cc[b[dif]]], np.r_[out[b[dif]], out[a[dif]]])), shape=(nc, 5)).toarray()
near = (dist < 4) | strand
enclosed = (ar < 1.5) & (border[:, SILVER] > .8 * border.sum(1))
fill = enclosed[cc] & (out == SKIN) & near & (c[:, 2] > 150)
out[fill] = SILVER
# Round the blocky notches of the new hair edge: average the hair/skin decision over 0.6 mm along the boundary band
# and re-threshold (the line does not move on average; 0.5-1 mm square notches become smooth curves).
edge = np.zeros(n, bool); dif = (out[a] != out[b]) & np.isin(out[a], [SKIN, SILVER]) & np.isin(out[b], [SKIN, SILVER])
edge[a[dif]] = edge[b[dif]] = True
bandz = (c[:, 2] > 150) & ((c[:, 2] > A.brow_z) | (np.abs(c[:, 0] - A.center_x) > A.half_width))
smooth = np.flatnonzero(bandz & np.isin(out, [SKIN, SILVER]) & ~frame & (cKDTree(c[edge]).query(c, workers=4)[0] < .8) if edge.any() else np.zeros(n, bool))
for _ in range(2):
    hairish = (out == SILVER).astype(float)
    new = out.copy()
    for fi, ns in zip(smooth, tree.query_ball_point(c[smooth], r=.6, workers=4)):
        new[fi] = SILVER if (hairish[ns] * area[ns]).sum() / area[ns].sum() > .5 else SKIN
    out = new
nc, cc, ar = comps(out)
speck = (ar[cc] < .3) & (out == SILVER) & ~frame & (c[:, 2] > 150)
out[speck] = SKIN
nc, cc, ar = comps(out)
hole = (ar[cc] < .3) & (out == SKIN) & (c[:, 2] > 150) & bandz
out[hole] = SILVER
out[frame] = SILVER
assert np.all(out[frame] == SILVER)
np.save(A.dst, out.astype('u1'))
print(f'hairline: {strand.sum()} strand faces ({area[strand].sum():.1f} mm2) -> silver, {fill.sum()} enclosed skin faces filled, '
      f'{speck.sum()} silver specks removed')
