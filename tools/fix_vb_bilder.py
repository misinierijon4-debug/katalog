"""Repariert fehlende/weiße Tafelfotos der V&B-Einträge.

Der Import (import_vb_gesamt.py) suchte Fotos über eingebettete PDF-Bildobjekte;
auf manchen Seiten liegen die Fotos aber anders vor -> weißer Crop oder keiner.
Dieses Skript rendert die betroffenen Seiten und findet die Foto-Region
pixelbasiert (nicht-weiße Fläche in der Spur des jeweiligen Codes).

Aufruf:  uv run --with pdfplumber,pypdfium2,pillow,numpy,pypdf python tools/fix_vb_bilder.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pdfplumber
import pypdfium2 as pdfium
from PIL import Image

ROOT = Path(r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog")
SOURCE = ROOT / "VB_Mustertafelkataloge_gesamt.pdf"
CODE_RE = re.compile(r"\d{4}-[A-Z0-9]{2,5}-[A-Z0-9]{2}-\d{2}", re.I)
SCALE = 2.0
MIN_THUMB_BYTES = 4000  # kleinere Thumbs sind praktisch weiß


def load_katalog_js():
    raw = (ROOT / "katalog.js").read_text(encoding="utf-8").strip()
    body = re.sub(r"^window\.KATALOG_DATA\s*=\s*", "", raw).rstrip(";")
    return json.loads(body)


def save_katalog_js(data):
    out = "window.KATALOG_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (ROOT / "katalog.js").write_text(out, encoding="utf-8")


def targets(data):
    """Einträge mit fehlendem oder verdächtig kleinem (weißem) Bild."""
    result = []
    for e in data:
        if e.get("marke") != "vb":
            continue
        t = ROOT / "images" / "thumb" / (e["id"] + ".jpg")
        if not t.exists() or t.stat().st_size < MIN_THUMB_BYTES:
            result.append(e)
    return result


def code_groups(words):
    found = []
    for w in words:
        for code in CODE_RE.findall(w["text"]):
            item = dict(w)
            item["code"] = code.upper()
            found.append(item)
    groups = []
    for word in sorted(found, key=lambda w: (w["x0"], w["top"])):
        target = None
        for g in reversed(groups):
            if abs(g["x"] - word["x0"]) < 8 and 0 <= word["top"] - g["last_top"] <= 20:
                target = g
                break
        if target is None:
            groups.append({"x": word["x0"], "top": word["top"], "last_top": word["top"],
                           "codes": [word["code"]]})
        else:
            if word["code"] not in target["codes"]:
                target["codes"].append(word["code"])
            target["last_top"] = word["top"]
    return sorted(groups, key=lambda g: (g["top"], g["x"]))


def lane_for(group, groups, page_width):
    left = group["x"] < page_width / 2
    siblings = [g for g in groups if g is not group and abs(g["top"] - group["top"]) < 40
                and (g["x"] < page_width / 2) != left]
    if siblings:
        return (20, page_width / 2) if left else (page_width / 2, page_width - 20), True, left
    return (20, page_width - 20), False, left


def photo_bbox(img: Image.Image, x0, y0, x1, y1):
    """Bounding-Box der nicht-weißen Fläche im Bereich, per Zeilen-/Spaltendichte."""
    region = np.asarray(img.convert("L").crop((int(x0), int(y0), int(x1), int(y1))))
    mask = region < 235  # alles deutlich dunkler als Papierweiß
    if mask.mean() < 0.01:
        return None
    rows = mask.mean(axis=1)
    cols = mask.mean(axis=0)
    ry = np.where(rows > 0.04)[0]
    rx = np.where(cols > 0.04)[0]
    if len(ry) < 40 or len(rx) < 40:  # weniger als ~20pt Inhalt -> nur Textreste
        return None
    pad = 4
    return (x0 + max(0, rx[0] - pad), y0 + max(0, ry[0] - pad),
            x0 + min(mask.shape[1], rx[-1] + pad), y0 + min(mask.shape[0], ry[-1] + pad))


def save_images(img: Image.Image, box, entry_id):
    crop = img.crop(tuple(int(v) for v in box)).convert("RGB")
    if crop.width < 60 or crop.height < 40:
        return False
    large = crop.copy(); large.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
    thumb = crop.copy(); thumb.thumbnail((520, 520), Image.Resampling.LANCZOS)
    large.save(ROOT / "images" / "large" / f"{entry_id}.jpg", "JPEG", quality=90, optimize=True)
    thumb.save(ROOT / "images" / "thumb" / f"{entry_id}.jpg", "JPEG", quality=86, optimize=True)
    return True


def main():
    data = load_katalog_js()
    todo = targets(data)
    print(f"Zu reparieren: {len(todo)} Einträge")
    by_page = {}
    for e in todo:
        by_page.setdefault(e["seite"], []).append(e)

    doc = pdfium.PdfDocument(str(SOURCE))
    fixed, failed = [], []
    with pdfplumber.open(str(SOURCE)) as pdf:
        for page_no, entries in sorted(by_page.items()):
            page = pdf.pages[page_no - 1]
            words = page.extract_words(extra_attrs=["size"])
            groups = code_groups(words)
            render = doc[page_no - 1].render(scale=SCALE).to_pil()
            for e in entries:
                group = next((g for g in groups
                              if any(c in g["codes"] for c in (x.upper() for x in e["codes"]))), None)
                if group is None:
                    failed.append((e["id"], "Code auf Seite nicht gefunden"))
                    continue
                (lx0, lx1), split, left = lane_for(group, groups, page.width)
                above = [g["last_top"] for g in groups if g["last_top"] < group["top"] - 20
                         and ((g["x"] < page.width / 2) == left or not split)]
                band_top = max([t + 40 for t in above], default=80)
                if band_top >= group["top"] - 30:  # Band zu schmal/negativ -> ganze Spur absuchen
                    band_top = 80
                # Variante A: Foto oberhalb des Codes (Standard-Layout)
                bbox_a = None
                if group["top"] - 4 > band_top:
                    box_pt = (lx0, band_top, lx1, group["top"] - 4)
                    bbox_a = photo_bbox(render, *(v * SCALE for v in box_pt))
                # Variante B: Foto links neben dem Code (Zeilen-Layout, z. B. 9792-Seiten)
                bbox_b = None
                if group["x"] > 120:
                    next_top = min((g["top"] for g in groups if g["top"] > group["top"] + 20),
                                   default=page.height - 60)
                    box_pt = (20, group["top"] - 20, group["x"] - 8, next_top - 25)
                    if box_pt[2] - box_pt[0] > 60 and box_pt[3] - box_pt[1] > 40:
                        bbox_b = photo_bbox(render, *(v * SCALE for v in box_pt))
                # größere Fläche gewinnt (schützt vor Kopfzeilen/Sticker-Fehltreffern)
                def area(b):
                    return (b[2] - b[0]) * (b[3] - b[1]) if b else 0
                bbox = bbox_a if area(bbox_a) >= area(bbox_b) else bbox_b
                if bbox is None:
                    failed.append((e["id"], "keine Foto-Fläche gefunden"))
                    continue
                if save_images(render, bbox, e["id"]):
                    e["img"] = True
                    fixed.append(e["id"])
                else:
                    failed.append((e["id"], "Crop zu klein"))

    save_katalog_js(data)
    print(f"repariert: {len(fixed)}")
    for f in fixed:
        print("  ok ", f)
    print(f"nicht reparierbar: {len(failed)}")
    for eid, why in failed:
        print("  -- ", eid, "->", why)


if __name__ == "__main__":
    main()
