/* Service worker: network first, cache as fallback.
 * Online, every page and data file comes from the network (and the copy is saved).
 * Offline, the last saved copy is served, so the site opens with the last data it loaded. */
const CACHE = "job-watcher-v2";
const SHELL = [
  "./", "index.html", "browse.html", "market.html",
  "styles.css", "common.js", "today.js", "browse.js", "market.js",
  "vendor/papaparse.min.js", "vendor/chart.umd.min.js", "dfw.json",
  "manifest.webmanifest", "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png",
  "data/status.json", "data/history.csv",
];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const resp = await fetch(req, { cache: "no-cache" });
      if (resp.ok) cache.put(req, resp.clone());
      return resp;
    } catch (err) {
      const hit = await cache.match(req, { ignoreSearch: true });
      if (hit) return hit;
      if (req.mode === "navigate") return (await cache.match("index.html")) || Response.error();
      throw err;
    }
  })());
});
