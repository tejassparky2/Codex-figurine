from pathlib import Path
import numpy as np, zipfile,re
from scipy.sparse import coo_matrix
from scipy.special import expit
import trimesh
d=Path('/dev/shm/match');src=d/'Man-with-drink-220mm-U1-fit-study.3mf'; dest=Path('/dev/shm/style/man-couple-style-study.3mf')
with zipfile.ZipFile(src) as z: xml=z.read('3D/3dmodel.model')
v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',xml),float)
f=np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',xml),'i4')
codes=[b'4',b'8',b'0C',b'1C'];labels=np.array([codes.index(c) for c in re.findall(rb'paint_color="([^"]+)"',xml)])
c=v[f].mean(1); x,y,z=c.T
# Paint rounded almond eyes on the facial surface; protect the frame and all rear-facing material islands.
for ex,ez in [(-12.6,172.8),(8.4,174.6)]:
 dx=x-ex; dz=z-ez-.10*dx
 area=(abs(dx)<7.3)&(abs(dz)<5.1)&(y<-18)&(labels!=2)
 labels[area]=0
 nx=dx/6.9
 h=np.maximum(0,1-nx**2)**.72
 eye=area&(abs(nx)<1)&(dz<3.65*h)&(dz>-3.05*h)
 labels[eye]=3
 pupil=eye&(((dx-.1)/2.95)**2+((dz-.05)/3.1)**2<1)
 labels[pupil]=1
 labels[eye&(dz>3.65*h-.44)]=1
 labels[pupil&((dx+.75)**2+(dz-1.12)**2<.72**2)]=3
x,y,z=v.T.copy(); out=v.copy()
skin=np.zeros(len(v),bool); skin[np.unique(f[(c[:,2]>137)&(c[:,2]<190)&(labels!=2)&(c[:,1]<-12)])]=True
protected=np.unique(f[labels==2]);skin[protected]=False
# Fair the face surface along mesh neighbors without bridging glasses and skin.
ii=f[:,[0,1,2,1,2,0]].ravel();jj=f[:,[1,2,0,0,1,2]].ravel()
A=coo_matrix((np.ones(len(ii)),(ii,jj)),shape=(len(v),len(v))).tocsr(); denom=np.maximum(1,np.asarray(A.sum(1)).ravel())
for _ in range(16):
 avg=A@out[:,1]/denom
 out[skin,1]+=.54*(avg[skin]-out[skin,1])
# Add cheek volume and reduce the horizontal eye-fold depth underneath the larger painted eyes.
for ex,ez in [(-12.6,172.8),(8.4,174.6)]:
 dx=x-ex;dz=z-ez-.10*dx
 near=(dx/7.8)**2+(dz/4.9)**2
 core=skin&(near<1)
 around=skin&(near>1.08)&(near<2.65)&(y<-18)
 basis=np.column_stack((np.ones(len(v)),dx,dz,dx*dx,dx*dz,dz*dz))
 pred=basis[core]@np.linalg.lstsq(basis[around],out[around,1],rcond=None)[0]
 w=(1-near[core])**.75
 out[core,1]+=w*(pred-out[core,1]-1.4)
for ex in (-17.,13.):
 out[:,1]-=1.75*np.exp(-((x-ex)/10)**2-((z-159)/9)**2)*skin
# Lift corners of the smile; keep the existing teeth-only paint.
out[:,2]+=1.25*np.exp(-((abs(x-1)-8)/4.5)**2-((z-153)/4.3)**2)*skin
head=expit((z-139)/3)
out[:,0]*=1+head*(.09+.075*np.exp(-((z-154)/12)**2))
out[:,1]*=1+.045*head
out[:,2]=np.interp(out[:,2],[0,92,137,220],[0,85,130,220])
# Restore the source's continuous body and cheek contours. The earlier photographic
# outline fit created pointed shoes and a ledge along the forearm.
native=np.load('/dev/shm/drinkcheck/mesh.npz')['v']
blend=.86-.30*np.exp(-((z-173)/8)**2)
out[:,0]+=blend*(native[:,0]-v[:,0])*(1+.09*head)
out[:,2]+=.90*(native[:,2]-v[:,2])
vs=b'<vertices>'+b''.join(('<vertex x="%.6f" y="%.6f" z="%.6f"/>'%tuple(a)).encode() for a in out)+b'</vertices>'
ts=b'<triangles>'+b''.join(b'<triangle v1="%d" v2="%d" v3="%d" paint_color="%s"/>'%(a,b,c,codes[k]) for (a,b,c),k in zip(f,labels))+b'</triangles>'
xml=xml[:xml.index(b'<vertices>')]+vs+ts+xml[xml.index(b'</triangles>')+len(b'</triangles>'):]
with zipfile.ZipFile(src) as a,zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as b:
 for n in a.namelist():
  data=a.read(n)
  if n.endswith('.model'):data=xml
  if n.endswith('README.txt'):data=b'Couple-style sculpt study, 220 mm upright. Four physical head assignments retained. For visual review. Verify orientation, swap, supports and slice before use.'
  b.writestr(n,data)
m=trimesh.Trimesh(out,f,process=False)
assert m.is_watertight and m.is_volume and abs(m.extents[2]-220)<.001
