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
cent=v[f].mean(1)
px=216+cent[:,0]*4.608
py=288-(cent[:,2]-60)*4.608
# Confine this correction to the upper hair above the bride's forehead ornament.
crown=(px<206)&(py<np.interp(px,[35,70,95,122,152,173,191,206],[158,156,148,140,132,134,141,144]))&(z>=76)
t[crown&(t==0)]=1
# Remove burgundy and stray scarlet pigment on the face around the hand-painted smile.
brideLip=(((px-186)/25)**2+((py-246)/14)**2<1)&(cent[:,1]<0)
t[brideLip&(t==3)]=0
# Restore bright sari red wherever maroon shadow pixels strayed into the bride's sleeve.
sleeve=(px>116)&(px<171)&(py>300)&(py<348)&(cent[:,1]<0)
t[sleeve&(t==3)]=1
# Clean pigment along the outer edge of the bride's bead chain using its traced path.
u=px*2.5-75;w=py*2.5-265
chain=np.interp(w,[96,120,150,180,209,243,267,300,327],[296,252,223,198,170,145,119,95,80])
edge=(cent[:,1]<0)&(w>=96)&(w<328)&(u<chain-4)&(u>chain-18)&(t==0)
t[edge]=1
for cx,cy,rx,ry in [(626,24,45,47),(189,401,22,27)]:
 ornament=((u-cx)/rx)**2+((w-cy)/ry)**2<1
 t[ornament&(t==0)&(cent[:,1]<0)]=2
# Repaint pupil centers in normalized coordinates of the individual eye openings.
# Reference gaze fractions measured on the maroon portrait, in screen left-to-right order.
for name,frac,radius in [('Bride left',.407,.31),('Bride right',.32,.34),('Groom left',.665,.35),('Groom right',.504,.30)]:
 ids=np.load('/tmp/detail-regions.npz')[name]
 u=px[ids];w=py[ids];lo,hi=np.percentile(u,[.1,99.9]);top,bot=np.percentile(w,[.1,99.9]);width=hi-lo;height=bot-top
 cx=lo+width*frac;cy=top+height*.54
 iris=((u-cx)/(width*radius))**2+((w-cy)/(height*.49))**2<1
 glint=(((u-cx)/height+.085)**2+((w-cy)/height+.148)**2)<.090**2
 t[ids]=2;t[ids[iris]]=1;t[ids[iris&glint]]=2
 assert set(t[ids])=={1,2} and z[ids].min()>76
print('crown skin triangles remaining',sum(crown&(t==0)))

# Keep the tooth band white; the rose lip regions already map to skin.
out='Wedding-U1-150mm-gaze-corrected.3mf'
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
