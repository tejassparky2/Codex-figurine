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
