// Service worker de ORBIT Health: deja abrir la interfaz aunque el servidor tarde en responder.
// NUNCA guarda respuestas de /api: los datos clínicos siempre vienen del servidor, sin copias viejas.
const CACHE = "orbit-shell-v1";

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(["/"])).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api")) return;
  if (req.mode === "navigate") {                       // la página: red primero, copia si no hay respuesta
    e.respondWith(fetch(req).then((r) => { caches.open(CACHE).then((c) => c.put("/", r.clone())); return r; }).catch(() => caches.match("/")));
    return;
  }
  e.respondWith(                                       // archivos con nombre con hash: copia primero
    caches.match(req).then((hit) => hit || fetch(req).then((r) => {
      if (r.ok) caches.open(CACHE).then((c) => c.put(req, r.clone()));
      return r;
    }))
  );
});
