# Photoreal scene (Blender / Cycles)

`images/render_photo_shelf.jpg`: two cabinets (PLA and PETG) on a 48 × 24 in chrome wire shelf, next to a generic Voron 2.4-style enclosed printer on a workbench.

1. `python3 export.py`: exports the cabinet from the CAD as PLY files grouped by material (plus spool positions and the screen location) into `/tmp/scene/`.
2. Make the screen textures (label pages), see the top of `scene.py`'s inputs: `/tmp/scene/tex/label_PLA.png`, `label_PETG.png`, `printer_lcd.png`.
3. `pip install bpy` (Blender as a Python module), then `python3 scene.py 1.0 160 out.png`: arguments are resolution scale (1.0 = 1920 × 1200), samples, output.

The printer is a simplified stand-in built in the script (no logos); only the cabinets come from the CAD.
