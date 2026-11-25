# SPDX-License-Identifier: MIT
"""Cutaway render of the service void: right wall and roof removed, front row hidden."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source', 'render'))
import numpy as np, trimesh, manifold3d as mf
from scene import render, hexc, box as sbox
from interior import *
from tiles import make_tiles, cradle_world
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')
def tm(m):
    o = m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts, process=False)
COL = {'L': '#3b82c4', 'R': '#3b82c4', 'TOP': '#e8833a', 'BOT': '#5aa865', 'BACK': '#8f6fd1'}
items = [(sbox(-1500, 2000, -1500, 2000, -1, 0), hexc('#d8d4cc'))]
items += [(tm(t.build(simple=True).transform(t.M()[:3])), hexc(COL[t.f.name])) for t in make_tiles() if t.f.name in ('L', 'BOT', 'BACK')]
items += [(tm(cradle_world(s, k)), hexc('#c9c9c9')) for s in ('L', 'R') for k in range(4)]
items += [(tm(rod(k)), hexc('#d8bf8f')) for k in range(4)] + [(tm(c), hexc('#9aa0a6')) for k in range(4) for c in collars(k)]
SP = ['#ff7a1a', '#7b4fd6', '#e84393', '#11a3a3', '#8d99ae', '#f1f1ee']
items += [(tm(spool(1, i)), hexc(SP[i])) for i in (1, 2, 3, 4)]            # back row, slots 2-5 (1 and 6 out to show the cartridges)
items += [(tm(spool(0, i)), hexc('#d62828')) for i in (4,)]
C = {'desiccant_cartridge': '#f2b705', 'desiccant_lid': '#f2b705', 'plenum': '#5c6470', 'heater_duct': '#b02a2a',
     'floor_duct': '#b02a2a', 'sensor_housing': '#1f5f3a'}
for n, m in parts_world().items():
    items.append((tm(m), hexc(next(v for k, v in C.items() if n.startswith(k)))))
fan = box(FAN_X - 40, FAN_X + 40, PL_Y0 + PW_, PL_Y0 + PW_ + 25, FAN_Z - 40, FAN_Z + 40)
items.append((tm(fan), hexc('#222222')))
render(items, [], [], os.path.join(IMG, 'cad_interior.jpg'), eye=(980, -620, 620), target=(265, 280, 110), fov=36, W=1400, H=1050, key=(0.4, -0.7, 0.6))
print('ok')
