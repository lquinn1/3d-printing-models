# SPDX-License-Identifier: MIT
"""Renders of the front frame and header on the shell (door not yet designed)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source', 'render'))
import numpy as np, trimesh
from scene import render, hexc, box as sbox
from tiles import make_tiles, POCKET_XY, foot, cradle_world
from front import *
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')

def tm(m):
    o = m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts, process=False)
COL = {'L': '#3b82c4', 'R': '#3b82c4', 'TOP': '#e8833a', 'BOT': '#5aa865', 'BACK': '#8f6fd1'}
PC = {'frame': '#3a3d42', 'header_chassis': '#3a3d42', 'header_fascia': '#1d1e21', 'led': '#f1f1ee'}

tiles = make_tiles()
shell = [(tm(t.build(simple=True).transform(t.M()[:3])), hexc(COL[t.f.name])) for t in tiles]
pw = parts_world()
(wx, wz), (bx, bz), holes, win = tft_geometry()
y_l = FAS + TFT_GAP; y_p = y_l + TFT_STACK
extras = [
    (tm(box(bx - 49 + 6.54, bx - 49 + 91.5, y_l, y_p, bz - 27.75, bz + 27.75)), hexc('#0b0c0e')),   # lens/LCD
    (tm(box(wx - 37, wx + 37, y_l - 0.05, y_l + 0.2, wz - 1.5, wz + 24.8)), hexc('#e8590c')),       # label band
    (tm(box(bx - 49, bx + 49, y_p, y_p + 1.6, bz - 27.75, bz + 27.75)), hexc('#1f5f3a')),           # PCB
    (tm(cyl_y(ENC_X, ZC, -16, 0, 12, n=48)), hexc('#9aa0a6')),                                       # knob
    (tm(box(NFC_X - NFC_BOARD[0]/2, NFC_X + NFC_BOARD[0]/2, FAS, FAS + 1.6, ZC - NFC_BOARD[1]/2, ZC + NFC_BOARD[1]/2)), hexc('#b02a2a')),
]
def col(n):
    return hexc(next(v for k, v in PC.items() if n.startswith(k)))
floor = sbox(-1500, 2000, -1500, 2000, -1, 0)
front = [(tm(m), col(n)) for n, m in pw.items()]
render([(floor, hexc('#d8d4cc'))] + shell + front + extras, [], [],
       os.path.join(IMG, 'cad_front_frame.jpg'), eye=(-420, -1050, 700), target=(265, 150, 250), fov=34, W=1400, H=1150)

# header exploded, from the front-left and slightly below
ex = []
for n, m in pw.items():
    if n.startswith('header_fascia'): ex.append((tm(m.translate((0, -60, 0))), col(n)))
    elif n.startswith('header_chassis') or n.startswith('led'): ex.append((tm(m), col(n)))
ex += [(tm(e.vertices and m), c) for m, c in []]
board = [(box(bx - 49 + 6.54, bx - 49 + 91.5, y_l - 30, y_p - 30, bz - 27.75, bz + 27.75), '#0b0c0e'),
         (box(bx - 49, bx + 49, y_p - 30, y_p - 28.4, bz - 27.75, bz + 27.75), '#1f5f3a'),
         (box(NFC_X - NFC_BOARD[0]/2, NFC_X + NFC_BOARD[0]/2, FAS - 30, FAS - 28.4, ZC - NFC_BOARD[1]/2, ZC + NFC_BOARD[1]/2), '#b02a2a')]
ex += [(tm(b), hexc(c)) for b, c in board]
render(ex, [], [], os.path.join(IMG, 'cad_header_exploded.jpg'),
       eye=(150, -520, 600), target=(265, 0, 452), fov=36, W=1500, H=700, key=(-0.3, -0.8, 0.5))
print('ok')
