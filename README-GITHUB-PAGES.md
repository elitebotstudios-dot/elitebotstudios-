# Elite Bot Studios — website repository

Static, accessible engineering portfolio for **Elite Bot Studios**. The site documents the development of Muhammad Shahzaib Abbas, an Electrical Engineering undergraduate at NUST, Pakistan, with academic focus in power engineering and interests in embedded systems and intelligent hardware.

**Live:** <https://elitebotstudios.me> (primary). The Vercel alias <https://elitebotstudios.vercel.app> serves the same build and is not a canonical target.

## Site structure

- `index.html` — studio identity, interactive conceptual power-control system, engineering disciplines, project direction, founder profile, and lab preview.
- `projects.html` + `projects.json` — evidence-labelled project records. A nested `case_study` object generates `/projects/<slug>.html` and supports requirements, sensing/controller options, isolation notes, validation strategy and a staged roadmap. The Smart Energy Monitoring record is explicitly a concept.
- `project-template.html` — the public case-study standard, with a download of the blank Markdown template (`project-template.md`).
- `projects/power-stage-utility.html` — published software demonstration: an ideal buck sizing module with `assets/powerstage.js`, its UI, formulas, limits and reference tests. Clearly attributed as AI-assisted work produced for this site.
- `expertise.html` — connected knowledge areas with evidence labels, no proficiency percentages.
- `lab.html` and `content/lab-notes/*.md` — Markdown-authored technical notes. The index, homepage previews, sitemap and reading times are all generated from the same files.
- `services.html` — Collaboration page: who gets in touch, and what is in or out of scope.
- `tools.html` and `tools/*.html` — seven client-side engineering models: buck-converter explorer, PWM signal laboratory, trace width, linear regulator thermal, voltage divider, LED resistor, RC time constant.
- `about.html`, `contact.html`, legal pages, `404.html`, `offline.html`.
- `api/contact.js` — optional Vercel serverless function for contact delivery (see below).
- `assets/site.css`, `assets/site.js`, `assets/calc.js` — shared design and behaviour.
- `sw.js`, `sitemap.xml`, `robots.txt`, `llms.txt`, `vercel.json` — discovery, offline support, hosting config.

## Local development

There is no bundler or framework. Serve the repository root and open the pages:

```sh
python3 -m http.server 8080 --bind 0.0.0.0
```

## Build and regenerate

All HTML is generated. Edit content or templates, then rebuild:

```sh
python3 scripts/site/pages.py        # inner pages, project records, template page
python3 scripts/site/build_index.py  # homepage
python3 scripts/site/build_tools.py  # tools hub + six calculators
python3 scripts/build_sitemap.py     # sitemap from canonical tags
```

## Tests

```sh
python3 scripts/audit_site.py            # routes, nav, metadata, links, sitemap, reading-time and lab/project sync
node --check assets/site.js
node --check assets/calc.js
node --check sw.js
node tests/projects.test.js              # project renderer + hero system tabs
node tests/powerstage.test.js            # power-stage sizing reference cases and rejections
node tests/calculators.test.js           # calculator maths and boundaries
node tests/contact-api.test.js           # contact endpoint validation and fallback
python3 tests/notes.test.py              # Markdown pipeline
```

Browser tests (Playwright, optional, not a repository dependency) live outside the repo in the QA workspace: interactive behaviour, all six calculators, axe accessibility, responsive overflow, and Lighthouse.

## Adding content

- **Project:** copy the JSON shape from `project-template.md` into `projects.json`. Add a nested `case_study` object to generate a detail page; only populated sections render. Rebuild and run `scripts/audit_site.py`.
- **Lab note:** add a Markdown file to `content/lab-notes/` with `slug`, `title`, `date`, `tags`, `description` front matter. Rebuild; index, homepage previews, sitemap and read time update automatically.
- **Calculator:** add an entry to `scripts/site/build_tools.py`, a pure function and DOM wiring in `assets/calc.js`, then rebuild and add a reference case to `tests/calculators.test.js`.

## Contact delivery

The form posts JSON to `/api/contact`. The endpoint:

- validates name, email, category and message server-side;
- silently discards honeypot submissions;
- sends through Resend when `RESEND_API_KEY` and `CONTACT_TO` are set in the Vercel project;

To enable delivery, set these environment variables in Vercel (Project → Settings → Environment Variables) and redeploy:

| Variable | Purpose |
|---|---|
| `RESEND_API_KEY` | API key from resend.com |
| `CONTACT_TO` | inbox that receives enquiries |
| `CONTACT_FROM` | optional verified sender, e.g. `Elite Bot Studios <website@elitebotstudios.me>` |

Until they exist the endpoint returns `503 not_configured` and the page opens a local email draft instead, stating plainly that nothing was transmitted. The form never reports delivery it cannot verify. The destination mailbox itself must also be confirmed by the owner as receiving mail.

## Deploy

Vercel builds from the private GitHub repository's `main` branch. Use the authorized `deploy.sh` workflow. Never commit credentials, force-push, or change repository visibility.

After deploying, verify beyond the homepage: request every route on both hosts and compare the `ebs-build` meta tag, then confirm legacy URLs still return 404.
