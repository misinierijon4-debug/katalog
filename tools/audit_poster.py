"""Audit: entries whose label names a Poster should show the dark poster
panel at the top of their board image. Flags images whose top strip is light
(= poster area probably cropped off)."""
import json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)

with open(os.path.join(PROJ, "katalog.json"), encoding="utf-8") as f:
    data = json.load(f)
ekey = next(k for k in data if "eintr" in k)

def top_strip_lum(path):
    img = Image.open(path).convert("L")
    w, h = img.size
    strip = img.crop((int(w * 0.15), int(h * 0.02), int(w * 0.85), int(h * 0.06)))
    px = list(strip.getdata())
    return sum(px) / len(px)

flagged, ok, missing = [], 0, 0
for e in data[ekey]:
    label = e.get("label") or ""
    if not label.startswith("Poster"):
        continue
    p = os.path.join(PROJ, "images", "large", e["id"] + ".jpg")
    if not os.path.exists(p):
        missing += 1
        continue
    lum = top_strip_lum(p)
    if lum > 120:  # top of image is light -> poster panel probably cut off
        flagged.append((e["id"], e.get("marke"), e["seite"], round(lum)))
    else:
        ok += 1

print("Poster-Eintraege mit Bild:", ok + len(flagged), "| ok:", ok,
      "| verdaechtig:", len(flagged), "| ohne Bild:", missing)
for f in flagged:
    print("  ", f)
