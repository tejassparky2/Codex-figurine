"""Deepak "Coffee Master" display base, built headless in Blender.

  blender -b --factory-startup -P make_base.py -- --out ../out [--diameter 120 --height 30 --name Deepak --title "COFFEE MASTER"]

Builds the round two-tier pedestal, with the espresso machine and burlap coffee sack (props.py) standing on it (wider plinth with a rounded ledge, upper tier with a groove under a rounded lid,
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
p.add_argument('--height', type=float, default=30.4, help='mm; keep a multiple of 0.08 and 0.2 so the spool swap falls on a layer boundary')
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
# Stock filaments (PLAYBOOK section 2). Parts sharing a colour share a finish slot.
p.add_argument('--base-color', default='#4C2C21', help='Dark chocolate brown (owner, 2026-11-18); Tan is #976E52')
p.add_argument('--plate-color', default='#EFC13A', help='Gold')
p.add_argument('--lettering-color', default='#4C2C21', help='Dark chocolate brown')
p.add_argument('--black', default='#0E0E10')
p.add_argument('--silver', default='#8C979D', help='Simply Silver')
p.add_argument('--apricot', default='#E6BAA8', help='Apricot, for the burlap sack')
p.add_argument('--white', default='#F1ECE1', help='Pure White, for the cup')
p.add_argument('--no-props', action='store_true', help='base only, without the espresso machine and coffee sack')
p.add_argument('--machine-at', default='31.5,8', help='x,y of the machine centre on the base top (mm)')
p.add_argument('--sack-at', default='-36,6', help='x,y of the sack centre on the base top (mm)')
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


# Filaments that print visibly different from their slicer swatch: render with the printed colour (PLAYBOOK §2).
PREVIEW = {'#E6BAA8': '#DEA485'}


def material(name, hexcol):
    m = bpy.data.materials.new(name)
    shown = PREVIEW.get(hexcol.upper(), hexcol)
    rgb = [int(shown[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    m.diffuse_color = (*[c ** 2.2 for c in rgb], 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*[c ** 2.2 for c in rgb], 1)
    bsdf.inputs['Roughness'].default_value = .55 if name != 'Gold' else .35
    if name == 'Gold':
        bsdf.inputs['Metallic'].default_value = .6
    return m


PART_COLORS = {'Base brown': A.base_color, 'Gold': A.plate_color, 'Lettering brown': A.lettering_color}
if not A.no_props:
    PART_COLORS.update({'Black': A.black, 'Silver': A.silver, 'Apricot': A.apricot, 'White': A.white})
colors = list(dict.fromkeys(c.upper() for c in PART_COLORS.values()))      # finish slots, in order of first use
MATS = [material(name, hexcol) for name, hexcol in PART_COLORS.items()]
PROP_MATS = {name.lower(): m for name, m in zip(PART_COLORS, MATS) if name in ('Black', 'Silver', 'Apricot', 'White')}


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


machine_obs, sack_obs = [], []
if not A.no_props:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import props
    mx, my = map(float, A.machine_at.split(','))
    sx, sy = map(float, A.sack_at.split(','))
    machine_obs = props.espresso_machine(scene, PROP_MATS, mx, my, H)
    sack_obs = props.coffee_sack(scene, PROP_MATS, sx, sy, H)
    reach = max(math.hypot(v.co.x, v.co.y) for o in machine_obs + sack_obs for v in o.data.vertices)
    assert reach < RU - 1.0, f'a prop reaches {reach:.1f} mm from the centre; the top edge is at {RU:.1f} mm'
    print(f'props reach {reach:.1f} mm of the {RU:.1f} mm top radius')

export_stl([body_ob], A.out / 'Deepak-base-body.stl')
export_stl([plate_ob, *screw_obs], A.out / 'Deepak-base-plate.stl')
export_stl([name_ob, title_ob], A.out / 'Deepak-base-text.stl')
if machine_obs:
    export_stl(machine_obs, A.out / 'Deepak-espresso-machine.stl')
    export_stl(sack_obs, A.out / 'Deepak-coffee-sack.stl')

# ---------------------------------------------------------------- union into one mesh, keeping per-face materials
tools = [plate_ob, *screw_obs, name_ob, title_ob, *machine_obs, *sack_obs]
for o in tools:
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# Union one part at a time (a single self-intersecting union of all parts joined together left open and
# doubled edges at the plate and the sack). Source parts stay hidden in the .blend.
merged = body_ob
for m in MATS[1:]:
    merged.data.materials.append(m)
for tool in tools:
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
# Exact unions of many overlapping parts (beans, fins) can leave zero-volume sliver shells. Keep only the main
# connected shell and report what was dropped.
seen, islands = set(), []
for f0 in bm.faces:
    if f0.index in seen:
        continue
    stack, isl = [f0], []
    seen.add(f0.index)
    while stack:
        f1 = stack.pop()
        isl.append(f1)
        for e in f1.edges:
            for f2 in e.link_faces:
                if f2.index not in seen:
                    seen.add(f2.index)
                    stack.append(f2)
    islands.append(isl)
islands.sort(key=len, reverse=True)
dropped = [sum(f.calc_area() for f in isl) for isl in islands[1:]]
assert all(a < 2.0 for a in dropped), f'a real part is detached: shell areas {dropped}'
bmesh.ops.delete(bm, geom=[f for isl in islands[1:] for f in isl], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
print(f'removed {len(dropped)} sliver shells, total area {sum(dropped):.3f} mm2')
bm.to_mesh(merged.data)
bm.free()
slot_of = [colors.index(PART_COLORS[mm.name].upper()) if mm and mm.name in PART_COLORS else 0 for mm in merged.data.materials]

# ---------------------------------------------------------------- 3MFs with Orca per-triangle paint codes
codes = ['4', '8'] + [f'{i:X}C' for i in range(14)]
me = merged.data
verts = [v.co for v in me.vertices]
tris = [(tuple(pl.vertices), slot_of[pl.material_index]) for pl in me.polygons]
counts = [sum(1 for _, s in tris if s == k) for k in range(len(colors))]
# Four-head printer plan. Below the base top, heads carry the base colours; at z = H one pause swaps the heads
# whose colour is no longer needed for prop colours; any head idle below H is preloaded with a prop colour.
zface = [sum(me.vertices[i].co.z for i in t) / 3 for t, _ in tris]
low = sorted({s for (t, s), z in zip(tris, zface) if z <= H + 1e-4})   # the top skin is printed before the pause
high = sorted({s for (t, s), z in zip(tris, zface) if z > H + 1e-4})
assert len(low) <= 4 and len(high) <= 4, f'too many colours: below {low}, above {high}'
start = {s: h for h, s in enumerate(low)}
after = {s: start[s] for s in high if s in start}
free = [h for h in range(4) if h not in after.values()]
idle = [h for h in free if h >= len(low)]
for s in [s for s in high if s not in after]:
    h = (idle or free).pop(0)
    if h in free:
        free.remove(h)
    after[s] = h
    if h >= len(low):
        start[s] = h                              # preloaded in a head unused below H
swaps = [(h, colors[low[h]], colors[s]) for s, h in sorted(after.items(), key=lambda kv: kv[1]) if h < len(low) and low[h] != s]
tool_of = [start[s] if z <= H + 1e-4 else after[s] for (t, s), z in zip(tris, zface)]
start_spools = [next((colors[s] for s, h in start.items() if h == k), colors[low[0]]) for k in range(4)]
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
def write_3mf(path, labels, palette):
    tri_lines = [f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{codes[k]}"/>' for ((a, b, c), _), k in zip(tris, labels)]
    i0 = next(i for i, line in enumerate(model) if line.startswith('<triangle'))
    body = model[:i0] + tri_lines + model[i0 + len(tri_lines):]
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', types)
        z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', '\n'.join(body))
        z.writestr('Metadata/project_settings.config', json.dumps({'filament_colour': palette}))


write_3mf(A.out / 'Deepak-base-finish.3mf', [s for _, s in tris], colors)
write_3mf(A.out / 'Deepak-base-U1.3mf', tool_of, start_spools)

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
print(json.dumps(dict(finish_slots=colors, faces_per_slot=counts, start_spools=start_spools,
                      pause_before_first_layer_at_mm=H if swaps else None,
                      swaps=[f'head {h + 1}: {a} -> {b}' for h, a, b in swaps],
                      diameter=A.diameter, height=H, total_height=round(max(v.z for v in verts), 2), faces=len(tris),
                      upper_diameter=round(2 * RU, 2), plate_z=[round(ZC - HP / 2, 2), round(ZC + HP / 2, 2)],
                      plate_mm=[round(W, 2), round(HP, 2)], name_height_mm=round(name_h, 2), title_height_mm=round(title_h, 2))))
