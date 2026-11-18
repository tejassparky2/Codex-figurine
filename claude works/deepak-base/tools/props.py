"""Espresso machine and burlap coffee sack for the Deepak base (imported by make_base.py inside Blender).

Both are modelled in millimetres on the base top at z0 and measured from the approved render
(about 0.13 mm per image pixel at the machine, 0.124 at the sack):
- Machine (28 x 22 x 40 mm): black rounded housing, light-grey cup-warmer slats on top, a grey control panel with
  three black knobs, a black side knob, an open brewing bay with a grey back panel and group head, a horizontal
  silver portafilter whose black capsule handle passes in front of the right column and sticks out about 7 mm
  beyond the side, a grey drip tray with ribs and a white cup with a round handle.
- Sack (about 29 x 25.5 mm): a wide burlap bag with a rounded foot, a soft lump on the left, a thick folded collar
  (band plus rolled lip), a fine diamond weave, and coffee beans filling the mouth to just below the lip.

Printing: the portafilter and handle are horizontal, as in the render, so they need support (tree supports, or
support enforcers under the handle and portafilter). Everything else is self-supporting: the sack's foot and
collar overhangs stay under about 35 degrees from vertical, and the bay ceiling is a 22 mm bridge.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector


def _obj(scene, name, bm, mat):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def box(scene, name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((v.co.x + .5) * (x1 - x0) + x0, (v.co.y + .5) * (y1 - y0) + y0, (v.co.z + .5) * (z1 - z0) + z0))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=3, affect='EDGES', profile=.5)
    return _obj(scene, name, bm, mat)


def cone(scene, name, r_bottom, r_top, depth, loc, mat, axis=(0, 0, 1), segments=48):
    """Frustum from r_bottom to r_top along `axis`, centred at loc."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=r_bottom, radius2=r_top, depth=depth)
    rot = Vector((0, 0, 1)).rotation_difference(Vector(axis)).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(loc) @ rot, verts=bm.verts)
    return _obj(scene, name, bm, mat)


def ellipsoid(scene, name, radii, loc, yaw, mat, tilt=0.0, segments=(16, 10)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments[0], v_segments=segments[1], radius=1.0)
    m = Matrix.Translation(loc) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'X') @ Matrix.Diagonal((*radii, 1))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return _obj(scene, name, bm, mat)


def union_into(target, tools):
    """Exact boolean union of `tools` into `target` one at a time (robust for overlapping small parts)."""
    for t in tools:
        mod = target.modifiers.new('u', 'BOOLEAN')
        mod.operation, mod.solver, mod.object = 'UNION', 'EXACT', t
        mod.material_mode = 'TRANSFER'
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(t, do_unlink=True)
    return target


def espresso_machine(scene, mats, cx, cy, z0, yaw_deg=0.0):
    """Returns the machine's parts (front faces -Y before the yaw)."""
    black, silver, white = mats['black'], mats['silver'], mats['white']
    W, D, Hm = 28.0, 22.0, 40.0
    fy = -D / 2                                   # front face plane (local)
    bay_x, bay_lo, bay_top = 11.0, 1.0, 18.0
    parts = []
    body = box(scene, 'Machine body', -W / 2, W / 2, fy, D / 2, -0.73, Hm, black, bevel=1.2)   # sunk in, no ring on the top plane
    bay = box(scene, 'bay cut', -bay_x, bay_x, fy - 2, fy + 7, bay_lo, bay_top, black)
    mod = body.modifiers.new('bay', 'BOOLEAN')
    mod.operation, mod.solver, mod.object = 'DIFFERENCE', 'EXACT', bay
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(bay, do_unlink=True)
    parts.append(body)
    parts.append(box(scene, 'Bay back panel', -10.4, 10.4, fy + 6.4, fy + 7.4, bay_lo + .4, bay_top - .4, silver))
    for i in range(7):                            # light-grey cup-warmer slats on the top front
        x = -10.5 + i * 3.5
        parts.append(box(scene, f'Slat {i}', x - .65, x + .65, fy + 1.0, fy + 7.0, Hm - .6, Hm + 2.6, silver, bevel=.25))
    pz0, pz1 = 19.1, 35.3                         # control panel, measured
    kz = (pz0 + pz1) / 2
    parts.append(box(scene, 'Control panel', -11.5, 11.5, fy - .9, fy + .5, pz0, pz1, silver, bevel=.8))
    for x in (-7.0, 0.0, 7.0):
        parts.append(cone(scene, f'Knob {x:+.0f}', 2.5, 2.3, 2.4, (x, fy - .9 - .9, kz), black, axis=(0, -1, 0)))
    parts.append(cone(scene, 'Side knob', 2.15, 2.0, 3.0, (W / 2 + 1.1, 1.0, kz), black, axis=(1, 0, 0)))
    # Group head at the bay ceiling, then the horizontal portafilter and its handle (measured at 13.6 mm).
    hz = 13.6
    parts.append(cone(scene, 'Group head', 3.4, 4.2, 2.4, (-1.0, fy + 3.2, bay_top - 1.0), silver))   # overlaps the portafilter
    parts.append(cone(scene, 'Portafilter', 2.7, 2.7, 11.7, (1.85, fy + .6, hz), silver, axis=(1, 0, 0)))
    hx0, hx1, hr = 7.2, 21.3, 1.95                # black handle: passes in front of the right column, ~7 mm beyond the side
    parts.append(cone(scene, 'Portafilter handle', hr, hr, hx1 - hx0, ((hx0 + hx1) / 2, fy - .4, hz), black, axis=(1, 0, 0), segments=32))
    parts.append(ellipsoid(scene, 'Handle tip', (hr, hr, hr), (hx1, fy - .4, hz), 0, black, segments=(24, 12)))
    parts.append(box(scene, 'Drip tray', -10.4, 10.4, fy - .6, fy + 6.6, bay_lo + .4, 4.0, silver, bevel=.3))
    for i in range(6):                            # grate ribs
        x = -8.0 + i * 3.2
        parts.append(box(scene, f'Grate {i}', x - .45, x + .45, fy + .2, fy + 5.8, 3.8, 4.5, silver))
    cupx, cupy = -1.0, fy + 3.0
    parts.append(cone(scene, 'Cup', 2.5, 3.1, 5.9, (cupx, cupy, 3.9 + 2.95), white))          # sits on the tray
    parts.append(ellipsoid(scene, 'Cup handle', (1.3, 1.0, 1.3), (cupx + 3.45, cupy, 7.0), 0, white, segments=(20, 10)))
    m = Matrix.Translation((cx, cy, z0)) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')
    for o in parts:
        o.data.transform(m)
    return parts


def coffee_sack(scene, mats, cx, cy, z0, segments=560):
    """Returns the sack's parts: the woven bag (foot, body, lump, folded collar, mouth) and the unioned beans."""
    apricot, black = mats['apricot'], mats['black']
    # Profile (radius, height, woven?) measured from the render: a soft, pillowy bag that bulges low, narrows
    # to a shadowed neck, then a thick soft collar (band and rolled lip with only a faint crease between them).
    # The lowest ring is below the base top and the next above it.
    # Foot rounds in to about 87 % of the width at the base, as in the render; overhangs stay <= 45 degrees.
    pts = [(12.6, -.6, False), (12.8, .25, False), (13.5, 1.0, True), (14.1, 2.0, True), (14.5, 3.3, True)]
    for z in [4.5 + .3 * i for i in range(int(11.2 / .3) + 1)]:                    # body: almost cylindrical
        t = max(0.0, (z - 9.0) / 6.7)
        pts.append((14.9 - .6 * t ** 1.4, z, True))
    pts += [(14.05, 16.3, True), (13.75, 16.75, True)]                            # shallow neck crease
    for k in range(1, 13):                                                        # collar band: rounds out fast
        t = k / 12
        pts.append((13.75 + .9 * math.sin(min(1.0, t * 2.2) * math.pi / 2), 16.75 + 5.25 * t, True))
    for k in range(1, 17):                                                        # rolled lip: the widest part, merging
        a = math.radians(-55 + 215 * k / 16)                                      # into the band with no hard crease
        pts.append((13.3 + 1.6 * math.cos(a), 23.75 + 1.7 * math.sin(a), k < 9))
    pts += [(11.35, 24.0, False), (10.8, 23.1, False)]                            # inner lip down to the bean bed
    for k in range(1, 7):
        t = k / 7 * math.pi / 2
        pts.append((10.8 * math.cos(t), 23.1 + .7 * math.sin(t), False))
    pitch, depth = 1.0, .14                                                       # fine, soft knit (as rendered)

    def radius(r, z, a, woven):
        # Soft fabric: a lump on the left side under the collar, and slight unevenness all round.
        da = a % (2 * math.pi) - math.pi
        r += .9 * math.exp(-(da / .45) ** 2) * math.exp(-((z - 13.5) / 3.2) ** 2)
        r += .25 * math.sin(3 * a + .7) * math.sin(math.pi * min(max(z, 0), 25) / 25)
        if woven:
            s = r * a                                                             # smooth diamond knit
            r -= depth * (2 - math.cos(2 * math.pi * (s + z) / pitch) - math.cos(2 * math.pi * (s - z) / pitch)) / 4
        return r

    bm = bmesh.new()
    rings = []
    for r, z, woven in pts:
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            rr = radius(r, z, a, woven)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rings.append(ring)
    for ra, rb in zip(rings[:-1], rings[1:]):
        for i in range(segments):
            bm.faces.new((ra[i], ra[(i + 1) % segments], rb[(i + 1) % segments], rb[i]))
    top, bottom = bm.verts.new((0, 0, 23.8)), bm.verts.new((0, 0, -.6))
    for i in range(segments):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % segments], top))
        bm.faces.new((rings[0][(i + 1) % segments], rings[0][i], bottom))
    sack = _obj(scene, 'Sack body', bm, apricot)
    # Beans fill the mouth to just below the lip: a packed layer on the bed plus a few on top.
    beans = []
    n = 64
    for i in range(n):
        rho = 9.4 * math.sqrt((i + .5) / n)
        ang = i * math.radians(137.508)
        zb = 23.1 + .7 * math.sqrt(max(0.0, 1 - (rho / 10.8) ** 2)) + .35 + (.55 if i % 5 == 0 else 0)
        beans.append(ellipsoid(scene, f'Bean {i}', (1.55, 1.05, .8), (rho * math.cos(ang), rho * math.sin(ang), zb),
                               ang * 1.7, black, tilt=.25 * math.sin(i)))
    bean_mass = union_into(beans[0], beans[1:])
    bean_mass.name = 'Coffee beans'
    parts = [sack, bean_mass]
    m = Matrix.Translation((cx, cy, z0))
    for o in parts:
        o.data.transform(m)
    return parts
