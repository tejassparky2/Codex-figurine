from pathlib import Path
import zipfile,re,numpy as np,trimesh
d=Path('/dev/shm/match')
mesh=np.load(d/'fitted.npz'); v,f=mesh['v'],mesh['f']; l=np.load('/dev/shm/drinkcheck/labels.npy')
src=Path('/dev/shm/incoming.3mf'); dst=d/'Man-with-drink-220mm-U1-fit-study.3mf'
vs=b'<vertices>'+b''.join(('<vertex x="%.6f" y="%.6f" z="%.6f"/>'%tuple(x)).encode() for x in v)+b'</vertices>'
z=v[f,2]
orange=z[l==3].max();white=z[l==4].min()
assert orange<120<white
with zipfile.ZipFile(src) as a,zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as b:
 for name in a.namelist():
  data=a.read(name)
  if name.endswith('.model'):
   start=data.index(b'<vertices>');end=data.index(b'</vertices>')+11
   data=data[:start]+vs+data[end:]
  if name.endswith('README.txt'):
   data=(f'220 mm upright geometry study. Retains original four head assignments. T4 orange tops at {orange:.3f} mm; white starts at {white:.3f} mm. Manual swap at 120 mm upright only. Front photo texture is in the separate GLB, not encoded in filament paint. For inspection; slicing and printing unverified.').encode()
  b.writestr(name,data)
with zipfile.ZipFile(dst) as a, zipfile.ZipFile(src) as b:
 assert a.testzip() is None
 name='3D/3dmodel.model';s=a.read(name);old=b.read(name)
 assert s[s.index(b'</vertices>'):]==old[old.index(b'</vertices>'):]
 vs=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>',s),float)
 assert np.allclose(vs,v,atol=0.000001)
 m=trimesh.Trimesh(vs,f,process=False)
 print('Volume:',m.is_volume,'watertight:',m.is_watertight,'height:',m.extents[2],'orange top',orange,'white bottom',white)
