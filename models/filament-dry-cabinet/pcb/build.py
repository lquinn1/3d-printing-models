# SPDX-License-Identifier: MIT
"""Build the cabinet's PCBs from circuit.py: place, autoroute (Freerouting), pour ground,
check (DRC + connectivity), and write fabrication files and images.

  python3 pcb/build.py [--place-only] [board ...]

Needs KiCad 7 (pcbnew Python + kicad-cli), Java and freerouting.jar (FREEROUTING env var or
/tmp/fr/freerouting.jar), and xvfb-run for Freerouting's GUI-less run.
"""
import os, sys, subprocess, shutil, json, csv
import pcbnew
from circuit import FP, BOARDS

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = '/usr/share/kicad/footprints'
FR = os.environ.get('FREEROUTING', '/tmp/fr/freerouting.jar')
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))

# design rules (JLCPCB / PCBWay standard 2-layer, 2 oz)
CLEAR, TRACK, VIA, VIA_DRILL = 0.2, 0.4, 0.8, 0.4
CLASSES = {'Power': (2.0, 0.3), 'Mid': (1.0, 0.25)}  # track width, clearance (2 oz copper: 2 mm carries the 6.3 A heater)

def load_fp(key):
    lib, name = FP[key].split(':')
    f = pcbnew.FootprintLoad(os.path.join(LIB, lib + '.pretty'), name)
    if key == 'SOCK22X2':
        # second row of holes 2.54 mm further from J1 (local -x before the 270 deg turn becomes +y),
        # same pad numbers, so either row carries the same nets
        from circuit import ROW_ALT, ROW
        for p in list(f.Pads()):
            q = p.Duplicate(); d_ = V(ROW_ALT - ROW, 0); q.SetPos0(p.GetPos0() + d_); q.SetPosition(p.GetPosition() + d_)
            q.SetShape(pcbnew.PAD_SHAPE_OVAL); f.Add(q)
        f.SetFPID(pcbnew.LIB_ID('dcc', 'PinSocket_1x22_P2.54mm_TwinRow'))
    return f

def build(name, cfg):
    b = pcbnew.BOARD()
    ds = b.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_TrackMinWidth = mm(0.2); ds.m_MinClearance = mm(0.2); ds.m_ViasMinSize = mm(0.6)
    ns = ds.m_NetSettings
    d = ns.m_DefaultNetClass
    d.SetClearance(mm(CLEAR)); d.SetTrackWidth(mm(TRACK)); d.SetViaDiameter(mm(VIA)); d.SetViaDrill(mm(VIA_DRILL))
    for cname, (w, c) in CLASSES.items():
        nc = pcbnew.NETCLASS(cname); nc.SetTrackWidth(mm(w)); nc.SetClearance(mm(c))
        nc.SetViaDiameter(mm(1.6 if cname == 'Power' else 1.0)); nc.SetViaDrill(mm(0.8 if cname == 'Power' else 0.5))
        ns.m_NetClasses[cname] = nc
    nets = {}
    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
        return nets[n]
    for ref, key, val, x, y, rot, pads, mpn in cfg['parts']:
        f = load_fp(key)
        f.SetReference(ref); f.SetValue(val)
        f.SetPosition(V(x, y)); f.SetOrientationDegrees(rot)
        for p in f.Pads():
            n = pads.get(p.GetNumber())
            if n: p.SetNet(net(n))
        f.Value().SetVisible(False)
        b.Add(f)
    for i, (x, y) in enumerate(cfg['holes']):
        f = load_fp('M3'); f.SetReference(f'H{i+1}'); f.SetPosition(V(x, y)); f.Reference().SetVisible(False); b.Add(f)
    # outline with 2 mm corner radius
    W, H, r = cfg['w'], cfg['h'], 2.0
    def seg(a, c):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*c))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
    def arc(cx, cy, sx, sy, ex, ey):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetCenter(V(cx, cy)); s.SetStart(V(sx, sy))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
    seg((r, 0), (W - r, 0)); seg((W, r), (W, H - r)); seg((W - r, H), (r, H)); seg((0, H - r), (0, r))
    arc(W - r, r, W - r, 0, W, r); arc(W - r, H - r, W, H - r, W - r, H); arc(r, H - r, r, H, 0, H - r); arc(r, r, 0, r, r, 0)
    # title on the silkscreen
    t = pcbnew.PCB_TEXT(b); t.SetText(cfg['title'] + '  rev A'); t.SetLayer(pcbnew.B_SilkS)
    t.SetPosition(V(W / 2, H - 3)); t.SetTextSize(V(1.2, 1.2)); t.SetMirrored(True); b.Add(t)
    return b, nets

def sexp(text):
    """Minimal s-expression reader (strings in double quotes)."""
    import re
    toks = re.findall(r'"[^"]*"|\(|\)|[^\s()]+', text)
    stack = [[]]
    for t in toks:
        if t == '(': stack.append([])
        elif t == ')': x = stack.pop(); stack[-1].append(x)
        else: stack[-1].append(t.strip('"'))
    return stack[0][0]

def import_ses(b, path):
    """Add Freerouting's wires and vias (Specctra session file) to the board."""
    import re
    tree = sexp(open(path).read())
    routes = next(x for x in tree if isinstance(x, list) and x[0] == 'routes')
    res = next(x for x in routes if isinstance(x, list) and x[0] == 'resolution')
    k = 1e3 * float(res[2])                                  # file units per mm (res = units per um)
    layers = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu}
    byname = nets_by_name(b)
    netout = next(x for x in routes if isinstance(x, list) and x[0] == 'network_out')
    for n in netout[1:]:
        ni = byname[n[1]]
        for item in n[2:]:
            if item[0] == 'wire':
                path_ = next(x for x in item if isinstance(x, list) and x[0] == 'path')
                lay, w, pts = layers[path_[1]], float(path_[2]) / k, [float(v) for v in path_[3:]]
                xy = [(pts[i] / k, -pts[i + 1] / k) for i in range(0, len(pts), 2)]
                for a, c in zip(xy, xy[1:]):
                    t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetWidth(mm(w))
                    t.SetLayer(lay); t.SetNet(ni); b.Add(t)
            elif item[0] == 'via':
                dia, drill = (int(v) / 1000 for v in re.search(r'_(\d+):(\d+)_um', item[1]).groups())
                v = pcbnew.PCB_VIA(b); v.SetPosition(V(float(item[2]) / k, -float(item[3]) / k))
                v.SetWidth(mm(dia)); v.SetDrill(mm(drill)); v.SetNet(ni); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                b.Add(v)

def nets_by_name(b):
    return {str(n): ni for n, ni in b.GetNetsByName().items()}

def courtyard_report(b, cfg):
    """Courtyard overlaps and parts off the board (front courtyards, as boxes)."""
    fps = list(b.GetFootprints())
    boxes = {}
    for f in fps:
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False, False)
        boxes[f.GetReference()] = (bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6)
    issues = []
    refs = sorted(boxes)
    for i, a in enumerate(refs):
        A = boxes[a]
        if A[0] < -0.01 or A[1] < -0.01 or A[2] > cfg['w'] + 0.01 or A[3] > cfg['h'] + 0.01:
            # terminal blocks' wire side and the DevKit's antenna may hang over the edge on purpose
            issues.append(f'{a} outside board {tuple(round(v,1) for v in A)}')
        for c in refs[i+1:]:
            if {a, c} <= {'U1A', 'U1B', 'U1C'}: continue
            C = boxes[c]
            ox, oy = min(A[2], C[2]) - max(A[0], C[0]), min(A[3], C[3]) - max(A[1], C[1])
            if ox > 0.05 and oy > 0.05: issues.append(f'{a} x {c} overlap {ox:.1f} x {oy:.1f}')
    return issues, boxes

RESULTS = {}

def main():
    place_only = '--place-only' in sys.argv
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(BOARDS)
    for name in names:
        cfg = BOARDS[name]
        b, nets = build(name, cfg)
        issues, boxes = courtyard_report(b, cfg)
        print(f'== {name}: {len(issues)} placement issues')
        for s in issues: print('  ', s)
        out = os.path.join(HERE, name); os.makedirs(out, exist_ok=True)
        b.Save(os.path.join(out, name + '.kicad_pcb'))
        if place_only:
            import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(cfg['w']/10, cfg['h']/10 + 0.4))
            ax.add_patch(plt.Rectangle((0, 0), cfg['w'], cfg['h'], fill=False, lw=1.5))
            for r, (x0, y0, x1, y1) in boxes.items():
                ax.add_patch(plt.Rectangle((x0, y0), x1-x0, y1-y0, fill=True, alpha=0.25, ec='k', lw=0.5))
                ax.text((x0+x1)/2, (y0+y1)/2, r, ha='center', va='center', fontsize=6)
            for f in b.GetFootprints():
                for p in f.Pads():
                    q = p.GetPosition(); ax.plot(q.x/1e6, q.y/1e6, 'r.', ms=2)
            ax.set_xlim(-30, cfg['w']+30); ax.set_ylim(cfg['h']+15, -15); ax.set_aspect('equal')
            plt.savefig(f'/tmp/place_{name}.png', dpi=110, bbox_inches='tight'); plt.close()
            continue
        # ---------------------------------------------------------------- net classes
        ncs = b.GetDesignSettings().m_NetSettings.m_NetClasses
        for n, ni in nets.items():
            cls = 'Power' if n in cfg['power'] else 'Mid' if n in cfg['mid'] else None
            if cls: ni.SetNetClass(ncs[cls])
        pcb = os.path.join(out, name + '.kicad_pcb')
        for f in b.GetFootprints():
            if f.GetReference() in cfg.get('solid_gnd', ()):
                for p_ in f.Pads():
                    if p_.GetNetname() == 'GND': p_.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        # keep tracks and vias 0.8 mm off the board edge (the router only sees rule areas)
        W, H = cfg['w'], cfg['h']
        k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetDoNotAllowCopperPour(False); k.SetDoNotAllowTracks(True)
        k.SetDoNotAllowVias(True); k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); k.SetLayerSet(ls)
        ol = k.Outline(); ol.NewOutline()
        for x, y in ((-1, -1), (W + 1, -1), (W + 1, H + 1), (-1, H + 1)): ol.Append(mm(x), mm(y))
        ol.NewHole()
        for x, y in ((0.8, 0.8), (0.8, H - 0.8), (W - 0.8, H - 0.8), (W - 0.8, 0.8)): ol.Append(mm(x), mm(y), 0, 0)
        b.Add(k)
        if cfg.get('keepout'):
            x0, y0, x1, y1 = cfg['keepout']
            k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetDoNotAllowCopperPour(True); k.SetDoNotAllowTracks(True)
            k.SetDoNotAllowVias(True); k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
            ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); k.SetLayerSet(ls)
            ol = k.Outline(); ol.NewOutline()
            for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): ol.Append(mm(x), mm(y))
            b.Add(k)
        b.Save(pcb)
        # KiCad 7 keeps net class membership in the project file, not the board
        pro = pcb[:-len('.kicad_pcb')] + '.kicad_pro'
        pj = json.load(open(pro))
        pj['net_settings']['netclass_patterns'] = (
            [{'netclass': 'Power', 'pattern': n} for n in sorted(cfg['power'])] +
            [{'netclass': 'Mid', 'pattern': n} for n in sorted(cfg['mid'])])
        json.dump(pj, open(pro, 'w'), indent=2)
        # KiCad caches the project it saved above; route in a fresh process so the classes load
        r = subprocess.run([sys.executable, os.path.abspath(__file__), '--route', name])
        if r.returncode: sys.exit(r.returncode)

def route(name):
        cfg = BOARDS[name]
        out = os.path.join(HERE, name)
        pcb = os.path.join(out, name + '.kicad_pcb')
        b = pcbnew.LoadBoard(pcb)
        nets = nets_by_name(b)
        # ---------------------------------------------------------------- autoroute
        dsn, ses = os.path.join('/tmp', name + '.dsn'), os.path.join('/tmp', name + '.ses')
        for f in (dsn, ses):
            if os.path.exists(f): os.remove(f)
        b.SynchronizeNetsAndNetClasses(True)          # resolve the project's class patterns before export
        assert pcbnew.ExportSpecctraDSN(b, dsn), 'DSN export failed'
        r = subprocess.run(['xvfb-run', '-a', 'java', '-jar', FR, '-de', dsn, '-do', ses, '-mp', '100', '-dct', '0'],
                           capture_output=True, text=True, timeout=1500)
        assert os.path.exists(ses), r.stdout[-2000:] + r.stderr[-2000:]
        import_ses(b, ses)
        # ---------------------------------------------------------------- ground pour, both sides
        W, H = cfg['w'], cfg['h']
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(nets['GND'].GetNetCode())
            ol = z.Outline(); ol.NewOutline()
            for x, y in ((0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)): ol.Append(mm(x), mm(y))
            z.SetLocalClearance(mm(0.4)); z.SetMinThickness(mm(0.3))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetThermalReliefGap(mm(0.5))
            z.SetThermalReliefSpokeWidth(mm(0.6))
            b.Add(z)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(pcb)
        print(f'   routed: {len([t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T])} segments, '
              f'{len([t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T])} vias')
        # ---------------------------------------------------------------- checks
        b = pcbnew.LoadBoard(pcb)
        b.BuildConnectivity()
        rpt = os.path.join(out, name + '_drc.txt')
        pcbnew.WriteDRCReport(b, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
        txt = open(rpt).read()
        import re
        starved = re.findall(r'starved_thermal\].*\n.*\n.*\n\s+@\(.*\): PTH pad (\w+) \[GND\] of (\w+)', txt)
        if starved:   # tracks crowd out a spoke: connect those few pads solid, re-pour, re-check
            for pad, ref in starved:
                for p_ in b.FindFootprintByReference(ref).Pads():
                    if p_.GetNumber() == pad: p_.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(pcb)
            b = pcbnew.LoadBoard(pcb); b.BuildConnectivity()
            pcbnew.WriteDRCReport(b, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
            txt = open(rpt).read()
            print(f'   {len(starved)} GND pads switched to solid connection (spokes blocked by tracks)')
        items = re.findall(r'^\[(\w+)\]: .*\n\s+(?:Rule: .*|Local override); Severity: (\w+)', txt, re.M)
        errs = [k for k, sev in items if sev == 'error' and k != 'lib_footprint_issues']
        warns = sorted({k for k, sev in items if sev != 'error' and k != 'lib_footprint_issues'})
        unc = int(re.search(r'Found (\d+) unconnected pads', txt).group(1))
        print(f'   DRC: {len(errs)} errors {sorted(set(errs))}, {unc} unconnected pads; warnings: {warns}')
        assert unc == 0, 'unrouted connections'
        RESULTS[name] = dict(errors=len(errs), unconnected=unc, warnings=warns)
        # ---------------------------------------------------------------- fab outputs
        fab = os.path.join(out, 'fab'); shutil.rmtree(fab, ignore_errors=True); os.makedirs(fab)
        subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', '-o', fab + '/', '--layers',
                        'F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts', '--subtract-soldermask', pcb],
                       check=True, capture_output=True)
        subprocess.run(['kicad-cli', 'pcb', 'export', 'drill', '-o', fab + '/', '--format', 'excellon',
                        '--excellon-separate-th', '--generate-map', '--map-format', 'pdf', pcb], check=True, capture_output=True)
        zipf = shutil.make_archive(os.path.join(out, name + '_gerbers'), 'zip', fab)
        shutil.rmtree(fab)
        # bill of materials for this board
        with open(os.path.join(out, name + '_bom.csv'), 'w', newline='') as fh:
            w_ = csv.writer(fh); w_.writerow(['Ref', 'Value', 'Footprint', 'Part'])
            for ref, key, val, *_rest in sorted(cfg['parts'], key=lambda p: (p[0][0], int(re.sub(r'\D', '', p[0]) or 0), p[0])):
                w_.writerow([ref, val, FP[key].split(':')[1], _rest[-1]])
        # images: top and bottom as the fab will see them
        for side, layers, mirror in (('top', 'F.Cu,F.Mask,F.SilkS,Edge.Cuts', False), ('bottom', 'B.Cu,B.Mask,B.SilkS,Edge.Cuts', True)):
            svg = os.path.join('/tmp', f'{name}_{side}.svg')
            cmd = ['kicad-cli', 'pcb', 'export', 'svg', '-o', svg, '--layers', layers, '--exclude-drawing-sheet', '--page-size-mode', '2']
            if mirror: cmd.append('--mirror')
            subprocess.run(cmd + [pcb], check=True, capture_output=True)
        print(f'   wrote {os.path.relpath(zipf, HERE)}')

if __name__ == '__main__':
    if '--route' in sys.argv: route(sys.argv[sys.argv.index('--route') + 1])
    else: main()

def render_board(name, px_per_mm=12):
    """Board images (top and bottom) from KiCad's per-layer SVGs: green mask, gold pads, white silk."""
    import cairosvg, numpy as np
    from PIL import Image, ImageDraw
    cfg = BOARDS[name]
    pcb = os.path.join(HERE, name, name + '.kicad_pcb')
    W, H = cfg['w'], cfg['h']
    size = (int(W * px_per_mm), int(H * px_per_mm))
    def layer(l, mirror=False):
        # whole page (board mm = page mm), then crop to the board; mirror ourselves for the bottom
        svg = f'/tmp/{name}_{l}.svg'
        subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', '-o', svg, '--layers', l, '--black-and-white',
                        '--exclude-drawing-sheet', '--page-size-mode', '0', pcb], check=True, capture_output=True)
        import re as _re
        vb = [float(v) for v in _re.search(r'viewBox="([^"]+)"', open(svg).read()).group(1).split()]
        png = svg[:-4] + '.png'
        cairosvg.svg2png(url=svg, write_to=png, output_width=int(vb[2] * px_per_mm), background_color='white')
        im = Image.open(png).convert('L').crop((0, 0, size[0], size[1]))
        if mirror: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        return np.array(im) < 128
    b = pcbnew.LoadBoard(pcb)
    out = []
    for side, cu, mask, silk, mir in (('top', 'F.Cu', 'F.Mask', 'F.Silkscreen', False), ('bottom', 'B.Cu', 'B.Mask', 'B.Silkscreen', True)):
        C, M, S = layer(cu, mir), layer(mask, mir), layer(silk, mir)
        img = np.zeros(size[::-1] + (3,), np.uint8)
        shape = Image.new('L', size, 0)
        ImageDraw.Draw(shape).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=2 * px_per_mm, fill=255)
        inside = np.array(shape) > 0
        img[inside] = (20, 90, 45)                       # solder mask over bare board
        img[inside & C] = (40, 125, 60)                  # copper under the mask
        img[inside & M] = (200, 170, 90)                 # openings: gold (ENIG) pads
        img[inside & M & ~C] = (150, 140, 110)
        img[inside & S & ~M] = (240, 240, 235)           # silkscreen
        im = Image.fromarray(img)
        d = ImageDraw.Draw(im)
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetDrillSize().x <= 0: continue
                x, y = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
                if mir: x = W - x
                r = p.GetDrillSize().x / 2e6 * px_per_mm
                d.ellipse([x * px_per_mm - r, y * px_per_mm - r, x * px_per_mm + r, y * px_per_mm + r], fill=(25, 25, 25))
        for t in b.GetTracks():
            if t.Type() == pcbnew.PCB_VIA_T:
                x, y = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
                if mir: x = W - x
                r = t.GetDrillValue() / 2e6 * px_per_mm
                d.ellipse([x * px_per_mm - r, y * px_per_mm - r, x * px_per_mm + r, y * px_per_mm + r], fill=(25, 25, 25))
        out.append(im)
    gap = 20
    sheet = Image.new('RGB', (size[0], size[1] * 2 + gap), (250, 249, 246))
    sheet.paste(out[0], (0, 0)); sheet.paste(out[1], (0, size[1] + gap))
    return sheet
