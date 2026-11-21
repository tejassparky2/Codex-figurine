"""Owner 2026-11-21 (round 3): "turn red beads to white, turn light blue shirt to blue as mom's".
cs_round.npz -> cs_r3.npz. Red below 70 mm (the bracelet beads) -> white; baby's light-blue T-shirt -> mother's navy;
the royal-blue beads already print navy, so they are navy in the finish too. Red stays only for the mother's bindi and
the baby's forehead dot."""
import numpy as np, trimesh
z = np.load('cs_round.npz'); V, F, L = z['v'], z['f'], z['l'].astype(int).copy()
c = V[F].mean(1); area = trimesh.Trimesh(V, F, process=False).area_faces
for nm, s, to in [('red beads', (L == 5) & (c[:, 2] < 70), 2), ('light-blue shirt', L == 4, 3), ('royal-blue beads', L == 6, 3)]:
    print('%-17s %7d faces %7.1f mm2 -> %d' % (nm, s.sum(), area[s].sum(), to)); L[s] = to
r = L == 5; print('red left: z %.2f..%.2f mm, %.1f mm2' % (V[F[r]][:, :, 2].min(), V[F[r]][:, :, 2].max(), area[r].sum()))
np.savez('cs_r3.npz', v=V, f=F, l=L.astype('u1'))
