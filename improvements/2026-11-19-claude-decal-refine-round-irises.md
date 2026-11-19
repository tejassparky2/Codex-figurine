---
title: Decal refine - paint small traced features (irises) at design resolution, plus the round-iris geometry rule
author: claude
date: 2026-11-19
status: proposed
applies_to: eyes (irises, lash lines, whites), small logos/buttons, any traced feature under ~15 triangles across
tool: wedding-u1-skill/coloring/decal_refine.py; claude works/man-with-drink-v2/regression/check_round7.py (iris roundness check)
---

## Problem
Round 7 of man-with-drink v2. The owner wrote: "make both sides of the pupil round as in the art photo".
- Even after the 2-D eye design was made round, the exported 3MF showed irises with straight slanted sides.
- The mesh has ~0.35 mm triangles, so a 4 mm iris is only ~12 triangles across. Per-triangle votes plus contour_split flatten the arcs into lines.
- The first two designs were also wrong in geometry. With the centre near the upper lid, only the lower cap was visible (a bowl). With a small circle inside the opening, it read as a square bar.

## Method
- **Geometry rule, measured on the art:** the iris is a big circle cut by both lids, r ≈ 1.05× the opening height (~45 % of the eye width), with its centre at mid-opening. Lower it where the upper lid slopes.
- **`decal_refine.py`:**
  - Refines the faces inside the feature windows with conforming red-green midpoint subdivision: no T-junctions, surface unchanged, 2 levels give 0.09 mm edges.
  - Each sub-face takes the 2-D design class at its centroid, but only where the camera's ID map shows that sub-face's own source face, so it never paints through.
  - Islands under 0.08 mm² inside the windows merge into their longest-border neighbour.

## Evidence (author)
`claude works/man-with-drink-v2/regression/check_round7.py` renders the decoded 3MF labels straight front and measures the iris width profile:

| Version | Widest at (fraction of height) | Verdict |
|---|---|---|
| Delivered round 6 (r 1.9, centre near the lid, no decal) | 0.00 / 0.00 (bowl) | FAIL |
| Round-7 design without decal_refine | sides straight (renders reviewed) | rejected by eye |
| This release | 0.57 / 0.56, top quarter 0.93 / 0.92 of max | PASS |

- Speck pass: 763 islands → 0 inside the windows.
- Mesh: 1,016,788 → 1,125,860 faces, watertight, area unchanged to 1e-9; the tool runs in 3.6 s.
- `check_round6.py` is still PASS. Layer bands are still clean.
- Crops: `claude works/man-with-drink-v2/out/round7-eyes-and-hand.png`.
- The approval gate can't judge this job (judge photo not recoloured).

## How to use it
- Run `decal_refine.py cs.npz views/face_cls.npy views/face_id.npy cs2.npz --cam X0 Z1 PPM --win <eye windows> --levels 2 --lock frame_full.npy` after `contour_split`, then export cs2.npz.
- The class map and ID map come from the same orthographic face camera (`facecam.py` / `detail.py`).
- Don't use it on large regions: it adds faces (×16 per refined face). Keep the windows tight around the feature.

## Trials (other agents append here; never edit someone else's entry)
| Date | Agent | Job | Result (numbers) | Verdict |
|---|---|---|---|---|
