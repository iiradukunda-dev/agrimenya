// agrimenya Progressive Web App Service Worker
const CACHE_NAME = 'agrimenya-pwa-v4';

const PRECACHE_ASSETS = [
  '/offline.html',
  '/manifest.json',
  '/app/static/manifest.json',
  '/app/static/wheat.svg',
  '/app/static/icon-192.png',
  '/app/static/icon-512.png',
  '/app/static/icon-maskable-512.png',
  '/app/static/apple-touch-icon.png',
  '/app/static/favicon.png',
  '/app/static/ai_assistant_bulb.png'
];

// Install: precache core offline application shell
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.all(
        PRECACHE_ASSETS.map(async (url) => {
          const response = await fetch(url, { cache: 'reload' });
          if (!response.ok) {
            throw new Error(`[SW] Failed to precache ${url}: HTTP ${response.status}`);
          }
          await cache.put(url, response);
        })
      )
    )
  );
});

// Activate: clean up outdated caches & claim clients immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
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

  // Streamlit's HTML shell depends on a live session; use the standalone offline hub instead.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .catch(async () => {
          const offlinePage = await caches.match('/offline.html');
          if (offlinePage) return offlinePage;
          return new Response('Offline field hub is unavailable.', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
          });
        })
    );
    return;
  }

  // 2. Static files (images, css, js, fonts): Stale-While-Revalidate
  const isVideo = /\.(mp4|webm|mov)$/i.test(url.pathname);
  const isStatic =
    url.pathname.startsWith('/app/static/') ||
    url.pathname.startsWith('/static/') ||
    /\.(png|jpg|jpeg|svg|webp|css|js|woff2|woff|ttf|ico)$/i.test(url.pathname);

  if (isStatic && !isVideo) {
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
          .catch(() => cached || Response.error());

        return cached || fetchPromise;
      })
    );
  }
});
