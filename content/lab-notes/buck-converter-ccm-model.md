---
slug: buck-converter-ccm-model
title: A buck converter in continuous conduction mode
date: 2026-11-05
tags: [power electronics, DC-DC, simulation]
description: Derive ideal CCM duty and inductor ripple, estimate the CCM boundary, and separate model output from real converter behavior.
---

## Two switch states, one inductor

An ideal buck converter transfers energy through an inductor while the switch alternates between two states. During the **on** interval, the inductor sees `Vin − Vout`; during the **off** interval in the ideal freewheel path, it sees `−Vout`. Inductor current ramps up and down rather than changing instantaneously.

In steady-state **continuous conduction mode (CCM)**, volt-second balance across the inductor gives the familiar ideal conversion relation:

$$
D ≈ Vout / Vin
$$

This relationship assumes ideal switches and steady-state CCM. It is not a universal duty command for a physical converter. Switch and diode drops, winding resistance, dead time, control limits, and the selected controller change the real requirement. A single efficiency percentage does not specify those losses or provide a general duty-cycle correction.

## Inductor ripple from the slopes

The on-state current rise is the on-state voltage divided by inductance, multiplied by on-time. With `T = 1/fsw` and `ton = D·T`:

$$
ΔIL = (Vin − Vout)·D / (L·fsw) = Vout·(1 − D) / (L·fsw)   [ideal CCM]
$$

The two expressions agree when `D = Vout/Vin`. The average inductor current equals the load current in the ideal steady-state model, so the ripple-centered peak and valley estimates are:

$$
IL,peak ≈ Iout + ΔIL/2,     IL,valley ≈ Iout − ΔIL/2
$$

CCM requires a nonnegative valley current. Setting the valley to zero gives the ideal boundary inductance:

$$
Lcrit ≈ Vout·(1 − D) / (2·fsw·Iout)
$$

Below this load boundary, a diode-based buck's inductor current reaches zero for part of the cycle. In DCM, the ideal conversion ratio depends on load and inductance as well as input/output voltage; the simple CCM duty relation is no longer the complete model.

## Worked ideal CCM estimate

Consider an illustrative operating point: `Vin = 12 V`, `Vout = 5 V`, `fsw = 500 kHz`, `L = 22 µH`, and `Iout = 2 A`.

- Ideal CCM duty: `5/12 ≈ 41.7%`.
- Inductor ripple: approximately `0.265 A peak-to-peak`.
- CCM-model peak and valley: approximately `2.133 A` and `1.867 A`.
- Critical inductance at this load: approximately `1.46 µH`, below the illustrative `22 µH`.

These are **calculated model outputs**, not measured results. They omit switch and diode drops, inductor DCR, core loss, capacitor ESR, layout parasitics, control-loop dynamics, temperature, and transient behavior. The actual duty and waveforms depend on the chosen controller and hardware.

## Efficiency belongs in the power estimate

If a designer supplies an efficiency assumption `η`, it can estimate input power from output power:

$$
Pin ≈ Vout·Iout/η,     Ploss ≈ Pin − Vout·Iout
$$

That is a power-budget estimate. It is **not** a universal correction to `D = Vout/Vin`. Real duty depends on the individual loss mechanisms and the control loop.

## Explore the model

Use the [interactive buck-converter explorer](/tools/buck-converter.html) to vary the ideal CCM inputs and view a live PWM timing diagram and inductor-current ramp. When the valley-current condition is not met, the plot explicitly stops claiming a CCM waveform; the tool does not solve DCM.

## References

- [Texas Instruments, Basic Buck Topology (SLVA257A)](https://www.ti.com/lit/an/slva257a/slva257a.pdf)
- [Texas Instruments, LMR516xx buck converter datasheet](https://www.ti.com/lit/ds/symlink/lmr51606.pdf)
