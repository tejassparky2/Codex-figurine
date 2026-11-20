from pathlib import Path
import sys,numpy as np
sys.path.insert(0,'wedding-u1-skill/coloring')
from approved_match import load_model
v,f,l,p=load_model('/dev/shm/incoming.3mf')
z=v[f,2]
use=l==3
assert not np.any(use&(z.min(1)<120)&(z.max(1)>=120))
white=use&(z.min(1)>=120)
print('Dimensions',v.ptp(0) if hasattr(v,'ptp') else np.ptp(v,axis=0),'faces',len(f),'T4 orange top',z[use&~white].max(),'white bottom',z[white].min(),flush=True)
l[white]=4
np.savez('/dev/shm/drinkcheck/mesh.npz',v=v,f=f)
np.save('/dev/shm/drinkcheck/labels.npy',l)
