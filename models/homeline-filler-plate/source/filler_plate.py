# SPDX-License-Identifier: MIT
"""Snap-in filler plate for a Square D Homeline load center cover opening
(single- and double-pole versions). Inspired by the Square D HOMFPCP.

The opening in the cover runs across the breaker row; removed twist-outs leave
a continuous slot, so the plate latches only on the two side edges. Each end has
a folded (U-shaped) spring leaf with a hook that snaps behind the cover steel.

The part is a single 2D profile extruded through its height, so it prints lying
on its long edge (height = print Z) with the spring leaves flexing in the layer
plane, which makes them much stronger than leaves printed across the layers.

Coordinates: X across the opening (width), Z into the panel (0 = front of face),
Y = height (one breaker space per pole).
Usage: python3 filler_plate.py [out_dir]
"""
import sys, os, math
import cadquery as cq

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"

# ---- measured from the HOM1224L125PGCVP cover ----
OPEN_W = 59.33          # opening width between the side edges
SPACE_H = 25.0          # opening height per breaker space (1 in pitch)
STEEL_T = 1.33          # cover steel thickness at the opening edge

# ---- plate ----
FACE_W = 65.0           # face width (HOMFPCP is 2.56 in = 65 mm) -> ~2.8 mm overlap each side
FACE_T = 2.0            # face thickness
FACE_GAP = 0.2          # total height gap so neighbouring plates/breakers don't bind
FACE_CHAMFER = 0.6      # front edge chamfer

# ---- spring latch ----
DEPTH = 16.0            # overall depth from face front to back of the latch
EDGE_CLR = 0.165        # leaf outer surface inside the opening edge (per side)
LEAF_T = 1.2            # spring leaf thickness
POST_T = 2.0            # rigid post thickness
FLEX_GAP = 1.5          # room for the leaf to flex inward
FREE_GAP = 0.6          # gap between the leaf's free end and the back of the face
HOOK = 1.0              # hook protrusion beyond the leaf (bite on steel = HOOK - EDGE_CLR)
HOOK_CLR = 0.2          # clearance between steel back and hook ledge
HOOK_FLAT = 0.5         # flat on the hook before the lead-in ramp
RAMP = 4.0              # lead-in ramp length (along Z)
BRIDGE_T = 1.2          # thickness of the U bend that joins post and leaf

def latch_profile(sign):
    """Closed (x, z) polygons for one end; sign=+1 right, -1 left."""
    xo = OPEN_W / 2 - EDGE_CLR                 # leaf outer surface
    xl = xo - LEAF_T                           # leaf inner surface
    xp1 = xl - FLEX_GAP                        # post outer surface
    xp0 = xp1 - POST_T                         # post inner surface
    zl = FACE_T + STEEL_T + HOOK_CLR           # hook ledge (catches the back of the steel)
    polys = [
        [(xp0, FACE_T - 0.5), (xp1, FACE_T - 0.5), (xp1, DEPTH - BRIDGE_T), (xl, DEPTH - BRIDGE_T),
         (xl, FACE_T + FREE_GAP), (xo, FACE_T + FREE_GAP), (xo, zl), (xo + HOOK, zl),
         (xo + HOOK, zl + HOOK_FLAT), (xo, zl + HOOK_FLAT + RAMP), (xo, DEPTH), (xp0, DEPTH)],
    ]
    return [[(sign * x, z) for x, z in p] for p in polys]

def plate(poles=1):
    H = poles * SPACE_H - FACE_GAP
    # face: XZ profile extruded along Y (height)
    wp = lambda: cq.Workplane("XZ", origin=(0, H / 2, 0))   # XZ normal is -Y, so extrude H goes -Y
    face = wp().polyline([(-FACE_W/2 + FACE_CHAMFER, 0), (FACE_W/2 - FACE_CHAMFER, 0),
                          (FACE_W/2, FACE_CHAMFER), (FACE_W/2, FACE_T), (-FACE_W/2, FACE_T),
                          (-FACE_W/2, FACE_CHAMFER)]).close().extrude(H)
    body = face
    for sign in (+1, -1):
        for poly in latch_profile(sign):
            pts = poly if sign > 0 else poly[::-1]
            body = body.union(wp().polyline(pts).close().extrude(H))
    return body.val().clean(), H

def leaf_check(H):
    """Bending strain and insertion force for the spring leaf (simple cantilever)."""
    L = DEPTH - BRIDGE_T - (FACE_T + FREE_GAP)         # free leaf length
    d = HOOK + EDGE_CLR                                 # deflection to pass the steel edge
    strain = 3 * LEAF_T * d / (2 * L**2)
    E = 2000.0                                          # MPa, PETG/ABS ballpark
    I = H * LEAF_T**3 / 12
    F = 3 * E * I * d / L**3
    return L, d, strain, F

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
    for poles, name in ((1, "homeline_filler_plate_1pole"), (2, "homeline_filler_plate_2pole")):
        s, H = plate(poles)
        cq.exporters.export(s, f"{OUT}/{name}.step")
        cq.exporters.export(s, f"{OUT}/{name}.stl", tolerance=0.01, angularTolerance=0.1)
        watertight_stl(f"{OUT}/{name}.stl")
        bb = s.BoundingBox()
        L, d, strain, F = leaf_check(H)
        print(f"{name}: valid {s.isValid()} vol {s.Volume():.0f} mm3  size {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f}"
              f"  | leaf L {L:.1f} mm, deflection {d:.2f} mm, strain {strain*100:.2f} %, insert force ~{F:.0f} N per side")
