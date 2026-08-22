# README-GITHUB-PAGES — Deploy elitebotstudios.me from a NEW GitHub account

> Practical, step-by-step guide ONLY. This package is self-contained: no build
> step, no npm, no Node, no framework, no database, no server runtime.
> The entire content of THIS folder is the website. GitHub Pages serves it as-is.

---

## ⚠️ Read first — two things that are true right now (verified 2026-08-22)

1. The domain `elitebotstudios.me` is currently attached to a **personal**
   GitHub Pages user site (it serves that user's personal page over HTTP, and
   its HTTPS certificate is failing because the cert does not match this
   domain). **Remove that custom domain from the old site FIRST** (that
   GitHub account → Settings → Pages → Custom domain → Remove), otherwise
   GitHub will not attach/issue a certificate for the new repository.
2. This website uses root-relative paths (`/assets/...`, `/blog/...`) and is
   designed for the apex domain `https://elitebotstudios.me/`. Until the
   custom domain is attached, the temporary preview at
   `https://<account>.github.io/<repo>/` will look unstyled — that is
   EXPECTED and resolves itself the moment the custom domain is live.
   Do not "fix" it by rewriting paths; the site is intentionally apex-rooted.

Steps below are tagged: **[GITHUB]** = do on github.com (new account) ·
**[REGISTRAR]** = do at the domain registrar/DNS provider · **[LOCAL]** = do on your computer.

---

## A. Create repository  — [GITHUB]
1. Sign in to the NEW GitHub account.
2. New repository (any name, e.g. `elite-bot-studios`).
3. Public, no README/gitignore/license (empty repo).
4. Note: GitHub Pages is free only for PUBLIC repositories on personal plans.

## B. Upload / push files  — [GITHUB] or [LOCAL]
Upload the **contents** of this folder (the files themselves, not the folder)
as the repository root, so the repo contains `index.html` at the top level.

- **Option 1 (no tools):** on github.com open the new repo → *Add file* →
  *Upload files* → drag ALL files and folders from this package. Make sure
  hidden file `.nojekyll` is included (drag-drop normally includes dotfiles;
  verify it appears in the repo listing afterwards).
- **Option 2 (git):** clone the empty repo, copy the package contents into
  the clone, then `git add -A && git commit && git push`.
- After upload, confirm the repo root looks exactly like this folder:
  `index.html`, `404.html`, `sitemap.xml`, `robots.txt`, `llms.txt`,
  `sw.js`, `site.webmanifest`, `.nojekyll`, `blog/`, `assets/`, plus all
  `*.html` pages.

## C. Enable GitHub Pages  — [GITHUB]
Repo → **Settings → Pages** → Source: **Deploy from a branch**.

## D. Select branch  — [GITHUB]
Branch: `main` (or `master` if that is what you pushed).

## E. Select root directory  — [GITHUB]
Folder: `/ (root)`. The site root IS the repository root — do NOT use `/docs`.

## F. Configure custom domain `elitebotstudios.me`  — [GITHUB]
1. In the same **Settings → Pages** panel, under *Custom domain*, enter:
   ```
   elitebotstudios.me
   ```
2. Save. GitHub writes a `CNAME` file into the repo automatically (that is
   why this package intentionally does NOT ship a CNAME file — GitHub
   manages it, and shipping one could conflict while the domain is still
   attached to the old site).
3. If GitHub refuses with a "domain already taken" error, the old personal
   site still holds the domain → detach it there first (see ⚠️ above).

## G. Enable HTTPS  — [GITHUB]
1. In **Settings → Pages**, tick **Enforce HTTPS**.
2. GitHub issues the certificate automatically (usually minutes, worst case
   a few hours). Until the certificate appears the site will NOT load over
   HTTPS — wait for it; do not proceed to GSC/Bing until it works.
3. If the certificate fails or stays pending, remove the custom domain and
   add it again (this is the documented fix for the certificate mismatch
   currently observed on this domain).

## H. Configure www → apex  — [GITHUB] + [REGISTRAR]
1. [GITHUB] In **Settings → Pages → Custom domain**, also add:
   ```
   www.elitebotstudios.me
   ```
   GitHub Pages will serve the site on www as well; it cannot issue its own
   redirect rules, but that is safe here because every page's canonical tag
   already points to the apex `https://elitebotstudios.me/`.
2. [REGISTRAR] Confirm DNS (likely already correct — verified 2026-08-22):
   - Apex `elitebotstudios.me` → A records `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `www` → CNAME `<your-new-account>.github.io`
   (GitHub's Pages settings panel shows the exact expected records — always
   trust the panel over this document.)

## I. Verify the website  — [LOCAL]
After the certificate is issued, check each of these returns the expected result:
```
https://elitebotstudios.me/                 → 200, full styled site
https://elitebotstudios.me/blog.html        → 200
https://elitebotstudios.me/sitemap.xml      → 200, all URLs use .me
https://elitebotstudios.me/robots.txt       → 200, Sitemap: .me URL
https://elitebotstudios.me/llms.txt         → 200, .me URLs
https://elitebotstudios.me/404.html         → 200
https://elitebotstudios.me/some-missing-page → shows the branded 404 page
https://www.elitebotstudios.me/             → serves the same site
```
Browser: hard-refresh twice (service worker `ebs-v10` activates), test the
mobile menu, chat widget, calculators, and airplane-mode → offline page.

## J. Configure Apps Script endpoint  — [LOCAL + GITHUB]
1. [LOCAL] Deploy the Apps Script backend (the `Code.gs` file kept outside
   this package) as a web app: Execute as **Me**, access **Anyone**.
2. Copy the resulting `https://script.google.com/macros/s/<ID>/exec` URL.
3. [GITHUB] In the deployed repo, edit `index.html` → find:
   `leadEndpoint: ''` and paste the real URL between the quotes; commit.
   Until this is done the lead form fails honestly with a visible message —
   that is intentional and must not be "fixed" with a fake URL.

## K. Configure GA4  — [GITHUB]
1. Create a Google Analytics 4 property for `elitebotstudios.me` and copy
   its Measurement ID (format `G-XXXXXXXXXX`).
2. In the repo, replace ALL `ADD_REAL_GA4_ID` placeholders (36 across the
   HTML pages) with the real ID, and set `ga4Id` inside `EBS_CONFIG` in
   `index.html`.
3. Analytics stays disabled until you do this — the site works fully
   without it.

## L. Configure Google Search Console  — [GITHUB] + [REGISTRAR]
1. Add a property for `https://elitebotstudios.me` (URL-prefix property).
2. Verify with a REAL token. Easiest: [REGISTRAR] add the TXT record GSC
   shows you to the DNS zone. (No verification code ships in this package —
   use only the one GSC generates for your account.)
3. Submit `https://elitebotstudios.me/sitemap.xml` and request indexing.

## M. Configure Bing Webmaster  — [GITHUB]
1. Add the site in Bing Webmaster Tools (import from GSC after step L).
2. Submit `https://elitebotstudios.me/sitemap.xml`.

## N. Run final smoke tests  — [LOCAL]
```
curl -I https://elitebotstudios.me/                 # 200
curl -I https://elitebotstudios.me/index.html       # 200 (GitHub Pages serves the same page at /)
curl -I https://elitebotstudios.me/does-not-exist   # 404
curl -s https://elitebotstudios.me/sitemap.xml | head -5
curl -s https://elitebotstudios.me/robots.txt
```
Then: GSC "URL inspection" on the homepage → request indexing; confirm the
lead form shows the honest fallback until step J is done; confirm analytics
stay quiet until step K is done.

---

### Deployment facts (no surprises)
| Question | Answer |
|---|---|
| Build command | None |
| Output directory | None (repo root) |
| Node/npm/runtime | None required |
| SPA fallback | No — multi-page static site; `404.html` is served natively by GitHub Pages |
| Service worker | Works from the apex domain; paths are root-relative; version `ebs-v10` |
| `.nojekyll` | Present — tells GitHub Pages to skip Jekyll processing entirely |
| `_redirects` file | Intentionally NOT in this package (it is a Netlify/Cloudflare Pages feature; GitHub Pages ignores it and needs no redirect rules) |
