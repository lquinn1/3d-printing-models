# SPDX-License-Identifier: MIT
from scene import *
floor = box(-900, 1500, -1100, 1300, ZB-FEET-2, ZB-FEET)
# 1) hero (front 3/4 left)
op, gl, lab = cabinet()
render([(floor, hexc('#bdb6aa'))]+op, gl, lab, 'render_front.jpg', eye=(-620, -1150, 760), target=(250, 200, 200), fov=30)
# 2) rear 3/4 view (control pod, IEC inlet, back ports)
render([(floor, hexc('#bdb6aa'))]+op, gl, lab, 'render_rear.jpg', eye=(1150, 1500, 700), target=(250, 250, 200), fov=30, key=(0.55, 0.7, 0.55))
# 3) stack of two cabinets (PLA under PETG), front 3/4 right
pla_cols = ['#f1f1ee','#2f2f2f','#d62828','#2d7dd2','#4caf2a','#f2b705','#8d99ae','#ff7a1a','#7b4fd6','#e84393','#11a3a3','#f1f1ee']
op1, gl1, lab1 = cabinet(0, 0, 'PLA', pla_cols, ports_open=())
op2, gl2, lab2 = cabinet(0, ZT-ZB, 'PETG', SPOOL_COLS, ports_open=())
render([(floor, hexc('#bdb6aa'))]+op1+op2, gl1+gl2, lab1+lab2, 'render_stack.jpg', eye=(1350, -1650, 1150), target=(250, 200, 450), fov=34, H=1500)
print('ok')
