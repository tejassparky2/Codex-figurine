#!/usr/bin/env bash
# man-with-drink round 2 (Tripo d3a4cb08): full pipeline. Run from this folder with the figurine venv python as $P.
set -euo pipefail
P=${P:-python}; G=inputs-raw/man-with-drink.glb
$P -I tools/make_printable.py $G 220 1000000
$P -I tools/split_planes.py 102.3 95.7
$P -I tools/sample_texture.py $G
$P -I -c 'import numpy as np; np.save("glass_axis.npy", np.array([-8.05, -31.6]))'
$P -I tools/label.py 5
$P -I tools/views.py
$P -I tools/framemask.py
$P -I tools/facecam.py
$P -I tools/detail.py
$P -I tools/leakfix.py 6 12
$P -I tools/part_lock.py leak.npy leak.npy 14 42 -14 28 44 80 0 1 7 10 10 3.0
$P -I tools/finalize.py
$P -I - <<'PY'
import numpy as np, trimesh
z = np.load('printable.npz'); c = trimesh.Trimesh(z['v'], z['f'], process=False).triangles_center
ax = np.load('glass_axis.npy'); rad = np.hypot(c[:,0]-ax[0], c[:,1]-ax[1])
np.save('cs_keep.npy', (c[:,2] > 92) & (c[:,2] < 112) & (rad < 6.6))
PY
$P -I ../../wedding-u1-skill/coloring/contour_split.py printable.npz final.npy cs.npz --keep cs_keep.npy
MESH=cs.npz $P -I tools/export.py
$P -I tools/render_outputs.py
