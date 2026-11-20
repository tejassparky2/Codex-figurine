# Man with drink, round 4: customer's own image, 4-view Tripo, 220 mm, Snapmaker U1

## Why a round 4
The customer said the likeness was low ("smile has a slight gap between teeth and gums ... even the tilt of head is
wrong"). Their image is `reference/photo-front.jpg` (= round 1's). Round 2 had been made from a different art.

## Inputs
- **Art:** a ChatGPT printable edit of the customer's image (thicker aviator frames, solid hair and brows; face, smile and tilt kept): `reference/front.png`.
  - Left, right and back views come from one fresh chat each. The side views were then edited so the eyes are open.
  - Owner approved.
- **Model:** Tripo H3.1 multi-view, task f40b6cef (55 cr), `inputs-raw/man-with-drink.glb`, 1,904,884 tris. Owner picked it over round 1 and the round 3 / round 4 retries (see the figurines repo, `projects/man_black_polo/likeness_rounds_r4.png`).

## Decisions
- **Same as r2:** 220 mm; Apricot skin, Black, Simply Silver (hair, frames, tumbler), Orange whisky filled to the bottom, Pure White.
- **Upper teeth only.**
- **New for this customer:** a thin BLACK gap line under the upper teeth, as in the art. It is an exception to "never black in the mouth" (owner choice).

## Re-measured
- Glass: axis (4.6, -28.5), wall r 6.65, solid, z 95.4-112.8, liquid line 109.0.
- Head above z 136.
- Frame region z 160-189.
- Eyes, brows, teeth and gap traced at 60 px/mm (`renders/eyeR-grid.png`, `eyeL-grid.png`, `mouth-grid.png`).

## Fixes in this round
- **`framemask.py`** keeps only frame clusters ≥10% of the largest. Three thin eyelid edges (~500 faces each) had been painted silver as glasses.
- **Teeth/gap:** the upper-teeth bottom edge comes from the geometry, which steps back ~1 mm to recessed lower-teeth tips.
  - Everything between the upper teeth and the lower lip is the gap.
  - Skin slivers inside the gap that the front camera cannot see join it (`finalize.py`).
- **`raisededge.py`**, the generalised `hairedge.py`: run with label 1, z 118-146, to snap the collar/neck edge into the crease. A skin tab sat on the collar top.
- The r2 bridge-notch coordinates are disabled. The bridge was checked on renders.

## Verified / not verified
- **Verified:**
  - Both 3MFs decode exactly, are watertight, and are 1 body.
  - `verify_3mf.py` and `render_3mf.py` in the figurines repo.
  - At most 4 colours per band at 0.08 and 0.2 mm.
  - Orange is used up to 109.0 mm, the swap is at 120 mm, white starts at 155.0 mm.
  - Close-ups of the eyes, mouth (front and 10° below), collar and glass.
- **Not verified:**
  - No slicer, no G-code, no print. Practice gate not run this round.
  - From 10° below, a few thin skin lines remain inside the gap.

## Review (owner, 2026-11-19): "paint pink in place of black so it looks like mouth/tongue"
- The mouth gap is now Pink Cotton Candy #F2B3C0: label 5, code 3C, a 6th finish slot. This replaces the black gap line.
- **Physical plan:** pink rides on T2 between two extra pauses (the export asserts no black/pink band overlap):
  - at 148.0 mm, T2 Black → Pink (body black ends 142.2, pink starts 153.8);
  - at 165.0 mm, T2 Pink → Black (pink ends 157.9, face black starts 172.7);
  - plus the T4 Orange → White pause at 120 mm, as before.
- At most 4 colours per band at 0.08 and 0.2 mm. `renders/cmp-r4-mouth-pink.png`.

## Review (owner, 2026-11-20): "cut open that pink part"
- **`tools/cut_mouth.py`** (manifold3d boolean; `pip install manifold3d` in the e3d venv). It subtracts a cutter shaped like the traced mouth gap:
  - front view: between the upper-teeth bottom edge and the lower-lip edge, inset 0.06 mm;
  - depth: from in front of the face to 1.0 mm behind the front-most surface at each point.
- **Result:** 16.2 mm³ removed. Watertight, consistent winding, 1 body, 0 self-intersecting faces. The cut walls and floor are pink.
  - Side section at x=0 (`renders/cut-section.png`): a slot ~1.2 mm tall and ~2 mm deep behind the teeth line.
- **Tried first and rejected:** extruding the pink patch inward (`carve_mouth.py`). With per-face normals it gave 2684 self-intersecting faces; with a radial direction 1545, and with a ray-limited depth 467. The walls ran into the underside of the upper teeth.
- Export is `MESH=cs_cut.npz tools/export.py`. The T2 pink/black and T4 orange/white plans are unchanged. At most 4 colours per band.
- **Print note:** a 1.2 mm slot under an overhanging tooth row. Check the slicer preview; the teeth ceiling over the slot may want support or a slightly smaller nozzle line width.

## Review (owner, 2026-11-20): "more in" + "his face is not round but in the model it seems round"
- **Mouth cut deepened** to 2.0 mm behind the surface (`cut_mouth.py cs.npz cs_cut.npz 2.0`): 32.4 mm³ removed, 0 self-intersections.
- **`tools/taper_jaw.py`** narrows the lower face to the customer image's taper.
  - Front-view skin width profiles were aligned on the eye line (z 175.2) and mouth line (z 156.0) and compared relative to cheek width.
  - x is scaled about the face centre: 1.0 above z 169.4, 0.88 at the mouth, 0.81 at the jaw (z 144.5), back to 1.0 by z 138.5. The collar is untouched.
  - Vertices only, so the labels are kept. Watertight, 1 body, 0 self-intersections.
  - Before/after: `renders/heads_taper.png`.
- Export is `MESH=cs_taper.npz tools/export.py`. Pauses unchanged. At most 4 colours per band.

## Review (owner, 2026-11-20): "for mouth pink, instead of carving just cut it empty"
- No mouth paint. The gap is an empty slot: `cut_mouth.py cs.npz cs_cut.npz 4.0 0.06 0` (cut faces → skin), then `taper_jaw.py`.
  - The slot is ~1 mm tall and ~5 mm deep behind the teeth line (`renders/cut-section.png`). 63.4 mm³ removed, 0 self-intersections, watertight, 1 body.
  - The renderer has no shadows, so the slot shows as skin in the previews. A real print shades it dark.
- **Pink is gone, so T2 stays black all print.** Only the T4 Orange → White pause at 120 mm remains. The export prints the pink pauses only when pink is present.

## Review (owner, 2026-11-20): "match head shape with photo 1:1"
- **`tools/match_head.py`** (replaces the `taper_jaw.py` taper): a front-silhouette warp of the head onto the customer image.
  - **Heights:** a piecewise-linear map with the eye→mouth scale fixed (7.14 px/mm):
    - hair top 220.0 → 215.3;
    - chin 139.3 → 141.85;
    - eye line and mouth line held.
  - **Widths:** a per-row scale k(z) = photo/model silhouette width (0.76–0.86) and the centre shift (-1.8 to -0.8 mm). Both are sampled every 1 mm and fitted with quartic polynomials.
    - Per-vertex raster sampling made a step field and 932 self-intersections; the fitted field has 0.
  - The warp fades in over z 134–142, so the collar is unchanged. y is unchanged. The whole model is then scaled x1.0218 back to 220 mm.
- **`tools/lift_ears.py`** lifts both ears 2.2 mm (smooth local field, |x| > 22 mm only). The photo's ears sit higher.
- **Result:** the red-outline overlay `renders/match-overlay.png` and before/after `renders/match-before-after.png`.
  - The hair top, temples, ears, cheeks, jaw and chin follow the photo's head outline.
  - Watertight, 1 body, 0 self-intersections. 73.7 x 78.5 x 220 mm.
- **Chain:** `cut_mouth.py cs.npz cs_cut.npz 4.0 0.06 0` → `match_head.py cs_cut.npz cs_match.npz 6` → `lift_ears.py cs_match.npz cs_match2.npz 2.2` → `MESH=cs_match2.npz export.py`.
  - The T4 swap still has room: orange ends at 111.4 mm, swap at 120, white starts at 158.7. At most 4 colours per band.

## Review (owner, 2026-11-20): "add pink in it" + "add this same as photo" (smile-corner creases)
- **Pink slot interior:** `cut_mouth.py cs.npz cs_cut.npz 4.0 0.06 5`, then the same `match_head.py` (σ 6) and `lift_ears.py 2.2`.
- **`tools/smile_creases.py cs_match2.npz cs_match3.npz 1.0 0.35 1.35 2`** adds a short curved groove at each mouth corner, shaped from the photo:
  - his right corner curls up and out, his left turns up;
  - up to 0.88 mm deep, σ 0.35 mm, faded out within 1 mm of the slot and teeth, 2 rounds of local smoothing;
  - 0 self-intersections.
  - Comparison `renders/smile-compare.png`; shaded face `renders/face-ao.png` (`tools/ao_closeup.py` adds ambient occlusion, so slots and creases read as they will print).
- **`export.py`** now computes the T2 pink pauses and the T4 notes from the mesh. This version: T4 at 120 mm (orange ≤111.4, white ≥158.7); T2 black→pink at 152.5 mm and pink→black at 168.9 mm.
- At most 4 colours per band. verify_3mf passed both files. Not sliced.

## Review (owner, 2026-11-20): "revert that curls change ... below teeth fully open and paint pink on lower side ... just as art the inner lower pink"
- **Smile creases reverted.** This version is built from `cs_match2.npz` (no `smile_creases.py`).
- **Mouth opened fully:** `cut_mouth.py cs.npz cs_cut.npz 4.0 0.06 5 1.2`. The bottom of the cut drops 1.2 mm into the lower lip (tapering to the corners), and the inside is pink. 154.9 mm³ removed, 0 self-intersections.
- **`tools/lower_lip_pink.py cs_match2.npz cs_match4.npz 1.2`:** a pink band on the front of the lower lip, from the opening's bottom edge down 1.2 mm, tapering at the corners, as in the art. Comparison `renders/mouth-lip-compare.png`.
- Export is `MESH=cs_match4.npz`. Pauses: 120 T4 orange→white; 151.4 T2 black→pink; 168.9 T2 pink→black. At most 4 colours per band. Not sliced.

## Review (owner, 2026-11-20): "reduce whisky quantity and reduce the eyebrows"
- **`tools/whisky_brows.py cs_match4.npz cs_match5.npz 106.0 0.6`:**
  - **Whisky:** an exact plane split at z 106.0 (watertight, labels inherited). Orange above it inside the glass becomes silver: about half full (glass 97.1–115.7), like the art.
  - **Brows:** black above z 182.6 within 0.6 mm of the brow edge becomes skin. Area 135 → 81 mm², same shape, thinner and a little shorter.
  - Comparison: `renders/brows-whisky.png`.
- Export is `MESH=cs_match5.npz`. Pauses: 120 T4 (orange ≤106.0, white ≥158.7); 151.4 T2 black→pink; 168.9 T2 pink→black. At most 4 colours per band. Not sliced.

## Review (owner, 2026-11-20): "I said inside mouth lower side, not lips"
- The lower-lip band (`lower_lip_pink.py`) is removed. Pink is only inside the opening: floor 2156, ceiling 1424, back/sides 1335 faces. The lips are skin.
- Rebuilt as `whisky_brows.py cs_match2.npz cs_match6.npz 106.0 0.6`; export is `MESH=cs_match6.npz`. `renders/mouth6-cmp.png` shows the front, 20° above (the pink floor) and the shaded front.
- Pauses: 120 T4; T2 black→pink and pink→black from the export notes. At most 4 colours per band. Not sliced.

## Review (owner, 2026-11-20): "just remove pink"
- All pink (4915 faces, the mouth interior) is now skin: `cs_match7.npz`. The open mouth, the head match, the half-full whisky and the thinner brows are kept.
- Back to one pause: 120 mm T4 orange→white (orange ≤106.0, white ≥158.7). T2 stays black.
- 5 finish colours. At most 4 colours per band. verify_3mf passed. Not sliced.

## Review (owner, 2026-11-20): "just open that gap fully below the teeth"
- **Taller, deeper opening, no paint:** `cut_mouth.py cs.npz cs_cut.npz 6.0 0.06 0 2.5`, i.e. 6 mm deep, 2.5 mm lower into the lower lip, tapering to the corners. 382.9 mm³ removed.
- Then `match_head.py` (σ 6) → `lift_ears.py 2.2` → `whisky_brows.py 106.0 0.6` → `cs_match8.npz`. 0 self-intersections, watertight, 1 body.
- **Side cut at x=0** (`renders/cut-section8.png`): the opening is ~3 mm tall (z 155.9–158.9) under the upper teeth and runs >6 mm back. Shaded face: `renders/face8-ao.png`.
- One pause, 120 mm T4. At most 4 colours per band. verify_3mf passed. Not sliced. The tooth row now overhangs a ~3 mm cavity: check bridging/support in the slicer.

## Review (owner, 2026-11-20): "eyebrows not good"
- **Cause:** the brows are sculpted, raised pads. Painting less than the whole pad (the 0.6 mm trim, or `tools/redraw_brows.py` with outlines traced on the photo) leaves skin-coloured raised edges around the black.
- **Fix:** paint the whole sculpted brow again (`whisky_brows.py cs_match2.npz cs_match10.npz 106.0 0.0`).
  - Options compared in `renders/brows-options.png`: photo / trimmed / thin traced / full sculpted.
  - Thinner brows would need the brow pads reshaped in the geometry, not just paint.
- Export is `MESH=cs_match10.npz`. One pause, 120 mm. verify_3mf passed. Not sliced.

## Review (owner, 2026-11-20): "still shows the teeth in skin colour here; don't send the shadow render, the normal one is better"
- The empty opening read as skin in the normal (flat) render: the back of the cut shows Tripo's inner tooth shapes. The inside of the opening is now BLACK: `cut_mouth.py cs.npz cs_cut.npz 6.0 0.06 1 2.5`, then match/lift and `whisky_brows.py ... 106.0 0.0` → `cs_match11.npz`.
  - Black is already on T2 all print, so no extra pause.
- Previews are sent as the normal flat renders only (`out/Man-with-drink-front*.png`). AO renders are for internal checks.
- One pause, 120 mm. At most 4 colours per band. verify_3mf passed. Not sliced.
