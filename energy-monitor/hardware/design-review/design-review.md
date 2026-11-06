# Design review — DCM-HW-V1 rev A

Date: 2026-11-06 · Reviewer: Elite Bot Studios (AI-assisted) · Status: **draft reviewed, not built**

## What was actually verified, and how

| Verification | Method | Result |
|---|---|---|
| Netlist connectivity | `design/generate.py` computes pin coordinates and refuses to write a drawing where any wire endpoint floats or any pin is unreached | 37 pins, all connected |
| Electrical rules | `design/checks.py`, 25 rules written for this design | 25 pass, 0 fail |
| Sensor decode and integration | `firmware/test/test_core.cpp`, g++ on the host | 69 checks, 0 fail |
| Vectors vs the verified model | `energy-monitor/tests/vector-model-parity.test.js` | agree where policies agree; differences asserted where they do not |
| KiCad ERC | **not run** — no EDA tool was available in the authoring environment | see "Not verified" |
| Firmware compilation for ESP32 | **not run** — no ESP32 toolchain available | see "Not verified" |
| Physical build, power-up, measurement | **not performed** | see "Not verified" |

## Findings

1. **The 0.1 Ω shunt caps the measurable current at 0.819 A.** 50 mV at 0.5 A is
   61 % of the ±81.92 mV range, which is a good place to be, but a 1 A test would
   saturate the channel. A 1 A test needs 0.05 Ω and a fresh calibration. This is
   recorded rather than silently discovered later.
2. **The module is the least-defined part of the design.** INA226 breakout boards
   differ in shunt value, in the rail their I²C pull-ups use, in address strapping
   and in whether VBUS is tied to IN−. The carrier therefore fits its own 0.1 Ω
   shunt and its own 3.3 V pull-ups, and the review lists the module checks that
   must happen with a multimeter before the ESP32 is connected.
3. **Reverse-polarity protection sits upstream of the shunt.** This costs
   0.3–0.4 V of headroom but keeps the measurement honest: the shunt still sees
   the true load current and the sensor still measures what the load receives.
   Had the diode been placed after the shunt, the reported voltage would have
   included a drop the load never sees.
4. **The TVS clamps at 24.4 V, below the sensor's 36 V absolute maximum but above
   the 12 V rail.** It protects the sensor and the capacitors without conducting
   in normal operation.
5. **The fuse is a 1.1 A hold PTC, not a 0.5 A part.** A PTC at its hold current
   runs hot and drifts; at 0.5 A continuous this one sits at 45 % of hold. The
   bench supply's current limit remains the primary protection.

## Open questions that need the physical module

| # | Question | How to answer it |
|---|---|---|
| Q1 | What address does the module actually strap? | Read it with an I²C scanner; A0/A1 to GND should give 0x40 |
| Q2 | Where do the module's pull-ups go — 3.3 V, 5 V, or the module VCC? | Measure the module's SDA/SCL to VCC resistance with the board unpowered, then check the rail with it powered from 3.3 V only |
| Q3 | Is VBUS tied to IN− on the module? | Check continuity between the VBUS pin (if broken out) and IN−; if separate, wire VBUS to IN− |
| Q4 | What is the on-board shunt value, if any? | Measure with a milliohm meter or four-wire method; if it is in parallel with the external shunt, remove it or account for it |
| Q5 | Is the module's shunt amplifier common-mode range satisfied at 12 V? | Datasheet check against the module's actual IC |
| Q6 | Does the ESP32 board's 3.3 V regulator supply the module without excessive ripple? | Scope the 3V3 rail under I²C traffic |

## Not verified — stated plainly

- **No KiCad project and no ERC.** The schematic is generated from a netlist data
  file and drawn as SVG; `design/checks.py` implements the specific rules this
  design needs, but that is not a substitute for ERC on a real schematic. The
  KiCad netlist `netlist/dcm-hw-v1.net` is provided for import into Pcbnew,
  or for redrawing the schematic in KiCad and running ERC there.
- **The firmware has never been compiled for the ESP32.** Only the portable
  calculation core has been compiled and tested, with g++ on the host. The
  Arduino application layer in `src/main.cpp` has been written and reviewed but
  not built.
- **Nothing has been powered, measured, or calibrated.** No accuracy number in
  this repository comes from hardware.

## Recommended next actions, in order

1. Read this review and the requirements; decide whether the envelope is right.
2. Buy one INA226 module and one ESP32-DevKitC-32E; answer Q1–Q4 with a multimeter
   before connecting anything together.
3. Redraw the schematic in KiCad from the two SVG sheets, import or re-enter the
   netlist, and run ERC. Fix whatever it reports.
4. Build the carrier on a breadboard first, with the supply current-limited to
   100 mA, and confirm the sensor is detected at 0x40.
5. Only then move to the bench stages in `verification/calibration-plan/`.
