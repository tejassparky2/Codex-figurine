# Agent prompt for a new multicolor figurine

Copy this prompt into the agent that has the new sculpt and photographs. Fill in the bracketed inputs. A new checkout of this repository includes the toolkit and a worked wedding example.

> Build a printable multicolor project from [textured GLB and printable geometry] using [front, side and back photos]. Deliver it at [height in mm] for [printer, installed nozzle sizes, material and available colors]. My important color and facial-detail decisions are [list]. I can make [number] manual spool changes and hand paint [regions]. Use the steps below. Work on the actual mesh, open your exports in the target slicer and return downloadable files. Tell me where the reference is ambiguous, where the print relies on hand paint and which checks succeeded.

## From source to a painted master

1. **Record the inputs.** Keep untouched source files and record their hashes, dimensions, orientation, texture images, print height and reference views. Establish left and right from the subject and the camera. If only a photograph exists, first obtain a sculpt with a known back and sides. A single front photo leaves those surfaces ambiguous.
2. **Align the meshes.** Keep a high-detail textured original with UVs and an upright printable copy with millimeter coordinates. Align both at the same working height. Make a low-density analysis copy if needed. Compare a source-texture render to each photograph and record camera pose, scale and visible landmarks. Use the highest-priority reference for each feature when references disagree.
3. **Set the finish palette.** Assign a named material to each garment, flower band, piece of jewelry, skin area, eye feature and mouth region present in this model. Record permitted colors and adjacent materials for each region. Lighting, gloss and ambient shadows belong in presentation renders. Use flat material IDs for manufacturing.
4. **Create broad paint regions.** Install the baseline environment using the command below. Start with the supplied clean-colorize CLI. Choose the real up axes and palette for your inputs. Inspect the segmentation at garment seams, hairlines and occlusions. The wedding parameters are a starting point for tuning.

       python toolkit/scripts/clean_colorize.py model.glb --geometry printable.ply --height 150 --up-axis y --geometry-up-axis z --palette '#BE1825,#65142B,#EABE50,#FAF2DE,#D69B78,#171516' -o broad.3mf

5. **Trace the detail.** Register each eye opening independently. Record pupil center as a fraction of that eye’s width and height, and trace lids, lashes and catchlights against the source. Trace teeth, lips and the beard boundary separately. Use new camera coordinates, curves and visible-face masks. Rasterize triangle IDs with a depth buffer before projecting a mask, so a correction on a wrist cannot paint through to the garland behind it.
6. **Refine across the mesh.** Use same-material connected components, physical surface area and shared-edge adjacency. Give sharp creases and strong texture edges weaker smoothing weights. Preserve deliberate highlights and tiny ornaments. On disputed patches, compare the original UV texture with neighboring painted facets. The example trains an OpenCV random forest on confident interiors, propagates votes on the surface graph, then uses traced polygons and seeded GrabCut on individual contact boundaries. Rebuild the seeds, training rules and masks for each model. Inspect the reverse side after each correction.
7. **Repair and simplify.** Record shells and intended separate parts before editing. Protect paint-boundary triangles and their neighbours during decimation. Repair holes or invalid connectivity locally where possible. The wedding repair retained a single connected sculpture. Its “remove smallest components” step can discard valid accessories on a multipart model. Transfer labels with distance and normal agreement. Reopen the export and verify winding, edge incidence, expected shells, heights and transforms. Compare details on the repaired mesh to the original.

## From finished colors to physical filament

8. **Calculate layer conflicts.** On a single-mesh finish guide using this repository’s solid-triangle Orca paint encoding, run the layer tool below. It measures triangles intersecting each height band and lists every finish slot present. It produces a conservative surface estimate. Sliced extrusion paths are the final check.

       python scripts/layer_colors.py finish.3mf --band-mm 0.08 --heads 4 --output layer-colors.csv

9. **Design the swap schedule.** Read the slot labels from the finish palette. For each height interval, select the pigments actually loaded in the heads. A swap replaces that head’s pigment across the entire layer. Where too many colors coexist, record the substitute base, affected part and required paint, or discuss a split assembly. Check layers immediately below and above each swap in the slicer. The wedding model used two swaps at 36 and 76 mm. Recalculate both for the new model.
10. **Export separately.** Deliver a full-color finish guide and a printer project with the actual head assignments, correct preset, bed origin, nozzle sizes and scale. Reopen each archive, decode the triangles and compare labels with the intended arrays. Label manual pauses explicitly. State whether they are embedded. Create the after-paint hero from the exported guide and render the as-printed preview using the physical schedule.
11. **Inspect all sides.** Render registered source texture, flat finish labels and simulated print using identical cameras. Include front, back, both sides, obliques, top and underside. At native resolution inspect faces, hairlines, jewelry, flower bands, finger gaps, cuffs, garment borders, hems and soles. Keep per-camera ID maps, changed-pixel maps, and separate maps for areas requiring paint. Use the reference photographs for shape and material judgments. Correct-colored pixels in the wrong place still pass a palette check. Record unseen or ambiguous regions.
12. **Slice and deliver.** Use the actual printer/nozzle/material preset. Confirm manifold status, dimensions, bed placement, support needs and tool changes. If the slicer reports floating areas, configure supports, re-slice and examine the supported preview. Verify that G-code finalization succeeded before labeling a file ready for the printer. Deliver the editable print project, finishing guide, inspection views, spool/swap/paint instructions and a verification record. Publish only to the destination authorized for this job.

## Install and find the code

From the wedding-u1-skill directory on Linux with Python 3.12 and Mesa EGL:

    python3.12 -m venv .venv
    . .venv/bin/activate
    python -m pip install -r reviewed/requirements.txt
    python -m pip check

The toolkit handles source sampling and graph-cut segmentation. The reviewed directory contains the actual face-ID renderer, texture mapping, graph refinement, manual tracing, export and PDF code used on the wedding example. For a new job, keep its masks, palette, camera poses, scale, tool mapping and review notes together. Hand another agent those job-specific files along with the reusable workflow.

[Worked example and commands](reviewed/README.md) · [Original graph-cut and facial tracing stages](AGENT-PROMPT.md)
