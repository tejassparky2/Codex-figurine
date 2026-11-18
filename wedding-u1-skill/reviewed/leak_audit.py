"""Find finish-label disagreements using independently sampled local texture and surface adjacency."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree


def scan(mesh, labels, rgb, protected):
    centers = mesh.triangles_center
    a, b = mesh.face_adjacency.T
    graph = coo_matrix((np.ones(len(a)*2), (np.r_[a,b], np.r_[b,a])), shape=(len(labels),)*2).tocsr()
    edge = np.zeros(len(labels), bool)
    different = labels[a] != labels[b]
    edge[a[different]] = edge[b[different]] = True
    near_edge = edge | (graph @ edge > 0)
    seeds = np.flatnonzero(~near_edge)
    if not len(seeds):
        raise ValueError('No interior seed faces available')
    lab = cv2.cvtColor((rgb.astype('f4')/255).reshape(-1,1,3),cv2.COLOR_RGB2LAB).reshape(-1,3)
    outcomes = []
    confidence = []
    # Two spatial scales give independent votes about label continuity at a seam.
    for radius in (1.3, 3.2):
        features = np.column_stack((centers/radius, lab/[10,6,6], mesh.face_normals*.8))
        tree = cKDTree(features[seeds])
        winners = np.empty_like(labels)
        strengths = np.zeros(len(labels))
        for start in range(0,len(labels),30000):
            band = slice(start,start+30000)
            distances, nearest = tree.query(features[band], k=min(15,len(seeds)), workers=3)
            distances = distances.reshape(len(labels[band]),-1)
            nearest = seeds[nearest.reshape(distances.shape)]
            weights = 1/(.05+distances**2)
            votes = np.stack([(weights*(labels[nearest]==k)).sum(axis=1) for k in range(labels.max()+1)],axis=1)
            winners[band] = votes.argmax(axis=1)
            strengths[band] = votes.max(axis=1)/votes.sum(axis=1)
        outcomes.append(winners)
        confidence.append(strengths)
    proposed = outcomes[0]
    agree = proposed == outcomes[1]
    strength = np.minimum(*confidence)
    candidate = (proposed != labels) & agree & (strength >= .70)
    # A candidate must have a connected path to existing paint of its proposed
    # color. This prevents painting through a nearby garment onto a bracelet.
    connected = np.zeros(len(labels),bool)
    for k in np.unique(labels):
        grow = labels == k
        region = candidate & (proposed == k)
        for _ in range(8):
            grow |= region & (graph @ grow > 0)
        connected |= grow & region
    change = candidate & connected & (strength >= .94) & ~protected
    result = labels.copy()
    result[change] = proposed[change]
    return result, candidate, proposed, strength


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path,help='NPZ with v and f in millimeters')
    parser.add_argument('labels',type=Path)
    parser.add_argument('rgb',type=Path,help='Source RGB samples in matching face order')
    parser.add_argument('output',type=Path)
    parser.add_argument('--protect',type=Path,required=True,help='Boolean mask for intentional detail and overrides')
    parser.add_argument('--approved-labels',type=Path,help='Per-face signed integers. Use -1 for unknown and a finish slot for an approved region.')
    args = parser.parse_args()
    data = np.load(args.mesh)
    mesh = trimesh.Trimesh(data['v'],data['f'],process=False)
    labels,rgb,protected = [np.load(p,allow_pickle=False) for p in (args.labels,args.rgb,args.protect)]
    n = len(mesh.faces)
    if labels.shape!=(n,) or labels.dtype.kind not in 'ui' or labels.max()>31 or rgb.shape!=(n,3) or rgb.dtype!=np.uint8 or protected.shape!=(n,) or protected.dtype!=bool:
        parser.error('Invalid face arrays or label range (0–31)')
    result,flagged,proposed,strength = scan(mesh,labels,rgb,protected)
    if args.approved_labels:
        approved = np.load(args.approved_labels,allow_pickle=False)
        if approved.shape!=(n,) or approved.dtype.kind!='i' or approved.min() < -1 or approved.max()>31:
            parser.error('Invalid approved-labels array')
        known = approved>=0
        result[known] = approved[known]
        proposed[known] = approved[known]
        strength[known] = 1
        flagged[known] = approved[known]!=labels[known]
    changed = result!=labels
    args.output.mkdir(parents=True,exist_ok=False)
    np.save(args.output/'finish.npy',result)
    np.savez_compressed(args.output/'findings.npz',face=np.flatnonzero(flagged),prior=labels[flagged],suggested=proposed[flagged],confidence=strength[flagged],applied=changed[flagged])
    print(json.dumps(dict(scanned=n,flagged=int(flagged.sum()),applied=int(changed.sum()),held=int((flagged&~changed).sum()))))


if __name__=='__main__':
    main()
