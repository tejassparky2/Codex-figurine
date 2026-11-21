"""Family #00025 (Tripo A, v2 art, bumps removed): printable mesh + per-face texture colour.
in : figurines projects/family_portrait_compare/remake/tripoA_nobumps.npz (v mm Z-up front -Y, f, rgb per face)
out: printable.npz (v, f), face_rgb.npy
1. cut flat at z = CUT (the customer's base is printed separately and glued), shift to z=0, rescale to 150 mm;
2. repair + quadric decimation to TARGET faces;
3. per-face colour: nearest source face (centroid distance + normal agreement) on the cut, scaled source."""
import sys, numpy as np, trimesh, pymeshlab as ml
from pymeshfix import _meshfix
from scipy.spatial import cKDTree
SRC = sys.argv[1]; CUT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5; TARGET = int(sys.argv[3]) if len(sys.argv) > 3 else 1200000; H = 150.0
z = np.load(SRC); v, f, rgb = z['v'].astype(float), z['f'], z['rgb']
def fix(V, F):
    t = _meshfix.PyTMesh(); t.set_quiet(True); t.load_array(np.ascontiguousarray(V, dtype='f8'), np.ascontiguousarray(F, dtype='i4'))
    t.fix_connectivity(); t.remove_smallest_components(); t.fill_small_boundaries(); t.clean(max_iters=10)
    return t.return_arrays()
fv, ff = fix(v, f); src = trimesh.Trimesh(fv, ff, process=True)
if src.volume < 0: src.invert()
print('source repaired: volume', src.is_volume, 'watertight', src.is_watertight, 'faces', len(src.faces))
box = trimesh.creation.box(extents=[400, 400, 400]); box.apply_translation([0, 0, CUT + 200])
cut = trimesh.boolean.intersection([src, box], engine='manifold')
print('cut at z=%.2f: %d faces, watertight %s, bodies %d' % (CUT, len(cut.faces), cut.is_watertight, cut.body_count))
s = H / (cut.vertices[:,2].max() - CUT)
def tf(p): q = np.array(p, float); q[:,2] -= CUT; return q * s
V, F = fix(tf(cut.vertices), cut.faces)
ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(vertex_matrix=V, face_matrix=F))
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=TARGET, preservetopology=True, preservenormal=True, optimalplacement=True, qualitythr=0.4)
V, F = fix(ms.current_mesh().vertex_matrix(), ms.current_mesh().face_matrix()); V = np.round(V, 6)
t = trimesh.Trimesh(V, F, process=True, validate=True)
if t.volume < 0: t.invert()
print('printable: faces', len(t.faces), 'extents', np.round(t.extents, 2), 'watertight', t.is_watertight, 'winding', t.is_winding_consistent,
      'volume', t.is_volume, 'bodies', t.body_count, 'z min %.3f' % t.vertices[:,2].min())
assert t.is_watertight and t.is_winding_consistent and t.is_volume and t.body_count == 1
np.savez('printable.npz', v=t.vertices.astype('f8'), f=t.faces.astype('i4'))
# colour transfer from the full-resolution source (same transform)
sv = tf(v); sc = sv[f].mean(1); sn = np.cross(sv[f][:,1]-sv[f][:,0], sv[f][:,2]-sv[f][:,0]); sn /= np.linalg.norm(sn, axis=1, keepdims=True) + 1e-12
pc = t.triangles_center; pn = t.face_normals
d, idx = cKDTree(sc).query(pc, k=8, workers=-1)
score = d + 0.3 * (1 - np.einsum('fkd,fd->fk', sn[idx], pn))
best = idx[np.arange(len(pc)), score.argmin(1)]
np.save('face_rgb.npy', rgb[best])
print('colour transfer: nearest distance median %.3f p99 %.3f mm' % (np.median(d[:,0]), np.percentile(d[:,0], 99)))
