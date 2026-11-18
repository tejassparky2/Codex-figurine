from render import *
import cv2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
p=np.load(D/'new.npy');rgb=np.load(D/'rgb.npy');r,g,b=rgb.astype('f4').T
x=300+c[:,0]*600/104;y=450-(c[:,2]-75)*900/156
a,t=m.face_adjacency.T
G=coo_matrix((np.ones(len(a)*2,'f4'),(np.r_[a,t],np.r_[t,a])),shape=(len(p),len(p))).tocsr()
def region(i,pts,lab,allowed=range(7),margin=.7,dy=375):
 j=np.load(D/f'id{i}.npy');mask=np.zeros(j.shape,'u1');pts=np.asarray(pts,float);pts[:,1]+=dy;cv2.fillPoly(mask,[np.rint(pts*5/3).astype('i4')],1);ids=j[(mask>0)&(j>=0)]; seeds=np.zeros(len(p),bool);seeds[ids]=1
 from scipy.spatial import cKDTree
 cand=np.flatnonzero(np.isin(p,allowed)&((G@seeds.astype('f4')>0)|seeds))
 if len(ids) and len(cand):
  near=cKDTree(c[seeds]).query(c[cand])[0]<margin;p[cand[near]]=lab
# Front. Identify cuff, shirt opening and flower bands by their sculpt and UV source.
region(0,[(358,165),(379,166),(405,202),(419,216),(368,225),(364,202)],2,[4,3,1])
region(0,[(287,354),(340,354),(343,371),(290,369)],2,[3,4])
region(0,[(274,252),(310,249),(318,224),(335,227),(337,270),(285,278)],2,[4,3])
region(0,[(148,78),(178,65),(203,70),(237,86),(249,98),(228,118),(210,106),(181,92),(148,94)],2,[4,3])
region(0,[(339,19),(397,14),(399,37),(381,71),(354,71)],2,[4,3])
region(0,[(401,12),(418,13),(410,35),(393,51)],4,[3])
# Rear garland and collar and between shoulder trim.
region(4,[(248,186),(271,185),(277,214),(307,214),(315,210),(312,263),(300,278),(260,272)],2,[4,3,1])
region(4,[(267,289),(308,289),(307,318),(268,321)],1,[3,4])
region(4,[(327,93),(341,71),(365,59),(402,55),(437,65),(439,95),(416,81),(389,77),(358,82),(340,100)],2,[4,3])
region(6,[(353,228),(361,146),(367,141),(365,242),(357,250)],2,[4])
# Bride side neckline with original neck visible directly above the jasmine.
region(2,[(289,66),(311,62),(338,63),(364,65),(367,79),(383,79),(390,95),(370,91),(342,102),(294,103)],2,[4,3])
region(2,[(309,61),(326,57),(345,39),(362,35),(364,49),(358,62),(342,63)],4,[3])
# Recover physical neck, cheek and exposed skin where older paint used maroon to simulate a shadow.
p[(p==3)&(y>354)&(y<462)&(x<311)&(r>1.27*g)&(g>.44*r)&(b>.24*r)]=4
p[(p==3)&(y<324)&(x>300)&(r<1.5*g)&(r<63)&(l==5)]=5
# Shadow in recessed turban folds.
p[(x>298)&(y<293)&(p==5)&(c[:,1]>6)&(r>1.28*g)]=3
# Remove stray maroon on groom brows, inside both eyes white and black only.
p[(x>336)&(x<480)&(y>232)&(y<260)&(c[:,1]<0)&(p==3)]=5
# Original ankle/sole outlines.
p[(x>330)&(y>870)&(p==3)&(c[:,2]<1.5)]=0
# Head ornaments and earrings are solid gold, including their source-image highlights.
region(0,[(109,264),(119,248),(132,253),(134,266),(150,275),(147,294),(121,299),(115,292)],0,[2,4],dy=148)
