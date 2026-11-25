import os, sys, json, numpy as np, trimesh
sys.path.insert(0, '/home/claude/3d-printing-models/models/filament-dry-cabinet/cad')
os.chdir('/home/claude/3d-printing-models/models/filament-dry-cabinet/cad')
import render_hero as H
import interior as I

OUT = '/tmp/scene/ply'
groups = {}
def add(key, m): groups.setdefault(key, []).append(m)
add('shell', H.TILE)
for f in H.FEET: add('rubber', f)
for p in H.PORTS: add('orange', p)
pw = H.P.parts_world()
add('shell', H.tm(pw['pod_base'])); add('shell', H.tm(pw['pod_cover']))
import front as F
for n, m in F.parts_world().items():
    key = 'orange' if n in ('tft_bezel', 'nfc_tap_overlay', 'encoder_knob') else 'led' if 'led' in n else 'frame'
    add(key, H.tm(m))
for m, c in H.HINGES: add('steel', m)
from tiles import cradle_world
for s in 'LR':
    for k in range(4): add('part', H.tm(cradle_world(s, k)))
for n, m in I.parts_world().items():
    add('part_dark' if ('duct' in n or 'plenum' in n) else 'part_light', H.tm(m))
for k in range(4):
    add('wood', H.tm(I.rod(k)))
    for c in I.collars(k): add('collar', H.tm(c))
for (m, c), n in zip(H.DOOR_ITEMS, H.moving_parts().keys()):
    add('orange' if 'latch' in n else 'steel' if 'hinge' in n else 'frame', m)
for g in H.PANES: add('glass', g)
for k, ms in groups.items():
    trimesh.util.concatenate(ms).export(f'{OUT}/{k}.ply')
# spools: centre, width, axis x
sp = []
for row in (0, 1):
    for i in range(6):
        b = np.array(I.spool(row, i).bounding_box()).reshape(2, 3)
        sp.append(dict(row=row, i=i, c=b.mean(0).tolist(), size=(b[1]-b[0]).tolist()))
(wx, wz), _, _, _ = F.tft_geometry()
info = dict(spools=sp, tft=dict(x=wx, z=wz, y=F.FAS + F.TFT_GAP, w=74.0, h=49.6),
            bbox=[float(v) for v in (H.TILE.bounds.reshape(-1))], Z0=float(H.Z0), Z1=float(H.Z1))
json.dump(info, open('/tmp/scene/info.json', 'w'), indent=1)
print({k: len(v) for k, v in groups.items()}, info['bbox'])
