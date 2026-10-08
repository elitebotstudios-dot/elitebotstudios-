/* Functional check that projects.json actually drives the Projects page.
   Runs the real renderer from assets/site.js against the real JSON.
   Usage: node tests/projects.test.js                                   */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.resolve(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'projects.json'), 'utf8'));

/* minimal browser stubs: enough for site.js to load without throwing */
function stubEl() {
  return {
    addEventListener() {}, setAttribute() {}, getAttribute() { return null; },
    querySelectorAll() { return []; }, querySelector() { return null; },
    classList: { add() {} }, style: { setProperty() {} }, elements: [],
    appendChild() {}, closest() { return null; }
  };
}
const doc = {
  getElementById() { return null; },
  querySelectorAll() { return []; },
  addEventListener() {},
  createElement() { return stubEl(); }
};
const sandbox = {
  window: {}, document: doc, location: { pathname: '/' },
  navigator: {}, console,
  matchMedia: () => ({ matches: false, addEventListener() {} }),
  IntersectionObserver: undefined,
  fetch: () => Promise.reject(new Error('no network in test'))
};
sandbox.window.matchMedia = sandbox.matchMedia;
sandbox.window.document = doc;
sandbox.window.IntersectionObserver = undefined;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root, 'assets/site.js'), 'utf8'), sandbox);

const render = sandbox.window.EBS && sandbox.window.EBS.renderProjectCard;
if (typeof render !== 'function') { console.error('FAIL: renderer not exposed'); process.exit(1); }

/* ---------- the checks ---------- */
let fail = 0;
function ok(label, cond, extra) {
  console.log((cond ? '  PASS  ' : '  FAIL  ') + label + (extra ? '  → ' + extra : ''));
  if (!cond) fail++;
}

console.log('projects.json → Projects page\n');
ok('projects.json parses as an array', Array.isArray(data));
ok('at least one entry present', data.length > 0, data.length + ' entry');

const need = ['slug', 'title', 'status', 'problem', 'approach', 'date'];
data.forEach(function (p, i) {
  const missing = need.filter(function (k) { return !p[k]; });
  ok('entry ' + i + ' "' + (p.slug || '?') + '" has required fields', missing.length === 0,
     missing.length ? 'missing ' + missing.join(', ') : '');
  ok('entry ' + i + ' status is a known value',
     ['in-progress', 'complete'].indexOf(p.status) !== -1, p.status);
  const html = render(p);
  ok('entry ' + i + ' renders non-empty HTML', html.length > 200, html.length + ' chars');
  ok('entry ' + i + ' shows its title', html.indexOf(p.title) !== -1);
  ok('entry ' + i + ' shows the status chip',
     html.indexOf(p.status === 'in-progress' ? 'chip-amber' : 'chip-teal') !== -1);
  ok('entry ' + i + ' renders the problem text', html.indexOf(p.problem.slice(0, 30)) !== -1);
  if (p.results) ok('entry ' + i + ' shows results', html.indexOf(p.results.slice(0, 20)) !== -1);
  else if (p.results_note) ok('entry ' + i + ' shows the pending-results note',
     html.indexOf(p.results_note.slice(0, 20)) !== -1);
  ok('entry ' + i + ' tags escaped, no raw angle brackets',
     !/<\/?script/i.test(html));
});

/* ---------- dummy entry, exactly as Section 8 asks ---------- */
const dummy = {
  slug: 'zz-dummy-acceptance-test', title: 'ZZ Dummy Acceptance Test', status: 'complete',
  tags: ['test'], problem: 'Dummy problem text for the acceptance check.',
  approach: 'Dummy approach text.', bom: [{ part: 'Dummy part', detail: 'detail' }],
  firmware_repo: 'https://example.com/repo', media: [], results: 'Dummy measured result.',
  date: '2026-10'
};
const dhtml = render(dummy);
console.log('\ndummy entry injected:');
ok('dummy card renders', dhtml.length > 200);
ok('dummy shows its title', dhtml.indexOf(dummy.title) !== -1);
ok('dummy gets the teal COMPLETE chip', dhtml.indexOf('chip-teal') !== -1 && dhtml.indexOf('Complete') !== -1);
ok('dummy renders a BOM row', dhtml.indexOf('Dummy part') !== -1);
ok('dummy renders a Source button for firmware_repo', dhtml.indexOf('https://example.com/repo') !== -1);

/* XSS guard: a hostile title must not produce live markup */
const evil = Object.assign({}, dummy, { title: '<img src=x onerror=alert(1)>' });
const ehtml = render(evil);
ok('hostile title is escaped', ehtml.indexOf('<img') === -1, 'no raw <img> emitted');

console.log('\n' + (fail ? fail + ' CHECK(S) FAILED' : 'ALL CHECKS PASSED'));
process.exit(fail ? 1 : 0);
