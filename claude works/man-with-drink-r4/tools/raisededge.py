# Generalised hairedge.py: usage raisededge.py rings lam raised_label zmin zmax (r4: collar = label 1, z 120-146)
"""r2 review 5 (owner: "hair edges not painted"): the hair mass's side walls (sideburns, hairline) carry skin colour in
Tripo's texture, so the paint edge sits on the hair's top rim and the wall prints skin. Re-solve skin/silver in a wide
band (rings) around the hair boundary on the head with a near-zero texture term and a strong concave-crease prior, so
the edge drops into the crease where hair meets skin. Frame, brows, eyes, teeth and the glass are fixed.
In place on leak.npy."""
import sys, numpy as np, trimesh, maxflow
from scipy.sparse import coo_matrix
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False); c = m.triangles_center; n = len(c); area = m.area_faces
lab = np.load('leak.npy').astype(int); frame = np.load('frame_full.npy')
rings = int(sys.argv[1]) if len(sys.argv) > 1 else 14; lam = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
a, b = m.face_adjacency.T; G = coo_matrix((np.ones(2*len(a)), (np.r_[a, b], np.r_[b, a])), shape=(n, n)).tocsr()
RL = int(sys.argv[3]) if len(sys.argv) > 3 else 2; Z0 = float(sys.argv[4]) if len(sys.argv) > 4 else 150; Z1 = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9
hair = (lab == RL) & ~frame; head = (c[:,2] > Z0) & (c[:,2] < Z1)
bd = np.zeros(n, bool); d = ((lab[a] == 0) & hair[b]) | (hair[a] & (lab[b] == 0)); bd[a[d]] = bd[b[d]] = True; bd &= head
band = bd.copy()
for _ in range(rings): band |= (G @ band.astype('f4')) > 0
# keep off the frame and its surroundings (the frame edge has its own pass), and off traced features
near_frame = frame.copy()
for _ in range(4): near_frame |= (G @ near_frame.astype('f4')) > 0
band &= head & np.isin(lab, [0, RL]) & ~near_frame
print('hair-edge band faces', int(band.sum()))
cur = (lab == RL).astype(int)                                         # 0 skin, 1 silver
U = np.zeros((n, 2)); U[:, 0] = 1e9 * (~band & (cur == 1)); U[:, 1] = 1e9 * (~band & (cur == 0))
U[band, 0] += 0.02 * area[band] * (cur[band] == 1); U[band, 1] += 0.02 * area[band] * (cur[band] == 0)   # tiny: keep current
ev = m.face_adjacency_edges; Ln = np.linalg.norm(m.vertices[ev[:,0]] - m.vertices[ev[:,1]], axis=1); ang = np.degrees(m.face_adjacency_angles)
w = lam * Ln * np.where(m.face_adjacency_convex, np.exp(-(ang/60.)**2), np.exp(-(ang/12.)**2))
lin = U[:, 1] - U[:, 0]
g = maxflow.Graph[float](n, len(a)); g.add_nodes(n); g.add_edges(a, b, w, w)
g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
new = g.get_grid_segments(np.arange(n)).astype(int)
out = lab.copy(); out[band] = np.where(new[band] == 1, RL, 0)
print('raised label', RL, 'changed', int((out != lab).sum()), '| skin->raised', int(((out == RL) & (lab == 0)).sum()), '| raised->skin', int(((out == 0) & (lab == RL)).sum()))
np.save('leak.npy', out.astype('u1'))
