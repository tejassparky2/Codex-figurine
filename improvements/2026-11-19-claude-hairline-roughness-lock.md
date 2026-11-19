---
title: Hairline strands by surface roughness, and held objects defined by fitted geometry
author: claude
date: 2026-11-19
status: proposed
applies_to: hairlines with sculpted strands over skin-coloured texture; glasses/cups/props held in hands
tool: claude works/man-with-drink-v2/tools/hairline.py, claude works/man-with-drink-v2/tools/detail.py (glass by geometry), claude works/man-with-drink-v2/tools/glass_axis.py
---

## Problem
The owner flagged "colour leaks on finger and hair edges not coloured" on man-with-drink v2:
- Whisky orange had spread onto the fingers.
- The sculpted hair strands at the hairline were painted skin, because the texture there is skin with thin grey strokes.

## Method
- **Hairline:** skin faces within 1.8 mm of the hair whose normals deviate from their 0.7 mm neighbourhood (0.5 mm average) by more than 6° are strands. They become silver; then strands are grown and islands cleaned. The frame and the face centre below the brows are excluded.
- **Held glass:** fit the tumbler (RANSAC circle fit on the wall). Then:
  - anything inside the radius within the glass height is glass;
  - the wall counts only within 0.25 mm and facing out;
  - the rim bead and its underside ring count as glass;
  - anything else near the glass is finger skin.

## Evidence (author)
`claude works/man-with-drink-v2/regression/check_round6.py`:

| Version | Finger contact band | Rim lip non-silver | Ridged skin at the hairline |
|---|---:|---:|---:|
| Delivered before round 6 | 41.4 mm² | 14.7 mm² | 64.3 mm² |
| This release | 0.0 | 0.0 | 3.1 |

The front close-up and face renders are in `claude works/man-with-drink-v2/out/` (`round6-face-and-cup.png`). The gate can't judge this job yet: the judge photo still has the photo's colours rather than the owner's.

## How to use it
- Run `hairline.py final.npy final.npy` after `finalize.py`. Set `--center-x` to the eye midpoint and `--brow-z` to the brow top.
- For held objects, fit the geometry per model. Never copy radius tolerances from another job.

## Trials (other agents append here; never edit someone else's entry)
| Date | Agent | Job | Result (numbers) | Verdict |
|---|---|---|---|---|
