/* ===========================================================================
   content-consistency.test.js — the site may not contradict itself

   The defect this file exists for: for two sprints the projects index said "no
   hardware architecture, component selection, firmware, or test plan is being
   claimed yet" while a KiCad schematic, an ERC report and a cross-compiled
   firmware were sitting in the repository. Every individual page was internally
   plausible; the site as a whole was lying.

   So these checks are cross-page and evidence-driven:
     - stale concept-era phrasing is banned outright;
     - a claim may only appear if the artefact behind it exists;
     - the project status must be identical on every surface that states it;
     - the case study must link the things it describes.

   Run: node energy-monitor/tests/content-consistency.test.js
   ========================================================================== */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
let checks = 0;
const fails = [];
function ok(cond, label, detail) {
  checks += 1;
  if (!cond) fails.push(label + (detail === undefined ? '' : ' — ' + detail));
}

const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8');
const has = (rel) => fs.existsSync(path.join(ROOT, rel));
const text = (html) => html.replace(/<script[\s\S]*?<\/script>/g, ' ')
  .replace(/<style[\s\S]*?<\/style>/g, ' ')
  .replace(/<[^>]+>/g, ' ')
  .replace(/\s+/g, ' ');

/* Every public page that talks about the project, plus the instrument and the
   hardware page. Anything not listed here is not allowed to describe status. */
const SURFACES = [
  'index.html',
  'projects.html',
  'projects/smart-energy-monitoring.html',
  'projects/dc-energy-monitor.html',
  'projects/dc-energy-monitor-hardware.html',
  'projects/dc-energy-monitor-evidence.html',
  'about.html'
];

const pageText = {};
SURFACES.forEach((rel) => {
  ok(has(rel), `${rel} is built`);
  if (has(rel)) pageText[rel] = text(read(rel));
});

const everything = Object.values(pageText).join(' ');

/* ---- 1. stale concept-era phrasing --------------------------------------- */
{
  const banned = [
    /no hardware architecture/i,
    /not being claimed yet/i,
    /no simulation or repository/i,
    /those details will be added only after/i,
    /firmware is not written/i,
    /nothing is selected yet/i,
    /no selected parts/i,
    /schematic[^.]{0,40}planned/i,
    /no component (has been|is) selected/i,
    /software is not written/i
  ];
  banned.forEach((rx) => {
    const hit = everything.match(rx);
    ok(!hit, `no page carries the stale claim ${rx}`, hit && hit[0]);
  });
}

/* ---- 2. claims are only allowed when the artefact exists ----------------- */
{
  const artefacts = {
    schematic: 'energy-monitor/hardware/kicad/dcm-hw-v1.kicad_sch',
    erc: 'energy-monitor/hardware/kicad/erc-report.txt',
    netlist: 'energy-monitor/hardware/kicad/netlist-kicad.net',
    firmware: 'energy-monitor/firmware/BUILD-EVIDENCE.md',
    model: 'energy-monitor/model/dcem.js',
    modelTests: 'energy-monitor/tests/dcem-reference.test.js',
    dossier: 'assets/dossier-smart-dc-energy-monitor.pdf',
    manifest: 'energy-monitor/hardware/dcm-hw-v1.manifest.json'
  };
  Object.entries(artefacts).forEach(([name, rel]) => {
    ok(has(rel), `the ${name} artefact exists`, rel);
  });

  /* If a page mentions the schematic, the schematic exists — and vice versa:
     the case study must mention what the project has, or the work is invisible. */
  ok(/KiCad/i.test(pageText['projects/smart-energy-monitoring.html'] || ''),
    'the case study mentions the KiCad design');
  ok(/ERC/i.test(pageText['projects/smart-energy-monitoring.html'] || ''),
    'the case study mentions the electrical rule check');
  ok(/firmware/i.test(pageText['projects/smart-energy-monitoring.html'] || ''),
    'the case study mentions the firmware');
}

/* ---- 3. hardware claims may not outrun the hardware --------------------- */
{
  const prototypeBuilt = /prototype (has been|was) built|prototype complete|board (has been|was) assembled/i.test(everything);
  ok(!prototypeBuilt, 'no page claims a built prototype');

  /* The instrument legitimately says "true and measured values" about its own
     simulated channels, so this targets claims of a hardware result instead. */
  const measurementClaims = [
    /bench (measurement|result|test)s? (show|shows|showed|gave|produces|produced|confirm|confirms|confirmed)/i,
    /measured (accuracy|deviation|error) of [\d.]/i,
    /(we|this project) (measured|bench-tested)/i,
    /measured on the (board|prototype|hardware)/i,
    /accuracy (was|has been) (measured|verified) (at|on|against)/i
  ];
  measurementClaims.forEach(function (rx) {
    const hit = everything.match(rx);
    ok(!hit, 'no page claims a hardware measurement result', hit && hit[0]);
  });

  const calibrated = /calibrated (against|to) (a|the) reference/i.test(everything);
  ok(!calibrated, 'no page claims a completed calibration');

  /* and the negative must actually be stated, not merely omitted */
  const saysNotBuilt = /not (yet )?built|not built|no prototype|prototype does not exist/i.test(everything);
  ok(saysNotBuilt, 'the site states plainly that the prototype is not built');
  const saysNotFlashed = /never flashed|not flashed|has not been (flashed|uploaded)/i.test(everything);
  ok(saysNotFlashed, 'the site states that the firmware was never flashed');
  const saysNotMeasured = /no measurement|not measured|no bench/i.test(everything);
  ok(saysNotMeasured, 'the site states that no measurement exists');
}

/* ---- 4. status is identical on every surface that states it ------------- */
{
  const projects = JSON.parse(read('projects.json'));
  const milestones = projects[0].milestones;
  ok(milestones.length === 8, 'the project publishes eight stages', milestones.length);

  /* the case study renders the status table from this data */
  const cs = read('projects/smart-energy-monitoring.html');
  milestones.forEach((m) => {
    ok(cs.includes(m.status), `the case study shows the status "${m.status}"`, m.name);
  });

  /* the hardware page renders the ladder from the same data */
  const hw = read('projects/dc-energy-monitor-hardware.html');
  milestones.forEach((m) => {
    ok(hw.includes(m.status), `the hardware page shows the status "${m.status}"`, m.name);
  });

  /* the projects index card shows every stage too */
  const idx = read('projects.html');
  milestones.forEach((m) => {
    ok(idx.includes(m.status), `the projects index shows the status "${m.status}"`, m.name);
  });

  /* and the index card's prose is the current prose, not the concept-era text */
  ok(idx.includes(projects[0].results_note.slice(0, 40)),
    'the projects index quotes the current results note');
  ok(!/project track, not a built device/i.test(idx),
    'the projects index no longer describes the project as just a track');

  /* pending stages must actually be pending in the data */
  const pending = milestones.filter((m) => m.state === 'pending').map((m) => m.name);
  ['Physical prototype', 'Calibration', 'Physical validation'].forEach((name) => {
    ok(pending.includes(name), `${name} is recorded as pending`, pending.join(', '));
  });
}

/* ---- 5. the case study links what it describes -------------------------- */
{
  const cs = read('projects/smart-energy-monitoring.html');
  const required = [
    ['/projects/dc-energy-monitor.html', 'the running software model'],
    ['/projects/dc-energy-monitor-hardware.html', 'the hardware design'],
    ['/projects/dc-energy-monitor-evidence.html', 'the evidence hub'],
    ['/energy-monitor/model/dcem.js', 'the model source'],
    ['/energy-monitor/tests/dcem-reference.test.js', 'the reference tests'],
    ['/energy-monitor/hardware/kicad/dcm-hw-v1.kicad_sch', 'the KiCad schematic'],
    ['/energy-monitor/hardware/kicad/erc-report.txt', 'the ERC report'],
    ['/energy-monitor/firmware/BUILD-EVIDENCE.md', 'the firmware build evidence'],
    ['/assets/dossier-smart-dc-energy-monitor.pdf', 'the technical dossier']
  ];
  required.forEach(([href, what]) => {
    ok(cs.includes(href), `the case study links ${what}`, href);
  });
}

/* ---- 6. the evidence hub is honest and complete ------------------------- */
{
  const ev = read('projects/dc-energy-monitor-evidence.html');
  const links = [...new Set([...ev.matchAll(/href="(\/[^"#?]+)"/g)].map((m) => m[1]))]
    .filter((h) => h.startsWith('/energy-monitor/') || h.startsWith('/assets/'));
  ok(links.length >= 20, 'the evidence hub links at least twenty artefacts', links.length);
  links.forEach((href) => {
    ok(has(href.replace(/^\//, '')), `evidence link resolves: ${href}`);
  });
  /* every verified artefact in the hub must exist */
  const verifiedBlocks = ev.split('ev-chip ev-ok').length - 1;
  ok(verifiedBlocks >= 15, 'the hub labels its verified artefacts', verifiedBlocks);
  ok(!/ev-chip ev-warn/.test(ev) || /Untested/.test(ev),
    'any untested label is explained in the legend');
}

/* ---- 7. no duplicate or contradictory status words ---------------------- */
{
  /* "concept" may still appear as the name of a completed stage, but never as
     the description of the project's present state */
  const bad = /(project status|current status)[^.]{0,40}\bconcept\b/i;
  ok(!bad.test(everything), 'no page describes the current status as merely concept',
    (everything.match(bad) || [''])[0]);
  const chip = /In simulation/i.test(pageText['projects.html'] || '');
  ok(!chip, 'the projects index no longer labels the project "in simulation"');
}

if (fails.length) {
  console.log(`content consistency: ${checks - fails.length}/${checks} checks passed`);
  fails.forEach((f) => console.log('  FAIL ' + f));
  process.exit(1);
}
console.log(`PASS: site content consistency — ${checks} checks (no stale claims, claims bound to artefacts, status identical on every surface, hub links resolve)`);
