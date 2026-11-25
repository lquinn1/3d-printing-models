"""Photoreal scene: two dry cabinets on a chrome wire shelf, a CoreXY enclosed printer
(Voron 2.4-style, generic, no logos) on a workbench beside it. Cycles. Units: metres."""
import bpy, bmesh, json, math, sys, os
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
RES = float(ARGS[0]) if ARGS else 1.0
SAMPLES = int(ARGS[1]) if len(ARGS) > 1 else 128
OUT = ARGS[2] if len(ARGS) > 2 else '/tmp/scene/render.png'

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
info = json.load(open('/tmp/scene/info.json'))
MM = 0.001

# ------------------------------------------------------------------ materials
def mat(name, base, rough=0.5, metal=0.0, trans=0.0, ior=1.45, emit=None, estr=0.0, coat=0.0, bump=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*base, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Transmission Weight'].default_value = trans
    p.inputs['IOR'].default_value = ior
    p.inputs['Coat Weight'].default_value = coat
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = estr
    if bump:                                   # (scale, strength): fine noise for print texture / casting
        n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = bump[0]; n.inputs['Detail'].default_value = 6
        b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = bump[1]; b.inputs['Distance'].default_value = 0.0005
        nt.links.new(n.outputs['Fac'], b.inputs['Height']); nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return m

def layer_lines(m, pitch=0.0002, strength=0.25):
    """FDM layer lines: a z-banded bump (world z), for printed parts."""
    nt = m.node_tree; p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); w = nt.nodes.new('ShaderNodeTexWave')
    w.wave_type = 'BANDS'; w.bands_direction = 'Z'; w.inputs['Scale'].default_value = 1.0 / pitch / 10
    w.inputs['Distortion'].default_value = 0.3
    nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = strength; b.inputs['Distance'].default_value = 0.00005
    nt.links.new(w.outputs['Fac'], b.inputs['Height']); nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return m

def image_emit(name, path, strength=2.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path)
    nt.links.new(t.outputs['Color'], p.inputs['Base Color']); nt.links.new(t.outputs['Color'], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = strength; p.inputs['Roughness'].default_value = 0.08
    p.inputs['Coat Weight'].default_value = 1.0
    return m

def wood(name, c1, c2, scale=18.0, rough=0.45):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1, 1, 14)
    w = nt.nodes.new('ShaderNodeTexWave'); w.wave_type = 'RINGS'; w.inputs['Scale'].default_value = scale
    w.inputs['Distortion'].default_value = 6; w.inputs['Detail'].default_value = 3
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*c1, 1); r.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], w.inputs['Vector'])
    nt.links.new(w.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough; p.inputs['Coat Weight'].default_value = 0.3
    return m

M = dict(
    shell=layer_lines(mat('abs_charcoal', (0.030, 0.032, 0.036), 0.55)),
    frame=layer_lines(mat('abs_black', (0.018, 0.019, 0.021), 0.5)),
    orange=layer_lines(mat('abs_orange', (0.85, 0.20, 0.025), 0.42)),
    part=layer_lines(mat('abs_grey', (0.06, 0.065, 0.07), 0.5)),
    part_dark=layer_lines(mat('abs_grey2', (0.05, 0.05, 0.055), 0.5)),
    part_light=layer_lines(mat('abs_white', (0.75, 0.75, 0.74), 0.45)),
    collar=layer_lines(mat('abs_lgrey', (0.45, 0.47, 0.5), 0.45)),
    rubber=mat('rubber', (0.01, 0.01, 0.01), 0.9),
    steel=mat('steel', (0.62, 0.63, 0.64), 0.28, metal=1.0),
    led=mat('led_diffuser', (0.9, 0.9, 0.88), 0.4, emit=(1.0, 0.92, 0.82), estr=14.0),
    glass=mat('polycarbonate', (0.97, 0.98, 1.0), 0.0, trans=1.0, ior=1.585),
    wood=wood('poplar', (0.80, 0.68, 0.47), (0.66, 0.53, 0.33)),
    chrome=mat('chrome', (0.92, 0.92, 0.93), 0.07, metal=1.0),
    alu_black=mat('anodized_black', (0.02, 0.02, 0.022), 0.32, metal=0.7),
    alu=mat('aluminium', (0.80, 0.81, 0.82), 0.25, metal=1.0, bump=(900, 0.05)),
    pei=mat('pei_textured', (0.08, 0.07, 0.06), 0.75, bump=(4000, 0.25)),
    smoked=mat('smoked_acrylic', (0.55, 0.57, 0.6), 0.02, trans=1.0, ior=1.49),
    clear=mat('clear_acrylic', (0.98, 0.98, 1.0), 0.0, trans=1.0, ior=1.49),
    rail=mat('rail_steel', (0.7, 0.71, 0.72), 0.2, metal=1.0),
    wall=mat('wall_paint', (0.62, 0.62, 0.60), 0.92),
    floor=mat('concrete', (0.34, 0.33, 0.32), 0.6, bump=(60, 0.08)),
    bench_top=wood('butcher_block', (0.62, 0.43, 0.24), (0.48, 0.31, 0.16), scale=6, rough=0.35),
    bench_leg=mat('powder_black', (0.02, 0.02, 0.02), 0.6),
    flange=mat('spool_black', (0.02, 0.02, 0.02), 0.35, coat=0.3),
    cardboard=mat('cardboard', (0.45, 0.32, 0.19), 0.85, bump=(300, 0.05)),
    copper=mat('copper', (0.9, 0.55, 0.35), 0.3, metal=1.0),
    plate=mat('lcd_glass', (0.02, 0.02, 0.025), 0.05, coat=1.0),
)
def filament(rgb, name):
    m = mat(name, rgb, 0.28, coat=0.4)
    nt = m.node_tree; p = nt.nodes['Principled BSDF']          # winding grooves across the width
    tc = nt.nodes.new('ShaderNodeTexCoord'); w = nt.nodes.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'
    w.bands_direction = 'X'; w.inputs['Scale'].default_value = 175 * 0.5
    nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.6; b.inputs['Distance'].default_value = 0.0003
    nt.links.new(w.outputs['Fac'], b.inputs['Height']); nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return m
def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple((v/12.92) if v <= 0.04045 else ((v + 0.055)/1.055)**2.4 for v in c)

coll = sc.collection
def link(o, parent=None):
    coll.objects.link(o)
    if parent: o.parent = parent
    return o

def mesh_obj(name, verts, faces, material, parent=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.materials.append(material)
    return link(bpy.data.objects.new(name, me), parent)

def box(name, x0, x1, y0, y1, z0, z1, material, parent=None, bevel=0.0):
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    o = mesh_obj(name, v, f, material, parent)
    if bevel:
        bm = o.modifiers.new('bev', 'BEVEL'); bm.width = bevel; bm.segments = 3; bm.limit_method = 'ANGLE'
    return o

def cyl(name, r, p0, p1, material, parent=None, n=32, cap=True):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=cap, segments=n, radius1=r, radius2=r, depth=L)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(material)
    for poly in me.polygons: poly.use_smooth = True
    o = link(bpy.data.objects.new(name, me), parent)
    o.location = (p0 + p1) / 2; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return o

def tube_ring(name, r_out, r_in, width, center, axis, material, parent=None, n=96):
    """Annulus extruded along axis (for spool flanges / filament)."""
    bm = bmesh.new()
    a = bmesh.ops.create_circle(bm, cap_ends=False, segments=n, radius=r_out)['verts']
    b = bmesh.ops.create_circle(bm, cap_ends=False, segments=n, radius=r_in)['verts']
    faces = [bm.faces.new((a[i], a[(i+1) % n], b[(i+1) % n], b[i])) for i in range(n)]
    ext = bmesh.ops.extrude_face_region(bm, geom=faces)
    bmesh.ops.translate(bm, verts=[e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)], vec=(0, 0, width))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, -width/2))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(material)
    for poly in me.polygons: poly.use_smooth = True
    o = link(bpy.data.objects.new(name, me), parent)
    o.location = center; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(axis))
    return o

def spool(name, center, axis, colour, parent=None, D=0.200, W=0.068, fill=0.92):
    o = []
    rf = 0.050 + (D/2 - 0.004 - 0.050) * fill
    o.append(tube_ring(name + '_fil', rf, 0.050, W - 0.008, center, axis, filament(colour, name + '_mat'), parent))
    ax = Vector(axis).normalized()
    for s in (-1, 1):
        o.append(tube_ring(name + f'_fl{s}', D/2, 0.027, 0.0035, Vector(center) + ax * s * (W/2 - 0.00175), axis, M['flange'], parent))
    o.append(tube_ring(name + '_hub', 0.050, 0.027, W - 0.006, center, axis, M['flange'], parent))
    return o

# ------------------------------------------------------------------ room
box('floor', -4, 12, -6, 3, -0.02, 0.0, M['floor'])
box('wall', -4, 12, 0.78, 0.82, 0.0, 3.2, M['wall'])
box('wall_side', -1.6, -1.56, -6, 0.82, 0.0, 3.2, M['wall'])
# skirting board
box('skirting', -1.56, 6, 0.76, 0.78, 0.0, 0.09, mat('skirting', (0.8, 0.8, 0.78), 0.4))

# ------------------------------------------------------------------ wire shelving unit (48 x 24 x 72 in)
RW, RD, RH = 48*0.0254, 24*0.0254, 72*0.0254
RX0, RY0 = -0.06, 0.12
SHELVES = [0.16, 0.66, 1.26, 1.80]
rack = link(bpy.data.objects.new('rack', None))
for x in (RX0, RX0 + RW):
    for y in (RY0, RY0 + RD):
        cyl('post', 0.0127, (x, y, 0.035), (x, y, RH), M['chrome'], rack, n=24)
        cyl('foot', 0.016, (x, y, 0.0), (x, y, 0.035), M['bench_leg'], rack, n=24)
WIRE = 0.0022
def shelf(z):
    s = link(bpy.data.objects.new(f'shelf_{z}', None), rack)
    inset = 0.02
    xa, xb, ya, yb = RX0 + inset, RX0 + RW - inset, RY0 + inset, RY0 + RD - inset
    # perimeter frame: double rail front and back (truss), single on the sides
    for y in (ya, yb):
        cyl('rail', 0.003, (xa, y, z), (xb, y, z), M['chrome'], s, n=12)
        cyl('rail', 0.003, (xa, y, z - 0.028), (xb, y, z - 0.028), M['chrome'], s, n=12)
        n = 46
        for i in range(n):          # zig-zag truss
            x0 = xa + (xb - xa) * i / n; x1 = xa + (xb - xa) * (i + 1) / n
            za, zb = (z, z - 0.028) if i % 2 == 0 else (z - 0.028, z)
            cyl('truss', 0.0018, (x0, y, za), (x1, y, zb), M['chrome'], s, n=8, cap=False)
    for x in (xa, xb):
        cyl('rail', 0.003, (x, ya, z), (x, yb, z), M['chrome'], s, n=12)
        cyl('rail', 0.003, (x, ya, z - 0.028), (x, yb, z - 0.028), M['chrome'], s, n=12)
    # support bars under the deck
    for f in (0.33, 0.67):
        y = ya + (yb - ya) * f
        cyl('bar', 0.0022, (xa, y, z - 0.005), (xb, y, z - 0.005), M['chrome'], s, n=8)
    # deck wires front to back every 25 mm (array)
    nw = int((xb - xa - 0.024) / 0.0254) + 1
    for k in range(nw):
        xk = xa + 0.012 + k*0.0254
        cyl('deck', WIRE, (xk, ya, z + 0.0005), (xk, yb, z + 0.0005), M['chrome'], s, n=8, cap=False)
    # cross wires (side to side), two of them
    for f in (0.25, 0.75):
        y = ya + (yb - ya) * f
        cyl('xw', WIRE, (xa, y, z - 0.002), (xb, y, z - 0.002), M['chrome'], s, n=10)
    # post collars
    for x in (RX0, RX0 + RW):
        for y in (RY0, RY0 + RD):
            cyl('collar', 0.017, (x, y, z - 0.04), (x, y, z + 0.004), M['chrome'], s, n=24)
    return s
for z in SHELVES: shelf(z)

# ------------------------------------------------------------------ cabinets (CAD, mm -> m)
def import_ply(path, material, parent):
    if hasattr(bpy.ops.wm, 'ply_import'): bpy.ops.wm.ply_import(filepath=path)
    else: bpy.ops.import_mesh.ply(filepath=path)
    o = bpy.context.selected_objects[0]
    o.data.materials.clear(); o.data.materials.append(material)
    for poly in o.data.polygons: poly.use_smooth = False
    o.parent = parent
    return o

LAB = dict(PLA=['#e9e4d8', '#111111', '#c1121f', '#1d4ed8', '#16a34a', '#facc15', '#6b7280', '#ea580c', '#9333ea', '#db2777', '#0d9488', '#a16207'],
           PETG=['#f1f1ee', '#2f2f2f', '#d62828', '#2d7dd2', '#4caf2a', '#f2b705', '#8d99ae', '#ff7a1a', '#7b4fd6', '#e84393', '#11a3a3', '#f1f1ee'])
CAB_W = info['bbox'][3] * MM
def cabinet(name, x, y, z, label):
    root = link(bpy.data.objects.new('cab_' + name, None)); root.location = (x, y, z); root.scale = (MM, MM, MM)
    for f in sorted(os.listdir('/tmp/scene/ply')):
        k = f[:-4]
        import_ply('/tmp/scene/ply/' + f, M.get(k, M['part']), root)
    # spools (CAD coords in mm under the scaled root -> build in metres, then parent without scale)
    sroot = link(bpy.data.objects.new('spools_' + name, None)); sroot.location = (x, y, z)
    for s, col in zip(info['spools'], LAB[label]):
        c = Vector(s['c']) * MM
        spool(f'{name}_sp{s["row"]}{s["i"]}', c, (1, 0, 0), srgb(col), sroot, W=s['size'][0]*MM - 0.002)
    # screen: emissive label page behind the bezel window, facing -y
    t = info['tft']; sx, sz, sy = t['x']*MM, t['z']*MM, t['y']*MM - 0.0002
    w, h = t['w']*MM/2, t['h']*MM/2
    me = bpy.data.meshes.new('tft'); me.from_pydata([(sx - w, sy, sz - h), (sx + w, sy, sz - h), (sx + w, sy, sz + h), (sx - w, sy, sz + h)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(); [setattr(uv.data[i], 'uv', c) for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)])]
    me.materials.append(image_emit('label_' + label, f'/tmp/scene/tex/label_{label}.png', 2.2))
    link(bpy.data.objects.new('tft_' + name, me), sroot)
    # warm LED glow inside, under the header lip (the real strip is a line source)
    bpy.ops.object.light_add(type='AREA', location=(x + CAB_W/2, y + 0.06, z + 0.405))
    L = bpy.context.object; L.data.shape = 'RECTANGLE'; L.data.size = 0.46; L.data.size_y = 0.012
    L.data.energy = 9; L.data.color = (1.0, 0.86, 0.70); L.rotation_euler = (math.radians(180), 0, 0)
    return root

CY = RY0 + 0.012                                         # door front just behind the shelf's front rail
cabinet('pla', RX0 + 0.045, CY - 0.0, SHELVES[1] + 0.0045, 'PLA')
cabinet('petg', RX0 + RW - 0.045 - CAB_W, CY - 0.0, SHELVES[1] + 0.0045, 'PETG')

# props on the rack: filament boxes bottom shelf, a few spools top shelf
for i, (x, c) in enumerate(((0.05, 0.9), (0.30, 0.86), (0.55, 0.92), (0.80, 0.88))):
    bx = RX0 + x
    box(f'fbox{i}', bx, bx + 0.215, RY0 + 0.15, RY0 + 0.43, SHELVES[0] + 0.003, SHELVES[0] + 0.003 + 0.075 + 0.002*i, M['cardboard'], bevel=0.002)
for i, col in enumerate(['#3a3a3a', '#e8e8e2', '#b5121b']):
    spool(f'top{i}', (RX0 + 0.25 + i*0.10, RY0 + 0.30, SHELVES[3] + 0.101), (1, 0, 0), srgb(col))

# ------------------------------------------------------------------ workbench + printer (Voron 2.4 style, 350)
BX0, BX1, BY0, BY1, BZ = 1.45, 2.65, -0.02, 0.74, 0.88
box('bench_top', BX0, BX1, BY0, BY1, BZ - 0.04, BZ, M['bench_top'], bevel=0.003)
for x in (BX0 + 0.05, BX1 - 0.09):
    for y in (BY0 + 0.05, BY1 - 0.09):
        box('leg', x, x + 0.04, y, y + 0.04, 0.0, BZ - 0.04, M['bench_leg'], bevel=0.002)
box('stretcher', BX0 + 0.05, BX1 - 0.05, BY1 - 0.09, BY1 - 0.05, 0.12, 0.16, M['bench_leg'])
box('shelf_low', BX0 + 0.05, BX1 - 0.05, BY0 + 0.05, BY1 - 0.05, 0.16, 0.18, M['bench_top'])

def ext2020(name, p0, p1, parent):
    o = cyl(name, 0.01, p0, p1, M['alu_black'], parent, n=4)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = o.rotation_quaternion @ Matrix.Rotation(math.radians(45), 4, 'Z').to_quaternion()
    o.scale = (1.4142, 1.4142, 1)
    return o

PR = link(bpy.data.objects.new('printer', None))
F = 0.47; PX, PY = (BX0 + BX1)/2 - F/2 - 0.08, BY0 + 0.12
Z0 = BZ + 0.075                       # frame bottom, above feet and skirts
H = 0.55
def frame_box(z0, z1, top=True, bottom=True):
    for x in (PX + 0.01, PX + F - 0.01):
        for y in (PY + 0.01, PY + F - 0.01):
            ext2020('v', (x, y, z0), (x, y, z1), PR)
    for z in ([z0 + 0.01] if bottom else []) + ([z1 - 0.01] if top else []):
        for y in (PY + 0.01, PY + F - 0.01):
            ext2020('h', (PX + 0.02, y, z), (PX + F - 0.02, y, z), PR)
        for x in (PX + 0.01, PX + F - 0.01):
            ext2020('h', (x, PY + 0.02, z), (x, PY + F - 0.02, z), PR)
frame_box(Z0, Z0 + H)
frame_box(Z0 + H, Z0 + H + 0.12, top=True, bottom=False)                   # top hat
# skirts (printed, black, with orange accent strips) and feet
SK = M['frame']
for (x0, x1, y0, y1) in ((PX - 0.004, PX + F + 0.004, PY - 0.004, PY + 0.002), (PX - 0.004, PX + F + 0.004, PY + F - 0.002, PY + F + 0.004),
                         (PX - 0.004, PX + 0.002, PY, PY + F), (PX + F - 0.002, PX + F + 0.004, PY, PY + F)):
    box('skirt', x0, x1, y0, y1, BZ + 0.012, Z0 + 0.02, SK, bevel=0.002)
box('skirt_accent', PX + 0.02, PX + F - 0.02, PY - 0.0045, PY - 0.0035, BZ + 0.05, BZ + 0.056, M['orange'])
for x in (PX + 0.03, PX + F - 0.03):
    for y in (PY + 0.03, PY + F - 0.03):
        cyl('pfoot', 0.018, (x, y, BZ), (x, y, BZ + 0.012), M['rubber'], PR, n=24)
# display on the front skirt
me = bpy.data.meshes.new('lcd'); lx, lz = PX + F/2, BZ + 0.040
me.from_pydata([(lx - 0.045, PY - 0.0046, lz - 0.02), (lx + 0.045, PY - 0.0046, lz - 0.02), (lx + 0.045, PY - 0.0046, lz + 0.02), (lx - 0.045, PY - 0.0046, lz + 0.02)], [], [(0, 1, 2, 3)])
uv = me.uv_layers.new(); [setattr(uv.data[i], 'uv', c) for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)])]
me.materials.append(image_emit('printer_lcd', '/tmp/scene/tex/printer_lcd.png', 1.8)); link(bpy.data.objects.new('lcd', me), PR)
cyl('knob', 0.009, (lx + 0.075, PY - 0.004, lz), (lx + 0.075, PY - 0.016, lz), M['orange'], PR, n=24)
# panels: smoked sides/back, clear front doors, top hat clear, solid top
T = 0.003
box('panel_L', PX - 0.0035, PX - 0.0005, PY + 0.02, PY + F - 0.02, Z0 + 0.02, Z0 + H - 0.02, M['smoked'])
box('panel_R', PX + F + 0.0005, PX + F + 0.0035, PY + 0.02, PY + F - 0.02, Z0 + 0.02, Z0 + H - 0.02, M['smoked'])
box('panel_B', PX + 0.02, PX + F - 0.02, PY + F + 0.0005, PY + F + 0.0035, Z0 + 0.02, Z0 + H - 0.02, M['smoked'])
for x0, x1 in ((PX + 0.005, PX + F/2 - 0.002), (PX + F/2 + 0.002, PX + F - 0.005)):
    box('door', x0, x1, PY - 0.009, PY - 0.006, Z0 + 0.015, Z0 + H - 0.015, M['clear'])
    hx = x1 - 0.03 if x0 < PX + F/2 - 0.1 else x0 + 0.03
    box('handle', hx - 0.008, hx + 0.008, PY - 0.03, PY - 0.009, Z0 + H/2 - 0.06, Z0 + H/2 + 0.06, M['orange'], bevel=0.003)
for side in ((PX - 0.0035, PX - 0.0005, PY, PY + F), (PX + F + 0.0005, PX + F + 0.0035, PY, PY + F),
             (PX, PX + F, PY - 0.0035, PY - 0.0005), (PX, PX + F, PY + F + 0.0005, PY + F + 0.0035)):
    box('hat', side[0], side[1], side[2], side[3], Z0 + H + 0.005, Z0 + H + 0.115, M['clear'])
box('top', PX, PX + F, PY, PY + F, Z0 + H + 0.12, Z0 + H + 0.123, M['smoked'])
# panel clips (printed, orange)
for z in (Z0 + 0.12, Z0 + H - 0.12):
    for x in (PX + 0.002, PX + F - 0.002):
        box('clip', x - 0.006, x + 0.006, PY - 0.0045, PY + 0.004, z - 0.008, z + 0.008, M['orange'], bevel=0.0015)
# bed, gantry, toolhead
bz = Z0 + 0.30
box('bed', PX + 0.06, PX + F - 0.06, PY + 0.06, PY + F - 0.06, bz - 0.008, bz, M['alu'], bevel=0.001)
box('pei', PX + 0.065, PX + F - 0.065, PY + 0.065, PY + F - 0.065, bz, bz + 0.0008, M['pei'])
gz = Z0 + 0.44
for y in (PY + 0.035, PY + F - 0.035):
    ext2020('gy', (PX + 0.035, y, gz), (PX + F - 0.035, y, gz), PR)
for x in (PX + 0.035, PX + F - 0.035):
    ext2020('gx', (x, PY + 0.035, gz), (x, PY + F - 0.035, gz), PR)
    box('rail', x - 0.0045, x + 0.0045, PY + 0.05, PY + F - 0.05, gz + 0.010, gz + 0.016, M['rail'])
tx, ty = PX + F*0.58, PY + F*0.42
ext2020('xbeam', (PX + 0.04, ty, gz + 0.02), (PX + F - 0.04, ty, gz + 0.02), PR)
box('xrail', PX + 0.05, PX + F - 0.05, ty - 0.0045, ty + 0.0045, gz + 0.030, gz + 0.036, M['rail'])
# toolhead (printed, black body, orange face accents)
box('th_body', tx - 0.032, tx + 0.032, ty - 0.05, ty + 0.006, gz - 0.05, gz + 0.06, M['frame'], bevel=0.008)
box('th_face', tx - 0.026, tx + 0.026, ty - 0.053, ty - 0.049, gz - 0.035, gz + 0.045, M['orange'], bevel=0.004)
cyl('nozzle', 0.004, (tx, ty - 0.02, gz - 0.05), (tx, ty - 0.02, gz - 0.064), M['copper'], PR, n=16)
# print on the bed: a simple faceted vase in orange
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.035, depth=0.11, location=(tx - 0.02, ty - 0.02, bz + 0.055))
vase = bpy.context.object; vase.data.materials.append(M['orange'])
sd = vase.modifiers.new('tw', 'SIMPLE_DEFORM'); sd.deform_method = 'TWIST'; sd.angle = math.radians(60)
bpy.ops.object.shade_flat()
# corner Z belts / motors hint and drag chain
for x in (PX + 0.04, PX + F - 0.04):
    for y in (PY + 0.04, PY + F - 0.04):
        box('zbelt', x - 0.0045, x + 0.0045, y - 0.001, y + 0.001, Z0 + 0.05, gz, M['rubber'])
box('chain', PX + F - 0.075, PX + F - 0.06, PY + 0.05, PY + F - 0.08, gz + 0.04, gz + 0.055, M['rubber'], bevel=0.002)
# spool on the back holder
box('spool_holder', PX + F/2 - 0.01, PX + F/2 + 0.01, PY + F + 0.004, PY + F + 0.05, Z0 + H - 0.12, Z0 + H - 0.10, M['frame'])
spool('vspool', (PX + F/2, PY + F + 0.085, Z0 + H - 0.08), (1, 0, 0), srgb('#ff7a1a'))
# lights in the printer chamber (LED bars)
bpy.ops.object.light_add(type='AREA', location=(PX + F/2, PY + 0.06, Z0 + H - 0.03))
L = bpy.context.object; L.data.shape = 'RECTANGLE'; L.data.size = 0.40; L.data.size_y = 0.01; L.data.energy = 12
L.data.color = (0.92, 0.95, 1.0)

# ------------------------------------------------------------------ lighting + camera
def area(loc, target, size, energy, color=(1, 1, 1)):
    bpy.ops.object.light_add(type='AREA', location=loc); L = bpy.context.object
    L.data.size = size; L.data.energy = energy; L.data.color = color
    d = Vector(target) - Vector(loc); L.rotation_mode = 'QUATERNION'; L.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(d)
    return L
area((-0.9, -2.2, 2.6), (0.8, 0.3, 0.9), 2.2, 260, (1.0, 0.96, 0.9))         # key, upper left front
area((3.4, -1.8, 1.8), (1.6, 0.3, 0.9), 2.0, 90, (0.9, 0.95, 1.0))          # fill, right
area((1.0, 0.2, 3.0), (1.0, 0.3, 0.0), 3.0, 90)                               # ceiling bounce
world = bpy.data.worlds.new('world'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.36, 0.38, 0.42, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.12

cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 28; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 8
cam = link(bpy.data.objects.new('cam', cam_d)); sc.camera = cam
cam.location = (-0.75, -2.25, 1.42)
tgt = Vector((1.05, 0.36, 0.98))
cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (tgt - cam.location).to_track_quat('-Z', 'Y')
cam_d.dof.focus_distance = (Vector((0.6, 0.15, 0.9)) - cam.location).length

# ------------------------------------------------------------------ render
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception as e: print('denoiser:', e)
sc.cycles.max_bounces = 8; sc.cycles.transmission_bounces = 8; sc.cycles.glossy_bounces = 4; sc.cycles.diffuse_bounces = 3
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.cycles.blur_glossy = 1.0
sc.render.resolution_x = int(1920 * RES); sc.render.resolution_y = int(1200 * RES); sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = OUT
sc.render.threads_mode = 'AUTO'
bpy.ops.render.render(write_still=True)
print('rendered', OUT)
