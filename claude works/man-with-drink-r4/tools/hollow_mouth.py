"""Owner (2026-11-20, circled screenshot): "just open hollow that part" = the band from the upper teeth down to the
front of the lower lip. cut_mouth.py's 2.5 mm DROP did that with a straight-sided trapezoid and a flat floor that
faced the light, so it read as a skin box. Here:
  * outline: TOP = upper-teeth bottom edge (as cut_mouth), BOTTOM = lower-lip gap edge minus DROP*(1-u^2)^1.5,
    a rounded smile-shaped oval (u = -1..1 corner to corner), both as smooth splines (no kinks)
  * depth: DEPTH mm behind a quadratic fitted to the front-most surface (smooth back wall, no copied teeth)
  * floor: level until just inside the face, then falls FLOOR mm toward the back wall, so from the front you look
    into a hollow and not onto a shelf. The ceiling (under the teeth) stays level.
Cut faces are labelled CUT_LABEL (default 0 = skin: owner rule, never black in a mouth; pink rejected).
usage: hollow_mouth.py in.npz out.npz [depth=6] [drop=3.0] [floor=2.5] [inset=0.06]"""
import sys, numpy as np, trimesh
from scipy.spatial import cKDTree
from scipy.interpolate import CubicSpline
src, dst = sys.argv[1], sys.argv[2]
DEPTH, DROP, FLOOR, INSET = [float(a) for a in (sys.argv[3:7] + ['6', '3.0', '2.5', '0.06'][len(sys.argv[3:7]):])]
CUT_LABEL = 0
z = np.load(src); V, F, L = z['v'], z['f'], z['l'].astype(int)
m = trimesh.Trimesh(V, F, process=False)
TOP = np.array([(-11,155.75),(-8.5,155.25),(-5,155.2),(0,155.35),(3.33,155.6),(6,156.0),(8.17,156.9),(10.33,158.0)])
BOT = np.array([(-11,155.75),(-8.5,154.3),(-5,154.05),(0,154.15),(3.33,154.55),(6,155.15),(8.5,156.4),(10.33,158.0)])
ts, bs = CubicSpline(TOP[:,0], TOP[:,1]), CubicSpline(BOT[:,0], BOT[:,1])
XA, XB = TOP[0,0], TOP[-1,0]
def zt(x): return ts(x) - INSET
def zb(x):
    u = np.clip((2*x - XA - XB) / (XB - XA), -1, 1)
    return bs(x) - DROP * (1 - u*u) ** 1.5 + INSET
xs = np.linspace(XA, XB, 4000); ok = zt(xs) - zb(xs) > 0.15; x0, x1 = xs[ok].min(), xs[ok].max()
N, K = 320, 9; X = np.linspace(x0, x1, N)
Z = np.array([np.linspace(zb(x), zt(x), K) for x in X])
orig = np.c_[np.repeat(X, K), np.full(N*K, -80.0), Z.ravel()]
loc, ri, _ = m.ray.intersects_location(orig, np.tile([0, 1., 0], (N*K, 1)), multiple_hits=False)
yf = np.full(N*K, np.nan); yf[ri] = loc[:, 1]; yf = yf.reshape(N, K)
assert np.isfinite(yf).all(), 'a cutter ray missed the face'
# Smooth along x (per-column values made ridges and pockets in the floor and back wall).
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
sm = lambda a: gaussian_filter1d(maximum_filter1d(a, 25, mode='nearest'), 10, mode='nearest')
qc = np.polyfit(X, yf.min(1), 2)
Y1c = sm(yf.max(1)) + 0.6                                                         # just inside the face: floor still level
YBc = np.maximum(np.polyval(qc, X) + DEPTH, Y1c + 2.5)
YB = np.repeat(YBc[:, None], K, axis=1); Y1 = np.repeat(Y1c[:, None], K, axis=1)
fall = FLOOR * (1 - np.arange(K) / (K - 1))                                      # bottom row falls most, ceiling not at all
LAY = [(np.full((N, K), -80.0), Z), (Y1, Z), (YB, Z - fall[None, :])]
vid = lambda i, k, s: (s*N + i)*K + k
P = np.zeros((3*N*K, 3))
for s, (Yl, Zl) in enumerate(LAY):
    for i in range(N):
        for k in range(K):
            P[vid(i, k, s)] = (X[i], Yl[i, k], Zl[i, k])
T = []
for i in range(N-1):                                    # front (s=0) and back (s=2) faces
    for k in range(K-1):
        for s in (0, 2):
            a, b, c, d = vid(i, k, s), vid(i+1, k, s), vid(i+1, k+1, s), vid(i, k+1, s); T += [[a, b, c], [a, c, d]]
for s in (0, 1):                                        # bottom/top walls and end caps between layers
    for i in range(N-1):
        for k in (0, K-1):
            a, b, c, d = vid(i, k, s), vid(i+1, k, s), vid(i+1, k, s+1), vid(i, k, s+1); T += [[a, b, c], [a, c, d]]
    for i in (0, N-1):
        for k in range(K-1):
            a, b, c, d = vid(i, k, s), vid(i, k+1, s), vid(i, k+1, s+1), vid(i, k, s+1); T += [[a, b, c], [a, c, d]]
cut = trimesh.Trimesh(P, np.array(T), process=True); cut.fix_normals()
print('cutter watertight', cut.is_watertight, 'volume', cut.is_volume, '%.1f mm3' % cut.volume, '| x %.2f..%.2f' % (x0, x1),
      '| centre opening z %.2f..%.2f' % (zb(0.0), zt(0.0)))
assert cut.is_volume
res = trimesh.boolean.difference([m, cut], engine='manifold')
print('result faces', len(res.faces), 'watertight', res.is_watertight, 'volume', res.is_volume, 'bodies', res.body_count,
      'removed %.1f mm3' % (m.volume - res.volume))
assert res.is_watertight and res.is_volume and res.body_count == 1
rc = res.triangles_center
lab = L[cKDTree(m.triangles_center).query(rc)[1]]
cand = np.flatnonzero(cKDTree(cut.triangles_center).query(rc)[0] < 1.0)
on_cut = np.zeros(len(rc), bool)
if len(cand):
    _, dist, _ = trimesh.proximity.closest_point(cut, rc[cand]); on_cut[cand[dist < 1e-3]] = True
lab[on_cut] = CUT_LABEL
inside = (rc[:,0] > x0) & (rc[:,0] < x1) & (rc[:,2] > zb(rc[:,0]) - FLOOR - .05) & (rc[:,2] < zt(rc[:,0]) - .02) & (rc[:,1] > -40) & (rc[:,1] < -15)
stray = inside & ~on_cut & (lab != 3) & (lab != CUT_LABEL); lab[stray] = CUT_LABEL     # never black/pink specks in the mouth
print('cut faces', int(on_cut.sum()), '| stray non-skin specks inside ->', int(stray.sum()))
lab[lab == 5] = 0; print('pink anywhere -> skin (no pink on this model)')
np.savez(dst, v=res.vertices, f=res.faces.astype('i4'), l=lab.astype('u1'))
