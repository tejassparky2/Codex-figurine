# Deepak "Coffee Master" display base with espresso machine and coffee sack (Claude)

Built from `reference/approved-render.jpg` (sha256 `27c71105…`). The base, espresso machine and coffee sack print together as one piece. The figurine prints separately and is glued onto the clear strip in the middle of the top (owner, 2026-11-18).

## Files (`out/`)
| File | Use |
|---|---|
| `Deepak-base-U1.3mf` | **Print this on the Snapmaker U1.** Four head IDs plus one pause (below) |
| `Deepak-base-finish.3mf` | Finish guide: the same mesh, one slot per final colour (6 colours) |
| `Deepak-base.blend` | Blender 4.0 scene: the unioned print mesh, the hidden source parts, materials, camera and lights |
| `Deepak-base-{body,plate,text}.stl`, `Deepak-espresso-machine.stl`, `Deepak-coffee-sack.stl` | Parts before the union, for per-part filament assignment |
| `Deepak-base-hero.png`, `Deepak-machine.png`, `Deepak-sack.png`, `Deepak-base-plate.png` | Cycles renders |
| `Deepak-base-front.png`, `-front-detail.png` | Previews decoded from the exported finish 3MF |
| `compare-reference.png` | Approved render (top) vs this model (bottom) |
| `layer-colors-*.csv` | `scripts/layer_colors.py` at 0.08 and 0.2 mm |

## Colours and the U1 head plan (one pause)
| Head | Start (base, 0–30.4 mm) | After the pause at **30.4 mm** (machine and sack) |
|---|---|---|
| H1 | Dark chocolate #4C2C21: base and lettering | **Apricot #E6BAA8**: burlap sack |
| H2 | Gold #EFC13A: nameplate and screws | **Pure White #F1ECE1**: cup |
| H3 | Black #0E0E10 (idle) | Black: machine body, knobs, fins, handle, coffee beans |
| H4 | Simply Silver #8C979D (idle) | Silver: control panel, bay back, group head, portafilter, drip tray |

In Snapmaker Orca, add a pause **before the first layer that starts at or above 30.4 mm**. The base top is exactly 30.4 mm (380 layers of 0.08 mm, or 152 of 0.2 mm), so the swap falls on a layer boundary. At the pause, reload H1 with Apricot and H2 with White; the U1 lets you reload any head and purges it automatically. Check the layers just below and above 30.4 mm in the slicer preview.

## Design (parametric: `tools/make_base.py` + `tools/props.py`)
- **Base:** two tiers, 120 mm across and 30.4 mm tall.
  - Plinth 120 mm across and 10 mm tall, with a rounded ledge and a cove into the upper tier.
  - Upper tier 114 mm across, with a groove under a 6.1 mm lid with a rounded edge.
  - A 0.8 mm chamfered foot.
- **Nameplate:** 57.6 × 12.0 mm, curved to the tier, 1.2 mm proud, two screw domes.
  - "Deepak" in DejaVu Serif Bold, 5.2 mm tall.
  - "COFFEE MASTER" in DejaVu Sans Bold, 2.9 mm tall.
  - Both raised 0.8 mm.
- **Espresso machine:** 28 × 22 × 40 mm (with fins 42.6 mm), centre at (33, 8) mm. It has:
  - seven cup-warmer fins and a silver control panel with three Ø5.4 mm knobs;
  - a side knob;
  - an open bay with a silver back panel, group head, portafilter and black handle;
  - a silver drip tray with grate ribs, and a white cup with a handle.
- **Coffee sack:** 1.15 × scale, about 29 mm wide and 25.7 mm tall, centre at (−36, 3) mm. It has:
  - a burlap diamond weave (1.6 mm pitch, 0.35 mm deep);
  - a rolled rim as part of the same surface;
  - a heaped dome with 60 black coffee beans.
- **Figurine space:** the props reach at most 51.2 mm from the centre (the top edge is at 57 mm). The clear strip for the figurine's feet runs from x = −21 to +19 mm, front to back. Check the fit before gluing; move the props with `--machine-at x,y` and `--sack-at x,y`.

## Printability choices
- Print upright on the foot. Supports should be unnecessary; confirm in the slicer.
- The portafilter handle rises at about 38° out of the bay. That's a deliberate difference from the render, where it sticks out flat, so it doesn't need support.
- The group head and portafilter are frustums tied into the bay ceiling and back wall. The bay ceiling is a 22 mm bridge.
- Knobs and plate protrude ≤ 2.4 mm from vertical faces.
- The bottoms of the machine and sack are sunk 0.6–0.7 mm into the base, with no vertex ring on the top plane.
- Small features: lettering strokes are about 0.5 mm and the weave grooves 0.27 mm wide. **A 0.2 mm nozzle is recommended.** With 0.4 mm the weave will be faint.

## Rebuild
    cd tools
    blender -b --factory-startup -P make_base.py -- --out ../out [--base-color '#976E52'] [--no-props]
    blender -b ../out/Deepak-base.blend -P render_base.py -- --out ../out
The build takes about 70 s and the renders about 3 min on the CPU, using Blender 4.0.2 from apt.

## Verified / not verified
- **Verified:**
  - Both 3MFs reopen and decode with the same mesh: one body, watertight, consistent winding, every edge shared by 2 triangles. 156,364 triangles; 120 × 120 × 73 mm; 359 cm³.
  - Exact-union sliver shells (7, total 0.32 mm²) are removed automatically, and the build fails if a real part detaches.
  - From the files themselves: each head prints exactly one colour below and above the pause, matching the table.
  - `layer_colors.py` at 0.08 and 0.2 mm: at most 4 colours per band, none over 4.
  - Decoded front previews; compared with the approved render by eye.
- **Not verified:**
  - Snapmaker Orca import, the pause placement and slicing (Orca isn't installed here), G-code, physical print.
  - The approval gate wasn't run: in the approved image the figurine covers the base and the image is cropped at the bottom.
  - The base's true height below the crop is an estimate.
