# Development stage index

The initial Drive archive was figurine.zip (everything3d-main). Its figurines/scripts directory provided the source textured-3MF writer, example native paint bridge and structural verifier. The separate GitHub repository supplied graph coloring and render helpers. The original installation also registered figurine-colorize, figurine-blockcolor, figurine-split, pixar-figurine-render and piggybank-namesign. The latter four skills and the archive's web Studio were not called to produce the final model.

| Stage | Historical implementation |
|---|---|
| Original UV model and five-view/flat checks | wtex.py, wgl.py, wpreview.py |
| Initial palette, projected cleanup and native 3MF | wfix.py, wpaint2.py, finepreview.py |
| Figurine-style eyes and cleanup of connected islands | wstudio.py, wstudiopreview.py, wback.py |
| Four-view sheet and texture-color experiments | refbake.py, refviews.py, refpaint.py, refpaintpreview.py |
| Eye, mouth, hand and cuff contours; face-ID checks | clean-detail.py, clean-check.py, detailqa.py, detailqa-build.py |
| Initial same-red U1 mapping, then separate red and maroon | u1w.py, u1m.py, u1mprev.py |
| Reference gaze, crown fixes, hand-paint simulation | wgaze.py, gazeprev.py, afterpreview.py |
| Tangential edge relaxation on the native printable geometry | smoothu.py, smoothview.py |
| Solid jewelry, hairline, textile and flower corrections | matfix.py |
| Final surface-graph cleanup, depth masks and native exports | flatjob.py |
| Unlit finish and tool-swap turnarounds, hero | flatrender.py, flatprint.py, latesthero.py |

Read the included research report for the broader tool survey. It distinguishes recommended experiments from steps actually used. The historical 120 mm revisions and early tool maps have been superseded by the final 150 mm replay.
