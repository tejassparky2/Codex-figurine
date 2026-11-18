import trimesh
mesh = trimesh.load('source.glb', force='mesh', process=False)
mesh.merge_vertices(merge_tex=True, merge_norm=True)
mesh.simplify_quadric_decimation(face_count=480000).export('geometry.ply')
