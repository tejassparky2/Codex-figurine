"""RGB close-up (per-face colours from an Nx3 uint8 .npy). Was: Label close-up from any azimuth: python zoom.py labels.npy out.png wx wy wz half_mm yaw_deg [ppm] [elev]"""
import sys, numpy as np, moderngl as gl
from PIL import Image
lab = np.load(sys.argv[1]); out = sys.argv[2]; wx, wy, wz, hw, yaw = map(float, sys.argv[3:8]); ppm = float(sys.argv[8]) if len(sys.argv) > 8 else 25; el = np.deg2rad(float(sys.argv[9]) if len(sys.argv) > 9 else 0)
PAL = np.array([[222,164,133],[14,14,16],[140,151,157],[241,236,225],[249,168,0],[242,179,192]], 'f4')/255
import os; z = np.load(os.environ.get('MESH', 'printable.npz')); V, F = z['v'], z['f']; S = int(2*hw*ppm)
n = np.cross(V[F][:,1]-V[F][:,0], V[F][:,2]-V[F][:,0]); n /= np.linalg.norm(n, axis=1, keepdims=True)+1e-12
a = np.deg2rad(yaw); right = np.array([np.cos(a), -np.sin(a), 0]); fwd = np.array([np.sin(a)*np.cos(el), np.cos(a)*np.cos(el), -np.sin(el)]); up = np.cross(right, fwd)
shade = .78 + .22*np.clip(-(n @ (fwd*.8 - up*.4 + right*.3)), 0, 1)
ctx = gl.create_standalone_context(backend='egl'); fb = ctx.simple_framebuffer((S, S)); fb.use(); ctx.enable(gl.DEPTH_TEST)
p = ctx.program(vertex_shader="""#version 330
uniform vec3 r; uniform vec3 u; uniform vec3 d; uniform vec3 C; uniform float h; in vec3 pos; in vec3 col; out vec3 c;
void main(){vec3 q=pos-C; gl_Position=vec4(dot(q,r)/h,dot(q,u)/h,dot(q,d)/200.,1); c=col;}""", fragment_shader="""#version 330
in vec3 c; out vec4 o; void main(){o=vec4(c,1);}""")
p['r'].value = tuple(right); p['u'].value = tuple(up); p['d'].value = tuple(fwd); p['C'].value = (wx, wy, wz); p['h'].value = hw
col = np.repeat(((lab.astype('f4')/255.)*shade[:,None]).astype('f4'), 3, axis=0)
ctx.vertex_array(p, [(ctx.buffer(V[F].astype('f4').tobytes()), '3f', 'pos'), (ctx.buffer(col.tobytes()), '3f', 'col')]).render() if fb.clear(1,1,1,1,depth=1) is None else None
Image.frombytes('RGB', (S, S), fb.read()).transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(out)
