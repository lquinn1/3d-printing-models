"""Build a simple 3D scene of the dry cabinet from the spec numbers and render it
with a small perspective z-buffer renderer (opaque pass + tinted glass pass)."""
import sys, math, numpy as np, trimesh
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # source/layout.py
from layout import stadium, ROD_OD, ROD_CC, PITCH, WALL, DOOR, FEET
from PIL import Image, ImageDraw, ImageFont, ImageFilter

A = stadium(6, 120)
IW, ID, IH = A['iw'], A['idepth'], A['ih']
T = WALL; HEADER = 60.0
X0, X1 = -T, IW + T                 # exterior x
YF, YB = -DOOR, ID + T              # exterior y (front of door .. back)
ZB, ZT = -T, IH + T                 # exterior z (bottom of shell .. top)

def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[x1-x0, y1-y0, z1-z0])
    b.apply_translation([(x0+x1)/2, (y0+y1)/2, (z0+z1)/2]); return b
def cyl_x(x0, x1, y, z, r, sec=48):
    c = trimesh.creation.cylinder(radius=r, height=x1-x0, sections=sec)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0, 1, 0]))
    c.apply_translation([(x0+x1)/2, y, z]); return c
def cyl_z(x, y, z0, z1, r, sec=32):
    c = trimesh.creation.cylinder(radius=r, height=z1-z0, sections=sec); c.apply_translation([x, y, (z0+z1)/2]); return c
def cyl_y(x, y0, y1, z, r, sec=32):
    c = trimesh.creation.cylinder(radius=r, height=y1-y0, sections=sec)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [1, 0, 0]))
    c.apply_translation([x, (y0+y1)/2, z]); return c

def hexc(s):
    s = s.lstrip('#'); return tuple(int(s[i:i+2], 16)/255 for i in (0, 2, 4))

SHELL = hexc('#2a2b2e'); SEAM = hexc('#121214'); FRAME = hexc('#1d1e20')
SPOOL_COLS = ['#f2b705', '#4caf2a', '#d62828', '#7b4fd6', '#f1f1ee', '#2d7dd2',
              '#ff7a1a', '#11a3a3', '#e84393', '#8d99ae', '#f1f1ee', '#2f2f2f']

def cabinet(ox=0, oz=0, material='PETG', spool_cols=SPOOL_COLS, ports_open=(2, 9)):
    """Returns (opaque list of (mesh, rgb)), glass list, labels list of (xyz, text, kind)."""
    op, gl, labels = [], [], []
    def add(m, c):
        m = m.copy(); m.apply_translation([ox, 0, oz]); op.append((m, c))
    # core (dark, shows through tile seams)
    # dark backing plates behind the tiles (show through the tile seams, keep the interior open)
    add(box(X0+3, X0+5, 0, YB, ZB, ZT), SEAM); add(box(X1-5, X1-3, 0, YB, ZB, ZT), SEAM)
    add(box(X0, X1, 0, YB, ZT-5, ZT-3), SEAM); add(box(X0, X1, YB-5, YB-3, ZB, ZT), SEAM)
    add(box(X0, X1, 0, YB, ZB, ZB+3), SEAM)
    # left/right side tiles 2x2, top tiles 2x2 (2 mm seams)
    g = 2.0
    ys = np.linspace(0, YB, 3); zs = np.linspace(ZB, ZT, 3); xs = np.linspace(X0, X1, 3)
    for i in range(2):
        for j in range(2):
            for xa, xb in ((X0, X0+3), (X1-3, X1)):
                add(box(xa, xb, ys[i]+g/2, ys[i+1]-g/2, zs[j]+g/2, zs[j+1]-g/2), SHELL)
            add(box(xs[i]+g/2, xs[i+1]-g/2, ys[j]+g/2, ys[j+1]-g/2, ZT-3, ZT), SHELL)
    # corner posts (front vertical edges) and front frame
    for xa, xb in ((X0, X0+T), (X1-T, X1)):
        add(box(xa, xb, -1, 12, ZB, ZT), FRAME)
    # feet (stacking)
    for fx in (X0+20, X1-70):
        for fy in (10, YB-70):
            add(box(fx, fx+50, fy, fy+50, ZB-FEET, ZB), hexc('#141414'))
    # stacking pockets on the roof (darker recess)
    for fx in (X0+20, X1-70):
        for fy in (10, YB-70):
            add(box(fx, fx+50, fy, fy+50, ZT, ZT+0.6), hexc('#0c0c0c'))
    # top PTFE port modules: 12 (front row y=115, back row y=284)
    for i in range(6):
        xc = 10 + PITCH*(i+0.5)
        for k, yp in enumerate((A['y_front'], A['y_back'])):
            idx = k*6 + i
            add(cyl_z(xc, yp, ZT, ZT+4, 11), hexc('#232427'))
            if idx in ports_open:      # PTFE pass-through: coupler + tube going up
                add(cyl_z(xc, yp, ZT+4, ZT+14, 6), hexc('#d9d9d9'))
                add(cyl_z(xc, yp, ZT+14, ZT+80, 2.1, 16), hexc('#f4f4f4'))
            else:                      # blank plug
                add(cyl_z(xc, yp, ZT+4, ZT+7, 9), hexc('#3a3b3f'))
    # rear control pod with IEC C14 fused/switched inlet and vents
    pz0, pz1 = 30, 260
    add(box(70, 430, YB, YB+50, pz0, pz1), hexc('#232427'))
    add(box(300, 350, YB+50, YB+51, 150, 222), hexc('#0b0b0c'))                 # inlet module body
    add(box(306, 344, YB+51, YB+52, 190, 216), hexc('#1a1a1a'))                 # C14 socket
    add(box(306, 344, YB+51, YB+53, 160, 180), hexc('#b5121b'))                 # rocker switch
    add(box(312, 338, YB+51, YB+52.5, 154, 158), hexc('#444444'))                  # fuse drawer
    for k in range(9):                                                         # PSU vents
        add(box(95+k*18, 103+k*18, YB+50, YB+51, 80, 230), hexc('#0d0d0e'))
    labels.append(((325+ox, YB+53, 236+oz), '120V  3.15A T', 'rear'))
    # back PTFE ports: two staggered rows of 6 above the pod
    for i in range(6):
        xc = 10 + PITCH*(i+0.5)
        for k, zp in enumerate((IH-62, IH-36)):
            xx = xc + (-14 if k == 0 else 14)
            add(cyl_y(xx, YB, YB+4, zp, 11), hexc('#232427'))
            if (k*6+i) == 4:
                add(cyl_y(xx, YB+4, YB+14, zp, 6), hexc('#d9d9d9'))
                add(cyl_y(xx, YB+14, YB+120, zp, 2.1, 16), hexc('#f4f4f4'))
            else:
                add(cyl_y(xx, YB+4, YB+7, zp, 9), hexc('#3a3b3f'))
    # side link plates (stacking) - small plate near the top of each side
    add(box(X0-2, X0, 140, 260, ZT-30, ZT), hexc('#1b1c1f')); add(box(X1, X1+2, 140, 260, ZT-30, ZT), hexc('#1b1c1f'))
    # header (60 mm) across the front
    add(box(X0, X1, YF-1, 0, ZT-HEADER, ZT), FRAME)
    # label plate
    add(box(X0+28, X0+228, YF-3, YF-1, ZT-HEADER+10, ZT-10), hexc('#e6e7e9'))
    labels.append(((X0+128+ox, YF-3, ZT-HEADER/2+3+oz), material, 'plate'))
    # NFC tap pad (recessed, purple ring)
    add(box(X0+243, X0+313, YF-1.6, YF-1, ZT-HEADER+6, ZT-6), hexc('#7048e8'))
    add(box(X0+246, X0+310, YF-2.2, YF-1.2, ZT-HEADER+9, ZT-9), hexc('#25262b'))
    labels.append(((X0+278+ox, YF-2.3, ZT-HEADER/2+oz), 'NFC', 'nfc'))
    # display
    add(box(X0+330, X0+392, YF-2.5, YF-1, ZT-HEADER+8, ZT-8), hexc('#050608'))
    labels.append(((X0+361+ox, YF-2.6, ZT-HEADER/2+oz), '45°C\n14%', 'tft'))
    # encoder knob
    add(cyl_y(X0+440, YF-16, YF-1, ZT-HEADER/2, 13), hexc('#9aa0a6'))
    add(cyl_y(X0+440, YF-17, YF-16, ZT-HEADER/2, 11), hexc('#b8bdc2'))
    # door frame (25 mm border) and glass
    dz0, dz1 = ZB, ZT-HEADER-2
    bw = 24
    add(box(X0, X1, YF, YF+DOOR-3, dz0, dz0+bw+8), FRAME)          # bottom rail
    add(box(X0, X1, YF, YF+DOOR-3, dz1-bw, dz1), FRAME)            # top rail
    add(box(X0, X0+bw, YF, YF+DOOR-3, dz0, dz1), FRAME)            # hinge stile
    add(box(X1-bw, X1, YF, YF+DOOR-3, dz0, dz1), FRAME)            # latch stile
    for k in range(6):                                              # slot numbers on bottom rail
        labels.append(((10 + PITCH*(k+0.5)+ox, YF-0.5, dz0+bw/2+4+oz), str(k+1), 'num'))
    # hinges
    for hz in (dz0+50, (dz0+dz1)/2, dz1-50):
        add(cyl_z(X0-2, YF+6, hz-18, hz+18, 4.5), hexc('#111111'))
        add(box(X0-2, X0+10, YF-2, YF+2, hz-18, hz+18), hexc('#111111'))
    # handle
    add(box(X1-bw+4, X1-bw+16, YF-14, YF, (dz0+dz1)/2-45, (dz0+dz1)/2+45), hexc('#111111'))
    # glass (two panes, rendered as one tinted pane)
    g1 = box(X0+bw, X1-bw, YF+8, YF+10, dz0+bw+8, dz1-bw); g1.apply_translation([ox, 0, oz]); gl.append(g1)
    # interior back wall and floor liner (foil-ish)
    add(box(0, IW, ID-1, ID, 0, IH), hexc('#5c5f66'))
    add(box(0, IW, 0, ID, -1, 0), hexc('#4a4d53'))
    add(box(-1, 0, 0, ID, 0, IH), hexc('#53565c')); add(box(IW, IW+1, 0, ID, 0, IH), hexc('#53565c'))
    add(box(0, IW, 0, ID, IH, IH+1), hexc('#3d3f44'))
    # LED strip (warm white glow) under the header
    add(box(4, IW-4, 4, 12, IH-14, IH-10), hexc('#fff3c4'))
    # rods, risers, collars
    for yc, zc in ((A['y_front'], A['rod_front']), (A['y_back'], A['rod_back'])):
        for dy in (-ROD_CC/2, ROD_CC/2):
            add(cyl_x(0, IW, yc+dy, zc, ROD_OD/2), hexc('#f2f2f0'))
        for sx in (0, IW-12):
            add(box(sx, sx+12, yc-ROD_CC/2-22, yc+ROD_CC/2+22, 0, zc-ROD_OD/2+4), hexc('#2a2b2e'))
        for k in range(7):
            xk = 10 + PITCH*k
            for dy in (-ROD_CC/2, ROD_CC/2):
                add(cyl_x(xk-2, xk+2, yc+dy, zc, ROD_OD/2+3, 24), hexc('#3b3c40'))
    # spools
    for row, (yc, cz) in enumerate(((A['y_front'], A['cf']), (A['y_back'], A['cb']))):
        for i in range(6):
            col = hexc(spool_cols[(row*6+i) % len(spool_cols)])
            xc = 10 + PITCH*(i+0.5)
            w = 66
            add(cyl_x(xc-w/2+3, xc+w/2-3, yc, cz, 84), col)                     # filament
            for s in (-1, 1):                                                   # flanges
                add(cyl_x(xc+s*w/2-3*(s>0), xc+s*w/2+3*(s<0), yc, cz, 100, 64), hexc('#101010'))
            add(cyl_x(xc-w/2-0.5, xc+w/2+0.5, yc, cz, 27), hexc('#d9d9d9'))     # hub
    return op, gl, labels

def render(items, glass, labels, out, eye, target, fov=32, W=1500, H=1150, ss=2, bg_top='#e9e6df', bg_bot='#cfcac0', key=(-0.45, -0.75, 0.6)):
    Wr, Hr = W*ss, H*ss
    eye, target = np.array(eye, float), np.array(target, float)
    fwd = target-eye; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 0, 1]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    f = (Hr/2)/math.tan(math.radians(fov/2))
    def proj(P):
        d = P-eye; xc = d@right; yc = d@up; zc = d@fwd
        return Wr/2 + f*xc/zc, Hr/2 - f*yc/zc, zc
    # background gradient
    t = np.linspace(0, 1, Hr)[:, None, None]
    img = (1-t)*np.array(hexc(bg_top)) + t*np.array(hexc(bg_bot)); img = np.repeat(img, Wr, axis=1)
    zb = np.full((Hr, Wr), np.inf)
    key = np.array(key, float); key /= np.linalg.norm(key)
    fill = np.array([0.7, -0.3, 0.3]); fill /= np.linalg.norm(fill)
    def raster(V, F, shade_fn, glass_mode=False, gz=None):
        X, Y, Z = proj(V)
        for fi, f_ in enumerate(F):
            xs, ys, zs = X[f_], Y[f_], Z[f_]
            if (zs <= 1).any(): continue
            x0, x1 = int(max(xs.min(), 0)), int(min(xs.max()+1, Wr)); y0, y1 = int(max(ys.min(), 0)), int(min(ys.max()+1, Hr))
            if x0 >= x1 or y0 >= y1: continue
            gx, gy = np.meshgrid(np.arange(x0, x1)+0.5, np.arange(y0, y1)+0.5)
            d = (ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
            if abs(d) < 1e-9: continue
            w0 = ((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d
            w1 = ((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d
            w2 = 1-w0-w1; ins = (w0 >= 0)&(w1 >= 0)&(w2 >= 0)
            iz = w0/zs[0]+w1/zs[1]+w2/zs[2]; z = 1/np.where(iz > 0, iz, 1e-9)
            sub = zb[y0:y1, x0:x1]
            if glass_mode:
                m = ins & (z < sub)
                if m.any():
                    region = img[y0:y1, x0:x1]
                    region[m] = region[m]*0.86 + np.array(hexc('#cfeaff'))*0.14
                    # simple reflection streak
                    streak = ((gx+gy*0.6) % 900 < 26) & m
                    region[streak] = region[streak]*0.88 + 0.12
                continue
            m = ins & (z < sub); sub[m] = z[m]
            img[y0:y1, x0:x1][m] = shade_fn(fi)
    for mesh, col in items:
        V, F = mesh.vertices, mesh.faces
        N = mesh.face_normals
        cam = (V[F].mean(1)-eye); cam /= np.linalg.norm(cam, axis=1, keepdims=True)
        keep = (N*cam).sum(1) < 0.05            # back-face cull
        F2, N2 = F[keep], N[keep]
        col = np.array(col)
        def shade(fi, N2=N2, col=col):
            n = N2[fi]
            l = 0.32 + 0.62*max(0, n@key) + 0.18*max(0, n@fill)
            return np.clip(col*l + 0.05*max(0, n@np.array([0, 0, 1])), 0, 1)
        raster(V, F2, shade)
    for g in glass:
        raster(g.vertices, g.faces, None, glass_mode=True)
    im = Image.fromarray((np.clip(img, 0, 1)*255).astype(np.uint8))
    # labels (projected)
    dr = ImageDraw.Draw(im)
    F_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; F_M = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
    for (p, txt, kind) in labels:
        x, y, z = proj(np.array(p, float))
        if z <= 0: continue
        xi, yi = int(x), int(y)
        if not (0 <= xi < Wr and 0 <= yi < Hr) or z > zb[yi, xi] + 6: continue   # occluded
        scale = f/z
        if kind == 'plate':
            fnt = ImageFont.truetype(F_B, int(34*scale)); dr.text((x, y), txt, font=fnt, fill=(20, 20, 22), anchor='mm')
        elif kind == 'nfc':
            fnt = ImageFont.truetype(F_B, int(11*scale)); dr.text((x, y), '((·)) ' + txt, font=fnt, fill=(177, 151, 252), anchor='mm')
        elif kind == 'tft':
            fnt = ImageFont.truetype(F_M, int(11*scale))
            dr.multiline_text((x, y), txt, font=fnt, fill=(105, 219, 124), anchor='mm', align='center', spacing=2)
        elif kind == 'rear':
            fnt = ImageFont.truetype(F_B, int(9*scale)); dr.text((x, y), txt, font=fnt, fill=(200, 200, 200), anchor='mm')
        elif kind == 'num':
            fnt = ImageFont.truetype(F_B, int(11*scale)); dr.text((x, y), txt, font=fnt, fill=(150, 150, 150), anchor='mm')
    im = im.resize((W, H), Image.LANCZOS)
    im.save(out, quality=92)
    return im
