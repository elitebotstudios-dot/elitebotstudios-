#!/usr/bin/env python3
"""Rebuild sitemap.xml from generated canonical HTML pages."""
from pathlib import Path
from datetime import date
from html.parser import HTMLParser
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

ROOT=Path(__file__).resolve().parents[1]
SITE='https://elitebotstudios.me'
class CanonicalParser(HTMLParser):
    canonical=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='link' and a.get('rel')=='canonical': self.canonical=a.get('href')

urls=set()
for f in ROOT.rglob('*.html'):
    if f.name in ('404.html','offline.html'): continue
    raw = f.read_text(encoding='utf-8')
    # A noindex page is not a page of the site — a print source, for example —
    # so its canonical must not pull its target into the sitemap.
    if 'name="robots" content="noindex"' in raw: continue
    parser=CanonicalParser(); parser.feed(raw)
    url=parser.canonical
    if url and url.startswith(SITE): urls.add(url)
register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
root=Element(ns+'urlset')
for url in sorted(urls):
    entry=SubElement(root,ns+'url'); SubElement(entry,ns+'loc').text=url
    SubElement(entry,ns+'lastmod').text=date.today().isoformat()
    path=url.removeprefix(SITE)
    if path in ('','/'): freq,priority='monthly','1.0'
    elif path in ('/projects.html','/expertise.html','/lab.html','/tools.html'): freq,priority='weekly','0.9'
    elif path.startswith('/lab/'): freq,priority='yearly','0.6'
    elif path in ('/contact.html','/about.html'): freq,priority='monthly','0.8'
    elif path.startswith('/tools/'): freq,priority='monthly','0.7'
    else: freq,priority='yearly','0.3'
    SubElement(entry,ns+'changefreq').text=freq; SubElement(entry,ns+'priority').text=priority
ElementTree(root).write(ROOT/'sitemap.xml',encoding='utf-8',xml_declaration=True)
print('Wrote sitemap.xml with %d canonical URLs' % len(urls))
