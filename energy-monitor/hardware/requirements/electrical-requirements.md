# Electrical requirements — DCM-HW-V1

**Status: proposed, not verified against hardware.** Nothing in this document has
been measured. Each requirement is marked either **[verified]**, meaning it has
been checked against a datasheet or by a script in this repository, or
**[proposed]**, meaning it is a design intention that the bench will have to
confirm.

## Design envelope

| Quantity | Value | Status | Basis |
|---|---|---|---|
| Nominal input | 12 V DC | proposed | bench supply, supervised |
| Input range | 5–12 V DC | proposed | design envelope |
| Maximum input | 12 V DC | proposed | chosen, not measured |
| Design current | 0–0.5 A | proposed | first bench tests |
| Maximum measurable current | 0.8192 A | **verified** | INA226 ±81.92 mV full scale ÷ 0.1 Ω shunt |
| Load | resistive, low voltage | proposed | bench resistors |
| Supply | current-limited bench supply, ≤ 1 A limit | proposed | safety boundary |

## Requirements

| ID | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| E1 | Measure DC bus voltage at the load | Sensor bus reading within ±1 % of a reference meter at three points | proposed |
| E2 | Measure DC current through a shunt | Sensor current within ±2 % of a reference meter at three points | proposed |
| E3 | Derive instantaneous power | P = V × I from the same sample, no independent assignment | **verified** in firmware core tests |
| E4 | Accumulate energy over elapsed time | Trapezoidal on measured intervals; reference cases in `firmware/test/test_core.cpp` | **verified** in firmware core tests |
| E5 | Report through serial | CSV line at ≥ 1 Hz with timestamp, V, A, W, Wh, status | proposed (never run on a board) |
| E6 | Survive a sensor communication failure | Sample marked, interval not integrated, counter incremented | **verified** in firmware core tests |
| E7 | Protect the input | Series fuse, reverse-polarity diode, transient clamp | **verified** in `design/checks.py` (P1–P4) |
| E8 | Stay inside a low-voltage, supervised boundary | ≤ 24 V DC, ≤ 1 A supply limit, fused | proposed |
| E9 | Keep logic levels compatible | 3.3 V logic on both the MCU and the sensor; no 5 V on the bus | **verified** in `design/checks.py` (L1–L4) |
| E10 | Keep the measurement path clean | Shunt in series, sensor measuring the load side, reverse diode upstream | **verified** in `design/checks.py` (S5, P4, N7) |
| E11 | Allow probing | Test points on VIN, VPROT, VLOAD, GND, SCL | **verified** in `design/checks.py` (N4) |
| E12 | Report energy without inventing it | Gaps > 5 s and invalid samples never integrated | **verified** in firmware core tests |

## Accuracy targets (proposed, not achieved or measured)

| Quantity | Target | Note |
|---|---|---|
| Voltage | ±1 % of reading, 5–12 V | requires calibration against a reference meter |
| Current | ±2 % of reading, 0.05–0.5 A | shunt tolerance 0.5 % plus amplifier offset dominates at low current |
| Energy over 10 min | ±2 % | inherits the power error; no long-term drift claim |

These are targets to test against, not results. The site says "hardware not built"
and this document does not change that.

## Out of scope

- AC or mains measurement, isolation, three-phase, power factor.
- Battery charging, negative current in normal use (the firmware tracks exported
  energy but the V1 design has no source that can absorb it).
- A real-time clock: all timestamps are milliseconds since boot.
- Wireless reporting, data logging to storage, enclosures.
- Any claim about accuracy before a reference-meter comparison exists.
