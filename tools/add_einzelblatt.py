"""Replace a catalog page with a fresh single-page datasheet PDF (text layer).

The engers book pages 62 (MINERAL WALL/GARDENER) and 100 (ENJOY) exist as
regenerated one-pagers with identical board data. This script swaps in the
sharper version: print page + re-cropped board photos for the existing ids.
katalog.json data stays untouched except board_px200 and quelle.

Run with:  uv run --python 3.12 --with pymupdf --with pillow python tools/add_einzelblatt.py
"""
import fitz, io, json, os, re, shutil, sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"
DL = r"C:\Users\Mirsad.Karasalihovic\Downloads"
JOBS = [  # (source pdf, catalog page it replaces)
    (os.path.join(DL, "9555-9585-9557-MW21.pdf"), 62),
    (os.path.join(DL, "9555-9585-9557-EJ26.pdf"), 100),
]
CODE_RE = re.compile(r"^\d{4}-[A-Z0-9]{2,4}-\w{2}-\d{2}$")
PT2PX200 = 200.0 / 72.0

kat_path = os.path.join(PROJ, "katalog.json")
with open(kat_path, encoding="utf-8") as f:
    kat = json.load(f)
by_code = {}
for e in kat["einträge"]:
    for c in e["codes"]:
        by_code.setdefault((e["seite"], c), e)


def save_jpg(pix, path, maxdim, q):
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img.thumbnail((maxdim, maxdim), Image.LANCZOS)
    img.save(path, "JPEG", quality=q, optimize=True)


def board_panels(page):
    """The boards are big dark filled rects (vector) with tile photos inside."""
    panels = []
    for d in page.get_drawings():
        if d.get("fill") is None:
            continue
        r = d["rect"]
        if r.width > 100 and r.height > 100 and r.y0 > 70:
            panels.append(r)
    # drop rects fully inside another (photo frames etc.)
    return [r for r in panels if not any(o != r and o.contains(r) for o in panels)]


for src, seite in JOBS:
    doc = fitz.open(src)
    page = doc[0]
    # code positions on the sheet
    codes = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                t = s["text"].strip()
                if CODE_RE.match(t) and not t.startswith("91E"):
                    codes.append({"text": t, "x0": s["bbox"][0], "y0": s["bbox"][1]})
    print(f"Seite {seite}: {os.path.basename(src)} — {len(codes)} Codes: "
          + ", ".join(c["text"] for c in codes))

    # each code sits below its board panel: nearest panel above with x-overlap
    panels = board_panels(page)
    for c in codes:
        e = by_code.get((seite, c["text"]))
        if e is None:
            print(f"  !! {c['text']} nicht in katalog.json auf Seite {seite}")
            continue
        cand = [r for r in panels
                if r.y1 <= c["y0"] + 6 and r.x0 - 10 < c["x0"] < r.x1]
        if not cand:
            print(f"  !! kein Tafel-Panel für {c['text']}")
            continue
        r = max(cand, key=lambda r: r.y1) + fitz.Rect(-3, -3, 3, 3)
        r &= page.rect
        pix = page.get_pixmap(dpi=180, clip=r)
        save_jpg(pix, os.path.join(PROJ, "images", "large", e["id"] + ".jpg"), 1100, 80)
        save_jpg(pix, os.path.join(PROJ, "images", "thumb", e["id"] + ".jpg"), 420, 74)
        e["board_px200"] = [round(v * PT2PX200) for v in (r.x0, r.y0, r.x1, r.y1)]
        print(f"  ok {c['text']} -> {e['id']}.jpg  ({r.width:.0f}x{r.height:.0f}pt)")

    # replace print page and keep a copy of the source in the project
    dst = fitz.open()
    dst.insert_pdf(doc, from_page=0, to_page=0)
    dst.save(os.path.join(PROJ, "pages", f"seite-{seite:03d}.pdf"), garbage=4, deflate=True)
    dst.close()
    shutil.copy2(src, os.path.join(PROJ, os.path.basename(src)))
    doc.close()

note = "Seiten 62+100 ersetzt durch Einzelblatt-PDFs 9555-9585-9557-MW21/-EJ26 (Textlayer, 07/2026)"
if note not in kat.get("probleme", []) and note not in kat.get("quelle", ""):
    kat["quelle"] = kat.get("quelle", "") + " | " + note
with open(kat_path, "w", encoding="utf-8") as f:
    json.dump(kat, f, ensure_ascii=False, indent=1)
print("katalog.json aktualisiert")
