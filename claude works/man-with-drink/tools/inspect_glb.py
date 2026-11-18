import sys, trimesh, numpy as np, json, struct
for p in sys.argv[1:]:
    with open(p,'rb') as fh:
        fh.read(12); n,_=struct.unpack('<II',fh.read(8)); gj=json.loads(fh.read(n))
    gen=gj.get('asset',{}).get('generator'); ext=gj.get('extensionsUsed')
    s=trimesh.load(p,process=False)
    geoms=s.geometry if isinstance(s,trimesh.Scene) else {'mesh':s}
    print('==',p.split('/')[-1],'| generator:',gen,'| ext:',ext,'| nodes',len(gj.get('nodes',[])),'meshes',len(gj.get('meshes',[])),'images',len(gj.get('images',[])))
    m=s.to_geometry() if isinstance(s,trimesh.Scene) else s
    print('   faces',len(m.faces),'verts',len(m.vertices),'extents',np.round(m.extents,4),'bounds',np.round(m.bounds,3).tolist())
    for k,g in geoms.items():
        mat=getattr(g.visual,'material',None)
        tex=getattr(mat,'baseColorTexture',None) if mat is not None else None
        print('   geom',k,len(g.faces),'uv' if getattr(g.visual,'uv',None) is not None else 'no-uv','tex',None if tex is None else tex.size, type(mat).__name__,
              'metal/rough tex', None if mat is None or getattr(mat,'metallicRoughnessTexture',None) is None else mat.metallicRoughnessTexture.size,
              'normal', None if mat is None or getattr(mat,'normalTexture',None) is None else mat.normalTexture.size)
    w=trimesh.Trimesh(m.vertices,m.faces,process=True)
    print('   welded: watertight',w.is_watertight,'bodies',w.body_count,'volume?',w.is_volume)
