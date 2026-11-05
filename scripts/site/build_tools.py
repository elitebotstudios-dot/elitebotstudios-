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
        caveat='IPC-2221 is an empirical model, not a field solver. The resistance estimate assumes 20 °C ambient and adds your entered rise; it does not model copper planes, thermal reliefs, adjacent traces, or airflow. For anything carrying real power, treat the result as a floor: add margin, run a thermal test on the actual board, and check your fabricator\'s minimum trace and space.',
    ),
    dict(
        slug='buck-converter', name='Buck Converter Explorer',
        title='Interactive Buck Converter Explorer | Elite Bot Studios',
        desc='Explore the ideal continuous-conduction buck-converter model with adjustable input, output, frequency, inductance, load, and efficiency. Includes live PWM and inductor-current plots with the model boundary shown.',
        blurb='Adjust the operating point and inspect ideal CCM duty, inductor ripple, current limits, and an efficiency-based input-power estimate.',
        tags=['power conversion', 'interactive model', 'waveforms'],
        calc='buck',
        form='''          <p class="range-help">Scrub a control for a quick study, or type an exact value.</p>
          <div class="calc-row">
            <div class="calc-field">
              <label for="vin">Input voltage <span class="unit">V</span></label>
              <input id="vin" name="vin" type="number" value="12" min="4" max="48" step="0.1" inputmode="decimal">
              <div class="range-row"><div class="range-top"><span>INPUT</span><output id="vinRangeValue">12 V</output></div><input type="range" min="4" max="48" step="0.1" value="12" data-sync-range="vin" data-range-display="vinRangeValue" data-unit="V" aria-label="Adjust input voltage"></div>
            </div>
            <div class="calc-field">
              <label for="vout">Output voltage <span class="unit">V</span></label>
              <input id="vout" name="vout" type="number" value="5" min="0.5" max="36" step="0.1" inputmode="decimal">
              <div class="range-row"><div class="range-top"><span>OUTPUT</span><output id="voutRangeValue">5 V</output></div><input type="range" min="0.5" max="36" step="0.1" value="5" data-sync-range="vout" data-range-display="voutRangeValue" data-unit="V" aria-label="Adjust output voltage"></div>
            </div>
          </div>
          <div class="calc-row">
            <div class="calc-field">
              <label for="freq">Switching frequency <span class="unit">kHz</span></label>
              <input id="freq" name="freq" type="number" value="500" min="50" max="1000" step="10" inputmode="decimal">
              <div class="range-row"><div class="range-top"><span>FREQUENCY</span><output id="freqRangeValue">500 kHz</output></div><input type="range" min="50" max="1000" step="10" value="500" data-sync-range="freq" data-range-display="freqRangeValue" data-unit="kHz" aria-label="Adjust switching frequency"></div>
            </div>
            <div class="calc-field">
              <label for="inductance">Inductance <span class="unit">µH</span></label>
              <input id="inductance" name="inductance" type="number" value="22" min="2.2" max="100" step="0.1" inputmode="decimal">
              <div class="range-row"><div class="range-top"><span>INDUCTANCE</span><output id="inductanceRangeValue">22 µH</output></div><input type="range" min="2.2" max="100" step="0.1" value="22" data-sync-range="inductance" data-range-display="inductanceRangeValue" data-unit="µH" aria-label="Adjust inductance"></div>
            </div>
          </div>
          <div class="calc-row">
            <div class="calc-field">
              <label for="iout">Load current <span class="unit">A</span></label>
              <input id="iout" name="iout" type="number" value="2" min="0.1" max="10" step="0.05" inputmode="decimal">
              <div class="range-row"><div class="range-top"><span>LOAD</span><output id="ioutRangeValue">2 A</output></div><input type="range" min="0.1" max="10" step="0.05" value="2" data-sync-range="iout" data-range-display="ioutRangeValue" data-unit="A" aria-label="Adjust load current"></div>
            </div>
            <div class="calc-field">
              <label for="eff">Efficiency estimate <span class="unit">%</span></label>
              <input id="eff" name="eff" type="number" value="90" min="50" max="100" step="1" inputmode="decimal">
              <small class="range-help">Used for estimated input power only; it does not modify ideal duty.</small>
            </div>
          </div>''',
        outputs=[('duty', 'Ideal CCM duty ratio', True), ('ripple', 'Inductor ripple · CCM estimate', False),
                 ('peak', 'Peak current · CCM estimate', False), ('valley', 'Valley current · CCM estimate', False),
                 ('ripplepct', 'Ripple ratio · CCM estimate', False), ('lcrit', 'CCM boundary inductance', False),
                 ('ontime', 'Ideal switch on-time', False), ('mode', 'Operating-region check', False),
                 ('pin', 'Estimated input power', False), ('iin', 'Estimated input current', False),
                 ('loss', 'Estimated conversion loss', False)],
        formula='Ideal CCM: D ≈ V<sub>out</sub>/V<sub>in</sub> · ΔI<sub>L</sub> = V<sub>out</sub>(1−D)/(L f<sub>sw</sub>) · L<sub>crit</sub> = V<sub>out</sub>(1−D)/(2 f<sub>sw</sub> I<sub>out</sub>)<br>Power estimate: P<sub>in</sub> ≈ V<sub>out</sub>I<sub>out</sub>/η · P<sub>loss</sub> ≈ P<sub>in</sub>−P<sub>out</sub>. Efficiency is not a universal correction to duty.',
        caveat='This is a steady-state ideal CCM model. Duty uses D ≈ Vout/Vin; a real converter needs more duty to account for its actual switch, diode, winding, and control losses, but efficiency alone does not specify that correction. Ripple, peak, valley, and critical inductance are CCM estimates. If the CCM boundary is not met, this tool flags the region instead of pretending to solve a DCM controller. It does not model switch transitions, parasitics, capacitor ripple, loop compensation, thermal behavior, or startup. Use the controller datasheet and verify a real design.',
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
        rows.append('<div class="calc-readout%s">\n              <dt>%s</dt>\n              <dd data-key="%s" data-label="%s"%s>—</dd>\n            </div>'
                    % (' primary' if primary else '', label, key, label, ' aria-live="polite"' if primary else ''))
    rows = '\n            '.join(rows)
    visualization=''
    if t['calc']=='buck':
        visualization='''
            <figure class="buck-explorer" id="buckExplorer" aria-labelledby="buckPlotTitle">
              <div class="buck-explorer-head"><span id="buckPlotTitle">Switch timing &amp; inductor current</span><span>IDEAL CCM MODEL</span></div>
              <svg class="buck-plot" viewBox="0 0 660 300" role="img" aria-labelledby="buckSvgTitle buckSvgDesc">
                <title id="buckSvgTitle">Live buck converter timing and inductor-current model</title>
                <desc id="buckSvgDesc">The upper plot shows an idealized switch-node PWM pulse. The lower plot shows triangular inductor current only while the continuous-conduction model is applicable.</desc>
                <path class="buck-plot-grid" d="M58 38H610M58 66H610M58 94H610M58 145H610M58 180H610M58 215H610M58 250H610M58 30V255M196 30V255M334 30V255M472 30V255M610 30V255"/>
                <path class="buck-plot-axis" d="M58 30V255H610"/>
                <path class="buck-gate-trace" id="buckGateTrace" d="M58 94V48H284V94H610"/>
                <path class="buck-current-trace" id="buckCurrentTrace" d="M58 178L284 166L610 178"/>
                <path class="buck-dash" d="M284 32V250"/>
                <text x="60" y="24">SWITCH NODE / IDEAL PWM</text><text x="60" y="138">INDUCTOR CURRENT iL</text><text x="293" y="48">D·T</text><text id="buckPeriodLabel" x="420" y="282">T = 2.00 µs · ton = 0.83 µs</text><text x="615" y="265">t</text>
              </svg>
              <figcaption class="buck-boundary" id="buckPlotBoundary" aria-live="polite">Ideal continuous-conduction estimate; the triangular ripple is centered on the selected load current.</figcaption>
            </figure>'''

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
            <div class="calc-output" id="calcOut">
              <span class="label">Result</span>
            <dl class="calc-readout-group">
            %(rows)s
            </dl>
              <div class="calc-note" id="calcNote" data-key="note" role="status" aria-live="polite"></div>
              <div class="calc-actions">
                <button class="btn btn-ghost" type="button" id="calcCopy">Copy results</button>
              </div>
            </div>
            %(visualization)s
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
           rows=rows, formula=t['formula'], caveat=t['caveat'], visualization=visualization)

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
    art={
      'trace-width':'<path d="M18 53h42l15-13 19 26 16-32 14 19h48"/><path d="M22 25h126M22 81h126"/><circle cx="60" cy="53" r="4"/><circle cx="148" cy="53" r="4"/>',
      'buck-converter':'<path d="M16 62V31h42v31h83"/><path d="M16 88 58 73l42 15 42-15"/><path d="M58 20v78"/>',
      'linear-regulator':'<path d="M22 78V28h110v50z"/><path d="m50 68 18-32 20 32"/><path d="M138 35v37"/><circle cx="138" cy="28" r="4"/>',
      'voltage-divider':'<path d="M78 18v18m0 42v18M54 36h48v14H54zm0 22h48v14H54z"/><path d="M30 50h24m48 0h36M30 64h24m48 0h36"/>',
      'led-resistor':'<path d="M20 57h35m33 0h49"/><path d="M55 42v30h33V42z"/><path d="m102 44 24 13-24 13z"/><path d="m105 34 8-8m-1 17 9-9"/>',
      'rc-time-constant':'<path d="M18 24v66m0-33h28m0-20v40m14-40v40m0-20h72"/><path d="M82 38c13 0 16 6 20 15s10 15 30 15"/>'
    }
    cards=[]
    for i,t in enumerate(TOOLS):
        tags=''.join('<span class="chip">%s</span>'%x for x in t['tags'])
        cards.append('''<a class="tool-card reveal" href="/tools/%s.html"><div class="tool-card-top"><span>MODEL / %02d</span><svg viewBox="0 0 180 110" aria-hidden="true">%s</svg></div><h3>%s</h3><p>%s</p><div class="chips">%s</div><span class="tool-go">OPEN TOOL <b>↗</b></span></a>'''%(t['slug'],i+1,art.get(t['slug'],''),t['name'],t['blurb'],tags))
    body='''
    <section class="page-head tools-head"><div class="wrap"><span class="eyebrow">Engineering tools / browser-based</span><h1>Make the first estimate<br><em>inspectable.</em></h1><p>Six small models for checking units, exploring sensitivities, and understanding assumptions. They are learning and early-design aids—not design approval.</p></div></section>
    <section class="section tools-feature-section"><div class="wrap"><article class="tools-featured"><div class="tools-feature-copy"><span class="section-index">FEATURED / POWER CONVERSION</span><h2>Move the operating point.<br><em>See what changes.</em></h2><p>An interactive ideal CCM buck model with adjustable inputs, live inductor-current and PWM plots, and an explicit operating-region boundary.</p><div class="feature-chips"><span>IDEAL CCM</span><span>LIVE MODEL</span><span>EFFICIENCY ≠ DUTY CORRECTION</span></div><a class="btn btn-primary" href="/tools/buck-converter.html">Explore the buck converter ↗</a></div><div class="tools-feature-graphic" aria-hidden="true"><svg viewBox="0 0 540 260"><path d="M26 35h488M26 82h488M26 129h488M26 176h488M26 223h488M60 20v218m95-218v218m95-218v218m95-218v218m95-218v218m95-218v218" class="feature-gridline"/><path d="M26 113V59h184v54h304" class="feature-wave-gold"/><path d="M26 198 210 167 394 198 578 167" class="feature-wave-cyan"/><path d="M210 28v208" class="feature-wave-mark"/><text x="32" y="52">PWM</text><text x="32" y="158">iL</text><text x="218" y="50">D · T</text></svg></div></article></div></section>
    <section class="section tools-library"><div class="wrap"><div class="section-heading split-heading"><div><span class="section-index">MODEL LIBRARY / 06</span><h2>Useful equations.<br><em>Clear boundaries.</em></h2></div><p>Each calculator explains the model it applies, shows a worked output, and points out where real components, board layout, and operating conditions can change the answer.</p></div><div class="tool-library-grid">%s</div></div></section>
    <section class="section tool-principles"><div class="wrap"><div class="tool-principles-grid"><div><span class="section-index">HOW TO USE THESE</span><h2>A starting point,<br>not a sign-off.</h2></div><div><p>Inputs are calculated in your browser and are not sent to a calculation API. Use the result to inspect a relationship or frame a first estimate; then check component datasheets, tolerances, thermal paths, layout, and the relevant design standard.</p><a class="text-link" href="/lab/buck-converter-ccm-model.html">Read the CCM model note <b>↗</b></a></div></div></div></section>
'''.replace('%s','TOOLS_CARDS')
    body=body.replace('TOOLS_CARDS','\n'.join(cards))
    ld=json.dumps({'@context':'https://schema.org','@type':'CollectionPage','name':'Engineering Calculators & Explorers','url':'https://elitebotstudios.me/tools.html','description':'Client-side engineering calculators and interactive models for PCB trace width, buck conversion, regulator thermal estimates, voltage dividers, LED resistors, and RC time constants.','isPartOf':{'@type':'WebSite','url':'https://elitebotstudios.me'}},indent=2)
    page('Engineering Tools &amp; Calculators | Elite Bot Studios','Six browser-based engineering models, including an interactive buck converter explorer. Inspect calculations and assumptions for power conversion, PCB traces, circuits, and RC timing.','/tools.html',body,jsonld=ld)




if __name__ == '__main__':
    print('building tools…')
    hub()
    for t in TOOLS:
        calc_page(t)
    print('done.')
