# -*- coding: utf-8 -*-
"""Page bodies. Content is either verbatim from the approved brief or marked
data-owner="TODO" — nothing is invented."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import page, EMAIL, write, SCHEMA_GRAPH
from notes import POSTS

# ORG_LD was replaced by build.SCHEMA_GRAPH. Every page that emits schema now
# shares one @graph, so the organisation reads the same in each place.

# ----------------------------------------------------- focus and collaboration --
AREAS = [
    ("Embedded systems", "01", "Microcontroller architecture, firmware structure, peripheral communication, and timing are active study areas. Specific demonstrated work is linked only when a project record supports it.", ["Microcontroller fundamentals", "Firmware structure and state machines", "UART, SPI, I²C, ADC, PWM concepts"]),
    ("Power electronics", "02", "Power conversion and control are the academic centre of gravity: understanding switching behaviour, regulation, and the trade-offs behind converter design.", ["DC–DC conversion principles", "Switching devices and gate-drive concepts", "Model-based analysis and validation questions"]),
    ("Electronics & PCB", "03", "Circuit design and board-level implementation connect system requirements to buildable hardware. Design files and fabrication evidence will be published when verified.", ["Circuit analysis and component selection", "Schematic and PCB workflow", "Protection, grounding, and measurement"]),
    ("Control, instrumentation & IoT", "04", "Control and sensing link electrical behaviour with embedded computation. Connected-energy systems remain a direction of exploration, not a claim of deployed products.", ["Feedback and control fundamentals", "Sensors and signal conditioning", "Connected-device and energy-monitoring concepts"]),
]

def services():
    cards=[]
    for title,num,desc,items in AREAS:
        lis=''.join('<li>%s</li>'%x for x in items)
        cards.append('''<article class="card reveal"><span class="card-num">%s / FOCUS</span><h2>%s</h2><p>%s</p><ul class="prose">%s</ul></article>'''%(num,title,desc,lis))
    body='''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Capabilities &amp; collaboration</span><h1>Areas to explore together.</h1><p>Elite Bot Studios is an independent, evolving engineering initiative—not an established consultancy. These topics describe current academic focus and collaboration interests; they are not a promise of qualifications, certification, or unsupervised delivery.</p></div></section>
    <section class="section"><div class="wrap"><div class="grid grid-2">%s</div>
      <div class="notice" style="margin-top:24px"><div><b>Scope responsibly</b><p>Any practical engagement is discussed case by case against demonstrated experience. High-voltage, mains-connected, regulated, and safety-critical work is not offered for unsupervised commissioning. The portfolio distinguishes academic study, concepts, simulation, and measured hardware.</p></div></div>
      <p style="margin-top:24px"><a class="btn btn-ghost" href="/expertise.html">View the expertise map</a> <a class="btn btn-primary" href="/contact.html">Start a conversation</a></p>
    </div></section>'''
    page('Capabilities &amp; Collaboration | Elite Bot Studios','Engineering areas of study and collaboration interest: embedded systems, power electronics, electronics and PCB design, control, instrumentation, and IoT.','/services.html',body,jsonld=SCHEMA_GRAPH)


# ---------------------------------------------------------------- projects --
def projects():
    body = '''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Projects</span><h1>A portfolio that earns its claims.</h1><p>Concepts are labelled as concepts. Simulations and measurements will be published with their assumptions, methods, and limitations. There are no completed hardware case studies to claim today.</p></div></section>
    <section class="section"><div class="wrap">
      <div class="notice reveal"><div><b>Current portfolio status</b><p>One project track is recorded as a concept. It has no published prototype, repository, simulation, or bench results. Future project pages will only be expanded when actual evidence is available.</p></div></div>
      <h2 class="sr-only">Project records</h2><div id="projectsGrid" class="grid grid-2" aria-live="polite"></div>
      <div class="empty-state" id="projectsEmpty"><h3>Evidence is still being developed.</h3><p>The portfolio is intentionally small rather than padded with imagined case studies. The lab log records technical learning; project records will grow with verified work.</p><a class="btn btn-ghost" href="/lab.html">Visit the Engineering Lab</a></div>
      <div class="section-head" style="margin-top:52px"><span class="label">Case-study standard</span><h2>What a project record will contain</h2><p>System objective, architecture, verified hardware and software, design decisions, simulations, test conditions, measured results, limitations, lessons, and supporting files—only where those artifacts exist.</p><a class="text-link" href="/project-template.md">Open the reusable project template →</a></div>
    </div></section>
'''
    page('Engineering Projects &amp; Case Studies | Elite Bot Studios','Evidence-led project records in embedded systems, power electronics, PCB design, and control. Concepts are separated from simulations, prototypes, and measured work.','/projects.html',body,jsonld=SCHEMA_GRAPH)


# --------------------------------------------------------------------- lab --
# Lab-note content is authored in content/lab-notes/*.md and parsed by notes.py.


def lab_index():
    cards = []
    for p in POSTS:
        tags = ''.join('<span class="chip">%s</span>' % t for t in p['tags'])
        cards.append('''        <a class="post-card reveal" href="/lab/%s.html">
          <div class="post-meta"><time datetime="%s">%s</time><span>%s</span></div>
          <h3>%s</h3>
          <p>%s</p>
          <div class="chips">%s</div>
        </a>''' % (p['slug'], p['date'], p['date'], 'Lab Log', p['title'], p['desc'], tags))

    body = '''
    <section class="page-head">
      <div class="wrap">
        <span class="eyebrow">Lab Log</span>
        <h1>Notes from the bench.</h1>
        <p>What is being built, what broke, and what the measurements said. Written as the work happens.</p>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <h2 class="sr-only">Lab notes</h2>
        <div class="grid">
%s
        </div>
      </div>
    </section>
''' % '\n'.join(cards)

    page('Lab Log — Build Notes from the Bench | Elite Bot Studios',
         'Build notes from the bench: what is being built, what broke, and what the measurements said.',
         '/lab.html', body, jsonld=SCHEMA_GRAPH)


def lab_posts():
    for p in POSTS:
        tags = ''.join('<span class="chip">%s</span>' % t for t in p['tags'])
        body = '''
    <article>
      <header class="post-head">
        <div class="wrap">
          <a class="backlink" href="/lab.html">&larr; Lab Log</a>
          <h1>%s</h1>
          <div class="post-meta"><time datetime="%s">%s</time><span>Elite Bot Studios</span></div>
          <div class="chips">%s</div>
        </div>
      </header>
      <div class="section">
        <div class="wrap">
          <div class="prose reveal">
%s
          </div>
        </div>
      </div>
    </article>

    <section class="section">
      <div class="wrap">
        <div class="reveal" style="max-width:600px">
          <span class="label">Next</span>
          <h2 style="font-size:clamp(1.4rem,3.6vw,1.8rem);margin:12px 0 14px">Have a build in mind?</h2>
          <p style="color:var(--muted)">Describe the problem and you will get a scope, a parts list, and a fixed price.</p>
          <div class="hero-ctas" style="margin-top:24px">
            <a class="btn btn-primary" href="/contact.html">Start a Project</a>
            <a class="btn btn-ghost" href="/lab.html">More Lab Notes</a>
          </div>
        </div>
      </div>
    </section>
''' % (p['title'], p['date'], p['date'], tags, p['body'])

        write('/lab/%s.html' % p['slug'],
              __import__('build').head(
                  p.get('seo') or ('%s | Elite Bot Studios' % p['title']), p['desc'],
                  '/lab/%s.html' % p['slug'],
                  jsonld=json.dumps({
                      "@context": "https://schema.org", "@type": "Article",
                      "headline": p['title'], "datePublished": p['date'],
                      "author": {"@type": "Organization", "name": "Elite Bot Studios"},
                      "publisher": {"@type": "Organization", "name": "Elite Bot Studios"},
                      "mainEntityOfPage": "https://elitebotstudios.me/lab/%s.html" % p['slug']
                  }, indent=2))
              + __import__('build').header('/lab.html') + '\n  <main id="main">\n' + body
              + '\n  </main>\n' + __import__('build').footer())


# ------------------------------------------------------------- expertise --
def expertise():
    body = '''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Technical expertise</span><h1>Study areas, evidence, and direction.</h1><p>Skills are not assigned percentages. Each topic is classified by how it is represented here, and demonstrated capability is linked to an actual project or artifact.</p></div></section>
    <section class="section"><div class="wrap">
      <div class="notice"><div><b>Evidence status</b><p>No completed hardware case study is currently published. The sections below describe academic focus, subject areas, and interests from the owner-provided profile—not a claim of advanced proficiency or project validation.</p></div></div>
      <div class="expertise-grid">
        <article class="expertise-card"><span class="status-label">Academic focus</span><h2>Electrical engineering &amp; power</h2><p>Undergraduate study at NUST, Pakistan. The academic direction emphasizes power engineering; the detailed course list can be added once the owner supplies the verified course names.</p><ul><li>Electrical energy and power systems</li><li>Power conversion fundamentals</li><li>Engineering analysis and system models</li></ul></article>
        <article class="expertise-card"><span class="status-label">Currently developing</span><h2>Embedded systems &amp; electronics</h2><p>Complementary interests pursued alongside the electrical-engineering degree. Specific MCU, language, protocol, or tool proficiency is not asserted without supporting work.</p><ul><li>Microcontrollers and firmware</li><li>Digital and analog electronics</li><li>PCB design and hardware validation</li></ul></article>
        <article class="expertise-card"><span class="status-label">Learning map</span><h2>Control &amp; instrumentation</h2><p>Study topics that connect measurement, embedded control, and electrical systems.</p><ul><li>Feedback and control systems</li><li>Sensor interfaces and signal conditioning</li><li>Modeling, simulation, and test methodology</li></ul></article>
        <article class="expertise-card"><span class="status-label">Research interest</span><h2>Intelligent energy systems</h2><p>Long-term interests at the intersection of power engineering and embedded computation.</p><ul><li>Energy monitoring and instrumentation</li><li>Embedded control for power conversion</li><li>Renewable-energy integration and smart electrical systems</li></ul></article>
      </div>
      <div class="section-head" style="margin-top:54px"><span class="label">Evidence policy</span><h2>What “demonstrated” means here</h2><p>A project will be marked demonstrated only when the site can link to the relevant source, design files, simulation setup, or test evidence. Academic familiarity, current learning, and research interest remain separate labels.</p><a class="text-link" href="/projects.html">Review project records →</a></div>
    </div></section>
'''
    page('Technical Expertise &amp; Learning Map | Elite Bot Studios','A transparent learning map for embedded systems, power electronics, electronics, PCB design, control, instrumentation, and energy systems. Demonstrated skills are tied to published evidence.','/expertise.html',body,jsonld=SCHEMA_GRAPH)


# ------------------------------------------------------------------- about --
def about():
    body = '''
    <section class="page-head"><div class="wrap"><span class="eyebrow">About the engineer</span><h1>A student building toward the work.</h1><p>Elite Bot Studios is a technical brand and a public record of an engineer's development—not a large company or a claim of professional licensure.</p></div></section>
    <section class="section"><div class="wrap"><div class="founder-profile"><div class="profile-monogram" aria-hidden="true">MSA<span>EE · NUST</span></div><div class="prose"><span class="label">Founder</span><h2>Muhammad Shahzaib Abbas</h2><p>I am an Electrical Engineering undergraduate at the National University of Sciences and Technology (NUST), Pakistan. My academic direction emphasizes power engineering, and I am independently developing complementary interests in embedded systems, electronics, microcontrollers, and control.</p><p>I am interested in how embedded computation can make electrical and energy systems more observable and controllable. Elite Bot Studios gives me a place to document that development through practical designs, simulations, prototypes, and engineering notes—clearly separating what is planned from what has been built and measured.</p><p>My aim is to build useful technical depth over time and contribute to thoughtful engineering and research collaborations. I am also interested in further study and international research, particularly in Europe including Germany, as my academic path develops. This site will grow as verified projects, academic work, and supporting evidence become available.</p></div></div></div></section>
    <section class="section"><div class="wrap"><div class="section-head"><span class="label">Research interests</span><h2>Questions worth pursuing.</h2></div><div class="grid grid-3"><article class="card"><h3>Power electronics</h3><p>Modeling, design trade-offs, and control of power-conversion systems.</p></article><article class="card"><h3>Embedded control</h3><p>Microcontroller-based sensing, actuation, and real-time interaction with electrical systems.</p></article><article class="card"><h3>Intelligent energy systems</h3><p>Energy monitoring, renewable integration, and instrumentation for smart electrical systems.</p></article></div></div></section>
    <section class="section"><div class="wrap"><div class="section-head"><span class="label">Profile facts</span><h2>Verified identity, without filler.</h2></div><dl class="profile-facts"><div><dt>Current status</dt><dd>Electrical Engineering undergraduate</dd></div><div><dt>Institution</dt><dd>National University of Sciences and Technology (NUST), Pakistan</dd></div><div><dt>Academic emphasis</dt><dd>Power engineering</dd></div><div><dt>Technical interests</dt><dd>Embedded systems · electronics · control · energy systems</dd></div></dl><p class="muted-small" style="margin-top:20px">A CV, profile links, course list, photograph, and verified project artifacts will be added when provided and approved. No placeholder profile links or stock portrait are shown.</p></div></section>
    <section class="section"><div class="wrap"><div class="collaboration-card"><span class="label">Contact</span><h2>Research, learning, and engineering conversations.</h2><p>For academic discussion, research opportunities, internships, or appropriately scoped collaboration, use the contact page.</p><a class="btn btn-primary" href="/contact.html">Get in touch</a></div></div></section>
'''
    about_ld=json.loads(SCHEMA_GRAPH)
    about_ld['@graph'].append({
        '@type':'Person', '@id':'https://elitebotstudios.me/about.html#founder',
        'name':'Muhammad Shahzaib Abbas', 'url':'https://elitebotstudios.me/about.html',
        'email':EMAIL, 'jobTitle':'Electrical Engineering undergraduate',
        'affiliation':{'@type':'CollegeOrUniversity','name':'National University of Sciences and Technology (NUST)','address':{'@type':'PostalAddress','addressCountry':'PK'}},
        'knowsAbout':['Power engineering','Embedded systems','Electronics','Microcontrollers','Control systems','Intelligent energy systems']
    })
    page('About Muhammad Shahzaib Abbas | Elite Bot Studios','Muhammad Shahzaib Abbas is an Electrical Engineering undergraduate at NUST, Pakistan, focused academically on power engineering and exploring embedded systems, electronics, and control.','/about.html',body,jsonld=json.dumps(about_ld,indent=2))



# ----------------------------------------------------------------- contact --
CONTACT_FORM_JS = '''
  <script>
    (function contactComposer(){
      var form=document.getElementById('contactForm');if(!form)return;var status=document.getElementById('formStatus');
      function field(el,msg){var box=el.closest('.field');if(!box)return false;var error=box.querySelector('.err');el.setAttribute('aria-invalid',msg?'true':'false');if(error)error.textContent=msg||'';return !msg;}
      function validate(el){var v=(el.value||'').trim();if(el.required&&!v)return field(el,'This field is required.');if(el.type==='email'&&v&&!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(v))return field(el,'Enter a valid email address.');if(el.tagName==='TEXTAREA'&&v.length<20)return field(el,'Please add at least 20 characters.');return field(el,'');}
      Array.prototype.forEach.call(form.elements,function(el){if(!el.name)return;el.addEventListener('blur',function(){validate(el);});el.addEventListener('input',function(){if(el.getAttribute('aria-invalid')==='true')validate(el);});});
      form.addEventListener('submit',function(ev){ev.preventDefault();var ok=true,first=null;Array.prototype.forEach.call(form.elements,function(el){if(!el.name)return;if(!validate(el)){ok=false;if(!first)first=el;}});if(!ok){status.textContent='Please review the highlighted fields.';if(first)first.focus();return;}
        var data=new FormData(form);var lines=['Name: '+data.get('name'),'Email: '+data.get('email'),'Organization / university: '+(data.get('organization')||'Not provided'),'Inquiry: '+data.get('category'),'','Message:',data.get('message')];
        window.location.href='mailto:contact@elitebotstudios.me?subject='+encodeURIComponent('Elite Bot Studios — '+data.get('category'))+'&body='+encodeURIComponent(lines.join('\\n'));
        status.textContent='Your email app should open with a draft. Review it and press Send there; this website has not received or sent your message.';
      });
    }());
  </script>'''

def contact():
    body = '''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Contact</span><h1>Start a technical conversation.</h1><p>Choose the kind of discussion and share enough context for a useful reply.</p></div></section>
    <section class="section"><div class="wrap contact-layout"><div>
      <form id="contactForm" action="mailto:contact@elitebotstudios.me" method="post" enctype="text/plain" novalidate>
        <div class="field"><label for="name">Full name <span aria-hidden="true">*</span></label><input id="name" name="name" autocomplete="name" required maxlength="100"><span class="err" aria-live="polite"></span></div>
        <div class="field"><label for="email">Email <span aria-hidden="true">*</span></label><input id="email" name="email" type="email" autocomplete="email" required maxlength="254"><span class="err" aria-live="polite"></span></div>
        <div class="field"><label for="organization">Organization / university <span class="muted-small">(optional)</span></label><input id="organization" name="organization" autocomplete="organization" maxlength="120"><span class="err" aria-live="polite"></span></div>
        <div class="field"><label for="category">Inquiry type <span aria-hidden="true">*</span></label><select id="category" name="category" required><option value="">Choose a category</option><option>Engineering collaboration</option><option>Internship or job opportunity</option><option>Academic or research discussion</option><option>Hardware project inquiry</option><option>General question</option></select><span class="err" aria-live="polite"></span></div>
        <div class="field"><label for="message">Message <span aria-hidden="true">*</span></label><textarea id="message" name="message" required minlength="20" maxlength="1200" rows="7" placeholder="What are you working on or hoping to discuss?"></textarea><span class="err" aria-live="polite"></span></div>
        <button class="btn btn-primary" type="submit">Prepare email draft</button>
        <p class="form-note" id="formStatus" role="status" aria-live="polite">The form opens your own email application with a draft. Nothing is submitted to this website.</p>
      </form>
    </div><aside class="contact-aside"><div class="info-block"><h2>Direct email</h2><p><a href="mailto:contact@elitebotstudios.me">contact@elitebotstudios.me</a></p><p class="muted-small">If your device has no email app configured, write directly from any email service.</p></div><div class="info-block"><h2>Good context to include</h2><p>For a technical discussion, mention the system or research question, relevant constraints, and what kind of feedback or collaboration you are seeking.</p></div><div class="info-block"><h2>Privacy note</h2><p>Submitting this page does not transmit your information. The draft is created in your email application; it is sent only if you press Send there.</p></div></aside></div></section>
'''
    page('Contact | Elite Bot Studios','Contact Muhammad Shahzaib Abbas about engineering collaboration, internships, research discussion, hardware project inquiries, or general questions.','/contact.html',body,jsonld=SCHEMA_GRAPH,extra_head=CONTACT_FORM_JS)


# ------------------------------------------------------------ legal + errors --
def privacy():
    body = '''
    <section class="page-head">
      <div class="wrap">
        <span class="eyebrow">Legal</span>
        <h1>Privacy Policy</h1>
        <p>Last updated: 5 November 2026.</p>
      </div>
    </section>
    <section class="section">
      <div class="wrap">
        <div class="prose">
          <p>Elite Bot Studios ("we") operates elitebotstudios.me. This page explains what is collected when you
             use the site and what happens to it.</p>

          <h2>What is collected</h2>
          <ul>
            <li><b>Analytics.</b> The site uses Google Analytics 4 (measurement ID <code>G-HLQ4G5HBMZ</code>) to
                record aggregate usage: pages viewed, approximate region, device type, and referring site.</li>
            <li><b>Contact enquiries.</b> The contact page creates a draft in your own email application. The site does not transmit or store form fields. If you choose to send the email, the site operator receives the information you include.</li>
            <li><b>Server logs.</b> Our host (Vercel) records standard request logs, including IP address, for
                security and abuse prevention.</li>
          </ul>

          <h2>What is not collected</h2>
          <p>We do not sell, rent, or trade personal data. We do not run advertising pixels, behavioural
             profiling, or cross-site tracking. There are no third-party marketing cookies on this site.</p>

          <h2>Why it is collected</h2>
          <p>Analytics are used to understand aggregate site usage. Email details are used to respond to your message. Server logs are used for hosting operations and security.</p>

          <h2>Cookies</h2>
          <p>Google Analytics sets cookies. See the <a href="/cookies.html">Cookies</a> page for the specific
             names and how to refuse them.</p>

          <h2>Retention</h2>
          <p>Enquiry emails are kept for as long as needed to answer them and to keep a record of work agreed.
             Analytics data is retained according to Google's default retention period.</p>

          <h2>Your rights</h2>
          <p>You can ask what personal data we hold about you, ask for a copy, or ask for it to be deleted. Email
             <!--email_off--><a href="mailto:%s">%s</a><!--/email_off--> and we will respond within 30 days.</p>

          <h2>Third parties</h2>
          <ul>
            <li>Google Analytics — usage measurement</li>
            <li>Vercel — website hosting</li>
          </ul>

          <h2>Changes</h2>
          <p>If this policy changes materially, the "last updated" date above will change with it.</p>

          <h2>Contact</h2>
          <p>Questions about this policy: <!--email_off--><a href="mailto:%s">%s</a><!--/email_off-->.</p>
        </div>
      </div>
    </section>
''' % (EMAIL, EMAIL, EMAIL, EMAIL)
    page('Privacy Policy | Elite Bot Studios',
         'What elitebotstudios.me collects, why it is collected, how long it is kept, and how to have it removed.',
         '/privacy.html', body)


def terms():
    body = '''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Legal</span><h1>Terms of Use</h1><p>Last updated: 5 November 2026.</p></div></section>
    <section class="section"><div class="wrap"><div class="prose">
      <p>These terms apply to use of elitebotstudios.me and the material published on it.</p>
      <h2>Informational content</h2><p>Technical notes, calculator outputs, concepts, and project records are provided for education and discussion. They are not professional engineering approval, a safety certification, or a substitute for checking applicable standards, component datasheets, and qualified supervision.</p>
      <h2>Evidence and limitations</h2><p>Project status distinguishes concepts, models, prototypes, and tests. Calculations are estimates within their stated assumptions. No performance, suitability, admission, employment, or business outcome is guaranteed.</p>
      <h2>Use of technical material</h2><p>Before implementing a circuit or design, independently review it for the intended application, operating conditions, hazards, and regulatory requirements. Mains-connected, high-voltage, and safety-critical systems require appropriately qualified review.</p>
      <h2>External resources</h2><p>Links to third-party websites are provided for reference. Their content and availability are outside this site's control.</p>
      <h2>Contact</h2><p>Questions about these terms: <!--email_off--><a href="mailto:%s">%s</a><!--/email_off-->.</p>
    </div></div></section>
''' % (EMAIL, EMAIL)
    page('Terms of Use | Elite Bot Studios','Terms for using this site and its educational engineering notes, calculators, and project records.','/terms.html',body)




def cookies():
    body = '''
    <section class="page-head">
      <div class="wrap">
        <span class="eyebrow">Legal</span>
        <h1>Cookies</h1>
        <p>Last updated: 5 November 2026.</p>
      </div>
    </section>
    <section class="section">
      <div class="wrap">
        <div class="prose">
          <p>This site sets a small number of cookies, all for measurement. There are no advertising or
             cross-site tracking cookies.</p>

          <h2>Cookies we set</h2>
          <ul>
            <li><code>_ga</code> — Google Analytics 4. Distinguishes one browser from another. Expires after
                2 years.</li>
            <li><code>_ga_HLQ4G5HBMZ</code> — Google Analytics 4. Keeps session state for this property.
                Expires after 2 years.</li>
          </ul>

          <h2>What we do not set</h2>
          <p>No advertising cookies, no social media pixels, no cross-site tracking, and no profiling cookies.</p>

          <h2>How to refuse them</h2>
          <p>Every major browser lets you block or delete cookies in its settings. Blocking analytics cookies does
             not affect how the site works. You can also install Google's
             <a href="https://tools.google.com/dlpage/gaoptout" rel="noopener nofollow">Analytics opt-out
             browser add-on</a>.</p>

          <h2>Questions</h2>
          <p><!--email_off--><a href="mailto:%s">%s</a><!--/email_off--></p>
        </div>
      </div>
    </section>
''' % (EMAIL, EMAIL)
    page('Cookies | Elite Bot Studios',
         'The two Google Analytics cookies this site sets, what they do, how long they last, and how to refuse them.',
         '/cookies.html', body)


def notfound():
    body = '''
    <section class="error-page">
      <div class="wrap">
        <span class="error-code">404</span>
        <h1 style="font-size:clamp(1.4rem,4.4vw,2rem);margin:18px 0 14px">That page is not on the bench.</h1>
        <h2 class="sr-only">Where to go next</h2>
        <p style="color:var(--muted);max-width:52ch;margin:0 auto 30px">
           The link may be out of date, or the page may have been retired while the studio changed direction.
           Everything current is one click away.</p>
        <div class="hero-ctas" style="justify-content:center">
          <a class="btn btn-primary" href="/">Back to Home</a>
          <a class="btn btn-ghost" href="/projects.html">See Projects</a>
        </div>
        <ul class="chips" style="justify-content:center;margin-top:30px">
          <li><a class="chip" href="/services.html">Services</a></li>
          <li><a class="chip" href="/projects.html">Projects</a></li>
          <li><a class="chip" href="/lab.html">Lab Log</a></li>
          <li><a class="chip" href="/about.html">About</a></li>
          <li><a class="chip" href="/contact.html">Contact</a></li>
        </ul>
      </div>
    </section>'''
    page('Page not found | Elite Bot Studios',
         'That page could not be found. Browse services, projects, the lab log, or get in touch.',
         '/404.html', body, canonical='')


def offline():
    body = '''
    <section class="error-page">
      <div class="wrap">
        <span class="error-code">OFFLINE</span>
        <h1 style="font-size:clamp(1.4rem,4.4vw,2rem);margin:18px 0 14px">No connection right now.</h1>
        <h2 class="sr-only">Where to go next</h2>
        <p style="color:var(--muted);max-width:52ch;margin:0 auto 30px">
           This page was served from the cache. Pages you have already visited should still open; anything new
           needs a network connection.</p>
        <div class="hero-ctas" style="justify-content:center">
          <a class="btn btn-primary" href="/">Try Home</a>
          <a class="btn btn-ghost" href="/projects.html">Projects</a>
        </div>
        <p style="color:var(--faint);font-size:13px;margin-top:26px">
          Urgent? Email <!--email_off--><a href="mailto:%s" style="color:var(--teal)">%s</a><!--/email_off-->.
        </p>
      </div>
    </section>''' % (EMAIL, EMAIL)
    page('Offline | Elite Bot Studios',
         'You are offline. Previously visited pages are still available from the cache.',
         '/offline.html', body, canonical='')



if __name__ == '__main__':
    print('building pages…')
    services(); projects(); lab_index(); lab_posts(); expertise(); about(); contact()
    privacy(); terms(); cookies(); notfound(); offline()
    print('done.')
