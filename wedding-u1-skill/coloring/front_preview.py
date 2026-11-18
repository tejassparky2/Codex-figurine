"""Lit straight-front preview of an Orca paint_color 3MF (single mesh, solid per-triangle codes), decoded from the file.
Always deliver this with every revision. Optional face/detail crop by a z window.
usage: front_preview.py model.3mf out_prefix [--preview SLOT=#HEX ...] [--crop-z z0:z1]
Writes <out_prefix>-front.png (full figure) and, with --crop-z, <out_prefix>-front-detail.png."""
import argparse, json, re, zipfile, numpy as np, trimesh, moderngl as gl
from PIL import Image
p = argparse.ArgumentParser(); p.add_argument('model'); p.add_argument('out'); p.add_argument('--preview', action='append', default=[]); p.add_argument('--crop-z')
A = p.parse_args()
with zipfile.ZipFile(A.model) as z:
    s = next(z.read(k) for k in z.namelist() if k.endswith('.model')); pal = json.loads(z.read('Metadata/project_settings.config'))['filament_colour']
for kv in A.preview: k, h = kv.split('='); pal[int(k)-1] = h
v = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>', s), 'f4'); f = np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), 'i4')
codes = {c: i for i, c in enumerate([b'4', b'8', b'0C', b'1C', b'2C', b'3C', b'4C', b'5C'])}
l = np.array([codes[c] for c in re.findall(rb'paint_color="([^"]+)"', s)])
cols = np.array([[int(h[i:i+2], 16) for i in (1, 3, 5)] for h in pal], 'f4')/255
v -= [(v[:,0].max()+v[:,0].min())/2, (v[:,1].max()+v[:,1].min())/2, 0]; nrm = trimesh.Trimesh(v, f, process=False).vertex_normals.astype('f4')
ctx = gl.create_standalone_context(backend='egl')
pr = ctx.program(vertex_shader="""#version 330
uniform vec4 B; uniform float D; in vec3 pos; in vec3 normal; in vec3 rgb; out vec3 co; out vec3 N;
void main(){gl_Position=vec4((pos.x-B.x)/B.z,(pos.z-B.y)/B.w,pos.y/D,1); N=normal; co=rgb;}""", fragment_shader="""#version 330
in vec3 co; in vec3 N; out vec4 o; void main(){vec3 n=normalize(N); vec3 L=normalize(vec3(-.35,-.85,.45)); vec3 H=normalize(L+vec3(0,-1,0));
float d=.74+.30*max(0.,dot(n,L)); float sp=.05*pow(max(0.,dot(n,H)),30.); o=vec4(co*d+sp,1);}""")
pr['D'].value = float(np.abs(v[:,1]).max()*2+1)
vao = ctx.vertex_array(pr, [(ctx.buffer(v[f].tobytes()), '3f', 'pos'), (ctx.buffer(nrm[f].tobytes()), '3f', 'normal'), (ctx.buffer(np.repeat(cols[l], 3, 0).tobytes()), '3f', 'rgb')])
ctx.enable(gl.DEPTH_TEST); H = float(v[:,2].max()); hw = float(np.abs(v[:,0]).max())*1.05; hh = H*.53
jobs = [('front', 0, H/2, max(hw, hh*.45), hh)]
if A.crop_z: z0, z1 = map(float, A.crop_z.split(':')); r = (z1-z0)/2; jobs.append(('front-detail', 0, (z0+z1)/2, r, r))
for name, bx, by, sx, sy in jobs:
    W, Hp = (int(3000*sx/sy), 3000) if name == 'front' else (2000, 2000)
    fb = ctx.simple_framebuffer((W, Hp)); fb.use(); fb.clear(.90, .88, .85, 1, depth=1); pr['B'].value = (bx, by, sx, sy); vao.render()
    Image.frombytes('RGB', (W, Hp), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((W//2, Hp//2), Image.Resampling.LANCZOS).save(f'{A.out}-{name}.png')
print('wrote', A.out + '-front.png', '(+detail)' if A.crop_z else '')
