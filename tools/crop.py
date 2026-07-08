"""Crop board photos from PDF pages based on katalog.json board regions.

Writes images/large/<id>.jpg (max 1100px) and images/thumb/<id>.jpg (max 420px).
Also renders series cover pages to images/cover/<serie>.jpg.
"""
import fitz, io, json, os, re
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln engers.pdf"
PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"
PX2PT = 72.0 / 200.0

with open(os.path.join(HERE, "katalog.json"), encoding="utf-8") as f:
    data = json.load(f)

doc = fitz.open(PDF)
os.makedirs(os.path.join(PROJ, "images", "large"), exist_ok=True)
os.makedirs(os.path.join(PROJ, "images", "thumb"), exist_ok=True)
os.makedirs(os.path.join(PROJ, "images", "cover"), exist_ok=True)

def save_jpg(pix, path, maxdim, q=78, rot90=False):
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    if rot90:
        img = img.transpose(Image.ROTATE_270)
    img.thumbnail((maxdim, maxdim), Image.LANCZOS)
    img.save(path, "JPEG", quality=q, optimize=True)

import sys
only = sys.argv[1] if len(sys.argv) > 1 else None
n = 0
for e in data["entries"]:
    if not e["board_px200"]:
        continue
    if only and only not in e["id"]:
        continue
    page = doc[e["seite"] - 1]
    b = e["board_px200"]
    pad = 6 / PX2PT * PX2PT  # 6pt padding
    clip = fitz.Rect(b[0] * PX2PT - 4, b[1] * PX2PT - 4, b[2] * PX2PT + 4, b[3] * PX2PT + 4)
    clip &= page.rect
    pix = page.get_pixmap(dpi=180, clip=clip)
    rot = bool(e.get("rot90"))
    save_jpg(pix, os.path.join(PROJ, "images", "large", e["id"] + ".jpg"), 1100, 80, rot)
    save_jpg(pix, os.path.join(PROJ, "images", "thumb", e["id"] + ".jpg"), 420, 74, rot)
    n += 1
print("cropped", n, "boards")

def slug(s):
    s = s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

covers = {}
for c in data["covers"]:
    sl = slug(c["serie"])
    if sl in covers:
        continue
    covers[sl] = c
    page = doc[c["page"] - 1]
    pix = page.get_pixmap(dpi=110, clip=fitz.Rect(*c["rect"]) & page.rect)
    save_jpg(pix, os.path.join(PROJ, "images", "cover", sl + ".jpg"), 900, 74)
print("covers", len(covers))
with open(os.path.join(HERE, "covers.json"), "w", encoding="utf-8") as f:
    json.dump({k: v["serie"] for k, v in covers.items()}, f, ensure_ascii=False)
