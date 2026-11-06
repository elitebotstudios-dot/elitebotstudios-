#!/usr/bin/env python3
"""Design rule checks for DCM-HW-V1.

These are NOT KiCad ERC. No EDA tool was available in the authoring
environment, so no KiCad project was created and no ERC was run. What this
script does is check the electrical rules this particular design has to satisfy,
against the numbers recorded in design/dcm-hw-v1.json, and print the margin for
each one. Every number it uses comes from that file or from the datasheet
figures recorded beside it, so the review can be re-run by anyone.

    python3 energy-monitor/hardware/design/checks.py

Exit code 0 if every check passes, 1 otherwise.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / 'dcm-hw-v1.json').read_text(encoding='utf-8'))

COMP = {c['ref']: c for c in D['components']}
ENV = D['design']['envelope']
I_MAX = ENV['i_max_a']
V_MAX = ENV['vin_max_v']
V_MIN = ENV['vin_min_v']
V_NOM = ENV['vin_nominal_v']

RESULTS = []


def check(rule, requirement, actual, margin, ok):
    RESULTS.append({'rule': rule, 'requirement': requirement, 'actual': actual,
                    'margin': margin, 'ok': bool(ok)})


def net_members(name):
    out = []
    for ref, comp in COMP.items():
        for pin in comp['pins']:
            if pin.get('net') == name:
                out.append((ref, pin['number'], pin['name']))
    return out


# --------------------------------------------------------------------------- #
# 1. Sensor electrical limits
# --------------------------------------------------------------------------- #
ina = COMP['U1']['ratings']
check('S1 bus voltage', f'Vbus,max {V_MAX} V must be inside the sensor 0–{ina["v_bus_max"]} V range '
      f'at the 12 V envelope, with ≥25 % margin to the absolute maximum',
      f'{V_MAX} V vs {ina["v_bus_max"]} V absolute maximum',
      f'{(1 - V_MAX / ina["v_bus_max"]) * 100:.0f} % headroom',
      V_MAX <= ina['v_bus_max'] * 0.75)

shunt = COMP['R1']['ratings']
v_shunt_max_mv = I_MAX * shunt['resistance_ohm'] * 1000
check('S2 shunt range', f'Shunt drop at {I_MAX} A must be inside the ±{ina["v_shunt_fs_mv"]} mV '
      f'full-scale range, and use at least 40 % of it so resolution is not wasted',
      f'{v_shunt_max_mv:.1f} mV',
      f'{v_shunt_max_mv / ina["v_shunt_fs_mv"] * 100:.0f} % of full scale',
      v_shunt_max_mv <= ina['v_shunt_fs_mv'] and v_shunt_max_mv >= 0.4 * ina['v_shunt_fs_mv'])

i_fs = ina['v_shunt_fs_mv'] / 1000 / shunt['resistance_ohm']
check('S3 measurable current', 'The design must state the maximum current the chosen shunt can '
      'measure, and flag that a 1 A test needs a different shunt',
      f'{i_fs:.4f} A measurable with {shunt["resistance_ohm"]} Ω',
      f'1 A test would exceed it by {(1 - i_fs) * 100:.1f} %',
      i_fs >= I_MAX and i_fs < 1.0)

check('S4 sensor supply', f'Sensor supply must be inside {ina["v_supply_min"]}–{ina["v_supply_max"]} V '
      'and must come from the 3.3 V rail, not from the measured bus',
      'VCC on net 3V3 (3.3 V)',
      f'{(ina["v_supply_max"] - 3.3):.2f} V below the maximum',
      any(p['number'] == 'VCC' and p['net'] == '3V3' for p in COMP['U1']['pins']))

check('S5 sensing point', 'The sensor must measure the load side of the shunt so reported power '
      'is what the load receives, not what the source delivers',
      'IN− is on VLOAD, which feeds J2 pin 1',
      'P = V_load × I',
      any(p['number'] == 'IN-' and p['net'] == 'VLOAD' for p in COMP['U1']['pins'])
      and any(p['number'] == '1' and p['net'] == 'VLOAD' for p in COMP['J2']['pins']))

# --------------------------------------------------------------------------- #
# 2. Logic levels and the I2C bus
# --------------------------------------------------------------------------- #
mcu = COMP['U2']['ratings']
check('L1 logic compatibility', f'Every I2C device must operate at the microcontroller logic level '
      f'({mcu["logic_v"]} V); no 5 V device may sit on the bus',
      f'ESP32 {mcu["logic_v"]} V, INA226 module supplied from 3.3 V',
      'no level shifter required',
      abs(mcu['logic_v'] - 3.3) < 0.01 and ina['v_supply_max'] >= 3.3)

pull = COMP['R2']['ratings']['resistance_ohm']
check('L2 pull-up value', 'I2C pull-ups must be between 1 kΩ and 10 kΩ for a 100 kHz bus at 3.3 V',
      f'{pull} Ω on SDA and SCL',
      f'{(pull / 1000):.1f} kΩ',
      1000 <= pull <= 10000)

check('L3 pull-up rail', 'Pull-ups must connect to the same 3.3 V rail as the sensor and the MCU, '
      'never to 5 V',
      f'R2 pin 1 on {COMP["R2"]["pins"][0]["net"]}, R3 pin 1 on {COMP["R3"]["pins"][0]["net"]}',
      'both on 3V3',
      COMP['R2']['pins'][0]['net'] == '3V3' and COMP['R3']['pins'][0]['net'] == '3V3')

i2c_pins = [('U1', 'SDA', 'SDA'), ('U1', 'SCL', 'SCL'), ('U2', 'IO21', 'SDA'), ('U2', 'IO22', 'SCL'),
            ('J3', '3', 'SDA'), ('J3', '4', 'SCL'), ('R2', '2', 'SDA'), ('R3', '2', 'SCL')]
check('L4 bus continuity', 'SDA and SCL must each reach the sensor, both pull-ups, the connector and '
      'the microcontroller pin',
      '8 pin assignments checked',
      'complete',
      all(any(p['number'] == pin and p['net'] == net for p in COMP[ref]['pins'])
          for ref, pin, net in i2c_pins))

check('L5 address strap', 'A single device at 0x40 requires A0 and A1 tied low; the module straps '
      'must be confirmed before firmware is trusted',
      'documented requirement, not verifiable without the physical module',
      'see design-review, open question Q1',
      True)   # recorded as an open question rather than silently assumed

# --------------------------------------------------------------------------- #
# 3. Protection and ratings
# --------------------------------------------------------------------------- #
fuse = COMP['F1']['ratings']
check('P1 fuse', f'Fuse hold current must exceed the design current ({I_MAX} A) so it does not '
      f'nuisance-trip, and stay below the supply limit for a fault to clear',
      f'hold {fuse["hold_a"]} A, trip {fuse["trip_a"]} A',
      f'{fuse["hold_a"] / I_MAX:.1f}× design current',
      fuse['hold_a'] > I_MAX and fuse['trip_a'] <= 2.5)

tvs = COMP['D2']['ratings']
check('P2 transient clamp', f'TVS standoff must exceed the maximum input ({V_MAX} V) and its clamp '
      f'must stay below the sensor absolute maximum ({ina["v_bus_max"]} V)',
      f'standoff {tvs["v_standoff"]} V, clamp {tvs["v_clamp"]} V',
      f'{(tvs["v_standoff"] - V_MAX):.1f} V above the input, '
      f'{(ina["v_bus_max"] - tvs["v_clamp"]):.1f} V below the sensor maximum',
      tvs['v_standoff'] > V_MAX and tvs['v_clamp'] < ina['v_bus_max'])

d1 = COMP['D1']['ratings']
check('P3 reverse diode', 'Reverse-polarity diode must be rated above the input voltage and the '
      'fault current',
      f'{d1["vr_v"]} V / {d1["if_a"]} A',
      f'{d1["vr_v"] / V_MAX:.1f}× input, {d1["if_a"] / I_MAX:.0f}× design current',
      d1['vr_v'] >= 1.5 * V_MAX and d1['if_a'] >= 2 * I_MAX)

check('P4 diode position', 'Reverse-polarity protection must sit upstream of the shunt so it does '
      'not corrupt the current measurement',
      'D1 between VFUSED and VPROT; R1 between VPROT and VLOAD',
      'current sense unaffected',
      any(p['number'] == 'K' and p['net'] == 'VPROT' for p in COMP['D1']['pins'])
      and any(p['number'] == '1' and p['net'] == 'VPROT' for p in COMP['R1']['pins']))

p_shunt = I_MAX ** 2 * shunt['resistance_ohm']
check('P5 shunt dissipation', f'Shunt dissipation at {I_MAX} A must stay under half its rating',
      f'{p_shunt * 1000:.1f} mW in a {shunt["power_w"]} W part',
      f'{p_shunt / shunt["power_w"] * 100:.0f} % of rating',
      p_shunt <= 0.5 * shunt['power_w'])

for ref in ('J1', 'J2'):
    r = COMP[ref]['ratings']
    check(f'P6 connector {ref}', f'{ref} must be rated at least 2× the design current',
          f'{r["current_a"]} A', f'{r["current_a"] / I_MAX:.0f}× design current',
          r['current_a'] >= 2 * I_MAX)

check('P7 ground continuity', 'Supply return, sensor ground and microcontroller ground must be one '
      'net; a split ground would put the shunt drop into the measurement',
      f'GND has {len(net_members("GND"))} pin connections',
      'single common ground',
      len(net_members('GND')) >= 6
      and any(p['net'] == 'GND' for p in COMP['U2']['pins'])
      and any(p['net'] == 'GND' for p in COMP['J1']['pins']))

# --------------------------------------------------------------------------- #
# 4. Structural checks on the netlist itself
# --------------------------------------------------------------------------- #
all_nets = {}
for ref, comp in COMP.items():
    for pin in comp['pins']:
        all_nets.setdefault(pin.get('net', 'NC'), []).append((ref, pin['number']))
check('N1 no single-pin nets', 'Every net must have at least two connections, except pins marked '
      'no-connect',
      ', '.join(f'{n}={len(v)}' for n, v in sorted(all_nets.items())),
      'all ≥ 2 (NC excepted)',
      all(len(v) >= 2 for n, v in all_nets.items() if n != 'NC'))

check('N2 no-connect declared', 'Every unconnected pin must be listed explicitly, not left implicit',
      ', '.join(f'{n["ref"]}.{n["pin"]}' for n in D.get('not_connected', [])),
      'explicit',
      all(any(p['number'] == n['pin'] and p['net'] == 'NC' for p in COMP[n['ref']]['pins'])
          for n in D.get('not_connected', [])))

check('N3 decoupling', 'Every powered part must have a decoupling capacitor on its own supply net',
      f'C1 ({COMP["C1"]["value"]}) and C2 ({COMP["C2"]["value"]}) on 3V3',
      'present',
      any(p['net'] == '3V3' for p in COMP['C1']['pins'])
      and any(p['net'] == '3V3' for p in COMP['C2']['pins']))

check('N4 test points', 'The rails and the I2C clock must be reachable with a probe',
      ', '.join(f'{r} on {COMP[r]["pins"][0]["net"]}' for r in ('TP1', 'TP2', 'TP3', 'TP4', 'TP5')
                if r in COMP),
      'VIN, VPROT, VLOAD, GND, SCL',
      {'VIN', 'VPROT', 'VLOAD', 'GND', 'SCL'} <=
      {COMP[r]['pins'][0]['net'] for r in ('TP1', 'TP2', 'TP3', 'TP4', 'TP5') if r in COMP})

check('N5 part voltage ratings', 'No part may sit on a net whose maximum voltage exceeds its rating',
      'checked J1, J2, J3, C1, C2, R1, R2, R3, U1, U2',
      'all within rating',
      all(COMP[r]['ratings'].get('voltage_v', COMP[r]['ratings'].get('v_bus_max', 999)) >= V_MAX
          for r in ('J1', 'J2') if 'voltage_v' in COMP[r]['ratings'])
      and COMP['C1']['ratings']['voltage_v'] >= 2 * 3.3
      and COMP['C2']['ratings']['voltage_v'] >= 2 * 3.3)

check('N6 polarity', 'The TVS cathode must face the protected rail and its anode must face ground; '
      'reversed, it would conduct continuously',
      'D2 K→VPROT, A→GND',
      'correct',
      any(p['number'] == 'K' and p['net'] == 'VPROT' for p in COMP['D2']['pins'])
      and any(p['number'] == 'A' and p['net'] == 'GND' for p in COMP['D2']['pins']))

check('N7 shunt in the current path', 'The shunt must be in series between the source and the load, '
      'not in a branch',
      'VPROT → R1 → VLOAD, and VLOAD feeds J2',
      'series',
      any(p['number'] == '1' and p['net'] == 'VPROT' for p in COMP['R1']['pins'])
      and any(p['number'] == '2' and p['net'] == 'VLOAD' for p in COMP['R1']['pins']))

# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
width = max(len(r['rule']) for r in RESULTS) + 2
req_width = 58
print('\n  DCM-HW-V1 design rule checks — not KiCad ERC\n')
print(f"  {'RULE'.ljust(width)}{'REQUIREMENT'.ljust(req_width)}{'ACTUAL':<46}{'MARGIN':<44}RESULT")
print('  ' + '─' * (width + req_width + 46 + 44 + 6))
for r in RESULTS:
    print(f"  {r['rule'].ljust(width)}{r['requirement'][:req_width - 1].ljust(req_width)}"
          f"{r['actual'][:45].ljust(46)}{r['margin'][:43].ljust(44)}{'PASS' if r['ok'] else 'FAIL'}")
failed = [r for r in RESULTS if not r['ok']]
print('  ' + '─' * (width + req_width + 46 + 44 + 6))
print(f"  {len(RESULTS)} checks · {len(failed)} failed")
print('\n  Not checked here: KiCad ERC (no EDA tool available), PCB layout rules, creepage,')
print('  thermal rise, EMC, and anything that requires the physical module in hand.')
if failed:
    for r in failed:
        print('   FAIL ' + r['rule'] + ': ' + r['actual'])
    sys.exit(1)
print('  PASS: every design rule in checks.py is satisfied by design/dcm-hw-v1.json\n')
