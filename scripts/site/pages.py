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


def services():
    cards=[]
    for title,num,desc,items in AREAS:
        lis=''.join('<li>%s</li>'%x for x in items)
        cards.append('''<article class="card reveal"><span class="card-num">%s / FOCUS</span><h2>%s</h2><p>%s</p><ul class="prose">%s</ul></article>'''%(num,title,desc,lis))
    body='''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Capabilities &amp; collaboration</span><h1>Areas to explore together.</h1><p>Elite Bot Studios is an independent, evolving engineering initiative—not an established consultancy. These topics describe current academic focus and collaboration interests; they are not a promise of qualifications, certification, or unsupervised delivery.</p></div></section>
    <section class="section"><div class="wrap"><div class="grid grid-2">AREA_CARDS</div>
      <div class="notice" style="margin-top:24px"><div><b>Scope responsibly</b><p>Any practical engagement is discussed case by case against demonstrated experience. High-voltage, mains-connected, regulated, and safety-critical work is not offered for unsupervised commissioning. The portfolio distinguishes academic study, concepts, simulation, and measured hardware.</p></div></div>
      <p style="margin-top:24px"><a class="btn btn-ghost" href="/expertise.html">View the expertise map</a> <a class="btn btn-primary" href="/contact.html">Start a conversation</a></p>
    </div></section>'''
    body=body.replace('AREA_CARDS','\n'.join(cards))
    page('Capabilities &amp; Collaboration | Elite Bot Studios','Engineering areas of study and collaboration interest: embedded systems, power electronics, electronics and PCB design, control, instrumentation, and IoT.','/services.html',body,jsonld=SCHEMA_GRAPH)


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
      <div class="project-template-link"><div><span class="section-index">CASE STUDY WORKFLOW</span><h2>Record the method as well as the result.</h2><p>A reusable structure for objectives, architecture, software, simulation, measurements, limitations, and resources.</p></div><a class="btn btn-ghost" href="/project-template.md">Open project template ↗</a></div>
    </div></section>
'''
    body=body.replace('PROJECT_CARDS',cards).replace('EMPTY_ATTR',empty_attr)
    page('Engineering Projects &amp; Case Studies | Elite Bot Studios','Evidence-led project records in embedded systems, power electronics, PCB design, and control. Concepts are separated from simulations, prototypes, and measured work.','/projects.html',body,jsonld=SCHEMA_GRAPH)


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
        for key,title in [('hardware','Hardware'),('software','Firmware and software'),('schematics','Schematics and PCB'),('simulation','Simulation'),('testing','Testing and validation'),('results','Results'),('limitations','Limitations'),('lessons','Lessons learned'),('resources','Resources')]:
            value=record.get(key)
            if not value:continue
            if isinstance(value,list):
                rendered=''.join('<li>%s</li>'%html_escape(str(x),quote=True) for x in value)
                content='<ul class="project-detail-list">%s</ul>'%rendered
            else: content='<p>%s</p>'%html_escape(str(value),quote=True)
            extra_sections.append('<section class="detail-section"><span class="section-index">PROJECT NOTE</span><h2>%s</h2>%s</section>'%(title,content))
        body='''
    <article class="project-detail-page">
      <header class="project-detail-hero"><div class="wrap"><a class="backlink" href="/projects.html">← Projects</a><div class="project-detail-meta"><span class="chip %s">%s</span><span>%s</span><span>%s</span></div><h1>%s</h1><p class="project-detail-lede">%s</p><div class="project-detail-statusline"><span class="section-index">ENGINEERING OBJECTIVE</span><p>%s</p></div></div></header>
      <section class="section"><div class="wrap project-detail-layout"><aside class="project-quickfacts"><span class="section-index">PROJECT RECORD</span><dl><div><dt>Status</dt><dd>%s</dd></div><div><dt>Category</dt><dd>%s</dd></div><div><dt>Published stage</dt><dd>%s</dd></div></dl><p>This page describes a concept and its open questions. It is not a fabricated device, schematic, simulation, or test report.</p></aside><div class="project-detail-content"><section class="detail-section"><span class="section-index">OVERVIEW</span><h2>What question is this exploring?</h2><p>%s</p></section>
        <section class="detail-section"><div class="concept-architecture-head"><div><span class="section-index">SYSTEM ARCHITECTURE / ILLUSTRATIVE</span><h2>Functional roles to investigate.</h2><p>%s</p></div><span class="status-label">Concept only</span></div><ol class="concept-flow">%s</ol><p class="concept-caption">Illustrative system roles only. No component selection, electrical ratings, or measured performance is implied.</p></section>
        %s%s%s
        <section class="detail-section detail-evidence"><span class="section-index">CURRENT EVIDENCE</span><h2>Where the record stands.</h2><p>%s</p><p>Next additions will be made when the underlying design files, calculations, simulation setup, or test records exist.</p></section>
        <div class="project-detail-related"><a href="/tools/buck-converter.html">Explore the buck converter model ↗</a><a href="/lab.html">Read engineering notes ↗</a></div>
      </div></div></section>
    </article>
'''
        body=body%(status_class,status,html_escape(str(p.get('category','')),quote=True),html_escape(str(p.get('date','')),quote=True),html_escape(str(p.get('title','')),quote=True),html_escape(str(p.get('summary') or record.get('overview','')),quote=True),html_escape(str(p.get('objective','')),quote=True),status,html_escape(str(p.get('category','')),quote=True),status,html_escape(str(record.get('overview','')),quote=True),html_escape(str(record.get('architecture_label','Illustrative architecture')),quote=True),'\n'.join(nodes),list_section('open_questions','Questions to resolve'),list_section('future_directions','Possible next investigations'),'\n'.join(extra_sections),html_escape(str(p.get('results_note','')),quote=True))
        page('%s | Project Record | Elite Bot Studios'%html_escape(str(p.get('title','Project')),quote=True),str(p.get('summary') or p.get('objective','Engineering project record.')),'/projects/%s.html'%slug,body,jsonld=SCHEMA_GRAPH)


# --------------------------------------------------------------------- lab --
# Lab-note content is authored in content/lab-notes/*.md and parsed by notes.py.

def lab_index():
    cards=[]
    for p in POSTS:
        tags=''.join('<span class="chip">%s</span>'%t for t in p['tags'][:3])
        cards.append('''<a class="journal-entry reveal" href="/lab/%s.html"><div class="journal-entry-meta"><span>%s</span><span>%d MIN READ</span></div><h3>%s</h3><p>%s</p><div class="chips">%s</div><b>OPEN NOTE ↗</b></a>'''%(p['slug'],p['date'],p['read_time'],p['title'],p['desc'],tags))
    body='''
    <section class="page-head"><div class="wrap"><span class="eyebrow">Engineering Lab / Notebook</span><h1>Ideas become clearer<br><em>when written down.</em></h1><p>Educational notes on embedded systems, power conversion, models, and engineering method. Explanations are distinct from measured observations.</p></div></section>
    <section class="section"><div class="wrap"><h2 class="sr-only">Engineering note index</h2><div class="lab-index-intro"><span class="section-index">READ / MODEL / QUESTION</span><p>Each note explains a concept with stated assumptions, useful equations, and references where appropriate. No simulated curve is presented as a bench result.</p></div><div class="journal-list">%s</div><div class="section-tail"><span>MARKDOWN-AUTHORED · STATICALLY PUBLISHED</span><a class="text-link" href="/content/README.md">How notes are authored <b>↗</b></a></div></div></section>
'''%''.join(cards)
    page('Engineering Lab &amp; Technical Notes | Elite Bot Studios','Engineering notes on embedded systems, PWM, power conversion, simulation, measurement, and practical design concepts. Educational content clearly labels assumptions and evidence.','/lab.html',body,jsonld=SCHEMA_GRAPH)


def lab_posts():
    for p in POSTS:
        tags=''.join('<span class="chip">%s</span>'%t for t in p['tags'])
        headings=re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',p['body'])
        toc=''.join('<li><a href="#%s">%s</a></li>'%(slug,html_unescape(re.sub(r'<[^>]+>','',title))) for slug,title in headings)
        toc_html=('<details class="article-toc"><summary>On this page</summary><ol>%s</ol></details>'%toc) if toc else ''
        body='''
    <article class="technical-article">
      <div class="article-progress" role="progressbar" aria-label="Reading progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span id="readingProgress"></span></div>
      <header class="post-head"><div class="wrap"><a class="backlink" href="/lab.html">← Engineering Lab</a><p class="article-kicker">ENGINEERING NOTE / %s</p><h1>%s</h1><div class="article-meta"><time datetime="%s">%s</time><span>%d min read</span><span>Educational note</span></div><div class="chips">%s</div></div></header>
      <div class="article-layout wrap">%s<div class="prose article-prose">%s</div></div>
      <div class="wrap article-related"><span class="section-index">CONTINUE EXPLORING</span><a href="/tools/buck-converter.html">Buck converter explorer ↗</a><a href="/projects.html">Project records ↗</a></div>
    </article>
'''%(p['date'],p['title'],p['date'],p['date'],p['read_time'],tags,toc_html,p['body'])
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
    <section class="section about-direction"><div class="wrap"><div class="section-heading split-heading"><div><span class="section-index">02 / RESEARCH DIRECTION</span><h2>Questions that cross<br><em>disciplinary boundaries.</em></h2></div><p>Areas of curiosity—not published research contributions.</p></div><div class="research-lines"><article><span>01</span><h3>Digital power conversion</h3><p>How embedded control and power-stage dynamics shape converter behavior.</p></article><article><span>02</span><h3>Energy instrumentation</h3><p>How measurement quality changes the decisions a system can make.</p></article><article><span>03</span><h3>Intelligent electrical systems</h3><p>How connected hardware can improve visibility and control of energy use.</p></article></div></div></section>
    <section class="section about-profile"><div class="wrap about-profile-grid"><div><span class="section-index">03 / PROFILE</span><h2>Academic foundation.</h2><p class="about-profile-lede">The detail that matters is the work and study behind the title.</p></div><dl class="profile-facts"><div><dt>Name</dt><dd>Muhammad Shahzaib Abbas</dd></div><div><dt>Current status</dt><dd>Electrical Engineering undergraduate</dd></div><div><dt>Institution</dt><dd>National University of Sciences and Technology (NUST), Pakistan</dd></div><div><dt>Academic direction</dt><dd>Power engineering</dd></div><div><dt>Complementary interests</dt><dd>Embedded systems · electronics · control</dd></div></dl></div></section>
    <section class="section about-now"><div class="wrap about-now-grid"><div><span class="section-index">04 / CURRENT PRACTICE</span><h2>Learn it.<br><em>Connect it. Document it.</em></h2></div><div><p>Current work is about developing a rigorous foundation and learning to move between circuit behavior, power flow, embedded decisions, and clear technical documentation. The public project index separates planned directions from artifacts that have actually been produced.</p><a class="text-link" href="/projects.html">See project status <b>↗</b></a></div></div></section>
    <section class="section"><div class="wrap"><div class="collaboration-card"><span class="section-index">05 / CONNECT</span><h2>Good engineering starts with a good question.</h2><p>Open to academic discussion, research conversations, internships, and appropriately scoped engineering collaboration.</p><a class="btn btn-primary" href="/contact.html">Start a conversation ↗</a></div></div></section>
'''
    about_ld=json.loads(SCHEMA_GRAPH)
    about_ld['@graph'].append({'@type':'Person','@id':'https://elitebotstudios.me/about.html#founder','name':'Muhammad Shahzaib Abbas','url':'https://elitebotstudios.me/about.html','email':EMAIL,'jobTitle':'Electrical Engineering undergraduate','affiliation':{'@type':'CollegeOrUniversity','name':'National University of Sciences and Technology (NUST)','address':{'@type':'PostalAddress','addressCountry':'PK'}},'knowsAbout':['Power engineering','Embedded systems','Electronics','Microcontrollers','Control systems','Intelligent energy systems']})
    page('About Muhammad Shahzaib Abbas | Elite Bot Studios','Muhammad Shahzaib Abbas studies Electrical Engineering at NUST, Pakistan, with an academic direction in power engineering and interests in embedded systems, electronics, and control.','/about.html',body,jsonld=json.dumps(about_ld,indent=2))


# ----------------------------------------------------------------- contact --
CONTACT_FORM_JS = '''
  <script>
    (function(){
      function initContactComposer(){
      var form=document.getElementById('contactForm');if(!form)return;var status=document.getElementById('formStatus');
      function field(el,msg){var box=el.closest('.field');if(!box)return false;var error=box.querySelector('.err');el.setAttribute('aria-invalid',msg?'true':'false');if(error)error.textContent=msg||'';return !msg;}
      function validate(el){var v=(el.value||'').trim();if(el.required&&!v)return field(el,'This field is required.');if(el.type==='email'&&v&&!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(v))return field(el,'Enter a valid email address.');if(el.tagName==='TEXTAREA'&&v.length<20)return field(el,'Please add at least 20 characters.');return field(el,'');}
      Array.prototype.forEach.call(form.elements,function(el){if(!el.name)return;el.addEventListener('blur',function(){validate(el);});el.addEventListener('input',function(){if(el.getAttribute('aria-invalid')==='true')validate(el);});});
      form.addEventListener('submit',function(ev){ev.preventDefault();var ok=true,first=null;Array.prototype.forEach.call(form.elements,function(el){if(!el.name)return;if(!validate(el)){ok=false;if(!first)first=el;}});if(!ok){status.textContent='Please review the highlighted fields.';if(first)first.focus();return;}
        var data=new FormData(form);var lines=['Name: '+data.get('name'),'Email: '+data.get('email'),'Organization / university: '+(data.get('organization')||'Not provided'),'Inquiry: '+data.get('category'),'','Message:',data.get('message')];
        window.location.href='mailto:contact@elitebotstudios.me?subject='+encodeURIComponent('Elite Bot Studios — '+data.get('category'))+'&body='+encodeURIComponent(lines.join('\\n'));
        status.textContent='Your email app should open with a draft. Review it and press Send there; this website has not received or sent your message.';
      });
      }
      if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initContactComposer,{once:true});else initContactComposer();
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
    services(); projects(); project_detail_pages(); lab_index(); lab_posts(); expertise(); about(); contact()
    privacy(); terms(); cookies(); notfound(); offline()
    print('done.')
