"""Import the complete V&B sample-panel PDF into Mustertafeln-Katalog.

The source is a compilation containing repeated catalogue sections. Entries are
deduplicated by overlapping panel codes, while every unique code remains
searchable. Existing URBAN PULSE entries keep their IDs.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium
from PIL import Image
from pypdf import PdfReader, PdfWriter

SOURCE = Path(r"C:\Users\Mirsad.Karasalihovic\AppData\Local\Temp\VB_Mustertafelkataloge_gesamt (2).pdf")
ROOT = Path(r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog")
CODE_RE = re.compile(r"\d{4}-[A-Z0-9]{2,5}-[A-Z0-9]{2}-\d{2}", re.I)
ART_RE = re.compile(r"^(?:\d{4}[A-Z0-9-]{2,8}|[A-Z]{2,5}\s*\d{3,5})$", re.I)
SIZE_RE = re.compile(r"^\d+(?:[.,]\d+)?x\d+(?:[.,]\d+)?(?:\s*cm)?$", re.I)
CATEGORIES = ("Bodentafeln", "Wandtafeln", "Handtafeln", "Displays", "Rückwand")
BAD_TITLES = {
    "MUSTERTAFELKATALOG", "SAMPLE PANEL CATALOGUE", "NEUHEITEN", "NOVELTIES",
    "BEMUSTERUNG NEUHEITEN", "SAMPLING NOVELTIES", "AUSGABE", "EDITION",
}


def data_entries(data: dict) -> tuple[str, list[dict]]:
    key = next(k for k in data if "eintr" in k)
    return key, data[key]


def clean_series(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"^\s*\d+\s*[|·-]?\s*", "", value).strip(" |·-\n\t")
    value = re.sub(r"\s+", " ", value)
    if not value or len(value) > 60 or value.upper() in BAD_TITLES:
        return None
    if CODE_RE.search(value) or value.lower() in {"floor panels", "wall panels", "sample panel formats"}:
        return None
    return value


def page_series(text: str, words: list[dict] | None, current: str | None) -> str | None:
    # Most layouts expose a large title in the upper-left corner.
    title_words = [w for w in (words or []) if w["top"] < 100 and w.get("size", 0) >= 15.5
                   and w["x0"] < 430 and not str(w["text"]).isdigit()]
    if title_words:
        lines: list[list[dict]] = []
        for w in sorted(title_words, key=lambda z: (z["top"], z["x0"])):
            if not lines or abs(lines[-1][0]["top"] - w["top"]) > 3:
                lines.append([w])
            else:
                lines[-1].append(w)
        for line in lines:
            candidate = clean_series(" ".join(w["text"] for w in line))
            if candidate and not any(x.lower() in candidate.lower() for x in ("floor panels", "wall panels")):
                return candidate

    # Fallback for titles represented by a font pdfplumber cannot decode.
    compact = re.sub(r"\s+", " ", text.replace("|", " ")).strip()
    for category in CATEGORIES:
        pos = compact.find(category)
        if pos >= 0:
            prefix = compact[max(0, pos - 70):pos]
            prefix = re.sub(r".*(?:Catalogue|Katalog|202[0-9])\s*", "", prefix, flags=re.I)
            candidate = clean_series(prefix)
            if candidate:
                return candidate

    # Divider pages normally contain only the series name.
    lines = [clean_series(x) for x in text.splitlines()]
    lines = [x for x in lines if x]
    if len(lines) <= 4:
        for candidate in lines:
            if candidate and candidate.upper() == candidate and len(candidate) >= 3:
                return candidate
    return current


def material_from(text: str) -> str | None:
    for category in CATEGORIES:
        if category.lower() in text.lower():
            return category
    if "floor panels" in text.lower():
        return "Bodentafeln"
    if "wall panels" in text.lower():
        return "Wandtafeln"
    return None


def code_words(words: list[dict]) -> list[dict]:
    found = []
    for w in words:
        matches = CODE_RE.findall(w["text"])
        for code in matches:
            item = dict(w)
            item["code"] = code.upper()
            found.append(item)
    return found


def group_codes(found: list[dict]) -> list[dict]:
    groups: list[dict] = []
    for word in sorted(found, key=lambda w: (w["x0"], w["top"])):
        target = None
        for group in reversed(groups):
            if abs(group["x"] - word["x0"]) < 8 and 0 <= word["top"] - group["last_top"] <= 20:
                target = group
                break
        if target is None:
            groups.append({"x": word["x0"], "top": word["top"], "last_top": word["top"],
                           "bottom": word["bottom"], "codes": [word["code"]]})
        else:
            if word["code"] not in target["codes"]:
                target["codes"].append(word["code"])
            target["last_top"] = word["top"]
            target["bottom"] = max(target["bottom"], word["bottom"])
    return sorted(groups, key=lambda g: (g["top"], g["x"]))


def line_words(words: list[dict]) -> list[list[dict]]:
    lines: list[list[dict]] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if not lines or abs(lines[-1][0]["top"] - word["top"]) > 3:
            lines.append([word])
        else:
            lines[-1].append(word)
    return lines


def parse_group(group: dict, groups: list[dict], words: list[dict], page_width: float) -> dict:
    left_side = group["x"] < page_width / 2
    siblings = [g for g in groups if g is not group and abs(g["top"] - group["top"]) < 40
                and (g["x"] < page_width / 2) != left_side]
    split = bool(siblings)
    x0, x1 = (20, page_width / 2) if left_side else (page_width / 2, page_width - 20)
    if not split:
        x0, x1 = 20, page_width - 20
    same_lane = [g for g in groups if g["top"] > group["top"] + 20
                 and ((g["x"] < page_width / 2) == left_side or not split)]
    end = min((g["top"] for g in same_lane), default=745) - 8
    region = [w for w in words if x0 <= (w["x0"] + w["x1"]) / 2 <= x1
              and group["top"] - 3 <= w["top"] < end]
    lines = line_words(region)
    texts = [" ".join(w["text"] for w in line) for line in lines]
    joined = " | ".join(texts[:6])
    size = None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*x\s*(\d+(?:[.,]\d+)?)\s*cm", joined, re.I)
    if m:
        size = f"{m.group(1)} x {m.group(2)} cm"
    label_parts = []
    for label in ("Übersichtstafel", "Poster", "Etikett", "Bestückungssatz", "Rückwand"):
        if label.lower() in joined.lower():
            label_parts.append(label)
    label = " & ".join(label_parts) or None

    articles = []
    for line in lines:
        vals = [w["text"].strip() for w in line]
        if len(vals) < 3 or not re.fullmatch(r"\d+(?:[.,]\d+)?", vals[0]):
            continue
        art_idx = next((i for i, value in enumerate(vals[1:], 1) if ART_RE.match(value)), None)
        size_idx = next((i for i, value in enumerate(vals[1:], 1) if SIZE_RE.match(value)), None)
        if art_idx is None or size_idx is None or size_idx <= art_idx:
            continue
        articles.append({
            "stueck": vals[0],
            "artnr": vals[art_idx],
            "farbe": " ".join(vals[art_idx + 1:size_idx]) or None,
            "groesse": vals[size_idx].replace("cm", "").strip(),
        })
    return {"codes": group["codes"], "tafel_groesse": size, "label": label,
            "artikel": articles, "x0": x0, "x1": x1, "end": end, "split": split}


def crop_box(group: dict, parsed: dict, groups: list[dict], images: list[dict], page_height: float) -> tuple[float, float, float, float] | None:
    same_lane_before = [g for g in groups if g["top"] < group["top"] - 20
                        and ((g["x"] < 297) == (group["x"] < 297) or not parsed["split"])]
    band_top = max((g["top"] + 70 for g in same_lane_before), default=95)
    candidates = []
    for image in images:
        cx = (image["x0"] + image["x1"]) / 2
        if image["top"] < band_top or image["bottom"] > group["top"] - 3:
            continue
        if parsed["split"] and not parsed["x0"] <= cx <= parsed["x1"]:
            continue
        if image["x1"] - image["x0"] < 8 or image["bottom"] - image["top"] < 2:
            continue
        candidates.append(image)
    if not candidates:
        top = max(95, band_top)
        if group["top"] - top < 25:
            return None
        return parsed["x0"] + 15, top, parsed["x1"] - 15, group["top"] - 6
    x0 = max(parsed["x0"], min(i["x0"] for i in candidates) - 4)
    x1 = min(parsed["x1"], max(i["x1"] for i in candidates) + 4)
    y0 = max(80, min(i["top"] for i in candidates) - 4)
    y1 = min(group["top"] - 4, max(i["bottom"] for i in candidates) + 4)
    return (x0, y0, x1, y1) if x1 - x0 > 30 and y1 - y0 > 20 else None


def render_crop(doc: pdfium.PdfDocument, pno: int, box: tuple[float, float, float, float], entry_id: str) -> None:
    scale = 2.0
    image = doc[pno].render(scale=scale).to_pil().convert("RGB")
    crop = image.crop(tuple(int(v * scale) for v in box))
    if crop.width < 30 or crop.height < 20:
        return
    large = crop.copy()
    large.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
    thumb = crop.copy()
    thumb.thumbnail((520, 520), Image.Resampling.LANCZOS)
    large.save(ROOT / "images" / "large" / f"{entry_id}.jpg", "JPEG", quality=90, optimize=True)
    thumb.save(ROOT / "images" / "thumb" / f"{entry_id}.jpg", "JPEG", quality=86, optimize=True)


def merge_into(entry: dict, parsed: dict, page_no: int, series: str, material: str | None) -> None:
    entry["marke"] = "vb"
    entry["seite"] = page_no
    entry["serie"] = series
    entry["material"] = material
    entry["codes"] = list(dict.fromkeys(entry.get("codes", []) + parsed["codes"]))
    if parsed["tafel_groesse"]:
        entry["tafel_groesse"] = parsed["tafel_groesse"]
    if parsed["label"]:
        entry["label"] = parsed["label"]
    if parsed["artikel"]:
        entry["artikel"] = parsed["artikel"]
    entry.setdefault("gt", False)
    entry.setdefault("display", False)
    notes = [n for n in entry.get("notizen", []) if "Neuheiten-Katalog 2026" not in n]
    if "V&B Gesamt-PDF" not in notes:
        notes.append("V&B Gesamt-PDF")
    entry["notizen"] = notes


def main() -> None:
    data_path = ROOT / "katalog.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    key, entries = data_entries(data)
    engers = [e for e in entries if e.get("marke") != "vb" and e.get("serie") != "URBAN PULSE"]
    existing_vb = [e for e in entries if e.get("marke") == "vb" or e.get("serie") == "URBAN PULSE"]
    code_map: dict[str, dict] = {}
    for entry in existing_vb:
        entry["_mapped"] = False
        for code in entry.get("codes", []):
            code_map[code.upper()] = entry

    new_entries: list[dict] = []
    page_records: dict[int, list[tuple[dict, dict, dict, tuple | None]]] = defaultdict(list)
    problems = []
    current_series = None

    text_reader = PdfReader(str(SOURCE))
    page_texts = []
    for index, page in enumerate(text_reader.pages):
        page_texts.append(page.extract_text() or "")
        if (index + 1) % 50 == 0:
            print(f"Textlayer {index + 1}/{len(text_reader.pages)}", flush=True)

    with pdfplumber.open(str(SOURCE)) as pdf:
        total = len(pdf.pages)
        for index, page in enumerate(pdf.pages):
            page_no = index + 1
            text = page_texts[index]
            if not CODE_RE.search(text):
                current_series = page_series(text, None, current_series)
                if page_no % 50 == 0:
                    print(f"analysiert {page_no}/{total}", flush=True)
                continue
            words = page.extract_words(extra_attrs=["size"])
            current_series = page_series(text, words, current_series)
            found = code_words(words)
            if not found:
                if page_no % 50 == 0:
                    print(f"analysiert {page_no}/{total}", flush=True)
                continue
            groups = group_codes(found)
            material = material_from(text)
            if not groups:
                problems.append({"seite_vb": page_no, "problem": "Codes erkannt, aber keine Tafelgruppe"})
                continue
            for group in groups:
                parsed = parse_group(group, groups, words, page.width)
                overlaps = [code_map[c] for c in parsed["codes"] if c in code_map]
                entry = overlaps[0] if overlaps else None
                if entry is not None and entry.get("_mapped"):
                    for code in parsed["codes"]:
                        if code not in entry["codes"]:
                            entry["codes"].append(code)
                        code_map[code] = entry
                    continue
                series = current_series or "V&B"
                if entry is None:
                    primary = re.sub(r"[^A-Z0-9]", "", parsed["codes"][0].upper())
                    entry = {
                        "id": f"vb_p{page_no:03}_{primary}", "seite": page_no, "serie": series,
                        "material": material, "codes": [], "tafel_groesse": None, "gt": False,
                        "artikel": [], "label": None, "notizen": [], "display": material == "Displays",
                        "marke": "vb",
                    }
                    new_entries.append(entry)
                merge_into(entry, parsed, page_no, series, material)
                entry["_mapped"] = True
                for code in entry["codes"]:
                    code_map[code.upper()] = entry
                box = crop_box(group, parsed, groups, page.images, page.height)
                page_records[page_no].append((entry, group, parsed, box))
            if page_no % 25 == 0:
                print(f"analysiert {page_no}/{total}", flush=True)

    unmapped = [e for e in existing_vb if not e.get("_mapped")]
    for entry in unmapped:
        problems.append({"id": entry["id"], "problem": "Bestehender V&B-Eintrag nicht im Gesamt-PDF gefunden"})
    final_vb = [e for e in existing_vb if e.get("_mapped")] + new_entries
    for entry in final_vb:
        entry.pop("_mapped", None)

    # Render one crop per canonical entry from its selected source page.
    doc = pdfium.PdfDocument(str(SOURCE))
    rendered = set()
    for page_no, records in sorted(page_records.items()):
        for entry, group, parsed, box in records:
            if entry["id"] in rendered or box is None:
                continue
            render_crop(doc, page_no - 1, box, entry["id"])
            rendered.add(entry["id"])
        if page_no % 25 == 0:
            print(f"Bilder bis Seite {page_no}", flush=True)

    # Generate lossless printable source pages only for canonical entries.
    page_dir = ROOT / "pages" / "vb"
    page_dir.mkdir(parents=True, exist_ok=True)
    used_pages = sorted({e["seite"] for e in final_vb})
    reader = PdfReader(str(SOURCE))
    for page_no in used_pages:
        writer = PdfWriter()
        writer.add_page(reader.pages[page_no - 1])
        with (page_dir / f"seite-{page_no:03}.pdf").open("wb") as handle:
            writer.write(handle)

    all_codes = {c for e in final_vb for c in e.get("codes", [])}
    data[key] = engers + sorted(final_vb, key=lambda e: (e["seite"], e["id"]))
    data["quelle"] = re.sub(r"\s*\|?\s*V&B.*$", "", data.get("quelle", "")) + " | V&B Gesamt-PDF (641 Seiten)"
    data["probleme"] = [p for p in data.get("probleme", []) if "seite_vb" not in p and "V&B" not in str(p)] + problems
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    shutil.copy2(SOURCE, ROOT / "VB_Mustertafelkataloge_gesamt.pdf")
    print(f"FERTIG: engers={len(engers)}, vb={len(final_vb)}, codes={len(all_codes)}, "
          f"neue={len(new_entries)}, Seiten-PDFs={len(used_pages)}, Bilder={len(rendered)}, Probleme={len(problems)}")


if __name__ == "__main__":
    main()
