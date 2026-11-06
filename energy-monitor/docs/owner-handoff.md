# Owner handoff — what needs a person, and what has been automated

Everything a machine can check has been checked. What remains needs parts, a
bench, a multimeter and a human who has read the design. This document is the
handover.

**Nothing here has been ordered, built, powered or measured.**

---

## 1. What exists right now

| Layer | State | Where |
|---|---|---|
| Software model | Verified — 661 checks | `energy-monitor/model/dcem.js`, run it at `/projects/dc-energy-monitor.html` |
| Requirements | Documented, draft for review | `energy-monitor/hardware/requirements/electrical-requirements.md` |
| Schematic | Native KiCad, ERC 0/0 | `energy-monitor/hardware/kicad/dcm-hw-v1.kicad_sch` |
| Netlist | Matches the design file on 42 pins | `energy-monitor/hardware/kicad/netlist-kicad.net` |
| Firmware | Cross-compiled for ESP32, never flashed | `energy-monitor/firmware/` |
| Prototype | **Does not exist** | — |
| Measurements | **None** | — |

---

## 2. Parts, and the choice you have to make

The schematic describes the **bare INA226AIDGSR in VSSOP-10**. That is what the
KiCad project contains, and it is the only variant where the VBUS connection is
explicit.

| Option | What it means | What to check |
|---|---|---|
| **A. Bare INA226AIDGSR** (as drawn) | VSSOP-10, 0.5 mm pitch. Needs an adapter board or a steady hand. | That you can solder it, or that an adapter exists. |
| **B. Breakout module** | Easier to wire. Vendors differ. | Address straps, pull-up rail (must be 3.3 V), on-board shunt value, and **whether VBUS is tied to IN−**. If it is not, the bus reading is meaningless. |
| **C. Custom PCB** | Not designed. | Would need layout, DRC and a fabrication order. Out of scope for now. |

Bill of materials: `energy-monitor/hardware/bom/dcm-hw-v1-bom.csv` — 17 line items
with manufacturer, ratings and rationale. No prices are quoted, because none were
checked.

Minimum parts to get a first reading: INA226AIDGSR (or a verified module), ESP32
DevKitC-32E, 0.1 Ω 1 W shunt, 4.7 kΩ resistors ×2, 10 µF and 100 nF capacitors,
2-way screw terminals ×2, 4-way header, hook-up wire, and one 12 Ω 10 W resistor
as a load.

---

## 3. Tools and instruments

| Needed | Why | Acceptable substitute |
|---|---|---|
| Bench supply with adjustable current limit | The first power-up must be able to fail safely | A 5 V USB supply plus an inline fuse, if you accept less control |
| Multimeter, 3.5 digits or better | Continuity, rail voltage, shunt resistance | — |
| Reference meter, better than 0.1 % V and 0.2 % A | Calibration needs a reference at least 10× better than the target | A calibrated bench DMM with a certificate |
| Power resistors | Loads: 12 Ω, 47 Ω, 100 Ω at 12 V | Any combination of higher-power parts |
| Optional: logic analyser | Seeing whether the I²C bus actually clocks | A scope, or the firmware's own error counters |

---

## 4. Safe low-voltage prerequisites

1. Everything stays at or below 24 V DC and 1 A. **There is no mains in this
   design and there must not be.**
2. Second person present whenever the circuit is energised.
3. Inline fuse fitted; supply current limit at 100 mA for the first power-up.
4. Work through `hardware/design-review/prototype-review-checklist.md` in order.
   It lists the stop conditions.
5. Do not connect the ESP32 to the carrier until the module checks in stage 2 of
   that checklist are done.

---

## 5. Flashing the firmware

```bash
cd energy-monitor/firmware
pio run -e esp32dev              # builds firmware.bin (already verified: 25.4 % flash)
pio run -e esp32dev -t upload    # requires the board connected by USB
pio device monitor -b 115200     # CSV output
```

The board must appear as a serial port. On the first run expect either the CSV
header and a first line, or a `# STATUS:` line saying the sensor was not found —
which is the firmware doing its job, not failing.

---

## 6. Outstanding design questions

From the design review, answerable only with the physical part:

1. What address does the module (if used) actually strap?
2. Where do its pull-ups go — 3.3 V, 5 V, or its own supply?
3. Is VBUS tied to IN−, or is it a separate pin that must be wired?
4. What is the on-board shunt value, and does it parallel the external 0.1 Ω?
5. Does the sensor's common-mode range hold at 12 V?
6. Does the 3.3 V rail hold up under I²C traffic?

---

## 7. How real results get onto the site later

The site is generated from files in this repository, so real bench results are
added by editing data, not by hand-writing HTML:

1. Fill in `energy-monitor/verification/calibration-plan/bench-test-template.csv`
   with the actual readings and conditions.
2. Add the measurements to the dossier source
   (`energy-monitor/docs/dossier.md`) — section 9 is where verified results live.
3. In `projects.json`, move the `Physical prototype` milestone from `pending` to
   `done` **only when a board exists**, and attach the artefact links.
4. Rebuild (`python3 scripts/site/*.py`, `python3 scripts/build_dossier.py`), run
   the test suite, and deploy.

The package-coherence test will keep you honest: if a page claims a measurement
while the milestone is pending, the build fails.

---

## 8. What this sprint could not do, and why

- It cannot assemble hardware, and did not pretend to.
- It cannot calibrate, because calibration compares two instruments and only one
  of them exists.
- It cannot verify an accuracy target, because that needs a reference meter.
- It cannot supply a CV or professional profile links; those are yours to approve
  first.

The next meaningful step is not another document. It is a bench, a fuse, and a
100 mA current limit.
