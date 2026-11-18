"""Split every triangle crossing horizontal planes z=z0 so paint boundaries can follow them exactly.
Edge intersections are shared by both neighbours, so the mesh stays watertight. In place on printable.npz;
the pre-split mesh is kept as printable-unsplit.npz."""
import sys, shutil, numpy as np, trimesh
from pathlib import Path
if not Path('printable-unsplit.npz').exists(): shutil.copy('printable.npz', 'printable-unsplit.npz')
z = np.load('printable-unsplit.npz'); V, F = z['v'].copy(), z['f'].copy()
for z0 in map(float, sys.argv[1:]):
    near = np.abs(V[:,2]-z0) < 0.01; V[near, 2] = z0                 # snap to avoid slivers
    s = np.sign(np.round(V[:,2]-z0, 9)).astype(int)
    e = np.sort(np.r_[F[:,[0,1]], F[:,[1,2]], F[:,[2,0]]], 1); e = np.unique(e[(s[e[:,0]]*s[e[:,1]]) < 0], axis=0)
    t = (z0 - V[e[:,0],2]) / (V[e[:,1],2] - V[e[:,0],2]); P = V[e[:,0]] + t[:,None]*(V[e[:,1]] - V[e[:,0]])
    newid = {tuple(k): len(V)+i for i, k in enumerate(e)}; V = np.vstack([V, P])
    out = []
    for f in F:
        sf = s[f]
        if not ((sf > 0).any() and (sf < 0).any()): out.append(f); continue
        # rotate so the face starts at the vertex that is alone on its side (or on the plane)
        for r in range(3):
            g = np.roll(f, -r); sg = s[g]
            if sg[0] == 0 and sg[1]*sg[2] < 0:                        # one vertex on plane, one edge crosses
                m = newid[tuple(sorted((g[1], g[2])))]; out += [[g[0], g[1], m], [g[0], m, g[2]]]; break
            if sg[0] != 0 and sg[1] == sg[2] == -sg[0]:               # lone vertex g0
                m1 = newid[tuple(sorted((g[0], g[1])))]; m2 = newid[tuple(sorted((g[0], g[2])))]
                out += [[g[0], m1, m2], [m1, g[1], g[2]], [m1, g[2], m2]]; break
    F = np.asarray(out); print('plane', z0, 'split edges', len(e), 'faces', len(F), flush=True)
m = trimesh.Trimesh(V, F, process=True, validate=True)
print('faces', len(m.faces), 'watertight', m.is_watertight, 'winding', m.is_winding_consistent, 'volume', m.is_volume, 'bodies', m.body_count)
assert m.is_watertight and m.is_winding_consistent and m.is_volume and m.body_count == 1
np.savez('printable.npz', v=m.vertices, f=m.faces.astype('i4'))
