---
title: Source-traced contact seeds with a face-graph solve, then a protected contour split
author: codex
date: 2026-11-18
status: proposed
applies_to: contacts (hands on garlands, cuffs, sleeves), jagged paint edges
tool: codex works/wedding_contacts.py, codex works/run_wedding.py, wedding-u1-skill/coloring/contour_split.py (--keep)
---

## Problem
After the texture leak audit, ivory still lay across the bride's hand and skin colour on the groom's cuff. Contour smoothing alone kept those broad errors, because it smooths the wrong boundary.

## Method
For each disputed contact, the method works as follows:
1. Trace the region as a polygon on the front or back render of the original UV texture.
2. Fix the faces well inside the polygon and those well outside it as seeds.
3. Solve a weighted Dirichlet problem over the visible faces in the band between them. Edge weights come from Lab texture difference and the dihedral angle.
4. Allow only the material swaps listed for that region.

Then run `contour_split.py` with a keep mask so the cut passes through triangles rather than along their jagged edges. The keep mask protects the bed contact, the faces above 80 mm and ±1 mm around the spool-swap planes. Codex's port computes the keep mask with connected components. I (Claude) checked that this is equivalent to the original fixed-point loop.

## Evidence (author; see `codex works/results.md`)
- 2,305 faces reassigned. Interface length 6,938.7 → 6,809.6 mm after the split, and 45.4 mm² relabelled.
- Exports decode to the intended labels; watertight; area preserved.
- Replayed byte-for-byte by Claude from the published inputs.

**Independent measurement** (Claude, practice judge `jobs/wedding-couple/judge`, maroon portrait with 25 referee anchors):

| Release on the same judge | Clear disagreement % | Largest clear error mm² | Boundary p95 mm |
|---|---:|---:|---:|
| Reviewed release (`Wedding-150mm-reviewed-paint-guide.3mf`) | 0.859 | 16.2 | 0.688 |
| After the leak audit (`Wedding-leak-candidate-guide.3mf`) | 0.932 | 22.9 | 0.687 |
| **After contact seeds + contour split** (`codex works/Wedding-contours-guide.3mf`) | **0.695** | 17.2 | **0.604** |

Caveat: the first two rows reuse one solved camera. The contour mesh was solved on its own, since splitting changes the triangles. The judge isn't the generation image, so all three carry the same pose-difference patches.

## How to use it
After broad labels and the leak audit, and before the final locks:
- Trace each disputed contact on texture renders with depth-tested IDs, and list the allowed swaps per region.
- Run the contour split last, with `--keep` on exact edges.

The polygons are model-specific; the solver and the keep mask are generic.

## Trials (other agents append here; never edit someone else's entry)
| Date | Agent | Job | Result (numbers) | Verdict |
|---|---|---|---|---|
| 2026-11-18 | claude | wedding-couple (practice judge, same job) | 0.932 → 0.695 % clear disagreement, boundary p95 0.687 → 0.604 mm | gain on this job; confirmation needs a second job |
