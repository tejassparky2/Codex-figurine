# Family #00025: Tripo A (v2 art), bumps removed, 150 mm, Snapmaker U1

Customer images, the Tripo model and renders stay local (public repo). Delivery: figurines `projects/family_portrait_compare/output_r2/`.

## Chain (e3d venv, from this folder)
1. `prep.py <figurines>/projects/family_portrait_compare/remake/tripoA_nobumps.npz 0.5 1200000`
   - meshfix repair;
   - flat cut at z 0.5 (glued base);
   - rescale to 150 mm;
   - decimate to 1.2 M faces;
   - per-face colour from the source mesh (median 0.04 mm).
2. `views.py`, then `label.py 4`: graph cut with region rules:
   - navy only on the mother; Tripo smeared navy into the back of the dad's tee;
   - no black on the dad below 88 mm (keeps the tee white and the beard black);
   - the baby tee, beads and ring in their boxes;
   - the flat cap follows its neighbours.
3. `dots.py`: kaala tika, flat black, at the removed bumps (mother bindi, baby forehead, baby cheek on the art's side only).
4. `eyes.py`: dad lens reflection → skin, mother cheek navy speck → skin. Texture eyes kept; the automatic printed-eye construction made black blobs (kept in the file as EYES_TRIED).
5. `finish.py`, then `contour_split.py printable.npz final.npy cs.npz`, then `export_family.py`, then `render_outputs.py`.

## Print
- **Heads:** T1 Apricot, T2 Black, T3 Pure White, T4 Navy. No pauses.
- **Blue beads** print navy.
- **Printed white, hand-paint after:** the baby's light-blue sleeves (1676 mm²), red beads (307 mm²).
- **Optional:** gold on the mother's ring finger (printed skin).
- **Checks:** verify_3mf passed on both files (watertight, 1 body, 174.24 × 123.59 × 150.00 mm); render_3mf done. Not sliced.
