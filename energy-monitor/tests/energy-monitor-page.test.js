/* ===========================================================================
   energy-monitor-page.test.js — the built pages must agree with the model

   The model and the site are generated from different places: the model is
   JavaScript, the pages are built by the Python site generator. These checks
   fail the build if the two drift apart.

     1. Every preset the model ships is offered in the instrument's scenario list.
     2. Every control id the dashboard script reads exists in the page, and every
        canvas the chart code looks for exists too.
     3. The numbers quoted on the pages are the numbers the model produces.
     4. Every artefact link on the pages points at a file that exists.
     5. The wording never claims hardware that does not exist.

   Run:  node energy-monitor/tests/energy-monitor-page.test.js
   (after `python3 scripts/site/build_energy.py`)
   ========================================================================== */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const DCEM = require(path.join(__dirname, '..', 'model', 'dcem.js'));

const ROOT = path.resolve(__dirname, '..', '..');
let checks = 0;
function ok(cond, label, detail) {
  checks += 1;
  assert.ok(cond, label + (detail === undefined ? '' : ' — ' + detail));
}

const dashboardPath = path.join(ROOT, 'projects', 'dc-energy-monitor.html');
const projectPath = path.join(ROOT, 'projects', 'smart-energy-monitoring.html');
ok(fs.existsSync(dashboardPath), 'the instrument page is built');
ok(fs.existsSync(projectPath), 'the project page is built');

const dashboard = fs.readFileSync(dashboardPath, 'utf8');
const project = fs.readFileSync(projectPath, 'utf8');

/* ---- 1. presets ------------------------------------------------------- */
DCEM.PRESETS.forEach((preset) => {
  ok(dashboard.includes('value="' + preset.id + '"'), `the instrument offers the preset "${preset.id}"`);
});
const optionCount = (dashboard.match(/<option value="[a-z-]+"/g) || []).length;
ok(optionCount >= DCEM.PRESETS.length, 'the scenario list is at least as long as the preset list', optionCount);

/* ---- 2. the HTML/JS contract ----------------------------------------- */
const dashboardScript = fs.readFileSync(path.join(ROOT, 'assets', 'energy-dashboard.js'), 'utf8');
const idsInScript = [...dashboardScript.matchAll(/\$\('([A-Za-z][A-Za-z0-9_-]*)'\)/g)].map((m) => m[1]);
const uniqueIds = [...new Set(idsInScript)];
ok(uniqueIds.length > 20, 'the script reads a substantial set of elements', uniqueIds.length);
uniqueIds.forEach((id) => {
  ok(dashboard.includes('id="' + id + '"'), `element #${id} exists in the instrument page`);
});
['emChart-voltage', 'emChart-current', 'emChart-power', 'emChart-energy'].forEach((id) => {
  ok(dashboard.includes('id="' + id + '"'), `canvas #${id} exists`);
  ok(dashboardScript.includes(id.replace('emChart-', 'emChart-')) || dashboardScript.includes("'emChart-'"),
    'the chart code derives the canvas ids from the chart list');
});
/* the four required readouts must be labelled, not just numbers */
['Voltage', 'Current', 'Power', 'Energy'].forEach((label) => {
  ok(dashboard.includes('>' + label + '<'), `the instrument labels the ${label} readout`);
});

/* ---- 3. the pages quote the model's own numbers ---------------------- */
function simulatePreset(id) {
  const preset = DCEM.PRESETS.find((p) => p.id === id);
  const run = DCEM.simulate(preset.config);
  return { preset, run };
}
{
  /* Reference case A: 12 V, 1 A, 3600 s → 43 200 J = 12 Wh */
  const a = DCEM.simulate({
    source: { mode: 'constant', voc: 12, rs: 0 }, load: { mode: 'current', i: 1 },
    measurement: {
      voltage: { sensitivity: 1, adcBits: 0 }, current: { sensitivity: 1, adcBits: 0 }
    },
    sampleInterval: 1, duration: 3600, noiseSeed: 1
  });
  assert.ok(Math.abs(a.results.energyJ - 43200) < 1e-6, 'case A still produces 43 200 J');
  ok(project.includes('43 200 J') && project.includes('12 Wh'), 'the project page quotes case A correctly');
  ok(dashboard.includes('43 200 J') && dashboard.includes('12 Wh'), 'the instrument page quotes case A correctly');

  /* Reference case C, whose value depends on the step convention */
  const c = DCEM.simulate({
    source: { mode: 'constant', voc: 10, rs: 0 },
    load: { mode: 'step', iBefore: 1, iAfter: 0.5, stepAt: 1800 },
    measurement: {
      voltage: { sensitivity: 1, adcBits: 0 }, current: { sensitivity: 1, adcBits: 0 }
    },
    sampleInterval: 1, duration: 3600, noiseSeed: 1
  });
  assert.ok(Math.abs(c.results.energyJ - 26997.5) < 1e-6, 'case C still produces 26 997.5 J');
  ok(project.includes('26 997.5 J'), 'the project page quotes the discrete case C value');
  ok(dashboard.includes('26 997.5 J'), 'the instrument page quotes the discrete case C value');

  /* Reference case E, hand-checkable */
  const e = DCEM.integrateSeries([
    { t: 0, p: 10 }, { t: 0.37, p: 12 }, { t: 1.2, p: 7 },
    { t: 2.05, p: 15 }, { t: 3.9, p: 9 }, { t: 7.31, p: 11 }
  ]);
  assert.ok(Math.abs(e.energyJ - 77.605) < 1e-9, 'case E still produces 77.605 J');
  ok(project.includes('77.605 J'), 'the project page quotes case E');

  /* the constant-load preset's own reported energy must not be quoted as if it
     were the ideal 3600 J */
  const cl = simulatePreset('constant-load');
  const deviation = (cl.run.results.energyJ - 3600) / 3600 * 100;
  ok(Math.abs(deviation) > 0.01, 'the constant-load preset is not the ideal 3600 J (quantisation bias exists)',
    deviation.toFixed(4) + ' %');
}

/* ---- 3b. no unsubstituted template placeholders ---------------------- */
[dashboard, project].forEach((html, i) => {
  const name = i === 0 ? 'instrument' : 'project';
  ok(!/@@[A-Z_]+@@/.test(html), `the ${name} page has no leftover template tokens`,
    (html.match(/@@[A-Z_]+@@/g) || []).join(', '));
  ok(!/src="SCREENSHOT"|>PROBLEM<|>APPLICATION<|>ISOLATION</.test(html),
    `the ${name} page has no unsubstituted bare placeholders`);
});

/* ---- 4. artefact links resolve ---------------------------------------- */
const seen = new Set();
[...dashboard.matchAll(/href="(\/energy-monitor\/[^"]+|\/assets\/energy-monitor[^"]*)"/g)]
  .concat([...project.matchAll(/href="(\/energy-monitor\/[^"]+|\/assets\/energy-monitor[^"]*)"/g)])
  .forEach((match) => {
    const href = match[1];
    if (seen.has(href) || href.endsWith('/')) return;
    seen.add(href);
    const target = path.join(ROOT, href.replace(/^\//, '').split('?')[0]);
    ok(fs.existsSync(target), `link target exists: ${href}`);
  });
ok(seen.size >= 6, 'the pages link to at least six artefacts', seen.size);

/* the datasets listed on the page must all exist */
['reference-case-a-constant.csv', 'reference-case-c-step.csv', 'reference-case-e-irregular.csv']
  .forEach((file) => {
    ok(fs.existsSync(path.join(ROOT, 'energy-monitor', 'examples', file)), `dataset exists: ${file}`);
  });

/* ---- 5. hardware claims ------------------------------------------------ */
{
  const forbidden = [
    /bench[- ]tested hardware/i,
    /measured prototype/i,
    /hardware prototype (is|was) complete/i,
    /calibrated against a reference meter(?! will)/i,
    /our sensor/i
  ];
  forbidden.forEach((rx) => {
    ok(!rx.test(project), 'the project page does not claim ' + rx, (project.match(rx) || [''])[0]);
    ok(!rx.test(dashboard), 'the instrument page does not claim ' + rx, (dashboard.match(rx) || [''])[0]);
  });
  ok(/Hardware prototype\s*<\/?[^>]*>?\s*Not yet built/i.test(project) || project.includes('Not yet built'),
    'the project page states that hardware is not built');
  ok(project.toLowerCase().includes('not built') || project.toLowerCase().includes('not yet built'),
    'the project page says the hardware does not exist');
  ok(dashboard.includes('Hardware prototype') && dashboard.includes('not built'),
    'the instrument page separates the software status from the hardware status');
  ok(project.includes('AI-assisted') || project.includes('AI assistance'),
    'the project page discloses AI assistance');
}

console.log(`PASS: energy monitor page contract — ${checks} checks (presets, HTML/JS ids, quoted numbers, artefact links, hardware wording)`);
