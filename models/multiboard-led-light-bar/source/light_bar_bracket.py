"""Multiboard LED light bar bracket (one part, use as many as you like).

Wedge-shaped brackets that hold an aluminium LED channel (18 x 8.5 mm outer)
with its diffuser facing back toward the wall, angled so the light grazes DOWN the
wall at LIGHT_ANGLE degrees to the wall surface. Each bracket has a Multiboard
push-fit plug (octagon 13.5 mm across flats) centred on its back face that presses
into a "Big Thread - Push-Fit Hole" bolt screwed into a Multiboard big hole. The
channel passes straight through the bracket, so the same part works at either end
or anywhere along the bar.

Coordinates (as installed): X along the bar, Y out from the board, Z up.
Usage: python3 light_bar_bracket.py [out_dir]
"""
import sys, math
import cadquery as cq

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"

# ---- LED channel (aluminium profile, from the product drawing) ----
CH_W, CH_H = 18.0, 8.5          # outer width / height incl. diffuser
CLR = 0.1                       # per-side clearance around the channel (0.2 printed a little loose)

# ---- light direction ----
LIGHT_ANGLE = 30.0              # angle between the light axis and the wall surface (deg)
CH_CENTER = (30.0, -8.0)        # channel centre (Y out from board, Z) relative to plug centre

# ---- bracket body ----
THICK = 13.5                    # bracket thickness along X (= plug size, so the plug prints flat on the bed)
WALL = 3.0                      # material around the pocket in the side profile
PLATE_H, PLATE_D = 40.0, 6.0    # back plate height (Z) and depth (Y) that sits on the bolt head
EDGE_R = 1.5                    # outer edge rounding

# ---- Multiboard push-fit plug (measured from the official push-fit holder) ----
PLUG_AF_BASE, PLUG_AF_TIP = 13.5, 13.24
PLUG_LEN, PLUG_CHAMFER = 8.5, 0.6
PLUG_X = THICK / 2              # plug centred on the back face


a = math.radians(LIGHT_ANGLE)
# unit vectors in the (Y, Z) side plane
n = (-math.sin(a), -math.cos(a))        # light axis: toward the wall and down
w = (math.cos(a), -math.sin(a))         # across the channel width
yc, zc = CH_CENTER

def rect_pts(hw, hh):
    return [(yc + sx*hw*w[0] + sy*hh*n[0], zc + sx*hw*w[1] + sy*hh*n[1])
            for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1))]

def hull(pts):
    pts = sorted(set(pts))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def bracket():
    # side profile: hull of the back plate and the channel + wall
    plate = [(0, -PLATE_H/2), (0, PLATE_H/2), (PLATE_D, PLATE_H/2), (PLATE_D, -PLATE_H/2)]
    prof = hull(plate + rect_pts(CH_W/2 + WALL, CH_H/2 + WALL))
    # YZ workplane: local x = Y, local y = Z, extrude along +X
    body = cq.Workplane("YZ").polyline(prof).close().extrude(THICK)
    body = body.edges().fillet(EDGE_R)

    # channel opening straight through the bracket
    hw, hh = CH_W/2 + CLR, CH_H/2 + CLR
    tunnel = (cq.Workplane("YZ").workplane(offset=-1)
              .polyline(rect_pts(hw, hh)).close().extrude(THICK + 2))
    body = body.cut(tunnel)

    # push-fit plug: tapered octagon along -Y from the back face, centred on it
    px = PLUG_X
    def octo(af, y):
        r = af / 2 / math.cos(math.pi/8)          # circumradius from across-flats
        return cq.Workplane("XZ", origin=(px, y, 0)).polygon(8, 2*r).val()
    y_cham, y_tip = -(PLUG_LEN - PLUG_CHAMFER), -PLUG_LEN
    secs = [cq.Wire.assembleEdges(octo(PLUG_AF_BASE, 0.5).Edges()),     # starts 0.5 mm inside the body
            cq.Wire.assembleEdges(octo(PLUG_AF_TIP, y_cham).Edges()),
            cq.Wire.assembleEdges(octo(PLUG_AF_TIP - 2*PLUG_CHAMFER, y_tip).Edges())]
    plug = cq.Solid.makeLoft(secs, True)
    # rotate 22.5 deg so flats (not corners) face the bed and the sides
    plug = plug.rotate(cq.Vector(px, 0, 0), cq.Vector(px, 1, 0), 22.5)
    body = body.union(cq.Workplane().add(plug))
    return body.val().clean()

def watertight_stl(path):
    """OCC can leave tiny seams where fillets meet flat faces; weld them so the STL is closed."""
    import numpy as np, trimesh, manifold3d as mf
    m = trimesh.load(path); m.merge_vertices(digits_vertex=5)
    mesh = mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32))
    mesh.merge()
    o = mf.Manifold(mesh).to_mesh()
    t = trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts)
    assert t.is_watertight, path
    t.export(path)

if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    parts = {"light_bar_bracket": bracket()}
    for name, s in parts.items():
        cq.exporters.export(s, f"{OUT}/{name}.step")
        cq.exporters.export(s, f"{OUT}/{name}.stl", tolerance=0.02, angularTolerance=0.1)
        watertight_stl(f"{OUT}/{name}.stl")
        bb = s.BoundingBox()
        print(name, "valid", s.isValid(), "vol", round(s.Volume(), 1),
              "bbox X %.1f-%.1f Y %.1f-%.1f Z %.1f-%.1f" % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
