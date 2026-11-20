import cadquery as cq, math

R_SKIRT = 43.808          # egg skirt outer radius (from egg.py)
CLR = 0.35                # radial clearance
BORE_R = R_SKIRT + CLR    # collar bore
HB = 80.0                 # base height
SKIRT = 12.0
DECK_T = 3.5
LEDGE_Z = HB - SKIRT - DECK_T
LEDGE_R = 40.0            # deck rests on ledge 40 -> BORE_R
WALL = 3.0
SOCKET_HOLE = 41.0        # through-hole for the socket's threaded neck

# ---------- outer profile (r, z) ----------
# one continuous tangent-smooth curve: rounded foot -> bell flare -> soft bead -> rim
OUTER_SPL = [(72.0, 0.0), (72.0, 1.6), (71.2, 4.2), (68.6, 8.0), (61.5, 18), (54.0, 35), (50.0, 52),
             (48.7, 63), (48.6, 69), (49.5, 73.5), (49.6, 76.0), (48.9, 78.8), (48.0, 80.0)]

ARC_PTS = [(72, 1.2), (69.2, 7.2), (55.0, 32.0), (48.8, 62.0), (49.4, 72.5), (48.0, 80.0)]
def outer_profile(wp, dr=0.0):
    # chain of tangent-continuous arcs (analytic torus/cone faces -> perfectly round & clean mesh)
    wp = wp.lineTo(ARC_PTS[0][0] - dr, ARC_PTS[0][1])
    for p in ARC_PTS[1:]:
        wp = wp.tangentArcPoint((p[0] - dr, p[1]), relative=False)
    return wp
outer = OUTER_SPL
# ---------- inner profile: offset of outer, then 45 deg ledge, then bore ----------
inner = [(72 - WALL - 1.5, 0), (66 - WALL + 0.5, 6.5), (61 - WALL, 18), (53.5 - WALL, 36), (49.5 - WALL, 54)]
r_last, z_last = inner[-1]
z_ch = LEDGE_Z - (r_last - LEDGE_R)   # start of 45-degree chamfer

prof = (outer_profile(cq.Workplane('XZ').moveTo(72.0, 0.0))
        .lineTo(BORE_R, HB).lineTo(BORE_R, LEDGE_Z).lineTo(LEDGE_R, LEDGE_Z)
        .lineTo(r_last, z_ch)
        .spline(list(reversed(inner[1:-1])) + [inner[0]], includeCurrent=True)
        .close())
base = prof.revolve(360, (0, 0, 0), (0, 1, 0))

# cord exit notch (arched) at the rim
notch = (cq.Workplane('YZ').moveTo(-4.75, -1).lineTo(4.75, -1).lineTo(4.75, 5)
         .threePointArc((0, 9.75), (-4.75, 5)).close().extrude(30)
         .translate((55, 0, 0)))
base = base.cut(notch)
# ---------- engraved quote, wrapped around the front (opposite the cord notch) ----------
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf'
LINES = [("Dream bravely,", 50.0, 9.5), ("little one.", 35.5, 9.5)]   # (text, z centre, cap size)
ENGRAVE = 0.8
outer_only = (outer_profile(cq.Workplane('XZ').moveTo(0, 0).lineTo(72.0, 0.0))
              .lineTo(0, HB).close().revolve(360, (0, 0, 0), (0, 1, 0)))
skin_in = (outer_profile(cq.Workplane('XZ').moveTo(0, 0).lineTo(72.0 - ENGRAVE - 0.05, 0),
                         ENGRAVE + 0.05).lineTo(0, HB).close().revolve(360, (0, 0, 0), (0, 1, 0)))
skin = outer_only.cut(skin_in)

def text_w(t, size):
    if not t.strip():
        return 0.0
    bb = cq.Workplane('XZ').text(t, size, 1, fontPath=FONT, halign='left', valign='center').val().BoundingBox()
    return bb.xmax
def outer_r_at(z):
    sec = outer_only.section(z).val().BoundingBox(); return sec.xmax

glyphs = None
for text, zc, size in LINES:
    R = outer_r_at(zc)
    total = text_w(text, size)
    for i, ch in enumerate(text):
        if ch == ' ':
            continue
        right = text_w(text[:i + 1], size)
        g = cq.Workplane('XZ').text(ch, size, 24, fontPath=FONT, halign='left', valign='center').val()
        gb = g.BoundingBox()
        xc = right - gb.xlen / 2 - (gb.xmax - gb.xlen) * 0          # glyph centre along the line
        g = g.translate(cq.Vector(-(gb.xmin + gb.xlen / 2), 12, zc))  # centre glyph, straddle y=0
        phi = math.pi + (xc - total / 2) / R
        g = g.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), math.degrees(phi) + 90)
        g = g.translate(cq.Vector(R * math.cos(phi), R * math.sin(phi), 0))
        glyphs = g if glyphs is None else glyphs.fuse(g)
engrave = cq.Workplane('XY').add(glyphs).intersect(skin)
base = base.cut(engrave)
base_solid = base.val().clean()

# ---------- socket deck (separate, prints flat; sleeve prints pointing up, hangs down in use) ----------
SOCKET_OD = 37.45          # measured socket casing diameter
BORE_CLR = 0.40            # bore is this much larger than the casing ...
RIB_D = 37.00              # ... and 6 crush ribs pinch it down to this (0.45 mm diametral interference; chosen from fit coupon)
N_RIBS, RIB_R = 6, 0.8     # rib count / rib round radius
SLEEVE_H, SLEEVE_W = 12.0, 2.4

def gripper(rib_d, sleeve_h=SLEEVE_H):
    """Returns (sleeve_body, ribbed_bore_tool). Body gets unioned, tool gets cut."""
    bore_r = (SOCKET_OD + BORE_CLR) / 2
    tot_h = DECK_T + sleeve_h
    body = cq.Workplane('XY').circle(bore_r + SLEEVE_W).extrude(tot_h)
    tip_r = rib_d / 2
    ribs = cq.Workplane('XY').polarArray(tip_r + RIB_R, 0, 360, N_RIBS).circle(RIB_R).extrude(tot_h + 2).translate((0, 0, -1))
    tool = cq.Workplane('XY').circle(bore_r).extrude(tot_h + 2).translate((0, 0, -1)).cut(ribs)
    # lead-in cones at both ends so the ribs ramp up instead of shearing off
    lead = 2.0
    cone = (cq.Workplane('XZ').moveTo(0, -1).lineTo(bore_r + 0.6 + 1 * (bore_r + 0.6 - tip_r) / lead, -1)
            .lineTo(tip_r - 0.05, lead).lineTo(0, lead).close().revolve(360, (0, 0, 0), (0, 1, 0)))
    tool = tool.union(cone).union(cone.mirror('XY').translate((0, 0, tot_h)))
    return body, tool

DECK_R = BORE_R - 0.3
deck = cq.Workplane('XY').circle(DECK_R).extrude(DECK_T).edges('<Z').chamfer(0.6)
g_body, g_tool = gripper(RIB_D)
deck = deck.union(g_body).cut(g_tool)
vents = cq.Workplane('XY').polarArray(32.5, 0, 360, 10).circle(2.6).extrude(DECK_T)
deck = deck.cut(vents)
# two finger slots to lift the deck out
slots = (cq.Workplane('XY').polarArray(DECK_R - 1.5, 90, 360, 2)
         .slot2D(9, 4, 90).extrude(DECK_T))
deck = deck.cut(slots)
deck_solid = deck.val().clean()

# ---------- fit coupon: four short grippers, interference 0.45 / 0.30 / 0.15 / 0.00 mm ----------
SIZES = (37.00, 37.15, 37.30, 37.45)
pitch = 52
coupon = cq.Workplane('XY').rect(4 * pitch, 64).extrude(2.4).edges('|Z').fillet(4)
for i, d in enumerate(SIZES):
    x = (i - 1.5) * pitch
    a_, b_ = gripper(d, sleeve_h=6.0)
    coupon = coupon.union(a_.translate((x, 4, 0))).cut(b_.translate((x, 4, 0)))
    coupon = coupon.cut(cq.Workplane('XY').workplane(offset=2.4 - 0.6).center(x, -26)
                        .text(f'{d:.2f}', 5.5, 0.6, kind='bold', combine=False))
coupon = coupon.val().clean()
SHRINK = 1.006

if __name__ == '__main__':
    print('base valid', base_solid.isValid(), 'deck', deck_solid.isValid(), 'ledge z', LEDGE_Z, 'chamfer start', z_ch)
    for name, s in [('nightlight_base', base_solid), ('socket_deck', deck_solid), ('socket_hole_test_coupon', coupon)]:
        s = s.scale(SHRINK)
        cq.exporters.export(s, f'out10/{name}.step')
        cq.exporters.export(s, f'out10/{name}.stl', tolerance=0.01, angularTolerance=0.04)
    print('ok')
