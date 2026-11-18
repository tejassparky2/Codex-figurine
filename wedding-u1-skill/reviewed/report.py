from render import *
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
import zipfile,re
wd=Path.cwd();out=wd/'Wedding-color-inspection.pdf';doc=Canvas(str(out),pagesize=(960,700),pageCompression=1)
p=np.load(D/'final.npy');physical=np.load(D/'physical.npy');rgb=np.load(D/'rgb.npy')
for base,expected in [('Wedding-U1-150mm-reviewed',physical),('Wedding-150mm-reviewed-paint-guide',p)]:
 with zipfile.ZipFile(wd/(base+'.3mf')) as z:
  assert z.testzip() is None;s=z.read('3D/3dmodel.model')
  codes={v:i for i,v in enumerate([b'4',b'8',b'0C',b'1C',b'2C',b'3C',b'4C'])}
  actual=np.fromiter((codes[q[1]] for q in re.finditer(b'paint_color="([^"]+)"',s)),dtype='u1');assert np.array_equal(expected,actual)
g=physical.copy();g[(physical==0)&(c[:,2]>=36)]=4;g[(physical==1)&(c[:,2]>=76)]=5
def txt(x,y,s,sz=13):
 doc.setFillColorRGB(.10,.15,.19);doc.setFont('Helvetica',sz);doc.drawString(x,y,s)
def place(im,x,y,w,h):
 doc.drawImage(ImageReader(im),x,y,w,h,preserveAspectRatio=True,anchor='c')
def pic(i,labs):return Image.fromarray(palette[np.r_[labs,7][np.load(D/f'id{i}.npy')]])
title=['Front','Bride side, three-quarter','Bride side','Bride side, rear','Back','Groom side, rear','Groom side','Groom side, three-quarter','From above','From below']
txt(30,655,'Wedding couple | Color inspection at 150 mm',26)
txt(30,623,'Supplied four-view reference. The requested groom color is maroon and all jewelry is gold.')
place(Image.open(wd/'reference/0.png').convert('RGB'),30,315,900,290)
txt(30,279,'How to read the pages',18)
for i,s in enumerate(['Each view pairs the source texture on this mesh with the revised flat paint and the simulated U1 print.',
'The print simulation applies the two spool changes by triangle-center height. A filament swap occurs on a whole layer.',
'White bases on upper gold details, skin bases for lip paint and other differences appear in the difference maps.',
'The source and output use the same geometry and camera. The supplied photos have different poses or perspective.',
'Coverage graphs count every visible model pixel at 1000 x 1500 per camera. They measure material labels,',
'not semantic accuracy or the printer’s ability to reproduce each edge. Occluded surfaces have no photo ground truth.']):
 txt(30,246-i*24,s.replace('’',"'"),12)
doc.showPage()
names=['Gold','Red','Ivory','Maroon','Skin','Black','Lip'];stats=[]
for i,t in enumerate(title):
 j=np.load(D/f'id{i}.npy');visible=j>=0;jj=j[visible];mismatch=p[jj]!=g[jj];changed=l[jj]!=p[jj];stats.append((changed.mean(),mismatch.mean()))
 tex=Image.fromarray(np.vstack([rgb,palette[-1]])[j]);fin=pic(i,p);sim=pic(i,g)
 txt(24,658,t,25)
 for k,(im,nm) in enumerate([(tex,'Source texture'),(fin,'After hand paint'),(sim,'Two-swap print')]):
  txt(30+312*k,627,nm,15);place(im,16+312*k,145,306,465)
 txt(25,119,f'{len(jj):,} visible pixels    |    {100*changed.mean():.2f}% of visible finish labels revised    |    {100*mismatch.mean():.2f}% need paint to match the guide',13)
 total=np.bincount(p[jj],minlength=7);sx=30
 for k,num in enumerate(total):
  wid=num/len(jj)*900;doc.setFillColorRGB(*(palette[k]/255));doc.rect(sx,80,wid,16,fill=1,stroke=0);sx+=wid
 for k,num in enumerate(total):txt(25+132*k,55,f'{names[k]} {100*num/len(jj):.1f}%',11)
 doc.showPage()
 if i in (0,2,4,6):
  # Overlapping full-width crops cover each height; all viewable source pixels retained for zoom.
  for row,(y0,y1,label) in enumerate([(0,670,'Heads and face details'),(570,1110,'Jewelry, flowers, arms and cuffs'),(990,1500,'Garlands, clothing, hems and feet')]):
   txt(25,650,t+' | '+label,22); txt(25,612,'Source texture',14);txt(485,612,'Revised finishing guide',14)
   for col,im in enumerate([tex,fin]):place(im.crop((0,y0,1000,y1)),15+465*col,300,462,300)
   # Show changed pixels and spool substitutions at the same scale.
   for col,(other,label2) in enumerate([(l,'Cyan shows revised finish assignments'),(g,'Cyan shows areas requiring finish paint')]):
    arr=np.asarray(fin).copy();mask=(np.r_[p,7][j]!=np.r_[other,7][j]);arr=(arr*.39+145).astype('u1');arr[mask]=[0,127,166];txt(20+465*col,278,label2,12);place(Image.fromarray(arr).crop((0,y0,1000,y1)),15+465*col,10,462,258)
   doc.showPage()
doc.save();print('changed faces',np.sum(p!=l),'area',m.area_faces[p!=l].sum(),'paint mismatch',m.area_faces[p!=g].sum()/m.area,'views',stats)
