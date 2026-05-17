const CACHE_NAME = "prayerstreak-v1";
const OFFLINE_URL = "/offline.html";
const OFFLINE_HTML = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PrayerStreak PH Offline</title>
  <style>
    body {
      align-items: center;
      background: #1E3A5F;
      color: #FFFFFF;
      display: flex;
      font-family: Poppins, sans-serif;
      justify-content: center;
      margin: 0;
      min-height: 100vh;
      padding: 24px;
      text-align: center;
    }
    main {
      max-width: 520px;
    }
    h1 {
      font-size: 1.6rem;
      margin-bottom: 0.75rem;
    }
    p {
      font-size: 1rem;
      line-height: 1.7;
      margin: 0;
    }
  </style>
</head>
<body>
  <main>
    <h1>You are offline.</h1>
    <p>Open PrayerStreak PH when you have internet to continue your prayer.</p>
  </main>
</body>
</html>`;

const CACHE_URLS = [
  "/",
  "/dashboard",
  "/community",
  "/leaderboard",
  "/static/core/manifest.json",
  "https://cdn.tailwindcss.com",
  "https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css",
  "https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Poppins:wght@400;500;600;700&display=swap"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      await cache.put(
        OFFLINE_URL,
        new Response(OFFLINE_HTML, {
          headers: { "Content-Type": "text/html; charset=utf-8" }
        })
      );

      await Promise.all(
        CACHE_URLS.map(async (url) => {
          try {
            const request = new Request(url, {
              mode: url.startsWith("http") ? "no-cors" : "same-origin"
            });
            const response = await fetch(request);
            await cache.put(request, response);
          } catch (error) {
            return undefined;
          }
        })
      );
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames
            .filter((cacheName) => cacheName !== CACHE_NAME)
            .map((cacheName) => caches.delete(cacheName))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        const responseClone = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseClone);
        });
        return networkResponse;
      })
      .catch(async () => {
        const cachedResponse = await caches.match(event.request);
        if (cachedResponse) {
          return cachedResponse;
        }

        if (event.request.mode === "navigate") {
          return caches.match(OFFLINE_URL);
        }

        return new Response("Offline", {
          status: 503,
          statusText: "Service Unavailable",
          headers: { "Content-Type": "text/plain; charset=utf-8" }
        });
      })
  );
});

self.addEventListener("push", (event) => {
  let payload = {
    title: "PrayerStreak PH",
    body: "Your quiet hour is now.",
    url: "/dashboard/"
  };

  if (event.data) {
    try {
      payload = { ...payload, ...event.data.json() };
    } catch (error) {
      payload.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      icon: "/static/core/images/icon-192.png",
      badge: "/static/core/images/icon-192.png",
      data: { url: payload.url || "/dashboard/" }
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || "/dashboard/";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ("focus" in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      return clients.openWindow(targetUrl);
    })
  );
});
