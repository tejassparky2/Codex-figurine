"""Glasses frame by geometry: minimum exit distance over a cone of 9 inward rays (embree). A free-standing or
half-buried 0.8 mm wire exits within ~1.2 mm in some direction; skin over the skull does not. Region: front of the
head around the glasses. Writes frame_full.npy and thickness.npy (cone-minimum thickness)."""
import numpy as np, trimesh
from scipy.spatial import cKDTree
z = np.load('printable.npz'); m = trimesh.Trimesh(z['v'], z['f'], process=False); c = m.triangles_center; nrm = m.face_normals
lab = np.load('broad.npy')
reg = np.flatnonzero((c[:,2] > 155) & (c[:,2] < 186) & (c[:,1] < 12) & (np.abs(c[:,0]) < 42))
def tangent_basis(n):
    a = np.where(np.abs(n[:, :1]) < .9, [[1., 0, 0]], [[0, 1., 0]]); t1 = np.cross(n, a); t1 /= np.linalg.norm(t1, axis=1, keepdims=True)
    return t1, np.cross(n, t1)
n = nrm[reg]; t1, t2 = tangent_basis(n); org = c[reg] - n*2e-3
dirs = [-n] + [-(np.cos(np.deg2rad(40))*n + np.sin(np.deg2rad(40))*(np.cos(k)*t1 + np.sin(k)*t2)) for k in np.linspace(0, 2*np.pi, 8, endpoint=False)]
best = np.full(len(reg), 99.)
for d in dirs:
    loc, ri, _ = m.ray.intersects_location(org, d, multiple_hits=False)
    dist = np.linalg.norm(loc - org[ri], axis=1); np.minimum.at(best, ri, dist)
thick = np.full(len(c), 99.); thick[reg] = best
seed = thick < 1.25
# keep thin faces connected (within 0.6 mm) to the main wire network; the network is the large thin cluster
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
a, b = m.face_adjacency.T; e = seed[a] & seed[b]
nc, cc = connected_components(coo_matrix((np.ones(e.sum()), (a[e], b[e])), shape=(len(c),)*2), directed=False)
size = np.bincount(cc[seed], minlength=nc); big = size >= 300
frame = seed & big[cc]
print('frame faces', frame.sum(), '| thin clusters kept', int(big.sum()), '| was skin', int((frame & (lab == 0)).sum()), '| was black', int((frame & (lab == 1)).sum()))
np.save('frame_full.npy', frame); np.save('thickness.npy', thick.astype('f4'))
import os
if os.path.exists('final.npy'): hl = np.load('final.npy').copy(); hl[frame] = 4; np.save('views/hl3.npy', hl)
