"""Codex's mouth (codex/figurine-evidence-sprint) re-applied to OUR clean mesh.

Codex: our cs_match10 -> front-fit (whole-body refit; makes the face crinkly at triangle level) -> couple-style
(face fairing, eye paint, head scale, smile-corner lift) -> refined-smile/revise.py -> portrait-smile/revise.py.
The mouth itself is made by smooth closed-form edits in the last two scripts (+ the corner lift). Here:
  S = A(ours)            A = affine ours -> Codex couple-style coordinates, fitted on a ring round the mouth
  P = portrait(refined(S))   Codex's own formulas, copied verbatim
  new = ours + A_lin^-1 (P - S)
so the mouth is Codex's and every other vertex (head match, ears, brows, whisky, eyes) is ours.

usage: codex_mouth_formula.py ours.npz codex_style.npz out.npz [frame.npz]
  frame.npz: a mesh with Codex's topology (cs_match10) in the same head frame as ours, used only to fit the
  affine; lets 'ours' be a different (e.g. uncut) mesh built by the same match/lift chain.
"""
import sys, numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
ours, style, out = sys.argv[1:4]
z = np.load(ours); V, F, L = z['v'], z['f'], z['l'].astype(int)
C = np.load(style)['v']
fz = np.load(sys.argv[4]) if len(sys.argv) > 4 else z                  # frame mesh: Codex topology
FV, FF, FL = fz['v'], fz['f'], fz['l'].astype(int)
assert C.shape == FV.shape and np.array_equal(np.load(style)['f'], FF)
def smooth(q): q = np.clip(q, 0, 1); return q * q * (3 - 2 * q)
T4 = np.isin(L, [3, 4])                                    # paint code 1C = tool T4 (white teeth above the swap)

# --- affine ours -> Codex style frame, on a ring around the mouth (outside every Codex mouth edit) ---
c = FV[FF].mean(1)
tv = FV[np.unique(FF[(FL == 3) & (c[:, 2] > 140) & (c[:, 2] < 165) & (c[:, 1] < -10)])]
mx, mz = (tv[:, 0].min() + tv[:, 0].max()) / 2, np.median(tv[:, 2])
r = np.sqrt(((FV[:, 0] - mx) / 34) ** 2 + ((FV[:, 2] - mz) / np.where(FV[:, 2] > mz, 8, 20)) ** 2)
front = FV[:, 1] < np.median(tv[:, 1]) + 14
ring = front & (r > 1.0) & (r < 1.4)
M = np.linalg.lstsq(np.c_[FV[ring], np.ones(ring.sum())], C[ring], rcond=None)[0]
S = np.c_[V, np.ones(len(V))] @ M
res = np.linalg.norm((np.c_[FV, np.ones(len(FV))] @ M)[ring] - C[ring], axis=1)
print('affine ring %d verts, residual mean %.3f p95 %.3f mm' % (ring.sum(), res.mean(), np.percentile(res, 95)))

# --- couple-style/resculpt.py: lift corners of the smile (skin only). The later z-restore keeps 10% of it in
#     their file, but their portrait comparison shows the lifted corners, so apply it as written. ---
v = S.copy(); x, y, zz = v.T
skin = np.zeros(len(v), bool); cc = v[F].mean(1)
skin[np.unique(F[(cc[:, 2] > 137) & (cc[:, 2] < 190) & (L != 2) & (cc[:, 1] < -12)])] = True
skin[np.unique(F[L == 2])] = False
v[:, 2] += 1.25 * np.exp(-((abs(x - 1) - 8) / 4.5) ** 2 - ((zz - 153) / 4.3) ** 2) * skin
S1 = v.copy()

# --- refined-smile/revise.py (verbatim maths) ---
t = v[F].mean(1); teeth = t[T4 & (t[:, 2] > 135) & (t[:, 2] < 165)]
x, y, zz = v.T
line = np.polyval(np.polyfit(teeth[:, 0], teeth[:, 2], 2), np.clip(x, -13, 13))
dy = zz - line
w = smooth((17 - abs(x + 0.5)) / 6) * smooth((-y - 15) / 6)
below = smooth((-dy + .5) / 2)
shift = -dy * (.31 + .38 * below) * np.exp(-(dy / 6.7) ** 2)
o = v.copy()
o[:, 2] += w * (shift - .65 * np.tanh(x / 7) * np.exp(-(dy / 5.8) ** 2))
arc = np.interp(x, np.arange(-10, 10, 2), [-24.8, -26.5, -28, -29.6, -31.1, -31.9, -31.7, -30.5, -28.4, -25.3])
o[:, 1] += w * .48 * np.exp(-(dy / 3.9) ** 2) * (arc - y)
v = o

# --- portrait-smile/revise.py (verbatim maths) ---
c2 = v[F].mean(1)
teeth = T4 & (c2[:, 2] > 140) & (c2[:, 2] < 162)
pts = v[np.unique(F[teeth])]
px = np.array([306,312,317,321,328,333,335,344,352,355,358,368,375,377,382,388,391,396,400,403,407,409])
upper = np.array([546,546,546,546,546,546,545,545,545,544,543,542,540,540,539,538,537,536,535,534,533,532])
lower = np.array([550,552,554,553,554,553,555,556,555,554,554,553,550,549,549,547,545,545,543,541,541,535])
x, y, zz = v.T
left, right = np.percentile(pts[:, 0], [.3, 99.7]); mid = (left + right) / 2
u = (x - left) / (right - left)
grid = np.linspace(left, right, 67)
def envelope(q):
    vals = [np.percentile(pts[abs(pts[:, 0] - g) < .48, 2], q) if np.any(abs(pts[:, 0] - g) < .48) else np.nan for g in grid]
    ok = np.isfinite(vals); vals = gaussian_filter1d(np.interp(grid, grid[ok], np.array(vals)[ok]), 1.2)
    return np.interp(x, grid, vals)
# ours: Codex clamps these lip/teeth curves at the ends of the tooth row, which leaves a kink (a visible
# vertical crease on the cheek). Same curves, evaluated on a 1-D x grid and Gaussian-smoothed (SIG mm).
SIG = 1.5
xs = np.arange(x.min() - 1, x.max() + 1, 0.05)
def env1(q):
    vals = [np.percentile(pts[abs(pts[:, 0] - g) < .48, 2], q) if np.any(abs(pts[:, 0] - g) < .48) else np.nan for g in grid]
    ok = np.isfinite(vals); vals = gaussian_filter1d(np.interp(grid, grid[ok], np.array(vals)[ok]), 1.2)
    return np.interp(xs, grid, vals)
lo1, hi1 = env1(4), env1(96)
tt1 = np.clip(px[0] + (xs - left) / (right - left) * (px[-1] - px[0]), px[0], px[-1])
mm = .177
top1 = 153.8 + (548 - PchipInterpolator(px, upper)(tt1)) * mm
bot1 = 153.8 + (548 - PchipInterpolator(px, lower)(tt1)) * mm
sm = lambda a: np.interp(x, xs, gaussian_filter1d(a, SIG / 0.05, mode='nearest'))
lo, hi, top, bottom = sm(lo1), sm(hi1), sm(top1), sm(bot1)
h = np.maximum(hi - lo, .45); orig = (hi + lo) / 2
center = (top + bottom) / 2
tt = np.clip(px[0] + u * (px[-1] - px[0]), px[0], px[-1])     # tooth grooves only (inside the tooth row)
w = smooth((-y - 13) / 8) * smooth((22 - abs(x - mid)) / 10) * smooth((12 - abs(zz - orig)) / 6)
dz = zz - orig
band = np.clip(dz / h, -.5, .5)
newz = zz + w * ((center - orig) + band * (top - bottom - h))
groove = sum(np.exp(-((tt - b) / 1.15) ** 2) for b in [320, 334, 355, 377, 391, 403])
tooth_area = smooth((2.1 - abs(dz)) / 1.25) * smooth((x - left + .1) / 1.4) * smooth((right - x + .1) / 1.4)
# ours: grooves only on tooth vertices (on the lip they made vertical stripes)
toothv = np.zeros(len(v), bool); toothv[np.unique(F[L == 3])] = True
newy = y + w * (.45 * groove * tooth_area * toothv + .50 * np.exp(-((dz + .95 * h) / .5) ** 2))
corner = smooth((abs(x - mid) - 6) / 4)
newz += w * corner * (.4 + .5 * np.tanh((x - mid) / 7))
P = v.copy(); P[:, 0] += w * (x - mid) * .115; P[:, 1] = newy; P[:, 2] = newz

# --- back to our frame ---
D = (P - S) @ np.linalg.inv(M[:3])
# ours: where the lower lip is pushed up behind the upper teeth the inner lip surfaces cross. Relax just those
# vertices (and one ring) back toward our own surface, which has 0 self-intersections, until none are left.
import pymeshlab
from scipy.sparse import coo_matrix
ii = F[:, [0, 1, 2, 1, 2, 0]].ravel(); jj = F[:, [1, 2, 0, 0, 1, 2]].ravel()
Adj = coo_matrix((np.ones(len(ii)), (ii, jj)), shape=(len(V), len(V))).tocsr()
for it in range(30):
    ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(V + D, F)); ms.compute_selection_by_self_intersections_per_face()
    sel = ms.current_mesh().face_selection_array()
    print('relax pass %d: self-intersecting faces %d' % (it, sel.sum()))
    if not sel.any(): break
    bad = np.zeros(len(V), bool); bad[np.unique(F[sel])] = True
    for _ in range(2): bad |= (Adj @ bad.astype(float)) > 0
    D[bad] *= 0.7
NV = V + D
d = np.linalg.norm(D, axis=1)
print('teeth span (Codex frame) %.2f mm | moved %d verts, max %.2f mm' % (right - left, (d > 1e-6).sum(), d.max()))
lab = z['l'].copy(); print('pink -> skin:', int((lab == 5).sum()), 'faces (owner: no pink, no black in the mouth)'); lab[lab == 5] = 0
np.savez(out, v=NV, f=F, l=lab)
