"""Refine visible wedding contacts with source-traced seeds and a face-graph Dirichlet solve."""
import argparse
from pathlib import Path
import cv2
import numpy as np
import trimesh
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import spsolve

# Polygons on the 600x900 front and rear views of the UV-textured mesh.
# Seeds are placed either side of the outline, leaving the intervening band free.
regions=[
 ('lower front ivory garland',0,2,[4,2],[(278,635),(290,643),(304,639),(315,625),(319,607),(331,605),(350,597),(356,593),(354,629),(353,651),(337,648),(319,649),(298,655),(286,661)]),
 ('groom cuff',0,2,[4,2,1,3],[(358,548),(372,545),(383,552),(396,570),(414,587),(424,594),(402,602),(367,608),(362,598),(361,579)]),
 ('bride hand',0,4,[4,2,1],[(277,586),(290,591),(305,598),(316,608),(320,618),(315,625),(315,631),(307,638),(298,643),(288,642),(275,639),(261,632),(264,625),(270,616)]),
 ('groom hand',0,4,[4,2,1,3],[(318,540),(330,540),(342,545),(358,550),(360,574),(364,589),(355,597),(338,603),(325,606),(315,601),(304,601),(300,596),(303,591),(294,591),(294,586),(298,582),(293,581),(294,576),(301,570),(312,565),(324,560),(322,555),(314,551)]),
 ('oblique ivory strand',3,2,[2,4],[(289,582),(300,589),(315,586),(321,584),(315,600),(306,620),(301,648),(297,654),(296,623)]),
 ('rear ivory strand',4,2,[2,4,1],[(253,567),(264,560),(277,565),(278,579),(288,586),(304,591),(316,591),(316,605),(308,652),(288,649),(265,652),(259,627)]),
 ('rear cuff gold border',4,0,[0,4,2,1,3],[(244,486),(256,478),(277,475),(282,485),(288,505),(293,529),(287,557),(278,565),(260,562),(267,545),(265,519),(257,501)]),
 ('groom maroon sleeve',4,3,[3,1,2],[(133,466),(159,441),(187,436),(208,450),(220,471),(232,493),(247,486),(258,502),(265,522),(264,545),(258,560),(236,566),(207,571),(179,563),(156,547),(141,517)]),
]
p=argparse.ArgumentParser(description=__doc__)
for key in ('job','labels','output'):p.add_argument(key,type=Path)
args=p.parse_args()
z=np.load(args.job/'repaired-u1.npz');m=trimesh.Trimesh(z['v'],z['f'],process=False)
rgb=np.load(args.job/'rgb.npy'); labels=np.load(args.labels).copy()
a,b=m.face_adjacency.T
lab=cv2.cvtColor((rgb.astype('f4')/255).reshape(-1,1,3),cv2.COLOR_RGB2LAB).reshape(-1,3)
delta=np.linalg.norm(lab[a]-lab[b],axis=1)
weight=.001+np.exp(-.5*(delta/10)**2-.5*(m.face_adjacency_angles/.8)**2)
G=coo_matrix((np.r_[weight,weight],(np.r_[a,b],np.r_[b,a])),shape=(len(labels),)*2).tocsr()
for name,i,color,allowed,points in regions:
    ids=np.load(args.job/f'id{i}.npy')
    mask=np.zeros(ids.shape,'uint8')
    cv2.fillPoly(mask,[np.rint(np.array(points)*5/3).astype('i4')],1)
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15))
    inner=cv2.erode(mask,kernel);outer=cv2.dilate(mask,kernel,iterations=2)
    visible=(ids>=0)&(outer!=0)
    # Include small facets that fall between raster samples. Use depth and local normals
    # to avoid marking surfaces behind the arm on the same projection ray.
    center=m.triangles_center
    angle=np.deg2rad(i*45)
    direction=np.array([np.sin(angle),np.cos(angle),0])
    depth=center@direction
    width=ids.shape[1]; height=ids.shape[0]
    col=np.clip(np.floor((.5+(center[:,0]*np.cos(angle)-center[:,1]*np.sin(angle))/104)*width).astype(int),0,width-1)
    row=np.clip(np.floor((.5-(center[:,2]-75)/156)*height).astype(int),0,height-1)
    hit=ids[row,col]
    near=(hit>=0)&(np.abs(depth-depth[hit])<.32)&(m.face_normals@direction<0)
    seen=np.zeros(len(labels),bool)
    seen[np.unique(ids[visible])]=True
    faces=np.flatnonzero(seen|(near&(outer[row,col]!=0)))
    is_core=inner[row[faces],col[faces]]!=0
    extended=cv2.dilate(mask,kernel)
    is_ext=(extended[row[faces],col[faces]]==0)&~is_core
    graph=G[faces][:,faces];L=diags(np.asarray(graph.sum(1)).ravel())-graph
    seed=is_core|is_ext;free=~seed
    prior=mask[row[faces],col[faces]].astype(float)
    sol=is_core.astype(float)
    # Weak outline prior resolves components isolated by self-occlusion.
    sol[free]=spsolve(L[free][:,free]+diags(np.full(free.sum(),.015)), -(L[free][:,seed]@sol[seed])+.015*prior[free])
    take=faces[(sol>=.65)&np.isin(labels[faces],allowed)]
    print(name,int((labels[take]!=color).sum()))
    labels[take]=color
np.save(args.output,labels)
