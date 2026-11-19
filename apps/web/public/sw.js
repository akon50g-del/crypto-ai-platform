// Minimal PWA service worker: cache the app shell, network-first for API.
// Trading data must never be served stale: API/WS requests bypass the cache.
const CACHE = 'crypto-ai-signals-v1';
const SHELL = ['/', '/dashboard', '/signals', '/login', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Never cache API calls, auth, or websockets — live data only.
  if (e.request.method !== 'GET' || url.pathname.startsWith('/api') || url.port === '4000' || url.port === '8000') return;
  if (url.origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request).then((r) => r || caches.match('/'))),
  );
});
