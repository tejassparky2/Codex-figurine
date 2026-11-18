exec(open('/tmp/clean-check.py').read().split('coords=v[f]')[0])
import zipfile,json
z=v[f,2].mean(1)*1.25; x=v[f,0].mean(1)
# Heads: 1 gold then skin, 2 red then black, 3 ivory, 4 maroon.
t=np.array([0,1,3,1,0,2,2,0],dtype='u1')[l]
t[(l==0)&(z<36)]=2
t[(l==4)&(z>=36)]=2
t[(l==1)&(z<76)]=3
t[(l==3)&(z>=76)]=3
# Leave forehead marks skin-colored for hand painting; preserve turban and jewelry.
for cx,cy,rx,ry in [(175,174,4,6),(277,154,4,7)]:
 xx=216+x*4.608;yy=288-(z/1.25-60)*4.608; m=(((xx-cx)/rx)**2+((yy-cy)/ry)**2<1)&(v[f,1].mean(1)<0)&np.isin(l,[2,3,7]);t[m]=0
# Keep the tooth band white; the rose lip regions already map to skin.
out='Wedding-U1-150mm-red-maroon.3mf'
codes=['4','8','0C','1C']
with zipfile.ZipFile('Wedding-clean-details.3mf') as old,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as new:
 for k in old.namelist():
  if k.endswith('.model'):
   a=s.index(b'<vertices>');b=s.index(b'</triangles>'); 
   with new.open(k,'w') as o:
    o.write(s[:a]+b'<vertices>')
    for j in range(0,len(v),50000):o.write(''.join(f'<vertex x="{a:.5f}" y="{b:.5f}" z="{c:.5f}"/>' for a,b,c in v[j:j+50000].astype(float)*1.25).encode())
    o.write(b'</vertices><triangles>')
    for j in range(0,len(f),50000):o.write(''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{codes[i]}"/>' for (a,b,c),i in zip(f[j:j+50000],t[j:j+50000])).encode())
    o.write(s[b:])
  elif k.endswith('project_settings.config'):new.writestr(k,json.dumps({'filament_colour':['#EFC13A','#DE1508','#FFF9F0','#771020']}))
  else:new.writestr(k,old.read(k))
with zipfile.ZipFile(out) as check:
 assert check.testzip() is None
 data=check.read('3D/3dmodel.model')
 assert data.count(b'paint_color=')==len(f)
 print('dimensions',v.ptp(0)*1.25 if hasattr(v,'ptp') else np.ptp(v,axis=0)*1.25, 'max',max(map(float,re.findall(rb'<vertex [^>]+ z="([^"]+)"',data))))
