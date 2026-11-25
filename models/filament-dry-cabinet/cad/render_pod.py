# SPDX-License-Identifier: MIT
"""Rear renders: pod with the cover pulled off, and the finished back."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source', 'render'))
import numpy as np, trimesh, manifold3d as mf
from scene import render, hexc, box as sbox
from tiles import make_tiles, SOCKETS, GLANDS, Y1
from coupons import port_module
from pod import *
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')
def tm(m):
    o = m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts, process=False)
COL = {'L': '#3b82c4', 'R': '#3b82c4', 'TOP': '#e8833a', 'BOT': '#5aa865', 'BACK': '#8f6fd1'}
shell = [(tm(t.build(simple=True).transform(t.M()[:3])), hexc(COL[t.f.name])) for t in make_tiles()]
plug = port_module('plug'); gl = port_module('gland')
mods = []
for face, p in SOCKETS:
    m = gl if (face == 'BACK' and any(abs(p[0] - gx) < 1 and abs(p[2] - gz) < 1 for gx, gz in GLANDS)) else plug
    if face == 'BACK':
        M = np.array([[1, 0, 0, p[0]], [0, 0, -1, Y1], [0, 1, 0, p[2]]], float)
    else:
        M = np.array([[1, 0, 0, p[0]], [0, 1, 0, p[1]], [0, 0, -1, p[2]]], float)
    mods.append((tm(m.transform(M)), hexc('#2b2d31')))
psu = box(PSU['x0'], PSU['x1'], PSU['y0'], PSU['y0'] + PSU['h'], PSU['z0'], PSU['z1'])
yc, zc = IEC_C
iec = box(PX1 - IEC_PANEL - 40, PX1 + 6, yc - 14, yc + 14, zc - 24, zc + 24)
inside = [(tm(psu), hexc('#b9bec4')), (tm(iec), hexc('#111111'))]
inside += [(tm(psu_clamp().translate((x, PSU['y0'] + PSU['h'] + 1.5, (PSU['z0'] + PSU['z1'])/2))), hexc('#555555')) for x in CLAMP_X]
board = box(PX0 + 120, PX0 + 190, PY0 + 15, PY0 + 17, PZ0 + 160, PZ0 + 186)       # ESP32 DevKitC on the carrier
inside += [(tm(board), hexc('#1f5f3a'))]
pw = parts_world()
floor = sbox(-1500, 2000, -1500, 2000, -1, 0)
base = [(tm(pw['pod_base']), hexc('#3a3d42')), (tm(pw['carrier_main']), hexc('#d9d9d9')), (tm(pw['carrier_left']), hexc('#d9d9d9'))]
cover_off = [(tm(pw['pod_cover'].translate((0, 140, 0))), hexc('#3a3d42'))]
render([(floor, hexc('#d8d4cc'))] + shell + mods + base + inside + cover_off, [], [],
       os.path.join(IMG, 'cad_pod_open.jpg'), eye=(1150, 1650, 650), target=(265, 380, 200), fov=32, W=1400, H=1100, key=(0.5, 0.8, 0.5))
render([(floor, hexc('#d8d4cc'))] + shell + mods + base + inside + [(tm(pw['pod_cover']), hexc('#3a3d42'))], [], [],
       os.path.join(IMG, 'cad_back.jpg'), eye=(1100, 1700, 900), target=(265, 300, 230), fov=34, W=1400, H=1100, key=(0.5, 0.8, 0.5))
print('ok')
