# Limitations — Smart DC Energy Monitor, Software Model V1

This list exists so that no reader has to guess what the model does not cover.

## What this software does not establish

- **No hardware accuracy.** No sensor, ADC, microcontroller or board was used.
  Nothing here predicts the accuracy of a real implementation, and no number in
  this repository is a measurement.
- **No AC, no mains, no isolation.** The model is DC only, at low voltage, with
  a single non-isolated measurement path.
- **No switched-mode behaviour.** Loads are modelled as smooth resistance or
  current demands; switching ripple, inrush and fast transients are outside the
  model. A load that changes faster than the sample interval is aliased, exactly
  as in real firmware.
- **No thermal or ageing effects.** Gain, offset and noise are constants.
- **No ADC non-idealities.** Quantisation is ideal uniform rounding: no INL,
  DNL, missing codes, aperture jitter or reference drift.
- **No MCU behaviour.** No fixed-point arithmetic, no timer jitter, no interrupt
  latency, no watchdog or brown-out behaviour.
- **No filtering design.** The optional low-pass is a single coefficient, chosen
  by the user; no anti-alias filter, no loop response, no settling analysis.

## What the numbers do and do not mean

- The trapezoidal energy estimate is exact for constant power and second-order
  accurate for smooth power. For a step it is wrong by the amount quantified in
  reference case C (0.0093 % for a 1 s sample interval).
- The noise generator is seeded and checked statistically. That validates the
  simulation, not any sensor.
- Quantisation bias in a product of two quantised quantities is real and is
  reproduced by the model (the `preset-constant-load` dataset shows +0.07 % from
  the ideal 3600 J), but its magnitude depends entirely on the sensing chain
  parameters the user enters.

## What would change the conclusions

A reference-meter comparison at several operating points, with the instrument,
wiring, load and ambient conditions recorded, is the only thing that could turn
this software into an accuracy claim. That is stage 7 of the hardware plan and
it has not been started.
