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

// ---- PWM signal laboratory -------------------------------------------------
const pwmDefault = c.pwm({ freq: 1000, duty: 0.25, high: 3.3 });
near(pwmDefault.period, 1e-3, 1e-15, 'PWM period at 1 kHz');
near(pwmDefault.ton, 250e-6, 1e-15, 'PWM on-time at 25 %');
near(pwmDefault.toff, 750e-6, 1e-15, 'PWM off-time at 25 %');
near(pwmDefault.dutyPct, 25, 1e-12, 'PWM duty percentage');
near(pwmDefault.average, 0.825, 1e-12, 'PWM average voltage');
near(pwmDefault.rms, 3.3 * Math.sqrt(0.25), 1e-12, 'PWM RMS voltage');
const pwmFast = c.pwm({ freq: 500e3, duty: 0.4, high: 12 });
near(pwmFast.period, 2e-6, 1e-18, 'PWM period at 500 kHz');
near(pwmFast.ton, 800e-9, 1e-18, 'PWM on-time at 500 kHz, 40 %');
near(pwmFast.average, 4.8, 1e-12, 'PWM average at 40 % of 12 V');
const pwmZero = c.pwm({ freq: 1000, duty: 0, high: 5 });
near(pwmZero.average, 0, 1e-12, 'PWM 0 % average is zero');
near(pwmZero.ton, 0, 1e-12, 'PWM 0 % on-time is zero');
assert.strictEqual(c.pwm({ freq: 1000, duty: 1.5, high: 5 }), null, 'duty above 100 % rejected');
assert.strictEqual(c.pwm({ freq: 0, duty: 0.5, high: 5 }), null, 'zero frequency rejected');
assert.strictEqual(c.pwm({ freq: 1000, duty: 0.5, high: -1 }), null, 'negative high level rejected');
assert.strictEqual(c.eng(0, 'V'), '0 V', 'zero formatted with its unit');
near(c.divider({ vin: 12, r1: 10000, r2: 10000 }).current, 0.6e-3, 1e-12, 'divider current 12 V / 20 kΩ');
near(c.led({ supply: 5, forward: 2, current: 0.01 }).resistance, 300, 1e-12, 'LED resistor for 10 mA');
console.log('PASS: PWM laboratory reference cases and formatting');
