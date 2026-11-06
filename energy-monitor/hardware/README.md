# Hardware design package — DCM-HW-V1 rev A

**Design complete as a draft. Not built, not powered, not measured.**

This folder is the design package for the measurement carrier between a
low-voltage bench supply and a load, with an INA226 measuring bus voltage and
shunt current and an ESP32-DevKitC reading it over I²C.

## What you have

```
design/dcm-hw-v1.json          the single source: components, pins, nets, layout, references
design/generate.py             generates the schematic SVGs, netlist, connection table and BOM
design/checks.py               25 design-rule checks with margins printed
schematic/dcm-hw-v1-sheet1.svg power path and current measurement
schematic/dcm-hw-v1-sheet2.svg sensor supply, I²C, microcontroller interface
netlist/dcm-hw-v1-connections.csv  pin-by-pin connection table
netlist/dcm-hw-v1.net          KiCad netlist, importable into Pcbnew
bom/dcm-hw-v1-bom.csv          bill of materials, no invented prices
requirements/electrical-requirements.md  requirements with verified/proposed status
design-review/design-review.md findings, open questions, what was not verified
datasheets-references/links.md official sources for every figure used
```

Regenerate everything after any change:

```bash
python3 energy-monitor/hardware/design/generate.py
python3 energy-monitor/hardware/design/checks.py
```

The generator refuses to write a drawing if any wire endpoint floats or any pin is
unreached, so the picture and the netlist cannot drift apart.

## How the circuit works, in plain terms

1. **Power comes in at J1** and passes through a resettable fuse, a Schottky diode
   (so reversed supply leads cannot damage anything) and a transient clamp.
2. **All of the load current then flows through R1**, a 0.1 Ω resistor. At 0.5 A
   that is 50 mV across it — small enough not to disturb the load, large enough for
   the sensor to measure.
3. **The INA226 measures two things**: the voltage across R1 (which gives current,
   because V/R = I) and the voltage at the load side of R1. Multiplying them gives
   the power the load is actually receiving.
4. **The ESP32 asks the sensor for those two numbers** over I²C every 250 ms,
   converts them to volts and amps, applies any calibration, multiplies to get
   power, and adds power × elapsed time to a running energy total.
5. **The total comes out of the USB serial port** as a line of CSV.

## Things that will bite if you skip them

- **The INA226 module you buy may not match the drawing.** Breakout boards differ
  in shunt value, pull-up rail and address strapping. Answer questions Q1–Q4 in the
  design review with a multimeter *before* connecting the ESP32.
- **Do not connect a 5 V pull-up to an ESP32 pin.** Use the 3.3 V pull-ups on the
  carrier (R2, R3) and remove or verify the module's own.
- **0.1 Ω limits you to 0.82 A.** A 1 A test needs 0.05 Ω and a new calibration.
- **The reverse diode costs you 0.3–0.4 V.** Set the supply to account for it, and
  expect the load voltage to read lower than the supply voltage. That is correct.
- **Start with the supply current limit at 100 mA.** Every first power-up should be
  able to fail without anything getting hot.

## Before you buy

1. Read `design-review/design-review.md`. It lists what was checked, what was not,
   and the six questions only the physical module can answer.
2. Read the two schematic sheets at full size, not as thumbnails.
3. Decide whether you want to build this carrier at all, or breadboard it first —
   breadboarding is the faster path to a working sensor, and the drawing then
   becomes the thing you transfer it onto.

## What this package is not

Not a PCB layout, not a KiCad project, not an ERC'd schematic, not a tested
circuit, and not a calibration result. Those are the next steps, in that order, in
`verification/calibration-plan/calibration-plan.md`.
