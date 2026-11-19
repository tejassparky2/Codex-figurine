"""Regression test for owner review round 6 (2026-11-19): "colour leaks on finger and hair edges not coloured".

Reads an exported finish guide (Orca paint 3MF) and checks, by geometry:
  1. finger contact band just outside the glass wall (r+0.25 .. r+0.8 mm, below the rim lip) carries no orange/silver,
  2. the glass rim lip (top 1.2 mm, within r+1.0 mm) is entirely silver (no skin band, no dark specks),
  3. ridged (hair-strand) skin 0.35-1.8 mm from the hair along the hairline is below 5 mm2.
Exit 0 = PASS, 1 = FAIL. Run from the job folder (needs glass_axis.npy).
usage: check_round6.py out/Man-with-drink-220mm-finish-guide.3mf
"""
import re
import sys
import zipfile

import numpy as np
import trimesh
from scipy.spatial import cKDTree

CODES = ['4', '8', '0C', '1C', '2C']          # finish slots: skin, black, silver, orange, white
SKIN, BLACK, SILVER, ORANGE = 0, 1, 2, 3
with zipfile.ZipFile(sys.argv[1]) as z:
    s = z.read('3D/3dmodel.model')
v = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', s), float)
f = np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), int)
lab = np.array([CODES.index(c.decode()) for c in re.findall(rb'paint_color="([^"]+)"', s)])
m = trimesh.Trimesh(v, f, process=False); c, n, A = m.triangles_center, m.face_normals, m.area_faces
ax = np.load('glass_axis.npy'); r = ax[2]
vv = c[:, :2] - ax[:2]; rad = np.linalg.norm(vv, axis=1); radial = (vv * n[:, :2]).sum(1) / np.maximum(rad, 1e-9)
wall = c[(np.abs(rad - r) < .25) & (radial > .6) & (c[:, 2] > 80) & (c[:, 2] < 112), 2]
GB, GT = np.percentile(wall, 1), np.percentile(wall, 99)
ok = True
band = (rad > r + .25) & (rad < r + .8) & (c[:, 2] > GB + .6) & (c[:, 2] < GT - 1.8)
leak = A[band & np.isin(lab, [SILVER, ORANGE])].sum()
print(f'1. finger contact band: orange/silver {leak:.2f} mm2 (limit 0.5)'); ok &= leak < .5
rim = (rad < r + 1.0) & (c[:, 2] > GT - 1.2) & (c[:, 2] < GT + .6)
bad = A[rim & (lab != SILVER)].sum()
print(f'2. rim lip: non-silver {bad:.2f} mm2 of {A[rim].sum():.1f} mm2 (limit 0.5)'); ok &= bad < .5
hair = (lab == SILVER) & (c[:, 2] > 150) & (np.abs(c[:, 0] - (-3.5)) > 0)   # frame included; restricted below
skin = (lab == SKIN) & (c[:, 2] > 150)
d = np.full(len(c), 99.); d[skin] = cKDTree(c[hair]).query(c[skin], workers=4)[0]
# Faces within 0.35 mm of the hair sit on the sculpted step of the hair edge itself and are always ridged; the defect
# was strands painted skin further out (up to ~1.8 mm), so only that band is measured.
cand = skin & (d > .35) & (d < 1.8) & ((c[:, 2] > 182) | ((np.abs(c[:, 0] + 3.5) > 16) & (c[:, 2] > 176)))
tree = cKDTree(c); idx = np.flatnonzero(cand); rough = np.zeros(len(c))
for st in range(0, len(idx), 20000):
    sl = idx[st:st + 20000]
    for fi, ns in zip(sl, tree.query_ball_point(c[sl], r=.7, workers=4)):
        mn = (n[ns] * A[ns, None]).sum(0); mn /= np.linalg.norm(mn) + 1e-12
        rough[fi] = np.degrees(np.arccos(np.clip(n[fi] @ mn, -1, 1)))
ridged = A[cand & (rough > 12)].sum()
print(f'3. ridged skin at the hairline: {ridged:.1f} mm2 (limit 5)'); ok &= ridged < 5
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
