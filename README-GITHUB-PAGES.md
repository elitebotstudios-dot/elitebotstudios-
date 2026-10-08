# Elite Bot Studios — site

Static site for an embedded systems and power electronics engineering studio.
No framework, no build step. Plain HTML, one shared stylesheet, one shared
script, and one hand-written WebGL renderer for the homepage hero.

**Live:** <https://elitebotstudios.me>

---

## Structure

```
/
├── index.html                      Home — hero, toolchain, delivery pipeline
├── services.html                   4 service blocks + how delivery works
├── projects.html                   Renders from projects.json
├── lab.html                        Build log index
├── lab/
│   ├── why-this-studio-exists.html
│   └── simulation-to-silicon.html
├── about.html                      Founder, rules, timeline
├── contact.html                    Contact form + direct email
├── privacy.html  terms.html  cookies.html
├── 404.html  offline.html
├── projects.json                   ← the only file you edit to add a build
├── HOW-TO-ADD-A-PROJECT.md         ← read this before editing projects.json
├── assets/
│   ├── site.css                    shared design system (all pages)
│   ├── site.js                     nav, scroll reveal, project loader
│   ├── hero3d.js                   WebGL2 hero scene (~45 KB, no libraries)
│   ├── hero-atlas.webp             soldermask/copper/silkscreen texture
│   ├── hero-poster.webp            1600px hero still (LCP + no-WebGL fallback)
│   ├── hero-poster-1200.webp       narrow-viewport variant
│   ├── chip-mark.svg               brand mark
│   └── favicon-*.png, logo-512.png, apple-touch-icon.png, social-preview.png
├── sw.js                           service worker (bump CACHE_VERSION on change)
├── site.webmanifest
├── robots.txt  sitemap.xml  llms.txt
└── vercel.json                     redirects, security headers, cache policy
```

---

## Hosting

Deployed on **Vercel**, serving the `main` branch directly. There is no
build step — pushing to `main` deploys the files as they are.

> **Important:** the repository is private and the Vercel project is on the
> Hobby plan. A commit whose author is not a member of the Vercel team will
> *not* trigger a deployment. If a push does not appear on the live site,
> make one small follow-up commit authored by the account that owns the
> Vercel project.

### Cache behaviour

The stylesheet, the scripts, the hero assets and the favicons are **not**
served under fixed filenames. The page generator appends a content hash:

```html
<link rel="stylesheet" href="/assets/site.css?v=a0ceec94" />
```

`build.asset(path)` computes the first 8 hex characters of the file's SHA-256
and appends them. A changed file therefore gets a new URL and is fetched
immediately; an unchanged file is never re-downloaded, which is what makes the
long TTLs below safe.

| Path | Policy |
|---|---|
| `/assets/site.css?v=…` | 1 day, `stale-while-revalidate` 7 days |
| `/assets/site.js?v=…`, `hero3d.js?v=…` | 1 day |
| `/assets/hero-atlas.webp?v=…`, posters | 1 day |
| other `/assets/*` | 1 day |
| `/projects.json` | 5 minutes |
| `/sw.js` | `no-store`, so updates always land |
| HTML | network first via the service worker |

`og:image` and the `schema.org` logo are deliberately left unversioned: they
are read by crawlers, and schema.org expects a stable logo URL.

**This matters more than it looks.** Shortening a TTL does not evict what a
CDN has already stored. Before fingerprinting was added, a stylesheet fix
deployed correctly to the origin while remaining invisible to anyone with a
warm cache — the header said 7 days, so the edge held the old file for 7 days.
If you ever add a new asset that pages reference directly, give it a `?v=`
too via `build.asset()`, or it will have the same problem.

Because the service worker is network-first for navigation, edited pages
appear on reload. If a stale page ever sticks, bump `CACHE_VERSION` in
`sw.js` (`ebs-v28` → `ebs-v29`).

---

## Editing content

### Adding a project
See **`HOW-TO-ADD-A-PROJECT.md`**. Short version: edit `projects.json`, commit.

### Adding a lab post
1. Copy `lab/why-this-studio-exists.html` as a template.
2. Change the `<title>`, `<meta name="description">`, `<link rel="canonical">`,
   the `<h1>`, the date, and the JSON-LD block.
3. Put the body inside `<div class="prose">`. Use `<h2>`, `<p>`, `<ul>`, `<li>`,
   `<code>`, `<blockquote>`.
4. Add a card to `lab.html` and a URL to `sitemap.xml`.
5. Bump `CACHE_VERSION` in `sw.js`.

### House rules
Everything published must be **actually built and actually measured**.

- Numbers need conditions attached (input voltage, load, temperature, instrument).
- Simulated results must be labelled as simulated.
- Never invent clients, testimonials, team members, or results.
- Anything the owner still has to supply is marked `data-owner="TODO"` in the
  markup. Grep for it before launch:

  ```bash
  grep -rn 'data-owner="TODO"' . --include='*.html'
  ```

---

## Regenerating the pages

The HTML files are generated, so edit the generator and rebuild rather than
editing a page by hand — a hand edit is lost the next time the generator runs.

```bash
python3 ../tools/pages.py          # services, projects, lab, about, contact, legal, 404
python3 ../tools/build_index.py    # homepage — carries the hero across
```

`tools/` sits outside the repo on purpose: it is a build system, not something
the deployed site should ship. Running both scripts twice produces
byte-identical output, so it is safe to re-run.

`build_index.py` asserts that the hero canvas, the JSON-LD block, the image
alt text and every fingerprinted reference are present before it writes. If a
future edit drops one, the build fails instead of shipping a broken homepage.

## Local development

```bash
python3 -m http.server 8080
# open http://localhost:8080
```

Use a local server rather than opening the files directly — `projects.html`
fetches `projects.json`, and `fetch` is blocked on `file://`.

---

## The hero scene

`assets/hero3d.js` is a hand-written WebGL2 renderer. No Three.js, no CDN,
no network requests beyond the two local textures.

It boots only when **all** of these hold:

- `prefers-reduced-motion` is not set
- the device is not a phone (coarse pointer on a small screen)
- `navigator.connection.saveData` is off and the connection is not 2G-class
- WebGL2 is available

Otherwise, and on any shader or context failure, the poster image simply
stays. The poster is the LCP element in every case, so the hero is never
blank and never blocks paint.

### Tuning it

| What | Where |
|---|---|
| Camera framing | `CAM` in `hero3d.js` (`az`, `el`, `fov`, `target`) |
| Fill ratio in frame | `FILL = { w, h }` |
| Light rig | `KEY`, `KCOL`, `FILLD`, `FCOL`, `RIM` |
| Exposure / bloom | `uExposure`, `uBloomAmt`, `uThreshold` in `drawPost()` |
| Board layout | `layout.json` at build time → baked into `hero-atlas.webp` |

Editing `hero-atlas.webp` alone changes what the board looks like; the
component geometry is generated in `buildInstances()` from the same data.

---

## Pre launch checklist

- [ ] `grep -rn 'data-owner="TODO"' . --include='*.html'` — resolve every hit
- [ ] Real GitHub and LinkedIn URLs in the footer (`data-owner="TODO"`)
- [ ] Founder name and photo on `about.html`
- [ ] Contact form endpoint set in `contact.html`, then remove its notice block
- [ ] Bench photos replace the rendered hero poster
- [ ] Governance jurisdiction confirmed on `terms.html`
- [ ] `CACHE_VERSION` bumped in `sw.js`
