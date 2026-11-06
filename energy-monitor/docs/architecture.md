# Architecture — Smart DC Energy Monitor, Software Model V1

## Signal path

```
  ┌──────────┐    ┌──────────┐    ┌───────────────┐    ┌──────────────┐    ┌────────────┐
  │ DC source│───▶│   Load   │───▶│ V divider and │───▶│  ADC model   │───▶│  Sampled   │
  │ Voc, Rs  │    │ R or I(t)│    │ shunt amp +   │    │ clamp + round│    │ processing │
  └──────────┘    └──────────┘    │ gain/offset/n │    │ to LSB       │    │ + energy   │
                                  └───────────────┘    └──────────────┘    └────────────┘
                                         ▲                                      │
                                         │                                      ▼
                                  sensing parameters                    CSV / dashboard
```

Two paths run in parallel at every sample: the **true** operating point (solved
from the source and load) and the **reported** value (after the sensing chain).
They are never allowed to collapse into one another in the interface.

## Module structure

```
energy-monitor/
  model/dcem.js          the whole model, dependency-free, UMD wrapper
  tests/
    dcem-reference.test.js      cases A–G against hand-derived values
    dcem-independent.test.js    ten groups against independent constructions
    energy-monitor-page.test.js checks the built page against the model
  examples/
    generate.js                 writes the reference datasets
    *.csv                       shipped datasets with metadata headers
  docs/
    model.md requirements.md architecture.md limitations.md
    hardware-plan.md reproduce.md
```

`assets/energy-dashboard.js` is presentation only: it builds a configuration
from the controls, feeds the sampler and draws charts. It contains no physics.

## Processing pipeline (as an embedded loop would have it)

1. **Acquire** — at each sample instant, solve the operating point and read both channels.
2. **Timestamp** — the sample carries its simulated time; non-increasing times are rejected.
3. **Convert** — reconstruct engineering units from the ADC code, optionally applying per-channel calibration.
4. **Filter** — optional first-order low-pass, off by default because it changes reference results.
5. **Compute power** — `V_meas · I_meas`, and `V_true · I_true` alongside.
6. **Accumulate energy** — trapezoidal rule over the actual interval, split at sign changes.
7. **Log** — the running record is the exported CSV; rejected samples are counted.
8. **Invalid data** — classified, counted, never integrated.

## State that the interface manages

| State | Meaning |
|---|---|
| `Ready` | configuration loaded, accumulator empty |
| `Running` | simulated time advances on requestAnimationFrame |
| `Paused` | no time advance, no samples; resume continues the same run |
| `Complete` | duration reached; restart begins a new run |

A reset clears samples, accumulators and the clock. Changing the load model or
the calibration starts a new run, so energy from an unrelated configuration can
never appear in a later total.
