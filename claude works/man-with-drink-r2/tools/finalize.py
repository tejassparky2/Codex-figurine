"""Merge sub-printable paint islands (< MIN mm2) into their longest-shared-edge neighbour, report what remains.
Protected: eye/mouth details are traced on purpose (catchlights ~0.4 mm2)."""
import numpy as np, trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
MIN = 0.16
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False); c = m.triangles_center; n = len(c); area = m.area_faces
lab = np.load('leak.npy').astype(int); a, b = m.face_adjacency.T; ev = m.face_adjacency_edges; L = np.linalg.norm(m.vertices[ev[:,0]] - m.vertices[ev[:,1]], axis=1)
def comps(lab):
    same = lab[a] == lab[b]; nc, cc = connected_components(coo_matrix((np.ones(same.sum()), (a[same], b[same])), shape=(n, n)), directed=False)
    return nc, cc, np.bincount(cc, weights=area, minlength=nc)
ax = np.load('glass_axis.npy'); rad = np.hypot(c[:,0]-ax[0], c[:,1]-ax[1])
editable = (c[:,2] < 135) & ~((c[:,2] > 92) & (c[:,2] < 112) & (rad < 6.6))
order = np.argsort(np.r_[a, b], kind='stable'); src = np.r_[a, b][order]; dst = np.r_[b, a][order]
first = np.searchsorted(src, np.arange(n)); deg = np.bincount(src, minlength=n)
nb3 = np.full((n, 3), -1); k3 = np.arange(len(src)) - first[src]; ok = k3 < 3; nb3[src[ok], k3[ok]] = dst[ok]
smoothed = 0
for it in range(4):
    L3 = np.where(nb3 >= 0, lab[np.clip(nb3, 0, None)], -1)
    for k in (0, 1):                                          # skin, black only
        two = ((L3 == k).sum(1) >= 2) & (lab != k) & np.isin(lab, [0, 1]) & editable & (deg == 3)
        lab[two] = k; smoothed += int(two.sum())
print('sawtooth faces smoothed', smoothed)
# Small skin islands enclosed by silver on the head (nose-pad plates, scalp specks between hair spikes) -> silver.
nc, cc, ar = comps(lab); d = lab[a] != lab[b]; A, B = a[d], b[d]
nbs = coo_matrix((np.r_[L[d], L[d]], (np.r_[cc[A], cc[B]], np.r_[lab[B], lab[A]])), shape=(nc, 5)).toarray()
encl = (ar < 3.0) & (nbs[:, 2] > 0.8*nbs.sum(1)); tgt = encl[cc] & (lab == 0) & (c[:,2] > 135)
lab[tgt] = 2; print('enclosed skin islands -> silver', int(tgt.sum()), 'faces')
moved = 0
for it in range(6):
    nc, cc, ar = comps(lab); small = ar[cc] < MIN
    d = lab[a] != lab[b]; A, B = a[d], b[d]; rows = np.r_[cc[A], cc[B]]; nb = np.r_[lab[B], lab[A]]; ln = np.r_[L[d], L[d]]; k = small[np.r_[A, B]]
    M = coo_matrix((ln[k], (rows[k], nb[k])), shape=(nc, 5)).toarray(); new = np.where(small & (M[cc].sum(1) > 0), M.argmax(1)[cc], lab)
    step = int((new != lab).sum()); moved += step; lab = new
    if not step: break
nc, cc, ar = comps(lab)
print('faces merged', moved, '| components', nc, '| smallest island mm2 %.3f' % ar.min())
for k, nm in enumerate(['skin','black','silver','white','orange']):
    s = np.unique(cc[lab == k]); print(f'{nm:7s} {100*area[lab==k].sum()/area.sum():6.2f}% area  {len(s):4d} islands  smallest {ar[s].min():8.3f} mm2  z {c[lab==k,2].min():6.1f}..{c[lab==k,2].max():6.1f}')
# Colour lock: the geometric glasses frame is always silver, applied last so nothing can overwrite it.
# r2: the tumbler foot flares to r 6.9 mm at z 94-96, outside the glass zone, and its shadow labelled 1268 faces black.
# Nothing black is within 7.5 mm of the glass axis (the shirt is at y -12.8 there): the foot is glass.
foot = (lab == 1) & (c[:,2] > 92) & (c[:,2] < 112) & (rad < 7.5); lab[foot] = 2; print('glass foot black -> silver', int(foot.sum()))
# r2 review 5: no white below the upper teeth's bottom edge (the gap and the flattened lower-teeth patch are skin).
XS = [-12.5, -12, -8, -4, -1, 0, 1, 2, 3, 4, 5, 6.5]; ZS = [150.9, 150.4, 149.85, 149.85, 149.8, 150.42, 150.42, 150.65, 151.22, 151.6, 152.0, 152.6]
mouthbox = (c[:,0] > -13) & (c[:,0] < 7) & (c[:,2] > 147) & (c[:,2] < 154) & (c[:,1] < -18)
gapw = mouthbox & (lab == 3) & (c[:,2] < np.interp(c[:,0], XS, ZS) - 0.02)
try: gapw |= np.load('lower_teeth_patch.npy') & (lab == 3)
except FileNotFoundError: pass
lab[gapw] = 0; print('white below the upper teeth -> skin', int(gapw.sum()))
nc, cc, ar = comps(lab); wm = mouthbox & (lab == 3) & (ar[cc] < 2.0)          # specks apart from the teeth row
lab[wm] = 0; print('small white specks in the mouth -> skin', int(wm.sum()), 'faces')
frame = np.load('frame_full.npy')
# r2 review 5: stray silver on the face (e.g. a sliver under the brow end): non-frame silver pieces under 3 mm2 on the
# face take their neighbours' majority colour. The hair mass is one big piece and is unaffected.
nc, cc, ar = comps(lab); d = lab[a] != lab[b]; A, B = a[d], b[d]
nbs = coo_matrix((np.r_[L[d], L[d]], (np.r_[cc[A], cc[B]], np.r_[lab[B], lab[A]])), shape=(nc, 5)).toarray()
face_zone = (c[:,2] > 150) & (c[:,2] < 186) & (c[:,1] < -12)
stray = (lab == 2) & ~frame & face_zone & (ar[cc] < 3.0)
nb = nbs.copy(); nb[:, 2] = 0; tgt = nb.argmax(1)[cc]
ok = stray & (nb.sum(1)[cc] > 0); lab[ok] = tgt[ok]; print('stray face silver -> neighbour colour', int(ok.sum()), 'faces')
# r2: the lower bridge bar is fused into the nose at x -8.2..-6.1, so its cone thickness exceeds the wire threshold and
# a skin notch is left on the bar. Paint the bar band there by measured geometry: the bar's lower edge runs from z 171.43
# (x -8) to 171.86 (x -6), its top at ~172.65 (frame faces either side, see LEARNING-LOG r2). Generic growth was tried
# and rejected: it spread silver over the nose bridge.
x = c[:,0]; zlo = 171.86 + (x + 6) * (171.86 - 171.43) / 2
notch = (lab == 0) & (x > -8.2) & (x < -6.1) & (c[:,2] > zlo) & (c[:,2] < 172.65) & (c[:,1] < -29.6) & (c[:,1] > -31.2)
print('bridge notch faces -> frame', int(notch.sum())); frame = frame | notch; np.save('frame_final.npy', frame)
print('frame lock: faces forced silver', int((lab[frame] != 2).sum())); lab[frame] = 2
assert np.all(lab[frame] == 2)
np.save('final.npy', lab.astype('u1'))
