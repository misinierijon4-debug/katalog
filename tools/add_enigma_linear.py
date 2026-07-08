"""Add ENIGMA and LINEAR (komplett neue Serien) zum Katalog.

Beide Quell-PDFs haben einen echten Textlayer, aber ein anderes Layout als
das engers.pdf-Buch: pro Seite ein Wand-/Bodendekor in mehreren Formaten,
Codes stehen ENTWEDER direkt über dem zugehörigen Foto (Wandtafeln) ODER
rechts neben einem Fotopaar (Bodentafeln mit "gestrichener" Vergleichsvariante,
an der roten Diagonale erkennbar). Es gibt keine einheitliche 2-Spalten-
Aufteilung wie bei Urban Pulse, daher wird hier über Bild-Nähe zugeordnet
statt über eine feste COL_SPLIT-Grenze.

Neue Seiten laufen ab 282 weiter (Urban Pulse endete bei 281).

Run with:  uv run --python 3.12 --with pymupdf --with pillow python tools/add_enigma_linear.py
"""
import fitz, io, json, os, re, sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"
PAGE_OFFSET = 281  # Urban Pulse endet bei 281
PT2PX200 = 200.0 / 72.0

CODE_RE = re.compile(r"^\d{4}-[A-Z0-9]{2,4}-[A-Z0-9]{2,3}-\d{2}$")
SIZE_RE = re.compile(r"^(GT\s*)?(?:[\d,]+\s*[xX]\s*[\d,]+\s*/?\s*)+(cm)?$")
ART_RE = re.compile(
    r"Art\.?\s*([A-Za-z]{2,4})\s*(\d{3,4})\s*"
    r"\(\s*([\d,]+)\s*(Stk|St)k?\.?\s*(Set)?\s*\)\s*"
    r"([A-Za-zäöüßÄÖÜ]*)\s*([\d,]+\s*[xX]\s*[\d,]+\s*cm)?")

JOBS = [
    {"pdf": "Mustertafeln ENIGMA 2019.pdf", "serie": "ENIGMA", "quelle_note": "Mustertafeln ENIGMA 2019.pdf"},
    {"pdf": "Mustertafeln LINEAR.pdf", "serie": "LINEAR", "quelle_note": "Mustertafeln LINEAR.pdf"},
]

probleme = []
all_entries = []


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


def group_codes(code_spans):
    """Stapelt Codes derselben Spalte (kleiner x/y-Abstand) zu einer Tafel."""
    groups = []
    for s in sorted(code_spans, key=lambda s: (round(s["x0"] / 20), s["y0"])):
        placed = False
        for g in groups:
            last = g[-1]
            if abs(s["x0"] - last["x0"]) < 20 and 0 <= s["y0"] - last["y1"] < 16:
                g.append(s); placed = True; break
        if not placed:
            groups.append([s])
    return groups


def match_images(group_box, images):
    """Drei Layout-Varianten kommen im Dokument vor: Code über dem Foto,
    Code unter dem Foto, oder Code rechts neben einem Fotopaar (Bodentafeln
    mit gestrichener Vergleichsvariante). "beside" nur als Fallback nutzen —
    sonst reisst ein knapp daneben liegendes Bild fälschlich mit ein, wenn
    der Code eigentlich direkt über/unter seinem eigenen Foto steht."""
    gx0, gy0, gx1, gy1 = group_box
    direct = []
    for im in images:
        ix0, iy0, ix1, iy1 = im
        code_above_image = 0 <= iy0 - gy1 < 30 and abs(ix0 - gx0) < 40
        code_below_image = 0 <= gy0 - iy1 < 35 and abs(ix0 - gx0) < 40
        if code_above_image or code_below_image:
            direct.append(im)
    if direct:
        return direct
    return [im for im in images if abs(im[1] - gy0) < 20 and im[2] <= gx0 + 10]


def normalize_size(t):
    return t if t.rstrip().lower().endswith("cm") else t.rstrip() + " cm"


def find_size(image_union, all_spans, page_texts_used):
    ux0, uy0, ux1, uy1 = image_union
    cands = [s for s in all_spans if SIZE_RE.match(s["text"]) and 0 <= s["y0"] - uy1 < 20]
    aligned = [s for s in cands if abs(s["x0"] - ux0) < 40]
    if aligned:
        return normalize_size(aligned[0]["text"])
    band = [s for s in all_spans if SIZE_RE.match(s["text"]) and uy1 <= s["y0"] < uy1 + 40]
    if len(band) == 1:
        return normalize_size(band[0]["text"])
    return None


def save_jpg(pix, path, maxdim, q):
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img.thumbnail((maxdim, maxdim), Image.LANCZOS)
    img.save(path, "JPEG", quality=q, optimize=True)


os.makedirs(os.path.join(PROJ, "images", "large"), exist_ok=True)
os.makedirs(os.path.join(PROJ, "images", "thumb"), exist_ok=True)

seite_counter = PAGE_OFFSET
pdf_page_map = []  # (globale_seite, doc, pno) fuer den Druckseiten-Export

for job in JOBS:
    doc = fitz.open(os.path.join(PROJ, job["pdf"]))
    serie = job["serie"]
    for pno in range(doc.page_count):
        seite_counter += 1
        page = doc[pno]
        pdf_page_map.append((seite_counter, job["pdf"], pno))
        all_spans = spans_of(page)
        images = [[i["bbox"][0], i["bbox"][1], i["bbox"][2], i["bbox"][3]] for i in page.get_image_info()]

        # Kopfzeile: "Mustertafel ..." (mehrzeilig), "Größen ...", "Artikel ..." (mehrzeilig)
        # Codes koennen schon ab y~190 beginnen, also explizit ausschliessen,
        # sonst rutscht ein Board-Code in die Artikel-Kopfzeile.
        header_lines = sorted((s for s in all_spans if s["y0"] < 240 and not (s["bold"] and s["size"] > 20)
                               and not CODE_RE.match(s["text"])),
                              key=lambda s: s["y0"])
        section = None
        mustertafel_lines, artikel_lines = [], []
        for s in header_lines:
            if s["text"].startswith("Mustertafel"):
                section = "name"
            elif s["text"].startswith("Größen"):
                section = "groessen"
            elif s["text"].startswith("Artikel"):
                section = "artikel"
            if section == "name":
                mustertafel_lines.append(s["text"])
            elif section == "artikel":
                artikel_lines.append(s["text"])
        name = " ".join(mustertafel_lines) or None
        artikel_hinweis = " ".join(artikel_lines) or None

        code_spans = [s for s in all_spans if CODE_RE.match(s["text"])]
        if not code_spans:
            continue
        groups = group_codes(code_spans)

        for g in groups:
            gx0 = min(s["x0"] for s in g); gy0 = min(s["y0"] for s in g)
            gx1 = max(s["x1"] for s in g); gy1 = max(s["y1"] for s in g)
            codes = [s["text"] for s in g]
            imgs = match_images((gx0, gy0, gx1, gy1), images)
            if not imgs:
                probleme.append(f"{serie} Seite {seite_counter} (PDF-S.{pno+1}): kein Foto für {codes}")
                board_px200 = None
                image_union = None
            else:
                ux0 = min(i[0] for i in imgs); uy0 = min(i[1] for i in imgs)
                ux1 = max(i[2] for i in imgs); uy1 = max(i[3] for i in imgs)
                image_union = (ux0, uy0, ux1, uy1)

            groesse = find_size(image_union, all_spans, None) if image_union else None
            gt = bool(groesse and groesse.upper().startswith("GT"))

            # Art.-Zeilen + Poster/Notiz-Zeilen im Bereich zwischen dieser Gruppe
            # und der naechsten Gruppe derselben Spalte (bzw. Seitenende), aber
            # nur innerhalb der Bildbreite dieser Tafel (sonst blutet die Spalte
            # bei eng benachbarten Bildern in die Nachbarspalte hinein).
            if image_union:
                bx0, bx1 = image_union[0] - 15, image_union[2] + 15
            else:
                bx0, bx1 = gx0 - 15, gx0 + 260
            same_col = [o for o in groups if o is not g and abs(min(s["x0"] for s in o) - gx0) < 60]
            next_y = min([min(s["y0"] for s in o) for o in same_col
                          if min(s["y0"] for s in o) > gy1], default=900)
            body = [s for s in all_spans if gy1 - 4 < s["y0"] < next_y
                    and bx0 <= s["x0"] <= bx1 and not CODE_RE.match(s["text"])]
            artikel = []
            label = None
            notizen = []
            body_text_by_y = {}
            for s in body:
                body_text_by_y.setdefault(round(s["y0"]), []).append(s)
            body_lines = []
            for y in sorted(body_text_by_y):
                cells = sorted(body_text_by_y[y], key=lambda s: s["x0"])
                body_lines.append(" ".join(c["text"] for c in cells))
            for line in body_lines:
                if SIZE_RE.match(line):
                    continue
                m = ART_RE.search(line)
                if m:
                    prefix, num, stueck, _, _set, farbe, gr = m.groups()
                    artikel.append({
                        "artnr": f"{prefix.upper()} {num}",
                        "stueck": stueck.replace(".", ","),
                        "farbe": farbe or None,
                        "groesse": gr.replace(" ", "").replace("cm", " cm") if gr else None,
                    })
                elif line.lower().startswith("poster"):
                    label = line
                elif line.strip():
                    notizen.append(line.strip())

            if artikel_hinweis and not artikel:
                notizen.append(artikel_hinweis)

            code0 = codes[0].replace("-", "")
            entry = {
                "id": f"p{seite_counter}_{code0}",
                "seite": seite_counter, "serie": serie,
                "material": None,
                "codes": codes,
                "tafel_groesse": groesse, "gt": gt,
                "artikel": artikel, "label": label,
                "notizen": notizen, "display": False,
            }
            if name:
                entry["name"] = name
            if image_union:
                r = fitz.Rect(*image_union) + fitz.Rect(-4, -4, 4, 4)
                r &= page.rect
                pix = page.get_pixmap(dpi=180, clip=r)
                save_jpg(pix, os.path.join(PROJ, "images", "large", entry["id"] + ".jpg"), 1100, 80)
                save_jpg(pix, os.path.join(PROJ, "images", "thumb", entry["id"] + ".jpg"), 420, 74)
                entry["board_px200"] = [round(v * PT2PX200) for v in (r.x0, r.y0, r.x1, r.y1)]
            else:
                entry["board_px200"] = None
            all_entries.append(entry)
    doc.close()

print("geparst:", len(all_entries), "Tafeln")
for e in all_entries:
    print(f'  S.{e["seite"]} {e["serie"]:8s} {"/".join(e["codes"]):40s} {e["tafel_groesse"] or "-":20s} '
          f'{len(e["artikel"])} Art. {"IMG" if e["board_px200"] else "KEIN FOTO"}')
if probleme:
    print("\nPROBLEME:")
    for p in probleme:
        print(" -", p)

# ---- lossless Druckseiten ----
outdir = os.path.join(PROJ, "pages")
for seite, pdfname, pno in pdf_page_map:
    doc = fitz.open(os.path.join(PROJ, pdfname))
    dst = fitz.open()
    dst.insert_pdf(doc, from_page=pno, to_page=pno)
    dst.save(os.path.join(outdir, f"seite-{seite:03d}.pdf"), garbage=4, deflate=True)
    dst.close(); doc.close()
print("\nDruckseiten seite-{}..{} geschrieben".format(PAGE_OFFSET + 1, seite_counter))

# ---- katalog.json ----
kat_path = os.path.join(PROJ, "katalog.json")
with open(kat_path, encoding="utf-8") as f:
    kat = json.load(f)
neue_serien = {j["serie"] for j in JOBS}
kat["einträge"] = [e for e in kat["einträge"] if e["serie"] not in neue_serien]
kat["einträge"].extend(all_entries)
kat["probleme"] = [p for p in kat.get("probleme", [])
                   if not (isinstance(p, str) and any(p.startswith(s) for s in neue_serien))] + probleme
note = " + ".join(j["quelle_note"] for j in JOBS) + " (Seiten {}-{})".format(PAGE_OFFSET + 1, seite_counter)
if note not in kat.get("quelle", ""):
    kat["quelle"] = kat.get("quelle", "") + " | " + note
with open(kat_path, "w", encoding="utf-8") as f:
    json.dump(kat, f, ensure_ascii=False, indent=1)
print("katalog.json:", len(kat["einträge"]), "einträge")

# ---- katalog.js neu bauen ----
# Die Live-App laedt window.KATALOG_DATA aus katalog.js (nicht mehr inline in
# index.html). katalog.js wird komplett aus katalog.json neu erzeugt, damit
# beide Speicher nie auseinanderlaufen; die Lookup-Funktion am Dateiende
# bleibt unveraendert erhalten.
js_path = os.path.join(PROJ, "katalog.js")
with open(js_path, encoding="utf-8") as f:
    js_old = f.read()
m = re.search(r"^window\.KATALOG_DATA = \[.*?\];\n(.*)$", js_old, re.S)
js_rest = m.group(1)  # findeKatalogEintraege bleibt unveraendert

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
