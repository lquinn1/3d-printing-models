# SPDX-License-Identifier: MIT
"""Schematic sheets for the two boards (drawn with schemdraw), plus the ESP32 pin map and the
ribbon pinout, written to pcb/schematic.pdf and images/pcb_schematic.png.

The board files are built from circuit.py; this drawing is made to match it, section by section,
and check_schematic() at the bottom confirms every part drawn here is on a board with the same
value, and vice versa.
"""
import os, io
import matplotlib; matplotlib.use('Agg')
import schemdraw, schemdraw.elements as elm
from PIL import Image, ImageDraw, ImageFont
from circuit import BOARDS, RIBBON, J1, J3, GPIO

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, '..', 'images')
schemdraw.config(fontsize=11, lw=1.2)
DRAWN = set()     # (board, ref, value) drawn, for the cross-check

def part(board, ref, val):
    DRAWN.add((board, ref, val)); return f'{ref}\n{val}'

def sheet(fn):
    d = schemdraw.Drawing(show=False)
    fn(d)
    buf = io.BytesIO(d.get_imagedata('png'))
    return Image.open(buf).convert('RGB')

M, F = 'dcc_main', 'dcc_front'
G = lambda n: f'{n}\nGPIO{GPIO[n]}'

def b_24v(d):
    d += elm.Label().label('+24V_IN\nJ1 pin 1', loc='left')
    d += elm.Fuse().right().label(part(M, 'F1', '10 A mini blade'))
    d += elm.Dot(); d.push()
    d += elm.Capacitor(polar=True).down().label(part(M, 'C1', '100uF 35V'), loc='bottom'); d += elm.Ground()
    d.pop(); d += elm.Line().right(1.5); d += elm.Label().label('+24V', loc='right')

def b_heater_path(d):
    d += elm.Label().label('+24V', loc='left')
    d += elm.Switch().right().label(part(M, 'K1', 'G5LE-1A4 DC24') + '\ncontact COM-NO')
    d += elm.Line().right(1).label('HTR_P', loc='top')
    d += elm.ResistorVar().right().label('J2: PTC heater 24 V 150 W\nwith the TCO 102 °C in series\n(off board)', loc='bottom')
    d += elm.Line().right(1); d += elm.Label().label('HTR_N\n(Q1 drain)', loc='right')

def b_heater_fet(d):
    q = elm.NFet().reverse().label(part(M, 'Q1', 'IRLB3034'), loc='right'); d += q
    d += elm.Line().at(q.drain).up(0.5); d += elm.Label().label('HTR_N', loc='top')
    d += elm.Ground().at(q.source)
    d += elm.Line().at(q.gate).left(2.5); d += elm.Dot(); d.push()
    d += elm.Resistor().down().label(part(M, 'R4', '10k'), loc='bottom'); d += elm.Ground()
    d.pop(); d += elm.Resistor().left().label(part(M, 'R3', '100R'))
    d += elm.Label().label(G('HTR_PWM'), loc='left')

def b_relay(d):
    d += elm.Label().label('+24V', loc='left')
    d += elm.Switch(action='open').right().label('J3: KSD301 85 °C\nnormally closed (off board)')
    d += elm.Dot(); d += elm.Label().label('TSTAT_OUT', loc='top'); d.push()
    d += elm.Line().right(4.5); d += elm.Diode().down().reverse().label(part(M, 'D1', '1N4007'), loc='bottom')
    d += elm.Line().left(4.5)
    d.pop(); d += elm.Inductor2().down().label(part(M, 'K1', 'G5LE-1A4 DC24') + ' coil', loc='bottom')
    d += elm.Dot(); d += elm.Label().label('COIL_LO', loc='left')
    q = elm.BjtNpn(circle=True).anchor('collector').label(part(M, 'Q2', '2N3904'), loc='right'); d += q
    d += elm.Ground().at(q.emitter)
    d += elm.Line().at(q.base).left(2.5); d += elm.Dot(); d.push()
    d += elm.Resistor().down().label(part(M, 'R2', '10k'), loc='bottom'); d += elm.Ground()
    d.pop(); d += elm.Resistor().left().label(part(M, 'R1', '4k7'))
    d += elm.Label().label(G('RELAY_EN'), loc='left')

def b_fan_supply(d):
    d += elm.Label().label('+24V', loc='left')
    d += elm.Fuse().right().label(part(M, 'F3', '0.5A PTC'))
    d += elm.Line().right(1); d += elm.Label().label('FAN_24V → J4 pin 2\n(J4 pin 1 GND)', loc='right')

def b_fan_pwm(d):
    q = elm.BjtNpn(circle=True).label(part(M, 'Q3', '2N3904'), loc='right'); d += q
    d += elm.Line().at(q.collector).up(0.5); d += elm.Label().label('FAN_OC → J4 pin 4 (fan pulls it up)', loc='top')
    d += elm.Ground().at(q.emitter)
    d += elm.Line().at(q.base).left(2.5); d += elm.Dot(); d.push()
    d += elm.Resistor().down().label(part(M, 'R8', '10k'), loc='bottom'); d += elm.Ground()
    d.pop(); d += elm.Resistor().left().label(part(M, 'R7', '4k7'))
    d += elm.Label().label(G('FAN_PWM'), loc='left')

def b_fan_tach(d):
    d += elm.Label().label('TACH_RAW\nJ4 pin 3', loc='left')
    d += elm.Line().right(1); d += elm.Dot(); d.push()
    d += elm.Resistor().up().label(part(M, 'R5', '10k'), loc='bottom'); d += elm.Vdd().label('+3V3')
    d.pop(); d += elm.Resistor().right().label(part(M, 'R6', '1k'))
    d += elm.Dot(); d.push()
    d += elm.Capacitor().down().label(part(M, 'C2', '10nF'), loc='bottom'); d += elm.Ground()
    d.pop(); d += elm.Line().right(1); d += elm.Label().label(G('FAN_TACH'), loc='right')

def b_5v(d):
    d += elm.Label().label('+5V from the buck\n(J5 pin 3; pin 1 = +24V out)', loc='left')
    d += elm.Line().right(1); d += elm.Dot(); d.push()
    d += elm.Capacitor(polar=True).down().label(part(M, 'C3', '100uF 10V'), loc='bottom'); d += elm.Ground()
    d.pop(); d += elm.Line().right(1)
    d += elm.Schottky().right().label(part(M, 'D2', '1N5819'))
    d += elm.Dot(); d.push()
    d += elm.Capacitor().down().label(part(M, 'C7', '100nF'), loc='bottom'); d += elm.Ground()
    d.pop(); d += elm.Line().right(1); d += elm.Label().label('ESP_5V → DevKit 5V pin\n(blocks USB back-feed)', loc='right')

def b_led_feed(d):
    d += elm.Label().label('+5V', loc='left')
    d += elm.Fuse().right().label(part(M, 'F2', '3A PTC'))
    d += elm.Line().right(1); d += elm.Label().label('LED_5V → J6 → front J6', loc='right')

def b_pwr_led(d):
    d += elm.Label().label('+5V', loc='top')
    d += elm.Resistor().down().label(part(M, 'R9', '1k'), loc='bottom')
    d += elm.LED().down().label(part(M, 'D3', 'PWR'), loc='bottom'); d += elm.Ground()

def b_i2c(d):
    for i, (ref, net) in enumerate((('R10', 'SDA_A'), ('R11', 'SCL_A'), ('R12', 'SDA_B'), ('R13', 'SCL_B'))):
        if i: d.move(4, 0)
        d += elm.Vdd().label('+3V3'); d += elm.Resistor().down().label(part(M, ref, '2k2'), loc='bottom')
        d += elm.Label().label(G(net), loc='bottom')
        d.move(0, 3)

def b_ntc(d):
    d += elm.Vdd().label('+3V3')
    d += elm.Resistor().down().label(part(M, 'R14', '10k 1%'), loc='bottom')
    d += elm.Dot(); d.push()
    d += elm.Line().right(1.5); d += elm.Label().label(G('NTC') + ' (ADC1)', loc='right')
    d.pop(); d.push()
    d += elm.Line().left(2); d += elm.Capacitor().down().label(part(M, 'C4', '100nF'), loc='bottom'); d += elm.Ground()
    d.pop(); d += elm.Thermistor().down().label('J9: 10k NTC\nat the duct', loc='bottom'); d += elm.Ground()

def b_reed(d):
    d += elm.Vdd().label('+3V3')
    d += elm.Resistor().down().label(part(M, 'R15', '10k'), loc='bottom')
    d += elm.Dot(); d.push()
    d += elm.Line().right(1.5); d += elm.Label().label(G('REED') + '\n(switch: front J5, ribbon 18)', loc='right')
    d.pop(); d += elm.Capacitor().down().label(part(M, 'C5', '100nF'), loc='bottom'); d += elm.Ground()

def b_decouple(d):
    d += elm.Label().label('+3V3', loc='top')
    d += elm.Capacitor().down().label(part(M, 'C6', '100nF'), loc='bottom'); d += elm.Ground()
    d.move(5, 3)
    d += elm.Label().label(part(M, 'J11', 'SPARE IO21') + '\n1 +3V3  2 GPIO21  3 GND', loc='right')

def b_front_led(d):
    u = elm.Ic(pins=[elm.IcPin(name='1A', side='left', pin='2'), elm.IcPin(name='1OE', side='left', pin='1'),
                     elm.IcPin(name='1Y', side='right', pin='3'), elm.IcPin(name='VCC', side='top', pin='14'),
                     elm.IcPin(name='GND', side='bot', pin='7')],
               size=(3, 2.5), label=part(F, 'U1', '74AHCT125'))
    d += u
    d += elm.Line().at(u['1A']).left(1); d += elm.Label().label('LED_DIN\n(ribbon 12)', loc='left')
    d += elm.Line().at(u['1OE']).left(0.5); d += elm.Ground()
    d += elm.Line().at(u.VCC).up(0.5); d += elm.Vdd().label('LED_5V')
    d += elm.Line().at(u.GND).down(0.5); d += elm.Ground()
    d += elm.Resistor().at(u['1Y']).right().label(part(F, 'R4', '330R'))
    d += elm.Label().label('LED_DO → J7 pin 2 (strip DIN)\nchannels 2-4 off: OE to LED_5V, A to GND', loc='right')

def b_front_caps(d):
    d += elm.Label().label('LED_5V', loc='top')
    d += elm.Capacitor(polar=True).down().label(part(F, 'C5', '1000uF 16V') + ' at J7', loc='bottom'); d += elm.Ground()
    d.move(5, 3); d += elm.Label().label('LED_5V', loc='top')
    d += elm.Capacitor().down().label(part(F, 'C4', '100nF') + ' at U1', loc='bottom'); d += elm.Ground()
    d.move(5, 3); d += elm.Label().label('+3V3', loc='top')
    d += elm.Capacitor().down().label(part(F, 'C6', '100nF'), loc='bottom'); d += elm.Ground()

def b_encoder(d):
    for i, (r, c, net) in enumerate((('R1', 'C1', 'ENC_A'), ('R2', 'C2', 'ENC_B'), ('R3', 'C3', 'ENC_SW'))):
        if i: d.move(5, 6)
        d += elm.Vdd().label('+3V3'); d += elm.Resistor().down().label(part(F, r, '10k'), loc='bottom')
        d += elm.Dot(); d += elm.Label().label(net, loc='left')
        d += elm.Capacitor().down().label(part(F, c, '10nF'), loc='bottom'); d += elm.Ground()

PAGES = [
    ('Controller: 24 V in and heater (relay contact on the high side, MOSFET PWM on the low side)',
     [('24 V in', b_24v), ('heater path', b_heater_path), ('heater MOSFET', b_heater_fet)]),
    ('Controller: safety relay (the KSD301 opens the coil) and fan',
     [('relay coil', b_relay), ('fan supply', b_fan_supply), ('fan PWM (inverted)', b_fan_pwm), ('fan tach', b_fan_tach)]),
    ('Controller: 5 V, sensors, NTC, door reed',
     [('5 V to the DevKit', b_5v), ('LED strip feed', b_led_feed), ('power LED', b_pwr_led), ('I2C pull-ups', b_i2c),
      ('heater NTC', b_ntc), ('door reed', b_reed), ('decoupling, spare', b_decouple)]),
    ('Front breakout: LED level shifter, encoder pull-ups',
     [('LED data buffer', b_front_led), ('bulk and decoupling', b_front_caps), ('encoder (A, B, push)', b_encoder)]),
]

def page(title, blocks, width=2400):
    fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
    fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    ims = [(t, sheet(fn)) for t, fn in blocks]
    rows, row, x = [], [], 0
    for t, im in ims:
        if row and x + im.width + 60 > width: rows.append(row); row, x = [], 0
        row.append((t, im)); x += im.width + 60
    rows.append(row)
    H = 80 + sum(max(im.height for _, im in r) + 70 for r in rows)
    pg = Image.new('RGB', (width, H), 'white'); dr = ImageDraw.Draw(pg)
    dr.text((30, 20), title, font=fb, fill='black'); y = 80
    for r in rows:
        x = 30
        for t, im in r:
            dr.text((x, y), t, font=fs, fill=(90, 90, 90)); pg.paste(im, (x, y + 34))
            dr.rectangle([x - 10, y - 6, x + im.width + 10, y + 40 + im.height], outline=(200, 200, 200))
            x += im.width + 60
        y += max(im.height for _, im in r) + 70
    return pg

def text_sheet(lines, w=1500, h=900, title=''):
    im = Image.new('RGB', (w, h), 'white'); dr = ImageDraw.Draw(im)
    fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
    fm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 19)
    dr.text((30, 20), title, font=fb, fill='black')
    for i, l in enumerate(lines): dr.text((30, 70 + i * 26), l, font=fm, fill='black')
    return im

def pin_sheets():
    a = ['ESP32-S3-DevKitC-1 (N16R8), socketed (U1A = J1 row, U1B = J3 row, twin holes 22.86 / 25.40 mm)', '',
         f'{"J1":<4}{"pin":<6}{"net":<14}      {"J3":<4}{"pin":<6}{"net":<14}']
    n1 = ['3V3', '3V3', 'RST', 'IO4', 'IO5', 'IO6', 'IO7', 'IO15', 'IO16', 'IO17', 'IO18', 'IO8', 'IO3', 'IO46',
          'IO9', 'IO10', 'IO11', 'IO12', 'IO13', 'IO14', '5V', 'G']
    n3 = ['G', 'TX', 'RX', 'IO1', 'IO2', 'IO42', 'IO41', 'IO40', 'IO39', 'IO38', 'IO37', 'IO36', 'IO35', 'IO0',
          'IO45', 'IO48', 'IO47', 'IO21', 'IO20', 'IO19', 'G', 'G']
    for i in range(22):
        a.append(f'{i+1:<4}{n1[i]:<6}{(J1[i] or "-"):<14}      {i+1:<4}{n3[i]:<6}{(J3[i] or "-"):<14}')
    a += ['', 'Not used: IO35-37 (octal PSRAM), IO19/20 (USB), IO43/44 (console), IO0 (BOOT), IO38/48 (on-board RGB LED).',
          'IO45 and IO46 are boot straps: their 10k pull-downs (R4, R2) hold them low at reset, as required.']
    b = ['2 x 13 IDC, 1.27 mm flat cable, J10 (pod) <-> J1 (front). Odd and even pins alternate in the cable.', '']
    for k in range(1, 27, 2):
        b.append(f'{k:>3}  {RIBBON[k]:<12}   {k+1:>3}  {RIBBON[k+1]:<12}')
    return [text_sheet(a, h=820, title='ESP32 pin map'), text_sheet(b, h=520, title='Ribbon (main J10 to front J1)')]

def check_schematic():
    on_board = {(n, p[0], p[2]) for n, cfg in BOARDS.items() for p in cfg['parts']
                if not p[0].startswith(('J', 'U1A', 'U1B'))}
    drawn = {x for x in DRAWN if not x[1].startswith('J')}
    missing, extra = on_board - drawn, drawn - on_board
    assert not missing and not extra, (sorted(missing), sorted(extra))
    return len(drawn)

if __name__ == '__main__':
    ims = [page(t, b) for t, b in PAGES] + pin_sheets()
    n = check_schematic()
    pdf = os.path.join(HERE, 'schematic.pdf')
    ims[0].save(pdf, save_all=True, append_images=ims[1:], resolution=150)
    W = max(i.width for i in ims); H = sum(i.height for i in ims)
    tall = Image.new('RGB', (W, H), 'white'); y = 0
    for i in ims: tall.paste(i, (0, y)); y += i.height
    tall.save(os.path.join(IMG, 'pcb_schematic.png'))
    print(f'schematic: {len(ims)} pages, {n} parts drawn = parts on the boards')
