"""Report engers entries (main PDF) whose dark panel still extends notably
above the stored crop — i.e. poster area possibly still cut off after the fix."""
import fitz, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PDF = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln engers.pdf"
PX2PT = 72.0 / 200.0

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
    return out

def area(r):
    return max(0.0, r.width) * max(0.0, r.height)

rest = []
pages = {}
for e in data[ekey]:
    if e.get("marke") != "engers" or not e.get("board_px200"):
        continue
    if not (1 <= e["seite"] <= 261) or e["seite"] in (62, 100) or e.get("rot90"):
        continue
    pages.setdefault(e["seite"], []).append(e)

for pno, es in sorted(pages.items()):
    fills = dark_fills(doc[pno - 1])
    for e in es:
        b = fitz.Rect(*[v * PX2PT for v in e["board_px200"]])
        for f in fills:
            if area(f & b) < 0.5 * area(b):
                continue
            above = b.y0 - f.y0
            if above > 8:  # panel reaches >8pt above the crop
                rest.append((e["id"], e["seite"], round(above), e.get("label")))
            break

print("noch verdaechtig:", len(rest))
for r in rest:
    print("  ", r)
