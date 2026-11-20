"""Owner (r4): "reduce whisky quantity and reduce the eyebrows".
1. Whisky: split every triangle crossing z = LIQ exactly (shared edge points, watertight), then orange faces above LIQ
   inside the glass become silver. LIQ 106.0 mm = about half the glass (97.1-115.7), like the art.
2. Brows: black faces above z 182.6 (the eyes' black ends at ~182.5) within ERODE mm of a non-brow face become skin,
   so each brow shrinks evenly on all sides (thinner and a little shorter, same shape).
usage: whisky_brows.py in.npz out.npz [liquid_z] [erode_mm]"""
import sys, numpy as np, trimesh
from scipy.spatial import cKDTree
src, dst = sys.argv[1], sys.argv[2]; LIQ = float(sys.argv[3]) if len(sys.argv) > 3 else 106.0; ER = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
z = np.load(src); V, F, L = z['v'].astype('f8').copy(), z['f'].astype('i8'), z['l'].astype(int)
c = V[F].mean(1); o = L == 4; ax = c[o][:, :2].mean(0)
# --- 1. plane split at LIQ, labels inherited ---
near = np.abs(V[:, 2] - LIQ) < 1e-4; V[near, 2] = LIQ
s = np.sign(np.round(V[:, 2] - LIQ, 9)).astype(int)
e = np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1); e = np.unique(e[(s[e[:, 0]] * s[e[:, 1]]) < 0], axis=0)
t = (LIQ - V[e[:, 0], 2]) / (V[e[:, 1], 2] - V[e[:, 0], 2]); P = V[e[:, 0]] + t[:, None] * (V[e[:, 1]] - V[e[:, 0]])
newid = {tuple(k): len(V) + i for i, k in enumerate(e)}; V = np.vstack([V, P])
outF, outL = [], []
for f, lab in zip(F, L):
    sf = s[f]
    if not ((sf > 0).any() and (sf < 0).any()): outF.append(f); outL.append(lab); continue
    for r in range(3):
        g = np.roll(f, -r); sg = s[g]
        if sg[0] == 0 and sg[1] * sg[2] < 0:
            mm = newid[tuple(sorted((g[1], g[2])))]; outF += [[g[0], g[1], mm], [g[0], mm, g[2]]]; outL += [lab, lab]; break
        if sg[0] != 0 and sg[1] == sg[2] == -sg[0]:
            m1 = newid[tuple(sorted((g[0], g[1])))]; m2 = newid[tuple(sorted((g[0], g[2])))]
            outF += [[g[0], m1, m2], [m1, g[1], g[2]], [m1, g[2], m2]]; outL += [lab, lab, lab]; break
F = np.asarray(outF); L = np.asarray(outL); c = V[F].mean(1)
r = np.hypot(c[:, 0] - ax[0], c[:, 1] - ax[1])
up = (L == 4) & (c[:, 2] > LIQ) & (r < 9.0); L[up] = 2
print('liquid line %.1f mm: split %d edges, orange above -> silver %d faces; orange now z %.2f..%.2f' % (LIQ, len(e), int(up.sum()), c[L == 4, 2].min(), c[L == 4, 2].max()))
# --- 2. brows erosion ---
brow = (L == 1) & (c[:, 2] > 182.6) & (c[:, 1] < -10) & (np.abs(c[:, 0]) < 30)
reg = (c[:, 2] > 178) & (c[:, 2] < 196) & (np.abs(c[:, 0]) < 32) & (c[:, 1] < -5)
other = reg & ~brow
d = cKDTree(c[other]).query(c[brow])[0]
bi = np.flatnonzero(brow); shrink = bi[d < ER]
area = trimesh.Trimesh(V, F, process=False).area_faces
print('brows: %d faces, %.1f mm2 -> remove %d faces (%.1f mm2), keep %.1f mm2' % (len(bi), area[bi].sum(), len(shrink), area[shrink].sum(), area[bi].sum() - area[shrink].sum()))
L[shrink] = 0
tm = trimesh.Trimesh(V, F, process=False)
print('watertight', tm.is_watertight, 'winding', tm.is_winding_consistent, 'volume', tm.is_volume, 'bodies', tm.body_count, 'faces', len(F))
np.savez(dst, v=V, f=F.astype('i4'), l=L.astype('u1'))
