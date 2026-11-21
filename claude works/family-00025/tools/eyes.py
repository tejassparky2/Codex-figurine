"""Family #00025 face fixes + printed eyes (owner rule: white socket, round black iris at the texture iris, upper lash line).
- dad: the white blotch under his right lens is a baked lens reflection -> skin
- mother: the navy island on her cheek by the frame -> skin
- each eye: opening measured from its own white + small dark faces (the glasses frame, a big black island, is excluded)
reads materials_d.npy, writes materials_e.npy"""
import numpy as np, trimesh, sys
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pathlib import Path as _P; TK = str(_P(__file__).resolve().parents[3]/'wedding-u1-skill/toolkit/scripts'); sys.path.insert(0, TK)
from colorize_3mf import srgb_to_lab
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False)
c = m.triangles_center; nrm = m.face_normals; area = m.area_faces; n = len(c)
mat = np.load('materials_d.npy').astype(int).copy()
Lt = srgb_to_lab(np.load('face_rgb.npy').astype(float))[:,0]
ei, ej = m.face_adjacency.T
def comps(lbl):
    s = mat == lbl; k = s[ei] & s[ej]
    return s, connected_components(coo_matrix((np.ones(k.sum()), (ei[k], ej[k])), shape=(n, n)), directed=False)[1]
# 1) baked reflection / stray navy
for lbl, centre, name in [(2, (-35.37, -7.6, 118.81), 'dad lens reflection'), (3, (31.5, -12.71, 107.95), 'mother cheek navy')]:
    s, comp = comps(lbl); j = np.argmin(np.where(s, np.linalg.norm(c - centre, axis=1), 1e9)); t = s & (comp == comp[j])
    mat[t] = 0; print('%s -> skin: %.2f mm2' % (name, area[t].sum()))
# 2) printed eyes. centre (x, z), axis angle (deg)
# 2026-11-21: the automatic printed-eye construction below turned these eyes into black blobs (centres ~1 mm off at
# 1.2-1.9 mm eye heights); the texture-derived eyes (white both sides of a dark iris) read better, so they are kept.
EYES_TRIED = [('dad R', -30.9, 122.8, -9.7), ('dad L', -14.5, 120.2, -9.7), ('mom R', 14.0, 110.1, 9.4), ('mom L', 28.5, 112.5, 9.4),
        ('baby R', 33.3, 72.96, 5.6), ('baby L', 45.0, 74.1, 5.6)]
EYES = []
sb, compb = comps(1); bigb = np.bincount(compb[sb], weights=area[sb], minlength=compb.max()+1)
front = (nrm[:,1] < -0.1) & (c[:,1] < 0)
for name, ex, ez, ang in EYES:
    t = np.deg2rad(ang); ax, up = np.array([np.cos(t), np.sin(t)]), np.array([-np.sin(t), np.cos(t)])
    d = np.c_[c[:,0]-ex, c[:,2]-ez]; u, v = d @ ax, d @ up
    box = front & (np.abs(u) < 4.0) & (np.abs(v) < 2.0)
    yloc = np.median(c[box & (mat == 2), 1]); box &= np.abs(c[:,1] - yloc) < 2.5
    small_black = (mat == 1) & (bigb[compb] < 6.0)                   # irises, not the frame or brows
    eye = box & ((mat == 2) | (small_black & (np.abs(v) < 1.2)))
    u0, u1 = np.percentile(u[eye], [1, 99]); v0, v1 = np.percentile(v[eye], [2, 98])
    uc, vc = (u0 + u1) / 2, (v0 + v1) / 2; hw, hh = (u1 - u0) / 2 + 0.1, (v1 - v0) / 2 + 0.05
    uu, vv = u - uc, v - vc
    alm = box & ((uu / hw)**2 + (vv / (hh * (1 - 0.35*(uu/hw)**2)))**2 < 1.0) & ~((mat == 1) & ~small_black)
    ins = np.flatnonzero(alm); dk = ins[Lt[ins] < np.percentile(Lt[ins], 30)]
    iu = np.clip(np.average(uu[dk], weights=area[dk]), -hw + hh, hw - hh); R = hh * 0.98
    iris = alm & ((uu - iu)**2 + vv**2 < R**2)
    bins = np.round(uu[alm] / 0.15).astype(int); top = {}
    for b, q in zip(bins, vv[alm]): top[b] = max(top.get(b, -9), q)
    tb = np.array([top.get(b, -9) for b in np.round(uu / 0.15).astype(int)])
    lash = alm & (vv > tb - 0.22)
    mat[alm] = 2; mat[iris] = 1; mat[lash] = 1
    # stray white/black eye bits just outside the new socket -> skin
    rim = box & ~alm & ((mat == 2) | small_black) & ((uu / (hw + 0.5))**2 + (vv / (hh + 0.5))**2 < 1.0)
    mat[rim] = 0
    print('%-6s opening %.1f x %.1f mm, socket %.2f mm2, iris %.2f mm2 at u %+.2f, lash %.2f mm2' % (
        name, 2*hw, 2*hh, area[alm].sum(), area[iris].sum(), iu, area[lash].sum()))
# owner 2026-11-21: "where is baby's eyebrows" -- faint in the texture, so no pass painted them. Draw each as a thin solid
# black arc at the texture's darker brow band above the eye (couple eyes.py method).
BABY = []   # moved to roundify.py: face-by-face arcs this thin came out as broken dashes; drawn there as exact cuts
for name, ex, ez, ang, outer in BABY:
    t = np.deg2rad(ang); ax, up = np.array([np.cos(t), np.sin(t)]), np.array([-np.sin(t), np.cos(t)])
    d = np.c_[c[:,0]-ex, c[:,2]-ez]; u, v = d @ ax, d @ up
    near = (nrm[:,1] < -0.1) & (c[:,1] < -20) & (np.abs(u) < 3.6) & (v > 0.9) & (v < 4.2) & (mat == 0)
    sk = np.median(Lt[near]); bb = near & (Lt < sk - 4)
    bv = np.average(v[bb], weights=area[bb]) if bb.sum() > 20 else 2.2
    bv = float(np.clip(bv, 1.7, 3.0))
    uu = (u * outer + 0.2) / 2.9                              # -1 inner end .. +1 outer tail
    ctr = bv + 0.30 * (1 - uu**2) - 0.10 * uu                 # gentle arch, tail slightly lower
    th = 0.25 * np.clip(1.1 - 0.45 * np.abs(uu + 0.25), 0.45, 1)   # half thickness, tapering
    brow = (nrm[:,1] < -0.1) & (c[:,1] < -20) & (np.abs(uu) < 1) & (np.abs(v - ctr) < th) & (mat == 0)
    mat[brow] = 1
    print('%-7s brow: band at %.2f mm above the eye, %.2f mm2 black' % (name, bv, area[brow].sum()))
np.save('materials_e.npy', mat.astype('u1'))
