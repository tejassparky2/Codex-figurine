"""Printed eye construction (owner rule): the eye opening is a white socket, a round black iris sits where the texture's
iris is, and a thin black lash line runs along the upper lid. Brows: faces in a band above each eye that are clearly
darker than the surrounding skin in the texture become black (her brows are light brown, the label passes lost them).
Works in each eye's own 2-D frame (u along the eye axis, v up), front-facing faces only.
reads materials_f.npy, writes materials_e.npy"""
import numpy as np, trimesh
from pathlib import Path as _P; import sys; TK = str(_P(__file__).resolve().parents[3]/'wedding-u1-skill/toolkit/scripts'); sys.path.insert(0, TK)
from colorize_3mf import srgb_to_lab
z = np.load('printable.npz'); V, F = z['v'], z['f']; m = trimesh.Trimesh(V, F, process=False)
c = m.triangles_center; nrm = m.face_normals; area = m.area_faces
mat = np.load('materials_f.npy').astype(int).copy()
Lt = srgb_to_lab(np.load('face_rgb.npy').astype(float))[:,0]
# eye centre (x, z), axis angle (deg, + = rising to image right), half width, half height of the opening (mm)
EYES = [dict(n='him R', x=-8.37, z=136.13, ang=-5.5, hw=1.65, hh=0.50),
        dict(n='him L', x=-1.96, z=135.51, ang=-5.5, hw=1.40, hh=0.48),
        dict(n='her R', x=2.75, z=119.84, ang=22.4, hw=1.05, hh=0.42),
        dict(n='her L', x=7.42, z=121.76, ang=22.4, hw=1.45, hh=0.48)]
front = (nrm[:,1] < -0.15) & (c[:,1] < 0)
for e in EYES:
    t = np.deg2rad(e['ang']); ax, up = np.array([np.cos(t), np.sin(t)]), np.array([-np.sin(t), np.cos(t)])
    d = np.c_[c[:,0]-e['x'], c[:,2]-e['z']]; u, v = d @ ax, d @ up
    near = front & (np.abs(u) < e['hw'] + 1.5) & (v > -e['hh'] - 1.2) & (v < e['hh'] + 3.0)
    yloc = np.median(c[near & (np.abs(u) < e['hw']) & (np.abs(v) < e['hh']), 1]); near &= np.abs(c[:,1] - yloc) < 2.0
    # opening: the eye-like faces (black/white labels, or dark/bright texture) inside an almond around the centre
    alm = (u / e['hw'])**2 + (v / (e['hh'] * (1 - 0.35*(u/e['hw'])**2)))**2 < 1.15
    eyeish = np.isin(mat, [1, 3]) | (Lt < 45) | (Lt > 72)
    op = near & alm & eyeish
    # fill the almond core so the socket is solid
    op |= near & ((u / e['hw'])**2 + (v / e['hh'])**2 < 0.55)
    # iris centre: darkest texture inside the opening
    ins = np.flatnonzero(op); dk = ins[Lt[ins] < np.percentile(Lt[ins], 30)]
    iu, iv = np.average(u[dk], weights=area[dk]), np.average(v[dk], weights=area[dk])
    iu = np.clip(iu, -e['hw'] + e['hh'], e['hw'] - e['hh']); R = e['hh'] * 0.98
    iris = op & ((u - iu)**2 + (v - iv*0.3)**2 < R**2)
    # upper lash line: within 0.20 mm of the opening's top edge at each u
    bins = np.round(u[op] / 0.15).astype(int); top = {}
    for b, vv in zip(bins, v[op]): top[b] = max(top.get(b, -9), vv)
    tb = np.array([top.get(b, -9) for b in np.round(u / 0.15).astype(int)])
    lash = op & (v > tb - 0.20)
    mat[op] = 3; mat[iris] = 1; mat[lash] = 1
    # lower-lid and corner dark faces just outside the socket go back to skin (no black rims below the eye)
    rim = near & ~op & (mat == 1) & (v < 0.6 * e['hh']) & (np.abs(u) < e['hw'] + 0.6) & (v > -e['hh'] - 0.8)
    mat[rim] = 0
    # brow: darker-than-skin band above the eye
    band = near & (v > e['hh'] + 0.45) & (v < e['hh'] + 2.6) & (np.abs(u) < e['hw'] + 0.9) & np.isin(mat, [0, 1])
    sk = np.median(Lt[band & (mat == 0)]) if (band & (mat == 0)).any() else 70
    if e['n'].startswith('her'):
        # her brows are faint in the texture: draw a solid arc where the texture's darker band is
        bb = band & (Lt < sk - 6); bv = np.average(v[bb], weights=area[bb]) if bb.any() else e['hh'] + 1.4
        uu = u / (e['hw'] + 0.7); ctr = bv + 0.25 * (1 - uu**2) - 0.15*uu        # gentle arch, tail slightly lower
        th = 0.26 * np.clip(1.15 - 0.6*np.abs(uu + 0.2), 0.35, 1)                  # half thickness, tapering to the tail
        brow = near & (np.abs(uu) < 1) & (np.abs(v - ctr) < th) & np.isin(mat, [0, 1])
        mat[band & (mat == 1)] = 0
    else:
        brow = band & (Lt < sk - 9)
        mat[band & ~brow & (mat == 1) & (Lt > sk - 4)] = 0
    mat[brow] = 1
    print('%-6s socket %.2f mm2, iris %.2f mm2 at u %.2f, lash %.2f mm2, brow %.2f mm2 (skin L %.0f)' % (
        e['n'], area[op].sum(), area[iris].sum(), iu, area[lash].sum(), area[brow].sum(), sk))
# his closed smile: no white/cream specks on the mouth
mouth = (c[:,1] < -5) & (c[:,0] > -12.5) & (c[:,0] < 0) & (c[:,2] > 127.0) & (c[:,2] < 131.0) & np.isin(mat, [3, 7])
mat[mouth] = 0; print('his mouth specks -> skin:', int(mouth.sum()))
np.save('materials_e.npy', mat.astype('u1'))
