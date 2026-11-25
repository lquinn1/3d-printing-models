# SPDX-License-Identifier: MIT
"""Door checks: closed fit, seal backing, magnets, panes in their grooves, swing clearance."""
import itertools, numpy as np, manifold3d as mf
from tiles import make_tiles
from front import parts_world, MAGNET_Z, REED_Z
from door import *

fixed = [(t.name, t.build(simple=True).transform(t.M()[:3])) for t in make_tiles()] + \
        list(parts_world().items()) + list(fixed_hinges().items())
FIX = mf.Manifold.batch_boolean([m for _, m in fixed], mf.OpType.Add)
mov = moving_parts()
DOOR = mf.Manifold.batch_boolean(list(mov.values()), mf.OpType.Add)

# door members don't overlap each other (tenon in mortise, rails against stiles)
w = max((a ^ b).volume() for (_, a), (_, b) in itertools.combinations(list(door_parts().items()), 2))
print('door members max mutual overlap: %.3f mm3' % w)

# panes sit in the grooves without touching anything
panes = []
for a, b in SLOTS_T:
    x0 = XL1 - SLOT_DEPTH + PANE_CLR; z0 = ZB1 - SLOT_DEPTH + PANE_CLR
    pt = 2.36                                                       # 0.093 in polycarbonate
    yc = DY0 + (a + b)/2
    panes.append(box(x0, x0 + PANE[0], yc - pt/2, yc + pt/2, z0, z0 + PANE[1]))
print('panes vs door members: %.3f mm3' % sum((p ^ m).volume() for p in panes for m in door_parts().values()))
print('pane bite into the grooves: %.1f mm each edge' % (SLOT_DEPTH - PANE_CLR))

for deg in (0, 15, 30, 60, 90, 110):
    D = swing(DOOR, deg)
    P = mf.Manifold.batch_boolean([swing(p, deg) for p in panes], mf.OpType.Add)
    print(f'swing {deg:3d} deg: door vs fixed {((D + P) ^ FIX).volume():.3f} mm3')

# seal: the door's back face backs the whole EPDM loop on the ring
loop = [box(15, 24, DY1 + 0.05, DY1 + 0.2, 25, 423.5), box(507.4, 516.4, DY1 + 0.05, DY1 + 0.2, 25, 423.5),
        box(15, 516.4, DY1 + 0.05, DY1 + 0.2, 25, 34), box(15, 516.4, DY1 + 0.05, DY1 + 0.2, 414.5, 423.5)]
backing = DOOR.translate((0, 0.3, 0))      # door pressed back onto the squeezed EPDM
for i, s in enumerate(loop):
    print(f'EPDM band {i}: backed {100*(s ^ backing).volume()/s.volume():.1f} %')
# magnets line up
for z in list(MAGNET_Z) + [REED_Z]:
    probe = box(MAG_X - 0.5, MAG_X + 0.5, DY1 - 1.0, DY1 - 0.5, z - 0.5, z + 0.5)
    print(f'door magnet pocket at z {z:.0f}: open {(probe ^ DOOR).volume() < 1e-6}')
print(f'door: x {DX0}..{DX1}, y {DY0}..{DY1}, z {DZ0}..{DZ1}; gap to header {HDR_Z0 - DZ1:.1f} mm')
