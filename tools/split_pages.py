"""Split the original PDF into lossless single-page PDFs: pages/seite-NNN.pdf"""
import fitz, os, time

PDF = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln engers.pdf"
OUT = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog\pages"
os.makedirs(OUT, exist_ok=True)

src = fitz.open(PDF)
t0 = time.time()
total = 0
for i in range(src.page_count):
    dst = fitz.open()
    dst.insert_pdf(src, from_page=i, to_page=i)
    f = os.path.join(OUT, f"seite-{i+1:03d}.pdf")
    dst.save(f, garbage=4, deflate=True)
    dst.close()
    total += os.path.getsize(f)
print(f"{src.page_count} Seiten-PDFs, {total/1e6:.1f} MB gesamt, {time.time()-t0:.0f}s")
