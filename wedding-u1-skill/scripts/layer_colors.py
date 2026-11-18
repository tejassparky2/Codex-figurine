"""Count finish colors intersecting each height band of a single, upright Orca-painted mesh."""
import argparse
import csv
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('guide', type=Path)
parser.add_argument('--band-mm', type=float, default=0.2)
parser.add_argument('--heads', type=int, default=4)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not math.isfinite(args.band_mm) or args.band_mm <= 0 or args.heads < 1:
    parser.error('Provide a positive band size and head count.')
with zipfile.ZipFile(args.guide) as archive:
    root = ET.fromstring(archive.read('3D/3dmodel.model'))
items = root.findall('{*}build/{*}item')
objects = root.findall('{*}resources/{*}object')
if root.get('unit', 'millimeter') != 'millimeter' or len(items) != 1 or len(objects) != 1:
    parser.error('Use one instance of one millimeter mesh.')
item = items[0]
transform = np.fromstring(item.get('transform','1 0 0 0 1 0 0 0 1 0 0 0'), sep=' ').reshape(4,3)
mesh = objects[0].find('{*}mesh')
if mesh is None or item.get('objectid') != objects[0].get('id'):
    parser.error('Export a single mesh with one build item.')
vertices = np.asarray([[float(v.attrib[k]) for k in ('x','y','z')] for v in mesh.find('{*}vertices')])
z = vertices @ transform[:3,2] + transform[3,2]
faces = mesh.find('{*}triangles')
indices = np.asarray([[int(face.attrib[k]) for k in ('v1','v2','v3')] for face in faces])
labels = [face.get('paint_color','') for face in faces]
known = ['4','8','0C','1C','2C','3C','4C','5C']
if set(labels) - set(known):
    parser.error('This reader handles solid per-triangle Orca paint codes for slots 1 through 8.')
if z.min() < -0.001:
    parser.error('Place the model on the bed before measuring layer bands.')
bands = max(1, math.ceil(z.max()/args.band_mm))
lo = np.clip(np.floor(z[indices].min(1)/args.band_mm).astype(int),0,bands-1)
hi = np.clip(np.ceil(z[indices].max(1)/args.band_mm).astype(int)-1,lo,bands-1)
colors, code = np.unique(labels,return_inverse=True)
counts = np.zeros((bands+1,len(colors)),int)
np.add.at(counts,(lo,code),1)
np.add.at(counts,(hi+1,code),-1)
with args.output.open('w',newline='') as out:
    writer=csv.writer(out)
    writer.writerow(['bottom_mm','top_mm','finish_slots_1_based','color_count','over_head_count'])
    for i,row in enumerate(counts.cumsum(0)[:-1]):
        slots=sorted(known.index(k)+1 for k in colors[row>0])
        writer.writerow([round(i*args.band_mm,5),round((i+1)*args.band_mm,5),
                         ' '.join(map(str,slots)),len(slots),int(len(slots)>args.heads)])
