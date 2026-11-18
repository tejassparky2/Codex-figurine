"""Approval gate: compare a painted model with customer-approved image(s), pixel by pixel.

For every approved view this tool
  1. separates the figure from the background (alpha channel, --mask, or border colour),
  2. solves the camera (yaw, pitch, roll, scale, shift, perspective) by matching silhouettes,
  3. converts the approved image into finish-slot labels (palette + self-calibrated shading prototypes),
  4. renders the model's own paint labels from the solved camera with a depth-tested triangle-ID raster,
  5. compares the two label images pixel by pixel and reports every disagreeing patch with its faces,
     projected area in mm², 3-D position and a zoomed crop, plus a full tile sheet for vision review.

It never edits the model. Exit code 0 = PASS, 1 = FAIL (clear wrong-colour patches), 2 = CANNOT_JUDGE
(registration or labelling too weak), 3 = NEEDS_REVIEW (only close-call patches between near-identical colours in
the approved art remain; look at each REVIEW crop and fix the model or record why it is right). Compare the approved image with the FINISH GUIDE (one slot per finished colour),
not with the four-head printer project.

usage:
  approved_match.py MODEL OUT --approved front.png [--approved back.png@180 ...]
      MODEL is a single-mesh Orca 3MF with solid paint codes, or a mesh.npz (v, f) with --labels and --palette.
  Options: --prototypes protos.json  {"3": ["#5A0A12", "#8E1B2A"], ...}  extra colours per 1-based slot
           --mask fg.png  (one per --approved, same order)   --camera cam.json (reuse a solved camera)
           --edge-tol-mm 0.35  --max-hard-pct 0.25  --max-blob-mm2 0.6  --min-iou 0.95
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

import cv2
import moderngl as gl
import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import minimize

CODES = ['4', '8'] + [f'{i:X}C' for i in range(14)]   # Orca solid paint codes for slots 1..16


def hex_rgb(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def load_model(path, labels=None, palette=None):
    path = Path(path)
    if path.suffix.lower() == '.3mf':
        with zipfile.ZipFile(path) as z:
            models = [k for k in z.namelist() if k.endswith('.model')]
            s = b''.join(z.read(k) for k in models)
            pal = json.loads(z.read('Metadata/project_settings.config'))['filament_colour']
        if s.count(b'<mesh') != 1:
            raise SystemExit('Expected exactly one mesh in the 3MF')
        v = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', s), 'f8')
        f = np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), 'i4')
        paint = [c.decode() for c in re.findall(rb'<triangle [^>]*?paint_color="([^"]*)"', s)]
        if len(paint) != len(f):
            raise SystemExit('Some triangles have no paint code; export a fully painted finish guide')
        lookup = {c: i for i, c in enumerate(CODES)}
        bad = sorted(set(paint) - set(lookup))[:5]
        if bad:
            raise SystemExit(f'Brush-split paint codes found (e.g. {bad}); decode them to solid per-face labels first')
        lab = np.array([lookup[c] for c in paint], 'i4')
        return v, f, lab, pal if palette is None else palette
    z = np.load(path)
    if labels is None or palette is None:
        raise SystemExit('A mesh.npz needs --labels and --palette')
    return z['v'].astype('f8'), z['f'].astype('i4'), np.load(labels).astype('i4'), palette


class Raster:
    """Depth-tested triangle-ID renderer with an orthographic or weak-perspective camera."""

    def __init__(self, v, f):
        self.ctx = gl.create_standalone_context(backend='egl')
        self.center = (v.min(0) + v.max(0)) / 2
        self.extent = float(np.ptp(v, axis=0).max())
        self.prog = self.ctx.program(vertex_shader="""#version 330
uniform mat3 R; uniform vec3 c0; uniform float s; uniform vec2 t; uniform float k; uniform vec2 size; uniform float dz;
in vec3 pos; flat out int id;
void main(){ vec3 q = R*(pos-c0); float w = 1.0 + k*q.y;
  vec2 p = vec2(t.x + s*q.x/w, t.y - s*q.z/w);
  gl_Position = vec4(p.x/size.x*2.0-1.0, 1.0-p.y/size.y*2.0, q.y/dz, 1.0); id = gl_VertexID/3 + 1; }""",
            fragment_shader="""#version 330
flat in int id; out vec4 col;
void main(){ col = vec4(float(id & 255), float((id >> 8) & 255), float((id >> 16) & 255), 255.0)/255.0; }""")
        self.vao = self.ctx.vertex_array(self.prog, [(self.ctx.buffer(v[f].astype('f4').tobytes()), '3f', 'pos')])
        self.prog['c0'].value = tuple(self.center)
        self.prog['dz'].value = self.extent * 2
        self.fbs = {}

    @staticmethod
    def rotation(yaw, pitch, roll):
        a, b, c = np.deg2rad([yaw, pitch, roll])
        rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
        rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
        ry = np.array([[np.cos(c), 0, np.sin(c)], [0, 1, 0], [-np.sin(c), 0, np.cos(c)]])
        return ry @ rx @ rz

    def ids(self, cam, size):
        """cam = dict(yaw, pitch, roll, s px/mm, tx, ty px, k perspective); size = (W, H). Returns face ids, -1 = background."""
        W, H = size
        if size not in self.fbs:
            self.fbs[size] = self.ctx.simple_framebuffer(size)
        fb = self.fbs[size]
        fb.use()
        fb.clear(0, 0, 0, 0, depth=1)
        self.ctx.enable(gl.DEPTH_TEST)
        self.prog['R'].value = tuple(self.rotation(cam['yaw'], cam['pitch'], cam['roll']).T.ravel())
        self.prog['s'].value = cam['s']
        self.prog['t'].value = (cam['tx'], cam['ty'])
        self.prog['k'].value = cam['k']
        self.prog['size'].value = (W, H)
        self.vao.render()
        pix = np.frombuffer(fb.read(), 'u1').reshape(H, W, 3)[::-1].astype('i4')
        return pix @ np.array([1, 256, 65536], 'i4') - 1


def foreground(img, alpha, mask_path):
    if mask_path:
        return np.asarray(Image.open(mask_path).convert('L')) > 127
    if alpha is not None and alpha.min() < 250:
        return alpha > 127
    lab = cv2.cvtColor(img.astype('f4') / 255, cv2.COLOR_RGB2Lab)
    border = np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    bg = np.median(border, axis=0)
    fg = (np.linalg.norm(lab - bg, axis=2) > 7).astype('u1')
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), 'u1'))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((7, 7), 'u1'))
    n, cc, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    if n > 1:
        big = stats[1:, cv2.CC_STAT_AREA].max()
        keep = np.r_[False, stats[1:, cv2.CC_STAT_AREA] >= .01 * big]
        fg = keep[cc].astype('u1')
    # Fill enclosed holes (a white flower inside the silhouette is still figure).
    flood = fg.copy()
    pad = np.zeros((fg.shape[0] + 2, fg.shape[1] + 2), 'u1')
    cv2.floodFill(flood, pad, (0, 0), 1)
    return (fg | (1 - flood)).astype(bool)


def solve_camera(raster, target, yaw_hint, log):
    H, W = target.shape
    scale = min(1.0, 360 / max(H, W))
    small = cv2.resize(target.astype('u1'), (max(8, int(W * scale)), max(8, int(H * scale))), interpolation=cv2.INTER_AREA) > 0
    h, w = small.shape
    ys, xs = np.nonzero(small)
    tc = np.array([xs.mean(), ys.mean()])
    th = ys.max() - ys.min() + 1
    tw = xs.max() - xs.min() + 1

    def fit(yaw, pitch, roll=0., k=0.):
        cam = dict(yaw=yaw, pitch=pitch, roll=roll, s=.8 * h / raster.extent, tx=w / 2, ty=h / 2, k=k)
        for _ in range(3):
            m = raster.ids(cam, (w, h)) >= 0
            if not m.any():
                return cam, 0.
            yy, xx = np.nonzero(m)
            ratio = .5 * (th / (yy.max() - yy.min() + 1) + tw / (xx.max() - xx.min() + 1))
            c = np.array([xx.mean(), yy.mean()])
            cam['s'] *= ratio
            cam['tx'], cam['ty'] = tc + (np.array([cam['tx'], cam['ty']]) - c) * ratio
        m = raster.ids(cam, (w, h)) >= 0
        return cam, (m & small).sum() / max(1, (m | small).sum())

    yaws = np.arange(-40, 41, 5) + (yaw_hint or 0)
    best = max((fit(y, p) for y in yaws for p in range(-20, 21, 5)), key=lambda r: r[1])
    log(f'  coarse camera: yaw {best[0]["yaw"]:.0f}, pitch {best[0]["pitch"]:.0f}, IoU {best[1]:.4f}')
    # Refine all seven parameters at a finer resolution on a smooth (blurred) target.
    scale2 = min(1.0, 720 / max(H, W))
    W2, H2 = max(8, int(W * scale2)), max(8, int(H * scale2))
    soft = cv2.GaussianBlur(cv2.resize(target.astype('f4'), (W2, H2), interpolation=cv2.INTER_AREA), (0, 0), 1.5)
    c0 = best[0]
    f2 = W2 / w
    x0 = np.array([c0['yaw'], c0['pitch'], 0., np.log(c0['s'] * f2), c0['tx'] * f2, c0['ty'] * f2, 0.])

    def unpack(x):
        return dict(yaw=x[0], pitch=x[1], roll=x[2], s=float(np.exp(x[3])), tx=x[4], ty=x[5], k=float(np.clip(x[6], 0, .02)))

    def loss(x):
        m = raster.ids(unpack(x), (W2, H2)) >= 0
        return 1 - np.minimum(m, soft).sum() / max(1e-6, np.maximum(m, soft).sum())

    steps = np.diag([3, 3, 2, .03, 4, 4, .002])          # yaw, pitch, roll (deg), log scale, tx, ty (px), perspective
    res = minimize(loss, x0, method='Nelder-Mead',
                   options=dict(maxiter=260, xatol=1e-3, fatol=1e-6, initial_simplex=x0 + np.vstack([np.zeros(7), steps])))
    cam = unpack(res.x)
    # Back to full resolution; the perspective factor is per mm of depth and does not depend on image size.
    cam['s'] /= scale2
    cam['tx'] /= scale2
    cam['ty'] /= scale2
    log(f'  refined camera: soft IoU {1 - res.fun:.4f} after {res.nfev} renders')
    return cam


def mode_filter(lab, n_slots, size=3):
    """Replace each pixel's label with the majority in a size×size window (labels >= 0 only)."""
    votes = np.stack([cv2.boxFilter((lab == k).astype('f4'), -1, (size, size), normalize=False) for k in range(n_slots)], -1)
    out = votes.argmax(-1)
    out[lab < 0] = lab[lab < 0]
    return out


def classify(img, fg, palette, extra, margin, seg_k, log):
    lab = cv2.cvtColor(img.astype('f4') / 255, cv2.COLOR_RGB2Lab)
    weight = np.array([.45, 1., 1.], 'f4')         # chroma decides; lightness is mostly shading
    protos, owner, suspects = [], [], []
    for k, h in enumerate(palette):
        for hx in [h] + extra.get(str(k + 1), []):
            if hx.startswith('@'):
                # "@x,y,r": median colour of a small disk the agent picked ON this material in this image.
                x, y, r = (int(float(t)) for t in hx[1:].split(','))
                yy, xx = np.ogrid[:img.shape[0], :img.shape[1]]
                disk = ((xx - x) ** 2 + (yy - y) ** 2 <= r * r) & fg
                if disk.sum() < 5:
                    raise SystemExit(f'Prototype {hx} for slot {k + 1} is off the figure')
                sample = np.median(lab[disk], axis=0)
                protos.append(sample)
                # Anchor sanity check: an anchor nearer another slot's palette colour than its own may be on
                # the wrong material (e.g. a maroon anchor that landed on gold trim). Confirm it by eye.
                base = [cv2.cvtColor(np.array([[hex_rgb(q)]], 'f4') / 255, cv2.COLOR_RGB2Lab)[0, 0] for q in palette]
                near = int(np.argmin([np.linalg.norm((sample - q) * weight) for q in base]))
                rgb = cv2.cvtColor(sample.reshape(1, 1, 3).astype('f4'), cv2.COLOR_Lab2RGB)[0, 0]
                hexs = '#%02X%02X%02X' % tuple(np.clip(np.round(rgb * 255), 0, 255).astype(int))
                if near != k:
                    suspects.append(dict(anchor=hx, slot=k + 1, sampled=hexs, nearest_palette_slot=near + 1))
                    log(f'  CHECK ANCHOR {hx} for slot {k + 1}: sampled {hexs} is nearer slot {near + 1} ({palette[near]})')
            else:
                protos.append(cv2.cvtColor(np.array([[hex_rgb(hx)]], 'f4') / 255, cv2.COLOR_RGB2Lab)[0, 0])
            owner.append(k)
    px = lab[fg]

    def assign(protos, owner):
        d = np.linalg.norm((px[:, None, :] - np.array(protos)[None]) * weight, axis=2)
        per = np.full((len(px), len(palette)), np.inf, 'f4')
        for j, k in enumerate(owner):
            per[:, k] = np.minimum(per[:, k], d[:, j])
        order = np.sort(per, axis=1)
        return per.argmin(1), order[:, 1] - order[:, 0], np.argsort(per, axis=1)[:, 1]

    first, gap, _ = assign(protos, owner)
    calibrated = {}
    # Self-calibration: the approved render shades each material; learn one shaded prototype per slot
    # from its confident pixels, so lit gold or shadowed maroon is not mistaken for a neighbouring slot.
    anchored = {int(k) - 1 for k, v in extra.items() if any(str(e).startswith('@') for e in v)}
    for k in range(len(palette)):
        if k in anchored:
            # The agent's vision-picked anchors are trusted over self-calibration; record their mean as the look.
            mean = np.mean([pr for pr, o in zip(protos, owner) if o == k][1:], axis=0)
            rgb = cv2.cvtColor(mean.reshape(1, 1, 3).astype('f4'), cv2.COLOR_Lab2RGB)[0, 0]
            calibrated[str(k + 1)] = '#%02X%02X%02X' % tuple(np.clip(np.round(rgb * 255), 0, 255).astype(int))
            continue
        sure = (first == k) & (gap > 2 * margin)
        if sure.sum() > 200:
            mean = px[sure].mean(0)
            protos.append(mean)
            owner.append(k)
            rgb = cv2.cvtColor(mean.reshape(1, 1, 3).astype('f4'), cv2.COLOR_Lab2RGB)[0, 0]
            calibrated[str(k + 1)] = '#%02X%02X%02X' % tuple(np.clip(np.round(rgb * 255), 0, 255).astype(int))
    second, gap, runner = assign(protos, owner)
    out = np.full(fg.shape, -1, 'i4')
    lab_px = np.where(gap < margin, -2, second)
    out[fg] = lab_px
    log(f'  calibrated shaded prototypes: {calibrated}')
    sm = mode_filter(np.where(out == -2, -1, out), len(palette))
    out = np.where(out == -2, -2, np.where(fg, sm, -1))
    gapmap = np.zeros(fg.shape, 'f4')
    gapmap[fg] = gap
    runner_up = np.full(fg.shape, -1, 'i4')
    runner_up[fg] = runner
    unsure = fg & ((out == -2) | (gapmap < 2.5 * margin))
    confident_region = np.zeros(fg.shape, bool)
    if seg_k > 0:
        # Region vote: split the approved art along its own colour edges, then let each region take its
        # majority label. Shading inside one garment (shadowed cream vs lit cream) stays one region, so a
        # shadow is not judged on its own against a similar-looking material elsewhere (e.g. face skin).
        bgr = cv2.cvtColor(np.where(fg[..., None], img, 255).astype('u1'), cv2.COLOR_RGB2BGR)
        seg = cv2.ximgproc.segmentation.createGraphSegmentation(.8, seg_k, 30).processImage(bgr)
        seg = np.where(fg, seg, -1)
        nseg = seg.max() + 1
        ok = fg & (out >= 0)
        votes = np.zeros((nseg, len(palette)))
        np.add.at(votes, (seg[ok], out[ok]), 1)
        size = np.bincount(seg[fg], minlength=nseg)
        top = votes.argmax(1)
        decided = votes.sum(1)
        share = votes.max(1) / np.maximum(1, decided)
        strong = (share >= .6) & (decided >= .3 * size)
        # Only unsure pixels are settled by their region; a confident pixel is never overruled, so small
        # details (lips, bindis, catchlights) are not absorbed into the surrounding region.
        take = unsure & strong[np.maximum(seg, 0)]
        out[take] = top[seg[take]]
        confident_region = fg & ((share >= .75) & (decided >= .5 * size))[np.maximum(seg, 0)]
        log(f'  region vote: {nseg} regions; {100 * take.sum() / max(1, fg.sum()):.1f}% of figure pixels (unsure ones) settled by region majority')
    ambiguous = float((out[fg] == -2).mean())
    # Close calls: approved pixels whose best and second-best slot are nearly equally likely and that no
    # confident region vouches for. Disagreements made of these need a vision check, not an automatic verdict.
    close = fg & (gapmap < 2.5 * margin) & ~confident_region
    return out, calibrated, ambiguous, close, suspects, runner_up


def edges(lab):
    e = np.zeros(lab.shape, bool)
    e[:, 1:] |= lab[:, 1:] != lab[:, :-1]
    e[1:, :] |= lab[1:, :] != lab[:-1, :]
    return e


def run_view(raster, faces_xyz, labels, palette, img_path, yaw_hint, mask_path, camera, args, outdir, log):
    pil = Image.open(img_path)
    alpha = np.asarray(pil.convert('RGBA'))[..., 3] if 'A' in pil.getbands() else None
    img = np.asarray(pil.convert('RGB'))
    H, W = img.shape[:2]
    fg = foreground(img, alpha, mask_path)
    cam = camera or solve_camera(raster, fg, yaw_hint, log)
    ids = raster.ids(cam, (W, H))
    model_fg = ids >= 0
    iou = float((model_fg & fg).sum() / max(1, (model_fg | fg).sum()))
    log(f'  camera {json.dumps({k: round(float(v), 4) for k, v in cam.items()})}  silhouette IoU {iou:.4f}')
    target, calibrated, ambiguous, close, suspects, runner_up = classify(img, fg, palette, args.extra, args.margin, args.segment_k, log)
    model = np.where(model_fg, np.r_[labels, -1][ids], -1)
    drift = dict(median=0., p95=0., max=0.)
    if args.local_align_mm > 0:
        # Generated meshes never match the approved art exactly. Estimate only the large-scale shape drift
        # (optical flow, smoothed over --align-smooth-mm and capped at --local-align-mm) and pull the approved
        # labels onto the model. A patch smaller than the smoothing radius cannot be explained away.
        look = np.array([hex_rgb(calibrated.get(str(k + 1), h)) for k, h in enumerate(palette)], 'u1')
        model_look = np.full(img.shape, 255, 'u1')
        model_look[model_fg] = look[model[model_fg]]
        g1 = cv2.cvtColor(model_look, cv2.COLOR_RGB2GRAY)
        g2 = cv2.cvtColor(np.where(fg[..., None], img, 255).astype('u1'), cv2.COLOR_RGB2GRAY)
        flow = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM).calc(g1, g2, None)
        sigma = args.align_smooth_mm * cam['s']
        wgt = cv2.GaussianBlur(model_fg.astype('f4'), (0, 0), sigma) + 1e-6
        flow = np.dstack([cv2.GaussianBlur(flow[..., i] * model_fg, (0, 0), sigma) / wgt for i in range(2)])
        mag = np.linalg.norm(flow, axis=2)
        cap = args.local_align_mm * cam['s']
        flow *= np.minimum(1, cap / np.maximum(mag, 1e-6))[..., None]
        mags = np.linalg.norm(flow, axis=2)[model_fg] / cam['s']
        drift = dict(median=round(float(np.median(mags)), 3), p95=round(float(np.percentile(mags, 95)), 3), max=round(float(mags.max()), 3))
        gx, gy = np.meshgrid(np.arange(W, dtype='f4'), np.arange(H, dtype='f4'))
        mx, my = gx + flow[..., 0], gy + flow[..., 1]
        t2 = cv2.remap(target.astype('f4'), mx, my, cv2.INTER_NEAREST, borderValue=-1).astype('i4')
        fg2 = cv2.remap(fg.astype('u1'), mx, my, cv2.INTER_NEAREST, borderValue=0) > 0

        def agreement(t, g):
            ok = g & model_fg & (t >= 0)
            return ((t == model) & ok).sum() / max(1, (g | model_fg).sum())

        before, after = agreement(target, fg), agreement(t2, fg2)
        iou_aligned = float((model_fg & fg2).sum() / max(1, (model_fg | fg2).sum()))
        log(f'  local alignment: drift median {drift["median"]} mm, p95 {drift["p95"]} mm, max {drift["max"]} mm; '
            f'label agreement {before:.4f} -> {after:.4f}; silhouette IoU {iou:.4f} -> {iou_aligned:.4f}')
        if after > before:
            target, fg, iou = t2, fg2, iou_aligned
            close = cv2.remap(close.astype('u1'), mx, my, cv2.INTER_NEAREST, borderValue=0) > 0
            runner_up = cv2.remap(runner_up.astype('f4'), mx, my, cv2.INTER_NEAREST, borderValue=-1).astype('i4')
            img = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderValue=(255, 255, 255))
        else:
            drift = dict(median=0., p95=0., max=0., rejected=True)
            log('  local alignment rejected: it did not improve label agreement')
    both = fg & model_fg
    tol = max(1, int(round(args.edge_tol_mm * cam['s'])))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * tol + 1, 2 * tol + 1))
    band = cv2.dilate((edges(target) | edges(model)).astype('u1'), kernel) > 0
    valid = both & (target >= 0)
    # A close call whose runner-up is the model's colour is consistent with the art within its own uncertainty.
    consistent = valid & (target != model) & close & (runner_up == model)
    differ = valid & (target != model) & ~consistent
    hard = differ & ~band
    px_mm2 = 1 / cam['s'] ** 2
    # Boundary placement: distance from each model paint edge to the nearest approved edge, inside the figure.
    te = edges(np.where(valid, target, -1)) & valid
    me = edges(np.where(valid, model, -1)) & valid
    dist = cv2.distanceTransform((~te).astype('u1'), cv2.DIST_L2, 5)[me] / cam['s'] if te.any() and me.any() else np.zeros(1)
    n, cc, stats, cent = cv2.connectedComponentsWithStats(hard.astype('u1'), 8)
    blobs = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < args.min_blob_px:
            continue
        sel = cc == i
        fids = np.unique(ids[sel])
        fids = fids[fids >= 0]
        blobs.append(dict(
            id=0, area_mm2=round(float(area * px_mm2), 3), pixels=int(area),
            approved_slot=int(np.bincount(target[sel]).argmax()) + 1,
            model_slot=int(np.bincount(model[sel]).argmax()) + 1,
            needs_review=bool(close[sel].mean() > .5),
            bbox_px=[int(stats[i, 0]), int(stats[i, 1]), int(stats[i, 2]), int(stats[i, 3])],
            centroid_mm=[round(float(c), 2) for c in faces_xyz[fids].mean(0)] if len(fids) else None,
            faces=fids))
    blobs.sort(key=lambda b: -b['area_mm2'])
    for i, b in enumerate(blobs):
        b['id'] = i + 1
    per_slot = []
    for k in range(len(palette)):
        a, m = valid & (target == k), valid & (model == k)
        if a.any() or m.any():
            per_slot.append(dict(slot=k + 1, color=palette[k], approved_mm2=round(float(a.sum() * px_mm2), 1),
                                 model_mm2=round(float(m.sum() * px_mm2), 1), iou=round(float((a & m).sum() / max(1, (a | m).sum())), 4)))
    conf = np.zeros((len(palette), len(palette)), int)
    np.add.at(conf, (target[valid], model[valid]), 1)
    hard_pct = 100 * hard.sum() / max(1, valid.sum())
    firm = [b for b in blobs if not b['needs_review']]
    review = [b for b in blobs if b['needs_review']]
    firm_px = sum(b['pixels'] for b in firm)
    largest = blobs[0]['area_mm2'] if blobs else 0.
    largest_firm = firm[0]['area_mm2'] if firm else 0.
    reasons = []
    if iou < args.min_iou:
        verdict = 'CANNOT_JUDGE'
        reasons.append(f'silhouette IoU {iou:.3f} < {args.min_iou}: pose or geometry differs; supply a mask or camera')
    elif ambiguous > args.max_ambiguous:
        verdict = 'CANNOT_JUDGE'
        reasons.append(f'{100 * ambiguous:.1f}% of approved pixels match no slot clearly; add --prototypes')
    else:
        verdict = 'PASS'
        firm_pct = 100 * firm_px / max(1, valid.sum())
        if firm_pct > args.max_hard_pct or largest_firm > args.max_blob_mm2:
            verdict = 'FAIL'
            reasons.append(f'clear colour errors: {firm_pct:.3f}% of figure pixels, largest patch {largest_firm:.2f} mm2 '
                           f'(limits {args.max_hard_pct}%, {args.max_blob_mm2} mm2)')
        if hard_pct > args.max_hard_pct or largest > args.max_blob_mm2:
            if verdict == 'PASS':
                verdict = 'NEEDS_REVIEW'
            reasons.append(f'{len(review)} close-call patches (similar colours in the approved art) need a vision verdict; '
                           f'see patches/ marked REVIEW')
    outdir.mkdir(parents=True, exist_ok=True)
    pal_rgb = np.array([hex_rgb(h) for h in palette], 'u1')

    def paint(lbl):
        im = np.full(lbl.shape + (3,), 255, 'u1')
        im[lbl >= 0] = pal_rgb[lbl[lbl >= 0]]
        im[lbl == -2] = (255, 0, 255)
        return im

    diff = (img * .35 + 160).astype('u1')
    diff[differ & band] = (255, 200, 0)
    diff[hard] = (230, 0, 0)
    diff[fg ^ model_fg] = (0, 120, 255)
    sheet = np.concatenate([img, paint(model), paint(target), diff], 1)
    Image.fromarray(sheet).save(outdir / 'side_by_side.png')
    # Zoomed crops of each wrong patch: approved | model paint | difference.
    zdir = outdir / 'patches'
    zdir.mkdir(exist_ok=True)
    model_img = paint(model)
    for b in blobs[:args.max_crops]:
        x, y, w, h = b['bbox_px']
        r = max(w, h) // 2 + max(12, tol * 4)
        cx, cy = x + w // 2, y + h // 2
        x0, y0, x1, y1 = max(0, cx - r), max(0, cy - r), min(W, cx + r), min(H, cy + r)
        tiles = [a[y0:y1, x0:x1] for a in (img, model_img, diff)]
        z = max(1, 360 // max(1, max(y1 - y0, x1 - x0)))
        row = np.concatenate([np.kron(t, np.ones((z, z, 1), 'u1')) for t in tiles], 1)
        canvas = Image.new('RGB', (row.shape[1], row.shape[0] + 28), 'white')
        canvas.paste(Image.fromarray(row), (0, 28))
        ImageDraw.Draw(canvas).text((6, 6), f"{'REVIEW ' if b['needs_review'] else 'ERROR '}patch {b['id']}: approved slot {b['approved_slot']} ({palette[b['approved_slot'] - 1]}) "
                                    f"vs model slot {b['model_slot']} ({palette[b['model_slot'] - 1]}), {b["area_mm2"]} mm2, "
                                    f"{len(b['faces'])} faces, at {b['centroid_mm']} mm", fill='black')
        canvas.save(zdir / f"patch-{b['id']:03d}.png")
    # Full-coverage tile sheets for vision review: every tile of the figure, approved beside model.
    tdir = outdir / 'tiles'
    tdir.mkdir(exist_ok=True)
    step = args.tile_px
    tiles = []
    for ty in range(0, H, step):
        for tx in range(0, W, step):
            sl = (slice(ty, min(H, ty + step)), slice(tx, min(W, tx + step)))
            if fg[sl].mean() < .02:
                continue
            tiles.append(dict(x=tx, y=ty, hard_px=int(hard[sl].sum()), edge_px=int((differ & band)[sl].sum())))
    per_page = 12
    for p in range(0, len(tiles), per_page):
        page = Image.new('RGB', (3 * (4 * step + 24), 4 * (2 * step + 30)), 'white')
        d = ImageDraw.Draw(page)
        for j, t in enumerate(tiles[p:p + per_page]):
            sl = (slice(t['y'], t['y'] + step), slice(t['x'], t['x'] + step))
            pair = np.concatenate([np.pad(a[sl], ((0, step - a[sl].shape[0]), (0, step - a[sl].shape[1]), (0, 0)), constant_values=255)
                                   for a in (img, model_img)], 1)
            pair = np.kron(pair, np.ones((2, 2, 1), 'u1'))
            gx, gy = (j % 3) * (4 * step + 24), (j // 3) * (2 * step + 30)
            page.paste(Image.fromarray(pair), (gx, gy + 24))
            flag = 'WRONG' if t['hard_px'] else ('edge' if t['edge_px'] else 'ok')
            d.text((gx + 4, gy + 6), f"tile x{t['x']} y{t['y']}: {flag} (hard {t['hard_px']} px, edge {t['edge_px']} px)",
                   fill='red' if t['hard_px'] else 'black')
        page.save(tdir / f'sheet-{p // per_page + 1:02d}.png')
    np.savez_compressed(outdir / 'patch_faces.npz', **{f"patch_{b['id']:03d}": b['faces'] for b in blobs},
                        approved_slot=np.array([b['approved_slot'] for b in blobs]))
    (outdir / 'camera.json').write_text(json.dumps({k: float(v) for k, v in cam.items()}, indent=1))
    report = dict(
        image=str(img_path), verdict=verdict, reasons=reasons, silhouette_iou=round(iou, 4), shape_drift_mm=drift,
        px_per_mm=round(cam['s'], 3), edge_tolerance_mm=args.edge_tol_mm,
        figure_pixels=int(valid.sum()), ambiguous_pct=round(100 * ambiguous, 3),
        hard_mismatch_pct=round(hard_pct, 4), consistent_close_call_pct=round(100 * consistent.sum() / max(1, valid.sum()), 4), edge_band_mismatch_pct=round(100 * (differ & band).sum() / max(1, valid.sum()), 4),
        boundary_offset_mm=dict(median=round(float(np.median(dist)), 3), p95=round(float(np.percentile(dist, 95)), 3)),
        suspect_anchors=suspects, patches=len(blobs), review_patches=len(review), largest_patch_mm2=largest, largest_clear_error_mm2=largest_firm, calibrated_prototypes=calibrated,
        per_slot=per_slot, confusion_rows_approved_cols_model=conf.tolist(),
        tiles=dict(total=len(tiles), wrong=sum(t['hard_px'] > 0 for t in tiles), sheets=-(-len(tiles) // per_page)),
        top_patches=[{k: v for k, v in b.items() if k != 'faces'} | dict(face_count=len(b['faces'])) for b in blobs[:40]])
    (outdir / 'report.json').write_text(json.dumps(report, indent=1))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('model')
    p.add_argument('out', type=Path)
    p.add_argument('--approved', action='append', required=True, help='image path, optionally @yaw-hint in degrees')
    p.add_argument('--mask', action='append', default=[])
    p.add_argument('--camera', action='append', default=[])
    p.add_argument('--labels')
    p.add_argument('--palette', help='comma-separated hex list for mesh.npz input')
    p.add_argument('--prototypes', help='JSON of extra colours per 1-based slot')
    p.add_argument('--edge-tol-mm', type=float, default=.35)
    p.add_argument('--margin', type=float, default=4., help='Lab gap below which an approved pixel is ambiguous')
    p.add_argument('--max-hard-pct', type=float, default=.25)
    p.add_argument('--max-blob-mm2', type=float, default=.6)
    p.add_argument('--min-iou', type=float, default=.95)
    p.add_argument('--max-ambiguous', type=float, default=.05)
    p.add_argument('--min-blob-px', type=int, default=4)
    p.add_argument('--max-crops', type=int, default=60)
    p.add_argument('--tile-px', type=int, default=96)
    p.add_argument('--local-align-mm', type=float, default=2.0, help='cap on smoothed shape-drift correction; 0 = rigid camera only')
    p.add_argument('--segment-k', type=float, default=300, help='region-vote granularity of the approved art (0 = per-pixel only)')
    p.add_argument('--align-smooth-mm', type=float, default=4.0, help='smoothing radius of the drift field; keep well above the smallest leak you must catch')
    args = p.parse_args()
    args.extra = json.loads(Path(args.prototypes).read_text()) if args.prototypes else {}
    v, f, labels, palette = load_model(args.model, args.labels, args.palette.split(',') if args.palette else None)
    raster = Raster(v, f)
    centers = v[f].mean(1)
    args.out.mkdir(parents=True, exist_ok=True)
    log_lines = []

    def log(s):
        print(s, flush=True)
        log_lines.append(s)

    summary = []
    for i, spec in enumerate(args.approved):
        path, _, hint = spec.partition('@')
        log(f'view {i + 1}: {path}')
        cam = json.loads(Path(args.camera[i]).read_text()) if i < len(args.camera) else None
        rep = run_view(raster, centers, labels, palette, path, float(hint) if hint else None,
                       args.mask[i] if i < len(args.mask) else None, cam, args, args.out / f'view{i + 1}', log)
        log(f"  {rep['verdict']}: hard mismatch {rep['hard_mismatch_pct']}%, {rep['patches']} patches, "
            f"largest {rep['largest_patch_mm2']} mm², boundary offset median {rep['boundary_offset_mm']['median']} mm "
            f"{'; '.join(rep['reasons'])}")
        summary.append(rep['verdict'])
    overall = next((v for v in ('CANNOT_JUDGE', 'FAIL', 'NEEDS_REVIEW') if v in summary), 'PASS')
    (args.out / 'gate.txt').write_text(overall + '\n' + '\n'.join(log_lines) + '\n')
    print('GATE', overall)
    sys.exit({'PASS': 0, 'FAIL': 1, 'CANNOT_JUDGE': 2, 'NEEDS_REVIEW': 3}[overall])


if __name__ == '__main__':
    main()
