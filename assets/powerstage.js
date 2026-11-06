/* ===========================================================================
   powerstage.js — ideal buck power-stage sizing (software demonstration)

   Turns a converter specification into an inductor value, a current-stress
   estimate and an output-capacitor estimate, using the ideal continuous
   conduction mode (CCM) buck relations:

     D(Vin)      = Vout / Vin                              (ideal conversion ratio)
     ΔI_L(Vin)   = Vout (1 − Vout/Vin) / (L fsw)            peak-to-peak ripple
     L_req       = Vout (1 − Vout/Vin,max) / (ΔI_L,tgt fsw)
     L_crit(Vin) = Vout (1 − Vout/Vin) / (2 Iout fsw)       zero-valley boundary
     V_ripple    = ΔI_L / (8 fsw C) + ΔI_L·ESR              capacitive + resistive

   WORST-CASE SELECTION
   ΔI_L(Vin) rises monotonically with Vin, because the off-time fraction
   (1 − Vout/Vin) grows as the input rises. Inductor ripple, peak current,
   valley current, inductor RMS current and the CCM boundary are therefore all
   worst at V_in,max. Duty and on-time move the other way and are worst at
   V_in,min. Both ends of the range are reported; nothing is evaluated at a
   single arbitrary voltage.

   ATTRIBUTION
   Written with AI assistance while building this website. It is a published
   software artefact, not the site owner's independent engineering work, and it
   does not describe a built, simulated or measured converter.

   MODEL LIMITS
   Ideal switches and diode (no forward drop), ideal inductor (no DCR, no core
   loss, no saturation), ideal capacitor apart from the ESR term the caller
   supplies, fixed switching frequency, steady-state CCM at full load, zero
   dead time, no loop dynamics. Capacitance figures are first-order estimates:
   see the cap object for which term each number comes from. Nothing here is a
   substitute for a datasheet, a vendor design tool or a bench measurement.
   ========================================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.PowerStage = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  function positive(v) { return typeof v === 'number' && isFinite(v) && v > 0; }
  function finite(v) { return typeof v === 'number' && isFinite(v); }
  function num(v, fallback) { return finite(v) ? v : fallback; }

  /* ---- single-operating-point relations (pure, independently testable) ---- */

  /** Ideal CCM duty ratio at one input voltage. */
  function duty(vout, vin) { return vout / vin; }

  /** Peak-to-peak inductor ripple for a given inductance at one input. */
  function ripple(vout, vin, inductance, fsw) {
    return vout * (1 - vout / vin) / (inductance * fsw);
  }

  /** Inductance at which the valley current reaches zero at full load. */
  function criticalInductance(vout, vin, iout, fsw) {
    return vout * (1 - vout / vin) / (2 * iout * fsw);
  }

  /** Capacitive part of the output ripple for a resistive load. */
  function capRipple(vout, vin, inductance, fsw, capacitance) {
    return ripple(vout, vin, inductance, fsw) / (8 * fsw * capacitance);
  }

  /** Output-capacitor RMS ripple current for a triangular ripple. */
  function capRms(deltaIl) { return deltaIl / Math.sqrt(12); }

  /* ------------------------------------------------------------- sizing ---- */
  /**
   * @param {object} spec
   * @param {number} spec.vinMin        minimum input voltage [V]
   * @param {number} spec.vinMax        maximum input voltage [V]
   * @param {number} spec.vout          regulated output voltage [V]
   * @param {number} spec.iout          full load current [A]
   * @param {number} spec.fsw           switching frequency [Hz]
   * @param {number} spec.ripplePct     inductor ripple target, % of iout (0–200]
   * @param {number} spec.voutRipplePct output ripple target, % of vout (0–100]
   * @param {number} [spec.esr]         output capacitor ESR [Ω], default 0
   * @param {number} [spec.derating]    fraction of nominal capacitance that
   *                                    remains after tolerance, DC bias and
   *                                    ageing, default 1 (no derating)
   * @param {number} [spec.loadStep]    load step used for the transient
   *                                    estimate [A], default 0 = not evaluated
   * @param {number} [spec.sweepPoints] points in the operating-point sweep
   * @returns {object|null} null when the specification is not sizeable
   */
  function designBuck(spec) {
    if (!spec || typeof spec !== 'object') return null;

    var vinMin = spec.vinMin, vinMax = spec.vinMax, vout = spec.vout;
    var iout = spec.iout, fsw = spec.fsw;
    var ripplePct = spec.ripplePct, voutRipplePct = spec.voutRipplePct;
    var esr = num(spec.esr, 0), derating = num(spec.derating, 1);
    var loadStep = num(spec.loadStep, 0);

    if (!positive(vinMin) || !positive(vinMax) || !positive(vout) ||
        !positive(iout) || !positive(fsw) || !positive(ripplePct) ||
        !positive(voutRipplePct)) return null;
    if (vinMax < vinMin) return null;
    if (vout >= vinMin) return null;          /* buck needs headroom at vinMin */
    if (ripplePct > 200 || voutRipplePct > 100) return null;
    if (esr < 0 || !(derating > 0) || derating > 1 || loadStep < 0) return null;

    var targetRipple = iout * ripplePct / 100;      /* A peak-to-peak */
    var voutRipple = vout * voutRipplePct / 100;    /* V peak-to-peak allowance */

    /* Ripple is worst at V_in,max: the off-time fraction is largest there. */
    var dutyMin = duty(vout, vinMax);               /* duty at vinMax */
    var dutyMax = duty(vout, vinMin);               /* duty at vinMin */
    var inductance = ripplePct === 200
      ? criticalInductance(vout, vinMax, iout, fsw)
      : vout * (1 - dutyMin) / (targetRipple * fsw);

    var deltaIlWorst = ripple(vout, vinMax, inductance, fsw);
    var deltaIlMinVin = ripple(vout, vinMin, inductance, fsw);

    var iPeak = iout + deltaIlWorst / 2;
    var iValley = iout - deltaIlWorst / 2;
    var iRms = Math.sqrt(iout * iout + (deltaIlWorst * deltaIlWorst) / 12);

    var lCritWorst = criticalInductance(vout, vinMax, iout, fsw);
    var lCritMinVin = criticalInductance(vout, vinMin, iout, fsw);

    /* ---- output capacitor -------------------------------------------------
       ΔVout = ΔI_L/(8 fsw C)  [capacitive]
             + ΔI_L·ESR        [resistive, added as a worst-case sum]
       The ESR term is subtracted from the budget first; if it consumes the whole
       allowance no capacitance can meet the target. */
    var esrRipple = deltaIlWorst * esr;
    var capBudget = voutRipple - esrRipple;
    var capFeasible = capBudget > 1e-12;
    var cEffective = capFeasible ? deltaIlWorst / (8 * fsw * capBudget) : Infinity;
    var cIdealNoEsr = deltaIlWorst / (8 * fsw * voutRipple);

    /* ---- transient estimate (load release, energy balance) ----------------
       ½ L ΔI² = ½ C ((V + δ)² − V²) = C V δ (1 + δ/(2V))
       Assumes the loop restores the inductor current only after the excursion,
       ignores ESR and loop bandwidth. A first-order floor, not a loop design. */
    var cTransient = 0;
    if (loadStep > 0) {
      cTransient = inductance * loadStep * loadStep /
        (2 * vout * voutRipple * (1 + voutRipple / (2 * vout)));
    }
    var cRequiredEffective = Math.max(capFeasible ? cEffective : Infinity, cTransient);
    var cNominal = isFinite(cRequiredEffective) ? cRequiredEffective / derating : Infinity;

    /* ---- operating-point sweep across the input range --------------------- */
    var points = Math.max(2, Math.min(41, Math.round(num(spec.sweepPoints, 9))));
    var sweep = [];
    for (var i = 0; i < points; i += 1) {
      var vin = points === 1 ? vinMax : vinMin + (vinMax - vinMin) * i / (points - 1);
      var dIl = ripple(vout, vin, inductance, fsw);
      sweep.push({
        vin: vin,
        duty: duty(vout, vin),
        deltaIl: dIl,
        ripplePct: (dIl / iout) * 100,
        iPeak: iout + dIl / 2,
        iValley: iout - dIl / 2,
        onTime: duty(vout, vin) / fsw,
        capRipple: dIl / (8 * fsw * (isFinite(cNominal) && cNominal > 0 ? cNominal * derating : 1))
      });
    }

    return {
      /* worst-case operating point for ripple-shaped quantities */
      worst: {
        vin: vinMax,
        duty: dutyMin,
        deltaIl: deltaIlWorst,
        iPeak: iPeak,
        iValley: iValley,
        iRms: iRms
      },
      /* worst-case operating point for duty and on-time */
      timing: {
        dutyMin: dutyMin,
        dutyMax: dutyMax,
        onTimeMin: dutyMin / fsw,
        onTimeMax: dutyMax / fsw,
        period: 1 / fsw
      },
      deltaIlAtMinVin: deltaIlMinVin,
      rippleTargetA: targetRipple,
      inductance: inductance,
      iPeak: iPeak,
      iValley: iValley,
      iRms: iRms,
      lCrit: lCritWorst,
      lCritAtMinVin: lCritMinVin,
      ccm: iValley >= 0,
      ripplePctActual: (deltaIlWorst / iout) * 100,
      /* inductance required at the *minimum* input, for comparison only */
      inductanceAtMinVin: vout * (1 - dutyMax) / (targetRipple * fsw),
      /* rule of thumb only: saturation rating with 20 % headroom over I_peak */
      satRecommend: 1.2 * iPeak,
      cap: {
        voutRippleTarget: voutRipple,
        esr: esr,
        esrRipple: esrRipple,
        capBudget: capFeasible ? capBudget : 0,
        feasible: capFeasible,
        cIdealNoEsr: cIdealNoEsr,
        cEffective: cEffective,
        cTransient: cTransient,
        cRequiredEffective: cRequiredEffective,
        derating: derating,
        cNominal: cNominal,
        rmsCurrent: capRms(deltaIlWorst)
      },
      loadStep: loadStep,
      sweep: sweep
    };
  }

  return {
    designBuck: designBuck,
    duty: duty,
    ripple: ripple,
    criticalInductance: criticalInductance,
    capRipple: capRipple,
    capRms: capRms
  };
}));
