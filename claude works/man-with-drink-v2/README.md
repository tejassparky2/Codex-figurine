# Man with drink v2: 220 mm, Snapmaker U1, 4 heads plus one manual swap

This is a regenerated Tripo model (2026-11-19). The owner noticed that the v1 head was turned away from the photo. The colour decisions are the same as in v1 (`../man-with-drink/README.md`, rounds 1–5).

## Why v2: head pose, measured
`tools/head_pose.py` finds the pupils on a straight-front render of the GLB texture and reads their 3-D positions. It was validated on v1, where it reproduces the paint-based measurement (12.4° vs 12.7°).

| | Head turn | Tilt (eye line) | Eye midpoint off the body centre line |
|---|---:|---:|---:|
| Approved photo | ~0° (nose centred between the eyes) | ~5.4° | ~0 mm |
| v1 Tripo | 12.4° | 7.1° | 7.6 mm |
| **v2 Tripo** | **6.0°** | 6.8° | **3.4 mm** |

The tilt is mostly in the photo itself. v2 halves the turn and the side shift. See `renders/head-pose-photo-v1-v2.png`.

## Inputs (sha256 in `inputs.sha256`)
- `inputs-raw/man-with-drink-v2.glb`: Tripo, 1,876,560 triangles, 4096² texture, **watertight as delivered** (v1 wasn't).
- `reference/approved-full-body.jpg` (the owner's full-body image) and `reference/photo-front.jpg` (the v1 reference).

## Colours (stock list) and the U1 plan
| Head | Start | After the pause at 120.00 mm |
|---|---|---|
| T1 | Apricot #E6BAA8: skin | unchanged |
| T2 | Black #0E0E10: shirt, trousers, shoes, brows, irises, lash lines | unchanged |
| T3 | Simply Silver #8C979D: hair, glasses frame, glass rim | unchanged |
| T4 | Orange #F9A800: whisky, used **87.6–99.0 mm** | **Pure White #F1ECE1**: teeth and eye whites, used 148.2–172.5 mm |

- The drink fills the glass **from its bottom to the liquid line at 99.0 mm** (owner, round 5). Only the rim is silver.
- Eyes are realistic: white, black iris, 0.40 mm lash line, no catchlight. The mouth is white teeth only; lips and the gap are skin.

## Pipeline (`tools/`, run in order from this folder; `P=<venv>/bin/python tools/run_all.sh` runs them all)
Same stages as v1. What changed for this mesh:
1. `make_printable.py <glb> 220 1000000`: 1,000,000 triangles, watertight, one body, 76.4 × 79.7 × 220 mm.
2. **New `glass_axis.py`:** RANSAC plus least-squares circle fit of the tumbler wall from geometry. Result: axis (3.607, −29.024), **radius 7.56 mm** (v1 was 6.69), wall 88.4–104.4 mm.
   - **All glass radius limits in `label.py`, `detail.py`, `finalize.py`, `leakfix.py` and the contour-split keep mask are now relative to the fitted radius**, not v1's fixed numbers.
3. `split_planes.py 99.0`: the liquid line, measured on the texture. The glass wall is 76 % orange at 98.5–99.0 mm and 39 % at 99.0–99.5 mm.
4. `sample_texture.py`, `label.py 5`, `views.py`.
5. `framemask.py`: 26,598 frame faces. Its debug highlight no longer needs `final.npy`, so the script now runs start to finish.
6. `facecam.py`, then **`detail.py` with eyes, brows and mouth re-traced on this face** at 40 px/mm on a 0.5 mm grid. Evidence: `renders/eye-his-*-grid.png`, `eyes-traced.png`, `mouth-traced.png`.
7. `leakfix.py 6 12`, `part_lock.py … 14 42 -12 26 44 80 0 1 7 10 10 3.0` (the hand against the trousers), `finalize.py`. The frame lock is applied last.
8. `contour_split.py --keep` (glass zone kept), `export.py` and `render_outputs.py` (hero **straight front**).

## Round 6 (owner: "colour leaks on finger and hair edges not coloured")
- **Finger leak:** the radius tolerances inherited from v1 (tuned for its 6.7 mm glass) reached into fingers pressed against this 7.56 mm glass.
  - `detail.py` now defines the glass by geometry alone: everything inside the fitted radius, the cylinder wall (within 0.25 mm, facing out), and the rim lip including its thicker bead and underside ring.
  - Silver or orange near the glass that fails this test returns to skin.
  - Result: finger contact band 41.4 → 0.0 mm² of orange/silver; rim lip all silver (it had a 14.7 mm² skin band and dark specks).
- **Hair edges:** the texture paints thin grey strokes over skin at the hairline, so the sculpted strands came out skin.
  - New `tools/hairline.py` finds them by shape: skin within 1.8 mm of the hair whose normals deviate more than 6° (0.5 mm average) from their 0.7 mm neighbourhood. It turns them silver, grows whole strands and cleans islands. The frame and the face centre below the brows are excluded.
  - Runs after `finalize.py`: 10,351 faces (256 mm²).
- **Regression test** (`regression/check_round6.py`, with the owner's crops): the delivered pre-round-6 file FAILs (41.4 / 14.7 / 64.3 mm²); this release PASSes (0.0 / 0.0 / 3.1 mm²).

## Verified / not verified
- **Verified:**
  - Both 3MFs reopen and decode: 1,016,750 triangles, watertight, consistent winding, one body, 76.4 × 79.7 × 220 mm. Every decoded label matches the arrays.
  - 20 colour islands; the smallest is 0.52 mm².
  - `layer_colors.py` at 0.08 and 0.2 mm: no band over 4 colours, and no band with both orange and white, so the 120 mm swap is clean.
  - Hero, face close-up, front previews and the 12-view turnaround were reviewed by eye (face, glasses, both hands, glass, back).
- **Approval gate: CANNOT_JUDGE**, the same as v1 (6.7 % ambiguous). The judge photo still has the photo's colours (orange skin, brownish hair, clear glass) rather than the owner's choices. It must be recoloured to the decisions before the gate can PASS or FAIL this job (`jobs/man-with-drink/README.md`).
- **Not verified:** Snapmaker Orca slice, G-code, physical print.
