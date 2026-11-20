# Man with drink · 220 mm front-view fit study

The comparison shows the approved portrait, the original four-head paint in a straight-on view, and an orthographic front render decoded from the exported GLB. The reshaped front silhouette IoU against the extracted portrait mask rose from 0.85675 to 0.97489 at 712 × 1600. The profile fit used that same portrait, so this measures fit to the supplied view rather than independent validation.

The GLB projects the approved image onto visible facets; 363,252 facets use the image. The rest use the original material colors. Lighting and transparent-glass detail in the front texture come from the photograph. The real tumbler remains an opaque mesh, and textures can transition abruptly when viewed from the side. The lower hand and shoes still show silhouette differences.

The U1 study contains the reshaped mesh with the original tool assignments. The photo texture is available only in the GLB. Reopening the 3MF confirmed the triangle and paint records were retained, a watertight consistently oriented volume, and 220 mm height. In the upright study the orange top is 96.863 mm and white begins at 151.725 mm. No slice, support check or print test has been made. The normal four-head front evaluation on the reshaped finish gave CANNOT_JUDGE (6.7% ambiguous reference pixels); this is a working file for inspection.

## Reproduce

At repo root, create /dev/shm/drinkcheck and /dev/shm/match. Place the original Drive project (SHA-256 c23c5cdfa4353d72304c884c5fe4cab0fb83dd8b513b233bffef9aa26aaedc99) at /dev/shm/incoming.3mf. Copy these Python scripts to /dev/shm/match and use the figurine venv. Run check.py, fit.py, texture.py, and project.py in that order, keeping the repository root as the working directory. The fit uses monotonic vertical landmarks and row-wise horizontal landmarks and outline extents. The depth axis is preserved. The renderer reopens the GLB and samples its exported material image and UVs.
