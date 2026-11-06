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
    record = _record()['case_study']
    reqs = record.get('requirements') or []
    req_status = {
        'R1': ('Met by the software model', 'ok'),
        'R2': ('Partially met — uncertainty stated in the model, no hardware calibration yet', 'part'),
        'R3': ('Met in software (local record and CSV export)', 'ok'),
        'R4': ('Preserved — the model is DC-only and low-voltage', 'ok'),
        'R5': ('Met — model, tests, datasets and assumptions are published', 'ok'),
    }
    req_rows = ''.join(
        '<tr><th scope="row">%s</th><td>%s</td><td><span class="em-req" data-state="%s">%s</span></td></tr>'
        % (r['id'], r['text'], req_status.get(r['id'], ('—', 'part'))[1], req_status.get(r['id'], ('—',))[0])
        for r in reqs)
    sensing_rows = ''.join(
        '<tr><th scope="row">%s</th><td>%s</td></tr>' % (o['method'], o['note'])
        for o in record.get('sensing_options') or [])
    mcu_rows = ''.join(
        '<tr><th scope="row">%s</th><td>%s</td></tr>' % (o['model'], o['note'])
        for o in record.get('mcu_options') or [])
    questions = ''.join('<li>%s</li>' % q for q in record.get('open_questions') or [])
    validation = ''.join('<li>%s</li>' % v for v in record.get('validation') or [])

    milestones = [
        ('1', 'Approve hardware requirements', 'Not started'),
        ('2', 'Select components against datasheets', 'Not started'),
        ('3', 'Review the schematic', 'Not started'),
        ('4', 'Build the supervised low-voltage prototype', 'Not started'),
        ('5', 'Implement firmware using the model as its arithmetic reference', 'Not started'),
        ('6', 'Bench measurements with recorded conditions', 'Not started'),
        ('7', 'Calibrate against a reference instrument', 'Not started'),
        ('8', 'Document results, including failures', 'Not started'),
        ('9', 'Compare simulation with measurement', 'Not started'),
    ]
    milestone_rows = ''.join(
        '<li class="em-milestone"><span>%s</span><h3 class="em-milestone-h">%s</h3><b>%s</b></li>' % (no, name, status)
        for no, name, status in milestones)

    body = '''
    <article class="em-project">
      <header class="em-project-hero"><div class="wrap">
        <a class="backlink" href="/projects.html">&larr; Projects</a>
        <div class="em-project-meta">
          <span class="chip chip-teal">Software model V1 · verified</span>
          <span class="chip chip-amber">Hardware · not built</span>
          <span>Project 01</span><span>2026-11</span>
        </div>
        <h1>Smart Energy Monitoring.<br><em>Now a working software model.</em></h1>
        <p class="em-project-lede">A low-voltage DC energy monitor, modelled end to end: source, load, sensing chain, ADC, sampled processing and energy accumulation. The model, its reference cases and an independent verification suite are published, and the instrument runs in the browser.</p>
        <div class="em-project-actions">
          <a class="btn btn-primary" href="/projects/dc-energy-monitor.html">Launch the DC Energy Monitor <span aria-hidden="true">&#8599;</span></a>
          <a class="btn btn-ghost" href="/energy-monitor/docs/model.md">Read the model documentation</a>
        </div>
        <figure class="em-project-shot"><img src="@@SCREENSHOT@@" width="1200" height="1203" alt="The DC energy monitor instrument after a completed run: status bar, architecture blocks, controls, four live readouts and four charts of voltage, current, power and accumulated energy. All values are simulated." loading="lazy" decoding="async"><figcaption>The instrument after a step-load run. Solid traces are the simulated truth, dashed traces are what the sensing chain reports. Every value shown is simulated.</figcaption></figure>
      </div></header>

      <section class="section em-status-section"><div class="wrap">
        <div class="em-status-grid">
          <div><span class="em-tag em-tag-ok">Software Model V1</span><h2 class="em-status-h">Verified against reference cases</h2><p>The model, seven reference cases, an independent verification suite and six published datasets are complete for the scope in the requirements document. Status is verifiable by running two Node commands.</p></div>
          <div><span class="em-tag">Hardware prototype</span><h2 class="em-status-h">Not yet built</h2><p>No sensor, ADC, microcontroller, board or enclosure exists. Nothing has been energised. The hardware plan lists the milestones and the approvals required before anything is.</p></div>
        </div>
      </div></section>

      <section class="section"><div class="wrap em-study">
        <section class="em-study-block"><span class="section-index">01 / PROBLEM</span><h2>Energy data is only useful if you know how far to trust it.</h2>
          <p>@@PROBLEM@@</p>
          <p>A monitoring system that reports 12.00 W is making a claim about a measurement chain: a divider, a shunt, an amplifier, an ADC, an arithmetic rule and a clock. Each of those contributes an error, and the errors do not cancel. The useful question is not "what does it read?" but "how far can that reading be from the truth, and why?"</p>
        </section>

        <section class="em-study-block"><span class="section-index">02 / OBJECTIVE</span><h2>Build the measurement chain in software first.</h2>
          <p>@@APPLICATION@@</p>
          <p>V1 has one job: implement the whole chain so that every stage can be inspected, varied and tested independently. A student building the hardware next year should be able to point at the model and say "this is what the firmware must compute, these are the error terms it must tolerate, and this is the test it must pass".</p>
          <ul class="em-scope-list">
            <li><b>In scope:</b> DC source and load models, configurable sensing with gain, offset, noise and quantisation, sampled power, trapezoidal energy, CSV logging, an interactive instrument.</li>
            <li><b>Out of scope:</b> AC or mains measurement, isolation, PCB design, firmware, calibration against a reference meter, any accuracy claim about hardware.</li>
          </ul>
        </section>

        <section class="em-study-block"><span class="section-index">03 / SYSTEM DESIGN</span><h2>Two paths through the same signal.</h2>
          <p>The model solves the electrical operating point at every sample instant, then passes it through the sensing chain. That gives two numbers per channel — the truth and what a firmware would report — and the difference between them is the subject of the whole project.</p>
          <figure class="em-arch-figure">
            <svg viewBox="0 0 1080 300" role="img" aria-labelledby="emArchTitle emArchDesc">
              <title id="emArchTitle">Signal path of the DC energy monitor model</title>
              <desc id="emArchDesc">A DC source feeds a load. The same operating point feeds two paths: an ideal path holding the simulated truth, and a measurement path through a voltage divider or shunt amplifier, gain and offset errors, noise, an ADC with quantisation, and a calibration correction. Both paths reach sampled processing, which computes power and accumulates energy, then logging and the instrument.</desc>
              <path class="em-arch-line" d="M150 120h90M370 120h60M580 120h60"/>
              <rect class="em-arch-box" x="30" y="80" width="120" height="80" rx="6"/>
              <text class="em-arch-t" x="48" y="112">DC source</text>
              <text class="em-arch-s" x="48" y="132">Voc, Rs</text>
              <rect class="em-arch-box" x="250" y="80" width="120" height="80" rx="6"/>
              <text class="em-arch-t" x="268" y="112">Load</text>
              <text class="em-arch-s" x="268" y="132">R or I(t)</text>

              <path class="em-arch-line-cyan" d="M310 80V40h330"/>
              <text class="em-arch-label" x="330" y="30">SIMULATED TRUTH</text>
              <rect class="em-arch-box-cyan" x="640" y="16" width="180" height="48" rx="6"/>
              <text class="em-arch-t" x="656" y="46">True V, I → P</text>

              <path class="em-arch-line" d="M370 120h40"/>
              <rect class="em-arch-box" x="410" y="80" width="170" height="80" rx="6"/>
              <text class="em-arch-t" x="426" y="110">Dividers and</text>
              <text class="em-arch-t" x="426" y="130">shunt amplifier</text>
              <text class="em-arch-s" x="426" y="150">gain, offset, noise</text>
              <rect class="em-arch-box" x="640" y="80" width="180" height="80" rx="6"/>
              <text class="em-arch-t" x="656" y="110">ADC</text>
              <text class="em-arch-s" x="656" y="130">n bits, Vref</text>
              <text class="em-arch-s" x="656" y="148">quantisation</text>
              <rect class="em-arch-box" x="880" y="80" width="170" height="80" rx="6"/>
              <text class="em-arch-t" x="896" y="110">Calibration</text>
              <text class="em-arch-s" x="896" y="130">per channel</text>

              <path class="em-arch-line-cyan" d="M820 120h60"/>
              <path class="em-arch-line" d="M880 160v40H700"/>
              <rect class="em-arch-box" x="520" y="200" width="180" height="70" rx="6"/>
              <text class="em-arch-t" x="536" y="228">Sampled processing</text>
              <text class="em-arch-s" x="536" y="248">P = V·I, trapezoid</text>
              <path class="em-arch-line" d="M700 235h80"/>
              <rect class="em-arch-box" x="780" y="200" width="150" height="70" rx="6"/>
              <text class="em-arch-t" x="796" y="228">Logging</text>
              <text class="em-arch-s" x="796" y="248">CSV, instrument</text>
              <path class="em-arch-line-cyan" d="M820 64v16"/>
            </svg>
            <figcaption>Both paths come from the same operating point. The model never lets the reported value stand in for the truth without showing both.</figcaption>
          </figure>
        </section>

        <section class="em-study-block"><span class="section-index">04 / ENGINEERING MATHEMATICS</span><h2>Power, and the integral that turns it into energy.</h2>
          <div class="em-study-math">
            <div class="em-study-eq"><span>Instantaneous power</span><div class="em-eq"><math display="block"><mrow><mi>P</mi><mo>=</mo><mi>V</mi><mo>·</mo><mi>I</mi></mrow></math></div><p>Computed twice: once from the reported voltage and current, once from the simulated truth.</p></div>
            <div class="em-study-eq"><span>Energy, discretely</span><div class="em-eq"><math display="block"><mrow><msub><mi>E</mi><mi>j</mi></msub><mo>=</mo><msub><mi>E</mi><mrow><mi>j</mi><mo>−</mo><mn>1</mn></mrow></msub><mo>+</mo><mfrac><mrow><msub><mi>P</mi><mrow><mi>j</mi><mo>−</mo><mn>1</mn></mrow></msub><mo>+</mo><msub><mi>P</mi><mi>j</mi></msub></mrow><mn>2</mn></mfrac><mo>·</mo><mo>(</mo><msub><mi>t</mi><mi>j</mi></msub><mo>−</mo><msub><mi>t</mi><mrow><mi>j</mi><mo>−</mo><mn>1</mn></mrow></msub><mo>)</mo></mrow></math></div><p>The interval comes from the timestamps, never from an assumed period.</p></div>
            <div class="em-study-eq"><span>Watt-hours</span><div class="em-eq"><math display="block"><mrow><msub><mi>E</mi><mtext>Wh</mtext></msub><mo>=</mo><mfrac><msub><mi>E</mi><mtext>J</mtext></msub><mn>3600</mn></mfrac></mrow></math></div><p>Accumulators hold joules; 1 Wh = 3600 J exactly.</p></div>
          </div>
          <p class="em-study-note">The trapezoidal rule is second order: halving the sample interval quarters the integration error. The independent suite checks that convergence rate directly rather than trusting it.</p>
        </section>

        <section class="em-study-block"><span class="section-index">05 / SOFTWARE ARCHITECTURE</span><h2>One module, no dependencies, two consumers.</h2>
          <p><code>energy-monitor/model/dcem.js</code> holds all of the physics and arithmetic. The dashboard is the second consumer of that file, not a reimplementation: if the model and the instrument could disagree, that would defeat the purpose.</p>
          <ol class="em-study-steps">
            <li><span>01</span><div><b>Source and load</b><p>Solved together so voltage, current and resistance cannot contradict each other.</p></div></li>
            <li><span>02</span><div><b>Sensing and ADC</b><p>Sensitivity, gain error, offset, noise, clamping and uniform quantisation, per channel.</p></div></li>
            <li><span>03</span><div><b>Sampling and validation</b><p>Timestamps, rejection of duplicate or non-monotonic samples, counters instead of silence.</p></div></li>
            <li><span>04</span><div><b>Power and energy</b><p>Trapezoidal accumulation on the real interval, with imported and exported energy separated.</p></div></li>
            <li><span>05</span><div><b>Logging</b><p>CSV with both truth and measurement columns, written locally.</p></div></li>
          </ol>
        </section>

        <section class="em-study-block"><span class="section-index">06 / VERIFICATION</span><h2>Seven reference cases, two independent methods.</h2>
          <p>The reference suite asserts hand-derived values with stated tolerances. The independent suite compares the model against a different construction — a second integrator over 500 random series, a closed-form sine integral with a convergence-order check, Ohm's law and Kirchhoff balance, additivity across consecutive runs, and statistics on the noise generator.</p>
          <div class="table-scroll" tabindex="0" role="region" aria-label="Reference cases, scrollable">
            <table class="em-table">
              <caption class="sr-only">Reference cases and their expected results</caption>
              <thead><tr><th scope="col">Case</th><th scope="col">Input</th><th scope="col">Expected</th><th scope="col">Basis</th></tr></thead>
              <tbody>
                <tr><th scope="row">A</th><td>12 V, 1 A, 3600 s</td><td class="em-mono">43 200 J / 12 Wh</td><td>exact — constant power</td></tr>
                <tr><th scope="row">B</th><td>5 V, 2 A, 1800 s</td><td class="em-mono">18 000 J / 5 Wh</td><td>exact</td></tr>
                <tr><th scope="row">C</th><td>10 V, 1 A → 0.5 A at 1800 s</td><td class="em-mono">26 997.5 J / 7.49931 Wh</td><td>step convention, 0.0093 % below the 27 000 J ideal</td></tr>
                <tr><th scope="row">D</th><td>12 V, 0 A, 600 s</td><td class="em-mono">0 J</td><td>zero current, voltage still measured</td></tr>
                <tr><th scope="row">E</th><td>irregular timestamps</td><td class="em-mono">77.605 J</td><td>hand-checkable; a uniform-spacing estimate would give 77.973 J</td></tr>
                <tr><th scope="row">F</th><td>+2 % gain, +50 mV offset</td><td class="em-mono">10.4 V → 10.000 V calibrated</td><td>analytical, and the correction is exact</td></tr>
                <tr><th scope="row">G</th><td>invalid datasets</td><td class="em-mono">classified and refused</td><td>six defect classes, each with its own code</td></tr>
              </tbody>
            </table>
          </div>
          <p class="em-study-note">Test output, not a summary: <code>67 assertions</code> in the reference suite and <code>594 checks</code> in the independent suite, both runnable with Node and no packages.</p>
        </section>

        <section class="em-study-block"><span class="section-index">07 / TRADE-OFFS</span><h2>Choices that cost something.</h2>
          <dl class="em-tradeoffs">
            <div><dt>Trapezoidal instead of rectangular</dt><dd>Second-order accuracy for two multiplications and one extra stored sample. The rectangular rule would have been simpler and would have biased every step.</dd></div>
            <div><dt>Per-channel calibration</dt><dd>Two independent corrections instead of one shared one. A divider and a shunt amplifier do not share a tolerance, and an early version of the model got this wrong.</dd></div>
            <div><dt>Ideal quantisation only</dt><dd>The model does not reproduce INL, DNL or reference drift. They matter for a real ADC and would need datasheet numbers to model honestly.</dd></div>
            <div><dt>Seeded noise instead of random</dt><dd>Reproducible runs and testable statistics, at the cost of not being able to show a "different" run on each reload.</dd></div>
            <div><dt>No filtering by default</dt><dd>A first-order low-pass is available but off, because it changes reference results. Turning it on is a decision the user makes, not a hidden default.</dd></div>
            <div><dt>Browser-side only</dt><dd>No server, no account, no upload. The cost is that a run lives and dies in the tab unless it is exported.</dd></div>
          </dl>
        </section>

        <section class="em-study-block"><span class="section-index">08 / RESULTS</span><h2>What the software demonstrates.</h2>
          <ul class="em-result-list">
            <li>A DC power and energy calculation that matches hand-derived values exactly where the mathematics is exact, and to a quantified tolerance where it is not.</li>
            <li>A sensing chain whose gain, offset, noise and quantisation each produce the error the equations predict, with calibration recovering the value.</li>
            <li>A sampling rule that uses real timestamps, so irregular intervals integrate correctly.</li>
            <li>Honest failure: invalid data is refused and counted rather than integrated into a plausible-looking total.</li>
            <li>An instrument that shows the truth and the measurement at the same time, so the difference is never hidden behind a single number.</li>
          </ul>
        </section>

        <section class="em-study-block"><span class="section-index">09 / LIMITATIONS</span><h2>What it does not establish.</h2>
          <ul class="em-result-list">
            <li>No hardware accuracy of any kind: no sensor, ADC, MCU or board has been used.</li>
            <li>No AC, mains, isolation or grid behaviour.</li>
            <li>No switched-mode or fast-transient load behaviour; loads that change faster than the sample interval are aliased.</li>
            <li>No ADC non-idealities, no fixed-point arithmetic, no timer jitter.</li>
            <li>No filtering design and no loop response.</li>
          </ul>
          <p class="em-study-note">The full list is in <a href="/energy-monitor/docs/limitations.md">limitations.md</a>.</p>
        </section>
      </div></section>

      <section class="section em-plan-section"><div class="wrap">
        <div class="section-heading split-heading"><div><span class="section-index">09b / HARDWARE DESIGN</span><h2>From model<br><em>to circuit.</em></h2></div><p>The measurement chain the model describes now has a schematic, a netlist, a bill of materials, a design review and a firmware core. It still has no prototype.</p></div>
        MS_LADDER
        <div class="em-hardware-teaser">
          <div><h3>What exists</h3><p>Two schematic sheets generated from a single netlist, 25 design-rule checks with their margins printed, a bill of materials with a stated rationale for every part, a portable C++ calculation core that compiles and passes 69 desktop checks, and a calibration procedure with a blank recording sheet.</p></div>
          <div><h3>What does not exist</h3><p>No KiCad project and no ERC, no compiled ESP32 firmware, no PCB, no assembled board, no measurement and no calibration. The hardware page says which of those is which, in detail.</p></div>
        </div>
        <div class="em-project-actions"><a class="btn btn-primary" href="/projects/dc-energy-monitor-hardware.html">Open the hardware design <span aria-hidden="true">&#8599;</span></a><a class="btn btn-ghost" href="/energy-monitor/verification/calibration-plan/calibration-plan.md">Calibration plan</a></div>
      </div></section>

      <section class="section em-plan-section"><div class="wrap">
        <div class="section-heading split-heading"><div><span class="section-index">10 / NEXT PHASE</span><h2>From model<br><em>to bench.</em></h2></div><p>A supervised, low-voltage hardware prototype. No component has been selected and nothing has been energised. Every milestone below is not started.</p></div>
        <ol class="em-milestones">@@MILESTONES@@</ol>
        <div class="em-plan-grid">
          <div><h3>Requirements carried over</h3>
            <div class="table-scroll" tabindex="0" role="region" aria-label="Requirements and their status, scrollable"><table class="em-table em-req-table"><caption class="sr-only">Requirements with their current status</caption><thead><tr><th scope="col">ID</th><th scope="col">Requirement</th><th scope="col">Status</th></tr></thead><tbody>@@REQUIREMENT_ROWS@@</tbody></table></div>
          </div>
          <div><h3>Open questions</h3><ul class="em-result-list">@@QUESTIONS@@</ul></div>
        </div>
        <div class="em-plan-tables">
          <div><h3>Sensing methods to compare</h3><div class="table-scroll" tabindex="0" role="region" aria-label="Sensing options, scrollable"><table class="em-table"><caption class="sr-only">Sensing options</caption><tbody>@@SENSING_ROWS@@</tbody></table></div><p class="em-study-note">Nothing is selected. Each method is listed with the trade-off that would decide it.</p></div>
          <div><h3>Controller candidates</h3><div class="table-scroll" tabindex="0" role="region" aria-label="Controller options, scrollable"><table class="em-table"><caption class="sr-only">Controller options</caption><tbody>@@MCU_ROWS@@</tbody></table></div><p class="em-study-note">Controller choice follows the measurement decisions, not the other way round.</p></div>
        </div>
        <div class="em-safety"><span class="section-index">SAFETY AND ISOLATION</span><p>@@ISOLATION@@</p><p class="em-study-note">The first build is limited to a supervised bench supply at 24 V DC or less with a current limit of 1 A or less, an inline fuse, and a second person present. No mains wiring.</p></div>
        <div class="em-validation"><span class="section-index">HOW A HARDWARE RESULT WOULD BE CHECKED</span><ul class="em-result-list">@@VALIDATION@@</ul></div>
      </div></section>

      <section class="section em-dev-section"><div class="wrap">
        <div class="em-dev-head"><div><span class="section-index">11 / DEVELOPMENT AND ATTRIBUTION</span><h2>How this was made, and what is whose.</h2></div><span class="status-label">Software artefact · AI-assisted</span></div>
        <dl class="em-meta-strip">
          <div><dt>Status</dt><dd>Software Model V1, verified</dd></div>
          <div><dt>Attribution</dt><dd>AI-assisted implementation</dd></div>
          <div><dt>Dependencies</dt><dd>None</dd></div>
          <div><dt>Runtime</dt><dd>Browser and Node</dd></div>
          <div><dt>Hardware</dt><dd>Not built</dd></div>
        </dl>
        <div class="em-dev-grid">
          <article><h3>What the agent produced</h3><p>The model, both test suites, the datasets, the documentation, the instrument interface and this page were written with AI assistance. That is disclosed because it is material, not as a formality.</p></article>
          <article><h3>What the founder specified</h3><p>The project direction, the scope decision to stay low-voltage and DC, the ranges, the requirement to keep hardware claims separate from software claims, and the instruction that no measurement be invented.</p></article>
          <article><h3>What the founder still has to do</h3><p>Read and understand the model, re-derive at least the power and energy relations independently, run the test suites, break something and watch a test fail, then decide whether the trade-offs in section 07 are the ones he wants to defend.</p></article>
          <article><h3>How to check it without trusting this page</h3><p>Open the model file, run the two Node commands, compare the printed table with the numbers above. Nothing on this page is required to reproduce a result.</p><code class="em-code-block" tabindex="0" role="region" aria-label="Commands to reproduce the results">node energy-monitor/tests/dcem-reference.test.js
node energy-monitor/tests/dcem-independent.test.js</code></article>
          <article><h3>What is verifiable and what is not</h3><p>Verifiable: the arithmetic, the error model, the tests, the datasets, the instrument. Not verifiable here: anything about physical accuracy, because no physical system exists.</p></article>
          <article><h3>Repository layout</h3><p>Model, tests, examples and documentation sit under <code>energy-monitor/</code>. The dashboard script under <code>assets/</code> is presentation only. Nothing in the software model is presented as the founder's independent engineering work.</p></article>
        </div>
        <div class="em-dev-links">
          <span class="section-index">ARTEFACTS</span>
          @@ARTEFACTS@@
        </div>
        <div class="project-detail-related"><a href="/projects/dc-energy-monitor.html">Launch the instrument &#8599;</a><a href="/energy-monitor/docs/requirements.md">Requirements &#8599;</a><a href="/energy-monitor/docs/hardware-plan.md">Hardware plan &#8599;</a><a href="/lab.html">Engineering notes &#8599;</a></div>
      </div></section>
    </article>
    '''

    body = (body
            .replace('@@SCREENSHOT@@', build.asset('assets/energy-monitor-dashboard.webp'))
            .replace('@@PROBLEM@@', record.get('problem') or record.get('overview', ''))
            .replace('@@APPLICATION@@', record.get('application', ''))
            .replace('@@ISOLATION@@', record.get('isolation', ''))
            .replace('@@MILESTONES@@', milestone_rows)
            .replace('@@REQUIREMENT_ROWS@@', req_rows)
            .replace('@@QUESTIONS@@', questions)
            .replace('@@SENSING_ROWS@@', sensing_rows)
            .replace('@@MCU_ROWS@@', mcu_rows)
            .replace('@@VALIDATION@@', validation)
            .replace('MS_LADDER', _milestone_ladder())
            .replace('@@ARTEFACTS@@', _artefacts_html()))

    ld = json.loads(build.SCHEMA_GRAPH)
    ld['@graph'].append({
        "@type": "SoftwareSourceCode",
        "name": "Smart DC Energy Monitor — Software Model V1",
        "description": "A simulated low-voltage DC energy-monitoring system with a configurable sensing chain, sampled power and trapezoidal energy accumulation, published with reference and independent test suites.",
        "codeRepository": "https://elitebotstudios.me/energy-monitor/model/dcem.js",
        "url": "https://elitebotstudios.me/projects/dc-energy-monitor.html",
        "author": {"@type": "Organization", "name": "Elite Bot Studios"}
    })

    write('/projects/smart-energy-monitoring.html',
          build.head('Smart Energy Monitoring — verified software model | Elite Bot Studios',
                     'A low-voltage DC energy-monitoring project: a verified software model of the measurement chain, with published source, reference cases and an independent test suite. Hardware prototype not built.',
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
      <p>A measurement carrier between a low-voltage bench supply and a load: fuse, reverse-polarity diode, transient clamp, a 0.1 Ω shunt and an INA226, read by an ESP32-DevKitC over I²C. Schematics, netlist, bill of materials, design review, firmware and calibration plan are published together.</p>
      <div class="em-head-tags">
        <span class="em-tag em-tag-ok">Design drafted and script-reviewed</span>
        <span class="em-tag em-tag-warn">KiCad ERC not run</span>
        <span class="em-tag em-tag-warn">Firmware not compiled for the board</span>
        <span class="em-tag">Prototype not built</span>
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
      <div class="section-heading split-heading"><div><span class="section-index">03 / SCHEMATIC</span><h2>Two sheets,<br><em>generated from one netlist.</em></h2></div><p>Both sheets are drawn from <code>design/dcm-hw-v1.json</code> by a script that refuses to emit a drawing with a floating connection. Open either at full size, or regenerate and check the output yourself.</p></div>
      <figure class="hw-sch"><figcaption><b>Sheet 1 — power path and current measurement</b><a href="/energy-monitor/hardware/schematic/dcm-hw-v1-sheet1.svg">Open full size &#8599;</a></figcaption>
        <div class="hw-sch-frame" tabindex="0" role="region" aria-label="Schematic sheet 1, scrollable on narrow screens"><img src="/energy-monitor/hardware/schematic/dcm-hw-v1-sheet1.svg" width="1080" height="700" alt="Schematic sheet 1: DC input J1 through fuse F1 and reverse-protection diode D1 to a junction feeding TVS D2 to ground, then shunt R1 to the load terminals J2. Test points on the input and load side. The INA226 pins IN+ and IN- are attached by VPROT and VLOAD labels." loading="lazy" decoding="async"></div>
        <p class="hw-caption">The current path is drawn explicitly. The sensor taps across the shunt through the VPROT and VLOAD net labels, which is why no wire runs from the sensor to the middle of the circuit.</p>
      </figure>
      <figure class="hw-sch"><figcaption><b>Sheet 2 — sensor supply, I²C and microcontroller interface</b><a href="/energy-monitor/hardware/schematic/dcm-hw-v1-sheet2.svg">Open full size &#8599;</a></figcaption>
        <div class="hw-sch-frame" tabindex="0" role="region" aria-label="Schematic drawing, scrollable on narrow screens"><img src="/energy-monitor/hardware/schematic/dcm-hw-v1-sheet2.svg" width="1080" height="560" alt="Schematic sheet 2: INA226 module supply and ground, decoupling capacitors C1 and C2, 4.7 kilo-ohm pull-ups R2 and R3 to 3.3 volts, a four-way connector J3 and the ESP32-DevKitC with SDA on GPIO21 and SCL on GPIO22." loading="lazy" decoding="async"></div>
        <p class="hw-caption">Connectivity on this sheet is carried by net labels; the pin-by-pin truth is in the connection table.</p>
      </figure>
      <div class="hw-erc-note">
        <span class="section-index">WHAT HAS NOT BEEN DONE</span>
        <p><strong>No KiCad project exists and no ERC has been run.</strong> No EDA tool was available in the environment where this was designed. Instead, the circuit is described in one JSON file; a generator draws the schematic and emits a KiCad netlist; and <code>design/checks.py</code> checks the 25 electrical rules this design depends on, printing the margin for each. That is not the same as ERC, and it is not presented as such. The next step for the owner is to redraw the sheets in KiCad, import or re-enter the netlist, and run ERC.</p>
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
          <tr><th scope="row">U1</th><td>INA226 module (CJMCU-226 class)</td><td>Voltage and current measurement</td><td class="hw-mono">0–36 V, ±81.92 mV, 2.7–5.5 V</td><td>16-bit, 3.3 V logic, no level shifting</td></tr>
          <tr><th scope="row">U2</th><td>Espressif ESP32-DevKitC-32E</td><td>Microcontroller</td><td class="hw-mono">3.3 V logic</td><td>Same logic level as the sensor, documented, widely available</td></tr>
          <tr><th scope="row">C1, C2</th><td>10 µF 1210, 100 nF 0603, 25 V X7R</td><td>Decoupling</td><td class="hw-mono">25 V</td><td>Standard pair at the sensor supply pin</td></tr>
          <tr><th scope="row">R2, R3</th><td>Yageo RC0603 4k7 1 %</td><td>I²C pull-ups</td><td class="hw-mono">4.7 kΩ</td><td>On the carrier, to 3.3 V, so the module's own pull-ups can be removed</td></tr>
          <tr><th scope="row">J3</th><td>4-way 2.54 mm header</td><td>Link to the MCU</td><td class="hw-mono">3 A</td><td>Four wires: 3V3, GND, SDA, SCL</td></tr>
        </tbody>
      </table></div>
      <p class="hw-caption">The full BOM with rationale and datasheet links for every line is in the download package.</p>
    </div></section>

    <section class="section hw-firmware-section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">06 / FIRMWARE</span><h2>A core that runs<br><em>on a desktop.</em></h2></div><p>The arithmetic lives in a platform-free C++ core with no Arduino headers, so it can be compiled and tested without a board. The application layer that touches I²C and the serial port is separate.</p></div>
      <div class="hw-fw-grid">
        <article><h3>Modules</h3><ul><li>Register decode (INA226, no I²C)</li><li>Calibration per channel</li><li>Power and trapezoidal energy</li><li>Missing-data policy and counters</li><li>I²C and serial application layer</li></ul></article>
        <article><h3>Missing-data policy</h3><p>An invalid reading costs two intervals — the one ending at it and the one starting from it. A gap longer than five seconds is not integrated at all. Both are counted, so a period with no measurement cannot look like a period of zero power.</p></article>
        <article><h3>Timing</h3><p>Milliseconds since boot in an unsigned 32-bit counter; subtraction wraps correctly after 49.7 days. There is no real-time clock in this design, so no date or time of day is claimed.</p></article>
        <article><h3>What has run</h3><p>The core compiles with <code>g++ -std=c++17 -Wall -Wextra</code> and passes <strong>69 checks</strong> across eight vector sets. The ESP32 application layer has <strong>never been compiled</strong>, because no ESP32 toolchain was available.</p><code class="hw-code" tabindex="0" role="region" aria-label="Commands to run the firmware tests">g++ -std=c++17 -I include -o /tmp/t src/core/*.cpp test/test_core.cpp
/tmp/t</code></article>
      </div>
      <div class="table-scroll" tabindex="0" role="region" aria-label="Firmware test vectors, scrollable"><table class="hw-table"><caption class="sr-only">Firmware vector sets and expected results</caption>
        <thead><tr><th scope="col">Vector set</th><th scope="col">What it exercises</th><th scope="col">Expected energy</th><th scope="col">Integrated / held / gaps</th></tr></thead>
        <tbody>
          <tr><th scope="row">constant</th><td>12 V, 0.25 A, 1 s samples</td><td class="hw-mono">0.007500000 Wh (= 27 J)</td><td class="hw-mono">9 / 0 / 0</td></tr>
          <tr><th scope="row">step</th><td>Current step falls between samples</td><td class="hw-mono">0.003250000 Wh</td><td class="hw-mono">4 / 0 / 0</td></tr>
          <tr><th scope="row">irregular</th><td>Uneven timestamps</td><td class="hw-mono">0.002964861 Wh</td><td class="hw-mono">4 / 0 / 0</td></tr>
          <tr><th scope="row">gap</th><td>7 s hole exceeds the 5 s limit</td><td class="hw-mono">0.004000000 Wh</td><td class="hw-mono">3 / 1 / 1</td></tr>
          <tr><th scope="row">invalid</th><td>Sensor NACK mid-run</td><td class="hw-mono">0.001666667 Wh</td><td class="hw-mono">2 / 2 / 0</td></tr>
          <tr><th scope="row">rollover</th><td>32-bit millisecond wrap</td><td class="hw-mono">0.002083333 Wh</td><td class="hw-mono">2 / 0 / 0</td></tr>
          <tr><th scope="row">zero-current</th><td>Voltage present, no load</td><td class="hw-mono">0.000000000 Wh</td><td class="hw-mono">5 / 0 / 0</td></tr>
          <tr><th scope="row">calibrated</th><td>+2 % gain, +30 mV offset</td><td class="hw-mono">0.000843563 Wh</td><td class="hw-mono">1 / 0 / 0</td></tr>
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
    body = body.replace('MS_LADDER', _milestone_ladder()).replace('HW_FILES', _files_list())

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


if __name__ == '__main__':
    energy_monitor_page()
    energy_project_page()
    hardware_page()
