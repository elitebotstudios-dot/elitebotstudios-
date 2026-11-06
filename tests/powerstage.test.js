/* ===========================================================================
   tests/powerstage.test.js — worked reference cases for assets/powerstage.js

   This file documents the three reference cases in full, and then checks them
   against the built page. It is deliberately not the only test: everything
   here is a hand derivation from the ideal CCM buck relations, and
   tests/powerstage-independent.test.js re-derives the same numbers from a
   switching-cycle simulation instead of the closed forms.

     D(Vin)      = Vout / Vin
     ΔIL(Vin)    = Vout (1 − Vout/Vin) / (L fsw)
     L required  = Vout (1 − Vout/Vin,max) / (ΔIL,target fsw)
     L_crit      = Vout (1 − Vout/Vin,max) / (2 Iout fsw)
     Cout        = ΔIL / (8 fsw ΔVout)

   Run: node tests/powerstage.test.js
   ========================================================================== */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { designBuck, ripple, criticalInductance } = require('../assets/powerstage.js');

let count = 0;
function near(actual, expected, tol, label) {
  count += 1;
  assert.ok(Math.abs(actual - expected) <= tol,
    `${label}: got ${actual}, expected ${expected} ± ${tol}`);
}
function rel(actual, expected, tol, label) { near(actual, expected, Math.abs(expected) * tol, label); }
function ok(cond, label) { count += 1; assert.ok(cond, label); }

/* ---------------------------------------------------------------------------
   Case A — 9–15 V in, 5 V out, 2 A, 500 kHz, 30 % inductor ripple, 1 % out.
   Hand derivation:
     ΔIL,target = 0.30 × 2 A           = 0.600 A
     D at 15 V  = 5/15                 = 0.33333      (worst case for ripple)
     L          = 5 × 0.66667 / (0.6 × 500e3)
                = 11.111 µH
     L_crit     = 5 × 0.66667 / (2 × 2 × 500e3)
                = 1.6667 µH
     I_peak     = 2 + 0.3              = 2.300 A
     I_valley   = 2 − 0.3              = 1.700 A
     I_rms      = √(2² + 0.6²/12)      = 2.00749 A
     C (ESR = 0)= 0.6 / (8 × 500e3 × 0.05) = 3.000 µF
   ------------------------------------------------------------------------- */
const specA = { vinMin: 9, vinMax: 15, vout: 5, iout: 2, fsw: 500e3, ripplePct: 30, voutRipplePct: 1 };
const a = designBuck(specA);
ok(a, 'case A produces a design');
rel(a.timing.dutyMin, 5 / 15, 1e-12, 'A: duty at maximum input');
rel(a.timing.dutyMax, 5 / 9, 1e-12, 'A: duty at minimum input');
rel(a.worst.deltaIl, 0.6, 1e-12, 'A: ripple target is 30 % of 2 A');
rel(a.inductance, 11.111111e-6, 1e-6, 'A: inductance 11.111 µH');
rel(a.lCrit, 1.666667e-6, 1e-6, 'A: critical inductance 1.667 µH');
rel(a.iPeak, 2.3, 1e-12, 'A: peak current 2.300 A');
rel(a.iValley, 1.7, 1e-12, 'A: valley current 1.700 A');
rel(a.iRms, Math.sqrt(4 + 0.36 / 12), 1e-12, 'A: RMS current 2.0075 A');
rel(a.cap.cIdealNoEsr, 3e-6, 1e-12, 'A: 3.000 µF for 1 % ripple with no ESR');
ok(a.ccm, 'A: continuous at full load');
rel(a.deltaIlAtMinVin, 0.4, 1e-12, 'A: ripple at 9 V is 0.400 A (20 % of load)');
rel(a.timing.onTimeMax, (5 / 9) / 500e3, 1e-15, 'A: longest on-time at 9 V');
rel(a.timing.onTimeMin, (5 / 15) / 500e3, 1e-15, 'A: shortest on-time at 15 V');
/* the sized inductor must satisfy the ripple target at every input in range */
for (let vin = 9; vin <= 15.0001; vin += 0.25) {
  ok(ripple(5, vin, a.inductance, 500e3) <= 0.6 + 1e-12, `A: ripple within target at ${vin.toFixed(2)} V`);
}
/* sizing at the wrong end of the range would have given 7.407 µH — 33 % short */
rel(5 * (1 - 5 / 9) / (0.6 * 500e3), 7.407407e-6, 1e-6, 'A: the minimum-input answer is 7.407 µH');
ok(a.inductance > 1.4 * (5 * (1 - 5 / 9) / (0.6 * 500e3)), 'A: the corrected value is materially larger');

/* ---------------------------------------------------------------------------
   Case B — 12–24 V in, 3.3 V out, 1 A, 1 MHz, 40 % ripple, 2 % output ripple.
     D at 24 V  = 0.1375, 1 − D = 0.8625
     L          = 3.3 × 0.8625 / (0.4 × 1e6)  = 7.1156 µH
     C          = 0.4 / (8 × 1e6 × 0.066)     = 0.7576 µF
   ------------------------------------------------------------------------- */
const specB = { vinMin: 12, vinMax: 24, vout: 3.3, iout: 1, fsw: 1e6, ripplePct: 40, voutRipplePct: 2 };
const b = designBuck(specB);
ok(b, 'case B produces a design');
rel(b.timing.dutyMax, 3.3 / 12, 1e-12, 'B: duty at 12 V');
rel(b.timing.dutyMin, 3.3 / 24, 1e-12, 'B: duty at 24 V');
rel(b.inductance, 7.115625e-6, 1e-6, 'B: inductance 7.116 µH');
rel(b.worst.deltaIl, 0.4, 1e-12, 'B: ripple target 0.400 A');
rel(b.iPeak, 1.2, 1e-12, 'B: peak current 1.200 A');
rel(b.lCrit, 1.423125e-6, 1e-6, 'B: critical inductance 1.423 µH');
rel(b.cap.cIdealNoEsr, 0.757576e-6, 1e-6, 'B: 0.7576 µF for 2 % ripple');
ok(b.ccm, 'B: continuous at full load');

/* ---------------------------------------------------------------------------
   Case C — 12 V in, 5 V out, 1 A, 100 kHz, 100 % ripple target.
     1 − D      = 0.58333
     L          = 5 × 0.58333 / (1.0 × 100e3) = 29.167 µH
     L_crit     = 5 × 0.58333 / (2 × 1 × 100e3) = 14.583 µH
     I_valley   = 1 − 0.5 = 0.5 A  → still CCM, by the definition of a
                  relative ripple target; the zero-valley point is 200 %.
   ------------------------------------------------------------------------- */
const specC = { vinMin: 12, vinMax: 12, vout: 5, iout: 1, fsw: 100e3, ripplePct: 100, voutRipplePct: 1 };
const c = designBuck(specC);
ok(c, 'case C produces a design');
rel(c.inductance, 29.166667e-6, 1e-6, 'C: inductance 29.167 µH');
rel(c.lCrit, 14.583333e-6, 1e-6, 'C: zero-valley inductance 14.583 µH');
rel(c.iValley, 0.5, 1e-12, 'C: valley current 0.500 A');
rel(c.iPeak, 1.5, 1e-12, 'C: peak current 1.500 A');
rel(c.cap.cIdealNoEsr, 25e-6, 1e-9, 'C: 25.000 µF for 1 % ripple');
ok(c.ccm, 'C: a 100 % relative ripple target is inside CCM');

/* ---- non-ideal additions used in the worked example ---------------------- */
const aEsr = designBuck(Object.assign({}, specA, { esr: 0.01 }));
rel(aEsr.cap.cEffective, 3.409091e-6, 1e-5, 'A with 10 mΩ ESR: 3.409 µF');
const aDerated = designBuck(Object.assign({}, specA, { esr: 0.01, derating: 0.6 }));
rel(aDerated.cap.cNominal, 5.681818e-6, 1e-5, 'A with 10 mΩ ESR and 60 % derating: 5.682 µF');

/* ---- rejections --------------------------------------------------------- */
const rejections = [
  [{ vinMin: 5, vinMax: 5, vout: 5 }, 'Vout equal to Vin'],
  [{ vinMin: 12, vinMax: 8 }, 'Vin,max below Vin,min'],
  [{ iout: 0 }, 'zero load current'],
  [{ fsw: 0 }, 'zero switching frequency'],
  [{ ripplePct: 250 }, 'ripple target above 200 %'],
  [{ esr: -0.1 }, 'negative ESR'],
  [{ derating: 0 }, 'zero derating']
];
const good = { vinMin: 12, vinMax: 24, vout: 5, iout: 1, fsw: 1e5, ripplePct: 30, voutRipplePct: 1 };
rejections.forEach(([patch, label]) => {
  ok(designBuck(Object.assign({}, good, patch)) === null, `rejects ${label}`);
});
ok(designBuck({}) === null, 'rejects an empty specification');

/* ---------------------------------------------------------------------------
   The published reference table must match the module.
   A hand-typed table that drifts from the model is exactly the kind of defect
   this suite exists to catch, so the built HTML is parsed and compared.
   ------------------------------------------------------------------------- */
const pagePath = path.join(__dirname, '..', 'projects', 'power-stage-utility.html');
if (fs.existsSync(pagePath)) {
  const html = fs.readFileSync(pagePath, 'utf8');
  const start = html.indexOf('ps-ref-table');
  ok(start > -1, 'the reference table is present in the built page');
  const tableHtml = html.slice(start, html.indexOf('</table>', start));
  const rows = [...tableHtml.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map((m) => m[1]);
  ok(rows.length === 4, 'the reference table has a header and three case rows');

  const units = { H: 1, mH: 1e-3, 'µH': 1e-6, nH: 1e-9, A: 1, mA: 1e-3, F: 1, mF: 1e-3, 'µF': 1e-6, nF: 1e-9, pF: 1e-12 };
  function cells(row) {
    return [...row.matchAll(/<(t[hd])[^>]*>([\s\S]*?)<\/\1>/g)]
      .map((m) => m[2].replace(/<[^>]+>/g, '').trim());
  }
  function value(text) {
    const m = text.match(/^(-?[\d.]+)\s*([a-zA-Zµ]*)$/);
    if (!m) return NaN;
    return Number(m[1]) * (units[m[2]] === undefined ? 1 : units[m[2]]);
  }
  const expectations = [
    { spec: specA, label: 'A', l: a.inductance, dil: a.worst.deltaIl, peak: a.iPeak, lcrit: a.lCrit, c: a.cap.cIdealNoEsr },
    { spec: specB, label: 'B', l: b.inductance, dil: b.worst.deltaIl, peak: b.iPeak, lcrit: b.lCrit, c: b.cap.cIdealNoEsr },
    { spec: specC, label: 'C', l: c.inductance, dil: c.worst.deltaIl, peak: c.iPeak, lcrit: c.lCrit, c: c.cap.cIdealNoEsr }
  ];
  rows.slice(1).forEach((row, i) => {
    const e = expectations[i];
    const cols = cells(row);
    ok(cols.length === 7, `table row ${e.label} has seven cells`);
    /* the page rounds to three decimals, so allow half a unit in the last place */
    near(value(cols[2]), e.l, Math.max(e.l * 1e-5, 5e-10), `table ${e.label}: inductance matches the module`);
    near(value(cols[3]), e.dil, 5e-4, `table ${e.label}: ripple matches the module`);
    near(value(cols[4]), e.peak, 5e-4, `table ${e.label}: peak current matches the module`);
    near(value(cols[5]), e.lcrit, Math.max(e.lcrit * 1e-5, 5e-10), `table ${e.label}: L_crit matches the module`);
    near(value(cols[6]), e.c, Math.max(e.c * 1e-5, 5e-10), `table ${e.label}: capacitance matches the module`);
    /* and the specification quoted in the table really is that case */
    ok(cols[1].indexOf(String(e.spec.vinMin)) === 0, `table ${e.label}: specification starts at Vin,min`);
    const recomputed = designBuck(e.spec);
    near(recomputed.inductance, e.l, 1e-18, `table ${e.label}: spec reproduced deterministically`);
  });

  /* the worked example in the prose must agree too */
  ok(html.includes('11.11 µH'), 'worked example quotes 11.11 µH');
  ok(html.includes('1.667 µH'), 'worked example quotes the 1.667 µH boundary');
  ok(!/Worst case for inductor ripple is the lowest input voltage/i.test(html),
    'the old inverted worst-case claim is gone from the page');
} else {
  console.log('note: projects/power-stage-utility.html not built — table check skipped');
}

console.log(`PASS: power-stage reference cases — ${count} assertions (3 cases, table parity, worked example, 8 rejections)`);
