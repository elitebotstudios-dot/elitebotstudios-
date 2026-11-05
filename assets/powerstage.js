/* ===========================================================================
   powerstage.js — ideal buck power-stage sizing utility

   A small, dependency-free calculation module used by the "Power-stage sizing
   utility" demonstration page. It sizes an inductor and output capacitor from
   a specification, using the ideal continuous-conduction buck relations.

   ATTRIBUTION
   This module was written with AI assistance while building this website. It is
   a software demonstration, not the site owner's independent engineering work,
   and it does not describe a built or measured converter.

   MODEL LIMITS
   Ideal switches, ideal inductor (no DCR), ideal capacitor (no ESR), fixed
   switching frequency, steady-state CCM, negligible dead time. Real designs
   need device drops, ripple current heating, saturation margin, ESR ripple,
   loop stability and thermal verification. See the page for the full list.
   ========================================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.PowerStage = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  function positive(v) { return typeof v === 'number' && isFinite(v) && v > 0; }

  /**
   * @param {object} spec
   * @param {number} spec.vinMin  minimum input voltage [V]
   * @param {number} spec.vinMax  maximum input voltage [V]
   * @param {number} spec.vout    regulated output [V]
   * @param {number} spec.iout    maximum load current [A]
   * @param {number} spec.fsw     switching frequency [Hz]
   * @param {number} spec.ripplePct  desired peak-to-peak inductor ripple, % of iout
   * @param {number} spec.voutRipplePct  desired output voltage ripple, % of vout
   */
  function designBuck(spec) {
    var vinMin = spec.vinMin, vinMax = spec.vinMax, vout = spec.vout;
    var iout = spec.iout, fsw = spec.fsw;
    var ripplePct = spec.ripplePct, voutRipplePct = spec.voutRipplePct;

    if (!positive(vinMin) || !positive(vinMax) || !positive(vout) || !positive(iout) ||
        !positive(fsw) || !positive(ripplePct) || !positive(voutRipplePct)) return null;
    if (vinMax < vinMin) return null;
    if (vout >= vinMin) return null;            /* buck needs headroom at min input */
    if (ripplePct > 100 || voutRipplePct > 50) return null;

    var dutyMax = vout / vinMin;                /* worst case: lowest input */
    var dutyMin = vout / vinMax;
    var targetRipple = iout * ripplePct / 100;  /* A peak-to-peak */

    /* ΔIL = Vout (1 − D) / (L fsw)  ⇒  L = Vout (1 − D) / (ΔIL fsw)
       Worst case (largest ripple) is at minimum input, i.e. maximum duty. */
    var inductance = vout * (1 - dutyMax) / (targetRipple * fsw);
    var deltaIl = targetRipple;                 /* by construction at vinMin */
    var iPeak = iout + deltaIl / 2;
    var iValley = iout - deltaIl / 2;
    var iRms = Math.sqrt(iout * iout + (deltaIl * deltaIl) / 12);
    var lCrit = vout * (1 - dutyMax) / (2 * fsw * iout);
    var continuous = iValley >= 0;

    /* Ideal CCM output-capacitor estimate for a resistive load:
       ΔVout ≈ ΔIL / (8 fsw Cout)  ⇒  Cout = ΔIL / (8 fsw ΔVout) */
    var voutRipple = vout * voutRipplePct / 100;
    var capacitance = deltaIl / (8 * fsw * voutRipple);

    return {
      dutyMax: dutyMax, dutyMin: dutyMin,
      inductance: inductance, deltaIl: deltaIl,
      iPeak: iPeak, iValley: iValley, iRms: iRms,
      lCrit: lCrit, ccm: continuous,
      capacitance: capacitance, voutRipple: voutRipple,
      onTimeMax: dutyMax / fsw, period: 1 / fsw,
      /* Inductance that keeps ripple at the target at maximum input instead */
      inductanceMaxVin: vout * (1 - dutyMin) / (targetRipple * fsw)
    };
  }

  return { designBuck: designBuck };
}));
