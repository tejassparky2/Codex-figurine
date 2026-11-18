"""Espresso machine and burlap coffee sack for the Deepak base (imported by make_base.py inside Blender).

Both are modelled in millimetres, standing on the base top at z0, and styled after the approved render:
- Machine: black rounded housing with cup-warmer fins, a silver control panel with three black knobs, a black
  side knob, an open brewing bay with a silver back panel, group head and portafilter, a black handle, a silver
  drip tray and a white cup.
- Sack: a bulging burlap sack with a woven cross-hatch, a rolled rim and a mound of black coffee beans.

Print-driven choices: the portafilter handle rises at about 38 degrees, so it needs little or no support; the group head and portafilter are frustums tied into the back wall; protrusions on
vertical faces are at most 2 mm; the bay ceiling is a 22 mm bridge.
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


def ellipsoid(scene, name, radii, loc, yaw, mat):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
    m = Matrix.Translation(loc) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Diagonal((*radii, 1))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return _obj(scene, name, bm, mat)


def espresso_machine(scene, mats, cx, cy, z0, yaw_deg=0.0):
    """Returns the machine's parts (front faces -Y before the yaw)."""
    black, silver, white = mats['black'], mats['silver'], mats['white']
    W, D, Hm = 28.0, 22.0, 40.0
    fy = -D / 2                                   # front face plane (local)
    parts = []
    body = box(scene, 'Machine body', -W / 2, W / 2, fy, D / 2, -0.73, Hm, black, bevel=1.2)   # sunk in, no ring on the top plane
    # Brewing bay: an open recess in the lower front.
    bay_top = 23.0
    bay = box(scene, 'bay cut', -11, 11, fy - 2, fy + 7, 5, bay_top, black)
    mod = body.modifiers.new('bay', 'BOOLEAN')
    mod.operation, mod.solver, mod.object = 'DIFFERENCE', 'EXACT', bay
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(bay, do_unlink=True)
    parts.append(body)
    parts.append(box(scene, 'Bay back panel', -10.4, 10.4, fy + 6.4, fy + 7.4, 5.4, bay_top - .4, silver))
    for i in range(7):                            # cup-warmer fins on the top front
        x = -10.5 + i * 3.5
        parts.append(box(scene, f'Fin {i}', x - .6, x + .6, fy + 1.0, fy + 7.0, Hm - .6, Hm + 2.6, black, bevel=.25))
    parts.append(box(scene, 'Control panel', -11.5, 11.5, fy - .9, fy + .5, 25.5, 36.5, silver, bevel=.6))
    for x in (-7.0, 0.0, 7.0):                    # three knobs
        parts.append(cone(scene, f'Knob {x:+.0f}', 2.7, 2.4, 2.4, (x, fy - .9 - .9, 31.0), black, axis=(0, -1, 0)))
    parts.append(cone(scene, 'Side knob', 2.2, 2.0, 2.6, (W / 2 + .9, 2.0, 33.0), black, axis=(1, 0, 0)))
    # Group head and portafilter: frustums narrowing downward, tied into the ceiling and the back wall.
    gx, gy = -2.0, fy + 4.6
    parts.append(cone(scene, 'Group head', 3.4, 4.6, 2.8, (gx, gy, bay_top - 1.2), silver))
    parts.append(cone(scene, 'Portafilter', 2.9, 3.6, 2.0, (gx, gy, bay_top - 3.4), silver))
    # Handle: out of the bay opening, to the right and up (~38 degrees), clear of the ceiling lip and the panel.
    d = Vector((.35, -.70, .62)).normalized()
    start = Vector((gx + 2.6, gy - 1.0, bay_top - 3.8))
    parts.append(cone(scene, 'Portafilter handle', 1.15, 1.25, 8.0, start + d * 4.0, black, axis=tuple(d), segments=24))
    parts.append(box(scene, 'Drip tray', -10.4, 10.4, fy - .6, fy + 6.6, 4.6, 6.8, silver, bevel=.3))
    for i in range(6):                            # grate ribs
        x = -8.0 + i * 3.2
        parts.append(box(scene, f'Grate {i}', x - .45, x + .45, fy + .2, fy + 5.8, 6.6, 7.3, silver))
    parts.append(cone(scene, 'Cup', 2.6, 3.2, 5.0, (gx, gy - .4, 6.7 + 2.5), white))          # rests on the tray
    parts.append(box(scene, 'Cup handle', gx + 2.9, gx + 4.6, gy - .9, gy + .1, 7.9, 10.7, white, bevel=.3))
    m = Matrix.Translation((cx, cy, z0)) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')
    for o in parts:
        o.data.transform(m)
    return parts


def coffee_sack(scene, mats, cx, cy, z0, segments=400, scale=1.15):
    """Returns the sack's parts: woven body with rolled rim and bean-mound top, then the beans."""
    apricot, black = mats['apricot'], mats['black']
    # The bottom ring sits below the base top and the next one above it, so no ring lies in that plane.
    prof = [(10.0, -.6), (10.05, .25), (10.6, .8)]
    z = 1.0
    while z < 17.0:
        prof.append((10.6 + 1.9 * math.sin(math.pi * z / 19.0), z))
        z += .15
    # The bean dome starts inside the rolled rim's tube, so the two surfaces cross at a clear angle (a near-
    # tangent meeting left open edges in the exact boolean).
    # Rolled rim as part of the same lathe profile (a separate torus left open edges in the exact boolean):
    # out and over a 1.5 mm round, then in to the bean dome.
    DOME_R, DOME_Z, DOME_H = 9.8, 19.0, 3.4         # a heaped mound, as in the approved render
    rc, rr = (11.6, 18.8), 1.5
    prof += [(11.15, 17.2)]
    for k in range(0, 19):
        a = math.radians(-90 + 270 * k / 18)
        prof.append((rc[0] + rr * math.cos(a), rc[1] + rr * math.sin(a)))
    prof += [(DOME_R, DOME_Z)]
    for k in range(1, 9):                         # low dome where the beans sit
        t = k / 9 * math.pi / 2
        prof.append((DOME_R * math.cos(t), DOME_Z + DOME_H * math.sin(t)))
    pitch, depth, width = 1.6, .35, .17          # grooves wider than the mesh spacing, so the weave does not alias

    def weave(r, zz, a):
        if not 1.2 < zz < 16.6:
            return r
        s = r * a
        g1 = abs((s + zz) / pitch - round((s + zz) / pitch))
        g2 = abs((s - zz) / pitch - round((s - zz) / pitch))
        return r - depth * max(math.exp(-(g1 / width) ** 2), math.exp(-(g2 / width) ** 2))

    bm = bmesh.new()
    rings = []
    for r, zz in prof:
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            rr = weave(r, zz, a)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), zz)))
        rings.append(ring)
    for ra, rb in zip(rings[:-1], rings[1:]):
        for i in range(segments):
            bm.faces.new((ra[i], ra[(i + 1) % segments], rb[(i + 1) % segments], rb[i]))
    top, bottom = bm.verts.new((0, 0, DOME_Z + DOME_H)), bm.verts.new((0, 0, -.6))
    for i in range(segments):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % segments], top))
        bm.faces.new((rings[0][(i + 1) % segments], rings[0][i], bottom))
    parts = [_obj(scene, 'Sack body', bm, apricot)]
    # Beans: a phyllotaxis mound on the dome, each a small ellipsoid partly sunk into it.
    n = 60
    for i in range(n):
        rho = 8.0 * math.sqrt((i + .5) / n)       # beans stay clear of the rim tube
        ang = i * math.radians(137.508)
        zs = DOME_Z + DOME_H * math.sqrt(max(0.0, 1 - (rho / DOME_R) ** 2))
        parts.append(ellipsoid(scene, f'Bean {i}', (1.7, 1.2, .9), (rho * math.cos(ang), rho * math.sin(ang), zs + .3),
                               ang * 1.7, black))
    m = Matrix.Translation((cx, cy, z0)) @ Matrix.Scale(scale, 4)   # 1.15: about 29 x 25 mm, as in the approved render
    for o in parts:
        o.data.transform(m)
    return parts
