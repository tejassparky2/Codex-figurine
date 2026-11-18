import sys
sys.path.insert(0,'toolkit/scripts')
import render_3mf as r, numpy as np, re,zipfile,json
from pathlib import Path
m,c,p=r.load_colored_3mf(Path('first.3mf'))
lab=np.argmin(((c[:,None].astype(float)-p[None])**2).sum(2),1)
X,Y,Z=m.triangles_center.T
x=300+X*6;y=746-Z*6
# Retain raised flowers along the left outline, behind the bride's arm.
flower=(y>373)&(y<654)&(x<np.interp(y,[373,397,442,500,554,654],[147,169,169,164,151,155])) 
lab[flower & np.isin(lab,[0,6,7])]=5
pants=(x>326)&(y>633)&(y<712)&np.isin(lab,[0,6,7,5]);lab[pants]=5
# Remove intermediate brown along garment borders, shadows and hairlines.
brown=(lab==6)
lab[brown & (y<320)]=1
lab[brown & (y>=320)&(y<354)]=0
lab[brown & (y>=354)&(x>=350)&(y<632)]=2
lab[brown & (y>=354)&(x<350)&(y<700)]=3
lab[brown & (y>=700)]=2
lab[brown & (y>=354) & (y<382) & (x>200) & (x<269)]=0
lab[np.isin(lab,[0,6]) & (x>331) & (y>628) & (y<645)]=5
for cx,cy,rx,ry in [(214,288,10,12),(277,269,8,11),(359,247,9,11),(416,242,10,11)]:
 eye=((x-cx)/rx)**2+((y-cy)/ry)**2
 iris=(eye<1)&(Y<0)&np.isin(lab,[1,6])
 lab[iris]=6;lab[iris&(eye<.43)]=1
 lab[iris&(((x-cx+2.4)/2.2)**2+((y-cy+3.7)/2.2)**2<1)]=5
codes=['4','8','0C','1C','2C','3C','4C','5C']
with zipfile.ZipFile('first.3mf') as z:
 for native,path in [(False,'wedding.3mf'),(True,'Wedding-painted.3mf')]:
  with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as out:
   for k in z.namelist():
    d=z.read(k)
    if k.endswith('.model'):
     it=iter(lab)
     def sub(mt):
      i=next(it);return re.sub(rb' p1="\d+"',b'',mt[0])[:-2]+((' paint_color="%s"/>'%codes[i]) if native else (' p1="%d"/>'%i)).encode()
     d=re.sub(rb'<triangle [^>]+/>',sub,d)
     if native:
      d=re.sub(rb'<m:colorgroup.*?</m:colorgroup>',b'',d).replace(b' pid="2" pindex="0"',b'').replace(b'<resources>',b'<metadata name="Application">Figurine Colorize</metadata><resources>')
    out.writestr(k,d)
   if native:out.writestr('Metadata/project_settings.config',json.dumps({'filament_colour':['#%02X%02X%02X'%tuple(v) for v in p.astype(int)]}))
