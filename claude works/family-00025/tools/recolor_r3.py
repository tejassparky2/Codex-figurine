"""Owner 2026-11-21 (round 3): "turn red beads to white, turn light blue shirt to blue as mom's".
cs_round.npz -> cs_r3.npz. Red below 70 mm (the bracelet beads) -> white; baby's light-blue T-shirt -> white (owner: white reads better than the mother's navy);
the royal-blue beads already print navy, so they are navy in the finish too. Red stays only for the mother's bindi and
the baby's forehead dot."""
import numpy as np, trimesh
z = np.load('cs_round.npz'); V, F, L = z['v'], z['f'], z['l'].astype(int).copy()
c = V[F].mean(1); area = trimesh.Trimesh(V, F, process=False).area_faces
for nm, s, to in [('red beads', (L == 5) & (c[:, 2] < 70), 2), ('light-blue shirt', L == 4, 2), ('royal-blue beads', L == 6, 3)]:
    print('%-17s %7d faces %7.1f mm2 -> %d' % (nm, s.sum(), area[s].sum(), to)); L[s] = to
# owner, same day (front of the wrist, viewer's left to right: marked bead, front bead, navy bead, top bead):
# "turn that marked bead to black and next to that white, then current white one to black" -> black, white, navy, black
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
m = trimesh.Trimesh(V, F, process=False); a, b = m.face_adjacency.T; n = len(F)
box = (c[:, 0] > -12) & (c[:, 0] < 20) & (c[:, 2] > 44) & (c[:, 2] < 68) & (c[:, 1] < 0)
def bead(lbl, centre):
    S = box & (L == lbl); k = S[a] & S[b]
    comp = connected_components(coo_matrix((np.ones(k.sum()), (a[k], b[k])), shape=(n, n)), directed=False)[1]
    j = np.argmin(np.where(S, np.linalg.norm(c - centre, axis=1), 1e9)); return S & (comp == comp[j])
BEADS = [('marked bead (navy)', 3, (-0.8, -32.5, 53.4), 1), ('front bead (white)', 2, (1.6, -36.8, 55.6), 2),
         ('top bead (white)', 2, (9.8, -33.1, 60.7), 1)]
sel = [(nm, bead(lbl, ctr), to) for nm, lbl, ctr, to in BEADS]
for nm, t, to in sel:
    L[t] = to; print('%-19s -> %s: %.1f mm2, centre %s' % (nm, ['skin', 'black', 'white', 'navy'][to], area[t].sum(), np.round(c[t].mean(0), 1)))
# owner (circled): skin tongue under the baby's chin running into the white T-shirt. Upward-facing skin below the jaw
# is the neck / collar shelf, not the face -> white, so the jaw line is the edge.
nz = m.face_normals[:, 2]
neck = (L == 0) & (c[:, 0] > 46) & (c[:, 0] < 57) & (c[:, 2] > 55) & (c[:, 2] < 62) & (c[:, 1] < -15) & (nz > 0.35)
L[neck] = 2
# leftover skin flecks inside the new white (not joined to the face) -> white
nb = (L == 0) & (c[:, 0] > 44) & (c[:, 0] < 58) & (c[:, 2] > 54) & (c[:, 2] < 64) & (c[:, 1] < -15)
k = nb[a] & nb[b]; comp = connected_components(coo_matrix((np.ones(k.sum()), (a[k], b[k])), shape=(n, n)), directed=False)[1]
ca = np.bincount(comp[nb], weights=area[nb], minlength=comp.max() + 1); fleck = nb & (ca[comp] < 3.0)
L[fleck] = 2; neck |= fleck; print('skin under the baby jaw -> white: %.1f mm2' % area[neck].sum())
# owner: "that should be white not black" -> the black strip on the shoulder between the white collar and the overall
# strap (upward-facing shelf; texture shaded it dark) is T-shirt. x < 55: the strap itself runs over the shoulder at x 55-57
shoulder = (L == 1) & (c[:, 0] > 50) & (c[:, 0] < 55.8) & (c[:, 2] > 61.5) & (c[:, 2] < 65) & (c[:, 1] < 5) & (nz > 0.3)
L[shoulder] = 2
# big shelf triangles leave spikes at the strap edge: small white / black islands there flip to the other colour
reg = (c[:, 0] > 53.5) & (c[:, 0] < 57.5) & (c[:, 2] > 61) & (c[:, 2] < 65.5) & (c[:, 1] < 5) & np.isin(L, [1, 2])
for _ in range(3):
    same = reg[a] & reg[b] & (L[a] == L[b]); comp = connected_components(coo_matrix((np.ones(same.sum()), (a[same], b[same])), shape=(n, n)), directed=False)[1]
    ca = np.bincount(comp[reg], weights=area[reg], minlength=comp.max() + 1); sm = reg & (ca[comp] < 0.6)
    if not sm.any(): break
    L[sm] = np.where(L[sm] == 1, 2, 1)
print('black shoulder strip -> white: %.1f mm2' % area[shoulder].sum())
r = L == 5; print('red left: z %.2f..%.2f mm, %.1f mm2' % (V[F[r]][:, :, 2].min(), V[F[r]][:, :, 2].max(), area[r].sum()))
np.savez('cs_r3.npz', v=V, f=F, l=L.astype('u1'))
