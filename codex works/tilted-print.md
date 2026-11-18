# Tilted wedding print, 668 layers

The user-supplied G-code has SHA-256 `a36697bb7e680a0d9a61b2d881bfcc373d08feb7dd50c1ae2b8a7188e625e053`. It declares Snapmaker Orca 2.4.1, starts at 0.25 mm, uses 0.20 mm increments and ends at 133.65 mm. There are no executable M600, M0, M1, M25 or PAUSE lines. The M600 in the configuration footer names the pause command.

To estimate pigment needs, use tilted_wedding.py with the G-code, repaired-u1.npz, final.npy and physical.npy from the reviewed replay. The script selects extruding object paths tagged Outer wall or Overhang wall, excluding support and tower segments. It aligns their midpoints to the reviewed surface and uses only short segments within 0.65 mm whose tool ID agrees with the reference. Top surfaces, long segments and ambiguous differences due to manual repaint are omitted. This is an estimate of sampled wall length and cannot certify the entire printed appearance.

The rigid fit was approximately -34.5 degrees about X, with median distance 0.22 mm. For each candidate pause, sum the matched old-color wall length after it and new-color wall length before it. Among these samples the minima were layer 230 (46.05 mm) for gold to skin and layer 365 (73.05 mm) for red to black. Both swaps are compromises. At layer 230, head 1 has about 12 mm of gold and 14 mm of skin wall. At layer 366, head 2 has about 54 mm of red and 60 mm of black wall. Changing one spool at a layer boundary cannot produce both pigments on that layer. These are not universal heights for other orientations.

Start heads 1–4 with gold, bright red, warm white and maroon. Insert the two manual pauses before the named layers only if the overlapping patches will be touched up. Keep heads 3 and 4 loaded. For clean filament-only separation, redesign the tool assignment or orientation and verify the ranges again. Keep this G-code independent of subsequent 3MF revisions.

Varying the nearest-surface cutoff from 0.4 to 0.9 mm shifted the estimated head 1 optimum from layer 229 to 230 and kept head 2 at 365. This sensitivity check supports the overlap diagnosis while showing the precision of the touch-up estimate.
