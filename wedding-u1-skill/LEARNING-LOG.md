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
- **How:** recorded hashes, triangle counts, texture size and whether each mesh is watertight. Rendered each unlit from 6 sides (`jobs/man-with-drink/tools/texview.py`).
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
