# Smart DC Energy Monitor
## Engineering Design and Verification Report

**Elite Bot Studios · Project 01 · revision B · 6 November 2026**

A low-voltage DC energy monitor built in three layers: a software model verified
against reference cases, a native KiCad schematic that passes electrical rule
check, and firmware that cross-compiles for an ESP32. The physical prototype has
not been built and no measurement of hardware exists.

---

## 1. Abstract

This report documents the design of a low-voltage direct-current energy monitor
intended to measure bus voltage and load current, derive instantaneous power and
integrate energy over time. The work is presented in three independent but
mutually verifiable layers.

The **software model** implements the entire measurement chain — source, load,
sensing, analogue-to-digital conversion, sampled power and energy accumulation —
and is verified by 67 hand-derived reference assertions and 594 checks against
independent constructions. The **electrical design** is a native KiCad schematic
built from official library symbols, passing electrical rule check with zero
errors and zero warnings, whose exported netlist agrees with the design file on
all 42 pins. The **firmware** extracts current from the shunt voltage, timestamps
each sample, integrates energy with an explicit missing-data policy, and
cross-compiles for the ESP32 target using PlatformIO with the Xtensa GCC 14.2.0
toolchain; its arithmetic and its sensor driver pass 98 host checks.

What the project does **not** have is equally important: no printed circuit
board, no assembled prototype, no flashed firmware and no measurement against a
reference instrument. No accuracy figure is claimed. The report distinguishes
throughout between what has been verified computationally and what remains
untested physical work.

---

## 2. Objectives

The motivating question is not what an energy monitor displays, but how far that
display can be from the truth and which stage put the error there.

A monitor reporting 12.00 W is making a claim about a chain of components. A
divider scales voltage; a shunt converts current into a small differential
voltage; an amplifier and an ADC convert both into numbers; firmware multiplies
them and a clock decides how long to accumulate. Each stage contributes an error
the others do not cancel, and several of those errors — gain error, a stale
sample, an interval integrated across missing data — are indistinguishable from a
real change in the load.

The project therefore has three objectives:

1. Implement the measurement chain in software so that every stage can be varied and tested in isolation.
2. Produce an electrically valid hardware design for the same chain, checked by tools rather than by assertion.
3. Implement firmware whose arithmetic can be tested without hardware, and prove it compiles for the intended target.

---

## 3. Requirements

Requirements are marked **verified** where an artefact or script in the
repository checks them, and **proposed** where they remain intentions that only
a bench can confirm.

| ID | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| S1 | Model a DC source with series resistance | Terminal voltage follows Voc − I·Rs | verified |
| S2 | Five load models: resistance, current, step, duty, sequence | Each produces the documented operating point | verified |
| S3 | Configurable sensing per channel | Reported value reproducible from the documented equation | verified |
| S4 | Quantisation with saturation reporting | Values on the LSB grid; half-LSB bound; clipping counted | verified |
| S5 | Per-channel calibration | True error terms recover the true value exactly | verified |
| S6 | Sample timestamps with rejection of invalid data | Duplicate, non-monotonic, non-numeric and out-of-range refused | verified |
| S7 | Power from measured values and from truth | Both reported side by side | verified |
| S8 | Energy by trapezoidal integration on actual intervals | Reference cases A, B, C, E reproduce hand values | verified |
| S9 | Separate imported and exported energy | Net, import and export reported | verified |
| S10 | CSV export with a documented column set | Round trip within 1e-6 | verified |
| S11 | Deterministic runs | Same configuration and seed give identical output | verified |
| E1 | Measure bus voltage at the load | Within ±1 % of a reference meter at three points | proposed |
| E2 | Measure DC current through a shunt | Within ±2 % of a reference meter at three points | proposed |
| E3 | Derive instantaneous power | P = V × I from the same sample | verified |
| E4 | Accumulate energy over elapsed time | Trapezoidal on measured intervals | verified |
| E5 | Report through serial | CSV at ≥ 1 Hz with status | proposed (never run on a board) |
| E6 | Survive a sensor communication failure | Sample marked, interval not integrated, counter incremented | verified |
| E7 | Protect the input | Series fuse, reverse diode, transient clamp | verified by design rule check |
| E9 | Keep logic levels compatible | 3.3 V on both sides; no 5 V on the bus | verified by design rule check |
| E12 | Report energy without inventing it | Gaps and invalid samples never integrated | verified |

The design envelope is 5–12 V DC nominal and 0–0.5 A, with a bench supply
current-limited to 1 A. A 1 A test would require a 0.05 Ω shunt: with 0.1 Ω the
measurable maximum is 0.8192 A, set by the sensor's ±81.92 mV shunt range.

---

## 4. System architecture

The same signal path is described three ways.

```
 DC source ──▶ [fuse] ──▶ [Schottky] ──┬──▶ INA226 IN+ ──[0.1 Ω shunt]── INA226 IN− ──▶ load
                                        │                                        │
                                     [TVS]                                   VBUS tied here
                                        │                                        │
                                       GND ◀────────── common ground ────────────┘
                                                                                 │
                                             INA226 ──I²C (0x40, 3.3 V)──▶ ESP32-DevKitC
                                                                                 │
                                                                   CSV on USB serial 115200
```

The shunt is in series with the load, the sensor measures the **load side** of
it, and the reverse-polarity diode sits **upstream** of the shunt. That ordering
is deliberate: the diode costs headroom, but it cannot corrupt the measurement,
and the reported power is what the load actually receives.

Three descriptions exist for this one path, which is what makes verification
possible:

| Description | Artefact | Verified by |
|---|---|---|
| Simulation | `energy-monitor/model/dcem.js` | 661 automated checks |
| Schematic | `energy-monitor/hardware/kicad/dcm-hw-v1.kicad_sch` | ERC, netlist comparison |
| Firmware | `energy-monitor/firmware/` | 98 host checks, cross-compilation |

---

## 5. Mathematical model

**Power** is computed twice, from the measured voltage and current and from the
simulated truth, and both are reported:

```
P = V · I
```

**Energy** is accumulated with the trapezoidal rule over the actual interval
between accepted samples:

```
E_import += ½ (P_prev + P_now) · Δt
E_export += ½ (|P_prev| + |P_now|) · Δt          (negative power)
E_Wh = (E_import − E_export) / 3600
```

An interval containing a sign change is split at the zero crossing by linear
interpolation before integration, so imported and exported energy are each
integrated over the region where they apply.

**Why trapezoidal.** It is exact for constant power and second-order accurate for
piecewise-linear power. For a step that straddles one interval it smears the
step across that interval; with 1 s sampling the error on a 27 000 J run is
2.5 J, or 0.0093 %. Halving the sample interval quarters that error — a
convergence order the independent suite checks directly rather than assuming.

**Why actual intervals.** The model never assumes uniform spacing. Integrating a
constant 18 W profile at deliberately irregular timestamps must produce exactly
P · (t_end − t_start); this is asserted to 1e-9 J. Summing power samples without
multiplying by time is dimensionally wrong, and at 0.5 s sampling it is out by a
factor of two.

**Sensing chain**, per channel, in signal order:

```
pin  = value · S · (1 + g) + Vos + n        sensitivity, gain error, offset, noise
pin' = clamp(pin, 0, Vref)                  saturation, flagged
code = round(pin' / LSB),  LSB = Vref / 2^bits
reported = code · LSB / S                   uncalibrated
reported = (code · LSB − Vos,est) / (S · (1 + g_est))   calibrated
```

Calibration is per channel: a divider and a shunt amplifier have independent
tolerances, and one correction cannot serve both. An early revision shared a
single correction across both channels; the test suite caught it.

**Missing data.** An invalid sample costs two intervals — the one ending at it
and the one starting from it — because the alternative is to integrate across a
stale reading. A gap longer than five seconds is treated as missing data and not
integrated at all. Both events are counted, so a period with no measurement
cannot be mistaken for a period of zero power.

---

## 6. Hardware design

| Item | Selection | Key figures |
|---|---|---|
| Sensor | Texas Instruments INA226AIDGSR, VSSOP-10 | 0–36 V bus, ±81.92 mV shunt, 16-bit, 2.7–5.5 V supply |
| Shunt | 0.1 Ω, 0.5 %, 1 W, 2512 | 50 mV at 0.5 A (61 % of range), 25 mW |
| Controller | Espressif ESP32-DevKitC-32E | 3.3 V logic, I²C on GPIO21/22 at 100 kHz |
| Series protection | Bourns MF-R110 PTC | 1.1 A hold, 2.2 A trip |
| Reverse polarity | onsemi SS34 Schottky | 3 A, 40 V, upstream of the shunt |
| Transient clamp | Littelfuse SMBJ15A | 15 V standoff, 24.4 V clamp at peak current |
| Pull-ups | 4.7 kΩ to 3.3 V, on the carrier | keeps the bus at the sensor's own supply level |

**A correction worth recording.** Revision A of this design treated the sensor as
a breakout module and never modelled VBUS. On the bare IC, VBUS is pin 8, a
separate input that must be wired to IN− for load-side measurement; the
datasheet's own application example does exactly that. Without it the bus reading
comes from the wrong node and every power figure is wrong while appearing
plausible. Revision B specifies the bare IC, wires VBUS to VLOAD, straps A0 and
A1 to ground for address 0x40, and marks ALERT as an explicit no-connect.

**Electrical verification.** The schematic is a native KiCad 9 project generated
from the design file and built from official library symbols. `kicad-cli sch erc`
reports **0 errors and 0 warnings** after two genuine errors were fixed by
correcting symbol pin types rather than by disabling the rule. Twenty-five
purpose-written design rules additionally check the things ERC cannot: sensor
ranges, shunt dissipation and current limit, clamp voltage against the sensor's
absolute maximum, connector ratings, ground continuity and measurement polarity.

---

## 7. Firmware architecture

```
include/dcm/types.h        units, Status, Calibration, Sample, EnergyTotals
include/dcm/transport.h    the I2C boundary as an interface
include/dcm/ina226.h       register map and decode declarations
include/dcm/sensor.h       device logic: configuration, identity, reads
include/dcm/integrator.h   energy accumulation and the missing-data policy
src/core/*.cpp             implementations, free of Arduino
src/main.cpp               ESP32 application layer (Wire transport, CSV, self-test)
test/test_core.cpp         69 host checks over eight vector sets
test/test_sensor.cpp       29 host checks against a mock I2C bus
```

The split exists so the arithmetic can be tested without a board: the host tests
drive the same `dcm::Ina226Sensor` through a simulated bus that can acknowledge,
NACK, report the wrong identity, saturate, over-range or recover.

Two decisions dominate the firmware's behaviour:

- **Current is derived from the shunt voltage and the known resistance**, not from the device's current register. This removes any dependence on the calibration register having been written correctly, at the cost of one division per sample.
- **Timestamps are unsigned 32-bit milliseconds**, so subtraction wraps correctly after 49.7 days. There is no real-time clock, so no date or time of day is claimed anywhere in the output.

**Build.** `pio run -e esp32dev` with PlatformIO 6.2.0, the espressif32 8.0.0
platform and the Xtensa GCC 14.2.0 toolchain produces `firmware.bin` using
25.4 % of flash and 7.2 % of RAM, with no warnings at `-Wall -Wextra`. The first
attempt failed: `setup()` and `loop()` were inside an anonymous namespace, so the
Arduino core could never have called them. The binary has never been flashed.

---

## 8. Verification methodology

No test in this project asserts a value produced by the code it is testing.

| Suite | Method | Checks |
|---|---|---|
| Reference cases | Hand-derived expectations from P = VI and the trapezoidal rule | 67 |
| Model independent | Second integrator over 500 random series; closed-form sine integral with a convergence-order check; Ohm and Kirchhoff balance; additivity; quantisation bounds; noise statistics | 594 |
| Energy duration | 1 s, 9 s, 1 hour, irregular and invalid-sample cases, hand-derived, against both the firmware policy and the model | 48 |
| Firmware core | Vector sets generated from the written policy, not from the C++ | 69 |
| Sensor driver | The driver against a programmable mock bus | 29 |
| Vectors vs model | The firmware vectors replayed through the verified model | 20 |
| Netlist agreement | The KiCad export compared pin by pin with the design file | 42 pins |
| Configuration | Manifest values compared with the C++ sources, the design file and the published pages | 30 |
| Package coherence | Every referenced artefact exists; claims are bound to artefacts | 237 |
| Design rules | 25 electrical rules with margins printed | 25 |
| ERC | `kicad-cli sch erc` | 0 errors, 0 warnings |

The reference and independent suites are deliberately complementary: a model
error that is consistent with itself survives the first and fails the second.

---

## 9. Verified results

Actual output from the suites, not a summary of intent:

| Case | Input | Expected | Result |
|---|---|---|---|
| A | 12 V, 1 A, 3600 s | 43 200 J = 12 Wh | exact |
| B | 5 V, 2 A, 1800 s | 18 000 J = 5 Wh | exact |
| C | 10 V, 1 A → 0.5 A at 1800 s | 27 000 J continuous ideal | 26 997.5 J (0.0093 % low) |
| D | 12 V, 0 A, 600 s | 0 J | exact, voltage still reported |
| E | irregular timestamps, 5 intervals | 77.605 J by hand | 77.605 J |
| F | +2 % gain, +50 mV offset | 10.4 V uncalibrated, 10.000 V calibrated | exact both ways |
| G | six invalid-data classes | classified and refused | all refused |
| Q | 12-bit ADC, 3.3 V, ÷4 divider | 3.2227 mV per LSB at the input | exact |
| Energy | 3 W for 1 s / 9 s / 3600 s | 3 J / 27 J / 10 800 J | exact |
| Firmware | gap, invalid sample, 32-bit rollover | held, counted, wrap-safe | all pass |
| ESP32 | `pio run -e esp32dev` | links for Xtensa LX6 | SUCCESS, 25.4 % flash |
| KiCad ERC | `dcm-hw-v1.kicad_sch` | no pin conflicts | 0 errors, 0 warnings |

---

## 10. Design limitations

- **No hardware accuracy.** No sensor, ADC, microcontroller or board was used. Nothing in this report predicts the accuracy of a real implementation.
- **DC only, single channel, non-isolated.** No AC, mains, grid or isolation.
- **No switched-mode behaviour.** Loads are smooth resistance or current demands; anything faster than the sample interval is aliased.
- **No ADC non-idealities.** Quantisation is ideal uniform rounding: no INL, DNL, reference drift or aperture jitter.
- **No MCU behaviour.** No fixed-point arithmetic, timer jitter or interrupt latency is modelled.
- **The module question is unresolved.** If a breakout module is used instead of the bare IC, its shunt value, pull-up rail, address straps and VBUS connection must be verified physically.
- **ERC is not correctness.** It proves the connections are electrically legal, not that the circuit does the right thing.
- **A compile is not a run.** The firmware has never executed on hardware.

---

## 11. Future physical testing

Seven stages, each with an observable exit condition, defined in
`verification/calibration-plan/calibration-plan.md` and summarised in
`hardware/design-review/prototype-review-checklist.md`:

1. Review the design and decide bare IC or module.
2. Identify the parts: markings, shunt resistance, module pull-up rail, VBUS.
3. Unpowered continuity; prove no short from the protected rail to ground.
4. First power-up at 5 V and 100 mA with no load.
5. Communication: I²C scan finds 0x40, identity registers read correctly.
6. Known loads, compared with a multimeter.
7. Six-point reference comparison, then calibration, then a repeat.
8. Uncertainty statement: residual error at each point, repeatability and conditions.

Only after stage 8 does this project have an accuracy figure to publish. Until
then the website states the accuracy targets as targets, with no evidence.

---

## 12. References and source locations

**Datasheets** (official sources, not redistributed):

- Texas Instruments INA226, *36 V, 16-bit, ultra-precise I²C output current / voltage / power monitor*, SBOS547A. `https://www.ti.com/product/INA226`
- Espressif ESP32-DevKitC-32E documentation, `https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/`
- Bourns MF-R series PTC, onsemi SS34, Littelfuse SMBJ, Vishay CRCW and Yageo RC series: linked individually in `hardware/datasheets-references/links.md`.

**Source locations** (all served from this site):

| Artefact | Path |
|---|---|
| Simulation model | `/energy-monitor/model/dcem.js` |
| Model tests | `/energy-monitor/tests/` |
| Reference datasets | `/energy-monitor/examples/` |
| KiCad schematic | `/energy-monitor/hardware/kicad/dcm-hw-v1.kicad_sch` |
| ERC report | `/energy-monitor/hardware/kicad/erc-report.txt` |
| Netlist | `/energy-monitor/hardware/kicad/netlist-kicad.net` |
| Bill of materials | `/energy-monitor/hardware/bom/dcm-hw-v1-bom.csv` |
| Design review | `/energy-monitor/hardware/design-review/design-review.md` |
| Firmware | `/energy-monitor/firmware/` |
| Build evidence | `/energy-monitor/firmware/BUILD-EVIDENCE.md` |
| Evidence hub | `/projects/dc-energy-monitor-evidence.html` |

---

## 13. Attribution and contributions

**Produced with AI assistance.** The software model, the test suites, the
schematic generator, the KiCad project, the firmware, the documentation and this
report were written with AI assistance during the construction of the Elite Bot
Studios website. This is disclosed because it is material to how the work should
be read: it is a well-instrumented engineering exercise, not a body of
independently authored personal engineering.

**Specified by the founder.** The project direction; the decision to remain
low-voltage and DC; the operating envelope; the requirement that hardware claims
stay separate from software claims; and the rule that no measurement, credential
or result be invented.

**Not yet done by the founder.** Reading and re-deriving the power and energy
relations independently; running the suites and breaking something deliberately;
reviewing the schematic pin by pin; building the board; and measuring it. Until
those happen, the project's most valuable claim is that it knows exactly what it
has and has not verified.

---

*Report generated from the repository at revision B. Every figure in sections 8
and 9 is printed by a suite that can be re-run; every claim in sections 3 to 7 is
linked to an artefact in section 12.*
