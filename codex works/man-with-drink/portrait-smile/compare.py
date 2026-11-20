from pathlib import Path
from PIL import Image,ImageDraw
d=Path('/dev/shm/photo-smile');photo=Image.open('/dev/shm/drink/jobs/man-with-drink/judge/approved-front.jpg')
out=Image.new('RGB',(990,184),'#f5f1e9');dr=ImageDraw.Draw(out)
for i,(name,img) in enumerate([('Approved portrait',photo.crop((237,496,469,602))),('Previous sculpt',Image.open(d/'mouth-earlier.png')),('Revised sculpt',Image.open(d/'mouth-front.png'))]):
 out.paste(img.convert('RGB').resize((330,151),Image.Resampling.LANCZOS),(330*i,30));dr.text((330*i+9,9),name,fill='#332a23')
out.save(d/'portrait-comparison.jpg',quality=96)
