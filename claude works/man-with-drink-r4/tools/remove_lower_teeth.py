"""r2 (owner: "there is Tripo lower teeth clay, I don't want that"): flatten the sculpted lower teeth.
They are a ~1 mm step tucked ~1 mm behind the upper teeth, on top of the lower lip (renders/mouth-sections.png).
Selected: faces in the mouth box below the upper teeth's bottom edge zcut(x), behind the lip front (y > -28.6), with
low texture chroma (teeth and dark gap; lips have chroma >= 45). Their interior vertices get 80 rounds of uniform
Laplacian smoothing with the patch boundary fixed, which relaxes the teeth into a smooth membrane between the lower lip
and the upper teeth. Topology is unchanged (still watertight); a self-intersection check runs on the result.
In place on printable.npz (the original is kept as printable-with-lower-teeth.npz). Re-run sample_texture.py after."""
import shutil, numpy as np, trimesh, cv2
from pathlib import Path
if not Path('printable-with-lower-teeth.npz').exists(): shutil.copy('printable.npz', 'printable-with-lower-teeth.npz')
z = np.load('printable-with-lower-teeth.npz'); V, F = z['v'].copy(), z['f']
m = trimesh.Trimesh(V, F, process=False); c = m.triangles_center; n = len(F)
rgb = np.load('face_rgb.npy'); Lab = cv2.cvtColor(rgb.reshape(-1,1,3), cv2.COLOR_RGB2LAB).reshape(-1,3).astype(float); ch = np.hypot(Lab[:,1]-128, Lab[:,2]-128)
# upper teeth bottom edge (mm), from cross-sections (x < 0) and the front texture (x >= 0), minus 0.08 mm
XS = [-12.5, -12, -8, -4, -1, 0, 1, 2, 3, 4, 5, 6.5]; ZS = [150.9, 150.4, 149.85, 149.85, 149.8, 150.42, 150.42, 150.65, 151.22, 151.6, 152.0, 152.6]
zcut = np.interp(c[:,0], XS, ZS) - 0.08
sel = (c[:,0] > -12.5) & (c[:,0] < 6.5) & (c[:,2] > 148.3) & (c[:,2] < zcut) & (c[:,1] > -28.6) & (c[:,1] < -21) & (ch < 40)
# keep the largest connected patch(es) only (drop stray faces elsewhere)
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
a, b = m.face_adjacency.T; e = sel[a] & sel[b]
nc, cc = connected_components(coo_matrix((np.ones(e.sum()), (a[e], b[e])), shape=(n, n)), directed=False)
size = np.bincount(cc[sel], minlength=nc); sel &= size[cc] >= 50
vin = np.unique(F[sel]); vout = np.unique(F[~sel]); free = np.setdiff1d(vin, vout)
print('faces', int(sel.sum()), 'area mm2 %.2f' % m.area_faces[sel].sum(), '| vertices moved', len(free), 'fixed boundary', len(vin) - len(free))
E = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]; E = np.unique(np.sort(E, 1), axis=0)
isfree = np.zeros(len(V), bool); isfree[free] = True
E = E[isfree[E[:, 0]] | isfree[E[:, 1]]]
for it in range(80):
    s = np.zeros_like(V); k = np.zeros(len(V))
    np.add.at(s, E[:, 0], V[E[:, 1]]); np.add.at(s, E[:, 1], V[E[:, 0]]); np.add.at(k, E[:, 0], 1); np.add.at(k, E[:, 1], 1)
    V[free] += 0.5 * (s[free] / k[free, None] - V[free])
d = np.linalg.norm(V - z['v'], axis=1); print('max vertex move mm %.3f, median %.3f' % (d[free].max(), np.median(d[free])))
t = trimesh.Trimesh(V, F, process=False)
assert t.is_watertight and t.is_winding_consistent
import pymeshlab as ml
ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(vertex_matrix=V, face_matrix=F)); ms.compute_selection_by_self_intersections_per_face()
bad = ms.current_mesh().face_selection_array(); near = np.linalg.norm(c - [-3, -26, 150], axis=1) < 15
print('self-intersecting faces near the mouth', int((bad & near).sum()), '| total', int(bad.sum()))
z0 = np.load('printable-with-lower-teeth.npz')
ms0 = ml.MeshSet(); ms0.add_mesh(ml.Mesh(vertex_matrix=z0['v'], face_matrix=F)); ms0.compute_selection_by_self_intersections_per_face()
print('before smoothing: total self-intersecting faces', int(ms0.current_mesh().face_selection_array().sum()))
np.save('lower_teeth_patch.npy', sel)
np.savez('printable.npz', v=V, f=F)
