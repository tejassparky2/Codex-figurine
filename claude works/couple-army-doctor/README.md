# Couple (army officer + doctor): 150 mm, Snapmaker U1

Customer photos, the Tripo model and all renders stay local (this repo is public). Local delivery: figurines `projects/couple_army_doctor/out/`.

## Chain (run from this folder with the e3d venv)
1. `make_printable.py inputs-raw/couple.glb 150 1000000`: Tripo 3d964c6f, multi-view front+back; 1.0 M faces, watertight, 1 body.
2. `sample_texture.py inputs-raw/couple.glb` → `views.py`.
3. `label.py 4`: 10 materials by graph cut with region limits:
   - yellow only on her;
   - gold only on his jacket;
   - red only on her dress front;
   - cream only on her shoes and his collar.
4. `faces.py 0.6`: face-only skin/black/white re-solve. The broad pass merged his eyes with his brows and lost her brows.
5. `eyes.py`: printed eyes (owner rule): white socket, round black iris at the texture iris, upper lash line. Her faint brows are drawn as solid arcs at the texture's brow band. His closed smile has no white.
6. `finish.py`: brown hair → black, cream → white, his tie knot → black, island merge (0.6 mm², details 0.25 mm²).
7. `contour_split.py printable.npz final.npy cs.npz` (wedding-u1-skill/coloring).
8. `export_couple.py`: finish guide (8 colours) + U1 project (4 heads, 3 pauses, ≥0.25 mm clearance each side, asserted).
9. `render_outputs.py`: previews from the finish guide.

## Print plan
- **Heads at the start:** T1 Pure White, T2 Yellow #FFCC33, T3 Black, T4 Apricot (skin, whole print).
- **Pauses:**
  - 6.9 mm: T1 white → green (her shoes end 6.17, green starts 7.60);
  - 12.0 mm: T3 black → white (his shoes end 9.46);
  - 88.3 mm: T2 yellow → black (yellow ends 88.04, black starts 88.57).
- **Printed white and hand-painted:**
  - gold buttons and shoulder stars, 133 mm²;
  - red dress buttons, 14 mm²;
  - stethoscope chest piece (silver), 17 mm²;
  - the dress top inside the coat above 88.05 mm (yellow), 204 mm².
- **Green spool:** not on the shelf (only bright Grass Green). The preview uses #2E4A2C dark olive; set `GREEN=#xxxxxx` in export_couple.py's environment once a spool is chosen.

## Checks
- verify_3mf passed on both files: watertight, 1 body, 79.79 × 40.21 × 150.00 mm.
- render_3mf done. Swap clearances asserted in the export.
- Not sliced or printed.
