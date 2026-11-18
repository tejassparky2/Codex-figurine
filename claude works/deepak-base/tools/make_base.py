"""Deepak "Coffee Master" display base, built headless in Blender.

  blender -b --factory-startup -P make_base.py -- --out ../out [--diameter 120 --height 30 --name Deepak --title "COFFEE MASTER"]

Builds the round two-tier pedestal (wider plinth with a rounded ledge, upper tier with a groove under a rounded lid,
chamfered foot), a nameplate curved to the
cylinder, two screw domes and raised lettering. Everything is unioned into ONE watertight mesh whose faces carry
three finish slots: 1 base brown, 2 nameplate gold, 3 lettering dark brown. It writes:
  Deepak-base.blend, Deepak-base-finish.3mf (Orca per-triangle paint_color), Deepak-base-{body,plate,text}.stl
Units are millimetres; Z is up; the plate faces -Y (front).
"""
import argparse
import json
import math
import sys
import zipfile
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument('--out', type=Path, required=True)
p.add_argument('--diameter', type=float, default=120.0)
p.add_argument('--height', type=float, default=30.5)
p.add_argument('--lip', type=float, default=6.1, help='height of the top lid above the groove')
p.add_argument('--plinth', type=float, default=10.0, help='height of the wider bottom plinth')
p.add_argument('--upper-ratio', type=float, default=0.95, help='upper tier diameter / plinth diameter')
p.add_argument('--name', default='Deepak')
p.add_argument('--title', default='COFFEE MASTER')
p.add_argument('--plate-width', type=float, default=0.48, help='arc width as a fraction of the diameter')
p.add_argument('--plate-height', type=float, default=0, help='mm; 0 = fill the upper tier between the ledge cove and the groove, as in the approved render')
p.add_argument('--relief', type=float, default=0.8, help='lettering height above the plate (mm)')
p.add_argument('--segments', type=int, default=360)
p.add_argument('--serif-font', default='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf')
p.add_argument('--sans-font', default='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
p.add_argument('--colors', default='#976E52,#EFC13A,#4C2C21', help='slot 1 base, slot 2 plate, slot 3 lettering (stock filaments)')
A = p.parse_args(argv)
A.out.mkdir(parents=True, exist_ok=True)
R, H = A.diameter / 2, A.height
RU = R * A.upper_ratio                   # upper tier radius; the plate and lettering bend around it
PLATE_T, PLATE_EMBED, TEXT_EMBED = 1.2, 0.6, 0.3
W = A.plate_width * A.diameter
TIER_LO, TIER_HI = A.plinth + 0.8, H - A.lip - 0.6           # top of the ledge cove, bottom of the groove
ZC = (TIER_LO + TIER_HI) / 2                                 # plate centred on the upper tier
HP = A.plate_height or (TIER_HI - TIER_LO - 0.9)             # 0.45 mm clearance top and bottom
assert HP <= TIER_HI - TIER_LO - 0.6, 'plate taller than the upper tier'

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = 'MILLIMETERS'


def material(name, hexcol):
    m = bpy.data.materials.new(name)
    rgb = [int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    m.diffuse_color = (*[c ** 2.2 for c in rgb], 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*[c ** 2.2 for c in rgb], 1)
    bsdf.inputs['Roughness'].default_value = .55 if name != 'Gold' else .35
    if name == 'Gold':
        bsdf.inputs['Metallic'].default_value = .6
    return m


colors = A.colors.split(',')
MATS = [material('Base brown', colors[0]), material('Gold', colors[1]), material('Lettering brown', colors[2])]


def new_object(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


# ---------------------------------------------------------------- body: lathe of a profile, fans to the axis
def body():
    # Two tiers, as in the approved render: a wider plinth with a rounded ledge, then the upper tier with a
    # groove under a lid whose top edge is rounded.
    c_bot, r_top, r_ledge = 0.8, 2.0, 1.5        # foot chamfer, lid edge radius, plinth ledge radius
    zg, gh, gd = H - A.lip, 1.2, 0.8             # groove centre, height, depth
    prof = [(R - c_bot, 0.0), (R, c_bot), (R, A.plinth - r_ledge)]
    for k in range(1, 7):                        # quarter-round outer edge of the plinth ledge
        a = k / 6 * math.pi / 2
        prof.append((R - r_ledge + r_ledge * math.cos(a), A.plinth - r_ledge + r_ledge * math.sin(a)))
    prof += [(RU + .8, A.plinth)]
    for k in range(1, 5):                        # small cove into the upper tier
        a = k / 4 * math.pi / 2
        prof.append((RU + .8 - .8 * math.sin(a), A.plinth + .8 - .8 * math.cos(a)))
    prof += [(RU, zg - gh / 2), (RU - gd, zg), (RU, zg + gh / 2), (RU, H - r_top)]
    for k in range(1, 9):                        # quarter-round lid edge
        a = k / 8 * math.pi / 2
        prof.append((RU - r_top + r_top * math.cos(a), H - r_top + r_top * math.sin(a)))
    bm = bmesh.new()
    n = A.segments
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z)) for i in range(n)])
    for a_ring, b_ring in zip(rings[:-1], rings[1:]):
        for i in range(n):
            bm.faces.new((a_ring[i], a_ring[(i + 1) % n], b_ring[(i + 1) % n], b_ring[i]))
    bottom = bm.verts.new((0, 0, 0))
    top = bm.verts.new((0, 0, H))
    for i in range(n):
        bm.faces.new((rings[0][(i + 1) % n], rings[0][i], bottom))
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % n], top))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_object('Body', bm, MATS[0])


# ---------------------------------------------------------------- plate: structured curved slab
def to_cyl(s, z, r):
    a = s / RU
    return (r * math.sin(a), -r * math.cos(a), z)


def plate():
    rc, bev = 2.5, 0.5                           # corner radius, front edge rounding
    ns, nv = max(60, int(W / .4)), 24
    def z_range(s):
        dx = abs(s) - (W / 2 - rc)
        half = HP / 2 if dx <= 0 else HP / 2 - rc + math.sqrt(max(rc * rc - dx * dx, 0))
        return ZC - half, ZC + half
    def front_r(s, z, lo, hi):
        d = min(W / 2 - abs(s), z - lo, hi - z)
        f = min(1, max(0, d) / bev)
        return RU + PLATE_T * (.55 + .45 * math.sqrt(1 - (1 - f) ** 2))
    bm = bmesh.new()
    grid = {}
    ss = [-W / 2 + W * i / ns for i in range(ns + 1)]
    for side, rad in (('f', None), ('b', RU - PLATE_EMBED)):
        for i, s in enumerate(ss):
            lo, hi = z_range(s)
            for j in range(nv + 1):
                z = lo + (hi - lo) * j / nv
                r = front_r(s, z, lo, hi) if side == 'f' else rad
                grid[side, i, j] = bm.verts.new(to_cyl(s, z, r))
    for i in range(ns):
        for j in range(nv):
            bm.faces.new((grid['f', i, j], grid['f', i + 1, j], grid['f', i + 1, j + 1], grid['f', i, j + 1]))
            bm.faces.new((grid['b', i, j + 1], grid['b', i + 1, j + 1], grid['b', i + 1, j], grid['b', i, j]))
    for i in range(ns):                          # bottom and top rims
        bm.faces.new((grid['b', i, 0], grid['b', i + 1, 0], grid['f', i + 1, 0], grid['f', i, 0]))
        bm.faces.new((grid['f', i, nv], grid['f', i + 1, nv], grid['b', i + 1, nv], grid['b', i, nv]))
    for i in (0, ns):                            # end strips
        for j in range(nv):
            bm.faces.new((grid['f', i, j], grid['f', i, j + 1], grid['b', i, j + 1], grid['b', i, j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_object('Plate', bm, MATS[1])


def screws():
    obs = []
    for sx in (-1, 1):
        s = sx * (W / 2 - 3.6)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.1)
        ob = bpy.context.object
        ob.name = f'Screw {sx}'
        ob.scale = (1, .55, 1)                   # dome depth along the plate normal
        a = s / RU
        ob.rotation_euler = (0, 0, a)
        ob.location = to_cyl(s, ZC, RU + PLATE_T)
        ob.data.materials.append(MATS[1])
        obs.append(ob)
    return obs


# ---------------------------------------------------------------- lettering: font -> mesh -> bent onto the plate
def lettering(text, font, target_width, zline):
    cu = bpy.data.curves.new(text, 'FONT')
    cu.body = text
    cu.font = bpy.data.fonts.load(font)
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    cu.size = 1.0
    cu.extrude = (A.relief + TEXT_EMBED) / 2
    cu.resolution_u = 6
    ob = bpy.data.objects.new(text, cu)
    scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.object
    ob.select_set(False)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    xs = [v.co.x for v in bm.verts]
    k = target_width / (max(xs) - min(xs))
    # Glyph edges are at most a few mm long, so bending them as straight chords sags < 0.1 mm on this radius,
    # well inside TEXT_EMBED. (Splitting long edges here corrupted glyph caps, so it is not done.)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    zmid = (A.relief + TEXT_EMBED) / 2
    for v in bm.verts:
        s, y, t = v.co.x * k, v.co.y * k, v.co.z      # t in [-e, e] across the extrusion
        v.co = to_cyl(s, zline + y, RU + PLATE_T - TEXT_EMBED + (t + zmid))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.materials.clear()
    ob.data.materials.append(MATS[2])
    heights = [v.co.z for v in ob.data.vertices]
    return ob, max(heights) - min(heights)


body_ob, plate_ob = body(), plate()
screw_obs = screws()
name_ob, name_h = lettering(A.name, A.serif_font, .39 * W, ZC + .17 * HP)
title_ob, title_h = lettering(A.title, A.sans_font, .62 * W, ZC - .26 * HP)


def export_stl(obs, path):
    """Binary STL of the objects in world coordinates (no add-on needed)."""
    import struct
    tris = []
    for o in obs:
        dg = bpy.context.evaluated_depsgraph_get()
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        mw = o.matrix_world
        for t in me.loop_triangles:
            tris.append([mw @ me.vertices[i].co for i in t.vertices])
        o.evaluated_get(dg).to_mesh_clear()
    with open(path, 'wb') as fp:
        fp.write(b'Deepak base'.ljust(80, b' ') + struct.pack('<I', len(tris)))
        for a, b, c in tris:
            n = (b - a).cross(c - a).normalized()
            fp.write(struct.pack('<12fH', *n, *a, *b, *c, 0))


export_stl([body_ob], A.out / 'Deepak-base-body.stl')
export_stl([plate_ob, *screw_obs], A.out / 'Deepak-base-plate.stl')
export_stl([name_ob, title_ob], A.out / 'Deepak-base-text.stl')

# ---------------------------------------------------------------- union into one mesh, keeping per-face materials
for o in [plate_ob, *screw_obs, name_ob, title_ob]:
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
merged = body_ob
merged.data.materials.clear()
for m in MATS:
    merged.data.materials.append(m)
for tool in [plate_ob, *screw_obs, name_ob, title_ob]:
    mod = merged.modifiers.new('union', 'BOOLEAN')
    mod.operation, mod.solver, mod.object = 'UNION', 'EXACT', tool
    mod.material_mode = 'TRANSFER'
    bpy.context.view_layer.objects.active = merged
    bpy.ops.object.modifier_apply(modifier=mod.name)
    tool.hide_set(True)
    tool.hide_render = True
merged.name = 'Deepak base (print)'
bm = bmesh.new()
bm.from_mesh(merged.data)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.to_mesh(merged.data)
bm.free()
mats_index = {m.name: i for i, m in enumerate(merged.data.materials)}
slot_of = [ [m.name for m in MATS].index(mm.name) if mm and mm.name in [x.name for x in MATS] else 0 for mm in merged.data.materials]

# ---------------------------------------------------------------- 3MF with Orca per-triangle paint codes
codes = ['4', '8', '0C']
me = merged.data
verts = [v.co for v in me.vertices]
tris = [(tuple(pl.vertices), slot_of[pl.material_index]) for pl in me.polygons]
counts = [sum(1 for _, s in tris if s == k) for k in range(3)]
model = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
         '<metadata name="Application">Blender make_base.py</metadata><resources><object id="1" type="model" name="Deepak base"><mesh><vertices>']
model += [f'<vertex x="{v.x:.5f}" y="{v.y:.5f}" z="{v.z:.5f}"/>' for v in verts]
model.append('</vertices><triangles>')
model += [f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{codes[s]}"/>' for (a, b, c), s in tris]
model.append('</triangles></mesh></object></resources><build><item objectid="1" transform="1 0 0 0 1 0 0 0 1 135 135 0"/></build></model>')
types = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
         '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
         '<Default Extension="config" ContentType="text/plain"/></Types>')
rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
with zipfile.ZipFile(A.out / 'Deepak-base-finish.3mf', 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', types)
    z.writestr('_rels/.rels', rels)
    z.writestr('3D/3dmodel.model', '\n'.join(model))
    z.writestr('Metadata/project_settings.config', json.dumps({'filament_colour': colors}))

# ---------------------------------------------------------------- presentation scene, then save the .blend
cam_data = bpy.data.cameras.new('Camera')
cam = bpy.data.objects.new('Camera', cam_data)
scene.collection.objects.link(cam)
cam_data.lens = 70
cam.location = (0, -3.6 * A.diameter, .95 * A.diameter)
cam.rotation_euler = (math.radians(77), 0, 0)
scene.camera = cam
for name, loc, energy in (('Key', (-150, -260, 320), 1.1e6), ('Fill', (260, -180, 160), 4e5), ('Rim', (0, 300, 300), 3e5)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy, ld.size = energy, 160
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(lo)
world = bpy.data.worlds.new('World')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.62, .63, .65, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .6
scene.world = world
bpy.ops.wm.save_as_mainfile(filepath=str(A.out / 'Deepak-base.blend'))
print(json.dumps(dict(upper_diameter=round(2 * RU, 2), plate_z=[round(ZC - HP / 2, 2), round(ZC + HP / 2, 2)], faces=len(tris), slot_faces=dict(base=counts[0], plate=counts[1], lettering=counts[2]),
                      diameter=A.diameter, height=H, plate_mm=[round(W, 2), round(HP, 2)],
                      name_height_mm=round(name_h, 2), title_height_mm=round(title_h, 2))))
