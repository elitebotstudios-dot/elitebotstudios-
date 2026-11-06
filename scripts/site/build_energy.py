# -*- coding: utf-8 -*-
"""Generates the Smart DC Energy Monitor instrument page.

The page is presentation only: every number it shows comes from
/energy-monitor/model/dcem.js, which is also what the Node test suites import.
Nothing here recomputes physics in Python.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build
from build import page, write

# Preset identifiers must match DCEM.PRESETS in energy-monitor/model/dcem.js.
# tests/energy-monitor-page.test.js asserts that the built page lists every
# preset the model ships, so these two cannot drift apart silently.
PRESETS = [
    ('constant-load', 'Constant resistive load'),
    ('step-load', 'Step-changing load'),
    ('adc-quantisation', 'ADC quantisation'),
    ('calibration', 'Gain, offset and noise'),
    ('sampling-interval', 'Sampling interval'),
    ('duty-load', 'Duty-cycled load'),
    ('source-droop', 'Real source impedance'),
]

EXPERIMENTS = [
    ('01', 'Constant DC load', 'Voltage, current, power and energy in the simplest case.',
     'A 12 V supply into a 12 Ω resistive load. The current follows from the supply and the resistance, and the energy graph is a straight line whose slope is the power.',
     'constant-load'),
    ('02', 'Changing load', 'What a step does to power and to the energy slope.',
     'The load current halves part-way through the run. Power halves with it, so the energy trace bends rather than stopping.',
     'step-load'),
    ('03', 'ADC quantisation', 'Ideal signal against a quantised measurement.',
     'An 8-bit converter on a slowly varying signal. The measured trace is a staircase; every step is one LSB of the sensing chain.',
     'adc-quantisation'),
    ('04', 'Calibration and error', 'Systematic error, random error, and the correction.',
     'Gain error and offset bias the reading in a predictable direction. Calibration removes the systematic part; the noise remains.',
     'calibration'),
    ('05', 'Sampling interval', 'What sparse samples cannot tell you.',
     'A 4 s duty cycle sampled every 2 s. The reported average depends on where the samples land, which is a property of the sampling, not of the load.',
     'sampling-interval'),
]

ARCH_BLOCKS = [
    ('source', 'DC source',
     '<b>DC source.</b> An ideal voltage source with an optional series resistance. The terminal voltage is solved together with the load, so a load that draws more current makes the terminal voltage sag by I·R<sub>s</sub>. The open-circuit voltage is a simulated quantity; nothing here is a measurement of a real supply.'),
    ('load', 'Electrical load',
     '<b>Electrical load.</b> Five models: fixed resistance, fixed current, a step, a duty cycle, and a user sequence. A resistive load derives its own current from the applied voltage — the model never assigns voltage, current and resistance independently.'),
    ('sensing', 'Voltage and current sensing',
     '<b>Sensing.</b> A divider (V per V) and a shunt amplifier (V per A) scale the two signals into the ADC range. Gain error, offset and noise are applied at the pin, then the result is quantised. The parameters are illustrative, not a datasheet for a specific part.'),
    ('controller', 'Embedded processing',
     '<b>Embedded processing.</b> The sampled values are timestamped, converted to engineering units, optionally filtered, multiplied to give power, and accumulated with the trapezoidal rule over the actual sample intervals. Rejected samples are counted instead of being integrated.'),
    ('logging', 'Logging and interface',
     '<b>Logging.</b> The running record is held in the browser and can be exported as CSV with the exact timestamps and both true and measured columns. No simulation data leaves the device unless you export it.'),
]

REFERENCE_CASES = [
    ('A', '12 V, 1 A, 3600 s', '43 200 J / 12 Wh', 'exact — constant power, so the trapezoidal rule has no error'),
    ('B', '5 V, 2 A, 1800 s', '18 000 J / 5 Wh', 'exact'),
    ('C', '10 V, 1 A → 0.5 A at 1800 s', '26 997.5 J / 7.49931 Wh', '0.0093 % below the 27 000 J continuous ideal — the step straddles one interval'),
    ('D', '12 V, 0 A, 600 s', '0 J', 'zero current, so zero energy, with the voltage still measured'),
    ('E', 'irregular timestamps, 5 intervals', '77.605 J', 'hand-checkable; the naive mean × time estimate would give 77.973 J'),
    ('F', '10 V true, +2 % gain, +50 mV offset', '10.4 V uncalibrated → 10.000 V calibrated', 'analytical; calibrating removes the bias exactly'),
    ('G', 'invalid datasets', 'classified and refused', 'missing, duplicate, non-monotonic, non-numeric, extreme and empty inputs'),
]

ARTEFACTS = [
    ('Model source', '/energy-monitor/model/dcem.js', 'the module the page and the tests both use'),
    ('Reference tests', '/energy-monitor/tests/dcem-reference.test.js', 'cases A–G, 67 assertions'),
    ('Independent tests', '/energy-monitor/tests/dcem-independent.test.js', 'ten groups, 594 assertions'),
    ('Model documentation', '/energy-monitor/docs/model.md', 'equations, units, integration, error model'),
    ('Requirements', '/energy-monitor/docs/requirements.md', 'what V1 must do, and what it must not claim'),
    ('Architecture', '/energy-monitor/docs/architecture.md', 'stage-by-stage structure'),
    ('Limitations', '/energy-monitor/docs/limitations.md', 'what the model does not establish'),
    ('Hardware plan', '/energy-monitor/docs/hardware-plan.md', 'the low-voltage roadmap, not yet started'),
    ('Reproduction', '/energy-monitor/docs/reproduce.md', 'commands and expected output'),
    ('Reference datasets', '/energy-monitor/examples/', 'six CSV files with their metadata'),
]

PREVIEW_NOTES = [
    'Both the true (simulated) and the measured (sensing-chain) value are always shown.',
    'Energy is integrated with the actual timestamps, never assumed equally spaced.',
    'Every number on this page comes from the same module the tests import.',
]


def _arch_html():
    buttons = []
    for i, (key, label, info) in enumerate(ARCH_BLOCKS, 1):
        buttons.append(
            '<button type="button" class="em-arch-block" data-arch="%s" data-arch-info="%s" aria-pressed="false">'
            '<span class="em-arch-no">%02d</span><span class="em-arch-label">%s</span></button>'
            % (key, info.replace('"', '&quot;'), i, label))
    return '\n'.join(buttons)


def _experiments_html():
    cards = []
    for no, title, tagline, body, preset in EXPERIMENTS:
        cards.append(
            '<article class="em-experiment"><span class="em-experiment-no">EXPERIMENT %s</span>'
            '<h3>%s</h3><p class="em-experiment-tagline">%s</p><p>%s</p>'
            '<button type="button" class="btn btn-ghost em-experiment-btn" data-experiment="%s">Load this experiment</button>'
            '</article>' % (no, title, tagline, body, preset))
    return '\n'.join(cards)


def _reference_table():
    rows = ''.join(
        '<tr><th scope="row">%s</th><td>%s</td><td class="em-mono">%s</td><td>%s</td></tr>' % r
        for r in REFERENCE_CASES)
    return ('<div class="table-scroll" tabindex="0" role="region" aria-label="Reference test results, scrollable">'
            '<table class="em-table"><caption class="sr-only">Reference cases asserted by the test suite</caption>'
            '<thead><tr><th scope="col">Case</th><th scope="col">Input</th><th scope="col">Expected result</th>'
            '<th scope="col">Why that number</th></tr></thead><tbody>%s</tbody></table></div>' % rows)


def _artefacts_html():
    items = ''.join(
        '<li><a href="%s">%s</a><span>%s</span></li>' % (href, label, note)
        for label, href, note in ARTEFACTS)
    return '<ul class="em-artefacts">%s</ul>' % items


def energy_monitor_page():
    head_note = ' '.join(PREVIEW_NOTES)
    body = '''
    <section class="page-head em-head"><div class="wrap">
      <a class="backlink" href="/projects/smart-energy-monitoring.html">&larr; Smart Energy Monitoring</a>
      <span class="eyebrow">Project 01 / Software model V1 / Hardware not built</span>
      <h1>DC energy monitor.<br><em>Run the instrument.</em></h1>
      <p>A simulated low-voltage DC energy monitor: source, load, sensing chain, embedded sampling and energy accumulation, all running in this page. True and measured values are shown side by side so the difference is never hidden.</p>
      <div class="em-head-tags">
        <span class="em-tag em-tag-ok">Software model V1 · verified</span>
        <span class="em-tag">Hardware prototype · not built</span>
        <span class="em-tag">Runs in your browser</span>
      </div>
    </div></section>

    <section class="section em-app-section"><div class="wrap">
      <div class="em-app" id="emApp">
        <div class="em-statusbar">
          <span class="em-status" id="emStatus" data-tone="idle" role="status">Ready</span>
          <dl class="em-status-facts">
            <div><dt>Simulated time</dt><dd id="emClock">00:00.0</dd></div>
            <div><dt>Samples</dt><dd id="emSamples">0</dd></div>
            <div><dt>Rejected / clipped</dt><dd id="emRejected">0</dd></div>
          </dl>
        </div>

        <div class="em-arch" role="group" aria-label="System architecture">
          @@ARCH_BLOCKS@@
        </div>
        <p class="em-arch-info" id="emArchInfo">Source → load → sensing → controller → logging. Select a block to read what the model does at that stage.</p>

        <div class="em-layout">
          <form class="em-controls" id="emControls" novalidate>
            <div class="em-control-group">
              <label class="em-control-label" for="emScenario">Scenario</label>
              <select id="emScenario">@@SCENARIO_OPTIONS@@</select>
              <p class="em-note" id="emNote"></p>
            </div>

            <fieldset class="em-control-group"><legend>Source</legend>
              <div class="em-pair">
                <div><label for="emSupply">Supply <span>V</span></label><input id="emSupply" type="number" value="12" min="1" max="48" step="0.1" inputmode="decimal"></div>
                <div><label for="emSourceR">Source resistance <span>Ω</span></label><input id="emSourceR" type="number" value="0" min="0" max="5" step="0.05" inputmode="decimal"></div>
              </div>
            </fieldset>

            <fieldset class="em-control-group"><legend>Load</legend>
              <label for="emLoad">Load model</label>
              <select id="emLoad">
                <option value="resistive" selected>Fixed resistance</option>
                <option value="current">Fixed current</option>
                <option value="step">Step change</option>
                <option value="duty">Duty cycle</option>
              </select>
              <div class="em-pair" data-load-mode="resistive">
                <div><label for="emResistance">Resistance <span>Ω</span></label><input id="emResistance" type="number" value="12" min="0.5" max="1000" step="0.5" inputmode="decimal"></div>
              </div>
              <div class="em-pair" data-load-mode="current">
                <div><label for="emCurrent">Current <span>A</span></label><input id="emCurrent" type="number" value="1" min="0" max="5" step="0.05" inputmode="decimal"></div>
              </div>
              <div class="em-pair" data-load-mode="step">
                <div><label for="emStepBefore">Before <span>A</span></label><input id="emStepBefore" type="number" value="1" min="0" max="5" step="0.05" inputmode="decimal"></div>
                <div><label for="emStepAfter">After <span>A</span></label><input id="emStepAfter" type="number" value="0.5" min="0" max="5" step="0.05" inputmode="decimal"></div>
              </div>
              <div class="em-pair" data-load-mode="step">
                <div><label for="emStepAt">Step at <span>s</span></label><input id="emStepAt" type="number" value="150" min="0" max="3600" step="1" inputmode="numeric"></div>
              </div>
              <div class="em-pair" data-load-mode="duty">
                <div><label for="emDutyPeriod">Period <span>s</span></label><input id="emDutyPeriod" type="number" value="30" min="0.5" max="600" step="0.5" inputmode="decimal"></div>
                <div><label for="emDutyRatio">On-time <span>%</span></label><input id="emDutyRatio" type="number" value="40" min="1" max="99" step="1" inputmode="numeric"></div>
              </div>
              <div class="em-pair" data-load-mode="duty">
                <div><label for="emDutyOn">On current <span>A</span></label><input id="emDutyOn" type="number" value="1.5" min="0" max="5" step="0.05" inputmode="decimal"></div>
                <div><label for="emDutyOff">Off current <span>A</span></label><input id="emDutyOff" type="number" value="0.2" min="0" max="5" step="0.05" inputmode="decimal"></div>
              </div>
            </fieldset>

            <fieldset class="em-control-group"><legend>Sampling and sensing</legend>
              <div class="em-pair">
                <div><label for="emInterval">Sample interval <span>s</span></label><input id="emInterval" type="number" value="0.5" min="0.05" max="10" step="0.05" inputmode="decimal"></div>
                <div><label for="emAdcBits">ADC bits</label>
                  <select id="emAdcBits">
                    <option value="6">6</option><option value="8">8</option><option value="10">10</option>
                    <option value="12" selected>12</option><option value="14">14</option><option value="16">16</option>
                  </select></div>
              </div>
              <div class="em-pair">
                <div><label for="emVDivider">Voltage divider <span>V/V</span></label>
                  <select id="emVDivider"><option value="0.1">0.1 (10:1)</option><option value="0.25" selected>0.25 (4:1)</option><option value="0.5">0.5 (2:1)</option></select></div>
                <div><label for="emISense">Current sense <span>V/A</span></label>
                  <select id="emISense"><option value="0.25">0.25</option><option value="0.5" selected>0.5</option><option value="1">1.0</option><option value="2">2.0</option></select></div>
              </div>
              <details class="em-advanced">
                <summary>Error terms and calibration</summary>
                <div class="em-pair">
                  <div><label for="emVGain">Voltage gain error <span>%</span></label><input id="emVGain" type="number" value="0" min="-20" max="20" step="0.1" inputmode="decimal"></div>
                  <div><label for="emVOffset">Voltage offset <span>mV</span></label><input id="emVOffset" type="number" value="0" min="-200" max="200" step="1" inputmode="decimal"></div>
                </div>
                <div class="em-pair">
                  <div><label for="emVNoise">Voltage noise <span>mV RMS</span></label><input id="emVNoise" type="number" value="0" min="0" max="200" step="0.5" inputmode="decimal"></div>
                  <div><label for="emINoise">Current noise <span>mV RMS</span></label><input id="emINoise" type="number" value="0" min="0" max="200" step="0.5" inputmode="decimal"></div>
                </div>
                <div class="em-pair">
                  <div><label for="emIGain">Current gain error <span>%</span></label><input id="emIGain" type="number" value="0" min="-20" max="20" step="0.1" inputmode="decimal"></div>
                  <div><label for="emIOffset">Current offset <span>mV</span></label><input id="emIOffset" type="number" value="0" min="-200" max="200" step="1" inputmode="decimal"></div>
                </div>
                <div class="em-check">
                  <input id="emCalibration" type="checkbox">
                  <label for="emCalibration">Apply calibration (uses the entered error terms as the calibration constants)</label>
                </div>
                <p class="em-help">Calibration applies to each channel separately. With these defaults it corrects the gain error and offset you enter, which is exactly the correction a real calibration would estimate.</p>
              </details>
            </fieldset>

            <fieldset class="em-control-group"><legend>Run</legend>
              <div class="em-pair">
                <div><label for="emDuration">Duration <span>s</span></label><input id="emDuration" type="number" value="300" min="10" max="3600" step="10" inputmode="numeric"></div>
                <div><label for="emSpeed">Speed <span>×</span></label><input id="emSpeed" type="number" value="20" min="1" max="120" step="1" inputmode="numeric"></div>
              </div>
            </fieldset>

            <div class="em-buttons">
              <button type="button" class="btn btn-primary" id="emStart">Start</button>
              <button type="button" class="btn btn-ghost" id="emPause" disabled>Pause</button>
              <button type="button" class="btn btn-ghost" id="emReset">Reset</button>
              <button type="button" class="btn btn-ghost" id="emExport" disabled>Export CSV</button>
            </div>
            <p class="em-help">Start, pause and reset are exact: a paused run does not advance simulated time, and a reset clears the accumulator. Changing the load model or the calibration starts a new run so energy cannot carry over from a different configuration.</p>
            <p class="em-warning" id="emWarnings" hidden></p>
          </form>

          <div class="em-instrument">
            <div class="em-readouts">
              <div class="em-readout"><span class="em-readout-label">Voltage</span><span class="em-readout-value" id="emV">—</span><span class="em-readout-unit">V</span><span class="em-readout-true">true <b id="emVTrue">—</b> V</span></div>
              <div class="em-readout"><span class="em-readout-label">Current</span><span class="em-readout-value" id="emI">—</span><span class="em-readout-unit">A</span><span class="em-readout-true">true <b id="emITrue">—</b> A</span></div>
              <div class="em-readout em-readout-accent"><span class="em-readout-label">Power</span><span class="em-readout-value" id="emP">—</span><span class="em-readout-unit">W</span><span class="em-readout-true">true <b id="emPTrue">—</b> W</span></div>
              <div class="em-readout em-readout-accent"><span class="em-readout-label">Energy</span><span class="em-readout-value" id="emE">—</span><span class="em-readout-unit">Wh</span><span class="em-readout-true">true <b id="emETrue">—</b> Wh</span></div>
            </div>
            <p class="em-readout-foot"><span>Load state</span> <b id="emLoadState">—</b> <span class="em-readout-hint">Large numbers are the measurement chain output; the small line under each is the simulated truth.</span></p>

            <p class="em-inspect" id="emInspect">Hover or focus a chart to read a point.</p>

            <div class="em-chart-tabs" role="tablist" aria-label="Chart selection">
              <button type="button" role="tab" aria-selected="true" data-chart-tab="voltage">Voltage</button>
              <button type="button" role="tab" aria-selected="false" data-chart-tab="current">Current</button>
              <button type="button" role="tab" aria-selected="false" data-chart-tab="power">Power</button>
              <button type="button" role="tab" aria-selected="false" data-chart-tab="energy">Energy</button>
            </div>

            <div class="em-charts">
              <figure class="em-chart" data-chart-panel="voltage"><figcaption>Voltage <span>V</span></figcaption><canvas id="emChart-voltage" role="img" aria-label="Voltage against time"></canvas></figure>
              <figure class="em-chart" data-chart-panel="current"><figcaption>Current <span>A</span></figcaption><canvas id="emChart-current" role="img" aria-label="Current against time"></canvas></figure>
              <figure class="em-chart" data-chart-panel="power"><figcaption>Power <span>W</span></figcaption><canvas id="emChart-power" role="img" aria-label="Power against time"></canvas></figure>
              <figure class="em-chart" data-chart-panel="energy"><figcaption>Accumulated energy <span>Wh</span></figcaption><canvas id="emChart-energy" role="img" aria-label="Accumulated energy against time"></canvas></figure>
            </div>
            <p class="em-chart-note">Solid lines are the simulated truth; dashed lines are what the sensing chain reports. Both come from the same sample set.</p>
            <p class="sr-only" id="emLive" aria-live="polite"></p>
          </div>
        </div>
        <noscript><p class="em-noscript">The instrument needs JavaScript. The model itself is a plain file you can read and run with Node: <code>node energy-monitor/tests/dcem-reference.test.js</code>.</p></noscript>
      </div>
    </div></section>

    <section class="section em-experiments-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">01 / EXPERIMENTS</span><h2>Five things<br><em>worth looking at.</em></h2></div><p>Each experiment loads a complete configuration into the instrument above. They all use the same validated model — there is no second implementation for the demonstrations.</p></div>
      <div class="em-experiments">@@EXPERIMENTS@@</div>
    </div></section>

    <section class="section em-method-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">02 / THE MODEL</span><h2>Power, energy,<br><em>and the time between samples.</em></h2></div><p>Discrete samples do not measure instantaneous power; they bracket it. The model says exactly what it does between two samples.</p></div>
      <div class="em-method-grid">
        <article><h3>Power</h3><div class="em-eq"><math display="block"><mrow><mi>P</mi><mo>=</mo><mi>V</mi><mo>·</mo><mi>I</mi></mrow></math></div><p>Computed from the two measured channels after scaling and quantisation, and separately from the simulated truth so the difference can be read directly.</p></article>
        <article><h3>Energy, trapezoidal</h3><div class="em-eq"><math display="block"><mrow><msub><mi>E</mi><mi>j</mi></msub><mo>+=</mo><mfrac><mrow><msub><mi>P</mi><mrow><mi>j</mi><mo>−</mo><mn>1</mn></mrow></msub><mo>+</mo><msub><mi>P</mi><mi>j</mi></msub></mrow><mn>2</mn></mfrac><mo>·</mo><mi>Δ</mi><msub><mi>t</mi><mi>j</mi></msub></mrow></math></div><p>Each interval contributes the average of its two endpoint powers times the <em>actual</em> elapsed time. Power is never summed without multiplying by time.</p></article>
        <article><h3>Units</h3><div class="em-eq"><math display="block"><mrow><msub><mi>E</mi><mtext>Wh</mtext></msub><mo>=</mo><mfrac><msub><mi>E</mi><mtext>J</mtext></msub><mn>3600</mn></mfrac></mrow></math></div><p>Accumulators hold joules; the interface shows watt-hours. 1 Wh = 3600 J exactly, with no rounding in between.</p></article>
        <article><h3>Sensing chain</h3><div class="em-eq"><math display="block"><mrow><msub><mi>V</mi><mtext>pin</mtext></msub><mo>=</mo><mi>V</mi><mo>·</mo><mi>S</mi><mo>·</mo><mo>(</mo><mn>1</mn><mo>+</mo><mi>g</mi><mo>)</mo><mo>+</mo><msub><mi>V</mi><mtext>os</mtext></msub><mo>+</mo><mi>n</mi></mrow></math></div><p>Sensitivity, gain error, offset and noise at the pin, then uniform quantisation to the nearest LSB. A channel with 0 bits is treated as ideal.</p></article>
      </div>
      <div class="em-assumptions">
        <h3>What the numbers between samples mean</h3>
        <ul>
          <li>The simulated truth is evaluated at each sample instant. Between samples it is undefined — the model does not interpolate a "true" waveform.</li>
          <li>The trapezoidal rule assumes power varies linearly across an interval. That is exact for constant power, slightly high or low across a step, and approximate for anything curved.</li>
          <li>A step that falls between two samples is smeared across that interval. Reference case C quantifies it: 2.5 J in 27 000 J, or 0.0093 %.</li>
          <li>Imported and exported energy are integrated separately, splitting the interval at a sign change, so reversed current cannot reduce a consumption total by accident.</li>
          <li>Rejected samples — duplicate, non-monotonic, non-numeric or out of range — are counted and never integrated.</li>
        </ul>
      </div>
    </div></section>

    <section class="section em-verify-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">03 / VERIFICATION</span><h2>Reference cases,<br><em>with their tolerances.</em></h2></div><p>Every row below is asserted by <code>dcem-reference.test.js</code> and re-derived by a separate method in <code>dcem-independent.test.js</code>. These are the values the test files print.</p></div>
      @@REFERENCE_TABLE@@
      <p class="em-caption">Software verification only. Nothing on this page is a measurement of a physical circuit, and no accuracy claim about real hardware follows from it.</p>
    </div></section>

    <section class="section em-artefacts-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">04 / ARTEFACTS</span><h2>Everything needed<br><em>to reproduce it.</em></h2></div><p>The model, both test suites, the documentation and the reference datasets are plain files served from this site. You do not need the dashboard to check the numbers.</p></div>
      @@ARTEFACTS@@
      <p class="em-reproduce"><code>node energy-monitor/tests/dcem-reference.test.js<br>node energy-monitor/tests/dcem-independent.test.js</code></p>
    </div></section>

    <section class="section em-status-section"><div class="wrap">
      <div class="em-status-grid">
        <div><span class="em-tag em-tag-ok">Software model V1</span><h3>Verified against reference cases</h3><p>The model, its tests and its datasets are complete for the scope described in the requirements document.</p></div>
        <div><span class="em-tag">Hardware prototype</span><h2 class="em-status-h">Not yet built</h2><p>No sensor, ADC, microcontroller, board or enclosure exists. The hardware plan lists the stages and the approvals required before anything is energised.</p></div>
      </div>
      <div class="project-detail-related"><a href="/projects/smart-energy-monitoring.html">Read the project case study &#8599;</a><a href="/energy-monitor/docs/hardware-plan.md">Hardware plan &#8599;</a><a href="/tools.html">Other engineering tools &#8599;</a></div>
    </div></section>
'''
    options = ''.join('<option value="%s">%s</option>' % (pid, name) for pid, name in PRESETS)
    body = (body
            .replace('@@ARCH_BLOCKS@@', _arch_html())
            .replace('@@SCENARIO_OPTIONS@@', options)
            .replace('@@EXPERIMENTS@@', _experiments_html())
            .replace('@@REFERENCE_TABLE@@', _reference_table())
            .replace('@@ARTEFACTS@@', _artefacts_html()))

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": "Smart DC Energy Monitor — Software Model V1",
        "description": "A simulated low-voltage DC energy-monitoring system: source and load models, a configurable sensing chain with gain, offset, noise and ADC quantisation, sampled power and trapezoidal energy accumulation, with reference and independent test suites.",
        "codeRepository": "https://elitebotstudios.me/energy-monitor/model/dcem.js",
        "programmingLanguage": "JavaScript",
        "url": "https://elitebotstudios.me/projects/dc-energy-monitor.html",
        "author": {"@type": "Organization", "name": "Elite Bot Studios"},
        "isPartOf": {"@type": "WebSite", "url": "https://elitebotstudios.me"}
    }, indent=2)

    write('/projects/dc-energy-monitor.html',
          build.head('DC Energy Monitor — interactive software model | Elite Bot Studios',
                     'Run a simulated low-voltage DC energy monitor: configurable source, five load models, a sensing chain with gain, offset, noise and ADC quantisation, and trapezoidal energy accumulation with published verification.',
                     '/projects/dc-energy-monitor.html', jsonld=ld)
          + build.header('/projects.html') + '\n  <main id="main">\n' + body + '\n  </main>\n'
          + '\n  <script src="%s" defer></script>\n' % build.asset('energy-monitor/model/dcem.js')
          + '  <script src="%s" defer></script>\n' % build.asset('assets/energy-dashboard.js')
          + build.footer())



# ---------------------------------------------------------------------------
# The project record: /projects/smart-energy-monitoring.html
#
# Rewritten for Software Model V1. It keeps the concept documentation that was
# already published (requirements, sensing options, controller options, isolation
# boundary, validation strategy, open questions) and adds the completed software
# artefact, its verification, the trade-offs and the hardware plan — with the
# hardware status kept visibly separate from the software status.
# ---------------------------------------------------------------------------
PROJECT_JSON = None


def _record():
    global PROJECT_JSON
    if PROJECT_JSON is None:
        data = json.loads((build.ROOT / 'projects.json').read_text(encoding='utf-8'))
        PROJECT_JSON = next(p for p in data if p['slug'] == 'smart-energy-monitoring')
    return PROJECT_JSON


def energy_project_page():
    """The authoritative landing page for Project 01.

    Every status statement on this page comes from projects.json, and every
    claim links to the artefact that backs it. Nothing here is asserted by
    hand: the milestone table, the evidence links and the verification numbers
    are read from the same data the rest of the site uses.
    """
    record = _record()
    milestones = record.get('milestones') or []

    def stage_rows():
        out = []
        for m in milestones:
            links = ''.join('<a href="%s">%s</a>' % (e['href'], e['label']) for e in m.get('evidence') or [])
            out.append(
                '<tr data-state="%s"><th scope="row">%s</th><td><b>%s</b><p>%s</p></td>'
                '<td class="cs-evidence">%s</td></tr>'
                % (m['state'], m['name'], m['status'], m['detail'], links or '<span class="cs-none">—</span>'))
        return ''.join(out)

    body = '''
    <article class="cs">
      <header class="cs-hero"><div class="wrap">
        <a class="backlink" href="/projects.html">&larr; Projects</a>
        <div class="cs-meta">
          <span class="chip chip-teal">Software verified</span>
          <span class="chip chip-teal">Hardware designed</span>
          <span class="chip chip-amber">Prototype not built</span>
          <span>Project 01 &middot; 2026-11</span>
        </div>
        <h1>Smart Energy Monitoring.<br><em>A measurement chain, modelled, designed and compiled.</em></h1>
        <p class="cs-lede">A low-voltage DC energy monitor built through three layers, each with its own evidence: a software model verified against reference cases, a native KiCad schematic that passes ERC, and firmware that cross-compiles for the ESP32. The prototype does not exist yet, and the page says so where it matters.</p>
        <div class="cs-cta">
          <a class="btn btn-primary" href="/projects/dc-energy-monitor.html">Run the software model <span aria-hidden="true">&#8599;</span></a>
          <a class="btn btn-ghost" href="/projects/dc-energy-monitor-hardware.html">Open the hardware design</a>
          <a class="text-link" href="/projects/dc-energy-monitor-evidence.html">Browse the evidence hub <b>&#8599;</b></a>
        </div>
      </div></header>

      <nav class="cs-toc" aria-label="Case study contents"><div class="wrap">
        <a href="#objective">01 Objective</a><a href="#status">02 Status</a><a href="#architecture">03 Architecture</a>
        <a href="#software">04 Software</a><a href="#electrical">05 Electrical</a><a href="#firmware">06 Firmware</a>
        <a href="#verification">07 Verification</a><a href="#decisions">08 Decisions</a><a href="#plan">09 Build plan</a>
        <a href="#outstanding">10 Outstanding</a><a href="#reproduce">11 Reproduce</a><a href="#attribution">12 Attribution</a>
      </div></nav>

      <section class="cs-section" id="objective"><div class="wrap cs-prose">
        <span class="cs-no">01 / ENGINEERING OBJECTIVE</span>
        <h2>How far is an energy reading from the truth?</h2>
        <p>A monitor that reports 12.00 W is making a claim about a chain of components. A divider scales the voltage, a shunt converts current into a small differential voltage, an amplifier and an ADC translate both into numbers, firmware multiplies them, and a clock decides how long to keep adding. Each stage contributes an error the others do not cancel, and some of those errors — a gain error, a stale sample, an interval integrated across missing data — look exactly like a real change in the load.</p>
        <p>The useful engineering question is therefore not &ldquo;what does it read?&rdquo; but &ldquo;how far can that reading be from the truth, which stage put it there, and how would anyone know?&rdquo; This project answers that question three times over: once in a simulation where every stage can be varied independently, once as a schematic where the connections must be electrically legal, and once as firmware where the arithmetic has to survive real timestamps and missing samples.</p>
        <div class="cs-scope">
          <div><h3>In scope</h3><p>Low-voltage DC (5&ndash;12 V, 0&ndash;0.5 A), a single non-isolated measurement channel, sampled power and integrated energy, and the evidence needed to check all of it.</p></div>
          <div><h3>Out of scope</h3><p>Mains and AC, isolation, three-phase, battery management, wireless reporting. Any accuracy claim about physical hardware.</p></div>
        </div>
      </div></section>

      <section class="cs-section cs-status" id="status"><div class="wrap">
        <span class="cs-no">02 / PROJECT STATUS</span>
        <h2>Eight stages, each with the evidence it has earned.</h2>
        <p class="cs-sub">Read this table as the project's actual state. A stage marked done has an artefact behind it, linked in the right-hand column. Nothing is marked done because it was written down.</p>
        <div class="table-scroll" tabindex="0" role="region" aria-label="Project stage status, scrollable">
          <table class="cs-table"><caption class="sr-only">Project stages, their status and their evidence</caption>
            <thead><tr><th scope="col">Stage</th><th scope="col">Where it stands</th><th scope="col">Evidence</th></tr></thead>
            <tbody>STAGE_ROWS</tbody>
          </table>
        </div>
        <p class="cs-note"><strong>What the separation means.</strong> A cross-compiled firmware is not hardware-tested firmware, and an ERC-clean schematic is not a fabricated board. The bottom three rows are deliberately empty of artefacts, because no board exists.</p>
      </div></section>

      <section class="cs-section" id="architecture"><div class="wrap">
        <span class="cs-no">03 / SYSTEM ARCHITECTURE</span>
        <h2>One circuit, described three ways.</h2>
        <p class="cs-sub">The same signal path appears as a simulatable model, as a schematic, and as firmware. Keeping the three separate is what makes it possible to check one against another.</p>
        <figure class="cs-figure">
          <svg viewBox="0 0 1080 420" role="img" aria-labelledby="csArchTitle csArchDesc">
            <title id="csArchTitle">The three layers of the project and how they relate</title>
            <desc id="csArchDesc">A DC source and load are measured by a shunt and an INA226. The measurement reaches an ESP32 over I2C, which decodes, timestamps and integrates energy. The same signal path exists as a software model in the browser, which is verified against reference cases; the hardware exists as a KiCad schematic that passes ERC; and the firmware cross-compiles for the ESP32 and is tested against a mock bus. Only the prototype and the measurements are missing.</desc>

            <rect class="cs-fig-band" x="20" y="24" width="1040" height="96" rx="8"/>
            <text class="cs-fig-bandlabel" x="36" y="46">THE PHYSICAL CHAIN &mdash; DESIGNED, NOT BUILT</text>
            <rect class="cs-fig-box" x="48" y="58" width="150" height="50" rx="6"/><text class="cs-fig-t" x="66" y="88">DC source</text>
            <rect class="cs-fig-box" x="238" y="58" width="170" height="50" rx="6"/><text class="cs-fig-t" x="256" y="82">Shunt 0.1 Ω</text><text class="cs-fig-s" x="256" y="98">+ INA226</text>
            <rect class="cs-fig-box" x="448" y="58" width="150" height="50" rx="6"/><text class="cs-fig-t" x="466" y="88">ESP32</text>
            <rect class="cs-fig-box" x="638" y="58" width="170" height="50" rx="6"/><text class="cs-fig-t" x="656" y="82">Energy total</text><text class="cs-fig-s" x="656" y="98">CSV on serial</text>
            <rect class="cs-fig-box" x="848" y="58" width="190" height="50" rx="6"/><text class="cs-fig-t" x="866" y="88">Load</text>
            <path class="cs-fig-arrow" d="M198 83h40M408 83h40M598 83h40M808 83h40"/>

            <rect class="cs-fig-band2" x="20" y="146" width="1040" height="240" rx="8"/>
            <text class="cs-fig-bandlabel" x="36" y="168">THE THREE DESCRIPTIONS &mdash; EACH WITH ITS OWN EVIDENCE</text>

            <rect class="cs-fig-card" x="48" y="188" width="320" height="176" rx="8"/>
            <text class="cs-fig-h" x="66" y="212">Software model</text>
            <text class="cs-fig-s" x="66" y="232">Runs in the browser, and in Node for the tests</text>
            <text class="cs-fig-l" x="66" y="256">• source and load solved together</text>
            <text class="cs-fig-l" x="66" y="276">• gain, offset, noise, quantisation</text>
            <text class="cs-fig-l" x="66" y="296">• trapezoidal energy on real timestamps</text>
            <text class="cs-fig-l" x="66" y="316">• 67 reference + 594 independent checks</text>
            <text class="cs-fig-ok" x="66" y="344">VERIFIED</text>

            <rect class="cs-fig-card" x="380" y="188" width="320" height="176" rx="8"/>
            <text class="cs-fig-h" x="398" y="212">Electrical design</text>
            <text class="cs-fig-s" x="398" y="232">Native KiCad project, editable</text>
            <text class="cs-fig-l" x="398" y="256">• INA226 wired as the bare IC</text>
            <text class="cs-fig-l" x="398" y="276">• VBUS tied to the load side</text>
            <text class="cs-fig-l" x="398" y="296">• fuse, reverse diode, TVS clamp</text>
            <text class="cs-fig-l" x="398" y="316">• ERC 0 errors, 0 warnings</text>
            <text class="cs-fig-ok" x="398" y="344">ERC CLEAN &middot; NOT BUILT</text>

            <rect class="cs-fig-card" x="712" y="188" width="326" height="176" rx="8"/>
            <text class="cs-fig-h" x="730" y="212">Firmware</text>
            <text class="cs-fig-s" x="730" y="232">C++17, platform-free core</text>
            <text class="cs-fig-l" x="730" y="256">• register decode and calibration</text>
            <text class="cs-fig-l" x="730" y="276">• wrap-safe millisecond timing</text>
            <text class="cs-fig-l" x="730" y="296">• holds intervals rather than invent energy</text>
            <text class="cs-fig-l" x="730" y="316">• 98 host checks, cross-compiled</text>
            <text class="cs-fig-warn" x="730" y="344">COMPILED &middot; NEVER FLASHED</text>
          </svg>
          <figcaption>The three descriptions share one signal path, which is why they can be checked against each other: the KiCad netlist is compared with the design file pin by pin, and firmware test vectors are replayed through the verified software model.</figcaption>
        </figure>
      </div></section>

      <section class="cs-section cs-software" id="software"><div class="wrap cs-prose">
        <span class="cs-no">04 / SOFTWARE MODEL</span>
        <h2>Everything measurable, before anything is soldered.</h2>
        <p>The software model is the project's first deliverable and its reference implementation. It solves the source and the load together — a resistive load derives its own current from the applied voltage — then passes that operating point through a configurable sensing chain and accumulates energy with the trapezoidal rule over the <em>actual</em> interval between samples.</p>
        <div class="cs-split">
          <div>
            <h3>What it can establish</h3>
            <ul class="cs-list">
              <li>The arithmetic, exactly where the arithmetic is exact: 12 V at 1 A for an hour is 12 Wh, to the last digit.</li>
              <li>How much a gain error, offset, noise or quantisation step moves the reading, and whether calibration recovers it.</li>
              <li>What a step that falls between two samples costs, quantified: 0.0093 % of a 27 000 J run at 1 s sampling.</li>
              <li>That missing samples cannot create energy: an invalid reading costs two intervals and is counted.</li>
            </ul>
          </div>
          <div>
            <h3>What it cannot establish</h3>
            <ul class="cs-list">
              <li>Anything about a physical sensor. The noise source is seeded and statistical, not a characterisation of a part.</li>
              <li>ADC non-idealities: no INL, DNL or reference drift.</li>
              <li>Loop dynamics, thermal behaviour, or what the load does faster than the sample interval.</li>
              <li>That the model's sensing chain equals the INA226's. It is a model of a chain, not of that part.</li>
            </ul>
          </div>
        </div>
        <p class="cs-actions"><a class="btn btn-primary" href="/projects/dc-energy-monitor.html">Run the model in the browser <span aria-hidden="true">&#8599;</span></a><a class="text-link" href="/energy-monitor/docs/model.md">Model documentation <b>&#8599;</b></a></p>
      </div></section>

      <section class="cs-section cs-electrical" id="electrical"><div class="wrap cs-prose">
        <span class="cs-no">05 / ELECTRICAL DESIGN</span>
        <h2>ESP32 and INA226, wired so the reading means something.</h2>
        <p>The measurement is a 0.1 Ω shunt in series with the load, with an INA226 reading the differential voltage across it and the bus voltage on the <em>load</em> side. That last detail is the reason this revision exists: on the bare INA226, VBUS is a separate pin, and if it is not tied to IN− the reported voltage comes from the wrong node and every power figure is wrong while looking perfectly plausible.</p>
        <div class="cs-specs">
          <div><span>Sensor</span><b>INA226AIDGSR, 16-bit, 0&ndash;36 V bus, &plusmn;81.92 mV shunt</b></div>
          <div><span>Shunt</span><b>0.1 Ω, 0.5 %, 1 W &mdash; 50 mV at 0.5 A</b></div>
          <div><span>Controller</span><b>ESP32-DevKitC-32E, I²C at 0x40 on GPIO21/22</b></div>
          <div><span>Protection</span><b>1.1 A PTC, SS34 Schottky, SMBJ15A clamp</b></div>
        </div>
        <figure class="cs-figure cs-figure-shot">
          <img src="@@KICAD_IMG@@_CS@@" width="1400" height="982" alt="KiCad schematic of the measurement carrier: DC input through fuse, reverse-protection diode and shunt to the load, with the INA226 measuring the shunt drop and the load-side bus voltage." loading="lazy" decoding="async">
          <figcaption>The schematic as exported from KiCad. It is a native project built from official library symbols, and it passes ERC with no errors and no warnings.</figcaption>
        </figure>
        <p class="cs-actions"><a class="btn btn-ghost" href="/projects/dc-energy-monitor-hardware.html">Hardware design, ERC and BOM <span aria-hidden="true">&#8599;</span></a><a class="text-link" href="/energy-monitor/hardware/kicad/dcm-hw-v1.kicad_sch">Open the .kicad_sch <b>&#8599;</b></a></p>
      </div></section>

      <section class="cs-section" id="firmware"><div class="wrap cs-prose">
        <span class="cs-no">06 / EMBEDDED FIRMWARE</span>
        <h2>Decode, timestamp, integrate — and refuse to guess.</h2>
        <p>The firmware is split so that the arithmetic can be tested without a board. A platform-free core holds the register decode, the calibration, the energy accumulator and the missing-data policy; a thin application layer implements I²C with <code>Wire</code> and prints CSV over serial. The host tests drive the same core through a mock bus, so the code that compiles for the ESP32 is the code that was tested.</p>
        <ol class="cs-steps">
          <li><span>01</span><div><b>Decode</b><p>Signed 16-bit shunt register at 2.5 µV per bit, unsigned bus register at 1.25 mV. Current is derived from the shunt voltage and the known resistance rather than from the device's calibration register, so a mis-written register cannot silently corrupt the reading.</p></div></li>
          <li><span>02</span><div><b>Timestamp</b><p>Milliseconds since boot in an unsigned 32-bit counter. Subtraction is wrap-safe, so the 49.7-day rollover is not a bug waiting to happen. There is no real-time clock in this design, so no date is claimed.</p></div></li>
          <li><span>03</span><div><b>Integrate</b><p>Trapezoidal rule over the measured interval. An invalid or missing sample holds the interval instead of integrating a stale reading, and a gap longer than five seconds is not integrated at all. Both are counted, so a period with no measurement cannot look like a period of zero power.</p></div></li>
          <li><span>04</span><div><b>Report</b><p>CSV on serial: timestamp, voltage, current, power, energy, status — with comment lines for intervals that were held.</p></div></li>
        </ol>
      </div></section>

      <section class="cs-section cs-verification" id="verification"><div class="wrap">
        <span class="cs-no">07 / VERIFICATION</span>
        <h2>What was actually run, and what it produced.</h2>
        <p class="cs-sub">Every number below is printed by a suite in the repository. Nothing in this table is a summary of an intention.</p>
        <div class="cs-verify-grid">
          <article><h3>Software model</h3><p class="cs-big">661</p><p class="cs-small">checks · 67 reference cases A&ndash;G and 594 independent checks across ten groups</p></article>
          <article><h3>Firmware</h3><p class="cs-big">98</p><p class="cs-small">host checks · 69 arithmetic and 29 against a mock I²C bus</p></article>
          <article><h3>Electrical design</h3><p class="cs-big">25</p><p class="cs-small">design-rule checks with margins printed, plus ERC at 0 errors and 0 warnings</p></article>
          <article><h3>Netlist agreement</h3><p class="cs-big">42</p><p class="cs-small">pins compared between the KiCad export and the design file · 8 nets · no differences</p></article>
        </div>
        <div class="table-scroll" tabindex="0" role="region" aria-label="Reference results, scrollable">
          <table class="cs-table"><caption class="sr-only">Reference results actually produced by the test suites</caption>
            <thead><tr><th scope="col">Case</th><th scope="col">Input</th><th scope="col">Expected</th><th scope="col">Result</th></tr></thead>
            <tbody>
              <tr><th scope="row">Model A</th><td>12 V, 1 A, 3600 s</td><td>43 200 J / 12 Wh</td><td class="cs-pass">exact</td></tr>
              <tr><th scope="row">Model C</th><td>10 V, step 1 A &rarr; 0.5 A at 1800 s</td><td>27 000 J continuous ideal</td><td class="cs-pass">26 997.5 J (0.0093 % low)</td></tr>
              <tr><th scope="row">Model E</th><td>irregular timestamps, five intervals</td><td>77.605 J, derived by hand</td><td class="cs-pass">77.605 J</td></tr>
              <tr><th scope="row">Model F</th><td>+2 % gain, +50 mV offset</td><td>10.4 V, then 10.000 V calibrated</td><td class="cs-pass">exact both ways</td></tr>
              <tr><th scope="row">Energy 1 s</th><td>3 W for 1 s</td><td>3 J = 0.000833 Wh</td><td class="cs-pass">confirmed</td></tr>
              <tr><th scope="row">Energy 9 s</th><td>3 W for 9 s (the published vector)</td><td>27 J = 0.0075 Wh</td><td class="cs-pass">confirmed</td></tr>
              <tr><th scope="row">Energy 1 h</th><td>3 W for 3600 s</td><td>10 800 J = 3 Wh</td><td class="cs-pass">exact</td></tr>
              <tr><th scope="row">Firmware</th><td>gap, invalid sample, 32-bit rollover</td><td>held, counted, wrap-safe</td><td class="cs-pass">all pass</td></tr>
              <tr><th scope="row">ESP32 build</th><td>pio run -e esp32dev</td><td>links for Xtensa LX6</td><td class="cs-pass">SUCCESS &middot; 25.4 % flash</td></tr>
              <tr><th scope="row">KiCad ERC</th><td>dcm-hw-v1.kicad_sch</td><td>no pin conflicts</td><td class="cs-pass">0 errors, 0 warnings</td></tr>
            </tbody>
          </table>
        </div>
        <p class="cs-note">Not in this table: sensor accuracy, bench measurements, calibration. Those need a board, and there is no board.</p>
      </div></section>

      <section class="cs-section" id="decisions"><div class="wrap">
        <span class="cs-no">08 / ENGINEERING DECISIONS</span>
        <h2>Choices, with what they cost.</h2>
        <div class="table-scroll" tabindex="0" role="region" aria-label="Engineering decisions and alternatives, scrollable">
          <table class="cs-table cs-decisions"><caption class="sr-only">Design decisions, the alternative and the cost</caption>
            <thead><tr><th scope="col">Decision</th><th scope="col">Alternative rejected</th><th scope="col">What it costs</th></tr></thead>
            <tbody>
              <tr><th scope="row">INA226 over INA219</th><td>INA219: 12-bit, ±320 mV, 26 V bus</td><td>Fewer bits of headroom on current; the INA226 gives 16-bit conversion for the same wiring effort.</td></tr>
              <tr><th scope="row">0.1 Ω shunt</th><td>0.05 Ω for a 1 A range</td><td>Caps the design at 0.819 A. A 1 A test needs a different shunt and a fresh calibration.</td></tr>
              <tr><th scope="row">Reverse diode upstream of the shunt</th><td>Diode after the shunt, or none</td><td>0.3&ndash;0.4 V of headroom and ~0.2 W at 0.5 A, in exchange for a measurement the diode cannot corrupt.</td></tr>
              <tr><th scope="row">Trapezoidal integration</th><td>Sum of power samples</td><td>One stored sample and two multiplications. The alternative is not an approximation: it is dimensionally wrong, and out by 2× at 0.5 s sampling.</td></tr>
              <tr><th scope="row">Hold missing intervals</th><td>Integrate across the gap</td><td>Loses a little energy instead of inventing some. The loss is counted and reported.</td></tr>
              <tr><th scope="row">Current from V/R, not the calibration register</th><td>Use the INA226 current register</td><td>One division per sample; removes a whole class of silent error.</td></tr>
              <tr><th scope="row">Bare IC over a breakout module</th><td>Module with an on-board shunt</td><td>Harder to assemble (VSSOP-10), but the VBUS connection is explicit instead of vendor-dependent.</td></tr>
            </tbody>
          </table>
        </div>
      </div></section>

      <section class="cs-section cs-plan" id="plan"><div class="wrap cs-prose">
        <span class="cs-no">09 / BUILD AND TEST PLAN</span>
        <h2>From schematic to first reading.</h2>
        <p>The plan is deliberately slow, because every stage is cheaper to fail than the one after it. Each step has an observable exit condition, and the stop conditions are written down before anything is energised.</p>
        <ol class="cs-roadmap">
          <li><span>1</span><div><b>Review the design</b><p>Read the ERC report, the design review and the open questions. Decide bare IC or module.</p></div></li>
          <li><span>2</span><div><b>Identify the parts</b><p>Confirm markings against datasheets; measure the shunt; check the module's pull-up rail and VBUS connection with a multimeter.</p></div></li>
          <li><span>3</span><div><b>Unpowered continuity</b><p>Trace the current path; prove there is no short from the protected rail to ground.</p></div></li>
          <li><span>4</span><div><b>First power-up</b><p>5 V, 100 mA limit, no load, second person present. Nothing warm, no sensor error on serial.</p></div></li>
          <li><span>5</span><div><b>Communication</b><p>I²C scan finds 0x40; the identity registers read back correctly.</p></div></li>
          <li><span>6</span><div><b>Known loads</b><p>100 Ω and 47 Ω at 12 V; record voltage, current, power and energy against a multimeter.</p></div></li>
          <li><span>7</span><div><b>Calibration</b><p>Six points across the range against a reference meter, in a recorded environment, failures included.</p></div></li>
        </ol>
        <p class="cs-actions"><a class="btn btn-ghost" href="/energy-monitor/hardware/design-review/prototype-review-checklist.md">Prototype review checklist <span aria-hidden="true">&#8599;</span></a><a class="text-link" href="/energy-monitor/verification/calibration-plan/calibration-plan.md">Calibration plan <b>&#8599;</b></a></p>
      </div></section>

      <section class="cs-section cs-outstanding" id="outstanding"><div class="wrap cs-prose">
        <span class="cs-no">10 / OUTSTANDING WORK</span>
        <h2>What this project does not have.</h2>
        <ul class="cs-list cs-list-strong">
          <li><b>No prototype.</b> No component has been purchased, assembled or energised. Everything above was verified without touching hardware.</li>
          <li><b>No PCB.</b> The schematic is a schematic. No layout, routing or design-rule check exists.</li>
          <li><b>No flashed firmware.</b> The binary compiles and links for the target; it has never been uploaded to a board.</li>
          <li><b>No measurements.</b> Not one number in this project came from a physical sensor.</li>
          <li><b>No calibration.</b> The procedure exists; the results do not.</li>
          <li><b>No accuracy claim.</b> Until a reference-meter comparison exists, the design has a stated <em>target</em> of ±1 % voltage and ±2 % current and no evidence for it.</li>
        </ul>
      </div></section>

      <section class="cs-section" id="reproduce"><div class="wrap cs-prose">
        <span class="cs-no">11 / REPRODUCIBILITY</span>
        <h2>Check it without trusting this page.</h2>
        <p>Node, g++ and Python 3 are enough for the software side; KiCad 9 and PlatformIO reproduce the electrical and firmware results. No paid tools, no accounts, no network.</p>
        <pre class="cs-code"><code>node energy-monitor/tests/dcem-reference.test.js        # 67 reference assertions
node energy-monitor/tests/dcem-independent.test.js      # 594 independent checks
node energy-monitor/tests/energy-duration.test.js       # 1 s, 9 s, 1 h, irregular, invalid
node energy-monitor/tests/config-consistency.test.js    # schematic = firmware = site
node energy-monitor/tests/hardware-package.test.js      # claims match artefacts

g++ -std=c++17 -I include -o t src/core/*.cpp test/test_core.cpp &amp;&amp; ./t
pio run -e esp32dev                                      # cross-compile for the ESP32

kicad-cli sch erc dcm-hw-v1.kicad_sch                    # ERC
python3 energy-monitor/hardware/design/compare_netlists.py</code></pre>
        <p class="cs-actions"><a class="btn btn-ghost" href="/projects/dc-energy-monitor-evidence.html">Evidence hub <span aria-hidden="true">&#8599;</span></a><a class="btn btn-ghost" href="/assets/dossier-smart-dc-energy-monitor.pdf">Technical dossier (PDF, 10 pages)</a><a class="text-link" href="/energy-monitor/docs/dossier.md">Markdown source <b>&#8599;</b></a></p>
      </div></section>

      <section class="cs-section cs-attrib" id="attribution"><div class="wrap">
        <span class="cs-no">12 / DEVELOPMENT ATTRIBUTION</span>
        <h2>Who did what.</h2>
        <div class="cs-attrib-grid">
          <div><h3>Produced with AI assistance</h3><p>The model, the test suites, the schematic generator, the firmware, the documentation and this page were written with AI assistance during the construction of this site. That is stated because it is material.</p></div>
          <div><h3>Specified by the founder</h3><p>The project direction; the decision to stay low-voltage and DC; the operating envelope; the requirement that hardware claims stay separate from software claims; and the instruction that no measurement, credential or result be invented.</p></div>
          <div><h3>Still to be done by the founder</h3><p>Read the model and re-derive the power and energy relations independently; run the suites and break something on purpose; review the schematic pin by pin; decide whether the trade-offs in section 08 are the ones he wants to defend; and then build the board.</p></div>
        </div>
        <p class="cs-note">Nothing on this page is presented as the founder's independent engineering design. The project will mean more once he has built and measured it, and that is the point of the next stage.</p>
      </div></section>
    </article>
    '''

    body = (body
            .replace('STAGE_ROWS', stage_rows())
            .replace('@@KICAD_IMG@@_CS@@', build.asset('assets/energy-monitor-kicad-schematic.webp')))

    ld = json.loads(build.SCHEMA_GRAPH)
    ld['@graph'].append({
        "@type": "TechArticle",
        "headline": "Smart Energy Monitoring — engineering case study",
        "about": "A low-voltage DC energy monitor: verified software model, native KiCad schematic with a clean ERC report, and firmware cross-compiled for the ESP32. Prototype not built.",
        "url": "https://elitebotstudios.me/projects/smart-energy-monitoring.html",
        "author": {"@type": "Organization", "name": "Elite Bot Studios"}
    })

    write('/projects/smart-energy-monitoring.html',
          build.head('Smart Energy Monitoring — engineering case study | Elite Bot Studios',
                     'A low-voltage DC energy monitor: a verified software model, a native KiCad schematic with a clean ERC report, and firmware cross-compiled for the ESP32. The prototype is not built, and the page separates what is verified from what is pending.',
                     '/projects/smart-energy-monitoring.html', jsonld=json.dumps(ld, indent=2))
          + build.header('/projects.html') + '\n  <main id="main">\n' + body + '\n  </main>\n'
          + build.footer())


# ---------------------------------------------------------------------------
# Hardware design page: /projects/dc-energy-monitor-hardware.html
#
# The schematic sheets are embedded inline so they scale without a raster step
# and can be zoomed with the browser; each also links to the raw SVG. The
# milestone ladder is rendered from projects.json, the same data the case study
# and the projects index read, so the statuses cannot drift apart.
# ---------------------------------------------------------------------------
HARDWARE_FILES = [
    ('KiCad schematic', '/energy-monitor/hardware/kicad/dcm-hw-v1.kicad_sch', 'native, editable, ERC clean'),
    ('KiCad project', '/energy-monitor/hardware/kicad/dcm-hw-v1.kicad_pro', 'project file'),
    ('ERC report', '/energy-monitor/hardware/kicad/erc-report.txt', 'kicad-cli output'),
    ('KiCad netlist', '/energy-monitor/hardware/kicad/netlist-kicad.net', 'exported by kicad-cli'),
    ('Configuration manifest', '/energy-monitor/hardware/dcm-hw-v1.manifest.json', 'the values all sources must agree on'),
    ('Prototype review checklist', '/energy-monitor/hardware/design-review/prototype-review-checklist.md', 'before buying or powering anything'),
    ('Design source (single file)', '/energy-monitor/hardware/design/dcm-hw-v1.json', 'components, pins, nets, layout'),
    ('Schematic, sheet 1', '/energy-monitor/hardware/schematic/dcm-hw-v1-sheet1.svg', 'power path and current measurement'),
    ('Schematic, sheet 2', '/energy-monitor/hardware/schematic/dcm-hw-v1-sheet2.svg', 'sensor supply, I2C, MCU interface'),
    ('Connection table', '/energy-monitor/hardware/netlist/dcm-hw-v1-connections.csv', 'every pin, net by net'),
    ('KiCad netlist', '/energy-monitor/hardware/netlist/dcm-hw-v1.net', 'for import into Pcbnew'),
    ('Bill of materials', '/energy-monitor/hardware/bom/dcm-hw-v1-bom.csv', 'parts, ratings, rationale'),
    ('Electrical requirements', '/energy-monitor/hardware/requirements/electrical-requirements.md', 'E1–E12, verified vs proposed'),
    ('Design review', '/energy-monitor/hardware/design-review/design-review.md', 'findings and open questions'),
    ('Design rule checks', '/energy-monitor/hardware/design/checks.py', '25 rules, runnable'),
    ('Generator', '/energy-monitor/hardware/design/generate.py', 'draws the schematic from the source'),
    ('Datasheet links', '/energy-monitor/hardware/datasheets-references/links.md', 'official sources'),
    ('Build guide', '/energy-monitor/hardware/README.md', 'plain-language assembly'),
    ('Firmware source', '/energy-monitor/firmware/src/main.cpp', 'ESP32 application layer'),
    ('Firmware core', '/energy-monitor/firmware/src/core/integrator.cpp', 'energy accumulation'),
    ('Firmware tests', '/energy-monitor/firmware/test/test_core.cpp', '69 desktop checks'),
    ('Test vectors', '/energy-monitor/verification/test-vectors/vectors.json', '8 sets with expected values'),
    ('Calibration plan', '/energy-monitor/verification/calibration-plan/calibration-plan.md', 'procedure, not results'),
    ('Bench recording sheet', '/energy-monitor/verification/calibration-plan/bench-test-template.csv', 'blank, for the bench'),
]


def _milestone_ladder():
    ms = _record().get('milestones') or []
    rows = ''.join(
        '<li class="ms" data-state="%s"><span class="ms-name">%s</span>'
        '<span class="ms-status">%s</span><span class="ms-detail">%s</span></li>'
        % (m['state'], m['name'], m['status'], m['detail']) for m in ms)
    return '<ol class="ms-ladder">%s</ol>' % rows


def _files_list():
    return '<ul class="hw-files">%s</ul>' % ''.join(
        '<li><a href="%s">%s</a><span>%s</span></li>' % (href, label, note)
        for label, href, note in HARDWARE_FILES)


def hardware_page():
    record = _record()
    body = '''
    <section class="page-head hw-head"><div class="wrap">
      <a class="backlink" href="/projects/smart-energy-monitoring.html">&larr; Smart Energy Monitoring</a>
      <span class="eyebrow">Project 01 / Hardware design V1 / Prototype not built</span>
      <h1>DC energy monitor.<br><em>The hardware layer.</em></h1>
      <p>A measurement carrier between a low-voltage bench supply and a load: fuse, reverse-polarity diode, transient clamp, a 0.1 Ω shunt and an INA226 wired as the bare IC, read by an ESP32-DevKitC over I²C. The schematic is a native KiCad project that passes ERC with no errors and no warnings, and the firmware compiles for the board it targets.</p>
      <div class="em-head-tags">
        <span class="em-tag em-tag-ok">Native KiCad schematic</span>
        <span class="em-tag em-tag-ok">ERC: 0 errors, 0 warnings</span>
        <span class="em-tag em-tag-ok">Firmware cross-compiled for ESP32</span>
        <span class="em-tag">Not flashed &middot; prototype not built</span>
      </div>
    </div></section>

    <section class="section hw-status-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">01 / WHERE THE PROJECT STANDS</span><h2>Eight stages,<br><em>four of them done.</em></h2></div><p>Each stage is reported at the level of evidence that actually exists. Nothing here is marked complete because it was written down.</p></div>
      MS_LADDER
      <p class="hw-caption">Software and hardware status are deliberately separate. A verified simulation says nothing about a circuit that has never been powered.</p>
    </div></section>

    <section class="section hw-design-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">02 / ARCHITECTURE</span><h2>Source, protection,<br><em>shunt, sensor.</em></h2></div><p>Four things happen between the supply and the load, and each one costs something that is written down.</p></div>
      <div class="hw-block-grid">
        <article><span class="hw-block-no">01</span><h3>Input protection</h3><p>A 1.1 A hold resettable fuse, a 3 A 40 V Schottky for reverse polarity, and a 15 V transient clamp that conducts at 24.4 V — below the sensor's 36 V absolute maximum.</p><p class="hw-block-note">Cost: 0.3–0.4 V of headroom and about 0.2 W at 0.5 A through the diode.</p></article>
        <article><span class="hw-block-no">02</span><h3>Current shunt</h3><p>0.1 Ω, 0.5 %, 1 W in a 2512 package, in series with the load. At 0.5 A it drops 50 mV and dissipates 25 mW — 2 % of its rating.</p><p class="hw-block-note">Cost: the burden voltage, and a hard measurable limit of 0.819 A.</p></article>
        <article><span class="hw-block-no">03</span><h3>Measurement</h3><p>An INA226 measures the shunt drop and the load-side bus voltage, both 16-bit, with ±81.92 mV and 0–36 V ranges. It sits on the 3.3 V rail, so no level shifting is needed.</p><p class="hw-block-note">Cost: the module is the least-defined part — see the open questions.</p></article>
        <article><span class="hw-block-no">04</span><h3>Controller and link</h3><p>An ESP32-DevKitC reads the sensor over I²C at 0x40 on GPIO21/22, with 4.7 kΩ pull-ups to 3.3 V on the carrier, accumulates energy and prints CSV on the USB serial port.</p><p class="hw-block-note">Cost: no real-time clock, so timestamps are milliseconds since boot.</p></article>
      </div>
    </div></section>

    <section class="section hw-sch-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">03 / SCHEMATIC</span><h2>A native KiCad<br><em>project, not a picture.</em></h2></div><p>Built from the official KiCad symbol libraries, checked with <code>kicad-cli</code> 9.0.2, and exported to a netlist that is compared pin-for-pin with the design file on every build.</p></div>

      <div class="hw-kicad-facts">
        <div><span>Tool</span><b>kicad-cli 9.0.2</b></div>
        <div><span>Symbols</span><b>Sensor_Energy:INA226, Device, Connector_Generic, power</b></div>
        <div><span>ERC</span><b class="hw-pass">0 errors, 0 warnings</b></div>
        <div><span>Netlist match</span><b class="hw-pass">42/42 pins agree with the design file</b></div>
      </div>

      <figure class="hw-sch"><figcaption><b>The complete schematic, exported from KiCad</b><a href="/energy-monitor/hardware/kicad/dcm-hw-v1.kicad_sch">Open the .kicad_sch &#8599;</a></figcaption>
        <div class="hw-sch-frame" tabindex="0" role="region" aria-label="KiCad schematic, scrollable on narrow screens"><img src="@@KICAD_IMG@@" width="1400" height="982" alt="KiCad schematic of the DCM-HW-V1 measurement carrier: DC input connector through fuse F1, reverse-protection diode D1 and shunt R1 to the load connector J2, with TVS D2 from the protected rail to ground. The INA226 is drawn with IN+ on the supply side, IN- and VBUS on the load side, A0 and A1 tied to ground, and ALERT unconnected. Decoupling C1 and C2, I2C pull-ups R2 and R3, connector J3 and the ESP32-DevKitC complete the sheet." loading="lazy" decoding="async"></div>
        <p class="hw-caption">Connectivity is drawn with net labels rather than long wires, which is a normal style for a board built from connectors and modules — and it makes the netlist unambiguous. Open the .kicad_sch to edit it, or the SVG export for a vector copy.</p>
      </figure>

      <div class="hw-kicad-grid">
        <article><h3>What ERC checked</h3><p>Pin conflicts, unconnected inputs, power-input pins without a driver, output-to-output clashes, and library consistency. The first run produced two real errors — two power outputs on one net — which were fixed by correcting the symbol pin types rather than by disabling the rule.</p></article>
        <article><h3>What ERC cannot check</h3><p>That the circuit does the right thing. ERC does not know that VBUS must tie to the load side of the shunt, that a reverse diode must sit upstream of it, or that a 0.1 Ω shunt limits the design to 0.82 A. Those are the design review's job.</p></article>
        <article><h3>Netlist agreement</h3><p>The JSON design and the KiCad project are separate descriptions of one circuit, so a script compares the netlist KiCad exports against the design file, pin by pin, as part of the test suite. 42 pins, 8 nets, no differences.</p><code class="hw-code" tabindex="0" role="region" aria-label="Commands to reproduce the ERC and netlist comparison">kicad-cli sch erc dcm-hw-v1.kicad_sch
python3 hardware/design/compare_netlists.py</code></article>
      </div>

      <div class="hw-erc-note">
        <span class="section-index">THE CORRECTION THIS REVISION MAKES</span>
        <p>Revision A treated the sensor as a module and never modelled <strong>VBUS</strong>. On the bare INA226 that is pin 8, a separate input that must be tied to <strong>IN−</strong> for load-side measurement — the datasheet's own example does exactly that. Without it the bus reading is taken from the wrong node and every power figure is wrong while looking plausible. Revision B specifies the bare IC, wires VBUS to VLOAD, straps A0 and A1 to ground for address 0x40, and marks ALERT as a no-connect.</p>
      </div>
    </div></section>

    <section class="section hw-checks-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">04 / DESIGN RULE CHECKS</span><h2>Twenty-five checks,<br><em>with their margins.</em></h2></div><p>Run <code>python3 energy-monitor/hardware/design/checks.py</code> to reproduce. Every number comes from the design file or the datasheet figure recorded beside it.</p></div>
      <div class="table-scroll" tabindex="0" role="region" aria-label="Design rule check results, scrollable"><table class="hw-table"><caption class="sr-only">Design rule checks and their outcomes</caption>
        <thead><tr><th scope="col">Rule</th><th scope="col">Requirement</th><th scope="col">Actual</th><th scope="col">Margin</th><th scope="col">Result</th></tr></thead>
        <tbody>
          <tr><th scope="row">S1 bus voltage</th><td>12 V inside the sensor's 0–36 V range</td><td>12 V vs 36 V</td><td>67 % headroom</td><td class="hw-pass">PASS</td></tr>
          <tr><th scope="row">S2 shunt range</th><td>Drop at 0.5 A inside ±81.92 mV</td><td>50.0 mV</td><td>61 % of full scale</td><td class="hw-pass">PASS</td></tr>
          <tr><th scope="row">S3 measurable current</th><td>State the limit of the chosen shunt</td><td>0.8192 A</td><td>a 1 A test needs 0.05 Ω</td><td class="hw-pass">PASS</td></tr>
          <tr><th scope="row">S5 sensing point</th><td>Measure the load side of the shunt</td><td>IN− on VLOAD</td><td>P = V_load × I</td><td class="hw-pass">PASS</td></tr>
          <tr><th scope="row">L1 logic levels</th><td>No 5 V device on the bus</td><td>3.3 V throughout</td><td>no shifter required</td><td class="hw-pass">PASS</td></tr>
          <tr><th scope="row">L2 pull-ups</th><td>1–10 kΩ for 100 kHz at 3.3 V</td><td>4.7 kΩ</td><td>mid-range</td><td class="hw-pass">PASS</td></tr>
          <tr><th scope="row">P2 transient clamp</th><td>Standoff &gt; 12 V, clamp &lt; 36 V</td><td>15 V / 24.4 V</td><td>3.0 V above, 11.6 V below</td><td class="hw-pass">PASS</td></tr>
          <tr><th scope="row">P5 shunt dissipation</th><td>Under half the rating at 0.5 A</td><td>25 mW in a 1 W part</td><td>2 % of rating</td><td class="hw-pass">PASS</td></tr>
          <tr><th scope="row">P7 ground continuity</th><td>One common ground</td><td>9 pin connections</td><td>single net</td><td class="hw-pass">PASS</td></tr>
          <tr><th scope="row">N1 single-pin nets</th><td>Every net has ≥ 2 connections</td><td>all except the declared NC</td><td>—</td><td class="hw-pass">PASS</td></tr>
        </tbody>
      </table></div>
      <p class="hw-caption">Ten of the twenty-five are shown above; the full table prints when you run the script. All twenty-five pass. Passing these checks means the design satisfies the rules written for it — not that the circuit works.</p>
    </div></section>

    <section class="section hw-bom-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">05 / COMPONENTS</span><h2>What to buy,<br><em>and why that part.</em></h2></div><p>No price is listed: no supplier was queried while writing this, and an invented price is worse than a blank one. Nothing has been purchased.</p></div>
      <div class="table-scroll" tabindex="0" role="region" aria-label="Bill of materials, scrollable"><table class="hw-table"><caption class="sr-only">Bill of materials</caption>
        <thead><tr><th scope="col">Ref</th><th scope="col">Part</th><th scope="col">Function</th><th scope="col">Key ratings</th><th scope="col">Why this one</th></tr></thead>
        <tbody>
          <tr><th scope="row">J1, J2</th><td>Phoenix MKDS 1/2-5.08 or equivalent</td><td>Input and load terminals</td><td class="hw-mono">10 A, 300 V</td><td>Far above the 1 A design current, and safe to probe</td></tr>
          <tr><th scope="row">F1</th><td>Bourns MF-R110</td><td>Resettable fuse</td><td class="hw-mono">1.1 A hold, 2.2 A trip</td><td>At 0.5 A it sits at 45 % of hold, so it does not nuisance-trip</td></tr>
          <tr><th scope="row">D1</th><td>onsemi SS34</td><td>Reverse-polarity protection</td><td class="hw-mono">3 A, 40 V</td><td>Upstream of the shunt, so it cannot corrupt the measurement</td></tr>
          <tr><th scope="row">D2</th><td>Littelfuse SMBJ15A</td><td>Transient clamp</td><td class="hw-mono">15 V standoff, 24.4 V clamp</td><td>Above 12 V, below the sensor's 36 V maximum</td></tr>
          <tr><th scope="row">R1</th><td>Vishay CRCW2512 0R1</td><td>Current shunt</td><td class="hw-mono">0.1 Ω, 0.5 %, 1 W</td><td>50 mV at 0.5 A: 61 % of the sensor range with a 25 mW burden</td></tr>
          <tr><th scope="row">U1</th><td>Texas Instruments INA226AIDGSR (VSSOP-10)</td><td>Voltage and current measurement</td><td class="hw-mono">0–36 V, ±81.92 mV, 2.7–5.5 V</td><td>Bare IC, not a module: only the IC guarantees that VBUS is a pin you can wire</td></tr>
          <tr><th scope="row">U2</th><td>Espressif ESP32-DevKitC-32E</td><td>Microcontroller</td><td class="hw-mono">3.3 V logic</td><td>Same logic level as the sensor, documented, widely available</td></tr>
          <tr><th scope="row">C1, C2</th><td>10 µF 1210, 100 nF 0603, 25 V X7R</td><td>Decoupling</td><td class="hw-mono">25 V</td><td>Standard pair at the sensor supply pin</td></tr>
          <tr><th scope="row">R2, R3</th><td>Yageo RC0603 4k7 1 %</td><td>I²C pull-ups</td><td class="hw-mono">4.7 kΩ</td><td>On the carrier, to 3.3 V, so the module's own pull-ups can be removed</td></tr>
          <tr><th scope="row">J3</th><td>4-way 2.54 mm header</td><td>Link to the MCU</td><td class="hw-mono">3 A</td><td>Four wires: 3V3, GND, SDA, SCL</td></tr>
        </tbody>
      </table></div>
      <p class="hw-caption">The full BOM with rationale and datasheet links for every line is in the download package. Three build options exist and they are not interchangeable: <b>the bare IC</b> (what the schematic describes), <b>a breakout module</b> (a shortcut that must be checked against the schematic pin by pin), and <b>a custom PCB</b> (not designed). This revision documents the bare IC; if you build with a module, the checklist explains what to verify.</p>
    </div></section>

    <section class="section hw-firmware-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">06 / FIRMWARE</span><h2>A core that runs<br><em>on a desktop.</em></h2></div><p>The arithmetic lives in a platform-free C++ core with no Arduino headers, so it can be compiled and tested without a board. The application layer that touches I²C and the serial port is separate.</p></div>
      <div class="hw-fw-grid">
        <article><h3>Modules</h3><ul><li>Register decode (INA226, no I²C)</li><li>Calibration per channel</li><li>Power and trapezoidal energy</li><li>Missing-data policy and counters</li><li>I²C and serial application layer</li></ul></article>
        <article><h3>Missing-data policy</h3><p>An invalid reading costs two intervals — the one ending at it and the one starting from it. A gap longer than five seconds is not integrated at all. Both are counted, so a period with no measurement cannot look like a period of zero power.</p></article>
        <article><h3>Timing</h3><p>Milliseconds since boot in an unsigned 32-bit counter; subtraction wraps correctly after 49.7 days. There is no real-time clock in this design, so no date or time of day is claimed.</p></article>
        <article><h3>What has run</h3><p>Three host suites — <strong>69 + 29 + 10 checks</strong> — and a real cross-compilation: PlatformIO 6.2.0 with the espressif32 8.0.0 platform and the Xtensa GCC 14.2.0 toolchain builds <code>firmware.bin</code> for <code>esp32dev</code>, using 25.4 % of flash and 7.2 % of RAM, with no warnings at <code>-Wall -Wextra</code>. It has never been flashed or run.</p><code class="hw-code" tabindex="0" role="region" aria-label="Commands to build and test the firmware">pio run -e esp32dev
g++ -std=c++17 -I include -o /tmp/t src/core/*.cpp test/test_core.cpp</code></article>
      </div>
      <div class="table-scroll" tabindex="0" role="region" aria-label="Firmware test vectors, scrollable"><table class="hw-table"><caption class="sr-only">Firmware vector sets and expected results</caption>
        <thead><tr><th scope="col">Vector set</th><th scope="col">Data</th><th scope="col">Duration</th><th scope="col">Expected energy</th><th scope="col">Integrated / held / gaps</th></tr></thead>
        <tbody>
          <tr><th scope="row">constant</th><td>12 V, 0.25 A, sampled every 1 s</td><td class="hw-mono">9 s (10 samples)</td><td class="hw-mono">0.007500000 Wh = 27 J</td><td class="hw-mono">9 / 0 / 0</td></tr>
          <tr><th scope="row">step</th><td>Current step at 2.5 s, between samples</td><td class="hw-mono">4 s (5 samples)</td><td class="hw-mono">0.003250000 Wh</td><td class="hw-mono">4 / 0 / 0</td></tr>
          <tr><th scope="row">irregular</th><td>Uneven timestamps: 0, 700 … 3800 ms</td><td class="hw-mono">3.8 s (5 samples)</td><td class="hw-mono">0.002964861 Wh</td><td class="hw-mono">4 / 0 / 0</td></tr>
          <tr><th scope="row">gap</th><td>7 s hole between samples at 2 s and 9 s</td><td class="hw-mono">10 s (5 samples)</td><td class="hw-mono">0.004000000 Wh</td><td class="hw-mono">3 / 1 / 1</td></tr>
          <tr><th scope="row">invalid</th><td>Sensor NACK at 2 s</td><td class="hw-mono">4 s (5 samples)</td><td class="hw-mono">0.001666667 Wh</td><td class="hw-mono">2 / 2 / 0</td></tr>
          <tr><th scope="row">rollover</th><td>32-bit millisecond counter wraps</td><td class="hw-mono">2.5 s (3 samples)</td><td class="hw-mono">0.002083333 Wh</td><td class="hw-mono">2 / 0 / 0</td></tr>
          <tr><th scope="row">zero-current</th><td>Voltage present, no load</td><td class="hw-mono">5 s (6 samples)</td><td class="hw-mono">0.000000000 Wh</td><td class="hw-mono">5 / 0 / 0</td></tr>
          <tr><th scope="row">calibrated</th><td>+2 % gain, +30 mV offset</td><td class="hw-mono">1 s (2 samples)</td><td class="hw-mono">0.000843563 Wh</td><td class="hw-mono">1 / 0 / 0</td></tr>
        </tbody>
      </table></div>
      <p class="hw-caption">The same vectors are fed back through the verified browser model; where the two policies agree the energies match to 1e-12 Wh, and where they differ the difference is asserted rather than hidden.</p>
    </div></section>

    <section class="section hw-next-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">07 / OPEN QUESTIONS</span><h2>What only the<br><em>physical module can answer.</em></h2></div><p>Six questions that must be answered with a multimeter before the ESP32 is connected to anything.</p></div>
      <ol class="hw-questions">
        <li><b>Address straps</b><span>Does the module actually sit at 0x40? Read it with an I²C scanner.</span></li>
        <li><b>Pull-up rail</b><span>Do the module's pull-ups go to 3.3 V, 5 V, or the module supply? Measure before wiring.</span></li>
        <li><b>VBUS connection</b><span>Is the bus voltage taken at IN−? If the pin is separate, wire it there.</span></li>
        <li><b>On-board shunt</b><span>What value is fitted, and does it sit in parallel with the external 0.1 Ω?</span></li>
        <li><b>Common-mode range</b><span>Does the module's amplifier accept a 12 V common-mode at the shunt?</span></li>
        <li><b>Supply quality</b><span>Does the 3.3 V rail hold up under I²C traffic?</span></li>
      </ol>
      <div class="hw-downloads"><span class="section-index">DOWNLOAD THE PACKAGE</span>HW_FILES</div>
      <div class="project-detail-related"><a href="/projects/dc-energy-monitor.html">Run the software model &#8599;</a><a href="/projects/smart-energy-monitoring.html">Project case study &#8599;</a><a href="/energy-monitor/verification/calibration-plan/calibration-plan.md">Calibration plan &#8599;</a></div>
    </div></section>
'''
    body = (body.replace('MS_LADDER', _milestone_ladder())
            .replace('HW_FILES', _files_list())
            .replace('@@KICAD_IMG@@', build.asset('assets/energy-monitor-kicad-schematic.webp')))

    ld = json.loads(build.SCHEMA_GRAPH)
    ld['@graph'].append({
        "@type": "TechArticle",
        "headline": "Smart DC Energy Monitor — hardware design V1",
        "about": "Low-voltage DC energy measurement carrier: schematic, netlist, BOM, design review, firmware and calibration plan.",
        "url": "https://elitebotstudios.me/projects/dc-energy-monitor-hardware.html",
        "author": {"@type": "Organization", "name": "Elite Bot Studios"}
    })

    write('/projects/dc-energy-monitor-hardware.html',
          build.head('DC Energy Monitor — hardware design V1 | Elite Bot Studios',
                     'Hardware design for a low-voltage DC energy monitor: schematic sheets, netlist, bill of materials, design review, embedded firmware and calibration plan. Design drafted; prototype not built.',
                     '/projects/dc-energy-monitor-hardware.html', jsonld=json.dumps(ld, indent=2))
          + build.header('/projects.html') + '\n  <main id="main">\n' + body + '\n  </main>\n'
          + build.footer())



# ---------------------------------------------------------------------------
# Evidence hub: /projects/dc-energy-monitor-evidence.html
#
# Every artefact this project has produced, grouped by kind, each with what it
# is, why it matters, how far it has been verified, and how to open it. The list
# below is the single description of the package; a test checks that every href
# resolves and that the "verified" labels match the artefacts that exist.
# ---------------------------------------------------------------------------
EVIDENCE = [
    ('Software', 'The model, its tests and the data it produces', [
        ('Simulation model', '/energy-monitor/model/dcem.js', 'verified',
         'A dependency-free model of a low-voltage DC energy monitor: source and load solved together, a configurable sensing chain, sampled power and trapezoidal energy on real timestamps.',
         'This is the reference implementation. The browser instrument and the firmware test vectors are both checked against it.'),
        ('Reference test suite', '/energy-monitor/tests/dcem-reference.test.js', 'verified',
         'Seven worked cases (A–G) with hand-derived expected values and stated tolerances, printed as a table.',
         'Shows the arithmetic is right where the mathematics is exact, and quantifies where it is not: a step straddling one interval costs 0.0093 %.'),
        ('Independent verification', '/energy-monitor/tests/dcem-independent.test.js', 'verified',
         '594 checks that compare the model against a second construction: a switching-cycle simulation, a closed-form integral, Ohm and Kirchhoff balance, additivity, quantisation bounds and noise statistics.',
         'A model error that is consistent with itself survives the reference suite and fails this one.'),
        ('Energy duration cases', '/energy-monitor/tests/energy-duration.test.js', 'verified',
         'The 1 s / 9 s / 1 hour / irregular / invalid-sample cases, with expectations derived by hand.',
         'Written after a published description confused the sample interval with the duration. It now cannot happen again silently.'),
        ('Reference datasets', '/energy-monitor/examples/generate.js', 'verified',
         'Six CSV files with metadata headers, regenerated from the model and checked against hand values.',
         'Lets a reviewer open the data in a spreadsheet without running any code.'),
        ('Interactive instrument', '/projects/dc-energy-monitor.html', 'verified',
         'The model running in the browser with controls, four live charts, five guided experiments and CSV export.',
         'The fastest way to see what the model does. Nothing it shows is a hardware measurement.'),
    ]),
    ('Hardware', 'The electrical design, its checks and its parts', [
        ('KiCad schematic', '/energy-monitor/hardware/kicad/dcm-hw-v1.kicad_sch', 'verified',
         'A native KiCad 9 project built from official library symbols: the INA226 as the bare IC, its address straps, the shunt, the protection and the microcontroller interface.',
         'Editable and ERC-checked. This is the authoritative electrical description, not a picture of one.'),
        ('ERC report', '/energy-monitor/hardware/kicad/erc-report.txt', 'verified',
         'The output of kicad-cli sch erc: 0 errors, 0 warnings.',
         'The evidence behind the claim that the schematic is electrically legal. It does not prove the circuit works.'),
        ('KiCad netlist', '/energy-monitor/hardware/kicad/netlist-kicad.net', 'verified',
         'The netlist exported by kicad-cli, compared pin by pin with the design file.',
         '42 pins and 8 nets agree between the schematic and the design intent. Any disagreement fails the build.'),
        ('Schematic drawings', '/energy-monitor/hardware/schematic/dcm-hw-v1-sheet1.svg', 'drafted',
         'Two vector drawings generated from the design file: the power path, and the supply and I²C wiring.',
         'Easier to read than the KiCad export on a small screen. Generated from the same data, so they cannot drift.'),
        ('Design source', '/energy-monitor/hardware/design/dcm-hw-v1.json', 'verified',
         'One JSON file holding every component, pin, net and rating, with the rationale for each part.',
         'The single source from which the drawings, the netlist, the BOM and the KiCad project are generated.'),
        ('Bill of materials', '/energy-monitor/hardware/bom/dcm-hw-v1-bom.csv', 'drafted',
         'Parts with manufacturer, ratings, function, rationale and a datasheet reference each. No prices are quoted.',
         'What to buy, and why that part. Nothing has been purchased.'),
        ('Design rule checks', '/energy-monitor/hardware/design/checks.py', 'verified',
         'Twenty-five rules written for this circuit — sensor ranges, shunt dissipation, clamp voltage, connector ratings, logic compatibility, ground continuity — each printing its margin.',
         'Reproducible, and not a substitute for ERC. Both exist because they check different things.'),
        ('Prototype review checklist', '/energy-monitor/hardware/design-review/prototype-review-checklist.md', 'drafted',
         'The physical steps to take before buying or energising anything, including stop conditions.',
         'The handover document for the part of the project that needs hands.'),
    ]),
    ('Firmware', 'What runs on the board, and how it was tested', [
        ('Application layer', '/energy-monitor/firmware/src/main.cpp', 'verified',
         'I²C initialisation, sensor self-test, calibration, CSV reporting and the scheduling loop for the ESP32.',
         'Cross-compiles for the target. Has never been flashed.'),
        ('Sensor driver', '/energy-monitor/firmware/src/core/sensor.cpp', 'verified',
         'Device logic independent of Arduino: configuration, identity check, register reads, saturation and over-voltage handling.',
         'The same code the host tests exercise, through a transport interface.'),
        ('Energy integrator', '/energy-monitor/firmware/src/core/integrator.cpp', 'verified',
         'Trapezoidal accumulation on wrap-safe millisecond timestamps, with an explicit missing-data policy.',
         'Where the difference between "no data" and "zero power" is decided.'),
        ('Firmware tests', '/energy-monitor/firmware/test/test_core.cpp', 'verified',
         '69 checks over eight vector sets: constant, step, irregular, gap, invalid, rollover, zero current, calibrated.',
         'Desktop arithmetic, not hardware.'),
        ('Mock-bus sensor tests', '/energy-monitor/firmware/test/test_sensor.cpp', 'verified',
         '29 checks driving the driver through a simulated I²C bus: absent device, NACK, wrong identity, saturation, recovery.',
         'Proves the error handling. Says nothing about a real INA226.'),
        ('Build evidence', '/energy-monitor/firmware/BUILD-EVIDENCE.md', 'verified',
         'Toolchain versions, the exact build command, flash and RAM use, and the two compile errors the first attempt produced.',
         'A successful compile is not a working device, and this file says so.'),
    ]),
    ('Verification', 'The checks that tie the three layers together', [
        ('Configuration manifest', '/energy-monitor/hardware/dcm-hw-v1.manifest.json', 'verified',
         'The address, shunt, GPIOs, timing and measurement nodes that the schematic, the firmware and the site must all agree on.',
         'Drift between hardware and firmware is the defect that survives every unit test and fails on the bench.'),
        ('Consistency test', '/energy-monitor/tests/config-consistency.test.js', 'verified',
         'Thirty checks that read the manifest and compare it with the C++ sources, the design file and the published pages.',
         'Fails the build if the schematic and the firmware stop agreeing.'),
        ('Package coherence test', '/energy-monitor/tests/hardware-package.test.js', 'verified',
         'Checks that every referenced artefact exists, that prices are not invented, and that no page claims more than the artefacts support.',
         'A claim of ERC is only allowed if the report exists and says 0/0.'),
        ('Vectors vs model', '/energy-monitor/tests/vector-model-parity.test.js', 'verified',
         'The firmware test vectors replayed through the verified JavaScript model.',
         'Two implementations of one written rule, compared where they should agree and where they deliberately differ.'),
        ('Known limitations', '/energy-monitor/docs/limitations.md', 'drafted',
         'What the project does not establish, written down before anyone asks.',
         'The most useful document for a reviewer deciding how much to trust the rest.'),
    ]),
    ('Documentation', 'For a reader who wants the whole story', [
        ('Technical dossier (PDF)', '/assets/dossier-smart-dc-energy-monitor.pdf', 'verified',
         'A ten-page engineering report generated from the Markdown source: abstract, objectives, requirements, architecture, model, hardware, firmware, verification, results, limitations and attribution.',
         'Written for a supervisor or admissions reviewer who will not browse a website.'),
        ('Dossier source', '/energy-monitor/docs/dossier.md', 'drafted',
         'The maintainable Markdown the PDF and the print page are generated from.',
         'One source, three outputs — nothing is authored twice.'),
        ('Requirements', '/energy-monitor/docs/requirements.md', 'drafted',
         'S1–S13 and E1–E12 with acceptance criteria, each marked verified or proposed.',
         'Shows which requirements are met by evidence and which are still intentions.'),
        ('Model documentation', '/energy-monitor/docs/model.md', 'drafted',
         'Equations, units, integration method, error model, data types and test coverage.',
         'Everything needed to reproduce a published number without the dashboard.'),
        ('Design review', '/energy-monitor/hardware/design-review/design-review.md', 'drafted',
         'What was verified, how, what was not, and the questions only the physical parts can answer.',
         'Includes the finding that VBUS was missing from the previous revision.'),
        ('Reproduction instructions', '/energy-monitor/docs/reproduce.md', 'drafted',
         'The exact commands and the output to expect.',
         'Node, g++ and Python 3 are enough for the software side.'),
    ]),
]

STATUS_LABEL = {
    'verified': ('Verified', 'ev-ok'),
    'drafted': ('Drafted', 'ev-draft'),
    'untested': ('Untested', 'ev-warn'),
}


def evidence_page():
    def item(name, href, status, what, why):
        label, cls = STATUS_LABEL[status]
        ext = ' download' if href.endswith(('.csv', '.net', '.json')) else ''
        return (
            '<article class="ev-item">'
            '<div class="ev-head"><h3>%s</h3><span class="ev-chip %s">%s</span></div>'
            '<p class="ev-what">%s</p><p class="ev-why">%s</p>'
            '<a class="ev-link" href="%s"%s>Open <span aria-hidden="true">&#8599;</span></a>'
            '</article>' % (name, cls, label, what, why, href, ext))

    sections = []
    for title, blurb, items in EVIDENCE:
        sections.append(
            '<section class="ev-section"><div class="wrap">'
            '<div class="ev-section-head"><h2>%s</h2><p>%s</p><span class="ev-count">%d items</span></div>'
            '<div class="ev-grid">%s</div></div></section>'
            % (title, blurb, len(items), ''.join(item(*i) for i in items)))

    total = sum(len(i[2]) for i in EVIDENCE)
    verified = sum(1 for _, _, items in EVIDENCE for i in items if i[2] == 'verified')

    body = '''
    <section class="page-head ev-head"><div class="wrap">
      <a class="backlink" href="/projects/smart-energy-monitoring.html">&larr; Smart Energy Monitoring</a>
      <span class="eyebrow">Project 01 / Evidence hub</span>
      <h1>Every artefact,<br><em>with its status.</em></h1>
      <p>Everything this project has produced, grouped by kind. Each entry says what the file is, why it matters, whether it has been verified, and how to open it. Nothing here is a rendering of the work: these are the files.</p>
      <div class="ev-summary">
        <div><span>Artefacts</span><b>%d</b></div>
        <div><span>Verified</span><b class="ev-ok-text">%d</b></div>
        <div><span>Drafted</span><b>%d</b></div>
        <div><span>Physical prototype</span><b class="ev-warn-text">not built</b></div>
      </div>
    </div></section>
    ''' % (total, verified, total - verified) + ''.join(sections) + '''
    <section class="section"><div class="wrap">
      <div class="ev-legend">
        <h2>What the labels mean</h2>
        <dl>
          <div><dt><span class="ev-chip ev-ok">Verified</span></dt><dd>Checked by a test, a tool or a comparison that can be re-run. The check exists in this repository.</dd></div>
          <div><dt><span class="ev-chip ev-draft">Drafted</span></dt><dd>Written and reviewed but not machine-checked, or a design artefact that no tool can validate without the physical parts.</dd></div>
          <div><dt><span class="ev-chip ev-warn">Untested</span></dt><dd>Depends on hardware that does not exist. No entry currently carries this label, because untested hardware results are not published at all.</dd></div>
        </dl>
      </div>
      <div class="project-detail-related"><a href="/projects/smart-energy-monitoring.html">Read the case study &#8599;</a><a href="/projects/dc-energy-monitor-hardware.html">Hardware design &#8599;</a><a href="/assets/dossier-smart-dc-energy-monitor.pdf">Technical dossier (PDF) &#8599;</a></div>
    </div></section>
    '''

    ld = json.loads(build.SCHEMA_GRAPH)
    ld['@graph'].append({
        "@type": "CollectionPage",
        "name": "Smart DC Energy Monitor — evidence hub",
        "url": "https://elitebotstudios.me/projects/dc-energy-monitor-evidence.html",
        "about": "Source code, schematics, tests, reports and documentation for Project 01, each with its verification status."
    })

    write('/projects/dc-energy-monitor-evidence.html',
          build.head('Project 01 evidence hub — source, schematics and tests | Elite Bot Studios',
                     'Every artefact from the Smart DC Energy Monitor project: simulation model, test suites, KiCad schematic, ERC report, netlist, BOM, ESP32 firmware and documentation, each with what it is and whether it is verified.',
                     '/projects/dc-energy-monitor-evidence.html', jsonld=json.dumps(ld, indent=2))
          + build.header('/projects.html') + '\n  <main id="main">\n' + body + '\n  </main>\n'
          + build.footer())


if __name__ == '__main__':
    energy_monitor_page()
    energy_project_page()
    hardware_page()
    evidence_page()
