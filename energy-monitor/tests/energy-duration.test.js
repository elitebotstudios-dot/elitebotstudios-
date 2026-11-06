/* ===========================================================================
   energy-duration.test.js — the duration question, settled independently

   WHY THIS FILE EXISTS
   A previous report described the "constant" firmware vector set as
   "12 V, 0.25 A, 1 s → 0.0075 Wh". Those three numbers cannot all be true:
   3 W for 1 s is 3 J = 0.000833 Wh, not 0.0075 Wh. Either the duration was
   misdescribed, the timestamps were wrong, or the integration was wrong.

   What the evidence shows (printed by this file):
     - the vector set has ten samples at 0, 1000 … 9000 ms;
     - the first and last timestamps differ by 9000 ms, i.e. nine intervals;
     - the power is exactly 3.000 W;
     - 3 W × 9 s = 27 J = 0.0075 Wh, which is what the code produces.

   So the calculation was correct and the *description* was wrong. This file
   asserts all five cases the review asked for, with values derived by hand,
   against both implementations (the firmware policy and the JavaScript model),
   so the duration can never drift out of agreement with the energy again.

   Run: node energy-monitor/tests/energy-duration.test.js
   ========================================================================== */
'use strict';
const assert = require('assert');
const path = require('path');
const fs = require('fs');

const DCEM = require(path.join(__dirname, '..', 'model', 'dcem.js'));
const VECTORS_PATH = path.join(__dirname, '..', 'verification', 'test-vectors', 'vectors.json');

let checks = 0;
function ok(cond, label, detail) {
  checks += 1;
  assert.ok(cond, label + (detail === undefined ? '' : ' — ' + detail));
}
function near(a, e, tol, label) {
  checks += 1;
  const d = Math.abs(a - e);
  assert.ok(d <= tol, `${label}: got ${a}, expected ${e} ± ${tol} (Δ ${d})`);
}

const WH_PER_J = 1 / 3600;

/* ---------------------------------------------------------------------------
   The firmware policy, re-implemented here from its written specification so
   this file does not depend on the C++ build. (The C++ integrator is covered
   separately in firmware/test/test_core.cpp.)
   --------------------------------------------------------------------------*/
function firmwarePolicy(samples, maxGapMs = 5000) {
  let prev = null, importJ = 0, exportJ = 0, integrated = 0, held = 0, gaps = 0;
  for (const s of samples) {
    const valid = s.valid !== false;
    if (!prev) { prev = { ...s, valid }; continue; }
    const dt = (s.t_ms - prev.t_ms) >>> 0;
    if (dt === 0) { held++; prev = { ...s, valid }; continue; }
    if (!valid || !prev.valid) { held++; prev = { ...s, valid }; continue; }
    if (dt > maxGapMs) { held++; gaps++; prev = { ...s, valid }; continue; }
    const j = 0.5 * (prev.p + s.p) * (dt / 1000);
    if (j >= 0) importJ += j; else exportJ -= j;
    integrated++;
    prev = { ...s, valid };
  }
  return { energyJ: importJ - exportJ, energyWh: (importJ - exportJ) * WH_PER_J, integrated, held, gaps };
}

/** Build a constant-power series at a fixed interval, as the firmware would see it. */
function constantSeries(powerW, durationS, intervalS) {
  const out = [];
  const n = Math.round(durationS / intervalS);
  for (let k = 0; k <= n; k += 1) out.push({ t_ms: k * intervalS * 1000, p: powerW });
  return out;
}

function modelEnergy(samples) {
  /* The model takes {t, p} in seconds. Timestamps here start at zero and are
        strictly increasing, so no rebasing is needed for cases A–C. */
  const res = DCEM.integrateSeries(samples.map((s) => ({ t: s.t_ms / 1000, p: s.p })));
  assert.ok(res.ok, 'the model accepts the series');
  return res.energyJ;
}

console.log('\n  Energy duration cases — hand-derived expectations\n');

/* =========================================================================
   CASE A — 12 V, 0.25 A, 1 second
     P = 12 × 0.25 = 3 W
     E = 3 W × 1 s = 3 J
     E = 3 / 3600 = 0.000833333… Wh
   ========================================================================== */
{
  const series = constantSeries(3, 1, 1);            // samples at 0 ms and 1000 ms
  ok(series.length === 2, 'A: one second at a 1 s interval is two samples', series.length);
  const fw = firmwarePolicy(series);
  near(fw.energyJ, 3, 1e-12, 'A: firmware policy gives 3 J for 1 s at 3 W');
  near(fw.energyWh, 3 / 3600, 1e-15, 'A: firmware policy gives 0.000833 Wh');
  near(fw.energyWh, 0.000833333333333, 1e-15, 'A: matches 0.000833333… Wh to 15 digits');
  near(modelEnergy(series), 3, 1e-12, 'A: the JavaScript model also gives 3 J');
  ok(Math.abs(fw.energyWh - 0.0075) > 0.001,
    'A: 1 second is emphatically NOT 0.0075 Wh — that is nine times too much');
}

/* =========================================================================
   CASE B — 12 V, 0.25 A, 9 seconds
     E = 3 W × 9 s = 27 J = 27 / 3600 = 0.0075 Wh exactly
   ========================================================================== */
{
  const series = constantSeries(3, 9, 1);            // samples at 0 … 9000 ms
  ok(series.length === 10, 'B: nine seconds at a 1 s interval is ten samples', series.length);
  const fw = firmwarePolicy(series);
  near(fw.energyJ, 27, 1e-12, 'B: firmware policy gives 27 J for 9 s at 3 W');
  near(fw.energyWh, 0.0075, 1e-15, 'B: firmware policy gives 0.0075 Wh');
  near(modelEnergy(series), 27, 1e-12, 'B: the JavaScript model also gives 27 J');
  ok(27 * WH_PER_J === 0.0075, 'B: 27 J is exactly 0.0075 Wh');

  /* And this is the published vector set: prove it is the same fixture. */
  const doc = JSON.parse(fs.readFileSync(VECTORS_PATH, 'utf8'));
  const set = doc.sets.find((s) => s.id === 'constant');
  ok(set !== undefined, 'B: the published "constant" vector set exists');
  ok(set.samples.length === 10, 'B: the published set has ten samples', set.samples.length);
  const span = (set.samples[set.samples.length - 1].t_ms - set.samples[0].t_ms) / 1000;
  near(span, 9, 0, 'B: the published set spans 9 s, not 1 s');
  ok(set.samples[0].t_ms === 0 && set.samples[1].t_ms === 1000,
    'B: its first interval is 1 s, which is where the confusion came from',
    `${set.samples[0].t_ms} → ${set.samples[1].t_ms} ms`);
  near(set.expected.energy_wh, 0.0075, 1e-15, 'B: its published expected energy is 0.0075 Wh');
  /* the description must state both the interval and the duration */
  ok(/every 1 s|one second apart|1 s sampling/i.test(set.description),
    'B: the description states the sample interval', set.description);
  ok(/9 s|nine seconds|9000 ms/.test(set.description),
    'B: the description states the nine-second duration', set.description);
  ok(!/^12 V, 0\.25 A, 1 s/.test(set.description),
    'B: the description does not lead with a bare "1 s" that could be read as a duration');
}

/* =========================================================================
   CASE C — 12 V, 0.25 A, 3600 seconds (one hour)
     E = 3 W × 3600 s = 10 800 J = 10 800 / 3600 = 3 Wh exactly
   ========================================================================== */
{
  /* At the firmware's default 1 s-class sampling, one hour of constant 3 W is
     exactly 3 Wh. Constant power makes the trapezoidal rule exact at any
     interval, which is what distinguishes a time-aware integrator from one that
     merely sums samples. */
  {
    const series = constantSeries(3, 3600, 1);
    const fw = firmwarePolicy(series);
    near(fw.energyJ, 10800, 1e-9, 'C: 1 s sampling gives 10 800 J for one hour');
    near(fw.energyWh, 3, 1e-12, 'C: 1 s sampling gives 3 Wh for one hour');
    near(modelEnergy(series), 10800, 1e-9, 'C: the model agrees at 1 s sampling');
  }

  /* A slower sampling rate interacts with the missing-data policy: the firmware
     treats any interval longer than max_gap_ms (default 5000 ms) as missing
     data. So at 60 s sampling the default policy discards the whole run — and
     that is the correct, documented behaviour, not a bug. It also means the
     configured sample interval must stay below the gap limit; the firmware now
     reports a configuration warning if it does not. */
  {
    const slow = constantSeries(3, 3600, 60);
    const heldByDefault = firmwarePolicy(slow);
    near(heldByDefault.energyJ, 0, 0,
      'C: at 60 s sampling the default 5 s gap limit holds every interval');
    ok(heldByDefault.held === slow.length - 1,
      'C: every slow interval is counted as held rather than integrated',
      `${heldByDefault.held} of ${slow.length - 1}`);
    const widened = firmwarePolicy(slow, 120000);
    near(widened.energyJ, 10800, 1e-9,
      'C: with the gap limit widened to 120 s the same hour integrates to 10 800 J');
    near(modelEnergy(slow), 10800, 1e-9,
      'C: the model, which has no gap limit, integrates the slow series exactly');
  }
  /* Summing power samples without multiplying by the interval gives a number
     with units of W·samples, not joules. With 1 s sampling it happens to be
     numerically close (10 803), which is exactly why the bug survives casual
     checking; with 0.5 s sampling it is out by a factor of two. */
  const halfSecond = constantSeries(3, 3600, 0.5);
  const naiveHalf = 3 * halfSecond.length;
  near(naiveHalf, 21603, 0, 'C: a naive sample-sum at 0.5 s gives 21 603 "joules"');
  ok(naiveHalf > 1.9 * 10800,
    'C: that is nearly twice the true 10 800 J — the error the time step prevents');
}

/* =========================================================================
   CASE D — irregular timestamps, derived by hand

   Power samples (chosen so the arithmetic is exact in binary floating point):

       t (s)   0.5    1.25    2.75    4.0     6.5
       P (W)   4       4       2       6       3

   Trapezoidal rule, interval by interval:
       ½(4+4)(1.25−0.50) = 4.0000 × 0.75 = 3.0000 J
       ½(4+2)(2.75−1.25) = 3.0000 × 1.50 = 4.5000 J
       ½(2+6)(4.00−2.75) = 4.0000 × 1.25 = 5.0000 J
       ½(6+3)(6.50−4.00) = 4.5000 × 2.50 = 11.2500 J
                                            ────────
                                             23.7500 J
       23.75 / 3600 = 0.006597222222… Wh

   A uniform-spacing estimator would multiply the mean power (3.8 W) by the
   total span (6.0 s) and get 22.8 J — 4 % low. That difference is asserted.
   ========================================================================== */
{
  const series = [
    { t_ms: 500, p: 4 }, { t_ms: 1250, p: 4 }, { t_ms: 2750, p: 2 },
    { t_ms: 4000, p: 6 }, { t_ms: 6500, p: 3 }
  ];
  const fw = firmwarePolicy(series);
  near(fw.energyJ, 23.75, 1e-12, 'D: firmware policy matches the hand total of 23.75 J');
  near(fw.energyWh, 23.75 / 3600, 1e-15, 'D: firmware policy gives 0.006597222 Wh');
  near(modelEnergy(series), 23.75, 1e-12, 'D: the model matches the same hand total');

  const meanPower = (4 + 4 + 2 + 6 + 3) / 5;
  const span = 6.5 - 0.5;
  const uniformEstimate = meanPower * span;
  near(uniformEstimate, 22.8, 1e-12, 'D: the uniform-spacing estimator gives 22.8 J');
  ok(Math.abs(uniformEstimate - 23.75) > 0.9,
    'D: assuming equal spacing is 0.95 J (4 %) wrong on this data');
}

/* =========================================================================
   CASE E — invalid and missing samples must not create energy

   Policy under test:
     - an invalid sample costs the interval that ends at it and the interval
       that starts from it;
     - a gap longer than max_gap_ms is not integrated at all;
     - a first sample that is invalid integrates nothing;
     - a run in which every sample is invalid integrates nothing.
   ========================================================================== */
{
  /* One invalid sample in the middle of a 5 × 1 s constant 3 W run. */
  const withHole = [
    { t_ms: 0, p: 3, valid: true }, { t_ms: 1000, p: 3, valid: true },
    { t_ms: 2000, p: 0, valid: false }, { t_ms: 3000, p: 3, valid: true },
    { t_ms: 4000, p: 3, valid: true }
  ];
  const fw = firmwarePolicy(withHole);
  ok(fw.held === 2, 'E: an invalid sample holds two intervals', fw.held);
  ok(fw.integrated === 2, 'E: only the two clean intervals are integrated', fw.integrated);
  near(fw.energyJ, 6, 1e-12, 'E: 2 × 3 J = 6 J, not the 12 J a blind run would give');
  ok(fw.energyJ < 12, 'E: the invalid interval never becomes energy');

  /* Every sample invalid: no energy at all, and it is counted. */
  const allBad = Array.from({ length: 6 }, (_, k) => ({ t_ms: k * 1000, p: 3, valid: false }));
  const bad = firmwarePolicy(allBad);
  near(bad.energyJ, 0, 0, 'E: a run of invalid samples accumulates exactly zero energy');
  ok(bad.held === 5, 'E: every interval is counted as held', bad.held);
  ok(bad.integrated === 0, 'E: nothing is integrated');

  /* A gap beyond the policy limit is held and counted, not integrated. */
  const gap = [
    { t_ms: 0, p: 3 }, { t_ms: 1000, p: 3 }, { t_ms: 2000, p: 3 },
    { t_ms: 9000, p: 3 }, { t_ms: 10000, p: 3 }
  ];
  const g = firmwarePolicy(gap);
  ok(g.gaps === 1, 'E: the 7 s hole is recorded as one gap', g.gaps);
  /* Three intervals were actually measured: [0,1 s], [1 s,2 s] and [9 s,10 s],
     each 3 J. The 7 s hole contributes nothing. */
  ok(g.integrated === 3, 'E: three intervals were integrated', g.integrated);
  near(g.energyJ, 9, 1e-12, 'E: 3 × 3 J = 9 J, with the 7 s hole contributing zero');

  /* The JavaScript model refuses an invalid series outright rather than
     silently producing a number — a different policy, asserted so the two are
     never assumed interchangeable. */
  const modelRes = DCEM.integrateSeries([{ t: 0, p: 3 }, { t: 1, p: NaN }]);
  ok(modelRes.ok === false && modelRes.energyJ === null,
    'E: the model refuses a non-finite sample instead of returning a plausible total');
}

/* =========================================================================
   Regression: any page that quotes the nine-second energy must also state the
   duration in the same row, and no page may label the set with a bare "1 s".
   ========================================================================== */
{
  const pages = ['projects/dc-energy-monitor-hardware.html', 'projects/smart-energy-monitoring.html'];
  const root = path.resolve(__dirname, '..', '..');
  let rowsChecked = 0;
  pages.forEach((rel) => {
    const file = path.join(root, rel);
    if (!fs.existsSync(file)) return;
    const html = fs.readFileSync(file, 'utf8');
    ok(!/12 V, 0\.25 A, 1 s samples/.test(html),
      `${rel} no longer labels the vector set with only a sample interval`);
    /* find the table row that quotes 27 J / 0.0075 Wh and require the duration */
    const rows = html.split('<tr').filter((r) => r.includes('0.007500000') || r.includes('= 27 J'));
    rows.forEach((row) => {
      rowsChecked += 1;
      ok(/9 s/.test(row), `${rel}: the row quoting 27 J also states the 9 s duration`,
        row.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 120));
    });
  });
  ok(rowsChecked >= 1, 'at least one published row was checked for its duration', rowsChecked);
}

console.log(`\n  A  1 s   → ${(3 / 3600).toFixed(12)} Wh   (3 J)
  B  9 s   → 0.007500000000 Wh   (27 J)
  C  1 h   → 3.000000000000 Wh   (10 800 J)
  D  irregular, hand-derived → 23.75 J = 0.006597222222 Wh
  E  invalid samples → 0 J from the unmeasured intervals\n`);
console.log(`PASS: energy duration cases — ${checks} checks across 1 s, 9 s, 1 hour, irregular and invalid-sample cases, in both implementations`);
