/* ===========================================================================
   energy-dashboard.js — the Smart DC Energy Monitor instrument

   This file is presentation only. Every number it displays comes from
   /energy-monitor/model/dcem.js, which is the same module the Node test suites
   import, so the instrument cannot drift away from the verified model.

   Responsibilities
     - build a model configuration from the controls
     - advance simulated time on requestAnimationFrame and feed the sampler
     - render four time-series charts (canvas 2D)
     - inspect points, export CSV, manage run state

   It never integrates energy itself and never invents a value: if the model
   rejects a sample, the rejection is counted and shown.
   ========================================================================== */
'use strict';
(function () {
  var root = document.getElementById('emApp');
  var D = window.DCEM;
  if (!root || !D) return;

  /* ------------------------------------------------------------------ dom -- */
  var $ = function (id) { return document.getElementById(id); };
  var el = {
    form: $('emControls'),
    status: $('emStatus'),
    clock: $('emClock'),
    samples: $('emSamples'),
    rejected: $('emRejected'),
    note: $('emNote'),
    v: $('emV'), i: $('emI'), p: $('emP'), e: $('emE'),
    vTrue: $('emVTrue'), iTrue: $('emITrue'), pTrue: $('emPTrue'), eTrue: $('emETrue'),
    loadModeSelect: $('emLoad'),
    loadState: $('emLoadState'),
    btnStart: $('emStart'), btnPause: $('emPause'), btnReset: $('emReset'),
    btnExport: $('emExport'),
    scenario: $('emScenario'),
    live: $('emLive'),
    inspect: $('emInspect'),
    archInfo: $('emArchInfo'),
    warnings: $('emWarnings'),
    calib: $('emCalibration')
  };

  var charts = {};
  var CHART_ORDER = ['voltage', 'current', 'power', 'energy'];
  var chartMeta = {
    voltage: { title: 'Voltage', unit: 'V', series: [{ key: 'vTrue', label: 'true', color: '#59D9E8', dash: null }, { key: 'vMeas', label: 'measured', color: '#D8B66A', dash: [5, 3] }] },
    current: { title: 'Current', unit: 'A', series: [{ key: 'iTrue', label: 'true', color: '#59D9E8', dash: null }, { key: 'iMeas', label: 'measured', color: '#D8B66A', dash: [5, 3] }] },
    power: { title: 'Power', unit: 'W', series: [{ key: 'pTrue', label: 'true', color: '#59D9E8', dash: null }, { key: 'pMeas', label: 'measured', color: '#D8B66A', dash: [5, 3] }] },
    energy: { title: 'Accumulated energy', unit: 'Wh', series: [{ key: 'energyWh', label: 'reported', color: '#8FD9C8', dash: null }] }
  };

  var state = {
    sampler: null,
    config: null,
    preset: null,
    running: false,
    complete: false,
    simTime: 0,
    nextSampleT: 0,
    lastFrame: 0,
    speed: 20,
    duration: 300,
    dt: 0.5,
    sampleCount: 0,
    rejected: 0,
    saturated: 0,
    lastDraw: 0,
    inspecting: null
  };
  var MAX_SAMPLES = 40000;

  var fmt = {
    num: function (v, digits) {
      if (v === null || v === undefined || !isFinite(v)) return '—';
      return v.toFixed(digits === undefined ? 3 : digits);
    },
    sim: function (t) {
      var m = Math.floor(t / 60), s = t - m * 60;
      return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s.toFixed(1);
    }
  };

  /* ------------------------------------------------------------- controls -- */
  function controlValue(id, fallback) {
    var input = $(id);
    if (!input) return fallback;
    var v = Number(input.value);
    return isFinite(v) ? v : fallback;
  }
  function checked(id) { var input = $(id); return !!(input && input.checked); }

  function loadMode() { return el.loadModeSelect ? el.loadModeSelect.value : 'resistive'; }

  function buildConfig() {
    var mode = loadMode();
    var load = { mode: mode };
    if (mode === 'resistive') load.r = controlValue('emResistance', 12);
    else if (mode === 'current') load.i = controlValue('emCurrent', 1);
    else if (mode === 'step') {
      load.iBefore = controlValue('emStepBefore', 1);
      load.iAfter = controlValue('emStepAfter', 0.5);
      load.stepAt = controlValue('emStepAt', 150);
    } else if (mode === 'duty') {
      load.period = controlValue('emDutyPeriod', 30);
      load.duty = controlValue('emDutyRatio', 40) / 100;
      load.iOn = controlValue('emDutyOn', 1.5);
      load.iOff = controlValue('emDutyOff', 0.2);
    }
    var calibration = checked('emCalibration');
    return {
      source: {
        mode: 'constant',
        voc: controlValue('emSupply', 12),
        rs: controlValue('emSourceR', 0)
      },
      load: load,
      measurement: {
        voltage: {
          sensitivity: controlValue('emVDivider', 0.25),
          gainError: controlValue('emVGain', 0) / 100,
          offsetV: controlValue('emVOffset', 0) / 1000,
          noiseRms: controlValue('emVNoise', 0) / 1000,
          adcBits: controlValue('emAdcBits', 12),
          adcVref: 3.3,
          calibration: {
            enabled: calibration,
            gainEstimate: controlValue('emVGain', 0) / 100,
            offsetEstimateV: controlValue('emVOffset', 0) / 1000
          }
        },
        current: {
          sensitivity: controlValue('emISense', 0.5) / 1000 * 1000,
          gainError: controlValue('emIGain', 0) / 100,
          offsetV: controlValue('emIOffset', 0) / 1000,
          noiseRms: controlValue('emINoise', 0) / 1000,
          adcBits: controlValue('emAdcBits', 12),
          adcVref: 3.3,
          calibration: {
            enabled: calibration,
            gainEstimate: controlValue('emIGain', 0) / 100,
            offsetEstimateV: controlValue('emIOffset', 0) / 1000
          }
        }
      },
      sampleInterval: controlValue('emInterval', 0.5),
      duration: state.duration,
      noiseSeed: 20261106
    };
  }

  /* ------------------------------------------------------------ run state -- */
  function setStatus(text, tone) {
    if (!el.status) return;
    el.status.textContent = text;
    el.status.setAttribute('data-tone', tone || 'idle');
  }

  function syncButtons() {
    if (el.btnStart) {
      el.btnStart.disabled = state.running;
      el.btnStart.textContent = state.complete ? 'Restart'
        : state.running ? 'Running…'
        : state.sampleCount > 0 ? 'Resume' : 'Start';
    }
    if (el.btnPause) el.btnPause.disabled = !state.running;
    if (el.btnExport) el.btnExport.disabled = state.sampleCount < 2;
  }

  function clearReadouts() {
    ['v', 'i', 'p', 'e', 'vTrue', 'iTrue', 'pTrue', 'eTrue'].forEach(function (k) {
      if (el[k]) el[k].textContent = '—';
    });
    if (el.clock) el.clock.textContent = '00:00.0';
    if (el.samples) el.samples.textContent = '0';
    if (el.rejected) el.rejected.textContent = '0';
    if (el.loadState) el.loadState.textContent = '—';
  }

  function resetRun(silent) {
    state.running = false;
    state.complete = false;
    state.simTime = 0;
    state.nextSampleT = 0;
    state.sampleCount = 0;
    state.rejected = 0;
    state.saturated = 0;
    state.inspecting = null;
    state.config = buildConfig();
    state.duration = controlValue('emDuration', 300);
    state.config.duration = state.duration;
    state.dt = state.config.sampleInterval;
    state.speed = controlValue('emSpeed', 20);
    state.sampler = D.createSampler(state.config);
    clearReadouts();
    setStatus('Ready', 'idle');
    if (el.warnings) {
      el.warnings.textContent = '';
      el.warnings.hidden = true;
    }
    if (el.inspect) el.inspect.textContent = 'Hover or focus a chart to read a point.';
    syncButtons();
    drawAll(true);
    if (!silent) announce('Run reset. Energy cleared.');
  }

  function announce(text) {
    if (el.live) el.live.textContent = text;
  }

  function startRun() {
    if (state.running) return;
    if (state.complete) resetRun(true);
    /* A paused run resumes: simulated time, samples and energy are kept. */
    if (state.sampleCount === 0) {
      state.config = buildConfig();
    }
    if (state.sampleCount === 0) {
      state.duration = controlValue('emDuration', 300);
      state.config.duration = state.duration;
      state.dt = state.config.sampleInterval;
      state.sampler = D.createSampler(state.config);
    }
    state.speed = controlValue('emSpeed', 20);
    if (state.config.warnings && state.config.warnings.length && el.warnings) {
      el.warnings.textContent = state.config.warnings.join(' · ');
      el.warnings.hidden = false;
    }
    state.running = true;
    state.complete = false;
    state.lastFrame = 0;
    setStatus('Running', 'run');
    syncButtons();
    announce('Simulation running at ' + state.speed + '× real time.');
    requestAnimationFrame(tick);
  }

  function pauseRun() {
    if (!state.running) return;
    state.running = false;
    setStatus('Paused', 'paused');
    syncButtons();
    announce('Simulation paused at ' + fmt.sim(state.simTime) + ' of simulated time.');
  }

  function completeRun() {
    state.running = false;
    state.complete = true;
    setStatus('Complete', 'done');
    syncButtons();
    var res = state.sampler.results();
    announce('Run complete: ' + fmt.num(res.energyWh, 4) + ' Wh accumulated over ' +
      fmt.num(res.durationS, 1) + ' s from ' + res.accepted + ' samples.');
  }

  /* ------------------------------------------------------------ the loop -- */
  function tick(now) {
    if (!state.running) return;
    if (!state.lastFrame) state.lastFrame = now;
    var realElapsed = Math.min((now - state.lastFrame) / 1000, 0.25);  /* clamp tab-switch jumps */
    state.lastFrame = now;
    var simAdvance = realElapsed * state.speed;
    var budget = 4000;                       /* never freeze the frame */
    var target = Math.min(state.simTime + simAdvance, state.duration);
    while (state.nextSampleT <= target + 1e-9 && state.sampleCount < MAX_SAMPLES && budget-- > 0) {
      var out = state.sampler.step(state.nextSampleT);
      if (out.ok) {
        state.sampleCount += 1;
        if (out.saturated) state.saturated += 1;
      } else {
        state.rejected += 1;
      }
      state.nextSampleT += state.dt;
    }
    state.simTime = target;
    renderReadouts();
    if (now - state.lastDraw > 60) {
      drawAll();
      state.lastDraw = now;
    }
    if (state.simTime >= state.duration - 1e-9) {
      renderReadouts();
      drawAll();
      completeRun();
      return;
    }
    requestAnimationFrame(tick);
  }

  function renderReadouts() {
    var samples = state.sampler ? state.sampler.samples : [];
    var last = samples.length ? samples[samples.length - 1] : null;
    if (last) {
      if (el.v) el.v.textContent = fmt.num(last.vMeas, 3);
      if (el.i) el.i.textContent = fmt.num(last.iMeas, 3);
      if (el.p) el.p.textContent = fmt.num(last.pMeas, 2);
      if (el.e) el.e.textContent = fmt.num(last.energyWh, 4);
      if (el.vTrue) el.vTrue.textContent = fmt.num(last.vTrue, 3);
      if (el.iTrue) el.iTrue.textContent = fmt.num(last.iTrue, 3);
      if (el.pTrue) el.pTrue.textContent = fmt.num(last.pTrue, 2);
      if (el.eTrue) el.eTrue.textContent = fmt.num(state.sampler.results().trueEnergyWh, 4);
      if (el.loadState) {
        el.loadState.textContent = last.fields.loadResistance !== null
          ? last.fields.loadResistance.toFixed(1) + ' Ω'
          : fmt.num(last.fields.loadCurrentDemand, 2) + ' A demand';
      }
    }
    if (el.clock) el.clock.textContent = fmt.sim(state.simTime);
    if (el.samples) el.samples.textContent = String(state.sampleCount);
    if (el.rejected) el.rejected.textContent = String(state.rejected + state.saturated);
  }

  /* -------------------------------------------------------------- charts -- */
  function Chart(canvas, kind) {
    this.canvas = canvas;
    this.kind = kind;
    this.ctx = canvas.getContext('2d');
    this.meta = chartMeta[kind];
    this.hoverIndex = null;
    var self = this;
    canvas.addEventListener('pointermove', function (e) { self.onPointer(e); });
    canvas.addEventListener('pointerleave', function () { self.hoverIndex = null; self.draw(); });
    canvas.addEventListener('focus', function () { self.draw(); });
    canvas.addEventListener('blur', function () { self.hoverIndex = null; self.draw(); });
    canvas.setAttribute('tabindex', '0');
  }

  Chart.prototype.samples = function () { return state.sampler ? state.sampler.samples : []; };

  Chart.prototype.onPointer = function (event) {
    var samples = this.samples();
    if (samples.length < 2) return;
    var rect = this.canvas.getBoundingClientRect();
    var frac = (event.clientX - rect.left) / rect.width;
    var bounds = this.bounds();
    var t = bounds.x0 + frac * (bounds.x1 - bounds.x0);
    var idx = Math.round((t - samples[0].t) / Math.max(1e-9, samples[samples.length - 1].t - samples[0].t) * (samples.length - 1));
    idx = Math.max(0, Math.min(samples.length - 1, idx));
    this.hoverIndex = idx;
    var s = samples[idx];
    if (el.inspect) {
      var parts = ['t = ' + fmt.num(s.t, 2) + ' s'];
      if (this.kind === 'energy') parts.push('energy ' + fmt.num(s.energyWh, 5) + ' Wh');
      else {
        var trueKey = { voltage: 'vTrue', current: 'iTrue', power: 'pTrue' }[this.kind];
        var measKey = { voltage: 'vMeas', current: 'iMeas', power: 'pMeas' }[this.kind];
        parts.push('true ' + fmt.num(s[trueKey], 4) + ' ' + this.meta.unit);
        parts.push('measured ' + fmt.num(s[measKey], 4) + ' ' + this.meta.unit);
      }
      el.inspect.textContent = parts.join(' · ');
    }
    this.draw();
  };

  Chart.prototype.bounds = function () {
    var samples = this.samples();
    var x0 = 0, x1 = Math.max(state.duration, state.simTime, 1);
    var y0 = 0, y1 = 1;
    var keys = this.meta.series.map(function (s) { return s.key; });
    var hasNegative = false, max = 0;
    for (var i = 0; i < samples.length; i += 1) {
      for (var k = 0; k < keys.length; k += 1) {
        var v = samples[i][keys[k]];
        if (v > max) max = v;
        if (v < 0) hasNegative = true;
      }
    }
    if (max <= 0) max = 1;
    y0 = hasNegative ? -max * 0.1 : 0;
    y1 = max * 1.12;
    return { x0: x0, x1: x1, y0: y0, y1: y1 };
  };

  function niceStep(raw) {
    if (!(raw > 0)) return 1;
    var pow = Math.pow(10, Math.floor(Math.log10(raw)));
    var n = raw / pow;
    var mult = n <= 1 ? 1 : n <= 1.5 ? 1.5 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 3 ? 3 : n <= 4 ? 4 : n <= 5 ? 5 : n <= 6 ? 6 : n <= 8 ? 8 : 10;
    return mult * pow;
  }

  Chart.prototype.draw = function () {
    var canvas = this.canvas, ctx = this.ctx;
    var dpr = window.devicePixelRatio || 1;
    var cssW = canvas.parentNode.clientWidth || 320;
    var cssH = canvas.parentNode.clientHeight || 180;
    if (canvas.width !== Math.round(cssW * dpr) || canvas.height !== Math.round(cssH * dpr)) {
      canvas.width = Math.round(cssW * dpr);
      canvas.height = Math.round(cssH * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    var pad = { l: 46, r: 12, t: 12, b: 26 };
    var w = cssW - pad.l - pad.r, h = cssH - pad.t - pad.b;
    if (w < 20 || h < 20) return;

    var b = this.bounds();
    var sx = function (t) { return pad.l + (t - b.x0) / (b.x1 - b.x0) * w; };
    var sy = function (v) { return pad.t + h - (v - b.y0) / (b.y1 - b.y0) * h; };

    /* grid + y labels */
    var step = niceStep((b.y1 - b.y0) / 4);
    ctx.font = '500 10px SFMono-Regular, Consolas, monospace';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (var v = b.y0; v <= b.y1 + 1e-9; v += step) {
      var y = sy(v);
      ctx.strokeStyle = 'rgba(89,217,232,0.09)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(pad.l, y);
      ctx.lineTo(pad.l + w, y);
      ctx.stroke();
      ctx.fillStyle = '#7E8B96';
      ctx.fillText(formatAxis(v, step), pad.l - 7, y);
    }

    /* x labels */
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (var k = 0; k <= 4; k += 1) {
      var t = b.x0 + (b.x1 - b.x0) * k / 4;
      ctx.fillStyle = '#7E8B96';
      ctx.fillText(Math.round(t) + ' s', sx(t), pad.t + h + 7);
    }

    /* axes */
    ctx.strokeStyle = 'rgba(150,170,185,0.35)';
    ctx.beginPath();
    ctx.moveTo(pad.l, pad.t);
    ctx.lineTo(pad.l, pad.t + h);
    ctx.lineTo(pad.l + w, pad.t + h);
    ctx.stroke();

    /* series */
    var samples = this.samples();
    var self = this;
    var maxPoints = Math.max(40, Math.floor(w * 2));
    var stride = samples.length > maxPoints ? Math.ceil(samples.length / maxPoints) : 1;
    this.meta.series.forEach(function (series) {
      ctx.strokeStyle = series.color;
      ctx.lineWidth = series.key === 'energyWh' ? 2 : 1.8;
      ctx.setLineDash(series.dash || []);
      ctx.beginPath();
      var started = false;
      for (var i = 0; i < samples.length; i += stride) {
        var s = samples[i];
        var x = sx(s.t), y = sy(s[series.key]);
        if (!started) { ctx.moveTo(x, y); started = true; } else { ctx.lineTo(x, y); }
      }
      if (samples.length) {
        var last = samples[samples.length - 1];
        ctx.lineTo(sx(last.t), sy(last[series.key]));
      }
      ctx.stroke();
      ctx.setLineDash([]);
    });

    /* legend */
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    var lx = pad.l + 8;
    this.meta.series.forEach(function (series) {
      ctx.strokeStyle = series.color;
      ctx.lineWidth = 2;
      ctx.setLineDash(series.dash || []);
      ctx.beginPath();
      ctx.moveTo(lx, pad.t + 8);
      ctx.lineTo(lx + 14, pad.t + 8);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#93A0AB';
      ctx.fillText(series.label, lx + 18, pad.t + 8);
      lx += 18 + ctx.measureText(series.label).width + 14;
    });

    /* inspection crosshair */
    if (this.hoverIndex !== null && samples[this.hoverIndex]) {
      var s = samples[this.hoverIndex];
      var cx = sx(s.t);
      ctx.strokeStyle = 'rgba(216,182,106,0.7)';
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(cx, pad.t);
      ctx.lineTo(cx, pad.t + h);
      ctx.stroke();
      ctx.setLineDash([]);
      this.meta.series.forEach(function (series) {
        ctx.fillStyle = series.color;
        ctx.beginPath();
        ctx.arc(cx, sy(s[series.key]), 3, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    /* accessibility label, throttled by only updating when values change */
    var lastSample = samples.length ? samples[samples.length - 1] : null;
    var label = this.meta.title + ' chart. ';
    if (lastSample) {
      label += this.meta.series.map(function (series) {
        return series.label + ' ' + fmt.num(lastSample[series.key], 3) + ' ' + self.meta.unit;
      }).join(', ') + ' at ' + fmt.num(lastSample.t, 1) + ' s';
    } else {
      label += 'no samples yet';
    }
    if (canvas.getAttribute('aria-label') !== label) canvas.setAttribute('aria-label', label);
  };

  function formatAxis(v, step) {
    var digits = step >= 1 ? 0 : step >= 0.1 ? 1 : step >= 0.01 ? 2 : 3;
    return v.toFixed(digits);
  }

  function drawAll() {
    CHART_ORDER.forEach(function (kind) {
      var chart = charts[kind];
      if (!chart) return;
      if (!chart.canvas.parentNode.clientWidth) return;     /* hidden tab */
      chart.draw();
    });
  }

  /* ------------------------------------------------------------ scenarios -- */
  function applyPreset(id) {
    var preset = D.PRESETS.filter(function (p) { return p.id === id; })[0];
    if (!preset) return;
    state.preset = preset;
    var cfg = preset.config;
    /* Write the preset into the controls so the user can see and then change
       every value it uses. */
    setValue('emSupply', cfg.source.voc);
    setValue('emSourceR', cfg.source.rs);
    setValue('emInterval', cfg.sampleInterval);
    setValue('emDuration', cfg.duration);
    setValue('emAdcBits', cfg.measurement.voltage.adcBits);
    setValue('emVDivider', cfg.measurement.voltage.sensitivity);
    setValue('emISense', cfg.measurement.current.sensitivity);
    setValue('emVGain', (cfg.measurement.voltage.gainError || 0) * 100);
    setValue('emVOffset', (cfg.measurement.voltage.offsetV || 0) * 1000);
    setValue('emVNoise', (cfg.measurement.voltage.noiseRms || 0) * 1000);
    setValue('emIGain', (cfg.measurement.current.gainError || 0) * 100);
    setValue('emINoise', (cfg.measurement.current.noiseRms || 0) * 1000);
    var mode = cfg.load.mode;
    setValue('emLoad', mode);
    if (mode === 'resistive') setValue('emResistance', cfg.load.r);
    if (mode === 'current') setValue('emCurrent', cfg.load.i);
    if (mode === 'step') {
      setValue('emStepBefore', cfg.load.iBefore);
      setValue('emStepAfter', cfg.load.iAfter);
      setValue('emStepAt', cfg.load.stepAt);
    }
    if (mode === 'duty') {
      setValue('emDutyPeriod', cfg.load.period);
      setValue('emDutyRatio', cfg.load.duty * 100);
      setValue('emDutyOn', cfg.load.iOn);
      setValue('emDutyOff', cfg.load.iOff);
    }
    if (el.calib) el.calib.checked = !!(cfg.measurement.voltage.calibration || {}).enabled;
    syncLoadFields();
    resetRun(true);
    if (el.note) {
      el.note.textContent = preset.description;
    }
    announce('Scenario loaded: ' + preset.name + '. Energy reset to zero.');
  }

  function setValue(id, value) {
    var input = $(id);
    if (!input) return;
    if (typeof value === 'number') input.value = String(Math.round(value * 1e6) / 1e6);
    else input.value = value;
  }

  function syncLoadFields() {
    var mode = loadMode();
    Array.prototype.forEach.call(root.querySelectorAll('[data-load-mode]'), function (node) {
      var modes = node.getAttribute('data-load-mode').split(' ');
      node.hidden = modes.indexOf(mode) === -1;
    });
  }

  /* --------------------------------------------------------------- export -- */
  function exportCSV() {
    var samples = state.sampler ? state.sampler.samples : [];
    if (samples.length < 2) return;
    var res = state.sampler.results();
    var cfg = state.config;
    var meta = {
      model: 'Elite Bot Studios DCEM ' + D.VERSION,
      generated: new Date().toISOString(),
      scenario: state.preset ? state.preset.id : 'custom',
      sample_interval_s: cfg.sampleInterval,
      duration_s: state.duration,
      supply_v: cfg.source.voc,
      source_resistance_ohm: cfg.source.rs,
      load_mode: cfg.load.mode,
      adc_bits: cfg.voltage ? cfg.voltage.adcBits : cfg.measurement.voltage.adcBits,
      reported_energy_wh: res.energyWh.toFixed(9),
      true_energy_wh: res.trueEnergyWh.toFixed(9),
      accepted_samples: res.accepted,
      rejected_samples: res.rejected
    };
    var csv = D.toCSV(samples, meta);
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    var stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    a.href = url;
    a.download = 'dcem-' + (state.preset ? state.preset.id : 'custom') + '-' + stamp + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
    announce('Exported ' + samples.length + ' samples as CSV.');
  }

  /* ------------------------------------------------------------ wiring up -- */
  function onControlChange(event) {
    /* live parameter changes are allowed mid-run: they change the true signal
       from now on, which is what a real load change does */
    if (event && event.target && event.target.id === 'emLoad') {
      syncLoadFields();
      resetRun(true);
      announce('Load model changed. A new run was started so energy from the previous load cannot carry over.');
      return;
    }
    if (event && event.target && event.target.id === 'emCalibration') {
      resetRun(true);
      return;
    }
    if (state.running || state.sampleCount === 0) {
      drawAll();
      return;
    }
    /* a paused run picks up the new configuration on restart, not silently */
  }

  function init() {
    if (!el.form) return;
    canvasSetup();
    el.form.addEventListener('input', onControlChange);
    el.form.addEventListener('change', onControlChange);
    if (el.btnStart) el.btnStart.addEventListener('click', startRun);
    if (el.btnPause) el.btnPause.addEventListener('click', pauseRun);
    if (el.btnReset) el.btnReset.addEventListener('click', function () { resetRun(false); });
    if (el.btnExport) el.btnExport.addEventListener('click', exportCSV);
    if (el.scenario) {
      el.scenario.addEventListener('change', function () {
        if (el.scenario.value) applyPreset(el.scenario.value);
      });
    }
    document.querySelectorAll('[data-arch]').forEach(function (button) {
      button.addEventListener('click', function () {
        document.querySelectorAll('[data-arch]').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
        button.setAttribute('aria-pressed', 'true');
        if (el.archInfo) el.archInfo.innerHTML = button.getAttribute('data-arch-info');
      });
    });
    var first = document.querySelector('[data-arch]');
    if (first) first.setAttribute('aria-pressed', 'true');
    syncLoadFields();
    syncChartPanels();
    resetRun(true);
    setStatus('Ready', 'idle');
    if (el.note) {
      var preset = D.PRESETS.filter(function (p) { return p.id === el.scenario.value; })[0];
      if (preset) el.note.textContent = preset.description;
    }
  }

  /* Below the breakpoint the four charts are shown one at a time, selected by
     the tab row; above it they are all visible. Kept in one place so the initial
     state, tab clicks and resizes cannot disagree. */
  function syncChartPanels() {
    var narrow = window.innerWidth <= 980;
    if (!narrow) {
      document.querySelectorAll('[data-chart-panel]').forEach(function (p) { p.hidden = false; });
      return;
    }
    var active = document.querySelector('[data-chart-tab][aria-selected="true"]');
    var kind = active ? active.getAttribute('data-chart-tab') : 'voltage';
    document.querySelectorAll('[data-chart-panel]').forEach(function (p) {
      p.hidden = p.getAttribute('data-chart-panel') !== kind;
    });
  }

  function canvasSetup() {
    CHART_ORDER.forEach(function (kind) {
      var canvas = document.getElementById('emChart-' + kind);
      if (canvas) charts[kind] = new Chart(canvas, kind);
    });
    /* mobile tab selector */
    var tabs = document.querySelectorAll('[data-chart-tab]');
    Array.prototype.forEach.call(tabs, function (tab) {
      tab.addEventListener('click', function () {
        var kind = tab.getAttribute('data-chart-tab');
        Array.prototype.forEach.call(tabs, function (t) {
          t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
        });
        syncChartPanels();
        var chart = charts[kind];
        if (chart) chart.draw();
      });
    });
    var resizeTimer = null;
    window.addEventListener('resize', function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        syncChartPanels();
        drawAll();
      }, 120);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  /* exposed for the browser QA suite only; not a public API */
  window.__dcemDashboard = {
    state: state,
    reset: resetRun,
    start: startRun,
    pause: pauseRun,
    applyPreset: applyPreset,
    charts: charts
  };
}());
