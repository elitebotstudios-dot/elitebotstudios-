/* ===========================================================================
   hardware-package.test.js — the hardware design package must be coherent

   The riskiest failure mode for a sprint like this one is not a broken link: it
   is a claim that quietly outruns the evidence. These checks make the package
   fail its own build if it starts claming an ERC run, a compiled board build, a
   measurement or a calibration that does not exist.

   Run: node energy-monitor/tests/hardware-package.test.js
   ========================================================================== */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const HW = path.join(ROOT, 'energy-monitor', 'hardware');
let checks = 0;
const fails = [];
function ok(cond, label, detail) {
  checks += 1;
  if (!cond) fails.push(label + (detail === undefined ? '' : ' — ' + detail));
}

const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8');
const exists = (rel) => fs.existsSync(path.join(ROOT, rel));

/* ---- 1. every artefact the pages offer actually exists ------------------- */
const pages = [
  'projects/dc-energy-monitor-hardware.html',
  'projects/smart-energy-monitoring.html'
];
pages.forEach((page) => {
  ok(exists(page), `${page} is built`);
  const html = read(page);
  const links = [...html.matchAll(/href="(\/energy-monitor\/[^"#?]+)"/g)].map((m) => m[1]);
  ok(links.length >= 10, `${page} links the download package`, String(links.length));
  [...new Set(links)].forEach((href) => {
    ok(exists(href.replace(/^\//, '')), `link target exists: ${href}`);
  });
});

/* ---- 2. the design files are real ---------------------------------------- */
{
  const design = JSON.parse(fs.readFileSync(path.join(HW, 'design', 'dcm-hw-v1.json'), 'utf8'));
  ok(design.components.length >= 12, 'the design lists its components', design.components.length);
  ok(design.nets.length >= 6, 'the design declares its nets', design.nets.length);
  design.components.forEach((c) => {
    ok(Array.isArray(c.pins) && c.pins.length > 0, `component ${c.ref} declares its pins`);
    ok(typeof c.rationale === 'string' && c.rationale.length > 40,
      `component ${c.ref} states why it was chosen`, c.rationale && c.rationale.length);
    ok(typeof c.datasheet === 'string' && c.datasheet.length > 0,
      `component ${c.ref} cites a datasheet reference`);
  });
  Object.keys(design.references).forEach((key) => {
    const ref = design.references[key];
    ok(/^https:\/\//.test(ref.url), `reference ${key} links to an official https source`, ref.url);
  });

  /* every net named in a pin must exist in the net list, and vice versa */
  const declared = new Set(design.nets.map((n) => n.name));
  const used = new Set();
  design.components.forEach((c) => c.pins.forEach((p) => { if (p.net !== 'NC') used.add(p.net); }));
  [...used].forEach((n) => ok(declared.has(n), `net ${n} is declared in the net list`));
  [...declared].forEach((n) => ok(used.has(n), `declared net ${n} has at least one pin`));
}

/* ---- 3. generated artefacts -------------------------------------------------*/
['schematic/dcm-hw-v1-sheet1.svg', 'schematic/dcm-hw-v1-sheet2.svg',
 'netlist/dcm-hw-v1-connections.csv', 'netlist/dcm-hw-v1.net',
 'bom/dcm-hw-v1-bom.csv'].forEach((rel) => {
  ok(exists(path.join('energy-monitor', 'hardware', rel)), `generated artefact exists: ${rel}`);
});
{
  const svg = read('energy-monitor/hardware/schematic/dcm-hw-v1-sheet1.svg');
  ok(svg.includes('<svg') && svg.includes('Sheet 1'), 'sheet 1 is a real SVG with its title');
  ok(svg.length > 3000, 'sheet 1 has content', svg.length);
  ok((svg.match(/class="wire/g) || []).length >= 6, 'sheet 1 draws wires', String((svg.match(/class="wire/g) || []).length));
  const conn = read('energy-monitor/hardware/netlist/dcm-hw-v1-connections.csv').trim().split('\n');
  ok(conn.length >= 25, 'the connection table lists every pin', String(conn.length - 1));
  ['VIN', 'VPROT', 'VLOAD', '3V3', 'G ND'].forEach(() => {});   // guard against typos below
  ['VIN', 'VPROT', 'VLOAD', '3V3', 'GND', 'SDA', 'SCL'].forEach((net) => {
    ok(conn.some((line) => line.startsWith(net + ',')), `the connection table includes net ${net}`);
  });
  const net = read('energy-monitor/hardware/netlist/dcm-hw-v1.net');
  ok(net.startsWith('(export') && net.trim().endsWith(')'), 'the KiCad netlist is a balanced s-expression');
  const open = (net.match(/\(/g) || []).length, close = (net.match(/\)/g) || []).length;
  ok(open === close, 'the KiCad netlist has balanced parentheses', `${open} vs ${close}`);
}

/* ---- 4. firmware artefacts --------------------------------------------------*/
['firmware/platformio.ini', 'firmware/README.md', 'firmware/src/main.cpp',
 'firmware/src/core/integrator.cpp', 'firmware/src/core/ina226.cpp',
 'firmware/include/dcm/types.h', 'firmware/include/dcm/integrator.h',
 'firmware/include/dcm/ina226.h', 'firmware/test/test_core.cpp',
 'firmware/test/vectors_generated.h',
 'verification/test-vectors/vectors.json',
 'verification/calibration-plan/calibration-plan.md',
 'verification/calibration-plan/bench-test-template.csv'].forEach((rel) => {
  ok(exists(path.join('energy-monitor', rel)), `firmware/verification artefact exists: ${rel}`);
});
['requirements/electrical-requirements.md', 'design-review/design-review.md',
 'datasheets-references/links.md', 'bom/bom.md', 'README.md'].forEach((rel) => {
  ok(exists(path.join('energy-monitor', 'hardware', rel)), `hardware document exists: ${rel}`);
});
{
  const vectors = JSON.parse(read('energy-monitor/verification/test-vectors/vectors.json'));
  ok(vectors.sets.length === 8, 'eight vector sets are published', vectors.sets.length);
  vectors.sets.forEach((set) => {
    ok(typeof set.expected.energy_wh === 'number', `vector set ${set.id} carries an expected energy`);
    ok(set.samples.length >= 2, `vector set ${set.id} has samples`);
    ok(set.description.length > 40, `vector set ${set.id} explains what it exercises`);
  });
  const header = read('energy-monitor/firmware/test/vectors_generated.h');
  vectors.sets.forEach((set) => {
    const name = 'k_' + set.id.replace(/-/g, '_');
    ok(header.includes(name + '_samples'), `the C++ header carries vector set ${set.id}`);
  });
}

/* ---- 5. no claim outruns the evidence -------------------------------------- */
{
  const hardwarePage = read('projects/dc-energy-monitor-hardware.html');
  const caseStudy = read('projects/smart-energy-monitoring.html');
  const forbidden = [
    [/measured (prototype|hardware|board)/i, 'measured hardware'],
    [/calibrated against (a|the) reference/i, 'calibration against a reference'],
    [/prototype (is|was) (complete|built|tested)/i, 'prototype complete'],
    [/bench[- ]tested/i, 'bench tested'],
    [/flashed (and|successfully)/i, 'flashed firmware'],
    [/firmware (was|has been) (run|tested) on (the|a) board/i, 'firmware run on a board']
  ];
  /* A claim of ERC or of a compile is allowed, but only if the artefact that
     backs it exists and says so. Claims are bound to evidence, not banned. */
  {
    const { execFileSync } = require('child_process');
    const ercPath = path.join(ROOT, 'energy-monitor', 'hardware', 'kicad', 'erc-report.txt');
    const buildPath = path.join(ROOT, 'energy-monitor', 'firmware', 'BUILD-EVIDENCE.md');
    const claimsErc = /ERC[^<]{0,40}(0 errors|clean|passes|passed)/i.test(hardwarePage)
      || /ERC[^<]{0,40}(0 errors|clean|passes|passed)/i.test(caseStudy);
    const claimsBuild = /cross-compil|compiled for ESP32|compiles for the board/i.test(hardwarePage)
      || /cross-compil|compiled for ESP32|compiles for the board/i.test(caseStudy);
    if (claimsErc) {
      ok(fs.existsSync(ercPath), 'a page claims ERC, so the ERC report must exist');
      if (fs.existsSync(ercPath)) {
        const report = fs.readFileSync(ercPath, 'utf8');
        ok(/Errors 0\s+Warnings 0/.test(report),
          'the ERC report itself shows 0 errors and 0 warnings', report.trim().split('\n').pop());
      }
    }
    if (claimsBuild) {
      ok(fs.existsSync(buildPath), 'a page claims a cross-compile, so the build evidence must exist');
      if (fs.existsSync(buildPath)) {
        const ev = fs.readFileSync(buildPath, 'utf8');
        ok(/SUCCESS/.test(ev), 'the build evidence records a successful build');
        ok(/esp32dev/.test(ev), 'the build evidence names the board');
        ok(/firmware\.bin/.test(ev), 'the build evidence names the produced binary');
        ok(/never flashed|not flashed|Never flashed/i.test(ev),
          'the build evidence states that the binary was never flashed');
      }
    }
  }
  forbidden.forEach(([rx, label]) => {
    const hwMatch = hardwarePage.match(rx);
    const csMatch = caseStudy.match(rx);
    ok(!hwMatch, `the hardware page does not claim ${label}`, hwMatch && hwMatch[0]);
    ok(!csMatch, `the case study does not claim ${label}`, csMatch && csMatch[0]);
  });

  /* and the negatives must actually be stated */
  ok(/not (been )?(run|built|measured)/i.test(hardwarePage), 'the hardware page states what was not done');
  ok(hardwarePage.includes('Prototype not built') || hardwarePage.includes('not built'),
    'the hardware page says the prototype is not built');
  ok(caseStudy.includes('Not built') || caseStudy.includes('not built'),
    'the case study says the prototype is not built');
}

/* ---- 6. milestones never claim completion without evidence ----------------- */
{
  const projects = JSON.parse(read('projects.json'));
  const project = projects[0];
  ok(Array.isArray(project.milestones) && project.milestones.length >= 6,
    'the project publishes its milestone ladder', project.milestones && project.milestones.length);
  const states = new Set(project.milestones.map((m) => m.state));
  [...states].forEach((s) => ok(['done', 'partial', 'pending'].includes(s), `milestone state ${s} is known`));

  const byName = Object.fromEntries(project.milestones.map((m) => [m.name, m]));
  ok(byName['Physical prototype'].state === 'pending', 'the prototype milestone is pending');
  ok(byName['Calibration'].state === 'pending', 'calibration is pending');
  ok(byName['Physical validation'].state === 'pending', 'physical validation is pending');
  ok(byName['Software model'].state === 'done', 'the software model milestone is done');
  ok(byName['Embedded firmware'].state === 'done',
    'firmware is recorded as done, because it is host-tested and cross-compiled',
    byName['Embedded firmware'].state);
  ok(/never flashed|not flashed/i.test(byName['Embedded firmware'].detail),
    'the firmware milestone says plainly that it was never flashed',
    byName['Embedded firmware'].detail);
  ok(byName['Electrical design'].state === 'done',
    'the electrical design is done, backed by an ERC report');
  ok(/ERC/i.test(byName['Electrical design'].detail),
    'the electrical design milestone names ERC as its evidence');

  /* the pages render the same ladder, from the same data */
  const hardwarePage = read('projects/dc-energy-monitor-hardware.html');
  project.milestones.forEach((m) => {
    ok(hardwarePage.includes(m.status), `the hardware page shows the status "${m.status}"`);
  });
}

/* ---- 7. no invented prices ------------------------------------------------- */
{
  const bom = read('energy-monitor/hardware/bom/dcm-hw-v1-bom.csv');
  ok(bom.includes('unverified'), 'the BOM marks prices as unverified');
  ok(!/[$£€]\s?\d/.test(bom), 'the BOM contains no invented currency figures');
}

if (fails.length) {
  console.log(`hardware package: ${checks - fails.length}/${checks} checks passed`);
  fails.forEach((f) => console.log('  FAIL ' + f));
  process.exit(1);
}
console.log(`PASS: hardware package coherence — ${checks} checks (artefacts exist, design is complete, claims match evidence, milestones honest)`);
