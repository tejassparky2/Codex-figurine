"""Two-tone hair (owner round 9: "two colours hair as in the art"): silver base, Pure White highlights on tuft crests.

The generated texture stripes every tuft with fine light/dark strands; copied per face that prints as speckle. The art
reads as light tuft tops over darker grooves, so the highlight is decided by shape:
  score = crest offset (face centre above the mean surface within --r mm, along its normal, in units of its spread)
          + --up x how much the face looks toward the key light (top front)
The top --frac of hair area by score becomes white, then it is made printable: morphological opening by --open-mm
(no strip narrower than ~2x that), islands under --min-island mm2 dropped, silver holes under --min-hole mm2 filled.
Kept silver: a --edge-mm band along the hairline (round 6 strand edge) and around the glasses frame, and the frame.
usage: hair_tone.py final.npy final.npy [--frac .18] [--r 1.5] [--up .25] [--open-mm .45] [--min-island 2.0]
"""
import argparse
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

p = argparse.ArgumentParser()
p.add_argument('src'); p.add_argument('dst')
p.add_argument('--frac', type=float, default=.18); p.add_argument('--r', type=float, default=1.5)
p.add_argument('--up', type=float, default=.25); p.add_argument('--open-mm', type=float, default=.45)
p.add_argument('--min-island', type=float, default=2.0); p.add_argument('--min-hole', type=float, default=1.0)
p.add_argument('--edge-mm', type=float, default=1.0); p.add_argument('--zmin', type=float, default=150.0)
A = p.parse_args()
SKIN, SILVER, WHITE = 0, 2, 3
d = np.load('printable.npz'); m = trimesh.Trimesh(d['v'], d['f'], process=False)
c, nrm, area = m.triangles_center, m.face_normals, m.area_faces; n = len(c)
lab = np.load(A.src).astype(int); frame = np.load('frame_full.npy')
hair = (lab == SILVER) & ~frame & (c[:, 2] > A.zmin)
hi = np.flatnonzero(hair); tree = cKDTree(c[hi])
off = np.zeros(n)
for s in range(0, len(hi), 20000):
    sl = hi[s:s + 20000]
    for f, ns in zip(sl, tree.query_ball_point(c[sl], r=A.r, workers=4)):
        j = hi[ns]; mu = (c[j] * area[j, None]).sum(0) / area[j].sum()
        off[f] = (c[f] - mu) @ nrm[f]
key = np.array([0, -.55, .83]); key /= np.linalg.norm(key)
score = np.zeros(n); score[hi] = off[hi] / off[hi].std() + A.up * np.clip(nrm[hi] @ key, 0, None) / .5
# keep a silver band along the hairline and around the frame
others = (lab != SILVER) | frame
dist = np.full(n, 99.0); dist[hi] = cKDTree(c[others & (c[:, 2] > A.zmin - 5)]).query(c[hi], workers=4)[0]
cand = hair & (dist > A.edge_mm)
o = np.argsort(-score[hi]); cum = np.cumsum(area[hi][o]); thr = score[hi][o][np.searchsorted(cum, A.frac * area[hi].sum())]
white = cand & (score >= thr)
# opening: erode then dilate by open-mm (geodesic approximated by 3-D distance within the hair)
ct = cKDTree(c[hi]); wi = np.flatnonzero(white[hi])
notw = hi[~white[hi]]
dn = np.full(n, 99.0)
if len(notw): dn[hi] = cKDTree(c[notw]).query(c[hi], workers=4)[0]
core = white & (dn > A.open_mm)
dc = np.full(n, 99.0)
if core.any(): dc[hi] = cKDTree(c[core]).query(c[hi], workers=4)[0]
white = white & (dc <= A.open_mm + .05)
a, b = m.face_adjacency.T
def comps(mask):
    same = mask[a] & mask[b]
    nc, cc = connected_components(coo_matrix((np.ones(same.sum()), (a[same], b[same])), shape=(n, n)), directed=False)
    return cc, np.bincount(cc, weights=area, minlength=nc)
cc, ar = comps(white); white &= ar[cc] >= A.min_island
cc, ar = comps(hair & ~white); hole = hair & ~white & (ar[cc] < A.min_hole); white |= hole & cand
out = lab.copy(); out[white] = WHITE; out[frame] = SILVER
assert np.all(out[frame] == SILVER)
np.save(A.dst, out.astype('u1'))
cc, ar = comps(white)
isl = ar[np.unique(cc[white])] if white.any() else np.zeros(0)
print(f'hair tone: {white.sum()} faces white = {area[white].sum():.1f} mm2 ({area[white].sum() / area[hi].sum() * 100:.1f} % of hair), '
      f'{len(isl)} islands, smallest {isl.min() if len(isl) else 0:.2f} mm2, holes filled {hole.sum()}')
