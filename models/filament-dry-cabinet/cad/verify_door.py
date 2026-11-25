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

# ------------------------------------------------------------------ latch
LEV = latch_lever(); POST = latch_post_world()
FIXED_NO_POST = mf.Manifold.batch_boolean([m for n, m in fixed if n != 'latch_post'], mf.OpType.Add)
DOOR_ONLY = mf.Manifold.batch_boolean([m for n, m in mov.items() if n != 'latch_lever'], mf.OpType.Add)
print('latch closed: lever vs post %.3f mm3, vs door %.3f, vs rest of cabinet %.3f'
      % ((LEV ^ POST).volume(), (LEV ^ DOOR_ONLY).volume(), (LEV ^ FIXED_NO_POST).volume()))
grown = latch_post_sleeve().translate((0, 0.15, 0))
print('latch closed: tooth touches the post (0.15 mm probe): %s' % ((LEV ^ grown).volume() > 1e-4))
# lever swing on its pivot, door closed: free of the door and cabinet
for a in (-5, -10, -15, -20, -30, -45):
    L = lever_turn(LEV, a)
    print(f'lever {a:4d} deg: vs door {(L ^ DOOR_ONLY).volume():.3f}  vs cabinet {(L ^ FIXED_NO_POST).volume():.3f}')
# release: lever angle at which the door can come straight forward past the post
def clear_to_open(a):
    L = lever_turn(LEV, a)
    return all((L.translate((0, -dy, 0)) ^ POST).volume() < 1e-3 for dy in np.arange(0.0, 20.1, 0.5))
rel = next((a for a in range(0, -46, -1) if clear_to_open(a)), None)
print(f'latch releases at {rel} deg of lever travel '
      f'(grip moves about {abs(66*np.sin(np.radians(rel or 0))):.0f} mm)')
# self-latching: door swung shut with the lever hanging closed; the post must meet the ramp,
# not the tooth's top. Probe the lever pushed back from 6 mm forward to closed.
hits = [(dy, (LEV.translate((0, -dy, 0)) ^ POST).volume()) for dy in np.arange(6.0, -0.01, -0.5)]
print('closing with lever down (door forward by dy): post meets the ramp first at dy = %.1f mm' %
      next(dy for dy, v in hits if v > 1e-3) if any(v > 1e-3 for _, v in hits) else 'no contact')
# draw-in: with the door short of closed by d, the closed lever overlaps the post -> it pulls the door in
def catches(d):
    """Door short of closed by d: raise the lever from open; the first contact must be on the
    post's back half (tooth hooks behind it), not on its top or front."""
    py, pz = LATCH_POST
    P = POST.translate((0, d, 0))                       # in the door's frame the post is d further back
    back = P ^ box(W - 1, W + 20, py + d, py + d + 10, pz - 10, pz + 10)
    front = P - back
    for a in np.arange(-25.0, 0.01, 0.25):
        L = lever_turn(LEV, a)
        if (L ^ P).volume() > 1e-3:
            return (L ^ back).volume() > 1e-3 and (L ^ front).volume() < 1e-3, a
    return False, None
for d in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    ok, a = catches(d)
    print(f'door {d:.1f} mm short of closed: tooth hooks behind the post: {ok} (first contact at {a} deg)')
# door swing with the lever down and with it opened
for a in (0, -20):
    D = swing(DOOR_ONLY + lever_turn(LEV, a), 0)
    for deg in (2, 5, 15, 30, 60, 90, 110):
        D = swing(DOOR_ONLY + lever_turn(LEV, a), deg)
        v = (D ^ FIX).volume()
        if v > 1e-3: print(f'  lever {a} deg, door {deg} deg: hits cabinet {v:.2f} mm3')
    print(f'door swing 2..110 deg with lever at {a} deg checked')
