"""Compare decoded deliverables with the original delivered job."""
import argparse
import hashlib
from pathlib import Path
import sys
import zipfile
from PIL import Image, ImageChops

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('job', type=Path)
args = parser.parse_args()
success = True
for reference in sorted((root / 'expected').iterdir()):
    target = args.job / reference.name
    if reference.suffix == '.3mf':
        with zipfile.ZipFile(reference) as old, zipfile.ZipFile(target) as new:
            matches = set(old.namelist()) == set(new.namelist()) and new.testzip() is None
            for name in old.namelist():
                with old.open(name) as a, new.open(name) as b:
                    matches &= hashlib.file_digest(a, 'sha256').digest() == hashlib.file_digest(b, 'sha256').digest()
    else:
        with Image.open(reference) as a, Image.open(target) as b:
            matches = a.size == b.size and ImageChops.difference(a.convert('RGB'), b.convert('RGB')).getbbox() is None
    print(reference.name, 'MATCH' if matches else 'DIFFERENCE')
    success &= matches
sys.exit(0 if success else 1)
