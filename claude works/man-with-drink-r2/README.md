# Man with drink, round 2: new Tripo model (d3a4cb08), 220 mm, Snapmaker U1

The same customer job as `claude works/man-with-drink/`, re-run end to end on a **new approved image and a new Tripo
model**. The pipeline is the round-1 one from the repo (`tools/`, copied, coordinates re-measured for this model).

## Inputs (sha256 in inputs.sha256)
- `reference/photo-front.jpg`: the new approved art (712 x 1600). Owner said "run Tripo as is": the thin wire glasses,
  streaky grey hair and clear glass were not cleaned in the art first.
- `inputs-raw/man-with-drink.glb`: Tripo Studio task d3a4cb08-3ced-421a-9ac7-124142d5c0b7 (55 credits), 1,974,166
  triangles, 4K texture. Already watertight as downloaded (0 open, 0 non-manifold edges after a 5 dp weld, 1 body).

## Decisions (same as round 1 unless stated)
- 220 mm, the round-1 height. Measures 76.2 x 81.3 x 220 mm, 356.8 cm3.
- Apricot skin, Black (shirt, trousers, shoes, brows, irises, lash line), Simply Silver (hair, glasses, tumbler),
  Orange (whisky), Pure White (teeth, eye whites). Realistic eyes: no catchlight, no wing. Teeth white, mouth gap skin.
- The tumbler on this model is **solid** (flat top at z 110.6, bottom 93.5), not hollow: whisky is painted on the
  outer wall only, between the base band (95.7) and the liquid line (102.3). The top stays silver.

## Re-measured coordinates (everything model-specific)
| What | Round 1 | Round 2 | How measured |
|---|---|---|---|
| Glass axis, wall radius | (-0.21, -29.55), 6.7 | (-8.05, -31.6), 5.85 | circle fit on mesh sections at z 109.5 (above the fingers) |
| Plane splits | 97.4, 91.0 | 102.3, 95.7 | `renders/grid-glass.png` (30 px/mm) |
| Head threshold | z > 140 | z > 135 | collar top 132.5, chin 138+ |
| Frame region | z 150-190 | z 155-186 | `renders/grid-face.png` |
| Face camera | x -28..28 | x -30..30 | |
| Eyes, brows, mouth | traced | re-traced | `renders/eyeR-grid.png`, `eyeL-grid.png`, `mouth-grid.png` (60 px/mm) |

## Fixes found in review (each verified on a close-up)
1. **Left teeth printed skin.** They sit in shadow (L 41-51, darker than the mouth gap at L 58), so the round-1 colour
   threshold (L > 68) dropped them. Teeth are now a traced polygon intersected with chroma < 40 (lip chroma ~50).
   Before/after: `renders/cmp-mouth.png` -> `renders/cmp-r2b.png`.
2. **Skin notch on the glasses bridge.** The lower bridge bar is fused into the nose at x -8.2..-6.1, so cone thickness
   there exceeds the 1.25 mm wire threshold. A generic "grow the frame by distance + normal" fix was tried and
   **rejected** (it spread silver over the nose bridge, 1713 faces). The bar band is painted by measured geometry (73
   faces) in `finalize.py`. Result: `renders/cmp-bridge.png`.
3. **Black on the tumbler foot.** The foot flares to r 6.9 mm, outside the glass zone, and its shadow became 1268 black
   faces. Nothing black is within 7.5 mm of the glass axis (the shirt is at y -12.8), so they are silver now.
   Result: `renders/cmp-glass.png`.
- The part lock (left hand vs trouser leg) found no boundary: on this model the hand does not touch the leg
  (`renders/cmp-handL.png`).

## Physical schedule (unchanged)
T1 Apricot, T2 Black, T3 Simply Silver, T4 Orange -> pause at 120.00 mm -> T4 Pure White.
Orange top 102.32 mm < 120 < white bottom 149.68 mm (asserted in export.py). `layer_colors.py` at 0.08 and 0.2 mm:
at most 4 colours in any band, no band over the head count.

## Approval gate: FAIL (practice), and why
`gate/round-1`, `gate/round-2` (camera IoU 0.968). Round 2 has corrected silver anchors and a brow anchor. It reports
clear disagreement of 1.87%, and the largest patches are the owner's decisions or art-vs-sculpt differences, not leaks:
- the clear glass shows the black shirt through it in the art; the model's glass is silver (owner decision, clear
  isn't stocked);
- the art's 0.3 mm wire frames vs Tripo's thick sculpted frame, painted silver over what is skin in the art;
- the art's hair has dark streaks with the same colour as the brows (both about #543427), so hair/brow pixels
  can't be separated by colour alone.
As round 1 noted, the photo must be recoloured to the decisions before this judge can PASS. Not done.

## Verified / not verified
- Verified: both 3MFs re-open and decode to the intended labels (`export.py`). Watertight, consistent winding, 1 body.
  The figurines repo's `verify_3mf.py` passes both, and `render_3mf.py` renders them.
  12-view turnaround: every pixel is a palette colour. Close-ups of mouth, bridge, glass and left hand.
- Not verified: no slicer has opened these files. No Snapmaker Orca slice, no support check, no G-code, no print.
  The gate does not PASS (see above).

## Run
`P=<venv python> bash tools/run_r2.sh` from this folder.

## Review 2 (owner, 2026-11-19): "the old model had teeth in lower side too"
- **Cause:** only the upper row was traced. The lower teeth are just tips under the upper row: ragged in the texture,
  and partly hidden from the straight-front camera.
- **Tried and dropped:** whitening light, low-chroma faces seen from a camera 30° below the mouth. It gave a ragged
  strip and left the sculpted lower teeth skin.
- **Fix (`detail.py`):** the traced area is the whole mouth opening, from the upper lip to the lower-lip edge (traced
  on `renders/tex-mouth-hi.png`), with chroma < 40 so both lips stay skin. Skin pieces fully enclosed by white inside
  the mouth box also become white.
- **Result:** `renders/cmp-lowerteeth.png` (front, and 20° below) and `out/Man-with-drink-front-face.png`.
  - White covers 0.55% of faces and starts at 148.89 mm, still above the 120 mm swap.
  - Seen from 20° below, a thin skin line remains between the rows (it is not enclosed). Not visible from the front.

## Review 3 (owner, 2026-11-19): "I don't want lower teeth for this model"
- Reverted `tools/detail.py` to the upper-row teeth trace (the first round-2 commit). The export is identical to the
  pre-review-2 version: 1,021,838 faces, white 0.28% of faces, white from 149.68 mm.
- Kept for reference: `renders/cmp-lowerteeth.png` shows the rejected both-rows version.

## Review 4 (owner, 2026-11-19): "there is Tripo lower teeth clay, I don't want that too"
- The sculpted lower teeth are a ~1 mm step, tucked ~1 mm behind the upper teeth, on top of the lower lip
  (`renders/mouth-sections.png`, side cross-sections at x -8, -4, 0, 3).
- **`tools/remove_lower_teeth.py`** (runs after the first `sample_texture.py`, then texture is re-sampled):
  - **Selection:** faces in the mouth box below the upper teeth's bottom edge, behind the lip front, with low texture chroma: 2052 faces, 42.5 mm².
  - **Smoothing:** 80 rounds of Laplacian smoothing with the patch boundary fixed, so the step relaxes into a smooth membrane.
  - **Result:** max vertex move 0.56 mm, median 0.23 mm. Topology unchanged, watertight, 0 self-intersecting faces before and after.
  - The original mesh is kept as `printable-with-lower-teeth.npz`.
- The upper-teeth trace was extended on the right, where those teeth reach lower than first traced, which removes the jagged skin bottoms.
- **Result:** `renders/cmp-flatten.png` (patch, before and after, from below) and `renders/cmp-r4.png` (front, below, bridge).
  - White is 0.34% of faces and starts at 149.67 mm.
  - At most 4 colours per band at 0.08 and 0.2 mm.
