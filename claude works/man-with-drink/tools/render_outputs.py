"""Renders decoded from the exported finish guide: 12-view unlit turnaround (exact palette check) and a lit hero."""
import re, zipfile, json, numpy as np, trimesh, moderngl as gl
from PIL import Image, ImageDraw
with zipfile.ZipFile('out/Man-with-drink-220mm-finish-guide.3mf') as z:
    s = z.read('3D/3dmodel.model'); pal = json.loads(z.read('Metadata/project_settings.config'))['filament_colour']
v = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>', s), 'f4')
f = np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), 'i4')
codes = {c: i for i, c in enumerate([b'4', b'8', b'0C', b'1C', b'2C'])}
l = np.array([codes[c] for c in re.findall(rb'paint_color="([^"]+)"', s)])
preview = list(pal); preview[0] = '#DEA485'                     # Apricot prints darker than its swatch
cols = np.array([[int(h[i:i+2], 16) for i in (1, 3, 5)] for h in preview], 'f4')/255
ctx = gl.create_standalone_context(backend='egl')
# 1) unlit turnaround
W, H = 600, 1500; fb = ctx.simple_framebuffer((W, H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
pr = ctx.program(vertex_shader="""#version 330
uniform mat2 rot; in vec3 pos; in vec3 rgb; out vec3 co; void main(){vec2 xy=rot*pos.xy; gl_Position=vec4(xy.x/58.,(pos.z-110.)/116.,xy.y/150.,1); co=rgb;}""",
fragment_shader="""#version 330
in vec3 co; out vec4 o; void main(){o=vec4(co,1);}""")
vao = ctx.vertex_array(pr, [(ctx.buffer(v[f].tobytes()), '3f', 'pos'), (ctx.buffer(np.repeat(cols[l], 3, 0).tobytes()), '3f', 'rgb')])
allowed = {0xFFFFFF} | {int(h[1:], 16) for h in preview}; views = []
for ang in range(0, 360, 30):
    a = np.deg2rad(ang); pr['rot'].value = (np.cos(a), np.sin(a), -np.sin(a), np.cos(a)); fb.clear(1, 1, 1, 1, depth=1); vao.render()
    im = Image.frombytes('RGB', (W, H), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM); aa = np.asarray(im).astype('i4')
    assert set(np.unique((aa[..., 0] << 16) + (aa[..., 1] << 8) + aa[..., 2])) <= allowed
    views.append(im.resize((300, 750), Image.Resampling.NEAREST))
sheet = Image.new('RGB', (300*6, 770*2), 'white'); d = ImageDraw.Draw(sheet)
for i, im in enumerate(views): sheet.paste(im, ((i % 6)*300, (i//6)*770+20)); d.text(((i % 6)*300+8, (i//6)*770+4), f'{i*30} degrees', fill='black')
sheet.save('out/Finish-all-sides.png')
# 2) lit hero (presentation only; the file's labels stay flat)
W, H = 1600, 3000; fb = ctx.simple_framebuffer((W, H)); fb.use(); fb.clear(.90, .88, .85, 1, depth=1)
m = trimesh.Trimesh(v, f, process=False); nrm = m.vertex_normals.astype('f4')
pr = ctx.program(vertex_shader="""#version 330
in vec3 pos; in vec3 normal; in vec3 rgb; out vec3 co; out vec3 N;
void main(){float c=cos(.42),s=sin(.42); float x=c*pos.x+s*pos.y, y=-s*pos.x+c*pos.y; gl_Position=vec4(x/62.,(pos.z-110.+.03*y)/116.,y/160.,1); N=vec3(c*normal.x+s*normal.y,-s*normal.x+c*normal.y,normal.z); co=rgb;}""",
fragment_shader="""#version 330
in vec3 co; in vec3 N; out vec4 o; void main(){vec3 n=normalize(N); vec3 L=normalize(vec3(-.5,-.75,.6)); vec3 H=normalize(L+vec3(0,-1,.05));
float d=.74+.30*max(0.,dot(n,L)); float sp=.05*pow(max(0.,dot(n,H)),30.); o=vec4(co*d+sp,1);}""")
vao = ctx.vertex_array(pr, [(ctx.buffer(v[f].tobytes()), '3f', 'pos'), (ctx.buffer(nrm[f].tobytes()), '3f', 'normal'), (ctx.buffer(np.repeat(cols[l], 3, 0).tobytes()), '3f', 'rgb')])
ctx.enable(gl.DEPTH_TEST); vao.render()
hero = Image.frombytes('RGB', (W, H), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((800, 1500), Image.Resampling.LANCZOS)
hero.save('out/Man-with-drink-hero.png'); hero.crop((150, 0, 650, 520)).resize((1000, 1040), Image.Resampling.LANCZOS).save('out/Man-with-drink-face.png')
# 3) straight front preview (always delivered): full figure and face, same lighting, no rotation
W, H = 1400, 3000; fb = ctx.simple_framebuffer((W, H)); fb.use(); fb.clear(.90, .88, .85, 1, depth=1)
pr = ctx.program(vertex_shader="""#version 330
uniform vec4 B; in vec3 pos; in vec3 normal; in vec3 rgb; out vec3 co; out vec3 N;
void main(){gl_Position=vec4((pos.x-B.x)/B.z,(pos.z-B.y)/B.w,pos.y/160.,1); N=normal; co=rgb;}""",
fragment_shader="""#version 330
in vec3 co; in vec3 N; out vec4 o; void main(){vec3 n=normalize(N); vec3 L=normalize(vec3(-.35,-.85,.45)); vec3 H=normalize(L+vec3(0,-1,0));
float d=.74+.30*max(0.,dot(n,L)); float sp=.05*pow(max(0.,dot(n,H)),30.); o=vec4(co*d+sp,1);}""")
vao = ctx.vertex_array(pr, [(ctx.buffer(v[f].tobytes()), '3f', 'pos'), (ctx.buffer(nrm[f].tobytes()), '3f', 'normal'), (ctx.buffer(np.repeat(cols[l], 3, 0).tobytes()), '3f', 'rgb')])
for name, Bx, By, hw, hh, size in [('front', 0, 110, 52, 116, (1400, 3000)), ('front-face', 0, 170, 34, 34, (2000, 2000))]:
    fb = ctx.simple_framebuffer(size); fb.use(); fb.clear(.90, .88, .85, 1, depth=1); pr['B'].value = (Bx, By, hw, hh); vao.render()
    im = Image.frombytes('RGB', size, fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    im.resize((size[0]//2, size[1]//2), Image.Resampling.LANCZOS).save(f'out/Man-with-drink-{name}.png')
print('ok', len(f), 'faces decoded')
