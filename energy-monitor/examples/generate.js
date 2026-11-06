#!/usr/bin/env node
/* ===========================================================================
   generate.js — write the reference datasets shipped with the project.

   The expected energies are literals derived by hand in the reference test
   file, not values read back from the model. If the model and the dataset ever
   disagree, the dataset is wrong and regeneration will show it in the tests.

   Run:  node energy-monitor/examples/generate.js
   ========================================================================== */
'use strict';
const fs = require('fs');
const path = require('path');
const DCEM = require(path.join(__dirname, '..', 'model', 'dcem.js'));

const OUT = __dirname;
const ideal = {
  voltage: { sensitivity: 1, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 0, adcVref: 3.3 },
  current: { sensitivity: 1, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 0, adcVref: 3.3 }
};

const datasets = [
  {
    file: 'reference-case-a-constant.csv',
    title: 'Reference case A — constant 12 V, 1 A, 3600 s',
    expectedJ: 43200,
    expectedWh: 12,
    config: {
      source: { mode: 'constant', voc: 12, rs: 0 },
      load: { mode: 'current', i: 1 },
      measurement: ideal, sampleInterval: 1, duration: 3600, noiseSeed: 1
    },
    note: 'P = 12 W for 3600 s. Constant power, so the trapezoidal rule is exact at any interval.'
  },
  {
    file: 'reference-case-b-constant.csv',
    title: 'Reference case B — constant 5 V, 2 A, 1800 s',
    expectedJ: 18000,
    expectedWh: 5,
    config: {
      source: { mode: 'constant', voc: 5, rs: 0 },
      load: { mode: 'current', i: 2 },
      measurement: ideal, sampleInterval: 1, duration: 1800, noiseSeed: 1
    },
    note: 'P = 10 W for 1800 s.'
  },
  {
    file: 'reference-case-c-step.csv',
    title: 'Reference case C — 10 V, 1 A → 0.5 A at 1800 s',
    expectedJ: 26997.5,
    expectedWh: 7.499305555555556,
    idealJ: 27000,
    config: {
      source: { mode: 'constant', voc: 10, rs: 0 },
      load: { mode: 'step', iBefore: 1, iAfter: 0.5, stepAt: 1800 },
      measurement: ideal, sampleInterval: 1, duration: 3600, noiseSeed: 1
    },
    note: 'Right-continuous step. The interval straddling the step is charged ½(10+5)·1 = 7.5 J, ' +
      'so the discrete result is 26997.5 J — 2.5 J (0.0093 %) below the continuous ideal of 27000 J.'
  },
  {
    file: 'preset-constant-load.csv',
    title: 'Preset: constant resistive load, 12 V into 12 Ω, 300 s',
    /* This preset runs through a 12-bit chain, so it is deliberately NOT a
       reference case: the reported energy differs from the 3600 J a perfect
       chain would give, and the size of that difference is the finding. */
    expectedJ: null,
    expectedWh: null,
    nominalJ: 3600,
    config: DCEM.PRESETS.find((p) => p.id === 'constant-load').config,
    note: 'Nominal load energy for this run is 12 W × 300 s = 3600 J. The dataset is produced by the ' +
      '12-bit measurement chain, so its reported energy sits a fraction of a percent away from that; ' +
      'the difference is quantisation bias, not a defect.'
  },
  {
    file: 'preset-sampling-interval.csv',
    title: 'Preset: 4 s duty cycle sampled at 2 s',
    expectedJ: null,
    expectedWh: null,
    config: DCEM.PRESETS.find((p) => p.id === 'sampling-interval').config,
    note: 'Sparse sampling of a 4 s duty cycle. No analytic total is quoted: the point of the dataset ' +
      'is that the reported average depends on where the samples fall, which is why it has none.'
  }
];

let written = 0;
datasets.forEach((d) => {
  const run = DCEM.simulate(d.config);
  const meta = {
    model: 'Elite Bot Studios DCEM ' + DCEM.VERSION,
    dataset: d.file,
    title: d.title,
    note: d.note,
    sample_interval_s: d.config.sampleInterval,
    duration_s: d.config.duration,
    expected_energy_j: d.expectedJ === null ? 'not quoted (see note)' : String(d.expectedJ),
    expected_energy_wh: d.expectedWh === null ? 'not quoted (see note)' : String(d.expectedWh),
    model_energy_j: run.results.energyJ.toFixed(6),
    model_energy_wh: run.results.energyWh.toFixed(9),
    samples: String(run.samples.length)
  };
  if (d.idealJ !== undefined) meta.continuous_ideal_j = String(d.idealJ);
  if (d.nominalJ !== undefined) {
    meta.nominal_energy_j = String(d.nominalJ);
    meta.deviation_from_nominal_pct = ((run.results.energyJ - d.nominalJ) / d.nominalJ * 100).toFixed(4);
  }
  const csv = DCEM.toCSV(run.samples, meta);
  fs.writeFileSync(path.join(OUT, d.file), csv);
  written += 1;
  const reference = d.expectedJ !== null ? d.expectedJ : d.nominalJ;
  const agree = d.expectedJ !== null
    ? (Math.abs(run.results.energyJ - d.expectedJ) < 1e-6 ? 'matches' : 'MISMATCH')
    : (d.nominalJ === undefined ? 'n/a — no analytic total by design'
       : ((run.results.energyJ - d.nominalJ) / d.nominalJ * 100).toFixed(3) + ' % from nominal');
  console.log(`  ${d.file.padEnd(34)} ${String(run.samples.length).padStart(6)} samples  model ${run.results.energyJ.toFixed(3)} J  reference ${reference === null ? '—' : reference} J  ${agree}`);
});

/* The irregular-sampling dataset is a hand-written table, not a simulation:
   it exists so a reviewer can check the trapezoidal rule by hand. */
const irregular = [
  { t: 0.00, p: 10 },
  { t: 0.37, p: 12 },
  { t: 1.20, p: 7 },
  { t: 2.05, p: 15 },
  { t: 3.90, p: 9 },
  { t: 7.31, p: 11 }
];
const checked = DCEM.integrateSeries(irregular);
const manual = irregular.slice(1).reduce((acc, cur, i) => {
  const prev = irregular[i];
  return acc + (prev.p + cur.p) / 2 * (cur.t - prev.t);
}, 0);
const rows = [
  '# model: Elite Bot Studios DCEM ' + DCEM.VERSION,
  '# dataset: reference-case-e-irregular.csv',
  '# title: Reference case E — irregular timestamps, hand-checkable',
  '# note: E = Σ ½(P_i + P_i+1)(t_i+1 − t_i) over the five intervals.',
  '# expected_energy_j: 77.605',
  '# hand_sum_j: ' + manual.toFixed(6),
  '# model_energy_j: ' + checked.energyJ.toFixed(6),
  't_s,p_w'
].concat(irregular.map((r) => `${r.t.toFixed(2)},${r.p.toFixed(3)}`)).join('\n');
fs.writeFileSync(path.join(OUT, 'reference-case-e-irregular.csv'), rows + '\n');
written += 1;
console.log(`  reference-case-e-irregular.csv         ${irregular.length} samples  model ${checked.energyJ.toFixed(3)} J  expected 77.605 J  ${Math.abs(checked.energyJ - 77.605) < 1e-9 ? 'matches' : 'MISMATCH'}`);

console.log(`\n  ${written} datasets written to energy-monitor/examples/`);
