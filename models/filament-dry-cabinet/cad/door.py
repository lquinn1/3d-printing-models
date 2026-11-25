# SPDX-License-Identifier: MIT
"""Door for the dry cabinet: 4 printed members (2 stiles, 2 rails split in halves),
twin polycarbonate panes in grooves, M3-pinned hinges, catch magnets and a pull handle.

World frame as in tiles.py / front.py. Closed, the door sits in front of the frame ring:
    x DX0 .. DX1, z DZ0 .. DZ1, y DY0 .. DY1  (DY1 = 12.5: EPDM on the ring, 3 mm squeezed to 1.5)
Member cross-section (door depth t = y - DY0, 0 = front):
    front lip 1.6 | front pane slot 2.6 | spacer 5.6 | back pane slot 2.6 | back lip 1.6   = 14
"""
import os, math, numpy as np, manifold3d as mf, cadquery as cq
from params import *
from coupons import cyl, save, cq_to_mf, OUT
from tiles import W, X_SLOT, Z0
from front import (box, cyl_x, cyl_y, cyl_z, F_Y0, HDR_Z0, HINGE_Z, MAGNET_Z, REED_Z, MAGNET_D, MAGNET_H,
                   M3_INSERT_D, M3_INSERT_L, M3_CLR, STILE_W, OPEN_X0, OPEN_X1, LIP_Z0)

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
EPDM_T, EPDM_SQ = 3.0, 1.5
DY1 = F_Y0 - EPDM_T + EPDM_SQ         # 12.5: door back face when closed
DT = 14.0
DY0 = DY1 - DT                        # -1.5: door front (1.5 mm proud of the header)
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
KN_R, PIN_D = 4.5, 3.3
MAG_X = W - 8.0
HANDLE_Z = (175.0, 305.0)
HANDLE_X = W - 12.0
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
        for hz in HANDLE_Z:                                  # handle screws from the back, heads flush
            m -= cyl_y(HANDLE_X, hz, DY0 - 1, DY1 + 1, M3_CLR/2)
            m -= cyl_y(HANDLE_X, hz, DY1 - 3.2, DY1 + 1, 3.1)
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

def handle():
    """D-pull on the right stile: two posts and a grip bar, M3 inserts in the posts."""
    xh = HANDLE_X; L_ = HANDLE_Z[1] - HANDLE_Z[0]
    m = None
    for hz in HANDLE_Z:
        p = box(xh - 6, xh + 6, DY0 - 24, DY0, hz - 6, hz + 6)
        m = p if m is None else m + p
    m += box(xh - 6, xh + 6, DY0 - 24, DY0 - 14, HANDLE_Z[0] - 6, HANDLE_Z[1] + 6)
    for hz in HANDLE_Z:
        m -= cyl_y(xh, hz, DY0 - M3_INSERT_L, DY0 + 1, M3_INSERT_D/2)
    return m

# ------------------------------------------------------------------ assembly / print
def door_parts():
    return {'door_stile_left': stile('L'), 'door_stile_right': stile('R'),
            'door_rail_bottom_left': rail('bottom', 'L'), 'door_rail_bottom_right': rail('bottom', 'R'),
            'door_rail_top_left': rail('top', 'L'), 'door_rail_top_right': rail('top', 'R')}

def moving_parts():
    d = door_parts()
    for i, hz in enumerate(HINGE_Z): d[f'hinge_door_leaf_{i}'] = hinge_door_leaf(hz)
    d['door_handle'] = handle()
    return d

def fixed_hinges():
    return {f'hinge_frame_leaf_{i}': hinge_frame_leaf(hz) for i, hz in enumerate(HINGE_Z)}

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
    save(to_print(handle(), np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], float).dot(np.eye(4))[:3] if False else
                  np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]], float)), 'door_handle')
    save(backup_tag(), 'backup_tag')
    print(f'pane (cut 2): {PANE[0]:.1f} x {PANE[1]:.1f} mm  ({PANE[0]/25.4:.2f} x {PANE[1]/25.4:.2f} in)')
    print(f'visible glass {XR0-XL1:.1f} x {ZT0-ZB1:.1f}; door {DX1-DX0:.1f} x {DZ1-DZ0:.1f} x {DT} mm, y {DY0}..{DY1}')
