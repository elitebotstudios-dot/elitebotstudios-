# -*- coding: utf-8 -*-
"""Build the flagship homepage and inline its original conceptual system artwork."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build

svg=(ROOT/'assets/system-study.svg').read_text(encoding='utf-8')
body=r'''
<main id="main">
  <section class="flagship" aria-labelledby="heroTitle">
    <div class="flagship-grain" aria-hidden="true"></div>
    <div class="wrap flagship-wrap">
      <div class="hero-meta"><span class="eyebrow">Elite Bot Studios <i>·</i> Engineering Study 01</span><span class="hero-meta-right">PAKISTAN <b> / </b> 2026</span></div>
      <div class="flagship-grid">
        <div class="flagship-copy">
          <p class="hero-kicker"><span></span> Embedded Intelligence. Real-World Power.</p>
          <h1 id="heroTitle">Where power<br>meets <em>embedded</em><br>intelligence.</h1>
          <p class="flagship-lede">Embedded systems, power electronics, and intelligent control—explored as one engineering system.</p>
          <div class="hero-ctas">
            <a class="btn btn-primary" href="/projects.html">Explore projects <span aria-hidden="true">↗</span></a>
            <a class="btn btn-ghost" href="/lab.html">Open the Engineering Lab</a>
          </div>
          <div class="hero-identity-line"><span>MUHAMMAD SHAHZAIB ABBAS</span><i></i><span>ELECTRICAL ENGINEERING · NUST</span></div>
        </div>
        <figure class="hero-machine">
          <div class="machine-head"><span class="machine-live"><i></i> SYSTEM STUDY / CONCEPT</span><span class="machine-ref">EB—01 <b>·</b> ARCHITECTURE</span></div>
          <div class="machine-art" aria-label="Interactive conceptual illustration of an embedded power-control system">
            SVG_HERO_ART
          </div>
          <figcaption class="machine-caption"><span>Illustrative architecture</span><span>Not a fabricated board or test result</span></figcaption>
        </figure>
      </div>
      <div class="hero-system-console">
        <div class="console-intro"><span class="console-index">01—04</span><span>Explore system blocks</span><span class="console-hint">SELECT TO INSPECT</span></div>
        <div class="system-tabs" role="tablist" aria-label="Explore system blocks">
          <button class="system-tab is-active" id="tabSource" type="button" role="tab" aria-selected="true" aria-controls="systemPanel" tabindex="0" data-system-node="source"><span>01</span>Power input</button>
          <button class="system-tab" id="tabConverter" type="button" role="tab" aria-selected="false" aria-controls="systemPanel" tabindex="-1" data-system-node="converter"><span>02</span>Conversion</button>
          <button class="system-tab" id="tabController" type="button" role="tab" aria-selected="false" aria-controls="systemPanel" tabindex="-1" data-system-node="controller"><span>03</span>Embedded control</button>
          <button class="system-tab" id="tabFeedback" type="button" role="tab" aria-selected="false" aria-controls="systemPanel" tabindex="-1" data-system-node="feedback"><span>04</span>Feedback</button>
        </div>
        <div class="system-explanation" id="systemPanel" role="tabpanel" aria-labelledby="tabSource" tabindex="0" aria-live="polite" aria-atomic="true">
          <div class="system-explanation-title"><span id="systemDetailKicker">01 / ENERGY BOUNDARY</span><h2 id="systemDetailTitle">Start with what the source can provide.</h2></div>
          <p id="systemDetailText">Input range, available power, and transients define the conditions every later block must respect. Those are design constraints—not decorative numbers.</p>
        </div>
        <div class="console-foot"><span>CONCEPTUAL SYSTEM · EDUCATIONAL USE</span><span>POWER <i>→</i> CONTROL <i>→</i> RESPONSE</span></div>
      </div>
    </div>
    <a class="scroll-cue" href="#focus" aria-label="Scroll to explore"><span></span>SCROLL TO EXPLORE</a>
  </section>

  <section class="section discipline-section" id="focus" aria-labelledby="focusTitle">
    <div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">A / DISCIPLINES</span><h2 id="focusTitle">One system.<br><em>Five lenses.</em></h2></div><p>Power becomes useful when electronics, computation, measurement, and control are designed together. These are the fields this studio studies and connects.</p></div>
      <div class="discipline-layout">
        <article class="discipline-card discipline-card-main"><span class="discipline-no">01</span><div class="discipline-graphic graphic-embedded" aria-hidden="true"><svg viewBox="0 0 360 220"><path d="M180 20v46M180 154v46M50 110h50m160 0h50M90 42l36 36m108 68 36 36M270 42l-36 36m-108 68-36 36"/><rect x="113" y="65" width="134" height="90" rx="8"/><path d="M132 85h36v50h-36zm54 0h42v8h-42zm0 19h42v8h-42zm0 19h29v8h-29z"/><circle cx="180" cy="110" r="3"/></svg></div><div><span class="discipline-tag">COMPUTE</span><h3>Embedded systems</h3><p>Firmware, microcontrollers, digital interfaces, and the logic that makes hardware respond.</p></div><a href="/expertise.html#embedded" aria-label="Explore embedded systems expertise">↗</a></article>
        <article class="discipline-card"><span class="discipline-no">02</span><div class="discipline-graphic graphic-power" aria-hidden="true"><svg viewBox="0 0 240 150"><path d="M20 77h40m120 0h40M60 42h44v70H60zm76 0h44v70h-44z"/><path d="M70 77h13l8-20 15 41 13-41 14 20h13m-89-56v-15m88 15v-15m-88 126v15m88-15v15"/></svg></div><div><span class="discipline-tag">CONVERT</span><h3>Power electronics</h3><p>Switching, regulation, energy flow, and converter behavior.</p></div><a href="/expertise.html#power" aria-label="Explore power electronics expertise">↗</a></article>
        <article class="discipline-card"><span class="discipline-no">03</span><div class="discipline-graphic graphic-pcb" aria-hidden="true"><svg viewBox="0 0 240 150"><path d="M35 28h170v94H35zM50 45h44v35H50zm95-5h42v42h-42zM72 80v24h44m21-27v27h48"/><circle cx="57" cy="108" r="4"/><circle cx="194" cy="108" r="4"/><path d="M94 62h20m-7-7 7 7-7 7"/></svg></div><div><span class="discipline-tag">CONNECT</span><h3>Electronics &amp; PCB</h3><p>Circuit ideas translated into schematic and board-level structure.</p></div><a href="/expertise.html#electronics" aria-label="Explore electronics and PCB expertise">↗</a></article>
        <article class="discipline-card"><span class="discipline-no">04</span><div class="discipline-graphic graphic-control" aria-hidden="true"><svg viewBox="0 0 240 150"><path d="M28 76h38l18-31 30 62 25-54 19 23h54"/><path d="M66 30v92m0-46h106m0-34v68"/><circle cx="66" cy="76" r="6"/><circle cx="172" cy="76" r="6"/></svg></div><div><span class="discipline-tag">MEASURE</span><h3>Control &amp; instrumentation</h3><p>Feedback, sensing, signal conditioning, and system response.</p></div><a href="/expertise.html#control" aria-label="Explore control and instrumentation expertise">↗</a></article>
        <article class="discipline-card discipline-card-wide"><span class="discipline-no">05</span><div class="discipline-graphic graphic-energy" aria-hidden="true"><svg viewBox="0 0 280 150"><path d="M24 76h54l24-24 31 48 27-48 26 24h70"/><circle cx="24" cy="76" r="5"/><circle cx="256" cy="76" r="5"/><path d="M57 47v58m164-58v58"/></svg></div><div><span class="discipline-tag">OBSERVE</span><h3>Connected energy systems</h3><p>Where embedded computation meets electrical measurement, monitoring, and future intelligent-energy applications.</p></div><a href="/expertise.html#energy" aria-label="Explore intelligent energy systems">↗</a></article>
      </div>
      <div class="section-tail"><span>AREAS OF STUDY &amp; EXPLORATION</span><a class="text-link" href="/expertise.html">Open the capability map <b>↗</b></a></div>
    </div>
  </section>

  <section class="section explorer-teaser" aria-labelledby="explorerTitle">
    <div class="wrap explorer-teaser-grid">
      <div class="explorer-copy"><span class="section-index">B / ENGINEERING PLAYGROUND</span><h2 id="explorerTitle">Make the model<br><em>move.</em></h2><p>Change converter inputs. Watch the ideal CCM estimate update, then inspect where the model stops being valid.</p><div class="explorer-tags"><span>IDEAL CCM</span><span>LIVE WAVEFORMS</span><span>NO API</span></div><a class="btn btn-primary" href="/tools/buck-converter.html">Open the buck converter explorer <span aria-hidden="true">↗</span></a></div>
      <div class="explorer-preview" aria-label="Static preview of the interactive buck-converter model"><div class="preview-top"><span>BUCK / CONTINUOUS CONDUCTION</span><span>MODEL PREVIEW</span></div><svg viewBox="0 0 620 270" aria-hidden="true"><path class="preview-gridline" d="M56 38h526M56 80h526M56 122h526M56 164h526M56 206h526M100 24v198m100-198v198m100-198v198m100-198v198m100-198v198"/><path class="preview-gate" d="M58 94V52h185v42h380"/><path class="preview-current" d="M58 192 243 146 428 192 613 146"/><path class="preview-mark" d="M243 36v180"/><text x="74" y="47">SWITCH NODE</text><text x="75" y="136">INDUCTOR CURRENT</text><text x="252" y="58">D·T</text><text x="520" y="250">TIME →</text></svg><div class="preview-values"><div><small>IDEAL DUTY</small><b>VOUT / VIN</b></div><div><small>RIPPLE MODEL</small><b>ΔIL · L · FSW</b></div><div><small>STATUS</small><b>CCM / DCM BOUNDARY</b></div></div><p class="preview-note">Illustrative axes; the interactive page plots from your selected inputs. No simulated measurements are shown here.</p></div>
    </div>
  </section>

  <section class="section portfolio-section" aria-labelledby="portfolioTitle">
    <div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">C / SELECTED DIRECTION</span><h2 id="portfolioTitle">The work starts<br><em>with a question.</em></h2></div><p>The portfolio distinguishes an idea from a designed system, a simulation, and measured hardware. Follow each project at the stage it is actually in.</p></div>
      <div id="featuredProject" aria-live="polite">
        <article class="featured-project"><div class="featured-project-mark" aria-hidden="true"><svg viewBox="0 0 120 96"><path d="M10 48h22m56 0h22M32 24h56v48H32zM46 36v24m14-24v24m14-24v24M4 20h16v56H4m80-56h16v56H84"/><circle cx="60" cy="48" r="4"/></svg></div><div><div class="post-meta"><span class="status-label">Concept</span><span>Embedded systems · Energy</span></div><h3>Smart Energy Monitoring</h3><p>A project direction exploring how embedded measurement might make electrical energy data easier to understand. The architecture and hardware remain open questions.</p><a class="text-link" href="/projects/smart-energy-monitoring.html">View the project record <b>↗</b></a></div></article>
      </div>
      <div class="section-tail"><span>CONCEPTS ARE ROADMAP, NOT RESULTS</span><a class="text-link" href="/projects.html">Browse project records <b>↗</b></a></div>
    </div>
  </section>

  <section class="section method-section" aria-labelledby="methodTitle">
    <div class="wrap"><div class="section-heading split-heading"><div><span class="section-index">D / DESIGN METHOD</span><h2 id="methodTitle">Question.<br><em>Model. Measure.</em></h2></div><p>Engineering is a loop, not a reveal. Assumptions become visible through models; physical tests show what those models missed.</p></div>
      <ol class="method-rail"><li><span>01</span><b>Define</b><small>Constraints &amp; question</small></li><li><span>02</span><b>Model</b><small>Make assumptions explicit</small></li><li><span>03</span><b>Design</b><small>Connect the system</small></li><li><span>04</span><b>Prototype</b><small>Build to learn</small></li><li><span>05</span><b>Measure</b><small>Record conditions</small></li><li><span>06</span><b>Refine</b><small>Let evidence lead</small></li></ol>
    </div>
  </section>

  <section class="section founder-section" aria-labelledby="founderTitle"><div class="wrap founder-grid"><div class="founder-aside"><span class="section-index">E / FOUNDER</span><div class="founder-seal" aria-hidden="true"><span>MSA</span><i>EE / NUST</i><b></b></div></div><div class="founder-copy"><p class="founder-role">ELECTRICAL ENGINEERING UNDERGRADUATE · NUST, PAKISTAN</p><h2 id="founderTitle">Muhammad Shahzaib<br><em>Abbas.</em></h2><p>Academic focus in power engineering. Growing interests in embedded control, electronics, and intelligent energy systems. Elite Bot Studios is the space where those threads become study, project direction, and documented technical work.</p><a class="text-link" href="/about.html">Meet the engineer <b>↗</b></a></div><div class="founder-note"><span>RESEARCH INTERESTS</span><ul><li>Power electronics</li><li>Embedded control</li><li>Energy monitoring</li><li>Intelligent electrical systems</li></ul><a href="/expertise.html">Explore the learning map <b>↗</b></a></div></div></section>

  <section class="section journal-section" aria-labelledby="journalTitle"><div class="wrap"><div class="section-heading split-heading"><div><span class="section-index">F / ENGINEERING LAB</span><h2 id="journalTitle">Notes for the<br><em>next experiment.</em></h2></div><p>Short technical reading on models, methods, and the difference between what is assumed and what is observed.</p><a class="text-link" href="/lab.html">Open the lab <b>↗</b></a></div><div class="journal-grid"><a class="journal-entry" href="/lab/buck-converter-ccm-model.html"><span>01 / POWER ELECTRONICS · 6 MIN</span><h3>A buck converter in<br>continuous conduction.</h3><p>Duty ratio, inductor ripple, and the edge where an ideal CCM model stops applying.</p><b>READ NOTE ↗</b></a><a class="journal-entry" href="/lab/pwm-duty-frequency-resolution.html"><span>02 / EMBEDDED SYSTEMS · 4 MIN</span><h3>PWM: duty, frequency<br>&amp; timer resolution.</h3><p>How timer periods and compare counts shape a digital control signal.</p><b>READ NOTE ↗</b></a></div></div></section>

  <section class="closing-section" aria-labelledby="closingTitle"><div class="wrap closing-grid"><span class="section-index">G / KEEP EXPLORING</span><h2 id="closingTitle">Curiosity asks.<br><em>Engineering answers.</em></h2><div class="closing-actions"><a class="btn btn-primary" href="/projects.html">Explore projects ↗</a><a class="btn btn-ghost" href="/contact.html">Start a conversation</a></div></div></section>
</main>
'''
body=body.replace('SVG_HERO_ART',svg)
html=build.head('Elite Bot Studios — Engineering the Connection Between Power &amp; Intelligence','An independent engineering portfolio exploring embedded systems, power electronics, intelligent control, and engineering design by Muhammad Shahzaib Abbas, Electrical Engineering undergraduate at NUST, Pakistan.','/',jsonld=build.SCHEMA_GRAPH)
html+=build.header('/')+body+build.footer()
SRC=ROOT/'index.html'
html='\n'.join(line.rstrip() for line in html.splitlines())+'\n'
SRC.write_text(html,encoding='utf-8')
print('index.html rebuilt:',len(html),'bytes')
