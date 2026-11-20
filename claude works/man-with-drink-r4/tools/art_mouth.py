"""Owner 2026-11-20: "mouth/lips not matching photo". Fit the mouth to the approved art's traced lines
(tools/mouth_compare.py TRACE, art px -> model mm) on the final-frame, uncut mesh:
  1. measure the model's visible teeth band (front rays): top/bottom per x, left/right ends
  2. 2-D thin-plate-spline warp in the front plane (x,z): model teeth top -> art mouth top (blue), model teeth bottom ->
     art teeth bottom (green), mouth corners -> art corners; a ring around the mouth (nose base, cheeks, chin) is
     fixed. Depth (y) untouched; only front-facing material moves (y gate), fading out radially.
  3. cut the art's crescent: from the teeth bottom (green; blue beyond the tooth row) down to the art's lower-lip
     line (red), to points at both corners; DEPTH behind the face, floor falling FLOOR toward the back. Skin inside.
usage: art_mouth.py in.npz out.npz [depth=6] [floor=2.0] [warp=1.0]"""
import sys, numpy as np, trimesh
from scipy.interpolate import RBFInterpolator, CubicSpline
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from scipy.spatial import cKDTree
src, dst = sys.argv[1], sys.argv[2]
DEPTH = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
FLOOR = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
WARP = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
s = float(np.load('views/match_scale.npy')[0]); PEYE, MEYE, S, XCP, XCM = 415.0, 175.2, 137.0 / 19.2, 344.0, -2.08
def mm(pts): p = np.asarray(pts, float); return np.c_[((p[:, 0] - XCP) / S + XCM) * s, (MEYE - (p[:, 1] - PEYE) / S) * s]
BLUE = mm([(280,544),(290,546),(300,547),(320,547),(340,546),(360,545),(380,543),(390,541),(400,538),(410,534),(420,528),(428,525)])
GREEN = mm([(305,550),(320,554),(340,555),(360,554),(380,551),(390,548),(400,545),(408,540)])
RED = mm([(280,544),(290,549),(300,553),(310,556),(320,558),(340,560),(360,559),(380,556),(400,551),(410,546),(420,535),(428,525)])
blue, green, red = (CubicSpline(c[:, 0], c[:, 1]) for c in (BLUE, GREEN, RED))
LC, RC = BLUE[0], BLUE[-1]                                   # art corners (mm)

z = np.load(src); V, F, L = z['v'].copy(), z['f'], z['l'].astype(int).copy()
L[L == 5] = 0                                                # no pink anywhere on this model
m = trimesh.Trimesh(V, F, process=False)
# 1. model teeth band seen from the front
xs = np.arange(-16, 14, 0.1); zs = np.arange(150, 168, 0.05)
gx, gz = np.meshgrid(xs, zs, indexing='ij'); org = np.c_[gx.ravel(), np.full(gx.size, -80.0), gz.ravel()]
loc, ri, ti = m.ray.intersects_location(org, np.tile([0, 1., 0], (len(org), 1)), multiple_hits=False)
lab = np.full(len(org), -1); lab[ri] = L[ti]; lab = lab.reshape(gx.shape)
tt, tb = np.full(len(xs), np.nan), np.full(len(xs), np.nan)
for i in range(len(xs)):
    w = np.flatnonzero(lab[i] == 3)
    if len(w) > 3: tt[i], tb[i] = zs[w.max()], zs[w.min()]
ok = np.isfinite(tt); il, ir = np.flatnonzero(ok)[[0, -1]]
xl, xr = xs[il], xs[ir]
print('model teeth x %.2f..%.2f | art teeth x %.2f..%.2f, art corners x %.2f / %.2f' % (xl, xr, GREEN[0, 0], GREEN[-1, 0], LC[0], RC[0]))
tts = gaussian_filter1d(np.interp(xs, xs[ok], tt[ok]), 4); tbs = gaussian_filter1d(np.interp(xs, xs[ok], tb[ok]), 4)
# 2. control points: model -> art
ax0, ax1 = GREEN[0, 0], GREEN[-1, 0]                          # art tooth-row ends
src_p, dst_p = [], []
for u in np.linspace(0.04, 0.96, 13):
    xm = xl + u * (xr - xl); xa = ax0 + u * (ax1 - ax0)
    src_p += [(xm, np.interp(xm, xs, tts)), (xm, np.interp(xm, xs, tbs))]
    dst_p += [(xa, float(blue(xa))), (xa, float(green(xa)))]
# corners: the model's mouth slit ends ~1.5 mm beyond its tooth row at the tooth-top height
src_p += [(xl - 1.5, np.interp(xl, xs, tts)), (xr + 1.5, np.interp(xr, xs, tts))]; dst_p += [tuple(LC), tuple(RC)]
src_p, dst_p = np.array(src_p), np.array(dst_p)
cx, cz = (LC[0] + RC[0]) / 2, float(np.mean(src_p[:, 1]))
AX, AZU, AZD = 21.0, 7.0, 9.0                                # fixed ring: cheeks, nose base, chin
ring = np.array([(cx + AX * np.cos(t), cz + (AZU if np.sin(t) > 0 else AZD) * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 40, endpoint=False)])
P = np.r_[src_p, ring]; D = np.r_[dst_p - src_p, np.zeros_like(ring)] * WARP
tps = RBFInterpolator(P, D, kernel='thin_plate_spline', smoothing=0.5)
print('control displacement mm: max %.2f, mean %.2f' % (np.linalg.norm(D, axis=1).max(), np.linalg.norm(D[:len(src_p)], axis=1).mean()))
x, y, zz = V.T
r = np.sqrt(((x - cx) / AX) ** 2 + ((zz - cz) / np.where(zz > cz, AZU, AZD)) ** 2)
def sm(q): q = np.clip(q, 0, 1); return q * q * (3 - 2 * q)
w = sm((1.15 - r) / 0.3) * sm((-y - 6) / 8)                    # inside the ring and on the face
sel = w > 0
d = tps(np.c_[x[sel], zz[sel]])
V[sel, 0] += w[sel] * d[:, 0]; V[sel, 2] += w[sel] * d[:, 1]
# fold check of the 2-D map on a grid
gx2, gz2 = np.meshgrid(np.arange(cx - AX, cx + AX, .25), np.arange(cz - AZD, cz + AZU, .25), indexing='ij')
q = np.c_[gx2.ravel(), gz2.ravel()]; rr = np.sqrt(((q[:, 0] - cx) / AX) ** 2 + ((q[:, 1] - cz) / np.where(q[:, 1] > cz, AZU, AZD)) ** 2)
mp = q + sm((1.15 - rr) / 0.3)[:, None] * tps(q); mp = mp.reshape(gx2.shape + (2,))
J = (np.diff(mp[:, :, 0], axis=0)[:, :-1] * np.diff(mp[:, :, 1], axis=1)[:-1, :] - np.diff(mp[:, :, 1], axis=0)[:, :-1] * np.diff(mp[:, :, 0], axis=1)[:-1, :]) / .0625
print('front-plane map Jacobian min %.2f (must stay > 0)' % J.min()); assert J.min() > 0.05
# hidden inner-lip surfaces at different depths can still cross (the y gate fades the warp): relax only those
# vertices (and two rings) back toward the original until there are 0 self-intersections
import pymeshlab
from scipy.sparse import coo_matrix
V0 = z['v']; Dv = V - V0
ii = F[:, [0, 1, 2, 1, 2, 0]].ravel(); jj = F[:, [1, 2, 0, 0, 1, 2]].ravel()
Adj = coo_matrix((np.ones(len(ii)), (ii, jj)), shape=(len(V), len(V))).tocsr()
for it in range(40):
    ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(V0 + Dv, F)); ms.compute_selection_by_self_intersections_per_face()
    bad_f = ms.current_mesh().face_selection_array()
    if it == 0 or not bad_f.any(): print('warp relax pass %d: self-intersecting faces %d' % (it, bad_f.sum()))
    if not bad_f.any(): break
    bad = np.zeros(len(V), bool); bad[np.unique(F[bad_f])] = True
    for _ in range(2): bad |= (Adj @ bad.astype(float)) > 0
    Dv[bad] *= 0.7
assert not bad_f.any()
V = V0 + Dv
m = trimesh.Trimesh(V, F, process=False)
# 3. crescent cutter (art lines, final frame)
def zt(xv):                                                    # top: teeth bottom (green) on the tooth row, blue beyond
    xv = np.asarray(xv, float); g = green(np.clip(xv, ax0, ax1)); b = blue(xv)
    bl = sm((xv - ax0 + 1.2) / 1.2) * sm((ax1 + 1.2 - xv) / 1.2)          # green on the row, blue 1.2 mm past it
    return bl * np.minimum(g, b) + (1 - bl) * b
def zb(xv): return red(np.asarray(xv, float))
x0, x1 = LC[0] + 0.15, RC[0] - 0.15
import os; N, K = int(os.environ.get("CUT_N", 300)), 9; X = np.linspace(x0, x1, N)
Z = np.array([np.linspace(zb(xx), max(zt(xx), zb(xx) + 0.05), K) for xx in X])
orig = np.c_[np.repeat(X, K), np.full(N * K, -80.0), Z.ravel()]
loc, ri, _ = m.ray.intersects_location(orig, np.tile([0, 1., 0], (N * K, 1)), multiple_hits=False)
yf = np.full(N * K, np.nan); yf[ri] = loc[:, 1]; yf = yf.reshape(N, K); assert np.isfinite(yf).all()
smx = lambda a: gaussian_filter1d(maximum_filter1d(a, 25, mode='nearest'), 10, mode='nearest')
Y1c = smx(yf.max(1)) + 0.6
YBc = np.maximum(np.polyval(np.polyfit(X, yf.min(1), 2), X) + DEPTH, Y1c + 2.5)
fall = FLOOR * (1 - np.arange(K) / (K - 1))
LAY = [(np.full((N, K), -80.0), Z), (np.repeat(Y1c[:, None], K, 1), Z), (np.repeat(YBc[:, None], K, 1), Z - fall[None, :])]
vid = lambda i, k, sl: (sl * N + i) * K + k
Pc = np.zeros((3 * N * K, 3))
for sl, (Yl, Zl) in enumerate(LAY):
    for i in range(N):
        for k in range(K): Pc[vid(i, k, sl)] = (X[i], Yl[i, k], Zl[i, k])
# Cutter = union of convex pieces, two per column pair (in front of the face: layers 0-1; behind it: layers 1-2).
# A single swept surface self-intersected where its front and back sections meet along the top wall.
pieces = []
for i in range(N - 1):
    for sl in (0, 1):
        pts = np.array([Pc[vid(ii, kk, ss)] for ii in (i, i + 1) for kk in (0, K - 1) for ss in (sl, sl + 1)])
        pieces.append(trimesh.convex.convex_hull(pts))
cut = trimesh.boolean.union(pieces, engine='manifold'); assert cut.is_volume
np.savez('views/art_cutter.npz', v=cut.vertices, f=cut.faces)
res = trimesh.boolean.difference([m, cut], engine='manifold')
print('cut: removed %.1f mm3 | watertight %s volume %s bodies %d | centre opening z %.2f..%.2f' % (
    m.volume - res.volume, res.is_watertight, res.is_volume, res.body_count, zb(cx), zt(cx)))
assert res.is_watertight and res.is_volume and res.body_count == 1
rc = res.triangles_center
lab2 = L[cKDTree(m.triangles_center).query(rc)[1]]
cand = np.flatnonzero(cKDTree(cut.triangles_center).query(rc)[0] < 1.0); on_cut = np.zeros(len(rc), bool)
if len(cand): _, dist, _ = trimesh.proximity.closest_point(cut, rc[cand]); on_cut[cand[dist < 1e-3]] = True
lab2[on_cut] = 0
inside = (rc[:, 0] > x0) & (rc[:, 0] < x1) & (rc[:, 2] > zb(rc[:, 0]) - FLOOR - .05) & (rc[:, 2] < zt(rc[:, 0]) - .02) & (rc[:, 1] > -40) & (rc[:, 1] < -15)
lab2[inside & (lab2 != 3)] = 0
lab2[lab2 == 5] = 0
np.savez(dst, v=res.vertices, f=res.faces.astype('i4'), l=lab2.astype('u1'))
print('saved', dst, len(res.faces), 'faces')
