/* Service Worker der Lagerkarte.
 *
 * Wichtigste Entscheidung: "Network first". Bei jedem Start wird zuerst der
 * Server gefragt und die Antwort frisch in den Cache gelegt. Solange Netz da
 * ist, sieht die installierte App also IMMER den aktuellen Netlify-Stand —
 * ein neuer Deploy ist nach einem Neustart der App da, ohne dass jemand einen
 * Cache leeren muss. Der Cache ist reines Sicherheitsnetz für "kein Netz".
 *
 * Die Umkehrung ("Cache first") wäre schneller, würde aber genau das Problem
 * erzeugen, das hier keiner haben will: die App zeigt tagelang eine alte
 * Version, obwohl längst neu deployt wurde. Deshalb bewusst nicht.
 */

// Bei Änderungen an dieser Datei hochzählen — dann räumt activate() die alten
// Caches weg. Für die Aktualität der Inhalte ist das nicht nötig (siehe oben),
// nur für einen sauberen Neuanfang.
var CACHE = "lagerkarte-v1";

// Was für einen brauchbaren Offline-Start mindestens dasein muss.
var PRECACHE = [
  "/",
  "/lagerkarte_2.html",
  "/katalog.js",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  "/icons/icon-512.png"
];

self.addEventListener("install", function (e) {
  // Einzeln laden: eine fehlende Datei darf die Installation nicht kippen.
  e.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return Promise.all(PRECACHE.map(function (url) {
        return cache.add(new Request(url, { cache: "reload" })).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (names) {
      return Promise.all(names.map(function (n) {
        return n === CACHE ? null : caches.delete(n);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

// Gespeichert wird ausschließlich die Lagerkarte selbst. Auf derselben
// Adresse liegt auch der Mustertafel-Katalog mit rund 290 MB Bildern unter
// /images/ und /pages/ — die würden den Cache sonst nach und nach volllaufen
// lassen, ohne dass die Lagerkarte etwas davon hat.
function gehoertZurApp(pathname) {
  return pathname === "/" ||
    pathname === "/lagerkarte_2.html" ||
    pathname === "/katalog.js" ||
    pathname === "/manifest.webmanifest" ||
    pathname.indexOf("/icons/") === 0;
}

self.addEventListener("fetch", function (e) {
  var req = e.request;

  // Nur eigene GET-Anfragen anfassen. Supabase-Sync, Tesseract und pdf.js
  // liegen auf fremden Servern und laufen unverändert direkt ins Netz.
  if (req.method !== "GET") return;
  var url;
  try { url = new URL(req.url); } catch (err) { return; }
  if (url.origin !== self.location.origin) return;

  e.respondWith(
    fetch(req).then(function (res) {
      // Nur echte Volltreffer spiegeln — keine Fehlerseiten, keine
      // Teilantworten (206), sonst liegt Müll im Offline-Vorrat.
      if (res && res.ok && res.type === "basic" && gehoertZurApp(url.pathname)) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); }).catch(function () {});
      }
      return res;
    }).catch(function () {
      // Kein Netz: aus dem Cache bedienen. Für Seitenaufrufe notfalls die
      // Lagerkarte selbst, damit die App auch unter /lagerkarte_2.html startet.
      return caches.match(req).then(function (hit) {
        if (hit) return hit;
        if (req.mode === "navigate") {
          return caches.match("/lagerkarte_2.html").then(function (page) {
            return page || caches.match("/");
          });
        }
        return Response.error();
      });
    })
  );
});
