/* ===========================================================================
   dcem.js — Smart DC Energy Monitor, Software Model V1

   A dependency-free model of a low-voltage DC energy-monitoring system:

     DC source -> load -> sensing -> ADC -> sampled processing -> energy

   Everything here is simulated. There is no hardware, no sensor, no ADC and
   no measurement of a real circuit in this file. The point of the model is to
   make the arithmetic and the error behaviour inspectable and testable before
   any hardware exists.

   DESIGN
   - The source and the load are solved together, so voltage, current and
     resistance can never contradict each other. A source with internal
     resistance and a resistive load produce one consistent operating point.
   - The measurement chain reproduces the sequence a real firmware would see:
     sensitivity -> amplifier gain error -> offset -> noise -> ADC code ->
     reconstructed engineering value -> optional calibration correction.
   - Energy is accumulated from the actual timestamps of accepted samples with
     the trapezoidal rule. Timestamps are never assumed to be uniformly spaced.
   - Nothing is silently discarded: rejected samples are counted and classified.

   CONVENTIONS
   - Time [s], voltage [V], current [A], resistance [ohm], power [W],
     energy [J] and [Wh]. 1 Wh = 3600 J.
   - Positive current is delivered to the load. Imported energy is the integral
     of positive power, exported energy the integral of negative power; they are
     integrated separately, splitting the interval at a sign change.
   - Load steps are right-continuous: the new state applies from the instant of
     the step. An interval that straddles a step is charged the trapezoidal
     average of its two endpoints, which is stated wherever a reference value
     depends on it.

   LIMITS (see docs/model.md for the full list)
   - Ideal wires, no inductance, no capacitance, no thermal effects.
   - The noise source is a fixed-seed PRNG, not a characterisation of a sensor.
   - Quantisation is ideal uniform rounding; no INL, DNL, missing codes or
     reference drift. A channel with adcBits = 0 is treated as an ideal
     transducer with no input range, which is how the reference cases isolate
     the energy arithmetic from the sensing chain.
   ========================================================================== */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.DCEM = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var VERSION = '1.0.0';
  var WH_PER_J = 1 / 3600;
  var ABS_MAX = 1e6;          /* |value| above this is treated as out of range */

  /* ------------------------------------------------------------------ util -- */
  function finite(v) { return typeof v === 'number' && isFinite(v); }
  function positive(v) { return finite(v) && v > 0; }
  function num(v, fallback) { return finite(v) ? v : fallback; }
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

  /* Deterministic PRNG (mulberry32). A fixed seed makes every run, and every
     reference dataset, reproducible — required for a testable model. */
  function makeRng(seed) {
    var a = (seed >>> 0) || 1;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* Box-Muller transform on two uniform draws. */
  function gaussian(rng) {
    var u = rng() || 1e-12, v = rng();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  /* ---------------------------------------------------------------- source -- */
  /* Source models, all expressed as an open-circuit voltage plus an internal
     series resistance. Rs = 0 is an ideal supply.

     modes:
       constant  { voc }
       droop     { voc, rs }              value is just Rs; named for clarity
       step      { voc, stepAt, vocAfter }
       ripple    { voc, rippleAmp, rippleHz }   deterministic sine, not random
       profile   { points: [{t, voc}, ...] }     piecewise-constant, right-continuous
  */
  function sourceConfig(raw) {
    var cfg = raw || {};
    return {
      mode: cfg.mode || 'constant',
      voc: num(cfg.voc, 12),
      rs: Math.max(0, num(cfg.rs, 0)),
      stepAt: num(cfg.stepAt, 0),
      vocAfter: num(cfg.vocAfter, num(cfg.voc, 12)),
      rippleAmp: Math.max(0, num(cfg.rippleAmp, 0)),
      rippleHz: positive(cfg.rippleHz) ? cfg.rippleHz : 50,
      points: Array.isArray(cfg.points) ? cfg.points.slice() : null
    };
  }

  /** Open-circuit voltage of the source at time t [s]. */
  function sourceVoc(src, t) {
    switch (src.mode) {
      case 'step': return t < src.stepAt ? src.voc : src.vocAfter;
      case 'ripple': return src.voc + src.rippleAmp * Math.sin(2 * Math.PI * src.rippleHz * t);
      case 'profile': {
        if (!src.points || !src.points.length) return src.voc;
        var v = src.points[0].voc;
        for (var i = 0; i < src.points.length; i += 1) {
          if (t >= src.points[i].t) v = src.points[i].voc;
        }
        return v;
      }
      default: return src.voc;
    }
  }

  /* ------------------------------------------------------------------ load -- */
  /* Load models. Every model yields the same shape: either a resistance or a
     demanded current. The operating point is then solved with the source.

     modes:
       resistive  { r }                                  I = Voc / (Rs + R)
       current    { i }                                  I = i, V = Voc - I·Rs
       step       { iBefore, iAfter, stepAt }             right-continuous
       duty       { period, duty, iOn, iOff }             phase = t mod period
       sequence   { points: [{t, i}, ...] }               right-continuous
  */
  function loadConfig(raw, warnings) {
    var cfg = raw || {};
    if (cfg.r !== undefined && !positive(cfg.r)) {
      warnings.push('load resistance must be greater than zero; using the 10 ohm default');
    }
    if (cfg.period !== undefined && !positive(cfg.period)) {
      warnings.push('duty-cycle period must be greater than zero; using the 60 s default');
    }
    return {
      mode: cfg.mode || 'resistive',
      r: positive(cfg.r) ? cfg.r : 10,
      i: Math.max(0, num(cfg.i, 1)),
      iBefore: Math.max(0, num(cfg.iBefore, num(cfg.i, 1))),
      iAfter: Math.max(0, num(cfg.iAfter, 0.5)),
      stepAt: num(cfg.stepAt, 0),
      period: positive(cfg.period) ? cfg.period : 60,
      duty: clamp(num(cfg.duty, 0.5), 0, 1),
      iOn: Math.max(0, num(cfg.iOn, 1)),
      iOff: Math.max(0, num(cfg.iOff, 0)),
      points: Array.isArray(cfg.points) ? cfg.points.slice() : null
    };
  }

  /** The load's demand at time t: { resistance } or { current }. */
  function loadState(load, t) {
    switch (load.mode) {
      case 'current': return { resistance: null, current: load.i };
      case 'step': return { resistance: null, current: t < load.stepAt ? load.iBefore : load.iAfter };
      case 'duty': {
        var phase = load.period > 0 ? (t % load.period) : 0;
        return { resistance: null, current: phase < load.duty * load.period ? load.iOn : load.iOff };
      }
      case 'sequence': {
        if (!load.points || !load.points.length) return { resistance: null, current: load.i };
        var i = load.points[0].i;
        for (var k = 0; k < load.points.length; k += 1) {
          if (t >= load.points[k].t) i = load.points[k].i;
        }
        return { resistance: null, current: Math.max(0, i) };
      }
      default: return { resistance: load.r, current: null };
    }
  }

  /** True operating point at time t, solving source and load together. */
  function operatingPoint(src, load, t) {
    var voc = sourceVoc(src, t);
    var state = loadState(load, t);
    var rs = src.rs;
    var i, v;
    if (state.resistance !== null) {
      i = voc / (rs + state.resistance);
      v = i * state.resistance;
    } else {
      i = state.current;
      v = voc - i * rs;
      if (v < 0) { v = 0; }               /* source cannot supply beyond Voc */
    }
    return { t: t, voc: voc, v: v, i: i, p: v * i, load: state, sourceLoss: i * i * rs };
  }

  /* ----------------------------------------------------------- measurement -- */
  /* One channel of the sensing chain, in the order a real signal experiences:

       engineering value
         -> × sensitivity            [V per V] or [V per A] at the ADC pin
         -> × (1 + gainError)        amplifier tolerance
         -> + offsetV                amplifier / ADC offset at the pin
         -> + noiseRms · N(0,1)
         -> sample-and-hold, clipped to the ADC input range [0, vref]
         -> quantise to nearest LSB  code = round(vin / lsb)
         -> reconstruct: naive (nominal sensitivity) or calibrated

     The reported value is what a firmware without calibration would print,
     i.e. (code · lsb) / sensitivity. With calibration enabled the estimates
     supplied by the caller replace sensitivity and offset.
  */
  function channelConfig(raw, warnings, label) {
    var cfg = raw || {};
    var bits = Math.round(num(cfg.adcBits, 12));
    if (cfg.adcBits !== undefined && !(bits >= 0 && bits <= 32)) {
      warnings.push(label + ' ADC bits outside 0–32; using ' + Math.max(0, Math.min(32, bits)));
      bits = Math.max(0, Math.min(32, bits));
    }
    if (cfg.sensitivity !== undefined && !positive(cfg.sensitivity)) {
      warnings.push(label + ' sensitivity must be greater than zero; using 1');
    }
    if (cfg.adcVref !== undefined && !positive(cfg.adcVref)) {
      warnings.push(label + ' ADC reference must be greater than zero; using 3.3 V');
    }
    var cal = cfg.calibration || {};
    return {
      sensitivity: positive(cfg.sensitivity) ? cfg.sensitivity : 1,
      gainError: finite(cfg.gainError) ? cfg.gainError : 0,
      offsetV: finite(cfg.offsetV) ? cfg.offsetV : 0,
      noiseRms: Math.max(0, num(cfg.noiseRms, 0)),
      adcBits: bits,
      adcVref: positive(cfg.adcVref) ? cfg.adcVref : 3.3,
      /* Calibration is stored per channel: a divider and a shunt amplifier have
         independent tolerances, so one correction cannot apply to both. */
      calibration: {
        enabled: !!cal.enabled,
        gainEstimate: finite(cal.gainEstimate) ? cal.gainEstimate : 0,
        offsetEstimateV: finite(cal.offsetEstimateV) ? cal.offsetEstimateV : 0
      }
    };
  }

  function channelLsb(ch) {
    if (!(ch.adcBits > 0)) return 0;
    return ch.adcVref / Math.pow(2, ch.adcBits);
  }

  /** Read one channel. Returns the measured value plus the intermediate states. */
  function readChannel(ch, trueValue, rng) {
    var amplified = trueValue * ch.sensitivity * (1 + ch.gainError) + ch.offsetV;
    if (ch.noiseRms > 0 && rng) amplified += ch.noiseRms * gaussian(rng);
    var lsb = channelLsb(ch);
    var maxCode = ch.adcBits > 0 ? Math.pow(2, ch.adcBits) - 1 : null;
    /* adcBits = 0 means "no ADC": the channel is an ideal transducer with no
       input range, used for reference cases that isolate the energy arithmetic. */
    var pin = ch.adcBits > 0 ? clamp(amplified, 0, ch.adcVref) : amplified;
    var saturated = ch.adcBits > 0 && pin !== amplified;
    var code = null;
    if (ch.adcBits > 0) {
      code = clamp(Math.round(pin / lsb), 0, maxCode);
    }
    var pinReconstructed = code === null ? pin : code * lsb;
    var gain = ch.sensitivity * (1 + ch.gainError);
    var value;
    var calib = ch.calibration;
    if (calib && calib.enabled) {
      /* The correction inverts the estimated gain (nominal sensitivity times the
         estimated error) and removes the estimated offset. */
      var gainCal = ch.sensitivity * (1 + calib.gainEstimate);
      value = (pinReconstructed - calib.offsetEstimateV) / gainCal;
    } else {
      value = pinReconstructed / ch.sensitivity;
    }
    return {
      value: value,
      pin: pin,
      code: code,
      lsb: lsb,
      saturated: saturated,
      amplified: amplified
    };
  }

  /* -------------------------------------------------------------- sampling -- */
  /* The sampler holds the state an embedded loop would hold between samples:
     the previous power sample (for the trapezoidal rule), the accumulators and
     the counters. Steps must be monotonic in time; anything else is rejected
     and counted rather than integrated. */
  function createSampler(config) {
    var cfg = normalizeConfig(config);
    var rng = makeRng(cfg.noiseSeed);
    var samples = [];
    var counters = { accepted: 0, rejected: 0, saturated: 0, rejectedByCode: {} };
    var energy = { importJ: 0, exportJ: 0 };
    var prev = null;
    var lastAcceptedT = null;
    var filter = { v: null, i: null };

    function reject(code, t, detail) {
      counters.rejected += 1;
      counters.rejectedByCode[code] = (counters.rejectedByCode[code] || 0) + 1;
      return { ok: false, code: code, t: t, detail: detail || null };
    }

    function step(t) {
      if (!finite(t)) return reject('NON_NUMERIC_TIMESTAMP', t);
      if (Math.abs(t) > ABS_MAX) return reject('OUT_OF_RANGE', t, 'timestamp');
      if (lastAcceptedT !== null) {
        if (t === lastAcceptedT) return reject('DUPLICATE_TIMESTAMP', t);
        if (t < lastAcceptedT) return reject('NON_MONOTONIC_TIMESTAMP', t);
      }
      var point = operatingPoint(cfg.src, cfg.load, t);
      if (!finite(point.v) || !finite(point.i) || !finite(point.p)) {
        return reject('NON_FINITE_OPERATING_POINT', t);
      }
      if (Math.abs(point.v) > ABS_MAX || Math.abs(point.i) > ABS_MAX) {
        return reject('OUT_OF_RANGE', t, 'operating point');
      }

      var vRead = readChannel(cfg.vChannel, point.v, rng);
      var iRead = readChannel(cfg.iChannel, point.i < 0 ? 0 : point.i, rng);

      var vOut = vRead.value;
      var iOut = iRead.value;

      /* Optional first-order low-pass on the measured signals. Off by default:
         it changes reference results, so it is an explicit choice. */
      if (cfg.filter.enabled) {
        var a = cfg.filter.alpha;
        filter.v = filter.v === null ? vOut : filter.v + a * (vOut - filter.v);
        filter.i = filter.i === null ? iOut : filter.i + a * (iOut - filter.i);
        vOut = filter.v;
        iOut = filter.i;
      }

      var measuredP = vOut * iOut;
      var current = {
        t: t,
        vTrue: point.v, iTrue: point.i, pTrue: point.p,
        vMeas: vOut, iMeas: iOut, pMeas: measuredP,
        energyWh: 0,
        fields: {
          voc: point.voc, loadCurrentDemand: point.load.current,
          loadResistance: point.load.resistance, sourceLoss: point.sourceLoss
        },
        adc: { vCode: vRead.code, iCode: iRead.code, lsbV: vRead.lsb, iLsb: iRead.lsb }
      };

      var saturated = vRead.saturated || iRead.saturated;
      if (saturated) counters.saturated += 1;

      var e = 0;
      if (prev) {
        var dt = t - prev.t;
        if (!(dt > 0)) return reject('NEGATIVE_INTERVAL', t);
        var pRef = cfg.reference === 'true' ? 'pTrue' : 'pMeas';
        e = integrateInterval(prev[pRef], current[pRef], dt, energy);
      }
      current.energyWh = (energy.importJ - energy.exportJ) * WH_PER_J;
      prev = current;
      lastAcceptedT = t;
      counters.accepted += 1;
      samples.push(current);
      return { ok: true, sample: current, saturated: saturated };
    }

    function results() {
      var total = (energy.importJ - energy.exportJ) * WH_PER_J;
      var trueEnergy = trueEnergyOf(samples);
      var measurable = samples.length;
      var sumP = 0, sumV = 0, sumI = 0, maxP = 0;
      for (var i = 0; i < measurable; i += 1) {
        sumP += samples[i].pMeas;
        sumV += samples[i].vMeas;
        sumI += samples[i].iMeas;
        if (samples[i].pMeas > maxP) maxP = samples[i].pMeas;
      }
      return {
        version: VERSION,
        warnings: cfg.warnings || [],
        sampleCount: samples.length,
        accepted: counters.accepted,
        rejected: counters.rejected,
        rejectedByCode: counters.rejectedByCode,
        saturated: counters.saturated,
        durationS: samples.length > 1 ? samples[samples.length - 1].t - samples[0].t : 0,
        energyJ: energy.importJ - energy.exportJ,
        energyWh: total,
        importWh: energy.importJ * WH_PER_J,
        exportWh: energy.exportJ * WH_PER_J,
        trueEnergyJ: trueEnergy.joules,
        trueEnergyWh: trueEnergy.joules * WH_PER_J,
        meanPowerW: measurable ? sumP / measurable : 0,
        meanVoltageV: measurable ? sumV / measurable : 0,
        meanCurrentA: measurable ? sumI / measurable : 0,
        maxPowerW: maxP,
        energyErrorPct: trueEnergy.joules ? ((energy.importJ - energy.exportJ) - trueEnergy.joules) / trueEnergy.joules * 100 : null
      };
    }

    return { step: step, results: results, samples: samples, config: cfg };
  }

  /* Trapezoidal area of one interval, split at a sign change so imported and
     exported energy are each integrated over the region where they apply. */
  function integrateInterval(p0, p1, dt, acc) {
    if (p0 >= 0 && p1 >= 0) {
      var positive = (p0 + p1) / 2 * dt;
      acc.importJ += positive;
      return positive;
    }
    if (p0 <= 0 && p1 <= 0) {
      var negative = (p0 + p1) / 2 * dt;
      acc.exportJ += -negative;
      return negative;
    }
    /* sign change inside the interval: locate the crossing by linear interpolation */
    var frac = p0 / (p0 - p1);
    var dt1 = dt * frac, dt2 = dt - dt1;
    var a1 = p0 / 2 * dt1;          /* triangle, ends at zero */
    var a2 = p1 / 2 * dt2;
    if (a1 > 0) acc.importJ += a1; else acc.exportJ += -a1;
    if (a2 > 0) acc.importJ += a2; else acc.exportJ += -a2;
    return a1 + a2;
  }

  /* True (unmeasured) energy of a sample set, for comparison in results. */
  function trueEnergyOf(samples) {
    var acc = { importJ: 0, exportJ: 0 };
    for (var i = 0; i < samples.length; i += 1) {
      if (i === 0) continue;
      integrateInterval(samples[i - 1].pTrue, samples[i].pTrue, samples[i].t - samples[i - 1].t, acc);
    }
    return { joules: acc.importJ - acc.exportJ, importJ: acc.importJ, exportJ: acc.exportJ };
  }

  /* ------------------------------------------------------------ validation -- */
  /* Validates a series of {t, p} or full samples before integration. Returns a
     classification for every problem found; never throws, never guesses. */
  function validateSeries(series) {
    var issues = [];
    if (!Array.isArray(series)) {
      return { ok: false, issues: [{ index: -1, code: 'NOT_A_SERIES', detail: 'expected an array' }] };
    }
    if (series.length === 0) {
      return { ok: false, issues: [{ index: -1, code: 'EMPTY_SERIES', detail: 'no samples' }] };
    }
    var prevT = null;
    for (var i = 0; i < series.length; i += 1) {
      var s = series[i] || {};
      var t = s.t;
      if (!finite(t)) {
        issues.push({ index: i, code: 'MISSING_OR_NON_NUMERIC_TIMESTAMP', detail: String(t) });
        continue;
      }
      if (Math.abs(t) > ABS_MAX) issues.push({ index: i, code: 'TIMESTAMP_OUT_OF_RANGE', detail: String(t) });
      var p = s.p !== undefined ? s.p : s.pMeas;
      if (!finite(p)) issues.push({ index: i, code: 'NON_FINITE_POWER', detail: String(p) });
      else if (Math.abs(p) > ABS_MAX) issues.push({ index: i, code: 'POWER_OUT_OF_RANGE', detail: String(p) });
      if (prevT !== null) {
        if (t === prevT) issues.push({ index: i, code: 'DUPLICATE_TIMESTAMP', detail: String(t) });
        else if (t < prevT) issues.push({ index: i, code: 'NON_MONOTONIC_TIMESTAMP', detail: String(t) });
      }
      prevT = t;
    }
    return { ok: issues.length === 0, issues: issues };
  }

  /* Integrate an arbitrary {t, p} series with the trapezoidal rule on the actual
     intervals. Refuses invalid input instead of returning a plausible number. */
  function integrateSeries(series) {
    var check = validateSeries(series);
    if (!check.ok) {
      return { ok: false, error: 'INVALID_SERIES', issues: check.issues, energyJ: null, energyWh: null };
    }
    var acc = { importJ: 0, exportJ: 0 };
    for (var i = 1; i < series.length; i += 1) {
      var a = series[i - 1], b = series[i];
      var pa = a.p !== undefined ? a.p : a.pMeas;
      var pb = b.p !== undefined ? b.p : b.pMeas;
      integrateInterval(pa, pb, b.t - a.t, acc);
    }
    return {
      ok: true,
      energyJ: acc.importJ - acc.exportJ,
      energyWh: (acc.importJ - acc.exportJ) * WH_PER_J,
      importJ: acc.importJ,
      exportJ: acc.exportJ,
      importWh: acc.importJ * WH_PER_J,
      exportWh: acc.exportJ * WH_PER_J,
      durationS: series[series.length - 1].t - series[0].t
    };
  }

  /* ---------------------------------------------------------------- config -- */
  function normalizeConfig(raw) {
    var cfg = raw || {};
    var meas = cfg.measurement || {};
    var warnings = [];
    if (cfg.sampleInterval !== undefined && !positive(cfg.sampleInterval)) {
      warnings.push('sample interval must be greater than zero; using 1 s');
    }
    if (cfg.duration !== undefined && !positive(cfg.duration)) {
      warnings.push('duration must be greater than zero; using 60 s');
    }
    return {
      warnings: warnings,
      src: sourceConfig(cfg.source),
      load: loadConfig(cfg.load, warnings),
      vChannel: channelConfig(meas.voltage, warnings, 'voltage'),
      iChannel: channelConfig(meas.current, warnings, 'current'),
      filter: {
        enabled: !!(meas.filter && meas.filter.enabled),
        alpha: meas.filter && positive(meas.filter.alpha) ? Math.min(1, meas.filter.alpha) : 1
      },
      noiseSeed: Math.round(num(cfg.noiseSeed, 12345)),
      reference: cfg.reference === 'true' ? 'true' : 'measured',
      sampleInterval: positive(cfg.sampleInterval) ? cfg.sampleInterval : 1,
      duration: positive(cfg.duration) ? cfg.duration : 60
    };
  }

  /**
   * Run a complete simulation: samples at t = 0, dt, 2dt … duration.
   * Returns the samples, the aggregated results and the rejected events.
   */
  function simulate(config) {
    var cfg = normalizeConfig(config);
    var sampler = createSampler(config);
    var dt = cfg.sampleInterval;
    var n = Math.floor(cfg.duration / dt);
    var rejected = [];
    for (var k = 0; k <= n; k += 1) {
      var out = sampler.step(k * dt);
      if (!out.ok) rejected.push(out);
    }
    var results = sampler.results();
    results.config = cfg;
    results.rejectedEvents = rejected;
    return { samples: sampler.samples, results: results };
  }


  /* -------------------------------------------------------------- presets -- */
  /* One set of configurations shared by the dashboard and the tests. Each entry
     is a complete, valid configuration; the dashboard renders them directly,
     and the independent test suite runs every one of them. */

  var CHAIN_DEFAULT = {
    voltage: { sensitivity: 0.25, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 12,
               adcVref: 3.3, calibration: { enabled: false, gainEstimate: 0, offsetEstimateV: 0 } },
    current: { sensitivity: 0.5, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 12,
               adcVref: 3.3, calibration: { enabled: false, gainEstimate: 0, offsetEstimateV: 0 } }
  };

  var PRESETS = [
    {
      id: 'constant-load',
      name: 'Constant resistive load',
      experiment: 1,
      tagline: 'One load, one voltage, one steady power.',
      description: 'A 12 V supply feeding a 12 Ω resistive load. The current is not chosen: it follows from the supply and the resistance, and power follows from both.',
      observe: [
        'Power stays at 12 W, so the energy graph is a straight line with slope 12 W.',
        'Voltage and current are flat: nothing in the chain is time-varying yet.',
        'The measured trace sits a fraction of an LSB away from the true trace.'
      ],
      config: {
        source: { mode: 'constant', voc: 12, rs: 0 },
        load: { mode: 'resistive', r: 12 },
        measurement: CHAIN_DEFAULT,
        sampleInterval: 0.5,
        duration: 300,
        noiseSeed: 20261106
      }
    },
    {
      id: 'step-load',
      name: 'Step-changing load',
      experiment: 2,
      tagline: 'The load halves; the energy slope halves with it.',
      description: 'A 10 V supply with a current-controlled load stepping from 1 A to 0.5 A at 150 s. Power steps from 10 W to 5 W.',
      observe: [
        'The energy graph bends at the step: its slope is power, so the slope halves.',
        'The accumulator never loses the energy it has already collected.',
        'The sampled step is smeared over one interval — that is integration error, not a physical ramp.'
      ],
      config: {
        source: { mode: 'constant', voc: 10, rs: 0 },
        load: { mode: 'step', iBefore: 1, iAfter: 0.5, stepAt: 150 },
        measurement: CHAIN_DEFAULT,
        sampleInterval: 0.5,
        duration: 300,
        noiseSeed: 20261106
      }
    },
    {
      id: 'adc-quantisation',
      name: 'ADC quantisation',
      experiment: 3,
      tagline: 'An 8-bit converter, viewed up close.',
      description: 'A slowly varying 10 V source measured through a 2:1 divider into an 8-bit converter. The ideal signal is smooth; the measured signal moves in 15.8 mV steps at the input (63 mV at the pin).',
      observe: [
        'The measured voltage is a staircase, not a curve.',
        'Every step is one LSB: 3.3 V / 256 / 0.5 = 25.8 mV at the input for this divider.',
        'Reported power inherits the staircase, and the energy estimate gains a small bias.'
      ],
      config: {
        source: { mode: 'ripple', voc: 10, rs: 0, rippleAmp: 0.35, rippleHz: 0.25 },
        load: { mode: 'current', i: 1 },
        measurement: {
          voltage: { sensitivity: 0.5, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 8, adcVref: 3.3 },
          current: { sensitivity: 0.5, gainError: 0, offsetV: 0, noiseRms: 0, adcBits: 8, adcVref: 3.3 }
        },
        sampleInterval: 0.5,
        duration: 120,
        noiseSeed: 20261106
      }
    },
    {
      id: 'calibration',
      name: 'Gain, offset and noise',
      experiment: 4,
      tagline: 'Two systematic errors and one random one.',
      description: 'The voltage channel has +3 % gain error, a 20 mV offset at the pin and 4 mV RMS noise; the current channel has a −2 % gain error. Calibration is off by default so the raw errors are visible.',
      observe: [
        'Reported power is high by roughly the gain error, not by the noise.',
        'The offset adds a constant bias: even at zero current the voltage reads high.',
        'Turning calibration on removes the systematic part; the noise remains.'
      ],
      config: {
        source: { mode: 'constant', voc: 9, rs: 0 },
        load: { mode: 'duty', period: 30, duty: 0.6, iOn: 1.2, iOff: 0.3 },
        measurement: {
          voltage: { sensitivity: 0.25, gainError: 0.03, offsetV: 0.02, noiseRms: 0.004, adcBits: 12,
                     adcVref: 3.3, calibration: { enabled: false, gainEstimate: 0, offsetEstimateV: 0 } },
          current: { sensitivity: 0.5, gainError: -0.02, offsetV: 0, noiseRms: 0.002, adcBits: 12,
                     adcVref: 3.3, calibration: { enabled: false, gainEstimate: 0, offsetEstimateV: 0 } }
        },
        sampleInterval: 0.5,
        duration: 240,
        noiseSeed: 424242
      }
    },
    {
      id: 'sampling-interval',
      name: 'Sampling interval',
      experiment: 5,
      tagline: 'A 4 s duty cycle, sampled too slowly.',
      description: 'A fast duty-cycled load (4 s period, 25 % on, 2 A) sampled at 2 s. The duty cycle is only twice the sample interval, so the samples land in almost the same phase every period.',
      observe: [
        'The reported average power drifts towards whichever phase the samples land on.',
        'Reducing the sample interval to 0.1 s recovers the true average power.',
        'Sparse samples cannot prove what happened between them.'
      ],
      config: {
        source: { mode: 'constant', voc: 12, rs: 0 },
        load: { mode: 'duty', period: 4, duty: 0.25, iOn: 2, iOff: 0 },
        measurement: CHAIN_DEFAULT,
        sampleInterval: 2,
        duration: 120,
        noiseSeed: 20261106
      }
    },
    {
      id: 'duty-load',
      name: 'Duty-cycled load',
      experiment: null,
      tagline: 'A load that switches itself on and off.',
      description: 'A 60 s duty cycle at 40 % on-time, 1.5 A on and 0.2 A off, sampled every 0.25 s so the switching is resolved.',
      observe: [
        'Power alternates between two levels; energy climbs in shallow steps.',
        'The average power approaches 40 % of the on-state power.',
        'The accumulator mixes both states correctly as long as the samples resolve them.'
      ],
      config: {
        source: { mode: 'constant', voc: 12, rs: 0 },
        load: { mode: 'duty', period: 60, duty: 0.4, iOn: 1.5, iOff: 0.2 },
        measurement: CHAIN_DEFAULT,
        sampleInterval: 0.25,
        duration: 600,
        noiseSeed: 20261106
      }
    },
    {
      id: 'source-droop',
      name: 'Real source impedance',
      experiment: null,
      tagline: 'A supply that sags under load.',
      description: 'The source has 0.8 Ω of internal resistance and the load steps between 0.5 A and 2 A. Terminal voltage sags by I·Rs, so power does not scale with current alone.',
      observe: [
        'Current doubles three times over; power rises by much less than that.',
        'Terminal voltage falls whenever the load takes more current.',
        'The energy lost inside the source is reported separately from the load energy.'
      ],
      config: {
        source: { mode: 'constant', voc: 12, rs: 0.8 },
        load: { mode: 'sequence', points: [{ t: 0, i: 0.5 }, { t: 120, i: 2 }, { t: 240, i: 0.8 }] },
        measurement: CHAIN_DEFAULT,
        sampleInterval: 0.25,
        duration: 360,
        noiseSeed: 20261106
      }
    }
  ];

  /* ------------------------------------------------------------------- csv -- */
  var CSV_COLUMNS = [
    't_s', 'v_true_v', 'i_true_a', 'p_true_w',
    'v_meas_v', 'i_meas_a', 'p_meas_w', 'energy_wh'
  ];

  function toCSV(samples, meta) {
    var lines = [];
    if (meta) {
      /* Metadata is written as comment lines so the body stays a clean table. */
      Object.keys(meta).forEach(function (k) {
        lines.push('# ' + k + ': ' + meta[k]);
      });
    }
    lines.push(CSV_COLUMNS.join(','));
    for (var i = 0; i < samples.length; i += 1) {
      var s = samples[i];
      lines.push([
        s.t.toFixed(6), s.vTrue.toFixed(6), s.iTrue.toFixed(6), s.pTrue.toFixed(6),
        s.vMeas.toFixed(6), s.iMeas.toFixed(6), s.pMeas.toFixed(6), s.energyWh.toFixed(9)
      ].join(','));
    }
    return lines.join('\n') + '\n';
  }

  /* Parse a CSV produced by toCSV back into records, for round-trip tests. */
  function parseCSV(text) {
    var rows = String(text).split(/\r?\n/).filter(function (line) {
      return line.trim() !== '' && line.charAt(0) !== '#';
    });
    if (!rows.length) return [];
    var header = rows[0].split(',');
    return rows.slice(1).map(function (line) {
      var cells = line.split(',');
      var rec = {};
      header.forEach(function (name, idx) { rec[name] = Number(cells[idx]); });
      return rec;
    });
  }

  return {
    VERSION: VERSION,
    PRESETS: PRESETS,
    CHAIN_DEFAULT: CHAIN_DEFAULT,
    WH_PER_J: WH_PER_J,
    sourceConfig: sourceConfig,
    loadConfig: loadConfig,
    channelConfig: channelConfig,
    sourceVoc: sourceVoc,
    loadState: loadState,
    operatingPoint: operatingPoint,
    channelLsb: channelLsb,
    readChannel: readChannel,
    createSampler: createSampler,
    integrateInterval: integrateInterval,
    integrateSeries: integrateSeries,
    validateSeries: validateSeries,
    normalizeConfig: normalizeConfig,
    simulate: simulate,
    makeRng: makeRng,
    gaussian: gaussian,
    toCSV: toCSV,
    parseCSV: parseCSV,
    CSV_COLUMNS: CSV_COLUMNS
  };
}));
