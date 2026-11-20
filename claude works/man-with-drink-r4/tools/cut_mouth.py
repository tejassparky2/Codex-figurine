"""Owner (r4): "cut open that pink part". Boolean-subtract a cutter from the head: in front view the cutter is the
traced mouth gap (between the upper teeth's bottom edge TB and the lower-lip edge GB, inset INSET mm); in depth it
runs from in front of the face to DEPTH mm behind the front-most surface at each point. Cut faces are pink (label 5);
all other faces keep their label (nearest original face). manifold3d engine.
usage: cut_mouth.py in.npz out.npz depth_mm [inset_mm]"""
import sys, numpy as np, trimesh
from scipy.spatial import cKDTree
src, dst, depth = sys.argv[1], sys.argv[2], float(sys.argv[3]); inset = float(sys.argv[4]) if len(sys.argv) > 4 else 0.06
z = np.load(src); V, F, L = z['v'], z['f'], z['l'].astype(int)
m = trimesh.Trimesh(V, F, process=False)
TOP = np.array([(-11,155.75),(-8.5,155.25),(-5,155.2),(0,155.35),(3.33,155.6),(6,156.0),(8.17,156.9),(10.33,158.0)])
BOT = np.array([(-11,155.75),(-8.5,154.3),(-5,154.05),(0,154.15),(3.33,154.55),(6,155.15),(8.5,156.4),(10.33,158.0)])
DROP = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0      # owner 2026-11-20: "fully open" -> cut DROP mm lower into the lower lip
ENDS = np.interp(BOT[:,0], [-11, -8.5, 8.5, 10.33], [0, 1, 1, 0])     # full drop in the middle, tapering to the corners
BOTd = BOT.copy(); BOTd[:,1] -= DROP * ENDS
zt = lambda x: np.interp(x, TOP[:,0], TOP[:,1]) - inset; zb = lambda x: np.interp(x, BOTd[:,0], BOTd[:,1]) + inset
xs = np.linspace(-11, 10.33, 2000); ok = zt(xs) - zb(xs) > 0.15; x0, x1 = xs[ok].min(), xs[ok].max()
N, K = 160, 7; X = np.linspace(x0, x1, N)
Z = np.array([np.linspace(zb(x), zt(x), K) for x in X])                 # N x K
# front-most surface y at each grid point, then DEPTH behind it
orig = np.c_[np.repeat(X, K), np.full(N*K, -80.0), Z.ravel()]
loc, ri, _ = m.ray.intersects_location(orig, np.tile([0, 1., 0], (N*K, 1)), multiple_hits=False)
yf = np.full(N*K, np.nan); yf[ri] = loc[:, 1]; yf = yf.reshape(N, K)
assert np.isfinite(yf).all(), 'a cutter ray missed the face'
YB = yf + depth
vid = lambda i, k, back: (i*K + k) * 2 + back
P = np.zeros((N*K*2, 3))
for i in range(N):
    for k in range(K):
        P[vid(i, k, 0)] = (X[i], -80.0, Z[i, k]); P[vid(i, k, 1)] = (X[i], YB[i, k], Z[i, k])
T = []
for i in range(N-1):
    for k in range(K-1):
        for bk in (0, 1):
            a, b, c, d = vid(i, k, bk), vid(i+1, k, bk), vid(i+1, k+1, bk), vid(i, k+1, bk); T += [[a, b, c], [a, c, d]]
    for k in (0, K-1):                                                   # bottom and top walls
        a, b, c, d = vid(i, k, 0), vid(i+1, k, 0), vid(i+1, k, 1), vid(i, k, 1); T += [[a, b, c], [a, c, d]]
for i in (0, N-1):                                                       # end caps
    for k in range(K-1):
        a, b, c, d = vid(i, k, 0), vid(i, k+1, 0), vid(i, k+1, 1), vid(i, k, 1); T += [[a, b, c], [a, c, d]]
cut = trimesh.Trimesh(P, np.array(T), process=True); cut.fix_normals()
print('cutter watertight', cut.is_watertight, 'volume ok', cut.is_volume, 'vol mm3 %.2f' % cut.volume, '| x %.2f..%.2f' % (x0, x1), '| depth', depth)
assert cut.is_volume
res = trimesh.boolean.difference([m, cut], engine='manifold')
print('result faces', len(res.faces), 'watertight', res.is_watertight, 'winding', res.is_winding_consistent, 'volume', res.is_volume, 'bodies', res.body_count, 'removed mm3 %.2f' % (m.volume - res.volume))
# labels: faces lying on the cutter surface are pink; others take the nearest original face label
rc = res.triangles_center
d_cut = np.abs(trimesh.proximity.signed_distance(cut, rc)) if len(rc) < 0 else None
near_cut = cKDTree(cut.triangles_center).query(rc)[0]
on_cut = np.zeros(len(rc), bool)
cand = np.flatnonzero(near_cut < 1.0)
if len(cand):
    _, dist, _ = trimesh.proximity.closest_point(cut, rc[cand]); on_cut[cand[dist < 1e-3]] = True
lab = L[cKDTree(m.triangles_center).query(rc)[1]]; lab[on_cut] = 5
# Inside the cut outline (front view) everything that is not tooth is mouth: skin specks there become pink.
inside = (rc[:,0] > x0) & (rc[:,0] < x1) & (rc[:,2] > zb(rc[:,0]) - 0.02) & (rc[:,2] < zt(rc[:,0]) + 0.02) & (rc[:,1] > -40) & (rc[:,1] < -18)
spk = inside & (lab == 0); lab[spk] = 5
print('cut faces (pink)', int(on_cut.sum()), '| skin specks inside the cut -> pink', int(spk.sum()))
CUT_LABEL = int(sys.argv[5]) if len(sys.argv) > 5 else 5
if CUT_LABEL != 5:                                      # owner 2026-11-20: "just cut it empty" -> no pink at all
    lab[lab == 5] = CUT_LABEL; print('pink -> label', CUT_LABEL, '(empty cut, no mouth paint)')
np.savez(dst, v=res.vertices, f=res.faces.astype('i4'), l=lab.astype('u1'))
