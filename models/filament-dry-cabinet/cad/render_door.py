# SPDX-License-Identifier: MIT
"""Renders: cabinet with the door closed, and with the door open 100 deg (latch close-ups: render_latch.py)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source', 'render'))
import numpy as np, trimesh, manifold3d as mf
from scene import render, hexc, box as sbox
from tiles import make_tiles, cradle_world, POCKET_XY, foot, ROD_Y, FLOOR, A, W
from front import parts_world, tft_geometry, FAS, TFT_GAP, TFT_STACK, ENC_X, ZC, NFC_X, NFC_BOARD, cyl_y
from door import *
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')
def tm(m):
    o = m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts, process=False)
COL = {'L': '#3b82c4', 'R': '#3b82c4', 'TOP': '#e8833a', 'BOT': '#5aa865', 'BACK': '#8f6fd1'}
shell = [(tm(t.build(simple=True).transform(t.M()[:3])), hexc(COL[t.f.name])) for t in make_tiles()]
front = [(tm(m), hexc('#e8833a' if n in ('tft_bezel', 'nfc_tap_overlay', 'encoder_knob') else '#1d1e21' if 'fascia' in n else '#f1f1ee' if 'led' in n else '#3a3d42')) for n, m in parts_world().items()]
hing = [(tm(m), hexc('#9aa0a6')) for m in fixed_hinges().values()]
(wx, wz), (bx, bz), holes, win = tft_geometry()
y_l = FAS + TFT_GAP
extras = [(tm(box(wx - 37, wx + 37, y_l, y_l + 4, wz - 24.8, wz + 24.8)), hexc('#0b0c0e')),
          (tm(box(wx - 37, wx + 37, y_l - 0.05, y_l + 0.2, wz + 24.8 - 49.6*220/320, wz + 24.8)), hexc('#1c6dd0')),
          ]
# rods + a few spools so the door has something to show
from coupons import cyl
inside = []
for k, y in enumerate(ROD_Y):
    rz = FLOOR + (A['rod_front'] if k < 2 else A['rod_back'])
    inside.append((tm(cyl(13.3, 0, 498, n=40).transform(np.array([[0,0,1,(W-498)/2],[1,0,0,y],[0,1,0,rz]], float))), hexc('#e9ecef')))
SP = ['#f1f1ee', '#2f2f2f', '#d62828', '#2d7dd2', '#4caf2a', '#f2b705', '#8d99ae', '#ff7a1a', '#7b4fd6', '#e84393', '#11a3a3', '#f1f1ee']
from tiles import X_SLOT, Y_FRONT_ROW, Y_BACK_ROW
for row, (yc, rz) in enumerate(((Y_FRONT_ROW, FLOOR + A['rod_front']), (Y_BACK_ROW, FLOOR + A['rod_back']))):
    zc = rz + 99.1
    for i, x in enumerate(X_SLOT):
        sp = cyl(100, -32, 32, n=64).transform(np.array([[0,0,1,x],[1,0,0,yc],[0,1,0,zc]], float))
        hub = cyl(28, -37.5, 37.5, n=32).transform(np.array([[0,0,1,x],[1,0,0,yc],[0,1,0,zc]], float))
        inside += [(tm(sp), hexc(SP[row*6 + i])), (tm(hub), hexc('#cfcfcf'))]
floor = sbox(-1500, 2000, -1500, 2000, -1, 0)
for deg, name, eye in ((0, 'cad_door_closed.jpg', (-480, -1150, 720)), (100, 'cad_door_open.jpg', (850, -1250, 760))):
    mv = moving_parts()
    door = [(tm(swing(m, deg)), hexc('#e8833a' if 'latch' in n else '#9aa0a6' if 'hinge' in n else '#2b2d31')) for n, m in mv.items()]
    panes = []
    for a, b in SLOTS_T:
        x0 = XL1 - SLOT_DEPTH + PANE_CLR; z0 = ZB1 - SLOT_DEPTH + PANE_CLR; yc = DY0 + (a + b)/2
        panes.append(tm(swing(box(x0, x0 + PANE[0], yc - 1.18, yc + 1.18, z0, z0 + PANE[1]), deg)))
    render([(floor, hexc('#d8d4cc'))] + shell + front + hing + extras + inside + door, panes, [],
           os.path.join(IMG, name), eye=eye, target=(265, 150, 240), fov=34, W=1400, H=1150)
print('ok')
