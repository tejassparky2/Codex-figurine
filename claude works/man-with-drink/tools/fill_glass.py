"""Owner, 2026-11-19: "for cup down fill with orange".

Recolours the tumbler from its bottom up to the liquid line (z 97.4 mm) orange, in both exported 3MFs, leaving
every other face untouched. That covers the outer band below the old 91.0 mm drink line and the underside.
Glass faces are found with the job's own geometry: the fitted tumbler axis (glass_axis.npy), radius < 7.6 mm
and 86.5 < z < 105.5 mm (the same zone the contour-split keep mask used), currently silver.

  python -I tools/fill_glass.py            (run from the job folder, after export.py)
"""
import json
import re
import zipfile
from pathlib import Path

import numpy as np

LIQUID = 97.4
ax = np.load('glass_axis.npy')
files = {'out/Man-with-drink-220mm-finish-guide.3mf': ('1C', '0C'),      # finish slot 4 orange, slot 3 silver
         'out/Man-with-drink-U1-220mm.3mf': ('1C', '0C')}                 # head T4 orange, head T3 silver
pattern = rb'paint_color="([^"]+)"'
changed_ref = None
for name, (orange, silver) in files.items():
    path = Path(name)
    with zipfile.ZipFile(path) as z:
        members = {k: z.read(k) for k in z.namelist()}
    s = members['3D/3dmodel.model']
    v = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', s), float)
    f = np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), int)
    codes = [c.decode() for c in re.findall(pattern, s)]
    assert len(codes) == len(f), 'every triangle must carry a solid paint code'
    c = v[f].mean(1)
    rad = np.hypot(c[:, 0] - ax[0], c[:, 1] - ax[1])
    glass = (rad < 7.6) & (c[:, 2] > 86.5) & (c[:, 2] < 105.5)
    target = glass & (c[:, 2] < LIQUID) & (np.array(codes) == silver)
    idx = np.flatnonzero(target)
    if changed_ref is None:
        changed_ref = idx
    assert np.array_equal(idx, changed_ref), 'both files must change the same faces'
    for i in idx:
        codes[i] = orange
    it = iter(codes)
    members['3D/3dmodel.model'] = re.sub(pattern, lambda _: b'paint_color="' + next(it).encode() + b'"', s)
    tmp = path.with_suffix('.tmp')
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as out:
        for k, data in members.items():
            out.writestr(k, data)
    tmp.replace(path)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert [x.decode() for x in re.findall(pattern, z.read('3D/3dmodel.model'))] == codes
    zc = c[idx, 2]
    print(f'{name}: {len(idx)} glass faces silver -> orange' + (f', z {zc.min():.2f}..{zc.max():.2f} mm' if len(idx) else ''))
