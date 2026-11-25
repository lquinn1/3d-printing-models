# SPDX-License-Identifier: MIT
"""Door for the dry cabinet: 4 printed members (2 stiles, 2 rails split in halves),
twin polycarbonate panes in grooves, M3-pinned hinges, corner catch magnets and a
draw-in lever latch (inspired by the Clicky-Clack fridge door) that doubles as the handle.

World frame as in tiles.py / front.py. Closed, the door sits in front of the frame ring:
    x DX0 .. DX1, z DZ0 .. DZ1, y DY0 .. DY1  (DY1 = 13.0: 3 mm foam seal on the ring, squeezed to 2.0)
Member cross-section (door depth t = y - DY0, 0 = front):
    front lip 1.6 | front pane slot 2.6 | spacer 5.6 | back pane slot 2.6 | back lip 1.6   = 14
"""
import os, math, numpy as np, manifold3d as mf, cadquery as cq
from params import *
from coupons import cyl, save, cq_to_mf, OUT
from tiles import W, X_SLOT, Z0
from front import (box, cyl_x, cyl_y, cyl_z, F_Y0, HDR_Z0, HINGE_Z, MAGNET_Z, REED_Z, MAGNET_D, MAGNET_H,
                   LATCH_Z, LATCH_POST,
                   M3_INSERT_D, M3_INSERT_L, M3_CLR, STILE_W, OPEN_X0, OPEN_X1, LIP_Z0)

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
EPDM_T, EPDM_SQ = 3.0, 2.0           # 33 % squeeze: what a soft foam seal is made for (was 50 %)
DY1 = F_Y0 - EPDM_T + EPDM_SQ         # 13.0: door back face when latched
DT = 14.0
DY0 = DY1 - DT                        # -1.0: door front (1.0 mm proud of the header)
DX0, DX1 = 1.0, W - 1.0
DZ0, DZ1 = Z0 + 1.0, HDR_Z0 - 1.0     # 11 .. 424.5
B = 30.0                              # member width
SLOT_DEPTH = 10.0
PANE_T = 2.6                          # slot for 2.0-2.5 mm polycarbonate
LIPF, SPACER = 1.6, 5.6
SLOTS_T = [(LIPF, LIPF + PANE_T), (LIPF + PANE_T + SPACER, LIPF + 2*PANE_T + SPACER)]
Y_MID = DY0 + LIPF + PANE_T + SPACER/2          # screw line between the panes
PANE_CLR = 0.5
HINGE_AXIS = (-4.5, DY0 - 4.5)        # outside the front-left corner
KN_R, PIN_D = 5.5, 3.3                # knuckle Ø11 (was Ø9)
MAG_X = W - 8.0
CORNER_SCREW_DZ = (7.0, 23.0)         # from the outer edge of each rail
TAG_TEXT = 'PETG'

XL1, XR0 = DX0 + B, DX1 - B           # inner edges of the stiles
ZB1, ZT0 = DZ0 + B, DZ1 - B           # inner edges of the rails
PANE = (XR0 + SLOT_DEPTH - (XL1 - SLOT_DEPTH) - 2*PANE_CLR, ZT0 + SLOT_DEPTH - (ZB1 - SLOT_DEPTH) - 2*PANE_CLR)

def slots_x(x0, x1, z0, z1):            # grooves cut parallel to x (rails), across the given z band
    return [box(x0, x1, DY0 + a, DY0 + b, z0, z1) for a, b in SLOTS_T]

def slots_z(x0, x1, z0, z1):            # grooves parallel to z (stiles)
    return [box(x0, x1, DY0 + a, DY0 + b, z0, z1) for a, b in SLOTS_T]

def corner_z(rail):
    return [(DZ0 if rail == 'bottom' else DZ1 - B) + d for d in CORNER_SCREW_DZ]

def stile(side):
    x0, x1 = (DX0, XL1) if side == 'L' else (XR0, DX1)
    m = box(x0, x1, DY0, DY1, DZ0, DZ1)
    sx0, sx1 = (XL1 - SLOT_DEPTH, XL1 + 1) if side == 'L' else (XR0 - 1, XR0 + SLOT_DEPTH)
    for s in slots_z(sx0, sx1, ZB1 - SLOT_DEPTH - 0.5, ZT0 + SLOT_DEPTH + 0.5): m -= s
    # corner screws through the stile into the rail ends (heads on the outer edge)
    xo = x0 if side == 'L' else x1
    d = 1 if side == 'L' else -1
    for z in corner_z('bottom') + corner_z('top'):
        m -= cyl_x(Y_MID, z, min(x0, x1) - 1, max(x0, x1) + 1, M3_CLR/2)
        m -= cyl_x(Y_MID, z, xo - 1 if d > 0 else xo - 7, xo + 7 if d > 0 else xo + 1, 3.1)
    if side == 'L':
        for hz in HINGE_Z:                                   # door-leaf screw (M3 insert in the edge)
            m -= cyl_x(Y_MID, hz, DX0 - 1, DX0 + M3_INSERT_L, M3_INSERT_D/2)
    else:
        for mz in list(MAGNET_Z) + [REED_Z]:                 # catch magnets + reed trigger, from the back
            m -= cyl_y(MAG_X, mz, DY1 - MAGNET_H, DY1 + 1, MAGNET_D/2, n=48)
        # latch: M3 insert in the edge for the lever's pivot screw, click magnet in the front face
        m -= cyl_x(LP_Y, LATCH_Z, DX1 - M3_INSERT_L, DX1 + 1, M3_INSERT_D/2)
        m -= cyl_y(CLICK_X, CLICK_Z, DY0 - 1, DY0 + MAGNET_H, MAGNET_D/2, n=48)
    return m

def rail(which, half):
    z0, z1 = (DZ0, ZB1) if which == 'bottom' else (ZT0, DZ1)
    xm = W/2
    x0, x1 = (XL1, xm) if half == 'L' else (xm, XR0)
    m = box(x0, x1, DY0, DY1, z0, z1)
    sz0, sz1 = (ZB1 - SLOT_DEPTH, ZB1 + 1) if which == 'bottom' else (ZT0 - 1, ZT0 + SLOT_DEPTH)
    for s in slots_x(x0 - 1, x1 + 1, sz0, sz1): m -= s
    # inserts in the outer end for the corner screws
    xe, d = (x0, 1) if half == 'L' else (x1, -1)
    for z in corner_z(which):
        m -= cyl_x(Y_MID, z, xe - 1 if d > 0 else xe - M3_INSERT_L, xe + M3_INSERT_L if d > 0 else xe + 1, M3_INSERT_D/2)
    # centre joint: stub tenon on the left half, mortise in the right half (acetone weld + 0.2 clr)
    tz0, tz1 = (z0 + 4, z1 - SLOT_DEPTH - 2) if which == 'bottom' else (z0 + SLOT_DEPTH + 2, z1 - 4)
    ty0, ty1 = DY0 + LIPF + PANE_T + 0.6, DY0 + LIPF + PANE_T + SPACER - 0.6
    if half == 'L':
        m += box(xm - 0.01, xm + 15, ty0, ty1, tz0, tz1)
    else:
        m -= box(xm - 1, xm + 15.4, ty0 - 0.2, ty1 + 0.2, tz0 - 0.2, tz1 + 0.2)
    if which == 'bottom':
        # slot numbers 1-6 (debossed 0.8 mm) and the backup-tag pocket, in the solid band under the slots
        zc = (DZ0 + ZB1 - SLOT_DEPTH) / 2
        for i, xs in enumerate(X_SLOT):
            if x0 < xs < x1:
                t = (cq.Workplane('XZ').workplane(offset=-(DY0 - 1))
                     .center(xs, zc).text(str(i + 1), 12, 1.8, fontPath=FONT, halign='center', valign='center'))
                m -= cq_to_mf(t.val())
        tag = box(xm - 20.5, xm + 20.5, DY0 - 1, DY0 + 1.2, zc - 6.5, zc + 6.5)
        m -= tag ^ box(x0, x1, DY0 - 2, DY1, z0, z1)
    return m

def backup_tag(text=TAG_TEXT):
    """40.6 x 12.6 x 1.2 tag; press-fits the pocket in the bottom rail (0.2 mm clearance)."""
    t = cq.Workplane().box(40.6, 12.6, 1.2, centered=(True, True, False)).edges('|Z').fillet(1.0)
    t = t.union(cq.Workplane().workplane(offset=1.2).text(text, 8, 0.6, fontPath=FONT, halign='center', valign='center'))
    return cq_to_mf(t.val())

# ------------------------------------------------------------------ hinges
def hinge_bands(hz):
    return {'frame': [(hz - 20, hz - 6.75), (hz + 6.75, hz + 20)], 'door': [(hz - 6.25, hz + 6.25)]}

def hinge_frame_leaf(hz):
    ax, ay = HINGE_AXIS
    m = None
    for z0, z1 in hinge_bands(hz)['frame']:
        k = cyl_z(ax, ay, z0, z1, KN_R, n=48)
        k += box(-3.2, 0, ay, 28.0, z0, z1)                                   # leaf along the stile side
        k += box(ax, -3.2 + 0.01, ay - KN_R + 1.2, ay + KN_R, z0, z1) ^ box(ax, 0, ay - 1, ay + KN_R, z0, z1)
        m = k if m is None else m + k
    # one piece: a web behind the door (y 14.5..28) joins the two knuckle leaves, so both
    # screws hold the whole leaf and it can't turn on either screw (v0.16)
    m += box(-3.2, 0, 14.5, 28.0, hz - 20, hz + 20)
    m -= cyl_z(ax, ay, hz - 21, hz + 21, PIN_D/2, n=32)
    for dz in (-12.0, 12.0):                                                  # into the stile's M3 inserts
        zz = hz + dz
        m -= cyl_x((F_Y0 + 28.0)/2, zz, -4, 1, M3_CLR/2)
        m -= cyl_x((F_Y0 + 28.0)/2, zz, -4, -1.6, 3.1)
    return m

def hinge_door_leaf(hz):
    ax, ay = HINGE_AXIS
    z0, z1 = hinge_bands(hz)['door'][0]
    m = cyl_z(ax, ay, z0, z1, KN_R, n=48)
    m += box(ax, DX0, ay - KN_R + 1.2, DY1 - 1.0, z0, z1) - box(-3.4, DX0 + 1, DY0 - 0.01, DY1, z0 - 1, z1 + 1)
    m += box(-3.4, DX0, DY0, DY1 - 1.0, z0, z1)                               # leaf on the door's edge
    m -= cyl_z(ax, ay, z0 - 1, z1 + 1, PIN_D/2, n=32)
    m -= cyl_x(Y_MID, hz, -5, DX0 + 1, M3_CLR/2)
    m -= cyl_x(Y_MID, hz, -5, -3.4 + 1.2, 3.1)
    return m

# ------------------------------------------------------------------ latch (draw-in lever)
# The lever turns on an M3 screw in the door's right edge (axis along x). Its arm runs back
# along the cabinet's side; a tooth at the end hooks behind an M4 post (bolt + sleeve) in
# the frame stile. Closing the door, the post rides up the tooth's ramp and drops into the
# notch (the click). Pressing the handle home draws the door onto the seal; a magnet pair
# holds it there. Pull the handle forward and the same motion unhooks and opens the door.
LP_Y = 6.0                             # pivot axis (y, z = LATCH_Z), inside the door's depth
LV_X0, LV_X1 = W + 1.0, W + 7.0        # lever plate (beside the cabinet's side face)
LV_ARM = (LATCH_Z - 8.0, LATCH_Z + 4.0)  # arm z band
POST_R = 3.0                           # 6 mm OD sleeve on an M4 bolt
SLEEVE_L = 8.0
CLICK_X, CLICK_Z = W - 13.4, 184.0     # click magnets: door front face / lever grip
GRIP = (W - 40.0, LV_X1, DY0 - 8.0, DY0 - 1.2, 172.0, 196.0)   # x0, x1, y0, y1, z0, z1
TOOTH_SLOPE = 0.6                      # tooth face lean (dy/dz): the draw-in ramp (about 2 mm)

def _tooth_face():
    """Line of the tooth's contact face (closed pose): it just touches the post."""
    py, pz = LATCH_POST
    n = np.array([1.0, -TOOTH_SLOPE]); n /= np.linalg.norm(n)      # from the post toward the face
    q = np.array([py, pz]) + POST_R * n
    return q, np.array([TOOTH_SLOPE, 1.0])                            # point, direction (y, z)

def latch_lever():
    py, pz = LATCH_POST
    za, zb = LV_ARM
    q, d = _tooth_face()
    yf = lambda z: q[0] + (z - q[1]) * d[0] / d[1]                   # face y at height z
    floor = pz - POST_R - 0.3
    top = pz + POST_R - 0.5
    # side plate: hub + arm + tooth, as a y-z polygon extruded along x
    poly = [(LP_Y - 7, za), (34.0, za), (34.0, 244.0), (yf(top) + 0.6, top), (yf(top), top),
            (yf(floor), floor), (py - POST_R - 0.6, floor), (py - POST_R - 0.6, zb), (LP_Y + 7, zb),
            (LP_Y + 7, LATCH_Z + 7), (LP_Y - 7, LATCH_Z + 7)]
    cs = mf.CrossSection([poly])
    if cs.area() < 0: cs = mf.CrossSection([poly[::-1]])
    plate = mf.Manifold.extrude(cs, LV_X1 - LV_X0).transform(
        np.array([[0, 0, 1, LV_X0], [1, 0, 0, 0], [0, 1, 0, 0]], float))   # (y, z, x) -> world
    m = plate + cyl_x(LP_Y, LATCH_Z, LV_X0, LV_X1, 7.0, n=48)            # round hub
    m += cyl_x(LP_Y, LATCH_Z, DX1 + 0.4, LV_X0 + 0.01, 4.0, n=40)        # boss: bears on the door edge
    # stem down to the grip, beside the door edge
    m += box(LV_X0, LV_X1, -1.0, 8.0, GRIP[4], LATCH_Z)
    # grip in front of the door, with a finger lip at the free end
    g0, g1, gy0, gy1, gz0, gz1 = GRIP
    m += box(g0, g1, gy0, gy1, gz0, gz1)
    m += box(LV_X0, LV_X1, gy0, 8.0, gz0, gz1)
    m += box(g0, g0 + 8, gy0 - 5, gy1, gz0, gz1) - box(g0 - 1, g0 + 9, gy0 - 6, gy0 - 2, gz0 + 4, gz1 - 4)
    # pivot screw: clearance + counterbore on the outside face
    m -= cyl_x(LP_Y, LATCH_Z, DX1, LV_X1 + 1, M3_CLR/2)
    m -= cyl_x(LP_Y, LATCH_Z, LV_X1 - 3.0, LV_X1 + 1, 3.1)
    # click magnet in the grip's back face
    m -= cyl_y(CLICK_X, CLICK_Z, gy1 - MAGNET_H, gy1 + 1, MAGNET_D/2, n=48)
    return m

def latch_post_sleeve():
    """6 mm OD sleeve for the M4 post bolt; stands SLEEVE_L out of the stile side face."""
    py, pz = LATCH_POST
    return cyl_x(py, pz, W, W + SLEEVE_L, POST_R, n=48) - cyl_x(py, pz, W - 1, W + SLEEVE_L + 1, 2.2, n=32)

def latch_post_world():
    """The bolt head too, for clearance checks."""
    py, pz = LATCH_POST
    return latch_post_sleeve() + cyl_x(py, pz, W + SLEEVE_L, W + SLEEVE_L + 4.0, 3.5, n=32)

def lever_turn(m, deg):
    """Turn a lever-attached solid about the pivot; negative = opening (grip comes forward)."""
    return m.translate((0, -LP_Y, -LATCH_Z)).rotate((deg, 0, 0)).translate((0, LP_Y, LATCH_Z))

# ------------------------------------------------------------------ assembly / print
def door_parts():
    return {'door_stile_left': stile('L'), 'door_stile_right': stile('R'),
            'door_rail_bottom_left': rail('bottom', 'L'), 'door_rail_bottom_right': rail('bottom', 'R'),
            'door_rail_top_left': rail('top', 'L'), 'door_rail_top_right': rail('top', 'R')}

def moving_parts():
    d = door_parts()
    for i, hz in enumerate(HINGE_Z): d[f'hinge_door_leaf_{i}'] = hinge_door_leaf(hz)
    d['latch_lever'] = latch_lever()
    return d

def fixed_hinges():
    d = {f'hinge_frame_leaf_{i}': hinge_frame_leaf(hz) for i, hz in enumerate(HINGE_Z)}
    d['latch_post'] = latch_post_world()
    return d

def swing(m, deg):
    """Open the door by deg (free edge comes toward the user, -y)."""
    ax, ay = HINGE_AXIS
    return m.translate((-ax, -ay, 0)).rotate((0, 0, -deg)).translate((ax, ay, 0))

FACE_DOWN = np.array([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]], float)
def to_print(m, M=None, diag=False):
    if M is not None: m = m.transform(M)
    if diag: m = m.rotate((0, 0, 45))
    b = m.bounding_box()
    return m.translate((-(b[0]+b[3])/2, -(b[1]+b[4])/2, -b[2]))

if __name__ == '__main__':
    for name, m in door_parts().items():
        t = save(to_print(m, FACE_DOWN, diag=name.startswith('door_stile')), name)
        e = t.bounds[1] - t.bounds[0]; assert e[0] <= 345 and e[1] <= 345, (name, e)
    save(to_print(hinge_frame_leaf(HINGE_Z[0])), 'hinge_frame_leaf')
    save(to_print(hinge_door_leaf(HINGE_Z[0])), 'hinge_door_leaf')
    # lever: outside face down (the x+ face), so the plate's layers run along the arm
    save(to_print(latch_lever(), np.array([[0, 1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, 0]], float)), 'latch_lever')
    save(to_print(latch_post_sleeve(), np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]], float)), 'latch_post_sleeve')
    save(backup_tag(), 'backup_tag')
    print(f'pane (cut 2): {PANE[0]:.1f} x {PANE[1]:.1f} mm  ({PANE[0]/25.4:.2f} x {PANE[1]/25.4:.2f} in)')
    print(f'visible glass {XR0-XL1:.1f} x {ZT0-ZB1:.1f}; door {DX1-DX0:.1f} x {DZ1-DZ0:.1f} x {DT} mm, y {DY0}..{DY1}')
