from render import *
import zipfile,json,re
wd=Path.cwd()
p=np.load(D/'final.npy')
# Enforce four physical tool assignments; when the target pigment is unavailable, preserve existing paint plan on unchanged faces.
h=c[:,2];physical=np.array([0,1,2,3,0,1,0])[p]
physical[(p==0)&(h>=36)]=2;physical[(p==4)&(h<36)]=2;physical[(p==5)&(h<76)]=3;physical[(p==1)&(h>=76)]=3
physical[(p==1)&(h>86)]=0
# Preserve legitimate established forehead/face paint bases.
physical[(p==l)&(p==1)&(h>76)&(u==0)]=0
codes=np.array(['4','8','0C','1C','2C','3C','4C'],dtype='S2')
for src,new,labels in [('Wedding-U1-repaired-020','Wedding-U1-150mm-reviewed','print'),('Wedding-finish-repaired','Wedding-150mm-reviewed-paint-guide','guide')]:
 with zipfile.ZipFile(wd/(src+'.3mf')) as zz,zipfile.ZipFile(wd/(new+'.3mf'),'w',zipfile.ZIP_DEFLATED) as out:
  for k in zz.namelist():
   s=zz.read(k)
   if k.endswith('.model'):
    old=re.findall(b'paint_color="([^"]+)"',s);labs=codes[physical if labels=='print' else p];assert len(old)==len(labs);it=iter(labs);s=re.sub(b'paint_color="[^"]+"',lambda _:b'paint_color="'+next(it)+b'"',s)
   out.writestr(k,s)
np.save(D/'physical',physical)
