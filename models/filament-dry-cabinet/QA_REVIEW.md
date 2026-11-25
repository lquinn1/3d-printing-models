# Filament dry cabinet: design and CAD QA review

Review of spec v0.15 and every STL in `cad/stl`, 2026-11-24. Each finding has a priority:

- **P1:** fix before the first full build (safety or a part that won't work).
- **P2:** should fix; it costs material, time or reliability.
- **P3:** optional improvement (looks or maker convenience).

**Fixed in this review** means the CAD and STLs were changed and re-checked. Everything else is a recommendation that has not been made yet.

## How it was checked

- **Mesh soundness:** every STL welded the way a slicer does (float32, merged by position), then checked for watertightness and non-manifold edges.
- **Printability:** bed fit (≤ 345 mm), area facing down at more than 45° above the first layer (overhangs and bridges), grouped by height so each one can be traced to a feature, and a ray-cast wall-thickness check.
- **Assembly:** all four assembly scripts re-run: `verify.py`, `verify_front.py`, `verify_door.py`, `verify_interior.py`, plus `pod.py check()`.
- **Engineering:** hand calculations on the rods, door seal, heater safety chain and power budget, and a cross-check of the BOM against the CAD.

## Summary

| # | Finding | Priority | Status |
|---|---|---|---|
| 1 | 11 threaded STLs had non-manifold "pinched" edges | P1 | **Fixed** |
| 2 | Desiccant lid was exported upside down (plate in mid-air) | P1 | **Fixed** |
| 3 | Heater safety chain: hot PTC on ABS ledges, AC-rated thermostat switching DC | P1 | Recommendation, BOM flagged |
| 4 | Door seal: foam tape probably needs far more force than 3 magnet pairs give | P1 (test) | Recommendation |
| 5 | Hinge frame leaf is two loose pieces, each held by one screw | P2 | Recommendation |
| 6 | PVC rods are at their temperature limit in the 55–60 °C cabinets | P2 | Recommendation |
| 7 | BOM: 24 PC4-M10 couplers listed, only 12 are ever in use | P2 | **Fixed** (BOM $781) |
| 8 | 20 near-identical tiles have no part labels | P2 | Recommendation |
| 9 | Material and print-time savings (infill, ports, plenum) | P2 | Recommendation |
| 10 | Knife edges on the feet and LED rails | P3 | Recommendation |
| 11 | Looks: box edges, seam reveals, two-tone, flush pull | P3 | Recommendation |
| 12 | Maker features: oven-safe desiccant, gel window, cut sheets, weight sensing | P3 | Recommendation |

The things that are already done well are listed at the end.

---

## 1. Non-manifold threaded parts (P1, fixed)

**Found:** 11 STLs failed once welded: all 3 port modules, the socket coupon, the 4 top tiles and 3 of the 4 back tiles. Between them they had 36 to 380 edges each shared by 4–10 triangles. PrusaSlicer, Orca and Bambu Studio would report "errors repaired" on them, and could fill or drop thin slivers inside the threads.

**Cause:** the cutters touched the thread mesh exactly, in two ways:
- the cylinder and cone facets lined up with the thread's vertex angles;
- the countersink cap planes landed on the thread's z grid, with the cone's narrow end exactly at the crest radius.

Manifold3D keeps such touching vertices separate, so the old `save()` check passed. They only merge in the STL.

**Fix (`coupons.py`):**
- `cyl(..., twist=TW)` turns the facets of every solid that touches a thread by 0.71°.
- `socket_cut` runs the thread 1.53 mm past both ends. Its cone planes sit off the thread grid, and each cone ends 0.17 mm inside the crest. The lead-in is still 45°, and the thread is unchanged.
- `save()` now also checks the mesh welded the way a slicer sees it, so this can't come back unnoticed.

All 66 STLs rebuilt; every one is now watertight when welded. All assembly checks pass.

> The socket's countersink is now 0.17 mm deeper. That's cosmetic, and the 0.25 mm thread fit you tested is unchanged.

## 2. Desiccant lid printed in mid-air (P1, fixed)

`print_pose()` flipped `desiccant_lid`. That put the 6 mm finger tab on the bed and the 64 × 130 mm slotted plate 6 mm up with nothing under it (5,920 mm² of unsupported ceiling). The flip was left over from the old heater-duct lid. The lid now prints as modelled: plate on the bed, tab up. Its overhang dropped to 77 mm², which is just the tab.

## 3. Heater safety chain (P1)

The design idea is right: a hardware cut-out that can't be overridden, PID control, and a fan-tach interlock in firmware. Three details weaken it.

**a. The element's temperature.** The BOM heater (European Thermodynamics HP05-1/22-12/24ET) is listed with a **220 °C** temperature rating. It sits on **printed ABS ledges**, and ABS softens at about 90–100 °C. If the fan stalls, a self-limiting PTC rises towards its limit. The KSD301 and TCO sit in the *outlet air*, so with no airflow they warm slowly while the ledges under the element soften. Options, best first:
- Use a PTC with a **low self-limit (≈ 100–120 °C surface)**. These are sold for incubators and enclosures and run safely even with no airflow. Measure it for HEATER before printing the duct.
- Put **aluminium angle or silicone standoffs** between the element and the ledges, so no ABS touches the element's frame.
- Clip **one thermal cut-out to the element's aluminium frame** (it reacts to a stalled fan in seconds). Keep the other in the outlet.

**b. Switching DC with an AC thermostat.** The KSD301 is rated for AC. Breaking 6.25 A at 24 V DC draws an arc that AC would put out at the next zero crossing. On an auto-reset part that cycles near its trip point, the contacts pit and can weld shut. The safer wiring is to let the KSD301 break a small **24 V relay coil** (or the MOSFET's gate supply) and the relay contacts carry the heater current. The one-shot TCO can stay in the 24 V line. Adding a relay is about $5 and isn't in the BOM yet.

**c. Test procedure.** The spec says to test the cut-outs. Make it a written step for the first build: unplug the fan, run the heater at 100 %, and log the NTC and the time to trip.

The power budget is fine. The heater (150 W), fan, LEDs (about 12 W at full white), ESP32, TFT and NFC come to about 175 W, against the LRS-200-24's 211 W.

## 4. Door seal force (P1: test before final build)

The seal is 9.5 × 3.2 mm EPDM sponge tape, about 2 m long, around the opening. Even a soft sponge needs about **15–35 kPa** to squeeze 25 %. Over 0.019 m² of seal that's roughly **250–650 N**. The three 10 × 3 mm N52 magnet pairs give maybe 10 N each across the 1–2 mm gap of a compressed seal, so **about 30 N in total**. The door will close, but the tape will hardly compress. It will touch the face without sealing it, and it will leak most at the corners.

**Cheap test:** stick 300 mm of tape on a scrap, press a door-weight block on it, and look for daylight. If it doesn't seal, either:
- switch to a **hollow P- or D-profile rubber seal** (fridge-style; Frost King V28WA "P-section" is 3/8 in × 7/32 in). It seals at a fraction of the force; or
- add a positive **cam or compression latch** on the right stile and keep the foam.

The magnets would then only hold the door shut; the latch or soft seal does the sealing. This matters more than anything else for how long the desiccant lasts.

## 5. Hinge frame leaf (P2)

`hinge_frame_leaf.stl` is **two separate pieces**, one per knuckle. Each is held by **one** M3 screw into a stile insert, so each can turn about its screw. The door with both panes weighs about 1.8 kg. Hanging 265 mm out from the hinges, that puts roughly 17 N on each hinge, which will slowly rotate the pieces, and the door sags onto the bottom rail. The knuckles are also small: Ø9 mm round a Ø3.3 pin leaves 2.85 mm of wall.

Recommendation:
- Make each frame leaf one piece, with a web on the stile side outside the door knuckle's swing, or at least add a Ø4 dowel boss per piece into a hole in the stile.
- Use two screws per leaf.
- Grow the knuckles to Ø11–12 mm.

Re-run `verify_door.py` for the 110° swing afterwards.

## 6. PVC rods at 55–60 °C (P2)

Schedule 40 PVC is rated to about 60 °C (140 °F) and creeps long before that. One rod carries about 3.75 kg (6 spools across 2 rods) over 498 mm, so it sags about **2 mm at 50 °C**, and that grows with creep. That's fine for the PLA, PETG and TPU cabinets (≤ 50 °C). **For the ABS/ASA (55 °C) and nylon/PC (60 °C) cabinets, use CPVC.** Industrial (grey) **Sch 80 CPVC** is rated to about 93 °C. It is iron-pipe size with the same 1.050 in OD, so the cradles fit as they are. Don't buy the orange "CTS" CPVC from home centres: it's 0.875 in OD.

## 7. BOM corrections (P2, fixed)

- **PC4-M10 couplers:** only 12 are ever in use, on the top ports or on the back ports when stacked. One 20-pack covers it. The BOM total drops from $793 to **$781**.
- **IEC inlet:** it goes in the **pod base's right side wall**, not the pod cover.
- **Heater and KSD301 lines:** now carry the notes from §3.

The Sheet, `BOM.csv`/`BOM.md` and `bom_source.csv` are all updated.

## 8. Part labels (P2)

There are 20 tiles, and most come in mirror pairs or upper/lower pairs, plus 12 front and door parts. None carry an ID. A wrong tile only shows up when its bolts don't line up.

**Recommendation:** deboss the STL name and an "↑ FRONT" arrow, 0.4 mm deep, on the inside face of each tile's edge rib. That face prints facing up and is hidden by foil after assembly. Do the same on the door rail ends and frame parts. It costs nothing in print time and saves the most assembly mistakes of anything here.

## 9. Material and print time (P2)

The parts are 8.5 L of solid plastic, which is about 6.2 kg as printed. The shell tiles are 59 % of it.

| Idea | Saving | Note |
|---|---|---|
| Print only 12 PTFE modules + 12 blank plugs + 1 gland (not 24 PTFE) | about 30 g, 12 couplers | Already reflected in the BOM |
| Tile infill 40 % → 25 % gyroid, keeping 4 walls | about 0.4 kg, several hours | A skin-down tile's skin is all solid layers, so infill only reaches the ribs, land strips and bosses. Four walls round every insert is what holds the bolts. Bump insert bosses back up with a modifier if you like. |
| Plenum walls 3 → 2.4 mm | about 70 g | Interior part; still stiff at 60 °C |
| Keep the 2.4 mm skin | none | Thinner skins save about 0.5 kg but change WALL and every dimension, and ABS warps more |

**Print time:** with no slicer here, a rough estimate is **120–180 printer-hours** for one cabinet at ABS speeds. Slice one top tile and one side tile to pin it down before ordering 7 kg.

The filament note in DESIGN §13 ("3–4 kg for the shell") assumed 40 % gyroid. §9 and the BOM (7 kg in all) are the current figures.

## 10. Small printability items (P3)

- **Feet:** the 45° frustum comes to a knife edge on the bed (0.3 mm at the rim). Add a 1 mm vertical land at the base so it doesn't curl or show elephant's foot.
- **LED rails:** the triangular profile has a sharp 40° edge on the bed (down to 0.13 mm thick). Clip 1 mm off both acute corners.
- **Everything else is clean:**
  - every part fits the 350 mm bed;
  - no part needs supports;
  - the remaining downward faces are thread flanks (60°, printed fine on your coupon), 45° countersinks, and short bridges: the cartridge slots (≤ 37 mm), the tenon pockets in the door rails and stiles (4 mm wide), and the duct ceiling (15 mm).

## 11. Looks (P3)

- **Box edges:** the 12 outside edges of the cabinet are square, and the corner seam sits right on the edge. A **3 mm chamfer or radius** on every outside box edge makes it look finished, hides the corner seam, and resists dings. Split it between the two meeting tiles.
- **Seam reveals:** the 0.8 mm skin chamfers make a 1.6 mm V at each seam. Widening it to **1.5 mm per side** makes the tile joints read as deliberate panel lines, and hides small steps between tiles.
- **Two-tone:** to match the concept, print the shell in a light ASA and the frame, header, door and pod in matte black ASA. Print the outside faces on **textured PEI**: every tile already prints skin-down, so the whole outside gets the same texture.
- **Colour per cabinet:** tie each cabinet's colour band on the screen to an accent: the backup tag, the door handle, or the LED idle colour.
- **Flush pull:** a recessed finger pull cut into the right stile instead of the D-pull gives a cleaner front and nothing to catch when cabinets are stacked or pushed together.

## 12. Maker features (P3)

- **Oven-safe desiccant:** the printed cartridges can't go in the oven, so recharging means pouring the gel out. Either size the bays to an off-the-shelf **aluminium rechargeable desiccant canister** (oven-safe, no pouring), or add a stainless mesh basket that lifts out of the printed cartridge.
- **Gel window:** a small clear window or slot where the door can see a cartridge, so you can check the indicating gel with the power off. A humidity indicator card behind the glass does the same.
- **Cut sheets:** a 1:1 PDF template for the foam panels and both polycarbonate panes, laid out on a 4 × 8 ft foam sheet and the 24 × 36 in polycarbonate sheet. That saves measuring and wasting material on 20 foam pieces.
- **Assembly guide:** exploded renders per phase, with the part labels from §8, the insert count per part, and the bolt length per joint. 239 inserts is a long session, so group them by tile.
- **Fewer bolts:** the tile seams use 75 bolts at a 75 mm spacing (`SPACING`). Since the tongue and groove does the aligning, 100 mm spacing would remove about 20 inserts and bolts. Check it on the `tile_joint_b` reprint first: the seam must still squeeze its foam tape evenly.
- **Weight per slot (future):** load cells under the rod cradles (HX711) would let Spoolman track how much filament is left in each slot. The cradles are the natural place for them if you ever redesign the cradles.

## Things that are already done well

- Mains, PSU and controller are all outside the heated chamber, the PSU is earthed, the inlet is fused, and only 24 V goes inside.
- The load path is good: the top and bottom span the full width, so a stacked cabinet's weight goes straight down the walls. The feet nest into roof pockets, and their bolt heads are hidden.
- Every tile prints skin-down with no supports, so the outside finish is consistent. Every part fits the bed with margin.
- One port design is used everywhere, with an O-ring seal and a blank as the default. Those are the right calls for a modular system.
- The screen doubles as the label, so changing what a cabinet holds needs no reprint.
- Removal paths, the door swing, seal backing and component fit are all checked in code, not by eye.
