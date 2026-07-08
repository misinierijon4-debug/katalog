"""Full OCR + layout dump for the Mustertafeln PDF.

Output: ocr_raw.json with per-page OCR lines (text, bbox at 200dpi, confidence)
plus vector-drawing rects and image rects (PDF points, 72dpi) for board detection.
"""
import fitz, json, os, sys, time
from rapidocr_onnxruntime import RapidOCR

PDF = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln engers.pdf"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ocr_raw.json")
PROGRESS = os.path.join(HERE, "ocr_progress.txt")

doc = fitz.open(PDF)
ocr = RapidOCR()

pages = []
t_start = time.time()
for i in range(doc.page_count):
    page = doc[i]
    pix = page.get_pixmap(dpi=200)
    result, _ = ocr(pix.tobytes("png"))
    lines = []
    if result:
        for box, txt, conf in result:
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            lines.append({
                "x0": round(min(xs)), "y0": round(min(ys)),
                "x1": round(max(xs)), "y1": round(max(ys)),
                "conf": round(float(conf), 3), "text": txt,
            })
    # vector fills (board backgrounds) - keep only large rects
    rects = []
    for d in page.get_drawings():
        r = d["rect"]
        if r.width > 40 and r.height > 40:
            rects.append({"x0": round(r.x0, 1), "y0": round(r.y0, 1),
                          "x1": round(r.x1, 1), "y1": round(r.y1, 1),
                          "fill": bool(d.get("fill")), "type": d.get("type")})
    imgs = []
    for inf in page.get_image_info():
        b = inf["bbox"]
        if (b[2] - b[0]) > 15 and (b[3] - b[1]) > 8:
            imgs.append([round(v, 1) for v in b])
    pages.append({"page": i + 1, "lines": lines, "rects": rects, "images": imgs})
    with open(PROGRESS, "w") as f:
        f.write(f"{i+1}/{doc.page_count} elapsed={time.time()-t_start:.0f}s\n")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(pages, f, ensure_ascii=False)
print("DONE", len(pages), "pages in", round(time.time() - t_start), "s")
