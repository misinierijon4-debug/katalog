# Plan: Fehlende Tafeln aus den Stücklisten in den Katalog aufnehmen

Stand: 15.07.2026 · Analyse der `ENGERS_SampleBoard_Stuecklisten_Eingabeliste.xlsx`
(Blatt „Masterdaten", aus `Downloads\MuTa Kataloge (1).zip\01_ENGERS`)

## Fortschritt (erledigt)

| Serie | Tafeln | Seiten | Commit |
|---|---|---|---|
| CEMENTO (CE46/CE87) | 2 | 311 | ee0e1ec |
| CENTRO | 28 | 312–325 | cd190a6 |
| NEO | 32 | 326–341 | cd190a6 |
| COLOR IT (inkl. EO) | 58 | 342–370 | 43a0570 |

Pipeline steht in `tools/stuecklisten/`: `gen_entries.ps1` (BOM→Einträge+Farben),
`gen_svg.ps1` (Board-SVG + A4-Seiten im Engers-Format), `render_batch.ps1`
(Edge-headless → seite-NNN.pdf + Thumbnails, direkte `& $edge`-Aufrufe mit
ErrorAction=Continue!), `insert_entries.ps1` (CRLF-toleranter Textsplice in
katalog.json + katalog.js). Nächste Serie: BOM extrahieren → gen_entries mit
`-StartSeite 371 -SerieName "<X>"` → gen_svg → render_batch → insert → commit.

## Befund

| | Anzahl |
|---|---|
| Materialcodes in Masterdaten gesamt | 3.073 |
| davon mit Tafel-Prefix (95xx/97xx wie im Katalog) | 2.937 |
| davon **nicht** im Katalog | 982 |
| davon echte Mustertafeln/Grundtafeln (Beschreibung „MT…"/„GT…") | **477** |
| → Variante eines vorhandenen Eintrags (Basis-Code schon im Katalog) | 10 |
| → komplett neue Tafeln (wie CEMENTO CE46/CE87) | **467** |

Der Rest der 982 sind Verkaufsposter (VP), Etiketten, Milieubilder, Übersichten und
Anonym-Varianten — **nicht katalogrelevant**.

Bereits erledigt als Muster: Serie CEMENTO `9557-CE46-04-10` + `9557-CE87-04-10`
→ Seite 311, Commit `ee0e1ec`. Genau dieses Verfahren wird für alle weiteren verwendet.

## Neue Tafeln nach Serien (467)

| Serie | Anzahl | Serie | Anzahl |
|---|---|---|---|
| SPA / SPA 2.0 | 87 | UNDERGROUND | 12 |
| TIME OUT | 84 | BEACH | 11 |
| STONEHENGE | 44 | FORUM | 9 |
| NATURAL | 42 | WOOD | 6 |
| COLOR IT (inkl. EO-Codes) | ~40 | RELAX | 6 |
| AMAZINGSTONE | 28 | ENIGMA | 4 |
| CENTRO | 26 | MADERA | 4 |
| NEO | 20 | HOME | 3 |
| | | X13/X18/X19/X20 + Sonstige | ~21 (unklar, manuell prüfen) |

Vollständige Listen: `tools/stuecklisten/fehlende_tafeln_neu.tsv` (Code + Beschreibung)
und `tools/stuecklisten/fehlende_tafeln_varianten.tsv`.

## Vorgehen (pro Serie ein Batch)

Wie bei CEMENTO Seite 311, aber skriptgesteuert:

1. **BOM extrahieren:** Für jeden Tafel-Code alle Stücklisten-Zeilen aus Masterdaten
   (Artikel, Stück, Beschreibung, Poster, Trägerplatte). Parser existiert als
   PowerShell-Ansatz (sharedStrings + sheet3.xml per Regex); als Skript nach
   `tools/stuecklisten/extract_bom.ps1` gießen.
2. **Tafelgröße bestimmen:** steht direkt in der Beschreibung („MT 92x92CM…",
   „GT 72x78CM…"). Prefix-Tabelle als Fallback (9555=GT 72x78, 9557=94x134,
   9585=65x130, 9524=123x164, 9539=92x92, 9540=65x65, 9552=125x92/92x125, …).
3. **Klebevorlage generieren:** Engers-Katalogformat (A4, „engers"-Logo, Serie rechts,
   Tafel-Grafik + Artikelliste) als HTML/SVG. Layout schematisch: Poster oben links,
   Fliesen proportional angeordnet, Bricks/Dekore als Streifenzone. Hinweiszeile
   „kein Original-Plan – eigene Anordnung". 2 Tafeln pro A4-Seite (wie Seite 311).
4. **PDF erzeugen:** Edge headless `--print-to-pdf` → `pages/seite-3xx.pdf`,
   fortlaufend ab **Seite 312**.
5. **Thumbnails:** Edge headless `--screenshot` pro Tafel → JPG via System.Drawing
   nach `images/thumb/` + `images/large/` (ID-Schema `p3xx_<code ohne Bindestriche>`).
6. **Katalog-Einträge:** in `katalog.json` einfügen (Format wie CE-Einträge, Notiz
   „aus ENGERS_SampleBoard-Stückliste (BOM …), kein Original-Plan"), `katalog.js`
   konsistent mitschreiben (kein Python auf dem Rechner — textuelles Einfügen oder
   PowerShell-Nachbau von `tools/build.py`).
7. **Validieren** (beide Dateien parsen, Anzahl vergleichen), **committen & pushen** —
   ein Commit pro Serie, damit es reviewbar bleibt.

## Die 10 Varianten — ERLEDIGT (07/2026)

`9552-TE60/TE90-0A`, `9555-NATU-01/03`, `9588-KV70/80/90-0C`, `9592-KV70/80/90-0C`:
Basis-Tafel existiert schon im Katalog mit anderem Suffix. Abgleich-Ergebnis:

- `9555-NATU-01/03-10`: bereits eigene Einträge (Seiten 307/308 aus den
  NATURAL-Anordnungsplänen) — nichts zu tun.
- Die übrigen 8 (`9552-TE60/TE90-0A`, `9588-KV70/80/90-0C`, `9592-KV70/80/90-0C`):
  Stücklisten-Beschreibung (Größe + Artikel) stimmt mit dem jeweils vorhandenen
  Eintrag überein → Alt-Code beim vorhandenen Eintrag ergänzt (wie 07/2026 bei
  PH…-08 gemacht), mit Notiz-Vermerk in `katalog.json`/`katalog.js`.

## Offene Punkte / Entscheidungen

- **Scope:** Alle 467 aufnehmen oder nur aktive Serien? Viele sind Altserien
  (SPA, TIME OUT, STONEHENGE …), die evtl. nie mehr geklebt werden.
  → Empfehlung: mit den Serien anfangen, die tatsächlich noch gebraucht werden;
  Rest nach und nach.
- **Codes mit Datenfehlern:** z. B. `9568-EOO!-00-10` (Ausrufezeichen), Beschreibungen
  mit abgeschnittenem Text — beim jeweiligen Batch manuell klären.
- **X13/X18/X19/X20-Codes** (~13 St.): unklare Serien, vor Aufnahme prüfen.
- Layout bleibt schematisch (keine echten Anordnungspläne vorhanden). Wenn Engers
  später Original-Pläne liefert, Seite austauschen.

## Reihenfolge (Vorschlag)

1. Varianten-Abgleich (10 St., schnell, keine neuen Seiten nötig)
2. Serien nach Bedarf des Lagers — sonst nach Größe absteigend:
   SPA → TIME OUT → STONEHENGE → NATURAL → COLOR IT → AMAZINGSTONE → CENTRO →
   NEO → UNDERGROUND → BEACH → FORUM → Rest
3. Zum Schluss Sonderfälle (X-Codes, Datenfehler)
