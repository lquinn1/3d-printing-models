# SPDX-License-Identifier: MIT
"""Door for the dry cabinet: 4 printed members (2 stiles, 2 rails split in halves),
twin polycarbonate panes in grooves, M3-pinned hinges, corner catch magnets and a flush
lift-bar handle that is also the latch: a hidden hook behind the door draws it onto the seal
(the draw-in idea comes from the Clicky-Clack fridge door).

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
                   LATCH_Z, KEEPER_PIN, KEEPER_PIN_R, KEEPER_X, keeper_pin,
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
        m -= bar_recess()
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

# ------------------------------------------------------------------ latch (flush lift-bar)
# A bar sits flush in a recess in the right stile and hangs from an M3 pivot near its top
# (axis along x). Behind the pivot a hook arm runs back through a slot in the door's back
# face, under a steel pin in the frame stile, and its tip rises behind the pin.
#  - Open: pull the bar's bottom end forward. The tip drops below the pin and the same pull
#    swings the door open.
#  - Close: push the door. The pin rides the tip's back chamfer and pushes it down; the bar
#    swings out a little, then drops back flush (gravity + a magnet pair) with the tip
#    behind the pin. The tip's front face ramps, so pressing the bar flush draws the door
#    up to about 1.7 mm further onto the seal; at the bottom the face is vertical and holds.
PIV = (Y_MID, LATCH_Z)                 # pivot axis (y, z): between the panes' depth, y 6
HUB_R = 4.5
BAR_X = (W - 17.8, W - 5.0)            # bar width 12.8
REC_X = (W - 18.4, W - 4.4)            # recess: 0.6 mm reveal each side
BAR_Y1 = 5.0                           # bar back face (front face flush at DY0)
REC_Y1 = 5.5
BAR_Z0 = 120.0                         # bottom end (finger scoop below it)
REC_Z = (116.0, 255.2)
ARM_X = (W - 10.0, W - 5.0)            # hook arm, flush with the bar's right face (print side)
ARM_Z0 = 244.0                         # arm underside
HOLD_H, RAMP_H, RAMP_SLOPE = 0.5, 2.5, 0.7   # tip catch face: vertical, then a draw-in ramp
BAR_MAG_Z = 135.0
BAR_MAG_X = (BAR_X[0] + BAR_X[1]) / 2

def _area(poly):
    return sum(a[0]*b[1] - b[0]*a[1] for a, b in zip(poly, poly[1:] + poly[:1])) / 2

def _yz_prism(poly, x0, x1):
    cs = mf.CrossSection([poly if _area(poly) > 0 else poly[::-1]])   # CCW, or the positive fill drops it
    return mf.Manifold.extrude(cs, x1 - x0).transform(
        np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], float))   # (y, z, x) -> world

def hook_profile():
    """y-z outline of the hook arm and tip, closed pose."""
    ky, kz = KEEPER_PIN
    yf = ky + KEEPER_PIN_R                          # catch face (touches the pin's back)
    za = kz - KEEPER_PIN_R - 0.4                    # arm top, under the pin
    zh = kz + HOLD_H
    zt = zh + RAMP_H                                # tip top
    yt = yf + RAMP_SLOPE * RAMP_H
    yb = yt + 0.5 + (zt - za)                       # 45 deg chamfer on the back: the closing ramp
    return [(PIV[0], ARM_Z0), (yb, ARM_Z0), (yb, za), (yt + 0.5, zt), (yt, zt), (yf, zh), (yf, za), (PIV[0], za)]

def latch_bar():
    """One y-z outline (bar + hub + rounded cap + hook) extruded across the bar's width, then
    the hook trimmed to its own width, so no two features meet on a shared outer face."""
    py, pz = PIV
    x0, x1 = BAR_X
    circ = lambda cy, cz, r, n=48: mf.CrossSection([[(cy + r*math.cos(t), cz + r*math.sin(t))
                                                      for t in np.linspace(0, 2*math.pi, n, endpoint=False)]])
    body = mf.CrossSection([[(DY0, BAR_Z0), (BAR_Y1, BAR_Z0), (BAR_Y1, pz), (DY0, pz)]])
    hub, cap = circ(py, pz, HUB_R), circ(py - 4.0, pz, 3.0)
    hook = mf.CrossSection([hook_profile()[::-1]] if _area(hook_profile()) < 0 else [hook_profile()])
    base = body + hub + cap
    xf = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], float)
    m = mf.Manifold.extrude(base + hook, x1 - x0).transform(xf).translate((x0, 0, 0))
    m -= mf.Manifold.extrude(hook - base, ARM_X[0] - x0 + 1).transform(xf).translate((x0 - 1, 0, 0))
    c = 0.8                                          # front long-edge chamfers
    for xa, sx in ((x0, 1), (x1, -1)):
        tri = [(xa - sx, DY0 + c + 1), (xa - sx, DY0 - 1), (xa + sx*(c + 1), DY0 - 1)]
        tri = tri if _area(tri) > 0 else tri[::-1]
        m -= mf.Manifold.extrude(mf.CrossSection([tri]), pz + 10 - BAR_Z0).translate((0, 0, BAR_Z0 - 5))
    m -= cyl_x(py, pz, x0 - 1, x1 + 1, 1.7)                          # turns on the M3 pivot screw
    m -= cyl_y(BAR_MAG_X, BAR_MAG_Z, BAR_Y1 - MAGNET_H, BAR_Y1 + 1, MAGNET_D/2, n=48)   # click magnet
    # finger relief: chamfer the bottom end's front so a fingertip lands behind it
    m -= _yz_prism([(DY0 - 1, BAR_Z0 - 1), (DY0 + 2.5, BAR_Z0 - 1), (DY0 - 1, BAR_Z0 + 3.5)], x0 - 1, x1 + 1)
    return m

def bar_recess():
    """Everything the lift-bar takes out of the right stile."""
    py, pz = PIV
    x0, x1 = REC_X
    m = box(x0, x1, DY0 - 1, REC_Y1, REC_Z[0], REC_Z[1])
    m += _yz_prism([(DY0 - 1, REC_Z[0] + 0.01), (REC_Y1, REC_Z[0] + 0.01), (DY0 - 1, REC_Z[0] - 16)], x0, x1)  # finger scoop
    m += box(x0, x1, DY0 - 1, 11.0, pz - HUB_R - 0.8, REC_Z[1])               # hub pocket
    m += box(ARM_X[0] - 0.5, ARM_X[1] + 0.5, 5.0, DY1 + 1, 236.0, REC_Z[1])   # arm slot through the back
    m += cyl_y(BAR_MAG_X, BAR_MAG_Z, REC_Y1 - 0.1, REC_Y1 + MAGNET_H, MAGNET_D/2, n=48)  # click magnet
    # pivot: M3 x 25 flat head from the door edge, threads into the far wall
    m += cyl_x(py, pz, x1 - 0.5, DX1 + 1, 1.7)
    m += mf.Manifold.cylinder(1.75, 1.6, 3.35, 40).transform(
        np.array([[0, 0, 1, DX1 - 1.75], [1, 0, 0, py], [0, 1, 0, pz]], float))
    m += cyl_x(py, pz, DX1 - 25.6, x0 + 0.5, 1.25)
    return m

def bar_turn(m, deg):
    """Turn a bar-attached solid about the pivot; negative = opening (bottom end comes forward)."""
    py, pz = PIV
    return m.translate((0, -py, -pz)).rotate((deg, 0, 0)).translate((0, py, pz))

# ------------------------------------------------------------------ assembly / print
def door_parts():
    return {'door_stile_left': stile('L'), 'door_stile_right': stile('R'),
            'door_rail_bottom_left': rail('bottom', 'L'), 'door_rail_bottom_right': rail('bottom', 'R'),
            'door_rail_top_left': rail('top', 'L'), 'door_rail_top_right': rail('top', 'R')}

def moving_parts():
    d = door_parts()
    for i, hz in enumerate(HINGE_Z): d[f'hinge_door_leaf_{i}'] = hinge_door_leaf(hz)
    d['latch_bar'] = latch_bar()
    return d

def fixed_hinges():
    d = {f'hinge_frame_leaf_{i}': hinge_frame_leaf(hz) for i, hz in enumerate(HINGE_Z)}
    d['keeper_pin'] = keeper_pin()
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
    # lift-bar: right face down (x+), so the arm lies on the bed and layers run along the hook
    save(to_print(latch_bar(), np.array([[0, 1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, 0]], float)), 'latch_bar')
    save(backup_tag(), 'backup_tag')
    print(f'pane (cut 2): {PANE[0]:.1f} x {PANE[1]:.1f} mm  ({PANE[0]/25.4:.2f} x {PANE[1]/25.4:.2f} in)')
    print(f'visible glass {XR0-XL1:.1f} x {ZT0-ZB1:.1f}; door {DX1-DX0:.1f} x {DZ1-DZ0:.1f} x {DT} mm, y {DY0}..{DY1}')
