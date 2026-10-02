const CACHE_NAME = 'ndtech-pos-v3';
const OFFLINE_URL = '/offline/';

// Only assets that actually exist may be precached. A single 404 used to make
// cache.addAll() reject and abort the whole service worker install, which
// disabled offline mode entirely. Keep this list in sync with nano/static/nano/.
const urlsToCache = [
    OFFLINE_URL, // Explicitly cache the offline page
    '/static/nano/css/app.css',
    '/static/nano/css/navbar.css',
    '/static/nano/notifications.js',
    '/static/nano/hamburger.js',
    '/static/nano/toast.js',
    '/static/nano/airtime.js',
    '/static/nano/manifest.json',
    '/static/nano/icon-96.png',
    '/static/nano/icon-192.png',
    '/static/nano/icon-512.png'
];

// Install event - cache critical resources (best effort, never all-or-nothing)
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => Promise.all(
                urlsToCache.map(url =>
                    cache.add(url).catch(error => {
                        console.warn('Skipping precache for', url, error);
                    })
                )
            ))
    );
    self.skipWaiting();
});

// Activate event - clean up old caches and claim clients
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Helper function to determine if request is API call
const isApiCall = (request) => {
    const accept = request.headers.get('Accept') || '';
    return request.url.includes('/api/') || accept.includes('application/json');
};

// Fetch event - Robust Offline Strategy
self.addEventListener('fetch', event => {
    // 1. Handle POST requests (Sales/Data mutations)
    if (event.request.method === 'POST') {
        if (!navigator.onLine) {
             // TODO: In a full implementation, you would save this request to IndexedDB here
             // and replay it when back online via Background Sync.
             // For now, we allow the fetch to fail so the UI can handle the error gracefully,
             // OR we could return a synthetic response saying "Saved Offline".
             return;
        }
        return; // Let browser handle online POST normally
    }

    // 2. Handle GET requests
    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                // Strategy: Stale-While-Revalidate for non-mutating data
                // Access cache first, but trigger network update in background

                const fetchPromise = fetch(event.request).then(networkResponse => {
                    // Check if valid response
                    if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                        return networkResponse;
                    }

                    // Clone and Cache updated response for next time
                    const responseToCache = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseToCache);
                    });

                    return networkResponse;
                }).catch(error => {
                    console.log('Fetch failed, returning offline page if navigation', error);
                    return null;
                });

                // Return cached response immediately if available, otherwise wait for network
                return cachedResponse || fetchPromise;
            })
            .then(response => {
                if (response) {
                    return response;
                }
                // Offline fallback. respondWith() must always receive a Response,
                // so never resolve with undefined here.
                if (event.request.mode === 'navigate') {
                    return caches.match(OFFLINE_URL).then(
                        cached => cached || new Response(
                            '<!doctype html><title>Offline</title><h1>You are offline</h1>',
                            { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
                        )
                    );
                }
                return new Response('', { status: 504, statusText: 'Offline' });
            })
    );
});

// Background sync for offline actions (Queue processing)
self.addEventListener('sync', event => {
    if (event.tag === 'sync-sales') {
        event.waitUntil(processOfflineSales());
    }
});

async function processOfflineSales() {
    // Placeholder: Logic to read from IndexedDB and POST to server
    console.log('Processing offline sales queue...');
    // 1. Open IndexedDB
    // 2. Get all pending transactions
    // 3. Iterate and fetch(api_endpoint, data)
    // 4. On success, delete from IndexedDB
}

// Push notification handler
self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'NDtech POS';
    const options = {
        body: data.body || 'New notification',
        icon: '/static/nano/icon-192.png',
        badge: '/static/nano/icon-96.png',
        vibrate: [100, 50, 100],
        data: { url: data.url || '/' }
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
