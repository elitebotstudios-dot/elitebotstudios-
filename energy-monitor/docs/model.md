# Smart DC Energy Monitor — model documentation

**Software Model V1 · `dcem.js` 1.0.0**
Elite Bot Studios · Project 01 · status: software verified against reference cases, hardware not built.

This document describes exactly what the model computes. It is written so that a
reader can reproduce any published number without opening the dashboard.

---

## 1. Scope

The model simulates a low-voltage DC energy-monitoring channel:

```
DC source → electrical load → voltage/current sensing → ADC → sampled processing → energy
```

It is a **software model**. No sensor, converter, microcontroller or board is
modelled from measured data, and no number in this repository is a measurement
of a physical circuit.

Default ranges (simulation defaults, not ratings): 5–12 V DC, 0–2 A, up to
48 V and 5 A on the sliders for exploration. The model does not address mains
voltages, AC, isolation or grid measurement.

---

## 2. Units and data types

| Quantity | Unit | Representation |
|---|---|---|
| Time | s | IEEE-754 double, monotonic, rejected if non-increasing |
| Voltage | V | double |
| Current | A | double, non-negative at the load (see §6) |
| Resistance | Ω | double > 0 |
| Power | W | double, `V × I` |
| Energy | J, Wh | double accumulators; 1 Wh = 3600 J exactly |
| ADC code | integer | 0 … 2^bits − 1 |

All arithmetic is double precision. No fixed-point behaviour of a real MCU is
simulated, so quantisation comes only from the ADC model.

---

## 3. Source and load

Open-circuit voltage `Voc(t)` and a series resistance `Rs`. The load demands
either a resistance `R` or a current `I`.

**Resistive load** — the current is *not* chosen, it follows:

```
I = Voc / (Rs + R)        V = I·R        P = V·I = Voc²·R / (Rs + R)²
```

**Current load** — the terminal voltage follows the demand:

```
V = Voc − I·Rs            P = V·I
```

In both cases the source delivers `Voc·I = P + I²·Rs`, so the load power plus
the source's internal loss equals the power drawn from the source. This is
asserted in `dcem-independent.test.js` for three resistive cases.

Load models: `resistive`, `current`, `step` (right-continuous), `duty` (phase =
`t mod period`), `sequence` (right-continuous piecewise constant). Source
models: `constant`, `step`, `ripple` (deterministic sine), `profile`.

---

## 4. Sensing and ADC chain

Per channel, in this order:

```
pin = value · S · (1 + g) + Vos + n        (n ~ N(0, σ²), deterministic seed)
pin = clamp(pin, 0, Vref)                  (saturation flag if clamped)
code = round(pin / q),  q = Vref / 2^bits
pin' = code · q
reported = pin' / S                        (uncalibrated)
reported = (pin' − Vos_est) / (S · (1 + g_est))   (calibrated)
```

- `S` is the channel sensitivity: V per V for the divider channel, V per A for
  the shunt-amplifier channel.
- Calibration is **per channel**, because a divider and a shunt amplifier have
  independent tolerances.
- `adcBits = 0` means "no ADC": an ideal transducer with no input range. The
  reference cases use this to isolate the energy arithmetic from the sensing
  chain.
- Saturation is reported, not hidden: the clipped value is used and counted.

The gain, offset and noise numbers in the presets are illustrative. They are
**not** datasheet values for a specific part.

---

## 5. Power and energy

Instantaneous power is computed from the reported (measured) voltage and current,
and separately from the simulated truth:

```
P_meas = V_meas · I_meas          P_true = V_true · I_true
```

Energy is accumulated with the trapezoidal rule over the **actual** interval
between accepted samples:

```
E_import += ½(P_prev + P_now)·Δt      when both endpoint powers are ≥ 0
E_export += ½(|P_prev| + |P_now|)·Δt  when both are ≤ 0
sign change inside an interval: split at the zero crossing by linear
interpolation, then integrate each part
E_net = E_import − E_export           E_Wh = E_net / 3600
```

Why trapezoidal: it is exact for constant power, and for piecewise-linear power
it approximates the integral with an error proportional to Δt². For a step
straddling an interval it smears the step across that interval; reference case C
measures that error at 2.5 J in 27 000 J (0.0093 %). A finer sample interval
halves the smear.

Why actual intervals: the model never assumes uniform spacing. `integrateSeries`
takes whatever timestamps it is given, and the sampler uses `t - t_prev`. The
independent tests integrate a constant 18 W profile at deliberately irregular
timestamps and require the result to equal `P·(t_end − t_start)` to 1e-9 J.

A rectangular rule is deliberately not offered as a "simpler" alternative: it
would introduce a first-order bias that is easy to mistake for a real effect.

---

## 6. Sign convention and errors

Positive current flows into the load. Imported and exported energy are tracked
separately; a net figure is shown, but the two components are always available
(`importWh`, `exportWh`). The current channel clamps a negative true current to
zero before sensing, because this version models non-negative consumption only.

Invalid data is classified, never integrated:

| Code | Meaning |
|---|---|
| `NON_NUMERIC_TIMESTAMP` | missing or non-numeric `t` |
| `DUPLICATE_TIMESTAMP` | `t` equal to the previous accepted sample |
| `NON_MONOTONIC_TIMESTAMP` | `t` earlier than the previous accepted sample |
| `NEGATIVE_INTERVAL` | non-positive `Δt` at integration time |
| `NON_FINITE_OPERATING_POINT` | NaN/Inf from the source-load solve |
| `OUT_OF_RANGE` | \|value\| > 1e6 |
| `NON_FINITE_POWER`, `POWER_OUT_OF_RANGE`, `TIMESTAMP_OUT_OF_RANGE` | per-series validation |
| `EMPTY_SERIES`, `NOT_A_SERIES` | nothing to integrate |

`validateSeries` returns the full list; `integrateSeries` refuses to return a
number when the input is invalid, returning `energyJ: null` with the issues.

---

## 7. Noise model

Gaussian noise from a seeded mulberry32 PRNG plus a Box–Muller transform. The
same seed replays the same sequence, which is what makes the reference datasets
reproducible. The generator is checked statistically in the independent tests
(unit standard deviation within 2 %, zero mean within 0.02).

This is a **simulation noise source**, not a characterisation of any sensor, and
nothing here predicts the noise of real hardware.

---

## 8. Determinism

Every configuration includes `noiseSeed`. Two runs of the same configuration
produce bit-identical sample arrays and energies. All seven shipped presets are
run twice in the test suite and compared.

---

## 9. Test coverage

| Suite | Contents |
|---|---|
| `dcem-reference.test.js` | cases A–G, 67 assertions, printed as a table with tolerances |
| `dcem-independent.test.js` | 10 groups, 594 assertions: a second integrator over 500 random series, closed-form sine integral with a convergence-order check, Ohm's law and Kirchhoff balance for the load models, additivity across consecutive runs, quantisation bounds and bit-depth behaviour, noise statistics, determinism, CSV round-trip, configuration warnings, and every preset |

The two suites fail differently: the reference file asserts hand-derived values,
and the independent file compares the model against a different construction. A
model error that is consistent with itself survives the first and fails the
second.

---

## 10. What is not modelled

See `limitations.md`. In short: no switch-mode behaviour, no AC or mains, no
isolation, no thermal effects, no input capacitance, no load transients faster
than the sample interval, no ADC INL/DNL or reference drift, no MCU timing or
fixed-point effects. No accuracy claim about hardware follows from any of this.
