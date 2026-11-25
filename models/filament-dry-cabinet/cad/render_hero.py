# SPDX-License-Identifier: MIT
"""Presentation renders built from the CAD, in finished colours (charcoal shell, dark frame):
  render_front.jpg   front 3/4, door closed, loaded with 12 spools, the screen showing the label page
  render_rear.jpg    rear 3/4: control pod, IEC inlet, back ports and the two cable glands
  render_stack.jpg   a PLA cabinet with a PETG cabinet stacked on it (feet in the roof pockets)
Engineering-colour views of the same parts are in render_tiles/door/front/pod/interior/latch.py.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source', 'render'))
import numpy as np, trimesh, manifold3d as mf
from scene import render, hexc, box as sbox
from tiles import make_tiles, SOCKETS, GLANDS, POCKET_XY, foot, cradle_world, Y1
from coupons import port_module
from front import parts_world as front_parts, tft_geometry, FAS, TFT_GAP, ENC_X, ZC, cyl_y
import interior as I
import pod as P
from door import moving_parts, fixed_hinges, SLOTS_T, XL1, SLOT_DEPTH, PANE_CLR, ZB1, DY0, PANE, box

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')
def tm(m):
    o = m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts, process=False)

SHELL, FRAME, DOOR, BAR, PART = hexc('#2e3136'), hexc('#1b1c1f'), hexc('#2b2d31'), hexc('#e8833a'), hexc('#3a3e44')
STEEL = hexc('#9aa0a6')
tiles = [t.build(simple=True).transform(t.M()[:3]) for t in make_tiles()]
TILE = tm(mf.Manifold.batch_boolean(tiles, mf.OpType.Add))
Z0 = min(TILE.vertices[:, 2]); Z1 = max(TILE.vertices[:, 2])
FEET = [tm(foot().mirror((0, 0, 1)).translate((x, y, Z0))) for x, y in POCKET_XY]
plug, gland = port_module('plug'), port_module('gland')

def ports():
    out = []
    for face, p in SOCKETS:
        g = face == 'BACK' and any(abs(p[0] - gx) < 1 and abs(p[2] - gz) < 1 for gx, gz in GLANDS)
        M = np.array([[1, 0, 0, p[0]], [0, 0, -1, Y1], [0, 1, 0, p[2]]] if face == 'BACK' else
                     [[1, 0, 0, p[0]], [0, 1, 0, p[1]], [0, 0, -1, p[2]]], float)
        nudge = (0, 0.4, 0) if face == 'BACK' else (0, 0, 0.4)     # render only: lift the flush flange off the tile face
        out.append(tm((gland if g else plug).transform(M).translate(nudge)))
    return out
PORTS = ports()

pw = P.parts_world()
yc, zc = P.IEC_C
POD = [(tm(pw['pod_base']), PART), (tm(pw['pod_cover']), PART),
       (tm(box(P.PX1 - P.IEC_PANEL - 40, P.PX1 + 6, yc - 14, yc + 14, zc - 24, zc + 24)), hexc('#111111'))]

INSIDE = [(tm(m), hexc('#3a3d42') if 'duct' in n or 'plenum' in n else hexc('#ececec')) for n, m in I.parts_world().items()]
INSIDE += [(tm(cradle_world(s, k)), PART) for s in 'LR' for k in range(4)]
for k in range(4):
    INSIDE.append((tm(I.rod(k)), hexc('#d8bf8f')))     # poplar dowel
    INSIDE += [(tm(c), hexc('#b9bec4')) for c in I.collars(k)]
ORANGE = hexc('#e8833a')
FRONT_PARTS = [(tm(m), ORANGE if n in ('tft_bezel', 'nfc_tap_overlay', 'encoder_knob') else hexc('#f1f1ee') if 'led' in n else FRAME) for n, m in front_parts().items()]
HINGES = [(tm(m), STEEL) for m in fixed_hinges().values()]

(wx, wz), _, _, _ = tft_geometry()
YL = FAS + TFT_GAP
def screen(band, name, rh):
    """The TFT label page: colour band (top 69 %), status line below, as dark glass in the bezel."""
    zb = wz + 24.8 - 49.6*220/320
    items = [(tm(box(wx - 37, wx + 37, YL, YL + 4, wz - 24.8, wz + 24.8)), hexc('#1b1e23')),
             (tm(box(wx - 37, wx + 37, YL - 0.05, YL + 0.2, zb, wz + 24.8)), hexc(band))]
    labels = [((wx, YL - 1.5, wz + 24.8 - 49.6*110/320), name, 'lblname'),
              ((wx, YL - 1.5, wz + 24.8 - 49.6*270/320), f'47.8°C   {rh}%        Maintain', 'lblstat')]
    return items, labels
KNOB = []   # encoder_knob is a printed part now (in FRONT_PARTS)

def door_and_glass():
    mv = moving_parts()
    d = [(tm(m), BAR if 'latch' in n else STEEL if 'hinge' in n else DOOR) for n, m in mv.items()]
    panes = []
    for a, b in SLOTS_T:
        x0 = XL1 - SLOT_DEPTH + PANE_CLR; z0 = ZB1 - SLOT_DEPTH + PANE_CLR; y = DY0 + (a + b)/2
        panes.append(tm(box(x0, x0 + PANE[0], y - 1.18, y + 1.18, z0, z0 + PANE[1])))
    return d, panes
DOOR_ITEMS, PANES = door_and_glass()

PETG = ['#f1f1ee', '#2f2f2f', '#d62828', '#2d7dd2', '#4caf2a', '#f2b705', '#8d99ae', '#ff7a1a', '#7b4fd6', '#e84393', '#11a3a3', '#f1f1ee']
PLA = ['#e9e4d8', '#111111', '#c1121f', '#1d4ed8', '#16a34a', '#facc15', '#6b7280', '#ea580c', '#9333ea', '#db2777', '#0d9488', '#a16207']
def spools(cols):
    out = []
    for row in (0, 1):
        for i in range(6):
            s = I.spool(row, i)
            out.append((tm(s), hexc(cols[row*6 + i])))
            hub = I.cyl(28, -I.SPOOL_W/2 - 0.5, I.SPOOL_W/2 + 0.5, n=32)
            c = np.array(s.bounding_box()).reshape(2, 3).mean(0)
            out.append((tm(hub.transform(np.array([[0, 0, 1, c[0]], [1, 0, 0, c[1]], [0, 1, 0, c[2]]], float))), hexc('#d0d0d0')))
    return out

def cabinet(dz=0.0, band='#1c6dd0', name='PETG', rh=18, cols=PETG):
    sc, lab = screen(band, name, rh)
    items = [(TILE, SHELL)] + [(f, hexc('#141414')) for f in FEET] + [(p, hexc('#e8833a')) for p in PORTS] + POD + FRONT_PARTS + HINGES + \
            KNOB + INSIDE + spools(cols) + DOOR_ITEMS + sc
    items = [(m.copy().apply_translation((0, 0, dz)), c) for m, c in items]
    glass = [g.copy().apply_translation((0, 0, dz)) for g in PANES]
    lab = [((p[0], p[1], p[2] + dz), t, k) for p, t, k in lab]
    return items, glass, lab

floor = lambda z: (sbox(-700, 1250, -900, 1350, z - 1, z), hexc('#bdb6aa'))
FZ = Z0 - 10.0
if __name__ == '__main__':
    it, gl, lab = cabinet()
    render([floor(FZ)] + it, gl, lab, os.path.join(IMG, 'render_front.jpg'), eye=(-560, -1200, 780), target=(265, 180, 230), fov=30, W=1500, H=1150)
    render([floor(FZ)] + it, gl, lab, os.path.join(IMG, 'render_rear.jpg'), eye=(1200, 1550, 760), target=(265, 280, 220), fov=30, W=1500, H=1150, key=(0.55, 0.7, 0.55))
    a, ga, la = cabinet(0, '#2e9e44', 'PLA', 12, PLA)
    b, gb, lb = cabinet(Z1 - Z0, '#1c6dd0', 'PETG', 18, PETG)
    render([floor(FZ)] + a + b, ga + gb, la + lb, os.path.join(IMG, 'render_stack.jpg'), eye=(1350, -1700, 1200), target=(265, 200, 470), fov=34, W=1500, H=1500)
    print('ok')
