/* ============================================================
   Elite Bot Studios — Service Worker (PWA offline cache)

   Bump CACHE_VERSION whenever content changes to force a refresh.
   Precaching is resilient: a missing file cannot break the whole
   cache install, so a new icon or asset never takes the site down.
   ============================================================ */
const CACHE_VERSION = 'ebs-v27';
const PRECACHE = [
  '/',
  '/index.html',
  '/services.html',
  '/projects.html',
  '/lab.html',
  '/lab/why-this-studio-exists.html',
  '/lab/simulation-to-silicon.html',
  '/about.html',
  '/contact.html',
  '/privacy.html',
  '/terms.html',
  '/cookies.html',
  '/offline.html',
  '/projects.json',
  '/assets/site.css',
  '/assets/site.js',
  '/assets/hero-poster.webp',
  '/assets/hero-poster-1200.webp',
  '/assets/chip-mark.svg',
  '/assets/favicon-16x16.png',
  '/assets/favicon-32x32.png',
  '/assets/apple-touch-icon.png',
  '/assets/logo-512.png',
  '/site.webmanifest'
];

/* Assets that are fetched lazily and only need caching once used. */
const RUNTIME = [
  '/assets/hero3d.js',
  '/assets/hero-atlas.webp'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) =>
      Promise.all(
        PRECACHE.map((url) =>
          cache.add(new Request(url, { cache: 'reload' })).catch(() => null)
        )
      )
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  /* HTML: network first, so content is never stale, with the cache as the
     offline fallback. */
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((c) => c.put(req, copy)).catch(() => {});
          return res;
        })
        .catch(() =>
          caches.match(req).then((hit) => hit || caches.match('/offline.html'))
        )
    );
    return;
  }

  /* Static assets: cache first, and cache lazy assets the first time they load. */
  event.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res && res.status === 200 && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => hit);
    })
  );
});
