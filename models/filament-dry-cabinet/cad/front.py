# SPDX-License-Identifier: MIT
"""Front frame and header for the dry cabinet.

World frame as in tiles.py (x across, y front -> back, z up). The tiles' front edges are at
y = DOOR (28). In front of them:

  y 14 .. 28  FRAME RING  (bolts to the tiles' FRONT inserts; the door's EPDM seals on its
                           front face at y = 14)
                - left / right stiles   x 0..25.7 / W-25.7..W,  z Z0 .. LIP_Z0
                - bottom rail (2 halves) x 25.7 .. W-25.7,       z Z0 .. 35.7
                - top lip  = bottom of the header chassis,       z LIP_Z0 .. HDR_Z0
  y  0 .. 14  DOOR (next phase) - overlays the ring, top edge just under the header
  y  0 .. 28  HEADER above the door, HDR_Z0 .. Z1 (68 mm), in 3 pieces:
                - chassis (back plate, top/bottom walls, lip) bolted to the cabinet
                - fascia (front plate) carrying the NFC pad / 3.5 in TFT / encoder,
                  held by a tongue at the top and two screws from underneath
  inside      LED rails (2) on the back of the lip, strip face 45 deg down and back.
"""
import os, math, numpy as np, manifold3d as mf
from params import *
from coupons import cyl, save, OUT
from tiles import (W, Y0, Z0, Z1, T, FLOOR, CEIL, FRONTS, A, box as tbox)

# ------------------------------------------------------------------ front parameters
F_Y0, F_Y1 = 14.0, Y0                 # frame ring depth (y)
STILE_W = T + 10.0                    # 25.7: 10 mm lip past the side wall
RAIL_H = T + 10.0                     # 25.7: bottom rail, 10 mm lip above the floor
HDR_Z0 = Z1 - HEADER_H                # 425.5: underside of the header
LIP_H = 12.0                          # door seals on the lip's front face
LIP_Z0 = HDR_Z0 - LIP_H               # 413.5: top of the door opening
OPEN_X0, OPEN_X1 = STILE_W, W - STILE_W
OPEN_Z0, OPEN_Z1 = Z0 + RAIL_H, LIP_Z0
FAS = 2.4                             # fascia thickness
WALL_H = 2.4                          # header walls
BAY_Y1 = 24.0                         # back plate y 24..28
HDR_SPLIT = (200.0, W - 200.0)        # chassis / fascia seams
ZC = (HDR_Z0 + Z1) / 2                # header centre line
EPDM_W = 9.0
M3_INSERT_D, M3_INSERT_L = 4.0, 6.0   # M3 x 5.7 heat-set
M3_CLR = 3.4
TFT_STACK = 4.5                       # lens front -> PCB front (measure the module)  FIT
TFT_GAP = 0.3                         # air gap between bezel and touch glass
NFC_BOARD = (65.0, 40.0)              # PN5180 module outline (measure yours)        FIT
NFC_X = HDR_SPLIT[0] / 2              # 100: centre of the left fascia
ENC_X = (HDR_SPLIT[1] + W) / 2        # 431.4: centre of the right fascia
ENC_HOLE = 7.2                        # EC11 M7 bushing
HINGE_Z = (85.0, 362.0)               # hinge centres (left stile side face)
MAGNET_Z = (85.0, 362.0)              # door catch magnets (right stile front face); the latch is at 250
LATCH_Z = 250.0                       # lift-bar pivot height (door.py)
# keeper for the lift-bar hook: a pocket in the right stile's front face, outside the seal line,
# with a steel pin across it (M3 x 16 flat head from the stile's outer side face)
KEEPER_PIN = (17.0, 251.0)            # (y, z) of the pin axis (along x)
KEEPER_PIN_R = 1.5                    # M3 shank
KEEPER_X = (W - 11.0, W - 4.0)        # pocket x (the hook arm is W-10 .. W-5)
KEEPER_Y1 = 27.0                      # pocket depth (frame back face is at 28)
KEEPER_Z = (232.0, 258.0)
MAGNET_D, MAGNET_H = 10.3, 3.2        # 10 x 3 mm neodymium
REED_Z = 200.0
LED_SCREW_X = (60.0, 180.0, W - 180.0, W - 60.0)
BRK_SLOT = (340.0, 380.0)            # x of the cable slot under the front breakout PCB (v0.18)
BRK_BOARD = (335.0, 415.0, 439.0, 483.0)   # front breakout PCB outline on the back plate (x0, x1, z0, z1)
LED_Z = (LIP_Z0 + HDR_Z0) / 2

def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube((x1-x0, y1-y0, z1-z0)).translate((x0, y0, z0))

def cyl_y(x, z, y0, y1, r, n=40):
    return mf.Manifold.cylinder(y1-y0, r, r, n).transform(
        np.array([[1, 0, 0, x], [0, 0, 1, y0], [0, -1, 0, z]], float))   # local z -> +y

def cyl_x(y, z, x0, x1, r, n=40):
    return mf.Manifold.cylinder(x1-x0, r, r, n).transform(
        np.array([[0, 0, 1, x0], [1, 0, 0, y], [0, 1, 0, z]], float))    # local z -> +x

def cyl_z(x, y, z0, z1, r, n=40):
    return mf.Manifold.cylinder(z1-z0, r, r, n).translate((x, y, z0))

def front_bolts(m, x0, x1, z0, z1, y_head):
    """Clearance holes for every tile FRONT insert behind this part, head pocket from y_head."""
    for face, p in FRONTS:
        x, _, z = p
        if x0 < x < x1 and z0 < z < z1:
            m -= cyl_y(x, z, y_head - 1, F_Y1 + 1, BOLT_CLEAR_D/2)
            m -= cyl_y(x, z, y_head - 1, y_head + BOLT_HEAD_H, BOLT_HEAD_D/2)
    return m

# ------------------------------------------------------------------ frame
def keeper_cut():
    py, pz = KEEPER_PIN
    m = box(KEEPER_X[0], KEEPER_X[1], F_Y0 - 1, KEEPER_Y1, KEEPER_Z[0], KEEPER_Z[1])
    m += cyl_x(py, pz, KEEPER_X[1] - 0.5, W + 1, 1.7)                    # clearance
    m += mf.Manifold.cylinder(1.75, 1.6, 3.35, 40).transform(              # 90 deg countersink
        np.array([[0, 0, 1, W - 1.75], [1, 0, 0, py], [0, 1, 0, pz]], float))
    m += cyl_x(py, pz, W - 16.6, KEEPER_X[0] + 0.5, 1.25)                # pilot (self-tapping)
    return m

def keeper_pin():
    """The M3 x 16 flat-head screw shank across the pocket (for checks and renders)."""
    py, pz = KEEPER_PIN
    return cyl_x(py, pz, W - 15.4, W, KEEPER_PIN_R, n=32)

def stile(side):
    x0, x1 = (0.0, STILE_W) if side == 'L' else (W - STILE_W, W)
    m = box(x0, x1, F_Y0, F_Y1, Z0, LIP_Z0)
    m = front_bolts(m, x0, x1, Z0, LIP_Z0, F_Y0)
    if side == 'L':
        for hz in HINGE_Z:                                 # M3 inserts for the hinge leaves
            for dz in (-12.0, 12.0):
                m -= cyl_x((F_Y0+F_Y1)/2, hz+dz, -1, M3_INSERT_L, M3_INSERT_D/2)
    else:
        xm = W - 8.0
        for mz in MAGNET_Z:                                # catch magnets, pressed in from the front
            m -= cyl_y(xm, mz, F_Y0 - 1, F_Y0 + MAGNET_H, MAGNET_D/2, n=48)
        # keeper pocket for the lift-bar hook + its pin: countersink and clearance in the outer
        # wall, pilot for the screw's thread in the wall on the far side of the pocket
        m -= keeper_cut()
        # reed switch pocket (2 x 14 mm glass reed) + wire channel up to the header bay
        m -= box(xm - 1.6, xm + 1.6, F_Y0 - 1, F_Y0 + 3.2, REED_Z - 9, REED_Z + 9)
        xc = OPEN_X1 + 6.5
        m -= box(xc - 2, xc + 2, 18, 22, REED_Z - 2, LIP_Z0 + 1)
        m -= box(xc - 2, xm + 1.6, 15.5, 19.5, REED_Z - 2, REED_Z + 2)
    return m

def bottom_rail(half):
    xm = W/2
    x0, x1 = (OPEN_X0, xm) if half == 'L' else (xm, OPEN_X1)
    m = box(x0, x1, F_Y0, F_Y1, Z0, Z0 + RAIL_H)
    return front_bolts(m, x0, x1, Z0, Z0 + RAIL_H, F_Y0)

# ------------------------------------------------------------------ header
def tft_geometry():
    """Window centre on the cabinet centre line; board shifted toward the pin end (+x)."""
    wx, wz = W/2, ZC
    bx = wx - TFT_VA_OFFSET            # TFT_VA_OFFSET = -2.33 -> board centre at +2.33
    holes = [(bx + sx*TFT_HOLES[1]/2, wz + sz*TFT_HOLES[0]/2) for sx in (-1, 1) for sz in (-1, 1)]
    win = (TFT_VA[1] + 2*BEZEL_WIN_CLR, TFT_VA[0] + 2*BEZEL_WIN_CLR)
    return (wx, wz), (bx, wz), holes, win

def chassis(i):
    x0 = (0.0, HDR_SPLIT[0], HDR_SPLIT[1])[i]; x1 = (HDR_SPLIT[0], HDR_SPLIT[1], W)[i]
    m = box(x0, x1, BAY_Y1, F_Y1, LIP_Z0, Z1)                         # back plate
    m += box(x0, x1, F_Y0, BAY_Y1, LIP_Z0, HDR_Z0)                    # lip (door seals on its face)
    m += box(x0, x1, FAS, BAY_Y1, HDR_Z0, HDR_Z0 + WALL_H)            # bottom wall
    m += box(x0, x1, FAS, BAY_Y1, Z1 - WALL_H, Z1)                    # top wall
    if i == 0: m += box(0, WALL_H, FAS, BAY_Y1, HDR_Z0, Z1)
    if i == 2: m += box(W - WALL_H, W, FAS, BAY_Y1, HDR_Z0, Z1)
    # tongue slots for the fascia (short ledges at each end of the piece)
    for xa in (x0 + 3, x1 - 12):
        led = box(xa, xa + 9, FAS, FAS + 6, Z1 - WALL_H - 4.5, Z1 - WALL_H)
        led -= box(xa - 1, xa + 10, FAS - 1, FAS + 3.6, Z1 - WALL_H - 3.3, Z1 - WALL_H - 1.3)
        m += led
    # fascia screws from underneath (M3 through the bottom wall)
    for xs in fascia_screw_x(i):
        m -= cyl_z(xs, FAS + 4.5, HDR_Z0 - 1, HDR_Z0 + WALL_H + 1, M3_CLR/2)
    m = front_bolts(m, x0, x1, LIP_Z0, Z1, BAY_Y1 - BOLT_HEAD_H)    # heads sit in the bay, on the back plate
    # LED rail inserts (M3, from the chamber side into the lip)
    for xs in LED_SCREW_X:
        if x0 + 6 < xs < x1 - 6:
            m -= cyl_y(xs, LED_Z, F_Y1 - M3_INSERT_L, F_Y1 + 1, M3_INSERT_D/2)
    if i == 2:
        # v0.18: 40 x 7 slot under the front breakout PCB (x 335..415): the flat 26-way ribbon and
        # the LED 5 V pair come up from the chamber here; seal it with RTV after wiring
        m -= box(BRK_SLOT[0], BRK_SLOT[1], BAY_Y1 - 1, F_Y1 + 1, HDR_Z0 + 4, HDR_Z0 + 11)
        xc = OPEN_X1 + 6.5                                             # reed wires up from the stile
        m -= box(xc - 2, xc + 2, 18, 22, LIP_Z0 - 1, HDR_Z0 + WALL_H + 1)
        m -= box(W - WALL_H - 1, W + 1, 8, 18, ZC - 7, ZC + 7)         # cable exit to the rear pod
    return m

def fascia_screw_x(i):
    x0 = (0.0, HDR_SPLIT[0], HDR_SPLIT[1])[i]; x1 = (HDR_SPLIT[0], HDR_SPLIT[1], W)[i]
    return (x0 + 7.5, x1 - 7.5) if i == 1 else (x0 + 30, x1 - 30)    # centre: clear of the TFT board

def fascia(i):
    x0 = (0.0, HDR_SPLIT[0], HDR_SPLIT[1])[i] + 0.15; x1 = (HDR_SPLIT[0], HDR_SPLIT[1], W)[i] - 0.15
    m = box(x0, x1, 0, FAS, HDR_Z0, Z1)
    # tongues into the chassis ledges
    for xa in (x0 + 3 - 0.15, x1 - 12 + 0.15):
        m += box(xa + 0.3, xa + 8.7, FAS - 0.01, FAS + 3.3, Z1 - WALL_H - 3.1, Z1 - WALL_H - 1.5)
    # screw tabs at the bottom (M3 heat-set from below)
    for xs in fascia_screw_x(i):
        m += box(xs - 5, xs + 5, FAS - 0.01, FAS + 9, HDR_Z0 + WALL_H + 0.2, HDR_Z0 + WALL_H + 10)
        m -= cyl_z(xs, FAS + 4.5, HDR_Z0 + WALL_H, HDR_Z0 + WALL_H + 0.2 + M3_INSERT_L, M3_INSERT_D/2)
    # front edge chamfer look: 0.6 mm reveal at the seams is left by the 0.15 gaps
    if i == 0:                                                         # NFC tap pad
        cx, cz = NFC_X, ZC
        # orange tap-zone overlay (nfc_tap_overlay) locates on two blind peg holes
        for px, pz in NFC_PEGS:
            m -= cyl_y(px, pz, -1, OV_PEG_L + 0.3, OV_PEG_D/2 + 0.15, n=24)
        # module locating posts + retainer bosses on the back
        bw, bh = NFC_BOARD
        for sx in (-1, 1):
            for sz in (-1, 1):
                px, pz = cx + sx*(bw/2 + 1.5), cz + sz*(bh/2 - 6)
                m += box(px - 1.5, px + 1.5, FAS - 0.01, FAS + 4, pz - 3, pz + 3)
        for sx in (-1, 1):
            bx_ = cx + sx*(bw/2 + 8)
            m += cyl_y(bx_, cz, FAS - 0.01, FAS + 8, 3.2)
            m -= cyl_y(bx_, cz, FAS + 1, FAS + 9, 1.1)                 # M2.5 self-tap pilot
    if i == 1:                                                         # TFT bezel + standoffs
        (wx, wz), (bx, bz), holes, (ww, wh) = tft_geometry()
        m -= box(wx - ww/2, wx + ww/2, -1, FAS + 1, wz - wh/2, wz + wh/2)
        # the 45 deg finger chamfer is on the orange bezel (tft_bezel); it locates on two blind peg holes
        for px, pz in BEZEL_PEGS:
            m -= cyl_y(px, pz, -1, OV_PEG_L + 0.3, OV_PEG_D/2 + 0.15, n=24)
        for hx, hz in holes:
            m += cyl_y(hx, hz, FAS - 0.01, FAS + TFT_GAP + TFT_STACK, 3.2)
            m -= cyl_y(hx, hz, FAS + 0.8, FAS + TFT_GAP + TFT_STACK + 1, 1.1)   # M2.5 self-tap pilot
    if i == 2:                                                         # encoder
        m -= cyl_y(ENC_X, ZC, -1, FAS + 1, ENC_HOLE/2, n=48)
    return m

# ---------------------------------------------------------------- orange overlays (v0.20)
# Glued on the fascia front (ABS cement or thin CA), located by two pegs each. Printed face down in orange.
OV_T = 1.2                             # overlay thickness, proud of the fascia
OV_PEG_D, OV_PEG_L = 2.5, 1.8          # pegs: blind holes 2.1 deep, so nothing pokes out of the 2.4 mm fascia
BEZEL_BORDER = 5.5                     # orange border round the window
BEZEL_R = 3.0
NFC_TAP_D = 46.0
_wx, _wz = W/2, ZC
BEZEL_PEGS = [(_wx - 37.52 - BEZEL_BORDER/2, _wz), (_wx + 37.52 + BEZEL_BORDER/2, _wz)]
NFC_PEGS = [(NFC_X - 17.0, ZC), (NFC_X + 12.0, ZC + 12.0)]       # not symmetric: it only goes on one way up

def rrect_y(cx, cz, w, h, r, y0, y1):
    """Rounded rectangle in x-z, extruded y0..y1."""
    pts = [mf.CrossSection.circle(r, 32).translate((sx*(w/2 - r), sz*(h/2 - r))) for sx in (-1, 1) for sz in (-1, 1)]
    cs = mf.CrossSection.batch_hull(pts)
    return mf.Manifold.extrude(cs, y1 - y0).transform(np.array([[1, 0, 0, cx], [0, 0, 1, y0], [0, -1, 0, cz]], float))

def tft_bezel():
    """Orange frame round the TFT window, on the fascia front (y -OV_T..0). Inner edge: 45 deg finger chamfer."""
    (wx, wz), _, _, (ww, wh) = tft_geometry()
    m = rrect_y(wx, wz, ww + 2*BEZEL_BORDER, wh + 2*BEZEL_BORDER, BEZEL_R, -OV_T, 0)
    m -= mf.Manifold.hull_points([[wx + sx*(ww/2 + OV_T), -OV_T - 0.01, wz + sz*(wh/2 + OV_T)] for sx in (-1, 1) for sz in (-1, 1)] +
                                 [[wx + sx*ww/2, 0.01, wz + sz*wh/2] for sx in (-1, 1) for sz in (-1, 1)])
    # soften the outer front edge: 0.5 mm chamfer
    m -= chamfer_ring(wx, wz, ww + 2*BEZEL_BORDER, wh + 2*BEZEL_BORDER, BEZEL_R, 0.5)
    for px, pz in BEZEL_PEGS:
        m += cyl_y(px, pz, -0.01, OV_PEG_L, OV_PEG_D/2, n=24)
    return m

def chamfer_ring(cx, cz, w, h, r, c):
    """Material to remove for a c x 45 deg chamfer on the front (y = -OV_T) outer edge of a rounded rect."""
    big = rrect_y(cx, cz, w + 2, h + 2, r + 1, -OV_T - 1, -OV_T + c)
    keep = mf.Manifold.batch_hull([rrect_y(cx, cz, w - 2*c, h - 2*c, max(r - c, 0.2), -OV_T - 0.001, -OV_T),
                                   rrect_y(cx, cz, w, h, r, -OV_T + c, -OV_T + c + 0.001)])
    return big - keep - rrect_y(cx, cz, w, h, r, -OV_T + c, 1)

def nfc_tap_overlay():
    """Orange tap zone over the PN5180 antenna: a disc with the tap mark debossed 0.5 mm."""
    cx, cz = NFC_X, ZC
    m = cyl_y(cx, cz, -OV_T, 0, NFC_TAP_D/2, n=128)
    big = cyl_y(cx, cz, -OV_T - 1, -OV_T + 0.5, NFC_TAP_D/2 + 1, n=128)
    keep = mf.Manifold.batch_hull([cyl_y(cx, cz, -OV_T - 0.001, -OV_T, NFC_TAP_D/2 - 0.5, n=128),
                                   cyl_y(cx, cz, -OV_T + 0.5, -OV_T + 0.501, NFC_TAP_D/2, n=128)])
    m -= big - keep - cyl_y(cx, cz, -OV_T + 0.5, 1, NFC_TAP_D/2, n=128)
    d0, d1 = -OV_T - 1, -OV_T + 0.5                                   # deboss depth 0.5
    for r in (7.0, 11.5, 16.0):
        arc = cyl_y(cx - 6, cz, d0, d1, r + 0.8, n=96) - cyl_y(cx - 6, cz, d0, d1, r - 0.8, n=96)
        arc ^= box(cx - 6 + r*0.25, cx + 30, d0, d1, cz - r*0.8, cz + r*0.8)
        m -= arc
    m -= cyl_y(cx - 6, cz, d0, d1, 2.6, n=32)
    for px, pz in NFC_PEGS:
        m += cyl_y(px, pz, -0.01, OV_PEG_L, OV_PEG_D/2, n=24)
    return m

def nfc_retainer():
    """Strap across the back of the PN5180 module, M2.5 into the fascia bosses."""
    bw, bh = NFC_BOARD
    L_ = bw + 16 + 8
    m = box(-L_/2, L_/2, 0, 2.4, -6, 6)
    for sx in (-1, 1):
        m -= cyl_y(sx*(bw/2 + 8), 0, -1, 3.4, 1.4)
        m += box(sx*(bw/2 + 8) - 4, sx*(bw/2 + 8) + 4, 0, 2.4, -6, 6)
        m -= cyl_y(sx*(bw/2 + 8), 0, -1, 3.4, 1.4)
    return m

def led_rail(half):
    """Prism under the lip, inside the chamber. Strip face 45 deg down-and-back, 12 mm strip."""
    x0, x1 = (OPEN_X0, W/2) if half == 'L' else (W/2, OPEN_X1)
    # profile in (t = y - F_Y1, s = z - LIP_Z0): mounting face t = 0, top s = LIP_H, slope face
    # triangle with its two sharp corners clipped 1 mm (no knife edges to curl on the bed)
    k = (LIP_H + 2) / LIP_H
    pts = [(0.0, 1.0), (k, 1.0), (LIP_H + 1, (LIP_H + 1) / k), (LIP_H + 1, LIP_H), (0.0, LIP_H)]
    prof = mf.CrossSection([pts])
    if prof.area() < 0: prof = mf.CrossSection([pts[::-1]])
    pr = mf.Manifold.extrude(prof, x1 - x0)                            # X=t, Y=s, Z=x
    m = pr.transform(np.array([[0, 0, 1, x0], [1, 0, 0, F_Y1], [0, 1, 0, LIP_Z0]], float))
    for xs in LED_SCREW_X:
        if x0 + 6 < xs < x1 - 6:
            m -= cyl_y(xs, LED_Z, F_Y1 - 1, F_Y1 + 20, M3_CLR/2)
            m -= cyl_y(xs, LED_Z, F_Y1 + 3, F_Y1 + 20, 3.2)
    return m

# ------------------------------------------------------------------ print orientation
FACE_DOWN = np.array([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]], float)   # y face -> bed, det +1
BACK_DOWN = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0]], float)   # y=28 face -> bed

def to_print(m, M, diag=False):
    m = m.transform(M)
    if diag: m = m.rotate((0, 0, 45))
    b = m.bounding_box()
    return m.translate((-(b[0]+b[3])/2, -(b[1]+b[4])/2, -b[2]))

def parts_world():
    return {
        'frame_stile_left': stile('L'), 'frame_stile_right': stile('R'),
        'frame_rail_bottom_left': bottom_rail('L'), 'frame_rail_bottom_right': bottom_rail('R'),
        'header_chassis_left': chassis(0), 'header_chassis_center': chassis(1), 'header_chassis_right': chassis(2),
        'header_fascia_nfc': fascia(0), 'header_fascia_tft': fascia(1), 'header_fascia_encoder': fascia(2),
        'led_rail_left': led_rail('L'), 'led_rail_right': led_rail('R'),
        'tft_bezel': tft_bezel(), 'nfc_tap_overlay': nfc_tap_overlay(),
    }

ORIENT = {'frame_stile': (FACE_DOWN, True), 'frame_rail': (FACE_DOWN, False), 'header_chassis': (BACK_DOWN, False),
          'header_fascia': (FACE_DOWN, False), 'led_rail': (BACK_DOWN, False),
          'tft_bezel': (FACE_DOWN, False), 'nfc_tap_overlay': (FACE_DOWN, False)}

if __name__ == '__main__':
    pw = parts_world()
    for name, m in pw.items():
        M, diag = next(v for k, v in ORIENT.items() if name.startswith(k))
        t = save(to_print(m, M, diag), name)
        bb = t.bounds; ext = bb[1] - bb[0]
        assert ext[0] <= 345 and ext[1] <= 345, (name, ext)
    save(nfc_retainer().transform(BACK_DOWN), 'nfc_retainer')
    print(f'opening {OPEN_X1-OPEN_X0:.1f} x {OPEN_Z1-OPEN_Z0:.1f} mm; lip at z {LIP_Z0:.1f}; '
          f'back-row spool clearance under the lip {LIP_Z0 - (FLOOR + A["top_back"]):.1f} mm')
