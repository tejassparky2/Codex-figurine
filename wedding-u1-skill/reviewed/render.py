import numpy as np,moderngl as gl,trimesh
from PIL import Image,ImageDraw
from pathlib import Path
D=Path.cwd()
z=np.load('repaired-u1.npz');v=z['v'];f=z['f'];l=z['l'];u=z['u']
m=trimesh.Trimesh(v,f,process=False);c=m.triangles_center
palette=np.array([[239,193,58],[222,21,8],[255,249,240],[119,16,32],[246,188,162],[19,18,19],[214,61,79],[209,218,223]],'u1')
angles=[(i,0) for i in range(0,360,45)]+[(0,65),(180,-65)]
def ids():
 ctx=gl.create_standalone_context(backend='egl');size=(1000,1500);fb=ctx.simple_framebuffer(size);fb.use();ctx.enable(gl.DEPTH_TEST)
 p=ctx.program(vertex_shader="""#version 330
 uniform vec3 r; uniform vec3 up; uniform vec3 dep; in vec3 pos; flat out int id; void main(){vec3 q=pos-vec3(0,0,75);gl_Position=vec4(dot(q,r)/52,dot(q,up)/78,dot(q,dep)/160,1);id=gl_VertexID/3+1;}""",fragment_shader="""#version 330
 flat in int id;out vec4 col;void main(){col=vec4(float(id&255),float((id>>8)&255),float(id>>16),255)/255.;}""")
 b=ctx.buffer(v[f].astype('f4').tobytes());vao=ctx.vertex_array(p,[(b,'3f','pos')])
 for i,(a,t) in enumerate(angles):
  a,t=np.deg2rad([a,t]);p['r'].value=(np.cos(a),-np.sin(a),0);p['up'].value=(np.sin(t)*np.sin(a),np.sin(t)*np.cos(a),np.cos(t));p['dep'].value=(np.cos(t)*np.sin(a),np.cos(t)*np.cos(a),-np.sin(t))
  fb.clear();vao.render();pix=np.frombuffer(fb.read(),dtype='u1').reshape(1500,1000,3)[::-1].astype('i4');ix=pix@np.array([1,256,65536],'i4')-1;np.save(D/f'id{i}',ix)
def sheet(labels,path):
 ims=[]
 for i in range(10):
  ix=np.load(D/f'id{i}.npy');im=Image.fromarray(palette[np.r_[labels,7][ix]]);ims.append(im.resize((225,338)))
 out=Image.new('RGB',(1125,676),'white')
 for i,im in enumerate(ims):out.paste(im,(i%5*225,i//5*338))
 out.save(path)
if __name__=='__main__':ids();sheet(l,D/'sheet.png')
