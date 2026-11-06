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

/* ---- cross-check against an independent switching-cycle model -------------
   The buck explorer is a single-operating-point tool, so it cannot make the
   worst-case error the power-stage utility had. It can still get a coefficient
   wrong, so the ripple, duty and critical inductance are re-derived here by
   integrating di/dt through one cycle and solving for volt-second balance,
   instead of re-using the same closed forms. */
(function independentBuckParity() {
  function simulatedDuty(vin, vout) {
    const net = (D) => (vin - vout) * D - vout * (1 - D);   // ∝ net volt-seconds
    let lo = 0, hi = 1;
    for (let i = 0; i < 200; i += 1) { const m = (lo + hi) / 2; if (net(m) > 0) hi = m; else lo = m; }
    return (lo + hi) / 2;
  }
  function simulatedRipple(vin, vout, L, f) {
    const T = 1 / f, D = simulatedDuty(vin, vout), steps = 4000;
    let i = 0, min = 0, max = 0;
    for (let k = 0; k < steps; k += 1) {
      const t = (k + 0.5) * T / steps;
      i += (t < D * T ? (vin - vout) : -vout) / L * (T / steps);
      if (i < min) min = i;
      if (i > max) max = i;
    }
    return max - min;
  }
  [[9, 5], [12, 5], [15, 5], [24, 3.3], [48, 12], [3.7, 1.8]].forEach(([vin, vout]) => {
    const r = c.buck({ vin, vout, freq: 500e3, inductance: 22e-6, iout: 2, eff: 0.9 });
    near(r.duty, simulatedDuty(vin, vout), 1e-6, `buck duty parity with cycle simulation at ${vin} V`);
    near(r.deltaIl, simulatedRipple(vin, vout, 22e-6, 500e3), 1e-3 * Math.max(r.deltaIl, 1e-3),
      `buck ripple parity with cycle simulation at ${vin} V`);
    /* the critical inductance must place the valley exactly at zero */
    const boundary = c.buck({ vin, vout, freq: 500e3, inductance: r.lCrit, iout: 2, eff: 1 });
    near(boundary.iValley, 0, 1e-9, `buck boundary inductance zeroes the valley at ${vin} V`);
    assert.strictEqual(boundary.ccm, true, `valley of zero is still flagged continuous at ${vin} V`);
  });
  /* ripple must rise with input voltage for a fixed inductor — the property the
     power-stage utility originally inverted */
  const at9 = c.buck({ vin: 9, vout: 5, freq: 500e3, inductance: 22e-6, iout: 2, eff: 1 }).deltaIl;
  const at15 = c.buck({ vin: 15, vout: 5, freq: 500e3, inductance: 22e-6, iout: 2, eff: 1 }).deltaIl;
  assert.ok(at15 > at9, 'buck ripple increases with input voltage');
  near(at15 / at9, (1 - 5 / 15) / (1 - 5 / 9), 1e-9, 'buck ripple ratio follows (1 − D)');

  /* IPC-2221: the model must invert its own published power law */
  const tw = c.traceWidth({ current: 3, rise: 10, copper: 1, length: 20, internal: false, ambient: 20 });
  near(tw.widthMil * 1.378 * 1, tw.areaMil2, 1e-9, 'trace width × copper thickness = area');
  near(tw.areaMil2, Math.pow(3 / (0.048 * Math.pow(10, 0.44)), 1 / 0.725), 1e-9, 'IPC-2221 area from the published constants');
  near(tw.widthMil, 53.8, 0.15, 'IPC-2221: 3 A, 10 °C, 1 oz external is 53.8 mil');
  const internal = c.traceWidth({ current: 3, rise: 10, copper: 1, length: 20, internal: true, ambient: 20 });
  near(internal.widthMil / tw.widthMil, Math.pow(2, 1 / 0.725), 1e-9, 'internal layers need 2^(1/0.725) times the width');
  /* Resistance must be recomputed from first principles: copper at the heated
     temperature (20 °C + ΔT), the geometry the IPC width implies, and the
     100 mm length. A model that quietly uses 20 °C resistivity fails this. */
  [[10, 20], [10, 60], [40, 20]].forEach(([rise, ambient]) => {
    const t = c.traceWidth({ current: 3, rise, copper: 1, length: 100, internal: false, ambient });
    const tM = t.widthMm * 1e-3;
    const thickM = t.thickMm * 1e-3;
    const rho = 1.724e-8 * (1 + 0.00393 * (ambient + rise - 20));
    near(t.resistance, rho * 0.1 / (tM * thickM), 1e-12,
      `trace resistance from geometry and copper temperature (ΔT ${rise} °C, ambient ${ambient} °C)`);
    near(t.copperTemp, ambient + rise, 1e-12, 'copper temperature is ambient plus the entered rise');
  });

  /* linear regulator: junction temperature is an absolute check, not a ratio */
  const lr = c.linear({ vin: 12, vout: 5, iout: 0.5, thetaJa: 65, ambient: 40, tjMax: 125 });
  near(lr.power, 3.5, 1e-12, 'linear regulator dissipation is (Vin − Vout)·Iout');
  near(lr.tj, 40 + 3.5 * 65, 1e-9, 'junction temperature = ambient + P·θJA');
  near(lr.maxCurrent, (125 - 40) / (65 * 7), 1e-9, 'maximum safe current from the thermal limit');
  assert.strictEqual(lr.safe, false, '3.5 W in a 65 °C/W package exceeds the 125 °C limit');
  const okCase = c.linear({ vin: 12, vout: 5, iout: 0.15, thetaJa: 65, ambient: 40, tjMax: 125 });
  assert.strictEqual(okCase.safe, true, '0.15 A in the same package stays inside the limit');
  near(okCase.tj, 40 + 7 * 0.15 * 65, 1e-9, 'the safe case lands at the expected junction temperature');
  console.log('PASS: buck, trace-width and linear-regulator models cross-checked against independent derivations');
})();
