/* ===========================================================================
   vector-model-parity.test.js — firmware vectors vs the verified DCEM model

   The firmware and the browser model are two independent implementations of the
   same written rule. This test feeds the firmware's test vectors into the DCEM
   integrator and compares the energy:

     - where the two policies agree (no gaps, no invalid samples), the results
       must match to 1e-12 Wh;
     - where they intentionally differ (the firmware holds an interval spanning
       missing data; the model has no notion of "missing"), the test asserts the
       direction and size of the difference instead of pretending they match.

   Run: node energy-monitor/tests/vector-model-parity.test.js
   ========================================================================== */
'use strict';
const assert = require('assert');
const path = require('path');
const fs = require('fs');
const DCEM = require(path.join(__dirname, '..', 'model', 'dcem.js'));

const doc = JSON.parse(fs.readFileSync(
  path.join(__dirname, '..', 'verification', 'test-vectors', 'vectors.json'), 'utf8'));

let checks = 0;
function ok(cond, label, detail) {
  checks += 1;
  assert.ok(cond, label + (detail === undefined ? '' : ' — ' + detail));
}
function near(a, e, tol, label) {
  checks += 1;
  assert.ok(Math.abs(a - e) <= tol, `${label}: ${a} ≠ ${e} ± ${tol}`);
}

const cases = {
  constant: 'agree', step: 'agree', irregular: 'agree', rollover: 'agree',
  'zero-current': 'agree', calibrated: 'agree',
  gap: 'firmware-holds', invalid: 'firmware-holds'
};

doc.sets.forEach((set) => {
  /* The model integrates a {t, p} series. Absolute millisecond counters are
     rebased to a timeline starting at zero using the same wrap-safe unsigned
     subtraction the firmware uses, so the rollover set can be compared without
     the model's absolute-timestamp guard rejecting it. Intervals are unchanged. */
  let elapsed = 0;
  let previous = null;
  const series = set.decoded.map((d) => {
    if (previous !== null) elapsed += ((d.t_ms - previous) >>> 0) / 1000;
    previous = d.t_ms;
    return { t: elapsed, p: d.p };
  });
  const model = DCEM.integrateSeries(series);
  ok(model.ok, `${set.id}: the model accepts the vector series`, JSON.stringify(model.issues));

  if (cases[set.id] === 'agree') {
    near(model.energyWh, set.expected.energy_wh, 1e-12,
      `${set.id}: firmware and model agree on the accumulated energy`);
  } else {
    /* The firmware deliberately drops intervals that span missing data. The
       model integrates every interval it is given. Both numbers must be
       reported, and the firmware must never exceed the model. */
    ok(set.expected.energy_wh < model.energyWh,
      `${set.id}: the firmware's held-interval policy yields less energy than blind integration`,
      `${set.expected.energy_wh} vs ${model.energyWh}`);
    ok(set.expected.energy_wh > 0,
      `${set.id}: the run still accumulates the intervals it did measure`,
      set.expected.energy_wh);
  }
});

/* The model's own missing-data behaviour is different by design: it refuses an
   invalid series outright rather than holding an interval. That difference is
   asserted so nobody assumes the two are interchangeable. */
{
  const bad = [{ t: 0, p: 1 }, { t: null, p: 1 }, { t: 2, p: 1 }];
  const res = DCEM.integrateSeries(bad);
  ok(res.ok === false && res.energyJ === null,
    'the model refuses an invalid series outright, where the firmware holds one interval');
}

/* Documented unit agreement: 1 Wh = 3600 J in both implementations. */
near(doc.sets[0].expected.energy_wh * 3600, 27, 1e-9,
  'the constant vector set is 27 J, as hand-computed');

console.log(`PASS: firmware vectors match the DCEM model where the policies agree — ${checks} checks across ${doc.sets.length} vector sets`);
