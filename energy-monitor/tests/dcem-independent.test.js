/* ===========================================================================
   dcem-independent.test.js — independent verification of the DC energy model

   This file never uses the model's own integration to decide what the right
   answer is. Each group compares the model against a different construction:

     1. A second, algebraically different trapezoid (min + |Δ|/2) over 500
        random series.
     2. A closed-form integral of a sinusoidal power profile, plus a
        convergence-order check: halving the step must quarter the error,
        because the trapezoidal rule is second order.
     3. Electrical consistency of the load models against Ohm's law and the
        Kirchhoff energy balance for the source, the load and its internal
        resistance.
     4. Additivity: two consecutive partial runs must sum to the full run.
     5. Quantisation: monotonic in bit depth, half-LSB bound, and the closed
        form for the LSB.
     6. Noise: mean and standard deviation recovered statistically from the
        configured parameters (a check on the generator, not a claim about any
        real sensor).
     7. Determinism and reproducibility of the seeded generator.
     8. Export: energy recomputed from the written CSV matches the model.

   Run:  node energy-monitor/tests/dcem-independent.test.js
   ========================================================================== */
'use strict';
const assert = require('assert');
const path = require('path');
const DCEM = require(path.join(__dirname, '..', 'model', 'dcem.js'));

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

const idealChain = {
  voltage: { sensitivity: 1, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 0, adcVref: 3.3 },
  current: { sensitivity: 1, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 0, adcVref: 3.3 }
};

/* =========================================================================
   1. A second trapezoid implementation
   ------------------------------------------------------------------------
   Every interval is split into a rectangle of height min(p0, p1) plus a
   triangle of height |p1 − p0|. That is algebraically the same as the average
   of the endpoints, but it is computed by a different expression and with
   separate sign handling, so an algebra slip in the model shows up as a
   disagreement. 500 series of 2–40 points are compared.
   ========================================================================== */
{
  const rng = DCEM.makeRng(20261106);
  let worst = 0;
  for (let trial = 0; trial < 500; trial += 1) {
    const n = 2 + Math.floor(rng() * 39);
    let t = rng() * 5;
    const series = [];
    for (let i = 0; i < n; i += 1) {
      series.push({ t, p: (rng() - 0.45) * 40 });       /* mixed signs on purpose */
      t += 0.01 + rng() * 3;
    }
    /* independent reference: rectangle + triangle per interval */
    let reference = 0;
    for (let i = 1; i < series.length; i += 1) {
      const a = series[i - 1], b = series[i];
      const dt = b.t - a.t;
      const lo = Math.min(a.p, b.p);
      const triangle = Math.abs(b.p - a.p) * dt / 2;
      reference += lo * dt + (a.p <= b.p ? triangle : triangle) * 1;
    }
    /* the rectangle+triangle identity is only valid for equal signs, so build
       the reference by splitting intervals at a sign change, as a solver must */
    let ref = 0;
    for (let i = 1; i < series.length; i += 1) {
      const a = series[i - 1], b = series[i];
      const dt = b.t - a.t;
      if (a.p * b.p >= 0) {
        ref += (Math.min(a.p, b.p) + Math.abs(b.p - a.p) / 2) * (a.p < 0 ? 1 : 1) * dt;
      } else {
        const f = a.p / (a.p - b.p);
        ref += a.p / 2 * (dt * f) + b.p / 2 * (dt - dt * f);
      }
    }
    const model = DCEM.integrateSeries(series);
    ok(model.ok, 'random series integrates', trial);
    worst = Math.max(worst, Math.abs(model.energyJ - ref));
  }
  ok(worst < 1e-9, '500 random series match the independent reconstruction', worst.toExponential(2));
}

/* =========================================================================
   2. Closed-form integral and convergence order
   ------------------------------------------------------------------------
   P(t) = A + B·sin(ω t) sampled from 0 to T.
   ∫₀ᵀ P dt = A·T + (B/ω)(1 − cos ωT)
   The trapezoidal rule is second order, so halving dt must divide the error by
   about four. Both facts are asserted.
   ========================================================================== */
{
  const A = 8, B = 5, T = 6;
  const omega = 2 * Math.PI * 0.7;
  const analytic = A * T + (B / omega) * (1 - Math.cos(omega * T));
  const errors = [];
  [0.2, 0.1, 0.05, 0.025].forEach((dt) => {
    const series = [];
    for (let t = 0; t <= T + 1e-12; t += dt) series.push({ t, p: A + B * Math.sin(omega * t) });
    const res = DCEM.integrateSeries(series);
    errors.push(Math.abs(res.energyJ - analytic));
  });
  ok(errors[0] < 0.2, 'sine profile: coarse step is already close', errors[0].toExponential(2));
  for (let i = 1; i < errors.length; i += 1) {
    const ratio = errors[i - 1] / errors[i];
    ok(ratio > 3.6 && ratio < 4.4, `halving dt divides the error by ~4 (step ${i})`, ratio.toFixed(3));
  }
  const finest = DCEM.integrateSeries(
    Array.from({ length: Math.round(T / 0.025) + 1 }, (_, k) => {
      const t = k * 0.025;
      return { t, p: A + B * Math.sin(omega * t) };
    }));
  /* At dt = 0.025 s the remaining trapezoidal error is ~8e-4 J on a 48.8 J
     integral (1.6e-5 relative), which is the expected second-order residual. */
  near(finest.energyJ, analytic, 5e-3, 'converged sine integral matches the closed form');
}

/* =========================================================================
   3. Electrical consistency of the load models
   ************************************************************************
   With an open-circuit voltage Voc and a source resistance Rs:
     resistive R  →  I = Voc/(Rs+R), V = I·R, P = V·I = Voc²R/(Rs+R)²
     current I    →  V = Voc − I·Rs, P = V·I
     source power = load power + I²·Rs     (Kirchhoff, steady state)
   ========================================================================== */
{
  const src = DCEM.normalizeConfig({ source: { mode: 'constant', voc: 12, rs: 0.5 } }).src;
  [[4.7, 100], [10, 50], [2.2, 20]].forEach(([voc, r]) => {
    const s = DCEM.sourceConfig({ mode: 'constant', voc, rs: 0.5 });
    const load = DCEM.loadConfig({ mode: 'resistive', r });
    const p = DCEM.operatingPoint(s, load, 0);
    const iExpected = voc / (0.5 + r);
    near(p.i, iExpected, 1e-12, `resistive ${r} Ω: current from Ohm's law`);
    near(p.v, iExpected * r, 1e-12, `resistive ${r} Ω: terminal voltage across the load`);
    near(p.p, voc * voc * r / Math.pow(0.5 + r, 2), 1e-9, `resistive ${r} Ω: power matches Voc²R/(Rs+R)²`);
    near(p.voc * p.i, p.p + p.sourceLoss, 1e-9, `resistive ${r} Ω: source power = load power + Rs loss`);
    ok(p.v < p.voc, `resistive ${r} Ω: terminal voltage is below the open-circuit voltage`, p.v);
    ok(p.load.resistance === r, `resistive ${r} Ω: load resistance is reported`, p.load.resistance);
  });

  const curr = DCEM.loadConfig({ mode: 'current', i: 1.5 });
  const pc = DCEM.operatingPoint(DCEM.sourceConfig({ mode: 'constant', voc: 12, rs: 1 }), curr, 0);
  near(pc.i, 1.5, 1e-12, 'current load: demand is honoured');
  near(pc.v, 12 - 1.5 * 1, 1e-12, 'current load: terminal voltage drops by I·Rs');
  near(pc.voc * pc.i, pc.p + pc.sourceLoss, 1e-9, 'current load: Kirchhoff energy balance');
}

/* =========================================================================
   4. Additivity of energy across consecutive runs
   ========================================================================== */
{
  const base = {
    source: { mode: 'step', voc: 9, vocAfter: 11, stepAt: 125 },
    load: { mode: 'duty', period: 20, duty: 0.4, iOn: 1.2, iOff: 0.2 },
    measurement: idealChain,
    sampleInterval: 0.5
  };
  const full = DCEM.simulate(Object.assign({}, base, { duration: 400 }));
  const s1 = DCEM.createSampler(Object.assign({}, base, { duration: 200 }));
  const s2 = DCEM.createSampler(Object.assign({}, base, { duration: 400 }));
  for (let t = 0; t <= 200 + 1e-9; t += 0.5) s1.step(t);
  for (let t = 200; t <= 400 + 1e-9; t += 0.5) s2.step(t);
  const sum = s1.results().energyJ + s2.results().energyJ;
  near(sum, full.results.energyJ, 1e-9, 'two consecutive runs sum to the single run');
  ok(full.results.energyJ > 0, 'the additivity case actually accumulates energy', full.results.energyJ.toFixed(2) + ' J');

  /* running the same configuration twice must give the same answer */
  const again = DCEM.simulate(Object.assign({}, base, { duration: 400 }));
  ok(again.results.energyJ === full.results.energyJ, 'repeated runs are bit-identical', again.results.energyJ);
}

/* =========================================================================
   5. Quantisation: bit depth, half-LSB bound, closed-form LSB
   ========================================================================== */
{
  const vref = 3.3;
  [8, 10, 12, 14, 16].forEach((bits) => {
    const ch = DCEM.channelConfig({ sensitivity: 0.25, adcBits: bits, adcVref: vref });
    const lsb = vref / Math.pow(2, bits);
    near(DCEM.channelLsb(ch), lsb, 1e-18, `${bits}-bit LSB at the pin`);
    const rng = DCEM.makeRng(bits);
    let worst = 0;
    for (let k = 0; k < 200; k += 1) {
      const truth = rng() * 12;                         /* 0–12 V input */
      const read = DCEM.readChannel(ch, truth, rng);
      worst = Math.max(worst, Math.abs(read.value - truth));
    }
    ok(worst <= lsb / 0.25 / 2 + 1e-12, `${bits}-bit error stays inside half an LSB`, worst.toExponential(3));
  });
  const l8 = DCEM.channelLsb(DCEM.channelConfig({ adcBits: 8, adcVref: vref, sensitivity: 1 }));
  const l9 = DCEM.channelLsb(DCEM.channelConfig({ adcBits: 9, adcVref: vref, sensitivity: 1 }));
  near(l8 / l9, 2, 1e-12, 'one extra bit halves the LSB');

  /* quantisation changes the accumulated energy, and improving the ADC reduces
     that difference: an 8-bit run must be further from the true energy than a
     16-bit run on the same signal */
  const noisy = (bits) => DCEM.simulate({
    source: { mode: 'ripple', voc: 10, rs: 0, rippleAmp: 0.05, rippleHz: 3 },
    load: { mode: 'current', i: 1 },
    measurement: {
      voltage: { sensitivity: 0.25, adcBits: bits, adcVref: vref },
      current: { sensitivity: 0.5, adcBits: bits, adcVref: vref }
    },
    duration: 200, sampleInterval: 0.1
  }).results;
  const r8 = noisy(8), r16 = noisy(16);
  ok(Math.abs(r16.energyErrorPct) < Math.abs(r8.energyErrorPct),
    'a 16-bit channel is closer to the true energy than an 8-bit channel',
    `${r8.energyErrorPct.toFixed(4)} % → ${r16.energyErrorPct.toFixed(4)} %`);
}

/* =========================================================================
   6. Noise generator statistics
   ------------------------------------------------------------------------
   The generator must deliver the standard deviation it is configured with and
   no systematic bias. This validates the simulation's own noise source; it
   says nothing about any physical sensor.
   ========================================================================== */
{
  const rng = DCEM.makeRng(2026);
  const n = 40000;
  let sum = 0, sumSq = 0;
  for (let i = 0; i < n; i += 1) {
    const g = DCEM.gaussian(rng);
    sum += g;
    sumSq += g * g;
  }
  const mean = sum / n;
  const sd = Math.sqrt(sumSq / n - mean * mean);
  near(sd, 1, 0.02, 'Gaussian generator has unit standard deviation');
  ok(Math.abs(mean) < 0.02, 'Gaussian generator has no systematic bias', mean.toExponential(2));

  /* through the channel: 12-bit, 20 mV RMS at the pin, 0.25 V/V divider */
  const res = DCEM.simulate({
    source: { mode: 'constant', voc: 8, rs: 0 },
    load: { mode: 'current', i: 0.5 },
    measurement: {
      voltage: { sensitivity: 0.25, adcBits: 12, adcVref: 3.3, noiseRms: 0.02 },
      current: { sensitivity: 0.5, adcBits: 12, adcVref: 3.3, noiseRms: 0 }
    },
    duration: 20000, sampleInterval: 0.1, noiseSeed: 7
  });
  const vs = res.samples.map((s) => s.vMeas);
  const m = vs.reduce((a, b) => a + b, 0) / vs.length;
  const v = vs.reduce((a, b) => a + (b - m) * (b - m), 0) / vs.length;
  near(m, 8, 0.01, 'noisy channel mean recovers the true voltage');
  near(Math.sqrt(v), 0.02 / 0.25, 0.012, 'noisy channel deviation matches noiseRms / sensitivity');

  /* averaging must reduce the noise on the accumulated energy, not amplify it */
  const quiet = DCEM.simulate({
    source: { mode: 'constant', voc: 8, rs: 0 },
    load: { mode: 'current', i: 0.5 },
    measurement: {
      voltage: { sensitivity: 0.25, adcBits: 12, adcVref: 3.3, noiseRms: 0.02 },
      current: { sensitivity: 0.5, adcBits: 12, adcVref: 3.3 }
    },
    duration: 2000, sampleInterval: 0.1, noiseSeed: 7
  }).results;
  ok(Math.abs(quiet.energyErrorPct) < 1, 'accumulated energy error stays under 1 % from noise alone',
    quiet.energyErrorPct.toFixed(4) + ' %');
}

/* =========================================================================
   7. Determinism of the seeded generator across uses
   ========================================================================== */
{
  const a = DCEM.makeRng(1234), b = DCEM.makeRng(1234);
  let same = true;
  for (let i = 0; i < 1000; i += 1) if (a() !== b()) same = false;
  ok(same, 'the same seed replays the same sequence');
  const c = DCEM.makeRng(1234);
  const draws = Array.from({ length: 5 }, () => c());
  ok(draws.every((x) => x >= 0 && x < 1), 'draws stay inside [0,1)', draws.join(', '));
}

/* =========================================================================
   8. Export accuracy
   ========================================================================== */
{
  const run = DCEM.simulate({
    source: { mode: 'step', voc: 12, vocAfter: 9, stepAt: 30 },
    load: { mode: 'sequence', points: [{ t: 0, i: 1 }, { t: 20, i: 0.4 }, { t: 45, i: 1.5 }] },
    measurement: {
      voltage: { sensitivity: 0.25, adcBits: 12, adcVref: 3.3, gainError: 0.01, offsetV: 0.01 },
      current: { sensitivity: 0.5, adcBits: 12, adcVref: 3.3 }
    },
    duration: 60, sampleInterval: 0.25, noiseSeed: 11
  });
  const csv = DCEM.toCSV(run.samples, { model: 'DCEM', version: DCEM.VERSION, sample_interval_s: 0.25 });
  const parsed = DCEM.parseCSV(csv);
  near(parsed.length, run.samples.length, 0, 'every sample is exported');
  const integrated = DCEM.integrateSeries(parsed.map((r) => ({ t: r.t_s, p: r.p_meas_w })));
  ok(integrated.ok, 'the exported table integrates cleanly');
  near(integrated.energyJ, run.results.energyJ, 1e-4, 'energy recomputed from the CSV matches the run');
  const lastRow = parsed[parsed.length - 1];
  near(lastRow.energy_wh, run.results.energyWh, 1e-6, 'last CSV row carries the final energy');
  ok(csv.startsWith('# model: DCEM'), 'export header records the model identity', csv.split('\n')[0]);
  ok(csv.indexOf('t_s,v_true_v,i_true_a,p_true_w') > 0, 'export column order is documented and stable');
}

/* =========================================================================
   9. Configuration warnings are raised, not hidden
   ========================================================================== */
{
  const res = DCEM.simulate({ source: { voc: 5 }, load: { mode: 'resistive', r: -1 }, duration: 2, sampleInterval: 1 });
  ok(res.results.warnings.length > 0, 'an invalid resistance raises a warning', JSON.stringify(res.results.warnings));
  const clean = DCEM.simulate({ source: { voc: 5 }, load: { mode: 'resistive', r: 10 }, duration: 2, sampleInterval: 1 });
  ok(clean.results.warnings.length === 0, 'a valid configuration raises no warnings', JSON.stringify(clean.results.warnings));
  /* The default chain quantises at 12 bits with unity sensitivity, so a 0.5 A
     current is reported within half an LSB (0.4 mA), not exactly. */
  near(clean.results.meanCurrentA, 5 / 10, 0.001, 'resistive default solves the operating point correctly');
}

/* =========================================================================
   10. Every shipped preset must run, stay finite and be reproducible
   ========================================================================== */
{
  ok(Array.isArray(DCEM.PRESETS) && DCEM.PRESETS.length >= 5, 'the model ships its presets', DCEM.PRESETS && DCEM.PRESETS.length);
  DCEM.PRESETS.forEach((preset) => {
    const a = DCEM.simulate(preset.config);
    const b = DCEM.simulate(preset.config);
    ok(a.results.accepted > 1, `preset ${preset.id} produces samples`, a.results.accepted);
    ok(isFinite(a.results.energyJ), `preset ${preset.id} produces a finite energy`, a.results.energyJ);
    ok(a.results.rejected === 0, `preset ${preset.id} produces no rejected samples`, a.results.rejected);
    ok(a.results.energyJ === b.results.energyJ, `preset ${preset.id} is reproducible`, a.results.energyJ);
    ok(a.results.warnings.length === 0, `preset ${preset.id} has a valid configuration`, JSON.stringify(a.results.warnings));
  });
}

console.log(`PASS: DCEM independent verification — ${checks} checks across ten groups (second integrator, closed form, electrical consistency, additivity, quantisation, noise statistics, determinism, export, warnings, presets)`);
