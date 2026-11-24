# SPDX-License-Identifier: MIT
"""Assembly checks for the shell: overlaps, bolt pairing, foot-in-pocket stacking."""
import itertools, numpy as np, manifold3d as mf
from tiles import *

tiles = make_tiles()
placed = []
for t in tiles:
    m = t.build()
    placed.append((t, m.transform(t.M()[:3])))

# 1) pairwise overlaps (tongue in groove, butt on land) should be ~0
worst = 0
for (a, ma), (b, mb) in itertools.combinations(placed, 2):
    v = (ma ^ mb).volume()
    if v > 0.05: print(f"  overlap {a.name} / {b.name}: {v:.2f} mm3")
    worst = max(worst, v)
print('max pairwise overlap: %.3f mm3' % worst)

# 2) shell is closed: the union should seal the interior box (probe a thin slab outside each face)
shell = mf.Manifold.batch_boolean([m for _, m in placed], mf.OpType.Add)
inner = mf.Manifold.cube((W-2*T-0.2, DEPTH-T-0.2, CEIL-FLOOR-0.2)).translate((T+0.1, Y0+0.1, FLOOR+0.1))
print('shell intrudes into the chamber: %.2f mm3' % (shell ^ inner).volume())
outer = mf.Manifold.cube((W, DEPTH, Z1-Z0)).translate((0, Y0, Z0))
print('shell outside the envelope: %.2f mm3' % (shell - outer).volume())
wall_vol = outer.volume() - inner.volume()
print('wall volume covered: %.1f %%' % (100*(shell ^ outer).volume()/wall_vol))

# 3) every bolt station lands in exactly one hole and one insert
probe = lambda p, r=1.0: mf.Manifold.sphere(r, 16).translate(tuple(p))
bad = 0
for p, bf, be, lf in JOINTS:
    hits = sum((probe(p) ^ m).volume() > 1e-3 for _, m in placed)
    if hits: bad += 1          # point sits in empty space (in a hole) in every tile
print('face-to-face bolt stations blocked by material:', bad, 'of', len(JOINTS))
bad = 0
for f, p, axis, sc in TGS:
    if sum((probe(p) ^ m).volume() > 1e-3 for _, m in placed): bad += 1
print('TG bolt stations blocked by material:', bad, 'of', len(TGS))

# 4) stacking: a foot of the cabinet above sits in each roof pocket without touching
roof = [m for t, m in placed if t.f.name == 'TOP']
ft = foot().mirror((0, 0, 1))          # printed upside down; in use the big face is up
for x, y in POCKET_XY:
    fm = ft.translate((x, y, Z1 + 0.0 + 10.0 - 10.0)).translate((0, 0, 0))
    # foot hangs below the upper cabinet's bottom face, which rests on the roof at z = Z1
    fm = foot().mirror((0, 0, 1)).translate((x, y, Z1))
    ov = sum((fm ^ r).volume() for r in roof)
    print(f'  foot in pocket at ({x:.0f}, {y:.0f}): overlap {ov:.3f} mm3')
