# Figurine colouring agent: mission prompt

Paste everything below the line into any agent (Claude, Codex/GPT or another) that colours a figurine in this repo. Fill in the bracketed parts. The same rules bind every agent, including the one that wrote this file.

---

You are colouring a customer figurine for multicolour 3D printing. The customer has approved an image. Your job is to deliver print files whose **finished colours match that approved image 1:1**: every part the right colour, no colour leaks, no stray patches. You must **prove** it before you deliver. Never hand over output you have not checked yourself, at pixel level, from the exported file.

**Your folder and the competition.**
- You are agent [claude | codex | name]. Work only in `<agent> works/<job>/`.
- The owner's neutral brief and judge are in `jobs/<job>/`; never edit the judge.
- When ready, write `<agent> works/<job>/submission.json` (format in `scoreboard/RULES.md`). The referee (`python scoreboard/score.py run <job>`) scores every agent with the same gate and judge.
- Points come from gate PASS, beating the other agents, and above all the owner accepting your delivery. Defects the owner has to find cost points; problems you report yourself don't.

**Inputs for this job**
- Approved image(s): [paths]. This is the image the customer said yes to. If the 3D model was generated from a different image, say so: the gate needs the image whose pose matches the model.
- 3D models: [1–2 Tripo GLBs] and optionally [a Meshy GLB].
- Print height [mm], printer [Snapmaker U1, 4 heads, nozzle], and anything else the owner said: [colour overrides, hand-paint allowed, spool changes allowed].

## 0. Before you start
1. Read `wedding-u1-skill/PLAYBOOK.md` in full: standing preferences, filament stock, the default pipeline, proven techniques and failures. Then read the latest entries of `wedding-u1-skill/LEARNING-LOG.md`.
2. Read `improvements/INDEX.md` and every proposal posted since your last job. Plan which ones to try on this job; you'll record a trial for each.
3. Set up the pinned environment: see the newest "Environment setup" entry in the log. You need Mesa EGL and `libopengl0`, plus `pip install -r wedding-u1-skill/reviewed/requirements.txt`.
4. Run `python -I wedding-u1-skill/coloring/approved_match_selftest.py Wedding-150mm-reviewed-paint-guide.3mf <scratch>`. It must end with both checks `ok`. If it doesn't, fix the gate before trusting it.

## 1. Non-negotiable rules
1. **The approved image is the colour truth.** The GLB texture is only evidence.
   - When they disagree, the approved image wins. Write the disagreement down.
   - The owner's written overrides (e.g. "groom maroon, not red") must be painted into an *edited copy* of the approved image. That keeps a single visual truth for the gate. Never keep a second, verbal truth.
2. **No delivery without the gate.** `coloring/approved_match.py` must report **PASS** on the finish guide for every approved view, after a vision review (step 6).
   - **FAIL** means fix and rerun.
   - **NEEDS_REVIEW** means look at every REVIEW crop and either fix it or record why the model is right.
   - **CANNOT_JUDGE** means the check didn't happen. Say so plainly and fix the inputs (camera, mask, anchors). Never call a CANNOT_JUDGE job done.
3. **Every claim comes from a tool run on the exported file.** Decoded labels, renders, gate reports and layer checks are all regenerated from the 3MF you deliver. Keep these apart: decoded array, rendered preview, gate verdict, slicer preview, G-code, physical print. Say which ones you actually did.
4. **Shape decides parts; colour decides only within a part.**
   - Use the geometric tools for contacts and thin parts: `part_lock`, `thin_network_lock`, `crease_snap`, `split_planes`.
   - Never use a 2-D mask without a depth-tested triangle-ID raster: it paints through to hidden surfaces.
   - **Locks go last, and `contour_split` goes after the locks.**
5. **Use only stock filaments** (PLAYBOOK §2), and say exactly what was substituted.
6. **Never delete or overwrite earlier deliverables.** Write new files and keep the old ones for comparison.

## 2. Intake (record everything in your own `<agent> works/<job>/README.md`)
1. Hash every input. Record triangle counts, texture size and whether each mesh is watertight.
2. Render each candidate GLB's texture unlit from 6 sides plus top and bottom, beside the approved image(s).
3. Choose the model for geometry and the texture for hidden sides. Write down why.
   - Prefer the candidate whose silhouette best matches the approved image: run the gate's camera solve on each and compare silhouette IoU.
   - Prefer correct hidden-side colours (Meshy was better on the back in one test; check, don't assume).
4. **Hidden sides.** Surfaces no approved view shows have no ground truth.
   - With 2–3 generated models, paint those surfaces from where the textures agree.
   - Where they disagree, list the region and choose by the approved image's style (same garment, same colour). Report it as an assumption.
   - If the customer can supply back or side views, ask for them: each extra approved view becomes another gate view.

## 3. Colour plan
1. Map every colour in the approved image to a finish slot: one slot per finished colour, including hand-paint colours.
2. Pick **anchors** in each approved image: points on each material, lit and shadowed (`{"<slot>": ["@x,y,r", …]}`).
   - Do this on a gridded zoom of the image. Never use a box that could clip a neighbouring material.
   - The gate prints `CHECK ANCHOR` when an anchor is nearer another slot's colour. Look at each one and move it or confirm it. A single anchor on the wrong material wrecks the whole comparison.
3. Plan the physical heads and spool swaps with `scripts/layer_colors.py` before painting fine details. A detail no head can print is a hand-paint decision, so tell the owner early.

## 4. Paint
Follow PLAYBOOK §3 (default pipeline) and §4 (techniques). Copy model-specific steps from the most similar job in your own folder. Learn from other agents' folders, but never edit them. Trace faces, eyes and mouths as shapes in mm on gridded crops at ≥40 px/mm, following the eye and mouth rules in PLAYBOOK §1.

## 5. Gate loop: repeat until PASS
```
python -I wedding-u1-skill/coloring/approved_match.py <finish-guide>.3mf <job>/gate/round-N \
    --approved <approved-front.png> [--approved <approved-back.png>@180] --prototypes <job>/anchors.json
```
1. **CANNOT_JUDGE.** Check, in order:
   - Is the silhouette IoU low? The pose differs: use the matching image, give a `@yaw` hint or `--mask`.
   - Is the ambiguity high? Add or fix anchors.
   - Does ivory or white touch a white background? Supply `--mask` or a transparent PNG.
2. **FAIL / NEEDS_REVIEW.** For each patch in `report.json` (largest first), open `patches/patch-NNN.png` and decide:
   - **Model wrong:** fix the cause, not the pixels. Contact leak → `part_lock`/`crease_snap`. Speckle → island merge/patch majority. Wrong part → region lock. Face detail → re-trace.
     - `patch_faces.npz` gives the faces and their 3-D centroid as seeds.
     - Don't blindly repaint them: they are only the faces visible from this camera.
   - **Gate wrong** (anchor, shadow, art vs geometry offset): record it in `review.md` with the crop. Fix the anchors if that's the cause.
3. Rerun the gate on the **re-exported** file. Keep each round's folder.
4. Every fix needs a before/after crop pair in `review.md`.

## 6. Pixel-level vision review (mandatory, even on PASS)
1. Open **every** `tiles/sheet-NN.png` for every view. Each tile shows the approved image beside the model. In `review.md`, give each tile a status: ok, fixed, or accepted with a reason. Zoom further with crops wherever you're unsure.
2. Inspect the 12-view unlit turnaround, top and underside, and lit front previews (full figure and face; `coloring/front_preview.py`). **The hero render is always straight front.** Look for:
   - leaks at hands, cuffs, collars, hems and hairlines,
   - specks on flowers and jewellery,
   - eyes, mouths and brows,
   - garment borders,
   - the back.
3. Check the hidden sides against the consensus texture and the approved style.

## 7. Physical checks and export
1. `scripts/layer_colors.py` at 0.08 and 0.2 mm bands. Design the swap schedule and assert its margins.
2. Export the finish guide and the printer project. Re-open both and decode every triangle against the intended arrays.
3. Run the slicer headless if available. Otherwise state that slicing was not verified. If a tilted orientation is used, recompute the swap heights.

## 8. Deliver
Write `submission.json`, run `python scoreboard/score.py run <job>` (practice or official, as the judge says), and give the owner:
- the files,
- front previews,
- the gate verdict per view (numbers from `report.json`),
- the remaining REVIEW items with crops,
- hand-paint and spool instructions,
- the hidden-side assumptions,
- a clear list of what was and wasn't verified.

Lead with problems, not praise.

## 9. Learn: every job and every review round
1. Add a dated `LEARNING-LOG.md` entry: what, how, why, when, result. Update `PLAYBOOK.md` if best practice changed.
2. **Every defect the owner finds becomes a regression case.**
   - Save the approved crop, the camera, the bad and fixed labels, and a one-line expectation under `<agent> works/<job>/regression/`.
   - Confirm the gate FAILs the bad version. If it doesn't, the gate missed it: improve the gate (or its defaults) until it does, and record that in the log.
3. Move fixes that work without model-specific coordinates into `wedding-u1-skill/coloring/`. Re-run the self-test and the earlier jobs' regression cases.
4. **Share what you learned in `improvements/`:**
   - Add a trial (with numbers) to every proposal you tested.
   - Post a new proposal (`improvements/TEMPLATE.md`) for any method that beat the previous result on the gate. Include the evidence, then run `python improvements/index.py`.
   - Never edit another agent's entry except to append a trial.
5. Commit and push the same day to your working branch. Never commit venvs, `__pycache__` or scratch arrays.

## 10. Keep the toolbox current (time-box to about 20 minutes per job, and log what you checked)
Look for releases and methods that would remove a manual step or a known failure:
- Generator features: Tripo/Meshy part segmentation, de-lighting, higher-resolution textures, multi-view input.
- Slicer texture-to-paint and brush-format changes: Snapmaker Orca, OrcaSlicer, Bambu Studio.
- Segmentation models that give part masks on the approved image, such as the SAM family. These help anchors and close calls.
- Mesh part segmentation, and background matting for white-on-white art.

Adopt something only after an **A/B on the regression cases and the self-test**: same mesh, same cameras, numbers in the log. Note licences (several strong research models are non-commercial). A new tool that hasn't been measured stays an experiment.
