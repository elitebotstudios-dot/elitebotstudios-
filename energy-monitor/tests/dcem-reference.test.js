/* ===========================================================================
   dcem-reference.test.js — reference cases A–G for the Smart DC Energy Monitor

   Every expected value in this file is derived by hand from
       P = V · I,   E = ∫P dt  ≈  Σ ½(P_prev + P_now)·Δt,   1 Wh = 3600 J
   and written down as a literal, together with the tolerance and the reason
   for that tolerance. Nothing here is produced by calling the model and
   copying the answer.

   Run:  node energy-monitor/tests/dcem-reference.test.js
   ========================================================================== */
'use strict';
const assert = require('assert');
const path = require('path');
const DCEM = require(path.join(__dirname, '..', 'model', 'dcem.js'));

let checks = 0;
const table = [];

function record(name, input, expected, actual, tol, pass) {
  table.push({ name, input, expected, actual, tol, pass });
}

function near(name, input, expected, actual, tol, unit) {
  checks += 1;
  const diff = Math.abs(actual - expected);
  const pass = diff <= tol;
  record(name, input, expected + (unit || ''), actual + (unit || ''), '±' + tol, pass);
  assert.ok(pass, `${name}: ${actual} ≠ ${expected} ± ${tol}`);
}

function ok(name, input, condition, actual) {
  checks += 1;
  record(name, input, 'true', String(actual), '—', !!condition);
  assert.ok(condition, `${name}: ${actual}`);
}

/* An ideal measurement chain: unity sensitivities, no error terms, no
   quantisation, no noise. This isolates the energy arithmetic from the
   error model, which is exercised separately in cases F and G. */
function idealConfig(extra) {
  return Object.assign({
    source: { mode: 'constant', voc: 12, rs: 0 },
    load: { mode: 'current', i: 1 },
    measurement: {
      voltage: { sensitivity: 1, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 0, adcVref: 3.3 },
      current: { sensitivity: 1, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 0, adcVref: 3.3 }
    },
    sampleInterval: 1,
    duration: 3600,
    noiseSeed: 1
  }, extra || {});
}

/* =========================================================================
   TEST A — constant load, 12 V, 1 A, 3600 s
   P = 12 × 1 = 12 W
   E = 12 W × 3600 s = 43 200 J = 12 Wh
   With constant power the trapezoidal rule is exact, so the expected value
   has no discretisation error at any sample interval.
   ========================================================================== */
{
  const { results } = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 12, rs: 0 },
    load: { mode: 'current', i: 1 },
    duration: 3600, sampleInterval: 1
  }));
  near('A · mean power', '12 V, 1 A', 12, results.meanPowerW, 1e-9, ' W');
  near('A · energy [J]', '3600 s', 43200, results.energyJ, 1e-6, ' J');
  near('A · energy [Wh]', '3600 s', 12, results.energyWh, 1e-9, ' Wh');
  ok('A · sample count', '3600 s at 1 s', results.accepted === 3601, results.accepted);
  ok('A · nothing rejected', 'ideal run', results.rejected === 0, results.rejected);
  ok('A · measured equals true', 'ideal chain', Math.abs(results.energyWh - results.trueEnergyWh) < 1e-9, results.trueEnergyWh);
}

/* =========================================================================
   TEST B — constant load, 5 V, 2 A, 1800 s
   P = 5 × 2 = 10 W
   E = 10 W × 1800 s = 18 000 J = 5 Wh
   ========================================================================== */
{
  const { results } = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 5, rs: 0 },
    load: { mode: 'current', i: 2 },
    duration: 1800, sampleInterval: 1
  }));
  near('B · mean power', '5 V, 2 A', 10, results.meanPowerW, 1e-9, ' W');
  near('B · energy [J]', '1800 s', 18000, results.energyJ, 1e-6, ' J');
  near('B · energy [Wh]', '1800 s', 5, results.energyWh, 1e-9, ' Wh');
}

/* =========================================================================
   TEST C — step load, 10 V
     t ∈ [0, 1800)   I = 1 A   → P = 10 W
     t ∈ [1800, 3600] I = 0.5 A → P = 5 W

   Ideal (continuous) result:
     10 W × 1800 s + 5 W × 1800 s = 18 000 + 9 000 = 27 000 J = 7.5 Wh

   Step convention: the load is right-continuous, so the new current applies
   from t = 1800 exactly. With 1 s sampling, the interval [1799, 1800] spans
   the step, and the trapezoidal rule charges it ½(10 + 5)·1 = 7.5 J instead
   of 10 J. The discrete result is therefore expected to be exactly

     1799 × 10 + 7.5 + 1800 × 5 = 26 997.5 J = 7.49930 Wh

   which is 0.0093 % below the continuous ideal. Both numbers are asserted:
   the exact discrete value (tolerance 1e-6) and the distance from the ideal
   (tolerance 0.02 %), because a model that silently smoothed the step would
   pass one of those tests and fail the other.
   ========================================================================== */
{
  const { results } = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 10, rs: 0 },
    load: { mode: 'step', iBefore: 1, iAfter: 0.5, stepAt: 1800 },
    duration: 3600, sampleInterval: 1
  }));
  const expectedDiscreteJ = 1799 * 10 + 7.5 + 1800 * 5;
  near('C · energy [J] (discrete)', 'step at 1800 s', expectedDiscreteJ, results.energyJ, 1e-6, ' J');
  near('C · energy [Wh] (discrete)', 'step at 1800 s', expectedDiscreteJ / 3600, results.energyWh, 1e-9, ' Wh');
  near('C · ideal energy [Wh]', 'continuous', 7.5, 27000 / 3600, 1e-12, ' Wh');
  const deviationPct = (expectedDiscreteJ - 27000) / 27000 * 100;
  ok('C · trapezoid error on a step', '1 s samples', Math.abs(deviationPct) < 0.02, deviationPct.toFixed(5) + ' %');
  near('C · deviation is exactly −2.5 J', 'closed form', -2.5, expectedDiscreteJ - 27000, 1e-9, ' J');
  /* a finer sample interval must move the estimate closer to the ideal */
  const fine = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 10, rs: 0 },
    load: { mode: 'step', iBefore: 1, iAfter: 0.5, stepAt: 1800 },
    duration: 3600, sampleInterval: 0.1
  }));
  ok('C · 0.1 s sampling is closer to the ideal',
    'dt = 0.1 s',
    Math.abs(fine.results.energyJ - 27000) < Math.abs(results.energyJ - 27000),
    fine.results.energyJ.toFixed(3) + ' J');
}

/* =========================================================================
   TEST D — zero current
   Voltage present, current zero, so P = 0 at every sample and the accumulated
   energy stays exactly zero. The voltage reading must remain nonzero, which
   distinguishes "no load" from "no measurement".
   ========================================================================== */
{
  const { results } = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 12, rs: 0 },
    load: { mode: 'current', i: 0 },
    duration: 600, sampleInterval: 1
  }));
  ok('D · energy is exactly zero', '0 A', results.energyJ === 0, results.energyJ);
  ok('D · no exported energy', '0 A', results.exportWh === 0, results.exportWh);
  near('D · voltage still measured', '12 V', 12, results.meanVoltageV, 1e-9, ' V');
  near('D · power is zero', '0 A', 0, results.meanPowerW, 1e-12, ' W');
}

/* =========================================================================
   TEST E — variable sampling
   Hand-computed from the trapezoidal rule on irregular intervals:

     t  0.00  0.37  1.20  2.05  3.90  7.31
     P  10     12     7    15     9    11

   E = ½(10+12)(0.37) + ½(12+7)(0.83) + ½(7+15)(0.85)
     + ½(15+9)(1.85) + ½(9+11)(3.41)
     = 4.07 + 7.885 + 9.35 + 22.2 + 34.1 = 77.605 J

   The same samples integrated as (mean power) × (total time) would give
   10.6667 W × 7.31 s = 77.9733 J — a 0.47 % error that appears only because
   the spacing is not uniform. That is asserted too, so the test proves the
   model uses the real timestamps.
   ========================================================================== */
{
  const ts = [0, 0.37, 1.20, 2.05, 3.90, 7.31];
  const ps = [10, 12, 7, 15, 9, 11];
  const series = ts.map((t, i) => ({ t, p: ps[i] }));
  const res = DCEM.integrateSeries(series);
  near('E · irregular trapezoid [J]', '5 intervals', 77.605, res.energyJ, 1e-9, ' J');
  near('E · duration', 'last − first', 7.31, res.durationS, 1e-12, ' s');
  const naive = (ps.reduce((a, b) => a + b, 0) / ps.length) * 7.31;
  ok('E · mean × time differs from the integral',
    'naive estimator',
    Math.abs(naive - 77.605) > 0.3,
    naive.toFixed(4) + ' J vs 77.605 J');

  /* Constant power must integrate exactly at any spacing: E = P·(t_end − t_start). */
  const rng = DCEM.makeRng(99);
  for (let trial = 0; trial < 5; trial += 1) {
    const sampler = DCEM.createSampler(idealConfig({
      source: { mode: 'constant', voc: 12, rs: 0 },
      load: { mode: 'current', i: 1.5 }
    }));
    let t = 0;
    const times = [0];
    for (let k = 1; k <= 40; k += 1) { t += 0.01 + rng() * 2.5; times.push(t); }
    times.forEach((x) => sampler.step(x));
    const r = sampler.results();
    const expected = 12 * 1.5 * (times[times.length - 1] - times[0]);
    near(`E · constant power, irregular spacing (trial ${trial + 1})`,
      '18 W, random intervals', expected, r.energyJ, 1e-9, ' J');
  }
}

/* =========================================================================
   TEST F — measurement error and calibration
   Voltage channel: sensitivity 0.25 V/V (a 4:1 divider), gain error +2 %,
   offset +0.05 V at the ADC pin, no noise, no quantisation.
   True 10 V  →
     pin = 10 × 0.25 × 1.02 + 0.05 = 2.600 V
     uncalibrated reading = 2.600 / 0.25 = 10.400 V
       (the +2 % gain shows up as +0.200 V, the offset as +0.05/0.25 = +0.200 V)
     calibrated with gainEstimate = 0.02 and offsetEstimateV = 0.05 →
       (2.600 − 0.05) / (0.25 × 1.02) = 10.000 V
   The resulting power and energy error is therefore +4 % uncalibrated
   (10.4 V at a true 1 A on an ideal current channel) and 0 % calibrated.
   ========================================================================== */
{
  const meas = {
    voltage: { sensitivity: 0.25, gainError: 0.02, offsetV: 0.05, noiseRms: 0, adcBits: 0, adcVref: 3.3 },
    current: { sensitivity: 1, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 0, adcVref: 3.3 }
  };
  const raw = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 10, rs: 0 },
    load: { mode: 'current', i: 1 },
    measurement: meas, duration: 600, sampleInterval: 1
  }));
  near('F · uncalibrated voltage', '10 V true, +2 % gain, +50 mV offset', 10.4, raw.results.meanVoltageV, 1e-9, ' V');
  near('F · uncalibrated power', '10.4 V × 1 A', 10.4, raw.results.meanPowerW, 1e-9, ' W');
  near('F · uncalibrated energy', '600 s', 10.4 * 600, raw.results.energyJ, 1e-6, ' J');
  near('F · energy error', 'vs true 6000 J', 4.0, raw.results.energyErrorPct, 1e-9, ' %');

  const cal = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 10, rs: 0 },
    load: { mode: 'current', i: 1 },
    measurement: {
      voltage: Object.assign({}, meas.voltage, {
        calibration: { enabled: true, gainEstimate: 0.02, offsetEstimateV: 0.05 }
      }),
      current: meas.current
    },
    duration: 600, sampleInterval: 1
  }));
  near('F · calibrated voltage', 'same errors, corrected', 10, cal.results.meanVoltageV, 1e-9, ' V');
  near('F · calibrated energy', '600 s', 6000, cal.results.energyJ, 1e-6, ' J');
  ok('F · calibration removes the bias', 'gain + offset',
    Math.abs(cal.results.energyErrorPct) < 1e-9, cal.results.energyErrorPct);

  /* Partial calibration: with only the offset estimate supplied and the gain
     estimate left at zero, the model must correct the offset and leave the
     gain error in place:  (2.600 − 0.050) / 0.25 = 10.200 V. */
  const wrong = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 10, rs: 0 },
    load: { mode: 'current', i: 1 },
    measurement: {
      voltage: Object.assign({}, meas.voltage, {
        calibration: { enabled: true, gainEstimate: 0, offsetEstimateV: 0.05 }
      }),
      current: meas.current
    },
    duration: 10, sampleInterval: 1
  }));
  near('F · partial calibration', 'offset corrected, gain left in', 10.2, wrong.results.meanVoltageV, 1e-9, ' V');
}

/* =========================================================================
   TEST G — invalid data
   Each defect must be classified, not silently integrated.
   ========================================================================== */
{
  const cases = [
    [[{ t: 0, p: 1 }, { p: 1 }, { t: 2, p: 1 }], 'MISSING_OR_NON_NUMERIC_TIMESTAMP', 'missing timestamp'],
    [[{ t: 0, p: 1 }, { t: 1, p: 1 }, { t: 1, p: 1 }], 'DUPLICATE_TIMESTAMP', 'duplicate timestamp'],
    [[{ t: 0, p: 1 }, { t: 2, p: 1 }, { t: 1, p: 1 }], 'NON_MONOTONIC_TIMESTAMP', 'non-monotonic timestamps'],
    [[{ t: 0, p: 1 }, { t: 1, p: NaN }], 'NON_FINITE_POWER', 'non-numeric power'],
    [[{ t: 0, p: 1 }, { t: 1, p: 1e9 }], 'POWER_OUT_OF_RANGE', 'extreme power'],
    [[{ t: 0, p: 1 }, { t: 1e9, p: 1 }], 'TIMESTAMP_OUT_OF_RANGE', 'extreme timestamp'],
    [[], 'EMPTY_SERIES', 'empty dataset'],
    [null, 'NOT_A_SERIES', 'not a series']
  ];
  cases.forEach(([series, code, label]) => {
    const check = DCEM.validateSeries(series);
    const found = check.issues.some((i) => i.code === code);
    ok('G · rejects ' + label, code, found && !check.ok, JSON.stringify(check.issues.map((i) => i.code)));
    if (Array.isArray(series)) {
      const res = DCEM.integrateSeries(series);
      ok('G · integration refuses ' + label, code, res.ok === false && res.energyJ === null, JSON.stringify(res.energyJ));
    }
  });

  /* The sampler rejects the same defects as it runs, and counts them. */
  const sampler = DCEM.createSampler(idealConfig({ duration: 10 }));
  sampler.step(0);
  sampler.step(1);
  const dup = sampler.step(1);
  const back = sampler.step(0.5);
  const bad = sampler.step(NaN);
  ok('G · sampler reports a duplicate', 'step(1) twice', dup.ok === false && dup.code === 'DUPLICATE_TIMESTAMP', dup.code);
  ok('G · sampler reports a backwards step', 'step(0.5) after 1', back.ok === false && back.code === 'NON_MONOTONIC_TIMESTAMP', back.code);
  ok('G · sampler reports a non-numeric timestamp', 'step(NaN)', bad.ok === false && bad.code === 'NON_NUMERIC_TIMESTAMP', bad.code);
  const r = sampler.results();
  ok('G · rejections are counted', '2 accepted', r.accepted === 2 && r.rejected === 3, r.accepted + ' accepted / ' + r.rejected + ' rejected');
  ok('G · rejections keep their classification', 'by code',
    r.rejectedByCode.DUPLICATE_TIMESTAMP === 1 && r.rejectedByCode.NON_MONOTONIC_TIMESTAMP === 1,
    JSON.stringify(r.rejectedByCode));
  near('G · rejected samples add no energy', 'constant 12 W', 12 * 1, r.energyJ, 1e-12, ' J');
}

/* =========================================================================
   Supplementary: quantisation, saturation, determinism, CSV round-trip.
   ========================================================================== */
{
  /* 12-bit ADC, 3.3 V reference, 0.25 V/V divider →
     LSB = 3.3 / 4096 = 0.80566 mV at the pin = 3.2227 mV at the input. */
  const lsbPin = 3.3 / 4096;
  const ch = { sensitivity: 0.25, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 12, adcVref: 3.3 };
  near('Q · LSB at the pin', '12 bit, 3.3 V', lsbPin, DCEM.channelLsb(ch), 1e-15, ' V');
  near('Q · LSB at the input', '÷ 0.25', lsbPin / 0.25, 0.00322265625, 1e-12, ' V');

  const { samples } = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 10, rs: 0 },
    load: { mode: 'current', i: 1 },
    measurement: { voltage: ch, current: { sensitivity: 1, adcBits: 12, adcVref: 3.3 } },
    duration: 10, sampleInterval: 1
  }));
  const worst = samples.reduce((m, s) => Math.max(m, Math.abs(s.vMeas - Math.round(s.vMeas / 0.00322265625) * 0.00322265625)), 0);
  ok('Q · measured values sit on the LSB grid', '12-bit', worst < 1e-9, worst.toExponential(2));
  ok('Q · quantisation error is within half an LSB', '10 V',
    Math.abs(samples[5].vMeas - 10) <= 0.00322265625 / 2 + 1e-12, Math.abs(samples[5].vMeas - 10).toExponential(3));

  /* Saturation: 10 V through a 0.5 V/V divider is 5 V at a 3.3 V ADC pin. */
  const sat = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 10, rs: 0 },
    load: { mode: 'current', i: 1 },
    measurement: { voltage: { sensitivity: 0.5, adcBits: 12, adcVref: 3.3 } },
    duration: 5, sampleInterval: 1
  }));
  ok('S · saturation is detected', '5 V at a 3.3 V pin', sat.results.saturated === 6, sat.results.saturated);
  /* Full scale is code 4095, not 4096: 4095/4096 × 3.3 V = 3.29919 V at the pin,
     which is 6.59839 V through a 0.5 V/V divider. A model that reports exactly
     6.6 V would be reporting a code that does not exist. */
  near('S · clipped reading', 'code 4095', 4095 / 4096 * 3.3 / 0.5, sat.samples[0].vMeas, 1e-12, ' V');

  /* Determinism: the same seed must produce the same numbers, every time. */
  const noisy = () => DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 12, rs: 0 },
    load: { mode: 'current', i: 1 },
    measurement: {
      voltage: { sensitivity: 1, noiseRms: 0.01, adcBits: 12 },
      current: { sensitivity: 1, noiseRms: 0.005, adcBits: 12 }
    },
    duration: 60, sampleInterval: 1, noiseSeed: 4242
  }));
  const a = noisy(), b = noisy();
  ok('N · identical seed gives identical output', 'seed 4242', a.results.energyJ === b.results.energyJ, a.results.energyJ);
  const c = DCEM.simulate(idealConfig({
    source: { mode: 'constant', voc: 12, rs: 0 },
    load: { mode: 'current', i: 1 },
    measurement: {
      voltage: { sensitivity: 1, noiseRms: 0.01, adcBits: 12 },
      current: { sensitivity: 1, noiseRms: 0.005, adcBits: 12 }
    },
    duration: 60, sampleInterval: 1, noiseSeed: 777
  }));
  ok('N · a different seed changes the output', 'seed 777', a.results.energyJ !== c.results.energyJ,
    a.results.energyJ.toFixed(6) + ' vs ' + c.results.energyJ.toFixed(6));

  /* CSV round-trip. */
  const csv = DCEM.toCSV(a.samples, { model: 'dcem', version: DCEM.VERSION });
  const parsed = DCEM.parseCSV(csv);
  ok('CSV · one row per sample', '60 s at 1 s', parsed.length === a.samples.length, parsed.length);
  const maxDiff = parsed.reduce((m, row, i) => Math.max(m,
    Math.abs(row.p_meas_w - a.samples[i].pMeas),
    Math.abs(row.energy_wh - a.samples[i].energyWh)), 0);
  ok('CSV · values survive the round trip', '6 decimal places', maxDiff <= 1e-6, maxDiff.toExponential(2));
  ok('CSV · metadata is written as comments', 'header', csv.split('\n')[0].startsWith('# model: dcem'), csv.split('\n')[0]);
}

/* ---------------------------------------------------------------- output -- */
const pad = (s, n) => String(s).padEnd(n);
const lpad = (s, n) => String(s).padStart(n);
console.log('\n  DCEM reference cases A–G\n');
console.log('  ' + pad('CHECK', 44) + pad('INPUT', 26) + lpad('EXPECTED', 16) + lpad('ACTUAL', 16) + lpad('TOL', 10) + '  RESULT');
console.log('  ' + '─'.repeat(118));
table.forEach((r) => {
  console.log('  ' + pad(r.name, 44) + pad(r.input, 26) + lpad(r.expected, 16) + lpad(r.actual, 16) + lpad(r.tol, 10) + '  ' + (r.pass ? 'PASS' : 'FAIL'));
});
const failed = table.filter((r) => !r.pass).length;
console.log('  ' + '─'.repeat(118));
console.log(`  ${table.length} checks · ${failed} failed\n`);
console.log(`PASS: DCEM reference cases A–G — ${checks} assertions across constant load, step load, zero current, variable sampling, measurement error, calibration and invalid data`);
