# -*- coding: utf-8 -*-
"""Page bodies. Content is either verbatim from the approved brief or marked
data-owner="TODO" — nothing is invented."""
import json, re, sys
from html import escape as html_escape, unescape as html_unescape
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

SITE_ROOT=Path(__file__).resolve().parents[2]
PROJECT_RECORDS=json.loads((SITE_ROOT/'projects.json').read_text(encoding='utf-8'))
PROJECT_STATUS={'concept':('Concept','chip-amber'),'simulation':('In simulation','chip-amber'),'design-completed':('Design completed','chip-amber'),'prototype-in-progress':('Prototype in progress','chip-amber'),'bench-tested':('Bench tested','chip-teal'),'complete':('Completed','chip-teal')}

def render_project(p):
    slug=p.get('slug','')
    if not __import__('re').fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug): raise ValueError('Unsafe project slug: '+slug)
    status,cls=PROJECT_STATUS.get(p.get('status'),('Unclassified','chip-amber'))
    def block(label,value): return '<div><dt>%s</dt><dd>%s</dd></div>'%(label,html_escape(str(value),quote=True)) if value else ''
    tags=''.join('<span class="chip">%s</span>'%html_escape(str(x),quote=True) for x in p.get('tags',[]))
    body=''.join([block('Objective',p.get('objective')),block('Context',p.get('problem')),block('Approach',p.get('approach')),block('Evidence',p.get('measured_results') or p.get('results') or p.get('results_note'))])
    action=''
    url=p.get('case_study_url') or ('/projects/%s.html'%slug if p.get('case_study') else '')
    if url and re.fullmatch(r'/projects/[a-z0-9-]+\.html',url): action='<a class="text-link" href="%s">Open project record ↗</a>'%html_escape(url,quote=True)
    return '<article class="card proj-card reveal" id="%s"><div class="post-meta"><span class="chip %s">%s</span><span>%s</span></div><h3>%s</h3><dl class="proj-body" style="margin:0">%s</dl>%s%s</article>'%(slug,cls,status,html_escape(str(p.get('category','')),quote=True),html_escape(str(p.get('title','')),quote=True),body,('<div class="chips">%s</div>'%tags) if tags else '',action)


COLLABORATION = [
    ('Research and academic discussion',
     'Questions about embedded control, energy instrumentation or power conversion where a student perspective, a literature pointer, or a second pair of eyes is useful.',
     ['Discussing a paper or approach', 'Reviewing a project plan or a test method', 'Pointing at relevant work worth reading']),
    ('Student and early-career collaboration',
     'Working alongside another student on a shared technical problem, usually with clearly split responsibilities and a written scope.',
     ['Shared simulation or documentation work', 'Peer review of schematics or firmware structure', 'Study groups around a specific topic']),
    ('Internships and graduate opportunities',
     'Placements where a supervised team can help an undergraduate develop hardware and firmware judgement.',
     ['Embedded or power-electronics internship', 'Research assistant or lab support role', 'Graduate scheme with a hardware track']),
    ('Low-voltage hardware conversations',
     'Early-stage questions about a small embedded or low-voltage power design, where a careful second opinion is more useful than a quotation.',
     ['Sensing and measurement approach', 'Board-level review before fabrication', 'Firmware structure and bring-up planning']),
]


def services():
    cards = []
    for index, (title, description, examples) in enumerate(COLLABORATION, 1):
        items = ''.join('<li>%s</li>' % html_escape(x) for x in examples)
        cards.append('''<article class="collab-card"><span class="card-num">%02d</span><h2>%s</h2><p>%s</p><ul>%s</ul></article>'''
                     % (index, html_escape(title), html_escape(description), items))
    body = '''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Collaboration</span><h1>What a useful conversation looks like.</h1><p>The studio is run by one undergraduate engineer, so the honest offer is attention rather than scale: technical discussion, careful review, and clearly scoped low-voltage work.</p></div></section>
    <section class="section"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">WHO GETS IN TOUCH</span><h2>Four kinds of<br><em>conversation.</em></h2></div><p>If your question is technical, say what you are measuring, building, or trying to understand. That is usually enough to start.</p></div>
      <div class="collab-grid">COLLAB_CARDS</div>
    </div></section>
    <section class="section collab-scope"><div class="wrap collab-scope-grid">
      <div><span class="section-index">SCOPE</span><h2>What is in, and what is not.</h2></div>
      <div>
        <ul class="scope-list">
          <li><b>In scope:</b> low-voltage embedded and power-electronics work, simulation studies, documentation, and review — the same territory as the tools and notes on this site.</li>
          <li><b>Needs supervision:</b> anything mains-connected, high-voltage, safety-critical, or requiring regulatory approval. That is not offered for unsupervised commissioning.</li>
          <li><b>Not claimed:</b> professional licensure, a team, an established consultancy, or delivered client projects.</li>
        </ul>
        <div class="collab-actions"><a class="btn btn-primary" href="/contact.html">Start a conversation <span aria-hidden="true">&#8599;</span></a><a class="text-link" href="/expertise.html">See what is being studied <b>&#8599;</b></a></div>
      </div>
    </div></section>
'''
    body = body.replace('COLLAB_CARDS', '\n'.join(cards))
    page('Collaboration — Research, Study and Low-Voltage Hardware | Elite Bot Studios',
         'How to work with Elite Bot Studios: research and academic discussion, student collaboration, internships, and careful low-voltage hardware conversations, with clear scope boundaries.',
         '/services.html', body, jsonld=SCHEMA_GRAPH)


# ---------------------------------------------------------------- projects --
def projects():
    cards='\n'.join(render_project(p) for p in PROJECT_RECORDS)
    empty_attr=' hidden' if PROJECT_RECORDS else ''
    body = '''
    <section class="page-head project-index-head"><div class="wrap"><span class="eyebrow">Portfolio / Engineering work</span><h1>Ideas, models, and<br><em>what comes next.</em></h1><p>Follow the engineering questions as they move through design. Every entry carries its real status: concept, model, prototype, or measured system.</p></div></section>
    <section class="section"><div class="wrap">
      <div class="project-section-label"><span class="section-index">01 / CURRENT PROJECT RECORDS</span><span>STATUS IS PART OF THE STORY</span></div>
      <h2 class="sr-only">Project records</h2><div id="projectsGrid" class="grid grid-2">PROJECT_CARDS</div>
      <div class="empty-state" id="projectsEmpty"EMPTY_ATTR><h3>Project records are taking shape.</h3><p>As project work develops, records will follow it with the relevant design files, models, and evidence.</p><a class="btn btn-ghost" href="/lab.html">Read the Engineering Lab</a></div>
      <div class="concept-architecture"><div class="concept-architecture-head"><div><span class="section-index">CONCEPT SKETCH / NOT A SELECTED DESIGN</span><h2>Smart energy monitoring</h2><p>A functional architecture to explore the system question. Sensing method, analog front end, controller, and data path are not yet selected.</p></div><span class="status-label">Exploration</span></div>
        <svg class="architecture-svg" viewBox="0 0 1080 220" role="img" aria-labelledby="archTitle archDesc"><title id="archTitle">Illustrative energy-monitoring system architecture</title><desc id="archDesc">Possible functional roles from electrical sensing through signal conditioning and embedded processing to logging or display. The blocks do not identify selected components or a built prototype.</desc><path class="architecture-route" d="M178 108h130m150 0h130m150 0h130"/><path class="architecture-route-cyan" d="M178 108h130m280 0h130"/><g><rect x="26" y="53" width="152" height="110" rx="5"/><text x="47" y="86">01 / INPUT</text><text class="architecture-title" x="47" y="116">Electrical</text><text class="architecture-title" x="47" y="138">sensing</text></g><g><rect x="308" y="53" width="150" height="110" rx="5"/><text x="329" y="86">02 / SIGNAL</text><text class="architecture-title" x="329" y="116">Analog</text><text class="architecture-title" x="329" y="138">front end</text></g><g><rect x="588" y="53" width="150" height="110" rx="5"/><text x="609" y="86">03 / COMPUTE</text><text class="architecture-title" x="609" y="116">Embedded</text><text class="architecture-title" x="609" y="138">processing</text></g><g><rect x="868" y="53" width="182" height="110" rx="5"/><text x="889" y="86">04 / USE</text><text class="architecture-title" x="889" y="116">Display or</text><text class="architecture-title" x="889" y="138">data logging</text></g><circle cx="178" cy="108" r="5"/><circle cx="458" cy="108" r="5"/><circle cx="738" cy="108" r="5"/><circle cx="868" cy="108" r="5"/></svg>
        <p class="concept-caption">Illustrative system roles only · not a schematic, component selection, or prototype description.</p>
      </div>
      <div class="roadmap-section"><div class="project-section-label"><span class="section-index">02 / POSSIBLE EXPLORATIONS</span><span>ROADMAP · NOT COMPLETED PROJECTS</span></div><div class="roadmap-grid"><article><span>POWER</span><h3>Digitally controlled buck converter</h3><p>A possible study of switch behavior, inductor ripple, and digital control assumptions.</p></article><article><span>CONTROL</span><h3>Embedded motor control</h3><p>A future direction connecting sensing, actuation, and feedback fundamentals.</p></article><article><span>ENERGY</span><h3>Battery monitoring</h3><p>A possible exploration of measurement, state estimation, and protection concepts.</p></article></div></div>
      <div class="project-template-link"><div><span class="section-index">CASE STUDY WORKFLOW</span><h2>Record the method as well as the result.</h2><p>A reusable structure for objectives, architecture, software, simulation, measurements, limitations, and resources.</p></div><a class="btn btn-ghost" href="/project-template.html">Open project template ↗</a></div>
    </div></section>
'''
    body=body.replace('PROJECT_CARDS',cards).replace('EMPTY_ATTR',empty_attr)
    page('Engineering Projects &amp; Case Studies | Elite Bot Studios','Evidence-led project records in embedded systems, power electronics, PCB design, and control. Concepts are separated from simulations, prototypes, and measured work.','/projects.html',body,jsonld=SCHEMA_GRAPH)


def project_template_page():
    body = '''
    <section class="page-head"><div class="wrap"><a class="backlink" href="/projects.html">&larr; Projects</a><span class="eyebrow">Documentation / Case-study standard</span><h1>How a project record is built.</h1><p>Every engineering record on this site follows the same structure, so a reader can compare a concept, a simulation, and a measured system on equal terms. Sections only appear when they contain real content.</p></div></section>
    <section class="section"><div class="wrap template-grid">
      <div class="template-intro">
        <span class="section-index">01 / STRUCTURE</span>
        <h2>Objective, method, evidence, limits.</h2>
        <p>A record answers four questions in order: what problem is being addressed, how it was approached, what evidence exists, and where the work stops. Status labels keep those stages honest.</p>
        <a class="btn btn-ghost" href="/project-template.md" download>Download the Markdown template &#8599;</a>
        <p class="muted-small">The download is the blank authoring template kept in the repository. It is a starting structure, not a completed project.</p>
      </div>
      <ol class="template-sections">
        <li><span>01</span><div><h3>Overview and objective</h3><p>The system, the engineering question, and the conditions the design must respect.</p></div></li>
        <li><span>02</span><div><h3>Architecture</h3><p>Signal and power flow, drawn as a diagram only when a real design or an explicitly labelled concept exists.</p></div></li>
        <li><span>03</span><div><h3>Hardware and software</h3><p>Confirmed parts, revisions, firmware structure, interfaces, and toolchain.</p></div></li>
        <li><span>04</span><div><h3>Design decisions</h3><p>Trade-offs considered, calculations used, and alternatives rejected.</p></div></li>
        <li><span>05</span><div><h3>Simulation</h3><p>Model, inputs, assumptions, and outputs, always identified as simulated.</p></div></li>
        <li><span>06</span><div><h3>Testing and validation</h3><p>Fixture, instruments, operating conditions, method, and acceptance criteria.</p></div></li>
        <li><span>07</span><div><h3>Results and limitations</h3><p>Measured values kept separate from expected and simulated ones, with the limits stated plainly.</p></div></li>
        <li><span>08</span><div><h3>Resources</h3><p>Repositories, documents, images, and demonstrations&mdash;only when they exist and can be shared.</p></div></li>
      </ol>
    </div></section>
    <section class="section template-scale-section"><div class="wrap"><div class="evidence-key template-key"><span class="section-index">STATUS SCALE</span><span><i>Concept</i> A direction and open questions</span><span><i>Simulation</i> Model output with stated assumptions</span><span><i>Design completed</i> Reviewed schematic or architecture</span><span><i>Prototype</i> Hardware exists</span><span><i>Bench tested</i> Measurements with conditions</span></div><div class="template-scale-actions"><a class="btn btn-ghost" href="/projects.html">Back to project records &#8599;</a><a class="text-link" href="/lab.html">Read the engineering notes <b>&#8599;</b></a></div></div></section>
'''
    page('Project Record Standard | Elite Bot Studios','How Elite Bot Studios structures engineering case studies: objective, architecture, decisions, simulation, testing, results, limitations, and resources.','/project-template.html',body,jsonld=SCHEMA_GRAPH)


def project_detail_pages():
    for p in PROJECT_RECORDS:
        record=p.get('case_study')
        if not record: continue
        slug=p['slug'];status,status_class=PROJECT_STATUS.get(p.get('status'),('Unclassified','chip-amber'))
        architecture=record.get('architecture') or []
        nodes=[]
        for i,node in enumerate(architecture,1):
            nodes.append('<li class="concept-node"><span>%02d / FUNCTION</span><h3>%s</h3><p>%s</p></li>'%(i,html_escape(str(node.get('name','')),quote=True),html_escape(str(node.get('detail','')),quote=True)))
        def list_section(key,title):
            items=record.get(key) or []
            if not items:return ''
            return '<section class="detail-section"><span class="section-index">PROJECT NOTE</span><h2>%s</h2><ul class="project-detail-list">%s</ul></section>'%(title,''.join('<li>%s</li>'%html_escape(str(x),quote=True) for x in items))
        extra_sections=[]
        def list_section_title(key,title,index_label):
            items=record.get(key) or []
            if not items:return ''
            return '<section class="detail-section"><span class="section-index">%s</span><h2>%s</h2><ul class="project-detail-list">%s</ul></section>'%(index_label,title,''.join('<li>%s</li>'%html_escape(str(x),quote=True) for x in items))
        for key,title in [('hardware','Hardware'),('software','Firmware and software'),('schematics','Schematics and PCB'),('simulation','Simulation'),('testing','Testing and validation'),('results','Results'),('limitations','Limitations'),('lessons','Lessons learned'),('resources','Resources')]:
            value=record.get(key)
            if not value:continue
            if isinstance(value,list):
                rendered=''.join('<li>%s</li>'%html_escape(str(x),quote=True) for x in value)
                content='<ul class="project-detail-list">%s</ul>'%rendered
            else: content='<p>%s</p>'%html_escape(str(value),quote=True)
            extra_sections.append('<section class="detail-section"><span class="section-index">PROJECT NOTE</span><h2>%s</h2>%s</section>'%(title,content))
        special=[]
        application=record.get('application')
        if application:
            special.append('<section class="detail-section"><span class="section-index">INTENDED APPLICATION</span><h2>Where it would be used.</h2><p>%s</p></section>'%html_escape(str(application),quote=True))
        reqs=record.get('requirements') or []
        if reqs:
            rows=''.join('<tr><th scope="row">%s</th><td>%s</td></tr>'%(html_escape(str(r.get('id','')),quote=True),html_escape(str(r.get('text','')),quote=True)) for r in reqs)
            special.append('<section class="detail-section"><span class="section-index">REQUIREMENTS / PROPOSED</span><h2>What the design has to satisfy.</h2><div class="table-scroll"><table><caption class="sr-only">Proposed requirements</caption><tbody>%s</tbody></table></div><p class="concept-caption">Requirements are proposals for review, not accepted specifications.</p></section>'%rows)
        def option_table(key,index_label,title,intro,name_key,note_key):
            items=record.get(key) or []
            if not items:return ''
            rows=''.join('<tr><th scope="row">%s</th><td>%s</td></tr>'%(html_escape(str(i.get(name_key,'')),quote=True),html_escape(str(i.get(note_key,'')),quote=True)) for i in items)
            return '<section class="detail-section"><span class="section-index">%s</span><h2>%s</h2><p>%s</p><div class="table-scroll"><table><caption class="sr-only">%s</caption><tbody>%s</tbody></table></div></section>'%(index_label,title,intro,title,rows)
        special.append(option_table('sensing_options','SENSING OPTIONS / PROPOSED','Possible sensing methods.','Nothing is selected yet. Each method is listed with the trade-off that would decide it.','method','note'))
        special.append(option_table('mcu_options','CONTROLLER OPTIONS / PROPOSED','Controller candidates.','Controller choice follows the measurement decisions, not the other way round.','model','note'))
        isolation=record.get('isolation')
        if isolation:
            special.append('<section class="detail-section"><span class="section-index">SAFETY &amp; ISOLATION</span><h2>Where this study stops.</h2><p>%s</p></section>'%html_escape(str(isolation),quote=True))
        validation=record.get('validation') or []
        if validation:
            special.append('<section class="detail-section"><span class="section-index">VALIDATION STRATEGY</span><h2>How a result would be checked.</h2><ul class="project-detail-list">%s</ul></section>'%''.join('<li>%s</li>'%html_escape(str(x),quote=True) for x in validation))
        roadmap=record.get('roadmap') or []
        if roadmap:
            rows=''.join('<li class="roadmap-step" data-status="%s"><span class="roadmap-status">%s</span><h3>%s</h3><p>%s</p></li>'%(html_escape(str(stage.get('status','')).lower(),quote=True),html_escape(str(stage.get('status','')),quote=True),html_escape(str(stage.get('stage','')),quote=True),html_escape(str(stage.get('deliverable','')),quote=True)) for stage in roadmap)
            special.append('<section class="detail-section"><span class="section-index">DEVELOPMENT ROADMAP</span><h2>Stages, and what each one produces.</h2><ol class="roadmap-track">%s</ol><p class="concept-caption">Status reflects work actually done on this date. Planned stages have no artifact yet.</p></section>'%rows)
        special_html=''.join(special)
        body='''
    <article class="project-detail-page">
      <header class="project-detail-hero"><div class="wrap"><a class="backlink" href="/projects.html">← Projects</a><div class="project-detail-meta"><span class="chip %s">%s</span><span>%s</span><span>%s</span></div><h1>%s</h1><p class="project-detail-lede">%s</p><div class="project-detail-statusline"><span class="section-index">ENGINEERING OBJECTIVE</span><p>%s</p></div></div></header>
      <section class="section"><div class="wrap project-detail-layout"><aside class="project-quickfacts"><span class="section-index">PROJECT RECORD</span><dl><div><dt>Status</dt><dd>%s</dd></div><div><dt>Category</dt><dd>%s</dd></div><div><dt>Published stage</dt><dd>%s</dd></div></dl><p>This page describes a concept and its open questions. It is not a fabricated device, schematic, simulation, or test report.</p></aside><div class="project-detail-content"><section class="detail-section"><span class="section-index">OVERVIEW</span><h2>What question is this exploring?</h2><p>%s</p></section>
        <section class="detail-section"><div class="concept-architecture-head"><div><span class="section-index">SYSTEM ARCHITECTURE / ILLUSTRATIVE</span><h2>Functional roles to investigate.</h2><p>%s</p></div><span class="status-label">Concept only</span></div><ol class="concept-flow">%s</ol><p class="concept-caption">Illustrative system roles only. No component selection, electrical ratings, or measured performance is implied.</p></section>
        %s%s%s
        %s
        <section class="detail-section detail-evidence"><span class="section-index">CURRENT EVIDENCE</span><h2>Where the record stands.</h2><p>%s</p><p>Next additions will be made when the underlying design files, calculations, simulation setup, or test records exist.</p></section>
        <div class="project-detail-related"><a href="/tools/buck-converter.html">Explore the buck converter model ↗</a><a href="/lab.html">Read engineering notes ↗</a></div>
      </div></div></section>
    </article>
'''
        body=body%(status_class,status,html_escape(str(p.get('category','')),quote=True),html_escape(str(p.get('date','')),quote=True),html_escape(str(p.get('title','')),quote=True),html_escape(str(p.get('summary') or record.get('overview','')),quote=True),html_escape(str(p.get('objective','')),quote=True),status,html_escape(str(p.get('category','')),quote=True),status,html_escape(str(record.get('overview','')),quote=True),html_escape(str(record.get('architecture_label','Illustrative architecture')),quote=True),'\n'.join(nodes),list_section('open_questions','Questions to resolve'),list_section('future_directions','Possible next investigations'),'\n'.join(extra_sections),special_html,html_escape(str(p.get('results_note','')),quote=True))
        page('%s | Project Record | Elite Bot Studios'%html_escape(str(p.get('title','Project')),quote=True),str(p.get('summary') or p.get('objective','Engineering project record.')),'/projects/%s.html'%slug,body,jsonld=SCHEMA_GRAPH)


# --------------------------------------------------------------------- lab --
# Lab-note content is authored in content/lab-notes/*.md and parsed by notes.py.

def lab_index():
    featured=next((x for x in POSTS if x['slug']=='buck-converter-ccm-model'),POSTS[0])
    others=[x for x in POSTS if x['slug']!=featured['slug']]
    feat_tags=''.join('<span class="chip">%s</span>'%t for t in featured['tags'])
    featured_html='<article class="lab-feature"><div class="lab-feature-copy"><span class="section-index">FEATURED NOTE</span><h2><a href="/lab/%s.html">%s</a></h2><p>%s</p><div class="chips">%s</div><p class="lab-feature-meta"><time datetime="%s">%s</time><span>%d min read</span></p><a class="btn btn-primary" href="/lab/%s.html">Read the note <span aria-hidden="true">&#8599;</span></a></div><div class="lab-feature-visual" aria-hidden="true"><svg viewBox="0 0 520 300"><path class="lab-viz-grid" d="M40 40h440M40 100h440M40 160h440M40 220h440M40 280h440M40 30v260M150 30v260M260 30v260M370 30v260M480 30v260"/><path class="lab-viz-gold" d="M40 120V70h150v50h330"/><path class="lab-viz-cyan" d="M40 235 190 195 340 235 490 195"/><path class="lab-viz-dash" d="M190 50v210"/><text x="46" y="60">IDEAL PWM</text><text x="46" y="186">INDUCTOR CURRENT</text><text x="200" y="62">D &middot; T</text></svg></div></article>'%(
        featured['slug'],featured['title'],featured['desc'],feat_tags,featured['date'],featured['date'],featured['read_time'],featured['slug'])
    cards=[]
    for note in others:
        tags=''.join('<span class="chip">%s</span>'%t for t in note['tags'][:3])
        cards.append('<a class="journal-entry reveal" href="/lab/%s.html"><div class="journal-entry-meta"><span>%s</span><span>%d MIN READ</span></div><h3>%s</h3><p>%s</p><div class="chips">%s</div><b>OPEN NOTE &#8599;</b></a>'%(
            note['slug'],note['date'],note['read_time'],note['title'],note['desc'],tags))
    topics=[]
    for note in POSTS:
        for tag in note['tags']:
            if tag.lower() not in [t.lower() for t in topics]:
                topics.append(tag)
    topic_html=''.join('<li><span class="chip">%s</span></li>'%html_escape(t,quote=True) for t in topics[:8])
    body='''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Engineering Lab / Notebook</span><h1>Ideas become clearer<br><em>when written down.</em></h1><p>Technical notes on embedded systems, power conversion, models, and engineering method. Each note states its assumptions, and calculated or simulated results are labelled separately from measured ones.</p></div></section>
    <section class="section"><div class="wrap"><h2 class="sr-only">Engineering note index</h2>
      <div class="lab-index-intro"><span class="section-index">%d PUBLISHED NOTES</span><p>Written and reviewed as part of the studio's own study. Long pieces include a contents list; notes link to related calculators or project records where they exist.</p></div>
      %s
      <div class="lab-topics"><span class="section-index">TOPICS</span><ul>%s</ul></div>
      <div class="journal-list">%s</div>
      <div class="section-tail"><span>READING ROOM &middot; ENGINEERING NOTES</span><a class="text-link" href="/tools.html">Try the engineering tools <b>&#8599;</b></a></div>
    </div></section>
'''%(len(POSTS),featured_html,topic_html,''.join(cards))
    page('Engineering Lab &amp; Technical Notes | Elite Bot Studios','Engineering notes on embedded systems, PWM, power conversion, simulation, measurement, and practical design concepts. Educational content clearly labels assumptions and evidence.','/lab.html',body,jsonld=SCHEMA_GRAPH)


RELATED = {
    'buck-converter-ccm-model': [('/tools/buck-converter.html', 'Buck converter explorer'),
                                 ('/tools/rc-time-constant.html', 'RC time constant tool'),
                                 ('/projects/smart-energy-monitoring.html', 'Smart Energy Monitoring record')],
    'pwm-duty-frequency-resolution': [('/tools/pwm-lab.html', 'PWM signal laboratory'),
                                      ('/tools/buck-converter.html', 'Buck converter explorer')],
    'adc-resolution-quantization': [('/tools/voltage-divider.html', 'Voltage divider tool'),
                                    ('/projects/smart-energy-monitoring.html', 'Smart Energy Monitoring record')],
    'simulation-is-not-measurement': [('/tools/buck-converter.html', 'Buck converter explorer'),
                                      ('/lab/buck-converter-ccm-model.html', 'Buck converter CCM note')],
    'why-document-the-process': [('/project-template.html', 'Project record standard'),
                                 ('/projects.html', 'Project records')],
}


def lab_posts():
    order = [x['slug'] for x in POSTS]
    for index, p in enumerate(POSTS):
        tags=''.join('<span class="chip">%s</span>'%t for t in p['tags'])
        headings=re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',p['body'])
        toc=''.join('<li><a href="#%s">%s</a></li>'%(slug,html_unescape(re.sub(r'<[^>]+>','',title))) for slug,title in headings)
        toc_html=('<details class="article-toc"><summary>On this page</summary><ol>%s</ol></details>'%toc) if toc else ''
        body='''
    <article class="technical-article">
      <div class="article-progress" role="progressbar" aria-label="Reading progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span id="readingProgress"></span></div>
      <header class="post-head"><div class="wrap"><a class="backlink" href="/lab.html">← Engineering Lab</a><p class="article-kicker">ENGINEERING NOTE / %s</p><h1>%s</h1><div class="article-meta"><time datetime="%s">%s</time><span>%d min read</span><span>Educational note</span></div><div class="chips">%s</div></div></header>
      <div class="article-layout wrap">%s<div class="prose article-prose">%s</div></div>
      <div class="wrap article-related"><span class="section-index">CONTINUE EXPLORING</span>RELATED_LINKS<nav class="article-pager" aria-label="More engineering notes">PREV_LINK NEXT_LINK</nav></div>
    </article>
'''%(p['date'],p['title'],p['date'],p['date'],p['read_time'],tags,toc_html,p['body'])
        related=''.join('<a href="%s">%s &#8599;</a>'%(html_escape(u,quote=True),html_escape(label,quote=True)) for u,label in RELATED.get(p['slug'],[]))
        def find(slug):
            return next((x for x in POSTS if x['slug']==slug), None) if slug else None
        prev_post = find(order[index+1]) if index+1 < len(order) else None
        next_post = find(order[index-1]) if index > 0 else None
        prev_link=('<a class="pager-link" rel="prev" href="/lab/%s.html"><span>Previous note</span>%s</a>'%(prev_post['slug'],prev_post['title'])) if prev_post else '<span></span>'
        next_link=('<a class="pager-link pager-next" rel="next" href="/lab/%s.html"><span>Next note</span>%s</a>'%(next_post['slug'],next_post['title'])) if next_post else '<span></span>'
        body=body.replace('RELATED_LINKS',related).replace('PREV_LINK',prev_link).replace('NEXT_LINK',next_link)
        schema=json.dumps({'@context':'https://schema.org','@type':'Article','headline':html_unescape(p['title']),'datePublished':p['date'],'author':{'@type':'Organization','name':'Elite Bot Studios'},'publisher':{'@type':'Organization','name':'Elite Bot Studios'},'mainEntityOfPage':'https://elitebotstudios.me/lab/%s.html'%p['slug']},indent=2)
        write('/lab/%s.html'%p['slug'],__import__('build').head('%s | Elite Bot Studios'%p['title'],p['desc'],'/lab/%s.html'%p['slug'],jsonld=schema)+__import__('build').header('/lab.html')+'\n  <main id="main">\n'+body+'\n  </main>\n'+__import__('build').footer())


# ------------------------------------------------------------- expertise --
def expertise():
    body='''
    <section class="page-head expertise-head"><div class="wrap"><span class="eyebrow">Technical map / 01</span><h1>How the disciplines<br><em>connect.</em></h1><p>Power engineering is the academic centre. Embedded systems, electronics, and control are the complementary threads being developed around it.</p></div></section>
    <section class="section expertise-network-section"><div class="wrap">
      <div class="expertise-network" aria-label="Conceptual connection map: power conversion, electronics, embedded computing, measurement, control, and connected energy systems interact as one system.">
        <svg viewBox="0 0 1000 420" role="img" aria-labelledby="expertiseDiagramTitle expertiseDiagramDesc"><title id="expertiseDiagramTitle">Engineering disciplines connect as a system</title><desc id="expertiseDiagramDesc">Power conversion, hardware, embedded computing, measurement and control form connected engineering disciplines; connected energy systems bring them together.</desc><path class="network-line network-line-gold" d="M190 105H432M568 105H810M190 315H432M568 315H810M500 142V278M220 132 430 288M780 132 570 288"/><path class="network-line network-line-cyan" d="M251 105H380m-9-7 9 7-9 7M620 105h129m-9-7 9 7-9 7M250 315h130m-9-7 9 7-9 7M620 315h130m-9-7 9 7-9 7M500 171v73m-7-9 7 9 7-9"/><circle class="network-node" cx="160" cy="105" r="42"/><circle class="network-node" cx="500" cy="105" r="42"/><circle class="network-node" cx="840" cy="105" r="42"/><circle class="network-node" cx="160" cy="315" r="42"/><circle class="network-node" cx="500" cy="315" r="42"/><circle class="network-node" cx="840" cy="315" r="42"/><text x="160" y="111">POWER</text><text x="500" y="111">HW</text><text x="840" y="111">EMBED</text><text x="160" y="321">SENSE</text><text x="500" y="321">CONTROL</text><text x="840" y="321">ENERGY</text><text class="network-caption" x="500" y="211">A SYSTEMS VIEW</text></svg>
      </div>
      <div class="expertise-legend"><span><i class="legend-gold"></i>Academic focus</span><span><i class="legend-cyan"></i>Complementary system links</span><span>Conceptual map · not a proficiency chart</span></div>
    </div></section>
    <section class="section expertise-details" aria-labelledby="knowledgeTitle"><div class="wrap">
      <div class="section-heading split-heading"><div><span class="section-index">KNOWLEDGE AREAS</span><h2 id="knowledgeTitle">A developing toolkit.</h2></div><p>Evidence is attached to work, not guessed from a percentage. The labels below distinguish the academic foundation from topics being explored and longer-term research questions.</p></div>
      <div class="expertise-grid">
        <article class="expertise-card" id="power"><span class="status-label">Academic foundation</span><h2>Power conversion</h2><p>The main academic direction: how electrical energy is modeled, converted, controlled, and delivered.</p><ul><li>Power engineering</li><li>DC–DC conversion principles</li><li>Switching behavior and power-system analysis</li></ul></article>
        <article class="expertise-card" id="embedded"><span class="status-label">Practical exploration</span><h2>Embedded computing</h2><p>Microcontroller-based systems as a bridge between electrical behavior and software-defined decisions.</p><ul><li>Microcontrollers and firmware</li><li>Digital interfaces and peripheral concepts</li><li>Embedded control and connected devices</li></ul></article>
        <article class="expertise-card" id="electronics"><span class="status-label">Practical exploration</span><h2>Electronics &amp; hardware</h2><p>From circuit-level reasoning to board-level implementation, with attention to interfaces and constraints.</p><ul><li>Analog and digital electronics</li><li>PCB design and hardware architecture</li><li>Measurement, protection, and validation</li></ul></article>
        <article class="expertise-card" id="control"><span class="status-label">Learning map</span><h2>Control &amp; instrumentation</h2><p>How sensing, models, and actuation combine to shape a system’s response.</p><ul><li>Feedback and control fundamentals</li><li>Sensor interfaces and signal conditioning</li><li>System modeling and simulation</li></ul></article>
        <article class="expertise-card expertise-card-wide" id="energy"><span class="status-label">Research interest</span><h2>Intelligent energy systems</h2><p>Long-term questions around energy monitoring, embedded control, renewable integration, and instrumented electrical systems.</p><a class="text-link" href="/projects.html">Follow the project directions <b>↗</b></a></article>
      </div>
      <div class="evidence-key"><span class="section-index">EVIDENCE KEY</span><span><i>Academic foundation</i> Course-based grounding</span><span><i>Practical exploration</i> Skills currently being developed</span><span><i>Demonstrated project work</i> Linked to an artifact when published</span><span><i>Research interest</i> Future questions, not claimed contributions</span></div>
    </div></section>
    '''
    page('Expertise Map | Elite Bot Studios','Explore how power engineering, embedded computing, electronics, control, and intelligent energy systems connect in Muhammad Shahzaib Abbas’s evolving engineering practice.','/expertise.html',body,jsonld=SCHEMA_GRAPH)


# ------------------------------------------------------------------- about --
def about():
    body='''
    <section class="page-head about-head"><div class="wrap"><span class="eyebrow">About / Muhammad Shahzaib Abbas</span><h1>The engineer behind<br><em>Elite Bot Studios.</em></h1><p>Electrical Engineering undergraduate at NUST, Pakistan. Academic focus in power engineering; independent interests in embedded systems, electronics, and control.</p></div></section>
    <section class="section about-editorial"><div class="wrap about-intro-grid"><div class="about-monogram" aria-label="Initials MSA">MSA<span>EE / NUST</span><i></i></div><div class="about-prose"><span class="section-index">01 / BACKGROUND</span><h2>Power systems drew me in.<br><em>Embedded control keeps widening the frame.</em></h2><p>I study Electrical Engineering at the National University of Sciences and Technology in Pakistan, with an academic direction in power engineering. Alongside my degree, I am building a complementary understanding of embedded systems, electronics, microcontrollers, and control.</p><p>I am drawn to the point where an electrical system becomes observable and responsive: sensing what is happening, deciding what should happen next, and understanding the limits of the hardware doing it. Elite Bot Studios is my long-term place to develop those ideas in public through models, project records, and technical notes.</p><p>My broader interests include power electronics, intelligent energy systems, and applied research. I am interested in postgraduate study and international research collaboration, particularly in Europe and Germany, as my academic path develops.</p></div></div></section>
    <section class="section about-evidence"><div class="wrap"><div class="section-heading split-heading"><div><span class="section-index">02 / EVIDENCE IN THE OPEN</span><h2>What you can check<br><em>right now.</em></h2></div><p>Everything below is public and self-contained. It is the fastest way to judge the level of work without reading a CV.</p></div>
      <div class="evidence-cards">
        <a class="evidence-card" href="/projects/smart-energy-monitoring.html"><span class="section-index">PROJECT RECORD</span><h3>Smart Energy Monitoring</h3><p>A design brief with requirements, sensing options, safety boundary and a staged roadmap. Status: concept.</p><b>Open the record &#8599;</b></a>
        <a class="evidence-card" href="/lab.html"><span class="section-index">ENGINEERING LAB</span><h3>Five technical notes</h3><p>Buck converter CCM, PWM timing, ADC resolution, and how simulation differs from measurement.</p><b>Read the notes &#8599;</b></a>
        <a class="evidence-card" href="/tools.html"><span class="section-index">ENGINEERING TOOLS</span><h3>Seven working models</h3><p>Including a buck-converter explorer and a PWM signal laboratory, each with stated assumptions and reference tests.</p><b>Open the tools &#8599;</b></a>
      </div>
    </div></section>
    <section class="section about-direction"><div class="wrap"><div class="section-heading split-heading"><div><span class="section-index">03 / RESEARCH DIRECTION</span><h2>Questions that cross<br><em>disciplinary boundaries.</em></h2></div><p>Areas of curiosity—not published research contributions.</p></div><div class="research-lines"><article><span>01</span><h3>Digital power conversion</h3><p>How embedded control and power-stage dynamics shape converter behavior.</p></article><article><span>02</span><h3>Energy instrumentation</h3><p>How measurement quality changes the decisions a system can make.</p></article><article><span>03</span><h3>Intelligent electrical systems</h3><p>How connected hardware can improve visibility and control of energy use.</p></article></div></div></section>
    <section class="section about-profile"><div class="wrap about-profile-grid"><div><span class="section-index">04 / PROFILE</span><h2>Academic foundation.</h2><p class="about-profile-lede">Power engineering is the academic direction. Embedded systems, electronics and control are the threads being developed around it, in coursework and in the open work on this site.</p></div><dl class="profile-facts"><div><dt>Name</dt><dd>Muhammad Shahzaib Abbas</dd></div><div><dt>Current status</dt><dd>Electrical Engineering undergraduate</dd></div><div><dt>Institution</dt><dd>National University of Sciences and Technology (NUST), Pakistan</dd></div><div><dt>Academic direction</dt><dd>Power engineering</dd></div><div><dt>Complementary interests</dt><dd>Embedded systems · electronics · control</dd></div></dl></div></section>
    <section class="section about-now"><div class="wrap about-now-grid"><div><span class="section-index">05 / CURRENT PRACTICE</span><h2>Learn it.<br><em>Connect it. Document it.</em></h2></div><div><p>Current work is about developing a rigorous foundation and learning to move between circuit behavior, power flow, embedded decisions, and clear technical documentation. The public project index separates planned directions from artifacts that have actually been produced.</p><a class="text-link" href="/projects.html">See project status <b>↗</b></a></div></div></section>
    <section class="section"><div class="wrap"><div class="collaboration-card"><span class="section-index">06 / CONNECT</span><h2>Good engineering starts with a good question.</h2><p>Open to academic discussion, research conversations, internships, and appropriately scoped engineering collaboration.</p><a class="btn btn-primary" href="/contact.html">Start a conversation ↗</a></div></div></section>
'''
    about_ld=json.loads(SCHEMA_GRAPH)
    about_ld['@graph'].append({'@type':'Person','@id':'https://elitebotstudios.me/about.html#founder','name':'Muhammad Shahzaib Abbas','url':'https://elitebotstudios.me/about.html','email':EMAIL,'jobTitle':'Electrical Engineering undergraduate','affiliation':{'@type':'CollegeOrUniversity','name':'National University of Sciences and Technology (NUST)','address':{'@type':'PostalAddress','addressCountry':'PK'}},'knowsAbout':['Power engineering','Embedded systems','Electronics','Microcontrollers','Control systems','Intelligent energy systems']})
    page('About Muhammad Shahzaib Abbas | Elite Bot Studios','Muhammad Shahzaib Abbas studies Electrical Engineering at NUST, Pakistan, with an academic direction in power engineering and interests in embedded systems, electronics, and control.','/about.html',body,jsonld=json.dumps(about_ld,indent=2))


# ----------------------------------------------------------------- contact --
CONTACT_FORM_JS = r'''
  <script>
    (function(){
      function initContact(){
        var form=document.getElementById('contactForm');
        if(!form)return;
        var status=document.getElementById('formStatus');
        var submit=form.querySelector('button[type="submit"]');
        var EMAIL='contact@elitebotstudios.me';

        function field(el,msg){
          var box=el.closest('.field');
          if(!box)return false;
          var error=box.querySelector('.err');
          el.setAttribute('aria-invalid',msg?'true':'false');
          if(error)error.textContent=msg||'';
          return !msg;
        }
        function validate(el){
          var v=(el.value||'').trim();
          if(el.required&&!v)return field(el,'This field is required.');
          if(el.type==='email'&&v&&!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v))return field(el,'Enter a valid email address.');
          if(el.tagName==='TEXTAREA'&&v.length<20)return field(el,'Please add at least 20 characters.');
          return field(el,'');
        }
        Array.prototype.forEach.call(form.elements,function(el){
          if(!el.name)return;
          el.addEventListener('blur',function(){validate(el);});
          el.addEventListener('input',function(){if(el.getAttribute('aria-invalid')==='true')validate(el);});
        });

        function draft(){
          var data=new FormData(form);
          var lines=['Name: '+data.get('name'),'Email: '+data.get('email'),
                     'Organization / university: '+(data.get('organization')||'Not provided'),
                     'Inquiry: '+data.get('category'),'','Message:',data.get('message')];
          window.location.href='mailto:'+EMAIL+'?subject='+encodeURIComponent('Elite Bot Studios — '+data.get('category'))+'&body='+encodeURIComponent(lines.join('\n'));
          status.style.color='var(--teal)';
          status.textContent='Direct delivery is not configured on this deployment yet, so your email app has been opened with the message ready to send. Nothing was transmitted by this website.';
        }

        form.addEventListener('submit',function(ev){
          ev.preventDefault();
          var ok=true,first=null;
          Array.prototype.forEach.call(form.elements,function(el){
            if(!el.name||!el.closest('.field'))return;
            if(!validate(el)){ok=false;if(!first)first=el;}
          });
          if(!ok){status.style.color='#E5726B';status.textContent='Please review the highlighted fields.';if(first)first.focus();return;}

          var payload={name:form.elements['name'].value,email:form.elements['email'].value,
                       organization:form.elements['organization'].value,category:form.elements['category'].value,
                       message:form.elements['message'].value,website:form.elements['website'].value};
          var original='Send message';
          if(submit){submit.disabled=true;submit.textContent='Sending…';}
          status.style.color='var(--muted)';status.textContent='Sending your message…';

          function restore(){if(submit){submit.disabled=false;submit.textContent=original;}}

          fetch('/api/contact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
            .then(function(res){
              return res.json().catch(function(){return null;}).then(function(body){return {status:res.status,body:body};});
            })
            .then(function(result){
              restore();
              if(result.status===200&&result.body&&result.body.delivered){
                form.reset();
                status.style.color='var(--teal)';
                status.textContent='Message sent. It has been delivered to the studio inbox; you will get a reply at the address you provided.';
                return;
              }
              if(result.status===422&&result.body&&result.body.fields){
                Object.keys(result.body.fields).forEach(function(key){
                  var el=form.elements[key];
                  if(el)field(el,result.body.fields[key]);
                });
                status.style.color='#E5726B';status.textContent='Please review the highlighted fields.';
                return;
              }
              if(result.status===502){
                status.style.color='#E5726B';
                status.textContent='The mail service did not accept the message. Please email '+EMAIL+' directly.';
                return;
              }
              draft();
            })
            .catch(function(){restore();draft();});
        });
      }
      if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initContact,{once:true});else initContact();
    }());
  </script>'''


def contact():
    body = '''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Contact</span><h1>Start a technical conversation.</h1><p>Share the kind of discussion you have in mind and enough context for a useful reply.</p></div></section>
    <section class="section"><div class="wrap contact-layout"><div>
      <form id="contactForm" action="/api/contact" method="post" novalidate>
        <div class="hp-field" aria-hidden="true"><label for="website">Leave this field empty</label><input id="website" name="website" type="text" tabindex="-1" autocomplete="off"></div>
        <div class="field"><label for="name">Full name <span aria-hidden="true">*</span></label><input id="name" name="name" autocomplete="name" required maxlength="100"><span class="err" aria-live="polite"></span></div>
        <div class="field"><label for="email">Email <span aria-hidden="true">*</span></label><input id="email" name="email" type="email" autocomplete="email" required maxlength="254"><span class="err" aria-live="polite"></span></div>
        <div class="field"><label for="organization">Organization / university <span class="muted-small">(optional)</span></label><input id="organization" name="organization" autocomplete="organization" maxlength="120"><span class="err" aria-live="polite"></span></div>
        <div class="field"><label for="category">Inquiry type <span aria-hidden="true">*</span></label><select id="category" name="category" required><option value="">Choose a category</option><option>Engineering collaboration</option><option>Academic or research discussion</option><option>Research opportunity</option><option>Internship or job opportunity</option><option>Hardware project inquiry</option><option>General question</option></select><span class="err" aria-live="polite"></span></div>
        <div class="field"><label for="message">Message <span aria-hidden="true">*</span></label><textarea id="message" name="message" required minlength="20" maxlength="1200" rows="7" placeholder="What are you working on or hoping to discuss?"></textarea><span class="err" aria-live="polite"></span></div>
        <button class="btn btn-primary" type="submit">Send message</button>
        <p class="form-note" id="formStatus" role="status" aria-live="polite">The status line reports what actually happened: a delivered message, a validation problem, or an email draft. Direct email is always available on the right.</p>
      </form>
    </div><aside class="contact-aside"><div class="info-block"><h2>Direct email</h2><p><a href="mailto:contact@elitebotstudios.me">contact@elitebotstudios.me</a></p><p class="muted-small">Use this if your device has no email app configured, or if you prefer not to use the form.</p></div><div class="info-block"><h2>Good context to include</h2><p>For a technical discussion, mention the system or research question, relevant constraints, and what kind of feedback or collaboration you are seeking.</p></div><div class="info-block"><h2>How the form handles your data</h2><p>If server delivery is configured, your message is sent through the site's own endpoint to the studio inbox. If it is not configured, nothing is transmitted and your email application opens with a draft instead. The form never reports a success it cannot verify.</p></div></aside></div></section>
'''
    page('Contact | Elite Bot Studios','Contact Muhammad Shahzaib Abbas about engineering collaboration, academic research discussion, research opportunities, internships, hardware project inquiries, or general questions.','/contact.html',body,jsonld=SCHEMA_GRAPH,extra_head=CONTACT_FORM_JS)


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
            <li><b>Contact enquiries.</b> When message delivery is configured on this deployment, the contact form sends your name, email address, optional organization, inquiry category, and message through a serverless endpoint to the studio inbox. When delivery is not configured, nothing is transmitted: your email application opens with a draft that you choose whether to send. The form reports which of these two paths actually occurred.</li>
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
    services(); projects(); project_detail_pages(); project_template_page(); lab_index(); lab_posts(); expertise(); about(); contact()
    privacy(); terms(); cookies(); notfound(); offline()
    print('done.')
