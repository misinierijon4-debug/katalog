"""Add the two missing TREASURE poster boards (TR18, gletscherweiß glänzend)
from "TREASURE B.pdf" page 4 as catalog page 310, and register alternative
order codes found in the Stücklisten exports:
  - PHOENIX 9540/9555-PH25/26/28/29-08-10 -> same boards as the -0B codes
  - MINERAL WALL/GARDENER 9560-GA21-04-10 -> 97x184 board (alias of 9569)

Run with:  uv run --python 3.12 --with pymupdf --with pillow python tools/add_treasure_b.py
Afterwards: tools/build.py + tools/build_auftraege.py
"""
import fitz, io, json, os, shutil, sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"
SRC = os.path.join(PROJ, "TREASURE B.pdf")
if not os.path.exists(SRC):
    SRC = r"C:\Users\Mirsad.Karasalihovic\AppData\Local\Temp\TREASURE B.pdf"
SEITE = 310
PT2PX200 = 200.0 / 72.0

kat_path = os.path.join(PROJ, "katalog.json")
with open(kat_path, encoding="utf-8") as f:
    kat = json.load(f)
entries = kat["einträge"]
by_id = {e["id"]: e for e in entries}
all_codes = {c for e in entries for c in e["codes"]}


def save_jpg(pix, path, maxdim, q):
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img.thumbnail((maxdim, maxdim), Image.LANCZOS)
    img.save(path, "JPEG", quality=q, optimize=True)


# --- 1) TREASURE TR18 poster boards from page 4 -------------------------
doc = fitz.open(SRC)
page = doc[3]
# board photos are stacks of image strips; group by column (left/right of x=300)
cols = {"L": [], "R": []}
for info in page.get_image_info():
    b = fitz.Rect(info["bbox"])
    if b.y0 < 100 or b.width < 150:   # logo etc.
        continue
    cols["L" if b.x0 < 300 else "R"].append(b)
boards = {}
for k, rects in cols.items():
    r = rects[0]
    for o in rects[1:]:
        r |= o
    boards[k] = r
print("Tafelfotos:", {k: tuple(round(v) for v in (r.x0, r.y0, r.x1, r.y1)) for k, r in boards.items()})

neu = [
    {
        "id": f"p{SEITE}_9524TR180410",
        "seite": SEITE,
        "serie": "TREASURE",
        "material": "Steingut 60x120cm",
        "codes": ["9524-TR18-04-10", "9569-TR18-04-10", "9562-TR18-04-10", "9566-TR18-04-10"],
        "tafel_groesse": "123x164 / 97x184 / 104x184 / 107x184 cm",
        "gt": False,
        "artikel": [
            {"artnr": "TRE 2880", "stueck": "1", "farbe": "gletscherweiß glzd.", "groesse": "60x120 cm"},
            {"artnr": "TRE 2881", "stueck": "1", "farbe": "Dekor", "groesse": "60x120 cm"},
        ],
        "label": "Poster 91E3-TRE2-00-10",
        "notizen": [],
        "display": False,
        "marke": "engers",
        "_board": "L",
    },
    {
        "id": f"p{SEITE}_9568TR180410",
        "seite": SEITE,
        "serie": "TREASURE",
        "material": "Steingut 60x120cm",
        "codes": ["9568-TR18-04-10", "9587-TR18-04-10", "9589-TR18-04-10", "9548-TR18-04-10"],
        "tafel_groesse": "100,5x192,5 / 100x200 / 123x200 / 123x209 cm",
        "gt": False,
        "artikel": [
            {"artnr": "TRE 2880", "stueck": "1", "farbe": "gletscherweiß glzd.", "groesse": "60x120 cm"},
            {"artnr": "TRE 2881", "stueck": "1", "farbe": "Dekor", "groesse": "60x120 cm"},
        ],
        "label": "Poster 91E3-TRE2-00-10",
        "notizen": [],
        "display": False,
        "marke": "engers",
        "_board": "R",
    },
]
for e in neu:
    if e["codes"][0] in all_codes:
        print(f"übersprungen (schon da): {e['codes'][0]}")
        continue
    r = boards[e.pop("_board")] + fitz.Rect(-3, -3, 3, 3)
    r &= page.rect
    pix = page.get_pixmap(dpi=180, clip=r)
    save_jpg(pix, os.path.join(PROJ, "images", "large", e["id"] + ".jpg"), 1100, 80)
    save_jpg(pix, os.path.join(PROJ, "images", "thumb", e["id"] + ".jpg"), 420, 74)
    e["board_px200"] = [round(v * PT2PX200) for v in (r.x0, r.y0, r.x1, r.y1)]
    entries.append(e)
    print(f"neu: {e['id']}  codes={e['codes']}")

dst = fitz.open()
dst.insert_pdf(doc, from_page=3, to_page=3)
dst.save(os.path.join(PROJ, "pages", f"seite-{SEITE:03d}.pdf"), garbage=4, deflate=True)
dst.close()
if SRC != os.path.join(PROJ, "TREASURE B.pdf"):
    shutil.copy2(SRC, os.path.join(PROJ, "TREASURE B.pdf"))
doc.close()

# --- 2) alternative order codes on existing boards ----------------------
ALIAS = {
    "p037_9555PH250B10": "9555-PH25-08-10",
    "p037_9555PH260B10": "9555-PH26-08-10",
    "p037_9555PH280B10": "9555-PH28-08-10",
    "p037_9555PH290B10": "9555-PH29-08-10",
    "p038_9540PH250B10": "9540-PH25-08-10",
    "p038_9540PH260B10": "9540-PH26-08-10",
    "p038_9540PH280B10": "9540-PH28-08-10",
    "p038_9540PH290B10": "9540-PH29-08-10",
    "p064_9569GA210410": "9560-GA21-04-10",
}
for eid, code in ALIAS.items():
    e = by_id.get(eid)
    if e is None:
        print(f"!! Eintrag {eid} fehlt")
        continue
    if code not in e["codes"]:
        e["codes"].append(code)
        print(f"Code ergänzt: {code} -> {eid}")

note = "TREASURE B.pdf S.4 als Seite 310 (TR18-Poster) + Alt-Codes PH…-08/9560-GA21 aus Stücklisten (07/2026)"
if note not in kat.get("quelle", ""):
    kat["quelle"] = kat.get("quelle", "") + " | " + note
with open(kat_path, "w", encoding="utf-8") as f:
    json.dump(kat, f, ensure_ascii=False, indent=1)
print("katalog.json aktualisiert:", len(entries), "Einträge")
