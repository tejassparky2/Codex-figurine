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
p.add_argument('--machine-at', default='31.5,8')
p.add_argument('--sack-at', default='-36,6')
A = p.parse_args(argv)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = A.samples
scene.cycles.use_denoising = False   # the distro build has no OpenImageDenoise
scene.view_settings.view_transform = 'Standard'
cam = scene.camera
ob = bpy.data.objects['Deepak base (print)']
# Smooth curved surfaces (sack, beans, knobs) but keep creases and flat faces crisp.
ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
if hasattr(ob.data, 'use_auto_smooth'):
    ob.data.use_auto_smooth = True
    ob.data.auto_smooth_angle = 0.6
mx, my = map(float, A.machine_at.split(','))
sx, sy = map(float, A.sack_at.split(','))


def look(loc, target, lens):
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens


views = [
    ('base-hero', (0, -430, 95), (0, 0, 32), 62, (1400, 1000)),
    ('base-plate', (0, -190, 17.3), (0, 0, 17.3), 120, (1400, 700)),
    ('machine', (mx, my - 165, 62), (mx + 3, my, 51), 105, (1000, 1100)),
    ('sack', (sx, sy - 145, 80), (sx, sy, 44), 115, (1000, 900)),          # ~14 degrees down, as in the render
]
for name, loc, target, lens, res in views:
    look(loc, target, lens)
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = str(A.out / f'Deepak-{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', scene.render.filepath)
