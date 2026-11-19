"""Customer 4-side presentation renders (front, his right, back, his left), decoded from the exported finish guide.
Same lit look as the hero; the camera (and its light) orbit the figure, so every side is lit the same way.
Writes out/customer-4-sides.png (one sheet) and out/customer-<side>.png."""
import re, zipfile, json, numpy as np, trimesh, moderngl as gl
from PIL import Image, ImageDraw, ImageFont
with zipfile.ZipFile('out/Man-with-drink-220mm-finish-guide.3mf') as z:
    s = z.read('3D/3dmodel.model'); pal = json.loads(z.read('Metadata/project_settings.config'))['filament_colour']
v = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>', s), 'f4')
f = np.array(re.findall(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s), 'i4')
codes = {c: i for i, c in enumerate([b'4', b'8', b'0C', b'1C', b'2C'])}
l = np.array([codes[c] for c in re.findall(rb'paint_color="([^"]+)"', s)])
preview = list(pal); preview[0] = '#DEA485'                     # Apricot prints darker than its swatch (as the hero)
cols = np.array([[int(h[i:i+2], 16) for i in (1, 3, 5)] for h in preview], 'f4')/255
v = v - np.r_[(v[:, :2].min(0) + v[:, :2].max(0)) / 2, v[:, 2].min()]          # bed position -> centred, feet at z=0
nrm = trimesh.Trimesh(v, f, process=False).vertex_normals.astype('f4')
ctx = gl.create_standalone_context(backend='egl'); W, H = 1600, 3000
pr = ctx.program(vertex_shader="""#version 330
uniform float ang; in vec3 pos; in vec3 normal; in vec3 rgb; out vec3 co; out vec3 N;
void main(){float c=cos(ang),s=sin(ang); float x=c*pos.x+s*pos.y, y=-s*pos.x+c*pos.y;
gl_Position=vec4(x/62.,(pos.z-110.+.03*y)/116.,y/160.,1); N=vec3(c*normal.x+s*normal.y,-s*normal.x+c*normal.y,normal.z); co=rgb;}""",
fragment_shader="""#version 330
in vec3 co; in vec3 N; out vec4 o; void main(){vec3 n=normalize(N); vec3 L=normalize(vec3(-.5,-.75,.6)); vec3 H=normalize(L+vec3(0,-1,.05));
float d=.74+.30*max(0.,dot(n,L)); float sp=.05*pow(max(0.,dot(n,H)),30.); o=vec4(co*d+sp,1);}""")
vao = ctx.vertex_array(pr, [(ctx.buffer(v[f].tobytes()), '3f', 'pos'), (ctx.buffer(nrm[f].tobytes()), '3f', 'normal'),
                            (ctx.buffer(np.repeat(cols[l], 3, 0).tobytes()), '3f', 'rgb')])
fb = ctx.simple_framebuffer((W, H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
views = []
for name, deg in [('Front', 0), ('Right side', 90), ('Back', 180), ('Left side', 270)]:   # his right = the glass hand
    pr['ang'].value = np.deg2rad(deg); fb.clear(.90, .88, .85, 1, depth=1); vao.render()
    im = Image.frombytes('RGB', (W, H), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((800, 1500), Image.Resampling.LANCZOS)
    im.save(f'out/customer-{name.lower().replace(" ", "-")}.png'); views.append((name, im))
try:
    font = ImageFont.truetype('DejaVuSans.ttf', 34)
except OSError:
    font = ImageFont.load_default()
sheet = Image.new('RGB', (800*4, 1500+70), (230, 224, 217)); d = ImageDraw.Draw(sheet)
for i, (name, im) in enumerate(views):
    sheet.paste(im, (i*800, 70)); tw = d.textlength(name, font=font); d.text((i*800 + (800-tw)/2, 18), name, fill=(60, 55, 50), font=font)
sheet.save('out/customer-4-sides.png')
print('ok', len(f), 'faces decoded; views:', ', '.join(n for n, _ in views))
