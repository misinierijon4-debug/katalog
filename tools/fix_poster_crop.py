"""Fix cropped-off poster areas on engers boards.

The original board detection preferred embedded photo images, so boards whose
upper part is a plain dark area (poster placeholder) were cropped too tight —
the poster zone was cut off in images/large + images/thumb (visible in the
katalog detail view and on Lagerkarte print sheets).

Fix: re-read the dark vector fill rects (the physical board panels) straight
from the engers PDF and, where such a panel cleanly contains an entry's board
region, expand board_px200 to the full panel and re-crop both images.

Scope: engers entries, seite 1..261 (main PDF), except pages 62/100 (those
pages were replaced by Einzelblatt-PDFs; handled separately if needed).
"""
import fitz, io, json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PDF = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln engers.pdf"
PX2PT = 72.0 / 200.0
SKIP_PAGES = {62, 100}

with open(os.path.join(PROJ, "katalog.json"), encoding="utf-8") as f:
    data = json.load(f)
ekey = next(k for k in data if "eintr" in k)
entries = data[ekey]

doc = fitz.open(PDF)

def dark_fills(page):
    """Large uniformly-dark filled rects = board panels."""
    out = []
    for dr in page.get_drawings():
        fill = dr.get("fill")
        r = dr["rect"]
        if not fill or r.width < 60 or r.height < 60:
            continue
        if max(fill) - min(fill) > 0.08:  # not gray
            continue
        if max(fill) > 0.6:  # too light (white tile placeholders, page bg)
            continue
        out.append(fitz.Rect(r))
    # merge overlapping/adjacent panels drawn in pieces
    merged = True
    while merged:
        merged = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a, b = out[i], out[j]
                if fitz.Rect(a.x0 - 2, a.y0 - 2, a.x1 + 2, a.y1 + 2).intersects(b):
                    out[i] = a | b
                    out.pop(j)
                    merged = True
                    break
            if merged:
                break
    return out

def save_jpg(pix, path, maxdim, q):
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img.thumbnail((maxdim, maxdim), Image.LANCZOS)
    img.save(path, "JPEG", quality=q, optimize=True)

def area(r):
    return max(0.0, r.width) * max(0.0, r.height)

by_page = {}
for e in entries:
    if e.get("marke") != "engers" or not e.get("board_px200"):
        continue
    if not (1 <= e["seite"] <= 261) or e["seite"] in SKIP_PAGES:
        continue
    if e.get("rot90"):
        continue  # rotated specials: leave untouched
    by_page.setdefault(e["seite"], []).append(e)

changed, nofill, guarded = [], [], []
for pno, es in sorted(by_page.items()):
    page = doc[pno - 1]
    fills = dark_fills(page)
    boards = {e["id"]: fitz.Rect(*[v * PX2PT for v in e["board_px200"]]) for e in es}
    for e in es:
        b = boards[e["id"]]
        cand = None
        for f in fills:
            inter = fitz.Rect(f) & b
            if area(inter) < 0.7 * area(b):
                continue
            if area(f) > 3.5 * area(b):
                guarded.append((e["id"], "fill zu gross"))
                cand = None
                break
            others = [oid for oid, ob in boards.items()
                      if oid != e["id"] and area(fitz.Rect(f) & ob) >= 0.7 * area(ob)]
            if others:
                guarded.append((e["id"], "fill deckt mehrere Tafeln"))
                cand = None
                break
            cand = f
            break
        if cand is None:
            if not any(g[0] == e["id"] for g in guarded):
                nofill.append(e["id"])
            continue
        new_px = [round(cand.x0 / PX2PT), round(cand.y0 / PX2PT),
                  round(cand.x1 / PX2PT), round(cand.y1 / PX2PT)]
        old = e["board_px200"]
        if all(abs(a - b2) <= 8 for a, b2 in zip(new_px, old)):
            continue  # crop was already (near) the full panel
        clip = fitz.Rect(cand.x0 - 4, cand.y0 - 4, cand.x1 + 4, cand.y1 + 4) & page.rect
        pix = page.get_pixmap(dpi=180, clip=clip)
        save_jpg(pix, os.path.join(PROJ, "images", "large", e["id"] + ".jpg"), 1100, 80)
        save_jpg(pix, os.path.join(PROJ, "images", "thumb", e["id"] + ".jpg"), 420, 74)
        e["board_px200"] = new_px
        changed.append((e["id"], old, new_px))

with open(os.path.join(PROJ, "katalog.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

print("geprueft:", sum(len(v) for v in by_page.values()))
print("neu zugeschnitten:", len(changed))
print("kein dunkles Panel gefunden:", len(nofill))
print("uebersprungen (Schutz):", len(guarded))
for cid, old, new in changed[:20]:
    print("  ", cid, old, "->", new)
if guarded:
    for g in guarded[:10]:
        print("  GUARD", g)
