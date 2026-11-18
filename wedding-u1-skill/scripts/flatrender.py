ctx=gl.create_standalone_context(backend='egl');size=(864,1152);fb=ctx.simple_framebuffer(size);fb.use();ctx.enable(gl.DEPTH_TEST)
pr=ctx.program(vertex_shader="""#version 330
uniform mat2 rot;in vec3 pos;in vec3 rgb;out vec3 co;void main(){vec2 xy=rot*pos.xy;gl_Position=vec4(xy.x*1.28/75,(pos.z-75)*.96/75,xy.y/150,1);co=rgb;}""",fragment_shader="""#version 330
in vec3 co;out vec4 col;void main(){col=vec4(co,1);}""")
buf=ctx.buffer(v[f].astype('f4').tobytes());colors=np.array([list(bytes.fromhex(k[1:])) for k in pal],'f4')/255
col=ctx.buffer(np.repeat(colors[l],3,axis=0).tobytes());vao=ctx.vertex_array(pr,[(buf,'3f','pos'),(col,'3f','rgb')])
views=[]
for angle in np.arange(0,360,30):
 a=np.deg2rad(angle);pr['rot'].value=(np.cos(a),np.sin(a),-np.sin(a),np.cos(a));fb.clear(1,1,1,1,depth=1);vao.render()
 im=Image.frombytes('RGB',size,fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 # Exact unlit palette check on every pixel, white background included.
 aa=np.asarray(im).astype('int32'); packed=(aa[:,:,0]<<16)+(aa[:,:,1]<<8)+aa[:,:,2]
 assert set(np.unique(packed))<=set([0xffffff]+[int(k[1:],16) for k in pal])
 if angle==0:im.save('Flat-finish-front.png')
 views.append(im.resize((324,432),Image.Resampling.NEAREST))
sheet=Image.new('RGB',(1296,1356),'white');d=ImageDraw.Draw(sheet)
for i,im in enumerate(views):
 xx=(i%4)*324;yy=(i//4)*452;sheet.paste(im,(xx,yy+20));d.text((xx+8,yy+3),str(i*30)+' degrees',fill='black')
sheet.save('Flat-finish-all-sides.png');sheet.thumbnail((800,850));sheet.save('flatcheck.png')
