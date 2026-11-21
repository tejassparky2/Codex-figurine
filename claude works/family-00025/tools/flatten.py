"""Owner 2026-11-21: "remove it" (the dad's sculpted forehead curl). Flatten the curl into the forehead, the same method as
remake/remove_bumps.py: fit a quadratic height field to the forehead skin around it (below the hairline only), take the
curl patch (connected faces inside a cylinder round the curl, standing above the fit), re-place the patch vertices
fold-free by a Tutte embedding with the boundary fixed, and put them on the fitted skin.
Vertices only (faces and order unchanged), so face_rgb.npy stays valid. In place on printable.npz (backup printable_orig.npz)."""
import numpy as np, trimesh, os, shutil
from scipy.sparse import coo_matrix, csr_matrix, diags
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spsolve
if not os.path.exists('printable_orig.npz'): shutil.copy('printable.npz', 'printable_orig.npz')
z = np.load('printable_orig.npz'); V0, F = z['v'], z['f']; V = V0.copy()
m = trimesh.Trimesh(V0, F, process=False); c = m.triangles_center; fn = m.face_normals; n_f = len(F)
mat = np.load('materials_e.npy').astype(int)            # pre-hairline labels: 0 = skin
a, b = m.face_adjacency.T
E = np.unique(np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1), axis=0)
# name, centre x, z, cylinder radius, top limit (stay below the hairline)
LUMPS = [('dad forehead curl', -28.9, 136.6, 2.5, 139.2)]   # R 3.0 reached under the hair overhang: 265 self-intersections
for name, x, zz, R, ztop in LUMPS:
    loc, ri, ti = m.ray.intersects_location([[x, -300., zz]], [[0, 1., 0]], multiple_hits=False); p0 = loc[0]; seed = ti[0]
    d0 = np.hypot(c[:, 0] - x, c[:, 2] - zz)
    ann = (d0 > R + 0.4) & (d0 < R + 2.2) & (fn[:, 1] < 0) & (mat == 0) & (c[:, 2] < ztop - 0.3) & (np.abs(c[:, 1] - p0[1]) < 4)
    nrm = fn[ann].mean(0); nrm /= np.linalg.norm(nrm); nrm = -nrm if nrm[1] > 0 else nrm
    t1 = np.cross(nrm, [0, 0, 1.]); t1 /= np.linalg.norm(t1); t2 = np.cross(nrm, t1)
    def uvh(P): q = P - p0; return q @ t1, q @ t2, q @ nrm
    va = np.unique(F[ann]); u, v, h = uvh(V0[va])
    A = np.c_[np.ones_like(u), u, v, u*u, u*v, v*v]; coef = np.linalg.lstsq(A, h, rcond=None)[0]
    H = lambda u, v: np.c_[np.ones_like(u), u, v, u*u, u*v, v*v] @ coef
    cu, cv, ch = uvh(c); axial = np.hypot(cu, cv)
    near = (axial < R) & (ch - H(cu, cv) < 2.5) & (ch - H(cu, cv) > -0.6) & (c[:, 2] < ztop) & (np.abs(c[:, 1] - p0[1]) < 4)
    e = near[a] & near[b]; nc, cc = connected_components(coo_matrix((np.ones(e.sum()), (a[e], b[e])), shape=(n_f, n_f)), directed=False)
    patch = near & (cc == cc[seed])
    vin = np.unique(F[patch]); vout = np.unique(F[~patch]); free = np.setdiff1d(vin, vout)
    idx = -np.ones(len(V), int); idx[vin] = np.arange(len(vin)); EP = E[(idx[E[:, 0]] >= 0) & (idx[E[:, 1]] >= 0)]
    k = len(vin); Adj = csr_matrix((np.ones(2*len(EP)), (np.r_[idx[EP[:, 0]], idx[EP[:, 1]]], np.r_[idx[EP[:, 1]], idx[EP[:, 0]]])), shape=(k, k))
    deg = np.asarray(Adj.sum(1)).ravel(); Lap = (diags(deg) - Adj).tocsr()
    fi = idx[free]; bi = np.setdiff1d(np.arange(k), fi)
    ub, vb, _ = uvh(V0[vin[bi]])
    uf = spsolve(Lap[fi][:, fi].tocsc(), -(Lap[fi][:, bi] @ ub)); vf = spsolve(Lap[fi][:, fi].tocsc(), -(Lap[fi][:, bi] @ vb))
    V[free] = p0 + np.outer(uf, t1) + np.outer(vf, t2) + np.outer(H(uf, vf), nrm)
    print('%s: patch %d faces, %d vertices moved, max move %.2f mm, fit residual median %.3f mm' % (
        name, patch.sum(), len(free), np.linalg.norm(V[free] - V0[free], axis=1).max(), np.median(np.abs(A @ coef - h))))
t = trimesh.Trimesh(V, F, process=False)
print('watertight', t.is_watertight, 'volume', t.is_volume, 'bodies', t.body_count)
np.savez('printable.npz', v=V, f=F)
