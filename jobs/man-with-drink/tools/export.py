"""Write the finish guide (5 finish colours) and the U1 print project (4 tool IDs) as Orca paint_color 3MFs,
then re-open both archives and verify geometry and decoded paint against the arrays."""
import json, re, zipfile, numpy as np, trimesh
z = np.load('printable.npz'); V, F = z['v'], z['f']; lab = np.load('final.npy').astype(int)
CODES = np.array(['4', '8', '0C', '1C', '2C'])
FINISH = ['#E6BAA8', '#0E0E10', '#8C979D', '#F9A800', '#F1ECE1']        # Apricot, Black, Simply Silver, Orange, Pure White
NAMES = ['Apricot (skin)', 'Black', 'Simply Silver', 'Orange (whisky)', 'Pure White']
finish = np.array([0, 1, 2, 4, 3])[lab]                                 # slot order: skin, black, silver, orange, white
tools = np.array([0, 1, 2, 3, 3])[lab]                                  # T4 prints orange, then white after the swap
SWAP = 120.0
TOOLS = ['#E6BAA8', '#0E0E10', '#8C979D', '#F9A800']                    # start-of-print spools
BED = (135.0, 135.0)                                                     # Snapmaker U1 270 x 270 bed centre
CT = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
      '<Default Extension="config" ContentType="text/plain"/></Types>')
RELS = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
def write(path, labels, colours, title, notes):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as out:
        out.writestr('[Content_Types].xml', CT); out.writestr('_rels/.rels', RELS)
        with out.open('3D/3dmodel.model', 'w') as fp:
            fp.write(('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
                      'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
                      f'<metadata name="Application">Figurine Colorize</metadata><metadata name="Title">{title}</metadata>'
                      '<resources><object id="1" type="model" name="Man with drink"><mesh><vertices>').encode())
            for i in range(0, len(V), 40000): fp.write(''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{zz:.6f}"/>' for x, y, zz in V[i:i+40000]).encode())
            fp.write(b'</vertices><triangles>')
            for i in range(0, len(F), 40000): fp.write(''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{p}"/>' for (a, b, c), p in zip(F[i:i+40000], CODES[labels[i:i+40000]])).encode())
            fp.write(f'</triangles></mesh></object></resources><build><item objectid="1" transform="1 0 0 0 1 0 0 0 1 {BED[0]} {BED[1]} 0"/></build></model>'.encode())
        out.writestr('Metadata/project_settings.config', json.dumps({'filament_colour': colours}))
        out.writestr('Metadata/README.txt', notes)
    with zipfile.ZipFile(path) as zz:                                   # independent re-read
        assert zz.testzip() is None; s = zz.read('3D/3dmodel.model')
    vs = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>', s), float)
    fs = np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), int)
    ps = np.array(re.findall(rb'paint_color="([^"]+)"', s), 'U')
    mm = trimesh.Trimesh(vs, fs, process=False)
    assert np.array_equal(ps, CODES[labels]) and len(fs) == len(F)
    assert mm.is_watertight and mm.is_winding_consistent and mm.is_volume and np.all(np.bincount(mm.edges_unique_inverse) == 2)
    print(path, len(fs), 'faces | size', np.round(mm.extents, 2), 'mm | bed bounds', np.round(mm.bounds + [BED[0], BED[1], 0], 1).tolist(),
          '| slots', dict(zip(colours, np.bincount(labels, minlength=len(colours)).tolist())))
guide_notes = ('Finish guide: the intended colours, one filament slot per finish colour.\n' +
               '\n'.join(f'Slot {i+1}: {nm} {h}' for i, (nm, h) in enumerate(zip(NAMES, FINISH))) +
               '\nPrint from Man-with-drink-U1-220mm.3mf, not from this file.\n')
print_notes = ('Snapmaker U1 project, 220 mm tall, scale 100%. Four tool heads:\n'
               'T1 Apricot #E6BAA8 (skin)  T2 Black #0E0E10  T3 Simply Silver #8C979D (hair, glasses, glass)  T4 Orange #F9A800 (whisky)\n'
               f'MANUAL SWAP (not embedded): add a pause at the first layer at or above {SWAP:.2f} mm and swap T4 Orange -> Pure White #F1ECE1 '
               '(teeth, eye whites, catchlights). Orange is only used up to 97.5 mm; white starts at 147.8 mm.\n'
               'Select your real U1 printer, nozzle and PLA+ presets in Snapmaker Orca before slicing.\n')
np.save('out/finish_slots.npy', finish.astype('u1')); np.save('out/tool_ids.npy', tools.astype('u1'))
write('out/Man-with-drink-220mm-finish-guide.3mf', finish, FINISH, 'Man with drink - finish guide', guide_notes)
write('out/Man-with-drink-U1-220mm.3mf', tools, TOOLS, 'Man with drink - Snapmaker U1', print_notes)
# Swap safety: T4 carries orange below the swap and white above it, never both in one layer.
h = V[F][:,:,2]
assert h[lab == 4].max() < SWAP and h[lab == 3].min() > SWAP, 'orange/white straddle the swap height'
print('T4 orange top %.2f mm < swap %.1f mm < white bottom %.2f mm' % (h[lab == 4].max(), SWAP, h[lab == 3].min()))
