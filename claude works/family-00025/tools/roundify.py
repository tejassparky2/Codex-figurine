"""Owner 2026-11-21: "fix all eyes and colour patches, pupil should be round and equal on both eyes".
Runs on cs.npz (after contour split), writes cs_round.npz.
- Eye opening = that eye's white faces + the black iris island(s) touching them (< 12 mm2: never frame, brows, hair).
  Opening -> white. Pupil = exact black circle, SAME radius on both eyes of a person (0.38 x the smaller opening height),
  centred vertically in the opening, horizontally at the pair's mean texture gaze. Only painted inside the opening.
- Dots: red bindi (mother), red forehead dot (baby), black cheek dot (baby) as exact circles.
- Before each circle the mesh is refined locally (conforming red-green edge splits to <= HMAX) so circles read round;
  the cut itself is a marching-triangles split on a per-vertex signed distance with shared edge points (watertight)."""
import numpy as np, trimesh, sys
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pathlib import Path as _P; TK = str(_P(__file__).resolve().parents[3]/'wedding-u1-skill/toolkit/scripts'); sys.path.insert(0, TK)
from colorize_3mf import srgb_to_lab
z = np.load('cs.npz'); V = z['v'].astype(float); F = z['f'].astype(np.int64); L = z['l'].astype(int)
Lt = srgb_to_lab(np.load('face_rgb.npy').astype(float))[:, 0][z['parent']]
def mesh(): return trimesh.Trimesh(V, F, process=False)

def refine(center, rad, hmax, passes=8):
    """conforming local refinement: split every edge longer than hmax that belongs to a face within rad of center."""
    global V, F, L, Lt
    import os
    if os.environ.get("NOREFINE"): return
    for _ in range(passes):
        cen = V[F].mean(1); reg = np.linalg.norm(cen - center, axis=1) < rad
        e = [F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]
        lens = [np.linalg.norm(V[x[:, 0]] - V[x[:, 1]], axis=1) for x in e]
        mid = {}; newV = []
        big = reg & (np.maximum(np.maximum(lens[0], lens[1]), lens[2]) > hmax)    # 1-to-4 split of whole faces (no needles)
        for k in range(3):
            sel = np.flatnonzero(big)
            for fi in sel:
                a, b = F[fi, k], F[fi, (k + 1) % 3]; key = (min(a, b), max(a, b))
                if key not in mid: mid[key] = len(V) + len(newV); newV.append((V[a] + V[b]) / 2)
        if not mid: break
        V = np.vstack([V, np.array(newV)])
        keep = np.ones(len(F), bool); addF, addL, addLt = [], [], []
        def m(a, b): return mid.get((min(a, b), max(a, b)))
        lo = np.linalg.norm(cen - center, axis=1) < rad + 3 * hmax + 0.5          # neighbours of the region
        for fi in np.flatnonzero(lo):
            v0, v1, v2 = F[fi]; m01, m12, m20 = m(v0, v1), m(v1, v2), m(v2, v0)
            cnt = (m01 is not None) + (m12 is not None) + (m20 is not None)
            if cnt == 0: continue
            keep[fi] = False; lf, ltf = L[fi], Lt[fi]
            if cnt == 3: tris = [(v0, m01, m20), (m01, v1, m12), (m20, m12, v2), (m01, m12, m20)]
            else:
                # rotate so the pattern is canonical
                vs = [v0, v1, v2]; ms = [m01, m12, m20]
                if cnt == 1:
                    k = [i for i in range(3) if ms[i] is not None][0]; a, b, cc = vs[k], vs[(k+1) % 3], vs[(k+2) % 3]; mab = ms[k]
                    tris = [(a, mab, cc), (mab, b, cc)]
                else:
                    k = [i for i in range(3) if ms[i] is None][0]          # unmarked edge = (vs[k], vs[k+1]) -> rotate it to (v2, v0)
                    r = (k + 1) % 3; a, b, cc = vs[r], vs[(r+1) % 3], vs[(r+2) % 3]; mab, mbc = ms[r], ms[(r+1) % 3]
                    tris = [(mab, b, mbc), (a, mab, mbc), (a, mbc, cc)]
            for t3 in tris: addF.append(t3); addL.append(lf); addLt.append(ltf)
        F = np.vstack([F[keep], np.array(addF, np.int64)]); L = np.r_[L[keep], addL]; Lt = np.r_[Lt[keep], addLt]

def circle(center, nrm, r, label, elig, depth=1.0):
    """exact circle cut; faces flagged in elig that fall inside get label."""
    global V, F, L, Lt
    import os
    if os.environ.get("NOCIRCLE"): L[elig & (np.linalg.norm(V[F].mean(1) - center, axis=1) < r)] = label; return
    q = V - center; dn = q @ nrm; planar = np.sqrt(np.maximum((q*q).sum(1) - dn*dn, 0))
    s = planar - r; far = np.abs(dn) > depth; s[far] = np.maximum(s[far], 1.0)
    EPS = 0.012                                    # keep vertices off the circle: no needle slivers at the cut
    s = np.where(np.abs(s) < EPS, np.where(s < 0, -EPS, EPS), s)
    inside_v = s < 0; cand = np.flatnonzero(inside_v[F].any(1))
    newV = []; key = {}
    def cut(i, j):
        k = (min(i, j), max(i, j))
        if k not in key:
            t = s[i] / (s[i] - s[j]); key[k] = len(V) + len(newV); newV.append(V[i] + t * (V[j] - V[i]))
        return key[k]
    keep = np.ones(len(F), bool); addF, addL, addLt = [], [], []
    for fi in cand:
        tri = F[fi]; ins = inside_v[tri]; lab_in = label if elig[fi] else L[fi]
        if ins.all(): L[fi] = lab_in; continue
        keep[fi] = False
        lone = np.flatnonzero(ins) if ins.sum() == 1 else np.flatnonzero(~ins)
        k0 = int(lone[0]); v0, v1, v2 = tri[k0], tri[(k0+1) % 3], tri[(k0+2) % 3]
        p01, p02 = cut(v0, v1), cut(v0, v2); lone_in = bool(ins[k0])
        for t3, is_in in [((v0, p01, p02), lone_in), ((p01, v1, v2), not lone_in), ((p01, v2, p02), not lone_in)]:
            addF.append(t3); addL.append(lab_in if is_in else L[fi]); addLt.append(Lt[fi])
    if newV: V = np.vstack([V, np.array(newV)])
    F = np.vstack([F[keep], np.array(addF, np.int64).reshape(-1, 3)]); L = np.r_[L[keep], np.array(addL, int)]; Lt = np.r_[Lt[keep], np.array(addLt)]

# ---- plan the eyes on the contour-split mesh ----
m = mesh(); c = m.triangles_center; area = m.area_faces; n = len(F); ei, ej = m.face_adjacency.T
def comps(mask):
    k = mask[ei] & mask[ej]; return connected_components(coo_matrix((np.ones(k.sum()), (ei[k], ej[k])), shape=(n, n)), directed=False)[1]
cb = comps(L == 1); bigb = np.bincount(cb, weights=area * (L == 1), minlength=cb.max() + 1); cw = comps(L == 2)
EYES = {'dad': [(-30.9, 122.8), (-14.5, 119.8)], 'mom': [(14.0, 110.1), (28.5, 112.5)], 'baby': [(33.3, 72.96), (45.0, 74.1)]}
plans = []
for who, eyes in EYES.items():
    info = []
    for ex, ez in eyes:
        near = (np.hypot(c[:,0] - ex, c[:,2] - ez) < 3.2) & (c[:,1] < 0)
        white = np.isin(cw, np.unique(cw[near & (L == 2)])) & (L == 2) & near
        smallb = (L == 1) & (bigb[cb] < 12.0) & near
        touch = np.zeros(n, bool); d = (white[ei] & smallb[ej]) | (smallb[ei] & white[ej]); touch[ei[d]] = touch[ej[d]] = True
        op = white | (np.isin(cb, np.unique(cb[touch & smallb])) & smallb)
        A = area[op]; ctr = np.average(c[op], axis=0, weights=A)
        nr = np.average(m.face_normals[op], axis=0, weights=A); nr /= np.linalg.norm(nr)
        dk = op & (Lt[:n] < np.percentile(Lt[:n][op], 35)); ic = np.average(c[dk], axis=0, weights=area[dk])
        info.append(dict(op=op, ctr=ctr, nr=nr, ic=ic, A=A.sum()))
    axis = info[1]['ctr'] - info[0]['ctr']; offs = []
    for e in info:
        u = axis - (axis @ e['nr']) * e['nr']; u /= np.linalg.norm(u); v = np.cross(e['nr'], u); e['u'], e['v'] = u, v
        pv = (c[e['op']] - e['ctr']) @ v; e['H'] = np.percentile(pv, 98) - np.percentile(pv, 2); e['vmid'] = (np.percentile(pv, 98) + np.percentile(pv, 2)) / 2
        offs.append((e['ic'] - e['ctr']) @ u)
    R = 0.38 * min(e['H'] for e in info); gaze = float(np.clip(np.mean(offs), -0.6, 0.6))
    for k, e in enumerate(info):
        e['pc'] = e['ctr'] + gaze * e['u'] + e['vmid'] * e['v']; plans.append((who, k, e, R))
        print('%-4s eye %d: opening %.2f mm2, height %.2f mm -> pupil radius %.2f mm (gaze %+.2f mm)' % (who, k, e['A'], e['H'], R, gaze))
for who, k, e, R in plans: L[e['op']] = 2                      # openings -> white
for who, k, e, R in plans:                                     # round pupils
    refine(e['pc'], R + 0.45, 0.06)
    cc = V[F].mean(1); elig = (L == 2) & (np.linalg.norm(cc - e['ctr'], axis=1) < 3.2) & (cc[:,1] < 0)
    circle(e['pc'], e['nr'], R, 1, elig, depth=1.2)
# ---- dots ----
s = 150.0 / 149.5
DOTS = [('mother bindi', (19.77, -12.85, 120.23), 0.55, 5), ('baby forehead', (38.25, -41.52, 80.20), 0.45, 5), ('baby cheek', (49.56, -40.68, 67.44), 0.38, 1)]
for name, p, r, col in DOTS:
    q = np.array([p[0]*s, p[1]*s, (p[2]-0.5)*s]); q = mesh().nearest.on_surface(q[None])[0][0]
    refine(q, r + 0.5, 0.05)
    m = mesh(); cc = m.triangles_center; near = np.linalg.norm(cc - q, axis=1) < r + 0.9
    L[near & (L == col)] = 0
    nr = np.average(m.face_normals[near], axis=0, weights=m.area_faces[near]); nr /= np.linalg.norm(nr)
    circle(q, nr, r, col, (L == 0) & near, depth=0.8)
    print('%-14s circle r %.2f mm, %s' % (name, r, 'red' if col == 5 else 'black'))
m = mesh(); cnt = np.bincount(m.edges_unique_inverse)
print('faces', len(F), '| watertight', m.is_watertight, 'winding', m.is_winding_consistent, 'volume', m.is_volume, 'bodies', m.body_count, '| edges !=2:', int((cnt != 2).sum()))
assert m.is_watertight and m.is_volume and m.body_count == 1 and (cnt == 2).all()
np.savez('cs_round.npz', v=V, f=F.astype('i4'), l=L.astype('u1'))
