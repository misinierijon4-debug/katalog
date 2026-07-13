# PLAN: NATURAL-Serie vollständig in den Katalog (Anordnungspläne, Seiten 2–4)

**Auftrag:** Die NATURAL-Anordnungspläne (Seiten 2–4 der PDF) haben keine eigenen
engers-Tafelcodes. Sie sollen trotzdem als Katalogeinträge erscheinen — mit
künstlichen Codes nach dem Muster `<Größen-Präfix>-NAT-<Designnummer>`
(Beispiel vom Nutzer: die vier Mosaik-Tafeln auf Seite 4 heißen
`9740-NAT-01` … `9740-NAT-04`, und weil 65x65 auch dem engers-Code 9540
entspricht, soll `9540-NAT-01` … ebenfalls als Name auftauchen).

## Quelle & Ist-Zustand (verifiziert am 13.07.2026)

- Quelldatei: `Mustertafeln NATURAL.pdf` im Projektordner — **identisch**
  (MD5 `32caf1d2…`) mit der vom Nutzer geschickten
  `%TEMP%\Mustertafelpläne NATURALneu.pdf`. 4 Seiten.
- Seite 1 ist bereits importiert (via `tools/add_natural.py`, Katalog-Seite 306):
  `9555-NATU-02-10` (NAT1240 beige + Dekor NAT1214, GT 72x78) und
  `9555-NATU-04-10` (NAT1280 grau + Dekor NAT1214, GT 72x78). Diese bleiben unverändert.
- Seiten 2–4 sind Anordnungspläne mit gerenderten Tafelbildern (croppbar!) und
  Größenlisten unter jeder Tafel — bisher NICHT im Katalog.
- `katalog.json`: 1266 Einträge, alle mit `marke` (`engers`/`vb`).

## Größen-Präfix-Zuordnung (aus katalog.json abgeleitet, belegt)

Jedes 4-stellige Code-Präfix steht für eine feste Tafelgröße. 95xx = engers,
97xx = V&B-Pendant derselben Größe. Bei Größen-Gruppen trägt ein Eintrag im
Bestand mehrere Codes (Vorbild: `9562-/9566-/9569-IR21-04-10` existieren als
Codes EINES Eintrags).

| Größe laut PDF | Codes für den Eintrag (Reihenfolge so übernehmen) |
|---|---|
| 72x78 (GT) | `9555-NAT-nn` |
| 65x65 | `9740-NAT-nn`, `9540-NAT-nn` *(9740 zuerst — explizite Nutzer-Vorgabe)* |
| 92x92 | `9739-NAT-nn`, `9539-NAT-nn` |
| 125x92 | `9552-NAT-nn` *(engers führt sie als 92x125; kein V&B-Pendant im Katalog)* |
| 65x130 | `9785-NAT-nn`, `9585-NAT-nn` |
| 94x134 | `9557-NAT-nn` |
| 97x184 / 104x184 / 107x184 | `9562-NAT-nn`, `9566-NAT-nn`, `9569-NAT-nn` (EIN Eintrag, drei Codes) |
| 100,5x192,5 | `9568-NAT-nn`, `9587-NAT-nn` (EIN Eintrag; Vorbild „100,5x192,5 / 100x200 cm“-Einträge) |
| Sonderanfertigung | kein eigener Eintrag — nur als Notiz „Sonderanfertigung möglich“ |

Anmerkung: Für 65x65 gäbe es auch V&B-Präfix 9705 — der Nutzer hat aber
ausdrücklich 9740 benannt; 9705 NICHT verwenden.

## Die 8 Designs und ihre Nummern

Seite 4 = Designs 01–04 (Nutzer-Vorgabe, Reihenfolge wie im PDF), Seiten 2–3
laufen als 05–08 weiter (Annahme — Reihenfolge wie im PDF):

| Nr. | PDF-Seite | Design (Artikel) | Poster/Label | Größen → Einträge |
|---|---|---|---|---|
| 01 | 4 | Wand NAT1220 + Mosaik NAT1222 | — | 72x78, 65x65, 92x92, 125x92 → 4 Einträge |
| 02 | 4 | Wand NAT1270 + Mosaik NAT1272 | — | dito → 4 Einträge |
| 03 | 4 | Wand NAT1250 + Mosaik NAT1252 | — | dito → 4 Einträge |
| 04 | 4 | Wand NAT1260 + Mosaik NAT1262 | — | dito → 4 Einträge |
| 05 | 2 | Wand NAT1280 + Dekore NAT1224/1274 + Boden NAT1220/1270 | Poster (s. u.) | 72x78, 65x130, 94x134, 97/104/107x184, 100,5x192,5 → 5 Einträge |
| 06 | 2 | Wand NAT1280 + Dekor NAT1214 + Boden NAT1270 | Poster (s. u.) | dito, **aber 72x78 überspringen** → 4 Einträge |
| 07 | 3 | Wand NAT1240 + Dekore NAT1254/1264 + Boden NAT1250/1260 | Poster (s. u.) | wie 05 → 5 Einträge |
| 08 | 3 | Wand NAT1240 + Dekor NAT1214 + Boden NAT1250/1260 | Poster (s. u.) | wie 06, **72x78 überspringen** → 4 Einträge |

**Warum 72x78 bei 06/08 überspringen:** Design 06 (NAT1280+NAT1214) und 08
(NAT1240+NAT1214) existieren in GT 72x78 bereits als ECHTE Tafeln
`9555-NATU-04-10` bzw. `9555-NATU-02-10` (Seite 306). Kein Duplikat anlegen;
stattdessen bei den bestehenden zwei Einträgen eine Notiz ergänzen:
„Weitere Größen als Anordnungsplan: siehe 9562-NAT-06 …“ bzw. „…-NAT-08“.

**Poster-Zuordnung Seiten 2–3:** Auf Seite 2 stehen „Poster NATURAL 30x60 grau“
und „… beige“, auf Seite 3 „… braun“ und „… beige“. Zuordnung zum Design NICHT
raten, sondern über die x/y-Koordinaten der Textspans zum nächstliegenden
Tafel-Panel bestimmen (wie `add_natural.py` das mit Codes macht).

**Gesamt: 34 neue Einträge** (16 von Seite 4 + 18 von Seiten 2–3).

## Eintrags-Schema (bestehendem Muster folgen)

```json
{
  "id": "p309_9740NAT01",            // p<seite>_<erster Code ohne Bindestriche>
  "seite": 309,                       // PDF-Seite 2→307, 3→308, 4→309
  "serie": "NATURAL",
  "material": "Steingut 30x60cm",
  "codes": ["9740-NAT-01", "9540-NAT-01"],
  "tafel_groesse": "65x65 cm",       // Schreibweise engers-Stil ohne Leerzeichen um das x
  "gt": false,                        // true nur bei 72x78 (GT)
  "artikel": [
    {"artnr": "NAT 1220", "groesse": "30x60 cm"},
    {"artnr": "NAT 1222"}             // Mosaik; stueck ist im Plan nicht angegeben → weglassen
  ],
  "label": null,                      // bzw. "Poster NATURAL 30x60 grau" (Seiten 2–3)
  "notizen": ["Anordnungsplan ohne eigenen Tafelcode — Code künstlich vergeben (NAT-01…08)",
               "Größen laut Plan: 72x78 / 65x65 / 92x92 / 125x92 cm",
               "Sonderanfertigung möglich"],   // letzteres nur Designs 05–08
  "marke": "engers",                  // WICHTIG, s. u.
  "display": false,
  "board_px200": [...]                // wie add_natural.py
}
```

- **`marke: "engers"` ist Pflicht** — sonst stuft die Lagerkarte
  (`markeFuerCode`, Präfix-Fallback 97xx→V&B) `9740-NAT-…` fälschlich als V&B
  ein. Das Katalog-Feld hat Vorrang vor dem Präfix-Fallback.
- Bekannte Farben aus Seite 1 übernehmen: NAT1240 = beige, NAT1280 = grau,
  NAT1214 = Dekor. Unbekannte Farben (Boden 1220/1250/1260/1270, Mosaike) weglassen.

## Umsetzungsschritte

1. **Neues Skript `tools/add_natural_plaene.py`** (Vorbild `add_natural.py`):
   - `Mustertafeln NATURAL.pdf` Seiten 2–4 öffnen (fitz/PyMuPDF).
   - Pro Seite Tafel-Panels finden (`board_panels`-Ansatz: große gefüllte
     Rechtecke; Seite 4 hat 4 Panels, Seiten 2–3 je 2).
   - Text-Spans („Mustertafel NATURAL … NAT12xx …“, „Größen …“, „Poster …“,
     „NAT12xx“-Labels) per Koordinaten dem nächsten Panel zuordnen.
   - Pro Design und Größen-Zeile die Einträge nach obiger Tabelle erzeugen.
   - Bilder croppen: `images/large/<id>.jpg` (1100px, q80) und
     `images/thumb/<id>.jpg` (420px, q74). Größen-Varianten desselben Designs
     teilen sich dasselbe Bild (Crop einfach mehrfach unter den jeweiligen ids speichern).
   - Druckseiten lossless ablegen: `pages/seite-307.pdf` … `seite-309.pdf`
     (PDF-Seiten 2–4 einzeln).
   - Idempotent: vor dem Einfügen alle Einträge mit `"-NAT-"` in den Codes
     entfernen (die echten `9555-NATU-…` von Seite 306 NICHT anfassen).
   - `katalog.json` aktualisieren, `quelle`-String ergänzen.
2. **`katalog.js` NUR über `tools/build.py` neu bauen.** Achtung Falle: der
   Inline-Rebuild in `add_natural.py` verwirft das `marke`-Feld (Regression!) —
   nicht kopieren. Run: `uv run --python 3.12 python tools/build.py`.
3. **Verifikation** (lokaler Server, launch.json „mustertafeln-katalog“, Port 8642):
   - `build.py`-Ausgabe: 1266 + 34 = 1300 Einträge; engers-Zähler +34.
   - Suche im Katalog-UI nach `9740-NAT`, `9540-NAT-01`, `9562-NAT-06` → Treffer
     mit Bild, Größe, Artikeln.
   - Stichprobe Lagerkarte (`lagerkarte_2.html` im Desktop-Root):
     `markeFuerCode("9740-NAT-01")` muss `engers` liefern.
   - Die 2 bestehenden NATURAL-Einträge (Seite 306) unverändert + neue Notiz.
4. **Commit & Push** ins Repo `misinierijon4-debug/katalog` (Hinweis: im
   Arbeitsverzeichnis liegen bereits ältere uncommittete Änderungen —
   NATURAL-Arbeit als eigenen, sauberen Commit halten; die alten Änderungen
   vorher separat committen oder gezielt stagen).

## Offene Annahmen (bei Abweichung Nutzer fragen)

- Designs der Seiten 2–3 werden als NAT-05…08 durchnummeriert (nur 01–04 waren vorgegeben).
- 9705 wird für 65x65 bewusst NICHT vergeben (Nutzer nannte 9740).
- Bei 06/08 wird die 72x78-Variante wegen der echten Codes von Seite 306 übersprungen.
