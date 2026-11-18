"""Regression test for approved_match.py. Run after every change to the gate.

1. Renders a shaded, anti-aliased "approved" image of a finish guide from a hidden camera.
2. The unchanged model must PASS and the solved camera must match the hidden one.
3. A planted leak (a patch of skin repainted ivory, or the slots given) must FAIL, and the largest
   reported patch must sit on the planted faces.

usage: approved_match_selftest.py FINISH_GUIDE.3mf WORKDIR [--from-slot 5 --to-slot 3]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import trimesh
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from approved_match import Raster, load_model, hex_rgb  # noqa: E402

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('guide')
p.add_argument('work', type=Path)
p.add_argument('--from-slot', type=int, default=5)
p.add_argument('--to-slot', type=int, default=3)
p.add_argument('--patch-faces', type=int, default=1500)
A = p.parse_args()
A.work.mkdir(parents=True, exist_ok=True)
gate = Path(__file__).with_name('approved_match.py')
v, f, labels, palette = load_model(A.guide)
mesh = trimesh.Trimesh(v, f, process=False)
r = Raster(v, f)
W, H = 900, 1200
hidden = dict(yaw=6.0, pitch=4.0, roll=1.0, s=H * .8 / np.ptp(v[:, 2]), tx=W / 2 + 7, ty=H / 2 - 5, k=.003)


def shaded(lbl):
    big = {kk: (vv * 2 if kk in ('s', 'tx', 'ty') else vv) for kk, vv in hidden.items()}
    ids = r.ids(big, (2 * W, 2 * H))
    pal = np.array([hex_rgb(h) for h in palette], 'f4')
    light = np.array([-.35, -.85, .45]) / np.linalg.norm([-.35, -.85, .45])
    shade = .70 + .30 * np.clip(mesh.face_normals @ light, 0, 1)
    img = np.full(ids.shape + (3,), 255., 'f4')
    m = ids >= 0
    img[m] = pal[lbl[ids[m]]] * shade[ids[m], None]
    return cv2.resize(np.clip(img, 0, 255).astype('u1'), (W, H), interpolation=cv2.INTER_AREA), ids[::2, ::2]


approved, ids = shaded(labels)
Image.fromarray(approved).save(A.work / 'approved.png')
np.savez(A.work / 'mesh.npz', v=v, f=f)
np.save(A.work / 'clean.npy', labels)


def run(lbl_path, out):
    cmd = [sys.executable, str(gate), str(A.work / 'mesh.npz'), str(A.work / out), '--approved', str(A.work / 'approved.png'),
           '--labels', str(lbl_path), '--palette', ','.join(palette)]
    code = subprocess.run(cmd).returncode
    return code, json.loads((A.work / out / 'view1' / 'report.json').read_text()), json.loads((A.work / out / 'view1' / 'camera.json').read_text())


code, rep, cam = run(A.work / 'clean.npy', 'clean')
err = {k: round(cam[k] - hidden[k], 4) for k in hidden}
print('camera error', err)
ok = code == 0 and abs(err['yaw']) < 1.5 and abs(err['pitch']) < 1.5 and abs(err['s']) / hidden['s'] < .01
print('clean model:', rep['verdict'], 'PASS expected ->', 'ok' if ok else 'BROKEN')

# Plant a visible leak: grow a patch of from-slot faces around a visible seed and repaint it.
visible = np.unique(ids[ids >= 0])
cand = visible[labels[visible] == A.from_slot - 1]
rng = np.random.default_rng(7)
seed = cand[rng.integers(len(cand))]
centers = v[f].mean(1)
order = np.argsort(np.linalg.norm(centers[cand] - centers[seed], axis=1))
patch = cand[order[:A.patch_faces]]
leaky = labels.copy()
leaky[patch] = A.to_slot - 1
np.save(A.work / 'leaky.npy', leaky)
code2, rep2, _ = run(A.work / 'leaky.npy', 'leaky')
top = rep2['top_patches'][0] if rep2['top_patches'] else None
dist = np.linalg.norm(np.array(top['centroid_mm']) - centers[patch].mean(0)) if top else np.inf
planted_mm2 = mesh.area_faces[patch].sum()
found = code2 == 1 and dist < 3 and top['approved_slot'] == A.from_slot and top['model_slot'] == A.to_slot
print(f'planted {len(patch)} faces ({planted_mm2:.1f} mm² of surface) at {centers[patch].mean(0).round(2)}')
print('leaky model:', rep2['verdict'], f"top patch {top and top['area_mm2']} mm² at {top and top['centroid_mm']} ({dist:.2f} mm off)",
      'FAIL expected ->', 'ok' if found else 'BROKEN')
sys.exit(0 if ok and found else 1)
