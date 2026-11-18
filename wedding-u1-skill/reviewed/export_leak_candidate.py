"""Apply changed finish labels to the reviewed wedding templates, preserving the upright two-swap map."""
import argparse
from pathlib import Path
import re
import zipfile

import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('repo',type=Path)
parser.add_argument('mesh',type=Path)
parser.add_argument('old',type=Path)
parser.add_argument('updated',type=Path)
parser.add_argument('outdir',type=Path)
args=parser.parse_args()
z=np.load(args.mesh)
before=np.load(args.old)
after=np.load(args.updated)
alphabet=[b'4',b'8',b'0C',b'1C',b'2C',b'3C',b'4C']
if before.shape!=after.shape or after.shape!=(len(z['f']),) or after.min()<0 or after.max()>=len(alphabet):
    parser.error('Invalid wedding face labels')
height=z['v'][z['f'],2].mean(1)
tools=np.array([0,1,2,3,0,1,0])[after]
tools[(after==0)&(height>=36)]=2
tools[(after==4)&(height<36)]=2
tools[(after==5)&(height<76)]=3
tools[(after==1)&(height>=76)]=3
tools[(after==1)&(height>86)]=0
args.outdir.mkdir(parents=True,exist_ok=False)
for template,output,labels in [
    ('Wedding-150mm-reviewed-paint-guide','Wedding-leak-candidate-guide',after),
    ('Wedding-U1-150mm-reviewed','Wedding-leak-candidate-U1',tools),
]:
    dst=args.outdir/(output+'.3mf')
    with zipfile.ZipFile(args.repo/(template+'.3mf')) as src, zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as out:
        for name in src.namelist():
            data=src.read(name)
            if name=='3D/3dmodel.model':
                pattern=rb'paint_color="([^"]+)"'
                old=re.findall(pattern,data)
                if len(old)!=len(labels):
                    raise ValueError('Unsupported encoding')
                if template.endswith('guide') and old!=[alphabet[k] for k in before]:
                    raise ValueError('Source labels differ from reviewed guide')
                for face in np.flatnonzero(before!=after):
                    old[face]=alphabet[labels[face]]
                codes=iter(old)
                data=re.sub(pattern,lambda _: b'paint_color="'+next(codes)+b'"',data)
            out.writestr(name,data)
    with zipfile.ZipFile(dst) as check:
        assert check.testzip() is None and re.findall(pattern,check.read('3D/3dmodel.model'))==old
