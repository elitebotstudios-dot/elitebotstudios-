/* Wires the published sizing module into the demonstration page.
   Kept separate from calc.js so the module can be tested on its own. */
'use strict';
(function () {
  var form = document.getElementById('psForm');
  if (!form || !window.PowerStage) return;

  var note = document.getElementById('psNote');
  var chip = document.getElementById('psCcmChip');
  var plot = document.getElementById('psPlot');
  var plotNote = document.getElementById('psPlotNote');
  var sweepBody = document.getElementById('psSweepBody');
  var out = document.getElementById('psOut');

  var KEYS = ['inductance', 'rippleWorst', 'rippleMinVin', 'peak', 'valley', 'irms',
    'lcrit', 'cNominal', 'cEsr', 'cTransient', 'cRms', 'duty', 'ontime', 'period'];

  function num(id) {
    var el = document.getElementById(id);
    if (!el || String(el.value).trim() === '') return NaN;
    var v = Number(el.value);
    return isFinite(v) ? v : NaN;
  }
  function eng(v, unit, digits) {
    if (v === null || v === undefined || !isFinite(v)) return '—';
    if (v === 0) return '0 ' + unit;
    var a = Math.abs(v);
    var scales = [[1e9, 'G'], [1e6, 'M'], [1e3, 'k'], [1, ''], [1e-3, 'm'], [1e-6, 'µ'], [1e-9, 'n'], [1e-12, 'p']];
    for (var i = 0; i < scales.length; i += 1) {
      if (a >= scales[i][0] || i === scales.length - 1) {
        return Number((v / scales[i][0]).toPrecision(digits || 4)) + ' ' + scales[i][1] + unit;
      }
    }
    return v + ' ' + unit;
  }
  function pct(v, digits) {
    if (!isFinite(v)) return '—';
    return Number(v.toPrecision(digits || 3)) + ' %';
  }
  function put(key, text, tone) {
    var el = out && out.querySelector('[data-ps="' + key + '"]');
    if (!el) return;
    el.textContent = text;
    if (tone) el.setAttribute('data-tone', tone);
    else el.removeAttribute('data-tone');
  }
  function setChip(text, tone) {
    if (!chip) return;
    chip.textContent = text;
    chip.setAttribute('data-tone', tone);
  }

  /* round an axis maximum up to a step a reader can divide by eye */
  function niceStep(raw) {
    if (!(raw > 0)) return 1;
    var pow = Math.pow(10, Math.floor(Math.log10(raw)));
    var n = raw / pow;
    var mult = n <= 1 ? 1 : n <= 1.5 ? 1.5 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 3 ? 3 :
      n <= 4 ? 4 : n <= 5 ? 5 : n <= 6 ? 6 : n <= 8 ? 8 : 10;
    return mult * pow;
  }

  /* ---- ripple against input voltage ---------------------------------- */
  function drawPlot(r) {
    if (!plot || !r) return;
    var W = 640, H = 230, L = 54, R = 18, T = 16, B = 38;
    var pts = r.sweep;
    var vinMin = pts[0].vin, vinMax = pts[pts.length - 1].vin;
    var yMax = 0;
    pts.forEach(function (p) { if (p.deltaIl > yMax) yMax = p.deltaIl; });
    var step = niceStep((yMax || 0.1) / 3.6);
    yMax = step * 4;
    var x = function (vin) {
      return vinMax === vinMin ? (L + (W - L - R) / 2)
        : L + (W - L - R) * (vin - vinMin) / (vinMax - vinMin);
    };
    var y = function (i) { return T + (H - T - B) * (1 - i / yMax); };
    var svg = ['<svg class="ps-plot-svg" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Inductor ripple falls as input voltage falls, peaking at the maximum input voltage">'];

    /* grid + y labels */
    for (var g = 0; g <= 4; g += 1) {
      var val = yMax * g / 4, yy = y(val);
      svg.push('<line class="ps-plot-grid" x1="' + L + '" y1="' + yy.toFixed(1) + '" x2="' + (W - R) + '" y2="' + yy.toFixed(1) + '"/>');
      svg.push('<text x="' + (L - 9) + '" y="' + (yy + 3.5).toFixed(1) + '" text-anchor="end">' + eng(val, 'A', 2) + '</text>');
    }
    /* axes */
    svg.push('<line class="ps-plot-axis" x1="' + L + '" y1="' + T + '" x2="' + L + '" y2="' + (H - B) + '"/>');
    svg.push('<line class="ps-plot-axis" x1="' + L + '" y1="' + (H - B) + '" x2="' + (W - R) + '" y2="' + (H - B) + '"/>');

    /* ripple target line at target level */
    var targetY = y(r.rippleTargetA);
    if (r.rippleTargetA <= yMax) {
      svg.push('<line class="ps-plot-target" x1="' + L + '" y1="' + targetY.toFixed(1) + '" x2="' + (W - R) + '" y2="' + targetY.toFixed(1) + '"/>');
      svg.push('<text class="ps-plot-tag" x="' + (L + 8) + '" y="' + (targetY - 7).toFixed(1) + '">target ' + eng(r.rippleTargetA, 'A', 2) + '</text>');
    }

    /* the trace */
    var d = '';
    pts.forEach(function (p, i) {
      d += (i ? 'L' : 'M') + x(p.vin).toFixed(1) + ' ' + y(p.deltaIl).toFixed(1);
    });
    var area = d + 'L' + x(vinMax).toFixed(1) + ' ' + (H - B) + 'L' + x(vinMin).toFixed(1) + ' ' + (H - B) + 'Z';
    svg.push('<path class="ps-plot-area" d="' + area + '"/>');
    svg.push('<path class="ps-plot-line" d="' + d + '"/>');

    /* the worst-case marker at Vin,max */
    var last = pts[pts.length - 1];
    svg.push('<circle class="ps-plot-dot" cx="' + x(last.vin).toFixed(1) + '" cy="' + y(last.deltaIl).toFixed(1) + '" r="4.5"/>');

    /* x labels */
    [0, 0.5, 1].forEach(function (f) {
      var vin = vinMin + (vinMax - vinMin) * f;
      svg.push('<text x="' + x(vin).toFixed(1) + '" y="' + (H - B + 18) + '" text-anchor="middle">' + Number(vin.toPrecision(3)) + ' V</text>');
    });
    svg.push('<text class="ps-plot-axis-label" x="' + ((L + W - R) / 2) + '" y="' + (H - 6) + '" text-anchor="middle">input voltage</text>');
    svg.push('</svg>');
    plot.innerHTML = svg.join('');
  }

  /* ---- operating-point table ----------------------------------------- */
  function fillSweep(r) {
    if (!sweepBody) return;
    if (!r) {
      sweepBody.innerHTML = '<tr><td colspan="7">No operating points: the specification cannot be sized.</td></tr>';
      return;
    }
    var rows = r.sweep.map(function (p) {
      var peak = p.iPeak.toFixed(3), valley = p.iValley.toFixed(3);
      var cls = p.iValley < 0 ? ' class="ps-row-dcm"' : '';
      return '<tr' + cls + '><th scope="row">' + Number(p.vin.toPrecision(3)) + ' V</th>' +
        '<td>' + (p.duty * 100).toFixed(1) + ' %</td>' +
        '<td>' + p.deltaIl.toFixed(3) + ' A</td>' +
        '<td>' + p.ripplePct.toFixed(1) + ' %</td>' +
        '<td>' + peak + ' A</td>' +
        '<td>' + valley + ' A</td>' +
        '<td>' + eng(p.onTime, 's', 3) + '</td></tr>';
    });
    sweepBody.innerHTML = rows.join('');
  }

  /* ---- readouts ------------------------------------------------------- */
  function run() {
    var spec = {
      vinMin: num('psVinMin'), vinMax: num('psVinMax'),
      vout: num('psVout'), iout: num('psIout'),
      fsw: num('psFsw') * 1e3,
      ripplePct: num('psRipple'), voutRipplePct: num('psVripple'),
      esr: num('psEsr') || 0,
      derating: (num('psDerating') || 100) / 100,
      loadStep: num('psLoadStep') || 0,
      sweepPoints: 5
    };
    var r = window.PowerStage.designBuck(spec);

    if (!r) {
      KEYS.forEach(function (k) { put(k, '—'); });
      setChip('not sizeable', 'warn');
      if (note) {
        note.textContent = 'This specification cannot be sized. Check that the minimum input is above the output voltage, that the maximum input is not below the minimum, and that current, frequency and ripple targets are positive.';
        note.setAttribute('data-tone', 'warn');
      }
      drawPlot(null);
      if (plot) plot.innerHTML = '';
      fillSweep(null);
      return;
    }
    if (note) note.removeAttribute('data-tone');

    put('inductance', eng(r.inductance, 'H'));
    put('rippleWorst', eng(r.worst.deltaIl, 'A') + ' · ' + pct(r.ripplePctActual));
    put('rippleMinVin', eng(r.deltaIlAtMinVin, 'A') + ' · ' + pct(r.deltaIlAtMinVin / spec.iout * 100));
    put('peak', eng(r.iPeak, 'A'));
    put('valley', eng(r.iValley, 'A'), r.iValley <= 0 ? 'warn' : null);
    put('irms', eng(r.iRms, 'A'));
    put('lcrit', eng(r.lCrit, 'H'));

    put('cNominal', r.cap.feasible && isFinite(r.cap.cNominal) ? eng(r.cap.cNominal, 'F') : 'not achievable');
    put('cEsr', r.cap.esr > 0
      ? eng(r.cap.esrRipple, 'V', 2) + ' of ' + eng(r.cap.voutRippleTarget, 'V', 2)
      : 'no ESR entered');
    put('cTransient', r.loadStep > 0 ? eng(r.cap.cTransient, 'F') : 'not evaluated');
    put('cRms', eng(r.cap.rmsCurrent, 'A'));
    put('duty', (r.timing.dutyMax * 100).toFixed(1) + ' % / ' + (r.timing.dutyMin * 100).toFixed(1) + ' %');
    put('ontime', eng(r.timing.onTimeMax, 's', 3) + ' / ' + eng(r.timing.onTimeMin, 's', 3));
    put('period', eng(r.timing.period, 's', 3));

    if (r.ccm) {
      setChip('CCM at full load', 'ok');
    } else {
      setChip('below the CCM boundary', 'warn');
    }

    if (note) {
      var text = 'Ripple, peak current, RMS current and the CCM boundary are worst at ' +
        Number(spec.vinMax.toPrecision(3)) + ' V; duty and on-time are worst at ' +
        Number(spec.vinMin.toPrecision(3)) + ' V. The inductance holds the ' +
        pct(spec.ripplePct) + ' ripple target across the whole range.';
      if (!r.cap.feasible) {
        text += ' The ESR alone exceeds the output-ripple budget, so no capacitance can meet it.';
      } else if (r.loadStep > 0 && r.cap.cTransient > r.cap.cEffective) {
        text += ' The transient requirement, not the ripple requirement, sets the capacitance here.';
      }
      note.textContent = text;
    }
    if (plotNote) {
      plotNote.textContent = 'Peak ripple ' + eng(r.worst.deltaIl, 'A', 3) + ' at ' +
        Number(spec.vinMax.toPrecision(3)) + ' V, falling to ' + eng(r.deltaIlAtMinVin, 'A', 3) +
        ' at ' + Number(spec.vinMin.toPrecision(3)) + ' V for the same ' + eng(r.inductance, 'H', 3) + '.';
    }
    drawPlot(r);
    fillSweep(r);
  }

  form.addEventListener('input', run);
  form.addEventListener('change', run);
  form.addEventListener('reset', function () { setTimeout(run, 0); });
  run();
}());
