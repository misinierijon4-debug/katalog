"""Add URBAN PULSE (Mutas Neuheiten 2026) boards to the katalog.

Source PDF has a real text layer (no OCR needed). Catalog pages continue
after the engers PDF: seite = 261 + pdf page number (262..281).

Does everything in one go:
  1. parse boards from text layer (codes, tafelgroesse, label, artikel, vermerke)
  2. crop board photos -> images/large|thumb/<id>.jpg, cover -> images/cover/urban-pulse.jpg
  3. lossless single pages -> pages/seite-262..281.pdf
  4. append entries to katalog.json (root, german keys)
  5. rebuild index.html from existing DATA/COVERS in index.html + index_template.html

Run with:  uv run --python 3.12 --with pymupdf --with pillow python tools/add_urban_pulse.py
"""
import fitz, io, json, os, re, shutil, sys
from PIL import Image

PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"
PDF_SRC = r"C:\Users\Mirsad.Karasalihovic\Downloads\20260115 Mutas_Urban Pulse_markierung_neuer code_relief.pdf"
PDF = os.path.join(PROJ, "Mustertafeln Urban Pulse Neuheiten 2026.pdf")
PAGE_OFFSET = 261          # engers katalog ends at seite 261
SERIE = "URBAN PULSE"
COVKEY = "urban-pulse"
COL_SPLIT = 270.0          # page is 540pt wide, 2 columns
PT2PX200 = 200.0 / 72.0

CODE_RE = re.compile(r"^\d{4}-[A-Z0-9]{2,4}-\w{2}-\d{2}$")
ARTNR_RE = re.compile(r"^\d{4}[A-Z]{2}\d{2}$")
SIZE_RE = re.compile(r"^(\d+)\s*x\s*(\d+)\s*cm$")
GROESSE_RE = re.compile(r"^\d+x\d+$")

if not os.path.exists(PDF):
    shutil.copy2(PDF_SRC, PDF)
doc = fitz.open(PDF)
probleme = []

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

def parse_page(pno):
    """pno = 0-based pdf page index; returns list of entry dicts (german keys)."""
    page = doc[pno]
    seite = PAGE_OFFSET + pno + 1
    spans = [s for s in spans_of(page) if s["y0"] < 735]  # drop footer page number

    # category header, e.g. "Bodentafeln | Handtafeln" (bold 14.5 next to URBAN PULSE)
    kat = None
    for s in spans:
        if s["y0"] < 65 and s["bold"] and abs(s["size"] - 14.5) < 1:
            kat = s["text"]
    if pno == 19 and not kat:
        kat = "Wandtafeln"  # page 20 has no header; display holds the 40x120 wall decors

    # board codes (bold, size 11-12)
    codes = [s for s in spans if s["bold"] and 10.5 < s["size"] < 12.6 and CODE_RE.match(s["text"])]
    codes.sort(key=lambda s: (0 if s["x0"] < COL_SPLIT else 1, s["y0"]))

    # group stacked codes (same column, small y gap) into one board
    groups = []
    for s in codes:
        col = 0 if s["x0"] < COL_SPLIT else 1
        if groups and groups[-1]["col"] == col and s["y0"] - groups[-1]["codes"][-1]["y1"] < 12:
            groups[-1]["codes"].append(s)
        else:
            groups.append({"col": col, "codes": [s]})

    entries = []
    for gi, g in enumerate(groups):
        col = g["col"]
        y_top = g["codes"][0]["y0"]
        nxt = [h for h in groups if h["col"] == col and h["codes"][0]["y0"] > y_top + 5]
        y_end = min((h["codes"][0]["y0"] for h in nxt), default=800) - 5
        seg = [s for s in spans if (0 if s["x0"] < COL_SPLIT else 1) == col
               and s["y0"] >= y_top - 3 and s["y0"] < y_end and s not in g["codes"]]

        tafel_groesse, name, label = None, None, None
        vermerk, descs, rows = [], [], {}
        for s in seg:
            t = s["text"]
            big = s["size"] > 10.3  # 11/12pt: tafelmass, uebersicht, code-beschreibung, vermerk
            if big or any(abs(s["y0"] - c["y0"]) < 5 for c in g["codes"]):
                if SIZE_RE.match(t):
                    tafel_groesse = re.sub(r"\s+", " ", t)
                elif "bersichtstafel" in t:
                    name = "Übersichtstafel"
                elif t.startswith("Vermerk") or "Schnitt" in t:
                    if "Schnitt" in t:
                        vermerk.append(t)
                elif any(abs(s["y0"] - c["y0"]) < 5 for c in g["codes"]):
                    descs.append(t)  # Rückwand / Bestückungssatz / Gradus
                continue
            key = round(s["y0"] / 5)  # 9/10pt: label + artikelzeilen
            rows.setdefault(key, []).append(s)

        artikel = []
        for key in sorted(rows):
            cells = sorted(rows[key], key=lambda s: s["x0"])
            texts = [c["text"] for c in cells]
            if len(texts) == 1 and texts[0] in ("Etikett", "Poster"):
                label = texts[0]
                continue
            art = next((t for t in texts if ARTNR_RE.match(t)), None)
            if art:
                i = texts.index(art)
                stueck = texts[i - 1] if i >= 1 and texts[i - 1].isdigit() else None
                groesse = next((t for t in texts[i + 1:] if GROESSE_RE.match(t)), None)
                farbe = " ".join(t for t in texts[i + 1:] if not GROESSE_RE.match(t)) or None
                artikel.append({"artnr": art, "stueck": stueck, "farbe": farbe, "groesse": groesse})
            else:
                probleme.append(f"Urban Pulse Seite {seite}: Zeile nicht zuordenbar: {' | '.join(texts)}")

        is_display = any("ckwand" in d or "Gradus" in d for d in descs)
        if descs and not name:
            name = " · ".join(descs)
        code0 = g["codes"][0]["text"].replace("-", "")
        notizen = [f"Vermerk: {v}" for v in vermerk] + ["Neuheiten-Katalog 2026"]
        entries.append({
            "id": f"p{seite}_{code0}",
            "seite": seite, "serie": SERIE,
            "material": kat,
            "codes": [c["text"] for c in g["codes"]],
            "tafel_groesse": tafel_groesse, "gt": False,
            "artikel": artikel, "label": label,
            "notizen": notizen, "display": is_display,
            "_page": pno,
            "_codebox": [min(c["x0"] for c in g["codes"]), min(c["y0"] for c in g["codes"]),
                         max(c["x1"] for c in g["codes"]), max(c["y1"] for c in g["codes"])],
        })
        if name:
            entries[-1]["name"] = name
    return entries

all_entries = []
for pno in range(1, doc.page_count):  # page 1 is the cover
    all_entries.extend(parse_page(pno))
print("parsed", len(all_entries), "boards")

# ---- crop board photos ----
# Images of one board form a contiguous cluster; the code block sits either
# below the board or (wide 120x182 boards, page 7/8) right of it.
os.makedirs(os.path.join(PROJ, "images", "large"), exist_ok=True)
os.makedirs(os.path.join(PROJ, "images", "thumb"), exist_ok=True)
os.makedirs(os.path.join(PROJ, "images", "cover"), exist_ok=True)

def save_jpg(pix, path, maxdim, q):
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img.thumbnail((maxdim, maxdim), Image.LANCZOS)
    img.save(path, "JPEG", quality=q, optimize=True)

def image_clusters(page):
    """Group non-logo images into contiguous board clusters (union-find, 6pt slack)."""
    boxes = [list(i["bbox"]) for i in page.get_image_info() if i["bbox"][1] >= 60]
    parent = list(range(len(boxes)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[0] - 6 < b[2] and b[0] - 6 < a[2] and a[1] - 6 < b[3] and b[1] - 6 < a[3]:
                parent[find(i)] = find(j)
    groups = {}
    for i, b in enumerate(boxes):
        groups.setdefault(find(i), []).append(b)
    return [[min(b[0] for b in g), min(b[1] for b in g),
             max(b[2] for b in g), max(b[3] for b in g)] for g in groups.values()]

by_page = {}
for e in all_entries:
    by_page.setdefault(e["_page"], []).append(e)

for pno, entries in by_page.items():
    page = doc[pno]
    assigned = {e["id"]: [] for e in entries}
    for c in image_clusters(page):
        best, bestd = None, 1e9
        for e in entries:
            gx0, gy0, gx1, gy1 = e["_codebox"]
            # code block directly below the board (text block is ~230pt wide)
            if gy0 >= c[3] - 6 and min(c[2], gx0 + 230) - max(c[0], gx0 - 10) > 20:
                d = gy0 - c[3]
                if d < bestd:
                    best, bestd = e, d
            # code block right of the board, starting near the board top
            if gx0 >= c[2] - 12 and c[1] - 10 <= gy0 <= c[3] + 6:
                d = gx0 - c[2]
                if d < bestd:
                    best, bestd = e, d
        if best is not None:
            assigned[best["id"]].append(c)
        else:
            probleme.append(f"Urban Pulse Seite {PAGE_OFFSET+pno+1}: Bild ohne Tafel bei {[round(v) for v in c]}")
    for e in entries:
        cs = assigned[e["id"]]
        if not cs:
            e["board_px200"] = None
            probleme.append(f"Urban Pulse Seite {e['seite']}: kein Tafelfoto gefunden ({e['codes'][0]})")
            continue
        r = fitz.Rect(min(c[0] for c in cs), min(c[1] for c in cs),
                      max(c[2] for c in cs), max(c[3] for c in cs)) + fitz.Rect(-4, -4, 4, 4)
        r &= page.rect
        pix = page.get_pixmap(dpi=180, clip=r)
        save_jpg(pix, os.path.join(PROJ, "images", "large", e["id"] + ".jpg"), 1100, 80)
        save_jpg(pix, os.path.join(PROJ, "images", "thumb", e["id"] + ".jpg"), 420, 74)
        e["board_px200"] = [round(v * PT2PX200) for v in (r.x0, r.y0, r.x1, r.y1)]

for e in all_entries:
    e.pop("_page"); e.pop("_codebox")
print("cropped", sum(1 for e in all_entries if e["board_px200"]), "boards")

# cover: biggest image on pdf page 1
p0 = doc[0]
big = max(p0.get_image_info(), key=lambda i: (i["bbox"][2] - i["bbox"][0]) * (i["bbox"][3] - i["bbox"][1]))
pix = p0.get_pixmap(dpi=110, clip=fitz.Rect(*big["bbox"]) & p0.rect)
save_jpg(pix, os.path.join(PROJ, "images", "cover", COVKEY + ".jpg"), 900, 74)
print("cover written")

# ---- lossless print pages ----
outdir = os.path.join(PROJ, "pages")
for i in range(doc.page_count):
    dst = fitz.open()
    dst.insert_pdf(doc, from_page=i, to_page=i)
    dst.save(os.path.join(outdir, f"seite-{PAGE_OFFSET + i + 1:03d}.pdf"), garbage=4, deflate=True)
    dst.close()
print("print pages seite-262..281 written")

# ---- katalog.json (root, german keys) ----
kat_path = os.path.join(PROJ, "katalog.json")
with open(kat_path, encoding="utf-8") as f:
    kat = json.load(f)
kat["einträge"] = [e for e in kat["einträge"] if not (e["seite"] > PAGE_OFFSET and e["serie"] == SERIE)]
kat["einträge"].extend(all_entries)
kat["probleme"] = [p for p in kat.get("probleme", [])
                   if not (isinstance(p, str) and p.startswith("Urban Pulse"))] + probleme
if isinstance(kat.get("quelle"), str) and "Urban Pulse" not in kat["quelle"]:
    kat["quelle"] += " + Mustertafeln Urban Pulse Neuheiten 2026.pdf (Seiten 262-281)"
with open(kat_path, "w", encoding="utf-8") as f:
    json.dump(kat, f, ensure_ascii=False, indent=1)
print("katalog.json:", len(kat["einträge"]), "einträge")

# ---- rebuild index.html: existing DATA/COVERS + new entries ----
with open(os.path.join(PROJ, "index.html"), encoding="utf-8") as f:
    html_old = f.read()
m = re.search(r"const DATA = (\[.*?\]);\nconst COVERS = (\{.*?\});\n", html_old, re.S)
data = json.loads(m.group(1))
covers = json.loads(m.group(2))
data = [d for d in data if d.get("serie") != SERIE]
for e in all_entries:
    has_img = os.path.exists(os.path.join(PROJ, "images", "thumb", e["id"] + ".jpg"))
    data.append({
        "id": e["id"], "seite": e["seite"], "serie": e["serie"], "name": e.get("name"),
        "material": e["material"], "codes": e["codes"],
        "tafel_groesse": e["tafel_groesse"], "gt": e["gt"],
        "artikel": [{k: v for k, v in a.items() if v is not None} for a in e["artikel"]],
        "label": e["label"], "notizen": e["notizen"],
        "display": e["display"], "img": has_img, "_covkey": COVKEY,
    })
covers[COVKEY] = SERIE

with open(os.path.join(PROJ, "index_template.html"), encoding="utf-8") as f:
    html = f.read()
html = html.replace("/*__DATA__*/[]", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
html = html.replace("/*__COVERS__*/{}", json.dumps(covers, ensure_ascii=False, separators=(",", ":")))
with open(os.path.join(PROJ, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("index.html:", len(data), "entries,", sum(1 for d in data if d["img"]), "with images")

for e in all_entries:
    print(f'  S.{e["seite"]} {"/".join(e["codes"])} | {e.get("material")} | {e.get("name","")} | '
          f'{e["tafel_groesse"] or "-"} | {e["label"] or "-"} | {len(e["artikel"])} Art. | '
          f'{"IMG" if e["board_px200"] else "KEIN BILD"}'
          + (" | DISPLAY" if e["display"] else "")
          + ("".join(" | " + n for n in e["notizen"] if n.startswith("Vermerk")) or ""))
if probleme:
    print("PROBLEME:")
    for p in probleme:
        print(" -", p)
