# -*- coding: utf-8 -*-
"""Build the portfolio homepage from the shared page shell."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build
SRC = str(ROOT / 'index.html')

body = r'''
  <main id="main">
    <section class="hero hero-identity" aria-labelledby="heroTitle">
      <div class="wrap hero-identity-grid">
        <div class="hero-copy">
          <span class="eyebrow">Independent Engineering Initiative · Pakistan</span>
          <h1 id="heroTitle">Engineering ideas into <em>intelligent hardware.</em></h1>
          <p class="hero-sub">Exploring embedded systems, power electronics, and intelligent control through practical engineering, simulation, prototyping, and documented technical work.</p>
          <p class="hero-tagline">Embedded Intelligence. Real-World Power.</p>
          <div class="hero-ctas">
            <a class="btn btn-primary" href="/projects.html">Explore engineering projects <span aria-hidden="true">→</span></a>
            <a class="btn btn-ghost" href="/about.html">Meet the engineer</a>
          </div>
          <p class="hero-note">An evolving portfolio by Muhammad Shahzaib Abbas · Electrical Engineering undergraduate at NUST, Pakistan.</p>
        </div>
        <aside class="hero-aside" aria-label="Portfolio status">
          <div class="identity-mark" aria-hidden="true"><span>EB</span><i></i><i></i><i></i></div>
          <p class="mono-kicker">A practice built in public</p>
          <p>Ideas are not presented as results. Each project records what is known, what remains open, and what evidence has actually been produced.</p>
          <a class="text-link" href="/lab.html">Read the engineering lab <span aria-hidden="true">↗</span></a>
        </aside>
      </div>
    </section>

    <section class="section focus-section" aria-labelledby="focusTitle">
      <div class="wrap">
        <div class="section-head">
          <span class="label">Engineering focus</span>
          <h2 id="focusTitle">A connected set of disciplines.</h2>
          <p>These are areas of study and exploration—not proficiency claims. Demonstrated work is linked from the portfolio as it becomes available.</p>
        </div>
        <div class="focus-grid">
          <article class="focus-card"><span class="card-num">01 / COMPUTE</span><h3>Embedded systems</h3><p>Microcontrollers, firmware structure, peripheral interfaces, timing, and device-level control.</p></article>
          <article class="focus-card"><span class="card-num">02 / CONVERT</span><h3>Power electronics</h3><p>Power conversion, switching behaviour, regulation, energy flow, and control-oriented models.</p></article>
          <article class="focus-card"><span class="card-num">03 / CONNECT</span><h3>Electronics &amp; PCB</h3><p>Circuits, component choices, schematic design, board layout, signal integrity, and validation.</p></article>
          <article class="focus-card"><span class="card-num">04 / CONTROL</span><h3>Control &amp; instrumentation</h3><p>Measurement chains, feedback, signal conditioning, actuation, and system response.</p></article>
          <article class="focus-card"><span class="card-num">05 / COMMUNICATE</span><h3>IoT &amp; energy systems</h3><p>Connected hardware and monitoring concepts where embedded control meets electrical energy.</p></article>
        </div>
        <a class="text-link" href="/expertise.html">See the learning map and evidence labels <span aria-hidden="true">→</span></a>
      </div>
    </section>

    <section class="section system-section" aria-labelledby="systemTitle">
      <div class="wrap">
        <div class="section-head">
          <span class="label">Interactive concept · educational diagram</span>
          <h2 id="systemTitle">A small system, seen as a whole.</h2>
          <p>Select a block to explore its role in a generic low-voltage embedded power system. This is a conceptual teaching diagram, not a prototype or measured design.</p>
        </div>
        <div class="system-shell">
          <div class="system-flow" role="group" aria-label="Conceptual embedded power system blocks">
            <button class="system-node is-active" type="button" data-system-node="source" aria-pressed="true" aria-controls="systemDetail"><span class="node-index">01</span><b>Power source</b><small>Input energy</small></button>
            <span class="system-link" aria-hidden="true"><svg viewBox="0 0 54 14"><path d="M1 7h45m-7-6 7 6-7 6"/></svg></span>
            <button class="system-node" type="button" data-system-node="converter" aria-pressed="false" aria-controls="systemDetail"><span class="node-index">02</span><b>DC–DC stage</b><small>Conversion</small></button>
            <span class="system-link" aria-hidden="true"><svg viewBox="0 0 54 14"><path d="M1 7h45m-7-6 7 6-7 6"/></svg></span>
            <button class="system-node" type="button" data-system-node="controller" aria-pressed="false" aria-controls="systemDetail"><span class="node-index">03</span><b>Controller</b><small>Measure · decide</small></button>
            <span class="system-link" aria-hidden="true"><svg viewBox="0 0 54 14"><path d="M1 7h45m-7-6 7 6-7 6"/></svg></span>
            <button class="system-node" type="button" data-system-node="sensing" aria-pressed="false" aria-controls="systemDetail"><span class="node-index">04</span><b>Sensing &amp; load</b><small>Feedback · output</small></button>
          </div>
          <div class="system-detail" id="systemDetail" tabindex="-1" aria-live="polite" aria-atomic="true">
            <span class="mono-kicker" id="systemDetailKicker">01 / SOURCE</span>
            <h3 id="systemDetailTitle">Start with the energy boundary.</h3>
            <p id="systemDetailText">A design begins by defining its input: voltage range, available power, expected transients, and the source's limits. Those constraints shape every block downstream.</p>
          </div>
          <p class="system-footnote"><span aria-hidden="true">↳</span> Generic functional blocks only. No component values, ratings, or operating results are implied.</p>
        </div>
      </div>
    </section>

    <section class="section project-preview" aria-labelledby="projectPreviewTitle">
      <div class="wrap">
        <div class="section-head section-head-row">
          <div><span class="label">Portfolio</span><h2 id="projectPreviewTitle">Evidence before adjectives.</h2><p>Project status is explicit. Concepts and unfinished work are not presented as completed engineering.</p></div>
          <a class="text-link" href="/projects.html">All projects <span aria-hidden="true">→</span></a>
        </div>
        <div id="featuredProject" aria-live="polite">
          <article class="featured-project">
            <div class="featured-project-mark" aria-hidden="true"><svg viewBox="0 0 120 96"><path d="M10 48h22m56 0h22M32 24h56v48H32zM46 36v24m14-24v24m14-24v24M4 20h16v56H4m80-56h16v56H84"/><circle cx="60" cy="48" r="4"/></svg></div>
            <div><div class="post-meta"><span class="status-label">Concept · not a prototype</span><span>Energy systems</span></div><h3>Smart energy monitoring</h3><p>A planned exploration of how embedded measurement and electrical energy data can work together. Hardware choices, architecture, and validation plan are not yet published.</p><a class="text-link" href="/projects.html">See the current project record <span aria-hidden="true">→</span></a></div>
          </article>
        </div>
      </div>
    </section>

    <section class="section method-section" aria-labelledby="methodTitle">
      <div class="wrap">
        <div class="section-head"><span class="label">Engineering method</span><h2 id="methodTitle">Design → simulate → prototype → measure → improve.</h2><p>A repeatable loop for turning an engineering question into a reviewable result. Every stage can expose an assumption worth revisiting.</p></div>
        <ol class="method-loop">
          <li><span>01</span><b>Design</b><small>Requirements &amp; model</small></li><li><span>02</span><b>Simulate</b><small>Assumptions made visible</small></li><li><span>03</span><b>Prototype</b><small>Build the smallest test</small></li><li><span>04</span><b>Measure</b><small>Record conditions &amp; data</small></li><li><span>05</span><b>Improve</b><small>Document the next revision</small></li>
        </ol>
      </div>
    </section>

    <section class="section profile-preview" aria-labelledby="profileTitle">
      <div class="wrap profile-preview-inner">
        <div class="profile-monogram" aria-hidden="true">MSA<span>EE · NUST</span></div>
        <div><span class="label">The engineer behind the studio</span><h2 id="profileTitle">Muhammad Shahzaib Abbas</h2><p>Electrical Engineering undergraduate at NUST, Pakistan, with an academic focus in power engineering and growing interests in embedded systems, electronics, and control.</p><p class="muted-small">An undergraduate profile—not a claim of graduate status, professional licensure, or industry experience.</p><a class="text-link" href="/about.html">Read the background and research interests <span aria-hidden="true">→</span></a></div>
      </div>
    </section>

    <section class="section lab-preview" aria-labelledby="labPreviewTitle">
      <div class="wrap">
        <div class="section-head section-head-row"><div><span class="label">Engineering Lab</span><h2 id="labPreviewTitle">Notes, models, and questions.</h2><p>A technical notebook for documenting learning and design decisions without inventing bench evidence.</p></div><a class="text-link" href="/lab.html">Visit the lab <span aria-hidden="true">→</span></a></div>
        <div class="lab-preview-grid"><a class="post-card" href="/lab/why-document-the-process.html"><span class="post-meta">Practice &amp; principles</span><h3>Why document the process?</h3><p>How to make project status, assumptions, and evidence legible to another engineer.</p></a><a class="post-card" href="/lab/simulation-is-not-measurement.html"><span class="post-meta">Simulation &amp; validation</span><h3>Simulation is a model, not a measurement</h3><p>Separate a model's output from what a real circuit does under stated test conditions.</p></a></div>
      </div>
    </section>

    <section class="section collaboration-section" aria-labelledby="collabTitle"><div class="wrap collaboration-card"><span class="label">Connect &amp; collaborate</span><h2 id="collabTitle">Interested in the work?</h2><p>Open to thoughtful technical conversations, academic and research discussions, and appropriately scoped low-voltage engineering collaborations. Any engagement is discussed against demonstrated experience and relevant supervision.</p><a class="btn btn-primary" href="/contact.html">Let's connect <span aria-hidden="true">→</span></a></div></section>
  </main>
'''

html = build.head(
    'Elite Bot Studios — Embedded Intelligence. Real-World Power.',
    'An independent engineering initiative by Muhammad Shahzaib Abbas, an Electrical Engineering undergraduate at NUST, Pakistan, exploring embedded systems, power electronics, intelligent hardware, and control.',
    '/', jsonld=build.SCHEMA_GRAPH)
html += build.header('/') + body + build.footer()
open(SRC, 'w', encoding='utf-8').write(html)
print('index.html rebuilt:', len(html), 'bytes')
