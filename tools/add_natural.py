"""Add NATURAL (komplett neue Serie) zum Katalog.

Quelle "Mustertafelpläne NATURALneu.pdf": Seite 1 hat echte Boardfotos im
Standard-Layout (wie MW21/EJ26 - Vektor-Panel + Codes/Art.-Zeilen), Seiten
2-4 sind reine Anordnungsplaene ohne eigene Codes und werden nicht als
Katalogeintraege erfasst.

Neue Seite laeuft nach LINEAR weiter (305 -> 306).

Run with:  uv run --python 3.12 --with pymupdf --with pillow python tools/add_natural.py
"""
import fitz, io, json, os, re, sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"
SEITE = 306
SERIE = "NATURAL"
PT2PX200 = 200.0 / 72.0

CODE_RE = re.compile(r"^\d{4}-[A-Z0-9]{2,4}-[A-Z0-9]{2,3}-\d{2}$")
ART_RE = re.compile(
    r"Art\.?\s*([A-Za-z]{2,4})\s*(\d{3,4})\s*"
    r"\(\s*([\d,]+)\s*(Stk|St)k?\.?\s*(Set)?\s*\)\s*"
    r"([A-Za-zäöüßÄÖÜ]*)\s*([\d,]+\s*[xX]\s*[\d,]+\s*ca?\.?\s*cm)?")


def spans_of(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                t = s["text"].strip()
                if not t:
                    continue
                out.append({"x0": s["bbox"][0], "y0": s["bbox"][1],
                            "x1": s["bbox"][2], "y1": s["bbox"][3],
                            "bold": "Bold" in s["font"], "size": s["size"], "text": t})
    return out


def board_panels(page):
    """Boards sind grosse dunkel gefuellte Rechtecke (Vektor) mit Fotos drin."""
    panels = []
    for d in page.get_drawings():
        if d.get("fill") is None:
            continue
        r = d["rect"]
        if r.width > 100 and r.height > 100 and r.y0 > 70:
            panels.append(r)
    return [r for r in panels if not any(o != r and o.contains(r) for o in panels)]


def save_jpg(pix, path, maxdim, q):
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img.thumbnail((maxdim, maxdim), Image.LANCZOS)
    img.save(path, "JPEG", quality=q, optimize=True)


doc = fitz.open(os.path.join(PROJ, "Mustertafeln NATURAL.pdf"))
page = doc[0]
spans = spans_of(page)
codes = [s for s in spans if CODE_RE.match(s["text"])]
panels = board_panels(page)

entries = []
for c in codes:
    cand = [r for r in panels if r.y1 <= c["y0"] + 6 and r.x0 - 10 < c["x0"] < r.x1]
    board = max(cand, key=lambda r: r.y1) if cand else None

    # Segment zwischen diesem Code und dem naechsten in derselben Spalte
    same_col = [o for o in codes if o is not c and abs(o["x0"] - c["x0"]) < 60]
    next_y = min([o["y0"] for o in same_col if o["y0"] > c["y0"]], default=900)
    bx0, bx1 = (board.x0 - 15, board.x1 + 15) if board else (c["x0"] - 15, c["x0"] + 260)
    body = [s for s in spans if c["y1"] - 4 < s["y0"] < next_y and bx0 <= s["x0"] <= bx1
            and not CODE_RE.match(s["text"])]

    tafel_groesse, label, notizen, artikel = None, None, [], []
    for s in sorted(body, key=lambda s: s["y0"]):
        t = s["text"]
        if re.match(r"^(GT\s*)?[\d,]+\s*[xX]\s*[\d,]+\s*cm$", t):
            tafel_groesse = re.sub(r"\s+", " ", t).strip()
            continue
        m = ART_RE.search(t)
        if m:
            prefix, num, stueck, _, _set, farbe, gr = m.groups()
            artikel.append({
                "artnr": f"{prefix.upper()} {num}", "stueck": stueck.replace(".", ","),
                "farbe": farbe or None,
                "groesse": re.sub(r"\s+", "", gr).replace("ca", "ca ").replace("cm", " cm") if gr else None,
            })
            continue
        if t.lower().startswith("poster"):
            label = re.sub(r"\s+", " ", t).strip()
        elif t.strip():
            notizen.append(re.sub(r"\s+", " ", t).strip())

    gt = bool(tafel_groesse and tafel_groesse.upper().startswith("GT"))
    entry = {
        "id": f"p{SEITE}_{c['text'].replace('-', '')}",
        "seite": SEITE, "serie": SERIE, "material": None,
        "codes": [c["text"]], "tafel_groesse": tafel_groesse, "gt": gt,
        "artikel": artikel, "label": label, "notizen": notizen, "display": False,
    }
    if board:
        r = board + fitz.Rect(-4, -4, 4, 4)
        r &= page.rect
        pix = page.get_pixmap(dpi=180, clip=r)
        os.makedirs(os.path.join(PROJ, "images", "large"), exist_ok=True)
        os.makedirs(os.path.join(PROJ, "images", "thumb"), exist_ok=True)
        save_jpg(pix, os.path.join(PROJ, "images", "large", entry["id"] + ".jpg"), 1100, 80)
        save_jpg(pix, os.path.join(PROJ, "images", "thumb", entry["id"] + ".jpg"), 420, 74)
        entry["board_px200"] = [round(v * PT2PX200) for v in (r.x0, r.y0, r.x1, r.y1)]
    else:
        entry["board_px200"] = None
        print(f"  !! kein Foto fuer {c['text']}")
    entries.append(entry)

print(f"NATURAL: {len(entries)} Tafeln geparst")
for e in entries:
    print(f'  {e["codes"]} {e["tafel_groesse"]} {len(e["artikel"])} Art. label={e["label"]!r}')

# ---- lossless Druckseite ----
dst = fitz.open()
dst.insert_pdf(doc, from_page=0, to_page=0)
dst.save(os.path.join(PROJ, "pages", f"seite-{SEITE:03d}.pdf"), garbage=4, deflate=True)
dst.close(); doc.close()
print(f"Druckseite seite-{SEITE:03d}.pdf geschrieben")

# ---- katalog.json ----
kat_path = os.path.join(PROJ, "katalog.json")
with open(kat_path, encoding="utf-8") as f:
    kat = json.load(f)
kat["einträge"] = [e for e in kat["einträge"] if e["serie"] != SERIE]
kat["einträge"].extend(entries)
kat["probleme"] = [p for p in kat.get("probleme", []) if not (isinstance(p, str) and p.startswith(SERIE))]
note = "Mustertafeln NATURAL.pdf (Seite {})".format(SEITE)
if note not in kat.get("quelle", ""):
    kat["quelle"] = kat.get("quelle", "") + " | " + note
with open(kat_path, "w", encoding="utf-8") as f:
    json.dump(kat, f, ensure_ascii=False, indent=1)
print("katalog.json:", len(kat["einträge"]), "einträge")

# ---- katalog.js neu bauen ----
js_path = os.path.join(PROJ, "katalog.js")
with open(js_path, encoding="utf-8") as f:
    js_old = f.read()
m = re.search(r"^window\.KATALOG_DATA = \[.*?\];\n(.*)$", js_old, re.S)
js_rest = m.group(1)

with open(os.path.join(PROJ, "index.html"), encoding="utf-8") as f:
    html = f.read()
covers = json.loads(re.search(r"const COVERS = (\{.*?\});", html).group(1))


def slug(s):
    s = (s or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


js_entries = []
for e in kat["einträge"]:
    has_img = os.path.exists(os.path.join(PROJ, "images", "thumb", e["id"] + ".jpg"))
    out = {
        "id": e["id"], "seite": e["seite"], "serie": e["serie"], "name": e.get("name"),
        "material": e["material"], "codes": e["codes"],
        "tafel_groesse": e["tafel_groesse"], "gt": e["gt"],
        "artikel": [{k: v for k, v in a.items() if v is not None} for a in e["artikel"]],
        "label": e["label"], "notizen": e["notizen"],
        "display": e["display"], "img": has_img,
    }
    sl = slug(e.get("serie"))
    if sl in covers:
        out["_covkey"] = sl
    js_entries.append(out)

with open(js_path, "w", encoding="utf-8") as f:
    f.write("window.KATALOG_DATA = " + json.dumps(js_entries, ensure_ascii=False, separators=(",", ":")) + ";\n\n")
    f.write(js_rest)
print("katalog.js:", len(js_entries), "entries,", sum(1 for d in js_entries if d["img"]), "with images")
