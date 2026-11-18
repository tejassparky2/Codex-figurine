from pathlib import Path
import json,zipfile,numpy as np,trimesh,re
import xml.etree.ElementTree as ET
import argparse
parser=argparse.ArgumentParser(description='Build repaired templates from extracted Snapmaker Orca 2.4.1 presets.')
parser.add_argument('profile_directory', type=Path)
D=parser.parse_args().profile_directory
def resolve(folder,name):
 j=json.loads((D/folder/(name+'.json')).read_text(encoding='utf-8-sig'));base=resolve(folder,j['inherits']) if j.get('inherits') else {}
 return base|{k:v for k,v in j.items() if k not in ('name','type','from','inherits','instantiation','setting_id','description','renamed_from','compatible_printers','version','is_custom_defined')}
machine='Snapmaker U1 (0.2 nozzle)';proc='0.08mm High Quality @Snapmaker U1 (0.2 nozzle)';fil='Generic PLA @U1 0.2 nozzle'
cfg=resolve('machine',machine)|resolve('process',proc)
for k,v in resolve('filament',fil).items():
 cfg[k]=v*4 if isinstance(v,list) and len(v)==1 else v
cfg.update(printer_settings_id=machine,print_settings_id=proc,filament_settings_id=[fil]*4,filament_colour=['#EFC13A','#DE1508','#FFF9F0','#771020'],curr_bed_type='Textured PEI Plate')
assert len(cfg['nozzle_diameter'])==4 and float(cfg['printable_height'])>=150
z=np.load('repaired-u1.npz');V=z['v'].copy();F=z['f'];V[:,2]-=V[:,2].min();V*=150/V[:,2].max()
codes=np.array(['4','8','0C','1C','2C','3C','4C'])
for name,label,conf in [('Wedding-U1-repaired-020.3mf',z['u'],cfg),('Wedding-finish-repaired.3mf',z['l'],{'filament_colour':['#EFC13A','#DE1508','#FFF9F0','#771020','#F6BCA2','#131213','#D63D4F']})]:
 with zipfile.ZipFile('Wedding-U1-150mm-material-locked.3mf') as old,zipfile.ZipFile(name,'w',zipfile.ZIP_DEFLATED) as out:
  for k in ['[Content_Types].xml','_rels/.rels']:out.writestr(k,old.read(k))
  with out.open('3D/3dmodel.model','w') as fp:
   fp.write(b'<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="1" type="model" name="Wedding couple"><mesh><vertices>')
   for i in range(0,len(V),30000):fp.write(''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x,y,z in V[i:i+30000]).encode())
   fp.write(b'</vertices><triangles>')
   for i in range(0,len(F),30000):fp.write(''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{col}"/>' for (a,b,c),col in zip(F[i:i+30000],codes[label[i:i+30000]])).encode())
   fp.write(b'</triangles></mesh></object></resources><build><item objectid="1" transform="1 0 0 0 1 0 0 0 1 135.5 136 0"/></build></model>')
  out.writestr('Metadata/project_settings.config',json.dumps(conf))
 with zipfile.ZipFile(name) as zz:
  assert zz.testzip() is None
  s=zz.read('3D/3dmodel.model')
  vs=np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>',s),float)
  fs=np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',s),int)
  m=trimesh.Trimesh(vs,fs,process=False)
  assert m.is_volume and m.is_watertight and m.is_winding_consistent and np.all(np.bincount(m.edges_unique_inverse)==2)
  assert len(np.unique(vs,axis=0))==len(vs)
  assert np.array_equal(np.array(re.findall(rb'paint_color="([^"]+)"',s),'U'),codes[label])
  print(name,len(fs),m.extents, m.bounds+np.array([135.5,136,0]),flush=True)
