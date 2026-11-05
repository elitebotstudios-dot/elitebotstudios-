# Elite Bot Studios — website repository

Static, accessible engineering portfolio for **Elite Bot Studios**. The site documents the development of Muhammad Shahzaib Abbas, an Electrical Engineering undergraduate at NUST, Pakistan, with academic focus in power engineering and interests in embedded systems and intelligent hardware.

**Live:** <https://elitebotstudios.me>

## Site structure

- `index.html` — studio identity, interactive conceptual power-control system, engineering disciplines, project direction, founder profile, and lab preview.
- `projects.html` + `projects.json` — evidence-labelled project records; nested `case_study` data generates dedicated `/projects/<slug>.html` pages. The current Smart Energy Monitoring record is explicitly a concept.
- `expertise.html` — academic focus, current learning, and research interests, without proficiency percentages.
- `lab.html` and `content/lab-notes/*.md` — four Markdown-authored technical notes with equations, code highlighting, tables, references, reading progress, and generated tables of contents.
- `services.html` — capabilities and collaboration areas; not a claim of established consultancy delivery.
- `tools.html` and `tools/*.html` — six client-side engineering models, including an interactive ideal-CCM buck explorer with synchronized controls, live PWM/current plots, and an explicit DCM boundary.
- `about.html`, `contact.html`, legal pages, `404.html`, and `offline.html`.
- `assets/site.css`, `assets/site.js`, and `assets/calc.js` — shared design and browser behaviour.
- `sw.js`, `sitemap.xml`, `robots.txt`, `llms.txt`, and `vercel.json` — discoverability, offline support, and hosting configuration.

## Edit and regenerate

Content sources live in `content/lab-notes/`, `projects.json`, and the page generator scripts in `scripts/site/`. Run from the repository root:

```sh
python3 scripts/site/pages.py
python3 scripts/site/build_index.py
python3 scripts/site/build_tools.py
python3 scripts/build_sitemap.py
node --check assets/site.js
node --check assets/calc.js
node tests/projects.test.js
node tests/calculators.test.js
python3 tests/notes.test.py
```

Use `HOW-TO-ADD-A-PROJECT.md` and `project-template.md` for project records. Read `content/README.md` to author a lab note. New notes are authored in Markdown, not in generated HTML.

## Contact behaviour

The contact page validates the form in the browser and opens a prefilled `mailto:` draft. The visitor must press Send in their own email client. The website does **not** transmit the form or confirm email delivery. A server-side form provider can be added later after the owner selects and authorizes one.

## Deploy

The site is deployed to Vercel from the private GitHub repository's `main` branch. Use the existing authorized `deploy.sh` workflow. Never commit credentials, force-push, or change repository visibility.
