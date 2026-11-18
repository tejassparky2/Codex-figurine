"""Weld, repair, decimate and place the Tripo GLB as an upright, watertight millimetre mesh.
Output printable.npz: v (Z-up mm, feet at z=0, centred X/Y), f.  Front of the figure faces -Y."""
import sys, numpy as np, trimesh, pymeshlab as ml
from pymeshfix import _meshfix
glb, H, target = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
m = trimesh.load(glb, force='mesh', process=False)
v = np.asarray(m.vertices, float); f = np.asarray(m.faces)
v = np.c_[v[:,0], -v[:,2], v[:,1]]          # glTF Y-up (front +Z) -> Z-up, front toward -Y
w = trimesh.Trimesh(v, f, process=False); w.merge_vertices()
def fix(V, F):
    t = _meshfix.PyTMesh(); t.set_quiet(True); t.load_array(np.ascontiguousarray(V, dtype="f8"), np.ascontiguousarray(F, dtype="i4"))
    t.fix_connectivity(); t.remove_smallest_components(); t.fill_small_boundaries(); t.clean(max_iters=10)
    return t.return_arrays()
V, F = fix(w.vertices, w.faces); print('repaired', len(F), flush=True)
ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(vertex_matrix=V, face_matrix=F))
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=target, preservetopology=True, preservenormal=True, optimalplacement=True, qualitythr=0.4)
V, F = fix(ms.current_mesh().vertex_matrix(), ms.current_mesh().face_matrix()); print('decimated', len(F), flush=True)
V = V - [(V[:,0].max()+V[:,0].min())/2, (V[:,1].max()+V[:,1].min())/2, V[:,2].min()]
V *= H / V[:,2].max(); V = np.round(V, 6)
t = trimesh.Trimesh(V, F, process=True, validate=True)
if t.volume < 0: t.invert()
print('faces', len(t.faces), 'extents', np.round(t.extents, 2), 'watertight', t.is_watertight, 'winding', t.is_winding_consistent,
      'volume ok', t.is_volume, 'bodies', t.body_count, 'volume cm3', round(t.volume/1000, 1))
assert t.is_watertight and t.is_winding_consistent and t.is_volume and t.body_count == 1
np.savez('printable.npz', v=t.vertices.astype('f8'), f=t.faces.astype('i4'))
