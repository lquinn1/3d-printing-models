# SPDX-License-Identifier: MIT
"""Interior checks: static fit with all 12 spools, rods and collars; removal paths."""
import itertools, numpy as np, manifold3d as mf
from interior import *
from tiles import make_tiles, cradle_world, SOCKETS
from front import parts_world as front_parts, LIP_Z0, OPEN_Z0, F_Y0
import pod

U = lambda ms: mf.Manifold.batch_boolean(list(ms), mf.OpType.Add)
tiles = U(t.build(simple=True).transform(t.M()[:3]) for t in make_tiles())
cradles = U(cradle_world(s, k) for s in ('L', 'R') for k in range(4))
rods = U([rod(k) for k in range(4)] + [c for k in range(4) for c in collars(k)])
frontp = U(front_parts().values())
spools = {(r, i): spool(r, i) for r in (0, 1) for i in range(6)}
inner = parts_world()
names = list(inner)

# 1) interior parts vs each other and vs the structure, rods, collars, spools
worst = 0
for (a, ma), (b, mb) in itertools.combinations(inner.items(), 2):
    v = (ma ^ mb).volume(); worst = max(worst, v)
    if v > 0.01: print(f'  overlap {a} / {b}: {v:.2f}')
print('interior parts mutual overlap max: %.3f mm3' % worst)
ALLSP = U(spools.values())
for n, m in inner.items():
    hits = {k: (m ^ v).volume() for k, v in (('tiles', tiles), ('cradles', cradles), ('rods+collars', rods), ('front', frontp), ('spools', ALLSP))}
    bad = {k: round(v, 2) for k, v in hits.items() if v > 0.01}
    print(f'{n:24s} {"clear" if not bad else bad}')

# 2) spools vs everything static (sanity)
print('spools vs rods/cradles/tiles: %.3f mm3' % ((ALLSP ^ (cradles + tiles)).volume()))

def sweep(part, path, obstacles, label):
    worst = 0; where = None
    for (dy, dz) in path:
        v = (part.translate((0, dy, dz)) ^ obstacles).volume()
        if v > worst: worst, where = v, (dy, dz)
    print(f'{label}: worst overlap along the path {worst:.3f} mm3' + (f' at dy {where[0]:.0f}, dz {where[1]:.0f}' if where else ''))

# 3) cartridge removal (front spool of the same slot removed): lift, then slide out through the door
for ci, slot in ((0, 0), (1, 5)):
    part = inner[f'desiccant_cartridge_{"1" if ci == 0 else "6"}'] + inner[f'desiccant_lid_{"1" if ci == 0 else "6"}']
    others = U([v for k, v in spools.items() if k != (0, slot)])
    obst = U([tiles, cradles, rods, frontp, others] + [v for n, v in inner.items() if not n.startswith('desiccant')])
    path = [(0, dz) for dz in np.linspace(0, CART_LIFT, 10)] + [(-dy, CART_LIFT) for dy in np.linspace(0, CART_Y0 + 20, 40)]
    sweep(part, path, obst, f'cartridge under slot {slot + 1} out through the door')

# 4) spool removal: front spool (lift 24, out); back spool after its front spool is out
others_all = U([tiles, cradles, rods, frontp] + list(inner.values()))
for i in (0, 2, 5):
    fs = spool(0, i)
    # roll it forward over the front rod (centre moves on an arc round the rod), then out
    ry, rz = ROD_Y[0], ROD_Z[0]; R = SPOOL_R + ROD_OD/2 + 0.5
    cy, cz = Y_FRONT_ROW, ROD_Z[0] + C_ABOVE
    a0 = math.atan2(cy - ry, cz - rz)
    arc = [(ry + R*math.sin(a) - cy, rz + R*math.cos(a) - cz) for a in np.linspace(a0, 0, 12)]
    dy_end, dz_end = arc[-1]
    sweep(fs, arc + [(dy_end - y, dz_end) for y in np.linspace(0, 260, 40)],
          U([others_all] + [v for k, v in spools.items() if k != (0, i)]), f'front spool slot {i+1} out')
    bs = spool(1, i)
    sweep(bs, [(0, z) for z in np.linspace(0, 26, 6)] + [(-y, 26) for y in np.linspace(0, 430, 60)],
          U([others_all] + [v for k, v in spools.items() if k not in ((0, i), (1, i))]), f'back spool slot {i+1} out (front spool removed)')
    # and the claim that it can NOT come out over a front spool that is still there
    best = None
    for lift in (85.0, 100.0):
        path = [(0, z) for z in np.linspace(0, lift, 8)] + [(-y, lift) for y in np.linspace(0, 430, 60)]
        obs = U([others_all] + [v for k, v in spools.items() if k != (1, i)])
        w = max((bs.translate((0, dy, dz)) ^ obs).volume() for dy, dz in path)
        best = w if best is None else min(best, w)
    print(f'  back spool slot {i+1} over a front spool still in place: min worst overlap {best:.1f} mm3 (blocked if > 0)')

# 5) fan and heater bodies fit their mounts
fan = box(FAN_X - 40, FAN_X + 40, PL_Y0 + PW_, PL_Y0 + PW_ + 25, FAN_Z - 40, FAN_Z + 40)
hz0 = FAN_Z - HEATER[1]/2
heater = box(FAN_X - HEATER[0]/2, FAN_X + HEATER[0]/2, HD_Y1 - HEATER_BACK_GAP - HEATER[2], HD_Y1 - HEATER_BACK_GAP, hz0, hz0 + HEATER[1])
for n, env in (('fan 80x80x25', fan), ('PTC heater', heater)):
    print(f'{n:14s} clashes: ' + str({k: round((env ^ m).volume(), 2) for k, m in inner.items() if (env ^ m).volume() > 0.01} or 'none'))
print('heater sits on PTFE pads on its ledges:', all((box(x - 1, x + 1, HD_Y1 - HEATER_BACK_GAP - 15, HD_Y1 - HEATER_BACK_GAP - 14, hz0 - HEATER_PAD - 0.5, hz0 - HEATER_PAD - 0.1) ^ inner['heater_duct']).volume() > 0 for x in (HD_X0 + DW + 2, HD_X1 - DW - 2)))
