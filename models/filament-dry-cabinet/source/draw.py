# SPDX-License-Identifier: MIT
import math, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, Polygon
from layout import *
A = stadium(6, 120)
IN=25.4
T=WALL; ID, IH, IW = A['idepth'], A['ih'], A['iw']
POD = 50.0

# ---------------- side section ----------------
fig, ax = plt.subplots(figsize=(11, 9))
# coordinates: y = 0 at inside face of door, increasing to the back; z = 0 at interior floor
ED = A['ed']; EH = A['eh']
y0 = -DOOR; z0 = -T - FEET
shell = '#3b3b3b'
# outer shell: floor, roof, back wall
ax.add_patch(Rectangle((0, -T), ID, T, color=shell))                 # floor
ax.add_patch(Rectangle((0, IH), ID, T, color=shell))                 # roof
ax.add_patch(Rectangle((ID, -T), T, IH+2*T, color=shell))            # back wall
for yy in (5, ID-60): ax.add_patch(Rectangle((yy, -T-FEET), 50, FEET, color='#222'))  # feet
# foam hatch inside walls
for r in [(0,-T+4,ID,T-8),(0,IH+4,ID,T-8),(ID+4,-T,T-8,IH+2*T)]:
    ax.add_patch(Rectangle(r[:2], r[2], r[3], facecolor='#f2d16b', alpha=0.55, hatch='////', edgecolor='#c9a227', lw=0))
# door (twin-wall polycarbonate) + header
ax.add_patch(Rectangle((-DOOR, -T), DOOR, IH+2*T-HEADER, facecolor='#9fd3f5', alpha=0.6, edgecolor='#333'))
ax.add_patch(Rectangle((-DOOR, IH+T-HEADER), DOOR+8, HEADER, color='#222'))
ax.text(-DOOR-6, IH+T-HEADER/2, 'header (68 mm):\nNFC pad, 3.5" TFT\n(label), encoder', ha='right', va='center', fontsize=8)
ax.text(-DOOR-6, IH/2-40, 'door: printed frame,\n2 x polycarbonate\n+ air gap, neoprene seal,\nflush lift-bar latch', ha='right', va='center', fontsize=8)
# rear control pod
ax.add_patch(Rectangle((ID+T, 30), POD, 230, facecolor='#555', edgecolor='#222'))
ax.text(ID+T+POD/2, 145, 'control pod\n(outside chamber)\nIEC C14 fused inlet\n24 V PSU, ESP32', rotation=90, ha='center', va='center', color='white', fontsize=8)
# rods + spools
def rodpair(yc, zc):
    for dy in (-ROD_CC/2, ROD_CC/2):
        ax.add_patch(Circle((yc+dy, zc), ROD_OD/2, color='white', ec='#888', zorder=5))
def cradle(yc, zc):
    ax.add_patch(Rectangle((yc-ROD_CC/2-22, 0 if zc<60 else 0), ROD_CC+44, zc-ROD_OD/2+2, facecolor='#777', alpha=0.35, zorder=1))
rodpair(A['y_front'], A['rod_front']); rodpair(A['y_back'], A['rod_back'])
for yc, cz, col, lab in ((A['y_front'], A['cf'], '#e8590c', 'front row F1-F6'), (A['y_back'], A['cb'], '#2f9e44', 'back row B1-B6 (raised 120)')):
    ax.add_patch(Circle((yc, cz), R, facecolor=col, alpha=0.35, edgecolor=col, lw=2, zorder=3))
    ax.add_patch(Circle((yc, cz), 28, facecolor='white', edgecolor=col, zorder=4))
    ax.text(yc, cz+R+8, lab, ha='center', fontsize=9, color=col)
# back-row support stand (printed riser on side walls)
ax.add_patch(Rectangle((A['y_back']-ROD_CC/2-20, 0), ROD_CC+40, A['rod_back']-ROD_OD/2, facecolor='none', edgecolor='#999', ls='--'))
# void contents: heater + fan + desiccant
vy0 = A['y_front']+R+8; vy1 = ID-6
ax.add_patch(Rectangle((vy0, 8), vy1-vy0, 50, facecolor='#ff8787', edgecolor='#c92a2a'))
ax.text((vy0+vy1)/2, 33, 'PTC heater + PWM fan duct', ha='center', va='center', fontsize=8)
ax.add_patch(Rectangle((vy0, 64), vy1-vy0, 60, facecolor='#ffd8a8', edgecolor='#e67700'))
ax.text((vy0+vy1)/2, 94, 'desiccant cartridges\n(silica gel, pull-out)', ha='center', va='center', fontsize=8)
ax.text((vy0+vy1)/2, 132, 'service void under back row', ha='center', fontsize=7, color='#555')
# airflow
ax.add_patch(FancyArrowPatch((vy0+5, 20), (A['y_front']+30, 25), arrowstyle='->', mutation_scale=15, color='#c92a2a'))
ax.add_patch(FancyArrowPatch((60, 40), (60, IH-40), connectionstyle='arc3,rad=-0.2', arrowstyle='->', mutation_scale=15, color='#c92a2a'))
ax.add_patch(FancyArrowPatch((ID-40, IH-40), (ID-40, 130), connectionstyle='arc3,rad=-0.2', arrowstyle='->', mutation_scale=15, color='#1971c2'))
ax.text(40, IH-25, 'warm air up the front', fontsize=8, color='#c92a2a')
ax.text(ID-150, IH-25, 'return through desiccant', fontsize=8, color='#1971c2')
# closable PTFE ports: top (one per slot) and back (above the control pod)
PORT='#7048e8'
for yp in (A['y_front'], A['y_back']):
    ax.add_patch(Rectangle((yp-9, IH-2), 18, T+6, facecolor=PORT, edgecolor='k', zorder=7))
    ax.plot([yp, yp], [A['cf']+R if yp==A['y_front'] else A['cb']+R, IH-2], ls=':', color=PORT, lw=1.5)
for zp in (IH-62, IH-36):
    ax.add_patch(Rectangle((ID-2, zp-9), T+6, 18, facecolor=PORT, edgecolor='k', zorder=7))
ax.plot([A['y_front'], A['y_front']+60, ID-2], [A['cf']+R, IH-36, IH-36], ls=':', color=PORT, lw=1.5)
ax.text(A['y_front']+15, IH+T+14, 'closable PTFE ports (top, 1 per slot)', color=PORT, fontsize=8)
ax.text(ID+T+10, IH-49, 'closable PTFE\nports (back)', color=PORT, fontsize=8, va='center')
# stacking: pockets in the roof that take the next cabinet's feet
for yy in (5, ID-60):
    ax.add_patch(Rectangle((yy, IH+T-FEET), 50, FEET, facecolor='white', edgecolor='#222', ls='--'))
ax.text(5, IH+T+14, 'stacking pocket', fontsize=7, color='#444')
# LED strip
ax.add_patch(Rectangle((5, IH-6), 10, 6, color='#fab005', zorder=6)); ax.text(18, IH-14, 'SK6812 strip', fontsize=7)
# sensors
ax.plot([ID/2], [IH-30], 'ks'); ax.text(ID/2+6, IH-35, 'SHT45 chamber', fontsize=7)
# lift clearance
xl = A['y_back'] - R - 14
ax.annotate('', xy=(xl, A['top_back']+A['lift']), xytext=(xl, A['top_back']), arrowprops=dict(arrowstyle='<->'))
ax.text(xl-4, A['top_back']+A['lift']/2, f"{A['lift']:.0f} lift room\nfor back spools", fontsize=7, va='center', ha='right')
# dimensions
def dim(p0, p1, txt, off, horiz=True):
    if horiz:
        ax.annotate('', xy=(p1, off), xytext=(p0, off), arrowprops=dict(arrowstyle='<->'))
        ax.text((p0+p1)/2, off-14, txt, ha='center', va='top', fontsize=9)
    else:
        ax.annotate('', xy=(off, p1), xytext=(off, p0), arrowprops=dict(arrowstyle='<->'))
        ax.text(off+8, (p0+p1)/2, txt, va='center', fontsize=9, rotation=90)
dim(-DOOR, ID+T, f"cabinet {A['ed']:.0f} mm ({A['ed']/IN:.1f} in)", -T-FEET-25)
dim(-DOOR, ID+T+POD, f"with rear control pod {A['ed']+POD:.0f} mm ({(A['ed']+POD)/IN:.1f} in)  < 20 in", -T-FEET-75)
dim(-T-FEET, IH+T, f"{round(A['eh']+0.5):.0f} mm ({A['eh']/IN:.1f} in)", ID+T+POD+25, horiz=False)
ax.annotate('', xy=(A['y_back'], A['cb']-R-25), xytext=(A['y_front'], A['cb']-R-25), arrowprops=dict(arrowstyle='<->', color='#555'))
ax.text((A['y_front']+A['y_back'])/2, A['cb']-R-40, f"rows {A['d']:.0f} apart", ha='center', fontsize=8, color='#555')
ax.set_xlim(-190, ID+T+POD+80); ax.set_ylim(-T-FEET-120, IH+T+40)
ax.set_aspect('equal'); ax.axis('off')
ax.set_title('Side section (front on the left): 12 spools, 2 offset rows x 6, PTFE ports, stackable', fontsize=12)
plt.savefig('layout_side.png', dpi=110, bbox_inches='tight')

# ---------------- front view ----------------
fig, ax = plt.subplots(figsize=(11, 8.2))
EW = A['ew']
ax.add_patch(Rectangle((-T, -T-FEET), EW, A['eh'], facecolor='#2b2b2b'))
# door glass and header
htop = IH + T; hy = htop - HEADER
ax.add_patch(Rectangle((0, -T+12), IW, hy-4-(-T+12), facecolor='#cfe8fc', alpha=0.9, edgecolor='#111', lw=3))
# NFC tap zone: orange overlay over the PN5180 antenna (front.py nfc_tap_overlay)
from matplotlib.patches import FancyBboxPatch
ax.add_patch(FancyBboxPatch((100-32+3, hy+HEADER/2-23+3), 64-6, 46-6, boxstyle='round,pad=3', facecolor='#e8833a', edgecolor='none'))
ax.add_patch(FancyBboxPatch((92-4.5, hy+HEADER/2+7.5-9.5), 9, 19, boxstyle='round,pad=1.5', facecolor='none', edgecolor='#9c4a14', lw=1.3))
for r in (5, 8.5, 12):
    ax.add_patch(matplotlib.patches.Arc((98.5, hy+HEADER/2+7.5), 2*r, 2*r, theta1=-42, theta2=42, color='#9c4a14', lw=1.3))
ax.text(100, hy+HEADER/2-13.5, 'TAP HERE', ha='center', va='center', color='#9c4a14', fontsize=6.5, weight='bold')
ax.text(100, hy+1, 'NFC (OpenPrintTag)', ha='center', va='bottom', fontsize=5.5, color='white')
# 3.5 in IPS touch TFT, centred: material name on a colour band + status line
cx, cz = IW/2, hy+HEADER/2
ax.add_patch(FancyBboxPatch((cx-37.5-5.5+3, cz-25.3-5.5+3), 75+11-6, 50.6+11-6, boxstyle='round,pad=3', facecolor='#e8833a', edgecolor='none'))   # orange bezel
ax.add_patch(Rectangle((cx-37, cz-24.8), 74, 49.6, facecolor='#050608', edgecolor='none'))
# label page as the firmware draws it (firmware/dry-cabinet.yaml): band = top 220 of 320 px
ax.add_patch(Rectangle((cx-37, cz+24.8-49.6*220/320), 74, 49.6*220/320, facecolor='#1c6dd0'))
ax.text(cx, cz+24.8-49.6*110/320, 'PETG', ha='center', va='center', color='white', fontsize=17, weight='bold')
ax.text(cx-33, cz+24.8-49.6*270/320, '47.8°C  18%', ha='left', va='center', color='white', fontsize=5, weight='bold')
ax.text(cx+33, cz+24.8-49.6*270/320, 'Maintain', ha='right', va='center', color='#8c939c', fontsize=4.5)
ax.text(cx, hy+0.5, '3.5" IPS touch TFT (label + menu)', ha='center', va='bottom', fontsize=5.5, color='white')
ax.add_patch(Circle((375, hy+HEADER/2), 12, facecolor='#e8833a', edgecolor='#9c4a14'))
ax.text(375, hy+1, 'encoder', ha='center', va='bottom', fontsize=6, color='white')
# flush lift-bar latch in the right door stile
ax.add_patch(Rectangle((IW-2, 94), 9, 135, facecolor='#e8833a', edgecolor='#111', lw=0.8))
ax.text(IW+8, 160, 'lift-bar latch\n(pull the bottom)', fontsize=8, va='center')
# LED strip just inside, under the header
ax.add_patch(Rectangle((10, hy-14), IW-20, 6, color='#fab005'))
for i in range(6):
    xc = 10 + PITCH*(i+0.5)
    # back row (higher) behind
    ax.add_patch(Rectangle((xc-SPOOL_W/2+2, A['cb']-R), SPOOL_W-4, SPOOL_D, facecolor='#2f9e44', alpha=0.35, edgecolor='#2f9e44'))
    ax.text(xc, A['cb']+R-22, f'B{i+1}', ha='center', fontsize=10, color='#1b6e2c', weight='bold')
    ax.add_patch(Rectangle((xc-SPOOL_W/2+2, A['cf']-R), SPOOL_W-4, SPOOL_D, facecolor='#e8590c', alpha=0.55, edgecolor='#e8590c'))
    ax.text(xc, A['cf'], f'F{i+1}', ha='center', va='center', fontsize=12, color='white', weight='bold')
    # index collar on front rod
    ax.add_patch(Rectangle((xc-PITCH/2+1, A['rod_front']-ROD_OD/2-4), 6, ROD_OD+8, color='#495057'))
    ax.add_patch(Rectangle((xc-PITCH/2+1, A['rod_back']-ROD_OD/2-4), 6, ROD_OD+8, color='#495057'))
    # slot number strip on door bottom rail
    ax.text(xc, -T+2, f'{i+1}', ha='center', va='bottom', fontsize=9, color='white')
for z in (A['rod_front'], A['rod_back']):
    ax.add_patch(Rectangle((0, z-ROD_OD/2), IW, ROD_OD, facecolor='white', edgecolor='#888', alpha=0.9))
ax.text(IW/2, -T-FEET-28, f"{A['ew']:.0f} mm ({A['ew']/IN:.1f} in) wide x {round(A['eh']+0.5):.0f} mm ({A['eh']/IN:.1f} in) tall", ha='center', fontsize=10)
ax.text(IW+8, A['rod_front'], '1 in poplar dowel rods\n+ index collars', fontsize=8, va='center')
ax.text(IW+8, IH+T-HEADER-11, 'SK6812 strip\n(5 LEDs per slot)', fontsize=8, va='center')
ax.set_xlim(-T-10, EW+90); ax.set_ylim(-T-FEET-45, A['eh']-T-FEET+10)
ax.set_aspect('equal'); ax.axis('off')
ax.set_title('Front view: slots F1-F6 / B1-B6, NFC tap zone, 3.5" touch TFT (shows the label), encoder', fontsize=12)
plt.savefig('layout_front.png', dpi=110, bbox_inches='tight')
print('ok')
