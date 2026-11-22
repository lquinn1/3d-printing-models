# SPDX-License-Identifier: MIT
"""Preview renders of the coupons (uses the concept renderer in source/render)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source', 'render'))
import trimesh, numpy as np
from scene import render, hexc, box
from coupons import *
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')

def tm(m):
    o = m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts, process=False)

parts = [
    (port_socket_coupon(), (0, 0), '#e8833a'),
    (port_blank_plug := port_module('plug'), (-45, -62), '#3d7dd8'),
    (port_module('ptfe'), (-5, -62), '#3d7dd8'),
    (rod_cradle(), (45, -70), '#5aa865'),
    (index_collar(), (100, -62), '#c9c9c9'),
    (tile_joint('a'), (-150, -20), '#d9c27a'),
    (tile_joint('b').rotate((0, 0, 180)).translate((0, -6, 0)), (-150, -20), '#cfb35f'),
]
items = [(box(-260, 200, -170, 120, -2, 0), hexc('#d8d4cc'))]
for m, (x, y), c in parts:
    items.append((tm(m.translate((x, y, 0))), hexc(c)))
render(items, [], [], os.path.join(IMG, 'cad_coupons.jpg'), eye=(-60, -300, 210), target=(-30, -25, 0), fov=40, W=1500, H=1000)

# cutaway: blank plug and PTFE module screwed into 0.25 sockets, cut on the y = 0 plane
half = mf.Manifold.cube((400, 200, 200)).translate((-200, 0, -100))
sock = port_socket_coupon()
plug = port_module('plug').translate((0, 0, -FLANGE_H_PLUG))
mod = port_module('ptfe').translate((40, 0, -FLANGE_H_MODULE))
best = min(range(0, 360, 3), key=lambda a: (sock ^ plug.rotate((0, 0, a))).volume()); plug = plug.rotate((0, 0, best))
mod0 = port_module('ptfe').translate((0, 0, -FLANGE_H_MODULE))
best2 = min(range(0, 360, 3), key=lambda a: (sock.translate((-40, 0, 0)) ^ mod0.rotate((0, 0, a))).volume())
mod = mod0.rotate((0, 0, best2)).translate((40, 0, 0))
cut = [(tm(sock ^ half), hexc('#e8833a')), (tm(plug ^ half), hexc('#3d7dd8')), (tm(mod ^ half), hexc('#3d7dd8'))]
render(cut, [], [], os.path.join(IMG, 'cad_port_section.jpg'), eye=(20, -230, 70), target=(20, 0, 3), fov=30, W=1400, H=800,
       key=(-0.3, -0.8, 0.5))
print('ok')
