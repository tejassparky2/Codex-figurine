import sys
sys.path.insert(0,'/workspace/figurine-colorize/scripts')
import render_3mf as r, numpy as np, cv2
from pathlib import Path
m,c,_=r.load_colored_3mf(Path("wedding.3mf"))
v=m.vertices; f=m.faces
for a in [0,180]:
 s=1 if a==0 else -1
 xy=np.round(np.stack([300+s*v[:,0]*6,746-v[:,2]*6],1)).astype('int32')[f]; depth=s*v[:,1][f].mean(1)
 col=(c[:,::-1]*(.7+.3*np.clip(m.face_normals@np.array([-.3,-.8*s,.4]),0,1))[:,None]).astype('uint8').tolist()
 im=np.full((770,600,3),255,'uint8')
 for i in np.argsort(-depth): cv2.fillConvexPoly(im,xy[i],col[i])
 cv2.imwrite(f'view{a}.png',im)
