# Requirements — Smart DC Energy Monitor, Software Model V1

Status: **V1 requirements met by the software model.** Hardware requirements are
listed separately and are **not** met, because no hardware exists.

## Purpose

Give the Smart Energy Monitoring project a first artefact that can be inspected,
run, and argued with: a simulation of the measurement chain that shows what an
embedded energy monitor would read, and how far that reading can be from the
truth.

## Functional requirements (software)

| ID | Requirement | Acceptance | Status |
|---|---|---|---|
| S1 | Model a DC source with optional series resistance | Terminal voltage follows `Voc − I·Rs`; resistive and current loads solve consistently | Met |
| S2 | Five load models: resistance, current, step, duty cycle, sequence | Each produces the documented operating point; steps are right-continuous | Met |
| S3 | Configurable sensing chain per channel: sensitivity, gain error, offset, noise, ADC bits, reference | Reported value reproducible by the documented equation | Met |
| S4 | Quantisation with a stated LSB and saturation reporting | Measured values on the LSB grid; half-LSB bound; clipping counted | Met |
| S5 | Per-channel calibration | With the true error terms, calibration recovers the true value exactly (no noise, no quantisation) | Met |
| S6 | Sample acquisition with timestamps, rejection of invalid samples | Duplicate, non-monotonic, non-numeric and out-of-range samples classified and refused | Met |
| S7 | Power from measured voltage and current, and separately from the truth | Both reported side by side at all times | Met |
| S8 | Energy by trapezoidal integration on actual intervals | Cases A, B, C, E reproduce their hand-computed values | Met |
| S9 | Separate imported and exported energy | Net, import and export reported | Met |
| S10 | CSV export with the documented column set | Round-trip within 1e-6; metadata as comment lines | Met |
| S11 | Deterministic runs | Same configuration and seed → identical output | Met |
| S12 | Browser instrument: start, pause, resume, reset, scenario load, point inspection | All verified by `visual-qa/energy-monitor-qa.js` | Met |
| S13 | No simulation data leaves the device unless the user exports it | No network calls in the model or the dashboard | Met |

## Non-functional requirements

| ID | Requirement | Acceptance | Status |
|---|---|---|---|
| N1 | Dependency-free model and interface | No runtime libraries; plain files | Met |
| N2 | Reproducible without the UI | Both Node suites run from a clean checkout | Met |
| N3 | Accessible interface | Keyboard operable, labelled controls, text alternatives for charts, no axe violations at 390 px and 1440 px | Met |
| N4 | Honest attribution | AI assistance disclosed on the page, in the repository and in the model header | Met |
| N5 | Mobile usable | No horizontal overflow; charts shown one at a time below 980 px | Met |

## Out of scope for V1

- Any mains-referenced, AC, or isolated measurement.
- Hardware, firmware, PCB, enclosure, calibration against a reference meter.
- RMS or AC power quantities, power factor, harmonics.
- Multi-channel or three-phase measurement.
- Network transport, cloud storage, dashboards on other devices.
- Accuracy claims of any kind about physical hardware.

## Hardware requirements (not started)

Defined in `hardware-plan.md`. None of them is met: no part has been selected or
purchased, no schematic exists, and nothing has been energised.
