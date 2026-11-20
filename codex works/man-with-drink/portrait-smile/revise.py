import re, zipfile
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
import trimesh
D=Path('/dev/shm/photo-smile');src=Path('/dev/shm/smile/Man-refined-smile-220mm.3mf')
with zipfile.ZipFile(src) as a: xml=a.read('3D/3dmodel.model')
v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',xml),float)
f=np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',xml),'i4')
p=np.array(re.findall(rb'paint_color="([^"]+)"',xml)); c=v[f].mean(1)
teeth=(p==b'1C')&(c[:,2]>140)&(c[:,2]<162)
pts=v[np.unique(f[teeth])]
# Pixel coordinates from the approved 712x1600 portrait. Y increases downward.
px=np.array([306,312,317,321,328,333,335,344,352,355,358,368,375,377,382,388,391,396,400,403,407,409])
upper=np.array([546,546,546,546,546,546,545,545,545,544,543,542,540,540,539,538,537,536,535,534,533,532])
lower=np.array([550,552,554,553,554,553,555,556,555,554,554,553,550,549,549,547,545,545,543,541,541,535])
# Use individual tooth boundaries from the photograph and the previous sculpt's own upper/lower edges.
x,y,z=v.T
left,right=np.percentile(pts[:,0],[.3,99.7]); mid=(left+right)/2
u=(x-left)/(right-left)
grid=np.linspace(left,right,67)
def envelope(q):
 vals=[np.percentile(pts[abs(pts[:,0]-g)<.48,2],q) if np.any(abs(pts[:,0]-g)<.48) else np.nan for g in grid]
 ok=np.isfinite(vals); vals=gaussian_filter1d(np.interp(grid,grid[ok],np.array(vals)[ok]),1.2)
 return np.interp(x,grid,vals)
lo,hi=envelope(4),envelope(96)
h=np.maximum(hi-lo,.45);orig=(hi+lo)/2
t=np.clip(px[0]+u*(px[-1]-px[0]),px[0],px[-1])
mm=.177
top=153.8+(548-PchipInterpolator(px,upper)(t))*mm
bottom=153.8+(548-PchipInterpolator(px,lower)(t))*mm
center=(top+bottom)/2
def smooth(q):
 q=np.clip(q,0,1);return q*q*(3-2*q)
w=smooth((-y-13)/8)*smooth((22-abs(x-mid))/10)*smooth((12-abs(z-orig))/6)
dz=z-orig
# Fit the visible white band and translate surrounding lip tissue smoothly.
band=np.clip(dz/h,-.5,.5)
newz=z+w*((center-orig)+band*(top-bottom-h))
# Give each incisor a shallow three-dimensional division, with a rounded lower edge.
groove=sum(np.exp(-((t-b)/1.15)**2) for b in [320,334,355,377,391,403])
tooth_area=smooth((2.1-abs(dz))/1.25)*smooth((x-left+.1)/1.4)*smooth((right-x+.1)/1.4)
newy=y+w*(.45*groove*tooth_area + .50*np.exp(-((dz+.95*h)/.5)**2))
# Asymmetric lift at the smile corners from the same traced photo.
corner=smooth((abs(x-mid)-6)/4)
newz+=w*corner*(.4+.5*np.tanh((x-mid)/7))
out=v.copy();out[:,0]+=w*(x-mid)*.115;out[:,1]=newy;out[:,2]=newz
vs=b'<vertices>'+b''.join(('<vertex x="%.6f" y="%.6f" z="%.6f"/>'%tuple(q)).encode() for q in out)+b'</vertices>'
xml=xml[:xml.index(b'<vertices>')]+vs+xml[xml.index(b'</vertices>')+11:]
dest=D/'Man-portrait-smile-220mm.3mf'
with zipfile.ZipFile(src) as a,zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as b:
 for n in a.namelist(): b.writestr(n,xml if n.endswith('.model') else a.read(n))
with zipfile.ZipFile(dest) as a:
 assert a.testzip() is None
 buf=a.read('3D/3dmodel.model');nv=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',buf),float)
 mesh=trimesh.Trimesh(nv,f,process=False);assert mesh.is_watertight and mesh.is_volume and abs(mesh.extents[2]-220)<.001
print('Teeth span mm before/after',np.ptp(pts[:,0]),np.ptp(nv[np.unique(f[teeth]),0]))
