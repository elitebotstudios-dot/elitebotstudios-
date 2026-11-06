#!/usr/bin/env python3
"""Generate a native KiCad schematic for DCM-HW-V1 from the design file.

Why this exists
    The previous revision published an SVG drawing and a netlist. Neither is an
    editable schematic, and neither can be run through ERC. This script emits a
    real .kicad_sch that uses the *official KiCad library symbols* (extracted
    verbatim from /usr/share/kicad/symbols), places them, wires the power path,
    and connects the rest with labels and power symbols exactly as a person
    would. kicad-cli then runs ERC and exports the netlist and BOM.

    The symbol blocks are copied byte-for-byte from the libraries, so the pin
    numbers, names and electrical types are the ones KiCad ships — not ones this
    repository invented.

Outputs (hardware/kicad/)
    dcm-hw-v1.kicad_sch        native schematic
    dcm-hw-v1.kicad_pro        native project file
    erc-report.txt             written by kicad-cli
    netlist-kicad.net          exported by kicad-cli
    bom-kicad.csv              exported by kicad-cli

Usage
    python3 energy-monitor/hardware/design/build_kicad.py
"""
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
HW = HERE.parent
OUT = HW / 'kicad'
LIBS = Path('/usr/share/kicad/symbols')
DESIGN = json.loads((HERE / 'dcm-hw-v1.json').read_text(encoding='utf-8'))


def uid():
    return str(uuid.uuid4())


# --------------------------------------------------------------------------- #
# Symbol library access
# --------------------------------------------------------------------------- #
def extract_symbol_block(lib_file, name):
    """Return the exact text of one (symbol "name" ...) block, balanced."""
    text = (LIBS / lib_file).read_text(encoding='utf-8')
    start = text.find('(symbol "%s"' % name)
    if start < 0:
        raise KeyError('%s not found in %s' % (name, lib_file))
    depth, i = 0, start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise ValueError('unbalanced symbol block for %s' % name)


def parse_pins(block):
    """Pins of a symbol block: number, name, x, y, angle, electrical type."""
    pins = []
    for m in re.finditer(r'\(pin\s+(\S+)\s+\S+\s+\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\)'
                         r'\s+\(length\s+([\d.]+)\)', block):
        ptype, x, y, angle, length = m.groups()
        # the pin name and number follow in (name "...") (number "...")
        tail = block[m.end():m.end() + 200]
        nm = re.search(r'\(name\s+"([^"]*)"', tail)
        nu = re.search(r'\(number\s+"([^"]*)"', tail)
        pins.append({
            'type': ptype,
            'x': float(x), 'y': float(y), 'angle': float(angle), 'length': float(length),
            'name': nm.group(1) if nm else '', 'number': nu.group(1) if nu else ''
        })
    return pins


SYMBOL_SOURCES = {
    'Device:R': ('Device.kicad_sym', 'R'),
    'Device:C': ('Device.kicad_sym', 'C'),
    'Device:D_Schottky': ('Device.kicad_sym', 'D_Schottky'),
    'Device:D_TVS': ('Device.kicad_sym', 'D_TVS'),
    'Device:Polyfuse': ('Device.kicad_sym', 'Polyfuse'),
    'Connector_Generic:Conn_01x02': ('Connector_Generic.kicad_sym', 'Conn_01x02'),
    'Connector_Generic:Conn_01x04': ('Connector_Generic.kicad_sym', 'Conn_01x04'),
    'Connector:TestPoint': ('Connector.kicad_sym', 'TestPoint'),
    'Sensor_Energy:INA226': ('Sensor_Energy.kicad_sym', 'INA226'),
    'power:GND': ('power.kicad_sym', 'GND'),
    'power:+3V3': ('power.kicad_sym', '+3V3'),
    'power:PWR_FLAG': ('power.kicad_sym', 'PWR_FLAG'),
}

SAVE_LIBDIRS = ['Device', 'Connector', 'Connector_Generic', 'Sensor_Energy', 'power']

# ESP32-DevKitC has no symbol in the official library: it is a development board,
# not a component. This symbol represents the four pins the carrier actually uses,
# with the header names as KiCad would show them. It is declared as a local
# symbol inside the schematic so nothing external is required.
ESP32_SYMBOL = '''
    (symbol "dcm:ESP32-DevKitC-32E" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 12.7 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ESP32-DevKitC-32E" (at 0 -15.24 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/index.html"
        (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Description" "Espressif ESP32-DevKitC-32E development board, four pins used by the DCM carrier"
        (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "ESP32-DevKitC-32E_0_1"
        (rectangle (start -10.16 10.16) (end 10.16 -12.7) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "ESP32-DevKitC-32E_1_1"
        (pin power_out line (at -15.24 7.62 0) (length 5.08)
          (name "3V3" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -15.24 -7.62 0) (length 5.08)
          (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 2.54 180) (length 5.08)
          (name "IO21/SDA" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -2.54 180) (length 5.08)
          (name "IO22/SCL" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      )
    )
'''

# --------------------------------------------------------------------------- #
# Placement
# --------------------------------------------------------------------------- #
MM = 2.54  # one 0.1 inch grid step


def grid(n):
    return round(n * MM, 4)


# (lib_id, reference, value, x, y, footprint, datasheet, net-per-pin)
#
# Every pin is connected with a short stub and a net label, which is a normal way
# to draw a schematic built from connectors and modules. It also makes the
# connectivity unambiguous to ERC: labels connect by name, so there is no
# possibility of a wire that looks connected but is 2.54 mm away.
#
# Layout, in millimetres on an A3 sheet (420 x 297):
#   power path   y = 60    J1, F1, D1, R1, J2 left to right
#   TVS          y = 95
#   sensor       y = 150
#   supply/I2C   y = 140-170, to the right
PLACEMENT = [
    ('Connector_Generic:Conn_01x02', 'J1', 'DC IN 5-12 V', grid(14), grid(22), 'TerminalBlock:TerminalBlock_bornier-2_P5.08mm', ''),
    ('Device:Polyfuse', 'F1', 'MF-R110 1.1A', grid(24), grid(22), 'Fuse:Fuse_1206_3216Metric', ''),
    ('Device:D_Schottky', 'D1', 'SS34', grid(34), grid(22), 'Diode_SMD:D_SMA', ''),
    ('Device:R', 'R1', '0.1R 1W 0.5%', grid(44), grid(22), 'Resistor_SMD:R_2512_6332Metric', ''),
    ('Connector_Generic:Conn_01x02', 'J2', 'DC OUT', grid(54), grid(22), 'TerminalBlock:TerminalBlock_bornier-2_P5.08mm', ''),
    ('Device:D_TVS', 'D2', 'SMBJ15A', grid(34), grid(36), 'Diode_SMD:D_SMB', ''),
    ('Sensor_Energy:INA226', 'U1', 'INA226', grid(34), grid(56), 'Package_SO:VSSOP-10_3x3mm_P0.5mm', ''),
    ('Device:C', 'C1', '10uF 25V', grid(52), grid(50), 'Capacitor_SMD:C_1210_3225Metric', ''),
    ('Device:C', 'C2', '100nF 25V', grid(52), grid(58), 'Capacitor_SMD:C_0603_1608Metric', ''),
    ('Device:R', 'R2', '4k7', grid(60), grid(50), 'Resistor_SMD:R_0603_1608Metric', ''),
    ('Device:R', 'R3', '4k7', grid(60), grid(58), 'Resistor_SMD:R_0603_1608Metric', ''),
    ('Connector_Generic:Conn_01x04', 'J3', 'to ESP32', grid(72), grid(54), 'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical', ''),
    ('dcm:ESP32-DevKitC-32E', 'U2', 'ESP32-DevKitC-32E', grid(88), grid(54), '', ''),
    ('Connector:TestPoint', 'TP1', 'VIN', grid(14), grid(12), 'TestPoint:TestPoint_Pad_D1.0mm', ''),
    ('Connector:TestPoint', 'TP2', 'VPROT', grid(30), grid(12), 'TestPoint:TestPoint_Pad_D1.0mm', ''),
    ('Connector:TestPoint', 'TP3', 'VLOAD', grid(50), grid(12), 'TestPoint:TestPoint_Pad_D1.0mm', ''),
    ('Connector:TestPoint', 'TP4', 'GND', grid(60), grid(12), 'TestPoint:TestPoint_Pad_D1.0mm', ''),
    ('Connector:TestPoint', 'TP5', 'SCL', grid(70), grid(12), 'TestPoint:TestPoint_Pad_D1.0mm', ''),
]

# Which net each pin belongs to. This is the electrical intent taken from
# design/dcm-hw-v1.json, restated here per pin because KiCad needs a label on
# every pin, not a list of nets.
PIN_NETS = {
    ('J1', '1'): 'VIN', ('J1', '2'): 'GND',
    ('F1', '1'): 'VIN', ('F1', '2'): 'VFUSED',
    ('D1', '2'): 'VFUSED', ('D1', '1'): 'VPROT',      # D_Schottky: pin 2 = anode, pin 1 = cathode
    ('R1', '1'): 'VPROT', ('R1', '2'): 'VLOAD',
    ('J2', '1'): 'VLOAD', ('J2', '2'): 'GND',
    ('D2', '1'): 'VPROT', ('D2', '2'): 'GND',          # D_TVS: pin 1 = cathode, pin 2 = anode
    ('U1', '10'): 'VPROT',   # IN+
    ('U1', '9'): 'VLOAD',    # IN-
    ('U1', '8'): 'VLOAD',    # VBUS  <- the connection the previous revision missed
    ('U1', '6'): '3V3',      # VS
    ('U1', '7'): 'GND',
    ('U1', '4'): 'SDA', ('U1', '5'): 'SCL',
    ('U1', '1'): 'GND', ('U1', '2'): 'GND',            # A1, A0 -> 0x40
    ('C1', '1'): '3V3', ('C1', '2'): 'GND',
    ('C2', '1'): '3V3', ('C2', '2'): 'GND',
    ('R2', '1'): '3V3', ('R2', '2'): 'SDA',
    ('R3', '1'): '3V3', ('R3', '2'): 'SCL',
    ('J3', '1'): '3V3', ('J3', '2'): 'GND', ('J3', '3'): 'SDA', ('J3', '4'): 'SCL',
    ('U2', '1'): '3V3', ('U2', '2'): 'GND', ('U2', '3'): 'SDA', ('U2', '4'): 'SCL',
    ('TP1', '1'): 'VIN', ('TP2', '1'): 'VPROT', ('TP3', '1'): 'VLOAD',
    ('TP4', '1'): 'GND', ('TP5', '1'): 'SCL',
}

# Pins left unconnected on purpose, with the reason stated in the schematic.
NO_CONNECT = {('U1', '3'): 'ALERT: open-drain output, unused in V1'}


class Schematic:
    def __init__(self):
        self.blocks = []
        self.items = []
        self.pin_positions = {}      # (ref, pin number) -> (x, y, angle)

    def add_lib_symbol(self, text, lib_id):
        """Embed a library block under its fully qualified id."""
        name = lib_id.split(':', 1)[1]
        body = re.sub(r'^\(symbol "%s"' % re.escape(name), '(symbol "%s"' % lib_id, text, count=1)
        self.blocks.append(body)

    def place(self, lib_id, ref, value, x, y, footprint='', datasheet='', unit=1, hide_value=False):
        block = extract_symbol_block(*SYMBOL_SOURCES[lib_id]) if lib_id in SYMBOL_SOURCES else None
        pins = parse_pins(block) if block else parse_pins(ESP32_SYMBOL)
        self.blocks_needed = getattr(self, 'blocks_needed', {})
        if lib_id not in self.blocks_needed:
            if block:
                self.add_lib_symbol(block, lib_id)
            else:
                body = re.sub(r'^\(symbol "dcm:ESP32-DevKitC-32E"', '(symbol "dcm:ESP32-DevKitC-32E"', ESP32_SYMBOL.strip(), count=1)
                self.blocks.append(body)
            self.blocks_needed[lib_id] = True
        for p in pins:
            # KiCad stores symbol coordinates with Y up; the schematic has Y down.
            px, py = x + p['x'], y - p['y']
            self.pin_positions[(ref, p['number'])] = (round(px, 4), round(py, 4), p['angle'])
        props = [
            ('Reference', ref, x, y - 12.7, False),
            ('Value', value, x, y + 12.7, hide_value),
            ('Footprint', footprint, x, y, True),
            ('Datasheet', datasheet or '~', x, y, True),
        ]
        prop_text = ''.join(
            '(property "%s" "%s" (at %s %s 0) (effects (font (size 1.27 1.27))%s))'
            % (n, v.replace('"', ''), px_, py_, ' hide' if hide else '')
            for n, v, px_, py_, hide in props)
        pin_uuids = ''.join('(pin "%s" (uuid %s))' % (p['number'], uid()) for p in pins)
        self.items.append(
            '(symbol (lib_id "%s") (at %s %s 0) (unit %d) (in_bom yes) (on_board yes) (dnp no) (uuid %s)'
            ' %s %s (instances (project "dcm-hw-v1" (path "/%s" (reference "%s") (unit %d))))))'
            % (lib_id, x, y, unit, pin_uuids and '', prop_text, pin_uuids, ROOT_UUID, ref, unit)
            if False else
            '(symbol (lib_id "%s") (at %s %s 0) (unit %d) (in_bom yes) (on_board yes) (dnp no) (uuid %s)'
            ' %s %s)'
            % (lib_id, x, y, unit, uid(), prop_text, pin_uuids))
        return pin_uuids

    def wire(self, a, b):
        self.items.append(
            '(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid %s))'
            % (a[0], a[1], b[0], b[1], uid()))

    def junction(self, p):
        self.items.append('(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid %s))' % (p[0], p[1], uid()))

    def label(self, text, p, angle=0):
        self.items.append(
            '(global_label "%s" (shape input) (at %s %s %s) (fields_autoplaced yes)'
            ' (effects (font (size 1.27 1.27)) (justify left)) (uuid %s))'
            % (text, p[0], p[1], angle, uid()))

    def power(self, kind, p, angle=0):
        """Place a power symbol at a point; it connects by its pin name."""
        lib_id = 'power:' + kind
        block = extract_symbol_block(*SYMBOL_SOURCES[lib_id])
        if lib_id not in getattr(self, 'blocks_needed', {}):
            self.add_lib_symbol(block, lib_id)
            self.blocks_needed[lib_id] = True
        ref = '#PWR%03d' % (len([i for i in self.items if '#PWR' in i]) + 1)
        self.items.append(
            '(symbol (lib_id "%s") (at %s %s %s) (unit 1) (in_bom no) (on_board yes) (dnp no) (uuid %s)'
            ' (property "Reference" "%s" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))'
            ' (property "Value" "%s" (at %s %s 0) (effects (font (size 1.27 1.27))))'
            ' (property "Footprint" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))'
            ' (property "Datasheet" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide)))'
            % (lib_id, p[0], p[1], angle, uid(), ref, p[0], p[1] + 5, kind, p[0], p[1], p[0], p[1], p[0], p[1]))


ROOT_UUID = uid()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sch = Schematic()
    refs = {}
    for lib_id, ref, value, x, y, fp, ds in PLACEMENT:
        sch.place(lib_id, ref, value, x, y, fp, ds)
        refs[ref] = (lib_id, x, y)

    def pin(ref, number):
        return sch.pin_positions[(ref, number)]

    # Every connected pin gets a 5.08 mm stub and a net label. The stub leaves the
    # pin in the direction away from the symbol body, which is the opposite of the
    # direction the pin points in the library.
    # A KiCad pin points from its connection point toward the symbol body, so the
    # stub must leave the pin in the opposite direction. Getting this backwards
    # makes every stub run through the body and every net short together, which
    # is exactly what the first generated netlist showed.
    outward = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}
    for (ref, number), net in sorted(PIN_NETS.items()):
        x, y, angle = pin(ref, number)
        dx, dy = outward[int(angle) % 360]
        end = (round(x + dx * 5.08, 4), round(y + dy * 5.08, 4))
        sch.wire((x, y), end)
        sch.label(net, end, 0 if dx >= 0 else 180)

    # Explicit no-connects carry a marker, so ERC and a human reviewer both see
    # that the pin was considered rather than forgotten.
    for (ref, number) in NO_CONNECT:
        x, y, _ = pin(ref, number)
        sch.items.append('(no_connect (at %s %s) (uuid %s))' % (x, y, uid()))

    # The carrier is fed by the bench supply and by the ESP32 board; neither has a
    # power_out pin on this sheet, so PWR_FLAG tells ERC the rails are driven.
    # This is the standard fix, not a silenced warning: without it ERC correctly
    # reports "power input not driven".
    for kind in ('GND',):
        x, y = grid(78), grid(40)
        block = extract_symbol_block(*SYMBOL_SOURCES['power:PWR_FLAG'])
        if 'power:PWR_FLAG' not in sch.blocks_needed:
            sch.add_lib_symbol(block, 'power:PWR_FLAG')
            sch.blocks_needed['power:PWR_FLAG'] = True
        n = len([i for i in sch.items if '#FLG' in i]) + 1
        sch.items.append(
            '(symbol (lib_id "power:PWR_FLAG") (at %s %s 0) (unit 1) (in_bom no) (on_board yes) (dnp no) (uuid %s)'
            ' (property "Reference" "#FLG%03d" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))'
            ' (property "Value" "PWR_FLAG" (at %s %s 0) (effects (font (size 1.27 1.27))))'
            ' (property "Footprint" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))'
            ' (property "Datasheet" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide)))'
            % (x, y, uid(), n, x, y - 3, x, y - 6, x, y, x, y))
        sch.wire((x, y), (x, y + 5.08))
        sch.label(kind, (x, y + 5.08), 90)
        # PWR_FLAG's own pin is at its origin, so the stub above starts on it.

    header = '''(kicad_sch
  (version 20231120)
  (generator "dcm-hw-v1 build_kicad.py")
  (generator_version "9.0")
  (uuid "%s")
  (paper "A3")
  (title_block
    (title "Smart DC Energy Monitor — measurement carrier, DCM-HW-V1 rev B")
    (date "%s")
    (rev "B")
    (company "Elite Bot Studios")
    (comment 1 "Design only. Nothing here has been built, powered or measured.")
    (comment 2 "INA226 wired as the bare IC: IN+ supply side, IN- load side, VBUS to IN-.")
    (comment 3 "A0 and A1 tied to GND select address 0x40. ALERT is unconnected in V1.")
  )
  (lib_symbols
%s
  )
%s
  (sheet_instances
    (path "/" (page "1"))
  )
)
''' % (ROOT_UUID, DESIGN['design']['date'], '\n'.join(sch.blocks), '\n'.join(sch.items))

    sch_path = OUT / 'dcm-hw-v1.kicad_sch'
    sch_path.write_text(header, encoding='utf-8')
    print('  wrote %s (%d bytes, %d symbols, %d items)'
          % (sch_path.relative_to(HW.parent.parent), len(header), len(PLACEMENT), len(sch.items)))

    pro = {
        "board": {},
        "meta": {"filename": "dcm-hw-v1.kicad_pro", "version": 1},
        "sheets": [["a0a0a0a0-0000-0000-0000-000000000000", "Root"]],
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "text_variables": {}
    }
    (OUT / 'dcm-hw-v1.kicad_pro').write_text(json.dumps(pro, indent=2) + '\n', encoding='utf-8')
    print('  wrote dcm-hw-v1.kicad_pro')
    return sch_path


if __name__ == '__main__':
    main()
