# Wedding example through the reviewed release

Use the repository root 3MFs as checkpoints. The original replay under scripts/ ends at the flat model. This directory covers material locking, repair and the subsequent ten-camera review. Run from the wedding-u1-skill directory with the environment in NEW-MODEL-PROMPT.md. Use a full clone so the parent repository contains the checkpoint files.

    python reviewed/replay.py ../wedding-reviewed-job

The runner creates a fresh directory, links the source, photos and checkpoint archives, and launches independent stages. It regenerates both reviewed 3MFs and the inspection PDF, then compares every uncompressed 3MF entry to the published copies. PDF creation dates can differ. Use --skip-report for a model-only replay. The original environment used Linux software EGL. Allow several GB of free memory and disk for intermediate data. Slicing and G-code preview can require substantially more memory.

| Stage | Implementation | What to replace for a new sculpt |
|---|---|---|
| Geometry and base paint through the flat release | scripts/replay.py and scripts/verify.py in the parent skill | Inputs, upright axes, scale, palette, feature curves, cameras and all spatial masks |
| Flat to material-locked | reviewed/lock_materials.py | Component IDs, flower and coat regions and observed swatch errors |
| Material-locked to repaired | reviewed/repair.py | Decimation budget, protected rings, required shells and label-transfer tolerances |
| Generate the repaired template 3MFs | reviewed/repaired_templates.py | Printer presets, colors, build transform and height |
| Rasterize ten triangle-ID views | reviewed/render.py | Orthographic framing, scale, orientations and palette |
| Register source texture samples | reviewed/source.py | Mesh correspondence, texture wrapping and UV orientation |
| Region classifier and surface graph | reviewed/paint.py | Color rules, protected details, reliable interior training samples |
| Visible corrections for contacts and facial features | reviewed/manual.py and reviewed/detail.py | Per-view polygons, source colors, depth masks and GrabCut seeds |
| Encode print slots and finish colors | reviewed/export.py | Physical heads, transitions and hand-paint bases |
| Inspect and compare | reviewed/report.py | Reference sheet, view labels, region crops and hardware schedule |

To regenerate earlier checkpoints, run the baseline replay and verification first. From its job directory run lock_materials.py, then repair.py. To rebuild the repaired 3MF templates, run repaired_templates.py with the extracted Snapmaker Orca v2.4.1 resources/profiles/Snapmaker directory as its positional argument. The standard reviewed replay uses the checked-in templates, which already contain the profile and placement.

**Recorded wedding results.** The reviewed mesh measures 150 mm tall, with 812,934 triangles and one part. Snapmaker Orca reported manifold geometry. The review changed 45,712 finish-label assignments compared with the repaired release. The inspection PDF covers ten 1000 × 1500 camera views. About 10.1% of surface area has a different simulated as-printed color from the hand-painted target under the two-swap plan. The supports-off slice reported floating regions. A support-enabled slice, finalized G-code export and physical print remain unverified.

**Tool choices.** The pipeline used Python, trimesh, NumPy/SciPy, PyMaxflow, PyMeshLab, PyMeshFix, OpenCV, ModernGL/EGL, Pillow, ReportLab and headless Snapmaker Orca. For native validation use the installed slicer executable with --info on the delivered print 3MF and --slice 0 --outputdir followed by a writable directory and that 3MF. Retain the exit code and inspect the final toolpath. The prepared example uses four 0.2 mm nozzles with 0.08 mm nominal layers. The two manual swaps and hand-paint regions are documented in the original agent prompt and the current PDF.

**Replay verification.** Running reviewed/replay.py from the material-locked inputs reproduced every uncompressed ZIP entry of both published reviewed 3MFs. Running the report stage on those outputs regenerated the 23-page PDF. The layer-color checker on the finish guide counted 822 of 1,875 uniform 0.08 mm bands with more than four finish slots. That calculation includes the full surface and uses uniform band spacing from the bed. It does not model first-layer offset, extrusion width or hidden toolpaths.
