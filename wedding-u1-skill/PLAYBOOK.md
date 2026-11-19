# Figurine colouring playbook (living document)

Read this before colouring any new model. The dated what/how/why/when record behind it is in [LEARNING-LOG.md](LEARNING-LOG.md); the repo-wide rules are in `/CLAUDE.md`. After every review round, add a log entry, push it the same day, and add to this playbook: what the owner flagged, the root cause, the fix, and the tool that now does it. When a fix works on two models, turn it into a default. The aim is that each model needs fewer review rounds than the last.

Sources so far:
- the wedding couple (this repo),
- the man-with-drink caricature (`claude works/man-with-drink/`),
- the dropped family-portrait comparison,
- the research note in `history/`,
- the local figurines session ("Build setup and live test", repo tejassparky2/Figurine). It sent the filament stock list and slicer findings verified on real slices; its own playbook is `docs/COLORING_PLAYBOOK.md` there. Keep the two in step.

## 1. Owner preferences (standing orders)

| Topic | Preference | Learned from |
|---|---|---|
| Eyes | **Depends on the style.**<br>• Realistic models: no catchlight, no eyeliner wing. Use the eye white, a dark iris and a 0.40 mm lash line.<br>• Stylised (Pixar/chibi): socket-shaped white, big round iris, one catchlight dot and a lash outline (see `projects/style_reference/printed_eyes_example*.jpg` in the Figurine repo).<br>• Rejected: ellipse-fit "goggle" eyes, and eyes that just follow the texture.<br>• Blank white eyes painted in the slicer are also acceptable. | Man-with-drink review 2; local session |
| Mouth | **Never black inside a mouth.** Teeth are white, **both rows when the smile shows them** (trace the whole opening; man-with-drink r2). The lips are skin. "Maroon will be bad for face": lips and bindi print skin or white and are hand-painted red. | Man-with-drink review 2; local session |
| Eyebrows | Solid, hole-free shapes with smooth edges. No patchy texture threshold. | Man-with-drink, review 2 |
| Glasses | **The whole frame is one colour, locked**: rims, bridge, nose pads and temple arms. No skin patches anywhere on the frame. | Man-with-drink, reviews 2–3 |
| Leaks | No colour spill at contacts (hand against clothes, sleeve hems, collar, hairline). Edges must follow the sculpt. | Man-with-drink, reviews 2–4 |
| Previews | **Always send straight-front previews** (full figure and face) with every revision, rendered from the exported file. | Man-with-drink, review 3 |
| Colours | Pick print colours only from the stock list in section 2. Say clearly when a requested colour (clear glass, brown iris) isn't stocked and what replaces it. | Filament list |
| Details | Beads and bracelets get 1–2 colours at most (customers accept this). The owner zooms in on faces, brows and beards, so edges there must be clean. | Local session |
| Face dots | **No raised bindis, moles or dots.** Remove them from the art before Tripo ("plain smooth skin" in ChatGPT), then paint them flat on the model. Tripo turns every dark dot into a bump. | Local session, customer rule |
| Bases | Printed separately and glued, so each model gets a flat bottom and no base. | Local session |
| Generation | Ask before spending Tripo credits. Prefer a model whose hidden back colours are already right (see section 6). | Toolkit and family comparison |

## 2. Filament stock (as of 2026-11-18, mostly Numakers PLA+ 1.75 mm)

| Filament | Slicer hex | Preview hex | Notes |
|---|---|---|---|
| Pure White | #F1ECE1 | | Use where the art asks for ivory or cream. |
| Apricot (skin) | #E6BAA8 | **#DEA485** | Prints darker than its swatch. Use the preview hex for renders. |
| Black | #0E0E10 | | Default for hair, beard, brows and lash lines (black, not brown). |
| Nuclear Red | #BB1E10 | | |
| Imperial Red (maroon) | #6E0B05 | | |
| Gold, silk PLA | #EFC13A | | Sticks poorly to the bed. Put supports, raft and wipe tower on white. |
| Yellow / gold | #FFCC33 | | Possibly the same spool as the silk gold. |
| Simply Silver | #8C979D | | Grey hair, metal frames, glassware. |
| Tan / milk-brown | #976E52 | | |
| Dark chocolate brown | #4C2C21 | | |
| Royal Blue | #01387B | | |
| Light Blue | #007CB0 | | Approximate. |
| Orange | #F9A800 | | Approximate. Used for whisky. |
| Pink (Cotton Candy) | #F2B3C0 | | |
| Purple | #854C83 | | |
| Grass Green | #00B51B | | Sealed. |

Printer: a Snapmaker U1 with 4 heads. More colours are possible only with manual swaps at set heights. During a pause any head can be reloaded, and it auto-purges.

**Slicer and U1 facts** (verified on real slices by the local session, Snapmaker Orca 2.4.1):
- **Pauses.** `machine_pause_gcode` is M600. During a pause the owner can reload ANY head from the screen, and each head auto-purges when its turn comes. So a swap only needs a pause between the last layer that uses the old colour and the first layer that uses the new one.
- **Silk gold (#EFC13A)** sticks badly to the bed and to itself.
  - Put support base, support interface and wipe tower on white (filament 3).
  - Keep Walls and Solid infill on the default "1", so the paint decides. Forcing them to one filament risks white showing on visible surfaces.
  - Sparse infill on white is fine. This cost about 10 minutes on an 18 h print.
- **Tilt moves every swap height.** A garland couple tilted −34.5° about X went from 150 to 133.65 mm high.
  - Upright, red and black had a +2.7 mm gap. Tilted, they overlapped by 7.7 mm. The gap stays clean only at ≤10° of tilt.
  - Detect a tilt by rotating the 3MF until each head's Z range matches the G-code (within 0.2 mm).
  - Owner's fix: raise the swap and hand-paint below it. Black covers red; red over black needs primer.
- **Brush-painted Orca saves** store TriangleSelector trees (e.g. `88880C81A80C…`), not simple codes. Decoder: `scripts/orca_paint_decode.py` in tejassparky2/Figurine.
  - Read the hex from the END, one nibble at a time. If `(c & 3) == 0` it's a leaf: state = `c >> 2`, and if that is 3 the next nibble + 3 is the state. Otherwise it splits into `(c & 3) + 1` children, depth-first.
  - One re-save changed the dominant slot of 50,276 faces. Always diff a re-saved project against the previous one (`scripts/compare_orca_paint.py` here).
- **The G-code is the final truth.** Map each head's visible extrusions (outer wall, overhang, top) back to faces through the 3MF build transform, and read off the real first and last layer for each colour. This caught an upper-lip strip printing black that the model view hid.

The owner hasn't yet said whether to use 0.2 mm or 0.4 mm nozzles. Keep painted islands at 0.16 mm² or larger, and lines at 0.4 mm or wider, so either works.

## 3. Default pipeline (run in this order)

Tools are in `coloring/` (generic) and each agent's `<agent> works/<job>/tools/` (as run, with model-specific coordinates). The neutral brief and judge of every job are in `jobs/<job>/`.

1. **Inputs.** Record hashes, triangle counts, texture size and whether the mesh is watertight (`claude works/man-with-drink/tools/inspect_glb.py`). Render each candidate model from 6 sides and compare it with the photo (`texview.py`). Watch for colour bleeding onto the hidden back.
2. **Printable mesh.** `coloring/make_printable.py`:
   - welds and repairs with PyMeshFix,
   - applies quadric decimation to about 1M triangles,
   - places the model Z-up, front toward −Y, feet at z=0, at its final height.
   - Do all colouring at the final size.
3. **Straight paint lines.** `coloring/split_planes.py z1 z2 …` cuts the mesh exactly at horizontal paint lines (liquid levels, hems), keeping it watertight. For curved edges, the local session's **contour split** is the general version: see 4.4.
4. **Texture per face.** `coloring/sample_texture.py`: the median of 4 barycentric samples per face, each projected onto the nearest source triangle with a compatible normal. Median error is about 0.04 mm.
5. **Broad labels.** Use the toolkit's crease-aware alpha-expansion with several texture prototypes per material and region limits (`claude works/man-with-drink/tools/label.py`). Lit and shadowed versions of one material are separate prototypes of the same label, so there is no boundary cost between them.
6. **Part locks, by geometry not texture.** See section 4.1.
7. **Face details.** Use a 40 px/mm front camera with the glasses hidden (`facecam.py`):
   - Trace the eyes as shapes in mm.
   - Make brows and teeth solid smoothed masks (`detail.py`).
8. **Crease snap.** `coloring/crease_snap.py` (or `leakfix.py` with texture prototypes) re-solves a 6-ring band around every boundary with a strong concave-crease prior.
9. **Cleanup and final locks.**
   - Run the sawtooth vote and merge islands under 0.16 mm².
   - Enclosed specks take the colour around them.
   - **Re-apply part locks last.**
10. **Contour split** (`coloring/contour_split.py`), the last colouring step. It replaces the 0.3 mm triangle sawtooth with smooth cuts. Pass `--keep` for areas whose edges are already exact (plane-split liquid lines). Without it, vertices on the plane sit at 50/50 and the straight line turns jagged.
11. **Export and verify.** `export.py` writes a finish guide (one slot per final colour) and a printer project (tool IDs). Reopen both, decode every triangle and compare it with the arrays. Run `scripts/layer_colors.py` at both 0.08 and 0.2 mm bands. Check the swap margins.
12. **Previews.** `coloring/front_preview.py` (always), a 12-view unlit turnaround with an exact palette check, and a lit hero. Decode all of them from the exported file.
13. **Approval gate (required before delivery).** `coloring/approved_match.py <finish-guide>.3mf <out> --approved <image> --prototypes anchors.json` for every approved view. Loop on fixes until PASS, then review every tile sheet and patch crop by eye (section 4.7). The mission prompt `/FIGURINE-AGENT-PROMPT.md` has the full loop.

## 4. Techniques that worked

### 4.1 Part lock by cone thickness (the biggest win)

Colour-based masks fail wherever two materials touch, because the texture is blurred and shaded there. Separate parts by **shape** instead.

**Cone thickness.**
- Fire 9 inward rays per face: the axis, plus 8 rays at 40° to it (embree via trimesh).
- Keep the shortest exit distance.
- A wire that is half-buried in the face still exits quickly in some direction.
- A single straight inward ray fails there: it travels through the head and reads "thick".

**Thin networks (glasses frames, wire jewellery, straps).**
- Tool: `coloring/thin_network_lock.py`.
- Take faces thinner than about 1.5× the wire diameter inside a box.
- Keep the connected networks of at least 300 faces.
- Paint them in one colour **as the very last step**.
- Man-with-drink: 1.25 mm limit, 29,673 faces, which covers the rims, double top bar, bridge, pads and temple arms.

**Thin part against a thick body (hands on clothes, arms on torso, ears on hair).**
- Tool: `coloring/part_lock.py`.
- Work only in a band around the existing boundary inside a box.
- Faces thinner than `thin_mm` belong to the part; faces thicker than `thick_mm` belong to the body.
- Then solve one binary min-cut with a strong concave-crease prior.
- Man-with-drink thumb against the trouser leg: thin 7 mm, thick 10 mm, 10 rings, λ 3.

**Hollow vessels (glasses, cups).**
- Fit the axis and radius from the wall faces with least squares.
- Use the radial distance and how much each face's normal points away from the axis.
- Fill the liquid between plane splits on the outer wall, the inner wall and the inner floor.
- Anything within the wall radius plus a small tolerance is the vessel, not fingers. Fingers pressed against it are hidden anyway.

### 4.2 Crease snapping

- The toolkit's boundary weight is length × exp(−(angle/σ)²): σ 14° for concave edges, 45° for convex.
- Paint edges then land on sculpted folds: sleeve hems, collar, hand contact, hairline.
- Re-solve only a narrow band around the boundaries, with a weak data term; everything outside the band stays fixed.
- With texture prototypes: `leakfix.py`, texture weight 0.35, λ 12. Without texture: `coloring/crease_snap.py`.

### 4.3 Facial features

- **Eyes.** Don't threshold by colour: the brown iris and the shadowed lid share a colour.
  - Trace in mm on a gridded crop at 120 px/mm: upper lid, lower lid, iris circle.
  - The opening is white, the iris inside the opening is black, plus a 0.40 mm lash line.
  - Add catchlights or wings only if a stylised look is requested.
- **The sclera can be mid-grey in the texture** (L* about 62). It is separated from skin by its very low chroma, not by brightness.
- **Brows and teeth.** Threshold inside a window, then:
  - close the gaps, keep the large pieces,
  - fill holes, open,
  - Gaussian-smooth the contour (`solid()` in `detail.py`).
- **Hide occluders** (glasses) in the face camera, so the skin and eyes behind the frame get painted.

### 4.4 Contour split for clean curved edges (local session, `projects/maroon_refine.py` in the Figurine repo)

- Average each filament's share onto the vertices.
- Cut triangles where two filaments' shares are equal. Shared edge points keep the mesh watertight and conforming.
- Use ITER 0 for the vertex labels; 2 ate thin eye-white crescents.
- Use 4 smoothing passes for the cut positions.
- This removes the 0.3 mm triangle sawtooth on eyes, brows and beards.
- **Ported: `coloring/contour_split.py`** (vectorised; regression asserts no open edges, the same body count and the area to 1e-6).
- On the man with the drink it added 14k faces and visibly smoothed the eyes, brows, teeth, frame edge and thumb.
- **Lesson: protect exact edges with `--keep`.** Cuts are blocked on edges a kept face touches, propagated to a fixed point, so no T-junctions form.
- The local session's next idea: leave vertices on concave folds unsmoothed, so the cut stays on the fold (`--protect-folds DEG`; not yet A/B-tested).

### 4.4b Texture noise on smooth shapes (beads, buttons): patch majority (local session A/B)

- Crease snap can't fix texture noise on a smooth sphere: there is no fold to snap to.
- Patch majority, with a gotcha: fold edges never form closed loops, so the components between fold edges merge into one giant patch.
- Fix: mark the fold **faces** (concave > 15°) as a barrier, dilate 1 ring and take the connected components. Give the barrier faces back to the adjacent small patch.
- Patches under 80 mm² then take their area-majority colour. Each bead becomes its own patch of about 50 mm².
- Limitation: where beads touch, they merge through the barrier.
- Still to A/B on that model: thin_network_lock or part_lock for strings of beads.

### 4.5 Remove baked shadows at the source

- Tripo Studio's Texture tool with **Remove Lighting at 4K** (20 credits) removed shadow patches that thresholds couldn't.
- Ask before spending the credits.
- Get colour from the Tripo texture, not by projecting the reference art onto the mesh: that misregisters by about 1 mm.

### 4.6 Swap planning

- One head can carry two colours when their height ranges don't overlap.
- Man-with-drink: orange 89.2–97.6 mm and white 147.8–172.5 mm share T4, with the swap at 120 mm.
- Check this with `scripts/layer_colors.py` (no band with both colours).
- Assert the margins in `export.py`.

### 4.7 Approval gate: comparing with the approved image pixel by pixel (`coloring/approved_match.py`)

What it does:
- Separates the figure from the background.
- Solves the camera from silhouettes: yaw, pitch, roll, scale, shift and perspective. A coarse grid, then Nelder–Mead on a soft IoU.
- Applies a smoothed, capped optical-flow correction for the generator's shape drift. It's kept only if it raises label agreement.
- Labels the approved art by slot, using vision-picked anchors and region voting.
- Renders the model's finish labels from the same camera with a depth-tested triangle-ID raster, then compares the two.

What it outputs:
- `report.json`: verdict, per-slot IoU, confusion matrix, boundary offset in mm, and patches with their faces and 3-D centroids.
- `patches/patch-NNN.png`: approved | model | difference crops.
- `tiles/sheet-NN.png`: every tile of the figure, for vision review.
- `patch_faces.npz` and `camera.json` (reuse the camera with `--camera` for fast rechecks).

Verdicts and exit codes: PASS 0 · FAIL 1 · CANNOT_JUDGE 2 · NEEDS_REVIEW 3 (close calls between near-identical colours in the art).

Measured (`approved_match_selftest.py`, reviewed wedding guide, hidden camera with perspective, shading and anti-aliasing):
- Camera recovered within 0.1°.
- The clean model PASSes.
- A planted 30-face skin→ivory leak (6.8 mm² of surface) FAILs, located within 0.4 mm. A 1,500-face leak is located within 0.8 mm.

Run on a real image (the maroon portrait, which is *not* the image the mesh was generated from):
- Silhouette IoU 0.943 rigid, 0.952 after drift correction.
- Without anchors the shaded cream trousers read as skin, and the gate falsely flagged 97 mm².
- With 25 vision-checked anchors the remaining top patches were art-versus-geometry offsets (beard edge, braid gap), not paint errors.

Rules learned building it:
- **Use the exact image the model was generated from as the approved view.** Another render of the same couple differs in pose, and the gate says CANNOT_JUDGE or produces false patches.
- **Anchors, not boxes.** A sample box that clipped the gold coat hem turned "shadow cream" gold-brown and flipped the whole face to ivory. Pick small `@x,y,r` points on a gridded zoom, lit and shadowed, and act on every `CHECK ANCHOR` warning. In the first attempt, 3 of 25 anchors were on the wrong material.
- Self-calibration amplifies its first guess, so anchored slots skip it.
- Shadowed cream and face skin can be the same colour in a render. Region voting and anchors resolve most of these. What's left is NEEDS_REVIEW and must be judged by eye, never auto-passed.
- Ivory or white art on a white background loses its edge in the cut-out (braid, feather). Ask for a transparent PNG or pass `--mask`.

## 5. Failures — don't repeat

- Colour thresholds for eyes, glasses frames or hand/clothes contacts. Each needed a geometric or traced replacement.
- A single inward ray for thickness (it misses half-buried wire). Use the cone.
- Hue alone to separate orange skin from whisky. Use the vessel geometry.
- A camera depth cutoff for "the glass top" without a height limit: the face sits at the same depth.
- Changing labels after the locks are applied. Locks must come last.
- Pupils or catchlights on a realistic model. Black inside a mouth.
- Smoothing labels with ITER ≥ 2: it eats thin features such as eye-white crescents.
- Any depth-unaware 2D fix: it paints through to surfaces behind. Always rasterise triangle IDs with a depth test first.
- Projecting reference art onto the mesh (misregisters by about 1 mm).
- Trusting the 3D texture's colours over the photo: brass frames in the texture versus silver in the photo, and over-orange skin.
- Delivering on rendered previews alone. The owner found every man-with-drink leak by eye over 4 rounds; the approval gate exists so the agent finds them first.
- Sampling approved-image colours with boxes, or skipping a `CHECK ANCHOR` warning (approval-gate build).
- Judging a model against an approved image it wasn't generated from, and reading pose differences as paint errors.

## 6. Choosing among generated models

On the family portrait:
- Meshy was watertight, with an 8K texture and correct colours on the hidden back.
- All three Tripo versions bled navy or lilac onto the back of the man's white T-shirt, and two weren't closed.

Always render the back before choosing.

## 7. Open experiments (next models)

- **Headless slicing.** Snapmaker Orca CLI `--info` / `--slice`, to confirm supports and paint on the real toolpath. Not yet done for any model.
- **Contour split with fold protection** (`--protect-folds`): A/B against the plain version on a beard or hairline.
- **Tilt-aware swap check.** Compute swap heights after the owner's chosen orientation, and verify them against the G-code (section 2).
- **De-shading before labelling** (research note): AO division and a down-weighted L*.
- **MediaPipe landmarks** to propose eye and mouth tracings automatically, then hand-check them.
- **Auto-detect contact pairs** for part locks: boundaries where thickness changes sharply across a concave crease.
- **Family bust A/B (local session):**
  - Baseline: hands clean, glasses OK.
  - Crease snap: cleaner finger webbing and frame base, but a black wedge at one brow end, and the beads not fixed.
  - Patch majority: fixed the front beads.
  - Next: thin_network_lock and part_lock on the same beads and frame.
  - Open problems: a cheek patch baked into the texture (fix at the source with Remove Lighting), a fuzzy hairline (contour split), buttons that go teal with no grey slot, and teal irises (traced eye pass).

## 8. Model log

| Model | Rounds | What the owner flagged | Fix now in the pipeline |
|---|---|---|---|
| Wedding couple (150 mm) | Many (see reviewed/) | Jewellery, flowers, cuffs, gaze | Graph cut, traced eyes, material locks, leak audit |
| Garland couple and others (local session) | — | Black in mouths, goggle eyes, tilt broke the swap gap, silk gold adhesion, one re-save repainted 50k faces | Contour split, M600 any-head swaps, G-code truth check, supports on white |
| Man with drink (220 mm) | 4 | 1. Leaks, Pixar eyes, black mouth, specs patches, brows. 2. Specs patches. 3. Hand patch | Crease snap, realistic eyes, teeth-only mouth, solid brows, glasses lock (cone thickness), hand part lock, front previews |
