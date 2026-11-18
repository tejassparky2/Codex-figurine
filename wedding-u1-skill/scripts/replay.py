"""Build in a new directory using the interpreter that launches this script."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('job', type=Path)
parser.add_argument('--decimate', action='store_true', help='Regenerate the working mesh instead of using the recorded one.')
args = parser.parse_args()
job = args.job.resolve()
job.mkdir(parents=True, exist_ok=True)
if any(job.iterdir()):
    parser.error('Choose an empty job directory to preserve existing work.')
for name in ['scripts', 'toolkit']:
    shutil.copytree(root / name, job / name)
shutil.copytree(root / 'inputs', job, dirs_exist_ok=True)
def run(*argv):
    print('Running', *argv, flush=True)
    subprocess.run([sys.executable, *argv], cwd=job, check=True)
if args.decimate:
    run('scripts/decimate.py')
run('toolkit/scripts/clean_colorize.py','source.glb','--geometry','geometry.ply','--palette','#F4B27F,#261D19,#771020,#D62621,#EFB333,#FFF2D9,#954F32,#DF6561','--height','120','--up-axis','y','--geometry-up-axis','y','--deshade','0','--no-shadow-fix','--lam','4','--min-island','.16','-o','first.3mf')
run('scripts/wfix.py')
run('scripts/wtex.py','source.glb','--height','120','-o','Wedding-full-color.3mf')
for stage in ['clean-detail','clean-check','wgaze','smoothu','matfix','flatjob','flatprint','latesthero']:
    run('scripts/'+stage+'.py')
from PIL import Image
with Image.open(job / 'Flat-finish-front.png') as front:
    front.crop((260, 566, 680, 1021)).save(job / 'Flat-hands-and-flowers.png')
