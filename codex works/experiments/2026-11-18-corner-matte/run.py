"""Construct a deterministic partial view from the clean synthetic regression reference."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from white_margin import white_margin_mask
from sprint import evidence, gate
from approved_match import foreground
import numpy as np
from PIL import Image

work=Path(sys.argv[1]).resolve()
fixture=Path(sys.argv[2]).resolve()
work.mkdir(exist_ok=True, parents=True)
out=Path(__file__).resolve().parent
rgb=np.asarray(Image.open(fixture/'approved.png').convert('RGB'))
# Choose an interior foreground pixel nearest the upper left quadrant.
mask=foreground(rgb,None,None)
y,x=np.nonzero(mask)
i=np.argmin((x-rgb.shape[1]*.32)**2+(y-rgb.shape[0]*.36)**2)
x,y=int(x[i]),int(y[i])
rgb=rgb[y:,x:].copy()
art=work/'cropped.png'
Image.fromarray(rgb).save(art)
cam=json.loads((fixture/'clean/view1/camera.json').read_text())
cam['tx']-=x
cam['ty']-=y
camera=work/'camera.json'
camera.write_text(json.dumps(cam))
# The extra known-background border gives flood fill access to all four frame edges.
fixed=white_margin_mask(rgb)
maskpath=work/'mask.png'
Image.fromarray(fixed.astype('uint8')*255).save(maskpath)
rows={n:gate(work,n,art=art,camera=camera,extra=opts) for n,opts in [('before',[]),('after',['--mask',maskpath])]}
(out/'results.json').write_text(json.dumps(dict(metrics=rows,crop_origin=[x,y],raw_fg_fraction=float(foreground(rgb,None,None).mean()),padded_fg_fraction=float(fixed.mean())),indent=2)+'\n')
evidence(work,list(rows),out/'comparison.jpg')
# Check the same padding rule on the full practice portrait and both existing planted leaks.
from sprint import JUDGE, ROOT
import zipfile
from sprint import GUIDE

with zipfile.ZipFile(GUIDE) as archive:
    palette=','.join(json.loads(archive.read('Metadata/project_settings.config'))['filament_colour'])

def mask_for(image, destination):
    im=np.asarray(Image.open(image).convert('RGB'))
    m=white_margin_mask(im)
    Image.fromarray(m.astype('uint8')*255).save(destination)

path=work/'portrait-mask.png'
mask_for(JUDGE/'approved-front.png',path)
practice={n:gate(work,n,extra=opts) for n,opts in [('practice-before',[]),('practice-after',['--mask',path])]}
evidence(work,list(practice),out/'practice.jpg')
checks={}
for count in (30,1500):
    base=fixture.parent/f's{count}'
    path=work/f'full-{count}.png'
    mask_for(base/'approved.png',path)
    checks[count]={}
    for state in ('clean','leaky'):
        ref=json.loads((base/state/'view1/report.json').read_text())
        name=f'full-{count}-{state}'
        row=gate(work,name,model=base/'mesh.npz',art=base/'approved.png',camera=base/state/'view1/camera.json',
                 extra=['--mask',path,'--labels',base/f'{state}.npy','--palette',palette])
        after=json.loads((work/name/'view1/report.json').read_text())
        checks[count][state]=dict(metrics=row,identical_top_patches=after['top_patches']==ref['top_patches'],
                                  same_verdict=ref['verdict']==after['verdict'])
    evidence(work,[f'full-{count}-clean',f'full-{count}-leaky'],out/f'control-{count}.jpg')
results=json.loads((out/'results.json').read_text())
results.update(practice=practice,controls=checks)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
