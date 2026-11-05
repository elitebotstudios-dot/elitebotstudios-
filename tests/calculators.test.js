const assert = require('assert');
const c = require('../assets/calc.js');

function near(actual, expected, tol, label) {
  assert.ok(Math.abs(actual - expected) <= tol, `${label}: got ${actual}, expected ${expected} ± ${tol}`);
}

// Ideal CCM buck: D=Vout/Vin; efficiency is only an input-power estimate.
const base = { vin: 12, vout: 5, freq: 500e3, inductance: 22e-6, iout: 2, eff: 0.9 };
const b = c.buck(base);
assert.ok(b);
near(b.duty, 5 / 12, 1e-12, 'ideal duty ratio');
near(b.deltaIl, 5 * (1 - 5 / 12) / (22e-6 * 500e3), 1e-12, 'inductor ripple');
near(b.lCrit, 5 * (1 - 5 / 12) / (2 * 500e3 * 2), 1e-12, 'critical inductance');
near(b.inputPower, 10 / 0.9, 1e-12, 'efficiency-based input power');
near(b.estimatedLoss, (10 / 0.9) - 10, 1e-12, 'estimated conversion loss');
assert.strictEqual(b.ccm, true);
const idealEff = c.buck(Object.assign({}, base, { eff: 1 }));
near(idealEff.duty, b.duty, 1e-12, 'efficiency does not alter ideal duty');
near(idealEff.inputPower, 10, 1e-12, '100% efficiency power estimate');
assert.strictEqual(idealEff.estimatedLoss, 0);
assert.strictEqual(c.buck(Object.assign({}, base, { vout: 12 })), null);
assert.strictEqual(c.buck(Object.assign({}, base, { eff: 0 })), null);
assert.strictEqual(c.buck(Object.assign({}, base, { eff: 1.01 })), null);
assert.strictEqual(c.buck(Object.assign({}, base, { iout: 0 })), null);
assert.strictEqual(c.buck(Object.assign({}, base, { iout: 0.1 })).ccm, false);

// IPC-2221 external-layer reference case and ambient-adjusted copper resistance.
const trace20 = c.traceWidth({ current: 3, rise: 10, copper: 1, length: 50, ambient: 20 });
const trace40 = c.traceWidth({ current: 3, rise: 10, copper: 1, length: 50, ambient: 40 });
near(trace20.widthMil, 53.8, 0.15, 'IPC-2221 trace width reference');
assert.ok(trace40.resistance > trace20.resistance, 'higher ambient must increase copper resistance');
assert.strictEqual(c.traceWidth({ current: -1, rise: 10, copper: 1 }), null);

// Other established calculator cases.
near(c.linear({ vin: 12, vout: 5, iout: 0.5, thetaJa: 65, ambient: 40 }).power, 3.5, 1e-12, 'linear regulator loss');
near(c.divider({ vin: 12, r1: 10000, r2: 10000 }).vout, 6, 1e-12, 'divider midpoint');
assert.strictEqual(c.divider({ vin: 0, r1: 10000, r2: 10000 }), null);
near(c.led({ supply: 5, forward: 2, current: 0.02 }).resistance, 150, 1e-12, 'LED resistor');
near(c.rc({ r: 10000, c: 100e-9 }).cutoff, 159.154943, 0.001, 'RC cutoff');
console.log('PASS: calculator reference cases, boundary conditions, and corrected buck-efficiency model');
