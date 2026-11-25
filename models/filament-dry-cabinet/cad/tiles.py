# SPDX-License-Identifier: MIT
"""Shell tiles for the dry cabinet: 4 side tiles x 2, 4 top, 4 bottom, 4 back = 20 tiles.

Construction (all mm, world frame: x across the width, y front->back, z up):
  * TOP and BOTTOM span the full width and depth (y = DOOR .. back face), so the side walls
    stand on the bottom and carry the roof (and a stacked cabinet) in direct bearing.
  * LEFT / RIGHT sides sit between them; the BACK sits between the sides, top and bottom.
  * Where a face butts against another, the butting tile has a plain 5 mm edge rib with
    M4 clearance holes (BUTT) and the face it lands on has a 20.7 mm solid strip with M4
    heat-set inserts from the inside (LAND).
  * Tiles inside one face meet with the V tongue-and-groove + inserts from the coupon (TG).
  * Front edges get a 12 mm rib with inserts for the front frame (FRONT).

Every tile is printed skin-down (outside face on the bed); foam goes in the open pocket.
"""
import os, sys, math, json
import numpy as np, manifold3d as mf, trimesh
from params import *
from coupons import to_mf, cyl, socket_cut, save, OUT

A = L.stadium(6, 120)
W, Y0, Y1, Z0, Z1, T = A['ew'], L.DOOR, A['ed'], L.FEET, A['eh'], WALL
FLOOR, CEIL = Z0 + T, Z1 - T                       # inside faces of bottom / top
LAND_W = T + RIB                                    # strip a butting tile lands on
FRONT_W = 12.0
TG_W = 10.0                                         # bolt height in TG joints (from the skin)
BOSS_D = 7.0                                        # B-side boss depth behind the rib
CHAMFER = 0.8
SEAM_GAP, END_GAP, SPACING, KEEPOUT = 25.0, 30.0, 75.0, 24.0

# ---------------------------------------------------------------- faces
class Face:
    def __init__(s, name, O, U, V, umax, vmax, edges, useams, vseams):
        s.name = name; s.O = np.array(O, float); s.U = np.array(U, float); s.V = np.array(V, float)
        s.N = np.cross(s.U, s.V); s.umax, s.vmax = umax, vmax
        s.edges = edges; s.useams = useams; s.vseams = vseams
    def world(s, u, v, w): return s.O + u*s.U + v*s.V + w*s.N
    def local(s, p):
        d = np.asarray(p, float) - s.O; return np.array([d @ s.U, d @ s.V, d @ s.N])
    def M(s):           # 3x4 local -> world
        return np.column_stack([s.U, s.V, s.N, s.O])

DEPTH = Y1 - Y0
FACES = {
    'L':   Face('L', (0, Y0, FLOOR), (0, 1, 0), (0, 0, 1), DEPTH, CEIL-FLOOR,
                dict(umin='FRONT', umax='LAND', vmin='BUTT', vmax='BUTT'), [143.0-Y0], [(CEIL-FLOOR)/2]),
    'R':   Face('R', (W, Y1, FLOOR), (0, -1, 0), (0, 0, 1), DEPTH, CEIL-FLOOR,
                dict(umin='LAND', umax='FRONT', vmin='BUTT', vmax='BUTT'), [Y1-143.0], [(CEIL-FLOOR)/2]),
    'TOP': Face('TOP', (0, Y1, Z1), (1, 0, 0), (0, -1, 0), W, DEPTH,
                dict(umin='LAND', umax='LAND', vmin='LAND', vmax='FRONT'), [W/2], [Y1-227.0]),
    'BOT': Face('BOT', (0, Y0, Z0), (1, 0, 0), (0, 1, 0), W, DEPTH,
                dict(umin='LAND', umax='LAND', vmin='FRONT', vmax='LAND'), [W/2], [227.0-Y0]),
    'BACK': Face('BACK', (T, Y1, FLOOR), (1, 0, 0), (0, 0, 1), W-2*T, CEIL-FLOOR,
                dict(umin='BUTT', umax='BUTT', vmin='BUTT', vmax='BUTT'), [(W-2*T)/2], [270.0]),
}
for f in FACES.values():
    assert np.allclose(f.N, np.cross(f.U, f.V))

# ---------------------------------------------------------------- features in world coordinates
X_SLOT = [T + 10 + L.PITCH*(i+0.5) for i in range(6)]                   # slot centres across
Y_FRONT_ROW, Y_BACK_ROW = Y0 + A['y_front'], Y0 + A['y_back']
TOP_PORTS = [(x, y) for y in (Y_FRONT_ROW, Y_BACK_ROW) for x in X_SLOT]
BACK_PORTS = [(x + (-14 if k == 0 else 14), FLOOR + A['ih'] + dz)
              for x in X_SLOT for k, dz in enumerate((-62, -36))]
GLAND = (T + 150, FLOOR + 150)                                          # pod -> chamber wiring
POCKET_XY = [(x, y) for x in (35.0, W-35.0) for y in (Y0+45, Y1-50)]     # roof pockets = foot spots
POD_PX0 = T + 85.0                                                       # rear pod: 330 x 230, see pod.py
POD_PTS = [(POD_PX0 + u, FLOOR + 10 + v) for u in (10, 110, 220, 320) for v in (10, 220)]
ROD_Y = [Y_FRONT_ROW - L.ROD_CC/2, Y_FRONT_ROW + L.ROD_CC/2, Y_BACK_ROW - L.ROD_CC/2, Y_BACK_ROW + L.ROD_CC/2]
FRONT_CRADLE_H = A['rod_front']                                         # 30: cradle sits on the floor
REAR_CRADLE_H = A['rod_back']                                           # 150: riser + cradle in one
CRADLE_HOLES_FRONT = [(dy, 10.0) for dy in (-21, 21)]
CRADLE_HOLES_REAR = [(dy, z) for dy in (-21, 21) for z in (20.0, 130.0)]

def cradle_pts(side):
    x = T if side == 'L' else W - T
    pts = []
    for k, y in enumerate(ROD_Y):
        holes = CRADLE_HOLES_FRONT if k < 2 else CRADLE_HOLES_REAR
        pts += [(x, y + dy, FLOOR + z) for dy, z in holes]
    return pts

# hard points: (face, world point, from 'in'|'out', pad size)
HARD = []
for s in ('L', 'R'):
    HARD += [(s, p, 'in', 16.0) for p in cradle_pts(s)]
HARD += [('BACK', (x, Y1, z), 'out', 16.0) for x, z in POD_PTS]
HARD += [('BOT', (x, y, Z0), 'out', 50.0) for x, y in POCKET_XY]
SOCKETS = [('TOP', (x, y, Z1)) for x, y in TOP_PORTS] + \
          [('BACK', (x, Y1, z)) for x, z in BACK_PORTS + [GLAND]]
POCKETS = [('TOP', (x, y, Z1)) for x, y in POCKET_XY]
KEEP = [np.array(p, float) for _, p, _, _ in HARD] + [np.array(p, float) for _, p in SOCKETS]

# ---------------------------------------------------------------- bolt lines
def spaced(a, b, forbid):
    """Evenly spaced stations in [a, b], kept END_GAP from the ends and SEAM_GAP from forbid."""
    cuts = sorted(f for f in forbid if a < f < b)
    lo = [a + END_GAP] + [f + SEAM_GAP for f in cuts]
    hi = [f - SEAM_GAP for f in cuts] + [b - END_GAP]
    out = []
    for s0, s1 in zip(lo, hi):
        if s1 - s0 < 10: continue
        n = max(2, int(math.ceil((s1 - s0)/SPACING)) + 1)
        out += list(np.linspace(s0, s1, n))
    return out

def keep(p):
    return all(np.linalg.norm(np.asarray(p) - k) > KEEPOUT for k in KEEP)

JOINTS = []     # (kind, world point, butt_face, butt_edge, land_face)  kind: BUTT/LAND pair
def add_joint(pts, butt, edge, land):
    for p in pts:
        if keep(p): JOINTS.append((np.array(p, float), butt, edge, land))

ys_L = FACES['L'].useams[0] + Y0; ys_T = Y1 - FACES['TOP'].vseams[0]
zs_L = FLOOR + FACES['L'].vseams[0]; zs_B = FLOOR + FACES['BACK'].vseams[0]
for side, x in (('L', T/2), ('R', W - T/2)):
    ys = spaced(Y0, Y1, [ys_L, ys_T])
    add_joint([(x, y, CEIL) for y in ys], side, 'vmax', 'TOP')
    add_joint([(x, y, FLOOR) for y in ys], side, 'vmin', 'BOT')
    zs = spaced(FLOOR, CEIL, [zs_L, zs_B])
    add_joint([(T if side == 'L' else W-T, Y1 - T/2, z) for z in zs], 'BACK', 'umin' if side == 'L' else 'umax', side)
xs = spaced(T, W - T, [W/2])
add_joint([(x, Y1 - T/2, CEIL) for x in xs], 'BACK', 'vmax', 'TOP')
add_joint([(x, Y1 - T/2, FLOOR) for x in xs], 'BACK', 'vmin', 'BOT')

FRONTS = []     # (face, world point) inserts from the front face
for side, x in (('L', T/2), ('R', W - T/2)):
    FRONTS += [(side, (x, Y0, z)) for z in spaced(FLOOR, CEIL, [zs_L])]
FRONTS += [('TOP', (x, Y0, Z1 - T/2)) for x in spaced(0, W, [W/2])]
FRONTS += [('BOT', (x, Y0, Z0 + T/2)) for x in spaced(0, W, [W/2])]

TGS = []        # (face, world point, axis 'u'|'v', seam coordinate)
for f in FACES.values():
    for us in f.useams:
        TGS += [(f.name, f.world(us, v, TG_W), 'u', us) for v in spaced(0, f.vmax, f.vseams) if keep(f.world(us, v, T/2))]
    for vs in f.vseams:
        TGS += [(f.name, f.world(u, vs, TG_W), 'v', vs) for u in spaced(0, f.umax, f.useams) if keep(f.world(u, vs, T/2))]

# ---------------------------------------------------------------- geometry helpers (tile-local)
def box(u0, u1, v0, v1, w0, w1):
    return mf.Manifold.cube((u1-u0, v1-v0, w1-w0)).translate((u0, v0, w0))

def cyl_dir(p, d, length, r, n=40):
    """Cylinder starting at p along unit vector d."""
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    a = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 1.0, 0])
    x = np.cross(a, d); x /= np.linalg.norm(x); y = np.cross(d, x)
    M = np.column_stack([x, y, d, np.asarray(p, float)])
    return mf.Manifold.cylinder(length, r, r, n).transform(M)

def edge_prism(profile_tw, edge, s0, s1, uw, vw):
    """Extrude a (t = outward from the edge face, w) profile along an edge from s0 to s1."""
    L_ = s1 - s0
    P = mf.Manifold.extrude(mf.CrossSection([profile_tw]), L_)            # X=t, Y=w, Z=s
    M = {'umin': [[-1, 0, 0, 0], [0, 0, 1, s0], [0, 1, 0, 0]],
         'umax': [[1, 0, 0, uw], [0, 0, -1, s1], [0, 1, 0, 0]],
         'vmin': [[0, 0, -1, s1], [-1, 0, 0, 0], [0, 1, 0, 0]],
         'vmax': [[0, 0, 1, s0], [1, 0, 0, vw], [0, 1, 0, 0]]}[edge]
    return P.transform(np.array(M, float))

INWARD = {'umin': (1, 0, 0), 'umax': (-1, 0, 0), 'vmin': (0, 1, 0), 'vmax': (0, -1, 0)}

def tongue_profile():
    h, z = TONGUE_W, SKIN + 1.8
    return [(-0.3, z-h), (0, z-h), (TONGUE_H, z), (0, z+h), (-0.3, z+h)]

def groove_profile():
    h, z = TONGUE_W, SKIN + 1.8; g = GROOVE_CLR*math.sqrt(2); e = 0.3
    # groove is cut *into* the tile: t negative = inward
    return [(e, z-h-g-e), (e, z+h+g+e), (-(TONGUE_H+g), z)]

def ccw(pts):
    a = sum(x0*y1 - x1*y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:]+pts[:1]))
    return pts if a > 0 else pts[::-1]

# ---------------------------------------------------------------- tiles
class Tile:
    def __init__(s, face, u0, u1, v0, v1):
        s.f = face; s.u0, s.u1, s.v0, s.v1 = u0, u1, v0, v1
        s.uw, s.vw = u1-u0, v1-v0
        f = face
        s.edges = {
            'umin': f.edges['umin'] if u0 == 0 else 'TG_A',
            'umax': f.edges['umax'] if math.isclose(u1, f.umax) else 'TG_B',
            'vmin': f.edges['vmin'] if v0 == 0 else 'TG_A',
            'vmax': f.edges['vmax'] if math.isclose(v1, f.vmax) else 'TG_B'}
        c = f.world((u0+u1)/2, (v0+v1)/2, T/2)
        s.name = s._name(c)
    def _name(s, c):
        n = s.f.name
        if n in ('L', 'R'):
            return f"side_{'left' if n == 'L' else 'right'}_{'front' if c[1] < Y0+DEPTH/2 else 'rear'}_{'lower' if c[2] < (FLOOR+CEIL)/2 else 'upper'}"
        if n in ('TOP', 'BOT'):
            return f"{'top' if n == 'TOP' else 'bottom'}_{'left' if c[0] < W/2 else 'right'}_{'front' if c[1] < Y0+DEPTH/2 else 'rear'}"
        return f"back_{'left' if c[0] < W/2 else 'right'}_{'lower' if c[2] < (FLOOR+CEIL)/2 else 'upper'}"
    def loc(s, p):          # world -> tile local
        u, v, w = s.f.local(p); return np.array([u - s.u0, v - s.v0, w])
    def inside(s, p, m=0.01):
        u, v, w = s.loc(p); return -m <= u <= s.uw+m and -m <= v <= s.vw+m
    def on_edge(s, p, edge, tol=0.05):
        u, v, _ = s.loc(p)
        return {'umin': abs(u) < tol and 0 <= v <= s.vw, 'umax': abs(u-s.uw) < tol and 0 <= v <= s.vw,
                'vmin': abs(v) < tol and 0 <= u <= s.uw, 'vmax': abs(v-s.vw) < tol and 0 <= u <= s.uw}[edge]
    def M(s):
        return s.f.M() @ np.vstack([np.eye(4)[:3], [0, 0, 0, 1]]) @ np.array(
            [[1, 0, 0, s.u0], [0, 1, 0, s.v0], [0, 0, 1, 0], [0, 0, 0, 1]], float)

    def build(s, simple=False):
        uw, vw = s.uw, s.vw
        add = [box(0, uw, 0, vw, 0, SKIN)]
        cut = []
        width = {'TG_A': RIB, 'TG_B': RIB, 'BUTT': RIB, 'LAND': LAND_W, 'FRONT': FRONT_W}
        for e, kind in s.edges.items():
            wd = width[kind]
            add.append({'umin': box(0, wd, 0, vw, 0, T), 'umax': box(uw-wd, uw, 0, vw, 0, T),
                        'vmin': box(0, uw, 0, wd, 0, T), 'vmax': box(0, uw, vw-wd, vw, 0, T)}[e])
            slen = vw if e[0] == 'u' else uw
            if kind == 'TG_A':
                add.append(edge_prism(ccw(tongue_profile()), e, 2.5, slen - 2.5, uw, vw))   # stop short: tongues cross at 4-tile corners
            if kind == 'TG_B':
                cut.append(edge_prism(ccw(groove_profile()), e, -1, slen+1, uw, vw))
        # TG bolts / inserts
        fn = s.f.name
        for face, p, axis, sc in TGS:
            if face != fn or not s.inside(p): continue
            for e in ('umin', 'umax', 'vmin', 'vmax'):
                if s.edges[e] not in ('TG_A', 'TG_B') or not s.on_edge(p, e): continue
                q = s.loc(p); d = np.array(INWARD[e], float)
                if s.edges[e] == 'TG_A':
                    cut.append(cyl_dir(q - d, d, RIB + 2, BOLT_CLEAR_D/2))
                else:
                    tang = np.array([d[1], d[0], 0.0])           # along the edge
                    a = q.copy(); a[2] = 0
                    corner = a - tang*BOSS/2
                    bx = [corner, corner + tang*BOSS, corner + tang*BOSS + d*(RIB+BOSS_D), corner + d*(RIB+BOSS_D)]
                    us = [c[0] for c in bx]; vs = [c[1] for c in bx]
                    add.append(box(min(us), max(us), min(vs), max(vs), 0, T))
                    cut.append(cyl_dir(q - d, d, INSERT_DEPTH + 1, INSERT_HOLE_D/2))
                    cut.append(cyl_dir(q - d, d, RIB + BOSS_D - 0.8 + 1, BOLT_CLEAR_D/2 - 0.4))
        # BUTT holes and LAND inserts
        for p, bf, be, lf in JOINTS:
            if bf == fn and s.inside(p) and s.on_edge(p, be) and s.edges[be] == 'BUTT':
                d = np.array(INWARD[be], float); q = s.loc(p)
                cut.append(cyl_dir(q - d, d, RIB + 2, BOLT_CLEAR_D/2))
            if lf == fn and s.inside(p):
                q = s.loc(p)
                cut.append(cyl(INSERT_HOLE_D/2, T - INSERT_DEPTH, T + 1, n=40).translate((q[0], q[1], 0)))
        # FRONT inserts
        for face, p in FRONTS:
            if face != fn or not s.inside(p): continue
            for e in ('umin', 'umax', 'vmin', 'vmax'):
                if s.edges[e] == 'FRONT' and s.on_edge(p, e):
                    d = np.array(INWARD[e], float); q = s.loc(p)
                    cut.append(cyl_dir(q - d, d, INSERT_DEPTH + 1, INSERT_HOLE_D/2))
        # hard points
        for face, p, side, pad in HARD:
            if face != fn or not s.inside(p): continue
            q = s.loc(p)
            add.append(box(q[0]-pad/2, q[0]+pad/2, q[1]-pad/2, q[1]+pad/2, 0, T))
            if side == 'in':
                cut.append(cyl(INSERT_HOLE_D/2, T - INSERT_DEPTH, T + 1, n=40).translate((q[0], q[1], 0)))
            else:
                cut.append(cyl(INSERT_HOLE_D/2, -1, INSERT_DEPTH, n=40).translate((q[0], q[1], 0)))
        # port sockets
        socks = []
        for face, p in SOCKETS:
            if face != fn or not s.inside(p): continue
            q = s.loc(p)
            add.append(cyl(SOCKET_OD/2, 0, T, n=96).translate((q[0], q[1], 0)))
            socks.append(q)
        # stacking pockets (roof): pad + 45 deg tapered pocket from the outside
        for face, p in POCKETS:
            if face != fn or not s.inside(p): continue
            q = s.loc(p)
            add.append(box(q[0]-30, q[0]+30, q[1]-30, q[1]+30, 0, T))
            o, fl, dp = 21.0, 10.5, 10.5
            pts = [(q[0]+sx*o, q[1]+sy*o, -1) for sx in (-1, 1) for sy in (-1, 1)] + \
                  [(q[0]+sx*fl, q[1]+sy*fl, dp) for sx in (-1, 1) for sy in (-1, 1)]
            pts += [(q[0]+sx*(o+1), q[1]+sy*(o+1), -1) for sx in (-1, 1) for sy in (-1, 1)]
            cut.append(mf.Manifold.hull_points([list(map(float, x)) for x in pts]))
        m = mf.Manifold.batch_boolean(add, mf.OpType.Add)
        if cut: m = m - mf.Manifold.batch_boolean(cut, mf.OpType.Add)
        for q in socks:
            cutter = cyl(PORT_D/2, -1, T + 1, n=48) if simple else socket_cut(0, T, PORT_CLR_SEL, n=96, dz=0.1)
            m = m - cutter.translate((q[0], q[1], 0))
        # chamfer the outside skin edges (outline only; tongues above w = CHAMFER survive)
        c = CHAMFER
        clip = mf.Manifold.hull_points([[x, y, z] for x, y, z in
            [(c, c, 0), (uw-c, c, 0), (uw-c, vw-c, 0), (c, vw-c, 0),
             (0, 0, c), (uw, 0, c), (uw, vw, c), (0, vw, c)]])
        clip = clip + box(-5, uw+5, -5, vw+5, c, T+1)
        m = m ^ clip
        s.m = m
        return m

def make_tiles():
    tiles = []
    for f in FACES.values():
        ub = [0.0] + f.useams + [f.umax]; vb = [0.0] + f.vseams + [f.vmax]
        for i in range(len(ub)-1):
            for j in range(len(vb)-1):
                tiles.append(Tile(f, ub[i], ub[i+1], vb[j], vb[j+1]))
    return tiles

# ---------------------------------------------------------------- loose parts
def foot():
    """Printed upside down (big face on the bed). Bolts up into the bottom-tile insert."""
    o, fl, h = 20.5, 10.0, 10.0
    pts = [(sx*o, sy*o, 0) for sx in (-1, 1) for sy in (-1, 1)] + [(sx*fl, sy*fl, h) for sx in (-1, 1) for sy in (-1, 1)]
    m = mf.Manifold.hull_points([list(map(float, p)) for p in pts])
    m -= cyl(BOLT_CLEAR_D/2, -1, h+1, n=40)
    m -= cyl(BOLT_HEAD_D/2, h - BOLT_HEAD_H, h + 1, n=40)
    return m

def cradle_world(side, k):
    """Cradle k (0..3 = front-front, front-back, back-front, back-back rod) placed on wall side."""
    h, holes = (FRONT_CRADLE_H, CRADLE_HOLES_FRONT) if k < 2 else (REAR_CRADLE_H, CRADLE_HOLES_REAR)
    m = cradle(h, holes)                      # local: x along the wall (y), y up (z), z out of the wall (x)
    if side == 'L':
        M = [[0, 0, 1, T], [1, 0, 0, ROD_Y[k]], [0, 1, 0, FLOOR]]
    else:
        M = [[0, 0, -1, W - T], [-1, 0, 0, ROD_Y[k]], [0, 1, 0, FLOOR]]
    return m.transform(np.array(M, float))

def cradle(h, holes):
    """Lies on its wall face (z = 0 is the wall). U saddle on the top edge, rod centre at height h."""
    Wd, Tk = 56.0, 12.0; r = ROD_OD/2 + CRADLE_CLR
    m = box(-Wd/2, Wd/2, 0, h, 0, Tk)
    m -= cyl(r, -1, Tk + 1, n=128).translate((0, h, 0))
    if h > 60:                                                       # lighten the riser
        m -= box(-Wd/2 + 9, Wd/2 - 9, 32, h - 34, -1, Tk + 1)
    for dy, z in holes:
        m -= cyl(BOLT_CLEAR_D/2, -1, Tk + 1, n=40).translate((dy, z, 0))
        m -= cyl(BOLT_HEAD_D/2, Tk - BOLT_HEAD_H, Tk + 1, n=40).translate((dy, z, 0))
    return m

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    tiles = make_tiles()
    report = []
    for t in tiles:
        m = t.build()
        tm = save(m, t.name)
        report.append(dict(name=t.name, size=[round(t.uw, 1), round(t.vw, 1)], edges=t.edges,
                           volume_cm3=round(tm.volume/1000, 1)))
        assert max(t.uw, t.vw) <= TILE_MAX, t.name
    save(foot(), 'foot')
    save(cradle(FRONT_CRADLE_H, CRADLE_HOLES_FRONT), 'rod_cradle_front')
    save(cradle(REAR_CRADLE_H, CRADLE_HOLES_REAR), 'rod_cradle_rear')
    json.dump(report, open(os.path.join(OUT, 'tiles.json'), 'w'), indent=1)
    print(len(tiles), 'tiles;', len(JOINTS), 'face-to-face bolts;', len(TGS), 'TG bolts;', len(FRONTS), 'front inserts')
