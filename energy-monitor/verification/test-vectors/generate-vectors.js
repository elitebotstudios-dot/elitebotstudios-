#!/usr/bin/env node
/* ===========================================================================
   generate-vectors.js — test vectors shared by the firmware test and the model

   Each vector set describes what the INA226 would have returned (raw register
   codes) at given millisecond timestamps, and what the firmware must compute
   from them: decoded volts and amps, power, and the accumulated energy under
   the documented missing-data policy.

   The expected values are computed here by an explicit replay of the policy —
   deliberately not by calling the firmware or the DCEM integrator, so the C++
   test is comparing two independent implementations of the same written rule.

   Outputs
     vectors.json                 for reviewers and for the website
     ../../firmware/test/vectors_generated.h   for the C++ test to compile in

   Usage: node energy-monitor/verification/test-vectors/generate-vectors.js
   ========================================================================== */
'use strict';
const fs = require('fs');
const path = require('path');

const SHUNT_LSB_V = 2.5e-6;      // INA226 shunt LSB
const BUS_LSB_V = 1.25e-3;       // INA226 bus LSB
const SHUNT_OHMS = 0.1;          // R1 on the DCM-HW-V1 carrier
const MAX_GAP_MS = 5000;         // IntegratorConfig default

const busRaw = (volts) => Math.round(volts / BUS_LSB_V);
const shuntRaw = (amps) => Math.round((amps * SHUNT_OHMS) / SHUNT_LSB_V);

/* Replay of the firmware policy, written from the header comment, not from the
   C++ source. */
function replay(samples, calib) {
  const c = calib || { v_gain: 1, v_offset: 0, i_gain: 1, i_offset: 0 };
  let prev = null, importJ = 0, exportJ = 0, integrated = 0, held = 0, gaps = 0;
  const decoded = [];
  for (const s of samples) {
    const v = (s.bus_raw * BUS_LSB_V) * c.v_gain + c.v_offset;
    const i = ((s.shunt_raw * SHUNT_LSB_V) / SHUNT_OHMS) * c.i_gain + c.i_offset;
    const valid = s.valid !== false;
    decoded.push({ t_ms: s.t_ms, v, i, p: v * i, valid });
    if (!prev) { prev = { ...s, v, i, valid }; continue; }
    const dt = (s.t_ms - prev.t_ms) >>> 0;              // wrap-safe, like the firmware
    if (dt === 0) { held++; prev = { ...s, v, i, valid }; continue; }
    if (!valid || !prev.valid) { held++; prev = { ...s, v, i, valid }; continue; }
    if (dt > MAX_GAP_MS) { held++; gaps++; prev = { ...s, v, i, valid }; continue; }
    const pPrev = prev.v * prev.i;
    const pNow = v * i;
    const j = 0.5 * (pPrev + pNow) * (dt / 1000);
    if (j >= 0) importJ += j; else exportJ -= j;
    integrated++;
    prev = { ...s, v, i, valid };
  }
  return {
    decoded,
    expected: {
      energy_wh: (importJ - exportJ) / 3600,
      import_j: importJ,
      export_j: exportJ,
      integrated,
      held,
      gaps,
      final_v: decoded.length ? decoded[decoded.length - 1].v : 0,
      final_i: decoded.length ? decoded[decoded.length - 1].i : 0,
      final_p: decoded.length ? decoded[decoded.length - 1].p : 0
    }
  };
}

/* Constant power for a known time: the trapezoidal rule is exact, so the
   expected energy can be checked by hand. 12 V × 0.25 A for 9 s = 27 J. */
const constant = {
  id: 'constant',
  description: '12 V, 0.25 A, sampled every 1 s for 9 s (ten samples, t = 0 … 9000 ms). Trapezoidal integration of constant power is exact: 3 W × 9 s = 27 J = 0.0075 Wh. Note that one second alone would be 3 J, not 27 J — the duration is nine seconds, and the 1 s figure in this description is the sample interval.',
  shunt_ohms: SHUNT_OHMS,
  calibration: { v_gain: 1, v_offset: 0, i_gain: 1, i_offset: 0 },
  samples: Array.from({ length: 10 }, (_, k) => ({
    t_ms: k * 1000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true
  })),
  hand_checked_j: 27
};

/* A step in current at t = 4 s, which straddles one interval. */
const step = {
  id: 'step',
  description: '12 V; current steps from 0.30 A to 0.15 A at 2.5 s, falling between samples at 2 s and 3 s. Five samples spanning 4 s; the interval containing the step is charged the trapezoidal average.',
  shunt_ohms: SHUNT_OHMS,
  calibration: { v_gain: 1, v_offset: 0, i_gain: 1, i_offset: 0 },
  samples: [
    { t_ms: 0, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.30), valid: true },
    { t_ms: 1000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.30), valid: true },
    { t_ms: 2000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.30), valid: true },
    { t_ms: 3000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.15), valid: true },
    { t_ms: 4000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.15), valid: true }
  ]
};

/* Irregular spacing: the interval comes from the timestamps, not a nominal period. */
const irregular = {
  id: 'irregular',
  description: 'Irregular timestamps (0, 700, 1500, 2600, 3800 ms — a 3.8 s span) with varying current. The integrator must use the real interval each time.',
  shunt_ohms: SHUNT_OHMS,
  calibration: { v_gain: 1, v_offset: 0, i_gain: 1, i_offset: 0 },
  samples: [
    { t_ms: 0, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.20), valid: true },
    { t_ms: 700, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.40), valid: true },
    { t_ms: 1500, bus_raw: busRaw(11.8), shunt_raw: shuntRaw(0.10), valid: true },
    { t_ms: 2600, bus_raw: busRaw(11.8), shunt_raw: shuntRaw(0.35), valid: true },
    { t_ms: 3800, bus_raw: busRaw(12.1), shunt_raw: shuntRaw(0.05), valid: true }
  ]
};

/* A gap longer than max_gap_ms is missing data and must not be integrated. */
const gap = {
  id: 'gap',
  description: 'A 7 s gap between samples at 2 s and 9 s exceeds the 5 s maximum. The run spans 10 s; the gap interval is held rather than integrated, and counted.',
  shunt_ohms: SHUNT_OHMS,
  calibration: { v_gain: 1, v_offset: 0, i_gain: 1, i_offset: 0 },
  samples: [
    { t_ms: 0, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.40), valid: true },
    { t_ms: 1000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.40), valid: true },
    { t_ms: 2000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.40), valid: true },
    { t_ms: 9000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.40), valid: true },
    { t_ms: 10000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.40), valid: true }
  ]
};

/* An invalid reading costs the interval that ends at it and the one after it. */
const invalid = {
  id: 'invalid',
  description: 'The sample at 2 s is marked invalid (sensor NACK) in a 4 s run sampled every 1 s. The interval ending at it and the interval starting from it are both held, so two 1 s intervals are lost rather than smeared over.',
  shunt_ohms: SHUNT_OHMS,
  calibration: { v_gain: 1, v_offset: 0, i_gain: 1, i_offset: 0 },
  samples: [
    { t_ms: 0, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true },
    { t_ms: 1000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true },
    { t_ms: 2000, bus_raw: 0, shunt_raw: 0, valid: false },
    { t_ms: 3000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true },
    { t_ms: 4000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true }
  ]
};

/* 32-bit millisecond rollover: the loop must not lose or gain energy. */
const ROLL = 4294967296;
const rollover = {
  id: 'rollover',
  description: 'The millisecond counter wraps between samples. Unsigned subtraction must still produce a 1.5 s interval; the run spans 2.5 s and the energy must match the same run without the wrap.',
  shunt_ohms: SHUNT_OHMS,
  calibration: { v_gain: 1, v_offset: 0, i_gain: 1, i_offset: 0 },
  samples: [
    { t_ms: ROLL - 3000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true },
    { t_ms: ROLL - 2000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true },
    { t_ms: (ROLL - 2000 + 1500) >>> 0, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true }
  ],
  note: 'timestamp_ms is stored as an unsigned 32-bit value, so the third sample wraps to a small number.'
};

/* Zero current: the accumulator must stay exactly at zero. */
const zeroCurrent = {
  id: 'zero-current',
  description: 'Voltage present, current zero, sampled every 1 s for 5 s. Power is zero at every sample, so the energy total must be exactly zero while the voltage is still reported.',
  shunt_ohms: SHUNT_OHMS,
  calibration: { v_gain: 1, v_offset: 0, i_gain: 1, i_offset: 0 },
  samples: Array.from({ length: 6 }, (_, k) => ({
    t_ms: k * 1000, bus_raw: busRaw(12), shunt_raw: 0, valid: true
  }))
};

/* Calibration applied in engineering units, as the firmware does it. */
const calibrated = {
  id: 'calibrated',
  description: 'Two samples 1 s apart with a +2 % voltage gain, +30 mV voltage offset and −1 % current gain applied in engineering units: corrected = raw × gain + offset.',
  shunt_ohms: SHUNT_OHMS,
  calibration: { v_gain: 1.02, v_offset: 0.03, i_gain: 0.99, i_offset: 0 },
  samples: [
    { t_ms: 0, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true },
    { t_ms: 1000, bus_raw: busRaw(12), shunt_raw: shuntRaw(0.25), valid: true }
  ]
};

const sets = [constant, step, irregular, gap, invalid, rollover, zeroCurrent, calibrated].map((s) => {
  const out = replay(s.samples, s.calibration);
  return Object.assign({}, s, {
    decoded: out.decoded.map((d) => ({
      t_ms: d.t_ms, v: Number(d.v.toFixed(9)), i: Number(d.i.toFixed(9)),
      p: Number(d.p.toFixed(9)), valid: d.valid
    })),
    expected: out.expected
  });
});

/* Structural self-checks before writing anything. */
let problems = 0;
const c0 = sets.find((s) => s.id === 'constant');
const handWh = c0.hand_checked_j / 3600;
if (Math.abs(c0.expected.energy_wh - handWh) > 1e-12) {
  console.error(`constant set: expected ${handWh} Wh by hand, replay produced ${c0.expected.energy_wh}`);
  problems++;
}
const z0 = sets.find((s) => s.id === 'zero-current');
if (z0.expected.energy_wh !== 0) { console.error('zero-current set produced non-zero energy'); problems++; }
const r0 = sets.find((s) => s.id === 'rollover');
const rollExpected = 12 * 0.25 * 2.5 / 3600;   // two intervals: 1 s and 1.5 s
if (Math.abs(r0.expected.energy_wh - rollExpected) > 1e-9) {
  console.error(`rollover set: expected ${rollExpected} Wh, got ${r0.expected.energy_wh}`);
  problems++;
}
const g0 = sets.find((s) => s.id === 'gap');
if (g0.expected.gaps !== 1) { console.error('gap set did not record exactly one gap'); problems++; }
const i0 = sets.find((s) => s.id === 'invalid');
if (i0.expected.held !== 2) { console.error(`invalid set held ${i0.expected.held} intervals, expected 2`); problems++; }
if (problems) process.exit(1);

const doc = {
  generated_by: 'energy-monitor/verification/test-vectors/generate-vectors.js',
  firmware_policy: {
    energy: 'trapezoidal on (t_n - t_n-1) milliseconds, unsigned arithmetic so rollover is safe',
    max_gap_ms: MAX_GAP_MS,
    invalid_sample: 'interval ending at an invalid sample AND the interval starting from it are held',
    calibration: 'corrected = raw_engineering × gain + offset, applied per channel'
  },
  sensor: { part: 'INA226', shunt_lsb_v: SHUNT_LSB_V, bus_lsb_v: BUS_LSB_V, shunt_ohms: SHUNT_OHMS },
  sets
};

fs.writeFileSync(path.join(__dirname, 'vectors.json'), JSON.stringify(doc, null, 2) + '\n');

/* C++ header for the firmware test. */
const lines = [];
lines.push('// Generated by generate-vectors.js — do not edit by hand.');
lines.push('// Regenerate: node energy-monitor/verification/test-vectors/generate-vectors.js');
lines.push('#pragma once');
lines.push('#include <cstdint>');
lines.push('');
lines.push('namespace dcm_test {');
lines.push('');
lines.push('struct VecSample { std::uint32_t t_ms; std::int16_t shunt_raw; std::uint16_t bus_raw; bool valid; };');
lines.push('struct VecSet {');
lines.push('  const char* id;');
lines.push('  int count;');
lines.push('  const VecSample* samples;');
lines.push('  float v_gain, v_offset, i_gain, i_offset;');
lines.push('  float shunt_ohms;');
lines.push('  double expected_energy_wh;');
lines.push('  double expected_final_v, expected_final_i, expected_final_p;');
lines.push('  int expected_integrated, expected_held, expected_gaps;');
lines.push('};');
lines.push('');
for (const s of sets) {
  const name = 'k_' + s.id.replace(/-/g, '_');
  lines.push(`// ${s.description}`);
  lines.push(`constexpr VecSample ${name}_samples[] = {`);
  for (const raw of s.samples) {
    lines.push(`  {${raw.t_ms}u, ${raw.shunt_raw}, ${raw.bus_raw}u, ${raw.valid ? 'true' : 'false'}},`);
  }
  lines.push('};');
  const last = s.decoded[s.decoded.length - 1];
  const c = s.calibration;
  const num = (x) => {
    const t = Number(x).toFixed(6);
    return (t.includes('.') ? t : t + '.0') + 'f';
  };
  lines.push(`constexpr VecSet ${name} = {"${s.id}", ${s.samples.length}, ${name}_samples, ` +
    `${num(c.v_gain)}, ${num(c.v_offset)}, ${num(c.i_gain)}, ${num(c.i_offset)}, ${num(s.shunt_ohms)}, ` +
    `${s.expected.energy_wh.toFixed(12)}, ${num(last.v)}, ${num(last.i)}, ${num(last.p)}, ` +
    `${s.expected.integrated}, ${s.expected.held}, ${s.expected.gaps}};`);
  lines.push('');
}
lines.push('constexpr VecSet kAllSets[] = {');
for (const s of sets) lines.push(`  ${'k_' + s.id.replace(/-/g, '_')},`);
lines.push('};');
lines.push(`constexpr int kSetCount = ${sets.length};`);
lines.push('');
lines.push('}  // namespace dcm_test');
fs.writeFileSync(path.join(__dirname, '..', '..', 'firmware', 'test', 'vectors_generated.h'),
  lines.join('\n') + '\n');

console.log('  vectors.json written with %d sets', sets.length);
for (const s of sets) {
  console.log(`    ${s.id.padEnd(14)} ${String(s.samples.length).padStart(2)} samples  ` +
    `${s.expected.energy_wh.toFixed(9)} Wh  integrated ${s.expected.integrated}  ` +
    `held ${s.expected.held}  gaps ${s.expected.gaps}`);
}
console.log('  firmware/test/vectors_generated.h written');
