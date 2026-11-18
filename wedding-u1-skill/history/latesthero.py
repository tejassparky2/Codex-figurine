from pathlib import Path
exec(Path('/tmp/flatjob.py').read_text().split('m=trimesh.Trimesh')[0].replace('Wedding-150mm-finish-guide','Wedding-150mm-flat-finish'))
ctx=gl.create_standalone_context(backend='egl')
sz=(2400,3000);fb=ctx.simple_framebuffer(sz);fb.use();fb.clear(.89,.86,.82,1,depth=1);ctx.enable(gl.DEPTH_TEST)
pr=ctx.program(vertex_shader="""#version 330
in vec3 pos;in vec3 normal;in vec3 rgb;out vec3 co;out vec3 N;void main(){float x=.9986*pos.x+.0523*pos.y;float y=-.0523*pos.x+.9986*pos.y;gl_Position=vec4(x/67.,(pos.z-75.+.035*y)/84.,y/155.,1);N=normal;co=rgb;}""",fragment_shader="""#version 330
in vec3 co;in vec3 N;out vec4 frag;void main(){vec3 n=normalize(N);vec3 L=normalize(vec3(-.55,-.72,.65));vec3 H=normalize(L+vec3(0,-1,.03));float d=.81+.21*max(0.,dot(n,L));float h=.042*pow(max(0.,dot(n,H)),25.);frag=vec4(co*d+h,1);}""")
m=trimesh.Trimesh(v,f,process=False);norm=m.vertex_normals.astype('f4')
colors=np.array([list(bytes.fromhex(k[1:])) for k in pal],dtype='f4')/255
def buf(a):return ctx.buffer(np.ascontiguousarray(a,dtype='f4').tobytes())
vao=ctx.vertex_array(pr,[(buf(v[f]),'3f','pos'),(buf(norm[f]),'3f','normal'),(buf(np.repeat(colors[l],3,axis=0)),'3f','rgb')]);vao.render()
im=Image.frombytes('RGB',sz,fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((1200,1500),Image.Resampling.LANCZOS);im.save('Wedding-finished-hero.png');im.thumbnail((320,400));im.save('/tmp/hero-check.jpg')
