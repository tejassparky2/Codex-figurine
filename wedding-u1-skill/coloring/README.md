# Reusable colouring tools

These are generic, model-independent tools proven on real models. Read `../PLAYBOOK.md` first.

Conventions:
- The mesh is `printable.npz` (`v` in mm, Z-up, front toward −Y, feet at z=0; `f` faces).
- Labels are one `uint8` per face, saved as `.npy`.
- Run the tools from the job folder with the venv from `../NEW-MODEL-PROMPT.md`, using `python -I`.

| Tool | What it does | Proven on |
|---|---|---|
| `make_printable.py <glb> <height_mm> <faces>` | Weld, repair with PyMeshFix, quadric decimation, place upright in mm. Asserts the result is watertight, has consistent winding and is one body. Writes `printable.npz`. | Man with drink |
| `split_planes.py z1 [z2 …]` | Cut every triangle crossing the given heights. Edge points are shared, so the mesh stays watertight. Gives straight paint lines. | Man with drink: liquid line and base band |
| `sample_texture.py <glb>` | Per-face texture colour: median of 4 samples, each projected onto the nearest source triangle with a compatible normal. Writes `face_rgb.npy`. | Man with drink: 0.04 mm median offset |
| `thin_network_lock.py mesh.npz x0 x1 y0 y1 z0 z1 max_mm min_faces out.npy [labels label out]` | Finds glasses frames, wire jewellery and straps by cone thickness. **Apply last.** | Man with drink: the glasses (1.25 mm, 300) |
| `part_lock.py in.npy out.npy x0 x1 y0 y1 z0 z1 thin_label thick_label thin_mm thick_mm [rings] [lam]` | Separates a thin part from the thick body it touches (hand on clothes) using thickness and a crease min-cut. Reads `printable.npz`. | Man with drink: thumb on trousers (7, 10, 10, 3.0) |
| `crease_snap.py mesh.npz in.npy out.npy [rings] [prior] [--protect m.npy] [--only a,b]` | Snaps boundaries onto sculpted creases without texture. | Man with drink |
| `contour_split.py mesh.npz labels.npy out.npz [--iter 0] [--t-iter 4] [--keep mask.npy] [--protect-folds DEG]` | Smooth paint edges cut through the triangles, instead of the per-triangle sawtooth. Watertight in and out, surface unchanged; regression checks are asserted. `--keep` leaves exact edges (plane splits) untouched. Run it **last**, after the locks. Ported from the local session's `maroon_refine.py`. | Man with drink: eyes, brows, teeth, frame and thumb (6.5 s on 1M faces) |
| `front_preview.py model.3mf out_prefix [--preview SLOT=#HEX] [--crop-z z0:z1]` | Lit straight-front previews decoded from the exported file. **Send with every revision.** | Man with drink |

Model-specific steps live with each job in `../../jobs/<model>/tools/`, kept exactly as run: broad labels with texture prototypes, eye tracing, the vessel/liquid rules and the export. Copy one as a template and replace the coordinates.
