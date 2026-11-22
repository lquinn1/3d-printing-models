import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
fig, ax = plt.subplots(figsize=(13, 8.5)); ax.set_xlim(0, 130); ax.set_ylim(0, 85); ax.axis('off')
def box(x, y, w, h, title, body='', fc='#e7f5ff', ec='#1971c2'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.4', fc=fc, ec=ec, lw=1.5))
    ax.text(x+w/2, y+h-1.6, title, ha='center', va='top', fontsize=9, weight='bold')
    if body: ax.text(x+w/2, y+h-5, body, ha='center', va='top', fontsize=7.5)
def wire(p, q, c='k', lab='', lw=1.6, ls='-'):
    ax.annotate('', xy=q, xytext=p, arrowprops=dict(arrowstyle='-', color=c, lw=lw, ls=ls))
    if lab: ax.text((p[0]+q[0])/2, (p[1]+q[1])/2+0.8, lab, fontsize=7, color=c, ha='center')
MAINS='#c92a2a'; V24='#e67700'; V5='#2f9e44'; SIG='#1971c2'
ax.add_patch(plt.Rectangle((1, 44), 40, 39, fill=False, ls='--', ec='#888')); ax.text(2, 81.5, 'REAR CONTROL POD (outside the heated chamber)', fontsize=8, color='#555')
box(3, 66, 16, 13, 'IEC C14 inlet', 'fused + switched\n3.15 A T, 5x20 mm\nPE to PSU FG', fc='#fff5f5', ec=MAINS)
box(23, 66, 16, 13, '24 V PSU', 'Mean Well LRS-200-24\n200 W, 8.8 A\n(enclosed, metal case)', fc='#fff4e6', ec=V24)
wire((19, 72), (23, 72), MAINS, 'L / N / PE')
box(3, 47, 16, 14, 'Buck 24 -> 5 V', '3-5 A module\n(LEDs, logic, display)', fc='#ebfbee', ec=V5)
box(23, 47, 16, 14, 'ESP32-S3', 'DevKitC-1 N16R8\nESPHome', fc='#e7f5ff', ec=SIG)
wire((31, 66), (31, 61), V24); wire((31, 63.5), (11, 63.5), V24); wire((11, 63.5), (11, 61), V24)
wire((19, 52), (23, 52), V5, '5 V')
# chamber side
ax.add_patch(plt.Rectangle((47, 2), 82, 81, fill=False, ls='--', ec='#888')); ax.text(48, 81.5, 'CHAMBER / FRONT HEADER', fontsize=8, color='#555')
box(50, 67, 17, 12, 'Heater MOSFET', 'logic-level N-FET\nlow-side, slow PWM', fc='#fff4e6', ec=V24)
box(73, 67, 25, 12, 'PTC heater 24 V 150 W', 'printed ABS/ASA duct\nKSD301 85 °C (auto-reset)\n+ TCO 102 °C in series', fc='#ffe3e3', ec=V24)
box(102, 67, 24, 12, 'Duct fan 24 V PWM', '4-pin, 25 kHz PWM\ntach -> pulse counter', fc='#fff4e6', ec=V24)
# 24 V bus
wire((39, 70), (44, 70), V24); wire((44, 70), (44, 64.5), V24); wire((44, 64.5), (120, 64.5), V24, '+24 V bus')
wire((85.5, 64.5), (85.5, 66.6), V24); wire((114, 64.5), (114, 66.6), V24)
wire((67, 73), (73, 73), V24, 'switched -')
# GPIO to MOSFET
wire((39, 59), (58.5, 59), SIG); wire((58.5, 59), (58.5, 66.6), SIG, '')
ax.text(46, 59.8, 'heater, fan PWM, tach', fontsize=7, color=SIG)
wire((58.5, 62), (108, 62), SIG); wire((108, 62), (108, 66.6), SIG)
# sensor row with an I/O bus underneath
box(50, 47, 22, 12, 'Sensors (I2C)', 'SHT45 chamber (top rear)\nSHT40 at desiccant outlet\nopt. SHT40 room/ambient', fc='#e7f5ff', ec=SIG)
box(76, 47, 22, 12, 'Heater outlet temp', 'NTC 10k (or DS18B20)\nfirmware over-temp cut', fc='#e7f5ff', ec=SIG)
box(102, 47, 24, 12, 'Door reed switch', 'light on when open\nheater/fan pause', fc='#e7f5ff', ec=SIG)
wire((39, 50), (44, 50), SIG); wire((44, 50), (44, 44.5), SIG); wire((44, 44.5), (114, 44.5), SIG, 'I2C / ADC / GPIO (3.3 V)')
for x in (61, 87, 114): wire((x, 44.5), (x, 46.6), SIG)
# UI and LEDs
box(50, 24, 24, 15, 'Front header UI', '3.2" IPS SPI TFT + FT6336U touch\n(label + menu), backlight PWM, EC11\ngraphical_display_menu', fc='#e7f5ff', ec=SIG)
wire((29, 47), (29, 31), SIG); wire((29, 31), (50, 31), SIG, 'SPI + encoder')
box(80, 24, 24, 15, 'SK6812 RGBW 5 V', '60 LED/m, ~30 LEDs\n74AHCT125 level shift\n330 R + 1000 uF', fc='#ebfbee', ec=V5)
wire((35, 47), (35, 21.5), SIG); wire((35, 21.5), (86, 21.5), SIG, 'LED data (RMT)'); wire((86, 21.5), (86, 23.6), SIG)
wire((11, 47), (11, 18.5), V5); wire((11, 18.5), (98, 18.5), V5, '5 V (fused 3 A)'); wire((98, 18.5), (98, 23.6), V5)
box(108, 6, 18, 14, 'NFC reader', 'PN5180 (ISO 15693\n+ 14443A), SPI\nOpenPrintTag tap pad', fc='#f3f0ff', ec='#7048e8')
wire((29, 31), (29, 15.5), SIG); wire((29, 15.5), (108, 15.5), SIG, 'shared SPI + NSS/BUSY/RST')
box(108, 24, 18, 15, 'Desiccant', 'pull-out silica gel\ncartridges in the\nreturn air path', fc='#fff9db', ec='#e67700')
box(3, 1, 38, 12.5, 'Network / integrations', 'Home Assistant (ESPHome API)\nweb_server for local status\nSpoolman: slot = location,\nHA script lights the slot', fc='#f8f9fa', ec='#495057')
for c, l, x in ((MAINS, 'mains 120 V', 50), (V24, '24 V', 70), (V5, '5 V', 84), (SIG, '3.3 V signal', 96)):
    ax.plot([x, x+4], [9, 9], color=c, lw=2); ax.text(x+5, 9, l, va='center', fontsize=8)
ax.set_title('Electrical block diagram (one cabinet)', fontsize=12)
plt.savefig('wiring.png', dpi=110, bbox_inches='tight'); print('ok')
