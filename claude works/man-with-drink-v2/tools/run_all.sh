#!/usr/bin/env bash
# Full man-with-drink pipeline from inputs-raw/ to out/. Run from the job folder with the figurine venv's python as $P.
set -euo pipefail
P=${P:-python}; G=inputs-raw/man-with-drink-v2.glb
$P -I tools/make_printable.py $G 220 1000000
$P -I tools/glass_axis.py                     # fits the tumbler axis and radius on this mesh
$P -I tools/split_planes.py 99.0
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
# owner round 6: sculpted hair strands at the hairline are hair (silver), found by surface roughness
$P -I tools/hairline.py final.npy final.npy
# contour split: smooth cut edges through triangles; the glass zone keeps its exact plane-split liquid line
$P -I - <<'PY'
import numpy as np, trimesh
z = np.load('printable.npz'); c = trimesh.Trimesh(z['v'], z['f'], process=False).triangles_center
ax = np.load('glass_axis.npy'); rad = np.hypot(c[:,0]-ax[0], c[:,1]-ax[1])
np.save('cs_keep.npy', (c[:,2] > 86.5) & (c[:,2] < 105.5) & (rad < ax[2] + .91))
PY
$P -I ../../wedding-u1-skill/coloring/contour_split.py printable.npz final.npy cs.npz --keep cs_keep.npy
# owner round 7: irises and lash lines painted at sub-triangle resolution from the traced 2-D design (round sides)
$P -I ../../wedding-u1-skill/coloring/decal_refine.py cs.npz views/face_cls.npy views/face_id.npy cs2.npz --cam -28 204 40 \
   --win -21.5 -7.5 166.6 171.4 --win 1.5 13.4 169.4 173.6 --levels 2 --lock frame_full.npy
MESH=cs2.npz $P -I tools/export.py
$P -I tools/render_outputs.py
$P -I regression/check_round6.py out/Man-with-drink-220mm-finish-guide.3mf
$P -I regression/check_round7.py out/Man-with-drink-220mm-finish-guide.3mf
