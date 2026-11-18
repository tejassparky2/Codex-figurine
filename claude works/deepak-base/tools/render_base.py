"""Render presentation views of Deepak-base.blend with Cycles (CPU, headless).

  blender -b ../out/Deepak-base.blend -P render_base.py -- --out ../out [--samples 128]
Writes Deepak-base-hero.png (near-level three-quarter, like the approved render), Deepak-base-plate.png,
Deepak-machine.png and Deepak-sack.png (close-ups).
"""
import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument('--out', type=Path, required=True)
p.add_argument('--samples', type=int, default=128)
p.add_argument('--machine-at', default='33,8')
p.add_argument('--sack-at', default='-36,3')
A = p.parse_args(argv)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = A.samples
scene.cycles.use_denoising = False   # the distro build has no OpenImageDenoise
scene.view_settings.view_transform = 'Standard'
cam = scene.camera
ob = bpy.data.objects['Deepak base (print)']
ob.data.polygons.foreach_set('use_smooth', [False] * len(ob.data.polygons))
mx, my = map(float, A.machine_at.split(','))
sx, sy = map(float, A.sack_at.split(','))


def look(loc, target, lens):
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens


views = [
    ('base-hero', (0, -430, 95), (0, 0, 32), 62, (1400, 1000)),
    ('base-plate', (0, -190, 17.3), (0, 0, 17.3), 120, (1400, 700)),
    ('machine', (mx - 40, my - 150, 85), (mx, my, 50), 85, (1000, 1100)),
    ('sack', (sx + 30, sy - 120, 75), (sx, sy, 41), 95, (1000, 900)),
]
for name, loc, target, lens, res in views:
    look(loc, target, lens)
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = str(A.out / f'Deepak-{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', scene.render.filepath)
