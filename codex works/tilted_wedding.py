import numpy as np,re
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Inspect the tilted wedding G-code against its reviewed upright mesh. Assumes relative extrusion, G0/G1 slicer paths and a mostly X-axis tilt.')
for arg in ('gcode','mesh','finish','physical'): parser.add_argument(arg,type=Path)
args=parser.parse_args()
obj=False;feature=''; layer=0;tool=0;absxy=True;x=y=0;out=[]
for line in open(args.gcode):
 if line.startswith('; printing object'):obj=True
 elif line.startswith('; stop printing object'):obj=False
 elif line.startswith(';TYPE:'):feature=line[6:].strip()
 elif line.startswith(';Z:'):layer+=1;z=float(line[3:])
 elif re.match(r'^T[0-3]\b',line):tool=int(line[1])
 elif line.startswith('G90'):absxy=True
 elif line.startswith('G91'):absxy=False
 elif line.startswith(('G0 ','G1 ')) and ('X' in line or 'Y' in line):
  d=dict((k,float(val)) for k,val in re.findall(r'([XYE])([-\d.]+)',line.split(';')[0]))
  xx=d.get('X',x) if absxy else x+d.get('X',0);yy=d.get('Y',y) if absxy else y+d.get('Y',0)
  if obj and feature in ('Outer wall','Overhang wall') and d.get('E',0)>0 and layer and absxy:
   out.append(((x+xx)/2,(y+yy)/2,z,layer,tool,np.hypot(x-xx,y-yy)))
  x,y=xx,yy
p=np.array(out)
m=np.load(args.mesh);c=m['v'][m['f']].mean(1);tree=cKDTree(c)
q=p[::85,:3];best=None
for angle in range(-55,56,5):
 R=Rotation.from_euler('x',angle,degrees=True).as_matrix()
 model=c[::8]@R.T;off=(p[:,:3].max(0)+p[:,:3].min(0)-model.max(0)-model.min(0))/2
 d,_=tree.query((q-off)@R);score=np.median(d)
 if best is None or score<best[0]:best=score,R,off,angle
_,R,off,angle=best
for i in range(45):
 s=(q-off)@R;d,ix=tree.query(s);keep=d<np.quantile(d,.85);A=c[ix[keep]];B=q[keep];a=A.mean(0);b=B.mean(0);u,_,vt=np.linalg.svd((A-a).T@(B-b));R=vt.T@u.T;off=b-a@R.T
print('initial',angle,'fit',Rotation.from_matrix(R).as_euler('xyz',degrees=True),off,np.quantile(d,[.5,.9]),flush=True)
sem=np.load(args.finish);physical=np.load(args.physical);d,ix=tree.query((p[:,:3]-off)@R,workers=3);ok=(d<.65)&(physical[ix]==p[:,4])&(p[:,5]<4)
for t,old,new in [(0,0,4),(1,1,5)]:
 lens=[]
 for mat in [old,new]:
  keep=ok&(p[:,4]==t)&(sem[ix]==mat);lens.append(np.bincount(p[keep,3].astype(int),p[keep,5],minlength=layer+1))
 oldlen,newlen=lens;conf=np.where((oldlen>2)&(newlen>2))[0];mis=np.cumsum(newlen)-newlen+np.sum(oldlen)-np.cumsum(oldlen)+oldlen;j=np.argmin(mis[1:])+1
 print('head',t+1,'ranges >=2mm',*[np.where(k>2)[0][[0,-1]] for k in lens],'overlap',conf[[0,-1]] if len(conf) else [],'best',j,'mm before/after',newlen[:j].sum(),oldlen[j:].sum(),'example',[(i,round(oldlen[i],1),round(newlen[i],1)) for i in conf[len(conf)//2:len(conf)//2+1]],flush=True)
