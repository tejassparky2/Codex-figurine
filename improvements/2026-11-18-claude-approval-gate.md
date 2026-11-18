---
title: Approval gate — pixel-by-pixel comparison with the customer-approved image, plus a referee
author: claude
date: 2026-11-18
status: proposed
applies_to: final verification of every job, agent scoring
tool: wedding-u1-skill/coloring/approved_match.py, wedding-u1-skill/coloring/approved_match_selftest.py, scoreboard/score.py
---

## Problem
Every leak on the man-with-drink model was found by the owner, over 4 review rounds. No tool compared the model with the image the customer actually approved.

## Method
1. Cut the figure out of the approved image.
2. Solve the camera from silhouettes, then correct the generator's shape drift with smoothed, capped flow. The correction is kept only if it improves label agreement.
3. Label the art by finish slot. The agent picks `@x,y,r` anchors by eye, and the tool flags any `CHECK ANCHOR` that sits closer to another slot's colour. Region voting is used only on unsure pixels.
4. Render the model's finish labels from the same camera through a depth-tested triangle-ID raster.
5. Compare the two. The output is a verdict, a patch list with faces, mm² and 3-D position, zoomed crops, and tile sheets for vision review.

The details are in PLAYBOOK §4.7.

## Evidence (author)
**Self-test** (reviewed wedding guide; hidden camera with perspective, shading and anti-aliasing):
- Camera error under 0.1°. The clean model PASSes.
- A planted 30-face (6.8 mm²) leak FAILs, located 0.39 mm off. A 1,500-face leak is located 0.80 mm off.

**Real art:** on the maroon portrait, the top patches reviewed by eye were differences between the art and the geometry, not paint errors.

**Known limits:**
- Needs the generation image for a tight pose match.
- White-on-white art needs a mask.
- Near-identical colours become NEEDS_REVIEW.
- Only the approved views are measured.

## How to use it
`approved_match.py <finish-guide>.3mf <out> --approved <img> --prototypes anchors.json`. Loop until PASS, then review every tile. Run `approved_match_selftest.py` after any change.

## Trials (other agents append here; never edit someone else's entry)
| Date | Agent | Job | Result (numbers) | Verdict |
|---|---|---|---|---|
