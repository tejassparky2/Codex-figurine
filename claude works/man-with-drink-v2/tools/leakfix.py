"""Snap paint boundaries to sculpted creases. Faces within a narrow band around skin/black/silver boundaries are
re-solved with alpha-expansion: weak texture unary, strong crease-weighted boundary cost. Everything outside the band
is fixed. The traced face, glasses frame and glass are protected."""
import sys, numpy as np, trimesh, maxflow
from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[3]/'wedding-u1-skill/toolkit/scripts'))
from colorize_3mf import srgb_to_lab
from scipy.sparse import coo_matrix
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False); c = m.triangles_center; n = len(c); area = m.area_faces
lab = np.load('detail.npy').astype(int); rgb = np.load('face_rgb.npy').astype(float); frame = np.load('frame_full.npy')
ax = np.load('glass_axis.npy'); rad = np.hypot(c[:,0]-ax[0], c[:,1]-ax[1])
face_details = (c[:,2] > 140) & (c[:,2] < 186) & (c[:,1] < -15) & (np.abs(c[:,0]) < 26)
protected = face_details | frame | ((c[:,2] > 86) & (c[:,2] < 106) & (rad < ax[2] + .91)) | np.isin(lab, [3, 4])
a, b = m.face_adjacency.T; G = coo_matrix((np.ones(2*len(a)), (np.r_[a, b], np.r_[b, a])), shape=(n, n)).tocsr()
edge = np.zeros(n, bool); d = (lab[a] != lab[b]) & np.isin(lab[a], [0,1,2]) & np.isin(lab[b], [0,1,2]); edge[a[d]] = edge[b[d]] = True
band = edge.copy()
for _ in range(int(sys.argv[1]) if len(sys.argv) > 1 else 6): band |= (G @ band.astype('f4')) > 0
band &= ~protected & np.isin(lab, [0, 1, 2])
print('band faces', band.sum())
# Unary: texture distance to the material prototypes (as in label.py), down-weighted; fixed faces pinned.
PROTO = {0: ['F3863A','E37938','E57230','C86834','A15832','F09A60','D9784A'], 1: ['191511','29241D','3A332C','10100E'],
         2: ['887E72','6D6459','A2978A','4D4337','C2B9AD','8C7B57','A89870','D1B591','B4B0AA','8F949A']}
feat = srgb_to_lab(rgb); feat[:,0] *= .5; U = np.full((n, 3), 0.)
for k, hx in PROTO.items():
    P = srgb_to_lab(np.array([[int(h[i:i+2], 16) for i in (0,2,4)] for h in hx], float)); P[:,0] *= .5
    U[:,k] = np.min(np.linalg.norm(feat[:,None]-P[None], axis=2), 1)
U = 0.35 * U * area[:,None]
U[(c[:,2] < 140), 2] = 1e9                                 # silver never below the head outside the glass
fixed = ~band; L3 = np.clip(lab, 0, 2); U[fixed] = 1e9; U[fixed, L3[fixed]] = 0
ev = m.face_adjacency_edges; Ln = np.linalg.norm(m.vertices[ev[:,0]] - m.vertices[ev[:,1]], axis=1); ang = np.degrees(m.face_adjacency_angles)
lam = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
w = lam * Ln * np.where(m.face_adjacency_convex, np.exp(-(ang/45.)**2), np.exp(-(ang/14.)**2))
cur = L3.copy(); E = lambda l: U[np.arange(n), l].sum() + w[l[a] != l[b]].sum(); print('E0 %.0f' % E(cur))
for it in range(4):
    ch = 0
    for al in range(3):
        li, lj = cur[a], cur[b]; A = w*(li != lj); B = w*(li != al); C = w*(lj != al)
        lin = U[:,al] - U[np.arange(n), cur]; np.add.at(lin, a, C-A); np.add.at(lin, b, -C)
        g = maxflow.Graph[float](n, len(a)); g.add_nodes(n); g.add_edges(a, b, B+C-A, np.zeros(len(a)))
        g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
        new = np.where(g.get_grid_segments(np.arange(n)), al, cur); ch += int((new != cur).sum()); cur = new
    print('pass', it+1, 'E %.0f' % E(cur), 'changed', ch)
    if not ch: break
out = lab.copy(); out[band] = cur[band]; out[frame] = 2
# Frame edge: re-solve skin/silver in a narrow band around the frame using thickness (thin = wire) and crease snapping.
thick = np.load('thickness.npy'); fb = np.zeros(n, bool); dd = (out[a] != out[b]) & (frame[a] | frame[b]); fb[a[dd]] = fb[b[dd]] = True
for _ in range(3): fb |= (G @ fb.astype('f4')) > 0
fb &= np.isin(out, [0, 2]) & (c[:,2] > 150) & (c[:,2] < 190) & ~((c[:,2] > 186) | (c[:,1] > 0))   # stay off the hair
U2 = np.full((n, 3), 1e9); U2[:, 0] = area*np.where(thick < 1.3, 1.0, 0.0); U2[:, 2] = area*np.where(thick < 1.6, 0.0, 1.0)
nf = ~fb; o3 = np.clip(out, 0, 2); U2[nf] = 1e9; U2[nf, o3[nf]] = 0; U2[fb & ~np.isin(out, [0, 2])] = 1e9
w2 = 2.0 * Ln * np.where(m.face_adjacency_convex, np.exp(-(ang/45.)**2), np.exp(-(ang/14.)**2))
cur2 = o3.copy()
for it in range(3):
    ch = 0
    for al in (0, 2):
        li, lj = cur2[a], cur2[b]; A = w2*(li != lj); B = w2*(li != al); C = w2*(lj != al)
        lin = U2[:,al] - U2[np.arange(n), cur2]; np.add.at(lin, a, C-A); np.add.at(lin, b, -C)
        g = maxflow.Graph[float](n, len(a)); g.add_nodes(n); g.add_edges(a, b, B+C-A, np.zeros(len(a)))
        g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
        new = np.where(g.get_grid_segments(np.arange(n)), al, cur2); ch += int((new != cur2).sum()); cur2 = new
    if not ch: break
print('frame-edge faces changed', int((cur2[fb] != out[fb]).sum()))
out[fb] = cur2[fb]
print('faces changed', int((out != lab).sum()))
np.save('leak.npy', out.astype('u1'))
