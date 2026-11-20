"""Couple (army officer + doctor): material labels on printable.npz from the per-face texture (face_rgb.npy) with
crease-aware alpha-expansion graph cut (same energy as man-with-drink r4 label.py).
Materials: 0 skin, 1 black, 2 green, 3 white, 4 yellow, 5 gold, 6 red, 7 cream (her shoes, his shirt), 8 brown hair, 9 silver.
He stands on -X (image left in front), she on +X. Front faces -Y."""
import sys, numpy as np, trimesh, maxflow
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pathlib import Path as _P; TK = str(_P(__file__).resolve().parents[3]/'wedding-u1-skill/toolkit/scripts'); sys.path.insert(0, TK)
from colorize_3mf import srgb_to_lab
z = np.load('printable.npz'); V, F = z['v'], z['f']; mesh = trimesh.Trimesh(V, F, process=False)
rgb = np.load('face_rgb.npy').astype(float); c = mesh.triangles_center; n = len(F); area = mesh.area_faces
K = 10
PROTO = {0: ['E29A68','C8825A','F0B58A','D9946A','B87454','EDA77A'],
         1: ['1D1A12','2C2117','151515','0E0E0E','24201A'],
         2: ['222F1D','2A3A25','1A2416','34452E','3C4A34'],
         3: ['E4DAD7','F2EDEA','D8CCC8','FFFFFF','C8BEBB','EDE4E0'],
         4: ['F6C604','E8B800','FFD200','D9A800','F8D030'],
         5: ['DBB143','C9A040','E8C460','B89030','A88A3A'],
         6: ['EC450E','D02010','C83020','E03A20'],
         7: ['DCBC91','E8D0A8','C8A878','D4B48A'],
         8: ['6A4020','87562D','4A311D','A06A3A','5A3818'],
         9: ['A0A0A0','C0C0C0','808080','B8B8B8']}
luma = 0.6
feat = srgb_to_lab(rgb); feat[:,0] *= luma
U = np.zeros((n, K))
for k, hexes in PROTO.items():
    P = srgb_to_lab(np.array([[int(h[i:i+2], 16) for i in (0,2,4)] for h in hexes], float)); P[:,0] *= luma
    U[:,k] = np.min(np.linalg.norm(feat[:,None]-P[None], axis=2), 1)
x, y, zz = c.T
allowed = np.ones((n, K), bool)
allowed[x < -6, 4] = False                                   # yellow: her dress / leggings only
allowed[~((x < 4) & (zz > 55)), 5] = False                   # gold: his buttons and shoulder stars
allowed[~((x > 0) & (zz > 25) & (zz < 102) & (y < 0)), 6] = False   # red: her dress buttons (front)
allowed[~((zz < 9) | ((zz > 112) & (zz < 132) & (x < 6))), 7] = False   # cream: her shoes, his shirt collar
allowed[~((zz > 80) & (x > -16)), 8] = False                 # brown: her hair lengths
allowed[~((zz > 70) & (zz < 115) & (x > -4)), 9] = False     # silver: stethoscope metal
allowed[(zz < 9) & (x > 2), 2] = False                       # no green on her shoes
U = U * area[:,None]; U[~allowed] = 1e9
ei, ej = mesh.face_adjacency.T; ev = mesh.face_adjacency_edges
L = np.linalg.norm(V[ev[:,0]] - V[ev[:,1]], axis=1); ang = np.degrees(mesh.face_adjacency_angles)
lam, sigma, csig = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0, 25.0, 60.0
w = lam * L * np.where(mesh.face_adjacency_convex, np.exp(-(ang/csig)**2), np.exp(-(ang/sigma)**2))
lab = U.argmin(1); energy = lambda lb: U[np.arange(n), lb].sum() + w[lb[ei] != lb[ej]].sum()
print('start E=%.0f' % energy(lab), flush=True)
for it in range(4):
    changed = 0
    for a in range(K):
        li, lj = lab[ei], lab[ej]; A = w*(li != lj); B = w*(li != a); C = w*(lj != a)
        lin = U[:,a] - U[np.arange(n), lab]; np.add.at(lin, ei, C-A); np.add.at(lin, ej, -C)
        g = maxflow.Graph[float](n, len(ei)); g.add_nodes(n); g.add_edges(ei, ej, B+C-A, np.zeros(len(ei)))
        g.add_grid_tedges(np.arange(n), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
        new = np.where(g.get_grid_segments(np.arange(n)), a, lab); changed += int((new != lab).sum()); lab = new
    print('pass %d E=%.0f changed %d' % (it+1, energy(lab), changed), flush=True)
    if not changed: break
for _ in range(5):                                            # merge islands < 0.3 mm2 into the longest-border neighbour
    same = lab[ei] == lab[ej]; nc, comp = connected_components(coo_matrix((np.ones(same.sum()), (ei[same], ej[same])), shape=(n,n)), directed=False)
    small = np.bincount(comp, weights=area, minlength=nc)[comp] < 0.3
    d = ~same; a_, b_ = ei[d], ej[d]; rows = np.r_[comp[a_], comp[b_]]; nb = np.r_[lab[b_], lab[a_]]; ln = np.r_[L[d], L[d]]; k = small[np.r_[a_, b_]]
    M = coo_matrix((ln[k], (rows[k], nb[k])), shape=(nc, K)).toarray(); new = np.where(small & (M[comp].sum(1) > 0), M.argmax(1)[comp], lab)
    new = np.where(allowed[np.arange(n), new], new, lab); step = int((new != lab).sum()); lab = new
    if not step: break
np.save('materials.npy', lab.astype('u1'))
NAMES = ['skin','black','green','white','yellow','gold','red','cream','brown','silver']
for k in range(K):
    s = lab == k
    if s.any(): print('%-6s %8.0f mm2  z %5.1f..%5.1f  (p1 %5.1f, p99 %5.1f)' % (NAMES[k], area[s].sum(), zz[s].min(), zz[s].max(), np.percentile(zz[s],1), np.percentile(zz[s],99)))
