# SPDX-License-Identifier: MIT
"""Renders of the tile set: exploded shell, assembled shell, one tile from the inside."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source', 'render'))
import numpy as np, trimesh
from scene import render, hexc, box as sbox
from tiles import *
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')
COL = {'L': '#3b82c4', 'R': '#3b82c4', 'TOP': '#e8833a', 'BOT': '#5aa865', 'BACK': '#8f6fd1'}

def tm(m):
    o = m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts, process=False)

tiles = make_tiles()
built = [(t, t.build(simple=True)) for t in tiles]
floor = sbox(-1500, 2000, -1500, 2000, -1, 0)

def scene(explode):
    items = [(floor, hexc('#d8d4cc'))]
    for t, m in built:
        wm = m.transform(t.M()[:3])
        if explode:
            c = t.f.world((t.u0+t.u1)/2, (t.v0+t.v1)/2, T/2)
            off = -t.f.N*explode
            # spread the tiles of a face apart a little too
            fc = t.f.world(t.f.umax/2, t.f.vmax/2, T/2)
            off = off + (c - fc)*0.18
            wm = wm.translate(tuple(off))
        items.append((tm(wm), hexc(COL[t.f.name])))
    for s in ('L', 'R'):
        for k in range(4):
            items.append((tm(cradle_world(s, k).translate(((-explode*0.0), 0, 0))), hexc('#c9c9c9')))
    for x, y in POCKET_XY:
        items.append((tm(foot().mirror((0, 0, 1)).translate((x, y, Z0 - (explode*1.6 if explode else 0)))), hexc('#444444')))
    return items

render(scene(140), [], [], os.path.join(IMG, 'cad_shell_exploded.jpg'),
       eye=(-1150, -1500, 1250), target=(265, 220, 230), fov=36, W=1500, H=1250)
render(scene(0), [], [], os.path.join(IMG, 'cad_shell.jpg'),
       eye=(-700, -1050, 900), target=(265, 220, 230), fov=36, W=1400, H=1100)

# one roof tile, inside face up (as it sits in the printer is upside down from this)
t = next(t for t in tiles if t.name == 'top_left_front')
m = t.build()                                      # full threads
# as printed: skin on the bed, foam pocket facing up
items = [(sbox(-200, 500, -200, 450, -1, 0), hexc('#d8d4cc')), (tm(m), hexc(COL['TOP']))]
render(items, [], [], os.path.join(IMG, 'cad_tile_top_left_front.jpg'),
       eye=(-60, -230, 260), target=(130, 105, 0), fov=42, W=1400, H=1000, key=(-0.4, -0.6, 0.7))
t = next(t for t in tiles if t.name == 'side_left_rear_lower')
items = [(sbox(-200, 600, -200, 450, -1, 0), hexc('#d8d4cc')), (tm(t.build(simple=True)), hexc(COL['L']))]
render(items, [], [], os.path.join(IMG, 'cad_tile_side_left_rear_lower.jpg'),
       eye=(-40, -250, 300), target=(150, 110, 0), fov=44, W=1400, H=1000, key=(-0.4, -0.6, 0.7))
print('ok')
