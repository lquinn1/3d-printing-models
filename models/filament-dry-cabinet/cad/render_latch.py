# SPDX-License-Identifier: MIT
"""Lift-bar latch renders:
  cad_latch_closed.jpg / cad_latch_open.jpg   outside, bar flush / bar pulled
  cad_latch_hidden.jpg                        door ajar: the hook behind the door and the keeper
  cad_latch_section.jpg                       5-step section storyboard (labelled)
  cad_latch_cycle.gif                         the same section, animated through a full cycle
"""
import os, sys, math, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source', 'render'))
import numpy as np, trimesh, manifold3d as mf
from PIL import Image, ImageDraw, ImageFont
from scene import render, hexc, box as sbox
from tiles import make_tiles, W
from front import parts_world, keeper_pin, KEEPER_PIN, cyl_x, cyl_y, MAGNET_D, MAGNET_H
from door import *

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def tm(m):
    o = m.to_mesh(); return trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts, process=False)

CLIP = box(470, W + 40, -120, 60, 60, 320)
tiles = [t.build(simple=True).transform(t.M()[:3]) for t in make_tiles()]
TILE = mf.Manifold.batch_boolean([t for t in tiles], mf.OpType.Add) ^ CLIP
FR_PARTS = {n: m ^ CLIP for n, m in parts_world().items() if (m ^ CLIP).volume() > 1}
mv = moving_parts()
BAR = mv.pop('latch_bar')
DOOR = mf.Manifold.batch_boolean(list(mv.values()), mf.OpType.Add) ^ CLIP
PIN = keeper_pin()
py, pz = PIV
PIVOT_SCREW = cyl_x(py, pz, DX1 - 25.0, DX1, 1.5, n=32)
BAR_MAG = cyl_y(BAR_MAG_X, BAR_MAG_Z, BAR_Y1 - 3.0, BAR_Y1, 5.0, n=48)
DOOR_MAG = cyl_y(BAR_MAG_X, BAR_MAG_Z, REC_Y1, REC_Y1 + 3.0, 5.0, n=48)
C = dict(door=hexc('#4a5361'), bar=hexc('#e8833a'), frame=hexc('#b9bcc2'), tile=hexc('#3b82c4'),
         pin=hexc('#d4a72c'), steel=hexc('#8c939c'), mag=hexc('#5b6470'), seal=hexc('#4caf50'),
         floor=hexc('#d8d4cc'))

def seal(d):
    """The door seal on the frame face (x 507.4..516.4), squeezed by the door's back face."""
    return box(507.4, 516.4, max(11.0, DY1 - d), 14.0, 40, 300)

def scene(d, a, cut=None):
    """Door pulled forward by d mm (small-angle stand-in for the swing), bar turned a degrees."""
    mv_ = lambda m: m.translate((0, -d, 0))
    items = [(TILE, C['tile'])] + [(m, C['frame']) for m in FR_PARTS.values()] + [(PIN, C['pin']), (seal(d), C['seal'])]
    items += [(mv_(DOOR), C['door']), (mv_(bar_turn(BAR, a)), C['bar']), (mv_(PIVOT_SCREW), C['steel']),
              (mv_(bar_turn(BAR_MAG, a)), C['mag']), (mv_(DOOR_MAG), C['mag'])]
    if cut is not None:
        k = box(0, cut, -200, 200, 0, 400)
        items = [(m ^ k, c) for m, c in items]
    return [(tm(m), c) for m, c in items if m.volume() > 1e-3]

def camera(eye, target, fov, Wd, Hd):
    eye, target = np.array(eye, float), np.array(target, float)
    fwd = target - eye; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 0, 1]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    f = (Hd/2)/math.tan(math.radians(fov/2))
    def proj(p):
        dd = np.array(p, float) - eye
        return Wd/2 + f*(dd@right)/(dd@fwd), Hd/2 - f*(dd@up)/(dd@fwd)
    return proj

def need_angle(d):
    if (BAR.translate((0, -d, 0)) ^ PIN).volume() < 1e-4: return 0.0
    return next(a for a in np.arange(0, -33, -0.25) if (bar_turn(BAR, a).translate((0, -d, 0)) ^ PIN).volume() < 1e-4)

def contact_angle(d):
    """Door short by d: the angle at which the bar, pushed back toward flush, first meets the pin."""
    for a in np.arange(-25, 0.01, 0.25):
        if (bar_turn(BAR, a).translate((0, -d, 0)) ^ PIN).volume() > 1e-4: return a - 0.25
    return 0.0

floor = sbox(-1500, 2000, -1500, 2000, -1, 0)
if __name__ == '__main__':
    # ---------------------------------------------------------------- outside views (full cabinet)
    TILE_F = mf.Manifold.batch_boolean(tiles, mf.OpType.Add)
    FRAME_F = list(parts_world().values())
    fullmv = moving_parts(); FBAR = fullmv.pop('latch_bar')
    FDOOR = mf.Manifold.batch_boolean(list(fullmv.values()), mf.OpType.Add)
    def outside(deg, a):
        sw = lambda m: swing(m, deg)
        items = [(TILE_F, C['tile'])] + [(m, C['frame']) for m in FRAME_F] + [(PIN, C['pin'])]
        if deg: items.append((seal(5), C['seal']))
        items += [(sw(FDOOR), C['door']), (sw(bar_turn(FBAR, a)), C['bar']), (sw(PIVOT_SCREW), C['steel'])]
        return [(floor, C['floor'])] + [(tm(m), c) for m, c in items]
    def panes(deg):
        out = []
        for a_, b_ in SLOTS_T:
            x0 = XL1 - SLOT_DEPTH + PANE_CLR; z0 = ZB1 - SLOT_DEPTH + PANE_CLR; yc = DY0 + (a_ + b_)/2
            out.append(tm(swing(box(x0, x0 + PANE[0], yc - 1.18, yc + 1.18, z0, z0 + PANE[1]), deg)))
        return out
    for a, name in ((0, 'cad_latch_closed.jpg'), (-22, 'cad_latch_open.jpg')):
        render(outside(0, a), panes(0), [], os.path.join(IMG, name),
               eye=(820, -420, 360), target=(505, 0, 200), fov=30, W=1100, H=900)
    # door ajar: the hook sticking out behind the door, and the keeper pocket + pin in the frame
    render(outside(9, 0), panes(9), [], os.path.join(IMG, 'cad_latch_hidden.jpg'),
           eye=(780, -150, 330), target=(515, -20, 248), fov=20, W=1100, H=900)

    # ---------------------------------------------------------------- section storyboard
    CUT = (ARM_X[0] + ARM_X[1]) / 2                     # through the hook, the pin and the magnets
    SEC = dict(eye=(W + 3000, -14, 190), target=(W, -14, 190), fov=3.9, W=560, H=1000)
    SEC_KEY = dict(key=(0.8, -0.35, 0.5))
    ZOOM = dict(y=(-4.0, 30.0), z=(235.0, 264.0))
    ZOOM.update(eye=(W + 3000, sum(ZOOM['y'])/2, sum(ZOOM['z'])/2), target=(W, sum(ZOOM['y'])/2, sum(ZOOM['z'])/2),
                fov=2*math.degrees(math.atan((ZOOM['z'][1] - ZOOM['z'][0])/2/3000)), W=300, H=256)
    proj = camera(SEC['eye'], SEC['target'], SEC['fov'], SEC['W'], SEC['H'])
    d5, d4 = 1.5, 5.0
    steps = [
        (0, 0, '1  Latched', 'Bar flush, hanging from its pivot.\nThe hook tip sits behind the pin.\nA magnet pair holds the bar.'),
        (0, -18, '2  Pull the bar', 'Pull the bottom forward ~40 mm.\nThe hook turns down and\ndrops clear of the pin (18 deg).'),
        (12, -22, '3  Door opens', 'Keep pulling: the same\nmotion swings the door open.\nLet go and the bar drops flush.'),
        (d4, need_angle(d4), '4  Push it shut', 'The pin rides up the chamfer\non the back of the hook and\nflicks the bar out a little.'),
        (d5, contact_angle(d5), '5  Click and draw in', 'The tip drops behind the pin.\nPress the bar flush: its ramp\npulls the door 1.5-2 mm onto the seal.'),
    ]
    panels = []
    tmp = tempfile.mkdtemp()
    for i, (d, a, title, text) in enumerate(steps):
        im = render(scene(d, a, CUT), [], [], os.path.join(tmp, f's{i}.png'), eye=SEC['eye'], target=SEC['target'],
                    fov=SEC['fov'], W=SEC['W'], H=SEC['H'], bg_top='#f4f2ee', bg_bot='#e4e0d8', **SEC_KEY).convert('RGB')
        # zoomed inset of the hook and pin
        zi = render(scene(d, a, CUT), [], [], os.path.join(tmp, f'z{i}.png'), eye=ZOOM['eye'], target=ZOOM['target'],
                    fov=ZOOM['fov'], W=ZOOM['W'], H=ZOOM['H'], bg_top='#f4f2ee', bg_bot='#e4e0d8', **SEC_KEY).convert('RGB')
        dr = ImageDraw.Draw(im)
        lab = ImageFont.truetype(FR, 17)
        def tag(p, txt, dx, dy, pr=proj, d_=dr):
            x, y = pr(p); x2, y2 = x + dx, y + dy
            d_.line([(x, y), (x2, y2)], fill=(40, 40, 40), width=2); d_.ellipse([x-3, y-3, x+3, y+3], fill=(40, 40, 40))
            d_.text((x2 + (4 if dx > 0 else -4), y2), txt, font=lab, fill=(20, 20, 20), anchor='lm' if dx > 0 else 'rm')
        # where the inset comes from
        (ax0, ay0), (ax1, ay1) = proj((CUT, ZOOM['y'][0], ZOOM['z'][1])), proj((CUT, ZOOM['y'][1], ZOOM['z'][0]))
        dr.rectangle([ax0, ay0, ax1, ay1], outline=(200, 40, 40), width=2)
        zd = ImageDraw.Draw(zi)
        if i == 0:
            ky, kz = KEEPER_PIN
            zp = camera(ZOOM['eye'], ZOOM['target'], ZOOM['fov'], ZOOM['W'], ZOOM['H'])
            yf = ky + KEEPER_PIN_R
            tag((CUT, ky, kz + 1.2), 'pin', -70, -50, zp, zd)
            tag((CUT, yf + 0.3, kz + 2.0), 'draw ramp', -10, -70, zp, zd)
            tag((CUT, yf + 4.7, kz + 0.5), 'chamfer', -10, 80, zp, zd)
            tag((CUT, 12, ARM_Z0 + 1), 'hook arm', -40, 50, zp, zd)
        zd.rectangle([0, 0, ZOOM['W'] - 1, ZOOM['H'] - 1], outline=(200, 40, 40), width=3)
        im.paste(zi, (12, 10))
        if i == 0:
            tag((CUT, -0.5, 185), 'lift-bar', -40, 0)
            tag((CUT, py, pz - 1), 'pivot', -40, 60)
            tag((CUT, 8, 110), 'door', -110, -20)
            tag((CUT, 20, 100), 'frame', -160, 20)
            tag((CUT, 6.5, BAR_MAG_Z), 'magnets', -120, 40)
            tag((CUT, 40, 175), 'wall', -1, 60)
        if i == 4:
            tag((CUT, 12.5, 140), 'seal', 50, 0)
        panels.append((im, title, text))
    pw, ph = SEC['W'], SEC['H']
    head, foot_ = 70, 120
    sheet = Image.new('RGB', (pw*3, (ph + head + foot_)*2), (250, 249, 246))
    dr = ImageDraw.Draw(sheet)
    ft, fb = ImageFont.truetype(FB, 30), ImageFont.truetype(FR, 21)
    for i, (im, title, text) in enumerate(panels):
        cx, cy = (i % 3)*pw, (i // 3)*(ph + head + foot_)
        sheet.paste(im, (cx, cy + head))
        dr.text((cx + 24, cy + 22), title, font=ft, fill=(30, 30, 30))
        dr.multiline_text((cx + 24, cy + head + ph + 10), text, font=fb, fill=(60, 60, 60), spacing=6)
    # legend in the 6th cell
    lx, ly = 2*pw + 40, ph + head + foot_ + head + 40
    dr.text((lx, ly - 50), 'Section through the hook (x = %.1f),' % CUT, font=fb, fill=(60, 60, 60))
    dr.text((lx, ly - 22), 'seen from the right side', font=fb, fill=(60, 60, 60))
    for j, (k, name) in enumerate((('bar', 'lift-bar + hook (printed)'), ('door', 'door stile'), ('frame', 'frame stile'),
                                   ('tile', 'side wall tile'), ('pin', 'keeper pin (M3 x 16 flat head)'),
                                   ('steel', 'pivot screw (M3 x 25 flat head)'), ('mag', '10 x 3 mm magnets'),
                                   ('seal', 'door seal (behind the cut)'))):
        y = ly + 30 + j*44
        dr.rectangle([lx, y, lx + 30, y + 30], fill=tuple(int(255*v) for v in C[k]), outline=(80, 80, 80))
        dr.text((lx + 44, y + 15), name, font=fb, fill=(40, 40, 40), anchor='lm')
    dr.multiline_text((lx, ly + 30 + 8*44 + 30),
                      'Releases at 18 deg of bar travel.\nThe bar stops at 33 deg.\nDraws the door in for gaps\nup to 2 mm (checked).',
                      font=fb, fill=(60, 60, 60), spacing=6)
    sheet.save(os.path.join(IMG, 'cad_latch_section.jpg'), quality=90)

    # ---------------------------------------------------------------- animated cycle
    seq = []
    seq += [(0, 0, 'Latched: bar flush')]*5
    seq += [(0, a, 'Pull the bar: the hook drops') for a in np.linspace(0, -20, 8)]
    seq += [(dd, -20 - 2*dd/12, 'Keep pulling: door opens') for dd in np.linspace(0.5, 12, 8)]
    seq += [(12, a, 'Let go: the bar drops flush') for a in np.linspace(-22, 0, 5)]
    seq += [(12, 0, 'Let go: the bar drops flush')]*3
    seq += [(dd, need_angle(dd), 'Push shut: the pin rides the chamfer') for dd in np.linspace(11, 1.75, 12)]
    seq += [(dd, contact_angle(dd) if dd > 0 else 0, 'Press the bar flush: door drawn in') for dd in np.linspace(1.5, 0, 6)]
    seq += [(0, 0, 'Latched: bar flush')]*6
    GW, GH, CAP = 420, 750, 56
    gfont = ImageFont.truetype(FB, 19)
    frames, durs = [], []
    for k, (dd, a, cap) in enumerate(seq):
        im = render(scene(dd, a, CUT), [], [], os.path.join(tmp, 'f.png'), eye=SEC['eye'], target=SEC['target'],
                    fov=SEC['fov'], W=GW, H=GH, ss=1, bg_top='#f4f2ee', bg_bot='#e4e0d8', **SEC_KEY).convert('RGB')
        fr = Image.new('RGB', (GW, GH + CAP), (250, 249, 246)); fr.paste(im, (0, CAP))
        ImageDraw.Draw(fr).text((14, CAP/2), cap, font=gfont, fill=(30, 30, 30), anchor='lm')
        frames.append(fr.convert('P', palette=Image.ADAPTIVE, colors=96))
        last = k + 1 == len(seq) or seq[k + 1][2] != cap
        durs.append(900 if last else 110)
    frames[0].save(os.path.join(IMG, 'cad_latch_cycle.gif'), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, optimize=True)
    print('ok', len(frames), 'frames')
