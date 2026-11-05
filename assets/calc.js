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
  var k = o.internal ? 0.024 : 0.048;
  if (!(I > 0) || !(dT > 0) || !(oz > 0)) return null;
  var areaMil2 = Math.pow(I / (k * Math.pow(dT, 0.44)), 1 / 0.725);
  var thickMil = oz * OZ_TO_MILS;
  var widthMil = areaMil2 / thickMil;
  var widthMm = widthMil * MIL2MM;
  var wM = widthMm * 1e-3, tM = thickMil * MIL2MM * 1e-3, lM = len * 1e-3;
  var R = (wM * tM) > 0 ? CU_RHO20 * (1 + CU_ALPHA * dT) * lM / (wM * tM) : 0;
  return {
    areaMil2: areaMil2, widthMil: widthMil, widthMm: widthMm,
    resistance: R, drop: I * R, power: I * I * R, thickMm: tM * 1e3
  };
}

function buck(o) {
  var vin = o.vin, vout = o.vout, f = o.freq, L = o.inductance, iout = o.iout, eff = o.eff || 1;
  if (!(vin > 0) || !(vout > 0) || !(f > 0) || !(L > 0) || vout >= vin) return null;
  var d = vout / (vin * eff);
  if (d > 1) return null;
  var dIl = vout * (1 - d) / (L * f);
  var ioutSafe = iout > 0 ? iout : 1e-9;
  return {
    duty: d, dutyIdeal: vout / vin, deltaIl: dIl,
    iPeak: iout + dIl / 2, iValley: iout - dIl / 2,
    ripplePct: (dIl / ioutSafe) * 100,
    lCrit: (vout * (1 - d)) / (2 * f * ioutSafe),
    ccm: iout > dIl / 2,
    onTimeNs: (d / f) * 1e9, periodNs: (1 / f) * 1e9,
    maxOut: vin * eff
  };
}

function linear(o) {
  var vin = o.vin, vout = o.vout, iout = o.iout, theta = o.thetaJa, ta = o.ambient;
  var tjmax = o.tjMax || 125;
  if (!(vin > 0) || vout < 0 || !(iout > 0) || vout > vin) return null;
  var drop = vin - vout, p = drop * iout, rise = p * theta, tj = ta + rise;
  return {
    drop: drop, power: p, rise: rise, tj: tj, headroom: tjmax - tj,
    efficiency: (vout / vin) * 100, safe: tj <= tjmax,
    maxCurrent: theta > 0 ? (tjmax - ta) / (theta * drop) : Infinity
  };
}

function divider(o) {
  var vin = o.vin, r1 = o.r1, r2 = o.r2;
  if (!(r1 > 0) || !(r2 > 0)) return null;
  var vout = vin * r2 / (r1 + r2), cur = vin / (r1 + r2);
  return {
    vout: vout, current: cur,
    p1: cur * cur * r1, p2: cur * cur * r2,
    ratio: r2 / (r1 + r2)
  };
}

function led(o) {
  var vs = o.supply, vf = o.forward, i = o.current, n = o.count || 1;
  if (!(vs > 0) || !(vf > 0) || !(i > 0)) return null;
  var drop = n * vf;
  if (drop >= vs) return null;
  var r = (vs - drop) / i, near = nearestE12(r);
  return {
    resistance: r, nearest: near, powerR: i * i * r,
    powerLed: drop * i, totalPower: vs * i, drop: drop
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
  module.exports = { traceWidth, buck, linear, divider, led, rc, nearestE12, E12, sig, eng };
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
      var v = parseFloat(el.value);
      return isFinite(v) ? v : fallback;
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

    var CALCS = {
      tracewidth: function (form, out) {
        var internal = radio(form, 'layer') === 'internal';
        var r = traceWidth({
          current: num(form, 'current'), rise: num(form, 'rise'),
          copper: num(form, 'copper'), length: num(form, 'length'), internal: internal
        });
        if (!r) { put(out, 'width', '—'); return; }
        put(out, 'width', Number(r.widthMm.toPrecision(3)) + ' mm');
        put(out, 'widthmil', Number(r.widthMil.toPrecision(3)) + ' mil');
        put(out, 'area', Number(r.areaMil2.toPrecision(3)) + ' mil²');
        put(out, 'resistance', eng(r.resistance, 'Ω'));
        put(out, 'drop', eng(r.drop, 'V'));
        put(out, 'power', eng(r.power, 'W'));
        var rec = r.widthMm <= 0.15 ? 'below the usual 0.15 mm fab minimum' :
                  r.widthMm <= 0.25 ? 'fine for most fabs, check the minimum' :
                  'comfortably inside typical fab limits';
        put(out, 'note', 'At 0.15 mm minimum trace/space this is ' + rec + '.');
      },

      buck: function (form, out) {
        var r = buck({
          vin: num(form, 'vin'), vout: num(form, 'vout'),
          freq: num(form, 'freq') * 1e3, inductance: num(form, 'inductance') * 1e-6,
          iout: num(form, 'iout'), eff: num(form, 'eff') / 100
        });
        if (!r) {
          put(out, 'duty', '—');
          put(out, 'note', 'Vout must be lower than Vin for a buck. Check the inputs.', 'warn');
          return;
        }
        put(out, 'duty', (r.duty * 100).toFixed(1) + ' %');
        put(out, 'ripple', eng(r.deltaIl, 'A'));
        put(out, 'peak', eng(r.iPeak, 'A'));
        put(out, 'ripplepct', r.ripplePct.toFixed(0) + ' % of load');
        put(out, 'lcrit', eng(r.lCrit, 'H'));
        put(out, 'mode', r.ccm ? 'Continuous (CCM)' : 'Discontinuous (DCM)',
            r.ccm ? 'ok' : 'warn');
        put(out, 'ontime', r.onTimeNs.toFixed(0) + ' ns');
        put(out, 'note', r.ccm
          ? 'Stays in continuous conduction at this load. Peak current sets the inductor saturation rating.'
          : 'This inductor is too small for the load — the converter enters discontinuous mode and the output ripple rises sharply. Increase L or the switching frequency.',
          r.ccm ? null : 'warn');
      },

      linear: function (form, out) {
        var r = linear({
          vin: num(form, 'vin'), vout: num(form, 'vout'), iout: num(form, 'iout'),
          thetaJa: num(form, 'theta'), ambient: num(form, 'ambient'), tjMax: 125
        });
        if (!r) { put(out, 'power', '—'); return; }
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
        if (!r) { put(out, 'vout', '—'); return; }
        put(out, 'vout', r.vout.toFixed(4) + ' V');
        put(out, 'current', eng(r.current, 'A'));
        put(out, 'ratio', (r.ratio * 100).toFixed(2) + ' %');
        put(out, 'p1', eng(r.p1, 'W'));
        put(out, 'p2', eng(r.p2, 'W'));
        put(out, 'note', 'Output impedance of this divider is R1 in parallel with R2, which loads whatever it feeds. Keep the standing current at least 10× the ADC leakage if this is a sense divider.');
      },

      led: function (form, out) {
        var r = led({
          supply: num(form, 'supply'), forward: num(form, 'forward'),
          current: num(form, 'current') / 1000, count: num(form, 'count')
        });
        if (!r) {
          put(out, 'resistance', '—');
          put(out, 'note', 'The forward voltage of the string is at or above the supply. Increase the supply or use fewer LEDs.', 'warn');
          return;
        }
        put(out, 'resistance', r.resistance.toFixed(1) + ' Ω');
        put(out, 'nearest', r.nearest ? r.nearest + ' Ω (E12)' : '—');
        put(out, 'powerr', (r.powerR * 1000).toFixed(1) + ' mW');
        put(out, 'powerled', (r.powerLed * 1000).toFixed(1) + ' mW');
        put(out, 'note', r.powerR > 0.125
          ? 'The resistor dissipates over 1/8 W — use a 1/4 W or larger part.'
          : 'A standard 1/8 W resistor is adequate here.');
      },

      rc: function (form, out) {
        var r = rc({ r: num(form, 'r'), c: num(form, 'c') * 1e-9 });
        if (!r) { put(out, 'tau', '—'); return; }
        put(out, 'tau', eng(r.tau, 's'));
        put(out, 'rise', eng(r.rise, 's'));
        put(out, 't95', eng(r.t95, 's'));
        put(out, 'cutoff', eng(r.cutoff, 'Hz'));
        put(out, 'note', 'A first-order RC reaches 63 % of its final value in one time constant, 95 % in three. For an ADC sample-and-hold, keep the source impedance low enough that this settles inside the sampling window.');
      }
    };

    Array.prototype.forEach.call(document.querySelectorAll('form[data-calc]'), function (form) {
      var out = document.getElementById('calcOut');
      var fn = CALCS[form.getAttribute('data-calc')];
      if (!out || !fn) return;

      function run() { fn(form, out); }
      form.addEventListener('input', run);
      form.addEventListener('change', run);
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
        if (el) { el.value = v; touched = true; }
      });
      if (touched) form.dispatchEvent(new Event('input'));
    });
  }());
}
