import trimesh,moderngl as gl,numpy as np
from PIL import Image
m=trimesh.load('source.glb',force='mesh',process=False)
v=m.vertices.copy(); v-=m.bounds.mean(0);v/=m.extents[1]/2
ctx=gl.create_standalone_context(backend='egl'); size=(1080,1440)
fb=ctx.simple_framebuffer(size);fb.use();fb.clear(1,1,1,1,depth=1);ctx.enable(gl.DEPTH_TEST)
pr=ctx.program(vertex_shader="""#version 330
in vec3 pos;in vec2 uv;out vec2 st;void main(){gl_Position=vec4(pos.x*1.28,pos.y*.96,-pos.z*.5,1);st=uv;}""",fragment_shader="""#version 330
uniform sampler2D tex;in vec2 st;out vec4 color;void main(){color=texture(tex,st);}""")
img=m.visual.material.baseColorTexture.convert('RGB')
t=ctx.texture(img.size,3,img.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes());t.build_mipmaps();t.use()
buf=ctx.buffer(np.c_[v,m.visual.uv].astype('f4').tobytes());ind=ctx.buffer(m.faces.astype('i4').tobytes());ctx.vertex_array(pr,[(buf,'3f 2f','pos','uv')],ind).render()
im=Image.frombytes('RGB',size,fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);im.save('Texture-front.png');im.resize((432,576)).save('/tmp/wsmall.png')
