"""Intersect exact edited triangles with referee patches at fixed camera."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sprint import CAMERA, GUIDE, JUDGE, ROOT, evidence, gate
from approved_match import Raster, load_model
import numpy as np
from PIL import Image

work=Path(sys.argv[1])
work.mkdir(exist_ok=True, parents=True)
out=Path(__file__).resolve().parent
candidate=ROOT/'Wedding-leak-candidate-guide.3mf'
rows={n:gate(work,n,m) for n,m in [('before',GUIDE),('after',candidate)]}
v,f,old,_=load_model(GUIDE)
v2,f2,new,_=load_model(candidate)
assert np.array_equal(v,v2) and np.array_equal(f,f2)
edits=np.flatnonzero(old!=new)
with np.load(ROOT/'Wedding-leak-findings.npz') as data:
    assert np.array_equal(edits,data['face'][data['applied'].astype(bool)])
cam=json.loads(CAMERA.read_text())
ids=Raster(v,f).ids(cam,Image.open(JUDGE/'approved-front.png').size)
visible=np.intersect1d(ids,edits)
result=dict(metrics=rows, changed=len(edits), visible=len(visible), unobserved=len(edits)-len(visible))
for name in rows:
    with np.load(work/name/'view1/patch_faces.npz') as patches:
        overlap={k:np.intersect1d(edits,patches[k]) for k in patches.files if k.startswith('patch_')}
    hits=[a for a in overlap.values() if len(a)]
    result[name]=dict(unique_edited_faces=len(np.unique(np.concatenate(hits))) if hits else 0,
                      patch_hits={k:len(a) for k,a in overlap.items() if len(a)})
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
evidence(work,list(rows),out/'comparison.jpg')
# Red in the lossless fourth panel is the gate's hard pixel mask (approved_match.run_view).
# Painting influences the gate's optical flow and boundary band even on unchanged triangles.
hard=[]
for name in rows:
    panels=np.asarray(Image.open(work/name/'view1/side_by_side.png'))
    hard.append(np.all(panels[:,-ids.shape[1]:]==[230,0,0],axis=2))
changed_pixel=np.isin(ids,edits)
result['pixel_transitions']={}
for name,region in [('edited',changed_pixel),('other',~changed_pixel)]:
    result['pixel_transitions'][name]=dict(new_hard=int(np.sum(~hard[0]&hard[1]&region)),
                                          resolved_hard=int(np.sum(hard[0]&~hard[1]&region)))
result['edited_slot_transitions']={}
for a,b in sorted(set(zip(old[edits],new[edits]))):
    faces=edits[(old[edits]==a)&(new[edits]==b)]
    result['edited_slot_transitions'][f'{a+1} to {b+1}']=dict(total=len(faces),visible=len(np.intersect1d(visible,faces)))
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
# Show the largest localized increase on an actually edited surface, in the same pixel coordinates.
import cv2
direct=(~hard[0]&hard[1]&changed_pixel).astype('uint8')
_,_,regions,_=cv2.connectedComponentsWithStats(direct,8)
if len(regions)>1:
    x,y,w,h,_=max(regions[1:],key=lambda r:r[-1])
    evidence(work,list(rows),out/'edited-crop.jpg',[int(e) for e in (x,y,w,h)])
else:
    # No hard pixel transitioned directly on an edit. Show the densest visible edit neighborhood.
    window=cv2.boxFilter(changed_pixel.astype('float32'),-1,(49,49),normalize=False)
    y,x=np.unravel_index(np.argmax(window),window.shape)
    evidence(work,list(rows),out/'edited-crop.jpg',[max(0,int(x)-24),max(0,int(y)-24),49,49])
result['rigid_control']={name:gate(work,name,model,extra=['--local-align-mm','0'])
                         for name,model in [('rigid-before',GUIDE),('rigid-after',candidate)]}
evidence(work,list(result['rigid_control']),out/'rigid.jpg')
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
