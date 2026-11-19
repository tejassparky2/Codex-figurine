"""Fit the tumbler's vertical axis and wall radius from the printable mesh (no texture needed).

Candidates: near-vertical faces in front of the torso at drink height. RANSAC over 3-point circles in XY, scored by
faces whose normals point radially out from the candidate axis, then a least-squares (Kasa) refinement on the inliers.
Writes glass_axis.npy = [cx, cy, r] and prints the wall's z range.
usage: glass_axis.py [z_lo z_hi]   (defaults 80 112)
"""
import sys
import numpy as np
import trimesh

z_lo, z_hi = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (80.0, 112.0)
d = np.load('printable.npz'); m = trimesh.Trimesh(d['v'], d['f'], process=False)
c, n = m.triangles_center, m.face_normals
cand = np.flatnonzero((c[:, 2] > z_lo) & (c[:, 2] < z_hi) & (np.abs(n[:, 2]) < .3) & (c[:, 1] < -12))
P, N = c[cand, :2], n[cand, :2] / np.linalg.norm(n[cand, :2], axis=1, keepdims=True)
rng = np.random.default_rng(0)


def score(cx, cy, r):
    v = P - [cx, cy]; d = np.linalg.norm(v, axis=1)
    radial = (v * N).sum(1) / np.maximum(d, 1e-9)
    return (np.abs(d - r) < .25) & (radial > .85)


best = (0, None)
for _ in range(4000):
    a, b, e = P[rng.choice(len(P), 3, replace=False)]
    A = np.array([[b[0] - a[0], b[1] - a[1]], [e[0] - a[0], e[1] - a[1]]]) * 2
    rhs = np.array([b @ b - a @ a, e @ e - a @ a])
    if abs(np.linalg.det(A)) < 1e-6:
        continue
    cx, cy = np.linalg.solve(A, rhs); r = np.hypot(*(a - [cx, cy]))
    if not 5.0 < r < 9.0:
        continue
    k = score(cx, cy, r).sum()
    if k > best[0]:
        best = (k, (cx, cy, r))
cx, cy, r = best[1]
for _ in range(3):                                   # Kasa least-squares refinement on the inliers
    inl = score(cx, cy, r); x, y = P[inl, 0], P[inl, 1]
    M = np.c_[x, y, np.ones_like(x)]; sol = np.linalg.lstsq(M, x * x + y * y, rcond=None)[0]
    cx, cy = sol[0] / 2, sol[1] / 2; r = np.sqrt(sol[2] + cx * cx + cy * cy)
inl = score(cx, cy, r)
zs = c[cand[inl], 2]
np.save('glass_axis.npy', np.array([cx, cy, r]))
print(f'axis ({cx:.3f}, {cy:.3f}) radius {r:.3f} mm | {inl.sum()} wall faces | wall z {zs.min():.2f}..{zs.max():.2f} mm')
