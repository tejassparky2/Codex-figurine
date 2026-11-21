"""Owner 2026-11-21 (round 3): "turn red beads to white, turn light blue shirt to blue as mom's".
cs_round.npz -> cs_r3.npz. Red below 70 mm (the bracelet beads) -> white; baby's light-blue T-shirt -> mother's navy;
the royal-blue beads already print navy, so they are navy in the finish too. Red stays only for the mother's bindi and
the baby's forehead dot."""
import numpy as np, trimesh
z = np.load('cs_round.npz'); V, F, L = z['v'], z['f'], z['l'].astype(int).copy()
c = V[F].mean(1); area = trimesh.Trimesh(V, F, process=False).area_faces
for nm, s, to in [('red beads', (L == 5) & (c[:, 2] < 70), 2), ('light-blue shirt', L == 4, 3), ('royal-blue beads', L == 6, 3)]:
    print('%-17s %7d faces %7.1f mm2 -> %d' % (nm, s.sum(), area[s].sum(), to)); L[s] = to
# owner, same day: "turn just one bead to black in bracelet" -> the front-most white bead (the one facing the viewer)
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
m = trimesh.Trimesh(V, F, process=False); a, b = m.face_adjacency.T; n = len(F)
S = (L == 2) & (c[:, 0] > -12) & (c[:, 0] < 20) & (c[:, 2] > 44) & (c[:, 2] < 68) & (c[:, 1] < 0)
k = S[a] & S[b]; comp = connected_components(coo_matrix((np.ones(k.sum()), (a[k], b[k])), shape=(n, n)), directed=False)[1]
j = np.argmin(np.where(S, np.linalg.norm(c - (1.6, -36.8, 55.6), axis=1), 1e9)); t = S & (comp == comp[j])
L[t] = 1; print('front white bead -> black: %.1f mm2, centre %s' % (area[t].sum(), np.round(c[t].mean(0), 1)))
r = L == 5; print('red left: z %.2f..%.2f mm, %.1f mm2' % (V[F[r]][:, :, 2].min(), V[F[r]][:, :, 2].max(), area[r].sum()))
np.savez('cs_r3.npz', v=V, f=F, l=L.astype('u1'))
