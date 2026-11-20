const CACHE_NAME = "entrelinhas-v15";
const SHELL = ["./", "./index.html", "./style.css", "./app.js", "./catalogo.js", "./favicon.svg", "./manifest.webmanifest", "./icons/icon-192.svg", "./icons/icon-512.svg", "./efeitos/nuvenzinha-brilhante-mascara.svg", "./efeitos/nuvenzinha-brilhante-mascara-diagonal.png"];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin === self.location.origin) {
    if (url.pathname.endsWith("/catalogo.js")) {
      // O catálogo muda automaticamente sem uma nova versão do service worker.
      // Buscamos a versão atual na rede e usamos o cache somente se estiver offline.
      event.respondWith(fetch(event.request).then(response => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        }
        return response;
      }).catch(() => caches.match(event.request)));
      return;
    }

    event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      return response;
    })));
  }
});
