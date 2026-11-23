# SPDX-License-Identifier: MIT
"""Wall-mounted slide-in holder for a slim LED-light remote.

The remote drops in from the top, buttons facing out, and rests on a floor.
Front lips along both sides and a solid band across the bottom keep it from
tipping forward; it lifts straight up and out. Two countersunk holes in the
back take drywall screws (or screws into anchors / a stud).

Prints upright (floor on the bed) so the lips and front band are plain
vertical walls: no supports, no bridges.

Coordinates: X across the remote (width), Y out from the wall (0 = wall),
Z up (0 = bottom of the holder = print bed).
Usage: python3 remote_holder.py [out_dir]
"""
import sys, os
import cadquery as cq

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"

# ---- remote, measured with calipers ----
REMOTE_W = 38.09        # width
REMOTE_T = 13.34        # thickness (at the thickest point; the back is curved)
REMOTE_L = 151.26       # length (reference only)

# ---- fit ----
CLR_W = 0.6             # total clearance across the width  (0.3 mm per side)
CLR_T = 0.5             # total clearance front-to-back
POCKET_R = 3.0          # pocket corner radius (remote has rounded corners)

# ---- holder ----
BACK = 4.0              # back plate thickness (deep enough to sink the screw heads)
WALL = 2.4              # side wall thickness
FRONT = 2.0             # front lip / band thickness
FLOOR = 3.0             # floor thickness
DEPTH_IN = 75.0         # how much of the remote sits inside (remote sticks out ~76 mm)
LIP = 5.0               # how far each front lip overlaps the remote's edge
BAND_H = 24.0           # height of the solid front band above the floor
WINDOW_R = 8.0          # radius of the bottom corners of the front opening
OUTER_R = 3.0           # radius on the outer front vertical edges
ENTRY = 1.2             # top lead-in chamfer on the pocket

# ---- screws (#6 / #8 drywall screw, bugle head ~8 mm) ----
SCREW_D = 4.5           # clearance hole
HEAD_D = 9.0            # countersink diameter at the surface
SCREW_Z = (34.0, 66.0)  # hole heights above the bed; both sit in the front opening so a driver reaches them

PW = REMOTE_W + CLR_W
PT = REMOTE_T + CLR_T
W = PW + 2 * WALL
D = BACK + PT + FRONT
H = FLOOR + DEPTH_IN


def rrect(w, t, r, z0, h, y0):
    """Rounded-rectangle prism, centred on X, from y0 to y0+t, z0 to z0+h."""
    return (cq.Workplane("XY").workplane(offset=z0)
            .center(0, y0 + t / 2).rect(w, t).extrude(h)
            .edges("|Z").fillet(r))


def holder(height=H, floor=FLOOR, band=BAND_H, screws=True):
    body = (cq.Workplane("XY").center(0, D / 2).rect(W, D).extrude(height))
    body = body.edges("|Z and >Y").fillet(OUTER_R).edges("|Z and <Y").fillet(1.0)

    # pocket for the remote
    body = body.cut(rrect(PW, PT, POCKET_R, floor, height, BACK))

    # front opening between the lips, with rounded bottom corners
    ww = PW - 2 * LIP
    win = (cq.Workplane("XY").workplane(offset=floor + band)
           .center(0, BACK + PT / 2 + D / 2).rect(ww, D).extrude(height))
    win = win.edges("|Y and <Z").fillet(min(WINDOW_R, ww / 2 - 0.1))
    body = body.cut(win)

    # lead-in chamfer at the top of the pocket
    lead = (cq.Workplane("XY").workplane(offset=height - ENTRY)
            .center(0, BACK + PT / 2).rect(PW, PT)
            .workplane(offset=ENTRY + 0.01).rect(PW + 2 * ENTRY, PT + 2 * ENTRY)
            .loft())
    body = body.cut(lead)

    if screws:
        for z in SCREW_Z:
            hole = cq.Workplane("XZ").center(0, z).circle(SCREW_D / 2).extrude(-BACK - 1).translate((0, -0.5, 0))
            depth = (HEAD_D - SCREW_D) / 2          # 90 deg countersink
            csk = cq.Solid.makeCone(SCREW_D / 2, HEAD_D / 2 + 0.3, depth + 0.3,
                                    pnt=cq.Vector(0, BACK - depth, z), dir=cq.Vector(0, 1, 0))
            body = body.cut(hole).cut(cq.Workplane().add(csk))
    return body.val().clean()


def fit_coupon():
    """A 10 mm slice of the holder (lips, no floor) to check the fit before the full print."""
    return holder(height=10.0, floor=0.0, band=-20.0, screws=False)


def watertight_stl(path):
    import numpy as np, trimesh, manifold3d as mf
    m = trimesh.load(path); m.merge_vertices(digits_vertex=5)
    mesh = mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32))
    mesh.merge()
    o = mf.Manifold(mesh).to_mesh()
    t = trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts)
    assert t.is_watertight, path
    t.export(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    parts = {"remote_wall_holder": holder(), "remote_fit_coupon": fit_coupon()}
    for name, s in parts.items():
        cq.exporters.export(s, f"{OUT}/{name}.step")
        cq.exporters.export(s, f"{OUT}/{name}.stl", tolerance=0.02, angularTolerance=0.1)
        watertight_stl(f"{OUT}/{name}.stl")
        bb = s.BoundingBox()
        print(name, "valid", s.isValid(), "vol", round(s.Volume(), 1),
              "bbox X %.1f-%.1f Y %.1f-%.1f Z %.1f-%.1f" % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
    print(f"pocket {PW:.2f} x {PT:.2f}  outer {W:.2f} W x {D:.2f} D x {H:.1f} H")
