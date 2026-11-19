"""Facial detail from the front face camera (frames hidden): brows, eyes, teeth and mouth line.
Pixel classes inside per-feature windows (mm) -> triangle labels by majority of visible pixels."""
import numpy as np, cv2, trimesh
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
X0, Z1, PPM = -28, 204, 40
lab = np.load('broad.npy').copy(); ids = np.load('views/face_id.npy'); frame = np.load('frame_full.npy')
z = np.load('printable.npz'); V, F = z['v'], z['f']; m = trimesh.Trimesh(V, F, process=False); c = m.triangles_center; n = len(F)
img = np.asarray(Image.open('renders/face-tex.png').convert('RGB')); H, W = ids.shape
L, A, B = [ch.astype(float) for ch in cv2.split(cv2.cvtColor(img, cv2.COLOR_RGB2LAB))]; L *= 100/255; A -= 128; B -= 128; chroma = np.hypot(A, B)
def win(x0, x1, z0, z1):
    msk = np.zeros((H, W), bool); msk[int((Z1-z1)*PPM):int((Z1-z0)*PPM), int((x0-X0)*PPM):int((x1-X0)*PPM)] = True; return msk
cls = np.full((H, W), -1)             # -1 untouched, 0 skin, 1 black, 3 white
def solid(mask, close_mm=.35, open_mm=.15, blur_mm=.22, min_mm2=1.0):
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*int(r*PPM)+1,)*2)
    u = cv2.morphologyEx(mask.astype('u1'), cv2.MORPH_CLOSE, k(close_mm))
    nc, cc, st, _ = cv2.connectedComponentsWithStats(u); keep = np.isin(cc, [i for i in range(1, nc) if st[i, 4] > min_mm2*PPM*PPM])
    u = keep.astype('u1'); cs, _ = cv2.findContours(u, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); u = np.zeros_like(u); cv2.drawContours(u, cs, -1, 1, -1)
    u = cv2.morphologyEx(u, cv2.MORPH_OPEN, k(open_mm)); u = cv2.GaussianBlur(u.astype('f4'), (0, 0), blur_mm*PPM) > .5
    return u
brows = win(-24.5, -8, 173.3, 180) | win(-2.5, 16.5, 175.8, 182.5)   # v2 positions
cls[brows] = 0; cls[solid(brows & (L < 47))] = 1      # solid, hole-free brows with smooth edges
# Eyes are traced, not thresholded: brown iris and shadowed lid have the same texture colour.
# Coordinates are front-view mm (x, z), measured on renders/eyeR-grid.png and eyeL-grid.png.
def px(pts): return np.array([[(x-X0)*PPM, (Z1-z)*PPM] for x, z in pts], np.int32)
def curve(pts, step=.05):
    pts = np.asarray(pts, float); xs = np.arange(pts[0,0], pts[-1,0]+1e-9, step*np.sign(pts[-1,0]-pts[0,0]))
    o = np.argsort(pts[:,0]); return np.c_[xs, np.interp(xs, pts[o,0], pts[o,1])]
EYES = {  # v2 mesh, traced on renders/face-tex.png (40 px/mm, 0.5 mm grid). Lids listed in increasing x, sharing corners.
  # Round 7 (owner: "make both sides of the pupil round as in the art photo"). Measured on the art: the iris is ~45 % of
  # the eye width (~2.2x the opening height), a big circle cut by BOTH lids with its equator at mid-opening, so each side
  # is a convex arc. Tried and rejected: r 1.9 with the centre near the upper lid (sides taper into a bowl) and r 1.25
  # nearly inside the opening (a narrow square bar). Rule: r ~1.05x opening height, centre at mid-opening.
 'his right': dict(up=[(-20.1,167.7),(-19.3,168.6),(-18.5,169.25),(-17.0,169.7),(-15.0,170.0),(-13.0,170.0),(-11.5,169.9),(-10.0,169.45),(-8.8,168.9)],
                   lo=[(-20.1,167.7),(-18.5,167.85),(-17.0,167.9),(-15.0,167.8),(-13.0,167.95),(-12.0,168.3),(-11.0,168.5),(-10.0,168.75),(-8.8,168.9)],
                   iris=(-14.0,168.95,2.2), glint=(-13.75,169.4,.3), tail=[(-20.1,167.7),(-20.6,167.5)]),
 'his left':  dict(up=[(2.06,170.06),(3.0,170.9),(4.0,171.75),(5.0,172.25),(6.0,172.56),(7.5,172.65),(9.0,172.6),(10.5,172.4),(11.75,172.15),(12.3,171.9)],
                   lo=[(2.06,170.06),(3.75,170.1),(5.25,170.19),(7.0,170.38),(8.75,170.69),(10.25,171.06),(11.5,171.5),(12.3,171.9)],
                   iris=(6.8,171.3,2.1), glint=(7.4,171.95,.3), tail=[(12.3,171.9),(12.8,171.95)])}
eyes = np.zeros((H, W), bool)
for nm, e in EYES.items():
    up, lo = curve(e['up']), curve(e['lo']); opening = np.zeros((H, W), 'u1'); cv2.fillPoly(opening, [px(np.r_[up, lo[::-1]])], 1); opening = opening.astype(bool)
    xs, zs = np.meshgrid((np.arange(W)+.5)/PPM + X0, Z1 - (np.arange(H)+.5)/PPM)
    cx, cz, r = e['iris']; iris = ((xs-cx)**2 + (zs-cz)**2 < r*r) & opening
    gx, gz, gr = e['glint']; glint = (xs-gx)**2 + (zs-gz)**2 < gr*gr
    liner = np.zeros((H, W), 'u1'); band = up                                                     # lash line along the lid only, no wing
    band = np.asarray(band, float); cv2.fillPoly(liner, [px(np.r_[band, (band + [0, .40])[::-1]])], 1); liner = liner.astype(bool) & ~opening
    ring = cv2.dilate((opening | liner).astype('u1'), np.ones((25, 25), 'u1')).astype(bool)   # ~0.3 mm skin margin
    cls[ring] = 0; cls[opening] = 3; cls[iris] = 1; cls[liner] = 1; eyes |= ring      # realistic: no catchlight
mouth = win(-12, 9, 146.5, 154.5)   # v2 position
cls[mouth] = 0
# Owner round 8 ("the smile is not matching"): the sculpt and texture smile match the art, but thresholded teeth came out
# thin with a ragged lower edge. Teeth (and the whole mouth opening) are now smooth traced crescents: per column the top and
# bottom of the solid mask, each fitted with a degree-4 curve in x (pinned at the corners), filled between. Lips and the
# mouth gap are always skin: the owner chose this over a thin black lower-lip line (round 8: "I don't want black ever in
# mouth, just replace black with skin colour").
import os
def curves(mask, deg=4):
    """Top and bottom of a crescent mask per column, each fitted with a degree-`deg` curve that is pinned (weight 50)
    to the two corner points, so both curves meet and the crescent tapers to a point at each end."""
    cols = np.flatnonzero(mask.any(0))
    top = np.array([np.flatnonzero(mask[:, c])[0] for c in cols]); bot = np.array([np.flatnonzero(mask[:, c])[-1] for c in cols])
    k = max(3, len(cols) // 40); rl, rr = (top[:k] + bot[:k]).mean() / 2, (top[-k:] + bot[-k:]).mean() / 2
    x = np.r_[cols, cols[0], cols[-1]]; w = np.r_[np.ones(len(cols)), 50, 50]
    return cols[0], cols[-1], np.polyfit(x, np.r_[top, rl, rr], deg, w=w), np.polyfit(x, np.r_[bot, rl, rr], deg, w=w)
def fill(c0, c1, pt, pb, cap=None, start=None):
    out = np.zeros((H, W), bool)
    for c in range(c0, c1 + 1):
        t, b_ = np.polyval(pt, c), np.polyval(pb, c)
        if cap is not None: t = max(t, b_ - cap)          # band hugging the lower edge, thinning to the corners
        if start is not None and start[c] >= 0: t = max(t, start[c])
        if b_ > t: out[int(round(t)):int(round(b_)) + 1, c] = True
    return out
tc0, tc1, tpt, tpb = curves(solid(mouth & (L > 68) & (chroma < 40), close_mm=.25, min_mm2=.3))
teeth = fill(tc0, tc1, tpt, tpb)
cls[teeth] = 3   # teeth; lips stay skin
np.save('views/face_cls.npy', cls)
# Triangle vote.
sel = (ids >= 0) & (cls >= 0); t = ids[sel]; k = cls[sel]
votes = coo_matrix((np.ones(len(t)), (t, k)), shape=(n, 4)).toarray(); tot = np.bincount(ids[ids >= 0], minlength=n)
touched = votes.sum(1) > 0; win_lab = votes.argmax(1); share = votes.max(1) / np.maximum(tot, 1)
apply = touched & (share > 0.45) & ~frame
lab[apply] = win_lab[apply]
# Inside the feature windows, faces the front camera cannot see (eyelid undersides etc.) take skin unless already set.
# Elsewhere on the head black/white are not allowed: dark hair shadows -> silver/skin by neighbour vote.
head = c[:,2] > 140
stray = head & ~apply & np.isin(lab, [1, 3])
a, b = m.face_adjacency.T
for _ in range(30):
    if not stray.any(): break
    nb = np.zeros((n, 5)); ok = ~stray
    np.add.at(nb, (a[ok[b]], lab[b[ok[b]]]), 1); np.add.at(nb, (b[ok[a]], lab[a[ok[a]]]), 1)
    nb[:, [1, 3]] = 0; fix = stray & (nb.sum(1) > 0); lab[fix] = nb[fix].argmax(1); stray &= ~fix
# Eye-region silver blobs from the broad pass that the camera did not resolve -> skin.
lab[head & (lab == 2) & ~frame & (c[:,2] < 186) & (c[:,1] < -12) & ((c[:,0] > -26) & (c[:,0] < 17))] = 0
# Re-assert the frame (including any face the vote touched).
lab[frame] = 2
# Whisky by geometry: the tumbler is hollow (inner floor z~89.5). Liquid line measured on the texture at z 97.4.
LIQUID = 99.0   # measured on the v2 texture: whisky band ends between 98.5 and 99.5 mm
ax = np.load('glass_axis.npy'); rad = np.hypot(c[:,0]-ax[0], c[:,1]-ax[1]); nz = m.face_normals[:,2]
zone = (c[:,2] > 87.0) & (c[:,2] < 105.5) & (rad < ax[2] + .51)
# Skin specks on the glass (not the hand): small skin components inside the glass zone join the glass.
a2, b2 = m.face_adjacency.T; sk = lab == 0; e2 = sk[a2] & sk[b2]
nc2, cc2 = connected_components(coo_matrix((np.ones(e2.sum()), (a2[e2], b2[e2])), shape=(n, n)), directed=False)
skarea = np.bincount(cc2, weights=m.area_faces, minlength=nc2)
lab[zone & sk & (skarea[cc2] < 3.0)] = 2
radial = ((c[:,0]-ax[0])*m.face_normals[:,0] + (c[:,1]-ax[1])*m.face_normals[:,1]) / np.maximum(rad, 1e-6)
wall = (c[:,2] > 87.6) & (c[:,2] < 104.9) & (rad < ax[2] + .76) & (radial > 0.7) & (np.abs(nz) < 0.35) & (lab == 0)
lab[wall] = 2; zone |= wall                                          # outward-facing cylinder wall is glass, not finger
# Inside 7.32 mm of the axis is glass: seam fins and ridge specks; finger triangles that close are pressed against the glass.
inner_glass = (c[:,2] > 87.6) & (c[:,2] < 104.9) & (rad < ax[2] + .63) & np.isin(lab, [0, 4]); lab[inner_glass] = 2; zone |= inner_glass
print('glass faces recovered from skin', inner_glass.sum())
# v2 (owner round 6: "colour leaks on finger"): the old radius tolerances (tuned for v1's 6.7 mm glass) reached into
# fingers pressed against this wider glass. The glass is now defined by geometry alone: the fitted cylinder (within
# 0.25 mm of the radius, facing out) plus the underside and top discs, inside the wall's own height range. Silver or
# orange near the glass that fails this test is a finger -> skin.
r = ax[2]; radial2 = radial
wall_z = c[(np.abs(rad - r) < .25) & (radial2 > .6) & (c[:,2] > 80) & (c[:,2] < 112), 2]
GB, GT = np.percentile(wall_z, 1), np.percentile(wall_z, 99)
zin = (c[:,2] > GB - .4) & (c[:,2] < GT + .4)
inside = (rad < r - .05) & zin            # nothing but glass lies inside the glass's own radius (incl. the recessed top and rim lip)
# ...except the little finger pressing up under the base (round 7): near the base, up-facing faces, and sideways faces
# well inside the wall, belong to the finger (the solid glass bottom only faces down there).
finger_in = (rad < r - .35) & (c[:,2] < GB + .7) & (nz > -.2)   # well inside the wall only; the wall itself stays glass
# At the wall near the base, glass faces point outward (wall) or down (base edge); an up-facing, not-outward face there is
# the top of the little finger.
finger_in |= (rad >= r - .35) & (rad < r + .6) & (c[:,2] < GB + .7) & (nz > .3) & (radial2 < .3)
# ...and just outside the wall near the base nothing of the solid glass faces up: up-facing faces there are the finger
# even when they also lean outward (the up-facing ridge that IS glass sits inside the radius).
finger_in |= (rad > r) & (rad < r + .6) & (c[:,2] < GB + .7) & (nz > .3)
# Below the underside plane the glass has no up-facing surface at all: those faces are the top of the little finger.
finger_in |= (rad < r + .6) & (c[:,2] < GB - .05) & (nz > .2)
inside &= ~finger_in
# The thicker top lip and its underside ring (fingertips stop ~1.5 mm lower and reach further out).
rim_bead = (((rad < r + 1.0) & (c[:,2] > GT - 1.2)) | ((rad < r + .45) & (c[:,2] > GT - 1.8))) & (c[:,2] < GT + .6)
base_bead = (rad < r + .6) & (c[:,2] > GB - .5) & (c[:,2] < GB + .5) & (nz < -.2)   # the slightly protruding base edge
glass_geo = (inside | rim_bead | base_bead | ((rad < r + .25) & zin & (radial2 > .3))) & ~finger_in
near = (c[:,2] > GB - 4) & (c[:,2] < GT + 2) & (rad < r + 1.5)
fingers = near & ~glass_geo & np.isin(lab, [2, 4])
lab[fingers] = 0; zone = glass_geo
print(f'glass by geometry: bottom {GB:.2f} top {GT:.2f} mm, {glass_geo.sum()} faces | finger faces returned to skin {fingers.sum()}')
rim_up = rim_bead & ((nz > .3) | (radial2 > .3))  # dark texture specks on the rim, but never the shirt behind the glass
cup = zone & (np.isin(lab, [0, 2, 4]) | inside | rim_up)   # inside the radius even dark texture specks are glass
# Owner, 2026-11-19: "for cup down fill with orange" -- the drink fills the glass from its bottom (outer base band,
# underside and inner floor) up to the liquid line; only the rim above the liquid stays silver.
drink = cup & (c[:,2] < LIQUID)
lab[cup] = 2; lab[drink] = 4
lab[(lab == 4) & ~drink] = 0       # orange only where the glass rule puts it; elsewhere it is a fingertip
# Round 7: Tripo fused the little finger into the glass base, leaving long sliver triangles that bridge the two; painted by
# centroid they show as orange spikes on the finger. Majority vote over edge neighbours at the base contact: an orange
# face with >= 2 skin neighbours -> skin, a skin face inside the radius with >= 2 orange neighbours -> orange.
fa, fb = m.face_adjacency.T
base_zone = (c[:,2] > GB - .8) & (c[:,2] < GB + 1.2) & (rad > r - 2.0) & (rad < r + 1.2)
for _ in range(4):
    sk_n = np.bincount(fa[lab[fb] == 0], minlength=n) + np.bincount(fb[lab[fa] == 0], minlength=n)
    or_n = np.bincount(fa[lab[fb] == 4], minlength=n) + np.bincount(fb[lab[fa] == 4], minlength=n)
    to_skin = base_zone & (lab == 4) & (sk_n >= 2)
    to_or = base_zone & (lab == 0) & (or_n >= 2) & (rad < r - .05) & ~finger_in
    if not (to_skin.any() or to_or.any()):
        break
    lab[to_skin] = 0; lab[to_or] = 4
print('base contact slivers: orange->skin / skin->orange settled')
np.save('detail.npy', lab.astype('u1'))
print('applied', apply.sum(), {nm: int((lab == i).sum()) for i, nm in enumerate(['skin','black','silver','white','orange'])})
