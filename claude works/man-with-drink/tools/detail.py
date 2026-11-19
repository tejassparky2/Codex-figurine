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
brows = win(-26, -13.5, 173.5, 179.5) | win(-6, 11.5, 176, 181.5)
cls[brows] = 0; cls[solid(brows & (L < 47))] = 1      # solid, hole-free brows with smooth edges
# Eyes are traced, not thresholded: brown iris and shadowed lid have the same texture colour.
# Coordinates are front-view mm (x, z), measured on renders/eyeR-grid.png and eyeL-grid.png.
def px(pts): return np.array([[(x-X0)*PPM, (Z1-z)*PPM] for x, z in pts], np.int32)
def curve(pts, step=.05):
    pts = np.asarray(pts, float); xs = np.arange(pts[0,0], pts[-1,0]+1e-9, step*np.sign(pts[-1,0]-pts[0,0]))
    o = np.argsort(pts[:,0]); return np.c_[xs, np.interp(xs, pts[o,0], pts[o,1])]
EYES = {  # upper lid, lower lid (both from inner->outer in increasing x), iris centre+radius, catchlight, lash tail end
 'his right': dict(up=[(-22.0,168.25),(-20.5,169.4),(-19.0,169.95),(-17.5,170.05),(-16.0,169.8),(-15.0,169.5),(-14.4,169.2)],
                   lo=[(-22.0,168.25),(-21.0,167.85),(-19.5,167.6),(-18.0,167.6),(-16.5,167.9),(-15.0,168.6),(-14.4,169.2)],
                   iris=(-18.35,168.85,2.15), glint=(-18.45,169.6,.36), tail=[(-22.0,168.25),(-23.0,167.75),(-23.6,167.35)]),
 'his left':  dict(up=[(-2.2,170.6),(-1.5,171.6),(-0.5,172.3),(1.0,172.7),(2.5,172.85),(4.0,172.7),(5.2,172.4),(6.2,172.0),(6.9,171.7)],
                   lo=[(-2.2,170.6),(-1.0,170.3),(0.5,170.05),(2.0,170.0),(3.5,170.1),(5.0,170.5),(6.2,171.1),(6.9,171.7)],
                   iris=(2.55,171.45,2.3), glint=(2.6,172.3,.36), tail=[(6.9,171.7),(8.2,171.55),(9.5,171.35)])}
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
mouth = win(-17, 7, 146.5, 153.5)
cls[mouth] = 0
cls[solid(mouth & (L > 68) & (chroma < 40), close_mm=.25, min_mm2=.3)] = 3   # teeth; lips and mouth gap stay skin
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
lab[head & (lab == 2) & ~frame & (c[:,2] < 186) & (c[:,1] < -12) & ((c[:,0] > -26) & (c[:,0] < 12))] = 0
# Re-assert the frame (including any face the vote touched).
lab[frame] = 2
# Whisky by geometry: the tumbler is hollow (inner floor z~89.5). Liquid line measured on the texture at z 97.4.
ax = np.load('glass_axis.npy'); rad = np.hypot(c[:,0]-ax[0], c[:,1]-ax[1]); nz = m.face_normals[:,2]
zone = (c[:,2] > 87.0) & (c[:,2] < 105.5) & (rad < 7.2)
# Skin specks on the glass (not the hand): small skin components inside the glass zone join the glass.
a2, b2 = m.face_adjacency.T; sk = lab == 0; e2 = sk[a2] & sk[b2]
nc2, cc2 = connected_components(coo_matrix((np.ones(e2.sum()), (a2[e2], b2[e2])), shape=(n, n)), directed=False)
skarea = np.bincount(cc2, weights=m.area_faces, minlength=nc2)
lab[zone & sk & (skarea[cc2] < 3.0)] = 2
radial = ((c[:,0]-ax[0])*m.face_normals[:,0] + (c[:,1]-ax[1])*m.face_normals[:,1]) / np.maximum(rad, 1e-6)
wall = (c[:,2] > 87.6) & (c[:,2] < 104.9) & (rad < 7.45) & (radial > 0.7) & (np.abs(nz) < 0.35) & (lab == 0)
lab[wall] = 2; zone |= wall                                          # outward-facing cylinder wall is glass, not finger
# Inside 7.32 mm of the axis is glass: seam fins and ridge specks; finger triangles that close are pressed against the glass.
inner_glass = (c[:,2] > 87.6) & (c[:,2] < 104.9) & (rad < 7.32) & np.isin(lab, [0, 4]); lab[inner_glass] = 2; zone |= inner_glass
print('glass faces recovered from skin', inner_glass.sum())
cup = zone & np.isin(lab, [2, 4])
# Owner, 2026-11-19: "for cup down fill with orange" -- the drink fills the glass from its bottom (outer base band,
# underside and inner floor) up to the liquid line; only the rim above the liquid stays silver.
drink = cup & (c[:,2] < 97.4)
lab[cup] = 2; lab[drink] = 4
lab[(lab == 4) & ~drink] = 0       # orange only where the glass rule puts it; elsewhere it is a fingertip
np.save('detail.npy', lab.astype('u1'))
print('applied', apply.sum(), {nm: int((lab == i).sum()) for i, nm in enumerate(['skin','black','silver','white','orange'])})
