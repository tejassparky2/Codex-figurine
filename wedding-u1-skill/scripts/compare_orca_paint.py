"""Compare encoded facet paint on corresponding meshes, including Orca split brush strokes."""
from array import array
import argparse
import csv
import sys
import zipfile
from pathlib import Path

import numpy as np
from xml.parsers import expat


def read_mesh(path):
    vertices = array('d')
    indices = array('I')
    paint = []
    meshes = 0
    in_mesh = False

    def start(tag, attrs):
        nonlocal meshes, in_mesh
        local = tag.rsplit('}',1)[-1]
        if local=='mesh':
            meshes += 1
            if meshes>1:
                raise ValueError('Expected exactly one mesh across project parts')
            in_mesh = True
        elif in_mesh and local=='vertex':
            vertices.extend(float(attrs[k]) for k in ('x','y','z'))
        elif in_mesh and local=='triangle':
            indices.extend(int(attrs[k]) for k in ('v1','v2','v3'))
            paint.append(attrs.get('paint_color',''))

    def end(tag):
        nonlocal in_mesh
        if tag.rsplit('}',1)[-1]=='mesh':
            in_mesh = False

    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            if member.lower().endswith('.model'):
                parser = expat.ParserCreate(namespace_separator='}')
                parser.StartElementHandler, parser.EndElementHandler = start, end
                with archive.open(member) as stream:
                    parser.ParseFile(stream)
    if not meshes or not paint:
        raise ValueError('No painted mesh triangles in project')
    return np.asarray(vertices).reshape(-1,3), np.asarray(indices).reshape(-1,3), paint


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
