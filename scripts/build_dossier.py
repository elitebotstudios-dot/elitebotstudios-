#!/usr/bin/env python3
"""Render the technical dossier from its Markdown source into a print page.

The Markdown file is the maintainable source. This script turns it into a
self-contained, print-styled HTML page; a headless browser then prints that page
to the downloadable PDF. Nothing is authored twice: the PDF, the print page and
the .md all come from `energy-monitor/docs/dossier.md`.

    python3 scripts/build_dossier.py

Outputs
    energy-monitor/docs/dossier-print.html   print-styled page (also the PDF source)
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'site'))
from notes import render_markdown  # noqa: E402  (same renderer as the lab notes)

SOURCE = ROOT / 'energy-monitor' / 'docs' / 'dossier.md'
OUT = ROOT / 'energy-monitor' / 'docs' / 'dossier-print.html'

PRINT_CSS = """
  @page { size: A4; margin: 18mm 16mm 20mm 16mm; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #fff; color: #14181c;
         font-family: 'Georgia', 'Times New Roman', serif; font-size: 10.4pt; line-height: 1.62; }
  .page { max-width: 190mm; margin: 0 auto; padding: 0; }
  .doc-head { border-bottom: 2px solid #1b3a49; padding-bottom: 10mm; margin-bottom: 8mm; }
  .doc-head .kicker { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 7.6pt;
                      letter-spacing: .18em; text-transform: uppercase; color: #3f4c56; }
  .doc-head .meta { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 8.4pt;
                    color: #3f4c56; margin-top: 6mm; }
  h1 { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 22pt; line-height: 1.14;
       margin: 6mm 0 2mm; letter-spacing: -.02em; color: #0f1c24; }
  h2 { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 12.4pt; margin: 9mm 0 3mm;
       color: #0f1c24; border-bottom: 1px solid #d3dbe1; padding-bottom: 1.6mm;
       page-break-after: avoid; }
  h3 { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10.6pt; margin: 6mm 0 2mm;
       color: #1b3a49; page-break-after: avoid; }
  p { margin: 0 0 3mm; }
  ul, ol { margin: 0 0 3mm; padding-left: 6mm; }
  li { margin-bottom: 1.4mm; }
  strong { color: #0f1c24; }
  code { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 8.8pt;
         background: #f2f5f7; padding: .4mm 1.2mm; border-radius: 1mm; }
  pre { background: #f6f8f9; border: 1px solid #dde4e9; border-left: 3px solid #1b3a49;
        padding: 3mm 4mm; overflow-x: auto; page-break-inside: avoid; margin: 0 0 4mm; }
  pre code { background: none; font-size: 8.2pt; line-height: 1.5; color: #22323d; }
  table { width: 100%; border-collapse: collapse; font-family: 'Helvetica Neue', Arial, sans-serif;
          font-size: 8.4pt; margin: 0 0 4mm; page-break-inside: avoid; }
  th { background: #edf2f5; text-align: left; padding: 1.8mm 2.4mm; border: 1px solid #cdd7de;
       font-weight: 600; color: #0f1c24; }
  td { padding: 1.6mm 2.4mm; border: 1px solid #dde4e9; vertical-align: top; }
  tbody tr:nth-child(even) td { background: #fafcfd; }
  hr { border: 0; border-top: 1px solid #d3dbe1; margin: 8mm 0; }
  a { color: #1b5b6e; text-decoration: none; }
  .doc-foot { margin-top: 10mm; padding-top: 4mm; border-top: 1px solid #d3dbe1;
              font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 7.8pt; color: #3f4c56; }
  h2 + p, h3 + p { page-break-before: avoid; }
"""


def main():
    text = SOURCE.read_text(encoding='utf-8')
    body = render_markdown(text)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Smart DC Energy Monitor — Engineering Design and Verification Report</title>
<meta name="description" content="Technical dossier for Project 01: software model, KiCad schematic, ESP32 firmware and their verification. Elite Bot Studios.">
<link rel="canonical" href="https://elitebotstudios.me/assets/dossier-smart-dc-energy-monitor.pdf">
<meta name="robots" content="noindex">
<meta name="ebs-print-source" content="true">
<style>{PRINT_CSS}</style>
</head>
<body>
<div class="page">
  <header class="doc-head">
    <span class="kicker">Elite Bot Studios &middot; Project 01 &middot; Technical dossier</span>
    <div class="meta">Revision B &middot; generated {date.today().isoformat()} from
      energy-monitor/docs/dossier.md &middot; software verified, hardware designed,
      prototype not built</div>
  </header>
  <main id="dossier">
  {body}
  </main>
  <footer class="doc-foot">
    Prepared with AI assistance as part of the Elite Bot Studios website. Not a
    body of independently authored personal engineering work; see section 13.
    No hardware measurement, calibration or accuracy claim is made anywhere in
    this report.
  </footer>
</div>
</body>
</html>
"""
    OUT.write_text(html, encoding='utf-8')
    print('  wrote %s (%d bytes)' % (OUT.relative_to(ROOT), len(html)))


if __name__ == '__main__':
    main()
