# SPDX-License-Identifier: MIT
"""Checks for the front frame + header against the shell tiles."""
import itertools, numpy as np, manifold3d as mf
from tiles import make_tiles, FRONTS, A, FLOOR, W, Y0, Z0, Z1
from front import *

tiles = [(t.name, t.build(simple=True).transform(t.M()[:3])) for t in make_tiles()]
pw = list(parts_world().items())
allp = tiles + pw
worst = 0
for (a, ma), (b, mb) in itertools.combinations(allp, 2):
    if a in dict(tiles) and b in dict(tiles): continue
    v = (ma ^ mb).volume()
    if v > 0.01: print(f'  overlap {a} / {b}: {v:.2f} mm3')
    worst = max(worst, v)
print('max overlap front parts vs everything: %.3f mm3' % worst)

front = mf.Manifold.batch_boolean([m for _, m in pw], mf.OpType.Add)
door_env = box(1, W - 1, 0, F_Y0 - 0.01, Z0 + 1, HDR_Z0 - 1)
print('frame/header material inside the door envelope: %.3f mm3' % (front ^ door_env).volume())
opening = box(OPEN_X0 + 0.01, OPEN_X1 - 0.01, 0, Y0 + 0.5, OPEN_Z0 + 0.01, OPEN_Z1 - 0.01)
print('material in the door opening: %.3f mm3' % ((front + mf.Manifold.batch_boolean([m for _, m in tiles], mf.OpType.Add)) ^ opening).volume())

# every FRONT insert: the part in front has a clear hole, the tile behind has the insert
probe = lambda p: mf.Manifold.sphere(1.0, 16).translate(tuple(p))
covered = blocked = 0
for face, p in FRONTS:
    x, y, z = p
    in_front = [n for n, m in pw if (m ^ box(x-0.5, x+0.5, F_Y0, F_Y1, z-0.5, z+0.5)).volume() > 0 or
                (m ^ probe((x, y - 2, z + 3))).volume() > 0]
    if not in_front: print('  FRONT insert not covered by any part:', face, np.round(p, 1)); continue
    covered += 1
    if any((m ^ probe((x, y - 1.5, z))).volume() > 1e-4 for _, m in pw): blocked += 1
print(f'FRONT inserts covered {covered}/{len(FRONTS)}, blocked {blocked}')

# spool lift: back-row spool top + 24 mm (clear the rods + collars) must pass under the lip
need = FLOOR + A['top_back'] + 24
print(f'back-row spool needs {need:.1f}, opening top {OPEN_Z1:.1f} -> margin {OPEN_Z1 - need:.1f} mm')

# components fit in the header bay
(wx, wz), (bx, bz), holes, win = tft_geometry()
y_l = FAS + TFT_GAP; y_p = y_l + TFT_STACK
lens = box(bx - 49 + 6.54, bx - 49 + 91.5, y_l, y_p, bz - 27.75, bz + 27.75)
pcb = box(bx - 49, bx + 49, y_p, y_p + 1.6 + 4.0, bz - 27.75, bz + 27.75)        # PCB + parts on the back
fpc = box(bx + 49 - 2, bx + 49 + 12, y_p, y_p + 3, bz - 10, bz + 10)               # FPC / pins at the +x end
enc = box(ENC_X - 7, ENC_X + 7, FAS, FAS + 15, ZC - 7.5, ZC + 7.5)
bw, bh = NFC_BOARD
nfc = box(NFC_X - bw/2, NFC_X + bw/2, FAS + 0.01, FAS + 4.0, ZC - bh/2, ZC + bh/2)
for name, env in (('TFT lens+LCD', lens), ('TFT PCB', pcb), ('TFT cable end', fpc), ('EC11 encoder', enc), ('PN5180 board', nfc)):
    hit = [(n, round((env ^ m).volume(), 2)) for n, m in pw if (env ^ m).volume() > 0.01]
    print(f'{name:14s} clashes: {hit or "none"}')
print('TFT: board %.1f..%.1f x, %.1f..%.1f z; bay z %.1f..%.1f' % (bx-49, bx+49, bz-27.75, bz+27.75, HDR_Z0+WALL_H, Z1-WALL_H))
