"""Parse ocr_raw.json into structured katalog.json (v2).

OCR boxes: 200dpi pixels. Image/vector rects: PDF points. pt = px * 72/200.
"""
import json, os, re, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "ocr_raw.json")
OUT = os.path.join(HERE, "katalog.json")
PX2PT = 72.0 / 200.0
PAGE_W_PX = 595.32 / PX2PT  # ~1654

SPECIAL_PAGES = set(range(216, 226)) | set(range(251, 258)) | {260, 261}

FULLWIDTH = {"（": "(", "）": ")", "，": ",", "．": ".", "：": ":"}
WORDFIX = {
    "silberweib": "silberweiß", "silberweiB": "silberweiß", "silberweis": "silberweiß",
    "edelweib": "edelweiß", "edelweiB": "edelweiß", "weib": "weiß", "weiB": "weiß",
    "grun": "grün", "moosgrun": "moosgrün", "dunkelgrun": "dunkelgrün",
    "Ruckseite": "Rückseite", "ruckseitig": "rückseitig", "ruickseitig": "rückseitig",
    "Ruckseitig": "Rückseitig", "Bestuckung": "Bestückung", "Stuck": "Stück",
    "Tafelchen": "Täfelchen", "Serienubersichten": "Serienübersichten", "MOBEL": "MÖBEL",
    "Grun": "Grün", "Flache": "Fläche", "moosgrin": "moosgrün", "edelweis": "edelweiß",
    "WilderVerband": "Wilder Verband", "Verfugung": "Verfugung",
}

RE_TAFEL_CODE = re.compile(r"^(\d{4})-([A-Z0-9]{3,5})-([A-Z0-9]{2,3})-(\d{2})$")
RE_LABEL_CODE = re.compile(r"(9\d[A-Z0-9]\d)-([A-Z0-9]{3,5})-(\d{2})-(\d{2})")
RE_SIZE_PREFIX = re.compile(
    r"^(GT)?((\d{1,3}(,\d{1,2})?x\d{1,3}(,\d{1,2})?)(cm)?/?)+(cm)?(/Sonderanfertigung)?")
RE_ART_G = re.compile(
    r"Art\.?\s*([A-Za-z][A-Za-z01]{1,3})\s*(\d{4})\s*"
    r"[^()]{0,4}?\(\s*(je\s+)?([\d,\.]+)\s*(?:St|Stk)k?\.?\s*(Set)?\.?\s*\)+\s*"
    r"((?:(?!Art\.)[^()])*?)\s*"
    r"(\d{1,3}(?:,\d)?\s*x\s*\d{1,3}(?:,\d)?\s*cm)", re.U)
RE_ART_SHORT = re.compile(
    r"^Art\.?\s*([A-Za-z][A-Za-z01]{1,3})\s*(\d{3,4})\s+([A-Za-zäöüßÄÖÜ /\-]{3,40})$")
RE_ART_START = re.compile(r"(?:^|\s)(?:\d\.\s*)?Art\.?\s*[A-Za-z0-9]{2,4}\s*\d{3,4}")

def norm_text(t):
    for k, v in FULLWIDTH.items():
        t = t.replace(k, v)
    t = t.replace("β", "ß")
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"(Poster|Etikett)(9\d)", r"\1 \2", t)
    t = re.sub(r"\s+", " ", t).strip()
    return " ".join(WORDFIX.get(w, w) for w in t.split(" "))

PREFIXFIX = {"BRL": "BRI"}  # verified against PDF p.100: "Art. BRI 3190"

def fix_farbe(f):
    """Normalize OCR-mangled German color names (model lacks umlauts/ß)."""
    if not f:
        return f
    f = re.sub(r"^[a-z]\s+(?=[a-zäöüA-Z])", "", f.strip())  # stray leading glyph
    parts = re.split(r"([\s\-]+)", f)
    out = []
    for w in parts:
        if not w or re.match(r"^[\s\-]+$", w):
            out.append(w); continue
        t = w
        if re.match(r"^[A-Za-zäöüßÄÖÜ0]+$", t) and len(re.findall(r"[A-Za-z]", t)) >= 3:
            t = t.replace("0", "o")
        lw = t.lower().replace("ooo", "oo")
        if lw != t.lower():
            t = lw
        m = re.match(r"^(gletscher|kalk|natur|silber|kristall|edel)?wei[a-zß]*$", lw)
        if m:
            t = (m.group(1) or "") + "weiß"
        m2 = re.match(r"^(moos|atoll|dunkel)?gr[uüio]+n$", lw)
        if m2:
            t = (m2.group(1) or "") + "grün"
        if lw in ("glanzend", "glinzend", "glnzend"):
            t = "glänzend"
        if lw == "antharzit":
            t = "anthrazit"
        out.append(t)
    return "".join(out)

def fix_alpha_prefix(p):
    if p and p[0] == "2":  # mosaic articles like "2ARI"
        return "2" + p[1:].replace("0", "O").replace("1", "I")
    return p.replace("0", "O").replace("1", "I")

def fix_label_code(t):
    def repl(m):
        g2 = m.group(2)
        g2 = g2[:-1].replace("0", "O").replace("1", "I") + g2[-1]
        return f"{m.group(1)}-{g2}-{m.group(3)}-{m.group(4)}"
    return RE_LABEL_CODE.sub(repl, t)

def px_line(l):
    return {**l, "text": norm_text(l["text"])}

def find_anchors(code_rows_x):
    anchors = []
    for x in sorted(code_rows_x):
        if not anchors or x - anchors[-1] > 100:
            anchors.append(x)
    return anchors

def anchor_of(x0, anchors):
    best = None
    for a in anchors:
        if x0 >= a - 45:
            best = a
    return best if best is not None else (anchors[0] if anchors else 0)

def merge_rows(lines, anchors, ytol=14):
    groups = {}
    for l in lines:
        a = anchor_of(l["x0"], anchors)
        groups.setdefault(a, []).append(l)
    out = []
    for a, ls in groups.items():
        ls = sorted(ls, key=lambda l: (l["y0"], l["x0"]))
        used = [False] * len(ls)
        for i in range(len(ls)):
            if used[i]:
                continue
            row = [ls[i]]; used[i] = True
            yc = (ls[i]["y0"] + ls[i]["y1"]) / 2
            for j in range(i + 1, len(ls)):
                if used[j]:
                    continue
                yc2 = (ls[j]["y0"] + ls[j]["y1"]) / 2
                if abs(yc2 - yc) <= ytol:
                    row.append(ls[j]); used[j] = True
            row.sort(key=lambda l: l["x0"])
            out.append({
                "text": " ".join(r["text"] for r in row),
                "x0": min(r["x0"] for r in row), "y0": min(r["y0"] for r in row),
                "x1": max(r["x1"] for r in row), "y1": max(r["y1"] for r in row),
                "conf": min(r["conf"] for r in row), "anchor": a,
            })
    out.sort(key=lambda l: (l["y0"], l["x0"]))
    return out

def cluster_rects(rects, gap=24):
    rects = [list(r) for r in rects]
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(rects):
            j = i + 1
            while j < len(rects):
                a, b = rects[i], rects[j]
                if (a[0] - gap < b[2] and b[0] - gap < a[2] and
                        a[1] - gap < b[3] and b[1] - gap < a[3]):
                    rects[i] = [min(a[0], b[0]), min(a[1], b[1]),
                                max(a[2], b[2]), max(a[3], b[3])]
                    rects.pop(j); changed = True
                else:
                    j += 1
            i += 1
    return rects

def parse_articles(body_text, body_rows):
    arts, seen = [], set()
    for m in RE_ART_G.finditer(body_text):
        prefix = fix_alpha_prefix(m.group(1).upper())
        num = m.group(2)
        stueck = ("je " if m.group(3) else "") + m.group(4).replace(".", ",") \
                 + (" Set" if m.group(5) else "")
        prefix = PREFIXFIX.get(prefix, prefix)
        farbe = m.group(6).strip(" |.-")
        farbe = re.sub(r"^\d+\.\s*", "", farbe).replace("|", " ").strip() or None
        farbe = fix_farbe(re.sub(r"\s+", " ", farbe)) if farbe else None
        groesse = re.sub(r"\s+", "", m.group(7)).replace("cm", " cm")
        key = (prefix, num, groesse, farbe)
        if key in seen:
            continue
        seen.add(key)
        arts.append({"artnr": f"{prefix} {num}", "stueck": stueck,
                     "farbe": farbe, "groesse": groesse})
    # short article rows: "Art. BRI 3110 onyxschwarz" (no pieces/size printed)
    for r in body_rows:
        m = RE_ART_SHORT.match(r["text"])
        if m:
            prefix = fix_alpha_prefix(m.group(1).upper())
            prefix = PREFIXFIX.get(prefix, prefix)
            if any((a["artnr"] == f"{prefix} {m.group(2)}") for a in arts):
                continue
            arts.append({"artnr": f"{prefix} {m.group(2)}", "stueck": None,
                         "farbe": fix_farbe(m.group(3).strip()), "groesse": None})
    return arts

def main():
    with open(RAW, encoding="utf-8") as f:
        pages = json.load(f)

    entries, covers, problems, checklist = [], [], [], []
    serie_current = None

    for p in pages:
        pno = p["page"]
        if pno in SPECIAL_PAGES:
            checklist.append({"page": pno, "serie": serie_current, "codes": [],
                              "typ": "SPEZIAL (manuell erfasst)"})
            continue
        lines = [px_line(l) for l in p["lines"] if l["text"].strip()]

        # header
        serie = None; material = None; display_title = None
        for l in lines:
            if l["y0"] > 330:
                continue
            m = re.match(r"^Serie\s+(.{2,40})$", l["text"])
            if m and "engers" not in m.group(1):
                serie = re.sub(r"\s*by engers.*$", "", m.group(1)).strip()
            m2 = re.match(r"^(Display|Theken-Display|Boden-Display)\s+(.{2,50})$", l["text"])
            if m2:
                display_title = l["text"]; serie = m2.group(2).strip()
            m3 = re.match(r"^(Steingut|Feinsteinzeug|Mosaik|Steinzeug)\b(.*)$", l["text"])
            if m3:
                material = l["text"]
        if serie:
            serie_current = serie

        # code lines (single OCR boxes)
        code_lines = []
        for l in lines:
            t = l["text"].replace(" ", "")
            m = RE_TAFEL_CODE.match(t)
            if m:
                code_lines.append((l, t))

        anchors = find_anchors([l["x0"] for l, _ in code_lines]) or [0]
        rows = merge_rows(lines, anchors)

        # board regions: images + big vector fills
        big_rects = [[r["x0"], r["y0"], r["x1"], r["y1"]] for r in p["rects"]
                     if r["fill"] and (r["x1"] - r["x0"]) > 60 and (r["y1"] - r["y0"]) > 60]
        imgs = [r for r in p["images"] if r[3] > 70]

        def to_px(cs):
            return [[c[0] / PX2PT, c[1] / PX2PT, c[2] / PX2PT, c[3] / PX2PT] for c in cs
                    if (c[2] - c[0]) > 100 and (c[3] - c[1]) > 80]

        clusters_img_px = to_px(cluster_rects(list(imgs)))
        clusters_all_px = to_px(cluster_rects(imgs + big_rects))

        page_codes = [c for _, c in code_lines]
        typ = None

        if not code_lines:
            if serie and len(lines) <= 6:
                covers.append({"page": pno, "serie": serie, "rect": [0, 68, 595.3, 841.9]})
                typ = "Serien-Deckblatt"
            elif len(lines) <= 4:
                typ = "Ambientebild (keine Daten)"
            else:
                typ = "UNKLAR - nicht erfasst"
                problems.append({"page": pno, "grund": "Seite ohne Tafel-Code, Layout unbekannt",
                                 "zeilen": [l["text"] for l in lines][:14]})
            checklist.append({"page": pno, "serie": serie_current, "codes": [], "typ": typ})
            continue

        checklist.append({"page": pno, "serie": serie_current, "codes": page_codes,
                          "typ": "Display" if display_title else "Tafeln"})

        # group code rows into blocks (stacked codes = one tafel with variants)
        code_rows = [r for r in rows if RE_TAFEL_CODE.match(r["text"].replace(" ", ""))]
        blocks = []
        for r in code_rows:
            attached = False
            for b in blocks:
                last = b["rows"][-1]
                if r["anchor"] == last["anchor"] and 0 <= r["y0"] - last["y1"] < 55:
                    b["rows"].append(r); b["codes"].append(r["text"].replace(" ", ""))
                    attached = True; break
            if not attached:
                blocks.append({"codes": [r["text"].replace(" ", "")], "rows": [r]})

        for b in blocks:
            first, last = b["rows"][0], b["rows"][-1]
            a = first["anchor"]
            next_y = min([o["rows"][0]["y0"] for o in blocks
                          if o is not b and o["rows"][0]["anchor"] == a
                          and o["rows"][0]["y0"] > last["y1"]] or [10 ** 9])
            cap = last["y1"] + 900
            body = [r for r in rows if r["anchor"] == a and last["y1"] - 6 < r["y0"] < min(next_y, cap)
                    and r not in b["rows"] and r["text"] not in ("Poster", "Etikett")]

            size = None; gt = False; label = None; notes = []
            lowconf = [r["text"] for r in b["rows"] + body if r["conf"] < 0.82]

            size_rows = set()
            for r in body:
                despaced = r["text"].replace(" ", "")
                if size is None and not RE_ART_START.search(r["text"]):
                    m = RE_SIZE_PREFIX.match(despaced)
                    if m and len(m.group(0)) >= 5:
                        matched = m.group(0)
                        gt = bool(m.group(1))
                        s = matched[2:] if gt else matched
                        s = s.replace("cm", "").replace("/", " / ")
                        s = re.sub(r"\s*/\s*Sonderanfertigung", " / Sonderanfertigung", s + " cm")
                        size = ("GT " if gt else "") + s
                        size_rows.add(id(r))
                        rest = r["text"].replace(" ", "")[len(matched):].strip(" ,")
                        if len(rest) > 3:
                            notes.append(re.sub(r"(?<=[a-zäöüß])(?=[A-Z])", " ", rest))
                        continue
                if ("Poster" in r["text"] or "Etikett" in r["text"]) and RE_LABEL_CODE.search(despaced):
                    label = fix_label_code(r["text"])
                    continue

            body_text = " ".join(r["text"] for r in body)
            arts = parse_articles(body_text, body)

            # leftover informative rows -> notes
            for r in body:
                t = r["text"]
                despaced = t.replace(" ", "")
                if id(r) in size_rows:
                    continue
                if label and (("Poster" in t or "Etikett" in t) and RE_LABEL_CODE.search(despaced)):
                    continue
                if RE_ART_START.search(t) or RE_ART_G.search(t):
                    continue
                if re.match(r"^\(?\d+(,\d+)?\s*(St|Stk)k?\.?\)?", t) or re.match(r"^\d+x\d+cm$", despaced):
                    continue  # article fragments already captured
                if len(t) > 2:
                    notes.append(t)

            def find_board(clusters_px):
                board = None; best_d = 10 ** 9
                for c in clusters_px:
                    if c[3] <= first["y0"] + 40 and c[2] > a - 60 and c[0] < a + 950:
                        d = first["y0"] - c[3]
                        if -40 <= d < min(best_d, 260):
                            best_d = d; board = c
                return board
            board = find_board(clusters_img_px) or find_board(clusters_all_px)
            unklar = []
            if not size and not display_title:
                unklar.append("keine Größenangabe erkannt")
            if not arts and not display_title:
                unklar.append("keine Artikelzeile erkannt")
            if board is None:
                unklar.append("kein Foto zugeordnet")
            if lowconf:
                unklar.append("niedrige OCR-Konfidenz: " + " | ".join(lowconf[:3]))

            eid = f"p{pno:03d}_{b['codes'][0].replace('-', '')}"
            entry = {
                "id": eid, "seite": pno, "serie": serie_current, "material": material,
                "codes": b["codes"], "tafel_groesse": size, "gt": gt, "artikel": arts,
                "label": label, "notizen": notes,
                "board_px200": [round(v) for v in board] if board else None,
                "display": bool(display_title),
            }
            if unklar:
                entry["unklar"] = unklar
                problems.append({"page": pno, "grund": "; ".join(unklar), "codes": b["codes"]})
            entries.append(entry)

    # merge manually verified entries + overrides for special pages
    man_path = os.path.join(HERE, "manual_entries.json")
    if os.path.exists(man_path):
        with open(man_path, encoding="utf-8") as f:
            man = json.load(f)
        for eid, patch in man["overrides"].items():
            for e in entries:
                if e["id"] == eid:
                    e.update(patch)
        entries.extend(man["entries"])
        man_pages = {}
        for e in man["entries"]:
            man_pages.setdefault(e["seite"], []).append(
                e["codes"][0] if e["codes"] else e.get("name", "?"))
        for ck in checklist:
            if ck["page"] in man_pages:
                ck["codes"] = man_pages[ck["page"]]
                ck["typ"] = "manuell erfasst"
        entries.sort(key=lambda e: e["seite"])
    problems.append({"page": 261, "grund": "Nur Foto eines COLOR IT Theken-Displays, "
                     "Detailtext im Foto nicht zuverlässig lesbar - nicht erfasst"})

    result = {"entries": entries, "covers": covers, "problems": problems, "checklist": checklist}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("entries:", len(entries), "| covers:", len(covers), "| problems:", len(problems),
          "| no-photo:", sum(1 for e in entries if not e["board_px200"]))

if __name__ == "__main__":
    main()
