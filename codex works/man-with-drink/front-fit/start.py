import sys, numpy as np, cv2, json
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,'wedding-u1-skill/coloring')
from approved_match import Raster,foreground
D=Path('/dev/shm/match')
z=np.load('/dev/shm/drinkcheck/mesh.npz'); v=z['v'];f=z['f'];l=np.load('/dev/shm/drinkcheck/labels.npy')
r=Raster(v,f)
ref=np.array(Image.open('jobs/man-with-drink/judge/approved-front.jpg').convert('RGB'))
W,H=ref.shape[1],ref.shape[0];pal=np.array([[230,186,168],[22,20,20],[140,151,157],[249,168,0],[241,236,225]])
cam=dict(yaw=0.,pitch=0.,roll=0.,s=6.21,tx=350.,ty=811.,k=0.)
def render(cam):
 ids=r.ids(cam,(W,H)); out=np.full((H,W,3),255,np.uint8); m=ids>=0
 out[m]=pal[l[ids[m]]]
 return ids,out
if __name__=='__main__':
 ims=[Image.fromarray(ref).resize((285,640))]
 for yaw in [-20,0,20,40]:
  ids,out=render(dict(cam,yaw=yaw));ims.append(Image.fromarray(out).resize((285,640)))
 can=Image.new('RGB',(285*len(ims),640))
 for i,im in enumerate(ims):can.paste(im,(285*i,0))
 can.save(D/'poses.jpg')
