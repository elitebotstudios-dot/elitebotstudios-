# Lab-note authoring

Repository documentation for maintainers. This file is not linked from the public site.

## File format

One Markdown file per note in `content/lab-notes/`:

```yaml
---
slug: example-note
title: A short technical title
date: 2026-11-05
tags: [embedded systems, testing]
description: One factual sentence used in the index and metadata.
---
```

The body follows the closing `---`. The dependency-free renderer supports headings (`##`, `###`), paragraphs, ordered and unordered lists, blockquotes, fenced code with language-aware highlighting (`c`, `cpp`, `js`, `python`), inline code, links, emphasis, inline equations (`$...$` or `\(...\)`), display equations (`$$`), same-site images (`![alt](/assets/plot.png)`), horizontal rules and pipe tables. Raw HTML is escaped.

`slug` must be lowercase-hyphenated and becomes `/lab/<slug>.html`. `date` must be `YYYY-MM-DD`. Reading time is derived from the rendered body.

## Publishing

```sh
python3 scripts/site/pages.py
python3 scripts/site/build_index.py
python3 scripts/build_sitemap.py
python3 scripts/audit_site.py
```

The note then appears in the lab index, the sitemap and — if listed in `featured` in `build_index.py` — the homepage preview, all from the same source.

## Rules

- Separate educational explanation, simulation/calculation, and measurement. Never present a model result as a bench result.
- Give units, stated assumptions, and references where a claim depends on an external source.
- Prefer one accurate note over several thin ones. Do not fabricate experiments.
