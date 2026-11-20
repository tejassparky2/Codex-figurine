"""After match_head.py: the customer image's ears sit ~2 mm higher than the model's (red-outline overlay,
renders/match-overlay.png). Smooth local lift: dz = LIFT * w, w = smoothstep(|x - xc| from 22 to 27 mm)
* exp(-((z-ze)^2 + (y-ye)^2) / (2*8^2)) per ear, so the ear, its root, the glasses arm resting on it and the hair
just around it move together; the face (|x| < 22) does not move. usage: lift_ears.py in.npz out.npz lift_mm"""
import sys, numpy as np, trimesh
src, dst, lift = sys.argv[1], sys.argv[2], float(sys.argv[3])
z = np.load(src); V = z['v'].astype('f8').copy(); F = z['f']; L = z['l']
EARS = [(-1, (-29.2, 10.9, 171.2)), (+1, (27.5, 10.6, 173.5))]
xc = -0.8
dz = np.zeros(len(V))
for sgn, (xe, ye, ze) in EARS:
    u = np.clip((sgn * (V[:, 0] - xc) - 22.0) / 5.0, 0, 1); u = u * u * (3 - 2 * u)
    g = np.exp(-((V[:, 2] - ze) ** 2 + (V[:, 1] - ye) ** 2) / (2 * 8.0 ** 2))
    dz += lift * u * g
V[:, 2] += dz
t = trimesh.Trimesh(V, F, process=False)
print('lift %.1f mm | moved vertices %d (max %.2f) | watertight %s winding %s volume %s bodies %d' % (lift, int((dz > 0.05).sum()), dz.max(), t.is_watertight, t.is_winding_consistent, t.is_volume, t.body_count))
import pymeshlab as ml
ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(vertex_matrix=V, face_matrix=F)); ms.compute_selection_by_self_intersections_per_face()
print('self-intersecting faces', int(ms.current_mesh().face_selection_array().sum()))
np.savez(dst, v=V, f=F, l=L)
