---
title: Multiboard LED Light Bar
category: Multiboard
status: Draft
material: PETG or ABS
printer: Voron 2.4 R2 350
tags: [multiboard, led, light-bar, wall-wash, push-fit]
summary: Wedge end brackets that hold an 18 x 8.5 mm LED channel on a Multiboard, aimed down the wall at 30°. Any channel length.
---

# Multiboard LED Light Bar

![Light bar on a Multiboard (render)](images/preview.png)

Two wedge-shaped end brackets hold an aluminium LED channel out from a Multiboard, with the diffuser facing **back and down toward the wall**. The light hits the wall at **30° to its surface**, which gives a long, soft wash downward. Each bracket presses onto a standard Multiboard **push-fit bolt**, and the channel ends slide into a pocket in each bracket, so the bar can be any length.

![Side section](images/section.png)

## Files

| File | Description |
|------|-------------|
| [`files/light_bar_bracket_left.stl`](files/light_bar_bracket_left.stl) / [`.step`](files/light_bar_bracket_left.step) | Left end bracket. Closed end. |
| [`files/light_bar_bracket_right_wire.stl`](files/light_bar_bracket_right_wire.stl) / [`.step`](files/light_bar_bracket_right_wire.step) | Right end bracket, with a Ø6 mm hole in the end wall for the LED strip's wire |
| [`source/light_bar_bracket.py`](source/light_bar_bracket.py) | CadQuery script. Change the light angle, channel size, standoff or pocket depth at the top and rerun it. |

You need **one of each bracket per bar**. To put the wire at the other end, mirror the brackets in the slicer.

## Hardware / Bill of Materials

| Qty | Item | Notes |
|-----|------|-------|
| 1 | Aluminium LED channel with diffuser, **18 × 8.5 mm outer** (16 × 7 mm inside) | Typical 1 m U-channel kits. The kit's end caps and mounting clips aren't used. |
| 1 | LED strip, up to about 15 mm wide | Sits in the channel |
| 2 | Multiboard **13 mm Big Thread – Flat Head – Push-Fit Hole – Bolt** | Printed. These screw into the Multiboard's big holes, and the brackets press into them. |

## Design

| Feature | Value |
|---------|-------|
| Light direction | Diffuser faces the wall. The light reaches the wall at 30° to its surface, aimed downward. |
| Channel pocket | 18.4 × 8.9 mm (0.2 mm clearance per side), 10.5 mm deep, tilted to match the light angle |
| Channel position | Centre about 30 mm out from the board and 8 mm below the bolt centre |
| Bracket | 16 mm thick, 40 mm tall where it meets the board, about 44 mm deep. Edges rounded R1.5. |
| Push-fit plug | Octagon 13.5 mm across the flats at the base, tapering to 13.24 mm, 8.5 mm long, 0.6 mm tip chamfer. The size comes from the official Multiboard push-fit holder. |
| Wire hole (right bracket) | Ø6 mm through the 5.5 mm end wall, centred on the channel |

### Channel length vs. bolt spacing

The Multiboard big holes are on a **25 mm grid**. Each pocket floor sits 1.25 mm outboard of its plug's centre, so with bolt centres **S** apart:

- **Full fit:** channel length = **S + 0 to 2.5 mm**. For example, an **uncut 1 m channel** fits bolts **1000 mm apart** (40 holes), with about 1.25 mm of slack at each end.
- **Cut channel:** cut it to the bolt spacing **plus about 1 mm**. For bolts 225 mm apart, cut it to about 226 mm.

Each end of the channel sits about 9 mm into its pocket.

## Print Settings

Not printed yet. Suggested settings:

| Setting | Value |
|---------|-------|
| Orientation | **Lay each bracket on its outer face**: the flat side with no pocket. The pocket opens upward, and the octagon plug lies flat on the bed, the way Multiboard push-fit parts are designed to print. |
| Supports | None |
| Walls / infill | 4 walls, 25–40% gyroid |
| Material | PETG or ABS. LED strips get warm, so avoid PLA if the strip runs bright. |

## Assembly

1. Screw two push-fit bolts into big holes on the same row, the right distance apart for your channel (see above). Stop when an octagon flat is level.
2. Put the LED strip in the channel, snap the diffuser on, and feed the wire out through the right bracket's hole.
3. Slide the channel ends into both brackets, with the **diffuser facing the wall**, toward the board.
4. Press both plugs into the bolts at the same time.

## Notes

- The pocket clearance (0.2 mm per side) is meant to be a light slip fit. If the channel is loose, add a drop of glue or a strip of tape on the channel end. If it's too tight, change `CLR` in the script.
- Multiboard is a trademark of its creator. These brackets are an original design made to fit the Multiboard push-fit system. Selling printed Multiboard parts may need Multiboard's commercial license.

## Revision History

- **v1.0** (2026-11-20): first version. 30° downward wall wash, push-fit plug, left and right (wire) brackets.
