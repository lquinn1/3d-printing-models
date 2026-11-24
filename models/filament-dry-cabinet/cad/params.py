# SPDX-License-Identifier: MIT
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
FOAM = 0.5 * IN             # 1/2 in XPS board: measured 0.5 in       TESTED
FOAM_CLR = 0.6              # pocket depth allowance over the foam board
WALL = SKIN + FOAM + FOAM_CLR          # = 15.7 mm (spec said 20; derived now)
assert abs(WALL - L.WALL) < 0.05, "update WALL in source/layout.py too"
RIB = 5.0                   # tile edge rib thickness
TILE_MAX = 330.0            # bed limit (Voron 2.4 350) with margin

# tongue and groove on mating rib faces
TONGUE_W, TONGUE_H = 1.6, 1.6           # width (across rib), height (protrusion)
GROOVE_CLR = 0.05                       # uniform gap on each V flank; retest   FIT

# M4 heat-set inserts + bolts across tile seams
INSERT_HOLE_D = 5.6         # typical M4 x 8.1 insert (CNC Kitchen / Ruthex) FIT
INSERT_DEPTH = 8.6
BOLT_CLEAR_D = 4.4
BOLT_HEAD_D, BOLT_HEAD_H = 7.4, 4.2     # M4 socket head + clearance
BOSS = 11.0                 # square boss around an insert

# ---------------------------------------------------------------- rods
ROD_OD = L.ROD_OD           # 26.67: measured 1.05 in, matches nominal   TESTED
CRADLE_CLR = 0.6            # radial clearance so the rod turns freely     FIT
COLLAR_GRIP = 0.35          # collar ID = ROD_OD - 2*grip (snaps on)       FIT
COLLAR_OD = 46.0            # stands 9.7 mm proud of the rod: keeps flanges apart
COLLAR_W = 5.0              # 80 mm pitch = 75 mm spool + 5 mm collar
SLOT_PITCH = L.PITCH

# ---------------------------------------------------------------- PTFE ports
PORT_D = 20.0               # nominal thread major diameter (M20 x 2 style)
PORT_P = 2.0
PORT_CLR = (0.15, 0.25, 0.35)   # radial clearances tested by the coupon FIT
PORT_CLR_SEL = 0.25         # chosen from the coupon (ABS)              TESTED
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

# ---------------------------------------------------------------- header + display
# 3.5 in 480x320 SPI TFT, capacitive touch (FT6336U), from the vendor drawing in docs/.
# Dimensions in the board's portrait frame: X across the 55.5 side, Y down the 98 side
# from the top edge (the 14-pin header is at the bottom). Mounted landscape in the header.
HEADER_H = 68.0
TFT_PCB = (55.5, 98.0)              # W x L
TFT_LENS = (55.5, 84.96)            # touch lens outline; starts 6.54 from the top edge
TFT_LENS_Y0 = 6.54
TFT_VA = (49.56, 74.04)             # touch / viewing area; starts 9.65 from the top, centred in X
TFT_VA_Y0 = 9.65
TFT_AA = (48.96, 73.44)             # LCD active area
TFT_HOLES = (49.5, 92.0)            # 4 x 3.2 mm holes, pad 4.7, pattern centred on the PCB
TFT_HOLE_D = 3.2
TFT_PINS_FROM_EDGE = 11.24          # first pin of the 14 x 2.54 header from the board edge
BEZEL_WIN_CLR = 0.5                 # window = VA + 0.5 each side, so a finger reaches the edges
# window centre is offset from the hole-pattern centre along the long axis:
TFT_VA_OFFSET = (TFT_VA_Y0 + TFT_VA[1]/2) - TFT_PCB[1]/2     # = -2.33 (towards the top edge)

if __name__ == "__main__":
    A = L.stadium(6, 120)
    ew = A['iw'] + 2*WALL; ed = A['idepth'] + WALL + L.DOOR; eh = A['ih'] + 2*WALL + L.FEET
    print(f"WALL {WALL:.1f} mm")
    print(f"exterior {ew:.0f} W x {ed:.0f} D (+50 pod = {ed+50:.0f}) x {eh:.0f} H mm"
          f" = {ew/IN:.1f} x {ed/IN:.1f} ({(ed+50)/IN:.1f}) x {eh/IN:.1f} in")
    print(f"TFT in header: {TFT_PCB[1]} x {TFT_PCB[0]} mm board, {(HEADER_H-TFT_PCB[0])/2:.2f} mm free above/below;"
          f" window {TFT_VA[1]+2*BEZEL_WIN_CLR:.1f} x {TFT_VA[0]+2*BEZEL_WIN_CLR:.1f}, offset {TFT_VA_OFFSET:+.2f} mm")
