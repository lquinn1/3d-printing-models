# SPDX-License-Identifier: MIT
"""Lift-bar latch fit-test coupon.

Short sections of the real door stile and frame stile around the latch, cut straight from
door.py / front.py so every hole, pocket and clearance is the production geometry:

  coupon_latch_door    right door stile, z 96..262: bar recess, finger scoop, pivot, arm slot,
                       click-magnet pocket. Slides front-to-back between the base's rails.
  coupon_latch_frame   right frame stile, z 96..262 (keeper pocket + pin hole, seal face),
                       standing on a base plate with two guide rails for the door section.
  latch_bar            the production bar (cad/stl/latch_bar.stl), unchanged.

Hardware: M3 x 25 flat head (pivot), M3 x 16 flat head (keeper pin), 2 x 10 x 3 mm magnets,
about 170 mm of the 5 x 3 mm door seal on the frame section's face (x 507.4..516.4 band).

What to try: push the door section in (it should click and latch on its own); press the bar
flush (the door section creeps 1.5-2 mm further onto the seal); pull the bar's bottom end
(the hook lets go at about 40 mm of travel and the door section comes forward with it).

Run: python3 cad/latch_coupon.py   (writes the STLs, checks the fit, renders images/cad_latch_coupon.jpg)
"""
import os, sys
import numpy as np, manifold3d as mf
from coupons import save
from door import (door_parts, latch_bar, bar_turn, DY0, DY1, XR0, DX1, FACE_DOWN)
from front import stile, keeper_pin, W, F_Y0, F_Y1

Z0, Z1 = 96.0, 262.0               # section height: the whole bar, scoop and keeper
BASE_T = 8.0
RAIL_H, RAIL_CLR = 15.0, 0.5
BASE_X = (XR0 - 6.5, W + 6.5)
BASE_Y = (DY0 - 44.0, F_Y1 + 4.0)

def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))

def door_section():
    return door_parts()['door_stile_right'] ^ box(XR0 - 1, DX1 + 1, DY0 - 1, DY1 + 1, Z0, Z1)

def frame_section():
    """The frame stile section on its base plate, with rails either side of the door section."""
    m = stile('R') ^ box(XR0, W + 1, F_Y0 - 1, F_Y1 + 1, Z0, Z1)
    m += box(BASE_X[0], BASE_X[1], BASE_Y[0], BASE_Y[1], Z0 - BASE_T, Z0)
    m += box(BASE_X[0], XR0 - RAIL_CLR, BASE_Y[0], DY1 + 0.5, Z0, Z0 + RAIL_H)           # left rail
    m += box(DX1 + RAIL_CLR, BASE_X[1], BASE_Y[0], F_Y0 - 0.5, Z0, Z0 + RAIL_H)          # right rail
    # label on the base: which way is the front
    return m

def check():
    D, F, B, P = door_section(), frame_section(), latch_bar(), keeper_pin()
    ok = lambda v: v < 1e-3
    r = {}
    r['door vs frame/base, closed'] = ok((D ^ F).volume())
    r['bar vs door, closed'] = ok((B ^ D).volume())
    r['bar vs frame, closed'] = ok((B ^ F).volume())
    r['hook touches the pin'] = (B ^ P.translate((0, 0.15, 0))).volume() > 1e-4
    r['door slides forward 40 mm clear of the rails'] = all(ok((D.translate((0, -t, 0)) ^ F).volume()) for t in range(1, 41, 3))
    sweep = mf.Manifold.batch_boolean([bar_turn(B, -18).translate((0, -t, 0)) for t in np.arange(0, 15.1, 0.5)], mf.OpType.Add)
    r['bar at 18 deg releases'] = ok((sweep ^ (P + F)).volume())
    r['bar swings to 30 deg clear of the base'] = all(ok((bar_turn(B, -a) ^ F).volume()) for a in range(0, 31, 3))
    for k, v in r.items(): print(f'  {k}: {v}')
    assert all(r.values())

if __name__ == '__main__':
    check()
    d = door_section().transform(FACE_DOWN)
    b = d.bounding_box(); save(d.translate((-(b[0]+b[3])/2, -(b[1]+b[4])/2, -b[2])), 'coupon_latch_door')
    f = frame_section()
    b = f.bounding_box(); save(f.translate((-(b[0]+b[3])/2, -(b[1]+b[4])/2, -b[2])), 'coupon_latch_frame')
    # ---------------------------------------------------------------- render
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source', 'render'))
    import trimesh
    from scene import render, hexc, box as sbox
    from render_latch import C, PIVOT_SCREW, BAR_MAG, DOOR_MAG
    tm = lambda m: trimesh.Trimesh(m.to_mesh().vert_properties[:, :3], m.to_mesh().tri_verts, process=False)
    IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')
    seal = box(507.4, 516.4, 11.0, F_Y0, Z0, Z1)
    def scene_(t, a):
        mv = lambda m: bar_turn(m, a).translate((0, -t, 0))
        return [(sbox(-2000, 3000, -2000, 3000, Z0 - BASE_T - 1, Z0 - BASE_T), C['floor']),
                (tm(frame_section()), C['frame']), (tm(keeper_pin()), C['pin']), (tm(seal), C['seal']),
                (tm(door_section().translate((0, -t, 0))), C['door']), (tm(mv(latch_bar())), C['bar']),
                (tm(PIVOT_SCREW.translate((0, -t, 0))), C['steel'])]
    from PIL import Image
    ims = [render(scene_(t, a), [], [], '/tmp/lc.png', eye=(760, -330, 330), target=(515, 0, 175),
                  fov=26, W=800, H=900).convert('RGB') for t, a in ((0, 0), (25, -22))]
    sheet = Image.new('RGB', (1600, 900)); sheet.paste(ims[0], (0, 0)); sheet.paste(ims[1], (800, 0))
    sheet.save(os.path.join(IMG, 'cad_latch_coupon.jpg'), quality=90)
