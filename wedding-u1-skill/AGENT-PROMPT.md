# Agent prompt — reproduce the wedding figurine from source to final hero

You are delivering a 150 mm wedding figurine for a four-toolhead Snapmaker U1. Execute the pipeline, reopen the results, render them and give me the files. Use the code and inputs in this package. The targets are in expected/. The finish guide depicts the intended hand painting; the U1 print file encodes four physical tool IDs.

## Start here

Use a Linux machine with Python 3.12, an EGL OpenGL 3.3 context (Mesa software rendering works), and enough RAM and local disk for the full mesh and intermediate archives. The original job ran with an 8 GiB memory limit. Allow roughly 2 GB of working disk beyond the environment and downloaded package. From the extracted skill directory:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip check
python scripts/replay.py ../wedding-job
python scripts/verify.py ../wedding-job
```

Each stage runs in a fresh process inside the new job folder. The replay defaults to the recorded 480,000-face working mesh. Add --decimate to regenerate it from the GLB. Keep the virtual environment and job directory separate. On Linux, install the distribution's Mesa EGL runtime if moderngl cannot create its standalone EGL context.

## Inputs and decisions

- inputs/source.glb contains the actual Tripo model, 1,974,931 triangles and a 4096 × 4096 base-color texture. Generation was already complete. No API key or paid call is needed.
- reference/0.png is “four_views (1).png”, the matching arrangement with bride on the viewer's left. 1.png is the different arrangement. 2.png is “front_maroon_chatgpt.png”; use this portrait for the groom's maroon outfit and relative pupil positions. 3.png is the supplemental garland strip. These files are under inputs/ before replay.
- Use bright red for the bride, maroon for the groom's coat, turban and shoes, solid gold for jewelry, ivory for flowers and white details, skin, black and rose. Eyes are black and white only. Give each pupil one white catchlight. Mouths have rose and white only, with the moustache and beard outside. The latest instructions override the four-view sheet's bright red groom and the portrait's white jewelry centers.
- Source links: [original GLB](https://drive.google.com/file/d/1Qz_mhfnj3iE8SH1u25HcNB6yAcnuAt-M/view), [image folder](https://drive.google.com/drive/folders/18zEZcgZKnZImN2EibNELN7v6F6S1y_FK), [upstream toolkit](https://github.com/everything3d/figurine-colorize), [additional project archive](https://drive.google.com/file/d/1C76IQ2XrEJnAGpm1St9ce1rKOlO0iDoZ/view). The research note is under history/. The bundled toolkit was checked out at 62e88ca.

## Execute the stages in order

1. **Keep two meshes.** Use trimesh and NumPy to preserve the original triangle order, UVs and texture. Use fast-simplification for the working copy. Convert Y-up to Z-up, center X/Y and place the feet at Z=0. Do the original labeling and camera tracing at 120 mm, then scale by 1.25 for delivery. Changing scale before tracing invalidates the spatial masks.
2. **Create the broad regions.** toolkit/scripts/clean_colorize.py uses SciPy nearest-neighbor transfer, Lab color distances and PyMaxflow alpha-expansion on the face graph. Make changes more expensive across smooth regions and cheaper at sculpted creases. Use the exact initial palette and CLI in scripts/replay.py. Historical parameters were lambda 4, minimum island 0.16 mm², automatic de-shading off and automatic shadow fix off. Dark patches are resolved by material and region. scripts/wfix.py applies the early flower, trouser and shadow corrections.
3. **Preserve a texture baseline.** scripts/wtex.py writes a textured 3MF with welded spatial vertices and separately indexed UVs. It preserves the embedded color image. Use this to diagnose geometry and texture orientation. The print deliverable uses per-face paint.
4. **Transfer and trace.** scripts/clean-detail.py maps the broad labels back to the original triangles with cKDTree and samples the source UV texture at face centroids. It contains the actual Bézier eye, lip, tooth, hand and cuff paths. Project using the saved orthographic front camera, clip hand corrections using depth and avoid painting through to occluded flowers. Save each eye/mouth face-index list. scripts/clean-check.py reopens the 3MF and checks the region label sets.
5. **Match the gaze and choose hardware colors.** scripts/wgaze.py places pupils independently using normalized left-to-right fractions 0.407, 0.32, 0.665 and 0.504 in the four eye openings. Retain lashes and painted highlights, remove brown from the eye openings, patch the crown and convert to 150 mm. Measure relative iris position within each opening on any new reference.
6. **Smooth the actual boundaries.** scripts/smoothu.py builds sparse vertex adjacency along the interfaces and a surrounding one-ring. It relaxes boundary vertices tangentially, limits movement to 0.28 mm and rejects moves that would excessively collapse or reverse affected triangles. It protects the feet, top and neighborhoods of the swap planes. This step changes geometry along paint boundaries.
7. **Enforce material rules.** scripts/matfix.py uses UV samples, localized masks, visibility and a 3-D distance to neighboring gold to fill jewelry centers, preserve black hair, remove dark fragments from the red sari, and clean hands and garlands. Keep skin between hands and sleeves, and ivory on flowers and the groom's cuff. Use the geometry and adjacency to distinguish overlapping surfaces.
8. **Run the final whole-mesh cleanup.** scripts/flatjob.py constructs weighted face adjacency with weaker connections across creases. It resolves small enclosed components below 0.75 mm², then runs 34 normalized graph-averaging iterations on a narrow boundary band with fixed interiors and protected facial regions. It includes the final masks for the back of the turban, coat, fingers, cuff and individual flower bands. These masks were tuned after inspecting unlit views.
9. **Export two models.** Wedding-150mm-flat-finish.3mf stores seven intended finished colors. Wedding-U1-150mm-flat.3mf stores the four-tool print mapping. The XML uses per-triangle paint_color and the corresponding filament_colour palette. Keep slot order with the file. scripts/flatjob.py decodes each saved file and verifies the labels against the export arrays. The expected size is about 93.25 × 50.50 × 150.00 mm.
10. **Check appearance separately from lighting.** scripts/flatrender.py and scripts/flatprint.py render 12 unlit views at 30° intervals. Each visible pixel in the original-size checks must be an allowed palette color or the background. Inspect the output for wrong placement of valid colors, especially ivory beside fingers, maroon under bangles, the rear turban, hair jewelry and the back of the sari. The pixel test checks palette membership. It cannot establish that every region matches a photograph.
11. **Render the final hero.** scripts/latesthero.py reads the finished-color 3MF, generates smoothed vertex normals, and renders through ModernGL/EGL at 2400 × 3000. Downsample to 1200 × 1500. Use the near-frontal pose, warm neutral background and soft highlights in the shader. Lighting is presentation only. The model's stored labels remain flat.
12. **Deliver and explain printing.** Supply both 3MFs, both turnarounds, the front close-up or detail crop and the hero. Use the U1 file at 100% scale. In Snapmaker Orca select the actual U1/nozzle profile, slice, and add pauses before the first layer at or above 36.00 mm and 76.00 mm. Start H1 gold, H2 bright red, H3 warm white and H4 maroon. At 36 mm change H1 gold to skin. At 76 mm change H2 red to black. Purge at each change. H3 and H4 stay loaded. Paint the lips rose, bindis red, and ivory-base upper trim and jewelry solid gold. The two spool changes are manual and are not embedded. Other small unavailable colors at specific heights are approximated; consult the as-printed turnaround. No physical print or U1 sliced toolpath was verified in the original job.

## Use on another figurine

Reuse the acquisition, geometry, graph, export and QA methods. Recompute the camera, silhouettes, scale, UV orientation, local coordinates, eye-opening curves, gaze fractions, mouth shapes and depth-limited masks. Face IDs and camera coordinates in these scripts belong to this couple. For another four-head job, measure color overlap at each layer and design its own slot mapping and swap heights. Never transfer the 36/76 mm schedule just because two models share the same height.

## Earlier experiments and tools

history/ contains snapshots of the custom Python scripts from development, including full-texture conversion, source renders, reference color remapping, earlier pupil and U1 variants, close-up checks and preview experiments. Some reference absolute paths from the original machine. scripts/ contains the portable final dependency chain. Headless rendering here used EGL/ModernGL; the final chain used no Blender, image generation, learned facial model, Tripo call or cloud rendering. The studio application, OpenSCAD and ancillary optional Python packages installed in the initial setup were separate from this model pipeline.

Be precise about verification. An identical decoded paint array, a matching rendered image, a slicer layer preview and a physical print are four different results. Report any remaining mismatch honestly.
