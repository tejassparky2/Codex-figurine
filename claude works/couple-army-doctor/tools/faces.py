"""Face-only re-label (skin / black / white) with light smoothing, so brows, eyes and teeth stay separate.
The broad pass (label.py, lam 4) merged each of his eyes with its brow and dropped her brows.
Faces inside each face ellipse (front-facing) that are skin/black/white/brown are re-solved from the texture.
Lips are skin (owner: no lip colour, never black in a mouth). His closed smile: no white.
usage: faces.py [lam=0.6]   reads materials.npy, writes materials_f.npy"""
import sys, numpy as np, trimesh, maxflow
from pathlib import Path as _P; TK = str(_P(__file__).resolve().parents[3]/'wedding-u1-skill/toolkit/scripts'); sys.path.insert(0, TK)
from colorize_3mf import srgb_to_lab
z = np.load('printable.npz'); V, F = z['v'], z['f']; mesh = trimesh.Trimesh(V, F, process=False)
c = mesh.triangles_center; nrm = mesh.face_normals; area = mesh.area_faces
rgb = np.load('face_rgb.npy').astype(float); mat = np.load('materials.npy').astype(int).copy()
lam = float(sys.argv[1]) if len(sys.argv) > 1 else 0.6
# name: centre x, z, radii, front y limit, mouth box (x0,x1,z0,z1) where white is allowed (teeth) or None
FACES = {'him': dict(cx=-6.9, cz=131.5, rx=7.8, rz=9.5, mouth=None),
         'her': dict(cx=9.5, cz=117.8, rx=8.5, rz=8.5, mouth=(5.0, 14.5, 111.0, 115.5))}
PROTO = {0: ['E29A68','C8825A','F0B58A','D9946A','B87454','EDA77A','D08070','C87068','E0A090','B06A5A'],   # skin + lips
         1: ['1D1A12','2C2117','151515','3A2A1E','4A3626','5A4030','6A5040','2A2420'],                   # lashes, iris, brows
         3: ['E8E2DC','F2EDEA','D8D0CA','FFFFFF','CCC4BE']}                                              # eye whites, teeth
feat = srgb_to_lab(rgb)
for name, p in FACES.items():
    r = ((c[:,0]-p['cx'])/p['rx'])**2 + ((c[:,2]-p['cz'])/p['rz'])**2
    sel = (r < 1) & (nrm[:,1] < -0.2) & (c[:,1] < 0) & np.isin(mat, [0, 1, 3, 8])
    idx = np.flatnonzero(sel); m = len(idx); pos = {f: i for i, f in enumerate(idx)}
    U = np.zeros((m, 3)); keys = [0, 1, 3]
    for j, k in enumerate(keys):
        P = srgb_to_lab(np.array([[int(h[i:i+2], 16) for i in (0,2,4)] for h in PROTO[k]], float))
        U[:,j] = np.min(np.linalg.norm(feat[idx][:,None]-P[None], axis=2), 1)
    if p['mouth'] is None:
        U[:,2] += 1e3 * (c[idx,2] < p['cz'] - 2.5)              # no white below the eyes (closed smile)
    else:
        x0, x1, z0, z1 = p['mouth']; inm = (c[idx,0] > x0) & (c[idx,0] < x1) & (c[idx,2] > z0) & (c[idx,2] < z1)
        U[(c[idx,2] < p['cz'] - 2.5) & ~inm, 2] += 1e3
        U[inm, 1] += 1e3                                           # never black in a mouth
    U *= area[idx][:,None]
    ei, ej = mesh.face_adjacency.T; both = sel[ei] & sel[ej]; ei, ej = ei[both], ej[both]
    a_, b_ = np.array([pos[e] for e in ei]), np.array([pos[e] for e in ej])
    ev = mesh.face_adjacency_edges[both]; Lw = lam * np.linalg.norm(V[ev[:,0]] - V[ev[:,1]], axis=1)
    lab = U.argmin(1)
    for it in range(4):
        ch = 0
        for a in range(3):
            li, lj = lab[a_], lab[b_]; A = Lw*(li != lj); B = Lw*(li != a); C = Lw*(lj != a)
            lin = U[:,a] - U[np.arange(m), lab]; np.add.at(lin, a_, C-A); np.add.at(lin, b_, -C)
            g = maxflow.Graph[float](m, len(a_)); g.add_nodes(m); g.add_edges(a_, b_, B+C-A, np.zeros(len(a_)))
            g.add_grid_tedges(np.arange(m), np.maximum(lin, 0), np.maximum(-lin, 0)); g.maxflow()
            new = np.where(g.get_grid_segments(np.arange(m)), a, lab); ch += int((new != lab).sum()); lab = new
        if not ch: break
    old = mat[idx].copy(); mat[idx] = np.array(keys)[lab]
    print(name, 'faces', m, '| black %.1f mm2, white %.1f mm2, changed %d' % (area[idx][lab == 1].sum(), area[idx][lab == 2].sum(), (old != mat[idx]).sum()))
np.save('materials_f.npy', mat.astype('u1'))
