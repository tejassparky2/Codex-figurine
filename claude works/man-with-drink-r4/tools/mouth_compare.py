"""Art mouth vs model mouth at the same scale, with the art's traced lines drawn on both.
usage: mouth_compare.py mesh.npz out.png   (art px <-> model mm via the match_head constants and match_scale)"""
import sys, numpy as np, trimesh, moderngl as gl
from PIL import Image, ImageDraw
mesh, out = sys.argv[1], sys.argv[2]
s = float(np.load('views/match_scale.npy')[0]); PEYE, MEYE, S, XCP, XCM = 415.0, 175.2, 137.0 / 19.2, 344.0, -2.08
mm = lambda c, r: (((np.asarray(c) - XCP) / S + XCM) * s, (MEYE - (np.asarray(r) - PEYE) / S) * s)
# traced on reference/photo-front.jpg (art px)
TRACE = {
 'mouth top (teeth top)': [(280,544),(290,546),(300,547),(320,547),(340,546),(360,545),(380,543),(390,541),(400,538),(410,534),(420,528),(428,525)],
 'teeth bottom':          [(305,550),(320,554),(340,555),(360,554),(380,551),(390,548),(400,545),(408,540)],
 'gap bottom / lower lip top': [(280,544),(290,549),(300,553),(310,556),(320,558),(340,560),(360,559),(380,556),(400,551),(410,546),(420,535),(428,525)],
 'upper lip top':         [(285,541),(300,539),(320,536),(340,534),(360,534),(380,533),(400,530),(415,527)],
}
COL = {'mouth top (teeth top)': (0,160,255), 'teeth bottom': (0,200,0), 'gap bottom / lower lip top': (230,20,20), 'upper lip top': (200,0,200)}
x0, y0, x1, y1, k = 262, 505, 446, 590, 8
art = Image.open('reference/photo-front.jpg').convert('RGB').crop((x0, y0, x1, y1)).resize(((x1-x0)*k, (y1-y0)*k), Image.LANCZOS)
z = np.load(mesh); V, F, L = z['v'].astype('f4'), z['f'], z['l'].astype(int)
m = trimesh.Trimesh(V, F, process=False); nrm = m.vertex_normals.astype('f4'); fn = m.face_normals.astype('f4')
cn = nrm[F]; flat = np.einsum('fkj,fj->fk', cn, fn) < np.cos(np.deg2rad(35)); cn[flat] = np.repeat(fn[:, None, :], 3, 1)[flat]
PAL = np.array([[222,164,133],[14,14,16],[140,151,157],[241,236,225],[241,236,225],[242,179,192]], 'f4') / 255
(XA, ZA), (XB, ZB) = mm(x0, y0), mm(x1, y1)                       # left/top and right/bottom in model mm
W, H = art.size
ctx = gl.create_standalone_context(backend='egl'); fb = ctx.simple_framebuffer((W, H)); fb.use(); ctx.enable(gl.DEPTH_TEST)
pr = ctx.program(vertex_shader="""#version 330
uniform vec4 B; in vec3 pos; in vec3 normal; in vec3 rgb; out vec3 co; out vec3 N;
void main(){gl_Position=vec4((pos.x-B.x)/(B.y-B.x)*2.-1.,(pos.z-B.w)/(B.z-B.w)*2.-1.,pos.y/160.,1); N=normal; co=rgb;}""",
fragment_shader="""#version 330
in vec3 co; in vec3 N; out vec4 o; void main(){vec3 n=normalize(N); vec3 L=normalize(vec3(-.35,-.85,.45)); vec3 H=normalize(L+vec3(0,-1,0));
float d=.74+.30*max(0.,dot(n,L)); float sp=.05*pow(max(0.,dot(n,H)),30.); o=vec4(co*d+sp,1);}""")
pr['B'].value = (float(XA), float(XB), float(ZA), float(ZB))
vao = ctx.vertex_array(pr, [(ctx.buffer(V[F].reshape(-1, 3).tobytes()), '3f', 'pos'), (ctx.buffer(np.ascontiguousarray(cn, 'f4').tobytes()), '3f', 'normal'),
                            (ctx.buffer(np.repeat(PAL[L], 3, 0).astype('f4').tobytes()), '3f', 'rgb')])
fb.clear(.9, .88, .85, 1, depth=1); vao.render()
mod = Image.frombytes('RGB', (W, H), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
def lines(im):
    d = ImageDraw.Draw(im)
    for name, pts in TRACE.items(): d.line([((c-x0)*k, (r-y0)*k) for c, r in pts], fill=COL[name], width=3)
    return im
sheet = Image.new('RGB', (W, H*4 + 40), 'white'); d = ImageDraw.Draw(sheet)
sheet.paste(art, (0, 0)); sheet.paste(mod, (0, H)); sheet.paste(lines(art.copy()), (0, 2*H)); sheet.paste(lines(mod.copy()), (0, 3*H))
d.text((10, 4*H + 10), 'rows: art | model | art + traced lines | model + the same lines.  blue mouth top, green teeth bottom, red gap bottom, purple upper-lip top', fill='black')
sheet.save(out); print(out, sheet.size, 'model window x %.1f..%.1f z %.1f..%.1f' % (XA, XB, ZB, ZA))
