from pathlib import Path
s=Path('/tmp/clean-check.py').read_text()
s=s.replace('in vec3 pos;', 'uniform mat2 rot;in vec3 pos;').replace('gl_Position=vec4(pos.x*1.28/60,(pos.z-60)*.96/60,pos.y/120,1);','vec2 xy=rot*pos.xy;gl_Position=vec4(xy.x*1.28/60,(pos.z-60)*.96/60,xy.y/120,1);')
s=s[:s.index('ctx.vertex_array(pr,')]+"""vao=ctx.vertex_array(pr,[(buf,'3f','pos'),(col,'3f','rgb')])
from PIL import ImageDraw
views=[]
for angle in [0,65,180,-65]:
 a=np.deg2rad(angle);pr['rot'].value=(np.cos(a),np.sin(a),-np.sin(a),np.cos(a));fb.clear(1,1,1,1,depth=1);vao.render()
 views.append(Image.frombytes('RGB',size,fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM))
parts=[('Faces and lips',0,(280,365,838,674)),('Hands, bangles and cuffs',0,(284,735,749,1050)),('Turban, plume and jewelry',0,(466,12,998,376)),('Garlands and braid',1,(130,560,880,1230)),('Sari and coat hems',0,(185,1015,952,1418)),('Back, collar and braid',2,(80,469,1030,1350)),('Sleeve and trim',3,(195,630,899,1220)),('Feet and hems',2,(150,1180,934,1430))]
sheet=Image.new('RGB',(1480,4*470),'white');d=ImageDraw.Draw(sheet)
for i,(title,k,box) in enumerate(parts):
 patch=views[k].crop(box);patch.thumbnail((720,425));ox=740*(i%2);oy=470*(i//2);sheet.paste(patch,(ox+(740-patch.width)//2,oy+30));d.text((ox+15,oy+8),title,fill='black')
sheet.save('Clean-detail-review.jpg',quality=96);sheet.thumbnail((950,1250));sheet.save('/tmp/detail-review.jpg')
"""
Path('/tmp/detailqa.py').write_text(s)
