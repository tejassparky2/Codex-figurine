"""Couple (army officer + doctor), 150 mm, Snapmaker U1. Writes:
  out/Couple-army-doctor-150mm-finish-guide.3mf : 8 finish colours (what it looks like after hand-painting)
  out/Couple-army-doctor-U1-150mm.3mf           : 4 tool heads, as printed (3 pauses), Orca paint_color codes
then re-opens both and checks geometry and decoded paint, and asserts every swap is clean.
Finish: 0 skin, 1 black, 2 green, 3 white, 4 yellow, 5 gold, 6 red, 7 silver.
Heads at start: T1 Pure White, T2 Yellow, T3 Black, T4 Apricot.
  pause S1: T1 white -> green;  pause S2: T3 black -> white;  pause S3: T2 yellow -> black.
Printed white and hand-painted: gold (buttons, stars), red (dress buttons), silver (stethoscope), yellow above S3."""
import json, re, zipfile, os, numpy as np, trimesh
MESH = os.environ.get('MESH', 'cs.npz'); GREEN = os.environ.get('GREEN', '#2E4A2C')
S1, S2, S3 = 6.9, 12.0, 88.3
GAP = 0.25                                                     # every colour clears its pause by >= 0.25 mm (a layer either side)
z = np.load(MESH); V, F = z['v'], z['f']; lab = z['l'].astype(int)
h = V[F][:,:,2]; lo, hi = h.min(1), h.max(1)
CODES = np.array(['4', '8', '0C', '1C', '2C', '3C', '4C', '5C'])
FINISH = ['#E6BAA8', '#0E0E10', GREEN, '#F1ECE1', '#FFCC33', '#EFC13A', '#BB1E10', '#8C979D']
NAMES = ['Apricot (skin)', 'Black', 'Green (uniform)', 'Pure White', 'Yellow (dress)', 'Gold (paint)', 'Red (paint)', 'Silver (paint)']
# physical head per face
tool = np.full(len(F), -1)
tool[lab == 0] = 3                                            # T4 skin
tool[lab == 2] = 0                                            # T1 green (above S1)
w = lab == 3; tool[w & (hi <= S1 - GAP)] = 0; tool[w & (hi > S1 - GAP)] = 2   # her shoes on T1 before S1, all other white on T3
b = lab == 1; tool[b & (hi <= S2 - GAP)] = 2; tool[b & (lo >= S3 + GAP)] = 1  # his shoes on T3 before S2, the rest on T2 after S3
y = lab == 4; tool[y & (hi <= S3 - GAP)] = 1; tool[y & (hi > S3 - GAP)] = 2   # yellow above S3 prints white, painted yellow
tool[np.isin(lab, [5, 6, 7])] = 2                             # gold, red, silver print white (paint)
assert (tool >= 0).all(), 'unassigned faces: %s' % np.bincount(lab[tool < 0])
TOOLS = ['#F1ECE1', '#FFCC33', '#0E0E10', '#E6BAA8']           # start-of-print spools
# swap safety: per head, colour before the pause never shares a layer band with colour after it
asserts = [('T1 white/green', (lab == 3) & (tool == 0), (lab == 2), S1),
           ('T3 black/white', (lab == 1) & (tool == 2), (tool == 2) & (lab != 1), S2),
           ('T2 yellow/black', (lab == 4) & (tool == 1), (lab == 1) & (tool == 1), S3)]
for nm, below, above, s in asserts:
    print('%s: before-pause top %.2f < pause %.1f < after-pause bottom %.2f' % (nm, hi[below].max(), s, lo[above].min()))
    assert hi[below].max() <= s - GAP and lo[above].min() >= s + GAP, nm
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
                      '<resources><object id="1" type="model" name="Couple army doctor"><mesh><vertices>').encode())
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
paint = {'gold (buttons, shoulder stars)': lab == 5, 'red (dress buttons)': lab == 6, 'silver (stethoscope chest piece)': lab == 7,
         'yellow (dress top inside the coat, above %.2f mm)' % (S3 - GAP): (lab == 4) & (hi > S3 - GAP)}
paint_txt = '\n'.join('  - %s: %.1f mm2' % (k, area[v].sum()) for k, v in paint.items())
guide_notes = ('Finish guide: the intended colours after hand-painting. Print from Couple-army-doctor-U1-150mm.3mf, not this file.\n' +
               '\n'.join(f'Slot {i+1}: {nm} {hx}' for i, (nm, hx) in enumerate(zip(NAMES, FINISH))) + '\n')
print_notes = ('Snapmaker U1 project, 150 mm tall, scale 100%. Four tool heads at the start:\n'
               'T1 Pure White #F1ECE1   T2 Yellow #FFCC33   T3 Black #0E0E10   T4 Apricot #E6BAA8 (skin, whole print)\n'
               f'PAUSE 1 at the first layer at or above {S1:.2f} mm: swap T1 Pure White -> Green {GREEN} (uniform). '
               f'White (her shoes) ends {hi[(lab == 3) & (tool == 0)].max():.2f} mm, green starts {lo[lab == 2].min():.2f} mm.\n'
               f'PAUSE 2 at the first layer at or above {S2:.2f} mm: swap T3 Black -> Pure White #F1ECE1 (coat, eyes, paint bases). '
               f'Black (his shoes) ends {hi[(lab == 1) & (tool == 2)].max():.2f} mm, white starts {lo[(tool == 2) & (lab != 1)].min():.2f} mm.\n'
               f'PAUSE 3 at the first layer at or above {S3:.2f} mm: swap T2 Yellow -> Black #0E0E10 (hair, stethoscope, tie, eyes, brows). '
               f'Yellow ends {hi[(lab == 4) & (tool == 1)].max():.2f} mm, black starts {lo[(lab == 1) & (tool == 1)].min():.2f} mm.\n'
               'Printed white, hand-paint afterwards:\n' + paint_txt + '\n'
               'Select your real U1 printer, nozzle and PLA+ presets in Snapmaker Orca before slicing. Supports and wipe tower on white.\n')
os.makedirs('out', exist_ok=True)
np.save('out/finish_slots.npy', lab.astype('u1')); np.save('out/tool_ids.npy', tool.astype('u1'))
write('out/Couple-army-doctor-150mm-finish-guide.3mf', lab, FINISH, 'Couple army doctor - finish guide', guide_notes)
write('out/Couple-army-doctor-U1-150mm.3mf', tool, TOOLS, 'Couple army doctor - Snapmaker U1', print_notes)
open('out/print-notes.txt', 'w').write(print_notes); print(print_notes)
