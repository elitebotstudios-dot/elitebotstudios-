/* Wires the published sizing module into the demonstration page.
   Kept separate from calc.js so the module can be tested on its own. */
'use strict';
(function () {
  var form = document.getElementById('psForm');
  if (!form || !window.PowerStage) return;
  var note = document.getElementById('psNote');

  function num(id, fallback) {
    var el = document.getElementById(id);
    if (!el || el.value.trim() === '') return NaN;
    var v = Number(el.value);
    return isFinite(v) ? v : NaN;
  }
  function eng(v, unit, digits) {
    if (!isFinite(v)) return '—';
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
  function put(key, text) {
    var el = form.parentNode.parentNode.querySelector('[data-ps="' + key + '"]');
    if (el) el.textContent = text;
  }

  function run() {
    var spec = {
      vinMin: num('psVinMin'), vinMax: num('psVinMax'),
      vout: num('psVout'), iout: num('psIout'),
      fsw: num('psFsw') * 1e3,
      ripplePct: num('psRipple'), voutRipplePct: num('psVripple')
    };
    var r = window.PowerStage.designBuck(spec);
    var keys = ['inductance', 'deltaIl', 'peakValley', 'irms', 'capacitance', 'duty', 'ontime', 'lcrit'];
    if (!r) {
      keys.forEach(function (k) { put(k, '—'); });
      note.textContent = 'This specification cannot be sized: check that the input range is valid, that the output is below the minimum input, and that current, frequency and ripple targets are positive.';
      return;
    }
    put('inductance', eng(r.inductance, 'H'));
    put('deltaIl', eng(r.deltaIl, 'A'));
    put('peakValley', eng(r.iPeak, 'A') + ' / ' + eng(r.iValley, 'A'));
    put('irms', eng(r.iRms, 'A'));
    put('capacitance', eng(r.capacitance, 'F'));
    put('duty', (r.dutyMax * 100).toFixed(1) + ' % / ' + (r.dutyMin * 100).toFixed(1) + ' %');
    put('ontime', eng(r.onTimeMax, 's'));
    put('lcrit', eng(r.lCrit, 'H'));
    note.textContent = 'Ideal steady-state CCM sizing at the worst-case duty point. Peak current is the inductor saturation requirement and RMS current the heating requirement; neither includes margin.';
  }

  form.addEventListener('input', run);
  form.addEventListener('change', run);
  form.addEventListener('reset', function () { setTimeout(run, 0); });
  run();
}());
