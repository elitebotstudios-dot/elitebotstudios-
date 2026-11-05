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

  /* close when the pointer goes down outside the menu and the toggle */
  document.addEventListener('pointerdown', function (e) {
    if (menu.getAttribute('data-open') !== 'true') return;
    if (menu.contains(e.target) || toggle.contains(e.target)) return;
    setOpen(false);
  });

  /* a tap on the page background should also dismiss it on touch devices */
  document.addEventListener('click', function (e) {
    if (menu.getAttribute('data-open') !== 'true') return;
    if (menu.contains(e.target) || toggle.contains(e.target)) return;
    setOpen(false);
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
var PROJECT_STATUS_CLASS = {
  'concept': 'chip-amber', 'simulation': 'chip-amber', 'design-completed': 'chip-amber',
  'prototype-in-progress': 'chip-amber', 'bench-tested': 'chip-teal', 'complete': 'chip-teal'
};
var PROJECT_STATUS_LABEL = {
  'concept': 'Concept', 'simulation': 'In simulation', 'design-completed': 'Design completed',
  'prototype-in-progress': 'Prototype in progress', 'bench-tested': 'Bench tested', 'complete': 'Completed'
};

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
  return '<div><dt>Hardware / BOM</dt><ul class="bom">' + items.map(function (b) {
    if (typeof b === 'string') return '<li><span>' + ebsEsc(b) + '</span></li>';
    return '<li><span>' + ebsEsc(b.part || '') + '</span><span>' + ebsEsc(b.detail || '') + '</span></li>';
  }).join('') + '</ul></div>';
}

function ebsList(label, items) {
  if (!items || !items.length) return '';
  return '<div><dt>' + label + '</dt><dd>' + items.map(ebsEsc).join(' · ') + '</dd></div>';
}

function ebsProjectCard(p) {
  var tags = (p.tags || []).map(function (t) { return '<span class="chip">' + ebsEsc(t) + '</span>'; }).join('');
  var links = '';
  function safeLink(url) {
    return typeof url === 'string' && (/^https:\/\//i.test(url) || /^\/(?!\/)/.test(url));
  }
  var source = p.github_url || p.firmware_repo;
  if (source && safeLink(source)) {
    links += '<a class="btn btn-ghost" href="' + ebsEsc(source) + '" rel="noopener noreferrer">Source</a>';
  }
  if (p.documentation_url && safeLink(p.documentation_url)) {
    links += '<a class="btn btn-ghost" href="' + ebsEsc(p.documentation_url) + '" rel="noopener noreferrer">Documentation</a>';
  }
  if (p.case_study_url && safeLink(p.case_study_url)) {
    links += '<a class="btn btn-ghost" href="' + ebsEsc(p.case_study_url) + '">Read case study</a>';
  }

  var anchor = /^[a-z0-9-]+$/.test(p.slug || '') ? ' id="' + p.slug + '"' : '';
  return '<article class="card proj-card reveal"' + anchor + '>'+
    '<div class="post-meta">' +
      '<span class="chip ' + (PROJECT_STATUS_CLASS[p.status] || '') + '">' +
        ebsEsc(PROJECT_STATUS_LABEL[p.status] || p.status || '') + '</span>' +
      '<span>' + ebsEsc(p.category || p.date || '') + '</span>' +
    '</div>' +
    '<h3>' + ebsEsc(p.title) + '</h3>' +
    '<dl class="proj-body" style="margin:0">' +
      ebsBlock('Objective', p.objective) +
      ebsBlock('Context', p.problem) +
      ebsBlock('Approach', p.approach) +
      ebsList('Hardware', p.hardware) + ebsBom(p.bom) +
      ebsList('Software', p.software) +
      ebsBlock('Simulation', p.simulation) +
      ebsBlock('Evidence', p.measured_results || p.results || p.results_note) +
      ebsBlock('Lessons', p.lessons) +
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

  /* Shipped visible. If the fetch fails, this honest "no builds yet" state is
     what the visitor sees — an empty grid with no explanation was the old
     behaviour and it was wrong. */
  var EMPTY = document.getElementById('projectsEmpty');

  function afterInject() {
    if (location.hash) {
      var target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target && target.scrollIntoView) setTimeout(function () { target.scrollIntoView(); }, 0);
    }
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

/* ----------------------------------------------------- homepage project --
   Reuses the same verified project data as the Projects page. The server-rendered
   static concept card remains as the no-JavaScript fallback. */
(function homeProject() {
  var mount = document.getElementById('featuredProject');
  if (!mount) return;
  fetch('/projects.json', { cache: 'no-cache' }).then(function (r) {
    if (!r.ok) throw new Error(String(r.status));
    return r.json();
  }).then(function (list) {
    if (!Array.isArray(list) || !list.length) return;
    var p = list[0];
    var status = PROJECT_STATUS_LABEL[p.status] || 'In development';
    var summary = p.summary || p.objective || p.problem || 'Project details will be published when evidence is available.';
    var slug = /^[a-z0-9-]+$/.test(p.slug || '') ? p.slug : '';
    mount.innerHTML = '<article class="featured-project">' +
      '<div class="featured-project-mark" aria-hidden="true"><svg viewBox="0 0 120 96"><path d="M10 48h22m56 0h22M32 24h56v48H32zM46 36v24m14-24v24m14-24v24M4 20h16v56H4m80-56h16v56H84"/><circle cx="60" cy="48" r="4"/></svg></div>' +
      '<div><div class="post-meta"><span class="status-label">' + ebsEsc(status) + '</span><span>' + ebsEsc(p.category || 'Project track') + '</span></div>' +
      '<h3>' + ebsEsc(p.title || 'Project record') + '</h3><p>' + ebsEsc(summary) + '</p>' +
      '<a class="text-link" href="/projects.html' + (slug ? '#' + slug : '') + '">See the project record <span aria-hidden="true">→</span></a></div></article>';
  }).catch(function () { /* retain the accessible static fallback */ });
}());

/* -------------------------------------------------- conceptual system map --
   A small, accessible interaction: each button describes a generic block in
   the educational power-system diagram. No device behaviour is simulated. */
(function systemMap() {
  var root = document.querySelector('.system-flow');
  var title = document.getElementById('systemDetailTitle');
  var text = document.getElementById('systemDetailText');
  var kicker = document.getElementById('systemDetailKicker');
  if (!root || !title || !text || !kicker) return;
  var content = {
    source: ['01 / SOURCE', 'Start with the energy boundary.', 'A design begins by defining its input: voltage range, available power, expected transients, and the source’s limits. Those constraints shape every block downstream.'],
    converter: ['02 / CONVERSION', 'Condition power for the system.', 'A DC–DC stage converts one DC voltage range to another. Topology, switching, component stresses, thermal limits, and regulation requirements depend on the actual source and load; this diagram assigns no ratings or values.'],
    controller: ['03 / CONTROL', 'Measure, decide, and command.', 'An embedded controller can sample signals, run control logic, and generate outputs such as PWM. Real designs must account for timing, isolation where required, startup, fault states, and safe defaults.'],
    sensing: ['04 / FEEDBACK & LOAD', 'Close the loop with measured behaviour.', 'Sensors and signal conditioning provide information about system state; the load is where useful output is delivered. Measurement range, accuracy, protection, and bandwidth must be chosen for a specific design.']
  };
  root.addEventListener('click', function (event) {
    var button = event.target.closest('[data-system-node]');
    if (!button || !root.contains(button)) return;
    var next = content[button.getAttribute('data-system-node')];
    if (!next) return;
    root.querySelectorAll('[data-system-node]').forEach(function (node) {
      var active = node === button;
      node.classList.toggle('is-active', active);
      node.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
    kicker.textContent = next[0];
    title.textContent = next[1];
    text.textContent = next[2];
  });
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
