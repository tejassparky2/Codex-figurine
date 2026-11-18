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
$P -I tools/export.py
$P -I tools/render_outputs.py
