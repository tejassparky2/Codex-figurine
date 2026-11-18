# KNOWLEDGE

## Pipeline

The pipeline starts with the approved image as colour truth and a generated GLB only as geometry/hidden-side evidence. Repair and decimate the mesh, place it Z-up, transfer source texture to faces, solve broad crease-aware Lab labels, then apply geometry locks (`part_lock`, `thin_network_lock`, `crease_snap`), contour split, export, and decode/reopen the 3MF. Two independent checks follow: replay/verify for exact flat releases and `approved_match.py` for camera-registered agreement with approved art. Slicer/G-code and physical checks are separate and have not been completed unless explicitly reported.

## Proven

- The repaired wedding mesh is a single watertight body; replayed flat releases matched byte-for-byte, and reviewed replay archives matched exactly.
- `approved_match_selftest.py` passes a clean model and rejects planted leaks at 30 and 1,500 visible faces. Its measured planted-patch locations were 0.39 mm and 0.80 mm from the reported centroids.
- The 25-anchor wedding practice gate currently reports FAIL, 0.6953% clear disagreement, 17.193 mm² largest clear error, 0.604 mm boundary p95, and 0.9513 silhouette IoU after local alignment.
- Contact seeds + protected contour split improved the practice wedding gate from 0.859% to 0.695%, boundary p95 from 0.687 to 0.604 mm, while only increasing the 3MF's triangles.
- Cone-thickness and part-lock geometry were accepted in the man-with-drink reviews.

## Open problems

- The practice judge uses a maroon portrait not the generation pose, so its patches are not fully trustworthy until the true generation image is recoloured.
- The surface audit changed 1,669 faces and was associated with a visible-front regression from 0.859% to 0.932% disagreement.
- Two anchors in the wedding judge are currently flagged as near the wrong slot.
- Ivory/white-on-white background, shadowed cream versus skin, and hidden-side assumptions remain weak.
- Automatic contact detection, eye/mouth proposal, AO de-shading, and hidden-side consensus are not proven.
- No running slicer, G-code from a current release, or physical print was verified.

## Code versus documentation

Code wins where prose and implementation disagree. In particular, `approved_match.py` is the implemented gate and must receive a solid-per-face finish guide; it rejects brush-split paint codes. `contour_split.py` is the authoritative implementation of the protected contour split, and `--keep` is propagated until fixed point. `leak_audit.py` documents confidence as weighted neighbour agreement, not correctness; `approved_match.py` is likewise stricter than the prose: local alignment is kept only when label agreement improves. The current scripts directory is under `wedding-u1-skill/scripts/`, while older prose names `scripts/`.
