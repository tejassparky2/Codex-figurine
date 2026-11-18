"""Run after the reviewed replay and surface leak audit. Paths refer to those job products."""
import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import trimesh

def boundary(mesh, labels):
    a,b = mesh.face_adjacency.T
    edges = mesh.face_adjacency_edges[labels[a] != labels[b]]
    return np.linalg.norm(mesh.vertices[edges[:,0]]-mesh.vertices[edges[:,1]],axis=1).sum()

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('mesh',type=Path)
parser.add_argument('labels',type=Path,help='Leak audit finish.npy')
parser.add_argument('print_project',type=Path,help='Corresponding four-head upright candidate')
parser.add_argument('guide',type=Path)
parser.add_argument('out',type=Path)
parser.add_argument('--base-labels',type=Path,help='Finish labels of input project before contact corrections')
args=parser.parse_args()
args.out.mkdir(parents=True,exist_ok=False)
z=np.load(args.mesh);v=z['v'].copy();f=z['f'];labs=np.load(args.labels)
v[:,2]-=v[:,2].min();v*=150/v[:,2].max()
m=trimesh.Trimesh(v,f,process=False)
low=v[f,2].min(1);high=v[f,2].max(1)
base=np.load(args.base_labels) if args.base_labels else labs
keep=(high>=80)|(low<=3)
for plane in (36,76):
    keep|=(low<plane+1)&(high>plane-1)
np.save(args.out/'keep.npy',keep)
np.savez(args.out/'scaled.npz',v=v,f=f)
derived=args.out/'contours.npz'
subprocess.run([sys.executable,Path(__file__).with_name('contour_split.py'),args.out/'scaled.npz',args.labels,derived,'--keep',args.out/'keep.npy','--protect-folds','30'],check=True)
data=np.load(derived);parent=data['parent'];label=data['l'];V=np.round(data['v'],6);F=data['f']
new=trimesh.Trimesh(V,F,process=False);changed=label!=labs[parent]
assert new.is_volume and np.all(np.bincount(new.edges_unique_inverse)==2) and not np.any(changed&keep[parent])
print('Boundary mm, original and split:',boundary(m,labs),boundary(new,label),'relabeled surface mm2:',new.area_faces[changed].sum())
codes=[b'4',b'8',b'0C',b'1C',b'2C',b'3C',b'4C']
for template,name,physical in [(args.guide,'Wedding-contours-guide',False),(args.print_project,'Wedding-contours-U1',True)]:
    with zipfile.ZipFile(template) as src, zipfile.ZipFile(args.out/(name+'.3mf'),'w',zipfile.ZIP_DEFLATED) as out:
        for k in src.namelist():
            s=src.read(k)
            if k.endswith('.model'):
                prior=np.array([codes.index(q) for q in re.findall(rb'paint_color="([^"]+)"',s)])
                assert len(prior)==len(f)
                # Check face and vertex order before transferring labels.
                source_f=np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',s),int)
                source_v=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',s),float)
                assert np.array_equal(source_f,f) and np.allclose(source_v,v,rtol=0,atol=0.000002)
                h=V[F,2].mean(1)
                if physical:
                    slots=np.array([0,1,2,3,0,1,0])[label]
                    slots[(label==0)&(h>=36)]=2
                    slots[(label==4)&(h<36)]=2
                    slots[(label==5)&(h<76)]=3
                    slots[(label==1)&(h>=76)]=3
                    slots[(label==1)&(h>86)]=0
                    target=np.where(label!=base[parent],slots,prior[parent])
                else:
                    assert np.array_equal(prior,base)
                    target=label
                with out.open(k,'w') as fp:
                    fp.write(s.split(b'<vertices>')[0]+b'<vertices>')
                    for i in range(0,len(V),10000):
                        fp.write(''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x,y,z in V[i:i+10000]).encode())
                    fp.write(b'</vertices><triangles>')
                    for i in range(0,len(F),10000):
                        fp.write(b''.join(b'<triangle v1="%d" v2="%d" v3="%d" paint_color="%s"/>'%(a,b,c,codes[t]) for (a,b,c),t in zip(F[i:i+10000],target[i:i+10000])))
                    fp.write(b'</triangles>'+s.split(b'</triangles>')[1])
                continue
            out.writestr(k,s)
    with zipfile.ZipFile(args.out/(name+'.3mf')) as zz:
        assert zz.testzip() is None
        xml=zz.read('3D/3dmodel.model')
        assert np.array_equal(np.array([codes.index(q) for q in re.findall(rb'paint_color="([^"]+)"',xml)]),target)
