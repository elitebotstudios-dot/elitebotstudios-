# Hardware implementation plan — Smart DC Energy Monitor

**Status: not started.** No component has been selected, quoted, purchased,
assembled or tested. Nothing in this document is a claim about work done.

This plan is for a supervised, low-voltage DC bench prototype. It deliberately
excludes mains wiring, household AC, battery packs with high short-circuit
current, and anything requiring isolation review by a qualified person.

> Every part characteristic mentioned below is a starting point for reading a
> datasheet, not a specification. Verify each figure against the current
> datasheet before selecting a part, and record the datasheet revision next to
> the decision.

---

## Safety boundary for the first build

- Source: bench supply limited to **≤ 24 V DC** and **≤ 1 A** current limit, or a
  fused low-voltage adapter of the same rating.
- Load: resistors rated above the dissipation involved, or an electronic load.
- Inline fuse on the positive rail; no exposed conductors while energised.
- Never work alone on an energised circuit; a second person must be able to
  remove power.
- Every change in wiring is reviewed before power is applied.
- The model's own defaults (5–12 V, 0–2 A) sit inside this boundary on purpose.

---

## Sensing options to compare

| Option | How it works | What it is good for | What to check before selecting |
|---|---|---|---|
| Shunt resistor + current-sense amplifier | A known resistance in the return path; an amplifier scales the small drop to the ADC range | Linearity, low cost, well-understood error budget | Amplifier common-mode range, gain error and offset drift, shunt tolerance and thermal EMF, power dissipated in the shunt |
| Hall-effect sensor module (e.g. the ACS7xx family) | Magnetic field from the conductor, output proportional to current | No series resistance, isolated by construction | Zero-current offset and its drift, ratiometric output vs ADC reference, bandwidth, sensitivity tolerance |
| Integrated I²C monitor with shunt (e.g. the INA219 / INA226 family) | Shunt plus ADC plus registers that also compute power | Fewer analogue decisions, digital output, calibrated registers | Bus-voltage range, conversion time, offset and gain error over temperature, whether the shunt is internal or external |
| External ADC (e.g. a 16-bit I²C ADC) plus conditioning | The ADC moves the accuracy question into one datasheet | Better resolution than many MCU ADCs, easier error budget | Reference quality, input range and PGA settings, conversion timing, noise vs data rate |

**Voltage sensing** in all cases: a resistor divider with an input filter. Check
the divider's loading on the measured node, the ADC sample-and-hold impedance
requirement, and the tolerance of the divider ratio.

---

## Controller options to compare

| Option | Notes | Verify in the datasheet |
|---|---|---|
| ESP32 family | Integrated Wi-Fi/BLE, integrated SAR ADC | ADC linearity and noise, usable input range, Wi-Fi activity vs ADC noise, deep-sleep current |
| STM32 family | Deterministic timers, good ADC peripherals, some parts offer hardware oversampling | ADC resolution and oversampling behaviour, reference options, DMA for continuous sampling |
| Any MCU + external ADC | Accuracy moves into a dedicated part | Bus timing, conversion rate vs the sample interval you need |

The model's sampling behaviour (a fixed interval with timestamps) maps directly
onto a timer-driven loop on any of these.

---

## Milestones

Statuses reflect work actually done. All are **not started**.

| # | Milestone | Output | Exit criterion |
|---|---|---|---|
| 1 | Approve hardware requirements | Ranges, accuracy target, safety boundary written and reviewed | Requirements signed off by a supervisor |
| 2 | Select components | Shortlist with datasheet figures and rejected alternatives | Every claim in the selection has a datasheet reference |
| 3 | Review the schematic | Schematic PDF with the measurement path, protection and reference | Reviewed by someone other than the author |
| 4 | Build the supervised prototype | One channel, fused, current-limited, on an insulated bench | Continuity and isolation checked before energising |
| 5 | Implement firmware | Timer-driven sampling, unit conversion, power, trapezoidal energy, CSV over serial | Firmware reproduces the model's arithmetic on synthetic inputs |
| 6 | Bench measurements | Recorded voltage/current/power points with instrument and conditions | At least five operating points across the range |
| 7 | Calibrate against a reference instrument | Gain and offset correction constants with their uncertainty | Deviation stated at every recorded point |
| 8 | Document results | Test table, photographs, conditions, failures included | A reader can repeat the measurement |
| 9 | Compare simulation and hardware | Difference table: model output vs measured value | Differences explained by the sensing chain, not by hand-waving |

Milestone 9 is the only one that can turn this software into a hardware claim.
Until it exists, the site will keep saying "hardware not built".

---

## What the software already gives the hardware phase

- A defined signal chain to implement, with parameters that map onto real parts
  (sensitivity in V per V and V per A, ADC bits and reference, gain, offset).
- A firmware arithmetic reference: the same equations, with test vectors, so the
  firmware can be checked against `dcem.js` on synthetic inputs before it ever
  touches a sensor.
- An error budget that can be compared with datasheet numbers instead of guessed.
