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
