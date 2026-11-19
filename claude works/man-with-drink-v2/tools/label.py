"""Broad finish labels on printable.npz with the toolkit's crease-aware alpha-expansion (clean_colorize.solve),
using per-face texture samples and several texture prototypes per finish material.
Finish slots: 0 skin, 1 black, 2 silver (hair, frames, glass), 3 white (teeth, eye whites), 4 orange (whisky)."""
import sys, numpy as np, trimesh, maxflow, cv2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pathlib import Path as _P; TK = str(_P(__file__).resolve().parents[3]/'wedding-u1-skill/toolkit/scripts'); sys.path.insert(0, TK)
from colorize_3mf import srgb_to_lab
z = np.load('printable.npz'); V, F = z['v'], z['f']; mesh = trimesh.Trimesh(V, F, process=False)
rgb = np.load('face_rgb.npy').astype(float); c = mesh.triangles_center; n = len(F); area = mesh.area_faces
hsv = cv2.cvtColor(rgb.astype('u1').reshape(-1,1,3), cv2.COLOR_RGB2HSV).reshape(-1,3).astype(float)
ax = np.load('glass_axis.npy'); rad = np.hypot(c[:,0]-ax[0], c[:,1]-ax[1])
glass = (c[:,2] > 87.6) & (c[:,2] < 104.9) & (rad < ax[2] + .76)
head = c[:,2] > 140
PROTO = {0: ['F3863A','E37938','E57230','C86834','A15832','F09A60','D9784A'],
         1: ['191511','29241D','3A332C','10100E'],
         2: ['887E72','6D6459','A2978A','4D4337','C2B9AD','8C7B57','A89870','D1B591','B4B0AA','8F949A'],
         3: ['F0EDE5','E6DED2','FFFFFF','DCD3C6'],
         4: ['D08A2A','C07820','E0A040','B87018','E8B050']}
luma = 0.5
feat = srgb_to_lab(rgb); feat[:,0] *= luma
U = np.zeros((n, 5))
for k, hexes in PROTO.items():
    P = srgb_to_lab(np.array([[int(h[i:i+2], 16) for i in (0,2,4)] for h in hexes], float)); P[:,0] *= luma
    U[:,k] = np.min(np.linalg.norm(feat[:,None]-P[None], axis=2), 1)
allowed = np.ones((n,5), bool)
allowed[~glass, 4] = False                               # whisky only inside the glass
allowed[~(head | glass), 2] = False                      # silver: hair, frames, glass
allowed[~(head & (c[:,1] < 0)), 3] = False               # white: front of the head only
allowed[glass, 1] = False                                # no black on the glass
inner = glass & (rad < ax[2] + .46); allowed[inner, 0] = False  # the cylinder itself is never skin
# Inside the glass zone a saturated warm face with skin hue on the outer band is a fingertip, otherwise whisky.
U[glass & (hsv[:,0] >= 14) & (hsv[:,1] > 90), 0] *= 2.0
U[glass & (hsv[:,0] < 14) & (hsv[:,1] > 90), 4] *= 2.0
U = U * area[:,None]; U[~allowed] = 1e9
ei, ej = mesh.face_adjacency.T; ev = mesh.face_adjacency_edges
L = np.linalg.norm(V[ev[:,0]] - V[ev[:,1]], axis=1); ang = np.degrees(mesh.face_adjacency_angles)
lam, sigma, csig = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0, 25.0, 60.0
w = lam * L * np.where(mesh.face_adjacency_convex, np.exp(-(ang/csig)**2), np.exp(-(ang/sigma)**2))
lab = U.argmin(1); energy = lambda lb: U[np.arange(n), lb].sum() + w[lb[ei] != lb[ej]].sum()
print('start E=%.0f' % energy(lab), flush=True)
for it in range(4):                                      # alpha-expansion, as in toolkit clean_colorize.solve
    changed = 0
    for a in range(5):
        li, lj = lab[ei], lab[ej]; A = w*(li != lj); B = w*(li != a); C = w*(lj != a)
        lin = U[:,a] - U[np.arange(n), lab]; np.add.at(lin, ei, C-A); np.add.at(lin, ej, -C)
        g = maxflow.Graph[float](n, len(ei)); g.add_nodes(n); g.add_edges(ei, ej, B+C-A, np.zeros(len(ei)))
        g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
        new = np.where(g.get_grid_segments(np.arange(n)), a, lab); changed += int((new != lab).sum()); lab = new
    print('pass %d E=%.0f changed %d' % (it+1, energy(lab), changed), flush=True)
    if not changed: break
# Merge islands below 0.3 mm2 (keeps 0.4-nozzle-sized details) into the neighbour with the longest shared edge.
for _ in range(5):
    same = lab[ei] == lab[ej]; nc, comp = connected_components(coo_matrix((np.ones(same.sum()), (ei[same], ej[same])), shape=(n,n)), directed=False)
    small = np.bincount(comp, weights=area, minlength=nc)[comp] < 0.3
    d = ~same; a_, b_ = ei[d], ej[d]; rows = np.r_[comp[a_], comp[b_]]; nb = np.r_[lab[b_], lab[a_]]; ln = np.r_[L[d], L[d]]; k = small[np.r_[a_, b_]]
    M = coo_matrix((ln[k], (rows[k], nb[k])), shape=(nc, 5)).toarray(); new = np.where(small & (M[comp].sum(1) > 0), M.argmax(1)[comp], lab)
    new = np.where(allowed[np.arange(n), new], new, lab); step = int((new != lab).sum()); lab = new
    if not step: break
np.save('broad.npy', lab.astype('u1'))
for k, nm in enumerate(['skin','black','silver','white','orange']): print(f'{nm:7s} {100*area[lab==k].sum()/area.sum():5.2f}%')
