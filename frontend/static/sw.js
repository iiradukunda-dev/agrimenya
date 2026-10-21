// agrimenya Progressive Web App Service Worker
const CACHE_NAME = 'agrimenya-pwa-v2';
const DATA_CACHE = 'agrimenya-data-v2';

const PRECACHE_ASSETS = [
  '/',
  '/offline.html',
  '/app/static/offline.html',
  '/manifest.json',
  '/app/static/manifest.json',
  '/app/static/wheat.svg',
  '/app/static/icon-192.png',
  '/app/static/icon-512.png',
  '/app/static/icon-maskable-512.png',
  '/app/static/apple-touch-icon.png',
  '/app/static/favicon.png'
];

// Install: precache core offline application shell
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.allSettled(
        PRECACHE_ASSETS.map((url) =>
          fetch(url, { cache: 'no-cache' })
            .then((response) => {
              if (response && response.status === 200) {
                return cache.put(url, response);
              }
            })
            .catch((err) => {
              console.warn('[SW] Precache skipped for:', url, err.message);
            })
        )
      );
    })
  );
});

// Activate: clean up outdated caches & claim clients immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME && key !== DATA_CACHE)
          .map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: intelligent caching strategy for offline agricultural resilience
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Bypass non-GET requests and WebSockets (Streamlit live session stream)
  if (req.method !== 'GET') return;
  if (url.pathname.includes('/_stcore/stream') || url.protocol === 'ws:' || url.protocol === 'wss:') {
    return;
  }

  // 1. Navigation requests: Network-first, fallback to cache or rich offline.html
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          }
          return response;
        })
        .catch(async () => {
          // Check cached page first
          const cached = await caches.match(req);
          if (cached) return cached;

          // Fallback to rich offline agro-hub
          const offlinePage = await caches.match('/offline.html') || await caches.match('/app/static/offline.html');
          if (offlinePage) return offlinePage;

          return new Response(
            `<!DOCTYPE html><html><head><meta charset="utf-8"><title>agrimenya Offline</title></head><body style="background:#021824;color:#e0f2fe;font-family:sans-serif;padding:2rem;text-align:center;"><h2>agrimenya is offline</h2><p>Please check your connection.</p></body></html>`,
            { headers: { 'Content-Type': 'text/html' } }
          );
        })
    );
    return;
  }

  // 2. Static files (images, css, js, fonts): Stale-While-Revalidate
  const isStatic =
    url.pathname.startsWith('/app/static/') ||
    url.pathname.startsWith('/static/') ||
    /\.(png|jpg|jpeg|svg|webp|mp4|css|js|woff2|woff|ttf|ico)$/i.test(url.pathname);

  if (isStatic) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const fetchPromise = fetch(req)
          .then((networkRes) => {
            if (networkRes && networkRes.status === 200) {
              const resClone = networkRes.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(req, resClone));
            }
            return networkRes;
          })
          .catch(() => cached);

        return cached || fetchPromise;
      })
    );
    return;
  }

  // 3. API / Data requests: Network first with Cache fallback
  event.respondWith(
    fetch(req)
      .then((networkRes) => {
        if (networkRes && networkRes.status === 200) {
          const resClone = networkRes.clone();
          caches.open(DATA_CACHE).then((cache) => cache.put(req, resClone));
        }
        return networkRes;
      })
      .catch(async () => {
        const cached = await caches.match(req);
        if (cached) return cached;
        return new Response(JSON.stringify({ offline: true, message: 'Working offline' }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
  );
});
