#!/usr/bin/env python3
"""Compare the KiCad netlist with the connectivity declared in the design file.

The design is described twice: once as JSON that generates the SVG drawings and
the connection table, and once as a native KiCad schematic generated from that
same JSON. Two descriptions of one circuit can drift apart, so this script reads
the netlist KiCad actually exported and compares it, pin by pin, with the JSON.

    python3 energy-monitor/hardware/design/compare_netlists.py

Exits non-zero on any difference. Anything it reports is a real disagreement
between the schematic and the design intent.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HW = HERE.parent
KICAD_NET = HW / 'kicad' / 'netlist-kicad.net'

DESIGN = json.loads((HERE / 'dcm-hw-v1.json').read_text(encoding='utf-8'))

# Power symbols and flags are schematic furniture, not components of the design.
SKIP_REFS = {'#FLG', '#PWR'}


def design_connections():
    """(ref, kicad pin) -> net, from the design file.

    Where a component's drawn pin name differs from the numbering KiCad uses for
    that part (a diode's A and K are pins 2 and 1), the design file records the
    KiCad number in a `kicad` field. That mapping is part of the design, not a
    convenience in this script.
    """
    out = {}
    for comp in DESIGN['components']:
        for pin in comp['pins']:
            net = pin.get('net')
            if net and net != 'NC':
                key = str(pin.get('kicad', pin['number']))
                out[(comp['ref'], key)] = net
    return out


def kicad_connections():
    """(ref, pin) -> net, from the netlist KiCad exported."""
    if not KICAD_NET.exists():
        print('  no KiCad netlist at %s — run build_kicad.py and kicad-cli first' % KICAD_NET)
        sys.exit(2)
    text = KICAD_NET.read_text(encoding='utf-8')
    out = {}
    current = None
    for line in text.splitlines():
        m = re.match(r'\s*\(net \(code "\d+"\) \(name "([^"]+)"\)', line)
        if m:
            current = m.group(1)
            continue
        m = re.match(r'\s*\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', line)
        if m and current:
            ref, pin = m.group(1), m.group(2)
            if any(ref.startswith(s) for s in SKIP_REFS):
                continue
            out[(ref, pin)] = current
    return out


def main():
    design = design_connections()
    kicad = kicad_connections()

    problems = []
    for key in sorted(set(design) | set(kicad)):
        d, k = design.get(key), kicad.get(key)
        if d != k:
            problems.append('  %-6s pin %-3s  design: %-8s  kicad: %-8s'
                            % (key[0], key[1], d or '—', k or '—'))

    print('\n  KiCad netlist vs design file — DCM-HW-V1 rev %s\n' % DESIGN['design']['revision'])
    print('  pins in the design file : %d' % len(design))
    print('  pins in the KiCad netlist: %d' % len(kicad))

    if problems:
        print('\n  DIFFERENCES:')
        print('\n'.join(problems))
        print('\n  FAIL: the schematic and the design file disagree.\n')
        return 1

    nets = sorted(set(design.values()))
    print('  nets compared          : %d (%s)' % (len(nets), ', '.join(nets)))
    print('\n  PASS: every pin is on the same net in both descriptions of the circuit.\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
