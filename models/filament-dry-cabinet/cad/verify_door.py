# SPDX-License-Identifier: MIT
"""Door checks: closed fit, seal backing, magnets, panes in their grooves, swing clearance."""
import itertools, math, numpy as np, manifold3d as mf
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

# ------------------------------------------------------------------ latch (flush lift-bar)
from front import keeper_pin
from door import KEEPER_PIN
BAR = latch_bar(); PIN = keeper_pin()
CLIP = box(490, 540, -80, 40, 90, 300)
FIX_NO_PIN = mf.Manifold.batch_boolean([m for n, m in fixed if n != 'keeper_pin'], mf.OpType.Add) ^ CLIP
DOOR_ONLY = mf.Manifold.batch_boolean([m for n, m in mov.items() if n != 'latch_bar'], mf.OpType.Add) ^ CLIP
print('bar closed: vs door %.3f, vs frame %.3f, vs pin %.3f mm3' % ((BAR ^ DOOR_ONLY).volume(), (BAR ^ FIX_NO_PIN).volume(), (BAR ^ PIN).volume()))
print('bar closed: hook touches the pin (0.15 mm probe): %s' % ((BAR ^ PIN.translate((0, 0.15, 0))).volume() > 1e-4))
stop = None
for a in np.arange(0, -45.1, -1.0):
    B = bar_turn(BAR, a)
    if (B ^ DOOR_ONLY).volume() > 1e-3: stop = a; break
    assert (B ^ FIX_NO_PIN).volume() < 1e-3 and (B ^ PIN).volume() < 1e-4, a
print(f'bar swings 0..{stop + 1:.0f} deg free of the door and frame; stops against the door at {stop:.0f}')
def free(a):
    B = bar_turn(BAR, a)
    sweep = mf.Manifold.batch_boolean([B.translate((0, -t, 0)) for t in np.arange(0, 15.01, 0.5)], mf.OpType.Add)
    return (sweep ^ PIN).volume() < 1e-4
rel = next(a for a in np.arange(0, -33, -0.5) if free(a))
print(f'hook releases at {rel} deg (bar bottom end {130*math.sin(math.radians(-rel)):.0f} mm forward)')
need = []
for d in np.arange(10, 0.24, -0.25):
    if (BAR.translate((0, -d, 0)) ^ PIN).volume() < 1e-4: need.append(0.0); continue
    need.append(next(a for a in np.arange(0, -33, -0.25) if (bar_turn(BAR, a).translate((0, -d, 0)) ^ PIN).volume() < 1e-4))
print(f'closing: the pin pushes the bar out at most {min(need)} deg (< stop), and it drops back flush at closed: '
      f'{(BAR ^ PIN).volume() < 1e-4}')
ky, kz = KEEPER_PIN
def catches(d):
    """Door short of closed by d: raising the bar from open, the first contact must be
    on the pin's back half (the hook pulls the door in), not its top or front."""
    for a in np.arange(-25, 0.01, 0.25):
        v = bar_turn(BAR, a).translate((0, -d, 0)) ^ PIN
        if v.volume() > 1e-4: return v.bounding_box()[1] > ky - 0.2, a
    return False, None
for d in (0.5, 1.0, 1.5, 2.0):
    ok, a = catches(d)
    print(f'door {d:.1f} mm short of closed: pushing the bar flush draws it in: {ok} (contact from {a} deg)')
for a in (0, -20):
    D = DOOR_ONLY + bar_turn(BAR, a)
    for deg in (2, 5, 15, 30, 60, 90, 110):
        v = (swing(D, deg) ^ (FIX_NO_PIN + PIN)).volume()
        assert v < 1e-3, (a, deg, v)
    print(f'door swing 2..110 deg with the bar at {a} deg: clear')
