# -*- coding: utf-8 -*-
"""Generates every page of elitebotstudios.me from one shell, so the nav,
footer, head and metadata can never drift apart between pages."""
import os, re

from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = str(ROOT)
SITE = 'https://elitebotstudios.me'
SITE_BUILD = 'EBS-2026.11.05-R6'
EMAIL = 'contact@elitebotstudios.me'
TAGLINE = 'Embedded Intelligence · Real-World Power'
ONELINER = ('An independent engineering initiative exploring embedded systems, power electronics, and '
            'intelligent hardware through practical designs, simulations, prototypes, and documented projects.')

CHIP = ('<svg viewBox="0 0 64 64" aria-hidden="true" focusable="false">'
        '<path d="M32 11.5 50 22v20L32 52.5 14 42V22z" fill="none" stroke="#D4AF37" '
        'stroke-width="3" stroke-linejoin="round"/>'
        '<text x="32" y="39" text-anchor="middle" font-family="ui-monospace, Menlo, monospace" '
        'font-size="19" font-weight="700" fill="#D4AF37">EB</text></svg>')

GH_ICON = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
           '<path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34'
           '-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.36 1.09 '
           '2.94.83.09-.65.35-1.09.63-1.34-2.22-.25-4.56-1.11-4.56-4.95 0-1.09.39-1.99 1.03-2.69-.1-.25-.45'
           '-1.27.1-2.65 0 0 .84-.27 2.75 1.03a9.4 9.4 0 0 1 5 0c1.91-1.3 2.75-1.03 2.75-1.03.55 1.38.2 2.4'
           '.1 2.65.64.7 1.03 1.6 1.03 2.69 0 3.85-2.34 4.7-4.57 4.95.36.31.68.92.68 1.85v2.74c0 .27.18.58.69'
           '.48A10 10 0 0 0 12 2z"/></svg>')

LI_ICON = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
           '<path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-.95 1.83'
           '-1.95 3.77-1.95 4.03 0 4.78 2.5 4.78 5.75V21h-4v-5.6c0-1.34-.02-3.06-1.87-3.06-1.87 0-2.16 1.45'
           '-2.16 2.96V21H9z"/></svg>')

# ---------------------------------------------------------------------------
# Asset fingerprinting.
#
# None of these filenames are content-hashed, and a CDN or browser that has
# already cached /assets/site.css will keep serving it long after the file
# changes. Appending ?v=<content hash> gives every revision its own URL, so a
# changed file is fetched immediately and an unchanged one is never
# re-downloaded. Without this, a stylesheet fix can be invisible for days.
# ---------------------------------------------------------------------------
import hashlib, os as _os

ASSET_ROOT = str(ROOT)
_hashes = {}


def asset(rel):
    """Return /assets/... with a short content hash appended."""
    rel = rel.lstrip('/')
    path = _os.path.join(ASSET_ROOT, rel)
    if rel not in _hashes:
        try:
            with open(path, 'rb') as fh:
                _hashes[rel] = hashlib.sha256(fh.read()).hexdigest()[:8]
        except OSError:
            _hashes[rel] = '0'
    return '/%s?v=%s' % (rel, _hashes[rel])


# ---------------------------------------------------------------------------
# Structured data. One @graph, emitted by every page that carries schema, so
# the organisation is described identically wherever it appears. Kept here and
# not inline in the pages, because pages are regenerated and would otherwise
# silently lose it.
# ---------------------------------------------------------------------------
SCHEMA_GRAPH = r'''{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://elitebotstudios.me/#organization",
      "name": "Elite Bot Studios",
      "url": "https://elitebotstudios.me/",
      "email": "contact@elitebotstudios.me",
      "logo": "https://elitebotstudios.me/assets/logo-512.png",
      "description": "An independent engineering initiative focused on embedded systems, power electronics, and intelligent hardware, explored through practical designs, simulations, prototypes, and documented projects."
    },
    {
      "@type": "WebSite",
      "@id": "https://elitebotstudios.me/#website",
      "url": "https://elitebotstudios.me/",
      "name": "Elite Bot Studios",
      "inLanguage": "en",
      "publisher": { "@id": "https://elitebotstudios.me/#organization" }
    }
  ]
}'''

NAV_LINKS = [('/projects.html', 'Projects'), ('/expertise.html', 'Expertise'),
             ('/lab.html', 'Engineering Lab'), ('/about.html', 'About'), ('/tools.html', 'Tools')]


def head(title, desc, path, extra_head='', og_image='/assets/social-preview.png',
         jsonld=None, canonical=None):
    # canonical='' means the page must not declare one (404, offline)
    no_canon = canonical == ''
    canon = (SITE + path) if canonical is None else canonical
    ld = ''
    if jsonld:
        ld = '\n  <script type="application/ld+json">\n  %s\n  </script>\n' % jsonld
    return '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
{canon_tag}

  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Elite Bot Studios" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
{ogurl_tag}
  <meta property="og:image" content="{site}{og}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{desc}" />
  <meta name="twitter:image" content="{site}{og}" />

  <link rel="icon" href="{fav32}" sizes="32x32" />
  <link rel="icon" href="{fav16}" sizes="16x16" />
  <link rel="apple-touch-icon" href="{apple}" />
  <link rel="manifest" href="{manifest}" />
  <meta name="theme-color" content="#080B10" />
  <meta name="ebs-build" content="{build_id}" />

  <link rel="stylesheet" href="{css_href}" />
{extra}
  <!-- GA4 is queued immediately, then loaded in idle time so it does not compete with the first render. -->
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-HLQ4G5HBMZ');
    (function deferAnalytics(){{
      var started = false;
      function load() {{
        if (started) return;
        started = true;
        var script = document.createElement('script');
        script.async = true;
        script.src = 'https://www.googletagmanager.com/gtag/js?id=G-HLQ4G5HBMZ';
        document.head.appendChild(script);
      }}
      setTimeout(function () {{
        if ('requestIdleCallback' in window) requestIdleCallback(load, {{ timeout: 2000 }});
        else load();
      }}, 6000);
    }})();
  </script>{ld}</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
'''.format(title=title, desc=desc, canon=canon, site=SITE, og=og_image, build_id=SITE_BUILD,
           extra=extra_head, ld=ld,
           css_href=asset('assets/site.css'),
           fav32=asset('assets/favicon-32x32.png'),
           fav16=asset('assets/favicon-16x16.png'),
           apple=asset('assets/apple-touch-icon.png'),
           manifest=asset('site.webmanifest'),
           canon_tag=('' if no_canon else '<link rel="canonical" href="%s" />' % canon),
           ogurl_tag=('' if no_canon else '<meta property="og:url" content="%s" />' % canon))


def header(current):
    def link(href, label):
        cur = ' aria-current="page"' if href == current else ''
        return '        <a href="%s"%s>%s</a>' % (href, cur, label)
    desktop = '\n'.join(link(h, l) for h, l in NAV_LINKS)
    mobile = '\n'.join('          <li>%s</li>' % link(h, l).strip()
                       for h, l in NAV_LINKS + [('/contact.html', 'Contact')])
    return '''
  <header class="nav">
    <div class="wrap nav-inner">
      <a class="brand" href="/">
        %s
        <span class="brand-word">Elite Bot Studios</span>
      </a>
      <nav class="nav-links" aria-label="Primary">
%s
      </nav>
      <div class="nav-actions">
        <a class="btn btn-amber" href="/contact.html">Contact</a>
        <button class="hamburger" type="button" id="navToggle" aria-expanded="false" aria-controls="mobileMenu" aria-label="Open menu">
          <span></span><span></span><span></span>
        </button>
      </div>
    </div>
    <div class="mobile-menu" id="mobileMenu" data-open="false">
      <nav aria-label="Mobile">
        <ul>
%s
        </ul>
      </nav>
    </div>
  </header>
''' % (CHIP, desktop, mobile)


def footer():
    return '''
  <footer class="footer">
    <div class="wrap footer-grid">
      <div>
        <p class="footer-tag">%s</p>
        <p>%s</p>
      </div>
      <div>
        <h3>Explore</h3>
        <ul class="footer-links">
          <li><a href="/projects.html">Projects</a></li>
          <li><a href="/expertise.html">Expertise</a></li>
          <li><a href="/lab.html">Engineering Lab</a></li>
          <li><a href="/tools.html">Engineering Tools</a></li>
          <li><a href="/services.html">Collaboration</a></li>
          <li><a href="/about.html">About</a></li>
        </ul>
      </div>
      <div>
        <h3>Connect</h3>
        <ul class="footer-links">
          <li><a href="/contact.html">Contact</a></li>
          <li><!--email_off--><a href="mailto:%s">%s</a><!--/email_off--></li>
          <li><a href="/privacy.html">Privacy</a></li>
          <li><a href="/terms.html">Terms</a></li>
          <li><a href="/cookies.html">Cookies</a></li>
        </ul>
      </div>
    </div>
    <div class="wrap footer-bottom">
      <span>Pakistan · Independent engineering initiative</span>
      <span>&copy; 2026 Elite Bot Studios</span>
    </div>
  </footer>

  <script src="%s" defer></script>
</body>
</html>
''' % (TAGLINE, ONELINER, EMAIL, EMAIL, asset('assets/site.js'))


def write(path, html):
    html='\n'.join(line.rstrip() for line in html.splitlines())+'\n'
    full = os.path.join(OUT, path.lstrip('/'))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(html)
    print('  wrote', path, len(html), 'bytes')


def page(title, desc, path, body, jsonld=None, extra_head='', canonical=None):
    return write(path, head(title, desc, path, extra_head=extra_head, jsonld=jsonld,
                            canonical=canonical)
                 + header(path) + '\n  <main id="main">\n' + body + '\n  </main>\n' + footer())
