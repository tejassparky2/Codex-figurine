# Deepak "Coffee Master" display base (Claude)

The pedestal only, as in `reference/approved-render.jpg` (sha256 `27c71105…`). The figure, sack and espresso machine aren't included. The base prints separately, and the figure is glued on (PLAYBOOK §1, Bases).

## Files (`out/`)
| File | Use |
|---|---|
| `Deepak-base-finish.3mf` | **Print this.** A single watertight mesh with per-triangle Orca paint: slot 1 base Tan, slot 2 plate Gold, slot 3 lettering Dark chocolate. Open it in Snapmaker Orca at 100 % |
| `Deepak-base.blend` | Blender 4.0 scene: the unioned print mesh, the hidden source parts, materials, camera and lights |
| `Deepak-base-{body,plate,text}.stl` | The parts before the union, if you'd rather assign filaments per part |
| `Deepak-base-hero.png`, `Deepak-base-plate.png` | Cycles renders |
| `Deepak-base-front.png`, `-front-detail.png` | Previews decoded from the exported 3MF (`coloring/front_preview.py`) |
| `compare-reference.png` | Approved render (top) vs this base (bottom) |
| `layer-colors-*.csv` | `scripts/layer_colors.py` at 0.08 and 0.2 mm |

## Design (all parametric in `tools/make_base.py`)
- **Size:** 120 mm diameter, 30.5 mm tall. In the approved render the base is about 0.89× the figure's height, so this suits a figure of about 135–150 mm. Change it with `--diameter/--height`.
- **Shape:** two tiers, as in the render.
  - A **plinth** 120 mm across and 10 mm tall, with a rounded 1.5 mm ledge and a 0.8 mm cove into the upper tier.
  - An **upper tier** 114 mm across.
  - A 0.8 mm deep **groove** under a 6.1 mm **lid** with a rounded 2 mm edge.
  - A 0.8 mm chamfered foot against elephant's foot.
  - A flat top (9,500 mm²) for gluing the figure.
- **Nameplate:**
  - A 57.6 × 12.1 mm arc, curved to the 57 mm tier radius. It stands 1.2 mm proud, with rounded front edges, and fills the upper tier with 0.45 mm clearance, as in the render.
  - Two Ø2.2 mm screw domes.
  - Lettering raised 0.8 mm and sunk 0.3 mm into the plate:
    - "Deepak" in DejaVu Serif Bold, 5.2 mm tall;
    - "COFFEE MASTER" in DejaVu Sans Bold, 2.9 mm tall (strokes about 0.5 mm).
- **Colours:** from the stock list, matched by sampling the approved render at grid-picked points.
  - **Base:** the render's base has lightness about 0.33–0.39 at hue ≈ 19°. Corrected for its lighting (its gold reads at 0.86× the filament's lightness), that is nearest **Tan #976E52**. Use `--colors '#4C2C21,…'` for a darker Dark chocolate base.
  - **Plate:** Gold #EFC13A.
  - **Lettering:** Dark chocolate #4C2C21 (the render's lettering measures hue 25°, lightness 0.23).

## Rebuild
    cd tools
    blender -b --factory-startup -P make_base.py -- --out ../out [--diameter 120 --height 30.5 --name Deepak --title "COFFEE MASTER"]
    blender -b ../out/Deepak-base.blend -P render_base.py -- --out ../out
Blender 4.0.2 from apt runs headless in the cloud container. The build takes about 10 s; the renders about 2 min on the CPU.

## Printing (Snapmaker U1)
- Print upright with the foot on the bed and no supports. The plate's lower edge is a 1.2 mm step and the letters stand 0.8 mm proud, both small overhangs; the groove's upper face is 45°.
- Load Tan, Gold and Dark chocolate in three heads. `layer_colors.py` finds at most 3 colours per band, so there are no swaps.
- Gold appears only on the plate (11.2–23.3 mm), never on the bed, so its poor bed adhesion doesn't matter here.
- A 0.2 mm nozzle is recommended for the 2.9 mm "COFFEE MASTER" letters. With 0.4 mm they print, but soft.

## Verified / not verified
- **Verified:**
  - The 3MF reopens and decodes. It is one body, watertight, with consistent winding; every edge is shared by 2 triangles. 34,920 triangles; 120 × 120 × 30.5 mm.
  - Paint per slot: base 19,170 faces, plate 10,918, lettering 4,832.
  - Layer colours at 0.08 and 0.2 mm.
  - Decoded front previews, and a side-by-side check against the approved render by eye.
- **Not verified:**
  - Snapmaker Orca import and slice (Orca isn't installed here), G-code, physical print.
  - The approval gate wasn't run: the approved image shows the figure on the base and is cropped at the base's bottom, so the base alone can't be registered to it. The comparison was by eye (`compare-reference.png`).
  - The base's true height below the crop is an estimate.
