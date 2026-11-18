"""Provisional per-face colour classes from the UV texture, and their height ranges at a target height."""
import sys, numpy as np, trimesh, cv2
H=float(sys.argv[2]) if len(sys.argv)>2 else 150
s=trimesh.load(sys.argv[1],process=False); m=s.to_geometry() if isinstance(s,trimesh.Scene) else s
v=np.asarray(m.vertices); f=m.faces; v=v-[ (v[:,0].max()+v[:,0].min())/2, v[:,1].min(), (v[:,2].max()+v[:,2].min())/2]; v*=H/v[:,1].max()
c=v[f].mean(1); area=trimesh.triangles.area(v[f])
# Area-weighted texture sample: 4 points per face (centroid + 3 inner points) to avoid seam outliers.
uvf=m.visual.uv[f]; img=np.asarray(m.visual.material.baseColorTexture.convert('RGB')); h,w=img.shape[:2]
def samp(uv): return img[np.clip(((1-uv[:,1])*h).astype(int),0,h-1),np.clip((uv[:,0]*w).astype(int),0,w-1)].astype('f4')
bary=np.array([[1/3,1/3,1/3],[.6,.2,.2],[.2,.6,.2],[.2,.2,.6]])
rgb=np.median(np.stack([samp(np.einsum('k,fkd->fd',b,uvf)) for b in bary]),0)
np.save('face_rgb.npy',rgb.astype('u1')); np.savez('mm150.npz',v=v.astype('f4'),f=f)
lab=cv2.cvtColor((rgb/255).reshape(-1,1,3).astype('f4'),cv2.COLOR_RGB2LAB).reshape(-1,3)
pal={'skin':[245,140,70],'black':[25,22,20],'charcoal':[60,55,50],'hair grey':[140,135,130],'hair light':[205,200,195],'brass frame':[160,135,90],'amber':[200,130,40],'white':[240,238,230]}
P=cv2.cvtColor((np.array(list(pal.values()),'f4')/255).reshape(-1,1,3),cv2.COLOR_RGB2LAB).reshape(-1,3)
k=np.argmin(((lab[:,None]-P[None])**2*[.5,1,1]).sum(2),1)
print(f'model {np.ptp(v,0).round(1)} mm  faces {len(f)}  surface {area.sum():.0f} mm2')
for i,n in enumerate(pal):
    s=k==i; z=c[s,1]
    if s.sum()==0: continue
    print(f'{n:12s} {100*area[s].sum()/area.sum():5.1f}% area  z {np.percentile(z,1):6.1f}..{np.percentile(z,99):6.1f} mm  (min {z.min():.1f} max {z.max():.1f})')
np.save('provisional_labels.npy',k.astype('u1'))
