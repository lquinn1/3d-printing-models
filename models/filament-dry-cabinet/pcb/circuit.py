# SPDX-License-Identifier: MIT
"""Filament dry cabinet electronics: the two boards as data (parts, footprints, nets, placement).

DCC-MAIN   controller board in the rear pod, on carrier_main (170 x 60 mm, holes on the 10 mm grid)
DCC-FRONT  breakout in the front header bay: display, NFC, encoder, reed, LED strip level shifter

They are joined by a 26-way ribbon (2 x 13 IDC, 1.27 mm flat cable) with grounds between the
fast lines. Everything is through-hole so it can be hand-soldered.

Part tuple: (ref, footprint, value, x, y, rot, {pad: net}, mpn)
  x, y in mm from the board's top-left corner, y down; rot in degrees (KiCad, CCW).
"""
FP = {
    'TB508_2': 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal',
    'TB508_4': 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-4-5.08_1x04_P5.08mm_Horizontal',
    'TB35_2': 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal',
    'TB35_3': 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal',
    'TB35_4': 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal',
    'IDC26': 'Connector_IDC:IDC-Header_2x13_P2.54mm_Vertical',
    'SOCK22': 'Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical',
    'SOCK22X2': 'Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical',   # + a twin row 2.54 mm out (build.py)
    'FAN': 'Connector:FanPinHeader_1x04_P2.54mm_Vertical',
    'RELAY': 'Relay_THT:Relay_SPDT_Omron-G5LE-1',
    'TO220': 'Package_TO_SOT_THT:TO-220-3_Vertical',
    'TO92': 'Package_TO_SOT_THT:TO-92_Inline',
    'R': 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal',
    'C': 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm',
    'CP10': 'Capacitor_THT:CP_Radial_D10.0mm_P5.00mm',
    'CP6': 'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm',
    'DO41': 'Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal',
    'FUSE': 'Fuse:Fuseholder_Blade_Mini_Keystone_3568',
    'PTC': 'Fuse:Fuse_Bourns_MF-RG300',
    'DIP14': 'Package_DIP:DIP-14_W7.62mm_Socket',
    'LED3': 'LED_THT:LED_D3.0mm',
    'H1x3': 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
    'H1x5': 'Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical',
    'H1x9': 'Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical',
    'H1x14': 'Connector_PinHeader_2.54mm:PinHeader_1x14_P2.54mm_Vertical',
    'M3': 'MountingHole:MountingHole_3.2mm_M3',
}

# ribbon between the boards (pin: net); odd pins on one row, even on the other, so in the flat
# cable each wire sits next to pin n-1 and n+1: SCK, MOSI, MISO and LED data each have a ground beside them
RIBBON = {1: 'GND', 2: 'SCK', 3: 'GND', 4: 'MOSI', 5: 'GND', 6: 'MISO', 7: 'GND', 8: 'TFT_CS',
          9: 'NFC_NSS', 10: 'TFT_DC', 11: 'GND', 12: 'LED_DIN', 13: 'GND', 14: 'SDA_A', 15: 'SCL_A',
          16: '+3V3', 17: '+5V', 18: 'REED', 19: 'TFT_BL', 20: 'FRONT_RST', 21: 'CTP_INT',
          22: 'NFC_BUSY', 23: 'NFC_RST', 24: 'ENC_A', 25: 'ENC_B', 26: 'ENC_SW'}

# ESP32-S3-DevKitC-1 headers (Espressif user guide, J1 and J3). GPIO35-37 belong to the octal
# PSRAM on R8 modules; 19/20 are USB; 43/44 the console UART; 0 is the BOOT button; 38/48 drive
# the on-board RGB LED (v1.1 / v1.0). GPIO45/46 are boot straps: both sit behind pull-downs here,
# which is the state they need at reset.
J1 = ['+3V3', '+3V3', None, 'REED', 'LED_DIN', 'SDA_B', 'SCL_B', 'TFT_BL', 'NFC_NSS', 'NFC_BUSY',
      'NFC_RST', 'SDA_A', 'FAN_TACH', 'RELAY_EN', 'SCL_A', 'TFT_CS', 'MOSI', 'SCK', 'MISO', 'TFT_DC',
      'ESP_5V', 'GND']
#     3V3     3V3     RST   GPIO4   GPIO5      GPIO6    GPIO7    GPIO15    GPIO16     GPIO17
#     GPIO18     GPIO8    GPIO3       GPIO46      GPIO9    GPIO10    GPIO11  GPIO12 GPIO13  GPIO14  5V  G
J3 = ['GND', None, None, 'NTC', 'FAN_PWM', 'ENC_B', 'CTP_INT', 'FRONT_RST', 'ENC_A', None, None, None,
      None, None, 'HTR_PWM', None, 'ENC_SW', 'SPARE_IO21', None, None, 'GND', 'GND']
#     G      TX    RX    GPIO1   GPIO2     GPIO42   GPIO41     GPIO40       GPIO39  38   37    36
#     35    0     GPIO45     48    GPIO47    GPIO21        20    19    G      G
GPIO = {'REED': 4, 'LED_DIN': 5, 'SDA_B': 6, 'SCL_B': 7, 'TFT_BL': 15, 'NFC_NSS': 16, 'NFC_BUSY': 17,
        'NFC_RST': 18, 'SDA_A': 8, 'FAN_TACH': 3, 'RELAY_EN': 46, 'SCL_A': 9, 'TFT_CS': 10, 'MOSI': 11,
        'SCK': 12, 'MISO': 13, 'TFT_DC': 14, 'NTC': 1, 'FAN_PWM': 2, 'ENC_B': 42, 'CTP_INT': 41,
        'FRONT_RST': 40, 'ENC_A': 39, 'HTR_PWM': 45, 'ENC_SW': 47, 'SPARE_IO21': 21}

def _row(nets):
    return {str(i + 1): n for i, n in enumerate(nets) if n}

# ------------------------------------------------------------------ main board
MAIN_W, MAIN_H = 170.0, 60.0
EX, EY = 166.0, 17.0          # ESP32 J1 pin 1; the rows run toward -x, J3 is below (+y)
ROW, ROW_ALT = 22.86, 25.40   # header spacing: Espressif drawing / measured on some boards (U1B has both rows)
MAIN = [
    # power in, fuse, bulk
    ('J1', 'TB508_2', '24 V IN', 12.5, 53, 0, {'1': '+24V_IN', '2': 'GND'}, 'Phoenix 1935161'),
    ('F1', 'FUSE', '10 A mini blade', 24, 47, 0, {'1': '+24V_IN', '2': '+24V'}, 'Keystone 3568 + Littelfuse 0297010'),
    ('C1', 'CP10', '100uF 35V', 8, 26, 270, {'1': '+24V', '2': 'GND'}, 'Panasonic EEU-FR1V101'),
    # heater: relay contact on the high side, MOSFET (PWM) on the low side
    ('K1', 'RELAY', 'G5LE-1A4 DC24', 30, 20, 0, {'1': '+24V', '4': 'HTR_P', '2': 'TSTAT_OUT', '5': 'COIL_LO'}, 'Omron G5LE-1A4 DC24'),
    ('D1', 'DO41', '1N4007', 20, 42, 0, {'1': 'TSTAT_OUT', '2': 'COIL_LO'}, 'onsemi 1N4007G'),
    ('J3', 'TB508_2', 'KSD301', 55, 53, 0, {'1': '+24V', '2': 'TSTAT_OUT'}, 'Phoenix 1935161'),
    ('J2', 'TB508_2', 'HEATER', 42, 53, 0, {'1': 'HTR_P', '2': 'HTR_N'}, 'Phoenix 1935161'),
    ('Q1', 'TO220', 'IRLB3034', 46, 36, 0, {'1': 'Q1_G', '2': 'HTR_N', '3': 'GND'}, 'Infineon IRLB3034PBF'),
    ('R3', 'R', '100R', 44, 42, 0, {'1': 'HTR_PWM', '2': 'Q1_G'}, 'Yageo CFR-25JB-52-100R'),
    ('R4', 'R', '10k', 60, 30, 90, {'1': 'HTR_PWM', '2': 'GND'}, 'Yageo CFR-25JB-52-10K'),
    ('Q2', 'TO92', '2N3904', 48, 22, 0, {'1': 'GND', '2': 'Q2_B', '3': 'COIL_LO'}, 'onsemi 2N3904BU'),
    ('R1', 'R', '4k7', 44, 26, 0, {'1': 'RELAY_EN', '2': 'Q2_B'}, 'Yageo CFR-25JB-52-4K7'),
    ('R2', 'R', '10k', 44, 29, 0, {'1': 'RELAY_EN', '2': 'GND'}, 'Yageo CFR-25JB-52-10K'),
    # fan
    ('J4', 'FAN', 'FAN 24V PWM', 120, 54, 0, {'1': 'GND', '2': 'FAN_24V', '3': 'TACH_RAW', '4': 'FAN_OC'}, 'Molex 47053-1000'),
    ('F3', 'PTC', '0.5A PTC', 103.5, 40, 0, {'1': '+24V', '2': 'FAN_24V'}, 'Bourns MF-R050'),
    ('R5', 'R', '10k', 122, 26, 0, {'1': 'TACH_RAW', '2': '+3V3'}, 'Yageo CFR-25JB-52-10K'),
    ('R6', 'R', '1k', 122, 29, 0, {'1': 'TACH_RAW', '2': 'FAN_TACH'}, 'Yageo CFR-25JB-52-1K'),
    ('C2', 'C', '10nF', 136, 32, 0, {'1': 'FAN_TACH', '2': 'GND'}, 'KEMET C315C103K5R5TA'),
    ('Q3', 'TO92', '2N3904', 124, 35, 0, {'1': 'GND', '2': 'Q3_B', '3': 'FAN_OC'}, 'onsemi 2N3904BU'),
    ('R7', 'R', '4k7', 136, 26, 0, {'1': 'FAN_PWM', '2': 'Q3_B'}, 'Yageo CFR-25JB-52-4K7'),
    ('R8', 'R', '10k', 136, 29, 0, {'1': 'FAN_PWM', '2': 'GND'}, 'Yageo CFR-25JB-52-10K'),
    # 5 V: Mean Well SD-15B-5 off-board (on carrier_left), back in here
    ('J5', 'TB508_4', 'BUCK 24V/5V', 68, 53, 0, {'1': '+24V', '2': 'GND', '3': '+5V', '4': 'GND'}, 'Phoenix 1935187'),
    ('C3', 'CP6', '100uF 10V', 78, 40, 0, {'1': '+5V', '2': 'GND'}, 'Panasonic EEU-FR1A101'),
    ('D2', 'DO41', '1N5819', 94, 24, 0, {'1': 'ESP_5V', '2': '+5V'}, 'onsemi 1N5819RLG'),
    ('F2', 'PTC', '3A PTC', 94, 46, 0, {'1': '+5V', '2': 'LED_5V'}, 'Bourns MF-RG300'),
    ('J6', 'TB508_2', 'LED 5V OUT', 104, 53, 0, {'1': 'LED_5V', '2': 'GND'}, 'Phoenix 1935161'),
    ('D3', 'LED3', 'PWR', 72, 44, 0, {'1': 'GND', '2': 'LED_A'}, 'Lite-On LTL-4231'),
    ('R9', 'R', '1k', 58, 44, 0, {'1': '+5V', '2': 'LED_A'}, 'Yageo CFR-25JB-52-1K'),
    # sensors, NTC, reed
    ('J7', 'TB35_4', 'SHT45 CHAMBER', 72, 7, 180, {'1': '+3V3', '2': 'GND', '3': 'SDA_A', '4': 'SCL_A'}, 'Phoenix 1984633'),
    ('J8', 'TB35_4', 'SHT40 PLENUM', 90, 7, 180, {'1': '+3V3', '2': 'GND', '3': 'SDA_B', '4': 'SCL_B'}, 'Phoenix 1984633'),
    ('J9', 'TB35_2', 'NTC', 104, 7, 180, {'1': 'NTC', '2': 'GND'}, 'Phoenix 1984617'),
    ('R10', 'R', '2k2', 122, 4, 0, {'1': 'SDA_A', '2': '+3V3'}, 'Yageo CFR-25JB-52-2K2'),
    ('R11', 'R', '2k2', 122, 7, 0, {'1': 'SCL_A', '2': '+3V3'}, 'Yageo CFR-25JB-52-2K2'),
    ('R12', 'R', '2k2', 135, 4, 0, {'1': 'SDA_B', '2': '+3V3'}, 'Yageo CFR-25JB-52-2K2'),
    ('R13', 'R', '2k2', 135, 7, 0, {'1': 'SCL_B', '2': '+3V3'}, 'Yageo CFR-25JB-52-2K2'),
    ('R14', 'R', '10k 1%', 148.5, 4, 0, {'1': '+3V3', '2': 'NTC'}, 'Yageo MFR-25FBF52-10K'),
    ('C4', 'C', '100nF', 152, 8, 0, {'1': 'NTC', '2': 'GND'}, 'KEMET C320C104K5R5TA'),
    ('R15', 'R', '10k', 64, 34, 90, {'1': 'REED', '2': '+3V3'}, 'Yageo CFR-25JB-52-10K'),
    ('C5', 'C', '100nF', 68, 34, 90, {'1': 'REED', '2': 'GND'}, 'KEMET C320C104K5R5TA'),
    # ribbon to the front breakout, spare pin
    ('J10', 'IDC26', 'FRONT 2x13', 47, 5, 270, {str(k): v for k, v in RIBBON.items()}, 'Amphenol T821126A1S100CEU'),
    ('C6', 'C', '100nF', 108, 14, 90, {'1': '+3V3', '2': 'GND'}, 'KEMET C320C104K5R5TA'),
    ('C7', 'C', '100nF', 100, 34, 90, {'1': 'ESP_5V', '2': 'GND'}, 'KEMET C320C104K5R5TA'),
    ('J11', 'H1x3', 'SPARE IO21', 82, 33, 90, {'1': '+3V3', '2': 'SPARE_IO21', '3': 'GND'}, 'Sullins PRPC003SAAN-RC'),
    # ESP32-S3-DevKitC-1 in sockets: J1 row, J3 row, and a second J3 row 2.54 mm further out
    ('U1A', 'SOCK22', 'ESP32 J1', EX, EY, 270, _row(J1), 'Sullins PPTC221LFBN-RC'),
    ('U1B', 'SOCK22X2', 'ESP32 J3', EX, EY + ROW, 270, _row(J3), 'Sullins PPTC221LFBN-RC (solder it in the row that fits)'),
]
MAIN_HOLES = [(5, 5), (165, 5), (5, 55), (165, 55)]   # 160 x 50: lands on the carrier's 10 mm grid

# ------------------------------------------------------------------ front breakout
FRONT_W, FRONT_H = 80.0, 44.0
FRONT = [
    ('J1', 'IDC26', 'FROM POD 2x13', 44, 6.5, 270, {str(k): v for k, v in RIBBON.items()}, 'Amphenol T821126A1S100CEU'),
    # display: same order as the TFT's own 14 pins, so a straight 14-wire jumper works
    ('J2', 'H1x14', 'TFT 3.5in', 4, 18, 90, {'1': '+5V', '2': 'GND', '3': 'TFT_CS', '4': 'FRONT_RST', '5': 'TFT_DC',
                                           '6': 'MOSI', '7': 'SCK', '8': 'TFT_BL', '10': 'SCL_A', '11': 'FRONT_RST',
                                           '12': 'SDA_A', '13': 'CTP_INT', '14': '+3V3'}, 'Sullins PRPC014SAAN-RC'),
    # PN5180 module, in the order of its own header (5V, 3V3, RST, NSS, MOSI, MISO, SCK, BUSY, GND)
    ('J3', 'H1x9', 'PN5180', 4, 25, 90, {'1': '+5V', '2': '+3V3', '3': 'NFC_RST', '4': 'NFC_NSS', '5': 'MOSI',
                                       '6': 'MISO', '7': 'SCK', '8': 'NFC_BUSY', '9': 'GND'}, 'Sullins PRPC009SAAN-RC'),
    ('J4', 'H1x5', 'ENCODER', 24, 33, 90, {'1': 'ENC_A', '2': 'GND', '3': 'ENC_B', '4': 'ENC_SW', '5': 'GND'}, 'Sullins PRPC005SAAN-RC'),
    ('R1', 'R', '10k', 41.2, 22, 0, {'1': 'ENC_A', '2': '+3V3'}, 'Yageo CFR-25JB-52-10K'),
    ('R2', 'R', '10k', 41.2, 25.5, 0, {'1': 'ENC_B', '2': '+3V3'}, 'Yageo CFR-25JB-52-10K'),
    ('R3', 'R', '10k', 41.2, 29, 0, {'1': 'ENC_SW', '2': '+3V3'}, 'Yageo CFR-25JB-52-10K'),
    ('C1', 'C', '10nF', 54, 23, 0, {'1': 'ENC_A', '2': 'GND'}, 'KEMET C315C103K5R5TA'),
    ('C2', 'C', '10nF', 54, 26.5, 0, {'1': 'ENC_B', '2': 'GND'}, 'KEMET C315C103K5R5TA'),
    ('C3', 'C', '10nF', 54, 30, 0, {'1': 'ENC_SW', '2': 'GND'}, 'KEMET C315C103K5R5TA'),
    ('J5', 'TB35_2', 'REED', 69, 38.5, 0, {'1': 'REED', '2': 'GND'}, 'Phoenix 1984617'),
    # LED strip: 5 V from the pod's fused output, level shifter here at the strip end
    ('J6', 'TB508_2', 'LED 5V IN', 44, 38.5, 0, {'1': 'LED_5V', '2': 'GND'}, 'Phoenix 1935161'),
    ('J7', 'TB35_3', 'LED STRIP', 56, 38.5, 0, {'1': 'LED_5V', '2': 'LED_DO', '3': 'GND'}, 'Phoenix 1984620'),
    ('U1', 'DIP14', '74AHCT125', 56, 4, 0, {'1': 'GND', '2': 'LED_DIN', '3': 'LED_Y', '4': 'LED_5V', '5': 'GND',
                                          '7': 'GND', '9': 'GND', '10': 'LED_5V', '12': 'GND', '13': 'LED_5V',
                                          '14': 'LED_5V'}, 'TI SN74AHCT125N + On Shore ED14DT'),
    ('C4', 'C', '100nF', 67.5, 9, 0, {'1': 'LED_5V', '2': 'GND'}, 'KEMET C320C104K5R5TA'),
    ('R4', 'R', '330R', 67.2, 15, 0, {'1': 'LED_Y', '2': 'LED_DO'}, 'Yageo CFR-25JB-52-330R'),
    ('C5', 'CP10', '1000uF 16V', 68, 26, 0, {'1': 'LED_5V', '2': 'GND'}, 'Panasonic EEU-FR1C102'),
    ('C6', 'C', '100nF', 10, 31, 0, {'1': '+3V3', '2': 'GND'}, 'KEMET C320C104K5R5TA'),
]
FRONT_HOLES = [(4, 40), (76, 4)]

BOARDS = {
    'dcc_main': dict(w=MAIN_W, h=MAIN_H, parts=MAIN, holes=MAIN_HOLES, title='Filament dry cabinet controller',
                     power={'+24V_IN', '+24V', 'HTR_P', 'HTR_N'}, mid={'+5V', 'LED_5V', 'ESP_5V'},
                     solid_gnd={'J1', 'Q1', 'J5'},   # heater return current: no thermal spokes on these GND pads
                     keepout=(EX - 8, EY + 2.5, MAIN_W, EY + ROW - 2.5)),   # under the DevKit's antenna, between the rows
    'dcc_front': dict(w=FRONT_W, h=FRONT_H, parts=FRONT, holes=FRONT_HOLES, title='Filament dry cabinet front breakout',
                      power=set(), mid={'LED_5V'}, solid_gnd=set(), keepout=None),
}
