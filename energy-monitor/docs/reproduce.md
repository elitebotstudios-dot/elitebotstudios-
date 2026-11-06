# Reproducing the results

Everything below runs with Node.js and no packages. The browser is not needed.

## 1. Run the reference cases

```bash
node energy-monitor/tests/dcem-reference.test.js
```

Prints a table of every check with input, expected value, actual value, tolerance
and PASS/FAIL, followed by:

```
PASS: DCEM reference cases A–G — 67 assertions across constant load, step load,
zero current, variable sampling, measurement error, calibration and invalid data
```

## 2. Run the independent verification

```bash
node energy-monitor/tests/dcem-independent.test.js
```

```
PASS: DCEM independent verification — 594 checks across ten groups (second
integrator, closed form, electrical consistency, additivity, quantisation, noise
statistics, determinism, export, warnings, presets)
```

## 3. Regenerate the reference datasets

```bash
node energy-monitor/examples/generate.js
```

Writes the six CSV files in `energy-monitor/examples/` and prints the energy each
one contains next to the value written in its metadata header.

## 4. Check one number by hand

`reference-case-e-irregular.csv` contains six rows:

| t (s) | P (W) |
|---|---|
| 0.00 | 10 |
| 0.37 | 12 |
| 1.20 | 7 |
| 2.05 | 15 |
| 3.90 | 9 |
| 7.31 | 11 |

```
½(10+12)(0.37) + ½(12+7)(0.83) + ½(7+15)(0.85) + ½(15+9)(1.85) + ½(9+11)(3.41)
= 4.07 + 7.885 + 9.35 + 22.2 + 34.1
= 77.605 J
```

which is what `integrateSeries` returns and what the dataset header records.

## 5. Run the browser suite (optional)

```bash
npm install --prefix /tmp/qa playwright
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw /tmp/qa/node_modules/.bin/playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw node visual-qa/energy-monitor-qa.js
```

The suite drives the real instrument: start, pause, resume, reset, scenario
loading, chart rendering, point inspection, CSV export, mobile tabs, and a
comparison of the displayed energy against the model run independently in Node.

## 6. Expected failure modes

If you change the model, the reference suite should fail loudly rather than
silently pass: the tolerances are absolute and small (1e-9 for exact quantities).
If a reference case stops failing after you change the integration rule, that is
a sign the test is no longer checking what it claims.
