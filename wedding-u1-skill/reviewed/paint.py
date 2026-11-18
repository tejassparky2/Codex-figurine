from render import *
import cv2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
rgb=np.load(D/'rgb.npy');r,g,b=rgb.astype('f4').T;h,s,val=cv2.cvtColor(rgb.reshape(-1,1,3),cv2.COLOR_RGB2HSV).reshape(-1,3).T.astype('f4')
x=300+c[:,0]*600/104;y=450-(c[:,2]-75)*900/156
a,bf=m.face_adjacency.T;n=len(l)
seed=l.copy()
# Restrict training to confidently painted interiors and their texture families.
ok=np.select([l==0,l==1,l==2,l==3,l==4,l==5,l==6],[(h>12)&(h<40)&(s>110),(r>135)&(g<.48*r)&(b<.46*r),(s<76)&(val>155),(r>27)&(g<.56*r)&(b<.73*r),(r>100)&(g>.47*r)&(b>.32*r)&(s>43)&(h<21),(val<88),(r>108)&(b<r)&(g<.7*r)])
dist=np.zeros(n,bool);cut=l[a]!=l[bf];dist[a[cut]]=dist[bf[cut]]=1
for _ in range(2):
 k=dist[a]|dist[bf];dist[a[k]]=dist[bf[k]]=1
ok=ok.astype(bool)&~dist
features=np.column_stack((rgb,h,s,c[:,0],c[:,1],c[:,2])).astype('f4')
tree=cv2.ml.RTrees_create();tree.setMaxDepth(18);tree.setMinSampleCount(12);tree.setTermCriteria((cv2.TERM_CRITERIA_MAX_ITER,60,0));cv2.setRNGSeed(673)
rng=np.random.default_rng(673);train=np.concatenate([rng.choice(np.where(ok&(l==i))[0],min(20000,int((ok&(l==i)).sum())),replace=False) for i in range(7)])
tree.train(features[train],cv2.ml.ROW_SAMPLE,l[train].astype('i4'));votes=tree.getVotes(features,0);scores=np.zeros((n,7),'f4');scores[:,votes[0]]=votes[1:]/60
# Local evidence for eyelids, pupils and highlights is drawn from original face artwork.
face=(c[:,1]<2)
eyes=face&(((x>150)&(x<303)&(y>289)&(y<351))|((x>341)&(x<474)&(y>255)&(y<304)))
# Preserve deliberate eye graphics; allow white/skin corrections at the outer sclera only.
idx=np.where(eyes&np.isin(l,[5,2]))[0];scores[idx,l[idx]]+=1.6
# Protected motifs on convex jewelry, feather, flowers, binder marks and lips.
def prefer(test,lab,weight=3):scores[test,lab]+=weight
prefer((l==0)&(y<239),0,2.5)
prefer((l==0)&(x<152)&(y>400)&(y<447),0,2)
prefer((l==6)&face,6,2)
prefer((l==1)&(y<290)&face,1,2)
prefer((y>870)&(x<322),0,4)
prefer((y>880)&(x>327),0,4)
# Maroon turban cloth encloses stray dark marks. Use nearby high-confidence chroma to locate boundary.
turban=(x>298)&(y<230)&(l==5)&(r>1.4*g)
prefer(turban,3,4)
# Shade in the hair and shadowed creases belong to the same physical material.
prefer((y<322)&(x>298)&(r>1.7*g)&(r<155)&(l==3),3,1)
# Material graph balances texture evidence with surface adjacency, with low coupling across chromatic edges.
dr=np.linalg.norm(rgb[a].astype('f4')-rgb[bf],axis=1)
weight=(.18+.82*np.exp(-(dr/37)**2))*(.25+.75*np.exp(-(m.face_adjacency_angles/.75)**2))
G=coo_matrix((np.r_[weight,weight],(np.r_[a,bf],np.r_[bf,a])),shape=(n,n)).tocsr()
# Restrict changes to the vicinity of existing same-material patches on the actual mesh.
prior=np.eye(7,dtype='f4')[l]
eligible=prior.copy()
for k in range(10):eligible=np.maximum(eligible,(G@eligible>0).astype('f4'))
scores+=.50*prior
scores[eligible==0]=-9
# Recover especially clear texture evidence on the outer surface and shadowed cloth.
def lock(mask,mat):scores[mask]=-12;scores[mask,mat]=12
lock((y>870)&(x<322),0)
lock(turban,3)
# Ivory fields intentionally include their baked crevice shadows.
lock((l==2)&(((x<150)&(y>450)&(y<770))|((x>327)&(y>735))|(y<120)),2)
lock((l==2)&(((s<90)|(val<190)))&(y>378)&(y<535)&~((x>280)&(x<345)&(y>458)),2)
lock((l==2)&(y>575)&(y<760)&(x>246)&(x<360),2)
# Treat the flower braid, including hidden surfaces, as an ivory piece.
lock((x<141)&(y>450)&(y<770)&np.isin(l,[4,0])&(s<118),2)
# An ivory flower is cream in shadow; in the disputed hand/neck areas the
# high-value, low-saturation textured facets locate the real white petals.
lock((l==4)&(val>=170)&(s<74)&(y>388)&(y<750)&(x>136)&(x<492),2)
# Clean skin, facial jewelry and shadowed fabric without classifying shading as pigment.
lock((l==3)&(r>1.4*g)&(y>400),3)
lock((l==4)&(y<450)&(s>64)&(h>3)&(h<18)&(val>125)&(~eyes),4)
lock((l==5)&(y<405)&(val<75)&~turban,5)
lock((l==0)&(y<450),0)
p=scores.argmax(1);one=np.eye(7,dtype='f4')
for _ in range(7):p=(scores+.70*(G@one[p])).argmax(1)
# Remove only sub-nozzle islands, keeping eye glints and bindi marks.
for _ in range(3):
 k=p[a]==p[bf];nc,cc=connected_components(coo_matrix((np.ones(k.sum(),'u1'),(a[k],bf[k])),shape=(n,n)),directed=False)
 ar=np.bincount(cc,weights=m.area_faces);A=a[~k];B=bf[~k];vote=np.bincount(np.r_[cc[A]*7+p[B],cc[B]*7+p[A]],weights=np.r_[weight[~k],weight[~k]],minlength=nc*7).reshape(nc,7);small=(ar[cc]<.5)&~(eyes&(p==2))&(vote.sum(1)[cc]>0);p[small]=vote.argmax(1)[cc[small]]
np.save(D/'new',p);sheet(p,D/'new.png')
