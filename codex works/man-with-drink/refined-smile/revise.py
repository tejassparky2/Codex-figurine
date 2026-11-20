from pathlib import Path
import zipfile,re,numpy as np,trimesh
D=Path('/dev/shm/smile')
src=Path('/dev/shm/style/man-couple-style-study.3mf')
with zipfile.ZipFile(src) as a:xml=a.read('3D/3dmodel.model')
v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',xml),float)
f=np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',xml),'i4')
p=np.array(re.findall(rb'paint_color="([^"]+)"',xml));t=v[f].mean(1)
teeth=t[(p==b'1C')&(t[:,2]>135)&(t[:,2]<165)]
print(np.percentile(teeth,[0,10,50,90,100],axis=0))
for x0 in np.arange(-12,14,2):
 a=teeth[abs(teeth[:,0]-x0)<1]
 if len(a):print(x0,a.mean(0),a[:,2].ptp() if hasattr(a,'ptp') else np.ptp(a[:,2]))
def smooth(a):
 a=np.clip(a,0,1)
 return a*a*(3-2*a)
x,y,z=v.T
line=np.polyval(np.polyfit(teeth[:,0],teeth[:,2],2),np.clip(x,-13,13))
dy=z-line
w=smooth((17-abs(x+0.5))/6)*smooth((-y-15)/6)
# Close the lower opening more than the upper lip, with a continuous transition to the chin.
below=smooth((-dy+.5)/2)
shift=-dy*(.31+.38*below)*np.exp(-(dy/6.7)**2)
out=v.copy()
out[:,2]+=w*(shift-.65*np.tanh(x/7)*np.exp(-(dy/5.8)**2))
# Compress depth around the opening toward the natural arc of the teeth.
arc=np.interp(x,np.arange(-10,10,2),[-24.8,-26.5,-28,-29.6,-31.1,-31.9,-31.7,-30.5,-28.4,-25.3])
out[:,1]+=w*.48*np.exp(-(dy/3.9)**2)*(arc-y)
dest=D/'Man-refined-smile-220mm.3mf'
vs=b'<vertices>'+b''.join(('<vertex x="%.6f" y="%.6f" z="%.6f"/>'%tuple(a)).encode() for a in out)+b'</vertices>'
xml=xml[:xml.index(b'<vertices>')]+vs+xml[xml.index(b'</vertices>')+11:]
with zipfile.ZipFile(src) as a,zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as b:
 for n in a.namelist():b.writestr(n,xml if n.endswith('.model') else a.read(n))
with zipfile.ZipFile(dest) as a:
 buf=a.read('3D/3dmodel.model')
 verts=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',buf),float)
 assert a.testzip() is None and np.array_equal(np.array(re.findall(rb'paint_color="([^"]+)"',buf)),p)
 m=trimesh.Trimesh(verts,f,process=False)
 assert m.is_watertight and m.is_volume and abs(m.extents[2]-220)<.001
