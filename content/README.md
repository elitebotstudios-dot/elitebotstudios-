# Content authoring

## Engineering Lab notes

Add a Markdown file under `content/lab-notes/` with this front matter:

```yaml
---
slug: example-note
title: A short technical title
date: 2026-11-05
tags: [embedded systems, testing]
description: One factual sentence used in the lab index and search metadata.
---
```

Write the article below the closing `---`. A dependency-free renderer supports headings (`##`/`###`), paragraphs, lists, blockquotes, fenced code, inline code/links/emphasis, inline and display equations, same-site asset images (`![alt](/assets/file.png)`), horizontal rules, and simple pipe tables. Raw HTML is escaped. Keep claims tied to real files, a stated model, or documented measurements; distinguish simulation from bench results.

Build from the website repository root:

```sh
python3 scripts/site/pages.py
python3 scripts/site/build_index.py
python3 scripts/site/build_tools.py
python3 scripts/build_sitemap.py
```

Edit Markdown for an article; do not hand-edit generated `lab/*.html` pages.

## Engineering projects

Use `project-template.md` and `HOW-TO-ADD-A-PROJECT.md`. `projects.json` is the published index; prepare new project data as a local draft until the status and supporting evidence are ready. Do not describe a concept as a prototype or fill in missing hardware/results by inference.
