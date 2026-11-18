"""Single preregistered change to CIELAB metric. Use only a scratch copy of the referee."""
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sprint import GUIDE, TOOLS, evidence, gate
import subprocess
import time

work=Path(sys.argv[1]).resolve()
work.mkdir(exist_ok=True, parents=True)
out=Path(__file__).resolve().parent
program=work/'approved_match.py'
src=(TOOLS/program.name).read_text()
token='weight = np.array([.45, 1., 1.]'
assert src.count(token)==1
program.write_text(src.replace(token,'weight = np.array([.25, 1., 1.]'))
rows={'before':gate(work,'before'), 'after':gate(work,'after',program=program)}
evidence(work,list(rows),out/'comparison.jpg')
shutil.copy(TOOLS/'approved_match_selftest.py',work)
checks={}
for size in (30,1500):
    start=time.monotonic()
    with (work/f'self{size}.log').open('w') as log:
        rc=subprocess.run([sys.executable,'-I',str(work/'approved_match_selftest.py'),str(GUIDE),
                           str(work/f'self{size}'),'--patch-faces',str(size)],stdout=log,stderr=subprocess.STDOUT).returncode
    checks[size]=dict(returncode=rc,seconds=round(time.monotonic()-start,2))
(out/'results.json').write_text(json.dumps(dict(metrics=rows,selftests=checks),indent=2)+'\n')
# Supplemental ground truth: project clean triangle labels at the generator's true camera.
# This test measures classification alone, independent of optical flow and geometry mismatch.
import importlib.util
import zipfile
import cv2
import numpy as np
from PIL import Image, ImageDraw
from approved_match import Raster, classify, edges

fixture=Path(sys.argv[2]).resolve()
im=np.asarray(Image.open(fixture/'approved.png').convert('RGB'))
h,w=im.shape[:2]
mesh=np.load(fixture/'mesh.npz')
v,f=mesh['v'],mesh['f']
cam=dict(yaw=6.,pitch=4.,roll=1.,s=h*.8/np.ptp(v[:,2]),tx=w/2+7,ty=h/2-5,k=.003)
ids=Raster(v,f).ids(cam,(w,h))
labels=np.load(fixture/'clean.npy')
truth=np.where(ids>=0,labels[np.maximum(0,ids)],-1)
interior=(ids>=0)&~cv2.dilate(edges(truth).astype('uint8'),np.ones((7,7),'uint8')).astype(bool)
with zipfile.ZipFile(GUIDE) as z:
    palette=json.loads(z.read('Metadata/project_settings.config'))['filament_colour']
spec=importlib.util.spec_from_file_location('challenger',program)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
x=np.arange(w)/w
gain=.55+.45*np.clip((x-.42)/.12,0,1)
shadow=im.copy()
shadow[ids>=0]=(im*gain[None,:,None])[ids>=0].astype('uint8')
roi=interior&(x[None,:]<.42)
stats={}
sheet=Image.new('RGB',(750,500),'white')
draw=ImageDraw.Draw(sheet)
for i,(name,fn) in enumerate([('L=.45',classify),('L=.25',module.classify)]):
    predicted=fn(shadow,ids>=0,palette,{},4.,300,lambda x: None)[0]
    wrong=(predicted>=0)&(predicted!=truth)&roi
    unknown=(predicted<0)&roi
    stats[name]=dict(pixels=int(roi.sum()),wrong=int(wrong.sum()),unknown=int(unknown.sum()),
                     correct=int(((predicted==truth)&roi).sum()))
    overlay=shadow.copy()
    overlay[wrong]=[240,0,0]
    overlay[unknown]=[0,150,255]
    picture=Image.fromarray(overlay)
    picture.thumbnail((370,465))
    sheet.paste(picture,(i*375,30))
    draw.text((i*375+4,6),name+' | wrong red / ambiguous blue',fill='black')
sheet.save(out/'cast-shadow.jpg',quality=90)
(out/'results.json').write_text(json.dumps(dict(metrics=rows,selftests=checks,synthetic_shadow=stats),indent=2)+'\n')
