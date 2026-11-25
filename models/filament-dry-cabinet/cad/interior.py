# SPDX-License-Identifier: MIT
"""Interior parts for the service void under the back row.

Airflow (return path): chamber air comes down the back wall -> into the two desiccant
cartridges (top and side grids) -> out of their inner grids into the PLENUM -> 80 mm fan in
the plenum's front wall -> PTC heater in the HEATER DUCT -> down into the FLOOR DUCT, which runs
forward under the front rods (between the collars of slot 3) -> out through louvres at the
bottom of the door -> up the door and back over the spools.

Cartridges sit under back slots 1 and 6. To recharge: open the door, lift out the front
spool in that slot, lift the cartridge 47 mm and slide it out over the front rods.
"""
import os, math, numpy as np, manifold3d as mf
from params import *
from coupons import cyl, save
from tiles import (W, T, Y1, FLOOR, A, X_SLOT, ROD_Y, Y_FRONT_ROW, Y_BACK_ROW, make_tiles, cradle_world)
from front import box, cyl_x, cyl_y, cyl_z, M3_INSERT_D, M3_INSERT_L, M3_CLR

BACK_IN = Y1 - T                         # inside face of the back wall (426.7)
# ---------------------------------------------------------------- spools / rods (for checks)
ROD_Z = [FLOOR + A['rod_front']]*2 + [FLOOR + A['rod_back']]*2
SPOOL_R, SPOOL_W, C_ABOVE = 100.0, 75.0, 99.1
COLLAR_X = [T + 10 + L.PITCH*k for k in range(1, 6)]
def rod(k):     return cyl(ROD_OD/2, T + 1, W - T - 1, n=48).transform(np.array([[0, 0, 1, 0], [1, 0, 0, ROD_Y[k]], [0, 1, 0, ROD_Z[k]]], float))
def collars(k): return [cyl(COLLAR_OD/2, x - COLLAR_W/2, x + COLLAR_W/2, n=48).transform(np.array([[0, 0, 1, 0], [1, 0, 0, ROD_Y[k]], [0, 1, 0, ROD_Z[k]]], float)) for x in COLLAR_X]
def spool(row, i, dy=0.0, dz=0.0):
    yc, rz = (Y_FRONT_ROW, ROD_Z[0]) if row == 0 else (Y_BACK_ROW, ROD_Z[2])
    x = X_SLOT[i]
    return cyl(SPOOL_R, x - SPOOL_W/2, x + SPOOL_W/2, n=72).transform(np.array([[0, 0, 1, 0], [1, 0, 0, yc + dy], [0, 1, 0, rz + C_ABOVE + dz]], float))

# ---------------------------------------------------------------- desiccant cartridges
CART_W, CART_L, CART_H = 72.0, 150.0, 72.0
CART_Y0 = 265.0
CART_X0 = [X_SLOT[0] - CART_W/2, X_SLOT[5] - CART_W/2]            # under slots 1 and 6
CW = 2.0                                                          # wall
CART_LIFT = 47.0

def grid_slots(x0, x1, y0, y1, z0, z1, axis, pitch=3.2, w=1.4):
    """Slot pattern through a wall. axis = the wall's normal ('x' or 'z')."""
    cuts = []
    if axis == 'x':
        for z in np.arange(z0, z1 - w, pitch):
            cuts.append(box(x0, x1, y0, y1, z, z + w))
    else:
        for y in np.arange(y0, y1 - w, pitch):
            cuts.append(box(x0, x1, y, y + w, z0, z1))
    return mf.Manifold.batch_boolean(cuts, mf.OpType.Add)

def cartridge(i):
    x0 = CART_X0[i]; x1 = x0 + CART_W; y0 = CART_Y0; y1 = y0 + CART_L; z0 = FLOOR; z1 = z0 + CART_H
    m = box(x0, x1, y0, y1, z0, z1) - box(x0 + CW, x1 - CW, y0 + CW, y1 - CW, z0 + CW, z1 + 1)
    # side grids (both sides: identical cartridges for either end), windows with ribs
    for xs in (x0 - 1, x1 - CW - 1):
        g = grid_slots(xs, xs + CW + 2, y0 + 14, y1 - 14, z0 + 10, z1 - 12, 'x')
        for yr in np.arange(y0 + 14 + 40, y1 - 14, 40.0):          # vertical stiffening ribs
            g -= box(xs - 1, xs + CW + 3, yr - 1.5, yr + 1.5, z0, z1)
        m -= g
    # lid ledge inside the top rim
    m += box(x0 + CW - 0.01, x1 - CW + 0.01, y0 + CW - 0.01, y1 - CW + 0.01, z1 - 5, z1 - 3) - \
         box(x0 + CW + 2, x1 - CW - 2, y0 + CW + 2, y1 - CW - 2, z1 - 6, z1)
    # lift handle at the door end
    h = box(x0 + 16, x1 - 16, y0 - 0.01, y0 + 12, z1 - 0.01, z1 + 12) - box(x0 + 22, x1 - 22, y0 - 1, y0 + 13, z1 + 1, z1 + 8)
    m += h
    return m

def cartridge_lid(i):
    x0 = CART_X0[i] + CW + 0.3; x1 = CART_X0[i] + CART_W - CW - 0.3
    y0 = CART_Y0 + CW + 12.3; y1 = CART_Y0 + CART_L - CW - 0.3          # stops short of the handle
    z1 = FLOOR + CART_H; z0 = z1 - 3.0
    m = box(x0, x1, y0, y1, z0, z1) - grid_slots(x0 + 4, x1 - 4, y0 + 4, y1 - 4, z0 - 1, z1 + 1, 'z')
    for yr in np.arange(y0 + 30, y1 - 10, 30.0):
        m += box(x0, x1, yr - 1.5, yr + 1.5, z0, z1)
    m += box(x0 + 20, x1 - 20, y1 - 12, y1 - 4, z1 - 0.01, z1 + 6)    # finger tab
    return m

# ---------------------------------------------------------------- plenum + fan
PL_X0, PL_X1 = CART_X0[0] + CART_W + 2.3, CART_X0[1] - 2.3            # 2.3 mm foam gasket each side
PL_Y0, PL_Y1 = CART_Y0, BACK_IN - 1.0
PL_Z1 = FLOOR + 100.0
PW_ = 3.0
FAN = 80.0; FAN_HOLES = 71.5; FAN_X = X_SLOT[2]; FAN_Z = FLOOR + 46.0

def plenum():
    """Five-sided box (open bottom, sits on the floor on foam tape). Printed top-down."""
    m = box(PL_X0, PL_X1, PL_Y0, PL_Y1, FLOOR, PL_Z1) - box(PL_X0 + PW_, PL_X1 - PW_, PL_Y0 + PW_, PL_Y1 - PW_, FLOOR - 1, PL_Z1 - PW_)
    # windows facing the cartridges' side grids
    for xs in (PL_X0 - 1, PL_X1 - PW_ - 1):
        m -= box(xs, xs + PW_ + 2, CART_Y0 + 16, CART_Y0 + CART_L - 16, FLOOR + 12, FLOOR + CART_H - 14)
    # fan in the front wall, blowing forward
    m -= cyl_y(FAN_X, FAN_Z, PL_Y0 - 1, PL_Y0 + PW_ + 1, 38.0, n=96)
    for sx in (-1, 1):
        for sz in (-1, 1):
            m -= cyl_y(FAN_X + sx*FAN_HOLES/2, FAN_Z + sz*FAN_HOLES/2, PL_Y0 - 1, PL_Y0 + PW_ + 1, M3_CLR/2)
    # SHT40 (desiccant outlet) port + cable notch to the gland
    m -= cyl_y(PL_X0 + 40, FLOOR + 70, PL_Y0 - 1, PL_Y0 + PW_ + 1, 3.0)
    m -= box(X_SLOT[1] - 8, X_SLOT[1] + 8, PL_Y1 - PW_ - 1, PL_Y1 + 1, PL_Z1 - 10, PL_Z1 + 1)
    return m

# ---------------------------------------------------------------- heater duct
HD_X0, HD_X1 = FAN_X - 45.0, FAN_X + 45.0
HD_Y1 = PL_Y0                                   # butts against the plenum front wall
HEATER = (80.0, 52.0, 30.0)                     # PTC element w x h x depth in flow (measure yours)  FIT
HEATER_BACK_GAP = 2.0                           # heater back face to the duct's open back
HEATER_PAD = 3.2                                # 1/8 in PTFE strip on each ledge: keeps the element off the ABS
DW = 2.5
STEPS = [(222.0, FLOOR + 40.0), (230.0, FLOOR + 76.0), (240.0, FLOOR + 86.0)]   # (front y, top z) - clears the front spools
HD_TOP = STEPS[-1][1]

def heater_duct_outer():
    return mf.Manifold.batch_boolean([box(HD_X0, HD_X1, y, HD_Y1, FLOOR, z) for y, z in STEPS], mf.OpType.Add)

def heater_duct():
    outer = heater_duct_outer()
    inner = mf.Manifold.batch_boolean([box(HD_X0 + DW, HD_X1 - DW, y + DW, HD_Y1 + 1, FLOOR + DW, z - DW) for y, z in STEPS], mf.OpType.Add)
    m = outer - inner
    # the heater slides in from the open back (fan side) before the duct is pushed onto the plenum
    # outlet into the floor duct (bottom of the front wall)
    m -= box(FD_X0 + 2, FD_X1 - 2, STEPS[0][0] - 1, STEPS[0][0] + DW + 1, FLOOR, FLOOR + FD_H - 2)
    # heater ledges (element sits 3 mm off the duct walls, on PTFE pads, never on bare ABS)
    hz0 = FAN_Z - HEATER[1]/2 - HEATER_PAD
    for xs in (HD_X0 + DW - 0.01, HD_X1 - DW - 4):
        m += box(xs, xs + 4.01, HD_Y1 - HEATER_BACK_GAP - HEATER[2], HD_Y1 - HEATER_BACK_GAP, FLOOR + DW - 0.01, hz0)
    # KSD301 thermostat through the front wall (Ø17 body, flange screws 24 mm apart, M3 inserts)
    tz = FLOOR + 22.0
    m -= cyl_y(FAN_X, tz, STEPS[0][0] - 1, STEPS[0][0] + DW + 1, 8.6, n=48)
    m += box(FAN_X - 17, FAN_X + 17, STEPS[0][0] + DW - 0.01, STEPS[0][0] + DW + 6, tz - 5, tz + 5) - \
         cyl_y(FAN_X, tz, STEPS[0][0], STEPS[0][0] + DW + 7, 8.6, n=48)
    for sx in (-1, 1):
        m -= cyl_y(FAN_X + sx*12, tz, STEPS[0][0] - 1, STEPS[0][0] + DW + M3_INSERT_L, M3_INSERT_D/2)
    # NTC probe hole and TCO zip-tie slots (inside the outlet chamber)
    m -= cyl_y(FAN_X + 30, FLOOR + 30, STEPS[0][0] - 1, STEPS[0][0] + DW + 1, 2.2)
    for sx in (-1, 1):
        m -= box(FAN_X - 30 + sx*6 - 1, FAN_X - 30 + sx*6 + 1, STEPS[1][0] - 1, STEPS[1][0] + DW + 1, FLOOR + 50, FLOOR + 54)
    # wire notch at the back for the heater leads
    m -= box(HD_X1 - DW - 1, HD_X1 + 1, HD_Y1 - 12, HD_Y1 + 1, HD_TOP - 14, HD_TOP - DW)
    return m

def heater_duct_lid():
    x0, x1 = HD_X0 + DW + 0.3, HD_X1 - DW - 0.3
    m = box(HD_X0, HD_X1, STEPS[1][0] + DW, HD_Y1, HD_TOP - DW, HD_TOP)
    m += box(x0, x1, STEPS[1][0] + DW + 0.3, HD_Y1 - 0.3, HD_TOP - DW - 2, HD_TOP - DW + 0.01) - \
         box(x0 + 2, x1 - 2, STEPS[1][0] + DW + 2.3, HD_Y1 - 2.3, HD_TOP - DW - 3, HD_TOP)
    return m

# ---------------------------------------------------------------- floor duct
FD_X0, FD_X1 = X_SLOT[2] - 33.0, X_SLOT[2] + 33.0      # between the collars of slot 3
FD_H = 14.0
FD_Y0 = 34.0

def floor_duct():
    y1 = STEPS[0][0] + 0.0
    m = box(FD_X0, FD_X1, FD_Y0, y1, FLOOR, FLOOR + FD_H) - box(FD_X0 + 2, FD_X1 - 2, FD_Y0 + 2, y1 + 1, FLOOR - 1, FLOOR + FD_H - 2)
    # louvres in the top at the door end
    for y in np.arange(FD_Y0 + 6, FD_Y0 + 46, 6.0):
        m -= box(FD_X0 + 6, FD_X1 - 6, y, y + 3, FLOOR + FD_H - 3, FLOOR + FD_H + 1)
    return m

# ---------------------------------------------------------------- sensor housing
def sensor_housing():
    """Vented box for an SHT4x breakout (up to 24 x 16 mm). VHB on the back."""
    m = box(-16, 16, 0, 12, -12, 12) - box(-14, 14, 2, 13, -10, 10)
    for x in np.arange(-11, 12, 4.0):
        m -= box(x, x + 1.6, 6, 13, -13, -9)
        m -= box(x, x + 1.6, 6, 13, 9, 13)
    m -= box(-3, 3, 1, 13, 9, 13)                        # cable exit
    lid = box(-16, 16, 12, 14, -12, 12) - grid_slots(-12, 12, 11, 15, -8, 8, 'x', pitch=3.0, w=1.4).transform(np.eye(4)[:3])
    return m, lid

CHAMBER_SENSOR = (W/2, BACK_IN, FLOOR + A['ih'] - 95.0)   # back wall, high: below the back ports, above the spools

def parts_world():
    p = {'desiccant_cartridge_1': cartridge(0), 'desiccant_cartridge_6': cartridge(1),
         'desiccant_lid_1': cartridge_lid(0), 'desiccant_lid_6': cartridge_lid(1),
         'plenum': plenum(), 'heater_duct': heater_duct(),
         'floor_duct': floor_duct()}
    sh, sl = sensor_housing()
    M = np.array([[1, 0, 0, CHAMBER_SENSOR[0]], [0, -1, 0, CHAMBER_SENSOR[1]], [0, 0, 1, CHAMBER_SENSOR[2]]], float)
    p['sensor_housing_chamber'] = (sh + sl).transform(np.array([[1, 0, 0, CHAMBER_SENSOR[0]], [0, 0, 1, CHAMBER_SENSOR[1]], [0, -1, 0, CHAMBER_SENSOR[2]]], float).dot(np.eye(4))[:3]) \
        if False else (sh + sl).rotate((0, 0, 180)).translate(CHAMBER_SENSOR)
    return p

def print_pose(name, m):
    if name == 'plenum':            m = m.mirror((0, 0, 1))          # top on the bed (no supports)
    if name == 'floor_duct':        m = m.mirror((0, 0, 1))
    # desiccant_lid prints as modelled: slotted plate on the bed, finger tab up.
    # (It was flipped, which left the 64 x 130 mm plate in mid-air on the 6 mm tab.)
    b = m.bounding_box()
    return m.translate((-(b[0]+b[3])/2, -(b[1]+b[4])/2, -b[2]))

if __name__ == '__main__':
    pw = parts_world()
    for n, m in pw.items():
        if n.endswith('_6'): continue                   # cartridges/lids are identical; print 2 of _1
        if n == 'sensor_housing_chamber': continue
        save(print_pose(n, m), n.replace('_1', ''))
    sh, sl = sensor_housing()
    save(print_pose('sensor_housing', sh), 'sensor_housing')
    save(print_pose('sensor_lid', sl.mirror((0, 1, 0))), 'sensor_housing_lid')
    gel = (CART_W - 2*CW) * (CART_L - 2*CW) * (CART_H - CW - 5) / 1000
    print(f'cartridge gel volume {gel:.0f} cm3 (~{gel*0.72:.0f} g silica gel at 0.72 g/cm3)')
