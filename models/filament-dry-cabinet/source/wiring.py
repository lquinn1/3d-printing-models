# SPDX-License-Identifier: MIT
"""Cabinet wiring (v0.18): every wire from the mains inlet to the LED strip, drawn by zone
(rear pod, chamber, header bay) and listed in one table.

Writes images/wiring.png and wiring/wire_list.csv; prints the markdown table for DESIGN.md §19.
Connector names (J1..J11 on the controller, J1..J7 on the front breakout) match pcb/circuit.py.
"""
import os, csv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')

# ID, from, to, signal, wire, colour, length, route, notes
WIRES = [
    ('W1', 'IEC inlet L (after its switch and fuse)', 'PSU L', '120 V line', '18 AWG UL1015', 'black', '0.3 m', 'pod (mains side)', 'Ferrules on both ends'),
    ('W2', 'IEC inlet N', 'PSU N', '120 V neutral', '18 AWG UL1015', 'white', '0.3 m', 'pod (mains side)', 'Ferrules'),
    ('W3', 'IEC inlet earth', 'PSU FG (earth)', 'protective earth', '18 AWG UL1015', 'green', '0.3 m', 'pod (mains side)', 'Ferrules. Mains stays on this side, zip-tied to the left-wall anchors'),
    ('W4', 'PSU +V', 'Controller J1-1', '+24 V', '18 AWG silicone', 'red', '0.25 m', 'pod', 'Ferrules. The board fuse (F1, 10 A) is on this feed'),
    ('W5', 'PSU −V', 'Controller J1-2', 'GND', '18 AWG silicone', 'black', '0.25 m', 'pod', 'Ferrules'),
    ('W6', 'Controller J5-1', 'SD-15 +Vin (pin 4)', '+24 V', '20 AWG silicone', 'red', '0.15 m', 'pod', 'SD-15B-5 on carrier_left; leave FG (pin 3) unconnected'),
    ('W7', 'Controller J5-2', 'SD-15 -Vin (pin 5)', 'GND', '20 AWG silicone', 'black', '0.15 m', 'pod', ''),
    ('W8', 'SD-15 +V out (pin 1)', 'Controller J5-3', '+5 V', '20 AWG silicone', 'red, marked "5V"', '0.15 m', 'pod', 'Mark it with a band of tape: it is not 24 V'),
    ('W9', 'SD-15 -V out (pin 2)', 'Controller J5-4', 'GND', '20 AWG silicone', 'black', '0.15 m', 'pod', ''),
    ('W10', 'Controller J2-1', 'TCO, then heater lead A', 'HTR+ (switched 24 V)', '18 AWG silicone', 'red', '0.8 m', 'gland 1, back wall, plenum', 'Join the TCO with crimp butt splices + heat-shrink, never solder (heat trips it). TCO at the duct outlet'),
    ('W11', 'Heater lead B', 'Controller J2-2', 'HTR− (to MOSFET)', '18 AWG silicone', 'black', '0.8 m', 'gland 1', 'Carries 6.3 A: keep W10/W11 18 AWG'),
    ('W12', 'Controller J3-1', 'KSD301 tab 1', '+24 V to the relay coil', '20 AWG silicone', 'red', '0.8 m', 'gland 1', '6.3 mm insulated female quick-connects (high-temp)'),
    ('W13', 'KSD301 tab 2', 'Controller J3-2', 'coil feed (TSTAT_OUT)', '20 AWG silicone', 'black', '0.8 m', 'gland 1', 'KSD301 clipped to the heater frame'),
    ('W14', 'Controller J4 (4-pin)', 'Fan', '24 V, GND, tach, PWM', '4-pin PWM fan extension', 'fan colours', '0.6 m', 'gland 1', 'Fan pinout: 1 GND, 2 +24 V, 3 tach, 4 PWM'),
    ('W15', 'Controller J9-1 / J9-2', 'Heater NTC (both leads)', 'NTC, GND', '22 AWG 4-core (2 used)', 'red, black', '0.8 m', 'gland 1', 'Splice to the NTC leads with heat-shrink; NTC epoxied in the duct hole'),
    ('W16', 'Controller J7-1..4', 'SHT45 chamber sensor', '3V3, GND, SDA_A, SCL_A', '22 AWG 4-core', 'red 3V3, black GND, white SDA, green SCL', '0.7 m', 'gland 1, up the back wall', 'Splice to a cut STEMMA QT lead at the sensor (red 3V3, black GND, blue SDA, yellow SCL)'),
    ('W17', 'Controller J8-1..4', 'SHT40 plenum sensor', '3V3, GND, SDA_B, SCL_B', '22 AWG 4-core', 'red 3V3, black GND, white SDA, green SCL', '0.5 m', 'gland 1', 'Same splice as W16'),
    ('W18', 'Controller J10', 'Front breakout J1', 'display, NFC, encoder, touch, reed, LED data, 5 V, 3V3', '26-way flat ribbon, 1.27 mm', 'grey, red stripe = pin 1', '1.5 m', 'gland 2, back wall, ceiling, header slot', 'Pass it through the gland and the slot first, then crimp both IDC sockets (pin 1 to the red stripe at both ends)'),
    ('W19', 'Controller J6-1', 'Front breakout J6-1', 'LED_5V (fused 3 A)', '20 AWG silicone', 'red, marked "5V"', '1.5 m', 'gland 2, alongside the ribbon', ''),
    ('W20', 'Controller J6-2', 'Front breakout J6-2', 'GND', '20 AWG silicone', 'black', '1.5 m', 'gland 2', ''),
    ('W21', 'Front breakout J2 (14 pins)', 'TFT 14-pin header', 'TFT + touch', '14 × female-female jumpers', 'any', '0.15 m', 'header bay', 'Same order at both ends: pin 1 to pin 1 (VCC)'),
    ('W22', 'Front breakout J3 (9 pins)', 'PN5180 header', '5V, 3V3, RST, NSS, MOSI, MISO, SCK, BUSY, GND', '9 × female-female jumpers', 'any', '0.15 m', 'header bay', 'J3 follows the common PN5180 board order; check the labels on yours and match by name'),
    ('W23', 'Front breakout J4 (5 pins)', 'EC11 encoder', 'A, GND (C), B, SW, GND', '5 × 26 AWG', 'any', '0.15 m', 'header bay', 'Solder at the encoder; female jumper ends on J4'),
    ('W24', 'Front breakout J5', 'Door reed switch', 'REED, GND', '2 × 26 AWG', 'any', '0.4 m', 'right frame stile channel into the header', 'Glass reed: bend its leads only away from the glass, and sleeve them'),
    ('W25', 'Front breakout J7-1..3', 'LED strip input', 'LED_5V, LED data, GND', '20 AWG (5 V, GND) + 26 AWG (data)', 'red, white, black', '0.2 m', 'header bay to under the lip', 'Solder to the top strip pads at its DIN end (right end, x about 500); the top strip runs right to left'),
    ('W26', 'Top strip DOUT (left end)', 'Bottom strip DIN (left end)', 'LED_5V, LED data, GND', '20 AWG (5 V, GND) + 26 AWG (data)', 'red, white, black', '0.45 m', 'down the inside front-left corner (side wall / frame), clipped', 'Chains the bottom strip and feeds its 5 V from both ends of the top strip'),
    ('W27', 'Bottom strip, left segment DOUT', 'Bottom strip, right segment DIN', 'LED_5V, LED data, GND', '22 AWG ×3', 'red, white, black', '0.1 m', 'across the slot-3 gap in the rails\' floor channel, in front of the floor duct', 'Jumper over the floor duct gap (x 191–261)'),
]

def table_md():
    out = ['| Wire | From | To | Carries | Wire | Colour | Length | Route | Notes |', '|---|---|---|---|---|---|---|---|---|']
    for w in WIRES: out.append('| ' + ' | '.join(w) + ' |')
    return '\n'.join(out)

# ------------------------------------------------------------------ drawing
C = dict(mains='#7a3d00', v24='#d62828', gnd='#333333', v5='#f08c00', sig='#1c6dd0', ribbon='#868e96')
def draw():
    fig, ax = plt.subplots(figsize=(22, 13)); ax.set_xlim(0, 200); ax.set_ylim(0, 120); ax.axis('off')
    def zone(x, y, w, h, t):
        ax.add_patch(plt.Rectangle((x, y), w, h, fill=False, ls='--', ec='#999', lw=1.2))
        ax.text(x + 1, y + h - 1.5, t, fontsize=11, color='#555', weight='bold', va='top')
    def box(x, y, w, h, t, body='', fc='#f1f3f5', ec='#495057'):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3', fc=fc, ec=ec, lw=1.4))
        ax.text(x + w/2, y + h - 1.2, t, ha='center', va='top', fontsize=10, weight='bold')
        if body: ax.text(x + w/2, y + h - 4.0, body, ha='center', va='top', fontsize=8.2)
    def pin(x, y, t, side='r'):
        ax.add_patch(plt.Rectangle((x - 1, y - 1), 2, 2, fc='#2b8a3e', ec='k', lw=0.6, zorder=5))
        ax.text(x + (1.8 if side == 'r' else -1.8), y, t, fontsize=7.6, ha='left' if side == 'r' else 'right', va='center', zorder=6)
        return (x, y)
    def wire(pts, col, lab=None, lw=2.0, at=0.5, ls='-'):
        xs, ys = zip(*pts); ax.plot(xs, ys, color=col, lw=lw, ls=ls, solid_capstyle='round', zorder=3)
        if lab:
            i = max(0, min(len(pts) - 2, int(at * (len(pts) - 1))))
            mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
            ax.text(mx, my + 0.9, lab, fontsize=8, color=col, ha='center', weight='bold', zorder=6,
                    bbox=dict(fc='white', ec='none', pad=0.3, alpha=0.85))
    zone(2, 2, 62, 116, 'REAR POD (outside the chamber)')
    zone(68, 2, 66, 116, 'CHAMBER (heated, 24 V and signals only)')
    zone(138, 2, 60, 116, 'FRONT: header bay and door')
    # --- pod
    box(5, 98, 18, 14, 'IEC C14 inlet', 'switch + T3.15 A fuse\nright side wall', fc='#fff5f5', ec=C['mains'])
    box(32, 96, 28, 18, 'PSU LRS-200-24', '24 V 8.8 A\nterminals: L N FG  +V −V', fc='#fff4e6', ec=C['v24'])
    box(5, 70, 20, 16, '5 V supply 24 → 5 V', 'Mean Well SD-15B-5\non carrier_left', fc='#fff9db', ec=C['v5'])
    box(8, 8, 46, 52, 'Controller PCB (DCC-MAIN)', 'ESP32-S3 DevKitC-1, relay, MOSFET,\nfuses, fan driver\non carrier_main', fc='#ebfbee', ec='#2b8a3e')
    for i, (a, b, c, t) in enumerate((('L', 'L', C['mains'], 'W1'), ('N', 'N', C['mains'], 'W2'), ('PE', 'FG', '#2f9e44', 'W3'))):
        y = 108 - 3.2 * i
        wire([(23.3, y), (31.7, y)], c, t, lw=1.8)
    j1a, j1b = pin(12, 60.3, 'J1 +24V', 'l'), pin(17, 60.3, 'J1 GND')
    wire([(46, 95.7), (46, 66), (12, 66), j1a], C['v24'], 'W4 +24 V', at=0.3)
    wire([(50, 95.7), (50, 64), (17, 64), j1b], C['gnd'], 'W5 GND', at=0.3)
    j5 = [pin(30 + 4 * k, 60.3, n, 'r' if k == 3 else None or 'r') for k, n in enumerate(('', '', '', 'J5'))]
    wire([(30, 60.3), (30, 76), (25.3, 76)], C['v24'], 'W6', at=0.6)
    wire([(34, 60.3), (34, 74), (25.3, 74)], C['gnd'], 'W7', at=0.7)
    wire([(25.3, 80), (38, 80), (38, 60.3)], C['v5'], 'W8 5V', at=0.4)
    wire([(25.3, 82), (42, 82), (42, 60.3)], C['gnd'], 'W9', at=0.4)
    # right-edge connectors
    R = {k: pin(54.3, y, k) for k, y in (('J2 HEATER', 52), ('J3 KSD301', 46), ('J4 FAN', 40), ('J9 NTC', 34),
                                          ('J7 SHT45', 28), ('J8 SHT40', 22), ('J10 RIBBON', 15), ('J6 LED 5V', 10))}
    for k in R: R[k] = (54.3, R[k][1])
    # glands
    for (gx, gy, t) in ((64, 37, 'gland 1'), (64, 12.5, 'gland 2')):
        ax.add_patch(Circle((gx, gy), 3.2, fc='white', ec='k', lw=1.5, zorder=4)); ax.text(gx, gy - 5, t, ha='center', fontsize=8)
    # --- chamber
    box(98, 54, 32, 14, 'PTC heater 150 W', 'in heater_duct, on PTFE pads\nTCO 102 °C spliced in lead A', fc='#ffe3e3', ec=C['v24'])
    box(98, 44, 32, 8, 'KSD301 85 °C (NC)', 'clipped to the heater frame', fc='#ffe3e3', ec=C['v24'])
    box(98, 34, 32, 8, 'Fan 80 mm 24 V PWM', 'plenum fan mount', fc='#fff4e6', ec=C['v24'])
    box(98, 26, 32, 6, '10k NTC', 'duct outlet', fc='#e7f5ff', ec=C['sig'])
    box(98, 84, 32, 10, 'SHT45 (chamber)', 'sensor_housing, top rear', fc='#e7f5ff', ec=C['sig'])
    box(98, 16, 32, 8, 'SHT40 (plenum)', 'desiccant outlet', fc='#e7f5ff', ec=C['sig'])
    def via_g1(p, y_end, col, lab, dy, xv):
        wire([p, (60, p[1]), (61.5, 37 + dy), (66.5, 37 + dy), (xv, 37 + dy), (xv, y_end), (97.7, y_end)], col, lab, at=0.9)
    via_g1(R['J2 HEATER'], 64, C['v24'], 'W10 HTR+', 1.6, 92)
    via_g1((54.3, 51), 57, C['gnd'], 'W11 HTR−', 1.2, 90)
    via_g1(R['J3 KSD301'], 50, C['v24'], 'W12', 0.8, 88)
    via_g1((54.3, 45), 46, C['gnd'], 'W13', 0.4, 86)
    via_g1(R['J4 FAN'], 38, C['v24'], 'W14 (4-wire)', 0.0, 84)
    via_g1(R['J9 NTC'], 29, C['sig'], 'W15', -0.4, 82)
    wire([R['J7 SHT45'], (60, 28), (61.5, 36.2), (66.5, 36.2), (72, 36.2), (72, 89), (97.7, 89)], C['sig'], 'W16 I²C A', at=0.9)
    via_g1(R['J8 SHT40'], 20, C['sig'], 'W17 I²C B', -1.2, 78)
    # ribbon + LED pair through gland 2, along the back wall and ceiling, into the header
    wire([R['J10 RIBBON'], (61.5, 13.2), (66.5, 13.2), (90, 13.2), (90, 6), (146, 6), (146, 62.7)], C['ribbon'], 'W18 26-way ribbon', lw=5, at=0.55)
    wire([R['J6 LED 5V'], (61.5, 11.4), (66.5, 11.4), (88, 11.4), (88, 4), (160, 4), (160, 62.7)], C['v5'], 'W19/W20 LED 5 V pair', at=0.55)
    ax.text(101, 108, 'Gland 1: heater, KSD301, fan, NTC, both sensors.\nGland 2: ribbon + LED 5 V pair, up the back wall,\nalong the ceiling in VHB clips, then through the\n40 × 7 mm slot into the header bay. Seal both with RTV.',
            fontsize=8.5, color='#555', ha='center', va='top')
    # --- front
    box(142, 62, 34, 26, 'Front breakout (DCC-FRONT)', '74AHCT125 LED driver,\nencoder pull-ups\nheader bay, x 335–415', fc='#ebfbee', ec='#2b8a3e')
    pin(146, 62, 'J1 ribbon'); pin(160, 62, 'J6 LED in')
    t2, t3 = pin(150, 88, 'J2 TFT'), pin(166, 88, 'J3 NFC')
    j4, j5, j7 = pin(176, 80, 'J4 ENC'), pin(176, 70, 'J5 REED'), pin(176, 65, 'J7 LED')
    box(140, 100, 24, 12, '3.5 in TFT', 'ST7796 + FT6336U\n14-pin header', fc='#e7f5ff', ec=C['sig'])
    box(168, 100, 24, 12, 'PN5180 NFC', 'behind the NFC fascia', fc='#f3f0ff', ec='#7048e8')
    box(184, 80, 12, 9, 'EC11', 'encoder', fc='#e7f5ff', ec=C['sig'])
    box(182, 44, 15, 10, 'Reed switch', 'right frame\nstile', fc='#e7f5ff', ec=C['sig'])
    box(170, 26, 26, 9, 'SK6812 top strip', '28 LEDs, under the header lip', fc='#fff9db', ec=C['v5'])
    box(170, 14, 26, 8, 'SK6812 bottom strip', '9 + 14 LEDs, floor rails', fc='#fff9db', ec=C['v5'])
    wire([(169.7, 30.5), (166.5, 30.5), (166.5, 18), (169.7, 18)], C['v5'], 'W26', at=0.5)
    wire([t2, (150, 99.7)], C['sig'], 'W21 ×14', at=0.5)
    wire([t3, (166, 92), (180, 92), (180, 99.7)], C['sig'], 'W22 ×9', at=0.5)
    wire([j4, (183.7, 84)], C['sig'], 'W23', at=0.5)
    wire([j5, (179, 70), (179, 49), (181.7, 49)], C['sig'], 'W24', at=0.5)
    wire([j7, (178, 65), (178, 40), (183, 40), (183, 35.3)], C['v5'], 'W25', at=0.6)
    # legend
    for k, (c, t) in enumerate(((C['mains'], 'mains 120 V'), ('#2f9e44', 'earth'), (C['v24'], '+24 V'), (C['gnd'], 'GND'),
                                (C['v5'], '+5 V'), (C['sig'], 'signal / 3.3 V'), (C['ribbon'], '26-way ribbon'))):
        ax.plot([140 + (k % 4) * 15, 144 + (k % 4) * 15], [10.5 - (k // 4) * 3.5] * 2, color=c, lw=3)
        ax.text(145 + (k % 4) * 15, 10.5 - (k // 4) * 3.5, t, fontsize=8, va='center')
    ax.set_title('Filament dry cabinet: wiring (v0.24). Wire numbers match the wire list in DESIGN.md §19', fontsize=13)
    plt.savefig(os.path.join(ROOT, 'images', 'wiring.png'), dpi=110, bbox_inches='tight'); plt.close()

if __name__ == '__main__':
    draw()
    os.makedirs(os.path.join(ROOT, 'wiring'), exist_ok=True)
    with open(os.path.join(ROOT, 'wiring', 'wire_list.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['Wire', 'From', 'To', 'Carries', 'Wire type', 'Colour', 'Length', 'Route', 'Notes']); w.writerows(WIRES)
    print(table_md())
