"""Shared runner. Invoke from repository root after replay and practice scoring."""
import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TOOLS = ROOT / 'wedding-u1-skill/coloring'
GUIDE = ROOT / 'Wedding-150mm-reviewed-paint-guide.3mf'
JUDGE = ROOT / 'jobs/wedding-couple/judge'
CAMERA = ROOT / 'scoreboard/runs/wedding-couple/round-1/codex/view1/camera.json'
sys.path.insert(0, str(TOOLS))


def gate(work, name, model=GUIDE, art=None, camera=CAMERA, program=None, extra=()):
    args = [sys.executable, '-I', str(program or TOOLS / 'approved_match.py'),
            str(model), str(work / name), '--approved', str(art or JUDGE / 'approved-front.png'),
            '--camera', str(camera)]
    if art is None:
        args.extend(['--prototypes', str(JUDGE / 'anchors.json')])
    start = time.monotonic()
    with (work / (name + '.log')).open('w') as log:
        rc = subprocess.run(args + list(map(str, extra)), stdout=log, stderr=subprocess.STDOUT).returncode
    view = work / name / 'view1'
    report = json.loads((view / 'report.json').read_text())
    assert rc == {'PASS': 0, 'FAIL': 1, 'CANNOT_JUDGE': 2, 'NEEDS_REVIEW': 3}[report['verdict']]
    return dict(verdict=report['verdict'], clear=report['hard_mismatch_pct'],
                largest=report['largest_clear_error_mm2'], review=report['review_patches'],
                p95=report['boundary_offset_mm']['p95'], iou=report['silhouette_iou'],
                ambiguous=report['ambiguous_pct'], seconds=round(time.monotonic()-start, 2))


def evidence(work, names, destination, box=None):
    """Full frame, same-coordinate crop, and an actual gate tile for each arm."""
    reports = [json.loads((work/n/'view1/report.json').read_text()) for n in names]
    patches = [p for r in reports for p in r['top_patches']]
    if box is None and patches:
        box = max(patches, key=lambda p: p['area_mm2'])['bbox_px']
    canvas = Image.new('RGB', (900, 410*len(names)), 'white')
    draw = ImageDraw.Draw(canvas)
    for i, name in enumerate(names):
        v = work/name/'view1'
        y = i*410
        im = Image.open(v/'side_by_side.png').convert('RGB')
        w, h = im.width//4, im.height
        thumb = im.copy()
        thumb.thumbnail((890,195))
        canvas.paste(thumb,(0,y+20))
        draw.text((4,y+2), name+'   reference / model / classified reference / disagreement',fill='black')
        x,t,bw,bh = box or (w//3,h//3,32,32)
        half=max(24,max(bw,bh)//2+10)
        cx,cy=x+bw//2,t+bh//2
        bounds=(max(0,cx-half),max(0,cy-half),min(w,cx+half),min(h,cy+half))
        for j in range(4):
            x0,y0,x1,y1=bounds
            tile=im.crop((x0+j*w,y0,x1+j*w,y1))
            tile.thumbnail((175,175))
            if max(tile.size)<175:
                tile=tile.resize(tuple(round(d*175/max(tile.size)) for d in tile.size),Image.Resampling.NEAREST)
            canvas.paste(tile,(j*180,y+232))
        draw.text((4,y+215),f'Fixed image crop {bounds}',fill='black')
        tile=Image.open(next(iter(sorted((v/'tiles').glob('*.png')))))
        tile.thumbnail((175,170))
        canvas.paste(tile,(721,y+232))
    canvas.save(destination,quality=90)
