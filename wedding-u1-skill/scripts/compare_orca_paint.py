"""Compare encoded facet paint on corresponding meshes, including Orca split brush strokes."""
import argparse
import csv
import sys
import zipfile
from pathlib import Path

import numpy as np
from lxml import etree


def read_mesh(path):
    result = None
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            if not member.lower().endswith('.model'):
                continue
            with archive.open(member) as stream:
                document = etree.parse(stream,etree.XMLParser(resolve_entities=False,no_network=True,collect_ids=False))
                for mesh in document.iterfind('.//{*}mesh'):
                    if result is not None:
                        raise ValueError('Expected one mesh across the project parts')
                    vertices = np.array([[float(v.get(axis)) for axis in 'xyz'] for v in mesh.find('{*}vertices')])
                    faces = mesh.find('{*}triangles')
                    indices = np.array([[int(f.get(k)) for k in ('v1','v2','v3')] for f in faces])
                    paint = [f.get('paint_color','') for f in faces]
                    result = vertices, indices, paint
                    mesh.clear()
    if result is None:
        raise ValueError('No mesh in project')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate',type=Path)
    parser.add_argument('approved',type=Path)
    parser.add_argument('--csv',type=Path,required=True)
    args = parser.parse_args()
    v, f, candidate = read_mesh(args.candidate)
    w, g, approved = read_mesh(args.approved)
    if len(f)!=len(g):
        parser.error('Face counts differ. Match the original topology first.')
    shift = v[f[0,0]] - w[g[0,0]]
    for start in range(0,len(f),40000):
        sl = slice(start,start+40000)
        if not np.allclose(v[f[sl]],w[g[sl]]+shift,atol=.0002,rtol=0):
            parser.error('Face positions or order differ; comparison stopped.')
    count = 0
    with args.csv.open('w',newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['face','local_x_mm','local_y_mm','local_z_mm','candidate_paint','approved_paint'])
        for i,(old,new) in enumerate(zip(candidate,approved)):
            if old!=new:
                writer.writerow([i,*v[f[i]].mean(axis=0).round(5),old,new])
                count+=1
    print(f'{count} encoded paint differences in {len(f)} corresponding triangles')
    return int(count>0)


if __name__=='__main__':
    sys.exit(main())
