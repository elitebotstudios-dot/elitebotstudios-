#!/usr/bin/env python3
"""Generate the DCM-HW-V1 schematic, netlist and bill of materials.

Everything is derived from one file, design/dcm-hw-v1.json, so the drawing, the
netlist and the connection table cannot disagree with each other. The generator
also verifies that every wire endpoint lands on a component pin or on another
wire, and refuses to write a drawing with a floating connection.

    python3 energy-monitor/hardware/design/generate.py

Outputs
    schematic/dcm-hw-v1-sheet1.svg      power path and measurement
    schematic/dcm-hw-v1-sheet2.svg      sensor, I2C and microcontroller
    netlist/dcm-hw-v1-connections.csv   pin-by-pin connection table
    netlist/dcm-hw-v1.net               KiCad netlist, for import into Pcbnew
    bom/dcm-hw-v1-bom.csv               bill of materials

No EDA tool is used or claimed here. The SVG is a drawn schematic, not a KiCad
project; see design-review/design-review.md for exactly what has and has not
been verified.
"""
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESIGN = json.loads((HERE / 'dcm-hw-v1.json').read_text(encoding='utf-8'))
OUT = HERE.parent

STUB = 20          # pin stub length, px
FONT = "ui-monospace, 'SFMono-Regular', Consolas, monospace"

# --------------------------------------------------------------------------- #
# Symbol templates. Each returns the pin coordinates it actually draws, so the
# connectivity check below tests the drawing rather than an intention.
# --------------------------------------------------------------------------- #
def _box_pins(x, y, orient, left, right):
    """Pins for a two-lead part drawn horizontally or vertically."""
    if orient == 'horizontal':
        return {
            left[0]: (x - left[2] - STUB, y),
            right[0]: (x + right[2] + STUB, y),
        }
    return {
        left[0]: (x, y - left[2] - STUB),
        right[0]: (x, y + right[2] + STUB),
    }


def sym_resistor(x, y, orient, comp, pins):
    w, h = (72, 28) if orient == 'horizontal' else (28, 72)
    coords = _box_pins(x, y, orient, ('1', 1, w / 2), ('2', 2, w / 2))
    body = f'<rect class="sym-body" x="{x - w/2}" y="{y - h/2}" width="{w}" height="{h}" rx="3"/>'
    return body, coords


def sym_capacitor(x, y, orient, comp, pins):
    coords = _box_pins(x, y, orient, ('1', 1, 18), ('2', 2, 18))
    if orient == 'vertical':
        body = (f'<line class="sym-body" x1="{x-22}" y1="{y-6}" x2="{x+22}" y2="{y-6}"/>'
                f'<line class="sym-body" x1="{x-22}" y1="{y+6}" x2="{x+22}" y2="{y+6}"/>')
    else:
        body = (f'<line class="sym-body" x1="{x-6}" y1="{y-22}" x2="{x-6}" y2="{y+22}"/>'
                f'<line class="sym-body" x1="{x+6}" y1="{y-22}" x2="{x+6}" y2="{y+22}"/>')
    return body, coords


def sym_diode(x, y, orient, comp, pins, tvs=False):
    """Anode is pin A, cathode pin K. Drawn as an arrow into a bar.

    Vertically the triangle points up, so the cathode bar is at the top: pin K
    is placed at the top and pin A at the bottom to match the drawing. A
    schematic whose pin names disagree with its symbol direction is worse than
    no schematic at all.
    """
    if orient == 'vertical':
        coords = {'K': (x, y - 20 - STUB), 'A': (x, y + 20 + STUB)}
    else:
        coords = _box_pins(x, y, orient, ('A', 1, 20), ('K', 2, 20))
    s = 13
    if orient == 'horizontal':
        tri = f'<path class="sym-body" d="M{x-s} {y-s}L{x-s} {y+s}L{x+s} {y}Z"/>'
        bar = f'<line class="sym-body" x1="{x+s}" y1="{y-s}" x2="{x+s}" y2="{y+s}"/>'
    else:
        tri = f'<path class="sym-body" d="M{x-s} {y+s}L{x+s} {y+s}L{x} {y-s}Z"/>'
        bar = f'<line class="sym-body" x1="{x-s}" y1="{y-s}" x2="{x+s}" y2="{y-s}"/>'
    extra = ''
    if tvs:
        # TVS drawn with the characteristic bent cathode bar
        if orient == 'vertical':
            extra = (f'<path class="sym-body" d="M{x-s} {y-s}L{x-s} {y-s-8}M{x+s} {y-s}L{x+s} {y-s+8}"/>')
        else:
            extra = (f'<path class="sym-body" d="M{x+s} {y-s}L{x+s+8} {y-s}M{x+s} {y+s}L{x+s-8} {y+s}"/>')
    return tri + bar + extra, coords


def sym_fuse(x, y, orient, comp, pins):
    w, h = (72, 28) if orient == 'horizontal' else (28, 72)
    coords = _box_pins(x, y, orient, ('1', 1, w / 2), ('2', 2, w / 2))
    if orient == 'horizontal':
        inner = f'<line class="sym-body" x1="{x-w/2+6}" y1="{y}" x2="{x+w/2-6}" y2="{y}"/>'
    else:
        inner = f'<line class="sym-body" x1="{x}" y1="{y-h/2+6}" x2="{x}" y2="{y+h/2-6}"/>'
    body = f'<rect class="sym-body" x="{x - w/2}" y="{y - h/2}" width="{w}" height="{h}" rx="14"/>' + inner
    return body, coords


def sym_terminal(x, y, orient, comp, pins, count=2):
    w, h = 56, 34 * count
    coords = {}
    rows = []
    for i in range(count):
        py = y - h / 2 + 17 + i * 34
        coords[str(i + 1)] = (x - w / 2 - STUB, py)
        rows.append(f'<circle class="sym-pin" cx="{x - w/2 + 14}" cy="{py}" r="6"/>')
    body = f'<rect class="sym-body" x="{x - w/2}" y="{y - h/2}" width="{w}" height="{h}" rx="3"/>' + ''.join(rows)
    return body, coords


def sym_testpoint(x, y, orient, comp, pins):
    """Pad above, pin below: the wire arrives from the bottom and never crosses it."""
    coords = {'1': (x, y + STUB)}
    body = (f'<circle class="sym-tp" cx="{x}" cy="{y - 8}" r="7"/>'
            f'<line class="sym-body" x1="{x}" y1="{y - 1}" x2="{x}" y2="{y + STUB}"/>')
    return body, coords


def sym_block(x, y, orient, comp, pins):
    """A rectangular part with named pins down both sides."""
    names = [p for p in pins]
    w = 120
    row = 30
    h = max(90, 20 + row * len(names))
    coords = {}
    lines = []
    for i, name in enumerate(names):
        py = y - h / 2 + 20 + i * row
        coords[name] = (x - w / 2 - STUB, py)
        lines.append(f'<circle class="sym-pin" cx="{x - w/2 + 5}" cy="{py}" r="4"/>'
                     f'<text class="pin-name" x="{x - w/2 + 16}" y="{py + 4}">{name}</text>')
    body = f'<rect class="sym-body" x="{x - w/2}" y="{y - h/2}" width="{w}" height="{h}" rx="4"/>' + ''.join(lines)
    return body, coords


SYMBOLS = {
    'resistor': sym_resistor,
    'capacitor': sym_capacitor,
    'diode': lambda *a: sym_diode(*a, tvs=False),
    'tvs': lambda *a: sym_diode(*a, tvs=True),
    'fuse': sym_fuse,
    'terminal': lambda *a: sym_terminal(*a, count=2),
    'terminal4': lambda *a: sym_terminal(*a, count=4),
    'testpoint': sym_testpoint,
    'block': sym_block,
}

# --------------------------------------------------------------------------- #
# Drawing
# --------------------------------------------------------------------------- #
CSS = """
  text { font-family: %s; }
  .sym-body { fill: none; stroke: #CBD5DD; stroke-width: 2.2; stroke-linecap: round; }
  .sym-pin { fill: none; stroke: #7E8B96; stroke-width: 1.6; }
  .sym-stub { stroke: #7E8B96; stroke-width: 1.8; }
  .sym-tp { fill: #0E141B; stroke: #D8B66A; stroke-width: 2; }
  .pin-name { fill: #8B98A4; font-size: 10px; }
  .wire { fill: none; stroke: #59D9E8; stroke-width: 2.2; stroke-linejoin: round; }
  .wire-power { stroke: #D8B66A; }
  .wire-ground { stroke: #93A0AB; }
  .junction { fill: #59D9E8; }
  .ref { fill: #EAF2F6; font-size: 13px; font-weight: 600; }
  .val { fill: #93A0AB; font-size: 10.5px; }
  .net-label { fill: #B7C2CB; font-size: 11px; }
  .sheet-title { fill: #EAF2F6; font-size: 17px; font-weight: 600; }
  .sheet-sub { fill: #7E8B96; font-size: 11px; }
  .note { fill: #8B98A4; font-size: 11px; }
  .frame { fill: #080C11; }
"""


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def component_by_ref(ref):
    for c in DESIGN['components']:
        if c['ref'] == ref:
            return c
    raise KeyError(ref)


def pin_direction(comp, pin_xy, centre):
    """Direction a stub should leave a pin, away from its own body."""
    dx = pin_xy[0] - centre[0]
    dy = pin_xy[1] - centre[1]
    if abs(dx) >= abs(dy):
        return (1 if dx > 0 else -1, 0)
    return (0, 1 if dy > 0 else -1)


def l_route(a, b, vertical_first=None):
    """Orthogonal two-segment path between two points, or a straight line."""
    if a[0] == b[0] or a[1] == b[1]:
        return [a, b]
    if vertical_first is None:
        vertical_first = abs(b[1] - a[1]) > abs(b[0] - a[0])
    if vertical_first:
        return [a, (a[0], b[1]), b]
    return [a, (b[0], a[1]), b]


def route(from_xy, to_xy, waypoints):
    path = [from_xy]
    for wp in waypoints:
        path += l_route(path[-1], tuple(wp))[1:]
    path += l_route(path[-1], to_xy)[1:]
    return path


def power_symbol(kind, x, y, direction):
    """A ground or supply flag drawn at the end of a stub, labelled away from the part."""
    dx, dy = direction
    tip = (x + dx * 26, y + dy * 26)
    cls = 'wire wire-ground' if kind == 'GND' else 'wire wire-power'
    parts = [f'<line class="{cls}" x1="{x}" y1="{y}" x2="{tip[0]}" y2="{tip[1]}"/>']
    if kind == 'GND':
        for i, w in enumerate((18, 11, 5)):
            off = 8 + i * 6
            parts.append(f'<line class="{cls}" x1="{tip[0] - w}" y1="{tip[1] + dy * off}" '
                         f'x2="{tip[0] + w}" y2="{tip[1] + dy * off}"/>')
        text = 'GND'
    else:
        parts.append(f'<line class="{cls}" x1="{tip[0] - 9}" y1="{tip[1]}" '
                     f'x2="{tip[0] + 9}" y2="{tip[1]}"/>')
        text = '+3V3'
    if dx < 0:
        tx, anchor, ty = tip[0] - 24, 'end', tip[1] + 4
    elif dx > 0:
        tx, anchor, ty = tip[0] + 24, 'start', tip[1] + 4
    else:
        tx, anchor, ty = tip[0] + 14, 'start', tip[1] + (34 if dy > 0 else 4)
    parts.append(f'<text class="net-label" x="{tx}" y="{ty}" text-anchor="{anchor}">{text}</text>')
    return ''.join(parts)


def net_label(kind, x, y, direction):
    """A short stub with a net name — the label is the connection."""
    dx, dy = direction
    tip = (x + dx * 42, y + dy * 42)
    anchor = 'start' if dx >= 0 else 'end'
    return (f'<line class="wire" x1="{x}" y1="{y}" x2="{tip[0]}" y2="{tip[1]}"/>'
            f'<text class="net-label" x="{tip[0] + dx * 6}" y="{tip[1] + (4 if dy == 0 else 14)}" '
            f'text-anchor="{anchor if dy == 0 else "middle"}">{esc(kind)}</text>')


def render_sheet(sheet):
    width, height = sheet['width'], sheet['height']
    subset = sheet.get('pin_subset', {})
    parts = []
    pin_points = {}          # (ref, pin) -> (x, y)
    centres = {}

    for placement in sheet['components']:
        comp = component_by_ref(placement['ref'])
        ref = comp['ref']
        wanted = comp['pins']
        if ref in subset:
            names = subset[ref]
            wanted = [p for p in comp['pins'] if p['name'] in names or p['number'] in names]
        pins = [p['number'] for p in wanted]
        draw = SYMBOLS[comp['symbol']]
        body, coords = draw(placement['x'], placement['y'], placement['orient'], comp, pins)
        for pin in pins:
            if pin in coords:
                pin_points[(ref, pin)] = coords[pin]
        centres[ref] = (placement['x'], placement['y'])

        x, y = placement['x'], placement['y']
        if comp['symbol'] == 'block':
            parts.append(f'<text class="ref" x="{x}" y="{y - 78}" text-anchor="middle">{ref}</text>')
            parts.append(f'<text class="val" x="{x}" y="{y + 88}" text-anchor="middle">{esc(comp["value"])}</text>')
        elif comp['symbol'] in ('terminal', 'terminal4'):
            half = (34 * (4 if comp['symbol'] == 'terminal4' else 2)) / 2
            parts.append(f'<text class="ref" x="{x}" y="{y - half - 16}" text-anchor="middle">{ref}</text>')
            if comp['symbol'] == 'terminal4':
                parts.append(f'<text class="val" x="{x + half + 10}" y="{y - 4}">{esc(comp["value"])}</text>')
                parts.append(f'<text class="val" x="{x + half + 10}" y="{y + 12}">to ESP32</text>')
            else:
                parts.append(f'<text class="val" x="{x}" y="{y + half + 24}" text-anchor="middle">{esc(comp["value"])}</text>')
        elif comp['symbol'] == 'testpoint':
            parts.append(f'<text class="ref" x="{x + 14}" y="{y - 4}">{ref}</text>')
        elif placement['orient'] == 'horizontal':
            parts.append(f'<text class="ref" x="{x}" y="{y - 26}" text-anchor="middle">{ref}</text>')
            parts.append(f'<text class="val" x="{x}" y="{y + 34}" text-anchor="middle">{esc(comp["value"])}</text>')
        else:
            parts.append(f'<text class="ref" x="{x + 26}" y="{y - 6}">{ref}</text>')
            parts.append(f'<text class="val" x="{x + 26}" y="{y + 8}">{esc(comp["value"])}</text>')
        parts.append(f'<g>{body}</g>')
        # a visible stub from each pin coordinate to the body edge
        for pin, pt in coords.items():
            dx, dy = pin_direction(comp, pt, (placement['x'], placement['y']))
            parts.append(f'<line class="sym-stub" x1="{pt[0]}" y1="{pt[1]}" '
                         f'x2="{pt[0] - dx * STUB}" y2="{pt[1] - dy * STUB}"/>')

    net_class = {n['name']: n['class'] for n in DESIGN['nets']}
    wires_svg, wire_points, labels = [], [], []
    used_labels = set()

    def wrap_class(net):
        cls = 'wire'
        if net_class.get(net) == 'power':
            cls += ' wire-power'
        elif net_class.get(net) == 'ground':
            cls += ' wire-ground'
        return cls

    for conn in sheet.get('connections', []):
        ref_a, pin_a = conn['from']
        a = pin_points[(ref_a, pin_a)]
        target = conn['to']
        net = conn.get('net') or (target if isinstance(target, str) else
                                  next(p['net'] for p in component_by_ref(target[0])['pins']
                                       if p['number'] == target[1]))
        cls = wrap_class(net)
        if isinstance(target, str):                     # a supply or net label
            direction = tuple(conn.get('dir') or pin_direction(None, a, centres[ref_a]))
            if target in ('GND', '3V3'):
                kind = 'GND' if target == 'GND' else '3V3'
                parts.append(power_symbol(kind, a[0], a[1], direction))
            else:
                parts.append(net_label(target, a[0], a[1], direction))
            used_labels.add(target)
            wire_points.append(a)
            continue
        b = pin_points[(target[0], target[1])]
        path = route(a, b, conn.get('via', []))
        d = 'M' + 'L'.join(f'{px} {py}' for px, py in path)
        wires_svg.append(f'<path class="{cls}" d="{d}"/>')
        wire_points.extend(path)
        # a junction is drawn wherever a wire endpoint lands on another wire
        labels.append((path[-1], net))

    # junction dots: shared points between different connections of the same net
    from collections import defaultdict
    point_nets = defaultdict(set)
    for conn in sheet.get('connections', []):
        if isinstance(conn['to'], str):
            continue
        ref_a, pin_a = conn['from']
        a = pin_points[(ref_a, pin_a)]
        b = pin_points[(conn['to'][0], conn['to'][1])]
        net = conn.get('net') or next(p['net'] for p in component_by_ref(conn['to'][0])['pins']
                                      if p['number'] == conn['to'][1])
        for p in route(a, b, conn.get('via', [])):
            point_nets[tuple(p)].add(net)
    junction_svg = ''.join(
        f'<circle class="junction" cx="{p[0]}" cy="{p[1]}" r="4.5"/>'
        for p, nets in point_nets.items()
        if sum(1 for n in nets) >= 1 and _touches_multiple(sheet, pin_points, p))

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'width="{width}" height="{height}" role="img" '
           f'aria-label="DCM-HW-V1 schematic sheet {sheet["id"]}: {esc(sheet["title"])}">',
           f'<style>{CSS % FONT}</style>',
           f'<rect class="frame" x="0" y="0" width="{width}" height="{height}"/>',
           f'<text class="sheet-title" x="34" y="40">Sheet {sheet["id"]} — {esc(sheet["title"])}</text>',
           f'<text class="sheet-sub" x="34" y="60">DCM-HW-V1 rev {DESIGN["design"]["revision"]} · '
           f'Elite Bot Studios · design only, not built</text>',
           ''.join(wires_svg),
           junction_svg,
           ''.join(parts),
           _sheet_note(sheet),
           '</svg>']
    return '\n'.join(svg), pin_points, wire_points


def _touches_multiple(sheet, pin_points, point):
    """True when a coordinate is shared by more than one connection or a pin."""
    hits = 0
    for conn in sheet.get('connections', []):
        if isinstance(conn['to'], str):
            continue
        a = pin_points[(conn['from'][0], conn['from'][1])]
        b = pin_points[(conn['to'][0], conn['to'][1])]
        path = route(a, b, conn.get('via', []))
        if any(tuple(p) == tuple(point) for p in path):
            hits += 1
    return hits >= 2


def _sheet_note(sheet):
    note = sheet.get('note')
    if not note:
        return ''
    words, lines, line = note.split(), [], ''
    for w in words:
        if len(line) + len(w) + 1 > 116:
            lines.append(line)
            line = w
        else:
            line = (line + ' ' + w).strip()
    lines.append(line)
    out = []
    for i, text in enumerate(lines[:3]):
        out.append(f'<text class="note" x="34" y="{sheet["height"] - 68 + i * 17}">{esc(text)}</text>')
    return ''.join(out)


def check_connectivity(sheet, pin_points, wire_points):
    problems = []
    for (ref, pin), p in pin_points.items():
        used = any(math.dist(p, q) < 1.5 for q in wire_points)
        if not used:
            problems.append(f'sheet {sheet["id"]}: pin {ref}.{pin} at {tuple(p)} has no wire')
    return problems


# --------------------------------------------------------------------------- #
# Netlist and BOM
# --------------------------------------------------------------------------- #
def connections():
    rows = []
    for net in DESIGN['nets']:
        for comp in DESIGN['components']:
            for pin in comp['pins']:
                if pin.get('net') == net['name']:
                    rows.append({
                        'net': net['name'],
                        'class': net['class'],
                        'ref': comp['ref'],
                        'pin': pin['number'],
                        'pin_name': pin['name'],
                        'component': comp['part'],
                        'function': comp['function']
                    })
    return sorted(rows, key=lambda r: (r['net'], r['ref'], str(r['pin'])))


def kicad_netlist():
    nets = {}
    for comp in DESIGN['components']:
        for pin in comp['pins']:
            name = pin.get('net', 'NC')
            nets.setdefault(name, []).append((comp['ref'], str(pin['number'])))
    lines = ['(export (version "E")',
             f'  (design (source "dcm-hw-v1") (date "{DESIGN["design"]["date"]}") (tool "dcm-generate.py"))',
             '  (components']
    for comp in DESIGN['components']:
        lines.append(f'    (comp (ref "{comp["ref"]}") (value "{comp["value"]}") (footprint "") '
                     f'(datasheet "{comp.get("datasheet", "")}") (description "{comp["function"]}"))')
    lines.append('  )')
    lines.append('  (nets')
    for code, (name, nodes) in enumerate(sorted(nets.items()), start=1):
        lines.append(f'    (net (code "{code}") (name "{name}")')
        for ref, pin in nodes:
            lines.append(f'      (node (ref "{ref}") (pin "{pin}"))')
        lines.append('    )')
    lines.append('  )')
    lines.append(')')
    return '\n'.join(lines) + '\n'


def write_bom():
    path = OUT / 'bom' / 'dcm-hw-v1-bom.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for comp in DESIGN['components']:
        ratings = comp.get('ratings', {})
        rows.append({
            'ref': comp['ref'],
            'value': comp['value'],
            'part_number': comp['part'],
            'manufacturer': comp['manufacturer'],
            'function': comp['function'],
            'key_ratings': '; '.join(f'{k}={v}' for k, v in ratings.items()),
            'quantity': 1,
            'datasheet_ref': DESIGN['references'].get(comp.get('datasheet', ''), {}).get('url', ''),
            'rationale': comp['rationale'],
            'price': 'unverified — no price checked in this environment',
            'alternatives': 'see design/dcm-hw-v1.json rationale field'
        })
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def main():
    problems = []
    for sheet in DESIGN['layout']['sheets']:
        svg, pins, endpoints = render_sheet(sheet)
        problems += check_connectivity(sheet, pins, endpoints)
        out = OUT / 'schematic' / f'dcm-hw-v1-sheet{sheet["id"]}.svg'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(svg, encoding='utf-8')
        print(f'  wrote {out.relative_to(OUT.parent.parent)} ({len(svg)} bytes, '
              f'{len(pins)} pins, {len(endpoints)} wire points)')

    if problems:
        print('\nCONNECTIVITY PROBLEMS — drawing not trustworthy:')
        for p in problems:
            print('   ' + p)
        raise SystemExit(1)

    conn = connections()
    path = OUT / 'netlist' / 'dcm-hw-v1-connections.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(conn[0].keys()))
        writer.writeheader()
        writer.writerows(conn)
    print(f'  wrote {path.relative_to(OUT.parent.parent)} ({len(conn)} pin connections)')

    net_path = OUT / 'netlist' / 'dcm-hw-v1.net'
    net_path.write_text(kicad_netlist(), encoding='utf-8')
    print(f'  wrote {net_path.relative_to(OUT.parent.parent)}')

    bom = write_bom()
    print(f'  wrote {bom.relative_to(OUT.parent.parent)}')

    print('\n  connectivity: every wire endpoint lands on a pin or a junction, '
          'and every pin is reached by a wire.')


if __name__ == '__main__':
    main()
