"""Ten orthographic triangle-ID cameras (8 azimuths, above, below) for a Z-up mm mesh whose front faces -Y.
python views.py            -> writes views/id{i}.npy
import views; views.sheet(labels, palette_rgb, path) -> unlit label turnaround."""
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
D = Path('views'); W, H = 800, 1600
ANG = [(a, 0) for a in range(0, 360, 45)] + [(0, 70), (180, -70)]
NAMES = ['front', 'front, his right 45', 'his right side', 'back, his right 135', 'back', 'back, his left 225', 'his left side', 'front, his left 315', 'above', 'below']
def ids():
    import moderngl as gl
    z = np.load('printable.npz'); v, f = z['v'], z['f']; zc = v[:,2].max()/2; half = v[:,2].max()*0.53
    ctx = gl.create_standalone_context(backend='egl'); fb = ctx.simple_framebuffer((W, H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
    p = ctx.program(vertex_shader="""#version 330
uniform vec3 r; uniform vec3 up; uniform vec3 dep; uniform float zc; uniform float half_; in vec3 pos; flat out int id;
void main(){vec3 q=pos-vec3(0,0,zc); gl_Position=vec4(dot(q,r)/(half_*0.5),dot(q,up)/half_,dot(q,dep)/(half_*2.),1); id=gl_VertexID/3+1;}""",
    fragment_shader="""#version 330
flat in int id; out vec4 col; void main(){col=vec4(float(id&255),float((id>>8)&255),float(id>>16),255)/255.;}""")
    p['zc'].value = zc; p['half_'].value = half
    vao = ctx.vertex_array(p, [(ctx.buffer(v[f].astype('f4').tobytes()), '3f', 'pos')])
    D.mkdir(exist_ok=True)
    for i, (a, t) in enumerate(ANG):
        a, t = np.deg2rad([a, t])
        # camera starts in front (looking +Y) and orbits the figure; azimuth a turns toward the figure's left
        fwd = np.array([np.sin(a)*np.cos(t), np.cos(a)*np.cos(t), -np.sin(t)])   # viewing direction
        right = np.array([np.cos(a), -np.sin(a), 0.]); up = np.cross(right, fwd)
        p['r'].value = tuple(right); p['up'].value = tuple(up); p['dep'].value = tuple(fwd)
        fb.clear(); vao.render()
        pix = np.frombuffer(fb.read(), dtype='u1').reshape(H, W, 3)[::-1].astype('i4')
        np.save(D/f'id{i}', pix @ np.array([1, 256, 65536], 'i4') - 1)
def image(i, labels, pal):
    j = np.load(D/f'id{i}.npy'); return Image.fromarray(np.vstack([pal, [255,255,255]]).astype('u1')[np.where(j >= 0, labels[j], len(pal))])
def sheet(labels, pal, path, scale=.5, which=range(10)):
    ims = [image(i, labels, pal) for i in which]; w, h = int(W*scale), int(H*scale)
    out = Image.new('RGB', (w*5, (h+18)*2), 'white'); d = ImageDraw.Draw(out)
    for k, (i, im) in enumerate(zip(which, ims)):
        x, y = (k%5)*w, (k//5)*(h+18); out.paste(im.resize((w, h), Image.Resampling.NEAREST), (x, y+18)); d.text((x+6, y+3), NAMES[i], fill='black')
    out.save(path)
if __name__ == '__main__':
    ids(); rgb = np.load('face_rgb.npy'); sheet(np.arange(len(rgb)), rgb, 'renders/source-on-printable.png')
