"""Convert a watertight STL to a STEP solid, merging coplanar triangles into flat faces.

Usage:  python3 mesh_to_step.py in.stl out.step   (needs trimesh and cadquery/OCP)
"""
import trimesh, sys, time
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.gp import gp_Pnt
from OCP.TopoDS import TopoDS
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeFix import ShapeFix_Solid
from OCP.TopAbs import TopAbs_SHELL, TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
t0=time.time()
m=trimesh.load(sys.argv[1]); m.merge_vertices()
P=[gp_Pnt(*map(float,v)) for v in m.vertices]
sew=BRepBuilderAPI_Sewing(1e-4)
for f in m.faces:
    poly=BRepBuilderAPI_MakePolygon(P[f[0]],P[f[1]],P[f[2]],True)
    sew.Add(BRepBuilderAPI_MakeFace(poly.Wire(),True).Face())
sew.Perform(); sh=sew.SewedShape(); print('sewn', round(time.time()-t0,1))
ex=TopExp_Explorer(sh,TopAbs_SHELL); shell=TopoDS.Shell_s(ex.Current())
solid=BRepBuilderAPI_MakeSolid(shell).Solid()
fix=ShapeFix_Solid(solid); fix.Perform(); solid=fix.Solid()
u=ShapeUpgrade_UnifySameDomain(solid,True,True,False); u.Build(); res=u.Shape()
n=0; e=TopExp_Explorer(res,TopAbs_FACE)
while e.More(): n+=1; e.Next()
g=GProp_GProps(); BRepGProp.VolumeProperties_s(res,g)
print('faces', len(m.faces),'->',n,'valid',BRepCheck_Analyzer(res).IsValid(),'volume',round(g.Mass(),1),'mesh vol',round(m.volume,1))
w=STEPControl_Writer(); w.Transfer(res,STEPControl_AsIs); w.Write(sys.argv[2]); print('done',round(time.time()-t0,1))
