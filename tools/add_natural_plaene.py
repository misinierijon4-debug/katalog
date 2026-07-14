"""Add NATURAL-Anordnungspläne (Seiten 2-4) als Katalogeinträge.

Siehe PLAN_NATURAL_ANORDNUNGSPLAENE.md. Die Pläne haben keine echten
engers-Tafelcodes; hier werden künstliche Codes `<Größen-Präfix>-NAT-<01..08>`
vergeben. Seite 1 (echte Tafeln 9555-NATU-..) bleibt unangetastet.

34 neue Einträge: 16 von PDF-Seite 4 (Designs 01-04) + 18 von Seiten 2-3
(Designs 05-08). Bei Designs 06/08 wird 72x78 übersprungen, weil diese
Kombination bereits als echte Tafel (9555-NATU-04/02-10, Seite 306) existiert;
dort wird stattdessen eine Verweis-Notiz ergänzt.

Run:  uv run --python 3.12 --with pymupdf --with pillow python tools/add_natural_plaene.py
"""
import fitz, io, json, os, re, sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"
SERIE = "NATURAL"
MATERIAL = "Steingut 30x60cm"
PT2PX200 = 200.0 / 72.0
FARBE = {"NAT 1240": "beige", "NAT 1280": "grau"}

# Größen-Präfix -> (Codes für den Eintrag, tafel_groesse, gt)
SIZES = {
    "72x78":  (["9555"],                 "GT 72x78 cm",                  True),
    "65x65":  (["9740", "9540"],         "65x65 cm",                     False),
    "92x92":  (["9739", "9539"],         "92x92 cm",                     False),
    "125x92": (["9552"],                 "125x92 cm",                    False),
    "65x130": (["9785", "9585"],         "65x130 cm",                    False),
    "94x134": (["9557"],                 "94x134 cm",                    False),
    "184":    (["9562", "9566", "9569"], "97x184 / 104x184 / 107x184 cm", False),
    "100,5":  (["9568", "9587"],         "100,5x192,5 cm",               False),
}
SIZES_P4 = ["72x78", "65x65", "92x92", "125x92"]
SIZES_P23 = ["72x78", "65x130", "94x134", "184", "100,5"]
GROESSEN_NOTE_P4 = "Größen laut Plan: 72x78 / 65x65 / 92x92 / 125x92 cm"
GROESSEN_NOTE_P23 = ("Größen laut Plan: 72x78 / 65x130 / 94x134 / "
                     "97x184 / 104x184 / 107x184 / 100,5x192,5 cm")


def art(artnr, groesse=None):
    a = {"artnr": artnr}
    if artnr in FARBE:
        a["farbe"] = FARBE[artnr]
    if groesse:
        a["groesse"] = groesse
    return a


# Design-Definitionen. pdf_page ist 0-indexiert; panel_x = ungefähre x0 des
# zugehörigen Board-Panels (zur Zuordnung Panel<->Design).
DESIGNS = [
    # ---- PDF-Seite 4 (Katalog-Seite 309): Mosaik-Designs 01-04 ----
    {"nr": "01", "pdf_page": 3, "seite": 309, "panel_x": 44,
     "artikel": [art("NAT 1220", "30x60 cm"), art("NAT 1222")],
     "sizes": SIZES_P4, "skip72": False, "poster": None,
     "caption": "NAT1220 mit Mosaik NAT1222", "gnote": GROESSEN_NOTE_P4, "sonder": False},
    {"nr": "02", "pdf_page": 3, "seite": 309, "panel_x": 301,
     "artikel": [art("NAT 1270", "30x60 cm"), art("NAT 1272")],
     "sizes": SIZES_P4, "skip72": False, "poster": None,
     "caption": "NAT1270 mit Mosaik NAT1272", "gnote": GROESSEN_NOTE_P4, "sonder": False},
    {"nr": "03", "pdf_page": 3, "seite": 309, "panel_x": 95,
     "artikel": [art("NAT 1250", "30x60 cm"), art("NAT 1252")],
     "sizes": SIZES_P4, "skip72": False, "poster": None,
     "caption": "NAT1250 mit Mosaik NAT1252", "gnote": GROESSEN_NOTE_P4, "sonder": False},
    {"nr": "04", "pdf_page": 3, "seite": 309, "panel_x": 366,
     "artikel": [art("NAT 1260", "30x60 cm"), art("NAT 1262")],
     "sizes": SIZES_P4, "skip72": False, "poster": None,
     "caption": "NAT1260 mit Mosaik NAT1262", "gnote": GROESSEN_NOTE_P4, "sonder": False},
    # ---- PDF-Seite 2 (Katalog-Seite 307): Designs 05-06 ----
    {"nr": "05", "pdf_page": 1, "seite": 307, "panel_x": 44,
     "artikel": [art("NAT 1280", "30x60 cm"), art("NAT 1224"), art("NAT 1274"),
                 art("NAT 1220"), art("NAT 1270")],
     "sizes": SIZES_P23, "skip72": False, "poster": "Poster NATURAL 30x60 grau",
     "caption": "NAT1280 mit Dekoren NAT1224 / 1274 und Boden NAT1220 / 1270",
     "gnote": GROESSEN_NOTE_P23, "sonder": True},
    {"nr": "06", "pdf_page": 1, "seite": 307, "panel_x": 304,
     "artikel": [art("NAT 1280", "30x60 cm"), art("NAT 1214", "ca 9x60 cm"),
                 art("NAT 1270")],
     "sizes": SIZES_P23, "skip72": True, "poster": "Poster NATURAL 30x60 beige",
     "caption": "NAT1280 mit Dekor NAT1214 und Boden NAT1270",
     "gnote": GROESSEN_NOTE_P23, "sonder": True},
    # ---- PDF-Seite 3 (Katalog-Seite 308): Designs 07-08 ----
    {"nr": "07", "pdf_page": 2, "seite": 308, "panel_x": 43,
     "artikel": [art("NAT 1240", "30x60 cm"), art("NAT 1254"), art("NAT 1264"),
                 art("NAT 1250"), art("NAT 1260")],
     "sizes": SIZES_P23, "skip72": False, "poster": "Poster NATURAL 30x60 braun",
     "caption": "NAT1240 mit Dekoren NAT1254 / 1264 und Boden NAT1250 / 1260",
     "gnote": GROESSEN_NOTE_P23, "sonder": True},
    {"nr": "08", "pdf_page": 2, "seite": 308, "panel_x": 303,
     "artikel": [art("NAT 1240", "30x60 cm"), art("NAT 1214", "ca 9x60 cm"),
                 art("NAT 1250"), art("NAT 1260")],
     "sizes": SIZES_P23, "skip72": True, "poster": "Poster NATURAL 30x60 beige",
     "caption": "NAT1240 mit Dekor NAT1214 und Boden NAT1250 / 1260",
     "gnote": GROESSEN_NOTE_P23, "sonder": True},
]

# Verweis-Notiz für die echten 72x78-Tafeln von Seite 306 (Design 06 & 08).
CROSSREF = {
    "9555-NATU-04-10": "Weitere Größen als Anordnungsplan: siehe 9562-NAT-06 u. a. (Katalogseite 307)",
    "9555-NATU-02-10": "Weitere Größen als Anordnungsplan: siehe 9562-NAT-08 u. a. (Katalogseite 308)",
}

KUENSTLICH_NOTE = "Anordnungsplan ohne eigenen Tafelcode — Code künstlich vergeben (NAT-01…08)"


def board_panels(page):
    panels = []
    for d in page.get_drawings():
        if d.get("fill") is None:
            continue
        r = d["rect"]
        if r.width > 100 and r.height > 100 and r.y0 > 40:
            panels.append(r)
    return [r for r in panels if not any(o != r and o.contains(r) for o in panels)]


def save_jpg(pix, path, maxdim, q):
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img.thumbnail((maxdim, maxdim), Image.LANCZOS)
    img.save(path, "JPEG", quality=q, optimize=True)


doc = fitz.open(os.path.join(PROJ, "Mustertafeln NATURAL.pdf"))
os.makedirs(os.path.join(PROJ, "images", "large"), exist_ok=True)
os.makedirs(os.path.join(PROJ, "images", "thumb"), exist_ok=True)

# Panels pro Seite einmalig ermitteln und dem jeweiligen Design zuordnen.
panels_by_page = {p: board_panels(doc[p]) for p in (1, 2, 3)}

entries = []
for dz in DESIGNS:
    page = doc[dz["pdf_page"]]
    panels = panels_by_page[dz["pdf_page"]]
    board = min(panels, key=lambda r: abs(r.x0 - dz["panel_x"])) if panels else None

    # Bild einmal pro Design croppen (wird für alle Größen-Varianten geteilt).
    board_img_pix = None
    board_px200 = None
    if board:
        r = board + fitz.Rect(-4, -4, 4, 4)
        r &= page.rect
        board_img_pix = page.get_pixmap(dpi=180, clip=r)
        board_px200 = [round(v * PT2PX200) for v in (r.x0, r.y0, r.x1, r.y1)]
    else:
        print(f"  !! kein Panel für Design {dz['nr']}")

    for skey in dz["sizes"]:
        if skey == "72x78" and dz["skip72"]:
            continue
        prefixes, tg, gt = SIZES[skey]
        codes = [f"{p}-NAT-{dz['nr']}" for p in prefixes]
        entry_id = f"p{dz['seite']}_{codes[0].replace('-', '')}"

        notizen = [KUENSTLICH_NOTE, dz["gnote"]]
        if dz["sonder"]:
            notizen.append("Sonderanfertigung möglich")

        entry = {
            "id": entry_id, "seite": dz["seite"], "serie": SERIE, "name": None,
            "material": MATERIAL, "codes": codes, "tafel_groesse": tg, "gt": gt,
            "artikel": [dict(a) for a in dz["artikel"]],
            "label": dz["poster"], "notizen": notizen,
            "marke": "engers", "display": False, "board_px200": board_px200,
        }
        entries.append(entry)

        if board_img_pix is not None:
            save_jpg(board_img_pix, os.path.join(PROJ, "images", "large", entry_id + ".jpg"), 1100, 80)
            save_jpg(board_img_pix, os.path.join(PROJ, "images", "thumb", entry_id + ".jpg"), 420, 74)

print(f"NATURAL-Pläne: {len(entries)} Einträge erzeugt")
for e in entries:
    print(f'  {e["id"]:20s} {e["codes"]}  {e["tafel_groesse"]:32s} {len(e["artikel"])} Art. label={e["label"]!r}')

# ---- lossless Druckseiten 307-309 (PDF-Seiten 2-4) ----
for pdf_page, seite in ((1, 307), (2, 308), (3, 309)):
    dst = fitz.open()
    dst.insert_pdf(doc, from_page=pdf_page, to_page=pdf_page)
    dst.save(os.path.join(PROJ, "pages", f"seite-{seite:03d}.pdf"), garbage=4, deflate=True)
    dst.close()
    print(f"Druckseite seite-{seite:03d}.pdf geschrieben")
doc.close()

# ---- katalog.json ----
kat_path = os.path.join(PROJ, "katalog.json")
with open(kat_path, encoding="utf-8") as f:
    kat = json.load(f)
key = next(k for k in kat if "eintr" in k)

# Idempotent: eigene künstliche NAT-Einträge entfernen (echte 9555-NATU-.. bleiben,
# da "-NAT-" nicht in "-NATU-" vorkommt).
before = len(kat[key])
kat[key] = [e for e in kat[key] if not any("-NAT-" in c for c in e.get("codes", []))]
removed = before - len(kat[key])
if removed:
    print(f"  {removed} vorhandene NAT-Plan-Einträge ersetzt")

# Verweis-Notizen bei den echten Seite-306-Tafeln setzen (idempotent).
for e in kat[key]:
    for c in e.get("codes", []):
        if c in CROSSREF and CROSSREF[c] not in e.get("notizen", []):
            e.setdefault("notizen", []).append(CROSSREF[c])

kat[key].extend(entries)

note = "Mustertafeln NATURAL.pdf Anordnungspläne (Seiten 307-309)"
if note not in kat.get("quelle", ""):
    kat["quelle"] = kat.get("quelle", "") + " | " + note

with open(kat_path, "w", encoding="utf-8") as f:
    json.dump(kat, f, ensure_ascii=False, indent=1)
print("katalog.json:", len(kat[key]), "Einträge")
