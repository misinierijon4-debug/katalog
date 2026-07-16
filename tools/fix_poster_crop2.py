"""Pass 2: expand crops for entries with a front Poster label.

Pass 1 guarded away pages where one dark fill covers several board regions.
Two sub-cases exist: (a) several ENTRIES share the SAME board (stacked code
variants) -> expansion is correct; (b) several DISTINCT boards sit on one
shared background panel (e.g. wood-plank pages) -> expansion would swallow
neighbouring tafeln. Pass 2 only treats entries whose label names a front
Poster, and only skips when the fill covers a genuinely DIFFERENT board.
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

doc = fitz.open(PDF)

def dark_fills(page):
    out = []
    for dr in page.get_drawings():
        fill = dr.get("fill")
        r = dr["rect"]
        if not fill or r.width < 60 or r.height < 60:
            continue
        if max(fill) - min(fill) > 0.08 or max(fill) > 0.6:
            continue
        out.append(fitz.Rect(r))
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
for e in data[ekey]:
    if e.get("marke") != "engers" or not e.get("board_px200"):
        continue
    if not (1 <= e["seite"] <= 261) or e["seite"] in SKIP_PAGES or e.get("rot90"):
        continue
    by_page.setdefault(e["seite"], []).append(e)

changed, skipped = [], []
for pno, es in sorted(by_page.items()):
    page = doc[pno - 1]
    fills = dark_fills(page)
    boards = {e["id"]: fitz.Rect(*[v * PX2PT for v in e["board_px200"]]) for e in es}
    for e in es:
        label = e.get("label") or ""
        if "Poster" not in label:
            continue
        b = boards[e["id"]]
        for f in fills:
            if area(f & b) < 0.5 * area(b):
                continue
            # skip if the fill also covers a genuinely different board
            distinct = [oid for oid, ob in boards.items()
                        if oid != e["id"]
                        and area(fitz.Rect(f) & ob) >= 0.7 * area(ob)
                        and area(ob & b) < 0.6 * min(area(ob), area(b))]
            if distinct:
                skipped.append((e["id"], pno, "Panel deckt fremde Tafel: " + distinct[0]))
                break
            new_px = [round(f.x0 / PX2PT), round(f.y0 / PX2PT),
                      round(f.x1 / PX2PT), round(f.y1 / PX2PT)]
            if all(abs(a2 - b2) <= 8 for a2, b2 in zip(new_px, e["board_px200"])):
                break
            clip = fitz.Rect(f.x0 - 4, f.y0 - 4, f.x1 + 4, f.y1 + 4) & page.rect
            pix = page.get_pixmap(dpi=180, clip=clip)
            save_jpg(pix, os.path.join(PROJ, "images", "large", e["id"] + ".jpg"), 1100, 80)
            save_jpg(pix, os.path.join(PROJ, "images", "thumb", e["id"] + ".jpg"), 420, 74)
            old = e["board_px200"]
            e["board_px200"] = new_px
            changed.append((e["id"], pno, old, new_px))
            break

with open(os.path.join(PROJ, "katalog.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

print("neu zugeschnitten:", len(changed))
for c in changed:
    print("  ", c[0], "S." + str(c[1]), c[2], "->", c[3])
print("uebersprungen:", len(skipped))
for s in skipped:
    print("  SKIP", s)
