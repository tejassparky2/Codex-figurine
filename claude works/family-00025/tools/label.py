"""Family #00025 materials on printable.npz from face_rgb.npy (crease-aware alpha-expansion graph cut, as couple label.py).
Materials: 0 skin, 1 black, 2 white, 3 navy, 4 light blue (baby tee), 5 red (beads), 6 royal blue (beads), 7 gold (ring).
Front faces -Y. Dad on -X (white tee), mother centre/right (navy top), baby on her lap at +X.
Region rules: navy only on the mother (x > -15; Tripo smeared navy into the back of the dad's tee); baby tee, beads and ring
only in their boxes. The flat bottom cap (glued to the base) takes its neighbours' labels."""
import sys, numpy as np, trimesh, maxflow
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pathlib import Path as _P; TK = str(_P(__file__).resolve().parents[3]/'wedding-u1-skill/toolkit/scripts'); sys.path.insert(0, TK)
from colorize_3mf import srgb_to_lab
z = np.load('printable.npz'); V, F = z['v'], z['f']; mesh = trimesh.Trimesh(V, F, process=False)
rgb = np.load('face_rgb.npy').astype(float); c = mesh.triangles_center; nrm = mesh.face_normals; n = len(F); area = mesh.area_faces
K = 8
PROTO = {0: ['C0743D','D7874B','9A5E36','E09A60','B06A38','CC8048'],
         1: ['211D19','332A23','5E3E28','151515','2A2622','3A302A'],
         2: ['EFDDCE','B1A4A4','F4ECE4','D8CCC4','C8BCB8','E6D6CA'],
         3: ['13153D','0F112E','1B2050','464566','2A2D55','757082'],
         4: ['79A0A1','658082','8BB5B5','6F9696'],
         5: ['A71226','C02030','8A1020'],
         6: ['2E1774','2A2A9A','3A2088'],
         7: ['C8A040','D8B050','B89030']}
luma = 0.5
feat = srgb_to_lab(rgb); feat[:,0] *= luma
U = np.zeros((n, K))
for k, hexes in PROTO.items():
    P = srgb_to_lab(np.array([[int(h[i:i+2], 16) for i in (0,2,4)] for h in hexes], float)); P[:,0] *= luma
    U[:,k] = np.min(np.linalg.norm(feat[:,None]-P[None], axis=2), 1)
x, y, zz = c.T
cap = (zz < 0.05) & (nrm[:,2] < -0.95)                         # flat glued bottom
allowed = np.ones((n, K), bool)
allowed[x < -15, 3] = False                                    # navy: mother only
allowed[(x < -15) & (zz < 88), 1] = False                      # dad below the beard: white tee and skin only (smear went black)
allowed[~((x > 8) & (x < 80) & (zz > 34) & (zz < 70)), 4] = False          # light blue: baby tee
allowed[~((x > -10) & (x < 18) & (zz > 46) & (zz < 66)), 5] = False        # red beads
allowed[~((x > -10) & (x < 18) & (zz > 46) & (zz < 66)), 6] = False        # royal blue beads
allowed[~((x > 15) & (x < 60) & (zz > 25) & (zz < 60) & (y < 0)), 7] = False   # mother's ring
U = U * area[:,None]; U[~allowed] = 1e9; U[cap] = 0               # cap: free, decided by neighbours
ei, ej = mesh.face_adjacency.T; ev = mesh.face_adjacency_edges
L = np.linalg.norm(V[ev[:,0]] - V[ev[:,1]], axis=1); ang = np.degrees(mesh.face_adjacency_angles)
lam, sigma, csig = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0, 25.0, 60.0
w = lam * L * np.where(mesh.face_adjacency_convex, np.exp(-(ang/csig)**2), np.exp(-(ang/sigma)**2))
w[cap[ei] | cap[ej]] = lam * L[cap[ei] | cap[ej]]                  # cap edges: plain length cost so the cap follows the walls
lab = U.argmin(1); energy = lambda lb: U[np.arange(n), lb].sum() + w[lb[ei] != lb[ej]].sum()
print('start E=%.0f' % energy(lab), flush=True)
for it in range(5):
    changed = 0
    for a in range(K):
        li, lj = lab[ei], lab[ej]; A = w*(li != lj); B = w*(li != a); C = w*(lj != a)
        lin = U[:,a] - U[np.arange(n), lab]; np.add.at(lin, ei, C-A); np.add.at(lin, ej, -C)
        g = maxflow.Graph[float](n, len(ei)); g.add_nodes(n); g.add_edges(ei, ej, B+C-A, np.zeros(len(ei)))
        g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
        new = np.where(g.get_grid_segments(np.arange(n)), a, lab); changed += int((new != lab).sum()); lab = new
    print('pass %d E=%.0f changed %d' % (it+1, energy(lab), changed), flush=True)
    if not changed: break
for _ in range(5):
    same = lab[ei] == lab[ej]; nc, comp = connected_components(coo_matrix((np.ones(same.sum()), (ei[same], ej[same])), shape=(n,n)), directed=False)
    small = np.bincount(comp, weights=area, minlength=nc)[comp] < 0.3
    d = ~same; a_, b_ = ei[d], ej[d]; rows = np.r_[comp[a_], comp[b_]]; nb = np.r_[lab[b_], lab[a_]]; ln = np.r_[L[d], L[d]]; k = small[np.r_[a_, b_]]
    M = coo_matrix((ln[k], (rows[k], nb[k])), shape=(nc, K)).toarray(); new = np.where(small & (M[comp].sum(1) > 0), M.argmax(1)[comp], lab)
    new = np.where(allowed[np.arange(n), new], new, lab); step = int((new != lab).sum()); lab = new
    if not step: break
np.save('materials.npy', lab.astype('u1'))
NAMES = ['skin','black','white','navy','lightblue','red','royalblue','gold']
for k in range(K):
    s = lab == k
    if s.any(): print('%-9s %8.0f mm2  z %5.1f..%5.1f (p1 %5.1f p99 %5.1f)' % (NAMES[k], area[s].sum(), zz[s].min(), zz[s].max(), np.percentile(zz[s],1), np.percentile(zz[s],99)))
