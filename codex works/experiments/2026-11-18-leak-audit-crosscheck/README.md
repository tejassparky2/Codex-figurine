# 2026-11-18 · Surface leak audit cross-check

**Hypothesis.** The 1,669-face surface-audit change set explains the visible-front regression from 0.859% to 0.932% clear disagreement.

**Method.** Decoded solid finish labels from the reviewed guide and leak-candidate guide with `approved_match.load_model`. Crossed the 1,669 changed face IDs with the gate's `patch_faces.npz` for both releases. Also measured the gate on the judge front and copied its side-by-side and largest patch crop.

**Numbers**

| Release | Clear disagreement | Largest clear error mm² | Review patches | Boundary p95 mm | Silhouette IoU | Runtime |
|---|---:|---:|---:|---:|---:|---:|
| Reviewed | 0.8594% | 16.229 | 4 | 0.0 (reported median), 0.688 known log | 0.9516 | 140.016 s |
| Leak candidate | 0.9316% | 22.924 | 3 | 0.687 known log | 0.9510 | 137.839 s |
| Contact + contour | 0.6953% | 17.193 | 3 | 0.604 known log | 0.9513 | 141.014 s |

The 1,669 changed faces produce 168 face IDs visible in the rerendered judge camera. Neither gate patch face set intersected the full 1,669 change set: 0 intersections with 2178 reviewed patch faces and 0 with 2504 leak patch faces.

**Vision.** The before/after side-by-side looks nearly unchanged. The largest leak-candidate crop is at the bride/groom hand and garment contact, and it was not one of the exact audited face IDs reported by the gate. Thus this is not evidence that the audit's 1,669 changes caused the measured visible patch; the gate and audit are in different face/raster intersections.

**Verdict.** Reject the blanket automatic application of this audit on the visible front until an exact visible-face correspondence is available. Keep the audit as a review tool, require `--approved-labels` for intentional regions, and inspect changes in depth-tested cameras. This does not prove hidden-side correctness.
