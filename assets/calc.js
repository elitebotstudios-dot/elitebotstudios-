/* ==========================================================================
   Elite Bot Studios — engineering calculators
   Pure functions first (so they can be tested outside a browser), then the
   DOM wiring. Everything runs locally: no network, no tracking, no storage.
   ========================================================================== */
'use strict';

var CU_RHO20 = 1.724e-8;   // ohm-metre at 20 C
var CU_ALPHA = 0.00393;    // per degree C
var MIL2MM = 0.0254;
var OZ_TO_MILS = 1.378;    // 1 oz copper = 1.378 mil

/* ---- IPC-2221 conductor sizing ------------------------------------------
   I = k * dT^0.44 * A^0.725, A in mil^2, k = 0.048 external / 0.024 internal.
   Rearranged for area, then divided by copper thickness. Empirical minimum. */
function traceWidth(o) {
  var I = o.current, dT = o.rise, oz = o.copper, len = o.length || 0;
  var ambient = o.ambient == null ? 20 : o.ambient;
  var k = o.internal ? 0.024 : 0.048;
  if (!(I > 0) || !(dT > 0) || !(oz > 0) || len < 0 || !(ambient > -273.15)) return null;
  var areaMil2 = Math.pow(I / (k * Math.pow(dT, 0.44)), 1 / 0.725);
  var thickMil = oz * OZ_TO_MILS;
  var widthMil = areaMil2 / thickMil;
  var widthMm = widthMil * MIL2MM;
  var wM = widthMm * 1e-3, tM = thickMil * MIL2MM * 1e-3, lM = len * 1e-3;
  var copperTemp = ambient + dT;
  var rho = CU_RHO20 * (1 + CU_ALPHA * (copperTemp - 20));
  var R = (wM * tM) > 0 ? rho * lM / (wM * tM) : 0;
  return {
    areaMil2: areaMil2, widthMil: widthMil, widthMm: widthMm,
    resistance: R, drop: I * R, power: I * I * R, thickMm: tM * 1e3,
    ambient: ambient, copperTemp: copperTemp
  };
}

function buck(o) {
  var vin = o.vin, vout = o.vout, f = o.freq, L = o.inductance;
  var iout = o.iout, eff = o.eff == null ? 1 : o.eff;
  if (!(vin > 0) || !(vout > 0) || vout >= vin || !(f > 0) || !(L > 0) ||
      !(iout > 0) || !(eff > 0) || eff > 1) return null;

  /* Ideal CCM conversion ratio: Vout ≈ D·Vin. Efficiency does not correct duty
     universally; its only use here is an estimate of input power/current. */
  var d = vout / vin;
  var dIl = vout * (1 - d) / (L * f);
  var pOut = vout * iout;
  var pIn = pOut / eff;
  var iValley = iout - dIl / 2;
  return {
    duty: d, dutyIdeal: d, deltaIl: dIl,
    iPeak: iout + dIl / 2, iValley: iValley,
    ripplePct: (dIl / iout) * 100,
    lCrit: (vout * (1 - d)) / (2 * f * iout),
    ccm: iValley >= 0,
    onTimeNs: (d / f) * 1e9, periodNs: (1 / f) * 1e9,
    outputPower: pOut, inputPower: pIn, inputCurrent: pIn / vin,
    estimatedLoss: pIn - pOut,
    inductorRms: Math.sqrt(iout * iout + (dIl * dIl) / 12)
  };
}

function linear(o) {
  var vin = o.vin, vout = o.vout, iout = o.iout, theta = o.thetaJa, ta = o.ambient;
  var tjmax = o.tjMax || 125;
  if (!(vin > 0) || vout < 0 || !(iout > 0) || vout > vin || !(theta > 0) || !(ta > -273.15)) return null;
  var drop = vin - vout, p = drop * iout, rise = p * theta, tj = ta + rise;
  return {
    drop: drop, power: p, rise: rise, tj: tj, headroom: tjmax - tj,
    efficiency: (vout / vin) * 100, safe: tj <= tjmax,
    maxCurrent: theta > 0 && drop > 0 ? Math.max(0, (tjmax - ta) / (theta * drop)) : Infinity
  };
}

function divider(o) {
  var vin = o.vin, r1 = o.r1, r2 = o.r2;
  if (!(vin > 0) || !(r1 > 0) || !(r2 > 0)) return null;
  var vout = vin * r2 / (r1 + r2), cur = vin / (r1 + r2);
  return {
    vout: vout, current: cur,
    p1: cur * cur * r1, p2: cur * cur * r2,
    ratio: r2 / (r1 + r2),
    zout: (r1 * r2) / (r1 + r2)
  };
}

function led(o) {
  var vs = o.supply, vf = o.forward, i = o.current, n = o.count == null ? 1 : o.count;
  if (!(vs > 0) || !(vf > 0) || !(i > 0) || !(n >= 1) || Math.floor(n) !== n) return null;
  var drop = n * vf;
  if (drop >= vs) return null;
  var r = (vs - drop) / i, near = nearestE12(r);
  var iActual = near ? (vs - drop) / near : null;
  return {
    resistance: r, nearest: near, powerR: i * i * r,
    powerLed: drop * i, totalPower: vs * i, drop: drop,
    currentSelected: iActual,
    currentErrorPct: iActual ? ((iActual - i) / i) * 100 : null,
    powerSelected: iActual ? iActual * iActual * near : null
  };
}

function rc(o) {
  var r = o.r, c = o.c;
  if (!(r > 0) || !(c > 0)) return null;
  var tau = r * c;
  return {
    tau: tau, t63: tau, t95: 3 * tau, t99: 5 * tau,
    cutoff: 1 / (2 * Math.PI * tau), rise: 2.197 * tau
  };
}

function pwm(o) {
  var freq = o.freq, duty = o.duty, high = o.high;
  if (!(freq > 0) || !isFinite(freq)) return null;
  if (!(duty >= 0) || !(duty <= 1) || !isFinite(duty)) return null;
  if (!(high > 0) || !isFinite(high)) return null;
  var period = 1 / freq;
  var ton = duty * period;
  var toff = period - ton;
  var average = duty * high;
  var rms = high * Math.sqrt(duty);
  return {
    period: period, ton: ton, toff: toff,
    dutyPct: duty * 100, average: average, rms: rms,
    high: high, low: 0,
    /* counts available in a 16-bit timer at this period, for context only */
    maxCounts: 65535
  };
}

var E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2];
function nearestE12(v) {
  if (!(v > 0)) return null;
  var exp = Math.floor(Math.log10(v)), best = null, bestErr = Infinity;
  for (var e = exp - 1; e <= exp + 1; e++) {
    for (var i = 0; i < E12.length; i++) {
      var cand = E12[i] * Math.pow(10, e), err = Math.abs(cand - v) / v;
      if (err < bestErr) { bestErr = err; best = cand; }
    }
  }
  return best;
}

/* --------------------------------------------------------------- format -- */
function sig(v, digits) {
  if (v === 0) return '0';
  if (!isFinite(v)) return '—';
  var a = Math.abs(v);
  if (a >= 1e6 || a < 1e-4) return v.toExponential(2).replace('e', ' × 10^');
  return Number(v.toPrecision(digits || 4)).toString();
}
function eng(v, unit) {
  if (!isFinite(v)) return '—';
  if (v === 0) return '0 ' + unit;
  var a = Math.abs(v);
  var scales = [[1e9, 'G'], [1e6, 'M'], [1e3, 'k'], [1, ''], [1e-3, 'm'], [1e-6, 'µ'], [1e-9, 'n'], [1e-12, 'p']];
  for (var i = 0; i < scales.length; i++) {
    if (a >= scales[i][0] || i === scales.length - 1) {
      return Number((v / scales[i][0]).toPrecision(4)) + ' ' + scales[i][1] + unit;
    }
  }
  return v + ' ' + unit;
}

if (typeof module !== 'undefined') {
  module.exports = { traceWidth, buck, linear, divider, led, rc, pwm, nearestE12, E12, sig, eng };
}

/* ============================================================ DOM wiring ==
   Each calculator page carries a <form data-calc="name"> and an output pane
   of <output data-key="..."> elements. Everything updates on input, so there
   is no "Calculate" button to forget to press.
   ======================================================================== */
if (typeof document !== 'undefined') {
  (function () {
    function num(form, name, fallback) {
      var el = form.querySelector('[name="' + name + '"]');
      if (!el) return fallback;
      if (el.value.trim() === '') return NaN;
      var v = Number(el.value);
      return isFinite(v) ? v : NaN;
    }
    function radio(form, name) {
      var el = form.querySelector('[name="' + name + '"]:checked');
      return el ? el.value : null;
    }
    function put(root, key, text, tone) {
      var el = root.querySelector('[data-key="' + key + '"]');
      if (!el) return;
      el.textContent = text;
      if (tone) el.setAttribute('data-tone', tone);
      else el.removeAttribute('data-tone');
    }

    function clearReadouts(root, keys) {
      keys.forEach(function (key) { put(root, key, '—'); });
    }

    function drawBuckPlot(root, r) {
      var plot=document.getElementById('buckExplorer') || root.parentNode;
      var gate=plot.querySelector('#buckGateTrace');
      var current=plot.querySelector('#buckCurrentTrace');
      var boundary=plot.querySelector('#buckPlotBoundary');
      var period=plot.querySelector('#buckPeriodLabel');
      if (!gate || !current || !boundary) return;
      if (!r) { gate.setAttribute('d',''); current.setAttribute('d',''); boundary.textContent='Enter valid values to plot the ideal CCM model.'; return; }
      var x0=58, x1=600, yHi=48, yLo=86, xD=x0+(x1-x0)*r.duty;
      gate.setAttribute('d','M'+x0+' '+yLo+'V'+yHi+'H'+xD+'V'+yLo+'H'+x1);
      if (period) period.textContent='T = '+(r.periodNs/1000).toFixed(2)+' µs · ton = '+(r.onTimeNs/1000).toFixed(2)+' µs';
      if (r.ccm) {
        var ymin=154, ymax=248, max=Math.max(r.iPeak*1.18,0.1), yv=ymax-(r.iValley/max)*(ymax-ymin), yp=ymax-(r.iPeak/max)*(ymax-ymin);
        current.setAttribute('d','M'+x0+' '+yv+'L'+xD+' '+yp+'L'+x1+' '+yv);
        boundary.textContent='Ideal continuous-conduction estimate · triangular ripple assumes steady state and ideal switch conversion.';
      } else {
        current.setAttribute('d','');
        boundary.textContent='The CCM boundary is not met at this load. Ripple and peak values above are CCM extrapolations; the DCM waveform and duty ratio are not solved by this model.';
      }
    }

    function drawPwmPlot(root, r, form) {
      var plot = document.getElementById('pwmLab') || root.parentNode;
      var trace = plot.querySelector('#pwmTrace');
      var avgLine = plot.querySelector('#pwmAverage');
      var grid = plot.querySelector('#pwmGrid');
      var caption = plot.querySelector('#pwmPlotCaption');
      var periodLabel = plot.querySelector('#pwmPeriodLabel');
      if (!trace || !avgLine || !caption) return;
      if (!r) {
        trace.setAttribute('d', '');
        avgLine.setAttribute('d', '');
        caption.textContent = 'Enter a positive frequency, duty between 0 % and 100 %, and a positive high level.';
        return;
      }
      var windowSeconds = parseFloat(form.querySelector('[name="span"]').value) * 1e-6;
      if (!(windowSeconds > 0)) windowSeconds = r.period * 3;
      var x0 = 64, x1 = 596, yHigh = 62, yLow = 138;
      var cycles = Math.max(1, Math.min(6, windowSeconds / r.period));
      var span = cycles * r.period;
      var pxPerSecond = (x1 - x0) / span;
      var d = 'M' + x0 + ' ' + yLow;
      for (var i = 0; i < cycles; i += 1) {
        var start = x0 + (i * r.period) * pxPerSecond;
        var edge = start + r.ton * pxPerSecond;
        var end = x0 + ((i + 1) * r.period) * pxPerSecond;
        d += 'V' + yHigh.toFixed(1) + 'H' + edge.toFixed(1) + 'V' + yLow + 'H' + end.toFixed(1);
      }
      trace.setAttribute('d', d);
      var yAvg = yLow - (r.average / r.high) * (yLow - yHigh);
      avgLine.setAttribute('d', 'M' + x0 + ' ' + yAvg.toFixed(1) + 'H' + x1);
      if (periodLabel) periodLabel.textContent = 'window ' + eng(span, 's') + ' · ' + cycles.toFixed(cycles < 2 ? 2 : 1) + ' cycles';
      var edgeNote = r.ton > 0 && r.toff > 0 ? 'One cycle: ' + eng(r.ton, 's') + ' high, ' + eng(r.toff, 's') + ' low.' : 'A 0 % or 100 % duty gives a constant level, not a switching waveform.';
      caption.textContent = edgeNote + ' The dashed line is the mathematical time-average, ' + eng(r.average, 'V') + ' — only a real filter or load dynamics turn that average into a smooth voltage.';
    }

    var CALCS = {
      tracewidth: function (form, out) {
        var internal = radio(form, 'layer') === 'internal';
        var r = traceWidth({
          current: num(form, 'current'), rise: num(form, 'rise'),
          copper: num(form, 'copper'), length: num(form, 'length'),
          ambient: 20, internal: internal
        });
        if (!r) {
          clearReadouts(out,['width','widthmil','area','resistance','drop','power']);
          put(out,'note','Enter a positive current, rise, copper thickness, nonnegative length, and a valid ambient temperature.','warn');
          return;
        }
        put(out, 'width', Number(r.widthMm.toPrecision(3)) + ' mm');
        put(out, 'widthmil', Number(r.widthMil.toPrecision(3)) + ' mil');
        put(out, 'area', Number(r.areaMil2.toPrecision(3)) + ' mil²');
        put(out, 'resistance', eng(r.resistance, 'Ω'));
        put(out, 'drop', eng(r.drop, 'V'));
        put(out, 'power', eng(r.power, 'W'));
        var rec = r.widthMm <= 0.15 ? 'below the usual 0.15 mm fab minimum' :
                  r.widthMm <= 0.25 ? 'fine for most fabs, check the minimum' :
                  'comfortably inside typical fab limits';
        put(out, 'note', 'Resistance uses 20 °C ambient plus the entered temperature rise. At a 0.15 mm fab minimum, this width is ' + rec + '.');
      },

      buck: function (form, out) {
        var r = buck({
          vin: num(form, 'vin'), vout: num(form, 'vout'),
          freq: num(form, 'freq') * 1e3, inductance: num(form, 'inductance') * 1e-6,
          iout: num(form, 'iout'), eff: num(form, 'eff') / 100
        });
        if (!r) {
          clearReadouts(out,['duty','ripple','peak','valley','ripplepct','lcrit','ontime','mode','pin','iin','loss']);
          put(out, 'note', 'Check that Vin > Vout > 0, inductance, current and frequency are positive, and the efficiency estimate is between 0 and 100%.', 'warn');
          drawBuckPlot(out, null);
          return;
        }
        put(out, 'duty', (r.duty * 100).toFixed(1) + ' %');
        put(out, 'ripple', eng(r.deltaIl, 'A'));
        put(out, 'peak', eng(r.iPeak, 'A') + ' (CCM estimate)');
        put(out, 'valley', eng(r.iValley, 'A') + ' (CCM estimate)');
        put(out, 'ripplepct', r.ripplePct.toFixed(1) + ' % of load');
        put(out, 'lcrit', eng(r.lCrit, 'H'));
        put(out, 'mode', r.ccm ? 'CCM boundary met' : 'CCM boundary not met', r.ccm ? 'ok' : 'warn');
        put(out, 'ontime', r.onTimeNs.toFixed(0) + ' ns');
        put(out, 'pin', eng(r.inputPower, 'W'));
        put(out, 'iin', eng(r.inputCurrent, 'A'));
        put(out, 'loss', eng(r.estimatedLoss, 'W'));
        put(out, 'note', r.ccm
          ? 'Ideal CCM model. D = Vout/Vin; efficiency is used only to estimate input power and loss. Check controller limits, switch drops, inductor saturation, capacitor ripple current, and transient response for a real design.'
          : 'The CCM boundary is not met at this load. Duty, ripple and peak values are CCM estimates—not a solved DCM operating point. Select a larger inductance or use a DCM model for this operating region.',
          r.ccm ? null : 'warn');
        drawBuckPlot(out, r);
      },

      linear: function (form, out) {
        var r = linear({
          vin: num(form, 'vin'), vout: num(form, 'vout'), iout: num(form, 'iout'),
          thetaJa: num(form, 'theta'), ambient: num(form, 'ambient'), tjMax: 125
        });
        if (!r) { clearReadouts(out,['power','tj','headroom','eff','maxcur','verdict']); put(out,'note','Enter Vin ≥ Vout ≥ 0, a positive load current, and a valid thermal resistance.','warn'); return; }
        put(out, 'power', r.power.toFixed(2) + ' W');
        put(out, 'tj', r.tj.toFixed(0) + ' °C');
        put(out, 'headroom', r.headroom.toFixed(0) + ' °C');
        put(out, 'eff', r.efficiency.toFixed(0) + ' %');
        put(out, 'maxcur', eng(r.maxCurrent, 'A'));
        put(out, 'verdict', r.safe ? 'Within the junction limit' : 'Over the junction limit',
            r.safe ? 'ok' : 'warn');
        put(out, 'note', r.safe
          ? 'Junction temperature is inside the 125 °C limit at this ambient. Thermal vias and copper area will only help.'
          : 'Junction temperature exceeds 125 °C. Reduce the input voltage, add a heatsink, or switch to a switching regulator — a linear part is burning ' +
            r.power.toFixed(1) + ' W as heat here.',
          r.safe ? null : 'warn');
      },

      divider: function (form, out) {
        var r = divider({ vin: num(form, 'vin'), r1: num(form, 'r1'), r2: num(form, 'r2') });
        if (!r) { clearReadouts(out,['vout','current','ratio','p1','p2']); put(out,'note','Enter a positive source voltage and positive resistor values.','warn'); return; }
        put(out, 'vout', r.vout.toFixed(4) + ' V');
        put(out, 'current', eng(r.current, 'A'));
        put(out, 'ratio', (r.ratio * 100).toFixed(2) + ' %');
        put(out, 'p1', eng(r.p1, 'W'));
        put(out, 'p2', eng(r.p2, 'W'));
        put(out, 'zout', eng(r.zout, 'Ω'));
        put(out, 'note', 'Output impedance of this divider is R1 in parallel with R2, which loads whatever it feeds. Keep the standing current at least 10× the ADC leakage if this is a sense divider.');
      },

      led: function (form, out) {
        var r = led({
          supply: num(form, 'supply'), forward: num(form, 'forward'),
          current: num(form, 'current') / 1000, count: num(form, 'count')
        });
        if (!r) {
          clearReadouts(out,['resistance','nearest','powerr','powerled']);
          put(out, 'note', 'Check that supply exceeds the total forward voltage and that current and LED count are positive.','warn');
          return;
        }
        put(out, 'resistance', r.resistance.toFixed(1) + ' Ω');
        put(out, 'nearest', r.nearest ? r.nearest + ' Ω (E12)' : '—');
        put(out, 'currentsel', r.currentSelected ? (r.currentSelected * 1000).toFixed(1) + ' mA' : '—');
        put(out, 'powerr', (r.powerR * 1000).toFixed(1) + ' mW');
        put(out, 'powerled', (r.powerLed * 1000).toFixed(1) + ' mW');
        var direction = r.currentErrorPct > 0 ? 'above' : 'below';
        put(out, 'note',
          (r.nearest
            ? 'The E12 value of ' + r.nearest + ' Ω sets the current ' + Math.abs(r.currentErrorPct).toFixed(1) + ' % ' + direction +
              ' the target (' + (r.currentSelected * 1000).toFixed(1) + ' mA), and dissipates ' + (r.powerSelected * 1000).toFixed(1) + ' mW. '
            : '') +
          (r.powerR > 0.125
            ? 'That is over 1/8 W, so use a 1/4 W or larger part.'
            : 'A standard 1/8 W resistor is adequate here.') +
          ' Always step to the next higher resistor if driving the LED above its rated current is a risk.');
      },

      pwm: function (form, out) {
        var r = pwm({ freq: num(form, 'freq') * 1e3, duty: num(form, 'duty') / 100, high: num(form, 'high') });
        if (!r) {
          clearReadouts(out, ['period','ontime','offtime','dutypct','avg','rms']);
          put(out, 'note', 'Duty must sit between 0 % and 100 %, and frequency and high level must be greater than zero.', 'warn');
          drawPwmPlot(out, null, form);
          return;
        }
        put(out, 'period', eng(r.period, 's'));
        put(out, 'ontime', eng(r.ton, 's'));
        put(out, 'offtime', eng(r.toff, 's'));
        put(out, 'dutypct', r.dutyPct.toFixed(1) + ' %');
        put(out, 'avg', eng(r.average, 'V'));
        put(out, 'rms', eng(r.rms, 'V'));
        put(out, 'note', 'Time-average = D · V_high and RMS = V_high · √D for an ideal 0 V / V_high square wave. A real load only sees the average if its own filtering is fast enough; a MOSFET gate, an LED and a motor each respond differently to the same waveform.');
        drawPwmPlot(out, r, form);
      },

      rc: function (form, out) {
        var r = rc({ r: num(form, 'r'), c: num(form, 'c') * 1e-9 });
        if (!r) { clearReadouts(out,['tau','rise','t95','cutoff']); put(out,'note','Enter positive resistance and capacitance values.','warn'); return; }
        put(out, 'tau', eng(r.tau, 's'));
        put(out, 'rise', eng(r.rise, 's'));
        put(out, 't95', eng(r.t95, 's'));
        put(out, 'cutoff', eng(r.cutoff, 'Hz'));
        put(out, 'note', 'A first-order RC reaches 63 % of its final value in one time constant, 95 % in three. For an ADC sample-and-hold, keep the source impedance low enough that this settles inside the sampling window.');
      }
    };

    function wireRanges(form) {
      Array.prototype.forEach.call(form.querySelectorAll('[data-sync-range]'), function (range) {
        var name=range.getAttribute('data-sync-range');
        var field=form.querySelector('[name="'+name+'"]');
        var display=document.getElementById(range.getAttribute('data-range-display'));
        if (!field) return;
        function paint() {
          range.value=field.value;
          if (display) display.textContent=Number(field.value).toLocaleString(undefined,{maximumFractionDigits:2})+' '+(range.getAttribute('data-unit')||'');
        }
        range.addEventListener('input',function(){field.value=range.value;paint();field.dispatchEvent(new Event('input',{bubbles:true}));});
        field.addEventListener('input',paint);
        field.addEventListener('change',paint);
        form.addEventListener('reset',function(){setTimeout(paint,0);});
        paint();
      });
    }

    Array.prototype.forEach.call(document.querySelectorAll('form[data-calc]'), function (form) {
      var out = document.getElementById('calcOut');
      var fn = CALCS[form.getAttribute('data-calc')];
      if (!out || !fn) return;

      function run() { fn(form, out); }
      wireRanges(form);
      form.addEventListener('input', run);
      form.addEventListener('change', run);
      form.addEventListener('reset', function () { setTimeout(run, 0); });
      run();

      var copy = document.getElementById('calcCopy');
      if (copy) {
        copy.addEventListener('click', function () {
          var lines = [];
          Array.prototype.forEach.call(out.querySelectorAll('[data-key]'), function (el) {
            var label = el.getAttribute('data-label');
            if (label) lines.push(label + ': ' + el.textContent);
          });
          var text = lines.join('\n') + '\n\nelitebotstudios.me';
          if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function () {
              copy.textContent = 'Copied';
              setTimeout(function () { copy.textContent = 'Copy results'; }, 1600);
            });
          }
        });
      }
    });

    /* ---- shareable links: read ?key=value pairs into the inputs ---------- */
    Array.prototype.forEach.call(document.querySelectorAll('form[data-calc]'), function (form) {
      var params = new URLSearchParams(location.search);
      var touched = false;
      params.forEach(function (v, k) {
        var el = form.querySelector('[name="' + k + '"]');
        if (el) { el.value = v; touched = true; el.dispatchEvent(new Event('input', { bubbles: true })); }
      });
      if (touched) form.dispatchEvent(new Event('input'));
    });
  }());
}
