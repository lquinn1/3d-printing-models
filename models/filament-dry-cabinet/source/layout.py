"""Layout calculator for the filament dry cabinet (all mm)."""
import math
IN = 25.4
# spools
SPOOL_D, SPOOL_W = 200.0, 75.0          # 1 kg spool, widest common width
SPOOL_CLR = 7.0                         # min gap between spool rims
PITCH = 80.0                            # slot pitch across the width
# rods: 3/4 in Sch 40 PVC
ROD_OD = 1.050 * IN                     # 26.67
ROD_CC = 110.0                          # spacing of the two rods under each row
# spool centre height above rod centres (rim resting on both rods)
R = SPOOL_D / 2
C_ABOVE_RODS = math.sqrt((R + ROD_OD/2)**2 - (ROD_CC/2)**2)
# shell
WALL = 20.0                             # printed tile + 1/2 in XPS foam
DOOR = 28.0                             # door frame with twin-wall polycarbonate
FEET = 15.0
CLR = 15.0                              # clearance spool <-> wall/door

def stadium(n_across, h_offset, lift_access=True):
    """Two rows (front low, back raised by h_offset)."""
    d = math.sqrt((SPOOL_D + SPOOL_CLR)**2 - h_offset**2) if h_offset < SPOOL_D + SPOOL_CLR else 0
    iw = n_across * PITCH + 2 * 10
    idepth = CLR + R + d + R + CLR
    rod_z_front = 35.0                  # rod centre above floor
    cf = rod_z_front + C_ABOVE_RODS     # front spool centre
    cb = cf + h_offset
    top_back = cb + R
    top_front = cf + R
    lift = max(0.0, (top_front + 5) - (cb - R)) if lift_access else 0.0
    ih = top_back + lift + 15
    ew, ed, eh = iw + 2*WALL, idepth + WALL + DOOR, ih + 2*WALL + FEET
    return dict(n=2*n_across, iw=iw, idepth=idepth, ih=ih, ew=ew, ed=ed, eh=eh,
                d=d, cf=cf, cb=cb, rod_front=rod_z_front, rod_back=rod_z_front+h_offset,
                y_front=CLR+R, y_back=CLR+R+d, lift=lift, top_front=top_front, top_back=top_back)

def single(n_across, tiers, tier_pitch=240):
    iw = n_across*PITCH + 20; idepth = CLR + SPOOL_D + CLR
    ih = 35 + C_ABOVE_RODS + R + (tiers-1)*tier_pitch + 25
    return dict(n=n_across*tiers, iw=iw, idepth=idepth, ih=ih, ew=iw+2*WALL, ed=idepth+WALL+DOOR, eh=ih+2*WALL+FEET)

if __name__ == "__main__":
    print(f"spool centre above rod centres: {C_ABOVE_RODS:.1f} mm; rod OD {ROD_OD:.2f}")
    A = stadium(6, 120)
    print("A  1 tier, 2 rows x 6 (offset 120):", {k: round(v,1) for k,v in A.items()})
    for k in ('ew','ed','eh'): print(f"   {k} = {A[k]:.0f} mm = {A[k]/IN:.1f} in")
    A2 = stadium(6, 120, lift_access=False)
    print("A' same without lift room:", round(A2['eh']), "mm", round(A2['eh']/IN,1), "in")
    B = stadium(3, 120)
    print("B  2 tiers x (2 rows x 3): W %.0f D %.0f H %.0f mm (%.1f x %.1f x %.1f in)" % (B['ew'],B['ed'],2*B['ih']+2*WALL+FEET, B['ew']/IN,B['ed']/IN,(2*B['ih']+2*WALL+FEET)/IN))
    C = single(4, 3)
    print("C  3 tiers x 4, single row: W %.0f D %.0f H %.0f mm (%.1f x %.1f x %.1f in)" % (C['ew'],C['ed'],C['eh'],C['ew']/IN,C['ed']/IN,C['eh']/IN))
    # dead space under back row for heater/desiccant
    print("void under back rods: from floor to back rod bottom = %.0f mm tall, %.0f mm deep" % (A['rod_back']-ROD_OD/2, A['idepth']-A['y_back']+R- (A['y_back']-R- A['y_front']) ))
