exec(open('/tmp/wgl.py').read().split('img=m.visual')[0].replace('in vec3 pos;','uniform float ca;uniform float sa;in vec3 pos;').replace('pos.x*1.28','(pos.x*ca-pos.z*sa)*1.28').replace('-pos.z*.5','-(pos.x*sa+pos.z*ca)*.5'))
from PIL import ImageDraw
import cv2
ref=Image.open('reference/0.png').convert('RGB')
img=Image.open('/tmp/reftex.png')
t=ctx.texture(img.size,3,img.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes());t.build_mipmaps();t.use()
buf=ctx.buffer(np.c_[v,m.visual.uv].astype('f4').tobytes());ind=ctx.buffer(m.faces.astype('i4').tobytes());vao=ctx.vertex_array(pr,[(buf,'3f 2f','pos','uv')],ind)
sheet=Image.new('RGB',(1600,1060),'white')
def fit(im,ref=False):
 a=np.asarray(im); yy,xx=np.where((a.min(2)<180)); im=im.crop((xx.min()-4,yy.min()-4,xx.max()+5,yy.max()+5)); im.thumbnail((385,484));return im
for i,ang in enumerate((0,-54,180,54)):
 pr['ca']=np.cos(np.radians(ang));pr['sa']=np.sin(np.radians(ang));fb.clear(1,1,1,1,depth=1);vao.render()
 im=Image.frombytes('RGB',size,fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);im.save(f'/tmp/refview{i}.png')
 for j,pic in enumerate([ref.crop((i*ref.width//4,51,(i+1)*ref.width//4,ref.height)),im]):
  pic=fit(pic);sheet.paste(pic,(400*i+(400-pic.width)//2,530*j+35));ImageDraw.Draw(sheet).text((400*i+10,530*j+8),['Reference','Model'][j]+' | '+['Front','Bride side','Back','Groom side'][i],fill='black')
sheet.save('Reference-comparison.jpg',quality=95);sheet.thumbnail((800,530));sheet.save('/tmp/refcompare.jpg')
