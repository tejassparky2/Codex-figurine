"""Per-face texture colour for printable.npz: 4 points per face, each projected onto the nearest
compatible source triangle (distance + normal agreement), UV interpolated, median of the 4 samples."""
import sys, numpy as np, trimesh
from scipy.spatial import cKDTree
glb = sys.argv[1]
z = np.load('printable.npz'); V, F = z['v'], z['f']
src = trimesh.load(glb, force='mesh', process=False)
sv = np.asarray(src.vertices, float); sv = np.c_[sv[:,0], -sv[:,2], sv[:,1]]
sv -= [(sv[:,0].max()+sv[:,0].min())/2, (sv[:,1].max()+sv[:,1].min())/2, sv[:,2].min()]; sv *= V[:,2].max()/sv[:,2].max()
sf = src.faces; uv = np.asarray(src.visual.uv, float)
img = np.asarray(src.visual.material.baseColorTexture.convert('RGB')); th, tw = img.shape[:2]
T = sv[sf]; sc = T.mean(1); n = np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
P = V[F]; pn = np.cross(P[:,1]-P[:,0], P[:,2]-P[:,0]); pn /= np.linalg.norm(pn, axis=1, keepdims=True) + 1e-12
tree = cKDTree(sc)
bary = np.array([[1/3,1/3,1/3],[.6,.2,.2],[.2,.6,.2],[.2,.2,.6]])
out = np.zeros((len(F), 4, 3), 'f4'); dist = np.zeros(len(F))
for s in range(0, len(F), 100000):
    sl = slice(s, s+100000); m = len(P[sl])
    for b, w in enumerate(bary):
        q = np.einsum('k,fkd->fd', w, P[sl])
        d, idx = tree.query(q, k=8, workers=4)
        tri = T[idx]; nn = n[idx]
        plane = np.abs(np.einsum('fkd,fkd->fk', q[:,None]-tri[:,:,0], nn))
        score = d + 0.6*plane + 0.25*(1 - np.einsum('fkd,fd->fk', nn, pn[sl]))
        best = idx[np.arange(m), score.argmin(1)]
        a, bb, c = sv[sf[best]].transpose(1,0,2)
        v0, v1, v2 = bb-a, c-a, q-a
        d00=(v0*v0).sum(1); d01=(v0*v1).sum(1); d11=(v1*v1).sum(1); d20=(v2*v0).sum(1); d21=(v2*v1).sum(1)
        den = d00*d11-d01*d01 + 1e-18; l1=(d11*d20-d01*d21)/den; l2=(d00*d21-d01*d20)/den
        L = np.clip(np.c_[1-l1-l2, l1, l2], 0, 1); L /= L.sum(1, keepdims=True)
        u = np.einsum('fk,fkd->fd', L, uv[sf[best]])
        out[sl, b] = img[np.clip(((1-u[:,1])*th).astype(int), 0, th-1), np.clip((u[:,0]*tw).astype(int), 0, tw-1)]
        if b == 0: dist[sl] = d.min(1)
    print(s, flush=True)
rgb = np.median(out, 1).astype('u1'); np.save('face_rgb.npy', rgb)
print('nearest-centroid distance mm: median %.3f  p99 %.3f  max %.3f' % (np.median(dist), np.percentile(dist, 99), dist.max()))
