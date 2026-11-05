# -*- coding: utf-8 -*-
"""Generates the engineering calculator hub and six individual tools.
Each page is a real, working tool: inputs, live results, the formula it uses,
and an honest note about what the number does and does not mean."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build
from build import page, write

CALC_JS = '  <script src="' + build.asset('assets/calc.js') + '" defer></script>\n'

TOOLS = [
    dict(
        slug='trace-width', name='PCB Trace Width',
        title='PCB Trace Width Calculator (IPC-2221) | Elite Bot Studios',
        desc='Calculate minimum PCB trace width from current, temperature rise, copper weight and layer, using the IPC-2221 power-law model. Includes resistance, voltage drop and power loss.',
        blurb='Minimum copper width for a given current and temperature rise, per IPC-2221. Returns resistance, voltage drop and loss for the length you enter.',
        tags=['IPC-2221', 'PCB', 'copper'],
        calc='tracewidth',
        form='''          <div class="calc-row">
            <div class="calc-field">
              <label for="current">Current <span class="unit">A</span></label>
              <input id="current" name="current" type="number" value="3" min="0.01" step="0.1" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="rise">Temperature rise <span class="unit">°C</span></label>
              <input id="rise" name="rise" type="number" value="10" min="1" max="100" step="1" inputmode="decimal">
            </div>
          </div>
          <div class="calc-row">
            <div class="calc-field">
              <label for="copper">Copper weight <span class="unit">oz</span></label>
              <select id="copper" name="copper">
                <option value="0.5">0.5 oz</option>
                <option value="1" selected>1 oz</option>
                <option value="2">2 oz</option>
                <option value="3">3 oz</option>
                <option value="4">4 oz</option>
                <option value="6">6 oz</option>
              </select>
            </div>
            <div class="calc-field">
              <label for="length">Trace length <span class="unit">mm</span></label>
              <input id="length" name="length" type="number" value="50" min="0" step="1" inputmode="decimal">
            </div>
          </div>
          <div class="calc-toggle">
            <label><input type="radio" name="layer" value="external" checked> External layer</label>
            <label><input type="radio" name="layer" value="internal"> Internal layer</label>
          </div>''',
        outputs=[('width', 'Minimum width', True), ('widthmil', 'In mils', False),
                 ('area', 'Cross-section', False), ('resistance', 'Resistance', False),
                 ('drop', 'Voltage drop', False), ('power', 'Power lost as heat', False)],
        formula='I = k · ΔT<sup>0.44</sup> · A<sup>0.725</sup>   →   A = ( I / (k · ΔT<sup>0.44</sup>) )<sup>1/0.725</sup>   →   w = A / (oz × 1.378 mil)<br>k = <b>0.048</b> external · <b>0.024</b> internal · A in mil² · R = ρ·L/A with ρ<sub>Cu</sub> = 1.724 × 10⁻⁸ Ω·m at 20 °C, +0.00393/°C',
        caveat='IPC-2221 is an empirical model from measured boards, not a field solver. It ignores copper planes, thermal reliefs, adjacent traces and airflow. For anything carrying real power, treat the result as a floor: add margin, run a thermal test on the actual board, and check your fabricator\'s minimum trace and space.',
    ),
    dict(
        slug='buck-converter', name='Buck Converter',
        title='Buck Converter Design Calculator | Elite Bot Studios',
        desc='Duty cycle, inductor ripple current, peak current and the critical inductance for a buck converter. Shows whether your design stays in continuous conduction.',
        blurb='Duty cycle, ripple current, peak current and the inductance at which the converter drops out of continuous conduction.',
        tags=['power', 'DC-DC', 'inductor'],
        calc='buck',
        form='''          <div class="calc-row">
            <div class="calc-field">
              <label for="vin">Input voltage <span class="unit">V</span></label>
              <input id="vin" name="vin" type="number" value="12" min="0.1" step="0.1" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="vout">Output voltage <span class="unit">V</span></label>
              <input id="vout" name="vout" type="number" value="5" min="0.1" step="0.1" inputmode="decimal">
            </div>
          </div>
          <div class="calc-row">
            <div class="calc-field">
              <label for="freq">Switching frequency <span class="unit">kHz</span></label>
              <input id="freq" name="freq" type="number" value="500" min="1" step="10" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="inductance">Inductance <span class="unit">µH</span></label>
              <input id="inductance" name="inductance" type="number" value="22" min="0.1" step="1" inputmode="decimal">
            </div>
          </div>
          <div class="calc-row">
            <div class="calc-field">
              <label for="iout">Load current <span class="unit">A</span></label>
              <input id="iout" name="iout" type="number" value="2" min="0.01" step="0.1" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="eff">Assumed efficiency <span class="unit">%</span></label>
              <input id="eff" name="eff" type="number" value="90" min="50" max="100" step="1" inputmode="decimal">
            </div>
          </div>''',
        outputs=[('duty', 'Duty cycle', True), ('ripple', 'Inductor ripple ΔIL', False),
                 ('peak', 'Peak inductor current', False), ('ripplepct', 'Ripple vs load', False),
                 ('lcrit', 'Critical inductance', False), ('ontime', 'Switch on-time', False),
                 ('mode', 'Conduction mode', False)],
        formula='D = V<sub>out</sub> / (V<sub>in</sub> · η)   ·   ΔI<sub>L</sub> = V<sub>out</sub>(1 − D) / (L · f<sub>sw</sub>)   ·   I<sub>peak</sub> = I<sub>out</sub> + ΔI<sub>L</sub>/2   ·   L<sub>crit</sub> = V<sub>out</sub>(1 − D) / (2 · f<sub>sw</sub> · I<sub>out</sub>)',
        caveat='Ideal switch model with a single efficiency term. It does not model diode or synchronous-rectifier losses, capacitor ESR, or the control loop. Peak current is what sizes the inductor\'s saturation rating — leave headroom above it. Verify stability and transient response on the bench.',
    ),
    dict(
        slug='linear-regulator', name='Linear Regulator Thermal',
        title='Linear Regulator Power & Junction Temperature | Elite Bot Studios',
        desc='Power dissipation, junction temperature rise and maximum safe current for a linear regulator, from dropout voltage, load current and package thermal resistance.',
        blurb='How much power a linear regulator turns into heat, and whether the junction stays inside its limit.',
        tags=['power', 'thermal', 'LDO'],
        calc='linear',
        form='''          <div class="calc-row">
            <div class="calc-field">
              <label for="vin">Input voltage <span class="unit">V</span></label>
              <input id="vin" name="vin" type="number" value="12" min="0" step="0.1" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="vout">Output voltage <span class="unit">V</span></label>
              <input id="vout" name="vout" type="number" value="5" min="0" step="0.1" inputmode="decimal">
            </div>
          </div>
          <div class="calc-row">
            <div class="calc-field">
              <label for="iout">Load current <span class="unit">A</span></label>
              <input id="iout" name="iout" type="number" value="0.5" min="0.001" step="0.05" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="theta">θ<sub>JA</sub> <span class="unit">°C/W</span></label>
              <input id="theta" name="theta" type="number" value="65" min="1" step="1" inputmode="decimal">
            </div>
          </div>
          <div class="calc-field">
            <label for="ambient">Ambient temperature <span class="unit">°C</span></label>
            <input id="ambient" name="ambient" type="number" value="40" min="-20" max="100" step="1" inputmode="decimal">
          </div>''',
        outputs=[('power', 'Power dissipated', True), ('tj', 'Junction temperature', False),
                 ('headroom', 'Margin to 125 °C', False), ('eff', 'Efficiency', False),
                 ('maxcur', 'Max safe current', False), ('verdict', 'Verdict', False)],
        formula='P = (V<sub>in</sub> − V<sub>out</sub>) · I<sub>out</sub>   ·   T<sub>J</sub> = T<sub>A</sub> + P · θ<sub>JA</sub>   ·   η = V<sub>out</sub> / V<sub>in</sub>',
        caveat='θ<sub>JA</sub> is the number that decides this, and the datasheet value assumes a JEDEC test board with a specific copper area. A real board with small pads runs hotter. 125 °C is a conventional design limit, not the absolute maximum rating — check your part. Measure the case temperature on the first prototype.',
    ),
    dict(
        slug='voltage-divider', name='Voltage Divider',
        title='Voltage Divider Calculator | Elite Bot Studios',
        desc='Output voltage, standing current and resistor power for a two-resistor divider, with the source impedance that loads whatever it feeds.',
        blurb='Output voltage from two resistors, plus the standing current that decides whether it is usable as a sensor front end.',
        tags=['analog', 'resistors', 'ADC'],
        calc='divider',
        form='''          <div class="calc-field">
            <label for="vin">Input voltage <span class="unit">V</span></label>
            <input id="vin" name="vin" type="number" value="12" min="0" step="0.1" inputmode="decimal">
          </div>
          <div class="calc-row">
            <div class="calc-field">
              <label for="r1">R1 <span class="unit">Ω</span></label>
              <input id="r1" name="r1" type="number" value="10000" min="0.1" step="100" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="r2">R2 <span class="unit">Ω</span></label>
              <input id="r2" name="r2" type="number" value="10000" min="0.1" step="100" inputmode="decimal">
            </div>
          </div>''',
        outputs=[('vout', 'Output voltage', True), ('current', 'Standing current', False),
                 ('ratio', 'Divider ratio', False), ('p1', 'Power in R1', False),
                 ('p2', 'Power in R2', False)],
        formula='V<sub>out</sub> = V<sub>in</sub> · R2 / (R1 + R2)   ·   I = V<sub>in</sub> / (R1 + R2)   ·   Z<sub>out</sub> = R1 ‖ R2',
        caveat='The output is not a stiff voltage source — its impedance is R1 in parallel with R2. If this feeds an ADC, keep the standing current well above the input leakage and make sure the impedance is low enough for the sample-and-hold to settle.',
    ),
    dict(
        slug='led-resistor', name='LED Series Resistor',
        title='LED Series Resistor Calculator | Elite Bot Studios',
        desc='Series resistor value for one or more LEDs from supply voltage, forward voltage and target current, with the nearest E12 value and resistor power.',
        blurb='The resistor between a supply and an LED string, with the nearest preferred value and the power it has to survive.',
        tags=['analog', 'LED', 'resistors'],
        calc='led',
        form='''          <div class="calc-row">
            <div class="calc-field">
              <label for="supply">Supply voltage <span class="unit">V</span></label>
              <input id="supply" name="supply" type="number" value="5" min="0.1" step="0.1" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="forward">Forward voltage <span class="unit">V</span></label>
              <input id="forward" name="forward" type="number" value="2" min="0.1" step="0.1" inputmode="decimal">
            </div>
          </div>
          <div class="calc-row">
            <div class="calc-field">
              <label for="current">Target current <span class="unit">mA</span></label>
              <input id="current" name="current" type="number" value="20" min="0.1" step="1" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="count">LEDs in series <span class="unit">n</span></label>
              <input id="count" name="count" type="number" value="1" min="1" step="1" inputmode="numeric">
            </div>
          </div>''',
        outputs=[('resistance', 'Series resistor', True), ('nearest', 'Nearest E12', False),
                 ('powerr', 'Power in resistor', False), ('powerled', 'Power in LEDs', False)],
        formula='R = (V<sub>supply</sub> − n · V<sub>f</sub>) / I   ·   P<sub>R</sub> = I² · R   ·   P<sub>LED</sub> = n · V<sub>f</sub> · I',
        caveat='V<sub>f</sub> varies part to part and falls as the LED warms, so the current is not as precise as it looks. For anything beyond an indicator, drive the LED from a constant-current source and check the datasheet curve at your actual current.',
    ),
    dict(
        slug='rc-time-constant', name='RC Time Constant',
        title='RC Time Constant Calculator | Elite Bot Studios',
        desc='Time constant, 10–90% rise time, settling time and cutoff frequency for an RC network from resistance and capacitance.',
        blurb='Time constant, rise time, settling time and the corner frequency of a first-order RC filter.',
        tags=['analog', 'filter', 'timing'],
        calc='rc',
        form='''          <div class="calc-row">
            <div class="calc-field">
              <label for="r">Resistance <span class="unit">Ω</span></label>
              <input id="r" name="r" type="number" value="10000" min="0.1" step="100" inputmode="decimal">
            </div>
            <div class="calc-field">
              <label for="c">Capacitance <span class="unit">nF</span></label>
              <input id="c" name="c" type="number" value="100" min="0.001" step="1" inputmode="decimal">
            </div>
          </div>''',
        outputs=[('tau', 'Time constant τ', True), ('rise', '10–90 % rise time', False),
                 ('t95', 'Settling to 95 %', False), ('cutoff', '−3 dB cutoff', False)],
        formula='τ = R · C   ·   t<sub>10–90</sub> = 2.197 τ   ·   t<sub>95</sub> = 3 τ   ·   f<sub>c</sub> = 1 / (2πτ)',
        caveat='Assumes an ideal step into a single-pole network with a stiff source. Real capacitors have ESR and leakage, and a real source has its own impedance, so the measured edge will be slower than this predicts.',
    ),
]


def calc_page(t):
    rows = []
    for key, label, primary in t['outputs']:
        rows.append('<div class="calc-readout%s">\n              <dt>%s</dt>\n              <dd data-key="%s" data-label="%s">—</dd>\n            </div>'
                    % (' primary' if primary else '', label, key, label))
    rows = '\n            '.join(rows)

    body = '''
    <section class="page-head">
      <div class="wrap">
        <a class="backlink" href="/tools.html">&larr; All tools</a>
        <h1 style="font-size:clamp(1.7rem,5vw,2.4rem);margin:14px 0 14px">%(name)s</h1>
        <p>%(blurb)s</p>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <h2 class="sr-only">Calculator inputs and results</h2>
        <div class="calc-grid">
          <form class="calc-panel" data-calc="%(calc)s" novalidate>
%(form)s
            <div class="calc-actions">
              <button class="btn btn-ghost" type="reset">Reset to defaults</button>
            </div>
          </form>

          <div>
            <div class="calc-output" id="calcOut" aria-live="polite">
              <span class="label">Result</span>
            <div class="calc-readout-group">
            %(rows)s
            </div>
              <div class="calc-note" id="calcNote" data-key="note"></div>
              <div class="calc-actions">
                <button class="btn btn-ghost" type="button" id="calcCopy">Copy results</button>
              </div>
            </div>
            <div class="calc-formula">%(formula)s</div>
          </div>
        </div>

        <div class="notice reveal" style="margin-top:34px;max-width:860px">
          <div>
            <b>Read this before you commit a design</b>
            <p>%(caveat)s</p>
          </div>
        </div>

        <div style="margin-top:34px" class="reveal">
          <a class="backlink" href="/tools.html">&larr; All tools</a>
        </div>
      </div>
    </section>
''' % dict(name=t['name'], blurb=t['blurb'], calc=t['calc'], form=t['form'],
           rows=rows, formula=t['formula'], caveat=t['caveat'])

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": t['name'],
        "applicationCategory": "EngineeringApplication",
        "operatingSystem": "Any browser",
        "url": "https://elitebotstudios.me/tools/%s.html" % t['slug'],
        "description": t['desc'],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "publisher": {"@type": "Organization", "name": "Elite Bot Studios",
                      "url": "https://elitebotstudios.me"}
    }, indent=2)

    page(t['title'], t['desc'], '/tools/%s.html' % t['slug'], body,
         jsonld=ld, extra_head=CALC_JS)


def hub():
    cards = []
    for t in TOOLS:
        tags = ''.join('<span class="chip">%s</span>' % x for x in t['tags'])
        cards.append('''          <a class="tool-card reveal" href="/tools/%s.html">
            <h3>%s</h3>
            <p>%s</p>
            <div class="chips">%s</div>
            <span class="tool-go">Open tool &rarr;</span>
          </a>''' % (t['slug'], t['name'], t['blurb'], tags))

    body = '''
    <section class="page-head">
      <div class="wrap">
        <span class="eyebrow">Tools</span>
        <h1>Small tools for early estimates.</h1>
        <p>Six tools for the questions that come up on every board: how wide the copper has to be, how hot the
           regulator will run, how much ripple the inductor will pass. They run entirely in your browser —
           nothing you type is sent anywhere.</p>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <h2 class="sr-only">Available calculators</h2>
        <div class="grid grid-2">
%s
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="prose reveal" style="max-width:760px">
          <h2>Why these are free</h2>
          <p>These lightweight educational calculators make common engineering equations easier to inspect and test. Inputs stay in the browser and are not sent to a calculation API. No account or email gate is required.</p>
          <h2>What they are not</h2>
          <p>Every one of these is a closed-form estimate. None of them replaces a field solver, a thermal
             test on a real board, or the datasheet of the part you actually bought. Each page says exactly
             where its model breaks down — read that note before you commit a design.</p>
        </div>
      </div>
    </section>
''' % '\n'.join(cards)

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Engineering Calculators",
        "url": "https://elitebotstudios.me/tools.html",
        "description": "Free engineering calculators for PCB trace width, buck converters, linear regulator thermals, voltage dividers, LED resistors and RC time constants.",
        "isPartOf": {"@type": "WebSite", "url": "https://elitebotstudios.me"}
    }, indent=2)

    page('Engineering Calculators — PCB, Power, Analog | Elite Bot Studios',
         'Free client-side engineering calculators: IPC-2221 trace width, buck converter design, '
         'linear regulator thermals, voltage dividers, LED resistors and RC time constants.',
         '/tools.html', body, jsonld=ld)


if __name__ == '__main__':
    print('building tools…')
    hub()
    for t in TOOLS:
        calc_page(t)
    print('done.')
