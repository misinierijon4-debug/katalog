# Plan: Mustertafeln-Katalog → Zwei-Marken-Katalog (engers + V&B)

**Für: Codex** — dieser Plan ist selbsterklärend, alle Pfade und Fakten stehen drin. Bitte in der angegebenen Reihenfolge arbeiten und vor Schritt 1 ein Backup des Projektordners anlegen.

---

## 1. Ziel

Die bestehende Katalog-Webapp `index.html` soll **zwei Kataloge in einer Datei** enthalten:

1. **engers** — der bestehende Katalog (651 Tafeln, Seiten 2–306 der Quell-PDFs). Bleibt optisch wie er ist (rot/beige, Akzent `#b02e2c`).
2. **V&B (Villeroy & Boch)** — neuer zweiter Katalog. Enthält die 45 bereits vorhandenen URBAN-PULSE-Tafeln (die fälschlich im engers-Katalog gelandet sind) **plus** alle Tafeln aus einem großen V&B-PDF, das der Nutzer mitliefert.

**UI-Entscheidung (mit dem Nutzer abgestimmt):** Umschalter-Tabs im Header („engers" / „V&B"). Ein Klick wechselt den kompletten Katalog **inklusive Farbschema**, damit man sofort sieht, in welcher Markenwelt man ist:
- engers: aktuelles Design unverändert (warm, beige Hintergrund `#f4f3f0`, roter Akzent).
- V&B: kühles Schema, z. B. Hintergrund `#eef2f6`, Akzent Dunkelblau `#1d3a6b` o. ä. — deutlich unterscheidbar, gleiche Layout-Struktur.
- Suche, Serien-Filter, Chips und Zähler gelten immer nur für die aktive Marke. Gewählte Marke in `localStorage` merken.

---

## 2. Ist-Zustand (Fakten — bitte nicht raten, das stimmt so)

Projektordner: `C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog\`

| Datei/Ordner | Rolle |
|---|---|
| `index.html` (~22 KB) | Die App. Lädt Daten via `<script src="katalog.js">`; im Code: `const DATA = window.KATALOG_DATA;` und `const COVERS = {...}` (inline, Slug → Serienname für Serien-Coverbilder). |
| `katalog.js` (~290 KB) | `window.KATALOG_DATA = [...]` — die **Wahrheit** für die App. 696 Einträge. |
| `katalog.json` (Projektroot) | Archiv-/Austauschformat mit deutschen Keys (`quelle`, `einträge`, `probleme`). Muss bei Änderungen mitgepflegt werden. |
| `index_template.html` | Template mit Platzhaltern `/*__DATA__*/[]` und `/*__COVERS__*/{}`. |
| `tools/build.py` | **VERALTET**: erwartet `tools/katalog.json` (existiert nicht mehr) mit englischem Key `entries` und injiziert Daten inline statt in `katalog.js`. Vor Benutzung anpassen oder Daten direkt in `katalog.js` + `katalog.json` schreiben. |
| `images/thumb/`, `images/large/`, `images/cover/` | Tafelfotos, Dateiname = `<id>.jpg`. |
| `pages/seite-NNN.pdf` | Verlustfreie Einzelseiten für die Druckfunktion (🖨-Button auf Karte + im Modal). |
| `auftraege.html` | Auftragsverwaltung, wird von `tools/build_auftraege.py` **aus index.html generiert** — nach jedem Rebuild von index.html neu ausführen. Nutzt Tesseract.js aus `ocr/` (braucht http, nicht file://). |
| `tools/add_urban_pulse.py` | **Vorlage für V&B-Import**: parst Textlayer eines V&B-PDFs, croppt Tafelfotos per Bild-Cluster, erzeugt Seiten-PDFs, aktualisiert Daten. |
| `tools/split_pages.py`, `tools/crop.py`, `tools/extract_ocr.py` | Weitere Pipeline-Bausteine (OCR nur nötig, wenn PDF keinen Textlayer hat). |

**Eintrags-Schema** (Beispiel):
```json
{
  "id": "p263_9740LA100A10",
  "seite": 263,
  "serie": "URBAN PULSE",
  "material": "Bodentafeln",
  "codes": ["9740-LA10-0A-10"],
  "tafel_groesse": "65 x 65 cm",
  "gt": false,
  "artikel": [{"artnr": "2639LA10", "stueck": "1", "farbe": "creme", "groesse": "60x60"}],
  "label": "Etikett",
  "notizen": ["Neuheiten-Katalog 2026"],
  "display": false,
  "board_px200": [90, 277, 372, 560]
}
```
(`board_px200` = Crop-Box auf dem 200-dpi-Seitenrender; in `katalog.js` steht stattdessen `img: true/false`.)

**Format-Erkennung der Marken** (so wurde geprüft, welche Tafeln V&B sind):
- engers: Codes `9555-XXNN-04-10`-Schema, Artikelnummern mit Leerzeichen (`ENI 1220`, `WOO 1413`), „GT 72x78 cm", rein deutsch.
- V&B: Codes wie `9740-LA10-0A-10`, Artikelnummern kompakt (`2639LA10`), zweisprachige Kataloge („Sample Panel Catalogue").

**Umgebung:**
- Kein systemweites Python/Node. Python läuft über `uv`: `C:\Users\Mirsad.Karasalihovic\.local\bin\uv.exe` (z. B. `uv run --with pypdf,pillow python script.py`). Python 3.12.
- Lokaler Testserver: PowerShell-HttpListener auf Port 8123 (Konfiguration in `C:\Users\Mirsad.Karasalihovic\.claude\.claude\launch.json`), serviert den Desktop. `auftraege.html`-OCR funktioniert nur über http.
- Alle UI-Texte deutsch, Vanilla JS, keine externen CDNs/Libraries.

---

## 3. Umsetzungsschritte

### Schritt 0 — Backup
Kompletten Projektordner kopieren, z. B. nach `Desktop\Mustertafeln-Katalog_backup_<datum>\`. Erst dann weiterarbeiten.

### Schritt 1 — Datenmodell: Feld `marke`
- Jeder Eintrag bekommt `"marke": "engers"` oder `"marke": "vb"`.
- Bestand: alle 651 Nicht-URBAN-PULSE-Einträge → `engers`; die 45 URBAN-PULSE-Einträge (Seiten 263–281, IDs `p263_…`–`p281_…`) → `vb`.
- In **beiden** Dateien pflegen: `katalog.js` und `katalog.json` (deutsche Keys!).
- IDs und Bilddateien der Urban-Pulse-Einträge unverändert lassen (Bilder existieren schon).

### Schritt 2 — Großes V&B-PDF importieren
Der Nutzer legt das PDF in den Projektordner (Dateiname beim Start erfragen/nachschauen). Vorgehen nach dem Muster von `tools/add_urban_pulse.py`:

1. **Textlayer prüfen** (`pypdf`): V&B-Kataloge hatten bisher Textlayer → direkt parsen, kein OCR. Falls doch bildbasiert: RapidOCR-Route wie `tools/extract_ocr.py`.
2. **Parsen**: pro Tafel Code (`9740-…`-Schema o. ä.), Tafelgröße, Artikelliste (`2639LA10`-Format: Stück, Artnr, Farbe, Größe), Serienname aus Seitenüberschrift. Serie ins Feld `serie`, `marke: "vb"`.
3. **Neue IDs mit Präfix `vb`**, z. B. `vb_p012_9740LA100A10` — verhindert Kollisionen mit engers-Seitennummern. `seite` = Seitennummer **innerhalb des V&B-PDFs**.
4. **Bilder croppen**: Seiten mit 200 dpi rendern, Tafelfotos per Bild-Cluster finden (wie in `add_urban_pulse.py`), `images/thumb/<id>.jpg` (+ `images/large/<id>.jpg` im selben Stil wie Bestand).
5. **Seiten-PDFs** für die Druckfunktion: nach `pages/vb/seite-NNN.pdf` (eigener Unterordner, eigene Zählung). Die Druckfunktion in `index.html` muss den Pfad je nach `marke` wählen.
6. **Duplikat-Check gegen die 45 vorhandenen Urban-Pulse-Tafeln** über `codes`: Wenn ein Code schon existiert, Eintrag NICHT doppelt anlegen, sondern vorhandenen Eintrag ggf. mit besseren Daten/Fotos aktualisieren.
7. Ergebnis in `katalog.js` + `katalog.json` schreiben; jede Seite ohne erkannte Tafel unter `probleme` in `katalog.json` protokollieren (wie bisher).

**Zusätzliches PDF vom Nutzer:** `20260115 Mutas_Urban Pulse_markierung_neuer code_relief.pdf` (20 Seiten, Textlayer, inhaltlich = „Mustertafeln Urban Pulse Neuheiten 2026.pdf" mit Markierungen für **neue Codes/Relief**). Damit die vorhandenen 45 Urban-Pulse-Einträge abgleichen: geänderte/neue Codes ins Feld `codes` übernehmen (alten Code behalten, neuen zusätzlich — beide sollen in der Suche treffen), Relief-Hinweis ggf. als Notiz.

### Schritt 3 — UI: Marken-Umschalter + Theming
In `index_template.html` (dann Rebuild) **und** konsistent in `index.html`:

1. **Tabs im Header**: zwei Buttons „engers" / „V&B" prominent oben (vor der Suche). Aktive Marke → `document.body.dataset.marke`, in `localStorage` (`katalog-marke`) persistieren.
2. **Theming über CSS-Variablen**: alle Farben laufen bereits über `:root{--bg,--card,--ink,--muted,--line,--accent,…}`. Ergänzen:
   ```css
   body[data-marke="vb"]{ --bg:#eef2f6; --accent:#1d3a6b; --line:#d8dfe8; --chip:#e3e9f1; --badge:#1d3a6b; … }
   ```
   Auch Header-Brand-Text umschalten („Mustertafeln · engers" ↔ „Mustertafeln · V&B") und `<title>` anpassen. Übergang darf gern mit kurzem `transition` weich sein.
3. **Filterung**: Grid, Serien-Dropdown, Chips, Zähler und Suche arbeiten nur auf `DATA.filter(e => e.marke === aktiveMarke)`. Serien-Covers (`COVERS`) je Marke getrennt.
4. **Druckfunktion**: Pfad `pages/seite-NNN.pdf` (engers) vs. `pages/vb/seite-NNN.pdf` (vb) anhand `e.marke`.
5. **Mobile prüfen**: Tabs müssen auf schmalem Viewport (~380 px) neben/über der Suche funktionieren.

### Schritt 4 — Rebuild abhängiger Dateien
1. `tools/build.py` reparieren (liest jetzt Root-`katalog.json` mit deutschen Keys, schreibt `katalog.js` statt Inline-Daten) **oder** bewusst ersetzen — auf keinen Fall blind laufen lassen.
2. `tools/build_auftraege.py` ausführen → `auftraege.html` neu generieren. Prüfen, dass Autocomplete/Code-Suche dort **beide Marken** findet (für Aufträge ist markenübergreifende Suche gewollt) und das `marke`-Feld nichts kaputt macht.
3. `pruefliste.md`/`pruefliste.html` nur anfassen, falls der Import neue Probleme protokolliert.

### Schritt 5 — Verifikation (Pflicht)
Über http://localhost:8123 (nicht file://) testen:
1. Tab-Wechsel: Farbschema wechselt komplett, Zähler stimmen (engers = 651, V&B = 45 + Neuimporte, Summe = Gesamtzahl).
2. Suche nach einem engers-Code (`9555-EN12-04-10`) im engers-Tab und einem V&B-Code (`9740-LA10-0A-10`) im V&B-Tab.
3. Stichprobe 5 neue V&B-Karten: Foto passt zum Code, Artikel vollständig, Modal öffnet, 🖨 lädt das richtige Seiten-PDF.
4. Reload: gewählte Marke bleibt erhalten (localStorage).
5. `auftraege.html`: Text-Import mit einem V&B- und einem engers-Code gemischt → beide werden erkannt.
6. Mobile-Viewport (375 px) gegenprüfen.

---

## 4. Stolperfallen

- **Encoding**: Alle Dateien UTF-8. PowerShell 5.1 schreibt standardmäßig UTF-16 — bei Python-Skripten explizit `encoding="utf-8"`. Deutsche Umlaute in `katalog.json`-Keys (`einträge`) beachten.
- **Keine typografischen Anführungszeichen** in Code einfügen (in der Vergangenheit gab es Copy-Paste-Schäden mit „"-Zeichen).
- **`tools/build.py` ist veraltet** (siehe Schritt 4.1) — vor jedem Lauf prüfen, sonst zerstört er `index.html`.
- **ENIGMA, LINEAR, NATURAL sind engers-Serien** (Seiten 282–306), obwohl sie nachträglich importiert wurden — NICHT zu V&B verschieben. Nur URBAN PULSE und das neue V&B-PDF sind V&B.
- **Eindeutige IDs**: neue V&B-IDs immer mit `vb_`-Präfix; niemals bestehende IDs umbenennen (Bilddateien hängen am Namen).
- Ordnerinhalt wurde schon einmal extern geleert — die `tools/`-Skripte sind die Rettungsleine, neue Skripte dort ablegen und lauffähig hinterlassen.
