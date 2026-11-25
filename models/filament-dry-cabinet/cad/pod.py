# SPDX-License-Identifier: MIT
"""Rear control pod: 330 x 230 x 50 mm printed box on the back panel (outside the chamber).

Holds the IEC C14 fused/switched inlet (snap-in, right side wall), the Mean Well LRS-200-24
(on rails, two clamp bars), and two drillable carrier plates for the ESP32-S3 DevKitC, the
24->5 V buck, MOSFET/level-shifter board and terminal blocks. Low-voltage wires go into the
chamber through the gland module in the back tile's 13th socket, which the pod surrounds.
Mains never leaves the pod.
"""
import os, numpy as np, manifold3d as mf, cadquery as cq
from params import *
from coupons import cyl, save, cq_to_mf, port_module
from tiles import T, Y1, FLOOR, POD_PX0, POD_PTS, GLAND
from front import box, cyl_x, cyl_y, cyl_z, M3_INSERT_D, M3_INSERT_L, M3_CLR

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
PX0, PX1 = POD_PX0, POD_PX0 + 330.0
PZ0, PZ1 = FLOOR + 10.0, FLOOR + 240.0
PY0, PY1 = Y1, Y1 + 50.0
PW = 3.0                                   # walls, back plate, cover
COV = PY1 - PW                             # cover sits on the walls here
# PSU: Mean Well LRS-200-24, 215 x 115 x 30 mm, terminals at the left (-x) end
PSU = dict(x0=PX0 + 105, x1=PX0 + 320, z0=PZ0 + 15, z1=PZ0 + 130, y0=PY0 + PW + 5, h=30.0)
CLAMP_X = (PX0 + 140, PX0 + 285)
# IEC C14 + fuse + switch, generic snap-in: 47.5 x 27.5 mm cut-out, 1-2 mm panel   (check yours)  FIT
IEC_CUT = (27.5, 47.5)                     # (along y, along z)
IEC_PANEL = 1.6
IEC_C = (PY0 + 25.0, PZ0 + 184.0)          # (y, z) centre on the right wall
CARRIERS = {'carrier_main': (PX0 + 100, PX0 + 280, PZ0 + 145, PZ0 + 214),
            'carrier_left': (PX0 + 8, PX0 + 93, PZ0 + 15, PZ0 + 105)}
CARRIER_STANDOFF = 8.0

def pod_base():
    m = box(PX0, PX1, PY0, PY0 + PW, PZ0, PZ1)                                 # back plate
    m += box(PX0, PX1, PY0, COV, PZ0, PZ0 + PW) + box(PX0, PX1, PY0, COV, PZ1 - PW, PZ1)
    m += box(PX0, PX0 + PW, PY0, COV, PZ0, PZ1) + box(PX1 - PW, PX1, PY0, COV, PZ0, PZ1)
    # cover screw columns in the corners (M3 inserts from the cover side)
    for x in (PX0 + 6, PX1 - 6):
        for z in (PZ0 + 6, PZ1 - 6):
            m += box(x - 6, x + 6, PY0, COV, z - 6, z + 6)
            m -= cyl_y(x, z, COV - M3_INSERT_L, COV + 1, M3_INSERT_D/2)
    # bolts into the back-tile inserts (M4, heads inside the pod)
    for x, z in POD_PTS:
        m -= cyl_y(x, z, PY0 - 1, PY0 + PW + 1, BOLT_CLEAR_D/2)
    # opening round the gland module (hex flange 30 AF + room for a spanner)
    m -= cyl_y(GLAND[0], GLAND[1], PY0 - 1, PY0 + PW + 1, 21.0, n=64)
    # PSU rails (5 mm air gap behind the metal case) and clamp posts
    for z in (PSU['z0'] + 12, PSU['z1'] - 12):
        m += box(PSU['x0'] + 5, PSU['x1'] - 5, PY0 + PW - 0.01, PSU['y0'], z - 4, z + 4)
    yf = PSU['y0'] + PSU['h'] + 1.5            # posts 1.5 mm proud: a 2 mm rubber pad gets squeezed
    for x in CLAMP_X:
        for z in (PSU['z0'] - 6, PSU['z1'] + 6):
            m += box(x - 5, x + 5, PY0 + PW - 0.01, yf, z - 5, z + 5)
            m -= cyl_y(x, z, yf - M3_INSERT_L, yf + 1, M3_INSERT_D/2)
    # end stop at the PSU's right end (terminals stay free at the left)
    m += box(PSU['x1'] + 1, PSU['x1'] + 5, PY0 + PW - 0.01, PSU['y0'] + 10, PSU['z0'] + 20, PSU['z1'] - 20)
    # IEC inlet: snap-in cut-out in the right wall, wall thinned to the panel thickness round it
    yc, zc = IEC_C
    m -= box(PX1 - PW - 1, PX1 - IEC_PANEL, yc - IEC_CUT[0]/2 - 3, yc + IEC_CUT[0]/2 + 3, zc - IEC_CUT[1]/2 - 3, zc + IEC_CUT[1]/2 + 3)
    m -= box(PX1 - PW - 1, PX1 + 1, yc - IEC_CUT[0]/2, yc + IEC_CUT[0]/2, zc - IEC_CUT[1]/2, zc + IEC_CUT[1]/2)
    # intake slots in the bottom wall under the PSU (exhaust is through the cover)
    for x in np.arange(PSU['x0'] + 15, PSU['x1'] - 10, 10.0):
        m -= box(x, x + 4, PY0 + PW + 6, COV - 6, PZ0 - 1, PZ0 + PW + 1)
    # carrier plate standoffs (M3 inserts)
    for name, (x0, x1, z0, z1) in CARRIERS.items():
        for x in (x0 + 5, x1 - 5):
            for z in (z0 + 5, z1 - 5):
                m += cyl_y(x, z, PY0 + PW - 0.01, PY0 + PW + CARRIER_STANDOFF, 4.0)
                m -= cyl_y(x, z, PY0 + PW + CARRIER_STANDOFF - M3_INSERT_L, PY0 + PW + CARRIER_STANDOFF + 1, M3_INSERT_D/2)
    # zip-tie anchors along the left wall (mains kept apart from low voltage) and by the gland
    for z in (PZ0 + 120, PZ0 + 175):
        a = box(PX0 + PW - 0.01, PX0 + PW + 8, PY0 + PW + 10, PY0 + PW + 18, z - 6, z + 6)
        a -= box(PX0 + PW - 1, PX0 + PW + 9, PY0 + PW + 12, PY0 + PW + 16, z - 2, z + 2)
        m += a
    return m

def pod_cover():
    m = box(PX0, PX1, COV, PY1, PZ0, PZ1)
    for x in (PX0 + 6, PX1 - 6):
        for z in (PZ0 + 6, PZ1 - 6):
            m -= cyl_y(x, z, COV - 1, PY1 + 1, M3_CLR/2)
            m -= cyl_y(x, z, PY1 - 1.8, PY1 + 1, 3.1)
    # exhaust slots over the PSU, and a smaller field over the controller
    for x in np.arange(PSU['x0'] + 10, PSU['x1'] - 10, 9.0):
        m -= box(x, x + 4, COV - 1, PY1 + 1, PSU['z0'] + 10, PSU['z1'] - 10)
    for x in np.arange(PX0 + 110, PX0 + 270, 9.0):
        m -= box(x, x + 4, COV - 1, PY1 + 1, PZ0 + 150, PZ0 + 200)
    # lip that locates inside the walls
    lip = box(PX0 + PW + 0.3, PX1 - PW - 0.3, COV - 3, COV, PZ0 + PW + 0.3, PZ1 - PW - 0.3)
    lip -= box(PX0 + PW + 2.3, PX1 - PW - 2.3, COV - 4, COV + 1, PZ0 + PW + 2.3, PZ1 - PW - 2.3)
    for x in (PX0 + 6, PX1 - 6):                       # notch the lip round the screw columns
        for z in (PZ0 + 6, PZ1 - 6):
            lip -= box(x - 7, x + 7, COV - 4, COV + 1, z - 7, z + 7)
    m += lip
    # mains warning, debossed 0.8 mm on the outside
    txt = (cq.Workplane('XZ').workplane(offset=-(PY1 + 1))
           .center(PX0 + 55, PZ1 - 25).text('120V~  3.15A T', 7, 1.8, fontPath=FONT, halign='center', valign='center'))
    m -= cq_to_mf(txt.val())
    txt = (cq.Workplane('XZ').workplane(offset=-(PY1 + 1))
           .center(PX0 + 55, PZ1 - 38).text('UNPLUG BEFORE OPENING', 4.5, 1.8, fontPath=FONT, halign='center', valign='center'))
    m -= cq_to_mf(txt.val())
    return m

def psu_clamp():
    """Bar across the PSU front, 2 x M3 into the clamp posts; rubber pad recommended."""
    L_ = PSU['z1'] - PSU['z0'] + 12 + 10
    m = box(-6, 6, 0, 4, -L_/2, L_/2)
    for s in (-1, 1):
        zz = s*(PSU['z1'] - PSU['z0'] + 12)/2
        m -= cyl_y(0, zz, -1, 5, M3_CLR/2)
    return m

def carrier(name):
    x0, x1, z0, z1 = CARRIERS[name]
    m = box(x0, x1, 0, 3, z0, z1)
    for x in (x0 + 5, x1 - 5):
        for z in (z0 + 5, z1 - 5):
            m -= cyl_y(x, z, -1, 4, M3_CLR/2)
    # 10 mm grid of 2.5 mm pilot holes for self-tapping screws / standoffs
    for x in np.arange(x0 + 15, x1 - 10, 10.0):
        for z in np.arange(z0 + 12, z1 - 8, 10.0):
            m -= cyl_y(x, z, -1, 4, 1.25, n=12)
    return m.translate((0, PY0 + PW + CARRIER_STANDOFF, 0))

def parts_world():
    return {'pod_base': pod_base(), 'pod_cover': pod_cover(),
            'carrier_main': carrier('carrier_main'), 'carrier_left': carrier('carrier_left')}

def check():
    import itertools
    from tiles import make_tiles
    tiles = [(t.name, t.build(simple=True).transform(t.M()[:3])) for t in make_tiles() if t.f.name == 'BACK']
    pw = list(parts_world().items())
    clamps = [psu_clamp().translate((x, PSU['y0'] + PSU['h'] + 1.5, (PSU['z0'] + PSU['z1'])/2)) for x in CLAMP_X]
    allp = tiles + pw + [('clamp', c) for c in clamps]
    worst = max((a ^ b).volume() for (_, a), (_, b) in itertools.combinations(allp, 2))
    print('pod parts / back tiles max overlap: %.3f mm3' % worst)
    solid = mf.Manifold.batch_boolean([m for _, m in pw] + clamps, mf.OpType.Add)
    psu = box(PSU['x0'], PSU['x1'], PSU['y0'], PSU['y0'] + PSU['h'], PSU['z0'], PSU['z1'])
    yc, zc = IEC_C
    iec = box(PX1 - IEC_PANEL - 45, PX1 - IEC_PANEL, yc - 15, yc + 15, zc - 25, zc + 25)
    glandm = port_module('gland').transform(np.array([[1, 0, 0, GLAND[0]], [0, 0, -1, Y1], [0, 1, 0, GLAND[1]]], float))
    for n, env in (('PSU 215x115x30', psu), ('IEC inlet body (45 deep)', iec), ('gland module', glandm)):
        print(f'{n:26s} clashes with pod parts: {(env ^ solid).volume():.3f} mm3')
    blocked = sum((mf.Manifold.sphere(1.0, 16).translate((x, Y1 + 1.5, z)) ^ solid).volume() > 1e-4 for x, z in POD_PTS)
    print(f'pod bolt holes blocked: {blocked} of {len(POD_PTS)}')
    print(f'clamp bar presses: PSU front y {PSU["y0"] + PSU["h"]:.1f}, bar underside y {PSU["y0"] + PSU["h"] + 1.5:.1f} (2 mm pad)')
    print(f'cover inner face y {COV:.1f}, highest part inside y {(solid - box(PX0, PX1, COV - 3.01, PY1, PZ0, PZ1)).bounding_box()[4]:.1f}')

BACK_DOWN = np.array([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]], float)   # y face -> bed (det +1)
def to_print(m, M):
    m = m.transform(M); b = m.bounding_box()
    return m.translate((-(b[0]+b[3])/2, -(b[1]+b[4])/2, -b[2]))

if __name__ == '__main__':
    for n, m in parts_world().items():
        if n == 'pod_cover':          # print outside face down
            m = m.transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0]], float))
            b = m.bounding_box(); m = m.translate((-(b[0]+b[3])/2, -(b[1]+b[4])/2, -b[2]))
        else:
            m = to_print(m, BACK_DOWN)
        save(m, n)
    save(to_print(psu_clamp(), BACK_DOWN), 'psu_clamp')
    save(port_module('gland'), 'port_gland_module')
    check()
    print(f'pod {PX1-PX0:.0f} x {PZ1-PZ0:.0f} x {PY1-PY0:.0f} mm at x {PX0:.1f}..{PX1:.1f}, z {PZ0:.1f}..{PZ1:.1f}')
