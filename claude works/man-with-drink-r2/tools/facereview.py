import sys, numpy as np; from PIL import Image
PAL = np.array([[222,164,133],[14,14,16],[140,151,157],[241,236,225],[249,168,0],[255,255,255]])
lab = np.load(sys.argv[1]); ids = np.load('views/face_id.npy'); frame = np.load('frame_mask.npy')
im = Image.fromarray(PAL[np.where(ids >= 0, lab[np.clip(ids,0,None)], 5)].astype('u1'))
tex = Image.open('renders/face-tex.png').convert('RGB')
both = Image.new('RGB', (im.width*2, im.height)); both.paste(tex, (0,0)); both.paste(im, (im.width,0))
both.resize((both.width//2, both.height//2)).save(sys.argv[2])
