# SPDX-License-Identifier: MIT
"""Fit-test coupons for the dry cabinet. Print these before the tiles.

  port_socket_coupon   three threaded sockets, radial clearance 0.15 / 0.25 / 0.35
  port_blank_plug      hex-flange blank plug with O-ring face groove
  port_ptfe_module     same, with a PC4-M10 hole and a PTFE bore
  rod_cradle           U-cradle for one end of a 3/4 in PVC rod
  index_collar         slide-on slot collar with three spring tabs
  tile_joint_a / _b    tile edge pair: V tongue and groove, M4 insert bosses, foam pocket

Bodies are built in CadQuery; threads are generated as meshes and combined with manifold3d.
"""
import os, math, tempfile
import numpy as np, trimesh, cadquery as cq, manifold3d as mf
from params import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stl')
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# ------------------------------------------------------------------ mesh helpers
def to_mf(V, F):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(V, np.float32), tri_verts=np.asarray(F, np.uint32)))

def cq_to_mf(shape):
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f: p = f.name
    cq.exporters.export(shape, p, tolerance=0.01, angularTolerance=0.08)
    m = trimesh.load(p); os.unlink(p); m.merge_vertices(digits_vertex=5)
    mesh = mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32))
    mesh.merge()
    out = mf.Manifold(mesh); assert out.status() == mf.Error.NoError, out.status()
    return out

def save(man, name):
    o = man.to_mesh(); t = trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts, process=False)
    assert t.is_watertight and t.is_volume, name
    t.export(os.path.join(OUT, name + '.stl'))
    b = t.bounds
    print(f"{name:20s} vol {t.volume/1000:6.1f} cm3   {b[1][0]-b[0][0]:.1f} x {b[1][1]-b[0][1]:.1f} x {b[1][2]-b[0][2]:.1f} mm")
    return t

def cyl(r, z0, z1, n=96, r1=None):
    return mf.Manifold.cylinder(z1-z0, r, r if r1 is None else r1, n).translate((0, 0, z0))

# ------------------------------------------------------------------ thread
def thread_profile(u):
    """ISO-like 60 deg profile for printing, 0 = root, 1 = crest; u in [0,1) of a pitch."""
    u = np.mod(u, 1.0)
    return np.select([u < 0.25, u < 0.5625, u < 0.6875],
                     [0.0, (u-0.25)/0.3125, 1.0], (1.0-u)/0.3125)

def thread_solid(d_major, pitch, z0, z1, grow=0.0, n=128, dz=0.05):
    """Solid of revolution-with-helix: r = r_minor + h*profile((z/P - theta/2pi)). grow adds radially."""
    h = 0.5413*pitch; r_min = d_major/2 - h + grow
    th = np.linspace(0, 2*np.pi, n, endpoint=False)
    zs = np.linspace(z0, z1, max(2, int(round((z1-z0)/dz))+1))
    U = zs[:, None]/pitch - th[None, :]/(2*np.pi)
    R = r_min + h*thread_profile(U)
    X = R*np.cos(th)[None, :]; Y = R*np.sin(th)[None, :]; Z = np.broadcast_to(zs[:, None], R.shape)
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    nz = len(zs); idx = np.arange(nz*n).reshape(nz, n)
    a = idx[:-1, :]; b = np.roll(idx[:-1, :], -1, 1); c = idx[1:, :]; d = np.roll(idx[1:, :], -1, 1)
    F = np.concatenate([np.stack([a, b, d], -1).reshape(-1, 3), np.stack([a, d, c], -1).reshape(-1, 3)])
    cb, ct = len(V), len(V)+1
    V = np.vstack([V, [0, 0, z0], [0, 0, z1]])
    bot = np.stack([np.full(n, cb), idx[0, (np.arange(n)+1) % n], idx[0, :]], -1)
    top = np.stack([np.full(n, ct), idx[-1, :], idx[-1, (np.arange(n)+1) % n]], -1)
    return to_mf(V, np.vstack([F, bot, top]))

def socket_cut(z0, z1, clr, n=128, dz=0.05):
    """Internal thread cutter plus 0.5 mm lead-in countersinks at both ends."""
    r = PORT_D/2 + clr
    cut = thread_solid(PORT_D, PORT_P, z0-1, z1+1, grow=clr, n=n, dz=dz)
    cut += cyl(r+0.5+1, z0-1, z0+0.5, r1=r)          # bottom countersink (45 deg)
    cut += cyl(r, z1-0.5, z1+1, r1=r+1.5)            # top countersink
    return cut

# ------------------------------------------------------------------ parts
def port_socket_coupon():
    xs = (-40.0, 0.0, 40.0); PL = 3.0
    plate = cq.Workplane().box(124, 52, PL, centered=(True, True, False)).edges('|Z').fillet(4)
    for x in xs:
        plate = plate.union(cq.Workplane().center(x, 0).circle(SOCKET_OD/2).extrude(SOCKET_LEN))
    for x, c in zip(xs, PORT_CLR):
        plate = plate.cut(cq.Workplane().workplane(offset=PL-0.6).center(x, 20.5)
                          .text(f"{c:.2f}", 6, 1, fontPath=FONT, halign='center', valign='center'))
    m = cq_to_mf(plate.val())
    for x, c in zip(xs, PORT_CLR):
        m -= socket_cut(0, SOCKET_LEN, c).translate((x, 0, 0))
    return m

def hex_flange(h):
    return cq.Workplane().polygon(6, FLANGE_AF/math.cos(math.pi/6)).extrude(h).edges('|Z').fillet(1.5)

def port_module(kind):
    """kind: 'plug' or 'ptfe'. Printed flange down (outside face on the bed)."""
    fh = FLANGE_H_PLUG if kind == 'plug' else FLANGE_H_MODULE
    body = hex_flange(fh)
    # O-ring face groove on the top of the flange (the face that seats against the wall)
    gi = GROOVE_ID/2; go = gi + GROOVE_W
    body = body.cut(cq.Workplane().workplane(offset=fh-GROOVE_DEPTH).circle(go).circle(gi).extrude(GROOVE_DEPTH+1))
    m = cq_to_mf(body.val())
    # threaded shank with a 1 mm chamfer at the tip
    z0, z1 = fh, fh + SHANK_LEN
    env = cyl(PORT_D/2+0.5, z0-0.2, z1-1.0) + cyl(PORT_D/2+0.5, z1-1.0, z1, r1=PORT_D/2-1.2)
    shank = thread_solid(PORT_D, PORT_P, z0-0.2, z1) ^ env
    m += shank + cyl(PORT_D/2-1.0, z0-0.5, z0+0.5)      # root fillet ring so the thread is fused
    if kind == 'ptfe':
        m -= cyl(PC4_HOLE_D/2, -1, PC4_HOLE_DEPTH, n=64)
        m -= cyl(PTFE_BORE/2, -1, z1+1, n=48)
        m -= cyl(PTFE_BORE/2+1, z1-0.8, z1+1, r1=PTFE_BORE/2) .translate((0, 0, 0))  # lead-in
    else:
        # finger grip: shallow cross slot on the outside face so a coin can turn it
        m -= cq_to_mf(cq.Workplane().box(18, 2.4, 2.4).val())
    return m

def rod_cradle():
    """Lies on its wall face. U saddle opens upward (+Z in use = +Y here)."""
    W, H, T = 56.0, 36.0, 12.0
    r = ROD_OD/2 + CRADLE_CLR
    b = (cq.Workplane('XY').box(W, H, T, centered=(True, False, False))
         .edges('|Z').fillet(3))
    b = b.cut(cq.Workplane('XY').center(0, H).circle(r).extrude(T))
    for x in (-21.0, 21.0):                              # M4 counterbored from the rod side
        b = b.cut(cq.Workplane().center(x, 13).circle(BOLT_CLEAR_D/2).extrude(T))
        b = b.cut(cq.Workplane().workplane(offset=T-BOLT_HEAD_H).center(x, 13).circle(BOLT_HEAD_D/2).extrude(BOLT_HEAD_H))
    b = b.faces('>Z').edges('not |Z').chamfer(0.6)
    return cq_to_mf(b.val())

def index_collar():
    """Slides on from the rod end; three spring tabs grip the PVC."""
    ri = ROD_OD/2 + 0.5                       # bore clears the pipe
    c = cq.Workplane().circle(COLLAR_OD/2).circle(ri).extrude(COLLAR_W)
    c = c.edges().chamfer(0.5)
    m = cq_to_mf(c.val())
    beam_t, slot_w, span = 1.6, 0.9, 54.0
    for k in range(3):
        a0 = math.radians(k*120 - span/2); a1 = math.radians(k*120 + span/2)
        # arc slot behind a thin beam
        rs = ri + beam_t
        pts_o = [(math.cos(a)*(rs+slot_w), math.sin(a)*(rs+slot_w)) for a in np.linspace(a0, a1, 24)]
        pts_i = [(math.cos(a)*rs, math.sin(a)*rs) for a in np.linspace(a1, a0, 24)]
        slot = mf.Manifold.extrude(mf.CrossSection([pts_o + pts_i]), COLLAR_W+2).translate((0, 0, -1))
        m -= slot
        # bump on the beam pointing into the bore: interference = COLLAR_GRIP + 0.5 clearance
        am = math.radians(k*120); bump_r = ri - (0.5 + COLLAR_GRIP)
        bump = cyl(2.2, 0, COLLAR_W, n=32).translate((math.cos(am)*(bump_r+2.2), math.sin(am)*(bump_r+2.2), 0))
        m += bump ^ cyl(ri+0.01, 0, COLLAR_W, n=128)
    return m

def tile_joint(side):
    """Coupon of two neighbouring tile edges. Skin on the bed, joint face at y = 0."""
    LX, LY = 70.0, 50.0
    t = cq.Workplane().box(LX, LY, SKIN, centered=(True, False, False))           # skin
    t = t.union(cq.Workplane().box(LX, RIB, WALL, centered=(True, False, False)))  # joint rib
    # thin rim on the other three sides so the foam pocket depth can be checked
    for (cx, cy, sx, sy) in ((-(LX/2-1), LY/2, 2, LY), ((LX/2-1), LY/2, 2, LY), (0, LY-1, LX, 2)):
        t = t.union(cq.Workplane().center(cx, cy).rect(sx, sy).extrude(WALL))
    zc_t = SKIN + 1.8                                     # tongue centre height
    zc_b = 10.0                                           # insert / bolt height
    bx = (-20.0, 20.0)
    if side == 'b':
        for x in bx:                                      # insert bosses behind the rib
            t = t.union(cq.Workplane().center(x, RIB + 3.5).rect(BOSS, 7).extrude(WALL))
    m = cq_to_mf(t.val())
    # V tongue (45 deg flanks, prints without support) / matching groove
    half, hgt = TONGUE_W, TONGUE_H
    if side == 'a':
        prof = mf.CrossSection([[(0.3, zc_t-half), (0.3, zc_t+half), (0, zc_t+half), (-hgt, zc_t), (0, zc_t-half)]])  # CCW
        m += _xbar(prof, LX)
        for x in bx:
            m -= _ybar_hole(x, zc_b, BOLT_CLEAR_D/2, -1, RIB+1)
    else:
        # true offset of the 45 deg V tongue: every flank is GROOVE_CLR away (tip moves c*sqrt2)
        g = GROOVE_CLR*math.sqrt(2); e = 0.3
        prof = mf.CrossSection([[(-e, zc_t-half-g-e), (hgt+g, zc_t), (-e, zc_t+half+g+e)]])
        m -= _xbar(prof, LX+2)
        for x in bx:
            m -= _ybar_hole(x, zc_b, INSERT_HOLE_D/2, -1, INSERT_DEPTH)
            m -= _ybar_hole(x, zc_b, BOLT_CLEAR_D/2-0.4, -1, RIB+7-0.8)   # bolt runout
    return m

def _xbar(prof_yz, length):
    """Extrude a (y, z) profile along X, centred on x = 0."""
    s = mf.Manifold.extrude(prof_yz, length)            # profile in XY, extruded along Z
    # map (x, y, z) -> (z - L/2, x, y): profile x->world y, profile y->world z, extrusion->world x
    return s.transform(np.array([[0, 0, 1, -length/2], [1, 0, 0, 0], [0, 1, 0, 0]], float))

def _ybar_hole(x, z, r, y0, y1):
    c = mf.Manifold.cylinder(y1-y0, r, r, 48)            # along Z
    return c.transform(np.array([[1, 0, 0, x], [0, 0, 1, y0], [0, -1, 0, z]], float))  # z->y

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    parts = {
        'port_socket_coupon': port_socket_coupon(),
        'port_blank_plug': port_module('plug'),
        'port_ptfe_module': port_module('ptfe'),
        'rod_cradle': rod_cradle(),
        'index_collar': index_collar(),
        'tile_joint_a': tile_joint('a'),
        'tile_joint_b': tile_joint('b'),
    }
    for k, v in parts.items(): save(v, k)
