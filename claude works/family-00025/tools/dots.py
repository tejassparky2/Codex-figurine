"""Flat dots (red bindi + red forehead dot, black kaala tika on the cheek) at the positions of the removed bumps (customer: "paint it like kaala tika, keep surface
smooth"). Source positions from figurines remake/bump_report.txt, mapped through prep.py's cut (z-0.5)*150/149.5.
The art shows ONE cheek dot (baby's left cheek = image right); Tripo also sculpted one on the other cheek: not painted.
Each dot = faces within R of the point, on the front skin. reads materials.npy, writes materials_d.npy"""
import numpy as np, trimesh
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False); c = m.triangles_center
mat = np.load('materials.npy').astype(int).copy()
s = 150.0 / 149.5
# owner 2026-11-21: "black dot only on baby cheek, red dot on mam and baby forehead"  (label 5 = red, 1 = black)
DOTS = [('mother bindi', (19.77, -12.85, 120.23), 0.62, 5), ('baby forehead dot', (38.25, -41.52, 80.20), 0.55, 5),
        ('baby cheek dot (art side)', (49.56, -40.68, 67.44), 0.48, 1)]
for name, p, R, col in DOTS:
    q = np.array([p[0]*s, p[1]*s, (p[2]-0.5)*s])
    q = m.nearest.on_surface(q[None])[0][0]                     # project onto the skin surface
    sel = (np.linalg.norm(c - q, axis=1) < R) & np.isin(mat, [0, 1])
    mat[sel] = col; print('%-26s %-5s at %s r %.2f mm: %d faces, %.2f mm2' % (name, 'red' if col == 5 else 'black', np.round(q, 2), R, sel.sum(), m.area_faces[sel].sum()))
np.save('materials_d.npy', mat.astype('u1'))
