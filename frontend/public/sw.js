// Service worker de ORBIT Health (v2). Meta: que se abra como una app instalada, incluso si el servidor tarda o está apagado.
// NUNCA guarda respuestas de /api: los datos clínicos siempre vienen del servidor, sin copias viejas.
const VERSION = "orbit-v2";
const CACHE_SHELL = `${VERSION}-shell`;
const CACHE_ACTIVOS = `${VERSION}-activos`;
const PRECARGA = ["/", "/offline.html", "/manifest.webmanifest", "/icono-192.png", "/icono-512.png", "/icono.svg"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE_SHELL).then((c) => c.addAll(PRECARGA)));        // no se activa solo: la página decide cuándo
});

self.addEventListener("message", (e) => { if (e.data === "activar") self.skipWaiting(); });

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api")) return;

  if (req.mode === "navigate") {                         // la página: red primero; sin red, la copia; sin copia, la pantalla "sin conexión"
    e.respondWith(
      fetch(req)
        .then((r) => { if (r.ok) { const copia = r.clone(); caches.open(CACHE_SHELL).then((c) => c.put("/", copia)); } return r; })
        .catch(() => caches.match("/").then((r) => r || caches.match("/offline.html")))
    );
    return;
  }
  if (url.pathname.startsWith("/assets/")) {             // archivos con hash en el nombre: copia primero (nunca cambian)
    e.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((r) => {
        if (r.ok) { const copia = r.clone(); caches.open(CACHE_ACTIVOS).then((c) => c.put(req, copia)); }
        return r;
      }))
    );
    return;
  }
  e.respondWith(                                          // iconos, manifiesto, etc.: frescos si hay red, copia si no
    fetch(req).then((r) => { if (r.ok) { const copia = r.clone(); caches.open(CACHE_SHELL).then((c) => c.put(req, copia)); } return r; })
      .catch(() => caches.match(req))
  );
});
