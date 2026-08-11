// T27: cache-first service worker over a small explicit precache list.
// Bump CACHE_NAME whenever 260703_Cellsnake.html, vendor/, the manifest or the
// icons change -- see AGENT_CONDUCT.md §2. Without the bump, players keep
// getting the stale cached game forever after their first visit.
const CACHE_NAME = 'cellular-zatacka-v28';

const PRECACHE_URLS = [
    './',
    './index.html',
    './260703_Cellsnake.html',
    './manifest.webmanifest',
    './vendor/pixi.min.js',
    './vendor/pixi-filters.js',
    './icons/icon-192.png',
    './icons/icon-512.png',
    './icons/icon-maskable-512.png',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(names => Promise.all(
                names.filter(name => name !== CACHE_NAME).map(name => caches.delete(name))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    event.respondWith(
        caches.match(event.request).then(cached => cached || fetch(event.request))
    );
});

// The page posts this once the player taps the "new version available"
// banner -- reloading out from under them unprompted would be hostile.
self.addEventListener('message', event => {
    if (event.data === 'SKIP_WAITING') self.skipWaiting();
});
