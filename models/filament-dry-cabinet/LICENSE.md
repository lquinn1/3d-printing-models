# License: Filament Dry Cabinet

This project uses two licenses: one for the design, one for the code.

## Design files and documentation: CC BY-NC-SA 4.0

Copyright (c) 2026 lquinn1

The printable models (STL and STEP files), the design spec (`DESIGN.md`), the README, the layout drawings, the wiring diagram and the renders are licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)**:
https://creativecommons.org/licenses/by-nc-sa/4.0/

In short, you may:
- print, build, modify and share the design

as long as you:
- **give credit** and link back to this project
- **don't use it commercially.** That includes selling the files, the printed parts or built cabinets.
- **share any remix under the same license**

## Code: MIT

Copyright (c) 2026 lquinn1

The source code is licensed under the MIT License. That covers the Python scripts in `cad/` and `source/` (layout, drawing, rendering and CAD generation), plus the ESPHome YAML and the PN5180 external component when they're added. Each code file carries an `SPDX-License-Identifier: MIT` line.

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Not covered

These files belong to others. They're included for reference only, and neither license above applies to them:
- `docs/tft_3.5in_capacitive_drawing.png` and `docs/tft_3.5in_pinout.png`: the display vendor's drawing and pinout
- `images/concept.jpg`: the original inspiration image

## Safety

This project includes 120 V mains wiring and a heater. It is provided as is, with no warranty. You build and use it at your own risk. Follow your local electrical codes, and use the hardware and firmware safety cut-outs described in DESIGN.md §6.3.
