# Technical dossier — Smart DC Energy Monitor

**Elite Bot Studios · Project 01 · 2026-11-06**
Software Model V1 verified · Hardware Design V1 drafted · Physical prototype not built

A single document for a technical reviewer who does not want to navigate a website.

---

## 1. Objective

Build, and eventually measure with, a low-voltage DC energy monitor: a system that
measures bus voltage and load current, derives power, accumulates energy over time,
and reports it. The project exists in three layers, and each layer is only claimed
at the level of evidence it has earned:

| Layer | Status | Evidence |
|---|---|---|
| Software model | **Verified** | 67 reference assertions + 594 independent checks, runnable with Node |
| Hardware design | **Drafted, script-reviewed** | Two schematic sheets, 25 design-rule checks, BOM, design review |
| Embedded firmware | **Core tested on desktop** | 69 checks with g++; ESP32 layer never compiled |
| Physical prototype | **Not built** | No part purchased or assembled |
| Calibration / validation | **Not started** | Procedure and blank sheet exist |

## 2. System architecture

```
 DC source ──▶ [fuse] ──▶ [Schottky] ──┬──▶ INA226 IN+ ──[0.1 Ω shunt]── INA226 IN− ──▶ [load]
                                       │                                        │
                                    [TVS]                                   bus voltage
                                       │                                        │
                                      GND ◀──────────── common ground ──────────┘
                                                                                │
                                            INA226 ──I²C (0x40, 3.3 V)──▶ ESP32-DevKitC
                                                                                │
                                                                  CSV on USB serial 115200
```

The shunt is in series with the load and the sensor measures the **load side** of
it, so the reported power is what the load receives. Reverse-polarity protection
sits upstream of the shunt, so it costs headroom but not measurement accuracy.

## 3. Software model (verified)

A dependency-free JavaScript model (`energy-monitor/model/dcem.js`) of the whole
measurement chain: source and load solved together, configurable sensing with gain,
offset, seeded noise and ADC quantisation, sampled power, trapezoidal energy
integration on real timestamps, and an explicit rejection policy for invalid data.

Verified against seven reference cases (A–G) with hand-derived expected values, and
re-verified by an independent suite that compares the model against a
switching-cycle simulation, a closed-form integral, Ohm/Kirchhoff balance,
additivity of consecutive runs, quantisation bounds and noise statistics.

Key numbers: 43 200 J = 12 Wh for 12 V/1 A over 3600 s (exact); 26 997.5 J instead
of 27 000 J for a step straddling one interval (0.0093 % low, second order in Δt);
77.605 J for a five-interval irregular profile, hand-checkable.

## 4. Proposed electrical design

| Item | Choice | Reason |
|---|---|---|
| Sensor | INA226, 16-bit, 0–36 V bus, ±81.92 mV shunt, 2.7–5.5 V supply | 3.3 V logic compatibility, no level shifting, load-side bus measurement |
| Shunt | 0.1 Ω, 0.5 %, 1 W, 2512 | 50 mV at 0.5 A (61 % of range), 25 mW dissipation |
| Controller | ESP32-DevKitC-32E | 3.3 V logic, default I²C on GPIO21/22, documented, widely available |
| Protection | 1.1 A hold PTC, SS34 Schottky, SMBJ15A TVS | Fault tolerance without corrupting the measurement |
| Link | 4-way header, 4.7 kΩ pull-ups to 3.3 V on the carrier | Removes dependence on the module's pull-up rail |

25 design-rule checks pass, including sensor range, shunt dissipation, TVS standoff
versus clamp, connector ratings, ground continuity, logic compatibility, address
strapping and test-point access.

## 5. Firmware architecture

Portable C++ core (no Arduino headers) plus a thin application layer:

- `ina226` — register decode: 2.5 µV shunt LSB, 1.25 mV bus LSB, current from V/R
- `integrator` — trapezoidal energy on wrap-safe millisecond timestamps, with a
  missing-data policy: an invalid sample costs two intervals, a gap over 5 s is not
  integrated, and both are counted
- `main.cpp` — I²C reads at 4 Hz, calibration, CSV reporting, sensor self-test

The core compiles with `g++ -std=c++17 -Wall -Wextra` and passes 69 checks over
eight vector sets, including a step, irregular timestamps, a 7 s gap, an invalid
reading, a 32-bit millisecond rollover and a calibration case. The same vectors are
run through the verified JavaScript model: where the policies agree the energies
match to 1e-12 Wh, and where they intentionally differ the difference is asserted.

## 6. Test evidence

| Suite | Location | Result |
|---|---|---|
| Model reference cases | `energy-monitor/tests/dcem-reference.test.js` | 67 assertions pass |
| Model independent verification | `energy-monitor/tests/dcem-independent.test.js` | 594 checks pass |
| Firmware core | `energy-monitor/firmware/test/test_core.cpp` | 69 checks pass |
| Vectors vs model | `energy-monitor/tests/vector-model-parity.test.js` | 20 checks pass |
| Design rule checks | `energy-monitor/hardware/design/checks.py` | 25 checks pass |
| Page/package contract | `energy-monitor/tests/hardware-package.test.js` | see the file |

All of it runs with Node, g++ and Python 3. No paid tools, no accounts.

## 7. Limitations

- The hardware has never been powered. No accuracy claim about the circuit exists.
- No KiCad project, no ERC: the schematic is generated from a netlist file and
  checked by purpose-written rules, which is not the same thing.
- The ESP32 application layer has never been compiled.
- The INA226 module is the least-defined part: shunt value, pull-up rail, address
  straps and bus-voltage tapping must be verified physically before use.
- The software model is an idealisation: no ADC INL/DNL, no thermal or ageing
  effects, no loop dynamics, no AC.
- No real-time clock: timestamps are milliseconds since boot.

## 8. Future physical validation

Nine staged steps, defined in `energy-monitor/verification/calibration-plan/`:
unpowered checks, supervised power-up at 100 mA, communication, known loads,
reference-meter comparison at six points, deviation analysis, calibration, repeat
measurement, uncertainty statement. Only after those does this project have an
accuracy figure to publish.

## 9. Attribution

The model, hardware design, firmware, documentation and website were produced with
AI assistance during the construction of this site, and that is disclosed on every
page that presents the work. The founder set the direction, the safety boundary and
the rule that no measurement or credential be invented; the founder has not yet
personally designed, built or measured this hardware, and nothing here claims
otherwise.

## 10. Reproduce the results

See `energy-monitor/docs/reproduce.md` for the software model, and
`energy-monitor/firmware/README.md` for the firmware core. Neither needs the
website or a browser.
