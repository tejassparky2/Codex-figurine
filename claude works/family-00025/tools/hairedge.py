"""Owner 2026-11-21 (dad close-up): hairline curls and beard strands painted skin -> ragged hair/beard edges.
1) Hair/beard edge: in a band of RINGS face-rings around the black/skin boundary on the dad's head, re-solve skin vs black
   with a near-zero "keep current" term and a strong concave-crease prior (raisededge.py, man-with-drink r4), so the edge
   drops into the crease where the sculpted hair meets the skin. The glasses (box round the frame), eyes, brows and
   dots are locked.
2) Bracelet: each bead takes ONE colour. Bracelet faces (red/blue) are split into beads at concave creases; each bead
   gets its area-majority colour.
reads materials_e.npy, writes materials_h.npy"""
import sys, numpy as np, trimesh, maxflow
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False); c = m.triangles_center; n = len(c); area = m.area_faces
lab = np.load('materials_e.npy').astype(int)
RINGS = int(sys.argv[1]) if len(sys.argv) > 1 else 10; LAM = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
a, b = m.face_adjacency.T; G = coo_matrix((np.ones(2*len(a)), (np.r_[a, b], np.r_[b, a])), shape=(n, n)).tocsr()
ev = m.face_adjacency_edges; Ln = np.linalg.norm(m.vertices[ev[:,0]] - m.vertices[ev[:,1]], axis=1); ang = np.degrees(m.face_adjacency_angles)
x, y, zz = c.T
# --- 1) dad hair / beard edge ---
head = (x < -10) & (zz > 92)
frame_box = (x > -50) & (x < -6) & (zz > 112.0) & (zz < 130.0) & (y < 2)        # glasses, eyes, brows: locked
hair = lab == 1
bd = np.zeros(n, bool); d = ((lab[a] == 0) & hair[b]) | (hair[a] & (lab[b] == 0)); bd[a[d]] = bd[b[d]] = True
bd &= head & ~frame_box
band = bd.copy()
for _ in range(RINGS): band |= (G @ band.astype('f4')) > 0
band &= head & ~frame_box & np.isin(lab, [0, 1])
cur = (lab == 1).astype(int)
U = np.zeros((n, 2)); U[:, 0] = 1e9 * (~band & (cur == 1)); U[:, 1] = 1e9 * (~band & (cur == 0))
U[band, 0] += 0.02 * area[band] * (cur[band] == 1); U[band, 1] += 0.02 * area[band] * (cur[band] == 0)
w = LAM * Ln                                                     # shortest boundary: fills the comb of skin strands
U[band, 1] -= 0.0; U[band, 0] += 0.01 * area[band]                # slight lean to black inside the band
lin = U[:, 1] - U[:, 0]
g = maxflow.Graph[float](n, len(a)); g.add_nodes(n); g.add_edges(a, b, w, w)
g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
new = g.get_grid_segments(np.arange(n)).astype(int)
out = lab.copy(); out[band] = np.where(new[band] == 1, 1, 0)
print('dad hair/beard edge: band %d faces | skin->black %.1f mm2, black->skin %.1f mm2' % (
    band.sum(), area[(out == 1) & (lab == 0)].sum(), area[(out == 0) & (lab == 1)].sum()))
# --- 1b) hairlines (mother, dad): sculpted strands painted skin. Use the SHAPE: strands are rough, forehead skin smooth.
from scipy.spatial import cKDTree
rough = np.zeros(n)
HL = [('mother', (c[:,0] > 4) & (c[:,0] < 38) & (zz > 119.5)), ('dad', (c[:,0] < -10) & (zz > 129.5))]
for nm, reg in HL:
    idx = np.flatnonzero(reg & (y < 5)); t = cKDTree(c[idx]); nb = t.query_ball_point(c[idx], 0.6); nr = m.face_normals
    for i, lst in zip(idx, nb):
        mn = (nr[idx[lst]] * area[idx[lst], None]).sum(0); mn /= np.linalg.norm(mn) + 1e-12
        rough[i] = np.degrees(np.arccos(np.clip(nr[i] @ mn, -1, 1)))
    nb2 = t.query_ball_point(c[idx], 0.8); rs = np.array([rough[idx[l]].mean() for l in nb2])
    hairb = out == 1
    bd = np.zeros(n, bool); d = ((out[a] == 0) & hairb[b]) | (hairb[a] & (out[b] == 0)); bd[a[d]] = bd[b[d]] = True; bd &= reg
    bandh = bd.copy()
    for _ in range(14): bandh |= (G @ bandh.astype('f4')) > 0
    bandh &= reg & np.isin(out, [0, 1]) & (y < 5)
    R = np.zeros(n); R[idx] = rs
    T = 7.0; cb = np.clip((T - R) / T, 0, 1); cs = np.clip((R - T) / T, 0, 1)       # cost of black when smooth, of skin when rough
    U2 = np.zeros((n, 2)); U2[:, 0] = 1e9 * (~bandh & (out == 1)); U2[:, 1] = 1e9 * (~bandh & (out == 0))
    U2[bandh, 0] += area[bandh] * cs[bandh]; U2[bandh, 1] += area[bandh] * cb[bandh]
    w2 = 0.35 * Ln
    lin = U2[:, 1] - U2[:, 0]
    g = maxflow.Graph[float](n, len(a)); g.add_nodes(n); g.add_edges(a, b, w2, w2)
    g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
    new = g.get_grid_segments(np.arange(n)).astype(int); before = out.copy()
    out[bandh] = np.where(new[bandh] == 1, 1, 0)
    print('%s hairline: band %d faces | skin->black %.1f mm2, black->skin %.1f mm2' % (
        nm, bandh.sum(), area[(out == 1) & (before == 0)].sum(), area[(out == 0) & (before == 1)].sum()))
# --- 1c) dad's forehead curl: a smooth sculpted lump (roughness misses it). Faces near it that stand > 0.35 mm proud of
#         the forehead plane (fitted on a skin ring round it) become black.
cx, cz = -29.3, 136.4
ringf = (np.hypot(x - cx, zz - (cz - 1.9)) < 5) & (np.hypot(x - cx, zz - (cz - 1.9)) > 3) & (out == 0) & (y < 0)
coef = np.linalg.lstsq(np.c_[x[ringf], zz[ringf], np.ones(ringf.sum())], y[ringf], rcond=None)[0]
prot = (np.c_[x, zz, np.ones(n)] @ coef) - y
curl = (np.hypot(x - cx, zz - cz) < 2.6) & (y < 0) & (out == 0) & (prot > 0.35)
out[curl] = 1; print('dad forehead curl -> black: %.1f mm2' % area[curl].sum())
# --- 2) bracelet beads: one colour each. Beads are split by angle around the ring (necks = area minima) ---
from scipy.ndimage import gaussian_filter1d
S = np.isin(out, [5, 6]) & (x > -12) & (x < 20) & (zz > 44) & (zz < 68)
P = c[S]; mu = P.mean(0); _, _, Vt = np.linalg.svd(P - mu, full_matrices=False); e1, e2 = Vt[0], Vt[1]
th = np.degrees(np.arctan2((P - mu) @ e2, (P - mu) @ e1)) % 360
hst = np.bincount((th // 2).astype(int), weights=area[S], minlength=180); hs = gaussian_filter1d(hst, 3, mode='wrap')
mins = [i for i in range(180) if hs[i] < hs[i-1] and hs[i] <= hs[(i+1) % 180]]
mins = sorted(mins, key=lambda i: hs[i]); cut = []
for i in mins:
    if all(min(abs(i - j), 180 - abs(i - j)) >= 17 for j in cut): cut.append(i)     # beads >= 34 deg apart
cut = np.sort(np.array(cut) * 2.0); print('bead necks at', cut.round(0).tolist(), 'deg ->', len(cut), 'beads')
bead = np.searchsorted(cut, th) % len(cut)
idx = np.flatnonzero(S); orig = lab[idx]
# The art alternates red / blue; Tripo's texture does not (5 red, 2 blue side by side). Alternate around the ring; with an
# odd bead count the one repeated pair goes at the back of the wrist (largest mean y = furthest from the viewer).
K = len(cut); my = np.array([np.average(c[idx[bead == k], 1], weights=area[idx[bead == k]]) for k in range(K)])
kb = int(np.argmax(my)); best = None
for ph in (0, 1):
    cols = np.zeros(K, int)
    for j in range(K): cols[(kb + j) % K] = 5 if (j + ph) % 2 == 0 else 6
    agree = sum(area[idx[bead == k]][orig[bead == k] == cols[k]].sum() for k in range(K))
    if best is None or agree > best[0]: best = (agree, cols)
cols = best[1]
for k in range(K):
    t = bead == k; out[idx[t]] = cols[k]
    print('  bead %d: %.1f mm2, mean y %+.1f -> %s' % (k, area[idx[t]].sum(), my[k], 'red' if cols[k] == 5 else 'blue'))
# small leftover islands of the other bead colour (touching caps) join their bead
for _ in range(3):
    S = np.isin(out, [5, 6]) & (x > -12) & (x < 20) & (zz > 44) & (zz < 68)
    same = S[a] & S[b] & (out[a] == out[b]); nc, comp = connected_components(coo_matrix((np.ones(same.sum()), (a[same], b[same])), shape=(n, n)), directed=False)
    ca = np.bincount(comp, weights=area, minlength=nc); small = S & (ca[comp] < 1.0)
    if not small.any(): break
    d = S[a] & S[b] & (out[a] != out[b]); flip = np.zeros(n, bool); flip[a[d & small[a]]] = True; flip[b[d & small[b]]] = True
    out[flip] = np.where(out[flip] == 5, 6, 5); print('bead cap specks flipped:', int(flip.sum()))
np.save('materials_h.npy', out.astype('u1'))
