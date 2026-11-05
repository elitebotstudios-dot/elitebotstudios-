/* Reference tests for assets/powerstage.js
   Values are derived by hand from the ideal CCM buck relations:
     D = Vout / Vin
     ΔIL = Vout (1 − D) / (L fsw)
     L = Vout (1 − Dmax) / (ΔIL_target fsw)
     Cout ≈ ΔIL / (8 fsw ΔVout)
   Usage: node tests/powerstage.test.js                                  */
const assert = require('assert');
const { designBuck } = require('../assets/powerstage.js');

function near(actual, expected, tol, label) {
  assert.ok(Math.abs(actual - expected) <= tol,
    `${label}: got ${actual}, expected ${expected} ± ${tol}`);
}

/* Case 1 — the operating point used throughout the site:
   9–15 V in, 5 V out, 2 A, 500 kHz, 30 % ripple, 1 % output ripple. */
const a = designBuck({ vinMin: 9, vinMax: 15, vout: 5, iout: 2, fsw: 500e3, ripplePct: 30, voutRipplePct: 1 });
assert.ok(a, 'case 1 must produce a design');
near(a.dutyMax, 5 / 9, 1e-12, 'duty at minimum input');
near(a.dutyMin, 5 / 15, 1e-12, 'duty at maximum input');
near(a.deltaIl, 0.6, 1e-12, 'target ripple 30 % of 2 A');
const expectedL = 5 * (1 - 5 / 9) / (0.6 * 500e3);
near(a.inductance, expectedL, 1e-15, 'inductance for target ripple at vinMin');
near(a.inductance, 7.407407e-6, 1e-9, 'inductance ≈ 7.41 µH');
near(a.iPeak, 2.3, 1e-12, 'peak current 2 A + 0.3 A');
near(a.iValley, 1.7, 1e-12, 'valley current 2 A − 0.3 A');
near(a.lCrit, 5 * (1 - 5 / 9) / (2 * 500e3 * 2), 1e-15, 'critical inductance');
assert.strictEqual(a.ccm, true, 'stays continuous at full load');
near(a.capacitance, 0.6 / (8 * 500e3 * 0.05), 1e-12, 'output capacitance ≈ 3.0 µF');
near(a.voutRipple, 0.05, 1e-12, '1 % of 5 V');
near(a.onTimeMax, (5 / 9) / 500e3, 1e-15, 'longest on-time');

/* Case 2 — 12 V nominal, 3.3 V out, 1 A, 1 MHz, 40 % ripple. */
const b = designBuck({ vinMin: 12, vinMax: 24, vout: 3.3, iout: 1, fsw: 1e6, ripplePct: 40, voutRipplePct: 2 });
assert.ok(b, 'case 2 must produce a design');
near(b.dutyMax, 3.3 / 12, 1e-12, 'case 2 duty');
near(b.deltaIl, 0.4, 1e-12, 'case 2 ripple target');
near(b.inductance, 3.3 * (1 - 0.275) / (0.4 * 1e6), 1e-15, 'case 2 inductance');
near(b.inductance, 5.98125e-6, 1e-12, 'case 2 inductance ≈ 5.98 µH');
assert.strictEqual(b.ccm, true, 'case 2 is continuous');

/* Case 3 — a large ripple target. Note the definition used here: ripple is a
   percentage of load current, so a 100 % target leaves a valley of Iout/2 and
   the design is still continuous. The CCM boundary is reported separately as
   lCrit, which is the inductance where the valley would reach zero at full load. */
const c = designBuck({ vinMin: 12, vinMax: 12, vout: 5, iout: 1, fsw: 100e3, ripplePct: 100, voutRipplePct: 1 });
assert.ok(c, 'case 3 must compute');
assert.strictEqual(c.ccm, true, 'a 100 % ripple target is still continuous by definition');
near(c.iValley, 0.5, 1e-12, 'valley current is Iout/2 at 100 % ripple');
near(c.lCrit, 5 * (1 - 5 / 12) / (2 * 100e3 * 1), 1e-15, 'critical inductance at 100 kHz, 1 A');

/* Rejections */
assert.strictEqual(designBuck({ vinMin: 5, vinMax: 5, vout: 5, iout: 1, fsw: 1e5, ripplePct: 30, voutRipplePct: 1 }), null, 'Vout equal to Vin rejected');
assert.strictEqual(designBuck({ vinMin: 12, vinMax: 8, vout: 5, iout: 1, fsw: 1e5, ripplePct: 30, voutRipplePct: 1 }), null, 'vinMax below vinMin rejected');
assert.strictEqual(designBuck({ vinMin: 12, vinMax: 24, vout: 5, iout: 0, fsw: 1e5, ripplePct: 30, voutRipplePct: 1 }), null, 'zero current rejected');
assert.strictEqual(designBuck({ vinMin: 12, vinMax: 24, vout: 5, iout: 1, fsw: 0, ripplePct: 30, voutRipplePct: 1 }), null, 'zero frequency rejected');
assert.strictEqual(designBuck({ vinMin: 12, vinMax: 24, vout: 5, iout: 1, fsw: 1e5, ripplePct: 150, voutRipplePct: 1 }), null, 'ripple above 100 % rejected');
assert.strictEqual(designBuck({}), null, 'empty spec rejected');

/* The inductance sized at vinMin must reproduce the ripple at vinMin. */
const rippleCheck = (a.vout === undefined ? 5 : 5) * (1 - (5 / 9)) / (a.inductance * 500e3);
near(rippleCheck, a.deltaIl, 1e-9, 'independence check: ripple recomputed from L');

console.log('PASS: power-stage sizing — 3 worked cases, boundary behaviour and 6 rejection rules');
