"""Owner (r4): "cut open that pink part". Extrude the pink mouth-gap patch (label 5) INTO the head by DEPTH mm:
the patch is replaced by a copy offset along the inward smoothed vertex normal, joined to the untouched boundary by a
wall of quads. Patch and wall are pink. Topology stays closed (watertight, consistent winding).
usage: carve_mouth.py in.npz out.npz depth_mm"""
import sys, numpy as np, trimesh
src, dst, depth = sys.argv[1], sys.argv[2], float(sys.argv[3])
z = np.load(src); V, F, L = z['v'].astype('f8'), z['f'].astype('i8'), z['l'].astype('i8')
m = trimesh.Trimesh(V, F, process=False)
P = np.flatnonzero(L == 5); Pm = np.zeros(len(F), bool); Pm[P] = True
# boundary edges of the patch, oriented as in the patch faces
E = np.c_[F[P][:, [0, 1]], F[P][:, [1, 2]], F[P][:, [2, 0]]].reshape(-1, 2)
key = np.sort(E, 1); u, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True); bnd = E[cnt[inv] == 1]
vp = np.unique(F[P])
# inward direction: horizontal, toward the head's vertical axis (x=0, y=HEAD_Y). One smooth field for the whole patch,
# so surfaces of the gap that face up or down do not fold (per-face normals did: 2684 self-intersecting faces).
EE = np.unique(np.sort(np.r_[F[P][:, [0, 1]], F[P][:, [1, 2]], F[P][:, [2, 0]]], 1), axis=0)
idx = -np.ones(len(V), int); idx[vp] = np.arange(len(vp))
HEAD_Y = float(sys.argv[4]) if len(sys.argv) > 4 else -5.0
d = np.c_[0.0 - V[vp, 0], HEAD_Y - V[vp, 1], np.zeros(len(vp))]; nrm = d / np.linalg.norm(d, axis=1, keepdims=True)
# Never cut through: per vertex, the room behind it is the first hit along the inward ray (other surfaces of the mouth
# sit < 1 mm behind the gap). Offset = min(depth, 0.45 * room), smoothed (min-biased) over the patch.
org = V[vp] + nrm * 1e-3
locs, ri, ti = m.ray.intersects_location(org, nrm, multiple_hits=False)
room = np.full(len(vp), 99.0); room[ri] = np.linalg.norm(locs - org[ri], axis=1)
off = np.minimum(depth, 0.45 * room)
for _ in range(4):
    nb = off.copy(); np.minimum.at(nb, idx[EE[:, 0]], off[idx[EE[:, 1]]]); np.minimum.at(nb, idx[EE[:, 1]], off[idx[EE[:, 0]]])
    off = 0.5 * (off + nb)
print('offset mm: min %.3f median %.3f max %.3f | room median %.3f' % (off.min(), np.median(off), off.max(), np.median(room)))
newv = V[vp] + off[:, None] * nrm; nid = len(V) + np.arange(len(vp))
V2 = np.vstack([V, newv]); remap = np.arange(len(V)); remap[vp] = nid
Fp = remap[F[P]]                                          # offset patch, same winding
a, b = bnd[:, 0], bnd[:, 1]; a2, b2 = remap[a], remap[b]
W = np.r_[np.c_[a, b, b2], np.c_[a, b2, a2]]               # wall quads
keep = ~Pm
F2 = np.vstack([F[keep], Fp, W]); L2 = np.r_[L[keep], np.full(len(Fp), 5), np.full(len(W), 5)]
used = np.zeros(len(V2), bool); used[F2.ravel()] = True; newid = -np.ones(len(V2), int); newid[used] = np.arange(used.sum())
V3, F3 = V2[used], newid[F2]
t = trimesh.Trimesh(V3, F3, process=False)
print(f'patch {len(P)} faces, {len(vp)} vertices offset {depth} mm, wall {len(W)} faces | watertight {t.is_watertight} winding {t.is_winding_consistent} volume {t.is_volume} bodies {t.body_count}')
import pymeshlab as ml
for nm, (VV, FF) in (('before', (V, F)), ('after', (V3, F3))):
    ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(vertex_matrix=VV, face_matrix=FF)); ms.compute_selection_by_self_intersections_per_face()
    print('self-intersecting faces', nm, int(ms.current_mesh().face_selection_array().sum()))
np.savez(dst, v=V3, f=F3.astype('i4'), l=L2.astype('u1'))
