"""Facial detail from the front face camera (frames hidden): brows, eyes, teeth and mouth line.
Pixel classes inside per-feature windows (mm) -> triangle labels by majority of visible pixels."""
import numpy as np, cv2, trimesh
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
X0, Z1, PPM = -30, 204, 40
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
brows = win(-25.5, -10, 175.5, 182.5) | win(-5, 13.5, 178, 184)
cls[brows] = 0; cls[solid(brows & (L < 47))] = 1      # solid, hole-free brows with smooth edges
# Eyes are traced, not thresholded: brown iris and shadowed lid have the same texture colour.
# Coordinates are front-view mm (x, z), measured on renders/eyeR-grid.png and eyeL-grid.png.
def px(pts): return np.array([[(x-X0)*PPM, (Z1-z)*PPM] for x, z in pts], np.int32)
def curve(pts, step=.05):
    pts = np.asarray(pts, float); xs = np.arange(pts[0,0], pts[-1,0]+1e-9, step*np.sign(pts[-1,0]-pts[0,0]))
    o = np.argsort(pts[:,0]); return np.c_[xs, np.interp(xs, pts[o,0], pts[o,1])]
EYES = {  # r2 model (Tripo d3a4cb08), traced on renders/eyeR-grid.png and eyeL-grid.png (60 px/mm crops of the 40 px/mm face camera)
 'his right': dict(up=[(-20.5,169.8),(-19.0,171.17),(-17.33,171.75),(-15.67,172.0),(-14.0,172.0),(-12.67,171.75),(-11.67,171.25),(-11.17,170.83)],
                   lo=[(-20.5,169.8),(-19.0,169.83),(-17.33,169.58),(-15.67,169.58),(-14.0,169.75),(-12.67,170.17),(-11.67,170.58),(-11.17,170.83)],
                   iris=(-15.55,171.05,2.4), glint=(-14.9,171.7,.36), tail=[]),
 'his left':  dict(up=[(0.17,171.75),(1.33,173.0),(2.67,173.75),(4.0,174.08),(5.33,174.17),(6.67,174.0),(8.0,173.58),(9.33,173.08),(10.33,172.67)],
                   lo=[(0.17,171.75),(1.33,171.58),(3.0,171.5),(4.67,171.5),(6.33,171.67),(7.67,172.0),(9.0,172.42),(10.33,172.67)],
                   iris=(4.8,172.85,2.6), glint=(5.25,173.65,.36), tail=[])}
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
mouth = win(-17, 11.5, 147.5, 156)
cls[mouth] = 0
# r2: the left teeth sit in shadow (L 41-51, darker than the mouth gap at 58), so teeth are TRACED as a polygon on
# renders/mouth-grid.png and intersected with low chroma (lip chroma ~50, teeth ~21-32) so the lip in front stays skin.
TEETH = [(-11.33,151.92),(-10,151.58),(-8,151.5),(-4.67,151.67),(-1.33,152.08),(2,152.67),(5,153.33),(5.3,152.6),(5,152.17),
         (3.17,151.92),(0.33,150.83),(-1.33,150.0),(-4.67,149.75),(-8,149.75),(-9.67,150.0),(-11,150.67)]
# Owner (r2 review): the lower teeth must show, as on the round-1 model. They are only tips under the upper row, ragged
# in the texture, so the whole mouth opening is white from the upper lip down to the lower-lip edge (traced on
# renders/tex-mouth-hi.png); the chroma test below keeps both lips skin. Nothing inside the mouth is black.
LOWER_LIP = [(-11.33,151.92),(-12,150.6),(-11,149.85),(-10,149.5),(-8,149.2),(-6,149.0),(-4,148.95),(-2,149.0),(0,149.15),
             (2,149.5),(4,150.1),(5.3,150.7),(5.3,152.6),(5,153.33)]
TEETH = [p for p in TEETH[:7]] + LOWER_LIP[::-1][:-1]
tpoly = np.zeros((H, W), 'u1'); cv2.fillPoly(tpoly, [px(TEETH)], 1)
cls[solid(tpoly.astype(bool) & (chroma < 40), close_mm=.3, min_mm2=.3)] = 3   # teeth and the opening between them; lips stay skin
np.save('views/face_cls.npy', cls)
# Triangle vote.
sel = (ids >= 0) & (cls >= 0); t = ids[sel]; k = cls[sel]
votes = coo_matrix((np.ones(len(t)), (t, k)), shape=(n, 4)).toarray(); tot = np.bincount(ids[ids >= 0], minlength=n)
touched = votes.sum(1) > 0; win_lab = votes.argmax(1); share = votes.max(1) / np.maximum(tot, 1)
apply = touched & (share > 0.45) & ~frame
lab[apply] = win_lab[apply]
# Mouth interior the front camera can't see (tops of the lower teeth, the gap between the rows): skin pieces fully
# enclosed by white inside the mouth box become white. Pieces touching the box edge are lips and stay skin.
mbox = (c[:,0] > -12.5) & (c[:,0] < 6.5) & (c[:,2] > 148.5) & (c[:,2] < 153.6) & (c[:,1] < -18)
a0, b0 = m.face_adjacency.T; sk = mbox & (lab == 0); e0 = sk[a0] & sk[b0]
nc0, cc0 = connected_components(coo_matrix((np.ones(e0.sum()), (a0[e0], b0[e0])), shape=(n, n)), directed=False)
edge_comp = np.zeros(nc0, bool); out_nb = (sk[a0] & ~mbox[b0]); edge_comp[cc0[a0[out_nb]]] = True; out_nb = (sk[b0] & ~mbox[a0]); edge_comp[cc0[b0[out_nb]]] = True
nonwhite_nb = np.zeros(nc0, bool); q = sk[a0] & ~sk[b0] & mbox[b0] & (lab[b0] != 3); nonwhite_nb[cc0[a0[q]]] = True; q = sk[b0] & ~sk[a0] & mbox[a0] & (lab[a0] != 3); nonwhite_nb[cc0[b0[q]]] = True
encl = sk & ~edge_comp[cc0] & ~nonwhite_nb[cc0]; lab[encl] = 3; print('mouth interior enclosed skin -> white', int(encl.sum()))
# Inside the feature windows, faces the front camera cannot see (eyelid undersides etc.) take skin unless already set.
# Elsewhere on the head black/white are not allowed: dark hair shadows -> silver/skin by neighbour vote.
head = c[:,2] > 135
stray = head & ~apply & np.isin(lab, [1, 3])
a, b = m.face_adjacency.T
for _ in range(30):
    if not stray.any(): break
    nb = np.zeros((n, 5)); ok = ~stray
    np.add.at(nb, (a[ok[b]], lab[b[ok[b]]]), 1); np.add.at(nb, (b[ok[a]], lab[a[ok[a]]]), 1)
    nb[:, [1, 3]] = 0; fix = stray & (nb.sum(1) > 0); lab[fix] = nb[fix].argmax(1); stray &= ~fix
# Eye-region silver blobs from the broad pass that the camera did not resolve -> skin.
lab[head & (lab == 2) & ~frame & (c[:,2] < 182) & (c[:,1] < -12) & ((c[:,0] > -22) & (c[:,0] < 20))] = 0
# Re-assert the frame (including any face the vote touched).
lab[frame] = 2
# Whisky by geometry: the tumbler is hollow (inner floor z~89.5). Liquid line measured on the texture at z 97.4.
ax = np.load('glass_axis.npy'); rad = np.hypot(c[:,0]-ax[0], c[:,1]-ax[1]); nz = m.face_normals[:,2]
zone = (c[:,2] > 93.0) & (c[:,2] < 111.2) & (rad < 6.2)
# Skin specks on the glass (not the hand): small skin components inside the glass zone join the glass.
a2, b2 = m.face_adjacency.T; sk = lab == 0; e2 = sk[a2] & sk[b2]
nc2, cc2 = connected_components(coo_matrix((np.ones(e2.sum()), (a2[e2], b2[e2])), shape=(n, n)), directed=False)
skarea = np.bincount(cc2, weights=m.area_faces, minlength=nc2)
lab[zone & sk & (skarea[cc2] < 3.0)] = 2
radial = ((c[:,0]-ax[0])*m.face_normals[:,0] + (c[:,1]-ax[1])*m.face_normals[:,1]) / np.maximum(rad, 1e-6)
wall = (c[:,2] > 93.0) & (c[:,2] < 111.2) & (rad < 6.45) & (radial > 0.7) & (np.abs(nz) < 0.35) & (lab == 0)
lab[wall] = 2; zone |= wall                                          # outward-facing cylinder wall is glass, not finger
# Inside 7.32 mm of the axis is glass: seam fins and ridge specks; finger triangles that close are pressed against the glass.
inner_glass = (c[:,2] > 93.0) & (c[:,2] < 111.2) & (rad < 6.0) & np.isin(lab, [0, 4]); lab[inner_glass] = 2; zone |= inner_glass
print('glass faces recovered from skin', inner_glass.sum())
cup = zone & np.isin(lab, [2, 4])
drink = cup & (c[:,2] > 95.7) & (c[:,2] < 102.3) & (rad > 5.0)   # r2: solid tumbler, whisky on the outer wall only
lab[cup] = 2; lab[drink] = 4
lab[(lab == 4) & ~drink] = 0       # orange only where the glass rule puts it; elsewhere it is a fingertip
np.save('detail.npy', lab.astype('u1'))
print('applied', apply.sum(), {nm: int((lab == i).sum()) for i, nm in enumerate(['skin','black','silver','white','orange'])})
