"""Bake the negative volumes in the OrcaSlicer/Bambu 3MF into a single solid STL.

Usage:  python3 bake_pockets.py ../files/bbq_probe_spool_stand_negative_volumes.3mf out.stl
Unions the normal parts (stand, 3 pegs, box) and subtracts the negative parts
(pocket A 31.54 x 90 x 65 mm, pocket B 40 x 20 x 65 mm; the engraved label is optional,
see ENGRAVE_LABEL).
The storage box's four vertical corners are rounded (CORNER_R, matching the ~3.75 mm
rounded edges on the stand's base plate and panel).
Needs numpy, trimesh, manifold3d.
"""
import xml.etree.ElementTree as ET, numpy as np, trimesh, re, sys, zipfile
NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
def mat(s):
    v=list(map(float,s.split())); M=np.eye(4)
    M[:3,:3]=np.array(v[:9]).reshape(3,3).T if len(v)==12 else np.eye(3); M[:3,3]=v[9:12]; return M
Z=zipfile.ZipFile(sys.argv[1])
obj=ET.fromstring(Z.read('3D/Objects/Assembly_4.model'))
meshes={}
for o in obj.iter('{%s}object'%NS['m']):
    V=np.array([[float(v.get(a)) for a in 'xyz'] for v in o.iter('{%s}vertex'%NS['m'])])
    F=np.array([[int(t.get(a)) for a in ('v1','v2','v3')] for t in o.iter('{%s}triangle'%NS['m'])])
    meshes[o.get('id')]=trimesh.Trimesh(V,F,process=False)
root=ET.fromstring(Z.read('3D/3dmodel.model'))
comps=[(c.get('objectid'),mat(c.get('transform'))) for c in root.iter('{%s}component'%NS['m'])]
build=mat(root.find('.//m:item',NS).get('transform'))
names=['stand','cyl1','cyl2','cyl3','cube(box)','TEXT neg','neg cube A','neg cube B']
parts={}
for (oid,T),n in zip(comps,names):
    m=meshes[oid].copy(); m.apply_transform(T)  # object coords (before build)
    parts[n]=m
    b=m.bounds; print(f'{n:12s} faces {len(m.faces):6d} min {b[0].round(2)} max {b[1].round(2)} size {(b[1]-b[0]).round(2)}')

if __name__=='__main__':
    import manifold3d as mf
    def M(tm):
        tm=tm.copy(); tm.merge_vertices()
        return mf.Manifold(mf.Mesh(vert_properties=np.asarray(tm.vertices,np.float32), tri_verts=np.asarray(tm.faces,np.uint32)))
    for n,m in parts.items():
        mm=M(m); print(f'{n:12s} watertight {m.is_watertight} manifold status {mm.status()} vol {round(mm.volume(),1)}')
    CORNER_R = 3.75
    ENGRAVE_LABEL = False   # True cuts "Luke's BBQ Probe Rack V3" into the box's end face (removed in V3.2)
    pos=['stand','cyl1','cyl2','cyl3']; neg=(['TEXT neg'] if ENGRAVE_LABEL else [])+['neg cube A','neg cube B']
    (x0,y0,z0),(x1,y1,z1) = parts['cube(box)'].bounds
    import math
    pts=[]
    for (cx,cy,a0) in ((x1-CORNER_R,y1-CORNER_R,0),(x0+CORNER_R,y1-CORNER_R,90),(x0+CORNER_R,y0+CORNER_R,180),(x1-CORNER_R,y0+CORNER_R,270)):
        for k in range(25):
            a=math.radians(a0+90*k/24); pts.append((cx+CORNER_R*math.cos(a), cy+CORNER_R*math.sin(a)))
    # start 0.02 mm below the stand's bottom so the two coplanar bottoms don't create slivers
    box=mf.Manifold.extrude(mf.CrossSection([pts]), z1-z0+0.02).translate((0,0,z0-0.02))
    print('rounded box bounds', np.round(box.bounding_box(),2))
    solid=mf.Manifold.batch_boolean([M(parts[n]) for n in pos]+[box], mf.OpType.Add)
    print('union vol', round(solid.volume(),1), 'genus', solid.genus())
    cut=solid - mf.Manifold.batch_boolean([M(parts[n]) for n in neg], mf.OpType.Add)
    cut=cut.translate((0,0,-cut.bounding_box()[2]))
    mesh=cut.to_mesh(); out=trimesh.Trimesh(mesh.vert_properties[:,:3], mesh.tri_verts)
    print('result faces', len(out.faces), 'watertight', out.is_watertight, 'vol', round(out.volume,1), 'bounds', out.bounds.round(2), 'bodies', len(out.split()))
    out.export(sys.argv[2])
    # also export cut-only of the pocket region check
    for n in neg:
        if n not in parts: continue
        b=parts[n].bounds; print(n,'bed-z', (b[0][2]-parts['stand'].bounds[0][2]).round(2), (b[1][2]-parts['stand'].bounds[0][2]).round(2))
