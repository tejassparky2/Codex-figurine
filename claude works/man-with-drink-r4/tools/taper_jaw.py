"""Owner/customer (r4): "his face is not round but in the model it seems round". Narrow the lower face to the customer
image's taper. Width profiles (front view, skin) were aligned on the eye line (model z 175.2) and mouth line (z 156.0)
and compared relative to cheek width at t=0.3 (views/width_profile.npy). Scale factor s(z) on x about the face centre:
1.0 at and above z 169.4, down to ~0.81 at the jaw (z 144.5), back to 1.0 by z 138.5 so the neck/collar is untouched.
Vertices only; faces and labels unchanged. usage: taper_jaw.py in.npz out.npz [strength 0..1.5]"""
import sys, numpy as np, trimesh
src, dst = sys.argv[1], sys.argv[2]; k = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
z = np.load(src); V = z['v'].astype('f8').copy(); F = z['f']; L = z['l']
ZC = np.array([138.5, 140.5, 142.5, 144.5, 146.4, 148.3, 150.2, 152.2, 154.1, 156.0, 157.9, 161.8, 165.6, 169.4])
SC = np.array([1.00, 0.95, 0.86, 0.81, 0.825, 0.835, 0.845, 0.86, 0.875, 0.88, 0.935, 0.951, 0.973, 1.00])
s = 1 - k * (1 - np.interp(V[:, 2], ZC, SC))
s[(V[:, 2] < 138.5) | (V[:, 2] > 169.4)] = 1.0
# face centre per height from the skin silhouette (front-facing skin), smoothed
c = V[F].mean(1); sk = (L == 0) & (c[:, 1] < -10)
zz = np.arange(138, 171, 1.0); cx = []
for h in zz:
    q = sk & (np.abs(c[:, 2] - h) < 0.5); cx.append((c[q, 0].min() + c[q, 0].max()) / 2 if q.sum() > 20 else 0.0)
cx = np.convolve(np.pad(cx, 2, mode='edge'), np.ones(5) / 5, mode='valid'); xc = np.interp(V[:, 2], zz, cx)
V[:, 0] = xc + (V[:, 0] - xc) * s
t = trimesh.Trimesh(V, F, process=False)
print('strength', k, '| min scale %.3f' % s.min(), '| centre x %.2f..%.2f' % (cx.min(), cx.max()), '| watertight', t.is_watertight, 'winding', t.is_winding_consistent, 'volume', t.is_volume, 'bodies', t.body_count)
import pymeshlab as ml
ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(vertex_matrix=V, face_matrix=F)); ms.compute_selection_by_self_intersections_per_face()
print('self-intersecting faces', int(ms.current_mesh().face_selection_array().sum()))
np.savez(dst, v=V, f=F, l=L)
