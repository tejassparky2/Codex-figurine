"""Family #00025 (Tripo A, v2 art, bumps removed), 150 mm, flat bottom (glued to a separately printed base), Snapmaker U1.
  out/Family-00025-150mm-finish-guide.3mf : 8 finish colours (after hand-painting)
  out/Family-00025-U1-150mm.3mf           : 4 heads for the whole print, no pauses
Finish: 0 skin, 1 black, 2 white, 3 navy, 4 light blue, 5 red, 6 royal blue, 7 gold.
Heads: T1 Apricot (skin), T2 Black, T3 Pure White, T4 Navy.
Printed white and hand-painted: baby's light-blue T-shirt, red bracelet beads, red bindi and forehead dot. Blue beads print navy."""
import json, re, zipfile, os, numpy as np, trimesh
MESH = os.environ.get('MESH', 'cs.npz'); NAVY = os.environ.get('NAVY', '#17254F')
z = np.load(MESH); V, F = z['v'], z['f']; lab = z['l'].astype(int)
h = V[F][:,:,2]; lo, hi = h.min(1), h.max(1)
CODES = np.array(['4', '8', '0C', '1C', '2C', '3C', '4C', '5C'])
FINISH = ['#E6BAA8', '#0E0E10', '#F1ECE1', NAVY, '#7BB7B4', '#BB1E10', '#01387B', '#EFC13A']
NAMES = ['Apricot (skin)', 'Black', 'Pure White', 'Navy (mother top)', 'Light blue (paint)', 'Red (paint)', 'Royal blue (beads)', 'Gold (paint)']
tool = np.array([0, 1, 2, 3, 2, 2, 3, 2])[lab]
TOOLS = ['#E6BAA8', '#0E0E10', '#F1ECE1', NAVY]
CT = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
      '<Default Extension="config" ContentType="text/plain"/></Types>')
RELS = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
BED = (135.0, 135.0)
def write(path, labels, colours, title, notes):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as out:
        out.writestr('[Content_Types].xml', CT); out.writestr('_rels/.rels', RELS)
        with out.open('3D/3dmodel.model', 'w') as fp:
            fp.write(('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
                      'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
                      f'<metadata name="Application">Figurine Colorize</metadata><metadata name="Title">{title}</metadata>'
                      '<resources><object id="1" type="model" name="Family 00025"><mesh><vertices>').encode())
            for i in range(0, len(V), 40000): fp.write(''.join(f'<vertex x="{a:.6f}" y="{b_:.6f}" z="{c:.6f}"/>' for a, b_, c in V[i:i+40000]).encode())
            fp.write(b'</vertices><triangles>')
            for i in range(0, len(F), 40000): fp.write(''.join(f'<triangle v1="{a}" v2="{b_}" v3="{c}" paint_color="{p}"/>' for (a, b_, c), p in zip(F[i:i+40000], CODES[labels[i:i+40000]])).encode())
            fp.write(f'</triangles></mesh></object></resources><build><item objectid="1" transform="1 0 0 0 1 0 0 0 1 {BED[0]} {BED[1]} 0"/></build></model>'.encode())
        out.writestr('Metadata/project_settings.config', json.dumps({'filament_colour': colours}))
        out.writestr('Metadata/README.txt', notes)
    with zipfile.ZipFile(path) as zz:
        assert zz.testzip() is None; s = zz.read('3D/3dmodel.model')
    vs = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>', s), float)
    fs = np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), int)
    ps = np.array(re.findall(rb'paint_color="([^"]+)"', s), 'U')
    mm = trimesh.Trimesh(vs, fs, process=False)
    assert np.array_equal(ps, CODES[labels]) and len(fs) == len(F)
    assert mm.is_watertight and mm.is_winding_consistent and mm.is_volume and np.all(np.bincount(mm.edges_unique_inverse) == 2)
    print(path, len(fs), 'faces | size', np.round(mm.extents, 2), 'mm | slots', dict(zip(colours, np.bincount(labels, minlength=len(colours)).tolist())))
area = trimesh.Trimesh(V, F, process=False).area_faces
paint = {'light blue (baby T-shirt sleeves)': lab == 4, 'red (bracelet beads, mother bindi, baby forehead dot)': lab == 5}
paint_txt = '\n'.join('  - %s: %.1f mm2' % (k, area[v].sum()) for k, v in paint.items())
paint_txt += '\n  - optional: gold on the ring finger of the mother (printed skin)'
guide_notes = ('Finish guide: the intended colours after hand-painting. Print from Family-00025-U1-150mm.3mf, not this file.\n' +
               '\n'.join(f'Slot {i+1}: {nm} {hx}' for i, (nm, hx) in enumerate(zip(NAMES, FINISH))) + '\n')
print_notes = ('Snapmaker U1 project, 150 mm tall, scale 100%. Flat bottom: glue onto the separately printed base.\n'
               f'Four heads for the whole print, no pauses: T1 Apricot #E6BAA8 (skin)  T2 Black #0E0E10  T3 Pure White #F1ECE1  T4 Navy {NAVY}\n'
               'Blue bracelet beads print navy (T4). Kaala tika on the baby cheek prints black, flat. Mother bindi and baby forehead dot print white, paint red.\n'
               'Printed white, hand-paint afterwards:\n' + paint_txt + '\n'
               'Select your real U1 printer, nozzle and PLA+ presets in Snapmaker Orca before slicing. Supports and wipe tower on white.\n')
os.makedirs('out', exist_ok=True)
np.save('out/finish_slots.npy', lab.astype('u1')); np.save('out/tool_ids.npy', tool.astype('u1'))
write('out/Family-00025-150mm-finish-guide.3mf', lab, FINISH, 'Family 00025 - finish guide', guide_notes)
write('out/Family-00025-U1-150mm.3mf', tool, TOOLS, 'Family 00025 - Snapmaker U1', print_notes)
open('out/print-notes.txt', 'w').write(print_notes); print(print_notes)
