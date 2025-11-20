const CACHE_NAME = 'ndtech-pos-v1';
const urlsToCache = [
    '/',
    '/accounts/login/',
    '/register/',
    '/static/nano/styles.css',
    '/static/nano/notifications.css',
    '/static/nano/hamburger.css',
    '/static/nano/notifications.js',
    '/static/nano/hamburger.js',
    '/static/nano/toast.js',
    '/static/nano/manifest.json',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Install event - cache resources
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Cache hit - return response
                if (response) {
                    return response;
                }

                // Clone the request
                const fetchRequest = event.request.clone();

                return fetch(fetchRequest).then(response => {
                    // Check if valid response
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }

                    // Clone the response
                    const responseToCache = response.clone();

                    // Cache successful GET requests
                    if (event.request.method === 'GET') {
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });
                    }

                    return response;
                }).catch(() => {
                    // Return offline page for navigation requests
                    if (event.request.destination === 'document') {
                        return caches.match('/');
                    }
                });
            })
    );
});

// Activate event - clean up old caches
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
});

// Background sync for offline actions
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

function doBackgroundSync() {
    // Handle background sync tasks
    console.log('Background sync triggered');
    return Promise.resolve();
}

// Push notification handler
self.addEventListener('push', event => {
    const options = {
        body: event.data ? event.data.text() : 'New notification from NDtech POS',
        icon: '/static/nano/manifest.json',
        badge: '/static/nano/manifest.json',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'View Details',
                icon: '/static/nano/manifest.json'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/nano/manifest.json'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('NDtech POS', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'explore') {
        // Open the app to notifications page
        event.waitUntil(
            clients.openWindow('/notifications/')
        );
    } else if (event.action === 'close') {
        // Just close the notification
        event.notification.close();
    } else {
        // Default action - open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});
