/* ===========================================================================
   tests/powerstage-independent.test.js

   An independent check of assets/powerstage.js. Nothing here re-uses the
   module's closed forms to build an expectation: every reference value is
   produced by a different method, so a defective equation in the module shows
   up as a disagreement rather than being asserted back to itself.

   Methods used as oracles:
     1. Time-domain integration of di/dt over one switching cycle, with the duty
        ratio found by bisection on the volt-second balance condition (the
        converter's own periodicity requirement), not from D = Vout/Vin.
     2. Numeric integration of the capacitor current to recover voltage ripple.
     3. Numeric integration of i² to recover RMS current.
     4. Dense input-voltage sweeps to locate the true worst case.
     5. Externally supplied hand figures for three reference cases, quoted in
        the engineering brief that commissioned the correction.
     6. Scaling and symmetry invariants that any correct model must satisfy.

   Usage: node tests/powerstage-independent.test.js
   ========================================================================== */
'use strict';
const assert = require('assert');
const PS = require('../assets/powerstage.js');
const { designBuck } = PS;

let checks = 0;
function ok(cond, label) { checks += 1; assert.ok(cond, label); }
function near(a, e, tol, label) {
  checks += 1;
  const err = Math.abs(a - e);
  assert.ok(err <= tol, `${label}: got ${a}, expected ${e} (Δ ${err} > ${tol})`);
}
function rel(a, e, tol, label) { near(a, e, Math.abs(e) * tol, label); }

/* =========================================================================
   1. Independent switching-cycle simulator
   -------------------------------------------------------------------------
   The inductor sees (Vin − Vout)/L while the high-side switch is on and
   −Vout/L while it is off. The steady-state duty ratio is whatever makes the
   net current change over one period zero; find it by bisection. Then measure
   the ripple directly.
   ========================================================================== */
function simulateCycle(vin, vout, L, fsw) {
  const T = 1 / fsw;
  const netDelta = (D) => ((vin - vout) * D * T - vout * (1 - D) * T) / L;
  let lo = 0, hi = 1;
  for (let i = 0; i < 200; i += 1) {
    const mid = (lo + hi) / 2;
    if (netDelta(mid) > 0) hi = mid; else lo = mid;
  }
  const D = (lo + hi) / 2;
  /* walk the cycle in small steps and track the extremes of the current */
  const steps = 2000;
  let I = 0, min = 0, max = 0;
  for (let i = 0; i < steps; i += 1) {
    const t = (i + 0.5) * T / steps;
    const slope = t < D * T ? (vin - vout) / L : -vout / L;
    I += slope * (T / steps);
    if (I < min) min = I;
    if (I > max) max = I;
  }
  return { duty: D, ripple: max - min, max, min };
}

function simulateCapRipple(vin, vout, L, fsw, C) {
  const T = 1 / fsw;
  const duty = vout / vin;                 /* steady state, from simulation below */
  const steps = 4000;
  const iout = (() => {
    /* mean inductor current over the cycle at the simulated duty */
    let sum = 0;
    for (let i = 0; i < steps; i += 1) {
      const t = (i + 0.5) * T / steps;
      const frac = t / T;
      const deltaIl = vout * (1 - vout / vin) / (L * fsw);
      sum += -deltaIl / 2 + deltaIl * frac;   /* triangular component only */
    }
    return sum / steps;                        /* ≈ 0 — the caps sees only ripple */
  })();
  let v = 0, vmin = 0, vmax = 0;
  for (let i = 0; i < steps; i += 1) {
    const t = (i + 0.5) * T / steps;
    const iL = -vout * (1 - vout / vin) / (L * fsw) / 2 +
      (vout * (1 - vout / vin) / (L * fsw)) * (t / T);
    const ic = iL - iout;
    v += (ic / C) * (T / steps);
    if (v < vmin) vmin = v;
    if (v > vmax) vmax = v;
  }
  return { ripple: vmax - vmin, duty };
}

/* --- 1a. the module's duty relation must match volt-second balance -------- */
[[12, 5], [15, 5], [9, 5], [24, 3.3], [48, 12]].forEach(([vin, vout]) => {
  const sim = simulateCycle(vin, vout, 22e-6, 500e3);
  rel(PS.duty(vout, vin), sim.duty, 1e-6, `duty parity with simulation at ${vin} V`);
});

/* --- 1b. ripple parity: closed form vs integrated current ----------------- */
[[12, 5, 22e-6, 500e3], [24, 3.3, 7.1156e-6, 1e6], [9, 5, 11.111e-6, 500e3], [15, 5, 11.111e-6, 500e3]]
  .forEach(([vin, vout, L, fsw]) => {
    const sim = simulateCycle(vin, vout, L, fsw);
    rel(PS.ripple(vout, vin, L, fsw), sim.ripple, 5e-3,
      `ripple parity with simulation at ${vin} V → ${vout} V`);
  });

/* --- 1c. the ripple must grow with input voltage, not shrink ------------- */
{
  const vout = 5, L = 11.111e-6, fsw = 500e3;
  let previous = -Infinity, rising = true;
  for (let vin = 6; vin <= 30; vin += 0.1) {
    const r = PS.ripple(vout, vin, L, fsw);
    if (r <= previous) rising = false;
    previous = r;
  }
  ok(rising, 'ΔI_L increases monotonically with Vin (dense sweep 6–30 V)');
  /* exact ratio from the (1 − Vout/Vin) factor: 9 V → 0.4444, 30 V → 0.8333 */
  rel(PS.ripple(vout, 30, L, fsw) / PS.ripple(vout, 9, L, fsw), (1 - 5 / 30) / (1 - 5 / 9),
    1e-9, 'ripple ratio between 30 V and 9 V follows (1 − Vout/Vin)');
}

/* --- 1d. dense sweep: the true maximum sits at V_in,max ------------------ */
{
  const spec = { vinMin: 9, vinMax: 15, vout: 5, iout: 2, fsw: 500e3, ripplePct: 30, voutRipplePct: 1 };
  const d = designBuck(spec);
  let worst = { vin: 0, ripple: -Infinity };
  for (let i = 0; i <= 400; i += 1) {
    const vin = 9 + (15 - 9) * i / 400;
    const r = PS.ripple(5, vin, d.inductance, 500e3);
    if (r > worst.ripple) worst = { vin, ripple: r };
  }
  rel(worst.vin, 15, 1e-9, 'sweep locates the worst-case ripple at V_in,max');
  rel(worst.ripple, d.worst.deltaIl, 5e-3, 'swept worst ripple equals the reported value');
  /* and the sized inductor must hold the target across the whole range */
  for (let i = 0; i <= 400; i += 1) {
    const vin = 9 + (15 - 9) * i / 400;
    const pct = PS.ripple(5, vin, d.inductance, 500e3) / 2 * 100;
    ok(pct <= 30 + 1e-9, `ripple stays within the 30 % target at ${vin.toFixed(2)} V`);
  }
}

/* =========================================================================
   2. External hand figures quoted in the engineering brief
   ========================================================================== */
/* Case A — 9–15 V → 5 V, 2 A, 500 kHz, 30 % ripple */
{
  const a = designBuck({ vinMin: 9, vinMax: 15, vout: 5, iout: 2, fsw: 500e3, ripplePct: 30, voutRipplePct: 1 });
  ok(a, 'case A produces a design');
  rel(a.inductance, 11.111e-6, 1e-3, 'case A inductance ≈ 11.111 µH');
  rel(a.lCrit, 1.6667e-6, 1e-3, 'case A critical inductance ≈ 1.667 µH');
  rel(a.iPeak, 2.3, 1e-9, 'case A peak current 2.3 A');
  rel(a.iValley, 1.7, 1e-9, 'case A valley current 1.7 A');
  ok(a.ccm, 'case A is comfortably continuous');
  rel(a.timing.dutyMax, 5 / 9, 1e-12, 'case A duty max at 9 V');
  rel(a.timing.dutyMin, 5 / 15, 1e-12, 'case A duty min at 15 V');
  ok(a.worst.vin === 15, 'case A worst-case ripple point is 15 V');
}

/* Case B — 12–24 V → 3.3 V, 1 A, 1 MHz, 40 % ripple */
{
  const b = designBuck({ vinMin: 12, vinMax: 24, vout: 3.3, iout: 1, fsw: 1e6, ripplePct: 40, voutRipplePct: 2 });
  ok(b, 'case B produces a design');
  rel(b.inductance, 7.116e-6, 2e-3, 'case B inductance ≈ 7.116 µH');
  rel(b.lCrit, 1.4231e-6, 2e-3, 'case B critical inductance ≈ 1.423 µH');
  rel(b.iPeak, 1.2, 1e-9, 'case B peak current 1.2 A');
}

/* Case C — 12 V → 5 V, 1 A, 100 kHz, 100 % ripple.
   The brief quotes 29.167 µH as the minimum ideal inductance. That is the
   inductance for the ripple *target*; the zero-valley boundary is half of it
   because ripple is quoted relative to Iout. Both must be reported, and the
   module must not confuse them. */
{
  const c = designBuck({ vinMin: 12, vinMax: 12, vout: 5, iout: 1, fsw: 100e3, ripplePct: 100, voutRipplePct: 1 });
  ok(c, 'case C produces a design');
  rel(c.inductance, 29.1667e-6, 1e-3, 'case C inductance ≈ 29.167 µH');
  rel(c.lCrit, 14.5833e-6, 1e-3, 'case C zero-valley boundary ≈ 14.583 µH');
  rel(c.inductance / c.lCrit, 2, 1e-9, 'at a 100 % ripple target L = 2·L_crit');
  rel(c.iValley, 0.5, 1e-9, 'case C valley is Iout/2 = 0.5 A, so still CCM');
  ok(c.ccm, 'a 100 % ripple target is inside CCM by definition');
}

/* =========================================================================
   3. CCM / DCM boundary behaviour
   ========================================================================== */
{
  const spec = { vinMin: 9, vinMax: 15, vout: 5, iout: 2, fsw: 500e3, ripplePct: 30, voutRipplePct: 1 };
  const d = designBuck(spec);
  const boundary = PS.criticalInductance(5, 15, 2, 500e3);
  rel(boundary, d.lCrit, 1e-12, 'critical inductance at Vin,max matches the module field');

  /* just below the boundary the valley must go negative */
  const below = designBuck(Object.assign({}, spec, { ripplePct: 200 })).inductance * 0.999;
  ok(PS.ripple(5, 15, below, 500e3) / 2 > 2, 'below L_crit the valley current is negative');

  /* the module must flag that case as non-continuous when it happens */
  const at200 = designBuck(Object.assign({}, spec, { ripplePct: 200 }));
  ok(Math.abs(at200.iValley) < 1e-12, 'a 200 % ripple target lands exactly on the boundary');
  ok(at200.ccm, 'the boundary itself is reported as continuous (valley = 0)');
  rel(at200.inductance, at200.lCrit, 1e-12, 'L at a 200 % target equals L_crit');

  /* L_crit grows with Vin too — a common place to get the worst case wrong */
  ok(PS.criticalInductance(5, 15, 2, 500e3) > PS.criticalInductance(5, 9, 2, 500e3),
    'L_crit is larger at Vin,max than at Vin,min');
  rel(d.lCritAtMinVin, PS.criticalInductance(5, 9, 2, 500e3), 1e-12, 'L_crit at Vin,min reported separately');
}

/* =========================================================================
   4. Scaling invariants — any correct model must satisfy these
   ========================================================================== */
{
  const base = { vinMin: 12, vinMax: 24, vout: 5, iout: 3, fsw: 400e3, ripplePct: 25, voutRipplePct: 1 };
  const b = designBuck(base);
  const doubleF = designBuck(Object.assign({}, base, { fsw: 800e3 }));
  rel(doubleF.inductance, b.inductance / 2, 1e-12, 'doubling fsw halves the inductance');
  const doubleRipple = designBuck(Object.assign({}, base, { ripplePct: 50 }));
  rel(doubleRipple.inductance, b.inductance / 2, 1e-12, 'doubling the ripple target halves the inductance');
  const doubleLoad = designBuck(Object.assign({}, base, { iout: 6 }));
  rel(doubleLoad.lCrit, b.lCrit / 2, 1e-12, 'doubling the load halves the boundary inductance');
  /* the ripple target is relative to the load, so doubling Iout doubles the
     absolute ripple allowance and halves the inductance */
  rel(doubleLoad.inductance, b.inductance / 2, 1e-12, 'a relative ripple target scales L with 1/Iout');
  rel(doubleLoad.deltaIlAtMinVin, 2 * b.deltaIlAtMinVin, 1e-12, 'absolute ripple doubles with the load');
  const wider = designBuck(Object.assign({}, base, { vinMax: 48 }));
  ok(wider.inductance > b.inductance, 'a wider input range requires more inductance');
  /* ripple must scale inversely with L at every point */
  [9, 12, 18, 24].forEach((vin) => {
    rel(PS.ripple(5, vin, b.inductance * 2, 400e3), PS.ripple(5, vin, b.inductance, 400e3) / 2,
      1e-12, `ripple ∝ 1/L at ${vin} V`);
  });
  /* on-time must run the opposite way to ripple */
  ok(b.timing.onTimeMax > b.timing.onTimeMin, 'longest on-time is at Vin,min');
  rel(b.timing.onTimeMax / b.timing.period, b.timing.dutyMax, 1e-12, 'on-time = D·T at Vin,min');
  rel(b.timing.onTimeMin / b.timing.period, b.timing.dutyMin, 1e-12, 'on-time = D·T at Vin,max');
}

/* =========================================================================
   5. RMS current — numeric integration of i²
   ========================================================================== */
{
  const spec = { vinMin: 9, vinMax: 15, vout: 5, iout: 2, fsw: 500e3, ripplePct: 30, voutRipplePct: 1 };
  const d = designBuck(spec);
  const deltaIl = d.worst.deltaIl, Iout = 2;
  const steps = 20000;
  let sum = 0;
  for (let i = 0; i < steps; i += 1) {
    const frac = (i + 0.5) / steps;
    const iL = Iout - deltaIl / 2 + deltaIl * frac;   /* triangle, symmetric */
    sum += iL * iL;
  }
  const rms = Math.sqrt(sum / steps);
  rel(d.iRms, rms, 1e-4, 'inductor RMS current matches numeric integration of i²');
  ok(d.iRms > Iout, 'RMS current exceeds the DC load current');
}

/* =========================================================================
   6. Output capacitor — numeric integration of the capacitor current
   ========================================================================== */
{
  const vin = 15, vout = 5, L = 11.111e-6, fsw = 500e3;
  [1e-6, 3e-6, 10e-6, 47e-6].forEach((C) => {
    const sim = simulateCapRipple(vin, vout, L, fsw, C);
    const formula = PS.capRipple(vout, vin, L, fsw, C);
    rel(formula, sim.ripple, 5e-3, `capacitive ripple ≈ ΔI_L/(8 f C) for C = ${C * 1e6} µF`);
  });

  const spec = { vinMin: 9, vinMax: 15, vout: 5, iout: 2, fsw: 500e3, ripplePct: 30, voutRipplePct: 1 };
  const d = designBuck(spec);
  rel(d.cap.cIdealNoEsr, 0.6 / (8 * 500e3 * 0.05), 1e-12, 'C for 1 % ripple with ESR = 0 is 3 µF');
  ok(d.cap.feasible, 'capacitor target is feasible with ESR = 0');

  /* ESR allowance must be subtracted from the budget before sizing C */
  const withEsr = designBuck(Object.assign({}, spec, { esr: 0.01 }));
  ok(withEsr.cap.esrRipple > 0, 'ESR contributes a ripple term');
  rel(withEsr.cap.esrRipple, 0.6 * 0.01, 1e-12, 'ESR ripple = ΔI_L · ESR');
  ok(withEsr.cap.cEffective > d.cap.cIdealNoEsr,
    'a nonzero ESR forces a larger capacitance for the same total ripple');
  rel(withEsr.cap.cEffective, 0.6 / (8 * 500e3 * (0.05 - 0.6 * 0.01)), 1e-9,
    'capacitance uses the ripple budget left after ESR');

  /* an ESR that eats the whole budget must be reported as infeasible */
  const hopeless = designBuck(Object.assign({}, spec, { esr: 0.2 }));
  ok(hopeless.cap.feasible === false, 'ESR above the ripple allowance is reported infeasible');
  ok(hopeless.cap.cEffective === Infinity, 'infeasible capacitor sizing returns Infinity, not a number');

  /* derating: nominal capacitance must be larger than the effective requirement */
  const derated = designBuck(Object.assign({}, spec, { derating: 0.5 }));
  rel(derated.cap.cNominal, derated.cap.cEffective * 2, 1e-12, '50 % derating doubles the nominal capacitance');

  /* transient floor */
  const tr = designBuck(Object.assign({}, spec, { loadStep: 1 }));
  ok(tr.cap.cTransient > 0, 'a load release produces a transient estimate');
  /* independently verify the energy balance it claims to solve */
  const C = tr.cap.cTransient, V = 5, dv = 0.05, Istep = 1;
  const stored = 0.5 * tr.inductance * Istep * Istep;
  const absorb = 0.5 * C * ((V + dv) * (V + dv) - V * V);
  rel(absorb, stored, 1e-9, 'transient capacitance satisfies the energy balance exactly');
  ok(tr.cap.cRequiredEffective >= tr.cap.cTransient - 1e-18,
    'the recommendation is never smaller than the transient floor');
  ok(tr.cap.cRequiredEffective >= tr.cap.cEffective - 1e-18,
    'the recommendation is never smaller than the ripple requirement');
  rel(tr.cap.cNominal, tr.cap.cRequiredEffective, 1e-12, 'no derating leaves the nominal value unchanged');

  rel(d.cap.rmsCurrent, 0.6 / Math.sqrt(12), 1e-12, 'capacitor RMS ripple current = ΔI_L/√12');
}

/* =========================================================================
   7. Operating-point sweep internal consistency
   ========================================================================== */
{
  const d = designBuck({ vinMin: 9, vinMax: 15, vout: 5, iout: 2, fsw: 500e3, ripplePct: 30, voutRipplePct: 1, sweepPoints: 9 });
  ok(d.sweep.length === 9, 'the sweep honours the requested number of points');
  rel(d.sweep[0].vin, 9, 1e-12, 'sweep starts at Vin,min');
  rel(d.sweep[d.sweep.length - 1].vin, 15, 1e-12, 'sweep ends at Vin,max');
  const last = d.sweep[d.sweep.length - 1];
  rel(last.deltaIl, d.worst.deltaIl, 1e-12, 'the sweep endpoint equals the reported worst case');
  rel(last.iPeak, d.iPeak, 1e-12, 'sweep peak current matches');
  let monotonic = true;
  for (let i = 1; i < d.sweep.length; i += 1) {
    if (d.sweep[i].deltaIl <= d.sweep[i - 1].deltaIl) monotonic = false;
    if (d.sweep[i].duty >= d.sweep[i - 1].duty) monotonic = false;
  }
  ok(monotonic, 'sweep ripple rises and duty falls as Vin rises');
}

/* =========================================================================
   8. Input validation
   ========================================================================== */
{
  const good = { vinMin: 12, vinMax: 24, vout: 5, iout: 1, fsw: 1e5, ripplePct: 30, voutRipplePct: 1 };
  const bad = [
    [{ vout: 12 }, 'Vout equal to Vin,min'],
    [{ vinMin: 24, vinMax: 12 }, 'Vin,max below Vin,min'],
    [{ iout: 0 }, 'zero load current'],
    [{ fsw: 0 }, 'zero switching frequency'],
    [{ fsw: -1e5 }, 'negative frequency'],
    [{ ripplePct: 0 }, 'zero ripple target'],
    [{ ripplePct: 201 }, 'ripple target above 200 %'],
    [{ voutRipplePct: 101 }, 'output ripple target above 100 %'],
    [{ esr: -0.01 }, 'negative ESR'],
    [{ derating: 0 }, 'zero derating'],
    [{ derating: 1.5 }, 'derating above 1'],
    [{ loadStep: -1 }, 'negative load step']
  ];
  bad.forEach(([patch, label]) => {
    ok(designBuck(Object.assign({}, good, patch)) === null, `rejects ${label}`);
  });
  ok(designBuck(null) === null, 'rejects a null specification');
  ok(designBuck({}) === null, 'rejects an empty specification');
  /* defaults must not change the headline numbers */
  const withDefaults = designBuck(good);
  const explicit = designBuck(Object.assign({}, good, { esr: 0, derating: 1, loadStep: 0 }));
  rel(withDefaults.inductance, explicit.inductance, 1e-15, 'omitted optional inputs default to ideal values');
}

console.log(`PASS: power-stage independent verification — ${checks} checks across 8 groups`);
