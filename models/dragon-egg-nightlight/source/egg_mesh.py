# SPDX-License-Identifier: MIT
"""High-resolution STL of the dragon egg, built directly as a mesh (same heightfield as egg.py)."""
import numpy as np, importlib.util, sys, time
import manifold3d as mf
import trimesh

spec = importlib.util.spec_from_file_location('egg', '/home/claude/egg/egg.py')
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)

NS = int(sys.argv[1]) if len(sys.argv) > 1 else 900     # samples along the profile
MT = int(sys.argv[2]) if len(sys.argv) > 2 else 1080    # samples around
OUT = sys.argv[3] if len(sys.argv) > 3 else 'out8/dragon_egg_shell.stl'
t0 = time.time()

def lowpass(h):
    # same light circular filter egg.py uses so STL and STEP match
    k = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
    # egg.py filters on its 300-pt grid; scale the kernel to this grid's spacing
    n = max(1, int(round(MT / 300)))
    out = np.zeros_like(h)
    for i, w in enumerate(k):
        out += w * np.roll(h, (i - 2) * n)
    return out

th = np.linspace(0, 2 * np.pi, MT, endpoint=False)
# ---- outer textured surface, rows from cut (s=0) up to S_END, then smooth tip rings to the apex
ss = np.linspace(0, e.S_END, NS)
rings = []
for z in np.linspace(e.CUT - e.SKIRT, e.CUT, 8)[:-1]:     # vertical skirt, part of the same surface
    rings.append(np.c_[e.R_CUT * np.cos(th), e.R_CUT * np.sin(th), np.full(MT, z)])
for s in ss:
    h = lowpass(e.height_s(th, np.full_like(th, s)))
    r0, z0 = float(e.r_of_s(s)), float(e.z_of_s(s)); nr, nz = e.normal_of_s(s)
    R = r0 + h * nr; Z = z0 + h * nz
    rings.append(np.c_[R * np.cos(th), R * np.sin(th), Z])
ztip = np.linspace(e.TOP_TEX, e.L, 40)[1:-1]
for z in ztip:
    R = float(e.r(z)); rings.append(np.c_[R * np.cos(th), R * np.sin(th), np.full(MT, z)])
V = np.vstack(rings); nR = len(rings)
apex = len(V); V = np.vstack([V, [0, 0, e.L]])
bottom_c = len(V); V = np.vstack([V, [0, 0, e.CUT - e.SKIRT]])
idx = np.arange(nR * MT).reshape(nR, MT)
a = idx[:-1]; b = np.roll(idx[:-1], -1, axis=1); c = np.roll(idx[1:], -1, axis=1); d = idx[1:]
F = np.vstack([np.c_[a.ravel(), b.ravel(), c.ravel()], np.c_[a.ravel(), c.ravel(), d.ravel()]])
top = idx[-1]; F = np.vstack([F, np.c_[top, np.roll(top, -1), np.full(MT, apex)]])
bot = idx[0];  F = np.vstack([F, np.c_[np.roll(bot, -1), bot, np.full(MT, bottom_c)]])
outer = trimesh.Trimesh(V, F, process=False)
if outer.volume < 0: outer.invert()
print('outer mesh', len(outer.faces), round(time.time() - t0, 1)); sys.stdout.flush()

def to_manifold(tm):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                               tri_verts=np.asarray(tm.faces, np.uint32)))
M_outer = to_manifold(outer)
print('outer manifold status', M_outer.status())

SEG = MT
solid = M_outer

# ---- inner cavity (same construction as egg.py)
Li, Bi = e.L - 2 * e.WALL, e.B - 2 * e.WALL
def ri(ze):
    x = ze - e.WALL - Li / 2
    v = (Li * Li - 4 * x * x) / (Li * Li + 8 * e.w * x + 4 * e.w * e.w)
    return Bi / 2 * np.sqrt(np.clip(v, 0, None))
zi = np.linspace(e.CUT, e.L - e.WALL, 320)
prof = [(0.0, e.CUT - e.SKIRT - 1), (e.R_CUT - e.WALL, e.CUT - e.SKIRT - 1), (e.R_CUT - e.WALL, e.CUT)]
prof += [(float(ri(z)), float(z)) for z in zi[:-1]] + [(0.0, e.L - e.WALL)]
inner = mf.Manifold.revolve(mf.CrossSection([prof]), 720)
shell = solid - inner
print('shell', round(time.time() - t0, 1)); sys.stdout.flush()

# ---- light holes at the scale-tip junctions (identical placement to egg.py)
holes = []
kmax = int(np.floor(e.v_of_s(e.S_END)))
for k in range(0, kmax + 1):
    sk = float(e.s_of_v(k))
    if sk < e.s_of_z(e.CUT + 12) or sk > e.S_END - 2 or e.r_of_s(sk) < 9:
        continue
    zk = float(e.z_of_s(sk)); rk = float(e.r_of_s(sk)); nr, nz = e.normal_of_s(sk)
    for j in range(e.NDIA):
        t = (j + 0.5 + 0.5 * (k % 2)) * 2 * np.pi / e.NDIA
        dvec = np.array([nr * np.cos(t), nr * np.sin(t), nz])
        c0 = np.array([rk * np.cos(t), rk * np.sin(t), zk]) - dvec * 6
        cyl = trimesh.creation.cylinder(radius=e.HOLE_D / 2, segment=[c0, c0 + dvec * 12], sections=40)
        holes.append(to_manifold(cyl))
shell = shell - mf.Manifold.batch_boolean(holes, mf.OpType.Add)
print('holes', len(holes), round(time.time() - t0, 1))

shell = shell.translate((0, 0, -(e.CUT - e.SKIRT))).scale((e.SHRINK,) * 3)
m = shell.to_mesh()
tm = trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts)
print('manifold status', shell.status(), 'genus', shell.genus())
print('final tris', len(tm.faces), 'watertight', tm.is_watertight, 'vol cm3', round(tm.volume / 1000, 1),
      'bbox', tm.extents.round(2))
tm.export(OUT)
print('done', round(time.time() - t0, 1))
