---
title: Filament Dry Cabinet
category: Storage
status: Design
material: ASA / PETG
printer: Voron 2.4 R2 350
tags: [filament, dry-box, dehumidifier, esphome, esp32, sk6812, spoolman, pvc, modular]
summary: Modular, heated, desiccant-dried 12-spool cabinet (one per material), with ESPHome control, SK6812 lighting and Spoolman slot IDs. Under 20 in deep.
---

# Filament Dry Cabinet

![Side section](images/layout_side.png)

A modular cabinet that stores **12 × 1 kg spools** and keeps them dry. A low-voltage **PTC heater** circulates warm air through **pull-out silica gel cartridges**. An **ESP32 running ESPHome** controls it, with a local display and knob for setpoints, and integrates with Home Assistant. **SK6812** lighting can highlight individual slots. Each spool position has an ID (`PETG-F3`, for example) for Spoolman's Location field. You'll build **one cabinet per material**. It plugs in through an **IEC C14 fused inlet**, and at **19.6 in deep** it fits standard shelves.

**Status: design spec for review. No CAD yet.** See **[DESIGN.md](DESIGN.md)** for the full spec.

![Front view](images/layout_front.png)

## At a Glance

| | |
|---|---|
| Capacity | 12 spools: two rows of 6, with the back row raised 120 mm |
| Size | 540 W × 447 D (497 with rear control pod) × 509 H mm (21.3 × 17.6 / 19.6 × 20.0 in) |
| Shelves | 3/4 in Sch 40 PVC rods in printed cradles, with printed index collars every 80 mm |
| Shell | Printed tile panels (≤ 330 mm) with 1/2 in XPS foam, and a twin-pane polycarbonate door |
| Drying | 24 V PTC heater (100/150 W) + PWM fan + about 700 g of silica gel |
| Control | ESP32-S3, SHT45/SHT40, 2.0 in TFT + encoder, ESPHome |
| Power | IEC C14 fused and switched inlet → Mean Well 24 V PSU in a rear pod outside the chamber |
| Safety | Hardware thermal cutouts (85 °C auto-reset + 102 °C fuse) and firmware interlocks |

## Files

| File | Description |
|------|-------------|
| [`DESIGN.md`](DESIGN.md) | Full design spec: requirements, layout options, construction, drying, electronics, ESPHome entities, Spoolman scheme, parts list, open questions |
| [`images/wiring.png`](images/wiring.png) | Electrical block diagram |
| [`source/layout.py`](source/layout.py) | Layout calculator. Change the spool and rod sizes or the offset and rerun it. |
| [`source/draw.py`](source/draw.py), [`source/wiring.py`](source/wiring.py) | Scripts that draw the layout and wiring figures |

## Revision History

- **v0.1** (2026-11-22): first design spec and layout for review.
