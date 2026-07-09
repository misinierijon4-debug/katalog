# Plan: Auftrags-Verwaltung zusammenlegen + automatische Kleben-Prüfung (Leere Tafeln + Poster)

Erstellt von: Claude (Planer-Rolle) — für Codex zur Umsetzung.
Branch: `ai/erste-aufgabe`

## Hintergrund / Begriffe (bitte zuerst lesen)

Bevor es losgeht, hier die wichtigsten Begriffe, damit nichts verwechselt wird:

- **Katalog-Webapp** (`index.html` + `katalog.js` + `katalog.json`): zeigt alle Mustertafeln aus dem PDF-Katalog. `katalog.js` enthält dieselben Daten wie `katalog.json`, aber als JavaScript-Variable `window.KATALOG_DATA` verpackt — dadurch funktioniert es auch, wenn man die Datei einfach per Doppelklick öffnet (kein Server nötig, kein `fetch()`-Problem).
- **Lagerkarte** (`lagerkarte_2.html`): eine eigenständige App, die den Bestand im Lager verwaltet (Tafeln-Bestand, Fliesen-Bestand, Auftragsprüfung, Auftrags-Verwaltung). Sie speichert alles im Browser (`localStorage`) und lädt aktuell **keine** Katalogdaten — das muss für Idee 2 und 3 ergänzt werden.
- **Mustertafel**: eine fertig geklebte Beispieltafel aus dem Katalog, z. B. `9557-IR21-04-10`. Steht im "Tafeln-Bestand" der Lagerkarte, wenn sie fertig ist.
- **Blanko-Tafel / "Leere Tafel"**: eine unbeklebte Rohtafel (nur die Platte), auf die eine neue Mustertafel geklebt wird. Liegt im **Fliesen**-Bestand, Kategorie "Leere Tafeln" (Codes wie `9557`, `9755`, `9539`, …). **Nicht verwechseln** mit dem Status "Tafel leer – neu kleben" im Tafeln-Bestand (das ist eine schon existierende Mustertafel, die leergeräumt wurde und neu beklebt werden muss — ein anderer Fall).
- **Kleben**: der Vorgang, eine neue Mustertafel herzustellen, indem man eine Blanko-Tafel + einzelne Fliesen-Stücke ("Bausteine", z. B. `BRI 3120`, `CAR 1270`) + ein Poster/Etikett zusammenfügt.
- **Poster / Etikett**: der bedruckte Aufkleber/das Bild, das auf die fertige Mustertafel kommt. Steht im Katalog-Datensatz im Feld `label` (z. B. `"Poster 91E0-IRO1-00-10"`).

## 1. Was gemacht werden soll

Drei zusammengehörige Änderungen an der Lagerkarte:

1. **Tabs zusammenlegen**: Die zwei getrennten Bereiche "Auftrag prüfen" und "Auftrags-Verwaltung" werden zu einem einzigen Tab "Auftrags-Verwaltung". Die Prüf-Funktion (Auftrag einfügen/hochladen und gegen den Bestand prüfen) ist danach komplett innerhalb dieses einen Tabs nutzbar, ein eigener "Auftrag prüfen"-Tab existiert nicht mehr.
2. **Leere Tafeln automatisch prüfen**: Für jede Mustertafel aus dem Katalog soll automatisch erkannt werden, welche Blanko-Tafel (leere Tafel) dafür gebraucht wird, und ob sie im Bestand ist — genau wie es heute schon für einzelne Fliesen-Codes geprüft wird. Dabei gilt: Codes, die nur im 2. Zeichen zwischen "9**5**xx" und "9**7**xx" unterscheiden, zählen als dieselbe Tafel (z. B. `9557` = `9757`).
3. **Poster-Verfügbarkeit prüfen**: Zusätzlich soll geprüft werden, ob das für eine Mustertafel benötigte Poster/Etikett verfügbar ist. Dafür wird ein neuer, zunächst leerer Poster-Bestand angelegt, den der Nutzer später manuell befüllt (die Katalog-Info dazu — welches Poster zu welcher Mustertafel gehört — ist bereits vorhanden).

Ziel-Endzustand: Wenn man in der Auftrags-Verwaltung einen Auftrag prüft und eine Position eine Mustertafel ist, die noch nicht fertig im Tafeln-Bestand liegt, zeigt das System automatisch: "Kleben möglich" (Blanko-Tafel + alle Fliesen-Bausteine + Poster vorhanden) oder "Kleben nicht möglich" mit einer aufklappbaren Liste, was genau fehlt.

## 2. Welche Dateien wahrscheinlich betroffen sind

| Datei | Was ändert sich |
|---|---|
| `lagerkarte_2.html` | Hauptdatei für alle drei Ideen: HTML-Struktur (Tabs/Sections), CSS (`data-view`-Regeln), JavaScript (Tab-Umschaltung, Prüf-Logik, neue Kleben-Prüf-Funktion, neue Poster-Kategorie) |
| `katalog.js` | Wird nur **gelesen** (liefert `window.KATALOG_DATA`), nicht inhaltlich verändert. Muss neu in `lagerkarte_2.html` eingebunden werden. |
| `katalog.json` | Nur zur Referenz/Kontrolle, keine Änderung nötig (Daten kommen zur Laufzeit aus `katalog.js`). |
| `index.html` | Kleiner Kontroll-Punkt: Zeile mit `LAGERKARTE_URL="../lagerkarte_2.html"` prüfen — da `lagerkarte_2.html` jetzt im selben Ordner wie `index.html` liegt, ist der Pfad vermutlich falsch und sollte `"lagerkarte_2.html"` (ohne `../`) heißen. Bitte vor dem Ändern kurz verifizieren, wie die Seite tatsächlich gehostet wird. |

Keine Änderungen nötig an: `auftraege.html`, `pruefliste.html`, `pruefliste.md`, den PDF-/Bild-Dateien, `ocr/`-Ordner.

## 3. Schritt-für-Schritt-Plan für Codex

### Idee 1: Tabs zusammenlegen

1. In `lagerkarte_2.html`: den Tab-Button mit `id="tabPruefen"` (Label "Auftrag prüfen") aus der Tab-Leiste entfernen.
2. Den kompletten Block `<div id="checkSection" class="check-section">…</div>` (enthält PDF-/Foto-Upload, Textfeld, "Prüfen"-Button, Ergebnis-Anzeige) aus seiner jetzigen Position herausnehmen und stattdessen an den Anfang von `<section id="auftraegeSection">…</section>` verschieben (direkt nach der Kopfzeile "Kommissionierung", vor der bestehenden PDF-Dropzone). Am besten als aufklappbaren Bereich "Auftrag manuell prüfen", damit die bestehende Dropzone nicht verdrängt wird.
3. CSS anpassen: Die Regel `#checkSection { display: none; }` bleibt als Basis-Zustand, aber `#app[data-view="pruefen"] #checkSection { display: block; }` durch `#app[data-view="auftraege"] #checkSection { display: block; }` ersetzen. Die gesamte CSS-Regelgruppe für `data-view="pruefen"` (blendet Dashboard/Karte/Banner aus) kann entfernt werden, da es diese Ansicht nicht mehr gibt.
4. In der JavaScript-Funktion `switchTab(tab)`: `"pruefen"` aus der Liste der erlaubten Tab-Werte entfernen.
5. Beim Laden des zuletzt aktiven Tabs aus dem Speicher (Prüfung auf `savedTab === "pruefen"`): diesen Fall entfernen bzw. auf `"auftraege"` umleiten, damit alte gespeicherte Zustände nicht zu einem Fehler führen.
6. Texte anpassen, die noch auf einen eigenen "Auftrag prüfen"-Tab verweisen (z. B. der Leertext in der Auftragsliste "…oder im Tab „Auftrag prüfen“ einen Auftrag prüfen…", die Erfolgsmeldung nach dem Speichern, die OCR-Fehlermeldung beim Foto-Upload) — auf die neue Struktur umformulieren (z. B. "…oder oben im Bereich „Auftrag prüfen“…").

### Idee 2: Leere Tafeln automatisch prüfen

7. In `lagerkarte_2.html` ein `<script src="katalog.js"></script>` einbinden (vor dem bestehenden `<script>`-Hauptblock), damit `window.KATALOG_DATA` zur Verfügung steht — genauso wie `index.html` es bereits macht.
8. Neue Hilfsfunktion schreiben, die aus einem Mustertafel-Code (z. B. `9557-IR21-04-10`) die ersten 4 Ziffern vor dem ersten Bindestrich herausschneidet (`9557`) — das ist der Code der benötigten Blanko-Tafel.
9. Neue Normalisierungs-Funktion für Blanko-Tafel-Codes schreiben: Ist das 2. Zeichen eine "7", durch "5" ersetzen (`9757` → `9557`), damit `95xx`- und `97xx`-Codes als gleich erkannt werden. Diese Funktion sowohl auf den benötigten Code (aus Schritt 8) als auch auf die Codes im Bestand ("Leere Tafeln"-Kategorie) anwenden, bevor verglichen wird.
10. Neue Funktion schreiben, die zu einem Mustertafel-Code den passenden Eintrag aus `window.KATALOG_DATA` findet (Vergleich über das `codes`-Array, mit der bereits vorhandenen `normalizeCode()`-Funktion normalisiert).
11. Neue Prüf-Funktion (z. B. `pruefeKlebenVerfuegbarkeit(mustertafelCode)`) schreiben, die für eine Mustertafel, die nicht bereits fertig im Tafeln-Bestand liegt:
    - die benötigte Blanko-Tafel ermittelt (Schritt 8+9) und deren Status im Fliesen-Bestand nachschlägt,
    - für jeden Eintrag in `artikel[]` des Katalog-Datensatzes (Feld `artnr`, z. B. `"BRI 3120"`) den Status im Fliesen-Bestand nachschlägt (gleiche Normalisierung wie bestehende Fliesen-Codes: Leerzeichen/Bindestriche entfernen, Großschreibung),
    - daraus ein Gesamtergebnis bildet: "kleben möglich" (alles vorhanden/nutzbar) oder "kleben nicht möglich" (mindestens etwas fehlt).
12. Diese Prüfung in die bestehende Auftragsprüfung einbauen: Wenn ein geprüfter Code nicht direkt im Tafeln-Bestand als "vorhanden" gilt, automatisch die neue Kleben-Prüfung aufrufen und das Ergebnis zusätzlich anzeigen (aufklappbare Detailliste mit ✓/? pro Baustein inkl. benötigter Menge aus `stueck`, plus Status der Blanko-Tafel) — ähnlich wie im Beispielbild mit "Kleben (Katalog S. …): ✓ BRI 3120 (je 4 St.) …".
13. Dieselbe Anzeige auch bei gespeicherten Aufträgen (Auftrags-Verwaltung, Positions-Tabelle) ergänzen, nicht nur beim erstmaligen Prüfen.

### Idee 3: Poster-Verfügbarkeit prüfen

14. Neue, zunächst leere Bestandskategorie "Poster-Bestand" anlegen (im Fliesen-Bestand, gleich aufgebaut wie die bestehende Kategorie "Leere Tafeln", aber mit `items: []`), damit sie über die normale Bestands-Oberfläche sichtbar ist und der Nutzer dort später Poster-Codes manuell einträgt.
15. Neue Hilfsfunktion schreiben, die aus dem Katalog-Feld `label` (z. B. `"Poster 91E0-IRO1-00-10"`, `"+ Etikett rückseitig 91E4-IRO1-00-10"`) den eigentlichen Code am Textende herausliest.
16. Die Kleben-Prüf-Funktion aus Idee 2 (Schritt 11) erweitern: falls der Katalog-Datensatz ein `label`-Feld hat, zusätzlich den daraus gelesenen Poster-Code im neuen Poster-Bestand nachschlagen und ins Gesamtergebnis einbeziehen (fehlendes Poster blockiert "kleben möglich" genauso wie ein fehlender Baustein).
17. In der Detailanzeige (Schritt 12) eine zusätzliche Zeile "Poster: ✓/? <Code>" ergänzen, nur wenn ein `label` vorhanden ist.

## 4. Welche Tests Codex machen soll

Nach jeder Idee einmal die Datei `lagerkarte_2.html` im Browser öffnen (Doppelklick reicht, kein Server nötig) und manuell durchklicken:

**Idee 1:**
- Es sind nur noch 3 Tabs sichtbar: Tafeln-Bestand, Fliesen-Bestand, Auftrags-Verwaltung.
- Im Tab "Auftrags-Verwaltung" ist der Prüf-Bereich (Upload/Textfeld/"Prüfen"-Button) sichtbar, oberhalb der Auftragsliste.
- Auftragstext einfügen → "Prüfen" klicken → Ergebnis erscheint, "Speichern" funktioniert, gespeicherter Auftrag taucht danach in der Liste darunter auf.
- Seite neu laden: kein Fehler in der Browser-Konsole, App startet normal (auch wenn vorher ein alter Zustand mit Tab "pruefen" gespeichert war).

**Idee 2:**
- Code `9557-IR21-04-10` eingeben (sofern nicht im Tafeln-Bestand): System erkennt "9557" als benötigte Blanko-Tafel und zeigt deren Status korrekt an.
- Bestand der Blanko-Tafel testweise von `9557` auf `9757` umbenennen: Ergebnis bleibt gleich (wird weiterhin als vorhanden erkannt) — Beleg für die 95/97-Gleichbehandlung.
- Blanko-Tafel komplett aus dem Bestand entfernen: Ergebnis wechselt zu "nicht im Lager" mit klarem Hinweis, was fehlt.
- Mustertafel mit mehreren Bausteinen prüfen: Detailliste zeigt jeden Baustein einzeln mit korrektem ✓/?-Status.
- Bestehende einfache Prüfung (Codes, die schon fertig im Bestand sind) funktioniert weiterhin unverändert — keine Regression.

**Idee 3:**
- Neue Kategorie "Poster-Bestand" ist im Fliesen-Bestand-Tab sichtbar (leer) und Codes lassen sich dort ganz normal hinzufügen.
- Mustertafel mit `label`-Feld prüfen: richtiger Poster-Code wird erkannt und als fehlend angezeigt (da Bestand noch leer ist).
- Poster-Code manuell im neuen Bestand ergänzen: Status wechselt zu "vorhanden".
- Mustertafel ohne `label`-Feld: keine Poster-Zeile, kein Fehler.

## 5. Wann die Aufgabe fertig ist

- Es gibt nur noch einen Tab "Auftrags-Verwaltung", der die komplette Auftragsprüfung enthält; kein separater "Auftrag prüfen"-Tab und keine toten Text-Verweise darauf mehr.
- Für jede Mustertafel aus dem Katalog erkennt das System automatisch die passende Blanko-Tafel (inkl. korrekter 95xx/97xx-Gleichbehandlung) und prüft deren Bestand genauso wie normale Fliesen-Codes.
- Für jede Mustertafel mit Poster-Angabe im Katalog wird die Verfügbarkeit im neuen (anfangs leeren) Poster-Bestand geprüft und angezeigt.
- Die Auftragsprüfung zeigt bei fehlender fertiger Mustertafel klar an, ob "Kleben möglich" ist, und falls nicht, was genau fehlt (Blanko-Tafel, welche Bausteine, Poster).
- Alle in Abschnitt 4 genannten Tests wurden manuell durchgeführt und funktionieren wie beschrieben, ohne bestehende Funktionen (Tafeln-/Fliesen-Bestand, Speichern/Laden, PDF-Import) zu beschädigen.
