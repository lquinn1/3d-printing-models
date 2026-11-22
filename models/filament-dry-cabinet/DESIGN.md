# Filament Dry Cabinet: Design Spec (v0.6)

This spec is for review before any CAD. v0.2 includes your answers to the open questions (§10). It sets the layout, construction, electronics, ESPHome control and the Spoolman slot scheme for **one cabinet**. You'll build **one cabinet per material family**: PLA, PETG, ABS/ASA, and so on.

## 1. Requirements

| # | Requirement | How this design meets it |
|---|-------------|------------------------------|
| R1 | Filament storage that also dehumidifies | Sealed, insulated chamber with a **low-voltage PTC heater**, a circulation fan and **pull-out silica gel cartridges** (§5) |
| R2 | Modular, looks like the concept picture | **Printed tile panels** (each ≤ 330 mm, to fit the 350 mm bed) bolted together, a dark frame and a full-width glass door (§4) |
| R3 | PVC or other hardware-store parts as spool shelves | Spools roll on **3/4 in Sch 40 PVC pipe** (26.7 mm OD) set in printed cradles (§4.3) |
| R4 | ESPHome (ESP32) with local controls and status | ESP32-S3, a **2.0 in TFT and rotary encoder** for setpoints, plus the HA API and a local web page (§6, §7) |
| R5 | SK6812 LED lighting | **SK6812 RGBW** strip under the front header, 5 LEDs per slot, so it can **light up a single slot** (§6.4) |
| R6 | Front label plate, and an index position for each spool that Spoolman can manage | Swappable **material label plate** in the header. **Slot IDs F1–F6 and B1–B6** on index collars and the door rail (§8). |
| R7 | **≤ 20 in (508 mm) deep** for standard shelves, **≤ 20 in shelf spacing** | **447 mm (17.6 in)** cabinet, **497 mm (19.6 in)** with the rear control pod, using offset-height rows. **494 mm (19.5 in) tall.** (§3) |
| R8 | IEC 320 C14 fused inlet | **Fused and switched C14 module** in the rear control pod (§6.1) |
| R9 | About 12 spools | **12 × 1 kg spools** (200 mm across, up to 75 mm wide) |
| R10 | PTFE feed ports that can be closed off, on the **top and back** | **12 top ports** (one per slot) and **12 back ports**, all using one plug-in **port module**: PTFE or sealed blank (§4.6) |
| R11 | Stackable | Feet nest into **pockets in the cabinet below**, with optional side links (§4.7) |
| R12 | 120 V mains only | Inlet, fuse and PSU are specified for 120 V (§6.1) |
| R13 | Works with **OpenPrintTag** NFC spool tags | A **PN5180 NFC tap pad** in the front header. Tap a spool to check it into a slot, and the slot is written to Spoolman's Location field (§4.4, §6.5, §8). |

## 2. Concept

![Concept render](images/render_front.jpg)

![Stacked pair](images/render_stack.jpg) ![Rear](images/render_rear.jpg)

Renders are drawn from the spec dimensions (§3). The original inspiration image:

![Concept](images/concept.jpg)

## 3. Layout (chosen: one level, two offset rows of six)

![Side section](images/layout_side.png)

![Front view](images/layout_front.png)

**Spools roll on two PVC rods per row**, with their axles running side to side, so their faces point out the door like in the concept picture. Two rods 110 mm apart put a 200 mm spool's centre **99 mm above the rod centres**.

**The back row is raised 120 mm.** This lets the two rows overlap in depth (centres 169 mm apart instead of 207 mm). The back spools show above the front ones, so you can read them through the door. It also leaves a **service void under the back row, about 184 × 142 × 500 mm**, which holds the heater, fan duct and desiccant cartridges without adding any height. In v0.2 the front rods sit 30 mm above the floor, so the void is 137 mm tall.

**There's 85 mm of lift room above the back row**, so you can lift a back spool up and over the front spool to take it out. **Kept in v0.2**, since your shelves allow 20 in. Without it, the cabinet would be 409 mm / 16.1 in tall.

### Overall size (layout A)

| | mm | in |
|---|---|---|
| Width | 540 | 21.3 |
| Depth (cabinet) | 447 | 17.6 |
| Depth with the rear control pod | 497 | **19.6 (< 20)** |
| Height (with 10 mm stacking feet) | **494** | **19.5** |
| Height per cabinet when stacked (feet nest into the pockets) | 484 | 19.1 |
| Interior (W × D × H) | 500 × 399 × 444 | 19.7 × 15.7 × 17.5 |

### Layout options considered (all 12 spools)

| Option | Arrangement | W × D × H (in) | Notes |
|---|---|---|---|
| **A (chosen)** | 1 level, 2 offset rows × 6 | **21.3 × 17.6 (19.6 with pod) × 19.5** | Uses the full shelf depth. Low enough to fit under typical shelf spacing. Dead space houses the heater and desiccant. |
| B | 2 levels × (2 offset rows × 3) | 11.8 × 17.6 × 36.9 | Narrow but very tall. Won't fit between most shelves. |
| C | 3 levels × 4, single row | 15.0 × 10.9 × 31.1 | Shallow and tall. Wastes half the shelf depth. |

`source/layout.py` recalculates all of this. Change the spool size, rod size or offset and rerun it.

## 4. Construction

### 4.1 Shell: printed tile panels
- **Walls are 20 mm thick:** a printed tile tray (2 mm skin plus edge ribs) holding **1/2 in XPS foam board** (hardware store), with the inside faced in **aluminium foil tape**. The foil works as a vapour barrier and reflects heat back in.
- **Tiles are ≤ 330 × 330 mm** (350 mm bed). Each face is a 2 × 2 grid of tiles: sides, top, bottom and back, about 20 tiles in all, plus a front frame and corner posts.
- **Tiles join** with tongue-and-groove edges, **M4 heat-set inserts and bolts**, and foam tape in the seams. You could swap a side tile later for one with a pass-through port or a window.
- **Material: ABS or ASA for every printed part** (your choice, v0.2). That gives every cabinet the same parts and lets any cabinet run up to 60 °C. ASA is better for parts that get sunlight or UV.
- **Feet:** printed, 10 mm tall, and they **nest into pockets in the top of the cabinet below** (§4.7).

### 4.2 Door
- A printed frame with **two panes of clear polycarbonate** (hardware-store "Lexan", 2–2.5 mm) and a 6 mm air gap. That insulates about twice as well as one pane, and stops condensation on the glass.
- **EPDM foam weatherstrip** around the opening, compressed by **magnetic catches** (10 × 3 mm neodymium magnets in printed pockets), plus a printed pull handle.
- **Printed hinges** with steel pins (M3 bolts or 1/8 in rod).
- A **reed switch** detects when the door is open. It turns the lights on and pauses the heater and fan.

### 4.3 Spool rods, cradles and index collars
- **4 × 3/4 in Sch 40 PVC rods**, each cut to about 498 mm (interior width minus 2 mm). Two carry the front row and two carry the back row.
- **Printed U-cradles** on the side walls let the rods turn, so spools spin freely and can feed out. The rods also lift straight out for cleaning. The back-row cradles sit on printed risers, 120 mm higher.
- **Index collars:** printed split rings that clip onto the PVC every **80 mm** (75 mm spool plus 5 mm gap). They keep spools in their slots and carry the slot number moulded on top.

### 4.4 Front header and label plate
- A 60 mm header above the door holds, from left to right:
  - a **swappable label plate**: multicolour printed text such as "PETG" that slides into a groove
  - the **NFC tap pad**, a recessed area with a printed tap icon over the PN5180 antenna
  - the **2.0 in TFT**
  - the **encoder knob**
- **The tap pad has no metal over it**, and the plastic covering the antenna is no more than 2–3 mm thick. If the PN5180 module you buy doesn't fit behind a 60 mm header, the header grows by up to 10 mm. The cabinet would then be 504 mm (19.8 in) tall, still under 20 in.
- The **slot numbers 1–6** are also moulded into the door's bottom rail, lined up with the columns.

### 4.5 Rear control pod (outside the chamber)
- A 50 mm deep printed box on the back panel. It holds the **IEC C14 inlet**, the **24 V PSU** and the **ESP32 board**, so mains wiring and electronics stay out of the heated, closed chamber.
- Wires pass into the chamber through a sealed gland.
- A removable back cover gives access, with ventilation slots for the PSU.

### 4.6 Closable PTFE ports (top and back)

**One port design is used everywhere.** Each tile gets a threaded **port socket**, a printed sleeve through the wall. A plug-in **port module** screws into the socket, sealed with an **O-ring**. The module comes in three versions:

| Module | Use |
|---|---|
| **PTFE pass-through** | **PC4-M10 push-fit coupler** on the outside for the 4 mm OD PTFE tube to the printer. Inside, a short PTFE guide tube runs toward the spool. |
| **Blank plug** | Seals any unused socket. It's the default in every socket. |
| **Feed cap** | Push-fit cap over the coupler for when the tube is disconnected but you want to keep the PTFE routing |

**Port positions:**
- **Top: 12 ports, one per slot.** They sit straight above each spool, at the front-row and back-row lines (§3 drawing). Filament comes off the top of the spool straight up.
- **Back: 12 ports in two staggered rows**, high on the back wall above the control pod. Guide tubes inside run up over the back row and down to each slot. **Use the back ports when cabinets are stacked**, since the cabinet above covers the top ports.

**Seal:** an O-ring on each module plus foam tape around the socket sleeve, so a closed port seals as well as the rest of the wall.

**Socket size:** about M20 × 2 printed thread, with a 16 × 2 mm O-ring. This will be finalised in CAD after a fit test with a printed coupon, the same approach used for the dragon egg socket.

### 4.7 Stacking

- **Feet nest into pockets:** each cabinet has four 10 mm feet that drop into matching **pockets in the roof** of the cabinet below. That keeps them aligned and stops them sliding.
- **Optional side links:** printed **link plates** bolt across the seam on each side, so a stack can't tip.
- **Limits:** stacks of **2, or 3 at most**. A loaded cabinet weighs roughly 12 kg of spools plus the cabinet itself, so the roof tiles get extra ribs around the pockets.
- **Power and ports:** every cabinet has its own inlet and controller. Stacking doesn't block the rear pods or the back ports.

## 5. Drying system

**How it works:** warm air holds the same amount of water at a much lower relative humidity, and warm plastic gives up moisture. The heater warms the chamber gently, and the **fan pulls chamber air down through the desiccant cartridges and over the PTC heater**. Warm, dry air leaves along the floor at the front, rises up the inside of the door, which also keeps the door glass clear, and returns down the back through the desiccant. Moisture driven out of the spools ends up in the silica gel, not back in the filament.

| Item | Spec |
|---|---|
| Heater | **24 V PTC element with fins, 150 W, the same in every cabinet**, in a printed **ABS/ASA** duct on standoffs. **PID control** sets how much of that power is used for each cabinet (§7). |
| Fan | 24 V **4-pin PWM** fan (60–80 mm) with tach, so the firmware can tell if it stops |
| Desiccant | **2 pull-out cartridges, about 300–400 g of orange indicating silica gel each**. They sit in the return-air path in the service void. |
| Recharging | Empty the gel into a metal tray and dry it in an oven at the temperature on the gel's packaging. **The printed cartridges can't go in the oven.** Firmware counts the days since the last recharge, and watches for absolute humidity creeping up. |
| Heat loss (estimate) | About 40 W at ΔT 15 °C, 65 W at ΔT 25 °C, and 90 W at ΔT 35 °C (walls U ≈ 1.5, twin-pane door U ≈ 2.7 W/m²K). 150 W gives a 60 °C cabinet headroom in a cool room and a fast warm-up. In a 40 °C PLA cabinet, PID simply runs it at a low duty, roughly 25–40 %. |

### Default settings per cabinet (storage, not hard drying)

| Cabinet | Max chamber temp | Target RH | Notes |
|---|---|---|---|
| PLA / PLA+ / silk | 40 °C | ≤ 30 % | Never above 45 °C |
| PETG / PCTG | 50 °C | ≤ 20 % | |
| ABS / ASA | 55 °C | ≤ 20 % | |
| TPU | 40 °C | ≤ 20 % | |
| Nylon / PC / CF blends | 60 °C | ≤ 10–15 % | Extra desiccant |

There's also a **"Dry" mode** that runs a timed cycle at the cabinet's maximum temperature, such as 6 h at 50 °C for PETG. It's a top-up, not a replacement for a proper filament dryer.

## 6. Electronics

![Electrical block diagram](images/wiring.png)

### 6.1 Power
- **Mains: 120 V only.**
- **Inlet:** a UL-recognised IEC 320 C14 panel module with a **fuse holder and switch** (5 × 20 mm, **3.15 A T** slow-blow, 250 V rated). Earth (PE) goes to the PSU's FG terminal and to any metal parts. Use 18 AWG wire with ferrules, plus strain relief. The module snaps into a printed cutout, sized from the datasheet of the exact part you buy.
- **PSU:** **Mean Well LRS-200-24** (24 V, 8.8 A) in its enclosed metal case, the same in every cabinet.
- **5 V:** a 24 → 5 V buck converter (3–5 A) for the LEDs, display and ESP32. The LED feed has its own 3 A fuse.

**Power budget at 24 V:** heater 6.3 A, fan 0.1–0.3 A, 5 V loads about 0.8 A (LEDs at full white about 3 A at 5 V). The peak is about 7.4 A with the 150 W heater, within the LRS-200's 8.8 A.

### 6.2 Controller and I/O (ESP32-S3-DevKitC-1 N16R8)

| Function | Part | ESP32 interface |
|---|---|---|
| Chamber T/RH | **SHT45** (top rear, out of the direct heater flow) | I2C |
| Desiccant-outlet T/RH | SHT40 (shows how well the desiccant is working) | I2C (second address or second bus) |
| Room T/RH (optional) | SHT40 in the control pod | I2C |
| Heater outlet temp | 10 k NTC (or DS18B20) at the duct outlet | ADC (or 1-wire) |
| Heater | logic-level N-MOSFET, low side | GPIO, `slow_pwm` (about 5 s period) |
| Fan | 4-pin PWM | LEDC at 25 kHz, tach to `pulse_counter` |
| LEDs | SK6812 RGBW, about 30 LEDs | `esp32_rmt_led_strip`, via a **74AHCT125** level shifter, 330 Ω series resistor and 1000 µF at the strip |
| Display | 2.0 in ILI9341/ST7789 SPI TFT | SPI |
| Local control | EC11 rotary encoder with push switch | `rotary_encoder` + GPIO |
| Door | reed switch + magnet | GPIO (`binary_sensor`) |
| Buzzer (optional) | piezo for alarms | GPIO / LEDC |

### 6.3 Safety (in layers)
1. **Hardware, cannot be overridden:** a **KSD301 85 °C auto-reset thermostat** and a **102 °C one-shot thermal fuse (TCO)** in series with the heater's 24 V feed, mounted on the duct outlet. The PTC element also limits itself.
2. **Firmware interlocks:** the heater is forced off if:
   - the chamber is above its maximum + 5 °C, or the heater outlet is above its limit
   - either sensor reads NaN, or a reading hasn't updated for 60 s
   - the fan tach is below its minimum while heating
   - the door is open
   - a heater cycle runs longer than the watchdog limit
3. **Mains** stays only in the rear pod: an enclosed PSU, a fused inlet and an earthed metal PSU case. Only 24 V goes into the chamber.

### 6.4 Lighting
- One **SK6812 RGBW** strip (60/m) runs under the front header, aimed down and back. That's about **30 LEDs, 5 per slot column**.
- An ESPHome **partition** light is set up for each column, so Home Assistant can **light up one slot**: for example, highlight F3 in white and B3 in a different colour.
- The door switch turns on the full light. Normal brightness is capped at about 60 % to limit heat and current.
- **Colour options:** choose a preset colour or a custom RGB colour from the encoder menu (**Lights → Colour / Custom colour**), or with the colour picker in Home Assistant. "White" uses the SK6812's **dedicated white LED** for the cleanest light, which is best when you're reading labels. The colours mix the RGB LEDs. A colour is a nice way to match each cabinet to its material (for example amber for PETG). The choice is saved and restored after a power cut.
- **Find slot** uses a contrasting highlight colour, so the chosen slot stands out against whatever colour the cabinet is set to.

### 6.5 NFC reader (OpenPrintTag)

- **Why the PN5180:** OpenPrintTag uses **NFC-V tags (ISO 15693, NXP ICODE SLIX/SLIX2)**. The common RC522 and PN532 readers only handle ISO 14443 tags (MIFARE/NTAG). The **NXP PN5180** reads **both ISO 15693 and ISO 14443A**, so the same pad also works with NTAG-based formats such as OpenSpool and TigerTag.
- **Wiring:** it shares the **SPI bus** with the TFT and adds its own **NSS, BUSY and RST** pins. It needs **5 V** (RF) and **3.3 V** (logic) from the existing rails.
- **Range:** a few centimetres. This is tap-to-check-in at the front of the cabinet, not automatic detection of each slot.
- **Firmware: an ESPHome external component (new work).** ESPHome has no built-in PN5180 support. The plan is a small external component that wraps an existing open-source **ESP-IDF PN5180 driver** (ISO 15693 inventory, read blocks, NDEF Type 5). It would publish:
  - the tag's **UID**, and the **raw OpenPrintTag payload** (CBOR in an NDEF record)
  - a few decoded fields for the screen: brand, material, colour, and nominal and remaining weight
- **Decoding:** full decoding is done in Home Assistant or a small helper service, which keeps the firmware simple.
- **Tags:** spools that don't come with an OpenPrintTag get a **blank ICODE SLIX2 tag**. NTAG215 won't work for OpenPrintTag. Write it once with a phone app (Prusa app, SimplyPrint) or a USB reader.

## 7. ESPHome (planned entities)

| Entity | Type | Notes |
|---|---|---|
| Chamber temperature / humidity | sensor | SHT45 |
| Chamber **absolute humidity** (g/m³) and **dew point** | template sensor | The real measure of dryness. RH alone drops just because the air is warm. |
| Desiccant outlet T/RH | sensor | Desiccant efficiency = absolute humidity in − out |
| Heater outlet temperature | sensor | NTC |
| Heater power % | sensor / output | slow PWM duty |
| Fan speed (RPM) | sensor | tach |
| **Target humidity** | number (restored) | Local menu + HA |
| **Max chamber temperature** | number (restored) | Capped by the material preset |
| **Fan minimum %** | number (restored) | Circulation while idle |
| Mode | select | `Off` / `Maintain` / `Dry (timed)` |
| Material preset | select | Sets the defaults in §5. The label plate is the physical match. |
| Heater max power % | number (restored) | Optional cap on top of PID, for example 60 % in a PLA cabinet |
| Chamber heater | climate (`pid`) | PID on chamber temperature, with **autotune** |
| PID autotune | **local menu item** (not an HA button) | Started from the encoder menu (see the menu below). Runs `climate.pid.autotune`. Progress and results show on the TFT. |
| Dry timer (h) | number | For `Dry` mode |
| Desiccant days since recharge | sensor + reset button | Reminder |
| Door | binary_sensor | |
| Fault | text_sensor | Last interlock that tripped |
| NFC tag UID / last scan | text_sensor | From the PN5180 component |
| NFC tag data | text_sensor (+ HA event `drybox_tag_scanned`) | Raw OpenPrintTag payload, plus decoded brand, material, colour and weight |
| NFC check-in / check-out | event to HA | Carries the cabinet, slot and tag UID. HA updates Spoolman. |
| Cabinet light, Slot F1…B6 lights | light | Full strip + per-slot partitions. Home Assistant gets the full RGBW colour picker. |
| Light colour | select (restored) | **White (W channel)** · Warm white · Red · Orange · Amber · Yellow · Green · Cyan · Blue · Purple · Magenta · **Custom** |
| Custom colour R / G / B | number × 3 (0–255, restored) | Used when Colour = Custom. Set from the encoder or from HA. |

**Control loop (Maintain mode):**
1. Above the target RH, the **PID climate** heats toward the max chamber temperature, and the fan runs at the heating speed. The PID output drives the heater's slow PWM, so every cabinet uses the same 150 W heater.
2. Once the RH is 3 % below target, the heater stops and the fan drops to its minimum circulation speed. The fan keeps air moving through the desiccant.
3. If absolute humidity keeps rising with the heater off, the cabinet flags that the desiccant needs recharging.

**PID tuning:** every cabinet uses the same heater, but cabinets differ in where they stand, their ambient temperature and how many spools they hold. Run **autotune once per cabinet** with it loaded and the door closed. Start it from the **encoder menu (Tuning → PID autotune → Start)**. It asks you to confirm, so a stray knob press can't start it. The screen then shows the progress. ESPHome's `pid` climate drives the heater in a relay cycle around the setpoint, and the suggested kp, ki and kd are shown on the TFT and written to the log. Put those into the YAML substitutions, or into the restored `number` entities if you'd rather tune it live. The firmware interlocks (§6.3) stay active during autotune.

**Local UI:** the TFT shows a status page (T, RH, absolute humidity, heater %, fan RPM, mode, material). Pressing the encoder opens a **`graphical_display_menu`**, where you adjust the setpoints with the knob.

**Menu (draft):**

| Menu | Items |
|---|---|
| Mode | Off / Maintain / Dry (timed) |
| Setpoints | Target RH · Max chamber temp · Fan minimum % · Heater max % · Dry timer (h) |
| Material preset | PLA · PETG · ABS/ASA · TPU · Nylon/PC (loads the defaults in §5) |
| Lights | On/off · Brightness · **Colour** (preset list) · **Custom colour** (R / G / B, 0–255) · Find slot (choose F1–B6 to light it) |
| Desiccant | Days since recharge · **Reset after recharge** (asks to confirm) |
| **Spools** | **Check in** (tap, choose a slot, confirm) · **Check out** (tap or choose a slot) · Last scanned tag · Slot map (F1–B6 with what's in each) |
| **Tuning** | **PID autotune → Start** (asks to confirm) · Abort · Last result (kp / ki / kd) |
| Info | IP address · Wi-Fi signal · firmware version · last fault |
| Exit | Back to the status page | Everything also works without Wi-Fi. The local `web_server` shows status on the network.

**Version note:** recent ESPHome releases are changing how `esp32_rmt_led_strip` sets channel order (`rgb_order` + `is_rgbw` versus a single `GRBW`-style setting). The YAML will target whichever version you run.

## 8. Spoolman slot scheme

- **Slot ID = `<cabinet>-<row><position>`**, for example **`PETG-F3`** or **`ABS-B6`**. Put it in Spoolman's **Location** field for the spool. F is the front row and B is the back row, and positions run 1–6 from left to right.
- **On the cabinet:** the label plate shows the cabinet name ("PETG"). Index collars and the door rail show 1–6. The rows are physically obvious: front is low, back is high.
- **Spoolman QR labels** go on the spool sides that face the door. They're still useful for spools without an NFC tag.

### 8.1 NFC check-in / check-out flow (OpenPrintTag)

1. **Tap the spool** on the header pad. The screen shows the brand, material and colour from the tag. A material that doesn't match the cabinet's preset gets a warning, for example "PLA in the PETG cabinet?".
2. **Pick a slot** with the encoder. It suggests the first empty slot from the slot map, and that slot **lights up** as you scroll.
3. **Confirm** with a press. The ESP32 sends a `check_in` event (cabinet, slot, UID and tag data) to Home Assistant.
4. **Home Assistant → Spoolman:** an automation looks up the spool by the tag's UID, which is stored in a Spoolman **extra field**. If it isn't there yet, the automation **creates the vendor, filament and spool** from the tag data. Then it sets **Location = `PETG-B4`** (for example).
5. **Check out:** tap the spool (or pick its slot) and confirm. The automation clears the Location or sets it to the printer's name.

The slot map on the cabinet is rebuilt from Spoolman's Location fields at startup and after each change, so Spoolman stays the single source of truth.

**Spoolman support:** upstream Spoolman doesn't read OpenPrintTag yet (there's a fork with NFC lookup that hasn't been merged), so this flow uses Spoolman's existing REST API and extra fields through Home Assistant. If upstream adds native NFC lookup later, step 4 gets simpler, and nothing on the cabinet changes.
- **Home Assistant (phase 5):** use the Spoolman integration plus a script that, when you pick a spool, **lights its slot** in that cabinet. It can also show each cabinet's spool list and remaining weight on a dashboard.

## 9. Bill of materials (one cabinet, draft)

**Hardware store**
- 3/4 in Sch 40 PVC pipe, about 2 m (4 rods × 498 mm)
- 24 × PC4-M10 push-fit couplers (only as many as you'll use) + 4 mm OD PTFE tube
- 16 × 2 mm nitrile O-rings (one per port module)
- 1/2 in XPS foam board (one 2 × 4 ft sheet covers it)
- Clear polycarbonate sheet, 2–2.5 mm, 2 panes about 510 × 400 mm
- EPDM foam weatherstrip, about 2 m
- Aluminium foil HVAC tape
- M4 heat-set inserts, M4 × 10/16 bolts, M3 bolts for hinge pins

**Electronics**
- IEC C14 fused and switched inlet module, 3.15 A T fuse
- Mean Well LRS-200-24
- 24 → 5 V buck converter, 5 A
- ESP32-S3-DevKitC-1 N16R8
- SHT45 + 1–2 × SHT40 breakout boards, 10 k NTC
- 24 V PTC heater element, 150 W
- KSD301 85 °C NC thermostat, 102 °C TCO
- Logic-level MOSFET module (heater)
- 24 V 4-pin PWM fan (60–80 mm)
- SK6812 RGBW 5 V strip (60/m, 0.5 m), 74AHCT125, 330 Ω, 1000 µF
- 2.0 in SPI TFT (ILI9341/ST7789), EC11 encoder, reed switch + magnet
- **PN5180 NFC module** (ISO 15693 + 14443A, SPI). Check the board size against the header (§4.4).
- **Blank ICODE SLIX2 tags** for spools that don't ship with OpenPrintTag
- Wire: 18 AWG for mains, 20 AWG for 24 V. Ferrules, connectors.

**Consumables**
- Orange indicating silica gel, about 1 kg
- ABS or ASA filament for all printed parts

## 10. Decisions (v0.2)

| Question | Decision |
|---|---|
| Shelf height | 20 in shelves. **Keep the lift room**, and the cabinet is **19.5 in tall** after trimming the feet, cradles and top clearance. |
| PTFE ports | **Yes, top and back, closable:** one port module design with PTFE, blank and cap versions (§4.6) |
| Stacking | **Yes:** nesting feet and pockets, plus optional side links (§4.7) |
| UI | **2.0 in TFT + encoder** |
| Mains | **120 V only** |
| Shell material | **ABS or ASA** for all printed parts |
| Heater | **150 W in every cabinet**, with the same PSU and parts. **PID with autotune** adjusts it for each cabinet. |
| NFC | **Add an OpenPrintTag reader:** a PN5180 tap pad in the header for checking spools in and out (§6.5, §8.1) |

Still open (not blocking CAD):
- **Which material cabinet to build first?** This now only changes the label plate and the firmware preset.
- **Port socket thread:** this will be confirmed with a fit-test print.
- **PN5180 module size:** this decides whether the header stays at 60 mm or grows to 70 mm.

## 11. Plan

| Phase | Deliverable |
|---|---|
| **1 (this)** | Design spec, layout, electrical plan, BOM |
| 2 | CAD: tiles, corner posts, front frame, door, hinges, rod cradles and risers, index collars, label plate, header with display, heater duct, desiccant cartridges, rear pod, **port sockets and modules with a fit-test coupon**, **stacking feet, pockets and links**. STEP and STL. |
| 3 | ESPHome YAML, pin map and wiring diagram |
| 3b | **ESPHome PN5180 external component**: ISO 15693 inventory and read, plus OpenPrintTag payload. Tested on a bench board before it goes in the cabinet. |
| 4 | Prototype: one cabinet. Test the fit, the heat-up and holding RH. |
| 5 | Home Assistant and Spoolman: **NFC check-in/out automation** (find or create the spool, set Location), slot lighting, dashboards, desiccant alerts |
