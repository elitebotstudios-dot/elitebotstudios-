/* ==========================================================================
   Elite Bot Studios — shared page behaviour
   Nav menu, scroll reveal, and the project grid. No dependencies.
   ========================================================================== */
'use strict';

/* ------------------------------------------------------------------ nav -- */
(function nav() {
  var toggle = document.getElementById('navToggle');
  var menu = document.getElementById('mobileMenu');
  if (!toggle || !menu) return;

  function setOpen(open) {
    menu.setAttribute('data-open', open ? 'true' : 'false');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  }

  toggle.addEventListener('click', function () {
    setOpen(menu.getAttribute('data-open') !== 'true');
  });
  menu.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') setOpen(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setOpen(false);
  });
  window.addEventListener('resize', function () {
    if (window.innerWidth > 900) setOpen(false);
  });

  /* mark the current section for assistive tech */
  var here = location.pathname.replace(/\/index\.html$/, '/').replace(/\/$/, '');
  Array.prototype.forEach.call(document.querySelectorAll('.nav-links a, .mobile-menu a'), function (a) {
    if ((a.getAttribute('href') || '').replace(/\/$/, '') === here) a.setAttribute('aria-current', 'page');
  });
}());

/* --------------------------------------------------------------- reveal -- */
(function reveal() {
  var items = document.querySelectorAll('.reveal');
  if (!items.length) return;

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(items, function (el) { el.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  Array.prototype.forEach.call(items, function (el) { io.observe(el); });
}());

/* ------------------------------------------------- project card renderer --
   Top level rather than hidden inside the page bootstrap, for two reasons:
   the grid must render whether or not the fetch succeeds, and
   tests/projects.test.js exercises exactly this code path.
   -------------------------------------------------------------------------- */
var PROJECT_STATUS_CLASS = { 'in-progress': 'chip-amber', 'complete': 'chip-teal' };
var PROJECT_STATUS_LABEL = { 'in-progress': 'In progress', 'complete': 'Complete' };

function ebsEsc(v) {
  return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}

function ebsBlock(label, value) {
  if (!value) return '';
  return '<div><dt>' + label + '</dt><dd>' + ebsEsc(value) + '</dd></div>';
}

function ebsBom(items) {
  if (!items || !items.length) return '';
  return '<div><dt>BOM</dt><ul class="bom">' + items.map(function (b) {
    if (typeof b === 'string') return '<li><span>' + ebsEsc(b) + '</span></li>';
    return '<li><span>' + ebsEsc(b.part || '') + '</span><span>' + ebsEsc(b.detail || '') + '</span></li>';
  }).join('') + '</ul></div>';
}

function ebsProjectCard(p) {
  var tags = (p.tags || []).map(function (t) { return '<span class="chip">' + ebsEsc(t) + '</span>'; }).join('');
  var links = '';
  if (p.firmware_repo) {
    links += '<a class="btn btn-ghost" href="' + ebsEsc(p.firmware_repo) + '" rel="noopener">Source</a>';
  }
  if (p.owner_todo) {
    links += '<span class="todo" data-owner="TODO">' + ebsEsc(p.owner_todo) + '</span>';
  }

  return '<article class="card proj-card reveal">' +
    '<div class="post-meta">' +
      '<span class="chip ' + (PROJECT_STATUS_CLASS[p.status] || '') + '">' +
        ebsEsc(PROJECT_STATUS_LABEL[p.status] || p.status || '') + '</span>' +
      '<span>' + ebsEsc(p.date || '') + '</span>' +
    '</div>' +
    '<h3>' + ebsEsc(p.title) + '</h3>' +
    '<dl class="proj-body" style="margin:0">' +
      ebsBlock('Problem', p.problem) +
      ebsBlock('Approach', p.approach) +
      ebsBom(p.bom) +
      ebsBlock('Firmware', p.firmware_note) +
      ebsBlock('Results', p.results || p.results_note) +
    '</dl>' +
    (tags ? '<div class="chips">' + tags + '</div>' : '') +
    (links ? '<div class="proj-links">' + links + '</div>' : '') +
  '</article>';
}

window.EBS = window.EBS || {};
window.EBS.renderProjectCard = ebsProjectCard;

/* --------------------------------------------------------- projects page -- */
(function projects() {
  var mount = document.getElementById('projectsGrid');
  if (!mount) return;

  var EMPTY = document.getElementById('projectsEmpty');

  function afterInject() {
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var cards = mount.querySelectorAll('.reveal');
    if (reduce || !('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(cards, function (el) { el.classList.add('in'); });
      return;
    }
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    Array.prototype.forEach.call(cards, function (el, i) {
      el.style.setProperty('--d', (i * 60) + 'ms');
      io.observe(el);
    });
  }

  fetch('/projects.json', { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
    .then(function (list) {
      if (!Array.isArray(list) || !list.length) return;
      mount.innerHTML = list.map(ebsProjectCard).join('');
      if (EMPTY) EMPTY.hidden = true;
      afterInject();
    })
    .catch(function () { /* keep the server-rendered fallback state */ });
}());

/* ------------------------------------------------------------------ PWA --
   Register the service worker so the new cache version replaces whatever is
   already installed in a returning visitor's browser. Without this, an older
   worker stays active indefinitely and keeps serving its own cached copy.
   Deferred to load so it never competes with first paint.
   -------------------------------------------------------------------------- */
(function serviceWorker() {
  if (!('serviceWorker' in navigator)) return;
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/sw.js').catch(function () {
      /* registration is an enhancement — a failure must not surface */
    });
  });
}());
