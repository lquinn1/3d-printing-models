import numpy as np, cadquery as cq, time, sys
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCP.TopTools import TopTools_ListOfShape

# ---------------- egg profile (Hugelschaffer), z measured from blunt end ----------------
L, B, w = 205.0, 132.0, 9.0
CUT = 22.0            # egg cut plane (blunt end removed -> opening)
WALL = 1.6            # base shell wall (mm)
SKIRT = 12.0          # vertical spigot below cut that drops into the base collar
H = 3.6               # max scale relief (mm), added outward along the surface normal
HOLE_D = 2.6          # light/vent holes at scale junctions (pre-shrink nominal)
SHRINK = 1.006        # ABS shrink compensation (uniform)
R_TIP = 4.5           # scales run up to where the egg radius is this small; tiny smooth tip above

def r(ze):
    x = ze - L / 2
    v = (L * L - 4 * x * x) / (L * L + 8 * w * x + 4 * w * w)
    return B / 2 * np.sqrt(np.clip(v, 0, None))

R_CUT = float(r(CUT))
zt = np.linspace(CUT, L, 20000); rt = r(zt)
st = np.concatenate([[0], np.cumsum(np.hypot(np.diff(zt), np.diff(rt)))])
s_of_z = lambda z: np.interp(z, zt, st)
iz = np.where((zt > L / 2) & (rt < R_TIP))[0][0]
TOP_TEX = float(zt[iz]); S_END = float(st[iz])
z_of_s = lambda s: np.interp(s, st, zt)
r_of_s = lambda s: r(z_of_s(s))
def normal_of_s(s):
    z = z_of_s(s); dr = (r(z + 0.01) - r(z - 0.01)) / 0.02
    n = np.hypot(1, dr); return 1 / n, -dr / n     # (nr, nz)

# ---------------- quilted diamond lattice (like the reference) ----------------
# Fixed number of diamonds around; row spacing follows the local circumference so the
# diamonds keep their proportions and shrink smoothly toward the tip.
NDIA = 12            # diamonds around the egg
ASPECT = 1.25        # diamond height / width
_ss = np.linspace(0, S_END, 8000)
_rs = np.maximum(r_of_s(_ss), 0.5)
_dv = 2 * NDIA / (ASPECT * 2 * np.pi * _rs)          # dv/ds  (rows are 1 unit of v apart)
_vs = np.concatenate([[0], np.cumsum(0.5 * (_dv[1:] + _dv[:-1]) * np.diff(_ss))])
V_OFF = 0.35                                           # phase so the bottom fade sits in a crease
v_of_s = lambda s: np.interp(s, _ss, _vs) + V_OFF
s_of_v = lambda v: np.interp(v - V_OFF, _vs, _ss)
ROWS = [None]   # kept for the log line

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

def height_s(theta, s):
    v = v_of_s(s)
    u = theta / (2 * np.pi) * NDIA
    pill = np.zeros_like(theta)
    for k in (np.floor(v) - 1, np.floor(v), np.floor(v) + 1, np.floor(v) + 2, np.floor(v) + 3):
        par = np.mod(k, 2)
        x = u - 0.5 * par; x = x - np.round(x)           # -0.5..0.5 across the scale
        y = v - k                                        # scale centre row at y=0
        yu = np.clip(1 - 2 * np.abs(x), 0, 1) ** 0.8     # pointed, slightly full UPPER (open) edge
        d = yu - y                                       # depth below this scale's open edge
        f = smooth(0.0, 0.3, d) * (1 - 0.92 * np.clip(d / 2.2, 0, 1) ** 1.7)   # rounded, puffy lip -> tucks under
        f *= 0.55 + 0.45 * np.cos(np.pi * x) ** 0.6       # rounded crown across the scale
        f = np.where((d >= 0) & (d <= 2.6), f, 0)
        pill = np.maximum(pill, f)
    r0 = r_of_s(s)
    scale = np.clip(r0 / 34.0, 0.3, 1.0)                 # shallower relief on the small tip diamonds
    z = z_of_s(s)
    fade = smooth(CUT + 2, CUT + 9, z) * (1 - smooth(S_END - 3.5, S_END - 0.3, s))
    return H * pill * scale * fade

def section_points(s, M):
    th = np.linspace(0, 2 * np.pi, M, endpoint=False)
    h = height_s(th, np.full_like(th, s))
    # light circular low-pass so the interpolating spline cannot overshoot at the scale lips
    k = np.array([0.1, 0.2, 0.4, 0.2, 0.1]); h = sum(w_ * np.roll(h, i - 2) for i, w_ in enumerate(k))
    r0, z0 = float(r_of_s(s)), float(z_of_s(s)); nr, nz = normal_of_s(s)
    R = r0 + h * nr; Z = z0 + h * nz
    return [cq.Vector(float(a * np.cos(t)), float(a * np.sin(t)), float(c)) for a, t, c in zip(R, th, Z)]

def build(nrows=280, M=300):
    t0 = time.time()
    ss = np.linspace(0, S_END, nrows)
    print('sections', len(ss), 'rows of diamonds', round(v_of_s(S_END) - V_OFF, 1)); sys.stdout.flush()
    wires = []
    for sv in ss:
        m = M
        wires.append(cq.Wire.assembleEdges([cq.Edge.makeSpline(section_points(sv, m), periodic=True)]))
    outer_tex = cq.Solid.makeLoft(wires, True)
    print('loft', time.time() - t0, outer_tex.isValid()); sys.stdout.flush()

    # smooth tip (revolved) above textured region
    zz = np.linspace(TOP_TEX, L, 80)
    tz = [float(z) for z in zz[:-1]]
    tip = (cq.Workplane('XZ').moveTo(0, TOP_TEX).lineTo(tz and float(r(TOP_TEX)), TOP_TEX)
           .spline([(float(r(z)), z) for z in tz[1:]] + [(0.0, L)], includeCurrent=True)
           .close().revolve(360, (0, 0, 0), (0, 1, 0)).val())
    skirt = cq.Solid.makeCylinder(R_CUT, SKIRT + 0.2, cq.Vector(0, 0, CUT - SKIRT))
    outer = outer_tex.fuse(skirt, tip, glue=False, tol=0.02).clean()
    print('outer', time.time() - t0, outer.isValid()); sys.stdout.flush()

    # inner cavity: egg scaled inward by WALL (approx normal offset)
    Li, Bi = L - 2 * WALL, B - 2 * WALL
    def ri(ze):
        x = ze - WALL - Li / 2
        v = (Li * Li - 4 * x * x) / (Li * Li + 8 * w * x + 4 * w * w)
        return Bi / 2 * np.sqrt(np.clip(v, 0, None))
    zi = np.linspace(CUT, L - WALL, 120)
    ipts = [(float(ri(z)), float(z)) for z in zi[:-1]] + [(0.0, L - WALL)]
    inner = (cq.Workplane('XZ').moveTo(0, CUT - SKIRT - 1).lineTo(R_CUT - WALL, CUT - SKIRT - 1)
             .lineTo(R_CUT - WALL, CUT).lineTo(min(ipts[0][0], R_CUT - WALL), CUT)
             .spline(ipts[1:], includeCurrent=True).close()
             .revolve(360, (0, 0, 0), (0, 1, 0)).val())
    shell = outer.cut(inner).clean()
    if HOLE_D > 0:
        holes = []
        kmax = int(np.floor(v_of_s(S_END)))
        for k in range(0, kmax + 1):
            sk = float(s_of_v(k))
            if sk < s_of_z(CUT + 12) or sk > S_END - 2 or r_of_s(sk) < 9:
                continue
            zk = float(z_of_s(sk)); rk = float(r_of_s(sk)); nr, nz = normal_of_s(sk)
            for j in range(NDIA):
                th = (j + 0.5 + 0.5 * (k % 2)) * 2 * np.pi / NDIA     # 4-way corner of the diamonds
                d = cq.Vector(nr * np.cos(th), nr * np.sin(th), nz)
                c = cq.Vector(rk * np.cos(th), rk * np.sin(th), zk) - d * 6
                holes.append(cq.Solid.makeCylinder(HOLE_D / 2, 12, c, d))
        print('holes', len(holes)); sys.stdout.flush()
        for b0 in range(0, len(holes), 16):
            shell = shell.cut(*holes[b0:b0 + 16])
            print('  batch', b0, round(time.time() - t0)); sys.stdout.flush()
        shell = shell.clean()
        print('holes cut', time.time() - t0, shell.isValid()); sys.stdout.flush()
    print('shell', time.time() - t0, shell.isValid()); sys.stdout.flush()
    # print orientation: skirt bottom at z=0
    return shell.translate(cq.Vector(0, 0, -(CUT - SKIRT))).scale(SHRINK)

if __name__ == '__main__':
    nr = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    M = int(sys.argv[2]) if len(sys.argv) > 2 else 264
    egg = build(nr, M)
    bb = egg.BoundingBox(); print('bbox', bb.xlen, bb.ylen, bb.zlen, 'R_CUT', R_CUT)
    cq.exporters.export(egg, 'out8/dragon_egg_shell.step')
    cq.exporters.export(egg, 'out8/dragon_egg_shell.stl', tolerance=0.02, angularTolerance=0.2)
    print('done')
