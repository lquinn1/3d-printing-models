"""Single source of truth for the dry cabinet CAD (all mm).

Layout numbers come from source/layout.py; everything printed is defined here.
Values marked FIT are settled by the fit-test coupons (cad/coupons.py).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source'))
import layout as L

IN = 25.4

# ---------------------------------------------------------------- shell / wall
SKIN = 2.4                  # outer printed skin of a tile (6 perimeters-ish at 0.4)
FOAM = 0.5 * IN             # 1/2 in XPS board (measure yours)            FIT
FOAM_CLR = 0.6              # pocket depth allowance over the foam board
WALL = SKIN + FOAM + FOAM_CLR          # = 15.7 mm (spec said 20; derived now)
assert abs(WALL - L.WALL) < 0.05, "update WALL in source/layout.py too"
RIB = 5.0                   # tile edge rib thickness
TILE_MAX = 330.0            # bed limit (Voron 2.4 350) with margin

# tongue and groove on mating rib faces
TONGUE_W, TONGUE_H = 1.6, 1.6           # width (across rib), height (protrusion)
GROOVE_CLR = 0.2                        # each side                    FIT

# M4 heat-set inserts + bolts across tile seams
INSERT_HOLE_D = 5.6         # typical M4 x 8.1 insert (CNC Kitchen / Ruthex) FIT
INSERT_DEPTH = 8.6
BOLT_CLEAR_D = 4.4
BOLT_HEAD_D, BOLT_HEAD_H = 7.4, 4.2     # M4 socket head + clearance
BOSS = 11.0                 # square boss around an insert

# ---------------------------------------------------------------- rods
ROD_OD = L.ROD_OD           # 26.67 nominal 3/4 in Sch 40 (measure yours)  FIT
CRADLE_CLR = 0.6            # radial clearance so the rod turns freely     FIT
COLLAR_GRIP = 0.35          # collar ID = ROD_OD - 2*grip (snaps on)       FIT
COLLAR_OD = 46.0            # stands 9.7 mm proud of the rod: keeps flanges apart
COLLAR_W = 5.0              # 80 mm pitch = 75 mm spool + 5 mm collar
SLOT_PITCH = L.PITCH

# ---------------------------------------------------------------- PTFE ports
PORT_D = 20.0               # nominal thread major diameter (M20 x 2 style)
PORT_P = 2.0
PORT_CLR = (0.15, 0.25, 0.35)   # radial clearances tested by the coupon FIT
PORT_CLR_SEL = 0.25         # value used in the real parts until tested
SOCKET_LEN = WALL           # socket sleeve runs right through the wall
SOCKET_OD = 30.0
SHANK_LEN = 14.0            # module thread length (shorter than the socket)
FLANGE_AF = 30.0            # hex flange across flats
FLANGE_H_PLUG = 5.0
FLANGE_H_MODULE = 9.0       # deep enough for the PC4-M10 thread
# O-ring: face seal under the flange. 22 x 2 mm (ID x CS).
# (The v0.6 spec said 16 x 2, but a 16 mm ID ring can't go round an M20 thread.)
ORING_ID, ORING_CS = 22.0, 2.0
GROOVE_DEPTH = 1.5          # ~25 % squeeze
GROOVE_W = 2.7
PC4_HOLE_D = 9.0            # PC4-M10 couplers self-thread into ~9 mm in ABS FIT
PC4_HOLE_DEPTH = 8.0
PTFE_BORE = 4.4             # 4 mm OD PTFE guide tube passes through

if __name__ == "__main__":
    A = L.stadium(6, 120)
    ew = A['iw'] + 2*WALL; ed = A['idepth'] + WALL + L.DOOR; eh = A['ih'] + 2*WALL + L.FEET
    print(f"WALL {WALL:.1f} mm")
    print(f"exterior {ew:.0f} W x {ed:.0f} D (+50 pod = {ed+50:.0f}) x {eh:.0f} H mm"
          f" = {ew/IN:.1f} x {ed/IN:.1f} ({(ed+50)/IN:.1f}) x {eh/IN:.1f} in")
