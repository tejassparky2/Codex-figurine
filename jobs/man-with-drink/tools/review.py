"""Turnaround sheet + front close-ups of a label array.  python review.py labels.npy tag"""
import sys, numpy as np; sys.path.insert(0, 'tools'); import views
from PIL import Image
PAL = np.array([[222,164,133],[14,14,16],[140,151,157],[241,236,225],[249,168,0]])
lab = np.load(sys.argv[1]); tag = sys.argv[2]
views.sheet(lab, PAL, f'renders/{tag}-sheet.png')
im = views.image(0, lab, PAL); W, H = im.size
im.crop((int(.25*W), 0, int(.75*W), int(.25*H))).resize((1200, 1200), Image.Resampling.NEAREST).save(f'renders/{tag}-head.png')
