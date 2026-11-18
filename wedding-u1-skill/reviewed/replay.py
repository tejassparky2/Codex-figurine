"""Reproduce the wedding review from the two published material-locked checkpoints."""
import argparse
from pathlib import Path
import subprocess
import sys
import zipfile

here = Path(__file__).resolve().parent
skill = here.parent
repo = skill.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('job', type=Path)
parser.add_argument('--skip-report', action='store_true')
args = parser.parse_args()
job = args.job.resolve()
job.mkdir(parents=True, exist_ok=True)
if any(job.iterdir()):
    parser.error('Choose an empty output directory.')
for source in [
    skill/'inputs/source.glb', skill/'inputs/reference',
    repo/'Wedding-150mm-material-locked-finish.3mf', repo/'Wedding-U1-150mm-material-locked.3mf',
    repo/'Wedding-U1-repaired-020.3mf', repo/'Wedding-finish-repaired.3mf',
]:
    job.joinpath(source.name).symlink_to(source.resolve(strict=True))
stages = ['repair', 'render', 'source', 'paint', 'detail', 'export']
if not args.skip_report:
    stages.append('report')
for stage in stages:
    print(f'Running {stage}', flush=True)
    subprocess.run([sys.executable, here/(stage+'.py')], cwd=job, check=True)
for name in ['Wedding-U1-150mm-reviewed.3mf', 'Wedding-150mm-reviewed-paint-guide.3mf']:
    with zipfile.ZipFile(repo/name) as expected, zipfile.ZipFile(job/name) as actual:
        if set(expected.namelist()) != set(actual.namelist()) or any(
            expected.read(member) != actual.read(member) for member in expected.namelist()
        ):
            raise SystemExit(f'Replay differs from the published {name}')
    print(f'All archive entries match {name}')
