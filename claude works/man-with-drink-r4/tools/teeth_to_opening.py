"""Owner (r4): "still it shows the teeth in skin colour". Between the bottom of the white upper teeth and the top
(ceiling) of the cut mouth opening, the lower edge of the sculpted upper teeth is still skin. Paint it white: per x,
front-facing skin faces with z between the opening's ceiling and the white teeth's bottom become white (label 3).
usage: teeth_to_opening.py in.npz out.npz"""
import sys, numpy as np, trimesh
src, dst = sys.argv[1], sys.argv[2]
z = np.load(src); V, F, L = z['v'], z['f'], z['l'].astype(int).copy()
m = trimesh.Trimesh(V, F, process=False); c = m.triangles_center; n = m.face_normals
box = (np.abs(c[:, 0] + 1) < 13) & (c[:, 2] > 150) & (c[:, 2] < 166) & (c[:, 1] < -18)
white = box & (L == 3)
ceil = box & (n[:, 2] < -0.9) & (c[:, 1] > -31) & (L == 0)              # flat downward faces: the cut's ceiling
xs = np.arange(-14, 12, 0.25); wb, cz = [], []
for x in xs:
    q = white & (np.abs(c[:, 0] - x) < 0.3); r = ceil & (np.abs(c[:, 0] - x) < 0.3)
    wb.append(c[q, 2].min() if q.any() else np.nan); cz.append(np.median(c[r, 2]) if r.sum() > 3 else np.nan)
wb, cz = np.array(wb), np.array(cz); ok = np.isfinite(wb) & np.isfinite(cz) & (wb > cz)
print('x columns with teeth above the opening: %d, gap median %.2f mm (max %.2f)' % (ok.sum(), np.median((wb - cz)[ok]), (wb - cz)[ok].max()))
WB = np.interp(c[:, 0], xs[ok], wb[ok]); CZ = np.interp(c[:, 0], xs[ok], cz[ok])
x0, x1 = xs[ok].min(), xs[ok].max()
strip = box & (L == 0) & (n[:, 1] < -0.3) & (c[:, 0] > x0) & (c[:, 0] < x1) & (c[:, 2] > CZ + 0.02) & (c[:, 2] < WB + 0.05)
L[strip] = 3
print('teeth strip skin -> white: %d faces, %.2f mm2' % (strip.sum(), m.area_faces[strip].sum()))
np.savez(dst, v=V, f=F, l=L.astype('u1'))
