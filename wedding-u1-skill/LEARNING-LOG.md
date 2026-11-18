# Learning log

This is the chronological record of every lesson, newest last. Each entry answers **what** happened, **how** it was done, **why** it worked or failed, **when** to use it, the **result**, and where the **files** are.

The [PLAYBOOK](PLAYBOOK.md) holds the current best practice distilled from this log. When an entry changes best practice, update the playbook in the same commit.

---

## 2026-11-18 · Environment setup (cloud container, Linux)

- **What:** installed the pinned pipeline and proved it end to end.
- **How:**
  - Create the venv with `python3.12 -m venv ~/.venvs/figurine`.
  - Install with `pip install -r wedding-u1-skill/reviewed/requirements.txt`. This includes `requirements.lock`, pymeshlab, pymeshfix and reportlab. `pip check` must be clean.
  - Install the system packages `libegl1 libegl-mesa0 libgl1-mesa-dri libgles2 libgl1` for headless ModernGL. Mesa llvmpipe gives OpenGL 4.5.
  - Also install `libopengl0 libglu1-mesa`. Without them, PyMeshLab's meshing filters fail to load (`libOpenGL.so.0` missing) and decimation is unavailable.
  - Download Google Drive files with `gdown` from a separate tools venv: `gdown --folder <url>` for folders, `gdown <file-id>` for files (this gdown version has no `--fuzzy` flag).
- **Why:** the repo needs EGL rendering and PyMeshLab, and neither works without these libraries.
- **When:** at the start of every fresh container.
- **Result:**
  - `scripts/replay.py` plus `verify.py` reproduced all six flat-release outputs byte-for-byte in 2 min 49 s.
  - Running Python inside the repo leaves `__pycache__`, which the stop hook flags as untracked. A root `.gitignore` now excludes it.
- **Not available:** Blender and Snapmaker Orca are not installed in the container. Geometry tools replaced Blender (see the glasses entry). Slicing remains unverified.

## 2026-11-18 · Choosing the generated model (family portrait, dropped)

- **What:** compared one Meshy and three Tripo GLBs of the same family photo.
- **How:** recorded hashes, triangle counts, texture size and whether each mesh is watertight. Rendered each unlit from 6 sides (`claude works/man-with-drink/tools/texview.py`).
- **Why it matters:** the generators invent the hidden back.
  - All three Tripo versions bled navy or lilac onto the back of the man's white T-shirt, and two were not closed.
  - Meshy was watertight, with an 8K texture and correct back colours.
- **When:** whenever more than one candidate model exists. Always render the back.
- **Result:** Meshy was recommended. The owner then dropped this model for the caricature.

## 2026-11-18 · Man with drink, round 1 (first delivery)

- **What:** a 220 mm Tripo caricature for the 4-head U1.
- **How:**
  - `make_printable` (repair, decimate to 1M, place upright) → `split_planes` at the liquid line → `sample_texture` (median of 4 samples per face) → broad graph cut with texture prototypes and region limits → traced eyes → whisky rules → islands → export → verify.
  - Colours came from the owner's stock list. A single swap works because orange (89–98 mm) and white (148–173 mm) never share a height.
- **Why these choices:**
  - The skin texture was too orange, so skin is Apricot.
  - The frames were brass in the texture but silver in the photo; the photo wins.
  - Clear filament isn't stocked, so the glass is silver.
  - The brown iris has no head left, so it's black.
- **Result:** delivered, and the files verified on reopening.
- **Lessons:**
  - The whisky and the orange skin share a hue, so the glass needed geometry: a fitted cylinder axis, the radius, and how much each face points away from the axis.
  - The jagged liquid line came from sliver triangles. Splitting along the plane fixed it.
  - A depth rule for "the glass top" also caught the face, which sits at the same depth. Always add a height limit.

## 2026-11-18 · Man with drink, round 2 (owner: leaks, Pixar eyes, black mouth, specs patches, brows)

- **What:** the owner wanted realistic eyes (no white dot), no black in the mouth, solid brows, no colour leaks, and the glasses all one colour.
- **How:**
  - **Eyes** (`detail.py`):
    - Traced in mm on 120 px/mm gridded crops: almond opening, iris circle, 0.40 mm lash line.
    - The catchlight and the eyeliner wing were removed.
  - **Mouth:** a smoothed teeth mask only. Everything else in the mouth is skin.
  - **Brows:** threshold, then close, keep large pieces, fill holes, open and smooth (`solid()`).
  - **Leaks:** `leakfix.py`, the crease snap. It re-solves a 6-ring band around each boundary with a weak texture term and a strong concave-crease prior (σ 14°).
- **Why it works:**
  - The texture is blurry and shaded at material contacts, but the sculpt has a fold there.
  - Weighting boundaries by crease puts the paint edge on the fold.
  - Thresholds fail on the eyes because the brown iris and the shadowed lid have the same colour.
- **When:** on every model, as a default step after the broad labels.
- **Result:** brows, eyes, mouth, sleeves and collar were accepted. The glasses still had patches.

## 2026-11-18 · Man with drink, round 3 (owner: glasses still patchy; "use headless Blender or lock colours")

- **What:** the bridge bar and the inner rims, which are half-buried in the nose, still read as skin.
- **How:** **cone-thickness glasses lock** (`coloring/thin_network_lock.py`).
  - Fire 9 inward rays per face (the axis plus 8 at 40°) and keep the shortest exit.
  - Faces under 1.25 mm thick form the frame: the largest connected network, 29,673 faces.
  - Force it to silver as the final step, after every other pass.
- **Why:**
  - A single straight inward ray from a half-buried wire travels into the head and reads "thick".
  - Some ray in the cone always exits through the wire within about 1 mm.
  - Locking last means no later pass can repaint it.
- **When:** for glasses, wire jewellery, straps and any thin attachment that must be one colour.
- **Result:** the owner confirmed "Glasses done".
- **Lesson:** a request to "use Blender" really means "use geometry". Do it in trimesh/embree when Blender is absent.

## 2026-11-18 · Man with drink, round 4 (owner: hand still has a patch)

- **What:** a ragged skin edge where his left thumb rests on the trouser leg.
- **How:** **part lock** (`coloring/part_lock.py`).
  - Measure cone thickness inside a box around the hand.
  - In a 10-ring band around the skin/black boundary, faces thinner than 7 mm are skin and faces thicker than 10 mm are trousers.
  - Solve one binary min-cut with a strong crease prior (λ 3). This changed 914 faces.
- **Why:** the thumb is 2–6 mm thick and the leg is 15–30 mm. Shape separates them where the texture can't.
- **When:** for any thin body part touching a thick one: hands on clothes, arms on the torso, ears in hair.
- **Result:** clean at 45 px/mm; the owner moved on to persistence.

## 2026-11-18 · Merged with the local figurines session

- **What:** pooled findings with the session on the owner's computer ("Build setup and live test", repo tejassparky2/Figurine).
- **How:**
  - Messaging that session needed the owner's one-time approval for cross-device messages. Approving it permanently limits this cloud session to trusted devices.
  - Their findings were merged into PLAYBOOK sections 1, 2, 4.4, 4.5 and 5.
- **Key imports:**
  - Orca brush paint is saved as TriangleSelector trees, and one re-save repainted 50,276 faces.
  - M600 pauses allow reloading any head.
  - Tilting the model moves every swap height.
  - Silk gold needs support base, interface and wipe tower on white.
  - The G-code is the final truth check.
  - Contour split gives clean curved edges.
  - Tripo Remove Lighting removes baked shadows.
- **Conflict resolved:** catchlights depend on the style. Realistic models get none (owner, round 2); stylised models get one (local session).
- **Next:** port contour split into `coloring/`, and merge their A/B results of part lock and crease snap on the family bust.

## 2026-11-18 · Contour split ported and adopted; the local session's family-bust A/B merged

- **What:** smooth paint edges cut through triangles, replacing the 0.3 mm per-triangle sawtooth on eyes, brows, teeth, the frame edge and the thumb.
- **How:**
  - `coloring/contour_split.py`, ported and vectorised from the local session's `maroon_refine.py`.
  - Area-weighted label shares go onto the vertices; ITER 0 for the vertex colours.
  - T_ITER 4 smoothing is used only for the cut positions, with one shared cut point per edge.
  - Two-colour triangles become 3 triangles, three-colour triangles 6. Single-face dots keep their colour.
  - Runtime 6.5 s for 1M faces. Asserted: no open edges, 1 body, area unchanged to 1e-6.
  - Applied after the locks, then exported with `MESH=cs.npz`.
- **Why:** the shares are smooth across the surface, so the cuts follow a smooth contour instead of triangle edges. The shared edge points keep the mesh conforming.
- **Failure found and fixed:** the exact plane-split liquid line went jagged, because vertices on the plane sit at 50/50.
  - Added `--keep mask`: kept faces are untouched, and cuts are blocked on any edge they touch, propagated until stable (no T-junctions).
  - The liquid line is straight again.
  - Before/after images: `claude works/man-with-drink/renders/contour-split-ab.png` and `contour-split-without-keep-glass.png`.
- **When:** as the last colouring step on every model. Use `--keep` wherever an edge is already exact.
- **Result:**
  - The man with the drink went to 1,022,958 faces.
  - Both 3MFs re-verified (decode, watertight, layer check at 0.08 and 0.2 mm, swap margins).
  - Front previews regenerated.
- **Merged from the local session's family-bust A/B:**
  - Crease snap can't fix texture noise on smooth beads (no fold). Patch majority with fold faces as a barrier can.
  - New customer rule: remove raised bindis, moles and dots from the art before Tripo.

## 2026-11-18 · Approval gate: checking the model against the customer-approved image, pixel by pixel

- **What:** the owner's goal is a 1:1 match with the approved image, with no leaks or patches, and the agent must verify that itself. Until now every leak was found by the owner, over 4 man-with-drink rounds. Added `coloring/approved_match.py`, the gate, plus `approved_match_selftest.py` and the shared mission prompt `/FIGURINE-AGENT-PROMPT.md` (loaded for Codex/GPT through `/AGENTS.md`).
- **How:**
  - Separate the figure from the background (alpha, `--mask`, or border colour).
  - Solve the camera from silhouettes: a 17×9 yaw/pitch grid with closed-form scale and shift, then Nelder–Mead over 7 parameters including perspective, on a soft IoU.
  - Apply a smoothed (4 mm) and capped (2 mm) optical-flow correction for generator shape drift. It's kept only if it raises label agreement.
  - Label the approved art by slot. Chroma-weighted Lab nearest-prototype; vision-picked `@x,y,r` anchors per slot; self-calibration for un-anchored slots; a 3×3 mode filter; graph-segmentation region voting that settles only unsure pixels.
  - Render the finish labels with a depth-tested triangle-ID raster from the same camera and compare, with a 0.35 mm edge band.
  - Output: patches with faces, mm², 3-D centroid and zoomed crops; tile sheets of the whole figure; per-slot IoU and confusion matrix; boundary offset in mm; verdict PASS/FAIL/CANNOT_JUDGE/NEEDS_REVIEW.
- **Why:**
  - Previews show the model, not the difference from the approved image. The gate turns "does it match?" into numbers and crops tied to faces.
  - A close call whose runner-up is the model's colour counts as consistent, not as a leak, and is reported separately.
- **When:** every job, every approved view, on the exported finish guide, before every delivery. Then review the tiles by eye.
- **Result** (self-test on the reviewed wedding guide; hidden camera with perspective, shading and anti-aliasing):
  - Camera error under 0.1°. The clean model PASSes.
  - A 30-face (6.8 mm²) skin→ivory leak FAILs, located 0.39 mm off. A 1,500-face leak FAILs, located 0.80 mm off.
  - Real maroon portrait (`inputs/reference/2.png`, not the generation image):
    - silhouette IoU 0.943 → 0.952 after drift correction;
    - 25 anchors;
    - 0.86% clear disagreement and a 16 mm² largest patch.
  - The top patches I reviewed were art-versus-geometry offsets (beard edge, braid gap), not paint errors.
- **Failures found while building it, now in PLAYBOOK §4.7 and §5:**
  - A sample box clipped the gold hem and flipped the face to ivory. 3 of 25 hand-picked anchors were on the wrong material, which led to the `CHECK ANCHOR` warning.
  - Self-calibration amplifies a wrong first guess, so anchored slots skip it.
  - Shadowed cream equals face skin in this render.
  - Ivory on a white background loses its edge in the cut-out.
  - Region voting that overruled confident pixels erased the lips. The self-test caught that regression, and only unsure pixels are voted now.
- **Not verified:** a gate PASS on a real job, since no real job has run since. Back views and multi-view sheets haven't been exercised on real art.
- **Next:**
  - Background matting for white-on-white art.
  - Segmentation-model masks (SAM family) to place anchors and part masks automatically.
  - Turn the man-with-drink owner findings into regression cases.

## 2026-11-18 · Per-agent folders and a scored competition (owner request)

- **What:** each agent works only in its own folder, and a referee awards points so the better method wins.
- **How:**
  - `gpt works/` was renamed `codex works/`, since Codex made it.
  - `jobs/man-with-drink/` was moved to `claude works/man-with-drink/`. Its `run_all.sh` paths still resolve, since the folder depth is the same.
  - `jobs/<job>/` now holds only the owner's neutral brief and `judge/` (approved views, referee anchors, masks).
  - `scoreboard/score.py` runs the approval gate with the judge on every `<agent> works/<job>/submission.json`. It ranks the results (verdict tier, then clear disagreement, then the largest clear error) and appends points to `ledger.json`, storing the judge's hash with each result. It regenerates `SCOREBOARD.md`, and the owner's accept/defect verdicts are recorded with `score.py owner`. Rules are in `scoreboard/RULES.md`.
  - The root wedding releases stay at the root because the replays read them there. They're credited to Codex in the job brief.
- **Why:** no confusion over who changed what. One judge for everyone makes the comparison fair, and the owner's acceptance carries the most points because the customer is the real judge.
- **Result:** two practice rounds (0 points, since neither judge is official yet):
  - **wedding-couple, Codex** (`codex works/Wedding-contours-guide.3mf`): FAIL, 0.695% clear disagreement, largest 17.2 mm². The reviewed root release measured 0.86% on the same judge, so Codex's contact + contour round improved the match.
  - **man-with-drink, Claude**: CANNOT_JUDGE. The anchor check showed the customer photo's skin, hair and glass differ from the owner's chosen filaments. The judge photo must be recoloured to the decisions before it can be official.
- **When:** every job. Write `submission.json`, run the referee, and record the owner's verdicts.

## 2026-11-18 · `improvements/`: agents pass improvements to each other (owner request)

- **What:** a shared exchange where Codex, Claude or any agent posts an improvement with evidence, and every agent tries the new proposals before its next job and appends a trial result.
- **How:**
  - Use `improvements/TEMPLATE.md`: front matter, then problem, method, evidence, how to use it, and a trials table.
  - `improvements/index.py` builds `INDEX.md`.
  - Statuses run proposed → confirmed (by a *different* agent or the owner) → adopted, or rejected or superseded.
  - Confirmation earns the author +2 (`scoreboard/RULES.md`).
  - AGENTS.md, CLAUDE.md and the mission prompt now require reading the index before a job and posting trials and proposals after it.
- **Seeded with four real entries:**
  - Codex: contact seeds + contour split.
  - Codex: surface leak audit.
  - Claude: approval gate.
  - Claude: cone-thickness locks (confirmed earlier by the owner on man-with-drink).
- **New evidence from seeding** (practice wedding judge, front view, measured by Claude):

  | Release | Clear disagreement |
  |---|---:|
  | Reviewed release | 0.859 % |
  | After leak audit | 0.932 % (slight regression on the visible front) |
  | After Codex's contact seeds + contour split | 0.695 % (best) |

  Recorded as trials on both Codex entries.
- **When:** every job, at the start and at the end.

## 2026-11-18 · Deepak base in Blender (owner: "make this base only in blender")

- **What:** the two-tier display base with a curved gold nameplate and raised lettering, from the approved Deepak render. The output is one watertight multicolour 3MF.
- **How:** `claude works/deepak-base/tools/make_base.py`, run headless in Blender 4.0.2 (apt).
  - The body is lathed from a profile with ring quads and fans to the axis.
  - The plate is a structured curved slab, so it follows the 57 mm tier radius exactly.
  - Lettering: font curve → mesh, then each vertex is mapped onto the cylinder.
  - Exact boolean union with `material_mode='TRANSFER'`, so each face keeps its material. Material index becomes the Orca paint code.
  - Verified outside Blender with trimesh, `layer_colors.py` and `front_preview.py`.
- **Why it failed at first, and the fixes:**
  1. The distro Blender has no `wm.stl_export`, so binary STL is written directly.
  2. Splitting long glyph edges with `subdivide_edges` corrupted glyph caps (edges shared by 128 faces), so it was removed. Straight chords on a 57 mm radius sag < 0.1 mm, well within the 0.3 mm embed.
  3. A reversed ledge arc duplicated a profile ring (360 edges with 4 faces). Caught by the edge-incidence check.
  4. Cycles needs `use_denoising=False`: the distro build has no OpenImageDenoise.
  5. My first colour samples used coordinates from the *scaled* preview of the photo and hit the background. Re-sampling on a gridded crop of the full-resolution image also revealed the **two-tier** shape, which the thumbnail hid.
- **When:** any parametric part (bases, nameplates, plaques). Run the edge-incidence and single-body checks after every boolean, and sample reference colours only on full-resolution gridded crops.
- **Result:**
  - 120 × 120 × 30.5 mm; one body; watertight; 34,920 triangles.
  - 3 colours with no swaps (Tan base, Gold plate, Dark chocolate lettering).
  - Matches the approved render by eye.
  - Not sliced in Orca, and no gate run (the approved image is cropped and the figure occludes the base).
- **Blender is now usable in the cloud container** (`apt-get install blender`): this supersedes "Blender not available" in the setup entry.

## 2026-11-18 · Deepak base, round 2 (owner: darker chocolate base; add the espresso machine and coffee sack to print with the base)

- **What:** the base is now Dark chocolate. The espresso machine and burlap sack (`claude works/deepak-base/tools/props.py`) are unioned onto the base top, and the figurine is glued on later.
- **How:**
  - Colours come from stock, six in all: Dark chocolate, Gold, Black, Silver, Apricot, White.
  - The script plans the four heads itself: colours used at or below the base top on H1–H2; at z = 30.4 mm one pause swaps them for prop colours; H3–H4 are preloaded with the other prop colours.
  - The base height is 30.4 mm, a whole number of both 0.08 and 0.2 mm layers, so the swap falls on a layer boundary.
- **Failures and fixes:**
  1. Joining all parts into one tool for a single self-intersecting exact union left 620 open and 1,996 doubled edges. Unioning one part at a time is clean.
  2. A separate torus rim meeting the bean dome almost tangentially left open edges. The rim is now part of the sack's own lathe profile, and the dome starts inside the rim tube.
  3. A ring of sack vertices lay exactly on the base top plane (degenerate). Sunk bottoms now put that plane mid-edge.
  4. Overlapping beans leave zero-volume sliver shells. The build keeps only the main shell and asserts any dropped shell is under 2 mm².
  5. The weave grooves were narrower than the mesh spacing and aliased into noise. They're now wider grooves (0.27 mm) on 400 segments.
  6. My first head-plan check hard-coded the swap from an earlier run and reported 52,983 false mismatches. The check now derives each head's colour from the exported files.
- **When:** any multi-part prop scene. Union sequentially, avoid near-tangent and coplanar contacts, check edge incidence and body count after every build, and derive swap plans from the files.
- **Result:**
  - One body, watertight, 156,364 triangles, 120 × 120 × 73 mm.
  - At most 4 colours per 0.08 and 0.2 mm band; each head prints one colour per range.
  - Matches the approved composition by eye. The handle is deliberately angled for printing.
  - Not sliced in Orca.

## 2026-11-18 · Deepak base, round 3 (owner: "coffee bag not good and not matching; machine missing 1 match")

- **What the owner flagged:**
  - The sack looked like a pot: stiff, coarse spiky weave, pinkish.
  - The machine lacked the render's signature part: the horizontal portafilter handle sticking out to the right.
- **Root causes:**
  1. I had traded the handle's look for printability (angled up inside the bay) without asking. The owner wants the render's look; supports are acceptable.
  2. The sack was modelled from the thumbnail, not measured. Its weave grooves were sharp and deep, and flat shading exaggerated them.
  3. Apricot was rendered with its slicer hex, although PLAYBOOK §2 says to render it with its printed colour #DEA485.
- **Fixes:**
  - Both props were re-measured on zoomed, gridded crops of the full-resolution render.
  - **Machine:**
    - a horizontal silver portafilter, with a black capsule handle at 13.6 mm, in front of the right column and about 7 mm beyond the side;
    - bay ceiling at 18 mm; panel from 19.1 to 35.3 mm;
    - grey slats; round cup handle.
  - **Sack:**
    - a pillowy profile: rounded foot, near-cylindrical body, left lump;
    - a thick soft collar with the lip widest;
    - a smooth sinusoidal diamond knit, 0.14 mm deep;
    - beans filling the mouth to below the lip.
  - Renders: smooth shading by angle, and Apricot shown with its printed colour.
  - New `out/compare-props.png` puts each prop next to the matching crop of the render.
- **Lessons:**
  - **Match the approved look first, then state the print cost** (here: supports under the handle). Ask before trading the look for printability.
  - Compare each prop against a zoomed crop of the reference, side by side, before delivering, not just the whole scene.
- **Result:**
  - The machine matches the render by eye. The sack matches in shape, collar, knit and beans; it's still more saturated than the render's beige (the closest stock filament), and the beans are black.
  - One body, watertight; at most 4 colours per band; head plan as before (pause at 30.4 mm: H1 → Apricot, H2 → White).
  - Not sliced.

---

### How to add an entry

Copy this template. Commit the log, the playbook and any tool change together, and push the same day.

```
## YYYY-MM-DD · <model>, round N (owner: <their words, short>)
- **What:**
- **How:** (tool, parameters, files)
- **Why:** (root cause, why the fix works)
- **When:** (which situations to reuse it in)
- **Result:** (what the owner said; what was verified, and what wasn't)
```
