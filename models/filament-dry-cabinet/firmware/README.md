# Firmware (ESPHome)

`dry-cabinet.yaml` runs one cabinet on the DCC-MAIN board (`../pcb/`). It compiles cleanly on ESPHome 2026.11 (ESP-IDF, ESP32-S3-DevKitC-1-N16R8): about 13 % of the app partition and 37 % of RAM.

## Flashing a cabinet

1. Copy `secrets.example.yaml` to `secrets.yaml` and fill in your Wi-Fi.
2. Copy `dry-cabinet.yaml` for each cabinet (for example `dry-cabinet-pla.yaml`) and change the top of `substitutions:`: `name`, `friendly_name` and `default_preset`. The pins underneath come from `pcb/circuit.py`; leave them alone.
3. The first flash goes over USB, with the DevKitC in its socket and the board **not** on 24 V: `esphome run dry-cabinet-pla.yaml`. After that, updates go over Wi-Fi.
4. If Wi-Fi fails, the cabinet starts its own access point with the same name. Connect to it to set Wi-Fi.
5. Home Assistant finds it on its own (ESPHome integration).

## First power-up checks

Do these on the bench, before the heater is wired to the chamber. Each one has a fix in the substitutions.

| Check | If wrong |
|---|---|
| Screen is landscape and the right way up | `tft_rotation`: 90 or 270 |
| Black background looks black, not white | `tft_invert`: true ↔ false |
| PETG label band is blue, not orange | `tft_color_order`: BGR ↔ RGB |
| White light uses the white LEDs, not RGB mixed | the strip may be RGBW in another order: change `channel_colors` |
| Fan speed reads about the fan's rated RPM at 100 % | tach `multiply` (2 pulses per turn on most PC fans) |
| Heater outlet temp reads room temperature cold | NTC B value (3950) or the NTC is open |
| Door sensor: Door = open when open | swap the reed position or add `inverted: true` |

Then test each **interlock** with the heater on (DESIGN §19 checklist): unplug the fan → "Fan stalled while heating" in 15 s; unplug the chamber sensor → "Chamber sensor lost" within 60 s; heat the NTC with a hot-air gun past 80 °C → "Heater outlet over temperature". Each one must switch off the relay and latch. Clear it from the menu (Info → Clear fault) or from HA.

## How it controls

Every 2 s the control loop:

1. **Interlocks** (any one latches a fault, opens the relay, sets heater 0 and runs the fan at 100 % to cool): chamber sensor missing or more than 60 s old · heater NTC missing · chamber more than 5 °C over the max · heater outlet over 80 °C · fan under 400 RPM for 15 s while heating · heater over 90 % for 20 min with the chamber still 15 °C short. No checks for the first 30 s after boot, while the sensors start; the outputs stay off then.
2. **Mode:** *Maintain* heats when RH is above target and stops 3 % below it. *Dry (timed)* heats for the dry timer, then goes back to Maintain (a reboot ends a dry cycle). *Off* is off, fan included.
3. **Door open** pauses heat and fan; the lights come on full and go off 10 s after it shuts.
4. **Heater:** the PID climate works toward the max chamber temperature. Its output, capped by *Heater max %*, is the slow-PWM duty (5 s period) on the MOSFET. The relay closes only while heating.
5. **Fan:** *Fan while heating* % when heating, *Fan minimum* % otherwise.

The hardware cut-outs (KSD301 85 °C on the relay coil, TCO 102 °C) work without the firmware.

## PID autotune

Load the cabinet with spools, shut the door, then **Menu → Tuning → PID autotune: start** and press again to confirm (8 s window). It takes 30–90 min. When it finishes, the new kp / ki / kd are applied, saved in flash and reused after every reboot, so nothing needs copying into the YAML. **Abort autotune** stops it. The substitution `pid_kp/ki/kd` values are only used until the first autotune.

## Local controls

- **Turn the knob** on the label page: switch between the label and detail pages.
- **Press**: open the menu. Turn to move, press to choose or to edit a value. The menu closes after 30 s.
- The backlight goes to 100 % on any knob use or door opening and back to *idle brightness* after 60 s.

The cabinet name (8 characters) is set from Home Assistant or the web page at `http://<name>.local`.

## Home Assistant

Entities: chamber and outlet T/RH, absolute humidity, dew point, desiccant pickup (g/m³ the desiccant removes), heater outlet temp, heater %, fan RPM, door, fault, status, all the settings, the cabinet light plus six slot-column lights, and *Find slot*.

`esphome.<name>_find_slot` lights a slot from a script, for example a Spoolman "where is this spool" button:

```yaml
action: esphome.dry_cabinet_petg_find_slot
data:
  slot: B4
```

Front and back slots in the same column share LEDs; the screen says which row.

## Not in this version

- **NFC (PN5180):** needs a custom ESPHome component; the pins are reserved and the entity `NFC last tag` is a placeholder. Check-in/check-out and the Spools menu come with it.
- **Touch (FT6336U):** wired on bus A; to be turned on with `ft63x6` later.
- **Name editing with the knob:** HA or the web page for now.
