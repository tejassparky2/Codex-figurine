from start import *
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d,median_filter
ids,before=render(cam)
factor=H/640
a=cv2.resize((ids>=0).astype('uint8'),(285,640),interpolation=cv2.INTER_NEAREST)
b=cv2.resize(foreground(ref,None,None).astype('uint8'),(285,640),interpolation=cv2.INTER_NEAREST)
# Horizontal landmarks shared by both models: top, brows, pupils, smile, chin, collar,
# tumbler rim and base, belt, fingertips, crotch, hems and level of soles.
ys=np.array([0,51,92,131,153,200,235,275,311,357,429,452,462,560,597,639])
yt=np.array([0,52,91,146,167,218,259,299,335,381,447,462,469,564,599,639])
ymap=PchipInterpolator(ys,yt)
def envelope(mask):
 lo=[];hi=[]
 for row in mask:
  xs=np.flatnonzero(row);lo.append(xs.min() if len(xs) else np.nan);hi.append(xs.max() if len(xs) else np.nan)
 def interp(vec):
  vec=np.array(vec);ok=np.isfinite(vec);return gaussian_filter1d(np.interp(np.arange(640),np.where(ok)[0],vec[ok]),2)
 return interp(lo),interp(hi)
s0,s1=envelope(a);t0,t1=envelope(b); yy=np.arange(640)
# The front-view centers of frames/mouth/cup and the gap between ankles constrain interior placement.
land=np.array([[51,118,133],[95,135,143],[145,133,137],[157,134,138],[202,136,143],[245,142,144],[275,150,150],[311,151,154],[357,151,154],[429,140,141],[461,142,141],[540,138,135],[582,136,131],[597,135,130]])
src=np.interp(yy,land[:,0],land[:,1]);dst=np.interp(yy,land[:,0],land[:,2])
xgrid=np.empty((640,285))
for y in yy:
 j=float(ymap(y))
 # Fade the outline constraint near the hair tip and the uneven shoe soles.
 amt=np.clip((y-52)/16,0,1)*np.clip((597-y)/16,0,1)
 L=s0[y];R=s1[y];mid=np.clip(src[y],L+1,R-1)
 if R-L<6: xgrid[y]=np.arange(285)+dst[y]-src[y];continue
 TL=np.interp(j,yy,t0);TR=np.interp(j,yy,t1)
 target_mid=np.clip(dst[y],TL+1,TR-1)
 sx=[0,L,mid,R,284];tx=[0,TL,target_mid,TR,284]
 if 474<=y<=589:
  def gap(m,row):
   vals=np.flatnonzero(m[int(row)]); parts=np.split(vals,np.flatnonzero(np.diff(vals)>1)+1)
   parts=[p for p in parts if len(p)>8]
   return (parts[0][-1],parts[-1][0]) if len(parts)==2 else None
  g=gap(a,y);h=gap(b,j)
  if g and h and L<g[0]<g[1]<R and TL<h[0]<h[1]<TR:
   sx=[0,L,*g,R,284];tx=[0,TL,*h,TR,284]
 xgrid[y]=amt*np.interp(np.arange(285),sx,tx)+(1-amt)*(np.arange(285)+dst[y]-src[y])
xgrid=gaussian_filter1d(xgrid,2,axis=0)
def mapx(x,y):
 return cv2.remap(xgrid.astype('f4'),x.astype('f4'),y.astype('f4'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
from scipy.ndimage import map_coordinates
center=(v.min(0)+v.max(0))/2
x=(cam['tx']+(v[:,0]-center[0])*cam['s'])*285/W
y=(cam['ty']-(v[:,2]-center[2])*cam['s'])/factor
u=map_coordinates(xgrid,[y,x],order=1,mode='nearest')
vv=ymap(y)
new=v.copy();s=(vv.max()-vv.min())/220.
new[:,0]=(u-142.5)/s;new[:,2]=(vv.max()-vv)/s
# Match pixel aspect ratio of the source JPEG.
new[:,0]*=(W/285)/factor
new[:,0]-=(new[:,0].min()+new[:,0].max())/2
camera=dict(cam,s=s*factor,tx=float(np.median(u*W/285-new[:,0]*s*factor)),ty=float(vv.max()*factor-110*s*factor))
out=Raster(new,f); ni=out.ids(camera,(W,H)); fg=foreground(ref,None,None)
def iou(i):
 m=i>=0;return (m&fg).sum()/(m|fg).sum()
print('raw front silhouette before and after',iou(ids),iou(ni),'min row derivative',np.diff(xgrid,axis=1).min())
np.savez(D/'fitted.npz',v=new,f=f)
(D/'camera.json').write_text(json.dumps(camera))
np.savez(D/'mapping.npz',u=u*W/285,vv=vv*factor)
