from manual import *
j=np.load(D/'id0.npy');tex=np.vstack([rgb,palette[-1]])[j]
def trace(pts,lab,allow,dx=7,dy=375):
 poly=np.array(pts,'f4');poly[:,1]+=dy;coords=np.rint(poly*5/3).astype('i4');x,y,w,h=cv2.boundingRect(coords);pad=30
 x-=pad;y-=pad;w+=pad*2;h+=pad*2
 src=tex[y:y+h,x:x+w].copy();ii=j[y:y+h,x:x+w];s=np.zeros((h,w),'u1');cv2.fillPoly(s,[(coords-[x,y]).astype('i4')],1)
 ker=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*dx+1,2*dx+1));lo=cv2.erode(s,ker);hi=cv2.dilate(s,ker);mask=np.where(lo,1,np.where(s,3,np.where(hi,2,0))).astype('u1');cv2.setRNGSeed(19)
 cv2.grabCut(src,mask,None,np.zeros((1,65),'f8'),np.zeros((1,65),'f8'),5,cv2.GC_INIT_WITH_MASK)
 ids=ii[(mask%2>0)&(ii>=0)];arr=np.unique(ids);p[arr[np.isin(p[arr],allow)]]=lab
trace([(265,201),(275,200),(282,196),(297,199),(312,209),(315,221),(308,226),(313,229),(308,241),(298,246),(291,246),(287,249),(274,245),(262,238)],4,[2,1,3,4],6)
trace([(301,178),(314,170),(322,168),(317,161),(324,159),(340,164),(357,172),(363,196),(358,210),(342,220),(329,224),(319,221),(313,212),(302,213),(295,206),(296,200),(291,198),(291,188)],4,[2,1,3,4],7)
trace([(359,171),(376,167),(385,178),(414,210),(418,217),(368,225),(363,203)],2,[4,2,3],6)
# Small isolated tip errors at skirt and coat edges.
for _ in range(3):
 same=p[a]==p[t];nc,cc=connected_components(coo_matrix((np.ones(same.sum(),'u1'),(a[same],t[same])),shape=(len(p),len(p))),directed=False)
 ar=np.bincount(cc,weights=m.area_faces);s1=a[~same];s2=t[~same];vote=np.bincount(np.r_[cc[s1]*7+p[s2],cc[s2]*7+p[s1]],minlength=nc*7).reshape(nc,7)
 small=(ar[cc]<.55)&~((y<355)&(p==2)&(x>150)&(x<473)&(c[:,1]<0))&(vote.sum(1)[cc]>0);p[small]=vote.argmax(1)[cc[small]]
np.save(D/'final',p);sheet(p,D/'review.png')
