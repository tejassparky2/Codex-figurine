"""Owner (r4): "just as art, the inner lower pink". In the art, under the upper teeth there is a thin dark gap, then the
top of the lower lip is pink. Paint a band on the FRONT of the lower lip, from the mouth opening's bottom edge down
BAND mm (tapering to 0 at the corners), pink (label 5). The opening's bottom edge per x is the lowest pink face of the
cut. usage: lower_lip_pink.py in.npz out.npz [band_mm]"""
import sys, numpy as np, trimesh
src, dst = sys.argv[1], sys.argv[2]; BAND = float(sys.argv[3]) if len(sys.argv) > 3 else 1.2
z = np.load(src); V, F, L = z['v'], z['f'], z['l'].astype(int).copy()
m = trimesh.Trimesh(V, F, process=False); c = m.triangles_center; n = m.face_normals
pk = (L == 5) & (c[:, 2] > 145) & (c[:, 2] < 170)
xs = np.arange(np.floor(c[pk, 0].min()), np.ceil(c[pk, 0].max()) + 0.01, 0.25)
edge = np.array([c[pk & (np.abs(c[:, 0] - x) < 0.2), 2].min() if (pk & (np.abs(c[:, 0] - x) < 0.2)).any() else np.nan for x in xs])
ok = np.isfinite(edge); xs, edge = xs[ok], edge[ok]
edge = np.convolve(np.pad(edge, 3, mode='edge'), np.ones(7) / 7, mode='valid')
x0, x1 = xs.min(), xs.max(); taper = np.clip(np.minimum(xs - x0, x1 - xs) / 2.5, 0, 1)
zb = np.interp(c[:, 0], xs, edge); h = BAND * np.interp(c[:, 0], xs, taper)
band = (L == 0) & (c[:, 0] > x0) & (c[:, 0] < x1) & (c[:, 2] < zb + 0.15) & (c[:, 2] > zb - h) & (n[:, 1] < -0.2) & (c[:, 1] < -18)
L[band] = 5
print('lower-lip pink band %.1f mm: %d faces, x %.1f..%.1f' % (BAND, int(band.sum()), x0, x1))
np.savez(dst, v=V, f=F, l=L.astype('u1'))
