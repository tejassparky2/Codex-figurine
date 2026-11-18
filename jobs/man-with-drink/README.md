# Man with drink: 220 mm, Snapmaker U1, 4 heads plus one manual swap

## Inputs (sha256 in inputs.sha256)
- `inputs-raw/man-with-drink.glb`: Tripo, 1,866,896 triangles, 4096² texture. It was one connected piece, not closed: 1 non-manifold edge and inconsistent winding.
- `reference/photo-front.jpg`: the front photo. The back and sides come from Tripo and have no photo reference.

## Decisions
- Height is 220 mm. The figure measures 76.8 × 79.6 × 220 mm and stands on its own soles with no base.
- Filaments come from the owner's stock list (Numakers PLA+, 2026-11-18):
  - Apricot #E6BAA8 for skin (preview colour #DEA485)
  - Black #0E0E10 for shirt, trousers, shoes, brows, irises and lash lines
  - Simply Silver #8C979D for hair, glasses frames and the tumbler
  - Orange #F9A800 for the whisky
  - Pure White #F1ECE1 for teeth, eye whites and catchlights
- Departures from the photo and texture:
  - The frames are silver, as in the photo; the texture has them brass.
  - The texture skin is too orange, so skin is Apricot instead.
  - The irises are black, not brown. There is no brown head left, and black matches the brows.
- Revision 2, per user review:
  - Eyes are realistic: white, black iris and a 0.40 mm lash line along the lid. There is no catchlight and no eyeliner wing.
  - The mouth is white teeth only; the lips and the gap are skin, with no black.
  - Brows are solid, hole-free shapes with smoothed edges.
  - The glasses frames are found by geometry and locked silver: rims, double top bar, bridge, nose pads and temple arms.
  - Colour boundaries are snapped to sculpted creases.
- The tumbler is silver: the user asked for a clear glass, but clear isn't stocked. The drink is orange on the outer and inner wall from the base band (91.0 mm) up to the liquid line (97.4 mm), and on the inner floor.

## Pipeline (tools/, run in order in this folder; `P=<venv>/bin/python tools/run_all.sh` does all of it)
1. `make_printable.py <glb> 220 1000000`: welds the mesh, repairs it with PyMeshFix, applies quadric decimation to 1.0M triangles, and places it Z-up, front toward -Y, feet at z=0. The result is watertight, has consistent winding, is a valid volume, and is 1 body.
2. `split_planes.py 97.4 91.0`: cuts the mesh exactly at the liquid line and the base band so those paint edges are straight. The mesh stays watertight; the result has 1,008,768 triangles.
3. `sample_texture.py <glb>`: takes the per-face texture colour as the median of 4 points. Each point is projected onto the nearest source triangle that agrees in normal. Median distance is 0.04 mm, maximum 0.39 mm.
4. `label.py 5`: the toolkit's crease-aware alpha-expansion, with several texture prototypes per material and region limits. Orange is allowed only in the glass, white only on the front of the head, silver only on the head and glass.
5. `views.py`: ten triangle-ID cameras. `facecam.py`: a 40 px/mm front face camera with the glasses frames hidden.
6. `framemask.py` (glasses colour lock):
   - Each triangle around the glasses gets a 9-ray cone of inward rays (embree), and the shortest exit distance is kept.
   - The 0.8 mm frame wire exits within 1.25 mm even where it is half-buried in the nose. Skin over the skull does not.
   - The largest connected thin network (29,673 faces) is the frame. `finalize.py` forces it to silver as the very last step.
   - Then `facecam.py`, the 40 px/mm face camera with the frame hidden.
7. `detail.py`:
   - Brows are solid smoothed masks and teeth are a smoothed mask.
   - The eyes are traced: almond opening, iris and 0.40 mm lash line, measured in mm on renders/eye*-grid.png.
   - Then the whisky and glass rules: hollow tumbler, axis at (-0.21, -29.55), wall radius 6.7 mm.
8. `leakfix.py 6 12`, then `part_lock.py leak.npy leak.npy 14 42 -12 26 44 80 0 1 7 10 10 3.0`. The part lock keeps his left thumb off the trouser leg.: re-solves a 6-ring band around the skin/black/silver boundaries. It uses a weak texture term and a strong crease term, so edges land on the sculpted folds. A second pass does the same for the frame edge using thickness.
9. `finalize.py`:
   - Smooths the skin/black sawtooth below the head.
   - Turns enclosed skin specks on the head silver.
   - Merges islands under 0.16 mm². The smallest island left is 0.207 mm².
10. `export.py`: writes the Orca `paint_color` 3MFs, then re-opens them and decodes every triangle against the arrays.
11. `render_outputs.py`: a 12-view unlit turnaround with an exact palette check on every pixel, the lit hero, and straight-front previews of the full figure and the face. All are decoded from the exported guide.

## Physical schedule
| Head | Start | After the pause at 120.00 mm |
|---|---|---|
| T1 | Apricot (skin) | unchanged |
| T2 | Black | unchanged |
| T3 | Simply Silver | unchanged |
| T4 | Orange (whisky, used 89.2–97.6 mm) | **Pure White** (teeth and eyes, used 147.7–172.6 mm) |

`scripts/layer_colors.py` on the finish guide, at both 0.08 mm and 0.2 mm bands, finds no band with more than 4 colours and no band with both orange and white.

## Verified / not verified
- Verified:
  - Both 3MFs reopen and decode to exactly the intended labels.
  - Both are watertight, have consistent winding, and every edge is used by exactly 2 triangles.
  - The model is 220 mm tall and centred on the 270 × 270 bed.
  - Every turnaround pixel is a palette colour.
- Not verified: no slicer has opened these files. There is no Snapmaker Orca slice, no support check, no G-code, and no physical print.
- Expect to need supports: the glasses frames (wire about 0.73 mm) stand clear of the face, and the outstretched hand and glass overhang.
