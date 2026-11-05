---
slug: adc-resolution-quantization
title: ADC resolution, quantization and the reference that decides it
date: 2026-11-05
tags: [embedded systems, measurement, ADC]
description: Where an ADC's numbers come from, what one code is worth, and why the reference and input impedance matter more than the bit count.
---

## The job of an ADC

An analog-to-digital converter maps an input voltage to an integer code. With `N` bits, a converter that spans ground to `VREF` produces `2^N` codes, and one code covers:

$$
VLSB = VREF / 2^N
$$

That single quantity — the *least significant bit* — is the honest headline specification, not the bit count. A 12-bit converter on a 3.3 V reference has a 0.806 mV LSB. The same 12-bit converter on a 1.0 V reference has 0.244 mV. The resolution improved by changing the reference, not the ADC.

## What resolution does not tell you

`VLSB` is the *quantization step*. Real error rarely stops there:

| Error source | What it does | Where to look |
| --- | --- | --- |
| Quantization | ±½ LSB uncertainty when rounding to a code | Inherent to the converter |
| Offset and gain error | Shifts every code, or scales all codes | Datasheet calibration section |
| INL / DNL | Non-uniform code spacing | Datasheet specification table |
| Reference accuracy and drift | Scales every code, and moves it with temperature | Reference datasheet |
| Input source impedance | Sampling capacitor cannot settle | ADC sample-and-hold timing |
| Noise | Blurs several codes together | Layout, grounding, filtering |

A useful rule for a slowly varying signal is that an ideal `N`-bit converter sampling a signal that spans full scale cannot resolve better than about `VREF/2^N`, and a converter using an external reference cannot be more accurate than that reference.

## Worked example: a divided battery voltage

Suppose a 12-bit ADC with a 3.3 V reference reads a 12 V battery through a divider. Choose `R1 = 33 kΩ` and `R2 = 10 kΩ`:

- Divider ratio: `R2 / (R1 + R2) = 10/43 ≈ 0.2326`
- Full-scale input voltage at the ADC: `3.3 / 0.2326 ≈ 14.19 V`
- One LSB in battery volts: `(14.19 V) / 4096 ≈ 3.46 mV`

Two consequences follow immediately.

1. **Source impedance.** The divider's output impedance is `R1‖R2 ≈ 7.67 kΩ`. If the sample-and-hold needs the input stable within half a code, that resistor and the sampling capacitor form an RC time constant that must settle in the sampling window — a large divider makes an accurate reading harder, not easier.
2. **Standing current.** The divider draws `12 V / 43 kΩ ≈ 279 µA` continuously. On a battery-powered node that may be the dominant consumer, which is why some designs switch the divider on only while measuring.

## Reading several codes instead of one

Averaging `M` uncorrelated samples reduces random noise by roughly `√M`, at the cost of time. Oversampling by `4×` buys about one extra bit of resolution in the ideal case; it does **not** correct offset, gain, INL or reference error, and it cannot help if the input is moving during the measurement window.

$$
\text{bits gained} = \tfrac{1}{2}\log_2(M)
$$

This is a model of noise averaging, not a promise about any particular converter.

## A practical checklist

- State the reference: internal, external, and its initial accuracy.
- Convert codes to volts in one place in the firmware, using calibrated constants.
- Check settling: keep source impedance low, or buffer the input.
- Test at two known points (offset and gain) before trusting a curve in between.
- Record the conditions with any published measurement.

An interactive demonstration of quantization is not included here; the arithmetic above is the part that matters first.

## References

- [Texas Instruments, ADC performance characteristics and specifications](https://www.ti.com/lit/an/sbaa327/sbaa327.pdf)
- [Microchip, Understanding ADC parameters](https://ww1.microchip.com/downloads/en/Appnotes/00699b.pdf)
