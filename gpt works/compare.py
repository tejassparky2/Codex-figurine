"""Render matched close-ups and calculate per-color surface changes on wedding candidates."""
import argparse
from pathlib import Path
import numpy as np
import moderngl as gl
import trimesh
from PIL import Image, ImageDraw
parser=argparse.ArgumentParser(description=__doc__)
for name in ('mesh','finish','split','png'):
    parser.add_argument(name,type=Path)
args=parser.parse_args()
old=np.load(args.mesh);new=np.load(args.split)
palette=np.array([[239,193,58],[222,21,8],[255,249,240],[119,16,32],[246,188,162],[19,18,19],[214,61,79]],'f4')/255
ctx=gl.create_standalone_context(backend='egl')
fb=ctx.simple_framebuffer((1000,700));fb.use();ctx.enable(gl.DEPTH_TEST)
shader=ctx.program(vertex_shader="""#version 330
uniform vec3 center;uniform vec2 axis;uniform float width;
in vec3 point;in vec3 normal;in vec3 color;out vec3 rgb;
void main(){vec3 q=point-center;float d=dot(q.xy,vec2(-axis.y,axis.x));gl_Position=vec4(dot(q.xy,axis)/width,q.z/(.7*width),d/160.,1.);rgb=color*(.84+.16*max(0.,dot(normal,normalize(vec3(-.4,-.7,.65)))));}
""",fragment_shader="""#version 330
in vec3 rgb;out vec4 c;void main(){c=vec4(rgb,1);}
""")
canvas=Image.new('RGB',(1400,1090),'white');draw=ImageDraw.Draw(canvas)
for col,(z,labels,title) in enumerate([(old,np.load(args.finish),'Texture cleanup'),(new,new['l'],'Contact seeds + contour split')]):
    draw.text((col*700+20,12),title,fill='black',font_size=25)
    m=trimesh.Trimesh(z['v'],z['f'],process=False)
    print(title,'areas by material',np.bincount(labels,weights=m.area_faces).round(1))
    buffers=[]
    for data in (m.vertices[m.faces],m.vertex_normals[m.faces],np.repeat(palette[labels],3,axis=0)):
        buffers.append(ctx.buffer(np.ascontiguousarray(data,dtype='f4').tobytes()))
    vao=ctx.vertex_array(shader,[(buf,'3f',attr) for buf,attr in zip(buffers,['point','normal','color'])])
    for row,(center,angle,width,text) in enumerate([((3,0,57),0,23,'Hands, bangles and garlands'),((14,0,53),150,25,'Sleeves and trim, oblique view')]):
        r=np.deg2rad(angle);shader['center'].value=center;shader['axis'].value=(np.cos(r),-np.sin(r));shader['width'].value=width
        fb.clear(.90,.91,.91,depth=1);vao.render()
        im=Image.frombytes('RGB',fb.size,fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        canvas.paste(im.resize((700,490),Image.Resampling.LANCZOS),(col*700,52+row*515))
        if col==0:draw.text((15,542+row*515),text,fill='black',font_size=16)
    vao.release()
    for buf in buffers:buf.release()
canvas.save(args.png)
