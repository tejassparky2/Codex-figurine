#!/usr/bin/env bash
# Full man-with-drink pipeline from inputs-raw/ to out/. Run from the job folder with the figurine venv's python as $P.
set -euo pipefail
P=${P:-python}; G=inputs-raw/man-with-drink.glb
$P -I tools/make_printable.py $G 220 1000000
$P -I tools/split_planes.py 97.4 91.0
$P -I tools/sample_texture.py $G
$P -I tools/label.py 5
$P -I tools/views.py
$P -I tools/framemask.py
$P -I tools/facecam.py
$P -I tools/detail.py
$P -I tools/leakfix.py 6 12
# part lock: his left thumb/hand (thin) against the trouser leg (thick)
$P -I tools/part_lock.py leak.npy leak.npy 14 42 -12 26 44 80 0 1 7 10 10 3.0
$P -I tools/finalize.py
# contour split: smooth cut edges through triangles; the glass zone keeps its exact plane-split liquid line
$P -I - <<'PY'
import numpy as np, trimesh
z = np.load('printable.npz'); c = trimesh.Trimesh(z['v'], z['f'], process=False).triangles_center
ax = np.load('glass_axis.npy'); rad = np.hypot(c[:,0]-ax[0], c[:,1]-ax[1])
np.save('cs_keep.npy', (c[:,2] > 86.5) & (c[:,2] < 105.5) & (rad < 7.6))
PY
$P -I ../../wedding-u1-skill/coloring/contour_split.py printable.npz final.npy cs.npz --keep cs_keep.npy
MESH=cs.npz $P -I tools/export.py
$P -I tools/render_outputs.py
