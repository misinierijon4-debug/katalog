"""Second OCR pass for rotated (landscape-in-portrait) pages.

Renders pages rotated 90° clockwise and OCRs them. Pages passed as args.
Appends results to ocr_rot.json: {page: [...lines in rotated coords...]}
"""
import fitz, json, os, sys
from rapidocr_onnxruntime import RapidOCR

PDF = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln engers.pdf"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ocr_rot.json")

doc = fitz.open(PDF)
ocr = RapidOCR()
res = {}
for pno in [int(x) for x in sys.argv[1:]]:
    page = doc[pno - 1]
    pix = page.get_pixmap(dpi=200, matrix=fitz.Matrix(200/72, 200/72).prerotate(90))
    result, _ = ocr(pix.tobytes("png"))
    lines = []
    if result:
        for box, txt, conf in result:
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            lines.append({"x0": round(min(xs)), "y0": round(min(ys)),
                          "x1": round(max(xs)), "y1": round(max(ys)),
                          "conf": round(float(conf), 3), "text": txt})
    res[str(pno)] = lines
    print("page", pno, "->", len(lines), "lines")
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("saved", OUT)
