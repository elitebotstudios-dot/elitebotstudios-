/* ============================================================
   Elite Bot Studios — Service Worker (PWA offline cache)
   Bump CACHE_VERSION whenever content changes to force refresh.
   Precaching is resilient: a missing file (e.g. an icon not yet
   uploaded to the web root) cannot break the whole cache install.
============================================================ */
const CACHE_VERSION = 'ebs-v22';
const PRECACHE = [
  '/',
  '/index.html',
  '/demo.html',
  '/calculator.html',
  '/pricing.html',
  '/audit.html',
  '/case-studies.html',
  '/blog.html',
  '/blog/article-1.html',
  '/blog/article-2.html',
  '/blog/article-3.html',
  '/blog/article-4.html',
  '/blog/article-5.html',
  '/blog/article-6.html',
  '/blog/article-7.html',
  '/blog/article-8.html',
  '/blog/article-9.html',
  '/blog/article-10.html',
  '/blog/article-11.html',
  '/privacy.html',
  '/terms.html',
  '/cookies.html',
  '/offline.html',
  '/site.webmanifest',
  '/assets/favicon-32x32.png',
  '/assets/apple-touch-icon.png',
  '/assets/logo-512.png',
  '/blog/img/article-1.svg',
  '/blog/img/article-2.svg',
  '/blog/img/article-3.svg',
  '/blog/img/article-4.svg',
  '/blog/img/article-5.svg',
  '/blog/img/article-6.svg',
  '/blog/img/article-7.svg',
  '/blog/img/article-8.svg',
  '/blog/img/article-9.svg',
  '/blog/img/article-10.svg',
  '/blog/img/article-11.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => Promise.all(
        PRECACHE.map((url) =>
          cache.add(url).catch(() => {
            /* skip missing optional asset; others still cache */
          })
        )
      ))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // Never intercept cross-origin requests (fonts, analytics, Calendly…)
  if (url.origin !== self.location.origin) return;

  // Navigations: network-first, offline fallback page
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() =>
          caches.match(req).then((cached) => cached || caches.match('/offline.html'))
        )
    );
    return;
  }

  // Assets: stale-while-revalidate
  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((res) => {
          if (res && res.status === 200) {
            const copy = res.clone();
            caches.open(CACHE_VERSION).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
