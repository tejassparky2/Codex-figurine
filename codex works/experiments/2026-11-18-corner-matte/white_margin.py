"""Generate a gate mask for cropped RGB figurine art on a known white background."""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'wedding-u1-skill/coloring'))
from approved_match import foreground


def white_margin_mask(rgb):
    pad = 10
    framed = np.pad(rgb, ((pad, pad), (pad, pad), (0, 0)), constant_values=255)
    return foreground(framed, None, None)[pad:-pad, pad:-pad]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    with Image.open(args.image) as image:
        rgb = np.asarray(image.convert('RGB'))
    mask = white_margin_mask(rgb)
    Image.fromarray(mask.astype('uint8') * 255).save(args.output)
