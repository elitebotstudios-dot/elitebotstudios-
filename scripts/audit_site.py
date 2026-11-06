#!/usr/bin/env python3
"""Static regression audit for the built site.

Checks the things that have actually broken before: missing routes, mismatched
navigation, duplicate/missing metadata, dead internal links, stale sitemap
entries, orphaned lab notes or project records, and leftover placeholder copy.

Usage:  python3 scripts/audit_site.py
Exit code 1 on any failure.
"""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://elitebotstudios.me'
errors = []
notes = []


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.headings = []
        self.canonical = []
        self.title = None
        self.description = None
        self.nav_top = []
        self.nav_mobile = []
        self.in_title = False
        self.in_nav = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'title':
            self.in_title = True
        if tag == 'meta' and a.get('name') == 'description':
            self.description = a.get('content', '')
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a.get('href', ''))
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.headings.append(int(tag[1]))
        if tag == 'nav':
            self.in_nav = a.get('aria-label')
        if tag == 'a':
            href = a.get('href', '')
            if self.in_nav == 'Primary':
                self.nav_top.append(href)
            elif self.in_nav == 'Mobile':
                self.nav_mobile.append(href)
            if href.startswith('/') and not href.startswith('//'):
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'nav':
            self.in_nav = None

    def handle_data(self, data):
        if self.in_title:
            self.title = (self.title or '') + data


pages = {}
for f in sorted(ROOT.rglob('*.html')):
    if '.git' in f.parts:
        continue
    rel = '/' + str(f.relative_to(ROOT))
    rel = rel.replace('/index.html', '/')
    p = Page()
    p.feed(f.read_text(encoding='utf-8'))
    pages[rel] = (p, f)

# --- required routes -------------------------------------------------------
REQUIRED = [
    '/', '/projects.html', '/projects/smart-energy-monitoring.html',
    '/expertise.html', '/lab.html', '/tools.html', '/tools/trace-width.html',
    '/tools/buck-converter.html', '/tools/linear-regulator.html',
    '/tools/voltage-divider.html', '/tools/led-resistor.html',
    '/tools/rc-time-constant.html', '/about.html', '/contact.html',
    '/services.html', '/privacy.html', '/terms.html', '/cookies.html',
    '/404.html', '/offline.html', '/project-template.html',
]
for route in REQUIRED:
    if route not in pages:
        errors.append('missing required page: ' + route)

# --- nav consistency -------------------------------------------------------
navs = {r: (p.nav_top, p.nav_mobile) for r, (p, _) in pages.items()}
reference = navs.get('/')
if reference:
    for route, nav in navs.items():
        if nav[1] and reference[1] and sorted(set(nav[1])) != sorted(set(reference[1])):
            errors.append('mobile nav differs on ' + route)
        if nav[0] and reference[0] and nav[0] != reference[0]:
            errors.append('desktop nav differs on ' + route)

# --- per-page checks -------------------------------------------------------
titles, descriptions = {}, {}
for route, (p, file) in pages.items():
    text = file.read_text(encoding='utf-8')
    if not p.title or not p.title.strip():
        errors.append('missing <title>: ' + route)
    elif p.title in titles:
        errors.append('duplicate title: %s and %s' % (route, titles[p.title]))
    else:
        titles[p.title] = route
    if not p.description:
        errors.append('missing meta description: ' + route)
    elif p.description in descriptions:
        errors.append('duplicate description: %s and %s' % (route, descriptions[p.description]))
    else:
        descriptions[p.description] = route
    if len(p.canonical) > 1:
        errors.append('multiple canonicals: ' + route)
    noindex = 'name="robots" content="noindex"' in text
    if route not in ('/404.html', '/offline.html') and not noindex:
        if len(p.canonical) != 1:
            errors.append('missing canonical: ' + route)
        elif not p.canonical[0].startswith(SITE):
            errors.append('canonical not on primary domain: %s (%s)' % (route, p.canonical[0]))
    if sum(1 for h in p.headings if h == 1) != 1:
        errors.append('expected exactly one h1: ' + route)
    if 'data-owner="TODO"' in text:
        errors.append('public TODO marker: ' + route)
    for bad in ('Calendly', 'lead generation', 'HVAC', 'CRM automation', 'AI business automation'):
        if bad.lower() in text.lower():
            errors.append('legacy agency copy (%s): %s' % (bad, route))
    for href in p.links:
        path, _, frag = href.partition('#')
        path = path.split('?')[0]
        target = ROOT / 'index.html' if path in ('', '/') else ROOT / path.lstrip('/')
        if not target.exists():
            errors.append('dead internal link %s on %s' % (href, route))
            continue
        if frag and target.suffix == '.html':
            tp = Page()
            tp.feed(target.read_text(encoding='utf-8'))
            if frag not in tp.ids and not (target.name == 'projects.html' and frag == 'smart-energy-monitoring'):
                errors.append('missing anchor target %s on %s' % (href, route))

# --- content synchronisation ----------------------------------------------
projects = json.loads((ROOT / 'projects.json').read_text(encoding='utf-8'))
for project in projects:
    if '/projects/%s.html' % project['slug'] not in pages:
        errors.append('project record page missing: ' + project['slug'])
    if project['title'] not in (ROOT / 'projects.html').read_text(encoding='utf-8'):
        errors.append('project missing from index: ' + project['slug'])

note_slugs = set()
for md in (ROOT / 'content' / 'lab-notes').glob('*.md'):
    front = md.read_text(encoding='utf-8').split('---')[1]
    slug = re.search(r'^slug:\s*(.+)$', front, re.M)
    if slug:
        note_slugs.add(slug.group(1).strip())
        if '/lab/%s.html' % slug.group(1).strip() not in pages:
            errors.append('lab note not generated: ' + slug.group(1).strip())
for route in pages:
    if route.startswith('/lab/') and route != '/lab.html':
        slug = route[len('/lab/'):-len('.html')]
        if slug not in note_slugs:
            errors.append('orphan lab page: ' + route)
for slug in note_slugs:
    if slug not in (ROOT / 'lab.html').read_text(encoding='utf-8'):
        errors.append('lab note missing from index: ' + slug)

# --- reading-time consistency ---------------------------------------------
index_html = (ROOT / 'index.html').read_text(encoding='utf-8')
lab_html = (ROOT / 'lab.html').read_text(encoding='utf-8')
def minutes(pattern, text, label):
    found = dict()
    for slug, value in re.findall(pattern, text):
        found[slug] = int(value)
    return found

article_times = {}
for slug in note_slugs:
    page = ROOT / 'lab' / (slug + '.html')
    m = re.search(r'(\d+) min read', page.read_text(encoding='utf-8'))
    if m:
        article_times[slug] = int(m.group(1))

def card_times(text):
    found = {}
    for slug in note_slugs:
        i = text.find('/lab/%s.html' % slug)
        if i == -1:
            continue
        window = text[i:i + 1400]
        m = re.search(r'(\d+)\s*(?:MIN READ|MIN\b|min read)', window, re.I)
        if m:
            found[slug] = int(m.group(1))
    return found

home_times = card_times(index_html)
lab_times = card_times(lab_html)
if not home_times:
    errors.append('no reading-time cards found on the homepage')
if len(lab_times) != len(note_slugs):
    errors.append('lab index shows %d of %d notes' % (len(lab_times), len(note_slugs)))
for slug, minutes_value in article_times.items():
    if slug in home_times and home_times[slug] != minutes_value:
        errors.append('reading time mismatch for %s: homepage %s vs article %s' % (slug, home_times[slug], minutes_value))
    if slug in lab_times and lab_times[slug] != minutes_value:
        errors.append('reading time mismatch for %s: lab %s vs article %s' % (slug, lab_times[slug], minutes_value))
notes.append('reading times checked: %d articles, %d home cards, %d lab cards' % (len(article_times), len(home_times), len(lab_times)))

# --- calculator page wiring ----------------------------------------------
for route in [r for r in pages if r.startswith('/tools/')]:
    text = (ROOT / route.lstrip('/')).read_text(encoding='utf-8')
    for required in ('id="calcOut"', 'id="calcNote"', 'data-calc=', 'assets/calc.js'):
        if required not in text:
            errors.append('calculator page %s missing %s' % (route, required))

# --- sitemap ---------------------------------------------------------------
sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
locs = re.findall(r'<loc>([^<]+)</loc>', sitemap)
if len(locs) != len(set(locs)):
    errors.append('duplicate sitemap URLs')
for loc in locs:
    path = loc.replace(SITE, '') or '/'
    if path not in pages:
        errors.append('sitemap points at missing page: ' + loc)
    elif path in ('/404.html', '/offline.html'):
        errors.append('sitemap includes non-indexable page: ' + loc)
for route in pages:
    if route in ('/404.html', '/offline.html'):
        continue
    # a noindex page must NOT be in the sitemap: including it would be the defect
    target = ROOT / (route.lstrip('/') or 'index.html')
    if target.is_dir():
        target = target / 'index.html'
    is_noindex = target.is_file() and 'name="robots" content="noindex"' in target.read_text(encoding='utf-8')
    if is_noindex:
        if SITE + route in locs:
            errors.append('noindex page listed in sitemap: ' + route)
        continue
    if SITE + route not in locs and (SITE + route + '.html') not in locs and route != '/':
        errors.append('page missing from sitemap: ' + route)

# --- service worker precache ----------------------------------------------
sw = (ROOT / 'sw.js').read_text(encoding='utf-8')
for path in re.findall(r"'([^']+\.(?:html|css|js|json|webp|png|svg|md|webmanifest))'", sw):
    if not path.startswith('/'):
        continue
    target = ROOT / path.lstrip('/')
    if not target.exists():
        errors.append('service worker precaches missing file: ' + path)

print('pages audited:', len(pages))
print('lab notes:', len(note_slugs), '| projects:', len(projects), '| sitemap urls:', len(locs))
for note in notes:
    print('note:', note)
if errors:
    print('\nFAILURES (%d):' % len(errors))
    for e in errors:
        print(' -', e)
    sys.exit(1)
print('PASS: routes, navigation, metadata, links, content sync, sitemap and precache')
