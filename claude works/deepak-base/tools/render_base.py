"""Render presentation views of Deepak-base.blend with Cycles (CPU, headless).

  blender -b ../out/Deepak-base.blend -P render_base.py -- --out ../out
Writes Deepak-base-hero.png (three-quarter, slightly from above, like the approved render) and
Deepak-base-plate.png (straight-on close-up of the nameplate).
"""
import argparse
import math
import sys
from pathlib import Path

import bpy

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument('--out', type=Path, required=True)
p.add_argument('--samples', type=int, default=128)
A = p.parse_args(argv)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = A.samples
scene.cycles.use_denoising = False   # the distro build has no OpenImageDenoise
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
cam = scene.camera
ob = bpy.data.objects['Deepak base (print)']
ob.data.polygons.foreach_set('use_smooth', [False] * len(ob.data.polygons))
d = max(ob.dimensions)
zc = 17.3

views = [
    ('hero', (0, -3.4 * d, 16 + 3.4 * d * math.tan(math.radians(8))), (math.radians(82), 0, 0), 70, (1400, 900)),
    ('plate', (0, -190, zc), (math.radians(90), 0, 0), 120, (1400, 700)),
]
for name, loc, rot, lens, res in views:
    cam.location, cam.rotation_euler = loc, rot
    cam.data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = str(A.out / f'Deepak-base-{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', scene.render.filepath)
