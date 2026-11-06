# Smart DC Energy Monitor — Software Model V1

Project 01 of Elite Bot Studios. A simulated low-voltage DC energy-monitoring
system: source, load, sensing chain, ADC quantisation, sampled power and
trapezoidal energy accumulation.

**Status:** software verified against reference cases. **Hardware: not built.**
No sensor, ADC, microcontroller or board has been used, and no number here is a
measurement of a physical circuit.

**Attribution:** written with AI assistance during the construction of this
site. It is published as a software artefact of Elite Bot Studios, not as the
founder's independent engineering design. See `docs/requirements.md` and the
project page for the details of that split.

## Layout

```
model/dcem.js                  the whole model — dependency-free, works in Node and the browser
tests/dcem-reference.test.js   cases A–G with hand-derived expectations
tests/dcem-independent.test.js ten groups against independent constructions
tests/energy-monitor-page.test.js  the built pages must agree with the model
examples/generate.js           regenerates the reference datasets
examples/*.csv                 six datasets with metadata headers
docs/model.md                  equations, units, integration, error model, coverage
docs/requirements.md           what V1 must do and must not claim
docs/architecture.md           signal path and module structure
docs/limitations.md            what the model does not establish
docs/hardware-plan.md          the low-voltage roadmap — not started
docs/reproduce.md              commands and expected output
```

## Run it

```bash
node energy-monitor/tests/dcem-reference.test.js
node energy-monitor/tests/dcem-independent.test.js
node energy-monitor/tests/energy-monitor-page.test.js
node energy-monitor/examples/generate.js
```

No packages, no build step. The browser instrument is
`/projects/dc-energy-monitor.html`, which loads `model/dcem.js` directly.

## What it does not do

No AC, no mains, no isolation, no hardware accuracy, no ADC non-idealities, no
firmware. Loads that change faster than the sample interval are aliased, as they
would be in real firmware. Read `docs/limitations.md` before quoting anything
from this directory.
